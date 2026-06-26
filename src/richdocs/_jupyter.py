"""Local Jupyter launcher for live-code blocks (dev only).

Ported from the former ``docs/hooks/jupyter_serve.py`` into a config-driven
class. During ``mkdocs serve`` it runs a tiny helper on 127.0.0.1:<port> so the
browser can spawn a Jupyter server (via the configured launcher script) without
restarting the build, and mirrors those routes on the MkDocs dev-server origin.
"""

from __future__ import annotations

import json
import logging
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

log = logging.getLogger("mkdocs.plugins.richdocs")

#: Neutral route prefix exposed by the dev helper (no project name).
LAUNCHER_PREFIX = "/__richdocs/jupyter"

# `mkdocs serve` reloads config (and plugin instances) on every rebuild, so the
# helper HTTP server is a module-level singleton keyed by port; requests are
# routed to whichever launcher instance is current.
_HELPER_SERVERS: dict[int, ThreadingHTTPServer] = {}
_HELPER_THREADS: dict[int, threading.Thread] = {}
_CURRENT_LAUNCHER: dict[int, JupyterLauncher] = {}

# Set once per process from ``on_startup`` (which, unlike ``on_config``, does not
# re-run on each serve rebuild).
_SERVE_MODE = False


def note_command(command: str) -> None:
    """Record whether MkDocs is running under ``serve`` (dev) vs ``build``."""
    global _SERVE_MODE
    _SERVE_MODE = command == "serve"


def _client_is_local(environ: dict[str, Any]) -> bool:
    addr = environ.get("REMOTE_ADDR") or ""
    return addr in {"127.0.0.1", "::1"} or addr.startswith("127.")


def _cors_headers(environ: dict[str, Any]) -> list[tuple[str, str]]:
    origin = environ.get("HTTP_ORIGIN")
    allow_origin = origin if origin and ("localhost" in origin or "127.0.0.1" in origin) else "*"
    return [
        ("Access-Control-Allow-Origin", allow_origin),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]


def _json_response(start_response: Any, status: str, payload: dict[str, Any], environ: dict[str, Any]) -> list[bytes]:
    body = json.dumps(payload).encode()
    headers = [("Content-Type", "application/json"), ("Content-Length", str(len(body)))]
    headers.extend(_cors_headers(environ))
    start_response(status, headers)
    return [body]


