# FeAssign

An exact minimum-total-cost assignment library in Fe, with an independently
structured verifier for an optimality certificate.

The complete target model assigns every task to a different resource for
`1 <= rows <= columns <= 32`, with all pairs allowed and full-range finite
`i64` costs. Extra resources can remain unused. The intended consumers are a
Linux native solve/verify CLI and an immutable EVM reference board committed
to the same problem.

## Development status

This is the local contest baseline created after November 3, 2026 at 00:00 UTC.
The optimizer, verifier, CLI and board are not implemented at this baseline.
No product correctness, performance or deployment result is claimed. The first
implementation gate measures the actual full-size representation on native
and EVM before the algorithm is built.

The intended pure core owns the bounded model, Hungarian optimizer and separate
dual-certificate verifier. It has no I/O, hashing, storage or network effects.
Python may independently enumerate small assignments for evidence; it will not
implement the product optimizer. A small C bridge may provide scalar native
I/O status only.

This model does not express forbidden edges, multiple-task capacity, routing,
minimum makespan, fairness, truthful costs, resource identity or work delivery.
The board is a reference consumer of the mathematical result, with no funds.

## Toolchain and provenance

Exact asset and source pins are in [toolchain.json](toolchain.json).
Initial native support targets Linux x86_64, including WSL on a Windows host.
Reproducible product commands and observed results will be documented as each
actual build gate is executed. Environment/upstream tests are not product tests.

Read [the provenance record](docs/PROVENANCE.md) for pre-window design,
preparatory experiments and AI assistance. Hungarian algorithms and duality
are classical; no new mathematical algorithm or global-first claim is made.

Original project source is MIT licensed. This repository is local; no public
repository, submission or contest acceptance is claimed.
