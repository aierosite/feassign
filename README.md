# FeAssign

An exact minimum-total-cost assignment library in Fe, with an independently
structured verifier for an optimality certificate.

The complete model assigns every task to a different resource for
`1 <= rows <= columns <= 32`, with all pairs allowed and full-range finite
`i64` costs. Extra resources can remain unused. The two consumers are a
Linux native solve/verify CLI and an immutable EVM reference board committed
to the same problem.

## What the example demonstrates

Both jobs prefer the same resource, which can accept only one of them. Choosing
each job's cheapest available resource in row order costs 4; Fe finds an
assignment costing 3 and supplies a certificate attaining the dual lower bound 3.
The reference board checks that certificate against the committed input without
rerunning the optimizer. [Run the example](docs/DEMO.md) after tool setup for the
normal result and three sensitive rejected submissions.

## Implementation and evidence

Product implementation began after November 3, 2026 at 00:00 UTC. The bounded
model, actual Hungarian optimizer, separate verifier, native CLI and immutable
board are implemented. Prior checkpoint evidence includes 2,906 actual exported
certificates independently inspected in Python, native/EVM functions, I/O
failures and three full32 Osaka transaction cases under ordinary limits.
The last complete fresh-source/output/cache reproduction is commit c46b24a.
The later board-only static-tail revision passed targeted board/protocol/demo
checks and reproduced its bytecode from a fresh archive; core/CLI code is unchanged.
[BOARD.md](docs/BOARD.md) and the candidate manifest distinguish those scopes.
Evidence is specific to its recorded source and compiler, not an exhaustive
full-domain proof or a remotely executed CI result. The main example was
revised to expose resource contention; the reproduction command below records
the actual result for the source being run.

Start with [the bounded API](docs/CORE-API.md), [the CLI](docs/CLI.md) and
[the board](docs/BOARD.md). [Stabilization](docs/STABILIZATION.md) and
[certificate reasoning](docs/PROOF.md) explain the current boundaries.
[Native evidence](docs/NATIVE-CHECKPOINT.md), [the optimizer checkpoint](docs/SOLVER.md),
[the verifier record](docs/VERIFIER.md) and
[the representation gate](docs/REPRESENTATION-GATE.md) preserve earlier
checkpoint scopes, compiler/profile failures and their repairs. Those dated
records are historical evidence; the run's source hashes establish its scope.
Actual human review and final freeze remain pending.

The pure core owns the bounded model, Hungarian optimizer and separate
dual-certificate verifier. It has no I/O, hashing, storage or network effects.
Python independently enumerates small assignments for evidence; it does not
implement the product optimizer. A small C bridge provides byte I/O and stream
status through scalar calls. Parsing, formatting and assignment mathematics stay in Fe.

This model does not express forbidden edges, multiple-task capacity, routing,
minimum makespan, fairness, truthful costs, resource identity or work delivery.
The board is a reference consumer of the mathematical result, with no funds.

## Toolchain and provenance

Exact asset and source pins are in [toolchain.json](toolchain.json).
Initial native support targets Linux x86_64, including WSL on a Windows host.
Product commands are below, with a complete fresh-source path in
[REPRODUCE.md](docs/REPRODUCE.md). Environment/upstream tests are not product tests.

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
printf 'FEASSIGN 1\n2 3\n1 2 9\n1 100 3\n' | target/native/feassign solve > target/example.cert
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

The build and checks require new output/evidence directories for each run.
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
