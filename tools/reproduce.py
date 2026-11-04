"""Reproduce FeAssign with fresh outputs."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files():
    for directory, names, files in os.walk(ROOT):
        names[:] = [n for n in names if n not in ('.git','.cache','out','target','__pycache__')]
        for name in sorted(files):
            path = Path(directory)/name
            yield str(path.relative_to(ROOT)), sha(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fe',default='fe')
    parser.add_argument('--anvil',default='anvil')
    parser.add_argument('--cast',default='cast')
    parser.add_argument('--out',required=True,type=Path)
    args = parser.parse_args()
    if sys.platform != 'linux' or not __debug__:
        parser.error('Enable Python assertions on Linux')
    binaries = {}
    for name in ['fe','anvil','cast']:
        path = shutil.which(getattr(args,name))
        if not path:
            parser.error('Missing executable: '+name)
        binaries[name] = str(Path(path).resolve())
    out = args.out.resolve()
    if out.is_relative_to(ROOT) and not out.is_relative_to(ROOT/'target'):
        parser.error('Use target/ or a fresh directory outside the source root')
    out.mkdir(parents=True)
    (out/'tmp').mkdir()
    (out/'cache').mkdir()
    initial_sources = dict(source_files())
    env = os.environ.copy()
    env['TMPDIR'] = str(out/'tmp')
    env['FE_CACHE_DIR'] = str(out/'cache')
    report = dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),success=False,
                  source_root=str(ROOT),source_hashes=initial_sources,records=[],
                  tool_binaries={k:dict(path=v,sha256=sha(Path(v))) for k,v in binaries.items()},
                  fresh_output=True,fresh_cache=True)
    marker = ROOT/'SOURCE_COMMIT'
    if marker.is_file():
        report['source_commit'] = marker.read_text().strip()
        if not re.fullmatch('[0-9a-f]{40}',report['source_commit']):
            raise RuntimeError('SOURCE_COMMIT must contain a full SHA')

    def save():
        (out/'reproduce.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

    def run(label,command,passed=None):
        record = dict(label=label,command=command,started_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        report['records'].append(record)
        save()
        with (out/(label+'.stdout')).open('wb') as stdout, (out/(label+'.stderr')).open('wb') as stderr:
            with subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True) as result:
                try:
                    result.wait(timeout=300)
                finally:
                    if result.returncode is None:
                        os.killpg(result.pid,signal.SIGKILL)
        record.update(exit_code=result.returncode,ended_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        if passed is not None:
            match = re.search(rb'(\d+) passed; (\d+) failed',b''.join((out/(label+x)).read_bytes() for x in ('.stdout','.stderr')))
            record['expected_functions'] = passed
            assert match and (int(match[1]),int(match[2])) == (passed,0), record
        save()
        if result.returncode != 0:
            raise RuntimeError(label+' failed; see logs')
        print(label+': passed',flush=True)

    try:
        version = subprocess.check_output([binaries['fe'],'--version']).decode().strip()
        pin = json.loads((ROOT/'toolchain.json').read_text())
        assert '26.5.1' in version and '149c758' in version
        assert sha(Path(binaries['fe'])) == pin['linux_amd64_asset_sha256']
        report['fe_version'] = version
        for backend in ['native','sonatina']:
            for ingot,count in [('assignment',8),('api_tests',46)]:
                run(ingot+'-'+backend,[binaries['fe'],'--color','never','test',str(ROOT),
                    '--ingot',ingot,'--backend',backend,'-O','1'],count)
        run('board-sonatina',[binaries['fe'],'--color','never','test',str(ROOT),
                              '--ingot','board','--backend','sonatina','-O','1'],2)
        run('api-boundaries',[sys.executable,str(ROOT/'tools/check-api-boundaries.py'),'--fe',binaries['fe']])
        demo = out/'demo'
        run('demo',[sys.executable,str(ROOT/'tools/demo.py'),'--fe',binaries['fe'],
            '--anvil',binaries['anvil'],'--cast',binaries['cast'],'--out',str(demo)])
        executable = demo/'native/feassign'
        run('native-certificates',[sys.executable,str(ROOT/'tools/check-native.py'),
            '--executable',str(executable),'--evidence',str(out/'native-certificates')])
        run('native-io',[sys.executable,str(ROOT/'tools/check-native-io.py'),
            '--executable',str(executable),'--evidence',str(out/'native-io')])
        common = [sys.executable,str(ROOT/'tools/check-board.py'),'--build-dir',str(demo/'board'),
            '--executable',str(executable),'--anvil',binaries['anvil'],'--cast',binaries['cast']]
        run('board-full32',common+['--evidence',str(out/'board-full32')])
        run('board-abi-edges',common+['--evidence',str(out/'board-abi-edges'),'--abi-edges'])
        observed = {name:json.loads(path.read_text()) for name,path in {
            'demo':demo/'demo.json','native':out/'native-certificates/results.json',
            'io':out/'native-io/results.json','full32':out/'board-full32/results.json',
            'abi':out/'board-abi-edges/results.json'}.items()}
        assert all(value['success'] for value in observed.values())
        assert observed['native']['counts']['certificates'] == observed['native']['counts']['roundtrips'] == 2906
        assert observed['native']['counts']['negative'] == 43
        assert len(observed['io']['records']) == 8
        assert len(observed['full32']['cases']) == 15 and len(observed['abi']['cases']) == 40
        assert all(observed[name]['node_stopped'] for name in ['demo','full32','abi'])
        assert dict(source_files()) == initial_sources, 'Source bytes changed during reproduction'
        report['observed_summary'] = dict(common_fe_functions_per_backend=54,evm_board_functions=2,
            intended_compiler_rejections=5,exported_certificates=2906,roundtrips=2906,
            classified_negative_cases=43,descriptor_checks=8,demo_transactions=5,
            full32_campaign_transactions=15,abi_campaign_transactions=40,
            all_owned_nodes_stopped=True,source_unchanged=True)
        report['success'] = True
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        report['ended_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        save()
    print('Full local reproduction passed: '+str(out/'reproduce.json'),flush=True)


if __name__ == '__main__':
    main()
