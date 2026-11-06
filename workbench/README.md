# FeAssign Proof Studio

Proof Studio is a local browser interface for the existing Fe solver and
verifier. It needs Python 3.10 or later and the same Linux x86-64 environment
and pinned tools as the [reproduction guide](../docs/REPRODUCE.md).

From the source root, run the normal demo into a new directory and start the
workbench from its verified output:

```sh
python3 tools/demo.py --fe "/absolute/path/to/fe" --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --out target/demo-01
python3 workbench/server.py --run-dir target/demo-01 --port 8765
```

Open `http://127.0.0.1:8765/`. On Windows, run these commands inside WSL, or
use `--wsl-distro <distribution>` with the Windows Python launcher and point
`--run-dir` at the accessible WSL output. The server checks the pinned tool
digests, native executable and runtime input hashes before serving. The optional
`--packet` argument adds a download for a matching review ZIP.

The packet's `source/` directory carries the commit marker. A Git checkout
uses Git to identify the source when the run record has no commit marker.

To view the full set of reproduction metrics in Evidence, run the
[11-stage reproduction](../docs/REPRODUCE.md) and pass its output directory to
`--run-dir`. The studio labels the active evidence scope.

- **Studio** edits or pastes a bounded signed i64 matrix, runs Fe and draws the
  selected edges returned by the solver.
- **Proof desk** verifies the exact text envelope with the Fe CLI. It shows
  the dual bound, constraint counts and the slack of an inspected edge.
  The duplicate-column example lets the reviewer observe a rejected proof.
  Solver results leave a manually changed editor intact. **Load solver
  certificate** replaces the editor with the certificate for that result.
- **Evidence** shows completed local Board receipts, including their hashes,
  and the normal demo or full reproduction record.
- **Review** keeps notes on this device in `workbench-feedback.jsonl` next to
  the reproduction directory. The optional `--feedback-file` sets its path.
  Keep the adjacent lock file while any workbench using that note file is open.

The graph animates the selected edges after Fe returns them. The browser uses
exact integer arithmetic to display the returned proof. Fe solves and accepts
or rejects certificates. The interface runs on loopback with Python's standard
library and static browser assets.
