# One local demonstration

The example assigns two independent jobs to three compatible resources. Every
job/resource pair is allowed, and a resource can take at most one job. The
integer costs are illustrative points, not measured prices or real dispatch:

| | Resource 0 | Resource 1 | Resource 2 |
| --- | ---: | ---: | ---: |
| Job 0 | 1 | 2 | 9 |
| Job 1 | 1 | 100 | 3 |

Both jobs prefer Resource 0. A greedy choice in row order gives Job 0
Resource 0 and Job 1 Resource 2, costing `1+3=4`.
The Fe solver selects columns `[1,0]`: Job 0 costs 2, Job 1 costs 1, total 3.
Resource 2 remains unused. The certificate contains row potentials `[2,2]` and
column potentials `[-1,0,0]`, so its lower bound is `2+2-1=3`.
Every `u+v` is at most the corresponding cost, selected edges are tight, column
potentials are nonpositive and unused ones are zero. These conditions prove
the minimum sum, independently of the search.

Follow the [pinned Linux setup](REPRODUCE.md) for the exact tools, hashes and
binary prerequisites, including Fe's GLIBC_2.39 and cast's libudev.so.1.
The observed environment is Ubuntu 24.04 under WSL. No external service or API
key is used. Run from this source root:

```sh
python3 tools/demo.py --fe /absolute/path/to/fe --anvil /absolute/path/to/anvil --cast /absolute/path/to/cast --out target/demo-01
```

Use a new output directory for each run. By default the OS selects a free
localhost port; optional `--port` requests a specific one. Before each RPC it
checks that the IPv4 listener belongs to its child process using readable Linux
`/proc`. RPC bypasses environment proxies; cleanup stops only that child.
It builds native Fe and the board with fresh output/cache, solves the versioned
example, checks the real certificate in Python, invokes Fe verify, starts its
own Osaka Anvil with the transaction cap enabled and deploys the committed
board. A successful submit receipt and getters must match Fe's p and total.
The owned node is stopped on success or failure. A failed run preserves logs.

The same run demonstrates three sensitive failures:

1. Duplicate selected columns: mathematical certificate rejection while Open.
2. A valid proof for every cost shifted by 1: immutable problem-digest rejection.
3. Repeating an already recorded result: Solved-state rejection.

Each has a real reverted receipt, sufficient declared gas and unchanged mutable
storage. The script checks revert messages, not just any failure. This is a
mathematical reference consumer, not a claim about resource identity, true input
costs, work delivery or payments. Identical-problem certificates are reusable.

`demo.json` records exact versions, binary/source hashes, proof, byte/code sizes,
transactions/receipts/state and separate native process-wall timings for a help
startup baseline, solve and verify. These single samples include startup and
I/O; do not subtract them to claim isolated-kernel speed or a savings ratio.
The native proof is `solution.cert`, the semantic problem bytes are
`problem.abi.hex` and all build/node/stdout/stderr evidence remains in the output.
The 32 × 32 and adversarial ABI measurements are separate from this small story.

Earlier gas, digest and timing samples used a different, uncontended matrix.
They retain that scope. Run the command above for this example's actual values
in `demo.json`, including `proof`, `comparison` and transaction receipts.
This small example establishes no universal performance bound or measured
production savings.
