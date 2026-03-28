"""Helpers that keep generated tooling artifacts up to date."""

from __future__ import annotations

import logging
import runpy
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
ABILITY_CSV = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
ABILITY_SCRIPT = ROOT / "scripts" / "generate_ability_log.py"
ABILITY_LOG = ROOT / "ABILITY_LOG.md"


def _latest_timestamp(paths: Iterable[Path]) -> float | None:
    """Return the newest modification time among the provided paths."""
    m_times = [path.stat().st_mtime for path in paths if path.exists()]
    if not m_times:
        return None
    return max(m_times)


def ensure_ability_log() -> None:
    """Regenerate `ABILITY_LOG.md` if the source CSV or generator script were updated.

    Running the CLI/launcher now keeps the log in sync automatically, so developers
    never have to remember to call `python scripts/generate_ability_log.py`.
    """
    if not ABILITY_SCRIPT.exists():
        logger.debug("Ability log generator script missing; skipping auto-update.")
        return
    if not ABILITY_CSV.exists():
        logger.debug("CSV source for abilities missing; skipping ability log auto-update.")
        return

    source_mtime = _latest_timestamp({ABILITY_SCRIPT, ABILITY_CSV})
    log_mtime = ABILITY_LOG.stat().st_mtime if ABILITY_LOG.exists() else None
    if log_mtime is not None and source_mtime is not None and log_mtime >= source_mtime:
        return

    logger.info("Regenerating ABILITY_LOG.md because sources changed.")
    try:
        runpy.run_path(str(ABILITY_SCRIPT), run_name="__main__")
    except Exception as exc:  # pragma: no cover - safety net for logging
        logger.exception("Ability log regeneration failed: %s", exc)
