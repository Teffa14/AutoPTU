from __future__ import annotations

import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_REPORTS_DIR = PROJECT_ROOT / ".pytest_tmp_runtime" / "isolated_reports"

shutil.rmtree(TEST_REPORTS_DIR, ignore_errors=True)
TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("AUTO_PTU_REPORTS_DIR", str(TEST_REPORTS_DIR))
