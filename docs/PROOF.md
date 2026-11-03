# What the certificate establishes

For a complete r-by-c integer cost matrix C with1 <= r <= c <=32, choose an
injection p from rows to columns. Minimize the sum of C[i,p[i]]. Extra columns
may be unused; every row must be assigned. This is a minimum-sum objective.

A certificate supplies p, one row potential u[i] and one column potential v[j].
The separate verifier checks shape, valid distinct indices, v[j] <=0, every
u[i]+v[j] <= C[i,j], equality on selected edges and v[j]=0 on unused columns.
It computes the actual selected sum from C; no claimed objective is trusted.

For any other injection q, summing the inequalities gives:

```text
sum C[i,q[i]] >= sum u[i] + sum v[q[i]] >= sum u[i] + sum_all v[j].
```

The second inequality uses v<=0: omitting unused nonpositive terms cannot lower
the sum. For p, tightness and zero unused potentials make both bounds equal.
Therefore p attains a lower bound for every injection and is optimal. This is
classical assignment duality, not a new algorithm or a machine-checked proof.
All conditions matter for rectangles. With costs `[5,3]`, omitting either column
sign or unused-zero independently allows a suboptimal selected cost5; directed
tests retain both counterexamples. A square potential-gauge shift does not
justify arbitrary normalization for rectangular instances.

The actual Fe optimizer uses Hungarian augmentations. Initially u is each row's
minimum and v is zero. A phase grows reached rows S and matched columns T;
|S|=|T|+1. Minimum nonnegative slack raises u on S and lowers v on T, preserving
feasibility and tightness. Zero delta still reaches a new column. A free column
ends the search before joining T, then predecessors augment the injection.
Matched columns remain matched; final unused columns retain zero v. A complete
first scan initializes slack explicitly, without an arithmetic infinity. The dummy slot is
private workspace33, excluded from public32 values. The solver checks its own
result with the separately structured verifier before returning a certificate.

At phase start, real columns are unreached and current is dummy0. Only the
first scan has current==0: it visits every real column and assigns its slack
and predecessor before either is used. Later scans choose current from1..c;
all remaining slacks are initialized. The potential-update loop runs after a
complete scan and dummy0 remains reached, so every unreached slot there is real
and has a slack. Separate initialized-slack flags duplicate this existing state.
Index0 is never read as a predecessor: augmentation stops at0. Clearing that
array again in every phase is unnecessary; initial fixed-array initialization
remains. These source invariants preserve tie comparisons and progress guards.

Intended work is O(r²c) solve and O(rc) verify, with O(r+c) solver workspace
beyond the matrix. These are algorithmic bounds, not measured speed or gas ratios.
All finite complete instances in the supported shape have an assignment.
There is no NoAssignment escape or forbidden-edge sentinel.

Costs are full i64. The sum of at most32 such values fits i128. Arithmetic
widens to i256 before combining values. For external certificates, two full-i128
potentials can sum to [-2^128,2^128-2]; these are not solver-generated bounds.
Valid full-i128 gauge shifts remain accepted.

For the solver, let L and H be the global cost extremes and D=H-L<=2^64-1.
Each real u[i] starts at its row minimum and only increases. Before an
augmentation a free real column k exists with v[k]=0. For every reached row i,
delta<=slack[k]<=C[i,k]-u[i], so the update keeps u[i]<=row_max.
Unreached rows do not change; augmentation changes owners, not potentials.
Thus real u stays in [L,H]. Tight matched edges give real v=C-u in [-D,0];
free columns stay at zero because search stops before reaching them.

Consequently C-u lies in [-D,D] and feasible reduced costs C-u-v in [0,2D].
The first complete scan initializes every real slack; later it is the minimum
reduced cost over reached rows. Subtracting delta<=slack keeps it nonnegative.
The free column also gives slack[k]<=D, hence 0<=delta<=D.

The private dummy v[0] is different. Let alpha be the sum of all r initial row
minima and F=sum(real u)+sum(real v), excluding dummy slots. Initially F=alpha.
Each complete dual update raises F by delta since |S|=|T|+1; augmentation leaves
F unchanged. At every completed feasible update, weak duality gives
F<=cost(any injection)<=rH, while alpha>=rL. Thus cumulative delta=F-alpha<=rD.
Dummy v[0] starts at zero and subtracts every delta without resetting, so it
stays in [-rD,0], above -2^69 for r<=32. No final successful output is needed
for this prefix bound. At completion objective=alpha-v[0]; -v[0] alone omits
the row-minimum initialization. The implementation recomputes the selected sum.

Sequential scalar writes need not themselves preserve global feasibility halfway
through an update. Even independent operand intervals bound u+delta by
[L,H+D], real v-delta by [-2D,0], slack-delta by [-D,2D], and dummy v[0]-delta
by [-(r+1)D,0]. These loose solver intermediate bounds have magnitude below
2^70; completed states satisfy the tighter invariants above. Generated real u
fits i64 and real v is at least -(2^64-1), so exported i128 suffices. Dummy slots
are not exported. Narrowing and progress failures are implementation invariant
failures, not extra unsupported valid inputs.

Problem and certificate fields are private. A shape-valid Certificate is still
an untrusted proof: indices and potentials can be mathematically invalid.
ProblemBuilder is opaque until consuming exact-count finish; logical costs,
not raw packed words, enter it. Four-i64-per-word packing is internal storage,
never the semantic ABI. Adapters bind both dimensions and validated cost values.

Independent evidence checks actual exported fields with arbitrary Python
integers and enumerates small injections. Large certificate/metamorphic cases
are not exhaustive full-domain tests. Correct input data, resource identity,
availability and delivered work remain outside this mathematical statement.
