"""Local review interface for the validated FeAssign candidate."""

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import quote
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

if os.name == "nt":
    import msvcrt
else:
    import fcntl


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
        full = load(full_file) if full_file.is_file() else None
        demo_dir = run / "demo" if full is not None else run
        demo_file = demo_dir / "demo.json"
        demo = load(demo_file)
        marker = SOURCE / "SOURCE_COMMIT"
        if marker.is_file():
            self.commit = marker.read_text(encoding="ascii").strip()
        elif full and full.get("source_commit"):
            self.commit = full["source_commit"]
        else:
            try:
                self.commit = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"],
                                                      text=True, stderr=subprocess.DEVNULL).strip()
            except (FileNotFoundError, subprocess.CalledProcessError) as error:
                raise ValueError("Use the packet's source directory or a checkout with Git available") from error
        if not re.fullmatch(r"[0-9a-f]{40}", self.commit):
            raise ValueError("Expected the full source commit SHA")
        self.package = package
        binary = demo_dir / "native/feassign"
        binary_sha = sha(binary)
        pins = load(SOURCE / "toolchain.json")
        expected_tools = {"fe": pins["linux_amd64_asset_sha256"], "anvil": pins["anvil_linux_amd64_asset_sha256"],
                          "cast": pins["cast_linux_amd64_asset_sha256"]}
        receipts = [{"label": row["label"], "status": int(row["receipt"]["status"], 16),
                     "gas": row["gas_used"], "stateUnchanged": row.get("state_unchanged"),
                     "hash": row["receipt"]["transactionHash"]} for row in demo["transactions"]]
        if not (demo["success"] and demo["node_stopped"] and binary_sha == demo["native_executable_sha256"]
                and demo["binary_sha256"] == expected_tools and [row["status"] for row in receipts] == [1, 0, 0, 1, 0]
                and all(row["stateUnchanged"] for row in receipts if row["status"] == 0)):
            raise ValueError("Run the pinned FeAssign demo successfully before starting the workbench")
        if full is not None and not (full["success"] and len(full["records"]) == 11
                and full.get("source_commit", self.commit) == self.commit
                and all(row["exit_code"] == 0 for row in full["records"])):
            raise ValueError("The complete reproduction record failed or belongs to another commit")
        for name, digest in demo["source_hashes"].items():
            if sha(SOURCE / name) != digest or (full is not None and full["source_hashes"].get(name) != digest):
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
        self.files["run"] = (full_file if full is not None else demo_file).read_bytes()
        if package:
            with ZipFile(package) as archive:
                roots = [name for name in archive.namelist() if name.count("/") == 1 and name.endswith("/MANIFEST.json")]
                if len(roots) != 1:
                    raise ValueError("Expected a single candidate manifest in the ZIP")
                manifest = json.loads(archive.read(roots[0]))
                prefix = roots[0].removesuffix("MANIFEST.json")
                packaged_hashes = manifest["source_hashes"]
                run_hashes = full["source_hashes"] if full is not None else demo["source_hashes"]
                if manifest["source_commit"] != self.commit or any(packaged_hashes.get(n) != d for n, d in run_hashes.items()):
                    raise ValueError("Candidate package and reproduction do not match")
                members = {"guide": "HANDOFF.md"}
                if full is not None:
                    members["demo"] = "evidence/current-run/DEMO-RESULT.md"
                for key, member in members.items():
                    data = archive.read(prefix + member)
                    if hashlib.sha256(data).hexdigest() != manifest["files"][member]:
                        raise ValueError(f"Evidence hash mismatch for {key}")
                    self.files[key] = data
        text = (demo_dir / "solution.cert").read_text(encoding="ascii")
        self.meta = {"commit": self.commit, "packageSha256": sha(package) if package else None,
                     "binarySha256": binary_sha, "compiler": demo["versions"]["fe"],
                     "runMode": "full" if full is not None else "demo",
                     "stages": len(full["records"]) if full is not None else None,
                     "summary": full["observed_summary"] if full is not None else None, "certificate": text,
                     "sample": certificate_fields(text), "greedy": demo["comparison"]["row_order_greedy_total"],
                     "receipts": receipts}
        self.feedback_path = feedback_path.resolve()
        self.feedback_lock_path = self.feedback_path.with_name(self.feedback_path.name + ".lock")
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

    @contextmanager
    def locked_feedback(self):
        # The lock is separate from the append-only data, so readers and writers
        # in different workbench processes agree on a single lock byte or inode.
        with self.lock, self.feedback_lock_path.open("a+b") as file:
            if os.name == "nt":
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
            else:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX)
            yield

    def notes(self):
        with self.locked_feedback():
            if not self.feedback_path.exists():
                return []
            with self.feedback_path.open(encoding="utf-8") as file:
                return [json.loads(line) for line in file]

    def save_note(self, topic, text):
        if not isinstance(topic, str) or topic not in NOTE_TOPICS or not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
            raise ValueError("Choose a topic and write a note of 1–4000 characters")
        note = {"id": uuid4().hex, "recordedUtc": datetime.now(timezone.utc).isoformat(),
                "sourceCommit": self.commit, "topic": topic, "text": text.strip()}
        with self.locked_feedback():
            with self.feedback_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(note, ensure_ascii=False) + "\n")
        return note


class LoopbackServer(ThreadingHTTPServer):
    allow_reuse_address = os.name != "nt"
    allow_reuse_port = False

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


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
            try:
                notes = review.notes()
            except (OSError, ValueError) as error:
                self.log_error("Review notes could not be read: %s", error)
                return self.json(500, {"error": "Review notes could not be read. See the server log."})
            return self.json(200, {"notes": notes})
        if self.path == "/evidence/package" and review.package:
            name = review.package.name
            disposition = (f'attachment; filename="{name}"' if re.fullmatch(r"[A-Za-z0-9._-]+", name) else
                           "attachment; filename=\"feassign.zip\"; filename*=UTF-8''" + quote(name, safe=""))
            return self.response(200, review.package.read_bytes(), "application/zip", disposition)
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
        except OSError as error:
            self.log_error("Local execution or storage failed: %s", error)
            self.json(500, {"error": "Local execution or storage failed. See the server log."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--run-dir", type=Path, default=SOURCE / "target/repro-01",
                        help="Output of tools/demo.py or tools/reproduce.py")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--feedback-file", type=Path)
    parser.add_argument("--wsl-distro")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("Choose a port from 0 to 65535")
    run = args.run_dir.resolve()
    feedback = args.feedback_file or run.parent / "workbench-feedback.jsonl"
    try:
        review = Review(run, args.packet, feedback, args.wsl_distro)
    except (OSError, ValueError, KeyError, BadZipFile, subprocess.CalledProcessError) as error:
        parser.error(f"Could not load a completed demo or reproduction: {error}")
    try:
        server = LoopbackServer(("127.0.0.1", args.port), Handler)
    except OSError as error:
        parser.error(f"Could not listen on 127.0.0.1:{args.port}. Choose a free --port. {error}")
    with server:
        server.review = review
        print(f"FeAssign review workspace: http://127.0.0.1:{server.server_port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
