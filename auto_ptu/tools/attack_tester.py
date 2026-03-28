"""Helpers for quick move testing against a dummy target."""
from __future__ import annotations

import difflib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from rich.console import Console

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, UseMoveAction, targeting

ROOT = Path(__file__).resolve().parents[2]
MOVES_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"

console = Console(legacy_windows=False)


@dataclass(frozen=True)
class MatchCandidate:
    name: str
    score: float


def _load_move_specs() -> list[MoveSpec]:
    moves = json.loads(MOVES_PATH.read_text(encoding="utf-8"))
    return [MoveSpec.from_dict(entry) for entry in moves]


def _score_match(query: str, name: str) -> float:
    query_lower = query.lower()
    name_lower = name.lower()
    score = difflib.SequenceMatcher(None, query_lower, name_lower).ratio()
    if query_lower in name_lower:
        score += 0.6
    if name_lower.startswith(query_lower):
        score += 0.3
    return score


def find_move_matches(query: str, names: Sequence[str], limit: int = 10) -> list[str]:
    query = query.strip()
    if not query:
        return []
    scored: list[MatchCandidate] = []
    for name in names:
        score = _score_match(query, name)
        if score < 0.35:
            continue
        scored.append(MatchCandidate(name=name, score=score))
    scored.sort(key=lambda entry: (-entry.score, entry.name.lower()))
    return [entry.name for entry in scored[:limit]]


