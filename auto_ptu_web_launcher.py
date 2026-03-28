from __future__ import annotations

import time
import webbrowser
from dataclasses import dataclass
import os
import socket
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
import threading
import traceback
import sys

from auto_ptu.api import server as _server  # Ensure FastAPI app is bundled.

_DEFAULT_WEB_PORT = 8010


@dataclass
class _ServerRuntime:
    error: str = ""


def main() -> int:
    port = _pick_web_port()
    url = f"http://127.0.0.1:{port}"
    if _is_server_responding(url):
        _open_browser_once(url)
        return 0

    runtime = _ServerRuntime()
    server_thread = threading.Thread(target=_run_server, args=(runtime, port), daemon=True)
    server_thread.start()
    try:
        if not _wait_for_server(url, timeout=10):
            if runtime.error:
                _write_log(runtime.error)
            _print_startup_failure(runtime.error or "Server did not become ready in time.")
            return 1
        _open_browser_once(url)
        while server_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception:
        _write_log("Launcher crashed unexpectedly.\n" + traceback.format_exc())
        _print_startup_failure("Launcher crashed unexpectedly.")
        return 1
    return 0


def _open_browser_once(url: str) -> None:
    lock = _lock_path()
    last = _read_lock_timestamp(lock)
    if last is not None and time.time() - last < 600:
        return
    _write_lock_timestamp(lock)
    _wait_for_server(url, timeout=10)
    webbrowser.open(url, new=1)


def _wait_for_server(url: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _is_server_responding(url):
            return True
        time.sleep(0.2)
    return False


def _is_server_responding(url: str) -> bool:
    try:
        with urlopen(url, timeout=1):
            return True
    except URLError:
        return False


def _run_server(runtime: _ServerRuntime, port: int) -> None:
    try:
        import uvicorn
    except Exception:
        runtime.error = "Failed to import uvicorn.\n" + traceback.format_exc()
        return
    try:
        uvicorn.run(
            "auto_ptu.api.server:app",
            host="127.0.0.1",
            port=port,
            log_level="info",
        )
    except Exception:
        runtime.error = "Server crashed on startup.\n" + traceback.format_exc()
        return


def _write_log(message: str) -> None:
    log_path = _log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"{message}\n", encoding="utf-8")
    except Exception:
        pass


def _log_path() -> Path:
    base = _portable_state_root()
    return base / "launcher.log"


def _print_startup_failure(reason: str = "") -> None:
    log_path = _log_path()
    print("AutoPTU failed to start the local server.")
    if reason:
        print(reason)
    if log_path.exists():
        try:
            print(f"Log: {log_path}")
            print(log_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        input("Press Enter to close...")
    except EOFError:
        # Explorer-launched one-file executables may not have a usable stdin.
        time.sleep(15)


def _lock_path() -> Path:
    base = _portable_state_root()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception:
        base = Path.home()
    return base / "browser_lock.txt"


def _portable_state_root() -> Path:
    env_root = os.environ.get("AUTO_PTU_RUNTIME_ROOT")
    if env_root:
        return Path(env_root) / "portable_data"
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "portable_data"
    return Path.home() / ".autoptu"


def _read_lock_timestamp(lock: Path) -> float | None:
    if not lock.exists():
        return None
    try:
        content = lock.read_text(encoding="utf-8").strip()
        return float(content) if content else None
    except Exception:
        return None


def _write_lock_timestamp(lock: Path) -> None:
    try:
        lock.write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass


def _pick_web_port() -> int:
    env_port = os.environ.get("AUTO_PTU_WEB_PORT", "").strip()
    if env_port:
        try:
            port = int(env_port)
        except ValueError:
            port = _DEFAULT_WEB_PORT
        else:
            if 1 <= port <= 65535:
                return port
    if _port_available(_DEFAULT_WEB_PORT):
        return _DEFAULT_WEB_PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
