# FeAssign

An exact minimum-total-cost assignment library in Fe, with an independently
structured verifier for an optimality certificate.

The complete target model assigns every task to a different resource for
`1 <= rows <= columns <= 32`, with all pairs allowed and full-range finite
`i64` costs. Extra resources can remain unused. The intended consumers are a
Linux native solve/verify CLI and an immutable EVM reference board committed
to the same problem.

## Development status

Implementation began after November 3, 2026 at 00:00 UTC. An initial bounded
`Problem` and shape-valid `Certificate`, checked construction and scalar
reference access and a separate mathematical verifier now exist. Model/API and
directed verifier checks have run on native and EVM;
see [the bounded API](docs/CORE-API.md). The initial full32 gate's scope and
the preserved EVM `-O 0` failure are in
[the representation gate](docs/REPRESENTATION-GATE.md).
See [certificate verification](docs/VERIFIER.md) for the contract, directed
evidence and repair of an EVM aggregate-stack failure. The optimizer, CLI and
board are not implemented yet.
Independent solver-oracle and deployed-board evidence remains pending.

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

With the pinned `fe` on PATH, from this repository root:

```sh
fe test . --ingot assignment --backend sonatina -O 1
fe test . --ingot assignment --backend native -O 0
```

The native command requires the supported Linux environment and its system
linker. The assignment ingot runs model checks; the api_tests ingot runs the
external API/verifier cases. The planned optimizer, CLI and board suite remains
pending. The initial EVM `-O 0` failure is retained; no all-profile claim is made.

Read [the provenance record](docs/PROVENANCE.md) for pre-window design,
preparatory experiments and AI assistance. Hungarian algorithms and duality
are classical; no new mathematical algorithm or global-first claim is made.

Original project source is MIT licensed. This repository is local; no public
repository, submission or contest acceptance is claimed.
