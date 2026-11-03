# Certificate verification

This records the initial FA02 checkpoint; its counts and profiles are historical.
The defining verification contract is unchanged. Current commands and check counts
are in [REPRODUCE.md](REPRODUCE.md); subsequent optimizer and protocol evidence is
in [SOLVER.md](SOLVER.md) and [BOARD.md](BOARD.md).

`verify(ref problem, ref certificate) -> Result<VerifyError, i128>` recomputes
the selected cost and verifies optimality for the complete finite assignment
model. It performs no optimization, I/O, hashing or storage operation.

The checks are explicit:

1. Valid bounded dimensions and the same row/column shape.
2. Every selected column is in range and selected columns are distinct.
3. Every column potential v is nonpositive.
4. For every pair, u[i]+v[j] is at most the actual cost[i,j].
5. Every selected edge is tight: u[i]+v[p[i]] equals its actual cost.
6. Every unused column has zero potential.

Every combined operation first widens costs/potentials to i256. At most 32
selected i64 costs are summed in i256 and then checked into i128. A narrowing
failure would violate the validated model bound and is an implementation
invariant failure, not an unsupported input. No objective supplied by a caller
is trusted or stored. Certificate uniqueness or solver-specific numeric bounds
are not required; a valid full-i128 cancellation is accepted.

For any other injection q, feasibility gives
`cost(q) >= sum(u) + sum(v selected by q)`. Because v is nonpositive, this is at
least `sum(u)+sum(all v)`. Tight selected edges and zero unused v make the
submitted assignment attain that same bound. This is the mathematical argument
for the model, not formal verification of the implementation. The optional
redundant dual-sum guard is not needed by this implementation; every defining
condition above is checked directly.

## Directed evidence

The shared verifier runs from the independent `api_tests` consumer. Sixteen
mathematical tests cover rectangular and square optima, two alternative optima,
a singleton, both full 32×32 all-i64-endpoint sums, full-i128 cancellation and hostile
i128 addition, every public error, and changed matrix values. The original API
consumer is a seventeenth test in that ingot. Seven model tests also check every
cell of a mixed-sign full 32×32 matrix and data ownership after the input changes.
The complete FA02 runs passed on EVM O1 and Linux native O0; three compiler
boundary cases rejected with their intended diagnostics at that checkpoint.

Two independent omission counterexamples use costs [5,3] with the more expensive
column0 selected. With u=3, v=[2,0], all the other explicit conditions hold, but
the positive-v check rejects. With u=5, v=[0,-2], sign, feasibility and selected
tightness hold, but unused-zero rejects. The optimum is 3 rather than5 in both
cases. These isolate the two rectangular conditions rather than depending on
a generic objective mismatch. Small example optima were also enumerated with
Python injections; this is an expected-value cross-check that preceded the
complete optimizer-oracle campaign recorded in SOLVER.md.

Inspected emitted IR gives verifier and matrix reader shared object-reference
parameters and sign-extends i128/i64 values before i256 additions. The verifier's
observed calls are only the dimension guard and private matrix reader; it has
no search/augmentation/slack/update dependency. Executing the same source on
two backends does not rule out a common bug. Larger independent and adversarial
coverage was outside this checkpoint and is recorded in the subsequent guides.

## Preserved implementation failures and repair

The first verifier suite passed all 17 tests on native but eight tests halted
with StackOverflow on both EVM O1 and O2. The trace showed growing live stack
values during large aggregate handling. Its helper had a by-value
`[i64;1024]` parameter and returned a full-array Problem. A two-test constructor
reduction did not reproduce the failure. This is evidence of a problematic
construction/call pattern, not a claim that all such literals fail or that a
specific compiler bug has been fully diagnosed.

The repair preserves the complete model and all 17 semantic scenarios. Problem
now owns 256 u256 words with four 64-bit signed lanes each; construction reads a
bounded buffer by shared reference and retains no reference. Public scalar
access and all mathematical checks stay unchanged. No heap/unsafe ownership
layer or host optimizer was introduced. Packing/conversion compile errors and
a test syntax error were retained and fixed before the complete passing runs.

The earlier EVM O0 failure of the initial representation is retained separately;
no current all-profile guarantee is made. The check driver also originally
copied IR from the assignment output path even when api_tests was selected;
that bookkeeping bug was corrected, the current O2 IR was captured explicitly,
and final run artifacts were collected from the proper ingot. A further guard
now copies only files explicitly reported written by the current run, avoiding
stale out/ artifacts after a compile failure. Final passing IR observations use
files reported written by those successful runs. Original test outputs/archives
were not replaced.

At that checkpoint internal test runtime sizes ranged from 96 to 9,531 bytes. These are test
programs and fixture initialization, not deployed AssignmentBoard code, initcode,
protocol transaction gas, or a universal size/performance bound. The actual
board deployment/receipt/state gate was outside FA02; see BOARD.md for its
later evidence.

The dated machine-readable record is [verifier.json](evidence/verifier.json).
The Hungarian optimizer, independent full solver-oracle campaign, CLI and board
are not implemented at this verifier checkpoint.
