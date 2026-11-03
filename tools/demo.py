"""Build and run the complete local FeAssign example on Linux x86-64.

Owns one ephemeral localhost Anvil; never connects a wallet or remote endpoint.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

import board_abi as abi
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_inspector', ROOT / 'tools/check-native.py')
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fe', default='fe')
    parser.add_argument('--anvil', default='anvil')
    parser.add_argument('--cast', default='cast')
    parser.add_argument('--out', required=True, type=Path, help='New evidence directory')
    parser.add_argument('--port', default=0, type=int)
    args = parser.parse_args()
    if sys.platform != 'linux' or not __debug__:
        parser.error('Linux x86-64 and Python assertions enabled are required')
    binaries = {}
    for name in ['fe', 'anvil', 'cast']:
        path = shutil.which(getattr(args, name))
        if not path:
            parser.error('Missing executable: '+name)
        binaries[name] = str(Path(path).resolve())
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    temporary = out / 'tmp'
    temporary.mkdir()
    env = os.environ.copy()
    env['TMPDIR'] = str(temporary)
    env['FE_CACHE_DIR'] = str(out / 'cache')
    versions = {name: subprocess.check_output([path, '--version']).decode().strip()
                for name, path in binaries.items()}
    for name in ['anvil', 'cast']:
        if '1.8.7' not in versions[name] or '985eeea031d79922cd654d4e94e6c3701e1c7d73' not in versions[name]:
            raise RuntimeError('Expected pinned Foundry1.8.7 full commit for '+name)
    report = dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), success=False,
                  versions=versions, binary_sha256={k:sha(Path(v)) for k,v in binaries.items()},
                  platform=sys.platform, transactions=[], native_timings={}, local_only=True)
    node = None

    def save():
        (out / 'demo.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')

    def run(label, command, data=None):
        start = time.perf_counter_ns()
        result = subprocess.run(command, input=data, capture_output=True, env=env, timeout=180)
        elapsed = time.perf_counter_ns()-start
        (out / (label+'.stdout')).write_bytes(result.stdout)
        (out / (label+'.stderr')).write_bytes(result.stderr)
        if result.returncode:
            raise RuntimeError(f'{label} failed with exit {result.returncode}; inspect preserved logs')
        return result, elapsed

    def rpc(method, params):
        return abi.rpc(node, port, method, params)

    def call(address, data):
        return rpc('eth_call', [dict(to=address, data='0x'+data.hex(), gas=hex(16777216)), 'latest'])

    def snapshot(address):
        return [rpc('eth_getStorageAt', [address, hex(i), 'latest'])['result'] for i in range(34)]

    def transaction(label, data, address=None, expected=1):
        (out / (label+'.calldata.hex')).write_text('0x'+data.hex()+'\n', encoding='ascii')
        request = {'from':sender, 'gas':hex(16777216), 'value':'0x0', 'data':'0x'+data.hex()}
        if address:
            request['to'] = address
        response = rpc('eth_sendTransaction', [request])
        record = dict(label=label, request=request, rpc=response, expected_status=expected)
        report['transactions'].append(record)
        save()
        if 'result' not in response:
            raise RuntimeError('Transaction RPC rejected '+label)
        until = time.monotonic()+15
        while True:
            receipt = rpc('eth_getTransactionReceipt', [response['result']])['result']
            if receipt is not None:
                break
            if time.monotonic() >= until:
                record['receipt_observation_timeout'] = True
                save()
                raise RuntimeError('Receipt not observed; inspect saved node and transaction evidence')
            time.sleep(0.05)
        record['receipt'] = receipt
        record['gas_used'] = int(receipt['gasUsed'], 16)
        included = rpc('eth_getTransactionByHash', [response['result']])['result']
        record['included_gas_limit'] = int(included['gas'], 16)
        assert int(receipt['status'],16) == expected and record['gas_used'] < 16777216
        assert record['included_gas_limit'] == 16777216
        save()
        return receipt, record

    try:
        run('build-native', [sys.executable, str(ROOT / 'tools/build-native.py'), '--fe', binaries['fe'],
            '--out-dir', str(out / 'native'), '--cache-dir', str(out / 'cache')])
        board_command = [binaries['fe'], '--color', 'never', 'build', str(ROOT), '--ingot', 'board',
            '--backend', 'sonatina', '-O', '1', '--emit', 'bytecode,runtime-bytecode,abi,metadata',
            '--out-dir', str(out / 'board')]
        run('build-board', board_command)
        report['board_build_command'] = board_command
        executable = out / 'native/feassign'
        report['native_executable_sha256'] = sha(executable)
        _, baseline = run('native-startup-help', [str(executable), '--help'])
        example = (ROOT / 'examples/resource-batch.txt').read_bytes()
        costs = [1,2,9,1,100,3]
        assert example.split() == inspector.solve_input(2,3,costs).split()
        solved, solve_ns = run('native-solve', [str(executable), 'solve'], example)
        exact = inspector.exact_minimum(2,3,costs)
        proof = inspector.inspect_certificate(solved.stdout, 2, 3, costs, exact)
        # A transparent comparator for this example, never a product optimizer:
        # both row minima choose0 (infeasible); row-order greedy chooses[0,2].
        greedy = [0,2]
        greedy_total = sum(costs[i*3+j] for i,j in enumerate(greedy))
        assert proof['selected'] == [1,0] and exact == 3 < greedy_total == 4
        assert proof['column_potentials'][0] < 0
        report['comparison'] = dict(row_minima_selected=[0,0], row_minima_feasible=False,
            row_order_greedy_selected=greedy, row_order_greedy_total=greedy_total,
            independent_exact_minimum=exact,
            scope='Illustrative two-row comparison, not measured production benefit')
        checked, verify_ns = run('native-verify', [str(executable), 'verify'], solved.stdout)
        assert checked.stdout == b'VALID 3\n' and not solved.stderr and not checked.stderr
        (out / 'solution.cert').write_bytes(solved.stdout)
        report['native_timings'] = dict(startup_help_process_ns=baseline, solve_process_ns=solve_ns,
            verify_process_ns=verify_ns, scope='Single process-wall samples including startup/I/O; not isolated kernel timing')
        report['proof'] = proof
        print('Fe solved the two-job, three-resource example: columns [1,0], total3; resource2 unused.', flush=True)
        print('Both jobs prefer resource0; row-order greedy costs4. The certificate proves the global minimum3.', flush=True)
        print('Independent Python conditions and the Fe verify command passed.', flush=True)

        creation = bytes.fromhex((out / 'board/AssignmentBoard.bin').read_text().strip().removeprefix('0x'))
        emitted = bytes.fromhex((out / 'board/AssignmentBoard.runtime.bin').read_text().strip().removeprefix('0x'))
        problem = abi.problem_payload(2,3,costs)
        digest = abi.keccak(problem, binaries['cast'])
        report['problem_digest'] = '0x'+digest.hex()
        (out / 'problem.abi.hex').write_text('0x'+problem.hex()+'\n',encoding='ascii')
        initcode = creation+abi.word(2)+abi.word(3)+digest
        assert len(initcode) <= 49152
        report.update(initcode_bytes=len(initcode), emitted_runtime_bytes=len(emitted))
        selectors = {key:abi.selector(sig,binaries['cast']) for key,sig in {
            'submit':'submit(int64[],uint8[],int128[],int128[])','details':'details()',
            'total':'totalCost()','selected':'selectedColumn(uint8)'}.items()}
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', args.port))
            port = probe.getsockname()[1]
        report['node_port'] = port
        node_command = [binaries['anvil'], '--host', '127.0.0.1', '--port', str(port), '--chain-id','31337',
            '--gas-limit','30000000','--hardfork','osaka','--enable-tx-gas-limit','--silent']
        report['node_command'] = node_command
        with (out / 'node.stdout').open('wb') as stdout, (out / 'node.stderr').open('wb') as stderr:
            node = subprocess.Popen(node_command, stdout=stdout, stderr=stderr, env=env)
        report['node_pid'] = node.pid
        until = time.monotonic()+15
        while True:
            try:
                report['node_client'] = rpc('web3_clientVersion',[])['result']
                break
            except OSError:
                if time.monotonic() >= until:
                    raise
                time.sleep(0.05)
        assert rpc('eth_chainId',[])['result'] == '0x7a69'
        sender = rpc('eth_accounts',[])['result'][0]
        cap_control = rpc('eth_sendTransaction',[{'from':sender,'to':sender,'gas':hex(16777217),'value':'0x0'}])
        assert 'error' in cap_control
        report['above_cap_control'] = cap_control
        receipt, _ = transaction('deploy',initcode)
        address = receipt['contractAddress']
        deployed = bytes.fromhex(rpc('eth_getCode',[address,'latest'])['result'][2:])
        assert len(deployed) <= 24576 and deployed.startswith(emitted)
        (out / 'deployed-code.hex').write_text('0x'+deployed.hex()+'\n',encoding='ascii')
        report.update(board_address=address,deployed_runtime_bytes=len(deployed),deployed_code_sha256=hashlib.sha256(deployed).hexdigest())
        before = snapshot(address)
        details_open = call(address,selectors['details'])['result']
        assert details_open == '0x'+(abi.word(2)+abi.word(3)+digest+abi.word(0)).hex()
        assert 'error' in call(address,selectors['total'])

        def rejected(label, data, message):
            before = snapshot(address)
            simulated = call(address,data)
            assert 'error' in simulated and message in simulated['error']['message']
            _, row = transaction(label,data,address,expected=0)
            after = snapshot(address)
            assert before == after
            row.update(storage_before=before,storage_after=after,state_unchanged=True,call_error=simulated['error'])
            print(label+': rejected; board state unchanged.',flush=True)
            save()

        p, u, v = proof['selected'],proof['row_potentials'],proof['column_potentials']
        rejected('invalid-certificate',selectors['submit']+abi.submit_payload(costs,[0,0],u,v),'invalid certificate')
        shifted = [x+1 for x in costs]
        inspector.inspect_certificate(inspector.envelope(2,3,shifted,p,[x+1 for x in u],v,5),2,3,shifted,5)
        rejected('different-matrix',selectors['submit']+abi.submit_payload(shifted,p,[x+1 for x in u],v),'wrong problem')
        data = selectors['submit']+abi.submit_payload(costs,p,u,v)
        _, row = transaction('record-result',data,address)
        total = abi.signed_word(bytes.fromhex(call(address,selectors['total'])['result'][2:]))
        chosen = [int(call(address,selectors['selected']+abi.word(i))['result'],16) for i in range(2)]
        assert total == proof['total'] == 3 and chosen == p
        details_solved = call(address,selectors['details'])['result']
        assert details_solved == '0x'+(abi.word(2)+abi.word(3)+digest+abi.word(1)).hex()
        row.update(recorded_total=total,recorded_selected=chosen,details_after=details_solved)
        print('Board receipt succeeded; stored columns [1,0] and total3 match Fe.',flush=True)
        rejected('repeat',data,'already solved')
        report['success'] = True
        report['source_hashes'] = {str(p.relative_to(ROOT)):sha(p) for p in
            sorted([ROOT/'fe.toml',ROOT/'toolchain.json',ROOT/'examples/resource-batch.txt',ROOT/'native/io.c']
            + list((ROOT/'ingots').rglob('*.fe'))+list((ROOT/'ingots').glob('*/fe.toml'))
            + list((ROOT/'tools').glob('*.py')))}
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        if node is not None:
            if node.poll() is None:
                node.terminate()
                try:
                    node.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    node.kill()
                    node.wait(timeout=5)
            report['node_stopped'] = node.poll() is not None
            report['node_exit_code'] = node.returncode
        report['ended_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        save()
    print('Complete local demo passed. Evidence: '+str(out/'demo.json'),flush=True)


if __name__ == '__main__':
    main()
