# FeAssign contest entry

FeAssign is an exact minimum-cost assignment library in Fe that exports a
checkable optimality certificate for both native and EVM consumers.

## Fe-specific contribution

The pure Fe ingot implements the owned bounded model, Hungarian optimizer and
separately structured rectangular dual-certificate verifier. Native Fe performs
parsing, solving, verification and formatting; a small C bridge supplies scalar
byte I/O. The immutable EVM reference board checks the same certificate against
a committed matrix without rerunning search. Private owned values, shared
`ref` reads, widening before checked arithmetic and explicit `uses` capabilities
make the mathematical and storage boundaries visible. See [the API](docs/CORE-API.md)
and [the five-minute explanation](docs/PITCH.md).

## Reproduce the entry

Use Linux x86-64, Python 3.10+, a C compiler and the exact Fe 26.5.1 and
Foundry Anvil/cast 1.8.7 assets pinned in [toolchain.json](toolchain.json).
[Setup and complete checks](docs/REPRODUCE.md) explain asset hashes, dependencies,
ordinary Osaka limits and fresh output directories. After setup, run:

```sh
python3 tools/demo.py --fe "/absolute/path/to/fe" --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --out target/demo-01
python3 tools/reproduce.py --fe "/absolute/path/to/fe" --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --out target/repro-01
```

The first command demonstrates optimal cost 3 versus row-order greedy cost 4,
then rejects an invalid proof, another matrix and a repeat. The second runs
all 11 stages and records actual source hashes, commands, outputs and receipts.
`target/demo-01` and `target/repro-01` must not already exist. Optional
[Proof Studio](workbench/README.md) uses these actual Fe results for its local UI.

## Scope and disclosure

The complete model is `1 <= rows <= columns <= 32`, all pairs allowed,
finite full-range `i64` costs, public `i128` certificates and widened `i256`
working arithmetic. The proof concerns that matrix, not truthful costs,
resource identity, delivered work, fairness or a general scheduling model.
The board holds no funds. Tests and source reasoning are not a machine-checked
proof, security audit, demand study or global performance/rank claim.

The UI's manual motion control and recorded desktop/mobile tasks have bounded
evidence. Actual OS reduced-motion integration and screen-reader speech remain
unverified. Owner approval is qualitative feedback, not a controlled first-use
benchmark. The owner reported review complete with no issues on November 8, 2026.

Design, research and generic tool experiments preceded the contest window;
product code and dedicated tests were authored after its November 3 opening.
Codex assisted research, design, implementation, tests, documentation and checks.
Hungarian and duality are classical. Third-party optimizers were researched or
used in separate disclosed comparison experiments; they do not implement the
product solver. [Provenance](docs/PROVENANCE.md), [attribution](THIRD-PARTY-NOTICES.md)
and the [MIT license](LICENSE) give the scope and reuse details.

This local entry still requires a public GitHub repository at the exact submitted
commit and the owner's final submission. No publication, submission or contest
acceptance is claimed. A later scheduled freeze is distinct from this prepared
entry; if code changes before the deadline, reproduce and submit the intended commit.
