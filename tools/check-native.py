"""Execute Fe, inspect its exported certificates with Python integers, test I/O.

No host assignment optimizer: tiny problems enumerate injections; larger ones
check every primal/dual condition and justified metamorphic relations.
"""
import argparse
import datetime as dt
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MIN64, MAX64 = -(2**63), 2**63 - 1
MIN128, MAX128 = -(2**127), 2**127 - 1
HEADER = b'FEASSIGN 1\n'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def solve_input(r, c, costs):
    return HEADER + (f'{r} {c}\n' + ' '.join(map(str, costs)) + '\n').encode('ascii')


def envelope(r, c, costs, p, u, v, total):
    return (f'FEASSIGN 1\n{r} {c}\n' + '\n'.join(' '.join(map(str, a))
            for a in (costs, p, u, v)) + f'\nTOTAL {total}\n').encode('ascii')


def inspect_certificate(data, r, c, costs, expected=None):
    tokens = data.decode('ascii').split()
    assert tokens[:2] == ['FEASSIGN', '1']
    assert tokens[2:4] == [str(r), str(c)]
    assert len(tokens) == 4 + r*c + 2*r + c + 2
    assert all(re.fullmatch(r'-?[0-9]+', x) for x in tokens[4:-2] + tokens[-1:])
    numbers = list(map(int, tokens[4:-2]))
    assert numbers[:r*c] == costs, 'exported problem differs from actual input'
    p = numbers[r*c:r*c+r]
    u = numbers[r*c+r:r*c+2*r]
    v = numbers[r*c+2*r:]
    assert tokens[-2] == 'TOTAL'
    total = int(tokens[-1])
    assert all(0 <= col < c for col in p) and len(set(p)) == r
    assert all(MIN128 <= x <= MAX128 for x in u + v + [total])
    assert all(x <= 0 for x in v), 'column sign'
    for i in range(r):
        for j in range(c):
            assert u[i] + v[j] <= costs[i*c+j], ('dual feasibility', i, j)
        assert u[i] + v[p[i]] == costs[i*c+p[i]], ('selected tightness', i)
    assert all(v[j] == 0 for j in set(range(c)) - set(p)), 'unused zero'
    assert total == sum(costs[i*c+p[i]] for i in range(r))
    assert total == sum(u) + sum(v), 'full dual equality (Python wide integers)'
    if expected is not None:
        assert total == expected, ('independent expected cost', total, expected)
    return dict(selected=p, row_potentials=u, column_potentials=v, total=total)


