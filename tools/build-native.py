"""Build the actual Fe CLI on Linux with its scalar-only stdio bridge."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fe', default='fe')
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'target/native')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / '.cache/native')
    args = parser.parse_args()
    if sys.platform != 'linux' or platform.machine() not in ('x86_64', 'AMD64'):
        parser.error('Run inside Linux x86-64, including the dedicated WSL distribution')
    fe = shutil.which(args.fe)
    cc = shutil.which('cc')  # Resolve BEFORE prepending the child-only wrapper.
    if not fe or not cc:
        parser.error('Fe 26.5.1 and a system C compiler named cc are required')
    fe, cc = str(Path(fe).resolve()), str(Path(cc).resolve())
    version = subprocess.run([fe, '--version'], check=True, capture_output=True, text=True).stdout.strip()
    if '26.5.1' not in version or '149c758' not in version:
        parser.error('Expected pinned Fe 26.5.1 (149c758)')
    pin = json.loads((ROOT / 'toolchain.json').read_text(encoding='utf-8'))
    if digest(Path(fe)) != pin['linux_amd64_asset_sha256']:
        parser.error('Compiler bytes do not match the pinned Linux x86-64 release asset')
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    wrapper_dir = out / 'link-driver'
    wrapper_dir.mkdir(exist_ok=True)
    wrapper = wrapper_dir / 'cc'
    trace = out / 'linker-args.txt'
    bridge = ROOT / 'native/io.c'
    wrapper.write_text('#!/bin/sh\nset -eu\n'
                       + 'printf \'%s\\n\' "$@" > ' + shlex.quote(str(trace)) + '\n'
                       + 'exec ' + shlex.quote(cc) + ' "$@" -std=c11 -Wall -Wextra -Werror '
                       + shlex.quote(str(bridge)) + '\n', encoding='utf-8', newline='\n')
    wrapper.chmod(0o755)
    env = os.environ.copy()
    env['PATH'] = str(wrapper_dir) + os.pathsep + env.get('PATH', '')
    env['FE_CACHE_DIR'] = str(args.cache_dir.resolve())
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    command = [fe, '--color', 'never', 'build', str(ROOT), '--ingot', 'cli',
               '--backend', 'native', '--emit', 'executable', '-O', '1', '--out-dir', str(out)]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / 'build.log').write_bytes(result.stdout)
    sys.stdout.buffer.write(result.stdout)
    executable = out / 'cli'
    if result.returncode == 0:
        if not executable.is_file():
            raise RuntimeError('Compiler succeeded without the expected CLI executable')
        executable.rename(out / 'feassign')
    sources = sorted([ROOT / 'fe.toml', ROOT / 'toolchain.json', bridge, Path(__file__).resolve()]
                     + list((ROOT / 'ingots/assignment').rglob('*.fe'))
                     + list((ROOT / 'ingots/cli').rglob('*.fe'))
                     + list((ROOT / 'ingots').glob('*/fe.toml')))
    report = dict(started_utc=started, ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  command=command, exit_code=result.returncode, fe_version=version,
                  fe_sha256=digest(Path(fe)), system_cc=cc,
                  sources={str(p.relative_to(ROOT)): digest(p) for p in sources},
                  child_only_path=True, bridge='native/io.c',
                  executable_sha256=digest(out / 'feassign') if result.returncode == 0 else None)
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
