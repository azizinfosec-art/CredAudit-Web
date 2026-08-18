from __future__ import annotations

import cgi
import argparse
import json
import shutil
import sys
import tempfile
import traceback
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
ENGINE_DIR = ROOT / "engine"
UPLOAD_ROOT = ROOT / ".credaudit_web"

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from credaudit import scan  # noqa: E402


CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".ico": "image/x-icon",
}


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _safe_extract_zip(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise ValueError("ZIP contains an unsafe path")
        archive.extractall(destination)


def _save_uploads(form: cgi.FieldStorage, destination: Path) -> list[str]:
    saved: list[str] = []
    fields = form["files"] if "files" in form else []
    if not isinstance(fields, list):
        fields = [fields]

    for field in fields:
        if not getattr(field, "filename", None):
            continue
        filename = Path(field.filename).name
        target = destination / filename
        with target.open("wb") as handle:
            shutil.copyfileobj(field.file, handle)
        saved.append(filename)

        if target.suffix.lower() == ".zip":
            extract_dir = destination / f"{target.stem}_extracted"
            extract_dir.mkdir(exist_ok=True)
            _safe_extract_zip(target, extract_dir)

    pasted = form.getfirst("pasted", "")
    if pasted.strip():
        target = destination / "pasted.txt"
        target.write_text(pasted, encoding="utf-8")
        saved.append(target.name)

    return saved


class CredAuditHandler(BaseHTTPRequestHandler):
    server_version = "CredAuditWeb/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            path = "/static/index.html"
        if path == "/api/health":
            _json_response(self, 200, {"ok": True, "engine": "credaudit"})
            return

        file_path = (ROOT / path.lstrip("/")).resolve()
        static_root = (ROOT / "static").resolve()
        if not str(file_path).startswith(str(static_root)) or not file_path.is_file():
            self.send_error(404)
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(file_path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/scan":
            self.send_error(404)
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            _json_response(self, 400, {"error": "Expected multipart/form-data"})
            return

        UPLOAD_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="scan_", dir=UPLOAD_ROOT) as tmp:
            scan_dir = Path(tmp)
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": content_type,
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                },
            )

            try:
                saved = _save_uploads(form, scan_dir)
                if not saved:
                    _json_response(self, 400, {"error": "Upload at least one file or paste text to scan."})
                    return

                mode = form.getfirst("mode", "fast")
                sensitivity = int(form.getfirst("sensitivity", "2"))
                min_confidence_raw = form.getfirst("min_confidence", "")
                min_confidence = int(min_confidence_raw) if min_confidence_raw else None
                safe = form.getfirst("safe", "true") == "true"

                result = scan(
                    str(scan_dir),
                    mode=mode,
                    sensitivity=sensitivity,
                    min_confidence=min_confidence,
                    safe=safe,
                    no_cache=True,
                    output_dir=str(scan_dir / "out"),
                )

                _json_response(
                    self,
                    200,
                    {
                        "counts": result.counts,
                        "elapsed_sec": result.elapsed_sec,
                        "exit_code": result.exit_code,
                        "files_scanned": result.files_scanned,
                        "findings": result.findings,
                        "inputs": saved,
                        "version": result.version,
                    },
                )
            except Exception as exc:
                traceback.print_exc()
                _json_response(self, 500, {"error": str(exc)})

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CredAudit Web")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    port = args.port
    server = ThreadingHTTPServer(("127.0.0.1", port), CredAuditHandler)
    print(f"CredAudit Web running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
