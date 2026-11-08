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

Start with the [judge handoff](JUDGING.md). Use Linux x86-64 with glibc 2.39+,
Python 3.10+ and a C compiler named `cc`. These commands opt into official,
SHA-256-pinned tool downloads into a local cache:

```sh
python3 tools/review.py native --download
python3 tools/review.py full --download
```

The first needs only Fe: it demonstrates optimal cost 3, rejects a duplicate
assignment and checks retained external witnesses. The second also uses pinned
Foundry 1.8.7 and runs all 11 stages, including the EVM demo's success,
invalid-proof, different-matrix and repeat receipts. Both preserve fresh output
directories. Explicit tool paths work offline without `--download`.
[Setup and complete checks](docs/REPRODUCE.md) explain the exact dependencies and
ordinary Osaka limits. Optional [Proof Studio](workbench/README.md) uses those
actual Fe results for its local UI.

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

The source is public at [aierosite/feassign](https://github.com/aierosite/feassign).
The previous entry at `7665af113dc6bb1b64037fd2e366729e83b91fef` was received
on November 8, 2026 and passed the organizer's registration/deadline checks.
That email did not decide technical eligibility or a prize. The latest valid
submission's full commit SHA identifies the replacement version for judging.
The scheduled final freeze remains distinct from the earlier owner review.
