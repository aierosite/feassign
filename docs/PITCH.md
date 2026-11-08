# FeAssign in five minutes

FeAssign computes a minimum-cost assignment and exports a checkable certificate.
It assigns every row to a different column, allowing extra columns to remain
unused. All pairs must be allowed and costs must be known finite integers.
It supports `1 <= rows <= columns <= 32`, with full `i64` costs.
It models small batches of compatible resources. Direct demand
from Fe users is still inferred; the demo is an illustrative model, not a
measured production deployment.

The demo has two jobs and three resources, with costs `[1,2,9]` and `[1,100,3]`.
Both jobs prefer resource 0, which can accept only one job. Taking each job's
cheapest available resource in row order costs 4: columns `[0,2]`. Fe instead
chooses resource 1 for job 0 and resource 0 for job 1, with total cost 3. Resource 2
remains unused. It exports selected indices and row/column potentials; the
dual lower bound is `2+2-1=3`. A small independent verifier checks every dual
inequality, selected-edge tightness, injectivity, nonpositive column potentials
and zero potentials for unused columns. Those checks establish a lower bound
attained by the selected assignment. Python independently inspects the actual
Fe output and enumerates tiny injections for reference evidence; it never
supplies the product optimizer.

Fe is central to the implementation. The pure assignment ingot owns the bounded
model, Hungarian optimizer and separate verifier. Native Fe parses bounded
versioned input, solves, verifies and formats a deterministic certificate. A
small scalar C bridge supplies byte I/O and stream status. The EVM consumer hashes a
canonical semantic problem and calls the same pure verifier. It does not run
the optimizer or trust a submitted objective. The board has immutable dimensions
and digest, records one verified result and rejects later submissions.

Three Fe choices make that boundary visible in the code: owned private Problem
and Certificate types with shared `ref` reads; checked integer conversion with
widening before arithmetic; and explicit `uses` declarations for the board's
immutable reads and mutable writes. The assignment ingot imports only core's
Result. The board imports its verifier without importing the search into its
submission path. See [the core](../ingots/assignment/src/lib.fe) and
[the board](../ingots/board/src/lib.fe). This is a reusable library and a
reference consumer; neither requires a production service or a funded protocol.

The verifier also checks witnesses from other optimizers. In a separate local
HiGHS experiment, five restored integer certificates passed both native Fe and
the existing board, including full32 costs at both i64 endpoints. A candidate
whose binary64 model lost a unit difference was rejected against the original
integers. [Try the small example](INTEROPERABILITY.md) without installing that
optimizer. Exact checking is useful even when search happens elsewhere; this
does not make FeAssign a general LP verifier or establish exclusive numeric
correctness or a solver speed ranking.

The core uses fixed capacities and wide arithmetic, with no I/O, hash, storage
or network. An opaque sequential constructor replaced a redundant 1024-cell
adapter buffer after an EVM code-limit failure. It preserves the full model
without an unsafe view. Hungarian and duality are classical; the contribution
is the Fe implementation, shared proof boundary, consumers and reproducible
evidence, not a new algorithm or global-first claim.

The evidence distinguishes tiny exhaustive spaces from representative large
cases. It includes endpoints and hostile i128 proofs, rectangular conditions,
ties, long/zero-delta augmentation, seeded/metamorphic checks, independent
certificate inspection, both backends, real I/O failures and actual Osaka
transactions for 32 × 32 matrices. Problem commitments hash a canonical tuple
of validated values. Dirty encodings are rejected; accepted nonminimal
representations encode the same values. Failed submissions preserve state.

One command after setup runs the normal story plus an invalid proof, another
matrix and a repeat. The evidence contains receipts, getter values, code/init
sizes, gas and honest process timings. See [the demo](DEMO.md) and
[board limits](BOARD.md).
[Proof Studio](../workbench/README.md) lets reviewers edit the matrix, replay
the returned matching, inspect an edge's dual slack and try a duplicate-column
certificate against the same Fe verifier. It launches from the normal demo's
output and labels the scope of the recorded evidence.
The board does not authenticate resources, make costs truthful, prove delivered
work or hold funds. It is not a general scheduler, makespan/fairness optimizer,
capacity/forbidden-edge model, routing tool or zero-knowledge proof system.

Codex assisted research, design, implementation and checking. Design and generic
tool experiments predate the window and remain disclosed; product code/tests
were authored after opening. No competition rank, audit or security guarantee
is implied. The local technical package still needs the actual planned human
review and final freeze; local execution is distinct from contest submission.
