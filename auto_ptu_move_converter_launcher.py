from __future__ import annotations

import contextlib
import json
import os
import socket
import socketserver
import sys
import threading
import time
import traceback
import webbrowser
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from auto_ptu.tools.move_converter import LocalModelConfig, convert_to_move, request_from_payload


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def _ui_root() -> Path:
    candidates = [
        _bundle_root() / "AutoPTUMoveConverter",
        Path(__file__).resolve().parent / "auto_ptu" / "api" / "static" / "AutoPTUMoveConverter",
        Path(__file__).resolve().parent / "dist" / "AutoPTUMoveConverter",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _portable_state_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "portable_data"
    return Path.home() / ".autoptu-move-converter"


def _log_path() -> Path:
    return _portable_state_root() / "move_converter_launcher.log"


def _write_log(message: str) -> None:
    path = _log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(message, encoding="utf-8")
    except Exception:
        pass


def _pick_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _read_json(url: str, headers: dict[str, str] | None = None) -> dict:
    request = Request(url, method="GET")
    for key, value in (headers or {}).items():
        if value:
            request.add_header(key, value)
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload if isinstance(payload, dict) else {}


def _test_model_connection(config: LocalModelConfig) -> dict[str, object]:
    provider = (config.provider or "ollama").strip().lower()
    model = (config.model or "").strip()
    if provider == "ollama":
        base_url = (config.base_url or "http://127.0.0.1:11434").rstrip("/")
        payload = _read_json(f"{base_url}/api/tags")
        models = payload.get("models") if isinstance(payload, dict) else []
        names = {
            str(entry.get("name") or "").strip()
            for entry in models
            if isinstance(entry, dict) and str(entry.get("name") or "").strip()
        }
        installed = not model or model in names or any(name.split(":")[0] == model for name in names)
        detail = f"Connected to Ollama at {base_url}."
        if model:
            detail += " Model is installed." if installed else " Server responded, but that model is not installed."
        return {
            "ok": True,
            "provider": "ollama",
            "base_url": base_url,
            "model": model,
            "model_available": installed,
            "detail": detail,
            "models": sorted(names),
        }
    base_url = (config.base_url or "http://127.0.0.1:8000").rstrip("/")
    headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
    payload = _read_json(f"{base_url}/v1/models", headers=headers)
    models = payload.get("data") if isinstance(payload, dict) else []
    names = {
        str(entry.get("id") or "").strip()
        for entry in models
        if isinstance(entry, dict) and str(entry.get("id") or "").strip()
    }
    available = not model or model in names
    detail = f"Connected to OpenAI-compatible endpoint at {base_url}."
    if model:
        detail += " Model is available." if available else " Server responded, but that model was not listed."
    return {
        "ok": True,
        "provider": "openai-compatible",
        "base_url": base_url,
        "model": model,
        "model_available": available,
        "detail": detail,
        "models": sorted(names),
    }


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=str(_ui_root()), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._write_json(200, {"ok": True})
            return
        if self.path in {"/", ""}:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path not in {"/api/convert", "/api/test-model"}:
            self._write_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            payload = json.loads(self.rfile.read(length).decode("utf-8") if length > 0 else "{}")
            payload = payload if isinstance(payload, dict) else {}
            if self.path == "/api/test-model":
                local_model_payload = payload.get("local_model") or {}
                config = LocalModelConfig(
                    enabled=bool(local_model_payload.get("enabled", False)),
                    provider=str(local_model_payload.get("provider") or "ollama"),
                    model=str(local_model_payload.get("model") or ""),
                    base_url=str(local_model_payload.get("base_url") or ""),
                    api_key=str(local_model_payload.get("api_key") or ""),
                    temperature=float(local_model_payload.get("temperature", 0.2) or 0.2),
                )
                result = _test_model_connection(config)
                self._write_json(200, result)
                return
            request = request_from_payload(payload)
            result = convert_to_move(request)
            self._write_json(200, result)
        except Exception as exc:
            self._write_json(
                400,
                {
                    "error": "request_failed",
                    "detail": str(exc),
                },
            )


def _serve(server: socketserver.TCPServer) -> None:
    server.serve_forever(poll_interval=0.2)


def _wait_for_server(url: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(f"{url}/api/health", timeout=1):
                return True
        except URLError:
            time.sleep(0.2)
    return False


def main() -> int:
    port = _pick_port()
    url = f"http://127.0.0.1:{port}"
    try:
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.ThreadingTCPServer(("127.0.0.1", port), _Handler)
    except Exception:
        _write_log(traceback.format_exc())
        return 1
    thread = threading.Thread(target=_serve, args=(server,), daemon=True)
    thread.start()
    try:
        if not _wait_for_server(url):
            _write_log("Server did not become ready in time.")
            return 1
        webbrowser.open(url, new=1)
        while thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception:
        _write_log(traceback.format_exc())
        return 1
    finally:
        with contextlib.suppress(Exception):
            server.shutdown()
        with contextlib.suppress(Exception):
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
