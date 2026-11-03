"""Standard ABI bytes for the published FeAssign protocol; no solver here."""
import subprocess

DOMAIN = int.from_bytes(b'FEASSIGN_PROBLEM'.ljust(32, b'\0'), 'big')
VERSION, OBJECTIVE = 1, 1


def word(value):
    assert -(2**255) <= value < 2**256
    return (value % (2**256)).to_bytes(32, 'big')


def narrow(value, bits, signed):
    assert -(2**(bits-1)) <= value < 2**(bits-1) if signed else 0 <= value < 2**bits
    return word(value)


def array(values, bits, signed):
    return word(len(values)) + b''.join(narrow(v, bits, signed) for v in values)


def problem_payload(rows, columns, costs):
    assert 1 <= rows <= columns <= 32 and len(costs) == rows*columns
    return b''.join(map(word, [DOMAIN, VERSION, OBJECTIVE, rows, columns, 6*32])) + array(costs, 64, True)


def keccak(data, cast):
    # Feed hex through stdin to avoid platform command-line length limits.
    result = subprocess.run([str(cast), 'keccak'], input=('0x'+data.hex()).encode('ascii'),
                            capture_output=True, check=True, timeout=30)
    digest = bytes.fromhex(result.stdout.decode('ascii').strip().removeprefix('0x'))
    assert len(digest) == 32
    return digest


def selector(signature, cast):
    return keccak(signature.encode('ascii'), cast)[:4]


def submit_payload(costs, selected, u, v):
    tails = [array(costs, 64, True), array(selected, 8, False),
             array(u, 128, True), array(v, 128, True)]
    offsets, cursor = [], 4*32
    for tail in tails:
        offsets.append(word(cursor))
        cursor += len(tail)
    return b''.join(offsets+tails)


def signed_word(data):
    assert len(data) == 32
    return int.from_bytes(data, 'big', signed=True)
