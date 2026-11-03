# One local demonstration

The example assigns two independent jobs to three compatible resources. Every
job/resource pair is allowed, and a resource can take at most one job. The
integer costs are illustrative points, not measured prices or real dispatch:

| | Resource0 | Resource1 | Resource2 |
| --- | ---: | ---: | ---: |
| Job0 |1|2|9|
| Job1 |1|100|3|

Both row minima choose Resource0, violating its one-job limit. A row-order
greedy choice gives Job0 Resource0 and Job1 Resource2, costing `1+3=4`.
The actual Fe solver selects columns `[1,0]`: Job0 costs2, Job1 costs1, total3.
Resource2 remains unused. The certificate contains row potentials `[2,2]` and
column potentials `[-1,0,0]`, so its lower bound is `2+2-1=3`.
Every u+v is at most the corresponding cost, the
selected edges are tight, column potentials are nonpositive and unused ones
are zero. These conditions prove the minimum sum, independently of the search.

Follow the [pinned Linux setup](REPRODUCE.md) for the exact tools, hashes and
binary prerequisites, including Fe's GLIBC_2.39 and cast's libudev.so.1.
The observed environment is Ubuntu24.04 under WSL. No external service or API
key is used. Run from this source root:

```sh
python3 tools/demo.py --fe /absolute/path/to/fe --anvil /absolute/path/to/anvil --cast /absolute/path/to/cast --out target/demo-01
```

Use a new output directory for each run. By default the OS selects a free
localhost port; optional `--port` requests a specific one. The script never
attaches to or stops an existing node.
It builds native Fe and the board with fresh output/cache, solves the versioned
example, checks the real certificate in Python, invokes Fe verify, starts its
own Osaka Anvil with the transaction cap enabled and deploys the committed
board. A successful submit receipt and getters must match Fe's p and total.
The owned node is stopped on success or failure. A failed run preserves logs.

The same run demonstrates three sensitive failures:

1. Duplicate selected columns: mathematical certificate rejection while Open.
2. A valid proof for every cost shifted by1: immutable problem-digest rejection.
3. Repeating an already recorded result: Solved-state rejection.

Each has a real reverted receipt, sufficient declared gas and unchanged mutable
storage. The script checks revert messages, not just any failure. This is a
mathematical reference consumer, not a claim about resource identity, true input
costs, work delivery or payments. Identical-problem certificates are reusable.

`demo.json` records exact versions, binary/source hashes, proof, byte/code sizes,
transactions/receipts/state and separate native process-wall timings for a help
startup baseline, solve and verify. These single samples include startup and
I/O; do not subtract them to claim isolated-kernel speed or a savings ratio.
The actual native proof is solution.cert, the semantic problem bytes are
problem.abi.hex and all build/node/stdout/stderr evidence remains in the output.
Full32 and adversarial ABI measurements are separate from this small story.

The earlier portable checkpoint used a different, uncontended matrix. Its gas,
digest and timing samples do not measure this revised example. A run of the
command above records this example's actual values in demo.json; compare its
`proof`, `comparison` and transaction receipts. Full32 evidence is a separate
campaign. No universal performance bound or measured production savings follow
from this small example.
