# FeAssign: judge handoff

**Solve once; check the optimality certificate independently.** FeAssign assigns
each row of an integer cost matrix to a distinct column at minimum total cost.
The Fe solver exports an assignment and dual potentials. A separate Fe verifier
checks their mathematical conditions without running the optimizer.

## First look: native Fe, no Foundry

Requirements: Linux x86-64, glibc >= 2.39 (Ubuntu 24.04 is a tested example),
Python >= 3.10 and `cc`. On Windows, use an existing compatible WSL distribution.
From the repository root:

```sh
python3 tools/review.py native --download
```

`--download` permits official GitHub release downloads. The helper checks the
exact SHA-256 before execution, keeps tools in `.cache/reviewer-tools`, makes no
system changes and creates a fresh `target/review-*` output on each invocation.
With a preinstalled pinned compiler, use `--fe /path/to/fe` and omit `--download`.

Expected final summary:

```text
VALID 3; duplicate rejected; exact wide witness accepted; converted witness rejected.
```

The output directory contains the real native binary, `solution.cert`, command
stdout/stderr, directed checks and `review.json`. Inspect the certificate or run
that binary's `verify` command with a certificate on stdin. This first look is
a subset, not a claim that the complete suite ran.

The small matrix is `[[1,2,9],[1,100,3]]`. Selection `[1,0]` costs 3;
row-order greedy costs 4. The duplicate-column negative must exit 4.
The wider example preserves a one-unit distinction above 2^53 in the original
integer matrix; it does not claim that every floating-point optimizer is wrong.

## Complete review: all 11 stages

```sh
python3 tools/review.py full --download --out target/judge-full-01
```

Choose an unused `--out` path; omitting it chooses a fresh name automatically.
This path also verifies and uses the pinned Anvil/cast assets. It invokes the
existing full reproduction unchanged: both Fe backends, intended compiler
rejections, native certificate/I/O checks and actual local EVM transactions.
`target/judge-full-01/full-run/reproduce.json` records the scope, source hashes,
commands and outcomes. Failure logs remain available; earlier runs are not deleted.
For exact dependencies, individual commands and limits, see [REPRODUCE.md](docs/REPRODUCE.md).

To open the optional UI from that completed full run:

```sh
python3 workbench/server.py --run-dir target/judge-full-01/full-run --port 8765
```

Keep that terminal running and open the printed loopback URL. If the port is
busy, use `--port 0` and open its printed URL. [Proof Studio](workbench/README.md)
explains draft preservation, the local service and review notes.

## Claims, evidence and boundaries

| Claim | Inspect | Reproduce |
|---|---|---|
| Fe performs optimization and separately verifies the certificate | [core](ingots/assignment/src/lib.fe), [reasoning](docs/PROOF.md) | native first look; full backend tests |
| Every supported cost is a full-range i64; proof arithmetic widens before combining | [numeric/API boundary](docs/CORE-API.md), [CLI](docs/CLI.md) | directed limits and full certificate campaign |
| EVM verification binds the original matrix and writes only after all checks | [Board](ingots/board/src/lib.fe), [ABI and limits](docs/BOARD.md) | full receipt/getter/state campaigns |
| Witnesses can come from another optimizer | [external examples and caveats](docs/INTEROPERABILITY.md) | native first look; optional supplied-witness Board replay |
| The contribution and reused work are disclosed | [provenance](docs/PROVENANCE.md), [notices](THIRD-PARTY-NOTICES.md) | source review |

Fe is central: the owned model, Hungarian optimizer, verifier, native parser and
formatter are Fe. The scalar C bridge handles byte I/O; Python builds and tests.
Fe's private owned values, shared references, wide checked integers and explicit
capabilities express the proof and storage boundaries. [CONTEST.md](CONTEST.md)
collects the pitch, submission history and disclosures.

The complete model is `1 <= rows <= columns <= 32`, every edge allowed,
unit-capacity columns and minimum-sum cost. It does not express forbidden edges,
general scheduling, fairness, truthful inputs or work delivery. The Board holds
no funds. Source reasoning and tests are not a formal proof, security audit,
user-demand study or guarantee of rank. No video, wallet or mainnet is needed.