def exact_minimum(r, c, costs):
    return min(sum(costs[i*c+j] for i, j in enumerate(p))
               for p in itertools.permutations(range(c), r))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'linux' or not __debug__:
        parser.error('Linux/WSL and Python assertions enabled are required')
    executable = args.executable.resolve()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    records = []
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    counts = dict(certificates=0, roundtrips=0, finite_space=0, all_shapes=0,
                  seeded=0, metamorphic=0, directed=0, negative=0, io=0)
    current = {}
    certificates = (evidence / 'certificates.jsonl').open('w', encoding='utf-8', newline='\n')

    def execute(mode, data):
        return subprocess.run([str(executable), mode], input=data, capture_output=True, timeout=10)

    def case(name, r, c, costs, expected=None, group='directed'):
        nonlocal current
        assert 1 <= r <= c <= 32 and len(costs) == r*c
        assert all(MIN64 <= value <= MAX64 for value in costs), 'test transform exceeded i64'
        current = dict(name=name, mode='solve', input=solve_input(r, c, costs).decode('ascii'))
        result = execute('solve', current['input'].encode('ascii'))
        current.update(returncode=result.returncode, stdout=result.stdout.decode('ascii', errors='backslashreplace'),
                       stderr=result.stderr.decode('ascii', errors='backslashreplace'))
        assert result.returncode == 0 and result.stderr == b'', current
        fields = inspect_certificate(result.stdout, r, c, costs, expected)
        repeat = execute('verify', result.stdout)
        assert repeat.returncode == 0 and repeat.stderr == b''
        assert repeat.stdout == f'VALID {fields["total"]}\n'.encode('ascii')
        counts['certificates'] += 1
        counts['roundtrips'] += 1
        counts[group] += 1
        certificates.write(json.dumps(dict(name=name, rows=r, columns=c, costs=costs,
                                expected=expected, **fields,
                                output_sha256=sha(result.stdout))) + '\n')
        return fields, result.stdout

    def reject(name, mode, data, code):
        nonlocal current
        current = dict(name=name, mode=mode, input_hex=data.hex())
        result = execute(mode, data)
        assert result.returncode == code, (name, result.returncode, result.stdout, result.stderr)
        assert result.stdout == b'', (name, 'unexpected success prefix')
        assert result.stderr.startswith(b'feassign: ')
        counts['negative'] += 1
        records.append(dict(name=name, mode=mode, expected=code, actual=result.returncode,
                            input_sha256=sha(data), stderr=result.stderr.decode('ascii')))

    try:
        _, sample = case('board-rectangle', 2, 3, [4, 1, 8, 2, 6, 3], 3)
        (evidence / 'sample-output.txt').write_bytes(sample)
        for value in [MIN64, MAX64, -1, 0]:
            case(f'singleton-{value}', 1, 1, [value], value)
        case('endpoint-delta', 2, 3, [MIN64, MAX64, MAX64] * 2, -1)
        for value in [MIN64, MAX64, 0]:
            case(f'full32-constant-{value}', 32, 32, [value] * 1024, 32*value)
        chain = [0 if j == 0 else 1 for _ in range(32) for j in range(32)]
        case('full32-zero-delta-chain', 32, 32, chain, 31)
        # Accept a valid extreme square gauge, but reject hostile sums without overflow.
        extreme = envelope(1, 1, [-1], [0], [MAX128], [MIN128], -1)
        got = execute('verify', extreme)
        assert got.returncode == 0 and got.stdout == b'VALID -1\n' and got.stderr == b''
        records.append(dict(name='full-i128-gauge-valid', actual=got.returncode))
        if not args.smoke:
            manifest = json.loads((ROOT / 'docs/evidence/oracle-cases.json').read_text())
            for space in manifest['spaces']:
                r, c, alphabet = space['rows'], space['columns'], space['alphabet']
                for ordinal in range(space['matrices']):
                    digits, costs = ordinal, []
                    for _ in range(r*c):
                        costs.append(alphabet[digits % len(alphabet)])
                        digits //= len(alphabet)
                    expected = exact_minimum(r, c, costs)
                    assert expected == space['expected_minima'][ordinal]
                    case(f'{space["name"]}-{ordinal}', r, c, costs, expected, 'finite_space')
            for c in range(1, 33):
                for r in range(1, c+1):
                    ro = [13*i-200 for i in range(r)]
                    co = [(17*j) % 37-18 for j in range(c)]
                    costs = [a+b for a in ro for b in co]
                    case(f'all-shapes-{r}x{c}', r, c, costs,
                         sum(ro)+sum(sorted(co)[:r]), 'all_shapes')
            rng = random.Random(20261103)
            for k in range(96):
                c = 32 if k % 3 == 0 else rng.randint(1, 32)
                r = c if k % 4 == 0 else rng.randint(1, c)
                costs = [rng.choice([MIN64, MAX64, -1, 0, 1, rng.randint(MIN64, MAX64)])
                         for _ in range(r*c)]
                expected = exact_minimum(r, c, costs) if c <= 6 else None
                case(f'seed-20261103-{k}', r, c, costs, expected, 'seeded')
            for k, (r, c) in enumerate([(1, 32), (2, 3), (6, 8), (16, 32), (32, 32)]):
                costs = [rng.randint(-10000, 10000) for _ in range(r*c)]
                base, original = case(f'metamorphic-{k}-base', r, c, costs, group='metamorphic')
                # Repeat checks deterministic output, without claiming a lexicographic optimum.
                assert execute('solve', solve_input(r, c, costs)).stdout == original
                offsets = [rng.randint(-500, 500) for _ in range(r)]
                case(f'metamorphic-{k}-row-offset', r, c,
                     [costs[i*c+j]+offsets[i] for i in range(r) for j in range(c)],
                     base['total']+sum(offsets), 'metamorphic')
                case(f'metamorphic-{k}-uniform-column-offset', r, c,
                     [x+71 for x in costs], base['total']+71*r, 'metamorphic')
                rp, cp = list(range(r)), list(range(c))
                rng.shuffle(rp)
                rng.shuffle(cp)
                case(f'metamorphic-{k}-row-column-permutation', r, c,
                     [costs[rp[i]*c+cp[j]] for i in range(r) for j in range(c)],
                     base['total'], 'metamorphic')
        invalid_solve = [
            ('empty', b'', 2), ('zero', b'0 1', 2), ('rows-above-columns', b'2 1 0 0', 2),
            ('over-cap', b'1 33', 2), ('negative-dimension', b'-1 1 0', 2),
            ('plus-dimension', b'+1 1 0', 2), ('fraction', b'1 1 1.0', 2),
            ('exponent', b'1 1 1e0', 2), ('cost-plus', b'1 1 +1', 2),
            ('cost-above-max', f'1 1 {MAX64+1}'.encode(), 2),
            ('cost-below-min', f'1 1 {MIN64-1}'.encode(), 2),
            ('long-magnitude', b'1 1 '+b'9'*10000, 2),
            ('missing-cost', b'2 2 1 2 3', 2), ('extra-cost', b'1 1 0 1', 2),
            ('bare-minus', b'1 1 -', 2), ('nul', b'1 1 0\0', 2),
            ('non-ascii-space', b'1 1 0\xc2\xa0', 2),
            ('escape', b'1 1 0\x1b', 2), ('extra-after-space', b'1 1 0 \nx', 2),
            ('oversized-trailing', b'1 1 0'+b' '*(131073-len(HEADER)-5), 3),
            ('oversized-leading', b' '*131073, 3),
        ]
        for name, data, code in invalid_solve:
            if name not in ('empty', 'oversized-leading'):
                data = HEADER + data
            reject(name, 'solve', data, code)
        for name, data in [('exact-cap', HEADER+b'1 1 0'+b' '*(131072-len(HEADER)-5)),
                           ('whitespace', b'\t'+HEADER+b'\t1\r\n1\v\f-000\t\n')]:
            result = execute('solve', data)
            assert result.returncode == 0 and result.stderr == b''
            inspect_certificate(result.stdout, 1, 1, [0], 0)
            records.append(dict(name=name, actual=result.returncode, bytes=len(data)))
        for name, data in [
            ('missing-solve-version', b'1 1 0'),
            ('wrong-solve-version', b'FEASSIGN 11 1 0'),
            ('noncanonical-solve-version', b'FEASSIGN 01\n1 1 0'),
            ('truncated-solve-header', b'FEASSIGN'),
        ]:
            reject(name, 'solve', data, 2)
        mutations = [
            ('positive-v-only', envelope(1, 2, [5, 3], [0], [3], [2, 0], 5), 4),
            ('unused-v-only', envelope(1, 2, [5, 3], [0], [5], [0, -2], 5), 4),
            ('infeasible', envelope(1, 2, [5, 3], [0], [5], [0]*2, 5), 4),
            ('not-tight', envelope(1, 1, [0], [0], [-1], [0], 0), 4),
            ('column-index', envelope(1, 1, [0], [255], [0], [0], 0), 4),
            ('duplicate', envelope(2, 2, [0]*4, [0, 0], [0, 0], [0, 0], 0), 4),
            ('wrong-total', envelope(1, 1, [0], [0], [0], [0], 1), 4),
            ('hostile-i128-sum', envelope(1, 1, [0], [0], [MIN128], [MIN128], 0), 4),
            ('u-above-i128', envelope(1, 1, [0], [0], [MAX128+1], [0], 0), 2),
            ('v-below-i128', envelope(1, 1, [0], [0], [0], [MIN128-1], 0), 2),
            ('total-above-i128', envelope(1, 1, [0], [0], [0], [0], MAX128+1), 2),
            ('wrong-version', sample.replace(b'FEASSIGN 1', b'FEASSIGN 2'), 2),
            ('extra-envelope-token', sample+b'extra', 2),
            ('truncated-envelope', sample.rsplit(b'TOTAL', 1)[0], 2),
        ]
        for name, data, code in mutations:
            reject(name, 'verify', data, code)
        for mode in ['', 'solv', 'solve-extra', 'VERIFY']:
            reject('usage-'+mode, mode, b'', 64)
        for argv in [[], ['solve', 'extra']]:
            result = subprocess.run([str(executable)]+argv, input=b'', capture_output=True, timeout=10)
            assert result.returncode == 64 and result.stdout == b''
            records.append(dict(name='argument-count', arguments=argv, actual=result.returncode))
        help_result = execute('--help', b'')
        assert help_result.returncode == 0 and help_result.stderr == b'' and b'\0' not in help_result.stdout
        # These are real Linux stream failures, not substitute mock bridge results.
        with open('/dev/full', 'wb', buffering=0) as full:
            result = subprocess.run([str(executable), 'solve'], input=HEADER+b'1 1 0',
                                    stdout=full, stderr=subprocess.PIPE, timeout=10)
        assert result.returncode == 5, ('flush failure', result.returncode)
        records.append(dict(name='dev-full-buffered-final-flush', actual=result.returncode))
        counts['io'] += 1
        read_fd, write_fd = os.pipe()
        os.close(read_fd)
        with os.fdopen(write_fd, 'wb', buffering=0) as broken:
            result = subprocess.run([str(executable), 'solve'], input=HEADER+b'1 1 0',
                                    stdout=broken, stderr=subprocess.PIPE, timeout=10)
        assert result.returncode == 5, ('broken pipe must not terminate by SIGPIPE', result.returncode)
        records.append(dict(name='closed-reader-pipe', actual=result.returncode))
        counts['io'] += 1
        directory_fd = os.open(str(evidence), os.O_RDONLY | os.O_DIRECTORY)
        try:
            result = subprocess.run([str(executable), 'solve'], stdin=directory_fd,
                                    capture_output=True, timeout=10)
        finally:
            os.close(directory_fd)
        assert result.returncode == 5 and result.stdout == b''
        records.append(dict(name='directory-read-error-not-eof', actual=result.returncode,
                            stderr=result.stderr.decode('ascii')))
        counts['io'] += 1
        success = True
    except Exception:
        (evidence / 'failure.json').write_text(json.dumps(current, indent=2)+'\n', encoding='utf-8')
        success = False
        raise
    finally:
        certificates.close()
        report = dict(started_utc=started, ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                      success=success, smoke=args.smoke, counts=counts, records=records,
                      executable=str(executable), executable_sha256=sha(executable.read_bytes()),
                      inspector_sha256=sha(Path(__file__).read_bytes()),
                      certificates_sha256=sha((evidence / 'certificates.jsonl').read_bytes()),
                      scope='Native CLI actual exported fields; Python arbitrary integers; no host Hungarian/JV',
                      limits=['Not exhaustive over full i64 or all 32x32 matrices',
                              'Not an EVM board/ABI/gas test', 'Not a formal proof or audit'])
        (evidence / 'results.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(dict(success=success, counts=counts, evidence=str(evidence))), flush=True)


if __name__ == '__main__':
    main()
