# Check an external optimizer's certificate

An assignment and row/column potentials can come from another optimizer.
FeAssign checks the exact original integer problem and every certificate
condition; it does not trust the optimizer's status or reported objective.
The existing native format and Board ABI already support this boundary.

## Try the retained small witness

After the [native build](../README.md), run from the source root:

```sh
target/native/feassign verify < examples/external-unit-gap-valid.cert
target/native/feassign verify < examples/external-unit-gap-converted.cert
```

The first command exits 0 and prints `VALID 18014398509481984`. The second
exits 4 with an invalid-certificate error and no success output. In
[Proof Studio](../workbench/README.md), paste either complete file into the proof
desk and verify it. The certificate contains its own matrix; compare that
matrix with the intended problem before using a result.

Here `M = 9007199254740992 = 2^53`. Original costs are:

| | Column 0 | Column 1 |
|---|---:|---:|
| Row 0 | M+1 | M |
| Row 1 | M | M+1 |

Binary64 conversion maps M+1 to M, losing the distinction. The retained raw
HiGHS candidate selects `[0,1]`; its cost on the original matrix is `2M+2`.
Its proposed row potentials `[M,M]` and column potentials `[0,0]` give bound
`2M`. The selected edges are not tight. Rejecting this witness is compatible
with optimal optimization of the converted floating-point model.

For the valid sample, the research adapter subtracted each row's minimum in
exact integer arithmetic before calling HiGHS. That yields `[[1,0],[0,1]]`.
It restored the integer row offsets to the returned row potentials and obtained
selection `[1,0]`, cost `2M` and the same bound `2M`. Fe validates the restored
witness against the original matrix. This particular transformation preserves
the unit gap; it is not a universal guarantee that every full-i64 matrix can
be converted losslessly for a floating-point solver.

These files retain numeric outputs from HiGHS 1.15.1 in a separate research
run. Rounding floating duals only constructs a candidate. A candidate may fail
even when the optimizer found an optimum; acceptance requires every exact
certificate condition. No HiGHS installation is needed to check these files,
and the product's solve command continues to run the Fe Hungarian optimizer.

## Existing local EVM boundary

On November 8, 2026 UTC, the unchanged Board built with Fe 26.5.1 accepted five
HiGHS-derived witnesses through its existing `submit` ABI. Original source
commit was `923bf4e71291f519298f1cc744f4db659a7c76fc`. Original core, CLI,
Board and workbench bytes are unchanged by this documentation/example revision.
The observed stored results were:

| Input | Preprocessing | Stored total | Submit receipt gasUsed |
|---|---|---:|---:|
| 2 x 3 contention | Exact row minima restored | 3 | 141606 |
| 3 x 4 signed rectangle | Raw | -14 | 177930 |
| 2 x 2 unit gap above 2^53 | Exact row minima restored | 18014398509481984 | 137635 |
| 32 x 32 all i64-max | Exact row minima restored | 295147905179352825824 | 2495517 |
| 32 x 32 all i64-min | Exact row minima restored | -295147905179352825856 | 2736989 |

The successful run has 17 receipts: five deployments, five accepted proofs,
five rejected repeats, the rejected raw unit-gap candidate and a rejected proof
for a different matrix. All seven failed submissions preserved all 34 mutable
storage slots. Getters returned the external selections and exact totals.
The last two negatives were submitted while the relevant board was still Open;
their rejection was due to the proof or commitment, rather than Solved state.
The different-matrix negative was constructed for this test; it was not another
HiGHS output. The first harness attempt has a separate successful deployment
and no submission; its incorrect immutable-layout assertion was corrected
without changing the product.

The node used pinned Anvil 1.8.7, Osaka, the enabled 16777216 transaction cap
and a 30000000 block limit; above-cap control was rejected. Every listed
transaction had a receipt/status and relevant code/getter/state readback, and
the owned node stopped. These are local configuration-specific observations,
not a public deployment or universal gas bound. Full receipts, calldata,
source bindings and the preserved harness calibration accompany the review
packet's external-proof evidence. Native checking is reproduced by the two
commands above; the standard [Board demo](DEMO.md) separately reproduces the
Fe-generated proof path.

The commitment and [Board ABI](BOARD.md) bind the original dimensions and costs.
The Board recomputes the total; no claimed objective is submitted. This witness
format applies to the documented complete, unit-capacity assignment model. It
does not certify arbitrary LP constraints, input truth, identity or delivered
work. Other integer tools can also return exact optima; no exclusive numeric
correctness, demand, general optimizer ranking or human approval is claimed.
