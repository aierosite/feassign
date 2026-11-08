# FeAssign Proof Studio

Proof Studio is a local browser interface for the existing Fe solver and
verifier. It needs Python 3.10 or later and the same Linux x86-64 environment
and pinned tools as the [reproduction guide](../docs/REPRODUCE.md).

From the source root, use the [judge handoff](../JUDGING.md) to complete the
full review into an unused directory, then start the workbench from that output:

```sh
python3 tools/review.py full --download --out target/studio-review-01
python3 workbench/server.py --run-dir target/studio-review-01/full-run --port 8765
```

Keep the server terminal running and open `http://127.0.0.1:8765/`. The full
review installs no system packages; `--download` permits verified official
tool downloads. It is unnecessary when supplying the pinned local tool paths.
You can also use the existing smaller [demo](../docs/DEMO.md) and pass its
output to `--run-dir`, or reuse a completed full run without rebuilding.
On Windows, run these commands inside WSL, or
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
  Large grids scroll within the card with row and resource headings visible.
  Press Enter in a cost cell to run the solver.
- **Proof desk** verifies the matrix and witness inside the text envelope with
  the Fe CLI. Its result refers to that embedded matrix. It shows
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

## Connection troubleshooting

An open tab does not keep its server alive. If the terminal closes, the machine
restarts or the process stops, the page can remain visible while requests fail.
`Local Fe service unavailable` describes that connection failure; it is not a
rejected certificate. Restart the same server command and retry the action in
the existing tab. The request error preserves the editor input; do not reload
or replace a draft just to reconnect. If using a new port, open the printed URL
and transfer any draft you want to keep explicitly. Use `--port 0` when 8765 is busy.
If the initial candidate never loaded and buttons remain disabled, preserve any
draft separately, then reload after the server is running. A previously loaded
page can retry its action without reloading.

For an HTTP execution/storage error, inspect the server terminal. For a native
verification rejection, the status contains the Fe CLI diagnostic. The server
does not depend on a public deployment, hosted API, wallet or external RPC.
