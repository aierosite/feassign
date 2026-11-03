# Bounded model API

The core uses two owned, private-field types and shared-reference scalar access.
Neither type implements Copy or an ABI/deserialization trait. This is a Fe API,
not a C ABI. There is no I/O, hashing, storage, allocation service or dependency
on std in the assignment ingot.

`new_problem(rows, columns, cost_count, costs)` consumes `[i64;1024]` storage.
It requires `1 <= rows <= columns <= 32` and exactly
`cost_count == rows * columns`, widening before multiplication. Only that
row-major prefix is semantic; remaining capacity is ignored. `rows`, `columns`
and checked `cost(ref problem, row, column)` expose values without returning or
copying the entire matrix. Out-of-range access returns `ModelError::Index`.

`new_certificate(ref problem, selected_count, row_potential_count,
column_potential_count, selected, row_potentials, column_potentials)` consumes
three 32-slot arrays. Logical counts must equal rows, rows and columns,
respectively. Counts describe the supplied semantic prefix, not physical
capacity. Adapters must validate actual decoded lengths before checked
narrowing into these counts; truncating a raw length is not valid decoding.

`certificate_shape`, `selected_column`, `row_potential` and `column_potential`
provide dimensions and checked scalar reads. All i128 potentials and all byte
values in selected indices are preserved. Construction validates shape only:
an index255, duplicate column, positive column potential or nonoptimal proof
may still be represented. The separate mathematical verifier must check every
condition rather than trust construction. No submitted objective is stored.

The library owns construction results; solving and verification are intended
to borrow them. Actual independent-ingot compilation rejects external literals
for every private field and rejects using a Problem after ownership moves.
The positive consumer in `api_tests` accesses the full32 representation and
both i128 potential endpoints on native and EVM. These checks are not a proof
of all aliasing behavior or zero copying throughout a whole application.

## Current checks

From the repository root with the pinned compiler:

```sh
fe test . --ingot assignment --backend sonatina -O 1
fe test . --ingot api_tests --backend sonatina -O 1
fe test . --ingot assignment --backend native -O 0
fe test . --ingot api_tests --backend native -O 0
python tools/check-api-boundaries.py --fe fe
```

Native commands require supported Linux and a system linker. The six model
tests and one separate-ingot consumer passed on the named profiles. Some
known-value checks may be optimized/constant-evaluated; their results are
language/API observations, not independent mathematical-oracle evidence.
The initial full32 IR/runtime evidence and EVM O0 failure remain in
[REPRESENTATION-GATE.md](REPRESENTATION-GATE.md). Compiler-negative fixtures
must fail for their specified privacy/move diagnostics, not for an unrelated
type or dependency error.

The optimizer, mathematical verifier, CLI and board are still forthcoming at
this model checkpoint. See [the dated model evidence](evidence/model-api.json).
