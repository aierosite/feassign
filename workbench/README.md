# FeAssign Proof Studio

Proof Studio is a local browser interface for the existing Fe solver and
verifier. It needs Python 3.10 or later and the same Linux x86-64 environment
and pinned tools as the [reproduction guide](../docs/REPRODUCE.md).

From the source root, run the complete reproduction into a new directory and
start the workbench from that result:

```sh
python3 tools/reproduce.py --fe "/absolute/path/to/fe" --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --out target/repro-01
python3 workbench/server.py --run-dir target/repro-01 --port 8765
```

Open `http://127.0.0.1:8765/`. On Windows, run these commands inside WSL, or
use `--wsl-distro <distribution>` with the Windows Python launcher and point
`--run-dir` at the accessible WSL reproduction output. The server checks the
native executable and its runtime input hashes before serving. The optional
`--packet` argument adds a download for a matching review ZIP.

- **Studio** edits or pastes a bounded signed i64 matrix, runs Fe and draws the
  selected edges returned by the solver.
- **Proof desk** verifies the exact text envelope with the Fe CLI. It shows
  the dual bound, selected-edge equalities and the slack of an inspected edge.
  The duplicate-column example lets the reviewer observe a rejected proof.
- **Evidence** reads completed local Board receipts and reproduction records.
- **Review** keeps notes on this device in `workbench-feedback.jsonl` next to
  the reproduction directory. The optional `--feedback-file` sets its path.

The graph animates the selected edges after Fe returns them. The browser uses
exact integer arithmetic to display the returned proof. Fe solves and accepts
or rejects certificates. The interface runs on loopback with Python's standard
library and static browser assets.
