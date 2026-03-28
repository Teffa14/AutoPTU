"""Roster CSV -> CampaignSpec conversion for unified encounter creation."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .csv_repository import PTUCsvRepository
from .data_loader import default_campaign
from .data_models import CampaignSpec, MatchPlan, MatchupSpec, PokemonSpec, TrainerSideSpec


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: object, default: int) -> int:
    text = _clean(value)
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def _normalize_side(value: object) -> str:
    raw = _clean(value).lower()
    if raw in {"player", "players", "ally", "allies", "you", "p1", "left"}:
        return "player"
    if raw in {"foe", "foes", "enemy", "enemies", "opponent", "opponents", "ai", "p2", "right"}:
        return "foe"
    # Allow arbitrary team labels for battle-royale style CSVs.
    slug = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return slug


def _pick_first(row: Dict[str, object], keys: Iterable[str]) -> str:
    for key in keys:
        if key in row:
            value = _clean(row.get(key))
            if value:
                return value
    return ""


def _collect_moves(row: Dict[str, object]) -> List[str]:
    indexed_moves: List[Tuple[int, str]] = []
    for key, raw_value in row.items():
        lower = str(key or "").strip().lower()
        match = re.fullmatch(r"(?:move|moves)_?(\d+)", lower)
        if not match:
            continue
        value = _clean(raw_value)
        if not value:
            continue
        indexed_moves.append((int(match.group(1)), value))
    if indexed_moves:
        indexed_moves.sort(key=lambda entry: entry[0])
        return [value for _, value in indexed_moves]
    joined = _pick_first(row, ("moves", "move_list"))
    if not joined:
        return []
    return [token.strip() for token in joined.replace(";", ",").split(",") if token.strip()]


def _normalize_move_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", _clean(value).lower())


def _collect_move_sources(row: Dict[str, object], moves: List[str]) -> Dict[str, str]:
    if not moves:
        return {}
    indexed_sources: List[str] = []
    for index in range(1, len(moves) + 1):
        value = _pick_first(row, (f"move_source{index}", f"move_source_{index}", f"movesource{index}", f"movesource_{index}"))
        indexed_sources.append(value)
    sources: Dict[str, str] = {}
    for move_name, source_name in zip(moves, indexed_sources):
        move_key = _normalize_move_key(move_name)
        source_value = _clean(source_name)
        if move_key and source_value:
            sources[move_key] = source_value
    return sources


def _collect_named_values(row: Dict[str, object], prefixes: Iterable[str], joined_keys: Iterable[str], limit: int) -> List[str]:
    values: List[str] = []
    prefix_set = tuple(str(prefix).lower() for prefix in prefixes)
    for key in row.keys():
        lower = str(key or "").strip().lower()
        if any(re.fullmatch(rf"{re.escape(prefix)}(?:_?\d+)?", lower) for prefix in prefix_set):
            value = _clean(row.get(key))
            if value:
                values.append(value)
    if values:
        return values[:limit]
    joined = _pick_first(row, joined_keys)
    if not joined:
        return []
    return [token.strip() for token in joined.replace(";", ",").split(",") if token.strip()][:limit]


def _normalize_stat_mode(value: object) -> str:
    raw = _clean(value).lower()
    return "post_nature" if raw == "post_nature" else "pre_nature"


def _split_semicolon_list(value: object) -> List[str]:
    text = _clean(value)
    if not text:
        return []
    return [token.strip() for token in text.split(";") if token.strip()]


def _collect_poke_edge_choices(row: Dict[str, object]) -> Dict[str, object]:
    return {
        "accuracy_training": _split_semicolon_list(_pick_first(row, ("poke_edge_accuracy_training", "edge_accuracy_training", "accuracy_training"))),
        "advanced_connection": _split_semicolon_list(_pick_first(row, ("poke_edge_advanced_connection", "edge_advanced_connection", "advanced_connection"))),
        "underdog_lessons": {
            "evolution": _pick_first(row, ("poke_edge_underdog_evolution", "edge_underdog_evolution", "underdog_evolution")),
            "moves": _split_semicolon_list(_pick_first(row, ("poke_edge_underdog_moves", "edge_underdog_moves", "underdog_moves")))[:3],
        },
    }


@dataclass
class _RosterRow:
    side: str
    slot: int
    species: str
    level: int
    nickname: str = ""
    abilities: List[str] = None  # type: ignore[assignment]
    items: List[str] = None  # type: ignore[assignment]
    poke_edges: List[str] = None  # type: ignore[assignment]
    nature: str = ""
    stat_mode: str = "pre_nature"
    tutor_points: int = 0
    moves: List[str] = None  # type: ignore[assignment]
    move_sources: Dict[str, str] = None  # type: ignore[assignment]
    poke_edge_choices: Dict[str, object] = None  # type: ignore[assignment]
    stats: Dict[str, int] = None  # type: ignore[assignment]
    order: int = 0


def _side_identifier(side: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", side.lower()).strip("-") or "side"
    candidate = base
    counter = 2
    while candidate in used:
        candidate = f"{base}-{counter}"
        counter += 1
    used.add(candidate)
    return candidate


def _primary_side_label(rows: List[_RosterRow]) -> str:
    preferred = {"player", "players", "ally", "allies", "you", "p1", "left"}
    for row in rows:
        if row.side in preferred:
            return row.side
    return rows[0].side


def _parse_rows(csv_text: str, default_level: int) -> List[_RosterRow]:
    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("Roster CSV is missing header row.")
    rows: List[_RosterRow] = []
    for idx, raw in enumerate(reader):
        row = {str(k or "").strip().lower(): (v if v is not None else "") for k, v in (raw or {}).items()}
        species = _pick_first(row, ("species", "pokemon", "name"))
        if not species:
            continue
        side = _normalize_side(_pick_first(row, ("side", "team", "faction")))
        if not side:
            raise ValueError(f"Row {idx + 2}: side must be one of player/foe.")
        slot_value = _as_int(_pick_first(row, ("slot", "index", "position")), idx + 1)
        level_value = _as_int(_pick_first(row, ("level", "lvl")), default_level)
        level_value = max(1, min(100, level_value))
        stats = {
            "hp": _as_int(_pick_first(row, ("hp", "hp_stat", "hpstat")), 0),
            "atk": _as_int(_pick_first(row, ("atk", "attack")), 0),
            "def": _as_int(_pick_first(row, ("def", "defense")), 0),
            "spatk": _as_int(_pick_first(row, ("spatk", "sp_atk", "special_attack", "specialattack", "spa")), 0),
            "spdef": _as_int(_pick_first(row, ("spdef", "sp_def", "special_defense", "specialdefense", "spdf")), 0),
            "spd": _as_int(_pick_first(row, ("spd", "speed")), 0),
        }
        moves = _collect_moves(row)
        rows.append(
            _RosterRow(
                side=side,
                slot=max(1, slot_value),
                species=species,
                level=level_value,
                nickname=_pick_first(row, ("nickname", "name", "alias")),
                abilities=_collect_named_values(row, ("ability",), ("abilities", "ability_list"), 4),
                items=_collect_named_values(row, ("item", "held_item"), ("items", "item_list"), 8),
                poke_edges=_collect_named_values(row, ("poke_edge", "pokeedge"), ("poke_edges", "poke_edge_list"), 8),
                nature=_pick_first(row, ("nature",)),
                stat_mode=_normalize_stat_mode(_pick_first(row, ("stat_mode", "stats_mode", "statmode"))),
                tutor_points=_as_int(_pick_first(row, ("tutor_points", "tutor_point", "tutorpoints", "tp")), 0),
                moves=moves,
                move_sources=_collect_move_sources(row, moves),
                poke_edge_choices=_collect_poke_edge_choices(row),
                stats=stats,
                order=idx,
            )
        )
    if not rows:
        raise ValueError("Roster CSV has no usable rows.")
    return rows


def _apply_stat_overrides(spec: PokemonSpec, stats: Dict[str, int]) -> None:
    if not isinstance(stats, dict):
        return
    hp = int(stats.get("hp", 0) or 0)
    atk = int(stats.get("atk", 0) or 0)
    defense = int(stats.get("def", 0) or 0)
    spatk = int(stats.get("spatk", 0) or 0)
    spdef = int(stats.get("spdef", 0) or 0)
    spd = int(stats.get("spd", 0) or 0)
    if hp > 0:
        spec.hp_stat = max(int(spec.hp_stat), hp)
    if atk > 0:
        spec.atk = max(int(spec.atk), atk)
    if defense > 0:
        spec.defense = max(int(spec.defense), defense)
    if spatk > 0:
        spec.spatk = max(int(spec.spatk), spatk)
    if spdef > 0:
        spec.spdef = max(int(spec.spdef), spdef)
    if spd > 0:
        spec.spd = max(int(spec.spd), spd)


def _apply_tutor_points(spec: PokemonSpec, tutor_points: int) -> None:
    spec.tutor_points = max(0, int(tutor_points or 0))


def _apply_move_sources(spec: PokemonSpec, move_sources: Dict[str, str]) -> None:
    if not isinstance(move_sources, dict):
        return
    normalized = {
        _normalize_move_key(key): _clean(value)
        for key, value in move_sources.items()
        if _normalize_move_key(key) and _clean(value)
    }
    spec.move_sources = normalized


def _apply_poke_edge_choices(spec: PokemonSpec, poke_edge_choices: Dict[str, object]) -> None:
    if not isinstance(poke_edge_choices, dict):
        return
    underdog = poke_edge_choices.get("underdog_lessons")
    if not isinstance(underdog, dict):
        underdog = {}
    spec.poke_edge_choices = {
        "accuracy_training": [name for name in _split_semicolon_list(";".join(map(str, poke_edge_choices.get("accuracy_training", []) or []))) if _clean(name)],
        "advanced_connection": [name for name in _split_semicolon_list(";".join(map(str, poke_edge_choices.get("advanced_connection", []) or []))) if _clean(name)],
        "underdog_lessons": {
            "evolution": _clean(underdog.get("evolution")),
            "moves": [name for name in _split_semicolon_list(";".join(map(str, underdog.get("moves", []) or []))) if _clean(name)][:3],
        },
    }


def _apply_poke_edges(spec: PokemonSpec, poke_edges: List[str]) -> None:
    if not isinstance(poke_edges, list):
        return
    spec.poke_edges = [{"name": name} for name in poke_edges if _clean(name)]


def _canonicalize_names(repo: PTUCsvRepository, row: _RosterRow) -> _RosterRow:
    species_name = repo.resolve_species_name(row.species) or row.species
    move_names = [repo.resolve_move_name(name) or name for name in (row.moves or [])]
    ability_names = [repo.resolve_ability_name(species_name, name, row.level) or name for name in (row.abilities or [])]
    item_names = [repo.resolve_item_name(name) or name for name in (row.items or [])]
    move_sources = {}
    for original_name, canonical_name in zip(row.moves or [], move_names):
        original_key = _normalize_move_key(original_name)
        canonical_key = _normalize_move_key(canonical_name)
        source_value = (row.move_sources or {}).get(original_key, "")
        if canonical_key and source_value:
            move_sources[canonical_key] = source_value
    return _RosterRow(
        side=row.side,
        slot=row.slot,
        species=species_name,
        level=row.level,
        nickname=row.nickname,
        abilities=ability_names,
        items=item_names,
        poke_edges=list(row.poke_edges or []),
        nature=row.nature,
        stat_mode=row.stat_mode,
        tutor_points=row.tutor_points,
        moves=move_names,
        move_sources=move_sources,
        poke_edge_choices=dict(row.poke_edge_choices or {}),
        stats=dict(row.stats or {}),
        order=row.order,
    )


def _reverse_nature_stats_if_needed(row: _RosterRow) -> Dict[str, int]:
    stats = dict(row.stats or {})
    if row.stat_mode != "post_nature" or not row.nature:
        return stats
    try:
        from .natures import nature_stat_modifiers
    except Exception:
        return stats
    modifiers = nature_stat_modifiers(row.nature)
    if not modifiers:
        return stats
    return {
        "hp": max(1, int(stats.get("hp", 0) or 0) - int(modifiers.get("hp_stat", 0) or 0)) if int(stats.get("hp", 0) or 0) > 0 else 0,
        "atk": max(1, int(stats.get("atk", 0) or 0) - int(modifiers.get("atk", 0) or 0)) if int(stats.get("atk", 0) or 0) > 0 else 0,
        "def": max(1, int(stats.get("def", 0) or 0) - int(modifiers.get("defense", 0) or 0)) if int(stats.get("def", 0) or 0) > 0 else 0,
        "spatk": max(1, int(stats.get("spatk", 0) or 0) - int(modifiers.get("spatk", 0) or 0)) if int(stats.get("spatk", 0) or 0) > 0 else 0,
        "spdef": max(1, int(stats.get("spdef", 0) or 0) - int(modifiers.get("spdef", 0) or 0)) if int(stats.get("spdef", 0) or 0) > 0 else 0,
        "spd": max(1, int(stats.get("spd", 0) or 0) - int(modifiers.get("spd", 0) or 0)) if int(stats.get("spd", 0) or 0) > 0 else 0,
    }


def _has_stat_overrides(stats: Dict[str, int]) -> bool:
    if not isinstance(stats, dict):
        return False
    return any(int(value or 0) > 0 for value in stats.values())


def campaign_from_roster_csv(
    *,
    csv_text: str,
    csv_root: Optional[str] = None,
    default_level: int = 30,
    ) -> CampaignSpec:
    rows = _parse_rows(csv_text, default_level=default_level)
    repo = PTUCsvRepository(root=csv_root)
    if not repo.available():
        raise FileNotFoundError(f"CSV bundle not found under {repo.root}.")
    grouped: Dict[str, List[Tuple[int, int, PokemonSpec]]] = {}
    for row in rows:
        row = _canonicalize_names(repo, row)
        stat_overrides = _reverse_nature_stats_if_needed(row)
        spec = repo.build_pokemon_spec(
            row.species,
            level=row.level,
            move_names=row.moves or None,
            nickname=row.nickname or None,
            assign_abilities=not bool(row.abilities),
            assign_nature=not bool(row.nature) and not _has_stat_overrides(stat_overrides),
            nature=row.nature or None,
        )
        if row.abilities:
            spec.abilities = [{"name": name} for name in row.abilities]
        if row.items:
            spec.items = [{"name": name} for name in row.items]
        if row.nature:
            spec.nature = row.nature
        spec.stat_mode = row.stat_mode
        _apply_stat_overrides(spec, stat_overrides)
        _apply_tutor_points(spec, row.tutor_points)
        _apply_move_sources(spec, row.move_sources)
        _apply_poke_edge_choices(spec, row.poke_edge_choices)
        _apply_poke_edges(spec, row.poke_edges)
        grouped.setdefault(row.side, []).append((row.slot, row.order, spec))
    if not grouped:
        raise ValueError("Roster CSV has no usable sides.")
    if len(grouped) == 1:
        only_entries = next(iter(grouped.values()))
        players_sorted = [spec for _, _, spec in sorted(only_entries, key=lambda pair: (pair[0], pair[1]))]
        foes_sorted = []
    else:
        player_entries = list(grouped.get("player", []))
        foe_entries = list(grouped.get("foe", []))
        if not player_entries or not foe_entries:
            raise ValueError("Roster CSV must include at least one player and one foe row.")
        players_sorted = [spec for _, _, spec in sorted(player_entries, key=lambda pair: (pair[0], pair[1]))]
        foes_sorted = [spec for _, _, spec in sorted(foe_entries, key=lambda pair: (pair[0], pair[1]))]
    base = default_campaign()
    return CampaignSpec(
        name="Roster CSV Arena",
        description="Encounter generated from roster CSV import.",
        default_weather=base.default_weather,
        grid=base.grid,
        players=players_sorted,
        foes=foes_sorted,
        metadata={"source": "roster_csv", "active_slots": 1, "side_count": len(grouped)},
    )


def match_plan_from_roster_csv(
    *,
    csv_text: str,
    csv_root: Optional[str] = None,
    default_level: int = 30,
    active_slots: int = 1,
    ai_mode: str = "player",
    seed: Optional[int] = None,
) -> MatchPlan:
    rows = _parse_rows(csv_text, default_level=default_level)
    repo = PTUCsvRepository(root=csv_root)
    if not repo.available():
        raise FileNotFoundError(f"CSV bundle not found under {repo.root}.")

    grouped: Dict[str, List[Tuple[int, int, PokemonSpec]]] = {}
    for row in rows:
        row = _canonicalize_names(repo, row)
        stat_overrides = _reverse_nature_stats_if_needed(row)
        spec = repo.build_pokemon_spec(
            row.species,
            level=row.level,
            move_names=row.moves or None,
            nickname=row.nickname or None,
            assign_abilities=not bool(row.abilities),
            assign_nature=not bool(row.nature) and not _has_stat_overrides(stat_overrides),
            nature=row.nature or None,
        )
        if row.abilities:
            spec.abilities = [{"name": name} for name in row.abilities]
        if row.items:
            spec.items = [{"name": name} for name in row.items]
        if row.nature:
            spec.nature = row.nature
        spec.stat_mode = row.stat_mode
        _apply_stat_overrides(spec, stat_overrides)
        _apply_tutor_points(spec, row.tutor_points)
        _apply_move_sources(spec, row.move_sources)
        _apply_poke_edge_choices(spec, row.poke_edge_choices)
        _apply_poke_edges(spec, row.poke_edges)
        grouped.setdefault(row.side, []).append((row.slot, row.order, spec))

    if len(grouped) < 2:
        only_label, only_entries = next(iter(grouped.items()))
        ordered = [spec for _, _, spec in sorted(only_entries, key=lambda pair: (pair[0], pair[1]))]
        identifier = _side_identifier(only_label, set())
        side = TrainerSideSpec(
            identifier=identifier,
            name=only_label.replace("_", " ").title(),
            controller="player" if ai_mode != "ai" else "ai",
            team=only_label,
            ai_level="standard",
            pokemon=ordered,
        )
        base = default_campaign()
        matchup = MatchupSpec(
            you=ordered[0],
            foe=ordered[0],
            label="Single-Team Roster Load",
            sides=[side],
        )
        return MatchPlan(
            matchups=[matchup],
            weather=base.default_weather,
            grid=base.grid,
            battle_context="full_contact",
            active_slots=max(1, int(active_slots)),
            description="Single-team encounter generated from roster CSV import.",
            seed=seed,
        )

    primary_side = _primary_side_label(rows)
    sides: List[TrainerSideSpec] = []
    used_identifiers: set[str] = set()
    for side_label, entries in grouped.items():
        ordered = [spec for _, _, spec in sorted(entries, key=lambda pair: (pair[0], pair[1]))]
        identifier = _side_identifier(side_label, used_identifiers)
        controller = "player" if (ai_mode != "ai" and side_label == primary_side) else "ai"
        sides.append(
            TrainerSideSpec(
                identifier=identifier,
                name=side_label.replace("_", " ").title(),
                controller=controller,
                team=side_label,
                ai_level="standard",
                pokemon=ordered,
            )
        )

    base = default_campaign()
    label = f"{len(sides)}-way Roster Battle"
    matchup = MatchupSpec(
        you=sides[0].pokemon[0],
        foe=sides[1].pokemon[0],
        label=label,
        sides=sides,
    )
    return MatchPlan(
        matchups=[matchup],
        weather=base.default_weather,
        grid=base.grid,
        battle_context="full_contact",
        active_slots=max(1, int(active_slots)),
        description="Encounter generated from roster CSV import.",
        seed=seed,
    )


def campaign_from_roster_csv_file(
    *,
    path: str | Path,
    csv_root: Optional[str] = None,
    default_level: int = 30,
) -> CampaignSpec:
    raw = Path(path).read_text(encoding="utf-8")
    return campaign_from_roster_csv(csv_text=raw, csv_root=csv_root, default_level=default_level)


def match_plan_from_roster_csv_file(
    *,
    path: str | Path,
    csv_root: Optional[str] = None,
    default_level: int = 30,
    active_slots: int = 1,
    ai_mode: str = "player",
    seed: Optional[int] = None,
) -> MatchPlan:
    raw = Path(path).read_text(encoding="utf-8")
    return match_plan_from_roster_csv(
        csv_text=raw,
        csv_root=csv_root,
        default_level=default_level,
        active_slots=active_slots,
        ai_mode=ai_mode,
        seed=seed,
    )
