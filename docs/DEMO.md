# One local demonstration

The example assigns two independent jobs to three compatible resources. Every
job/resource pair is allowed, and a resource can take at most one job. The
integer costs are illustrative points, not measured prices or real dispatch:

| | Resource0 | Resource1 | Resource2 |
| --- | ---: | ---: | ---: |
| Job0 |4|1|8|
| Job1 |2|6|3|

The actual Fe solver selects columns `[1,0]`: Job0 costs1, Job1 costs2, total3.
Resource2 remains unused. The certificate contains row potentials `[1,2]` and
column potentials `[0,0,0]`. Every u+v is at most the corresponding cost, the
selected edges are tight, column potentials are nonpositive and unused ones
are zero. These conditions prove the minimum sum, independently of the search.

Install the exact Fe26.5.1 release asset and Foundry1.8.7 tools for Linux x86-64,
plus Python3.10+ and a system C compiler named cc. WSL is supported. Tool hashes
and full commits are in toolchain.json. No external service or API key is used.
Run from this source root:

```sh
python3 tools/demo.py --fe /absolute/path/to/fe --anvil /absolute/path/to/anvil --cast /absolute/path/to/cast --out target/demo-01
```

Use a new output directory for each run. Optional `--port` changes the fresh
localhost Anvil port; the script never attaches to or stops an existing node.
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

The first executed portable Linux run observed total3, p `[1,0]`, deployed
code23668bytes, full initcode24155bytes, deployment5070834gas and normal submit
141938gas. Three expected rejections left state unchanged. Timing samples were
about3.56ms for help,5.46ms solve and5.26ms verify in that environment; subsequent
runs may differ. This is an observed example, not a universal performance bound.
