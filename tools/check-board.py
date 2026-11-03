"""Actual localhost product transactions under ordinary Osaka code/gas limits."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
import board_abi as abi
spec = importlib.util.spec_from_file_location('inspector', ROOT / 'tools/check-native.py')
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', required=True, type=Path)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--anvil', default='anvil')
    parser.add_argument('--cast', default='cast')
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--port', default=0, type=int)
    parser.add_argument('--abi-edges', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'linux' or not __debug__:
        parser.error('Linux and Python assertions enabled are required')
    logs = args.evidence.resolve()
    logs.mkdir(parents=True, exist_ok=False)
    build = args.build_dir.resolve()
    metadata = json.loads((build / 'AssignmentBoard.metadata.json').read_text())
    assert metadata['compiler'] == {'commit':'149c758', 'version':'26.5.1'}
    mapping = {'assignment/src/lib.fe':'ingots/assignment/src/lib.fe',
               'src/lib.fe':'ingots/board/src/lib.fe', 'src/tests.fe':'ingots/board/src/tests.fe'}
    sources = {}
    for key, name in mapping.items():
        content = (PRODUCT / name).read_bytes()
        assert metadata['sources'][key]['content'].encode() == content
        sources[name] = sha(content)
    record = {'sources':sources}
    tools = {}
    for name in ['anvil','cast']:
        path = shutil.which(getattr(args,name))
        if not path:
            parser.error('Missing executable: '+name)
        tools[name] = str(Path(path).resolve())
        version = subprocess.check_output([tools[name],'--version']).decode()
        if '1.8.7' not in version or '985eeea031d79922cd654d4e94e6c3701e1c7d73' not in version:
            parser.error('Expected Foundry1.8.7 full commit for '+name)
    creation = bytes.fromhex((build / 'AssignmentBoard.bin').read_text().strip().removeprefix('0x'))
    runtime = bytes.fromhex((build / 'AssignmentBoard.runtime.bin').read_text().strip().removeprefix('0x'))
    assert len(runtime)+96 <= 24576 and len(creation)+96 <= 49152
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',args.port))
        port = probe.getsockname()[1]
    command = [tools['anvil'], '--host','127.0.0.1','--port',str(port),
               '--chain-id','31337','--gas-limit','30000000','--hardfork','osaka',
               '--enable-tx-gas-limit','--silent']
    report = dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), command=command,
                  build_dir=str(build), source_hashes=record['sources'], creation_bytes=len(creation),
                  runtime_bytes=len(runtime), initcode_with_arguments_bytes=len(creation)+96,
                  normal_code_init_limits=True, tx_gas_limit=16777216, cases=[],
                  classification='Actual FeAssign product on isolated localhost; no real funds',
                  abi_edges=args.abi_edges, runner_sha256=sha(Path(__file__).read_bytes()), success=False)
    process = None
    transaction_index = 0

    def save():
        (logs / 'results.json').write_bytes((json.dumps(report, indent=2)+'\n').encode())

    def rpc(method, params):
        return abi.rpc(process, port, method, params)

    def call(address, data):
        return rpc('eth_call', [dict(to=address, data='0x'+data.hex(), gas=hex(16777216)), 'latest'])

    def send(label, data, address=None, expected=1):
        nonlocal transaction_index
        transaction_index += 1
        filename = f'{transaction_index:03}-{label}'
        (logs / (filename+'.hex')).write_text('0x'+data.hex()+'\n', encoding='ascii')
        transaction = {'from':sender, 'gas':hex(16777216), 'value':'0x0', 'data':'0x'+data.hex()}
        if address:
            transaction['to'] = address
        response = rpc('eth_sendTransaction', [transaction])
        row = dict(label=label, bytes=len(data), data_sha256=sha(data), gas_limit=16777216,
                   calldata_floor_reservation=21000+10*(data.count(0)+4*(len(data)-data.count(0))),
                   rpc=response, expected_receipt_status=expected)
        report['cases'].append(row)
        save()
        assert 'result' in response, row
        deadline = time.monotonic()+10
        while True:
            receipt = rpc('eth_getTransactionReceipt', [response['result']])['result']
            if receipt is not None:
                break
            if time.monotonic() >= deadline:
                row['receipt_observation_timeout'] = True
                save()
                raise RuntimeError('No receipt observed; inspect same owned node/transaction evidence')
            time.sleep(0.05)
        row.update(receipt=receipt, gas_used=int(receipt['gasUsed'], 16))
        included = rpc('eth_getTransactionByHash', [response['result']])['result']
        row['included_transaction_gas_limit'] = int(included['gas'], 16)
        save()
        assert int(receipt['status'], 16) == expected, row
        assert row['included_transaction_gas_limit'] == 16777216
        assert row['gas_used'] < 16777216, 'Must distinguish ordinary rejection from gas exhaustion'
        return receipt, row

    def snapshot(address):
        # Emitted IR has mutable solved/total at slots0/1 and chosen[32] from2.
        return [rpc('eth_getStorageAt', [address, hex(i), 'latest'])['result'] for i in range(34)]

    cast = Path(tools['cast'])
    selectors = {name: abi.selector(signature, cast) for name, signature in {
        'details': 'details()', 'total': 'totalCost()', 'selected': 'selectedColumn(uint8)',
        'submit': 'submit(int64[],uint8[],int128[],int128[])'}.items()}
    report['selectors'] = {k:v.hex() for k,v in selectors.items()}
    native = str(args.executable.resolve())
    report['native_executable'] = native
    report['native_binary_sha256'] = sha(Path(native).read_bytes())
    with (logs / 'node.stdout.log').open('wb') as stdout, (logs / 'node.stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        report['pid'] = process.pid
        try:
            deadline = time.monotonic()+15
            while True:
                try:
                    version = rpc('web3_clientVersion', [])['result']
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(0.1)
            report['client_version'] = version
            assert 'anvil/v1.8.7' in version.lower()
            assert rpc('eth_chainId', [])['result'] == '0x7a69'
            sender = rpc('eth_accounts', [])['result'][0]
            block = rpc('eth_getBlockByNumber', ['latest', False])['result']
            assert int(block['gasLimit'], 16) == 30000000
            cap = rpc('eth_sendTransaction', [{'from': sender, 'to': sender, 'value':'0x0', 'gas':hex(16777217)}])
            report['above_transaction_cap_control'] = cap
            assert 'error' in cap

            def deploy(name, r, c, digest):
                receipt, row = send(name+'-deploy', creation+abi.word(r)+abi.word(c)+digest)
                address = receipt['contractAddress']
                deployed = bytes.fromhex(rpc('eth_getCode', [address, 'latest'])['result'][2:])
                row['deployed_runtime_bytes'] = len(deployed)
                row['deployed_runtime_sha256'] = sha(deployed)
                (logs / (name+'-deployed-code.hex')).write_text('0x'+deployed.hex()+'\n', encoding='ascii')
                row['immutable_tail_bytes'] = len(deployed)-len(runtime)
                assert len(deployed) == len(runtime)+96 and len(deployed) <= 24576
                assert deployed.startswith(runtime)
                row['immutable_tail_hex'] = deployed[len(runtime):].hex()
                details = bytes.fromhex(call(address, selectors['details'])['result'][2:])
                assert details == abi.word(r)+abi.word(c)+digest+abi.word(0)
                assert 'error' in call(address, selectors['total'])
                return address

            def reject(name, address, data):
                before = snapshot(address)
                simulation = call(address, data)
                assert 'error' in simulation, simulation
                _, row = send(name, data, address, expected=0)
                after = snapshot(address)
                row.update(revert_call=simulation, storage_before=before, storage_after=after,
                           storage_unchanged=before == after)
                assert before == after
                save()

            scenarios = [('rectangle', 2, 3, [4, 1, 8, 2, 6, 3]),
                         ('full32-zero-chain', 32, 32, [0 if j == 0 else 1 for i in range(32) for j in range(32)]),
                         ('full32-i64-min', 32, 32, [inspector.MIN64]*1024),
                         ('full32-endpoint-delta', 32, 32, [inspector.MIN64 if j == 0 else inspector.MAX64
                                                          for i in range(32) for j in range(32)])]
            if args.abi_edges:
                scenarios = scenarios[:1]
            for name, r, c, costs in scenarios:
                solved = subprocess.run([native, 'solve'],
                    input=inspector.solve_input(r, c, costs), capture_output=True, timeout=30)
                assert solved.returncode == 0 and not solved.stderr
                proof = inspector.inspect_certificate(solved.stdout, r, c, costs)
                (logs / (name+'.cert')).write_bytes(solved.stdout)
                payload = abi.problem_payload(r, c, costs)
                (logs / (name+'-problem-abi.hex')).write_text('0x'+payload.hex()+'\n', encoding='ascii')
                digest = abi.keccak(payload, cast)
                address = deploy(name, r, c, digest)
                submission = selectors['submit']+abi.submit_payload(costs, proof['selected'], proof['row_potentials'], proof['column_potentials'])
                assert len(submission) == 4+32*(8+r*c+2*r+c)
                if name == 'rectangle':
                    bad_p = [0, 0]
                    reject('duplicate-columns', address, selectors['submit']+abi.submit_payload(costs, bad_p, proof['row_potentials'], proof['column_potentials']))
                    shifted = [x+1 for x in costs]
                    reject('valid-proof-wrong-matrix', address, selectors['submit']+abi.submit_payload(shifted, proof['selected'], [x+1 for x in proof['row_potentials']], proof['column_potentials']))
                    reject('wrong-vector-length', address, selectors['submit']+abi.submit_payload(costs, [1], proof['row_potentials'], proof['column_potentials']))
                    if args.abi_edges:
                        body = submission[4:]
                        tail_offsets = [int.from_bytes(body[i:i+32], 'big') for i in range(0,128,32)]
                        def replace_word(data, offset, value):
                            return data[:offset]+abi.word(value)+data[offset+32:]
                        for field, offset, value in [
                            ('dirty-positive-i64', tail_offsets[0]+32, (1 << 64)+4),
                            ('dirty-uint8', tail_offsets[1]+32, (1 << 8)+1),
                            ('dirty-positive-i128-u', tail_offsets[2]+32, (1 << 128)+1),
                            ('dirty-positive-i128-v', tail_offsets[3]+32, 1 << 128),
                            ('cost-length-out-of-bounds', tail_offsets[0], 1025),
                            ('offset-overflow', 0, 2**256-32),
                            ('offset-into-head', 0, 0),
                        ]:
                            reject(field, address, selectors['submit']+replace_word(body, offset, value))
                        reject('truncated-tail', address, submission[:-1])
                        reject('extra-cost-length', address, selectors['submit']+abi.submit_payload(costs+[0], proof['selected'], proof['row_potentials'], proof['column_potentials']))
                        reject('short-row-dual', address, selectors['submit']+abi.submit_payload(costs, proof['selected'], [1], proof['column_potentials']))
                        reject('short-column-dual', address, selectors['submit']+abi.submit_payload(costs, proof['selected'], proof['row_potentials'], [0, 0]))
                        # Tail permutation is a different wire representation of the same values.
                        tails = [body[tail_offsets[i]:tail_offsets[i+1] if i < 3 else len(body)] for i in range(4)]
                        order, reordered_offsets, cursor = [3, 1, 0, 2], [0]*4, 128
                        for i in order:
                            reordered_offsets[i] = cursor
                            cursor += len(tails[i])
                        reordered = selectors['submit']+b''.join(map(abi.word, reordered_offsets))+b''.join(tails[i] for i in order)
                        response = call(address, reordered)
                        assert abi.signed_word(bytes.fromhex(response['result'][2:])) == proof['total']
                        report['accepted_reordered_tails'] = dict(order=order, total=proof['total'], raw_sha256=sha(reordered))
                        # A valid proof for identical flat values cannot change its semantic header.
                        header_mutations = [('different-rows-columns', abi.problem_payload(1, 6, costs)),
                            ('different-domain', replace_word(payload, 0, abi.DOMAIN ^ 1)),
                            ('different-version', replace_word(payload, 32, 2)),
                            ('different-objective', replace_word(payload, 64, 2))]
                        for label, changed in header_mutations:
                            other = deploy(label, r, c, abi.keccak(changed, cast))
                            reject(label+'-valid-proof', other, submission)
                    # Same values, nonminimal offsets plus one ignored suffix.
                    body = submission[4:]
                    heads = b''.join(abi.word(int.from_bytes(body[i:i+32], 'big')+32) for i in range(0,128,32))
                    nonminimal = selectors['submit']+heads+bytes(32)+body[128:]+b'ignored suffix'
                    simulated = call(address, nonminimal)
                    assert abi.signed_word(bytes.fromhex(simulated['result'][2:])) == proof['total']
                    report['accepted_semantic_wire_variant'] = dict(raw_bytes_differ=True, gap_bytes=32,
                        suffix_bytes=14, total=proof['total'], canonical_problem_digest=digest.hex())
                    submission = nonminimal
                simulated = call(address, submission)
                assert abi.signed_word(bytes.fromhex(simulated['result'][2:])) == proof['total']
                _, row = send(name+'-submit', submission, address)
                total = abi.signed_word(bytes.fromhex(call(address, selectors['total'])['result'][2:]))
                details = bytes.fromhex(call(address, selectors['details'])['result'][2:])
                assert total == proof['total'] and details == abi.word(r)+abi.word(c)+digest+abi.word(1)
                chosen = [int(call(address, selectors['selected']+abi.word(i))['result'], 16) for i in range(r)]
                assert chosen == proof['selected']
                row.update(recorded_total=total, recorded_selected=chosen, details_after=details.hex())
                reject(name+'-repeat', address, submission)
                save()
            if args.abi_edges:
                # Constructor shape rejection is a real failed creation receipt.
                for r, c in [(0, 1), (2, 1), (1, 33), (33, 33)]:
                    receipt, row = send(f'invalid-constructor-{r}-{c}', creation+abi.word(r)+abi.word(c)+bytes(32), expected=0)
                    assert receipt['contractAddress'] is None or rpc('eth_getCode', [receipt['contractAddress'], 'latest'])['result'] == '0x'
                for name, r, c, costs, p, u, v in [
                    ('valid-full-i128-gauge', 1, 1, [-1], [0], [inspector.MAX128], [inspector.MIN128]),
                    ('alternative-zero-optimum', 2, 2, [0]*4, [1, 0], [0, 0], [0, 0]),
                    ('rectangular-sign-controls', 1, 2, [5, 3], [1], [3], [0, 0]),
                ]:
                    total = sum(costs[i*c+j] for i, j in enumerate(p))
                    exported = inspector.envelope(r, c, costs, p, u, v, total)
                    inspector.inspect_certificate(exported, r, c, costs, total)
                    checked = subprocess.run([native, 'verify'],
                        input=exported, capture_output=True, timeout=30)
                    assert checked.returncode == 0 and checked.stdout == f'VALID {total}\n'.encode()
                    address = deploy(name, r, c, abi.keccak(abi.problem_payload(r, c, costs), cast))
                    data = selectors['submit']+abi.submit_payload(costs, p, u, v)
                    if name == 'valid-full-i128-gauge':
                        body = data[4:]
                        offsets = [int.from_bytes(body[i:i+32], 'big') for i in range(0,128,32)]
                        for label, offset, value in [
                            ('dirty-negative-i64', offsets[0]+32, 2**64-1),
                            ('dirty-negative-i128', offsets[3]+32, 2**127),
                        ]:
                            reject(label, address, selectors['submit']+replace_word(body, offset, value))
                    if name == 'rectangular-sign-controls':
                        reject('positive-column-only', address, selectors['submit']+abi.submit_payload(costs, [0], [3], [2, 0]))
                        reject('unused-column-only', address, selectors['submit']+abi.submit_payload(costs, [0], [5], [0, -2]))
                        reject('i128-wrap', address, selectors['submit']+abi.submit_payload(costs, [0], [inspector.MIN128+5], [inspector.MIN128, 0]))
                    _, row = send(name+'-submit', data, address)
                    recorded = abi.signed_word(bytes.fromhex(call(address, selectors['total'])['result'][2:]))
                    assert recorded == total
                    actual_p = [int(call(address, selectors['selected']+abi.word(i))['result'], 16) for i in range(r)]
                    assert actual_p == p
                    row.update(recorded_total=recorded, recorded_selected=actual_p)
                    assert 'error' in call(address, selectors['selected']+abi.word(r))
                    save()
            report['success'] = True
        except Exception as error:
            report['error'] = repr(error)
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            report.update(node_stopped=process.poll() is not None, node_exit_code=process.returncode,
                          ended_utc=dt.datetime.now(dt.timezone.utc).isoformat())
            save()
            print(json.dumps({k:report.get(k) for k in ['success', 'runtime_bytes', 'initcode_with_arguments_bytes', 'error', 'node_stopped']}))


if __name__ == '__main__':
    main()
