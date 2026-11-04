# Hungarian optimizer and cost-oracle checkpoint

This checkpoint predates the streaming-construction repair and deployed board.
Current construction/API and repeated regression evidence are in [BOARD.md](BOARD.md).
The Hungarian and mathematical verifier algorithms are unchanged by that repair.

`solve(ref problem) -> Result<SolveError, Certificate>` runs the actual Hungarian
optimizer in Fe. It borrows the immutable problem and returns an owned
certificate. It calls the separately structured verifier before returning
success. The verifier never calls the optimizer.

The complete model remains `1 <= rows <= columns <= 32`, every pair allowed,
full finite i64 costs. There is no host optimizer, local-swap approximation,
square-only mode, arbitrary gauge normalization or smaller numeric range.

## Algorithm

Every row potential starts at that row's minimum; column potentials start at
zero. This makes every pair feasible even with negative costs. A tight partial
matching grows by one row at each phase.

Current code uses six local 33-slot arrays for row/column potentials, owners,
predecessors, slacks and reached flags. The initial checkpoint also stored
initialized-slack flags. Current code derives initialization from the first
complete scan at dummy0; every real slack is assigned before an update. Slot0
is a separate dummy; public certificate arrays still have32 zero-based slots.
There is no arithmetic-infinity sentinel; see [the invariant argument](PROOF.md).

Each search scans unreached columns, updates their best slack/predecessor and
chooses a minimum nonnegative delta. It increases reached-row potentials and
decreases reached-column potentials, preserving feasibility and tight matching.
A zero delta still reaches a new column. A free column ends search before it
joins the decreasing-potential set, so final unused columns retain zero v.
Predecessors then rotate the augmenting path.

The search/augmentation guards detect an internal invariant failure; they do
not declare a valid complete instance unassignable. Every such instance has an
assignment. With row-minimum initialization, total delta is bounded by
2*rows*2^63, so the resulting potentials fit i128. Working arithmetic is i256;
narrowing is checked. The cost comes from verifier recomputation, not the usual
unadjusted negative dummy potential. Intended algorithmic bounds are O(r²c)
work and O(r+c) workspace beyond the problem, not a performance/gas benchmark.
Tie handling is deterministic for the pinned implementation without promising
lexicographically minimal assignments or a unique certificate.

`SolveError::Shape` rejects malformed metadata defensively. `InternalInvariant`
is an implementation/compilation failure to investigate, not an unsupported
input escape. No such failure occurred in the successful directed/cost-oracle
campaign. Its exceptional branches have not been presented as normally
reachable input behavior or fabricated coverage; later fault/adversarial work
remains explicit.

## Observed directed cases

Ten external-consumer solver tests cover singleton/extra-resource endpoints,
an off-diagonal optimum, positive delta with a zero unused column potential,
a three-cycle that beats every two-swap from identity, a full 32×32 long augmenting
chain, full 32×32 zero-delta ties/repeated output, both all-i64-endpoint full 32×32 sums
and a reduced cost of 2^64-1. Every output is checked by the verifier again in the
consumer. An internal malformed-shape test covers the defensive Shape error.

## Independent cost comparisons

`python3 tools/generate-oracle.py` deterministically generates expected values
and `ingots/api_tests/src/oracle.fe`. It does not implement Hungarian/JV.

The finite spaces contain 2,252 entries: all ternary 1×1 through 1×4, ternary 2×2
and 2×3, binary 3×3, and i64-endpoint/zero 2×2 and 2×3 matrices. Python enumerates
all distinct-column injections using arbitrary-precision integers: 12,570
assignments in total. These expected minima are compared to actual Fe solve
and verify results in runtime loops on native and EVM. Spaces overlap in two
all-zero matrices; these are corpus entries, not 2,252 unique logical matrices.

A separate family covers every 528 valid (r,c) shape with
`C[i,j]=(13*i-200)+((17*j)%37-18)`. Its independent closed-form optimum is the
sum of all row offsets plus the r smallest column offsets. This is one known-
optimum matrix per shape, not exhaustive enumeration of general 32-sized data.
Together there are 2,780 corpus entries per backend, with 2,778 unique logical
matrices. The complete suite at this checkpoint had 52 Fe test functions on each
named backend, plus three intended external compiler rejections.

Run with the pinned compiler from the repository root:

```sh
python3 tools/generate-oracle.py
fe test . --ingot assignment --backend native -O 1
fe test . --ingot api_tests --backend native -O 1
fe test . --ingot assignment --backend sonatina -O 1
fe test . --ingot api_tests --backend sonatina -O 1
python3 tools/check-api-boundaries.py --fe fe
```

A filtered submodule-only EVM run with optional `--emit ir,rmir` failed its IR
export with "no root objects". The same oracle tests and full EVM suite passed
without that optional debug export. The failure is preserved; no input or
mathematical case was removed. Native emitted IR and prior directed EVM IR
remain available for actual-code observations. Debug objects are never the
normal build/link route.

The dated evidence is [solver.json](evidence/solver.json), with the full corpus
definition in [oracle-cases.json](evidence/oracle-cases.json).

## Remaining acceptance

At this solver checkpoint FA04 was partial: independent inspection of actual
selected/u/v still awaited an export adapter. The subsequent
[native checkpoint](NATIVE-CHECKPOINT.md) now records that inspection, guarded
seeded/metamorphic cases and implemented CLI/I/O acceptance. The earlier JSON
remains historical evidence. Subsequent board/full32 transaction and
demo/reproducibility evidence is in [BOARD.md](BOARD.md) and
[REPRODUCE.md](REPRODUCE.md). Actual human review and freeze remain pending.
These tests are not a formal proof or universal profile guarantee; the persistent
build goal remains active.
