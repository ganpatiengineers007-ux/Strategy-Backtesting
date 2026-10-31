"""Chhota token app (sirf stdlib). Browser se Fyers login -> token apne aap save.

Chalane ke liye .env me FYERS_REDIRECT_URI=http://127.0.0.1:8765/callback rakho (Fyers app me bhi wahi register ho).
Default sirf 127.0.0.1 par sunta hai (bahar se koi nahi pahunch sakta)."""
from __future__ import annotations

import html
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from fyers_hub.auth import flow
from fyers_hub.auth.store import load_token
from fyers_hub.settings import get_settings


def make_handler(settings):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # URL me auth_code hota hai - log nahi karna
            # Intentionally silent: auth_code would leak in logs
            pass

        def _send(self, code, body, ctype="text/html; charset=utf-8", headers=()):
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            for k, v in headers:
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urlparse(self.path)
            if u.path == "/login":
                self._send(302, "", headers=[("Location", flow.login_url(settings))])
            elif u.path == "/callback":
                try:
                    code = flow.parse_auth_code(self.path, settings)
                    flow.exchange_code(code, settings)
                    msg = "Token save ho gaya. Ye page band kar sakte ho."
                except Exception as e:  # noqa: BLE001
                    import logging
                    log = logging.getLogger("fyers_hub.auth.web")
                    log.exception("Callback error")
                    msg = f"Fail: {html.escape(str(e))}"
                self._send(200, f"<h3>{msg}</h3>")
            else:
                tok = load_token(settings.token_path)
                ok = bool(tok and tok.valid())
                left = int((tok.expires_at - time.time()) / 3600) if tok else 0
                st = f"valid (~{left} ghante)" if ok else "nahi hai / expire"
                self._send(200, f"<h2>Fyers token: {st}</h2><p><a href='/login'>Fyers login karo</a></p>")

    return H


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    s = get_settings()
    s.require_app()
    srv = ThreadingHTTPServer((host, port), make_handler(s))
    print(f"Token app: http://{host}:{port}/   (band karne ke liye Ctrl+C)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
