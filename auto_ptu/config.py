"""Centralized filesystem helpers for Auto PTU."""
from __future__ import annotations

import os
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", PACKAGE_ROOT.parent))
_SERVERLESS_PROJECT = str(PROJECT_ROOT).replace("\\", "/").startswith("/var/task")
SERVERLESS_RUNTIME = _SERVERLESS_PROJECT
RUNTIME_ROOT = Path(
    os.environ.get("AUTO_PTU_RUNTIME_ROOT")
    or ("/tmp/autoptu" if _SERVERLESS_PROJECT else "")
    or (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT)
)
DATA_DIR = PACKAGE_ROOT / "data"
CAMPAIGNS_DIR = DATA_DIR / "campaigns"
DEFAULT_CAMPAIGN_FILE = CAMPAIGNS_DIR / "demo_campaign.json"


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name)
    if not raw:
        return None
    return Path(raw).expanduser()


def _pick_existing_path(*candidates: Path | None) -> Path:
    existing = [candidate for candidate in candidates if candidate and candidate.exists()]
    if existing:
        return existing[0]
    for candidate in candidates:
        if candidate is not None:
            return candidate
    return PROJECT_ROOT


FILES_DIR = _pick_existing_path(_env_path("AUTO_PTU_FILES_DIR"), RUNTIME_ROOT / "files", PROJECT_ROOT / "files")
# Writable runtime overrides must win even before their directory exists. Serverless
# filesystems expose the bundled project tree as an existing but read-only path.
REPORTS_DIR = (
    _env_path("AUTO_PTU_REPORTS_DIR")
    or ((RUNTIME_ROOT / "reports") if os.environ.get("VERCEL") or _SERVERLESS_PROJECT else None)
    or _pick_existing_path(RUNTIME_ROOT / "reports", PROJECT_ROOT / "reports")
)
IMPLEMENTATION_DIR = _pick_existing_path(
    _env_path("AUTO_PTU_IMPLEMENTATION_DIR"),
    RUNTIME_ROOT / "IMPLEMENTATION FILES",
    PROJECT_ROOT / "IMPLEMENTATION FILES",
)
FOUNDRY_DIR = _pick_existing_path(_env_path("AUTO_PTU_FOUNDRY_DIR"), RUNTIME_ROOT / "Foundry", PROJECT_ROOT / "Foundry")
PTU_DATABASE_DIR = _pick_existing_path(
    _env_path("AUTO_PTU_PTU_DATABASE_DIR"),
    RUNTIME_ROOT / "PTUDatabase-main",
    PROJECT_ROOT / "PTUDatabase-main",
)


def ensure_data_dirs() -> None:
    """Make sure bundled data folders exist when package is copied around."""
    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_path(path: str | Path) -> Path:
    """Return an absolute path, expanding user shortcuts."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p


ensure_data_dirs()
