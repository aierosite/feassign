# FeAssign in five minutes

FeAssign gives a small minimum-cost assignment result a checkable explanation.
It assigns every row to a different column, allowing extra columns to remain
unused. All pairs must be allowed and costs must be known finite integers.
The complete supported model is1 <= rows <= columns <=32 with full i64 costs.
This fits a small batch choosing among compatible resources. Direct demand
from Fe users is still inferred; the demo is an illustrative model, not a
measured production deployment.

The demo has two jobs and three resources. Fe chooses resource1 for job0 and
resource0 for job1, with total cost3. It also exports one selected index per row
and row/column potentials. A small independent verifier checks every dual
inequality, selected-edge tightness, injectivity, nonpositive column potentials
and zero potentials for unused columns. Those checks establish a lower bound
attained by the selected assignment. Python independently inspects the actual
Fe output and enumerates tiny injections for reference evidence; it never
supplies the product optimizer.

Fe is central to the implementation. The pure assignment ingot owns the bounded
model, Hungarian optimizer and separate verifier. Native Fe parses bounded
versioned input, solves, verifies and formats a deterministic certificate. A
small scalar C bridge supplies only OS/stdio status. The EVM consumer hashes a
canonical semantic problem and calls the same pure verifier. It does not run
the optimizer or trust a submitted objective. The board has immutable dimensions
and digest, records one verified result and rejects later submissions.

The core remains explicit: fixed capacities, private owned state, shared reads,
wide working arithmetic and no I/O/hash/storage/network. One additional opaque
sequential constructor was introduced only after a real EVM code-limit failure.
It removed a redundant1024-cell adapter buffer without shrinking the model or
adding an unsafe view. Arithmetic and Hungarian/duality are classical; the
contribution is this Fe implementation, shared proof boundary, consumers and
reproducible evidence, not a new mathematical algorithm or a global-first claim.

The evidence distinguishes tiny exhaustive spaces from representative large
cases. It includes endpoints and hostile i128 proofs, rectangular conditions,
ties, long/zero-delta augmentation, seeded/metamorphic checks, independent
certificate inspection, both backends, real I/O failures and actual Osaka
transactions at full32. Raw ABI bytes are not the problem commitment: values
are validated/re-encoded first. Dirty encodings reject; accepted nonminimal
representations have the same meaning. Failed submissions preserve state.

One command after setup runs the normal story plus an invalid proof, another
matrix and a repeat. The evidence contains receipts, getter values, code/init
sizes, gas and honest process timings. See DEMO.md and BOARD.md for limits.
The board does not authenticate resources, make costs truthful, prove delivered
work or hold funds. It is not a general scheduler, makespan/fairness optimizer,
capacity/forbidden-edge model, routing tool or zero-knowledge proof system.

Codex assisted research, design, implementation and checking. Design and generic
tool experiments predate the window and remain disclosed; product code/tests
were authored after opening. No competition rank, audit or security guarantee
is implied. The local technical package still needs the actual planned human
review and final freeze before the persistent project goal can be complete.
