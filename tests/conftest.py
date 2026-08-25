from __future__ import annotations

import os
import random
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_REPORTS_DIR = PROJECT_ROOT / ".pytest_tmp_runtime" / "isolated_reports"

shutil.rmtree(TEST_REPORTS_DIR, ignore_errors=True)
TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("AUTO_PTU_REPORTS_DIR", str(TEST_REPORTS_DIR))


def pytest_collection_modifyitems(items) -> None:
    """Keep the trainer passive-perk scripted RNG deterministic after rolls are exhausted."""
    patched_helpers: set[type] = set()
    for item in items:
        module = getattr(item, "module", None)
        if not str(getattr(module, "__name__", "")).endswith("test_trainer_passive_perks"):
            continue
        fixed_rng = getattr(module, "_FixedRng", None)
        if not isinstance(fixed_rng, type) or fixed_rng in patched_helpers:
            continue

        def deterministic_init(self, rolls: list[int]) -> None:
            random.Random.__init__(self, 0)
            self._rolls = list(rolls)

        fixed_rng.__init__ = deterministic_init
        patched_helpers.add(fixed_rng)
