"""Helpers to load campaign definitions and convert between formats."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

from . import ptu_engine
from .config import CAMPAIGNS_DIR, DEFAULT_CAMPAIGN_FILE, resolve_path
from .data_models import CampaignSpec, MatchPlan, MatchupSpec, PokemonSpec, MoveSpec


def _load_raw(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to load YAML campaign files")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Campaign file must contain a JSON/YAML object")
    return data


def load_campaign(path: str | Path) -> CampaignSpec:
    path = resolve_path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return CampaignSpec.from_dict(_load_raw(path))


def load_builtin_campaign(name: str = "demo_campaign.json") -> CampaignSpec:
    filename = name
    if Path(filename).suffix == "":
        filename += ".json"
    path = CAMPAIGNS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Unknown built-in campaign {name}")
    return load_campaign(path)


def list_campaigns(directory: str | Path | None = None) -> Dict[str, Path]:
    root = resolve_path(directory) if directory else CAMPAIGNS_DIR
    if not root.exists():
        return {}
    out: Dict[str, Path] = {}
    for file in sorted(root.rglob("*")):
        if not file.is_file():
            continue
        if file.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue
        if file.name.startswith("_"):
            continue
        relative = file.relative_to(root)
        key = str(relative.with_suffix("")).replace("\\", "/")
        out[key] = file
    return out


def default_campaign() -> CampaignSpec:
    if DEFAULT_CAMPAIGN_FILE.exists():
        return load_campaign(DEFAULT_CAMPAIGN_FILE)
    raise FileNotFoundError("Demo campaign missing; reinstall package data")


def spec_from_engine_pokemon(mon: ptu_engine.Pokemon) -> PokemonSpec:
    return PokemonSpec(
        species=mon.species,
        level=mon.level,
        types=list(mon.types),
        hp_stat=mon.hp_stat,
        atk=mon.atk,
        defense=mon.def_,
        spatk=mon.spatk,
        spdef=mon.spdef,
        spd=mon.spd,
        name=mon.name,
        accuracy_cs=mon.accuracy_cs,
        evasion_phys=mon.evasion_bonus_phys,
        evasion_spec=mon.evasion_bonus_spec,
        evasion_spd=mon.evasion_bonus_spd,
        moves=[
            MoveSpec(
                name=m.name,
                type=m.type,
                category=m.category,
                db=m.db,
                ac=m.ac,
                range_kind=m.range_kind,
                range_value=m.range_value,
                target_kind=getattr(m, "target_kind", m.range_kind),
                target_range=getattr(m, "target_range", m.range_value),
                area_kind=getattr(m, "area_kind", None),
                area_value=getattr(m, "area_value", None),
                freq=m.freq,
                keywords=list(m.keywords),
                priority=m.priority,
                crit_range=m.crit_range,
                effects_text=m.effects_text,
            )
            for m in mon.known_moves
        ],
        items=[{"name": item.name, "slot": item.slot, "effects": item.effects} for item in mon.items],
        abilities=[
            {
                "name": ab.name,
                "hooks": [{"when": hook.when, "effect": hook.effect} for hook in ab.hooks],
            }
            for ab in mon.abilities
        ],
        statuses=[
            {"name": status.name, "kind": status.kind, "effects": status.effects, "duration": status.duration}
            for status in mon.statuses
        ],
        trainer_features=[
            {"name": tf.name, "when": tf.when, "effect": tf.effect} for tf in mon.trainer_features
        ],
        capabilities=[{"name": cap.name, "value": cap.value} for cap in mon.capabilities],
    )


def load_specs_from_excels(you_sheet: str | Path, foe_sheet: str | Path) -> Tuple[PokemonSpec, PokemonSpec]:
    parties = ptu_engine.load_party_from_excel(str(you_sheet), str(foe_sheet))
    return spec_from_engine_pokemon(parties["you"].mon), spec_from_engine_pokemon(parties["foe"].mon)


def plan_from_campaign(
    campaign: CampaignSpec,
    team_size: int = 1,
    preferred_tags: Iterable[str] | None = None,
) -> MatchPlan:
    """Convenience wrapper that delegates to AutoMatchPlanner lazily to avoid a circular import."""
    from .matchmaker import AutoMatchPlanner

    planner = AutoMatchPlanner(campaign)
    return planner.create_plan(team_size=team_size, prefer_tags=list(preferred_tags or []))


__all__ = [
    "load_campaign",
    "load_builtin_campaign",
    "list_campaigns",
    "default_campaign",
    "plan_from_campaign",
    "load_specs_from_excels",
    "spec_from_engine_pokemon",
]
