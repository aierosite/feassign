# Current API and adversarial review

One bounded assignment model, one Fe optimizer and one separate verifier serve
two adapters. The core imports core::Result only and has no std, I/O, hash,
storage, external call, unsafe span or allocator service. Its owned concepts are
Problem, Certificate and the opaque ProblemBuilder introduced for a measured
code-size failure. Buffer construction delegates to the same packing path.
There is no graph hierarchy, second optimizer or exposed packed-word API.

All six ModelError cases have directed constructor/access witnesses: Dimensions,
CostCount, AssignmentCount, RowPotentialCount, ColumnPotentialCount and Index.
The seven VerifyError cases have separate witnesses, including Shape,
ColumnIndex, DuplicateColumn, PositiveColumnPotential, DualInfeasible,
SelectedEdgeNotTight and NonzeroUnusedColumn. Tests exercise matrix changes,
full i64 sums, hostile i128 addition, valid extreme cancellation, surplus
columns, alternative optima, ties, long/zero-delta augmentation and offsets
above255. Scalar access and ownership/private-field compilation are checked.

SolveError::Shape is a defensive internal malformed-shape test; safe public
constructors reject that state earlier. InternalInvariant is a reserved
implementation failure, not a regular valid-input outcome. No such normal-input
failure was observed. An isolated copied source tree deliberately corrupted
the exported assignment, exercising the final verifier postcondition: the
damaged executable returned CLI status6 and no success certificate, while the
unaltered control returned the correct result. This is fault containment for
that injected path, not coverage of every guard or a claim that the correct
solver fails on that valid matrix. No mutation hook is in product source.

The full goal requires versioned input. Review found that only certificate
input originally required a header. Both solve and verify now require exact
`FEASSIGN 1`; missing, future, noncanonical and truncated solve headers reject.
The same2906 exported-certificate/roundtrip campaign passed with43 classified
negative cases, the exact128KiB boundary and real descriptor/I/O checks.
Public CLI outcomes distinguish syntax, size limit, invalid proof, I/O,
internal invariant and usage. Assertion-based Python evidence drivers refuse
optimized mode; Fe product checks do not depend on Python.

Native owners are fixed arrays and official live argc/argv views. No explicit
Fe heap owners require release. C owns stdio state and signal-layout handling;
normal success requires final checked flush, and read errors are not EOF.
This is not whole-process zero-allocation, leak, durability or abrupt-kill
cleanup evidence. The board's typed decoder can allocate before application
length guards; no universal hostile-wire memory bound is claimed.

Actual ABI controls distinguish empty decoder reverts from wrong-problem and
invalid-certificate errors. Semantic wire variants, dirty narrow values,
immutable header/matrix binding, state preservation and repeats have observed
transactions. No hypothetical error path is relabelled as a passed test.
Known compiler/profile/driver failures and faithful repairs remain in the
dated evidence. O1 is the validated profile; old O0 failures are not erased.
These checks support current acceptance, not an audit, formal verification,
bug-free claim, human acceptance or final freeze.
