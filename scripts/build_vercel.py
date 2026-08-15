"""Build the Career client without shipping its build-only Node dependencies."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "career_web"


def main() -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise RuntimeError("npm is required to build the Career client.")
    subprocess.run([npm, "--prefix", str(WEB_ROOT), "ci"], cwd=ROOT, check=True)
    subprocess.run([npm, "--prefix", str(WEB_ROOT), "run", "build"], cwd=ROOT, check=True)
    shutil.rmtree(WEB_ROOT / "node_modules", ignore_errors=True)


if __name__ == "__main__":
    main()
