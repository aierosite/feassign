# Bounded model API

The core uses owned, private-field Problem, Certificate and ProblemBuilder types
and shared-reference scalar access. None implements Copy or an ABI/deserialization trait. This is a Fe API,
not a C ABI. Source imports only core::Result and calls no std APIs; Fe supplies
implicit core/std dependencies. The source has no I/O, hash, storage or allocator API.

`new_problem(rows, columns, cost_count, ref costs)` reads a `[i64;1024]` buffer.
It requires `1 <= rows <= columns <= 32` and exactly
`cost_count == rows * columns`, widening before multiplication. Only that
row-major prefix is semantic; remaining capacity is ignored. Construction
copies values into owned private storage, retaining no input reference. The
caller can reuse/change its input buffer after construction. `rows`, `columns`
and checked `cost(ref problem, row, column)` expose values without returning or
copying the entire matrix. Out-of-range access returns `ModelError::Index`.

For streaming adapters, `start_problem(rows,columns)` checks shape and creates
an opaque builder. `append_cost(mut builder,value)` appends one logical i64 in
row-major order. An append beyond rows*columns returns CostCount without changing
the builder; `finish_problem(builder)` consumes it and returns an owned Problem
only after exactly that many appends. An incomplete finish returns CostCount.
There is no raw packed-word constructor or exposed partially initialized Problem.
The buffer convenience constructor delegates to this same packing path.

This additional concept follows a measured deployment failure: the initial
board staged 1024 i64 values before packing them, and its emitted runtime
exceeded the ordinary EVM code limit. Sequential construction removed the
staging array without an unsafe view, heap framework, host optimizer or model
reduction. The public stream remains logical signed costs; packed storage is
still private. Full32 append/read, overflow preservation, premature finish and
shape guards ran on both backends. External code cannot forge builder fields or
reuse one after finishing; the compiler-negative checker now has five cases.

`new_certificate(ref problem, selected_count, row_potential_count,
column_potential_count, selected, row_potentials, column_potentials)` stores
three 32-slot array values. These arrays are copyable: callers may reuse/change
their buffers without changing the owned certificate. Logical counts must equal
rows, rows and columns, respectively. Counts describe the supplied semantic
prefix, not physical capacity. Adapters must validate actual decoded lengths before checked
narrowing into these counts; truncating a raw length is not valid decoding.

`certificate_shape`, `selected_column`, `row_potential` and `column_potential`
provide dimensions and checked scalar reads. All i128 potentials and all byte
values in selected indices are preserved. Construction validates shape only:
an index 255, duplicate column, positive column potential or nonoptimal proof
may still be represented. The separate mathematical verifier must check every
condition rather than trust construction. No submitted objective is stored.

The library owns construction results; solving and verification borrow them.
Actual independent-ingot compilation rejects external literals
for every private field and rejects using a Problem after ownership moves.
The positive consumer in `api_tests` accesses the full 32×32 representation and
both i128 potential endpoints on native and EVM. These checks are not a proof
of all aliasing behavior or zero copying throughout a whole application.

The private representation packs four two's-complement i64 lanes into each of
256 u256 words. This preserves all 1,024 costs while reducing the size of a
Problem value at EVM function boundaries. Encoding uses a wider signed value
and adds 2^64 for negative inputs; decoding masks a 64-bit lane and subtracts 2^64
when its high bit is set. Conversions are checked and use no unsafe/pointers or
external allocator. This is an internal representation, not the ABI/commitment
format. Adapters must still encode the logical row-major i64 values and both
dimensions.

The original full-array-by-value interface passed the first model checks but
later produced StackOverflow in eight verifier-suite cases at both EVM O1/O2.
The same 17 semantic cases passed after the packed owned representation and
borrowed-buffer constructor were introduced. The two-case reduced constructor
experiment passed, so no universally reproduced compiler defect/root cause is
claimed. Original failures and pre-change sources remain recorded. See
[the verifier record](VERIFIER.md).

## Current checks

From the repository root with the pinned compiler:

```sh
fe test . --ingot assignment --backend sonatina -O 1
fe test . --ingot api_tests --backend sonatina -O 1
fe test . --ingot assignment --backend native -O 1
fe test . --ingot api_tests --backend native -O 1
python tools/check-api-boundaries.py --fe fe
```

Native commands require supported Linux and a system linker.
[REPRODUCE.md](REPRODUCE.md) lists current counts/commands;
[SOLVER.md](SOLVER.md) preserves the earlier expected-cost checkpoint. Some
known-value checks may be optimized/constant-evaluated; their results are
language/API observations, not independent mathematical-oracle evidence.
The initial full32 IR/runtime evidence and EVM O0 failure remain in
[REPRESENTATION-GATE.md](REPRESENTATION-GATE.md). Compiler-negative fixtures
must fail for their specified privacy/move diagnostics, not for an unrelated
type or dependency error.

The dated [model](evidence/model-api.json), [verifier](evidence/verifier.json)
and [optimizer](evidence/solver.json) records preserve their original source
hashes and checkpoint scopes. [board.json](evidence/board.json) is the original
sequential-builder/CLI/board checkpoint, before the later static-tail revision.
[BOARD.md](BOARD.md) describes the revised board, its targeted validation and
the candidate manifest that binds current source to evidence.
