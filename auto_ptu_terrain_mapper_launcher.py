from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn


_HOST = "127.0.0.1"
_PATH = "/terrain-mapper"


def _repo_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "_internal"
    return Path(__file__).resolve().parent


def _find_port(host: str, start: int = 8011, limit: int = 40) -> int:
    for port in range(start, start + limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError("No free port available for AutoPTU Terrain Mapper.")


def _runtime_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "portable_data"
    return Path.home() / ".autoptu-terrain-mapper"


def _configure_env() -> None:
    repo_root = _repo_root()
    os.environ.setdefault("AUTO_PTU_REPORTS_DIR", str(_runtime_data_dir() / "reports"))
    os.environ.setdefault("AUTOPTU_WEB_ONLY", "1")
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _open_browser(url: str) -> None:
    def _worker() -> None:
        time.sleep(1.0)
        webbrowser.open(url, new=1)
    threading.Thread(target=_worker, daemon=True).start()


def main() -> None:
    _configure_env()
    port = _find_port(_HOST)
    url = f"http://{_HOST}:{port}{_PATH}"
    _open_browser(url)
    uvicorn.run("auto_ptu.api.server:app", host=_HOST, port=port, reload=False, log_level="info")


if __name__ == "__main__":
    main()
