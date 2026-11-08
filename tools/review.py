"""Start a reproducible native review or the complete existing FeAssign checks."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
MAX_DOWNLOAD = 512 * 1024 * 1024


def sha(path):
    with path.open('rb') as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, path, expected):
    print('Downloading official asset: ' + url, flush=True)
    with urllib.request.urlopen(url, timeout=60) as response, path.open('xb') as output:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise ValueError('Official asset exceeded the download budget')
            output.write(chunk)
    if sha(path) != expected:
        raise ValueError('Downloaded asset SHA-256 mismatch; no downloaded tool was executed')


def tool(name, explicit, pins, allow_download):
    expected = pins['linux_amd64_asset_sha256' if name == 'fe' else name + '_linux_amd64_asset_sha256']
    cache = ROOT / '.cache/reviewer-tools'
    version = pins['fe_version' if name == 'fe' else 'anvil_version']
    cached = cache / (name + '-' + version)
    found = explicit or (str(cached) if cached.exists() else shutil.which(name))
    if found:
        resolved = shutil.which(str(found))
        if not resolved or sha(Path(resolved)) != expected:
            raise ValueError(name + ': expected the pinned Linux asset; check the path/SHA in toolchain.json')
        return str(Path(resolved).resolve())
    if not allow_download:
        raise ValueError(name + ': missing. Supply --' + name + ' /path/to/' + name + ' or opt in with --download')
    if not cache.resolve().is_relative_to(ROOT) or cache.is_symlink() or cached.is_symlink():
        raise ValueError('Tool cache must remain a regular directory inside this source checkout')
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='download-', dir=cache) as temporary:
        staging = Path(temporary)
        if name == 'fe':
            asset = staging / 'fe'
            download('https://github.com/argotorg/fe/releases/download/v' + version + '/fe_linux_amd64',
                     asset, expected)
            asset.chmod(0o755)
            with cached.open('xb') as output:
                output.write(asset.read_bytes())
            cached.chmod(0o755)
        else:
            archive = staging / 'foundry.tar.gz'
            download('https://github.com/foundry-rs/foundry/releases/download/v' + version
                     + '/foundry_v' + version + '_linux_amd64.tar.gz', archive,
                     pins['foundry_linux_amd64_archive_sha256'])
            with tarfile.open(archive, 'r:gz') as bundle:
                for binary in ('anvil', 'cast'):
                    member = bundle.getmember(binary)
                    if not member.isfile() or member.size > MAX_DOWNLOAD:
                        raise ValueError('Expected a bounded regular tool in the official archive')
                    source = bundle.extractfile(member)
                    if source is None:
                        raise ValueError('Could not read official ' + binary)
                    with source, (staging / binary).open('xb') as output:
                        shutil.copyfileobj(source, output)
                    if sha(staging / binary) != pins[binary + '_linux_amd64_asset_sha256']:
                        raise ValueError('Extracted ' + binary + ' SHA-256 mismatch')
            for binary in ('anvil', 'cast'):
                target = cache / (binary + '-' + version)
                if target.exists():
                    if sha(target) != pins[binary + '_linux_amd64_asset_sha256']:
                        raise ValueError('Existing ' + binary + ' cache differs; it was not overwritten')
                else:
                    with target.open('xb') as output:
                        output.write((staging / binary).read_bytes())
                    target.chmod(0o755)
    return str(cached)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scope', choices=('native', 'full'), nargs='?', default='native')
    parser.add_argument('--download', action='store_true', help='Allow SHA-verified official GitHub release downloads')
    for name in ('fe', 'anvil', 'cast'):
        parser.add_argument('--' + name)
    parser.add_argument('--out', type=Path, help='Fresh output directory; default: unique target/review-*')
    args = parser.parse_args()
    if sys.version_info < (3, 10) or sys.platform != 'linux' or platform.machine() not in ('x86_64', 'AMD64'):
        parser.error('Use Python 3.10+ inside Linux x86-64 (on Windows, open your WSL distribution). See JUDGING.md.')
    if not __debug__ or not shutil.which('cc'):
        parser.error('Enable Python assertions and install a C compiler named cc in your Linux environment.')
    libc, version = platform.libc_ver()
    if libc != 'glibc' or tuple(int(x) for x in version.split('.')[:2]) < (2, 39):
        parser.error('Pinned Fe requires glibc >= 2.39; use Ubuntu 24.04 x86-64 or a compatible environment.')
    out = (args.out or ROOT / ('target/review-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')
                               + '-' + uuid4().hex[:6])).resolve()
    if out.is_relative_to(ROOT) and not out.is_relative_to(ROOT / 'target'):
        parser.error('Use target/ or a fresh directory outside the source root')
    try:
        out.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        parser.error('Choose a fresh writable --out directory (or omit --out): ' + str(error))
    report = dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), scope=args.scope,
                  success=False, records=[], source_root=str(ROOT), tool_binaries={})

    def run(label, command, data=None, expected=0):
        print(label + ' ...', flush=True)
        result = subprocess.run(command, input=data, capture_output=True, cwd=ROOT,
                                timeout=None if args.scope == 'full' else 300)
        (out / (label + '.stdout')).write_bytes(result.stdout)
        (out / (label + '.stderr')).write_bytes(result.stderr)
        report['records'].append(dict(label=label, command=command, exit_code=result.returncode,
                                      expected_exit_code=expected))
        if result.returncode != expected:
            raise ValueError(label + ' failed; inspect ' + str(out / (label + '.stderr')))
        return result.stdout

    try:
        pins = json.loads((ROOT / 'toolchain.json').read_text(encoding='utf-8'))
        binaries = {name: tool(name, getattr(args, name), pins, args.download)
                    for name in (('fe',) if args.scope == 'native' else ('fe', 'anvil', 'cast'))}
        report['tool_binaries'] = {name: dict(path=path, sha256=sha(Path(path))) for name, path in binaries.items()}
        if args.scope == 'full':
            run('full', [sys.executable, str(ROOT / 'tools/reproduce.py'), '--fe', binaries['fe'],
                         '--anvil', binaries['anvil'], '--cast', binaries['cast'], '--out', str(out / 'full-run')])
            print('11-stage evidence: ' + str(out / 'full-run/reproduce.json'), flush=True)
        else:
            run('build', [sys.executable, str(ROOT / 'tools/build-native.py'), '--fe', binaries['fe'],
                          '--out-dir', str(out / 'native'), '--cache-dir', str(out / 'cache')])
            executable = str(out / 'native/feassign')
            certificate = run('solve', [executable, 'solve'], (ROOT / 'examples/resource-batch.txt').read_bytes())
            (out / 'solution.cert').write_bytes(certificate)
            if run('verify', [executable, 'verify'], certificate).strip() != b'VALID 3':
                raise ValueError('Expected the small optimum 3')
            # Keep the documented matrix/potentials; duplicate one selected column.
            tokens = certificate.decode('ascii').split()
            tokens[11] = tokens[10]
            run('reject-duplicate', [executable, 'verify'], (' '.join(tokens) + '\n').encode('ascii'), 4)
            for label in ('valid', 'converted'):
                result = run('external-' + label, [executable, 'verify'],
                             (ROOT / ('examples/external-unit-gap-' + label + '.cert')).read_bytes(),
                             0 if label == 'valid' else 4)
                if label == 'valid' and result.strip() != b'VALID 18014398509481984':
                    raise ValueError('Expected the exact wide-integer certificate total')
            run('native-smoke', [sys.executable, str(ROOT / 'tools/check-native.py'),
                                 '--executable', executable, '--smoke', '--evidence', str(out / 'checks')])
            print('VALID 3; duplicate rejected; exact wide witness accepted; converted witness rejected.', flush=True)
            print('This native review is a subset. Use full for the 11-stage EVM/native workflow.', flush=True)
        report['success'] = True
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
        print('Review failed: ' + str(error), file=sys.stderr)
    finally:
        report['ended_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (out / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print('Review record: ' + str(out / 'review.json'), flush=True)
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
