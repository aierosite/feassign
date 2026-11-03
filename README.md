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
reference access, an actual Hungarian optimizer and a separate mathematical
verifier now exist. Model/API, directed solver/verifier and independent expected-
cost checks have run on native and EVM;
see [the bounded API](docs/CORE-API.md). The initial full32 gate's scope and
the preserved EVM `-O 0` failure are in
[the representation gate](docs/REPRESENTATION-GATE.md).
See [certificate verification](docs/VERIFIER.md) for the contract, directed
evidence and repair of an EVM aggregate-stack failure. See
[the optimizer checkpoint](docs/SOLVER.md) for the 2,780 cost-reference cases and
their limits. The Linux [solve/verify CLI](docs/CLI.md) now exports real Fe
certificates. Python independently checked all primal/dual conditions for 2,906
exported results, with exact small-instance and controlled metamorphic checks;
see [native and independent evidence](docs/NATIVE-CHECKPOINT.md).
The [immutable EVM board](docs/BOARD.md) now binds a canonical semantic problem
digest and records one verified result. Actual Osaka transactions passed for
three full32 cases with ordinary code/init/transaction limits, including i64
endpoints. Signed/dirty ABI, alternate wire encodings and failed-state controls
also ran. Its measured code-size failure and sequential-construction repair are
preserved. See [board evidence](docs/evidence/board.json) for current source
hashes and limits. The [portable local demo](docs/DEMO.md) now runs on Linux with
the normal result and three sensitive failures. [Stabilization](docs/STABILIZATION.md)
and [certificate reasoning](docs/PROOF.md) state the boundaries. A fresh-source
complete-package rehearsal and actual human review/freeze remain separate
requirements; the full build goal is active.

The pure core owns the bounded model, Hungarian optimizer and separate
dual-certificate verifier. It has no I/O, hashing, storage or network effects.
Python independently enumerates small assignments for evidence; it does not
implement the product optimizer. A small C bridge supplies scalar native
I/O status only. Parsing, formatting and all assignment mathematics stay in Fe.

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
fe test . --ingot assignment --backend native -O 1
fe test . --ingot api_tests --backend sonatina -O 1
fe test . --ingot api_tests --backend native -O 1
```

The native command requires the supported Linux environment and its system
linker. The assignment ingot runs model checks; the api_tests ingot runs the
external API/solver/verifier and cost-oracle cases. The initial EVM `-O 0`
failure is retained; no all-profile claim is made.

Build and check the native consumer on Linux with the pinned compiler:

```sh
python3 tools/build-native.py --fe /absolute/path/to/fe-26.5.1
printf 'FEASSIGN 1\n2 3\n4 1 8\n2 6 3\n' | target/native/feassign solve > target/example.cert
target/native/feassign verify < target/example.cert
python3 tools/check-native.py --executable target/native/feassign --evidence target/check-native-01
python3 tools/check-native-io.py --executable target/native/feassign --evidence target/check-io-01
```

The EVM consumer is a separate ingot:

```sh
fe test . --ingot board --backend sonatina -O 1
fe build . --ingot board --backend sonatina -O 1 --emit bytecode,runtime-bytecode,abi,metadata --out-dir target/board
```

The contract uses no Call/fund/admin capability. Run the full local demo or
complete reproduction with pinned Linux tools:

```sh
python3 tools/demo.py --fe /absolute/path/to/fe --anvil /absolute/path/to/anvil --cast /absolute/path/to/cast --out target/demo-01
python3 tools/reproduce.py --fe /absolute/path/to/fe --anvil /absolute/path/to/anvil --cast /absolute/path/to/cast --out target/repro-01
```

See [reproduction](docs/REPRODUCE.md) for fresh-source/output/cache scope and
standalone full32/ABI checks. Local records are not a remotely passed CI result
or published deployment. The human review and final freeze are still pending.

The checks require fresh evidence directories; use a new suffix for a new run.
`--smoke` on check-native runs directed/negative/I/O checks without the larger
corpus. Python's standard library, Linux x86-64, a system C compiler (`cc`) and
the pinned Fe release asset are required. The signal-interruption test compiles
a test-only preload handler; it does not replace the actual I/O implementation.
No external service, host optimizer or API key is used.

Read [the provenance record](docs/PROVENANCE.md) for pre-window design,
preparatory experiments and AI assistance. Hungarian algorithms and duality
are classical; no new mathematical algorithm or global-first claim is made.

Original project source is MIT licensed. This repository is local; no public
repository, submission or contest acceptance is claimed.

[Third-party notices](THIRD-PARTY-NOTICES.md) retain tool/library attribution;
the [five-minute pitch](docs/PITCH.md) explains the result and its limits.
