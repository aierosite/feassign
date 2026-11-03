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

Costs are full i64. The sum of at most32 such values fits i128. Both mathematical
verification and optimization widen combined arithmetic to i256 first, including
hostile full-i128 u/v additions. The solver's generated real potentials have a
tighter bound: each u[i] stays between that row's minimum and maximum cost.
It starts at the minimum and only increases. Before every augmentation, even
the last, a free real column k exists and retains v[k]=0; full-matrix dual
feasibility therefore gives u[i]<=C[i,k]<=row_max. Augmentation changes owners,
not potentials. For global cost extremes L and H, tight matched edges then give
L-H<=v[j]<=0; unused v is zero. Thus generated u fits i64 and generated v is at
least -(2^64-1), so exported i128 suffices. This excludes the private dummy slot
and does not restrict external certificates: valid full-i128 gauge shifts remain
accepted. Narrowing and progress failures are implementation invariant failures,
not extra unsupported valid inputs. The objective is recomputed;
-dummyPotential would omit the nonzero row-minimum initialization.

Problem and certificate fields are private. A shape-valid Certificate is still
an untrusted proof: indices and potentials can be mathematically invalid.
ProblemBuilder is opaque until consuming exact-count finish; logical costs,
not raw packed words, enter it. Four-i64-per-word packing is internal storage,
never the semantic ABI. Adapters bind both dimensions and validated cost values.

Independent evidence checks actual exported fields with arbitrary Python
integers and enumerates small injections. Large certificate/metamorphic cases
are not exhaustive full-domain tests. Correct input data, resource identity,
availability and delivered work remain outside this mathematical statement.