class JupyterLauncher:
    """Owns the dev helper server and the spawned Jupyter process."""

    def __init__(
        self,
        *,
        jupyter_url: str,
        token: str,
        launcher_port: int,
        launcher_script: Path | None,
        cwd: Path,
    ) -> None:
        self.base_url = jupyter_url.rstrip("/")
        self.token = token
        self.port = launcher_port
        self.script = launcher_script
        self.cwd = cwd

        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    # -- jupyter process --------------------------------------------------

    def _jupyter_running(self) -> bool:
        url = f"{self.base_url}/api?token={self.token}"
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def _spawn_jupyter(self) -> tuple[bool, str]:
        if self.script is None or not self.script.is_file():
            return False, "missing_script"
        with self._lock:
            if self._jupyter_running():
                return True, "running"
            if self._process is not None and self._process.poll() is None:
                return True, "starting"
            try:
                self._process = subprocess.Popen(
                    ["bash", str(self.script)],
                    cwd=str(self.cwd),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )
            except OSError as exc:
                log.error("richdocs: failed to start docs Jupyter: %s", exc)
                return False, "spawn_failed"
            return True, "spawned"

    # -- request handling -------------------------------------------------

    def handle_request(self, environ: dict[str, Any], start_response: Any) -> list[bytes] | None:
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "GET")

        if not path.startswith(LAUNCHER_PREFIX):
            return None
        if not _client_is_local(environ):
            return _json_response(start_response, "403 Forbidden", {"ok": False, "error": "local_only"}, environ)
        if method == "OPTIONS":
            start_response("204 No Content", _cors_headers(environ))
            return [b""]
        if path == f"{LAUNCHER_PREFIX}/status" and method == "GET":
            return _json_response(
                start_response,
                "200 OK",
                {
                    "launcher": True,
                    "running": self._jupyter_running(),
                    "script": str(self.script) if self.script else None,
                },
                environ,
            )
        if path == f"{LAUNCHER_PREFIX}/start" and method == "POST":
            if self._jupyter_running():
                return _json_response(start_response, "200 OK", {"ok": True, "state": "running"}, environ)
            ok, state = self._spawn_jupyter()
            status = "200 OK" if ok else "503 Service Unavailable"
            return _json_response(start_response, status, {"ok": ok, "state": state}, environ)
        return _json_response(start_response, "404 Not Found", {"ok": False, "error": "not_found"}, environ)

    # -- helper http server ----------------------------------------------

    def _ensure_helper_server(self) -> None:
        # Route this port's requests to the current (latest) launcher instance.
        _CURRENT_LAUNCHER[self.port] = self
        if self.port in _HELPER_SERVERS:
            self._httpd = _HELPER_SERVERS[self.port]
            return

        port = self.port  # captured so the handler routes to the current launcher

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                log.debug(format, *args)

            def _dispatch(self) -> None:
                environ = {
                    "REQUEST_METHOD": self.command,
                    "PATH_INFO": urllib.parse.urlparse(self.path).path,
                    "REMOTE_ADDR": self.client_address[0],
                    "HTTP_ORIGIN": self.headers.get("Origin", ""),
                }

                def start_response(status: str, headers: list[tuple[str, str]]) -> None:
                    self.send_response(int(status.split()[0]))
                    for key, value in headers:
                        self.send_header(key, value)
                    self.end_headers()

                launcher = _CURRENT_LAUNCHER.get(port)
                handled = launcher.handle_request(environ, start_response) if launcher else None
                if handled is None:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"ok":false,"error":"not_found"}')
                    return
                for chunk in handled:
                    self.wfile.write(chunk)

            def do_GET(self) -> None:
                self._dispatch()

            def do_POST(self) -> None:
                self._dispatch()

            def do_OPTIONS(self) -> None:
                self._dispatch()

        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", self.port), _Handler)
        except OSError as exc:
            log.warning("richdocs: could not start Jupyter launcher on port %s: %s", self.port, exc)
            return
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        _HELPER_SERVERS[self.port] = httpd
        _HELPER_THREADS[self.port] = thread
        self._httpd = httpd
        log.info(
            "richdocs live-code Jupyter launcher at http://127.0.0.1:%s%s/start",
            self.port,
            LAUNCHER_PREFIX,
        )

    def _stop_helper_server(self) -> None:
        httpd = _HELPER_SERVERS.pop(self.port, None)
        _CURRENT_LAUNCHER.pop(self.port, None)
        self._httpd = None
        if httpd is None:
            return
        httpd.shutdown()
        httpd.server_close()
        thread = _HELPER_THREADS.pop(self.port, None)
        if thread is not None:
            thread.join(timeout=2)

    def _wrap_mkdocs_server(self, server: Any) -> Any:
        original = server.serve_request

        def serve_request(environ: dict[str, Any], start_response: Any) -> Any:
            handled = self.handle_request(environ, start_response)
            if handled is not None:
                return handled
            return original(environ, start_response)

        server.set_app(serve_request)
        return server

    # -- mkdocs lifecycle hooks (delegated by the plugin) ----------------

    def on_post_build(self) -> None:
        if _SERVE_MODE:
            self._ensure_helper_server()

    def on_serve(self, server: Any) -> Any:
        self._ensure_helper_server()
        self._wrap_mkdocs_server(server)
        log.info("richdocs live-code Jupyter launcher also on the MkDocs dev server at %s/start", LAUNCHER_PREFIX)
        return server

    def on_shutdown(self) -> None:
        self._stop_helper_server()
