"""Check the five intentional external-API compile failures with pinned Fe."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fe', default='fe', help='Fe26.5.1 executable')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = subprocess.check_output([args.fe, '--version'], text=True, timeout=15).strip()
    if '26.5.1' not in version or '149c758' not in version:
        raise RuntimeError('Expected pinned Fe26.5.1 commit149c758; observed: ' + version)
    cases = [
        ('private_problem', ['`rows` is not visible', '`columns` is not visible', '`packed_costs` is not visible'], 3),
        ('private_certificate', ['`rows` is not visible', '`columns` is not visible',
                                 '`selected` is not visible', '`row_potentials` is not visible',
                                 '`column_potentials` is not visible'], 5),
        ('use_after_move', ['cannot use a value after it was moved'], 1),
        ('private_builder', ['`problem` is not visible', '`count` is not visible'], 2),
        ('builder_after_finish', ['cannot use a value after it was moved'], 1),
    ]
    records = []
    for name, expected, errors in cases:
        fixture = root / 'tests/compile_fail' / name
        command = [args.fe, '--color', 'never', 'check', str(fixture)]
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=60)
        output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        ok = (result.returncode == 1 and output.count('error[') == errors
              and all(part in output for part in expected))
        records.append(dict(case=name, expected_rejection_observed=ok,
                            exit_code=result.returncode, diagnostics=output,
                            fixture_sha256=hashlib.sha256((fixture / 'src/lib.fe').read_bytes()).hexdigest()))
    # This output is intentionally suitable for a CI log or a saved JSON record.
    print(json.dumps(dict(compiler_required='26.5.1', compiler_observed=version, checks=records,
                          all_expectations_met=all(row['expected_rejection_observed'] for row in records)), indent=2))
    return 0 if all(row['expected_rejection_observed'] for row in records) else 1


if __name__ == '__main__':
    sys.exit(main())
