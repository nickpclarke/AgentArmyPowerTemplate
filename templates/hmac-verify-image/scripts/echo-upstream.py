"""Tiny echo upstream used by the hmac-verify doctor.

Records the body of the last POST to GET /last and supports POST /reset to
clear it. Stdlib-only so we can run it inside the same hmac-verify image
without adding any deps. The doctor uses /last to assert that a verified
request actually made it through the sidecar (proves "accepts-good-sig"
isn't a false PASS — i.e. that proxying really happened).
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_last: dict[str, object] = {"body": "", "headers": {}}


class Handler(BaseHTTPRequestHandler):
    def _respond(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003 — stdlib signature
        # Quieter than the default — the doctor's PASS/FAIL lines are the signal.
        pass

    def do_GET(self) -> None:  # noqa: N802 — stdlib signature
        if self.path == "/last":
            import json

            self._respond(200, json.dumps(_last).encode())
        elif self.path == "/livez":
            self._respond(200, b'{"ok":true}')
        else:
            self._respond(404, b'{"error":"not found"}')

    def do_POST(self) -> None:  # noqa: N802 — stdlib signature
        if self.path == "/reset":
            _last["body"] = ""
            _last["headers"] = {}
            self._respond(200, b'{"reset":true}')
            return
        # Anything else — record + 200.
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
        _last["body"] = body
        _last["headers"] = dict(self.headers.items())
        self._respond(200, b'{"echo":"ok"}')


def main() -> None:
    import os

    port = int(os.getenv("ECHO_PORT", "8085"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"echo-upstream listening on 0.0.0.0:{port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
