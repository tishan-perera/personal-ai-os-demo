"""Local JSON API and static desk. Standard library only."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from atrium.office import Office
from atrium.validate import ValidationError

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
MAX_BODY = 100_000

STATUS_FOR_CODE = {
    "missing_proposal": 404,
    "not_pending": 409,
    "body_too_large": 413,
}


class Holder:
    """Mutable handle so reset can replace the office under a lock."""

    def __init__(self, office: Office, quiet: bool = False) -> None:
        self.office = office
        self.quiet = quiet
        self.lock = threading.Lock()


class DeskServer(ThreadingHTTPServer):
    holder: Holder

    def __init__(
        self,
        server_address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        holder: Holder,
    ) -> None:
        self.holder = holder
        super().__init__(server_address, handler)


def make_server(office: Office, host: str, port: int, quiet: bool = False) -> DeskServer:
    holder = Holder(office, quiet=quiet)
    handler = _handler_factory(holder)
    return DeskServer((host, port), handler, holder)


def _handler_factory(holder: Holder) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            if not holder.quiet:
                print(f"atrium  {self.address_string()}  {fmt % args}")

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/favicon.ico":
                self._send(204, b"", "text/plain; charset=utf-8")
                return
            if path == "/api/health":
                with holder.lock:
                    mode = "llm" if holder.office.brain.enabled else "demo"
                self._send_json({"ok": True, "mode": mode, "product": "atrium", "fictional": True})
                return
            if path == "/api/state":
                with holder.lock:
                    payload = holder.office.state()
                self._send_json(payload)
                return
            if path in STATIC_FILES:
                name, content_type = STATIC_FILES[path]
                body = (STATIC_DIR / name).read_bytes()
                self._send(200, body, content_type)
                return
            self._send_error(404, "not_found", "That path is not part of the demo.")

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            try:
                if path == "/api/requests":
                    body = _read_json(self)
                    text = body.get("text", body.get("message"))
                    with holder.lock:
                        result = holder.office.handle(text)
                    self._send_json(result)
                    return
                if path == "/api/reset":
                    _read_optional_json(self)
                    with holder.lock:
                        _reset(holder)
                        payload = holder.office.state()
                    self._send_json(payload)
                    return
                prefix = "/api/proposals/"
                suffix = "/decision"
                if path.startswith(prefix) and path.endswith(suffix):
                    proposal_id = path[len(prefix) : -len(suffix)]
                    if not proposal_id or "/" in proposal_id:
                        self._send_error(404, "not_found", "That path is not part of the demo.")
                        return
                    body = _read_json(self)
                    with holder.lock:
                        result = holder.office.decide(
                            proposal_id,
                            body.get("decision"),
                            body.get("actor", "owner"),
                            body.get("note", ""),
                        )
                    self._send_json(result)
                    return
            except ValidationError as exc:
                self._send_error(STATUS_FOR_CODE.get(exc.code, 400), exc.code, str(exc))
                return
            self._send_error(404, "not_found", "That path is not part of the demo.")

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self._send(status, body, "application/json; charset=utf-8")

        def _send_error(self, status: int, code: str, message: str) -> None:
            self._send_json({"ok": False, "error": {"code": code, "message": message}}, status)

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if body:
                self.wfile.write(body)

    return Handler


def _reset(holder: Holder) -> None:
    current = holder.office
    holder.office = Office(brain=current.brain, clock=current.clock, on_change=current.on_change)
    if current.on_change is not None:
        current.on_change(holder.office)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    payload = _read_optional_json(handler)
    if payload is None:
        raise ValidationError("bad_json", "Expected a JSON object.")
    return payload


def _read_optional_json(handler: BaseHTTPRequestHandler) -> dict[str, Any] | None:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise ValidationError("bad_json", "Content-Length is not a number.") from exc
    if length < 0 or length > MAX_BODY:
        raise ValidationError("body_too_large", "The request body is too large.")
    if length == 0:
        return None
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("bad_json", "The body is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise ValidationError("bad_json", "The JSON body must be an object.")
    return data