def prompt_for_move_name(names: Sequence[str]) -> Optional[str]:
    """Prompt for a move name with fuzzy suggestions."""
    while True:
        raw = console.input("Move name (partial ok, blank to cancel): ").strip()
        if not raw:
            return None
        matches = find_move_matches(raw, names)
        if not matches:
            console.print("[yellow]No matches. Try another search.[/yellow]")
            continue
        if len(matches) == 1 and matches[0].lower() == raw.lower():
            return matches[0]
        console.print("Matches:")
        for idx, name in enumerate(matches, start=1):
            console.print(f"  {idx}. {name}")
        choice = console.input("Pick a number, or type a new search: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                return matches[idx]
        if choice:
            raw = choice
        else:
            return None


def _build_pokemon(
    *,
    species: str,
    move: MoveSpec,
    types: Sequence[str],
    controller: str,
    position: tuple[int, int],
    level: int = 20,
    hp_stat: int = 10,
    atk: int = 10,
    defense: int = 10,
    spatk: int = 10,
    spdef: int = 10,
    spd: int = 10,
    hp_override: Optional[int] = None,
    statuses: Sequence[str] = (),
    items: Sequence[str] = (),
    food_buff: bool = False,
    combat_stages: Sequence[str] = (),
) -> PokemonState:
    spec = PokemonSpec(
        species=species,
        level=level,
        types=list(types),
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=[move],
    )
    if items:
        spec.items = [{"name": item} for item in items]
    state = PokemonState(spec=spec, controller_id=controller, position=position)
    if statuses:
        state.statuses.extend({"name": entry} for entry in statuses)
    if combat_stages:
        _apply_combat_stages(state, combat_stages)
    if food_buff:
        state.add_food_buff({"name": "Food Buff", "effect": "Test Buff"})
    if hp_override is not None:
        state.hp = max(0, int(hp_override))
    if any(entry.strip().lower().replace(" ", "_") == "digestion_traded" for entry in statuses):
        state.add_temporary_effect("digestion_traded")
    return state


def _apply_combat_stages(state: PokemonState, entries: Sequence[str]) -> None:
    alias = {
        "atk": "atk",
        "def": "def",
        "spatk": "spatk",
        "sp_atk": "spatk",
        "spa": "spatk",
        "spdef": "spdef",
        "sp_def": "spdef",
        "spd": "spd",
        "speed": "spd",
        "accuracy": "accuracy",
    }
    for entry in entries:
        if not entry or "=" not in entry:
            continue
        raw_stat, raw_value = entry.split("=", 1)
        stat_key = alias.get(raw_stat.strip().lower())
        if not stat_key:
            continue
        try:
            value = int(raw_value.strip())
        except ValueError:
            continue
        state.combat_stages[stat_key] = max(-6, min(6, value))


def _positions_for_move(move: MoveSpec) -> tuple[tuple[int, int], tuple[int, int]]:
    attacker_pos = (5, 5)
    kind = targeting.normalized_target_kind(move)
    area = targeting.normalized_area_kind(move)
    if kind == "self":
        return attacker_pos, attacker_pos
    if area in {"line", "cone", "closeblast"}:
        return attacker_pos, (6, 5)
    if kind == "melee":
        return attacker_pos, (6, 5)
    distance = max(1, min(3, targeting.move_range_distance(move)))
    return attacker_pos, (attacker_pos[0] + distance, attacker_pos[1])


def run_move_test(
    move_name: str,
    *,
    seed: int = 1,
    resolve_pending: bool = True,
    show_log: bool = False,
    attacker_hp: Optional[int] = None,
    defender_hp: Optional[int] = None,
    attacker_statuses: Sequence[str] = (),
    defender_statuses: Sequence[str] = (),
    defender_items: Sequence[str] = (),
    defender_food_buff: bool = False,
    attacker_stages: Sequence[str] = (),
    defender_stages: Sequence[str] = (),
    defender_defense: Optional[int] = None,
    defender_spdef: Optional[int] = None,
) -> BattleState:
    moves = _load_move_specs()
    move_lookup = {move.name.lower(): move for move in moves if move.name}
    move = move_lookup.get(move_name.lower())
    if move is None:
        raise ValueError(f"Unknown move: {move_name}")
    healing_wish = move_lookup.get("healing wish") or move
    attacker_pos, defender_pos = _positions_for_move(move)
    attacker = _build_pokemon(
        species="Tester",
        move=move,
        types=[move.type or "Normal"],
        controller="attacker",
        position=attacker_pos,
        hp_override=attacker_hp,
        statuses=attacker_statuses,
        combat_stages=attacker_stages,
    )
    defender = _build_pokemon(
        species="Blissey",
        move=healing_wish,
        types=["Normal"],
        controller="defender",
        position=defender_pos,
        level=100,
        hp_stat=255,
        atk=10,
        defense=defender_defense if defender_defense is not None else 10,
        spatk=75,
        spdef=defender_spdef if defender_spdef is not None else 135,
        spd=55,
        hp_override=defender_hp,
        statuses=defender_statuses,
        items=defender_items,
        food_buff=defender_food_buff,
        combat_stages=defender_stages,
    )
    battle = BattleState(
        trainers={},
        pokemon={"attacker-1": attacker, "defender-1": defender},
        grid=GridState(width=15, height=10),
        rng=random.Random(seed),
    )
    battle.start_round()
    while battle.advance_turn() and battle.current_actor_id != "attacker-1":
        battle.end_turn()
    target_kind = targeting.normalized_target_kind(move)
    target_id = "defender-1"
    if target_kind == "self":
        target_id = "attacker-1"
    action = UseMoveAction(actor_id="attacker-1", move_name=move.name, target_id=target_id)
    battle.queue_action(action)
    battle.resolve_next_action()
    if resolve_pending and battle.has_pending_resolution("attacker-1"):
        battle.execute_pending_resolution("attacker-1")
    if show_log:
        for entry in battle.log:
            console.print(entry)
    return battle


def describe_move_test(
    move_name: str,
    *,
    seed: int = 1,
    resolve_pending: bool = True,
    show_log: bool = False,
    attacker_hp: Optional[int] = None,
    defender_hp: Optional[int] = None,
    attacker_statuses: Sequence[str] = (),
    defender_statuses: Sequence[str] = (),
    defender_items: Sequence[str] = (),
    defender_food_buff: bool = False,
    attacker_stages: Sequence[str] = (),
    defender_stages: Sequence[str] = (),
    defender_defense: Optional[int] = None,
    defender_spdef: Optional[int] = None,
) -> None:
    battle = run_move_test(
        move_name,
        seed=seed,
        resolve_pending=resolve_pending,
        show_log=show_log,
        attacker_hp=attacker_hp,
        defender_hp=defender_hp,
        attacker_statuses=attacker_statuses,
        defender_statuses=defender_statuses,
        defender_items=defender_items,
        defender_food_buff=defender_food_buff,
        attacker_stages=attacker_stages,
        defender_stages=defender_stages,
        defender_defense=defender_defense,
        defender_spdef=defender_spdef,
    )
    attacker = battle.pokemon["attacker-1"]
    defender = battle.pokemon["defender-1"]
    console.print(f"Move: {move_name}")
    console.print(f"Attacker HP: {attacker.hp}/{attacker.max_hp()}")
    console.print(f"Defender HP: {defender.hp}/{defender.max_hp()}")
    defender_moves = [mv.name for mv in defender.spec.moves if mv.name]
    if defender_moves:
        console.print(f"Defender moves: {', '.join(defender_moves)}")
    move_events = [evt for evt in battle.log if evt.get("move") == move_name]
    if move_events:
        console.print("Move events:")
        for event in move_events:
            console.print(event)
    else:
        console.print("No move-specific events logged.")


def list_moves() -> list[str]:
    return [move.name for move in _load_move_specs() if move.name]


__all__ = [
    "describe_move_test",
    "find_move_matches",
    "list_moves",
    "prompt_for_move_name",
    "run_move_test",
]
