"""Helpers for writing timestamped CLI session entries."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
SESSION_LOG_PATH = ROOT / "SESSION_LOG.md"

logger = logging.getLogger(__name__)

_HEADER = "# Auto PTU Session Log\n\n"


def _normalize_tags(tags: Sequence[str] | None) -> str:
    if not tags:
        return "(none)"
    cleaned = {tag.strip() for tag in tags if tag and tag.strip()}
    if not cleaned:
        return "(none)"
    return ", ".join(sorted(cleaned, key=str.lower))


def _ensure_header(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_HEADER, encoding="utf-8")


def _format_entry(
    *,
    timestamp: datetime,
    mode: str,
    campaign: str,
    team_size: int,
    weather: str | None,
    random_csv: bool,
    tags: Sequence[str] | None,
    seed: int | None,
) -> str:
    stamp = timestamp.strftime("%Y-%m-%d %H:%M:%S %Z").strip()
    headline = f"## {stamp} — {mode.strip().title() or 'Session'}"
    body = [
        f"- Campaign: {campaign}",
        f"- Team size: {team_size}",
        f"- Weather: {weather or 'default'}",
        f"- Random CSV: {'yes' if random_csv else 'no'}",
        f"- Tags: {_normalize_tags(tags)}",
    ]
    if seed is not None:
        body.append(f"- Seed: {seed}")
    return "\n".join([headline, *body])


def log_session(
    *,
    mode: str,
    campaign: str,
    team_size: int,
    random_csv: bool,
    tags: Sequence[str] | None = None,
    weather: str | None = None,
    seed: int | None = None,
) -> None:
    """Append a human-readable entry to SESSION_LOG.md."""
    try:
        _ensure_header(SESSION_LOG_PATH)
        entry = _format_entry(
            timestamp=datetime.now(timezone.utc),
            mode=mode,
            campaign=campaign,
            team_size=team_size,
            weather=weather,
            random_csv=random_csv,
            tags=tags,
            seed=seed,
        )
        with SESSION_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(entry)
            handle.write("\n\n")
    except OSError as exc:  # pragma: no cover - filesystem issues shouldn't crash CLI
        logger.debug("Unable to write session log: %s", exc)


__all__ = ["log_session", "SESSION_LOG_PATH"]
