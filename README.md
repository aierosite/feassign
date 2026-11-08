# FeAssign

An exact minimum-total-cost assignment library in Fe, with an independently
structured verifier for an optimality certificate.

[Contest entry overview](CONTEST.md) collects the pitch, Fe-specific contribution,
reproducible demo, disclosure and submission boundaries.

**Judges: start with [JUDGING.md](JUDGING.md).** It separates a native first look
from the complete EVM/native check and maps each claim to its evidence.

## Quick review

Use Linux x86-64 with glibc 2.39 or later (Ubuntu 24.04 works), Python 3.10+
and a C compiler named `cc`. On Windows, run inside your WSL Linux distribution.
From this checkout:

```sh
python3 tools/review.py native --download
```

This explicitly permits a download of the official, SHA-256-pinned Fe release
into this checkout's `.cache/`; it installs no system packages and needs no
Foundry, wallet or API key. It builds the actual Fe CLI, solves the example,
prints `VALID 3`, rejects a duplicated assignment, checks the retained exact
wide-integer witness and runs the existing directed native checks. Every run
keeps its own output directory and `review.json`.

For an offline run, supply `--fe /absolute/path/to/fe` or reuse the verified
cache and omit `--download`. The helper verifies tool bytes before execution.
For all 11 native/EVM stages, including actual local transaction receipts:

```sh
python3 tools/review.py full --download
```

Only the full path also obtains pinned Anvil/cast. See [setup and troubleshooting](docs/REPRODUCE.md)
and the optional [Proof Studio](workbench/README.md). The native first look is
a subset of the complete checks; neither workflow contacts a real-fund network.

[The five-minute pitch](docs/PITCH.md) explains the result and its limits.
[Proof Studio](workbench/README.md) opens the same solver and verifier in a
local browser, with an animated assignment map and an interactive proof desk.

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

The verifier can also check a certificate produced outside FeAssign. The
[external-optimizer example](docs/INTEROPERABILITY.md) includes a HiGHS-derived
certificate and a rejected candidate whose floating-point input lost a unit
difference. Both use the existing format and the original integer matrix.

## Implementation and evidence

Product implementation began after November 3, 2026 at 00:00 UTC. The bounded
model, actual Hungarian optimizer, separate verifier, native CLI and immutable
board are implemented. Retained evidence includes 2,906 exported certificates
independently inspected in Python, native/EVM functions, I/O failures and full32
Osaka transactions under ordinary limits. The retained full-source run at
63a90377759934cd3f8834f3e890027bb643b538 used Python 3.10.12 and passed
all 11 stages: 110 Fe test executions, 2,906 native certificate roundtrips,
43 directed CLI negatives, 8 descriptor/I/O cases and 60 receipted local EVM
transactions in separate demo/full32/ABI campaigns. Thirty-four failed calls
preserved all 34 checked mutable slots; four failed creations retained empty
code readbacks. The source/run manifest distinguishes this dated result from
any subsequent fresh reproduction.
[BOARD.md](docs/BOARD.md) and the
candidate manifest distinguish current source from earlier checkpoint evidence.
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
The owner reported completing human review with no issues on November 8, 2026.
That qualitative approval predates the reviewer-startup improvements; it is not
a controlled first-use benchmark. The scheduled final freeze is a separate checkpoint.

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
python3 tools/build-native.py --fe "/absolute/path/to/fe-26.5.1"
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
python3 tools/demo.py --fe "/absolute/path/to/fe" --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --out target/demo-01
python3 tools/reproduce.py --fe "/absolute/path/to/fe" --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --out target/repro-01
```

See [reproduction](docs/REPRODUCE.md) for fresh-source/output/cache scope and
standalone full32/ABI checks. Local records are not a remotely passed CI result
or published deployment. See CONTEST.md for current disclosure and limitations.

The build and checks require new output/evidence directories for each run.
`--smoke` on check-native runs directed/negative/I/O checks without the larger
corpus. Python's standard library, Linux x86-64, a system C compiler (`cc`) and
the pinned Fe release asset are required. The signal-interruption test compiles
a test-only preload handler; it does not replace the actual I/O implementation.
No external service, host optimizer or API key is used.

Read [the provenance record](docs/PROVENANCE.md) for pre-window design,
preparatory experiments and AI assistance. Hungarian algorithms and duality
are classical; no new mathematical algorithm or global-first claim is made.

Original project source is MIT licensed. The public repository is
[aierosite/feassign](https://github.com/aierosite/feassign). The previous entry at
`7665af113dc6bb1b64037fd2e366729e83b91fef` received confirmation on November 8
that registration and deadline checks passed. Technical eligibility and judging
remain separate. The exact commit supplied in the latest valid contest form
identifies the version to judge; this README does not claim a judging result.

[Third-party notices](THIRD-PARTY-NOTICES.md) retain tool/library attribution.
