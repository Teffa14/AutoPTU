"""Homebrew extension pack discovery and manifest parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExtensionPack:
    name: str
    path: Path
    priority: int
    manifest: Dict[str, Any]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_extension_manifest(path: Path) -> Optional[Dict[str, Any]]:
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def discover_extension_packs(root: Optional[Path] = None) -> List[ExtensionPack]:
    base = root or (_project_root() / "extensions")
    if not base.exists():
        return []
    packs: List[ExtensionPack] = []
    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        manifest = load_extension_manifest(entry)
        if not manifest:
            continue
        name = str(manifest.get("name") or entry.name)
        try:
            priority = int(manifest.get("priority", 0) or 0)
        except (TypeError, ValueError):
            priority = 0
        packs.append(
            ExtensionPack(
                name=name,
                path=entry,
                priority=priority,
                manifest=manifest,
            )
        )
    packs.sort(key=lambda pack: (pack.priority, pack.name.lower()))
    return packs
