"""Real Linux descriptor, incremental-input and interrupted-read checks."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_inspector', ROOT / 'tools/check-native.py')
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'linux' or not __debug__:
        parser.error('Linux/WSL and Python assertions enabled are required')
    executable = args.executable.resolve()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    records = []
    active = None
    success = False
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    def spawn(**kwargs):
        return subprocess.Popen([str(executable), 'solve'], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kwargs)

    def collect(process, code):
        out, err = process.communicate(timeout=5)
        assert process.returncode == code, (process.returncode, out, err)
        if code != 0:
            assert out == b'' and err == b'feassign: input/output failure\n', (out, err)
        else:
            assert err == b''
        return out

    def wait_blocked(process):
        until = time.monotonic()+5
        while time.monotonic() < until:
            assert process.poll() is None
            channel = Path(f'/proc/{process.pid}/wchan').read_text().strip()
            if channel in ('pipe_read', 'anon_pipe_read'):
                return channel
            time.sleep(0.005)
        raise AssertionError('Child not observed waiting in a pipe read')

    try:
        # Byte-at-a-time writes, with the writer open until the complete input.
        active = spawn(stdin=subprocess.PIPE)
        data = inspector.solve_input(2, 3, [4, 1, 8, 2, 6, 3])
        for byte in data:
            active.stdin.write(bytes([byte]))
            active.stdin.flush()
            time.sleep(0.002)
        channel = wait_blocked(active)
        assert not select.select([active.stdout], [], [], 0)[0], 'success before EOF'
        active.stdin.close()
        active.stdin = None
        out = collect(active, 0)
        inspector.inspect_certificate(out, 2, 3, [4, 1, 8, 2, 6, 3], 3)
        records.append(dict(name='byte-at-a-time-input', actual=0, bytes=len(data), waiting=channel))

        # A syntactically complete prefix must still wait for EOF/trailing input.
        active = spawn(stdin=subprocess.PIPE)
        active.stdin.write(inspector.HEADER+b'1 1 0 ')
        active.stdin.flush()
        channel = wait_blocked(active)
        assert not select.select([active.stdout], [], [], 0)[0]
        active.stdin.write(b'1')
        active.stdin.close()
        active.stdin = None
        out, err = active.communicate(timeout=5)
        assert active.returncode == 2 and out == b'' and err == b'feassign: invalid input\n'
        records.append(dict(name='valid-prefix-then-extra-token', actual=2, waiting=channel))

        # Actual EAGAIN, both before any token and after otherwise valid bytes.
        for name, prefix in [('empty-nonblocking', b''), ('prefix-nonblocking', inspector.HEADER+b'1 1 0 ')]:
            read_fd, write_fd = os.pipe()
            try:
                os.set_blocking(read_fd, False)
                if prefix:
                    os.write(write_fd, prefix)
                active = spawn(stdin=read_fd)
                collect(active, 5)  # Keep writer open: neither case is EOF.
                records.append(dict(name=name, actual=5, prefix_hex=prefix.hex(), writer_open=True))
            finally:
                os.close(read_fd)
                os.close(write_fd)

        helper = evidence / 'interrupt.so'
        command = ['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                   str(ROOT / 'tests/native/interrupt.c'), '-o', str(helper)]
        built = subprocess.run(command, capture_output=True, timeout=30)
        (evidence / 'interrupt-build.log').write_bytes(built.stdout+built.stderr)
        assert built.returncode == 0
        # The helper sets only a test signal handler. It does not replace read,
        # write, ferror, feof, fflush, our bridge, or the Fe executable.
        env = os.environ.copy()
        env['LD_PRELOAD'] = str(helper)
        for name, prefix in [('handled-eintr-empty', b''), ('handled-eintr-after-prefix', inspector.HEADER+b'1 1 0 ')]:
            active = spawn(stdin=subprocess.PIPE, env=env)
            if prefix:
                active.stdin.write(prefix)
                active.stdin.flush()
            channel = wait_blocked(active)
            os.kill(active.pid, signal.SIGUSR1)
            active.wait(timeout=5)  # Writer remains open until read was interrupted.
            active.stdin.close()
            active.stdin = None
            collect(active, 5)
            records.append(dict(name=name, actual=5, signal='SIGUSR1', waiting=channel,
                                sa_restart=False, writer_open_until_child_exit=True))

        # Large output forces a write failure before the final flush as well.
        with open('/dev/full', 'wb', buffering=0) as full:
            active = subprocess.Popen([str(executable), 'solve'], stdin=subprocess.PIPE,
                                      stdout=full, stderr=subprocess.PIPE)
            costs = list(range(1024))
            _, err = active.communicate(inspector.solve_input(32, 32, costs), timeout=10)
        assert active.returncode == 5
        records.append(dict(name='large-output-dev-full', actual=5, bytes_if_success='over libc buffer'))
        # stderr errors must not accidentally turn a usage/input failure into success.
        with open('/dev/full', 'wb', buffering=0) as full:
            active = subprocess.Popen([str(executable), 'solve'], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=full)
            out, _ = active.communicate(b'bad', timeout=5)
        assert active.returncode == 5 and out == b''
        records.append(dict(name='stderr-flush-failure', actual=5))
        success = True
    finally:
        if active is not None and active.poll() is None:
            active.kill()
            active.communicate()
        report = dict(started_utc=started, ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                      success=success, records=records, executable_sha256=sha(executable),
                      inspector_sha256=sha(Path(__file__)),
                      helper_source_sha256=sha(ROOT / 'tests/native/interrupt.c'),
                      helper_scope='Test-only handled SIGUSR1; no replaced I/O functions',
                      limits=['Not a guarantee against abrupt kill or host resource exhaustion',
                              'No I/O deadline, retry loop or durability claim'])
        (evidence / 'results.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(dict(success=success, checks=len(records), evidence=str(evidence))), flush=True)


if __name__ == '__main__':
    main()
