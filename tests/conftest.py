from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path


def _ensure_writable(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def pytest_configure(config) -> None:
    root = Path.cwd() / ".pytest_tmp_runtime"
    run_root = root / str(int(time.time() * 1000))
    tmp_root = run_root / "tmp"
    base_root = run_root / "basetemp"

    _ensure_writable(tmp_root)
    _ensure_writable(base_root)

    os.environ["TMP"] = str(tmp_root)
    os.environ["TEMP"] = str(tmp_root)
    tempfile.tempdir = str(tmp_root)

    # Override pytest.ini basetemp to avoid stale ACL/permission issues.
    config.option.basetemp = str(base_root)

