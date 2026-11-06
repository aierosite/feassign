"""Local review interface for the validated FeAssign candidate."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from uuid import uuid4
from zipfile import ZipFile


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent
STATIC = HERE / "dist"
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.css": ("app.css", "text/css; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8")}
NOTE_TOPICS = {"Clarity", "Correctness", "Reproduction", "Board evidence", "Other"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(number):
    digits = number.lstrip("-").lstrip("0")
    if not digits:
        return "0"
    return ("-" if number.startswith("-") else "") + digits


def certificate_fields(text):
    parts = text.split()
    rows, cols = map(int, map(canonical, parts[2:4]))
    end = 4 + rows * cols
    return {
        "matrix": [list(map(canonical, parts[start:start + cols])) for start in range(4, end, cols)],
        "selected": list(map(int, map(canonical, parts[end:end + rows]))),
        "u": list(map(canonical, parts[end + rows:end + rows * 2])),
        "v": list(map(canonical, parts[end + rows * 2:end + rows * 2 + cols])),
        "total": canonical(parts[-1]),
    }


class Review:
    def __init__(self, run, package, feedback_path, distro):
        full_file = run / "reproduce.json"
        full = load(full_file)
        self.commit = full.get("source_commit") or subprocess.check_output(
            ["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True
        ).strip()
        self.package = package
        demo = load(run / "demo/demo.json")
        binary = run / "demo/native/feassign"
        binary_sha = sha(binary)
        if not (full["success"] and len(full["records"]) == 11
                and all(row["exit_code"] == 0 for row in full["records"]) and demo["success"]
                and demo["node_stopped"] and binary_sha == demo["native_executable_sha256"]):
            raise ValueError("Run the complete FeAssign reproduction before starting the workbench")
        for name, digest in demo["source_hashes"].items():
            if full["source_hashes"].get(name) != digest or sha(SOURCE / name) != digest:
                raise ValueError(f"Reproduction does not match the checked-out runtime input {name}")
        if os.name == "nt":
            if not distro:
                raise ValueError("On Windows, supply --wsl-distro for the distribution that ran the reproduction")
            linux = "/mnt/" + binary.drive[0].lower() + "/" + binary.as_posix()[3:]
            self.command = ["wsl.exe", "-d", distro, "--exec", linux]
            self.process_options = {"creationflags": subprocess.CREATE_NO_WINDOW}
        else:
            self.command = [str(binary)]
            self.process_options = {}
        docs = SOURCE / "docs"
        self.files = {key: (docs / name).read_bytes() for key, name in {
            "demo": "DEMO.md", "proof": "PROOF.md", "pitch": "PITCH.md",
            "provenance": "PROVENANCE.md",
        }.items()}
        self.files["guide"] = (HERE / "README.md").read_bytes()
        self.files["run"] = full_file.read_bytes()
        if package:
            with ZipFile(package) as archive:
                roots = [name for name in archive.namelist() if name.count("/") == 1 and name.endswith("/MANIFEST.json")]
                if len(roots) != 1:
                    raise ValueError("Expected a single candidate manifest in the ZIP")
                manifest = json.loads(archive.read(roots[0]))
                prefix = roots[0].removesuffix("MANIFEST.json")
                if manifest["source_commit"] != self.commit or manifest["source_hashes"] != full["source_hashes"]:
                    raise ValueError("Candidate package and reproduction do not match")
                for key, member in {"guide": "HANDOFF.md", "demo": "evidence/current-run/DEMO-RESULT.md"}.items():
                    data = archive.read(prefix + member)
                    if hashlib.sha256(data).hexdigest() != manifest["files"][member]:
                        raise ValueError(f"Evidence hash mismatch for {key}")
                    self.files[key] = data
        text = (run / "demo/solution.cert").read_text(encoding="ascii")
        self.meta = {"commit": self.commit, "packageSha256": sha(package) if package else None,
                     "binarySha256": binary_sha,
                     "compiler": full["fe_version"], "stages": len(full["records"]),
                     "summary": full["observed_summary"], "certificate": text,
                     "sample": certificate_fields(text), "greedy": demo["comparison"]["row_order_greedy_total"],
                     "receipts": [{"label": row["label"], "status": int(row["receipt"]["status"], 16),
                                   "gas": row["gas_used"], "stateUnchanged": row.get("state_unchanged"),
                                   "hash": row["receipt"]["transactionHash"]} for row in demo["transactions"]]}
        self.feedback_path = feedback_path
        self.lock = Lock()

    def cli(self, operation, text):
        result = subprocess.run([*self.command, operation], input=text.encode("utf-8"),
                                capture_output=True, timeout=15, check=False, **self.process_options)
        return {"exitCode": result.returncode, "output": result.stdout.decode("utf-8", "replace"),
                "diagnostic": result.stderr.decode("utf-8", "replace").strip()}

    def solve(self, matrix):
        if not isinstance(matrix, list) or not 1 <= len(matrix) <= 32:
            raise ValueError("Use between 1 and 32 rows")
        rows = len(matrix)
        cols = len(matrix[0]) if isinstance(matrix[0], list) else 0
        if not rows <= cols <= 32 or any(not isinstance(row, list) or len(row) != cols for row in matrix):
            raise ValueError("Use a rectangular matrix with rows ≤ columns ≤ 32")
        for row in matrix:
            for value in row:
                if (not isinstance(value, str) or not re.fullmatch(r"-?[0-9]{1,19}", value)
                        or not -(2 ** 63) <= int(value) < 2 ** 63):
                    raise ValueError("Each cost must be a signed 64-bit decimal integer")
        wire = f"FEASSIGN 1\n{rows} {cols}\n" + "\n".join(" ".join(row) for row in matrix) + "\n"
        result = self.cli("solve", wire)
        if result["exitCode"] == 0:
            proof = certificate_fields(result["output"])
            verification = self.cli("verify", result["output"])
            result.update(proof=proof, verification=verification)
        return result

    def verify(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Paste a FeAssign certificate first")
        if len(text.encode("utf-8")) > 131072:
            raise ValueError("The certificate exceeds 131072 bytes")
        result = self.cli("verify", text)
        if result["exitCode"] == 0:
            result["proof"] = certificate_fields(text)
        return result

    def notes(self):
        with self.lock:
            if not self.feedback_path.exists():
                return []
            return [json.loads(line) for line in self.feedback_path.read_text(encoding="utf-8").splitlines()]

    def save_note(self, topic, text):
        if not isinstance(topic, str) or topic not in NOTE_TOPICS or not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
            raise ValueError("Choose a topic and write a note of 1–4000 characters")
        note = {"id": uuid4().hex, "recordedUtc": datetime.now(timezone.utc).isoformat(),
                "sourceCommit": self.commit, "topic": topic, "text": text.strip()}
        with self.lock:
            with self.feedback_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(note, ensure_ascii=False) + "\n")
        return note


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(20)

    def response(self, status, content, kind, disposition=None):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        self.wfile.write(content)

    def json(self, status, payload):
        self.response(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def local_host(self):
        return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        review = self.server.review
        if not self.local_host():
            return self.json(403, {"error": "Open the workspace on this device"})
        if self.path in ASSETS:
            name, mime = ASSETS[self.path]
            return self.response(200, (STATIC / name).read_bytes(), mime)
        if self.path == "/api/meta":
            return self.json(200, review.meta)
        if self.path == "/api/feedback":
            return self.json(200, {"notes": review.notes()})
        if self.path == "/evidence/package" and review.package:
            return self.response(200, review.package.read_bytes(), "application/zip", f'attachment; filename="{review.package.name}"')
        if self.path.startswith("/evidence/"):
            data = review.files.get(self.path.removeprefix("/evidence/"))
            if data:
                return self.response(200, data, "text/plain; charset=utf-8")
        self.json(404, {"error": "Page not found"})

    def do_POST(self):
        if not self.local_host() or self.headers.get("Origin") != "http://" + self.headers.get("Host", ""):
            return self.json(403, {"error": "Open this workspace in its own browser tab"})
        if self.headers.get_content_type() != "application/json":
            return self.json(415, {"error": "Send a JSON request"})
        review = self.server.review
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 800000:
                return self.json(413, {"error": "Request size is outside the allowed range"})
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object")
            if self.path == "/api/solve":
                return self.json(200, review.solve(body.get("matrix")))
            if self.path == "/api/verify":
                return self.json(200, review.verify(body.get("certificate")))
            if self.path == "/api/feedback":
                return self.json(201, review.save_note(body.get("topic"), body.get("text")))
            self.json(404, {"error": "Action not found"})
        except (ValueError, UnicodeError) as error:
            self.json(400, {"error": str(error)})
        except subprocess.TimeoutExpired:
            self.json(504, {"error": "Fe did not finish within 15 seconds"})
        except OSError:
            self.json(500, {"error": "Local execution or storage failed. See the server log."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--run-dir", type=Path, default=SOURCE / "target/repro-01")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--feedback-file", type=Path)
    parser.add_argument("--wsl-distro")
    args = parser.parse_args()
    run = args.run_dir.resolve()
    feedback = args.feedback_file or run.parent / "workbench-feedback.jsonl"
    review = Review(run, args.packet, feedback, args.wsl_distro)
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        server.review = review
        print(f"FeAssign review workspace: http://127.0.0.1:{server.server_port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
