"""Move-special hook registry for incremental, modular move logic."""

from __future__ import annotations

from dataclasses import dataclass, field
import copy
import json
import math
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from ... import ptu_engine
from ...data_models import MoveSpec
from .. import movement, targeting
from .. import calculations
from ..calculations import resolve_move_action
from ..move_traits import move_has_keyword, move_has_crash_trait, is_setup_move, move_has_contact_trait
from ..abilities.ability_variants import has_ability_exact, has_errata
from .move_effect_tools import (
    apply_trap_status,
    apply_follow_me,
    disable_items,
    disable_ability,
    disable_move,
    schedule_delayed_hit,
    clear_hazards,
    swap_hazards,
    set_terrain,
    set_weather,
    add_restore_on_switch,
)

if TYPE_CHECKING:
    from ..battle_state import BattleState, PokemonState


@dataclass
class MoveSpecialContext:
    battle: "BattleState"
    attacker_id: str
    attacker: "PokemonState"
    defender_id: Optional[str]
    defender: Optional["PokemonState"]
    move: MoveSpec
    result: Dict[str, object]
    damage_dealt: int
    events: List[dict]
    move_name: str
    hit: bool
    phase: str
    action_type: Optional[str]
    move_params: Dict[str, object] = field(default_factory=dict)


_MOVE_SPECIAL_HANDLERS: Dict[str, Dict[str, List[Callable[[MoveSpecialContext], None]]]] = {}
_GLOBAL_MOVE_SPECIAL_HANDLERS: Dict[str, List[Callable[[MoveSpecialContext], None]]] = {}
_MOVE_SPECIALS_INITIALIZED = False
_MOVE_SPEC_CACHE: Optional[Dict[str, MoveSpec]] = None
_METRONOME_POOL: Optional[List[MoveSpec]] = None
_STATUS_CONDITIONS_TO_CURE = {
    "burned",
    "poisoned",
    "badly poisoned",
    "paralyzed",
    "frozen",
    "frostbite",
    "sleep",
    "asleep",
    "drowsy",
    "confusion",
    "confused",
    "charmed",
    "fear",
    "taunted",
    "burn",
    "poison",
    "paralyze",
    "freeze",
}

_FEARSOME_DISPLAY_CURE_NAMES = {
    "burned",
    "poisoned",
    "badly poisoned",
    "paralyzed",
    "frozen",
    "frostbite",
    "sleep",
    "asleep",
    "confused",
    "confusion",
    "enraged",
    "infatuated",
    "suppressed",
    "taunted",
    "blinded",
    "slowed",
    "hindered",
    "stuck",
}


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


def _effect_roll(ctx: MoveSpecialContext) -> int:
    if ctx.defender is not None:
        move_name = str(ctx.move.name or "").strip().lower()
        for entry in list(ctx.defender.get_temporary_effects("immutable_mind_block")):
            expires_round = entry.get("expires_round")
            if expires_round is not None and ctx.battle.round > int(expires_round):
                if entry in ctx.defender.temporary_effects:
                    ctx.defender.temporary_effects.remove(entry)
                continue
            entry_move = str(entry.get("move") or "").strip().lower()
            if entry_move and entry_move != move_name:
                continue
            return -1
    for entry in list(ctx.attacker.get_temporary_effects("effect_range_block")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            if entry in ctx.attacker.temporary_effects:
                ctx.attacker.temporary_effects.remove(entry)
            continue
        return 0
    roll = int(ctx.result.get("roll") or 0)
    bonus = 0
    if ctx.attacker is not None:
        suppressed = False
        if getattr(ctx.battle, "abilities_suppressed_for", None):
            suppressed = ctx.battle.abilities_suppressed_for(ctx.attacker_id)
        if not suppressed:
            if ctx.attacker.has_ability("Serene Grace"):
                bonus += 2
            if ctx.attacker.has_ability("Stench") or has_errata(ctx.attacker, "Stench"):
                text = _effects_text_for(ctx.move).lower()
                if "flinch" in text:
                    bonus += 2
    if bonus:
        roll += bonus
    if ctx.attacker is not None and getattr(ctx.battle, "_roll_penalty", None):
        roll -= int(ctx.battle._roll_penalty(ctx.attacker))
    if (
        ctx.attacker is not None
        and ctx.move is not None
        and str(ctx.move.type or "").strip().lower() == "psychic"
        and str(ctx.move.category or "").strip().lower() != "status"
        and ctx.attacker.get_temporary_effects("mindbreak_bound")
    ):
        roll += 1
    if (
        ctx.attacker is not None
        and ctx.move is not None
        and str(ctx.move.type or "").strip().lower() == "steel"
        and ctx.attacker.has_trainer_feature("Polished Shine")
    ):
        roll += 2
    if ctx.attacker is not None and ctx.attacker.get_temporary_effects("brutal_training"):
        roll += 1
    if ctx.attacker is not None:
        for entry in list(ctx.attacker.get_temporary_effects("effect_range_bonus")):
            expires_round = entry.get("expires_round")
            if expires_round is not None and ctx.battle.round > int(expires_round):
                if entry in ctx.attacker.temporary_effects:
                    ctx.attacker.temporary_effects.remove(entry)
                continue
            try:
                roll += int(entry.get("amount", 0) or 0)
            except (TypeError, ValueError):
                continue
    if ctx.attacker is not None:
        roll += ctx.attacker.hardened_crit_effect_bonus(getattr(ctx.battle, "battle", None) or ctx.battle)
    return roll


def _dirty_trick_bonus(attacker: "PokemonState") -> int:
    return 2 if attacker.has_trainer_feature("Expert Trickster") else 0


def _dirty_trick_should_mark_on_failure(attacker: "PokemonState") -> bool:
    return not attacker.has_trainer_feature("Expert Trickster")


def _dirty_trick_apply_use(ctx: MoveSpecialContext, trick: str, *, succeeded: bool) -> None:
    if ctx.defender_id is None:
        return
    if succeeded or _dirty_trick_should_mark_on_failure(ctx.attacker):
        ctx.attacker.add_temporary_effect(
            "dirty_trick_used",
            target=ctx.defender_id,
            trick=trick,
        )


def _fearsome_display_active(attacker: "PokemonState") -> bool:
    return attacker.is_trainer_combatant() and attacker.has_trainer_feature("Fearsome Display")


def _load_move_spec_cache() -> Dict[str, MoveSpec]:
    global _MOVE_SPEC_CACHE
    if _MOVE_SPEC_CACHE is not None:
        return _MOVE_SPEC_CACHE
    path = Path(__file__).resolve().parents[2] / "data" / "compiled" / "moves.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _MOVE_SPEC_CACHE = {}
        return _MOVE_SPEC_CACHE
    cache: Dict[str, MoveSpec] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        spec = MoveSpec.from_dict(entry)
        if not spec.effects_text:
            spec.effects_text = str(entry.get("effects") or "")
        cache[name.lower()] = spec
    _MOVE_SPEC_CACHE = cache
    return cache


def _lookup_move_spec(name: str) -> Optional[MoveSpec]:
    if not name:
        return None
    key = name.strip().lower()
    cache = _load_move_spec_cache()
    spec = cache.get(key)
    if spec is not None:
        return spec
    alias_map = {
        "toxic thread": "toxic threads",
    }
    alias = alias_map.get(key)
    if alias:
        mapped = cache.get(alias)
        if mapped is None:
            return None
        return MoveSpec(
            name=name.strip() or mapped.name,
            type=mapped.type,
            category=mapped.category,
            db=mapped.db,
            ac=mapped.ac,
            range_kind=mapped.range_kind,
            range_value=mapped.range_value,
            target_kind=mapped.target_kind,
            target_range=mapped.target_range,
            area_kind=mapped.area_kind,
            area_value=mapped.area_value,
            freq=mapped.freq,
            effects_text=mapped.effects_text,
            range_text=mapped.range_text,
            keywords=list(mapped.keywords or []),
            priority=mapped.priority,
        )
    return None


def _metronome_pool() -> List[MoveSpec]:
    global _METRONOME_POOL
    if _METRONOME_POOL is not None:
        return _METRONOME_POOL
    blacklist = {
        "after you",
        "assist",
        "bestow",
        "copycat",
        "counter",
        "covet",
        "crafty shield",
        "destiny bond",
        "detect",
        "endure",
        "feint",
        "focus punch",
        "follow me",
        "helping hand",
        "king's shield",
        "kings shield",
        "metronome",
        "me first",
        "mimic",
        "mirror coat",
        "mirror move",
        "protect",
        "quash",
        "quick guard",
        "rage powder",
        "sketch",
        "sleep talk",
        "snatch",
        "snore",
        "spiky shield",
        "switcheroo",
        "thief",
        "transform",
        "trick",
        "wide guard",
    }
    pool = [
        move
        for move in _load_move_spec_cache().values()
        if move.name.strip().lower() not in blacklist
    ]
    _METRONOME_POOL = pool
    return pool


_STATUS_PATTERN = re.compile(
    r"\b(?P<verb>burns?|burned|burnt|poisons?|poisoned|paralyzes|paralyzed|freezes|frozen|"
    r"confuses|confused|flinches|flinched)\b"
    r".*?\bon\s+(?:a\s+)?(?P<threshold>\d+)\+",
    re.IGNORECASE,
)
_STATUS_EVEN_PATTERN = re.compile(
    r"\b(?P<verb>burns?|burned|burnt|poisons?|poisoned|paralyzes|paralyzed|freezes|frozen|"
    r"confuses|confused|flinches|flinched)\b"
    r".*?\beven-numbered roll",
    re.IGNORECASE,
)
_STATUS_ALWAYS_PATTERN = re.compile(
    r"\b(?P<verb>burns?|burned|burnt|poisons?|poisoned|paralyzes|paralyzed|freezes|frozen|"
    r"confuses|confused|flinches|flinched)\b"
    r"(?:\s+the\s+target|\s+its\s+target)?\b",
    re.IGNORECASE,
)
_CRIT_PATTERN = re.compile(r"critical hit on\s+(?:a\s+|an\s+)?(?P<threshold>\d+)\+", re.IGNORECASE)
_CRIT_EVEN_PATTERN = re.compile(r"critical hit on (?:an\s+)?even-numbered roll(?:s)?", re.IGNORECASE)
_RAISE_PATTERN = re.compile(
    r"raise(?:s)?\s+the\s+(?P<target>user|target)'?s?\s+"
    r"(?P<stats>[\w\s/]+?)\s+(?:by\s+)?\+?(?P<amount>\d+)\s+(?:combat stage|cs)"
    r"(?:\s+on\s+(?P<threshold>\d+)\+)?(?:\s+each)?",
    re.IGNORECASE,
)
_LOWER_PATTERN = re.compile(
    r"lower(?:s)?\s+the\s+(?P<target>user|target)'?s?\s+"
    r"(?P<stats>[\w\s/]+?)\s+(?:by\s+)?\-?(?P<amount>\d+)\s+(?:combat stage|cs)"
    r"(?:\s+on\s+(?P<threshold>\d+)\+)?(?:\s+each)?",
    re.IGNORECASE,
)


_STAT_ALIASES = {
    "attack": "atk",
    "atk": "atk",
    "defense": "def",
    "def": "def",
    "special attack": "spatk",
    "special atk": "spatk",
    "sp atk": "spatk",
    "sp. atk": "spatk",
    "special defense": "spdef",
    "special def": "spdef",
    "sp def": "spdef",
    "sp. def": "spdef",
    "speed": "spd",
    "spd": "spd",
    "accuracy": "accuracy",
    "evasion": "evasion",
}


def _effects_text_for(move: MoveSpec) -> str:
    if move.effects_text:
        return move.effects_text
    spec = _lookup_move_spec(move.name or "")
    if spec and spec.effects_text:
        return spec.effects_text
    return ""


def _normalize_effects_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": "\"",
        "\u201d": "\"",
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _has_specific_handler(move_name: str) -> bool:
    return bool(_MOVE_SPECIAL_HANDLERS.get(move_name, {}))


def _normalize_stats(text: str) -> List[str]:
    parts = [part.strip().lower() for part in re.split(r"and|,|/", text)]
    stats = []
    for part in parts:
        for key, stat in sorted(_STAT_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            if key in part:
                stats.append(stat)
                break
    return list(dict.fromkeys(stats))


def initialize_move_specials() -> None:
    """Explicitly load move-special registration modules."""
    global _MOVE_SPECIALS_INITIALIZED
    if _MOVE_SPECIALS_INITIALIZED:
        return
    _MOVE_SPECIALS_INITIALIZED = True
    from . import move_specials_items  # noqa: F401
    from . import move_specials_abilities  # noqa: F401


def _normalize_phase(phase: Optional[str]) -> str:
    normalized = str(phase or "").strip().lower()
    if normalized in {"pre_damage", "post_damage", "end_action"}:
        return normalized
    return "post_damage"


def _place_hazard_on_target_tile(ctx: MoveSpecialContext, hazard: str, layers: int) -> None:
    if ctx.defender is not None and ctx.defender.position is not None:
        ctx.battle._place_hazard(ctx.defender.position, hazard, layers, source_id=ctx.attacker_id)
        return
    if ctx.attacker.position is not None:
        ctx.battle._place_hazard(ctx.attacker.position, hazard, layers, source_id=ctx.attacker_id)


def _pivot_switch(ctx: MoveSpecialContext, *, effect: str) -> None:
    battle = ctx.battle
    attacker = ctx.attacker
    if attacker is None:
        return
    candidates = battle._bench_candidates(attacker.controller_id)
    if not candidates:
        return
    candidates.sort(key=lambda pid: (battle.pokemon[pid].hp or 0, pid), reverse=True)
    replacement_id = candidates[0]
    battle._apply_switch(attacker_id=ctx.attacker_id, replacement_id=replacement_id, allow_replacement_turn=True)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": effect,
            "description": f"{ctx.move.name} recalls the user after hitting.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


def register_move_special(
    *names: str,
    phase: str = "post_damage",
) -> Callable[[Callable[[MoveSpecialContext], None]], Callable[[MoveSpecialContext], None]]:
    def decorator(handler: Callable[[MoveSpecialContext], None]) -> Callable[[MoveSpecialContext], None]:
        resolved_phase = _normalize_phase(phase)
        for raw in names:
            name = str(raw or "").strip().lower()
            if not name:
                continue
            _MOVE_SPECIAL_HANDLERS.setdefault(name, {}).setdefault(resolved_phase, []).append(handler)
        return handler

    return decorator


def register_global_move_special(
    handler: Optional[Callable[[MoveSpecialContext], None]] = None,
    *,
    phase: str = "post_damage",
) -> Callable[[MoveSpecialContext], None]:
    def decorator(fn: Callable[[MoveSpecialContext], None]) -> Callable[[MoveSpecialContext], None]:
        resolved_phase = _normalize_phase(phase)
        _GLOBAL_MOVE_SPECIAL_HANDLERS.setdefault(resolved_phase, []).append(fn)
        return fn

    if handler is None:
        return decorator
    return decorator(handler)


def handle_move_specials(
    battle: "BattleState",
    attacker_id: str,
    attacker: "PokemonState",
    defender_id: Optional[str],
    defender: Optional["PokemonState"],
    move: MoveSpec,
    result: Dict[str, object],
    damage_dealt: int,
    *,
    phase: str = "post_damage",
    action_type: Optional[str] = None,
    move_params: Optional[Dict[str, object]] = None,
) -> List[dict]:
    events: List[dict] = []
    move_name = (move.name or "").strip().lower()
    hit = bool(result.get("hit"))
    resolved_phase = _normalize_phase(phase)
    ctx = MoveSpecialContext(
        battle=battle,
        attacker_id=attacker_id,
        attacker=attacker,
        defender_id=defender_id,
        defender=defender,
        move=move,
        result=result,
        damage_dealt=damage_dealt,
        events=events,
        move_name=move_name,
        hit=hit,
        phase=resolved_phase,
        action_type=action_type,
        move_params=dict(move_params or {}),
    )
    if (
        defender
        and defender.has_ability("Shield Dust")
        and (move.category or "").strip().lower() != "status"
        and resolved_phase in {"post_damage", "post_result"}
    ):
        return events
    if resolved_phase == "post_damage":
        for handler in _MOVE_SPECIAL_HANDLERS.get(move_name, {}).get(resolved_phase, []):
            handler(ctx)
        for handler in _GLOBAL_MOVE_SPECIAL_HANDLERS.get(resolved_phase, []):
            handler(ctx)
    else:
        for handler in _GLOBAL_MOVE_SPECIAL_HANDLERS.get(resolved_phase, []):
            handler(ctx)
        for handler in _MOVE_SPECIAL_HANDLERS.get(move_name, {}).get(resolved_phase, []):
            handler(ctx)
    return events


@register_global_move_special(phase="pre_damage")
def _generic_pre_damage_from_text(ctx: MoveSpecialContext) -> None:
    if _has_specific_handler(ctx.move_name):
        return
    text = _normalize_effects_text(_effects_text_for(ctx.move)).lower()
    if not text:
        return
    if "cannot miss" in text or "always hit" in text:
        ctx.result["hit"] = True
    if ctx.result.get("hit") and ctx.result.get("roll") is not None:
        roll = int(ctx.result.get("roll") or 0)
        match = _CRIT_PATTERN.search(text)
        if match:
            threshold = int(match.group("threshold"))
            if roll >= threshold:
                ctx.result["crit"] = True
        if _CRIT_EVEN_PATTERN.search(text) and roll % 2 == 0:
            ctx.result["crit"] = True


@register_global_move_special(phase="post_damage")
def _generic_post_damage_from_text(ctx: MoveSpecialContext) -> None:
    if _has_specific_handler(ctx.move_name):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    text = _normalize_effects_text(_effects_text_for(ctx.move)).lower()
    if not text:
        return
    roll = _effect_roll(ctx)
    status_map = {
        "burn": ("Burned", "burn"),
        "poison": ("Poisoned", "poison"),
        "paralyzes": ("Paralyzed", "paralysis"),
        "freeze": ("Frozen", "freeze"),
        "confuse": ("Confused", "confusion"),
        "flinch": ("Flinched", "flinch"),
    }
    match = _STATUS_PATTERN.search(text)
    if match:
        verb = match.group("verb").lower()
        threshold = int(match.group("threshold"))
        if roll >= threshold:
            for key, (status, effect) in status_map.items():
                if verb.startswith(key):
                    ctx.battle._apply_status(
                        ctx.events,
                        attacker_id=ctx.attacker_id,
                        target_id=ctx.defender_id,
                        move=ctx.move,
                        target=ctx.defender,
                        status=status,
                        effect=effect,
                        description=f"{ctx.move.name} inflicts {status} on a high roll.",
                        roll=roll,
                        remaining=1 if status in {"Flinched"} else None,
                    )
                    break
    if not match:
        always = _STATUS_ALWAYS_PATTERN.search(text)
        if always and "on " not in text:
            verb = always.group("verb").lower()
            for key, (status, effect) in status_map.items():
                if verb.startswith(key):
                    ctx.battle._apply_status(
                        ctx.events,
                        attacker_id=ctx.attacker_id,
                        target_id=ctx.defender_id,
                        move=ctx.move,
                        target=ctx.defender,
                        status=status,
                        effect=effect,
                        description=f"{ctx.move.name} inflicts {status}.",
                        remaining=1 if status in {"Flinched"} else None,
                    )
                    break
    if not match:
        even = _STATUS_EVEN_PATTERN.search(text)
        if even and roll % 2 == 0:
            verb = even.group("verb").lower()
            for key, (status, effect) in status_map.items():
                if verb.startswith(key):
                    ctx.battle._apply_status(
                        ctx.events,
                        attacker_id=ctx.attacker_id,
                        target_id=ctx.defender_id,
                        move=ctx.move,
                        target=ctx.defender,
                        status=status,
                        effect=effect,
                        description=f"{ctx.move.name} inflicts {status} on an even roll.",
                        remaining=1 if status in {"Flinched"} else None,
                    )
                    break
    if "falls asleep" in text or "falls asleep." in text:
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Sleep",
            effect="sleep",
            description=f"{ctx.move.name} puts the target to sleep.",
        )
    for pattern, sign in ((_RAISE_PATTERN, 1), (_LOWER_PATTERN, -1)):
        match = pattern.search(text)
        if not match:
            continue
        threshold = match.group("threshold")
        if threshold is not None:
            try:
                needed = int(threshold)
            except (TypeError, ValueError):
                needed = None
            if needed is not None and roll < needed:
                continue
        amount = int(match.group("amount")) * sign
        target = match.group("target").lower()
        stats = _normalize_stats(match.group("stats"))
        target_id = ctx.attacker_id if target == "user" else ctx.defender_id
        target_state = ctx.attacker if target == "user" else ctx.defender
        for stat in stats:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=target_id,
                move=ctx.move,
                target=target_state,
                stat=stat,
                delta=amount,
                description=f"{ctx.move.name} modifies {stat}.",
            )
    alt_target_lower = re.search(
        r"target'?s?\s+(?P<stats>[\w\s/]+?)\s+is\s+lowered\s+(?:by\s+)?\-?(?P<amount>\d+)\s+(?:combat stage|cs)",
        text,
    )
    if alt_target_lower:
        stats = _normalize_stats(alt_target_lower.group("stats"))
        amount = -int(alt_target_lower.group("amount"))
        for stat in stats:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.defender_id,
                move=ctx.move,
                target=ctx.defender,
                stat=stat,
                delta=amount,
                description=f"{ctx.move.name} modifies {stat}.",
            )
    alt_raise = re.search(
        r"raise(?:s)?\s+the\s+user'?s?\s+(?P<stats>[\w\s/]+?)\s+(?P<amount>\d+)\s+(?:combat stage|cs)",
        text,
    )
    if alt_raise:
        stats = _normalize_stats(alt_raise.group("stats"))
        amount = int(alt_raise.group("amount"))
        for stat in stats:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.attacker_id,
                move=ctx.move,
                target=ctx.attacker,
                stat=stat,
                delta=amount,
                description=f"{ctx.move.name} modifies {stat}.",
            )
    simple_lower = re.search(
        r"all legal targets.*?(?:are|have their)?\s*(?P<stat>accuracy|evasion|attack|defense|special attack|special defense|speed)\s+"
        r"(?:is\s+)?lowered\s+(?:by\s+)?\-?(?P<amount>\d+)\s+(?:combat stage|cs)",
        text,
    )
    if simple_lower:
        stat = _normalize_stats(simple_lower.group("stat"))[0]
        amount = -int(simple_lower.group("amount"))
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=amount,
            description=f"{ctx.move.name} modifies {stat}.",
        )


_DRAIN_MOVES_HALF = {
    "absorb",
    "mega drain",
    "giga drain",
    "drain punch",
    "leech life",
    "leech life [sm]",
    "draining kiss",
    "horn leech",
    "dream eater",
    "parabolic charge",
    "parabolic charge [sm]",
}


@register_move_special("helping hand")
def _helping_hand(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    ctx.defender.add_temporary_effect("accuracy_bonus", amount=2, expires_round=ctx.battle.round)
    ctx.defender.add_temporary_effect(
        "damage_bonus",
        amount=10,
        category="all",
        expires_round=ctx.battle.round,
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "helping_hand",
            "description": "Helping Hand boosts the target's next accuracy and damage rolls.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("lunge")
def _lunge_sprint_penalty(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    if not ctx.attacker.get_temporary_effects("sprint"):
        return
    ctx.defender.add_temporary_effect(
        "damage_bonus",
        amount=-5,
        category="all",
        expires_round=ctx.battle.round,
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "lunge_penalty",
            "amount": -5,
            "description": "Lunge imposes a damage penalty after a sprint.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("constrict", phase="pre_damage")
def _constrict_auto_hit(ctx: MoveSpecialContext) -> None:
    link = next(
        (
            entry
            for entry in ctx.attacker.temporary_effects
            if entry.get("kind") == "grapple_link"
            and str(entry.get("other", "")) == str(ctx.defender_id)
            and entry.get("dominant")
        ),
        None,
    )
    if link:
        ctx.result["hit"] = True


@register_move_special("glaciate")
def _glaciate_speed_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-1,
        description=f"{ctx.move.name} lowers Speed.",
    )
    if _effect_roll(ctx) % 2 == 0 and ctx.battle._is_actor_grounded(ctx.defender):
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Slowed",
            effect="slow",
            description=f"{ctx.move.name} slows grounded targets on even rolls.",
        )


@register_move_special("ice fang")
def _ice_fang_status(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    roll = _effect_roll(ctx)
    if roll < 18:
        return
    if roll == 20:
        statuses = ("Frozen", "Flinched")
    else:
        statuses = ("Frozen",) if ctx.battle.rng.randint(1, 2) == 1 else ("Flinched",)
    for status in statuses:
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status=status,
            effect=status.lower(),
            description=f"{ctx.move.name} inflicts {status}.",
            remaining=1 if status == "Flinched" else None,
        )


@register_move_special("leech seed")
def _leech_seed(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Leech Seed",
        effect="leech_seed",
        description="Leech Seed is applied.",
    )
    for status in ctx.defender.statuses:
        entry = status if isinstance(status, dict) else None
        if entry and str(entry.get("name") or "").strip().lower() == "leech seed":
            entry.setdefault("source_id", ctx.attacker_id)
            break


@register_move_special("belly drum")
def _belly_drum(ctx: MoveSpecialContext) -> None:
    max_hp = ctx.attacker.max_hp()
    loss = max(1, max_hp // 2)
    ctx.attacker.lose_hp(loss)
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=6,
        description="Belly Drum sharply raises Attack.",
    )


@register_move_special("flash")
def _flash_accuracy(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        description="Flash lowers Accuracy.",
    )


@register_move_special("reflect")
def _reflect_status(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    ctx.defender.statuses.append({"name": "Reflect", "charges": 2})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "reflect",
            "description": "Reflect shields against physical damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("light screen")
def _light_screen_status(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    ctx.defender.statuses.append({"name": "Light Screen", "charges": 2})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "light_screen",
            "description": "Light Screen shields against special damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("shell smash")
def _shell_smash_stats(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.attacker is None:
        return
    for stat in ("atk", "spatk", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=2,
            description="Shell Smash raises offensive stats and Speed.",
            effect="shell_smash",
        )
    for stat in ("def", "spdef"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=-1,
            description="Shell Smash lowers defenses.",
            effect="shell_smash",
        )


@register_move_special("stuff cheeks")
def _stuff_cheeks(ctx: MoveSpecialContext) -> None:
    events = ctx.battle._apply_food_buff_start(ctx.attacker_id, force=True)
    ctx.events.extend(events)
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=2,
        description="Stuff Cheeks raises Defense.",
    )       


@register_move_special("venom drench")
def _venom_drench_stats(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not (ctx.defender.has_status("Poisoned") or ctx.defender.has_status("Badly Poisoned")):
        return
    for stat in ("atk", "spatk", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=-1,
            description="Venom Drench lowers poisoned targets' stats.",
            effect="venom_drench",
        )


@register_move_special("yawn")
def _yawn_drowsy(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Drowsy",
        effect="drowsy",
        description="Yawn makes the target drowsy.",
    )


@register_move_special("yawn", phase="pre_damage")
def _yawn_cannot_miss(ctx: MoveSpecialContext) -> None:
    text = _normalize_effects_text(_effects_text_for(ctx.move)).lower()
    if "cannot miss" in text or "always hit" in text:
        ctx.result["hit"] = True


@register_move_special("conversion")
def _conversion(ctx: MoveSpecialContext) -> None:
    options = []
    if hasattr(ctx.battle, "_conversion_type_options"):
        options = list(ctx.battle._conversion_type_options(ctx.attacker))
    if not options:
        return
    chosen = str(ctx.move_params.get("chosen_type") or "").strip().title()
    if chosen not in options:
        chosen = str(options[0])
    ctx.attacker.spec.types = [chosen]
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "conversion",
            "new_type": chosen,
            "description": "Conversion changes the user's type.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("entrainment")
def _entrainment(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    abilities = ctx.attacker.ability_names()
    if not abilities:
        return
    chosen = abilities[0]
    while ctx.defender.remove_temporary_effect("entrained_ability"):
        continue
    ctx.defender.add_temporary_effect(
        "entrained_ability",
        ability=chosen,
        expires_round=ctx.battle.round + 3,
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "entrainment",
            "ability": chosen,
            "description": "Entrainment grants the user's ability.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("bestow")
def _bestow_transfer_item(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_items = list(ctx.attacker.spec.items or [])
    defender_items = list(ctx.defender.spec.items or [])
    if not attacker_items or defender_items:
        return
    gifted = attacker_items.pop(0)
    ctx.attacker.spec.items = attacker_items
    ctx.defender.spec.items = defender_items + [gifted]
    item_name = _item_name_text(gifted)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "bestow",
            "item": item_name,
            "description": f"Bestow transfers {item_name} to the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("covet")
def _covet_steal_item(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_items = list(ctx.attacker.spec.items or [])
    defender_items = list(ctx.defender.spec.items or [])
    if attacker_items or not defender_items:
        return
    stolen = defender_items.pop(0)
    ctx.defender.spec.items = defender_items
    ctx.attacker.spec.items = attacker_items + [stolen]
    item_name = _item_name_text(stolen)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "covet",
            "item": item_name,
            "description": f"Covet steals {item_name}.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_global_move_special(phase="pre_damage")
def _crash_on_miss_from_text(ctx: MoveSpecialContext) -> None:
    if ctx.result.get("hit"):
        return
    if ctx.result.get("blocked_by_shield"):
        return
    text = _normalize_effects_text(_effects_text_for(ctx.move)).lower()
    if "miss" not in text or "hit points" not in text:
        return
    if not move_has_crash_trait(ctx.move) and "1/4" not in text and "1/4th" not in text:
        return
    max_hp = ctx.attacker.max_hp()
    loss = max(1, max_hp // 4)
    before = ctx.attacker.hp or 0
    ctx.attacker.apply_damage(loss)
    dealt = max(0, before - (ctx.attacker.hp or 0))
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "crash",
            "amount": dealt,
            "description": f"{ctx.move.name} crashes on a miss.",
            "target_hp": ctx.attacker.hp,
        }
    )

@register_move_special(*_DRAIN_MOVES_HALF)
def _drain_half_damage(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    if ctx.damage_dealt <= 0:
        return
    drain_amount = max(0, int(ctx.damage_dealt) // 2)
    if drain_amount <= 0:
        return
    if ctx.defender.has_ability("Liquid Ooze"):
        ability_name = "Liquid Ooze"
        if has_ability_exact(ctx.defender, "Liquid Ooze [Errata]"):
            ability_name = "Liquid Ooze [Errata]"
        before = ctx.attacker.hp or 0
        ctx.attacker.apply_damage(drain_amount)
        dealt = max(0, before - (ctx.attacker.hp or 0))
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": ability_name,
                "move": ctx.move.name,
                "effect": "drain_reversal",
                "amount": dealt,
                "description": "Liquid Ooze harms drain users instead of healing them.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.heal(drain_amount)
    effect = "absorb" if ctx.move_name == "absorb" else "drain_heal"
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": effect,
            "amount": drain_amount,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("overdrive")
def _overdrive_heal(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if ctx.damage_dealt <= 0:
        return
    heal_amount = max(0, int(ctx.damage_dealt) // 2)
    if heal_amount <= 0:
        return
    ctx.attacker.heal(heal_amount)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "overdrive_heal",
            "amount": heal_amount,
            "target_hp": ctx.attacker.hp,
        }
    )


def _apply_simple_status(
    ctx: MoveSpecialContext,
    *,
    status: str,
    effect: str,
    threshold: Optional[int] = None,
    remaining: Optional[int] = None,
) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if threshold is not None and _effect_roll(ctx) < threshold:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status=status,
        effect=effect,
        description=f"{ctx.move.name} inflicts {status}.",
        remaining=remaining,
    )


def _apply_stage_delta(
    ctx: MoveSpecialContext,
    *,
    target: str,
    stat: str,
    delta: int,
    effect: str,
    require_hit: bool = True,
) -> None:
    if require_hit and not ctx.hit:
        return
    if target == "attacker":
        target_id = ctx.attacker_id
        target_state = ctx.attacker
    else:
        target_id = ctx.defender_id
        target_state = ctx.defender
    if target_state is None or target_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=target_id,
        move=ctx.move,
        target=target_state,
        stat=stat,
        delta=delta,
        effect=effect,
        description=f"{ctx.move.name} modifies {stat}.",
    )


@register_move_special("fling")
def _fling(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if not ctx.attacker.spec.items:
        return
    item = ctx.attacker.spec.items.pop(0)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "fling",
            "item": item,
            "description": "Fling throws a held item.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("hyperspace fury", phase="pre_damage")
def _hyperspace_fury_interrupt_block(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("no_interrupts", expires_round=ctx.battle.round)


@register_move_special("hyperspace fury")
def _hyperspace_fury_defense_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="def", delta=-1, effect="hyperspace_fury")
    _create_dimensional_rift(ctx)


@register_move_special("payback")
def _payback_noop(ctx: MoveSpecialContext) -> None:
    return


@register_move_special("snarl")
def _snarl_spatk_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spatk", delta=-1, effect="snarl")


@register_move_special("breaking swipe")
def _breaking_swipe_atk_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="atk", delta=-1, effect="breaking_swipe")


@register_move_special("spirit break")
def _spirit_break_spatk_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spatk", delta=-1, effect="spirit_break")


@register_move_special("electroweb", "bulldoze")
def _aoe_speed_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spd", delta=-1, effect="aoe_speed_drop")


@register_move_special("cotton spore")
def _cotton_spore_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spd", delta=-2, effect="cotton_spore")


@register_move_special("decoratee", "decorate")
def _decorate_buff(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="atk", delta=2, effect="decorate")
    _apply_stage_delta(ctx, target="defender", stat="spatk", delta=2, effect="decorate")


@register_move_special("hammer arm")
def _hammer_arm_slow(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="spd", delta=-1, effect="hammer_arm")


@register_move_special("flame charge")
def _flame_charge_speed(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="spd", delta=1, effect="flame_charge")


@register_move_special("v-create")
def _vcreate_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="def", delta=-1, effect="vcreate")
    _apply_stage_delta(ctx, target="attacker", stat="spdef", delta=-1, effect="vcreate")
    _apply_stage_delta(ctx, target="attacker", stat="spd", delta=-1, effect="vcreate")


@register_move_special("submission")
def _submission_trip(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Tripped", effect="trip", threshold=15)


@register_move_special("sandstorm sear")
def _sandstorm_sear_burn(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Burned", effect="burn", threshold=15)


@register_move_special("pyro ball")
def _pyro_ball_burn(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Burned", effect="burn", threshold=19)


@register_move_special("wildbolt storm")
def _wildbolt_storm_paralyze(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Paralyzed", effect="paralysis", threshold=15)


@register_move_special("blaze kick")
def _blaze_kick(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Burned", effect="burn", threshold=19)


@register_move_special("blue flare")
def _blue_flare(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Burned", effect="burn", threshold=17)


@register_move_special("blast burn")
def _blast_burn_burn(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Burned", effect="burn", threshold=17)


@register_move_special("body slam")
def _body_slam(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Paralyzed", effect="paralysis", threshold=15)


@register_move_special("bolt strike")
def _bolt_strike(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Paralyzed", effect="paralysis", threshold=17)


@register_move_special("bubble")
def _bubble(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spd", delta=-1, effect="bubble", require_hit=True)
    if _effect_roll(ctx) < 16:
        return


@register_move_special("bubblebeam")
def _bubblebeam(ctx: MoveSpecialContext) -> None:
    if _effect_roll(ctx) >= 18:
        _apply_stage_delta(ctx, target="defender", stat="spd", delta=-1, effect="bubblebeam", require_hit=True)


@register_move_special("bulk up")
def _bulk_up(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="atk", delta=1, effect="bulk_up", require_hit=False)
    _apply_stage_delta(ctx, target="attacker", stat="def", delta=1, effect="bulk_up", require_hit=False)


@register_move_special("captivate")
def _captivate(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.spec.gender and ctx.defender.spec.gender:
        if ctx.attacker.spec.gender.strip().lower() == ctx.defender.spec.gender.strip().lower():
            return
    if not ctx.attacker.spec.gender or not ctx.defender.spec.gender:
        return
    _apply_stage_delta(ctx, target="defender", stat="spatk", delta=-2, effect="captivate")


@register_move_special("charm")
def _charm(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="atk", delta=-2, effect="charm", require_hit=False)


@register_move_special("chatter")
def _chatter(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Confused", effect="confusion", threshold=16)


@register_move_special("confusion")
def _confusion_status(ctx: MoveSpecialContext) -> None:
    if ctx.attacker is not None and has_ability_exact(ctx.attacker, "Migraine [Errata]"):
        max_hp = ctx.attacker.max_hp()
        current_hp = ctx.attacker.hp or 0
        if max_hp > 0 and current_hp * 2 <= max_hp:
            return
    _apply_simple_status(ctx, status="Confused", effect="confusion", threshold=19)


@register_move_special("confusion")
def _confusion_migraine_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Migraine [Errata]"):
        return
    pending = next(iter(ctx.attacker.get_temporary_effects("migraine_errata_pending")), None)
    if pending is None:
        return
    if isinstance(pending, dict):
        pending_round = pending.get("round")
        if pending_round is not None and int(pending_round) != ctx.battle.round:
            ctx.attacker.remove_temporary_effect("migraine_errata_pending")
            return
        pending_move = str(pending.get("move") or "").strip().lower()
        if pending_move and pending_move != ctx.move_name:
            ctx.attacker.remove_temporary_effect("migraine_errata_pending")
            return
        pending_target = str(pending.get("target") or "")
        if pending_target and pending_target != ctx.defender_id:
            ctx.attacker.remove_temporary_effect("migraine_errata_pending")
            return
    ctx.attacker.remove_temporary_effect("migraine_errata_pending")
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("migraine_errata_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 2:
        return
    _apply_simple_status(ctx, status="Confused", effect="migraine_errata_confusion")
    if used_entry is None:
        ctx.attacker.add_temporary_effect("migraine_errata_used", count=used_count + 1)
    else:
        used_entry["count"] = used_count + 1
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Migraine [Errata]",
            "move": ctx.move.name,
            "effect": "confusion_crit",
            "description": "Migraine [Errata] empowers Confusion.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("confide")
def _confide(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spatk", delta=-1, effect="confide", require_hit=False)


@register_move_special("close combat")
def _close_combat(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="def", delta=-1, effect="close_combat", require_hit=True)
    _apply_stage_delta(ctx, target="attacker", stat="spdef", delta=-1, effect="close_combat", require_hit=True)


@register_move_special("crush claw")
def _crush_claw(ctx: MoveSpecialContext) -> None:
    if _effect_roll(ctx) % 2 == 0:
        _apply_stage_delta(ctx, target="defender", stat="def", delta=-1, effect="crush_claw", require_hit=True)


@register_move_special("dark pulse")
def _dark_pulse(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Flinched", effect="flinch", threshold=17, remaining=1)


@register_move_special("drum beating")
def _drum_beating(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spd", delta=-1, effect="drum_beating", require_hit=True)


@register_move_special("fell stinger")
def _fell_stinger(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    if not ctx.defender.fainted:
        return
    _apply_stage_delta(ctx, target="attacker", stat="atk", delta=2, effect="fell_stinger", require_hit=False)


@register_move_special("fleur cannon")
def _fleur_cannon(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="spatk", delta=-2, effect="fleur_cannon", require_hit=True)


@register_move_special("fire lash")
def _fire_lash(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="def", delta=-1, effect="fire_lash", require_hit=True)


@register_move_special("grav apple")
def _grav_apple(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="def", delta=-1, effect="grav_apple", require_hit=True)


@register_move_special("ice hammer")
def _ice_hammer(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="spd", delta=-1, effect="ice_hammer", require_hit=True)


@register_move_special("liquidation")
def _liquidation(ctx: MoveSpecialContext) -> None:
    if _effect_roll(ctx) >= 17:
        _apply_stage_delta(ctx, target="defender", stat="def", delta=-1, effect="liquidation", require_hit=True)


@register_move_special("steam eruption")
def _steam_eruption(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Burned", effect="burn", threshold=15)


@register_move_special("smart strike", phase="pre_damage")
def _smart_strike_hits(ctx: MoveSpecialContext) -> None:
    ctx.result["hit"] = True


@register_move_special("double iron bash")
def _double_iron_bash(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Flinched", effect="flinch", threshold=15, remaining=1)


@register_move_special("brutal swing")
def _brutal_swing_sleep(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Sleep", effect="sleep")


@register_move_special("defend order")
def _defend_order(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="def", delta=1, effect="defend_order", require_hit=False)
    _apply_stage_delta(ctx, target="attacker", stat="spdef", delta=1, effect="defend_order", require_hit=False)


@register_move_special("diamond storm")
def _diamond_storm(ctx: MoveSpecialContext) -> None:
    if _effect_roll(ctx) % 2 == 0:
        _apply_stage_delta(ctx, target="attacker", stat="def", delta=1, effect="diamond_storm", require_hit=True)


@register_move_special("discharge")
def _discharge(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Paralyzed", effect="paralysis", threshold=15)


@register_move_special("draco meteor")
def _draco_meteor(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="spatk", delta=-2, effect="draco_meteor", require_hit=True)
@register_move_special("brave bird")
def _brave_bird(ctx: MoveSpecialContext) -> None:
    # Forced movement handled by battle_state if push keyword parsed.
    return


@register_move_special("bleakwind storm")
def _bleakwind_storm_status(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Flinched", effect="flinch", threshold=15, remaining=1)
    _apply_simple_status(ctx, status="Frozen", effect="freeze", threshold=19)


@register_move_special("astral barrage")
def _astral_barrage_slow(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Slowed", effect="slow", remaining=1)


@register_move_special("springtide storm")
def _springtide_storm(ctx: MoveSpecialContext) -> None:
    if _effect_roll(ctx) < 16:
        return
    name_parts = [
        str(ctx.attacker.spec.name or "").lower(),
        str(ctx.attacker.spec.species or "").lower(),
    ]
    is_therian = any("therian" in part for part in name_parts)
    stats = ("atk", "def", "spatk", "spdef", "spd")
    if is_therian:
        for stat in stats:
            _apply_stage_delta(ctx, target="defender", stat=stat, delta=-1, effect="springtide_storm")
    else:
        for stat in stats:
            _apply_stage_delta(ctx, target="attacker", stat=stat, delta=1, effect="springtide_storm")


@register_move_special("rototiller")
def _rototiller(ctx: MoveSpecialContext) -> None:
    def _is_grass(pokemon: Optional["PokemonState"]) -> bool:
        if pokemon is None:
            return False
        return any(str(t).strip().lower() == "grass" for t in pokemon.spec.types)

    if _is_grass(ctx.attacker):
        _apply_stage_delta(ctx, target="attacker", stat="atk", delta=1, effect="rototiller")
        _apply_stage_delta(ctx, target="attacker", stat="spatk", delta=1, effect="rototiller")
    if _is_grass(ctx.defender):
        _apply_stage_delta(ctx, target="defender", stat="atk", delta=1, effect="rototiller")
        _apply_stage_delta(ctx, target="defender", stat="spatk", delta=1, effect="rototiller")


@register_move_special("roar of time", phase="pre_damage")
def _roar_of_time_slow(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="slow",
        description=f"{ctx.move.name} slows the target.",
        remaining=1,
    )


@register_move_special("eternabeam", phase="pre_damage")
def _eternabeam_slow(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="slow",
        description=f"{ctx.move.name} slows the target.",
        remaining=1,
    )


@register_move_special("scale shot")
def _scale_shot_buff(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="spd", delta=1, effect="scale_shot")
    _apply_stage_delta(ctx, target="attacker", stat="def", delta=-1, effect="scale_shot")


@register_move_special("clanging scales")
def _clanging_scales_def_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="def", delta=-1, effect="clanging_scales")


@register_move_special("dragon tail", "circle throw", "wicked blow")
def _push_trip_moves(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Tripped", effect="trip", threshold=15)


@register_move_special("hydro cannon")
def _hydro_cannon_push(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    ctx.battle._apply_push(ctx.attacker_id, ctx.defender_id, distance=3)


@register_move_special("outrage", "thrash", "petal dance")
def _rage_confuse(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        status="Enraged",
        effect="enraged",
        description=f"{ctx.move.name} enrages the user.",
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        status="Confused",
        effect="confusion",
        description=f"{ctx.move.name} confuses the user.",
    )


@register_move_special("burn up")
def _burn_up_remove_fire(ctx: MoveSpecialContext) -> None:
    types = [t for t in ctx.attacker.spec.types if str(t).strip().lower() != "fire"]
    if not types:
        types = ["Normal"]
    ctx.attacker.spec.types = types
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "burn_up",
            "new_types": list(types),
            "description": "Burn Up removes the Fire type.",
            "target_hp": ctx.attacker.hp,
        }
    )


def _add_temporary_type(ctx: MoveSpecialContext, new_type: str, *, effect: str) -> None:
    if ctx.defender is None:
        return
    normalized = str(new_type).strip().title()
    types = [t for t in ctx.defender.spec.types if t]
    if normalized not in {str(t).strip().title() for t in types}:
        types.append(normalized)
        ctx.defender.spec.types = types
    ctx.defender.add_temporary_effect("type_added", type=normalized, expires_round=ctx.battle.round + 5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": effect,
            "new_type": normalized,
            "description": f"{ctx.move.name} adds the {normalized} type.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("forest's curse")
def _forests_curse(ctx: MoveSpecialContext) -> None:
    _add_temporary_type(ctx, "Grass", effect="forest_curse")


@register_move_special("magic powder")
def _magic_powder(ctx: MoveSpecialContext) -> None:
    _add_temporary_type(ctx, "Psychic", effect="magic_powder")


@register_move_special("soak")
def _soak(ctx: MoveSpecialContext) -> None:
    _add_temporary_type(ctx, "Water", effect="soak")


@register_move_special("mystical power")
def _mystical_power(ctx: MoveSpecialContext) -> None:
    stats = {
        "atk": ctx.attacker.spec.atk,
        "def": ctx.attacker.spec.defense,
        "spatk": ctx.attacker.spec.spatk,
        "spdef": ctx.attacker.spec.spdef,
        "spd": ctx.attacker.spec.spd,
    }
    best_stat = max(stats.items(), key=lambda item: item[1])[0]
    _apply_stage_delta(ctx, target="attacker", stat=best_stat, delta=1, effect="mystical_power")


@register_move_special("energy blast")
def _energy_blast(ctx: MoveSpecialContext) -> None:
    if _effect_roll(ctx) >= 19:
        _apply_stage_delta(ctx, target="attacker", stat="spatk", delta=1, effect="energy_blast")


@register_move_special("energy sphere")
def _energy_sphere(ctx: MoveSpecialContext) -> None:
    if _effect_roll(ctx) >= 19:
        _apply_stage_delta(ctx, target="attacker", stat="spdef", delta=1, effect="energy_sphere")


@register_move_special("esper wing", phase="pre_damage")
def _esper_wing_crit(ctx: MoveSpecialContext) -> None:
    roll = int(ctx.result.get("roll") or 0)
    if roll >= 18:
        ctx.result["crit"] = True


@register_move_special("spacial rend", phase="pre_damage")
def _spacial_rend_crit(ctx: MoveSpecialContext) -> None:
    roll = int(ctx.result.get("roll") or 0)
    if roll % 2 == 0:
        ctx.result["crit"] = True


@register_move_special("wicked blow", phase="pre_damage")
def _wicked_blow_crit(ctx: MoveSpecialContext) -> None:
    if ctx.result.get("hit"):
        ctx.result["crit"] = True


@register_move_special("deadly strike", phase="pre_damage")
def _deadly_strike_crit(ctx: MoveSpecialContext) -> None:
    if ctx.result.get("hit"):
        ctx.result["crit"] = True


@register_move_special("magic burst")
def _magic_burst_block_aoo(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    ctx.defender.add_temporary_effect("aoo_blocked", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "aoo_blocked",
            "description": "Magic Burst blocks attacks of opportunity.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("cone of force")
def _cone_of_force(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="evasion", delta=-2, effect="cone_of_force")


@register_move_special("furious strikes")
def _furious_strikes(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    hits = int(ctx.result.get("strike_hits") or 1)
    if hits <= 0:
        return
    _apply_stage_delta(ctx, target="defender", stat="evasion", delta=-hits, effect="furious_strikes")


@register_move_special("coaching", "howl [ss]")
def _coaching_howl(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="atk", delta=1, effect="coaching")
    if (ctx.move.name or "").strip().lower() == "coaching":
        _apply_stage_delta(ctx, target="attacker", stat="def", delta=1, effect="coaching")
    if ctx.defender is not None and ctx.defender_id is not None:
        try:
            same_team = ctx.battle._team_for(ctx.attacker_id) == ctx.battle._team_for(ctx.defender_id)
        except Exception:
            same_team = False
        if same_team:
            _apply_stage_delta(ctx, target="defender", stat="atk", delta=1, effect="coaching")
            if (ctx.move.name or "").strip().lower() == "coaching":
                _apply_stage_delta(ctx, target="defender", stat="def", delta=1, effect="coaching")


@register_move_special("magnetic flux", "magnetic flux [sm]")
def _magnetic_flux(ctx: MoveSpecialContext) -> None:
    def _has_plus_minus(pokemon: Optional["PokemonState"]) -> bool:
        if pokemon is None:
            return False
        return pokemon.has_ability("Plus") or pokemon.has_ability("Minus")

    if _has_plus_minus(ctx.attacker):
        _apply_stage_delta(ctx, target="attacker", stat="def", delta=1, effect="magnetic_flux")
        _apply_stage_delta(ctx, target="attacker", stat="spdef", delta=1, effect="magnetic_flux")
    if _has_plus_minus(ctx.defender):
        _apply_stage_delta(ctx, target="defender", stat="def", delta=1, effect="magnetic_flux")
        _apply_stage_delta(ctx, target="defender", stat="spdef", delta=1, effect="magnetic_flux")


@register_move_special("gear up", "gear up [ss]")
def _gear_up(ctx: MoveSpecialContext) -> None:
    def _has_plus_minus(pokemon: Optional["PokemonState"]) -> bool:
        if pokemon is None:
            return False
        return pokemon.has_ability("Plus") or pokemon.has_ability("Minus")

    if _has_plus_minus(ctx.attacker):
        _apply_stage_delta(ctx, target="attacker", stat="atk", delta=1, effect="gear_up")
        _apply_stage_delta(ctx, target="attacker", stat="spatk", delta=1, effect="gear_up")
    if _has_plus_minus(ctx.defender):
        _apply_stage_delta(ctx, target="defender", stat="atk", delta=1, effect="gear_up")
        _apply_stage_delta(ctx, target="defender", stat="spatk", delta=1, effect="gear_up")


@register_move_special("brick break")
def _brick_break(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    ctx.defender.statuses = [
        entry
        for entry in ctx.defender.statuses
        if str(entry.get("name") or "").strip().lower() not in {"reflect", "light screen"}
    ]
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "brick_break",
            "description": "Brick Break shatters screens.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("dynamic punch")
def _dynamic_punch_confuse(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Confused", effect="confusion")


@register_move_special("ion deluge")
def _ion_deluge(ctx: MoveSpecialContext) -> None:
    if ctx.battle.grid is None or ctx.attacker.position is None:
        return
    target_pos = ctx.attacker.position
    if ctx.defender is not None and ctx.defender.position is not None:
        target_pos = ctx.defender.position
    tiles = targeting.affected_tiles(ctx.battle.grid, ctx.attacker.position, target_pos, ctx.move)
    ctx.battle.zone_effects.append(
        {
            "name": "Ion Deluge",
            "tiles": sorted(list(tiles)),
            "remaining": 3,
        }
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "ion_deluge",
            "tiles": sorted(list(tiles)),
            "description": "Ion Deluge electrifies the area.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special(
    "beak blast",
    "focus punch",
    "low kick",
    "grass knot",
    "seismic toss",
    "night shade",
    "facade",
    "façade",
    "fa�ade",
    "acrobatics",
    "nature power",
    "meteor beam",
    "secret force",
    "freeze-dry",
    "hidden power ghost",
    "rock blast",
    "rock throw",
    "rock wrecker",
    "power whip",
    "high horsepower",
    "land's wrath",
    "mud sport",
    "name",
    "bide",
    "psywave",
    "bolt beak",
    "shadow sneak",
    "backswing",
    "pierce!",
    "salvo",
    "attack of opportunity",
    "disarm",
    "push",
    "trip",
    "body press",
    "scratch",
    "seed bomb",
)
def _noop_mark_handled(ctx: MoveSpecialContext) -> None:
    return


@register_move_special("oblivion wing")
def _oblivion_wing_heal(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    roll = int(ctx.result.get("damage_roll") or 0)
    if roll <= 0:
        return
    if ctx.defender.has_ability("Liquid Ooze"):
        ability_name = "Liquid Ooze"
        if has_ability_exact(ctx.defender, "Liquid Ooze [Errata]"):
            ability_name = "Liquid Ooze [Errata]"
        before = ctx.attacker.hp or 0
        ctx.attacker.apply_damage(roll)
        dealt = max(0, before - (ctx.attacker.hp or 0))
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": ability_name,
                "move": ctx.move.name,
                "effect": "drain_reversal",
                "amount": dealt,
                "description": "Liquid Ooze harms drain users instead of healing them.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.heal(roll)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "drain_heal",
            "amount": roll,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("accelerock")
def _accelerock_dash(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    keywords = {str(k).strip().lower() for k in (ctx.move.keywords or [])}
    if "dash" not in keywords:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "accelerock_dash",
            "dash": True,
            "priority": ctx.move.priority,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("accelerock")
def _accelerock_ancient_power_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if _effect_roll(ctx) < 19:
        return
    for stat in ("atk", "def", "spatk", "spdef", "spd"):
        _apply_stage_delta(ctx, target="attacker", stat=stat, delta=1, effect="accelerock_boost")


@register_move_special("acid")
def _acid_lower_spdef(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    roll = ctx.battle.rng.randint(1, 100)
    if roll > 20:
        return
    before = ctx.defender.combat_stages.get("spdef", 0)
    after = max(-6, min(6, before - 1))
    if after == before:
        return
    ctx.defender.combat_stages["spdef"] = after
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "acid_lower_spdef",
            "roll": roll,
            "duration": roll,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("acid spray")
def _acid_spray_lower_spdef(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    before = ctx.defender.combat_stages.get("spdef", 0)
    after = max(-6, min(6, before - 2))
    amount = abs(after - before)
    if amount <= 0:
        return
    ctx.defender.combat_stages["spdef"] = after
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "acid_spray_lower_spdef",
            "amount": amount,
            "duration": 5,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("acupressure")
def _acupressure_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = ctx.battle.rng.randint(1, 8)
    mapping = {
        1: "atk",
        2: "def",
        3: "spatk",
        4: "spdef",
        5: "spd",
        6: "accuracy",
        7: "evasion",
    }
    stat = mapping.get(roll)
    if stat is None:
        candidates = ["atk", "def", "spatk", "spdef", "spd", "accuracy", "evasion"]
        lowest = min(ctx.attacker.combat_stages.get(s, 0) for s in candidates)
        stat = next(s for s in candidates if ctx.attacker.combat_stages.get(s, 0) == lowest)
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat=stat,
        delta=2,
        description="Acupressure sharply raises a combat stage.",
        effect="acupressure_boost",
        roll=roll,
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "acupressure_boost",
            "stat": stat,
            "roll": roll,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("after you")
def _after_you_reschedule(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    event = ctx.battle._schedule_after_you_target(ctx.attacker_id, ctx.defender_id, ctx.move.name)
    if event:
        ctx.events.append(event)


@register_move_special("agility")
def _agility_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    before = ctx.attacker.combat_stages.get("spd", 0)
    new_stage = max(-6, min(6, before + 2))
    if new_stage == before:
        return
    ctx.attacker.combat_stages["spd"] = new_stage
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "agility",
            "stat": "spd",
            "amount": new_stage - before,
            "new_stage": new_stage,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("air cutter")
def _air_cutter_crit(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.result.get("crit"):
        return
    roll = ctx.result.get("roll")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "air_cutter_crit",
            "roll": roll,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("air slash")
def _air_slash_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    if not ctx.defender.has_status("Flinch"):
        ctx.defender.statuses.append({"name": "Flinch"})
        ctx.events.append(
            {
                "type": "status",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "flinch",
                "status": "Flinch",
                "roll": roll,
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("dual wingbeat")
def _dual_wingbeat_flinch(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Flinched", effect="flinch", threshold=15, remaining=1)


@register_move_special("amnesia")
def _amnesia_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spdef",
        delta=2,
        effect="amnesia",
        description="Amnesia sharply raises Special Defense.",
    )


@register_move_special("apple acid")
def _apple_acid_lower_spdef(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        effect="apple_acid",
        description="Apple Acid lowers the target's Special Defense.",
    )


@register_move_special("ancient power")
def _ancient_power_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    for stat in list(ctx.attacker.combat_stages.keys()):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="ancient_power",
            description="Ancient Power raises all combat stages.",
            roll=roll,
        )


@register_move_special("ally switch")
def _ally_switch(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.position is None or ctx.defender.position is None:
        return
    attacker_pos = ctx.attacker.position
    defender_pos = ctx.defender.position
    ctx.attacker.position = defender_pos
    ctx.defender.position = attacker_pos
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "ally_switch",
            "from_position": attacker_pos,
            "to_position": defender_pos,
            "target_from_position": defender_pos,
            "target_to_position": attacker_pos,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("aqua jet")
def _aqua_jet_priority(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "priority_attack",
            "priority": ctx.move.priority,
            "roll": ctx.result.get("roll"),
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("aqua ring")
def _aqua_ring(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        status="Aqua Ring",
        effect="aqua_ring",
        description="Aqua Ring coats the user in healing water.",
    )
    if ctx.attacker.has_ability("Refreshing Veil"):
        if ctx.attacker.get_temporary_effects("refreshing_veil_used"):
            return
        cured = ctx.battle._remove_statuses_by_set(
            ctx.attacker, _STATUS_CONDITIONS_TO_CURE, limit=None
        )
        if cured:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "ability": "Refreshing Veil",
                    "move": ctx.move.name,
                    "effect": "cure",
                    "statuses": cured,
                    "description": "Refreshing Veil cures persistent status effects.",
                    "target_hp": ctx.attacker.hp,
                }
            )
        ctx.attacker.add_temporary_effect(
            "refreshing_veil_used",
            expires_round=ctx.battle.round + 999,
        )


@register_move_special("aqua tail")
def _aqua_tail_pass(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "aqua_tail_pass",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("assist")
def _assist_select_move(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    attacker_team = ctx.battle._team_for(ctx.attacker_id)
    candidate_names: List[str] = []
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != attacker_team:
            continue
        for move in mon.spec.moves:
            name = str(move.name or "").strip()
            if not name:
                continue
            if name.lower() == "assist":
                continue
            candidate_names.append(name)
    if not candidate_names:
        return
    chosen = ctx.battle.rng.choice(candidate_names)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "assist",
            "selected_move": chosen,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("aromatherapy")
def _aromatherapy(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    cured_targets: List[str] = []
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if mon.statuses:
            mon.statuses = []
            cured_targets.append(pid)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "aromatherapy",
            "cured": cured_targets,
        }
    )


@register_move_special("aromatic mist")
def _aromatic_mist(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    targets = [(ctx.attacker_id, ctx.attacker)]
    if ctx.defender_id and ctx.defender and ctx.defender_id != ctx.attacker_id:
        targets.append((ctx.defender_id, ctx.defender))
    for target_id, target in targets:
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=target_id,
            move=ctx.move,
            target=target,
            stat="spdef",
            delta=1,
            effect="aromatic_mist",
            description="Aromatic Mist raises Special Defense.",
        )


@register_move_special("assurance")
def _assurance_bonus(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    if ctx.defender_id not in ctx.battle.damage_this_round:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "assurance_bonus",
            "description": "Assurance boosts damage on previously hit targets.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("arcane fury")
def _arcane_fury_vulnerable(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Vulnerable",
        effect="vulnerable",
        description="Arcane Fury leaves the target vulnerable.",
        roll=roll,
        remaining=1,
    )


@register_move_special("arcane storm")
def _arcane_storm_slow(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="slowed",
        description="Arcane Storm slows the target.",
        roll=roll,
        remaining=1,
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Vulnerable",
        effect="vulnerable",
        description="Arcane Storm leaves the target vulnerable.",
        roll=roll,
        remaining=1,
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "arcane_storm",
            "roll": roll,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("anchor shot")
def _anchor_shot_trap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Trapped"):
        ctx.defender.statuses.append({"name": "Trapped", "remaining": 3})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "trapped",
            "status": "Trapped",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("attract")
def _attract_infatuate(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker_id == ctx.defender_id:
        return
    ignore_gender = False
    errata_burst = False
    for entry in list(ctx.attacker.get_temporary_effects("sonic_courtship_active")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            if entry in ctx.attacker.temporary_effects:
                ctx.attacker.temporary_effects.remove(entry)
            continue
        ignore_gender = True
        if str(entry.get("mode") or "").strip().lower() == "errata":
            errata_burst = True
            if entry in ctx.attacker.temporary_effects:
                ctx.attacker.temporary_effects.remove(entry)
        break
    if errata_burst:
        if ctx.attacker.position is None:
            return
        for pid, mon in ctx.battle.pokemon.items():
            if not mon.active or mon.fainted or mon.position is None:
                continue
            if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
                continue
            if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 3:
                continue
            ctx.battle._apply_status(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=pid,
                move=ctx.move,
                target=mon,
                status="Infatuated",
                effect="infatuated",
                description="Attract infatuates the target.",
                remaining=1,
            )
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": pid,
                    "ability": "Sonic Courtship [Errata]",
                    "move": ctx.move.name,
                    "effect": "sonic_courtship",
                    "description": "Sonic Courtship expands Attract into a burst.",
                    "target_hp": mon.hp,
                }
            )
        return
    if not ignore_gender:
        if ctx.attacker.gender() == "unknown" or ctx.defender.gender() == "unknown":
            return
        if ctx.attacker.gender() == ctx.defender.gender():
            return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Infatuated",
        effect="infatuated",
        description="Attract infatuates the target.",
        remaining=1,
    )
    if ignore_gender:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Sonic Courtship",
                "move": ctx.move.name,
                "effect": "sonic_courtship",
                "description": "Sonic Courtship ignores gender restrictions.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("aura wheel")
def _aura_wheel_speed(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    before = ctx.attacker.combat_stages.get("spd", 0)
    after = max(-6, min(6, before + 1))
    if after == before:
        return
    ctx.attacker.combat_stages["spd"] = after
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "aura_wheel",
            "stat": "spd",
            "amount": after - before,
            "new_stage": after,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("aurora beam")
def _aurora_beam_lower_attack(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 18:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="aurora_beam",
        description="Aurora Beam lowers Attack on 18+.",
        roll=roll,
    )


@register_move_special("aurora veil")
def _aurora_veil(ctx: MoveSpecialContext) -> None:
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "hail" not in weather and "snow" not in weather:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "move": ctx.move.name,
                "effect": "aurora_veil_fail",
                "description": "Aurora Veil fails without hail.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if not mon.has_status("Aurora Veil"):
            mon.statuses.append({"name": "Aurora Veil", "remaining": 4})
        ctx.events.append(
            {
                "type": "status",
                "actor": ctx.attacker_id,
                "target": pid,
                "move": ctx.move.name,
                "effect": "aurora_veil",
                "status": "Aurora Veil",
                "target_hp": mon.hp,
            }
        )


@register_move_special("autotomize")
def _autotomize_speed(ctx: MoveSpecialContext) -> None:
    before = ctx.attacker.combat_stages.get("spd", 0)
    after = max(-6, min(6, before + 2))
    if after == before:
        return
    ctx.attacker.combat_stages["spd"] = after
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "autotomize",
            "stat": "spd",
            "amount": after - before,
            "new_stage": after,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("baby-doll eyes")
def _baby_doll_eyes(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="baby_doll_eyes",
        description="Baby-Doll Eyes lowers Attack by -1 CS.",
    )


@register_move_special("bane")
def _bane_status(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Bane"):
        ctx.defender.statuses.append({"name": "Bane", "remaining": 3})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "bane",
            "status": "Bane",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("block", "spider web", "snap trap", phase="end_action")
def _simple_trap(ctx: MoveSpecialContext) -> None:
    if not ctx.defender or not ctx.hit:
        return
    remaining = 1
    if ctx.move_name == "spider web":
        remaining = 3
    apply_trap_status(
        ctx.battle,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        stuck=True,
        trapped=True,
        remaining=remaining,
        effect="trap",
        description="The target is trapped.",
        roll=ctx.result.get("roll"),
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "trap",
            "description": "The target is trapped.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("daze")
def _daze_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="daze",
        description="Daze puts the target to sleep on a hit.",
    )


@register_move_special("spore")
def _spore_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="spore",
        description="Spore puts the target to sleep.",
    )
    if ctx.attacker.has_ability("Dire Spore"):
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Poisoned",
            effect="dire_spore",
            description="Dire Spore adds poison on Spore.",
        )


@register_move_special("forewarn")
def _forewarn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    moves = [move for move in ctx.defender.spec.moves if move is not None]
    if not moves:
        return
    max_db = max(int(move.db or 0) for move in moves)
    warned = [str(move.name or "").strip() for move in moves if int(move.db or 0) == max_db]
    ctx.defender.add_temporary_effect(
        "forewarn_penalty",
        source_id=ctx.attacker_id,
        moves=warned,
        amount=2,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Forewarn",
            "move": ctx.move.name,
            "effect": "reveal",
            "moves": warned,
            "description": "Forewarn reveals the target's strongest moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("baneful bunker")
def _baneful_bunker(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Baneful Bunker"):
        ctx.attacker.statuses.append({"name": "Baneful Bunker"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "baneful_bunker",
            "status": "Baneful Bunker",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("protect")
def _protect(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Protect"):
        ctx.attacker.statuses.append({"name": "Protect"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "protect",
            "status": "Protect",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("obstruct")
def _obstruct(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Obstruct"):
        ctx.attacker.statuses.append({"name": "Obstruct"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "obstruct",
            "status": "Obstruct",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("quick guard")
def _quick_guard(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Quick Guard"):
        ctx.attacker.statuses.append({"name": "Quick Guard"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "quick_guard",
            "status": "Quick Guard",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("double team")
def _double_team(ctx: MoveSpecialContext) -> None:
    # Grants 3 activations that boost accuracy or evasion by +2.
    while ctx.attacker.remove_temporary_effect("double_team"):
        continue
    ctx.attacker.add_temporary_effect("double_team", charges=3)
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "double_team",
            "status": "Double Team",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("barrier")
def _barrier_grid(ctx: MoveSpecialContext) -> None:
    if ctx.battle.grid is None or ctx.attacker.position is None:
        return
    x, y = ctx.attacker.position
    for coord in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if not ctx.battle.grid.in_bounds(coord):
            continue
        ctx.battle._place_barrier_segment(coord, source_id=ctx.attacker_id, move_name=ctx.move.name, source_name="Barrier")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "barrier",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("bash!")
def _bash_status(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    if not ctx.defender.has_status("Bashed"):
        ctx.defender.statuses.append({"name": "Bashed", "remaining": 1})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "bash",
            "status": "Bashed",
            "roll": roll,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("blessed touch")
def _blessed_touch_heal(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    healed = ctx.defender._apply_tick_heal(1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "blessed_touch",
            "amount": healed,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("bone club")
def _bone_club_bone_lord(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not has_ability_exact(ctx.attacker, "Bone Lord"):
        return
    if not ctx.defender.has_status("Flinch"):
        ctx.defender.statuses.append({"name": "Flinch"})
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Bone Lord",
            "move": ctx.move.name,
            "effect": "flinch",
            "status": "Flinch",
            "description": "Bone Lord forces a flinch on Bone Club.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("bone club")
def _bone_club_bone_lord_errata(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not has_ability_exact(ctx.attacker, "Bone Lord [Errata]"):
        return
    used = False
    for entry in ctx.attacker.get_temporary_effects("bone_lord_errata_used"):
        if str(entry.get("move") or "").strip().lower() == "bone club":
            used = True
            break
    if used:
        return
    ctx.attacker.add_temporary_effect("bone_lord_errata_used", move="bone club")
    for stat in ("def", "spatk"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=-1,
            effect="bone_lord_errata",
            description="Bone Lord [Errata] lowers the target's defenses.",
        )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Bone Lord [Errata]",
            "move": ctx.move.name,
            "effect": "stage_drop",
            "description": "Bone Lord [Errata] lowers Defense and Special Attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("bone rush", phase="pre_damage")
def _bone_rush_bone_lord_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Bone Lord [Errata]"):
        return
    used = False
    for entry in ctx.attacker.get_temporary_effects("bone_lord_errata_used"):
        if str(entry.get("move") or "").strip().lower() == "bone rush":
            used = True
            break
    if used:
        return
    ctx.attacker.add_temporary_effect("bone_lord_errata_used", move="bone rush")
    ctx.result["strike_hits_override"] = 4
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Bone Lord [Errata]",
            "move": ctx.move.name,
            "effect": "strike_override",
            "amount": 4,
            "description": "Bone Lord [Errata] forces Bone Rush to hit four times.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sacred fire", "scald", "scorching sands", "searing shot")
def _burn_move_high_roll(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    effect_tag = f"{ctx.move_name.replace(' ', '_')}_burn"
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect=effect_tag,
        description=f"{ctx.move.name} burns the target.",
        roll=roll,
    )


@register_move_special("origin pulse")
def _origin_pulse_burn(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Burned", effect="burn", threshold=15)


@register_move_special("toxic")
def _toxic_badly_poison(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    defender_types = {t.lower().strip() for t in ctx.defender.spec.types if t}
    if ("poison" in defender_types or "steel" in defender_types) and not ctx.attacker.has_ability(
        "Corrosion"
    ):
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Badly Poisoned",
        effect="toxic",
        description="Toxic badly poisons the target.",
        roll=int(ctx.result.get("roll") or 0),
    )


# Additional move-special handlers (D-R coverage)


@register_move_special("dragon breath")
def _dragon_breath_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll <= 0:
        roll = ctx.battle.rng.randint(1, 20)
    if roll < 16:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="dragon_breath",
        description="Dragon Breath paralyzes on a high roll.",
        roll=roll,
    )


@register_move_special("dragon dance")
def _dragon_dance_boost(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="dragon_dance",
        description="Dragon Dance raises Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spd",
        delta=1,
        effect="dragon_dance",
        description="Dragon Dance raises Speed.",
    )


@register_move_special("dragon ascent")
def _dragon_ascent_lower_defenses(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=-1,
        effect="dragon_ascent",
        description="Dragon Ascent lowers Defense.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spdef",
        delta=-1,
        effect="dragon_ascent",
        description="Dragon Ascent lowers Special Defense.",
    )


@register_move_special("false swipe")
def _false_swipe_survive(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.defender.hp is None:
        return
    if ctx.defender.hp <= 0 and ctx.damage_dealt > 0:
        ctx.defender.hp = 1
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "false_swipe",
                "description": "False Swipe leaves the target with 1 HP.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("fire fang")
def _fire_fang_burn_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 20:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect="fire_fang_burn",
        description="Fire Fang burns on a high roll.",
        roll=roll,
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="fire_fang_flinch",
        description="Fire Fang flinches on a high roll.",
        roll=roll,
    )


@register_move_special("sand attack")
def _sand_attack_lower_accuracy(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        effect="sand_attack",
        description="Sand Attack lowers Accuracy.",
    )


@register_move_special("sand tomb")
def _sand_tomb_trap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Vortex",
        effect="sand_tomb_vortex",
        description="Sand Tomb traps the target in a vortex.",
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Trapped",
        effect="sand_tomb_trap",
        description="Sand Tomb traps the target.",
    )


@register_move_special("sandstorm")
def _sandstorm_weather(ctx: MoveSpecialContext) -> None:
    ctx.battle.weather = "Sandstorm"
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "sandstorm",
            "weather": ctx.battle.weather,
            "description": "Sandstorm whips up harsh winds.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("secret power")
def _secret_power_environment(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    tile_type = ""
    if ctx.battle.grid is not None and ctx.attacker.position is not None:
        tile = ctx.battle.grid.tiles.get(ctx.attacker.position, {})
        if isinstance(tile, dict):
            tile_type = str(tile.get("type") or "").strip().lower()
    if "long grass" in tile_type:
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Drowsy",
            effect="secret_power",
            description="Secret Power applies a terrain effect.",
            roll=roll,
        )


@register_move_special("safeguard")
def _safeguard_blessing(ctx: MoveSpecialContext) -> None:
    blessed = ctx.battle._apply_safeguard_blessing(ctx.attacker.controller_id)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "safeguard",
            "blessed": blessed,
            "description": "Safeguard protects allies from status conditions.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("feather dance")
def _feather_dance_lower_attack(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-2,
        effect="feather_dance",
        description="Feather Dance sharply lowers Attack.",
    )


@register_move_special("force palm")
def _force_palm_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 18:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="force_palm",
        description="Force Palm paralyzes on a high roll.",
        roll=roll,
    )


@register_move_special("fire punch")
def _fire_punch_burn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect="fire_punch",
        description="Fire Punch burns on a high roll.",
        roll=roll,
    )


@register_move_special("flirt")
def _flirt_infatuate(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Infatuated",
        effect="flirt",
        description="Flirt infatuates the target.",
    )


@register_move_special("floral healing")
def _floral_healing(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    max_hp = ctx.defender.max_hp()
    terrain_name = str((ctx.battle.terrain or {}).get("name") or "").strip().lower()
    if "grassy" in terrain_name:
        amount = max_hp * 2 // 3
    else:
        amount = max_hp // 2
    before = ctx.defender.hp or 0
    ctx.defender.heal(amount)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "floral_healing",
            "amount": (ctx.defender.hp or 0) - before,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("flower shield")
def _flower_shield(ctx: MoveSpecialContext) -> None:
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        type_names = {str(t).strip().lower() for t in (mon.spec.types or [])}
        if "grass" not in type_names:
            continue
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=pid,
            move=ctx.move,
            target=mon,
            stat="def",
            delta=2,
            effect="increase",
            description="Flower Shield raises Defense for Grass allies.",
        )


@register_move_special("nightmare")
def _nightmare_bad_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Sleep"):
        return
    if not ctx.defender.has_status("Bad Sleep"):
        ctx.defender.statuses.append({"name": "Bad Sleep"})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "nightmare",
            "description": "Nightmare applies Bad Sleep.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("noble roar")
def _noble_roar_lower_stats(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="noble_roar",
        description="Noble Roar lowers Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=-1,
        effect="noble_roar",
        description="Noble Roar lowers Special Attack.",
    )


@register_move_special("nuzzle")
def _nuzzle_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="nuzzle",
        description="Nuzzle paralyzes on hit.",
    )


@register_move_special("no retreat")
def _no_retreat_boost(ctx: MoveSpecialContext) -> None:
    for stat in ("atk", "def", "spatk", "spdef", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="no_retreat",
            description="No Retreat raises all combat stages.",
        )
    if not ctx.attacker.has_status("No Retreat"):
        ctx.attacker.statuses.append({"name": "No Retreat"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "no_retreat",
            "status": "No Retreat",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("ominous wind")
def _ominous_wind_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    for stat in ("atk", "def", "spatk", "spdef", "spd", "accuracy"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="ominous_wind",
            description="Ominous Wind boosts all combat stages.",
            roll=roll,
        )


@register_move_special("pain split")
def _pain_split(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_hp = int(ctx.attacker.hp or 0)
    defender_hp = int(ctx.defender.hp or 0)
    attacker_loss = attacker_hp // 2
    defender_loss = defender_hp // 2
    shared = (attacker_loss + defender_loss) // 2
    if ctx.attacker.hp is not None:
        ctx.attacker.hp = min(ctx.attacker.max_hp(), attacker_hp - attacker_loss + shared)
    if ctx.defender.hp is not None:
        ctx.defender.hp = min(ctx.defender.max_hp(), defender_hp - defender_loss + shared)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "pain_split",
            "attacker_hp": ctx.attacker.hp,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("parting shot")
def _parting_shot(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="parting_shot",
        description="Parting Shot lowers Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=-1,
        effect="parting_shot",
        description="Parting Shot lowers Special Attack.",
    )
    team = ctx.battle._team_for(ctx.attacker_id)
    candidates = [
        pid
        for pid, mon in ctx.battle.pokemon.items()
        if pid != ctx.attacker_id
        and ctx.battle._team_for(pid) == team
        and mon.hp is not None
        and mon.hp > 0
        and not mon.active
    ]
    if candidates:
        candidates.sort()
        replacement_id = candidates[0]
        ctx.battle._apply_switch(
            outgoing_id=ctx.attacker_id,
            replacement_id=replacement_id,
            initiator_id=ctx.attacker_id,
            allow_replacement_turn=False,
            allow_immediate=False,
        )
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "parting_shot",
                "replacement": replacement_id,
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("pay day")
def _pay_day(ctx: MoveSpecialContext) -> None:
    roll = ctx.battle.rng.randint(1, 6)
    coins = int(roll) * int(ctx.attacker.spec.level)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "pay_day",
            "coins": coins,
            "roll": roll,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("play nice")
def _play_nice(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="play_nice",
        description="Play Nice lowers Attack.",
    )


@register_move_special("play rough")
def _play_rough(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="play_rough",
        description="Play Rough lowers Attack on 17+.",
        roll=roll,
    )


@register_move_special("poison fang")
def _poison_fang(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Badly Poisoned",
        effect="poison_fang",
        description="Poison Fang badly poisons on a high roll.",
        roll=roll,
    )


@register_move_special("poison gas")
def _poison_gas(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="poison_gas",
        description="Poison Gas poisons the target.",
    )


@register_move_special("poison jab")
def _poison_jab(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="poison_jab",
        description="Poison Jab poisons on 15+.",
        roll=roll,
    )


@register_move_special("poison powder")
def _poison_powder(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="poison_powder",
        description="Poison Powder poisons on hit.",
    )


@register_move_special("powder")
def _powder(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Powdered",
        effect="powder",
        description="Powder coats the target and detonates on Fire-type attacks.",
    )


@register_move_special("poison sting")
def _poison_sting(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="poison_sting",
        description="Poison Sting poisons on a high roll.",
        roll=roll,
    )


@register_move_special("poison tail")
def _poison_tail(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="poison_tail",
        description="Poison Tail poisons on a high roll.",
        roll=roll,
    )


@register_move_special("powder snow")
def _powder_snow(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Frozen",
        effect="powder_snow",
        description="Powder Snow freezes on a high roll.",
        roll=roll,
    )


@register_move_special("power split")
def _power_split(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    avg_atk = (int(ctx.attacker.spec.atk) + int(ctx.defender.spec.atk)) // 2
    avg_spatk = (int(ctx.attacker.spec.spatk) + int(ctx.defender.spec.spatk)) // 2
    ctx.defender.add_temporary_effect(
        "stat_modifier",
        stat="atk",
        amount=avg_atk - int(ctx.defender.spec.atk),
        source=ctx.move.name,
    )
    ctx.defender.add_temporary_effect(
        "stat_modifier",
        stat="spatk",
        amount=avg_spatk - int(ctx.defender.spec.spatk),
        source=ctx.move.name,
    )
    ctx.attacker.add_temporary_effect(
        "power_split_bonus", atk=avg_atk, spatk=avg_spatk, round=ctx.battle.round
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "power_split",
            "atk": avg_atk,
            "spatk": avg_spatk,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("power swap")
def _power_swap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.attacker.combat_stages["atk"], ctx.defender.combat_stages["atk"] = (
        ctx.defender.combat_stages.get("atk", 0),
        ctx.attacker.combat_stages.get("atk", 0),
    )
    ctx.attacker.combat_stages["spatk"], ctx.defender.combat_stages["spatk"] = (
        ctx.defender.combat_stages.get("spatk", 0),
        ctx.attacker.combat_stages.get("spatk", 0),
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "power_swap",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("power-up punch")
def _power_up_punch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="power_up_punch",
        description="Power-Up Punch raises Attack.",
    )


@register_move_special("psybeam")
def _psybeam_confuse(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="psybeam",
        description="Psybeam confuses on a high roll.",
        roll=roll,
    )


@register_move_special("psychic fangs")
def _psychic_fangs_event(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "psychic_fangs",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("psychic terrain")
def _psychic_terrain(ctx: MoveSpecialContext) -> None:
    ctx.battle.terrain = {"name": "Psychic Terrain"}
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "psychic_terrain",
            "terrain": ctx.battle.terrain,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("psyshield bash")
def _psyshield_bash(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect("damage_reduction", amount=5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "psyshield_bash",
            "amount": 5,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("purify")
def _purify(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.statuses = []
    heal_amount = ctx.attacker.tick_value() * 2
    ctx.attacker.heal(heal_amount)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "purify",
            "amount": heal_amount,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("quash")
def _quash(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    if ctx.battle.current_actor_id != ctx.attacker_id:
        return
    if ctx.battle._initiative_index < 0:
        return
    entry_index: Optional[int] = None
    for idx, entry in enumerate(ctx.battle.initiative_order):
        if entry.actor_id == ctx.defender_id:
            entry_index = idx
            break
    if entry_index is None or entry_index <= ctx.battle._initiative_index:
        return
    entry = ctx.battle.initiative_order.pop(entry_index)
    ctx.battle.initiative_order.append(entry)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "quash",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("quick attack")
def _quick_attack_priority(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "priority_attack",
            "priority": ctx.move.priority,
            "roll": ctx.result.get("roll"),
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("quiver dance")
def _quiver_dance(ctx: MoveSpecialContext) -> None:
    for stat in ("spatk", "spdef", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="quiver_dance",
            description="Quiver Dance raises Special Attack, Special Defense, and Speed.",
        )


@register_move_special("rage powder")
def _rage_powder(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.attacker.add_temporary_effect("follow_me", round=ctx.battle.round, until_round=ctx.battle.round)
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Enraged",
        effect="rage_powder",
        description="Rage Powder enrages the target.",
    )


@register_move_special("raging fury")
def _raging_fury(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    if ctx.defender is not None and ctx.defender_id is not None:
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Enraged",
            effect="raging_fury",
            description="Raging Fury enrages the target.",
            roll=roll,
        )
    if not ctx.attacker.has_status("Enraged"):
        ctx.attacker.statuses.append({"name": "Enraged"})


@register_move_special("rain dance")
def _rain_dance(ctx: MoveSpecialContext) -> None:
    ctx.battle.weather = "Rain"
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "rain_dance",
            "weather": ctx.battle.weather,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("rapid spin")
def _rapid_spin_clear(ctx: MoveSpecialContext) -> None:
    for status_name in ("trapped", "leech seed"):
        ctx.attacker.remove_status_by_names({status_name})
    if ctx.battle.grid is not None:
        for coord, tile in list(ctx.battle.grid.tiles.items()):
            if isinstance(tile, dict) and "hazards" in tile:
                tile.pop("hazards", None)
                ctx.battle.grid.tiles[coord] = tile
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "rapid_spin",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("rapid spin [ss]")
def _rapid_spin_ss_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spd",
        delta=1,
        effect="rapid_spin_ss",
        description="Rapid Spin [SS] raises Speed.",
    )


@register_move_special("razor shell")
def _razor_shell_lower_def(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll % 2 != 0:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-1,
        effect="razor_shell",
        description="Razor Shell lowers Defense on even rolls.",
        roll=roll,
    )


@register_move_special("recover")
def _recover(ctx: MoveSpecialContext) -> None:
    amount = ctx.attacker.max_hp() // 2
    before = ctx.attacker.hp or 0
    ctx.attacker.heal(amount)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "recover",
            "amount": (ctx.attacker.hp or 0) - before,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("recycle")
def _recycle(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.consumed_items:
        return
    entry = ctx.attacker.consumed_items[-1]
    kind = str(entry.get("kind") or "").lower()
    item = entry.get("item")
    if kind == "item":
        events = ctx.battle._apply_item_use(ctx.attacker_id, ctx.attacker_id, item)
        ctx.events.extend(events)
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "move": ctx.move.name,
                "effect": "recycle_item",
                "item": str(item.get("name") if isinstance(item, dict) else item),
                "target_hp": ctx.attacker.hp,
            }
        )
    elif kind == "food_buff" and isinstance(item, dict):
        text = str(item.get("effect") or "")
        amount = 0
        for token in text.split():
            if token.isdigit():
                amount = int(token)
                break
        if amount <= 0:
            amount = ctx.attacker.tick_value()
        before = ctx.attacker.hp or 0
        ctx.attacker.heal(amount)
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "move": ctx.move.name,
                "effect": "recycle_food_buff",
                "amount": (ctx.attacker.hp or 0) - before,
                "buff": item.get("name"),
                "target_hp": ctx.attacker.hp,
            }
        )


@register_move_special("reflect type")
def _reflect_type(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    ctx.attacker.spec.types = list(ctx.defender.spec.types)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "reflect_type",
            "types": ctx.attacker.spec.types,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("refresh")
def _refresh(ctx: MoveSpecialContext) -> None:
    while ctx.attacker.remove_status_by_names({"poisoned", "burned", "paralyzed"}):
        continue
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "refresh",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("relic song")
def _relic_song_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="relic_song",
        description="Relic Song puts the target to sleep.",
        roll=roll,
    )


@register_move_special("rending spell")
def _rending_spell(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    damage = ctx.defender._apply_tick_damage(1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "rending_spell",
            "amount": damage,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("resonance beam")
def _resonance_beam(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 20:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        effect="resonance_beam",
        description="Resonance Beam lowers Special Defense on 20.",
        roll=roll,
    )


@register_move_special("pollen puff")
def _pollen_puff_ally_heal(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.battle._team_for(ctx.attacker_id) != ctx.battle._team_for(ctx.defender_id):
        return
    if ctx.attacker.get_temporary_effects("pollen_puff_used"):
        return
    ctx.attacker.add_temporary_effect("pollen_puff_used", round=ctx.battle.round)
    before = ctx.defender.hp or 0
    heal_amount = max(0, ctx.defender.max_hp() // 2)
    ctx.defender.heal(heal_amount)
    healed = max(0, (ctx.defender.hp or 0) - before)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "pollen_puff_heal",
            "amount": healed,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("present")
def _present_heal(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    present_heal = ctx.result.get("present_heal")
    if present_heal is None:
        roll = ctx.result.get("present_roll")
        try:
            present_heal = int(roll) == 1 if roll is not None else None
        except (TypeError, ValueError):
            present_heal = None
    if present_heal is None:
        effective_db = ctx.result.get("effective_db")
        if effective_db is None:
            effective_db = ctx.result.get("db")
        try:
            effective_db = int(effective_db) if effective_db is not None else None
        except (TypeError, ValueError):
            effective_db = None
        present_heal = effective_db == 0
    if not present_heal:
        return
    before = ctx.defender.hp or 0
    if ctx.defender.has_status("Heal Blocked") or ctx.defender.has_status("Heal Block"):
        return
    max_hp = ctx.defender.max_hp_with_injuries()
    ctx.defender.hp = min(max_hp + 20, (ctx.defender.hp or 0) + 20)
    healed = max(0, (ctx.defender.hp or 0) - before)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "present_heal",
            "amount": healed,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("return")
def _return_db(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    loyalty = ctx.attacker.loyalty_value()
    if loyalty is None:
        loyalty = 5
    db = max(1, min(20, 3 + int(loyalty)))
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "return_db",
            "db": db,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("retaliate")
def _retaliate_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    recent_round = ctx.battle.round - 1
    boosted = False
    for entry in ctx.battle.fainted_history:
        if entry.get("attacker") != ctx.defender_id:
            continue
        if int(entry.get("round", 0) or 0) < recent_round:
            continue
        ally_id = entry.get("defender")
        ally = ctx.battle.pokemon.get(ally_id) if ally_id else None
        if ally is None:
            continue
        if ally.controller_id != ctx.attacker.controller_id:
            continue
        boosted = True
        break
    if not boosted:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "retaliate_boost",
            "db": 14,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("revelation dance")
def _revelation_dance(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    move_type = ctx.move.type
    if ctx.attacker.spec.types:
        move_type = ctx.attacker.spec.types[0]
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "revelation_dance_type",
            "move_type": move_type,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )
    dance_used_before = ctx.battle.dance_moves_used_this_round.get(ctx.attacker_id, 0)
    if "dance" in ctx.move_name and dance_used_before:
        dance_used_before = max(0, dance_used_before - 1)
    if dance_used_before:
        bonus = min(15, 5 * int(dance_used_before))
        if bonus > 0:
            ctx.events.append(
                {
                    "type": "move",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "move": ctx.move.name,
                    "effect": "revelation_dance_bonus",
                    "amount": bonus,
                    "target_hp": ctx.defender.hp if ctx.defender else None,
                }
            )


@register_move_special("revenge")
def _revenge_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    damage_from = ctx.battle.damage_taken_from.get(ctx.attacker_id, set())
    if ctx.defender_id not in damage_from:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "revenge_boost",
            "db": 12,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("reversal")
def _reversal_bonus(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    bonus = max(0, int(ctx.attacker.injuries or 0))
    if bonus <= 0:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "reversal_bonus",
            "bonus_db": bonus,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("riposte", phase="pre_damage")
def _riposte_requires_trigger(ctx: MoveSpecialContext) -> None:
    if ctx.attacker.remove_temporary_effect("riposte_ready"):
        return
    ctx.result["hit"] = False
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "riposte_invalid",
            "description": "Riposte requires a missed melee attack to trigger.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("rest")
def _rest(ctx: MoveSpecialContext) -> None:
    if ctx.attacker.has_ability("Vital Spirit"):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "ability": "Vital Spirit",
                "move": ctx.move.name,
                "effect": "block",
                "description": "Vital Spirit prevents Rest.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.heal(ctx.attacker.max_hp())
    ctx.attacker.remove_status_by_names({"burned", "poisoned", "paralyzed", "confused"})
    sleep_entry = {"name": "Sleep", "remaining": 2, "rest_sleep": True}
    if not ctx.attacker.has_status("Sleep"):
        ctx.attacker.statuses.append(sleep_entry)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "rest",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("rising voltage")
def _rising_voltage(ctx: MoveSpecialContext) -> None:
    terrain_name = str((ctx.battle.terrain or {}).get("name") or "").strip().lower()
    if terrain_name != "electric terrain":
        ctx.battle.terrain = {"name": "Electric Terrain"}
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "move": ctx.move.name,
                "effect": "rising_voltage",
                "terrain": ctx.battle.terrain,
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "rising_voltage_spent",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("roar")
def _roar_force(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    distance = 1
    if ctx.defender is not None:
        distance = max(1, int((ctx.defender.spec.movement or {}).get("overland", 1) or 1))
    ctx.battle.apply_forced_movement(
        ctx.attacker_id,
        ctx.defender_id,
        {"kind": "push", "distance": distance},
    )


@register_move_special("rock climb")
def _rock_climb_confuse(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="rock_climb",
        description="Rock Climb confuses on a high roll.",
        roll=roll,
    )


@register_move_special("rock polish")
def _rock_polish(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spd",
        delta=2,
        effect="rock_polish",
        description="Rock Polish sharply raises Speed.",
    )


@register_move_special("rock slide")
def _rock_slide_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="rock_slide",
        description="Rock Slide flinches on a high roll.",
        roll=roll,
    )


@register_move_special("rock smash")
def _rock_smash_lower_def(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-1,
        effect="rock_smash",
        description="Rock Smash lowers Defense on a high roll.",
        roll=roll,
    )


@register_move_special("rock tomb")
def _rock_tomb_speed_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-1,
        effect="rock_tomb",
        description="Rock Tomb lowers Speed.",
    )


@register_move_special("rolling kick")
def _rolling_kick_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinched",
        effect="rolling_kick",
        description="Rolling Kick flinches on a high roll.",
        roll=roll,
        remaining=1,
    )


@register_move_special("sharpen")
def _sharpen_attack_raise(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="sharpen",
        description="Sharpen raises Attack.",
    )


@register_move_special("decoy")
def _decoy(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect(
        "follow_me", round=ctx.battle.round, until_round=ctx.battle.round + 1
    )
    ctx.attacker.add_temporary_effect(
        "evasion_bonus", amount=2, expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "decoy",
            "description": "Decoy draws attacks and boosts evasion.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("drizzle")
def _drizzle(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Drizzle"):
        return
    ctx.battle.weather = "Rain"
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Drizzle",
            "move": ctx.move.name,
            "effect": "weather",
            "weather": ctx.battle.weather,
            "description": "Drizzle summons rain.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("drizzle [errata]")
def _drizzle_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Drizzle [Errata]"):
        return
    ctx.battle.weather = "Rain"
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Drizzle [Errata]",
            "move": ctx.move.name,
            "effect": "weather",
            "weather": ctx.battle.weather,
            "description": "Drizzle [Errata] summons rain.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("flutter")
def _flutter(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Flutter"):
        return
    ctx.attacker.add_temporary_effect(
        "flank_immunity", expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Flutter",
            "move": ctx.move.name,
            "effect": "flank_immunity",
            "description": "Flutter prevents flanking.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("forest lord")
def _forest_lord(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Forest Lord"):
        return
    ctx.attacker.add_temporary_effect(
        "forest_lord", expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Forest Lord",
            "move": ctx.move.name,
            "effect": "prepare",
            "description": "Forest Lord prepares accuracy bonuses for Grass/Ghost moves.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("fox fire")
def _fox_fire(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Fox Fire"):
        return
    ctx.attacker.add_temporary_effect(
        "fox_fire", charges=2, expires_round=ctx.battle.round + 2
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Fox Fire",
            "move": ctx.move.name,
            "effect": "fox_fire",
            "description": "Fox Fire prepares an ember interrupt.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("fox fire [errata]")
def _fox_fire_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Fox Fire [Errata]"):
        return
    entry = next(iter(ctx.attacker.get_temporary_effects("fox_fire_errata")), None)
    if entry is None:
        ctx.attacker.add_temporary_effect("fox_fire_errata", charges=3)
    else:
        entry["charges"] = 3
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Fox Fire [Errata]",
            "move": ctx.move.name,
            "effect": "fox_fire",
            "description": "Fox Fire creates Ember wisps for follow-up attacks.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("frighten")
def _frighten(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Frighten"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-2,
        effect="frighten",
        description="Frighten lowers the target's Speed by -2 CS.",
    )


@register_move_special("frisk")
def _frisk(ctx: MoveSpecialContext) -> None:
    if (
        not ctx.attacker.has_ability("Frisk")
        or has_ability_exact(ctx.attacker, "Frisk [Feb Errata]")
        or has_ability_exact(ctx.attacker, "Frisk [SuMo Errata]")
    ):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    types = list(ctx.defender.spec.types or [])
    abilities = [str(entry.get("name") or "").strip() for entry in ctx.defender.spec.abilities or []]
    items = [
        str(item.get("name") or "").strip()
        for item in ctx.defender.spec.items
        if isinstance(item, dict)
    ]
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Frisk",
            "move": ctx.move.name,
            "effect": "frisk",
            "types": types,
            "abilities": abilities,
            "nature": getattr(ctx.defender.spec, "nature", None),
            "level": getattr(ctx.defender.spec, "level", None),
            "items": items,
            "description": "Frisk reveals the target's details.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("frisk [feb errata]")
def _frisk_feb_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Frisk [Feb Errata]"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    types = list(ctx.defender.spec.types or [])
    abilities = [str(entry.get("name") or "").strip() for entry in ctx.defender.spec.abilities or []]
    items = [
        str(item.get("name") or "").strip()
        for item in ctx.defender.spec.items
        if isinstance(item, dict)
    ]
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Frisk [Feb Errata]",
            "move": ctx.move.name,
            "effect": "frisk",
            "types": types,
            "abilities": abilities,
            "nature": getattr(ctx.defender.spec, "nature", None),
            "level": getattr(ctx.defender.spec, "level", None),
            "items": items,
            "description": "Frisk reveals the target's details.",
            "target_hp": ctx.defender.hp,
        }
    )


def _apply_interference(ctx: MoveSpecialContext, *, ability_name: str) -> None:
    if ctx.attacker.position is None:
        return
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
            continue
        if mon.position is None:
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 3:
            continue
        mon.add_temporary_effect(
            "accuracy_penalty",
            amount=2,
            expires_round=ctx.battle.round + 1,
            source=ability_name,
            source_id=ctx.attacker_id,
        )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "accuracy_penalty",
            "amount": 2,
            "description": "Interference penalizes nearby foes' accuracy.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("interference")
def _interference(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Interference"):
        return
    _apply_interference(ctx, ability_name="Interference")


@register_move_special("interference [errata]")
def _interference_errata(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Interference [Errata]"):
        return
    _apply_interference(ctx, ability_name="Interference [Errata]")


@register_move_special("intimidate [errata]")
def _intimidate_errata(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Intimidate [Errata]"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.position is None or ctx.defender.position is None:
        return
    if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 5:
        return
    if not _scene_ready(ctx.attacker, ctx.battle, f"intimidate_{ctx.defender_id}"):
        return
    stage_events: List[dict] = []
    ctx.battle._apply_combat_stage(
        stage_events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="intimidate",
        description="Intimidate [Errata] lowers Attack by -1 CS.",
    )
    ctx.events.extend(stage_events)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Intimidate [Errata]",
            "move": ctx.move.name,
            "effect": "attack_drop",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("leaf gift")
def _leaf_gift(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Leaf Gift"):
        return
    if not ctx.hit:
        return
    desired = None
    for entry in ctx.attacker.get_temporary_effects("leaf_gift_suit_choice"):
        desired = str(entry.get("suit") or "").strip().lower()
        if desired:
            break
    suits = {
        "nourishing": ("Nourishing Suit", ["Sun Blanket", "Leaf Guard"]),
        "heavy": ("Heavy Suit", ["Sturdy", "Overcoat"]),
        "vibrant": ("Vibrant Suit", ["Chlorophyll", "Photosynthesis"]),
    }
    suit_key = desired if desired in suits else "nourishing"
    suit_name, abilities = suits[suit_key]
    while ctx.attacker.remove_temporary_effect("leaf_gift_suit"):
        continue
    ctx.attacker.add_temporary_effect("leaf_gift_suit", suit=suit_name)
    for entry in list(ctx.attacker.get_temporary_effects("ability_granted")):
        if entry.get("source") == "Leaf Gift":
            ctx.attacker.temporary_effects.remove(entry)
    for ability in abilities:
        ctx.attacker.add_temporary_effect("ability_granted", ability=ability, source="Leaf Gift")
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Leaf Gift",
            "move": ctx.move.name,
            "effect": "suit",
            "suit": suit_name,
            "granted": abilities,
            "description": "Leaf Gift crafts a leaf suit.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("leaf guard [errata]")
def _leaf_guard_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Leaf Guard [Errata]"):
        return
    cured = ctx.battle._remove_statuses_by_set(
        ctx.attacker, _STATUS_CONDITIONS_TO_CURE, limit=1
    )
    if cured:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "ability": "Leaf Guard [Errata]",
                "move": ctx.move.name,
                "effect": "cure",
                "statuses": cured,
                "description": "Leaf Guard [Errata] cures a status affliction.",
                "target_hp": ctx.attacker.hp,
            }
        )
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" in weather or "sunny" in weather or "harsh sunlight" in weather:
        ctx.battle._restore_move_frequency_usage(ctx.attacker_id, ctx.move)


def _apply_life_force(ctx: MoveSpecialContext, *, ability_name: str) -> None:
    if not ctx.hit:
        return
    healed = ctx.attacker._apply_tick_heal(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": "Life Force restores a tick of HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("life force")
def _life_force(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Life Force"):
        return
    _apply_life_force(ctx, ability_name="Life Force")


@register_move_special("life force [errata]")
def _life_force_errata(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Life Force [Errata]"):
        return
    _apply_life_force(ctx, ability_name="Life Force [Errata]")


def _apply_lightning_kicks(
    ctx: MoveSpecialContext, *, ability_name: str, accuracy_bonus: int = 0
) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect(
        "kick_priority",
        expires_round=ctx.battle.round,
        source=ability_name,
        accuracy_bonus=accuracy_bonus,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "priority",
            "accuracy_bonus": accuracy_bonus or None,
            "description": "Lightning Kicks empowers the next Kick move with priority.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("lightning kicks")
def _lightning_kicks(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Lightning Kicks"):
        return
    _apply_lightning_kicks(ctx, ability_name="Lightning Kicks")


@register_move_special("lightning kicks [errata]")
def _lightning_kicks_errata(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Lightning Kicks [Errata]"):
        return
    _apply_lightning_kicks(ctx, ability_name="Lightning Kicks [Errata]", accuracy_bonus=4)


@register_move_special("lullaby")
def _lullaby(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Lullaby"):
        return
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect(
        "lullaby_ready",
        expires_round=ctx.battle.round,
        source="Lullaby",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Lullaby",
            "move": ctx.move.name,
            "effect": "sing_ready",
            "description": "Lullaby prepares Sing to auto-hit.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("magnet pull")
def _magnet_pull(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Magnet Pull"):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    defender_types = {t.lower().strip() for t in ctx.defender.spec.types if t}
    if "steel" not in defender_types:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Magnet Pull",
                "move": ctx.move.name,
                "effect": "no_effect",
                "description": "Magnet Pull only affects Steel-type targets.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    ctx.defender.add_temporary_effect(
        "magnet_pull",
        source_id=ctx.attacker_id,
        min_range=3,
        max_range=8,
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Magnet Pull",
            "move": ctx.move.name,
            "effect": "restrict",
            "description": "Magnet Pull restricts the target's movement range.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("magnet pull [errata]")
def _magnet_pull_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Magnet Pull [Errata]"):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    defender_types = {t.lower().strip() for t in ctx.defender.spec.types if t}
    if "steel" not in defender_types:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Magnet Pull [Errata]",
                "move": ctx.move.name,
                "effect": "no_effect",
                "description": "Magnet Pull [Errata] only affects Steel-type targets.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    choice_entry = next(iter(ctx.attacker.get_temporary_effects("magnet_pull_errata_choice")), None)
    if choice_entry is not None:
        ctx.attacker.remove_temporary_effect("magnet_pull_errata_choice")
    raw_choices = []
    direction = "pull"
    if isinstance(choice_entry, dict):
        raw = choice_entry.get("effects") or choice_entry.get("choices") or choice_entry.get("choice")
        if isinstance(raw, str):
            raw_choices = [item.strip().lower() for item in raw.split(",") if item.strip()]
        elif isinstance(raw, (list, tuple, set)):
            raw_choices = [str(item).strip().lower() for item in raw if item]
        direction_raw = str(
            choice_entry.get("direction") or choice_entry.get("mode") or choice_entry.get("push_pull") or ""
        ).strip().lower()
        if direction_raw in {"push", "pull"}:
            direction = direction_raw
    normalized: List[str] = []
    for token in raw_choices:
        if token in {"push", "pull"}:
            direction = token
            token = "move"
        if token in {"move", "max_range", "min_range"} and token not in normalized:
            normalized.append(token)
    if not normalized:
        normalized = ["move", "max_range"]
    selected: List[str] = []
    for token in normalized:
        if token not in selected:
            selected.append(token)
        if len(selected) >= 2:
            break
    if len(selected) < 2:
        for token in ("move", "max_range", "min_range"):
            if token not in selected:
                selected.append(token)
            if len(selected) >= 2:
                break
    min_range = 0
    max_range = 0
    if "move" in selected:
        distance = max(0, 6 - ctx.defender.weight_class())
        if distance > 0:
            ctx.battle.apply_forced_movement(
                ctx.attacker_id,
                ctx.defender_id,
                {"kind": direction, "distance": distance},
            )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Magnet Pull [Errata]",
                "move": ctx.move.name,
                "effect": "forced_movement",
                "kind": direction,
                "distance": distance,
                "description": "Magnet Pull [Errata] forces the target's position.",
                "target_hp": ctx.defender.hp,
            }
        )
    if "max_range" in selected:
        max_range = 6
    if "min_range" in selected:
        min_range = 3
    if min_range or max_range:
        ctx.defender.add_temporary_effect(
            "magnet_pull",
            source_id=ctx.attacker_id,
            min_range=min_range,
            max_range=max_range,
            expires_round=ctx.battle.round + 1,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Magnet Pull [Errata]",
                "move": ctx.move.name,
                "effect": "restrict",
                "min_range": min_range or None,
                "max_range": max_range or None,
                "description": "Magnet Pull [Errata] restricts the target's movement range.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("memory wipe")
def _memory_wipe(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Memory Wipe"):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    last_move = ""
    for entry in ctx.defender.get_temporary_effects("last_move"):
        last_move = str(entry.get("name") or "").strip()
        if last_move:
            break
    if last_move:
        ctx.defender.statuses.append({"name": "Disabled", "move": last_move, "remaining": 3})
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Memory Wipe",
                "move": ctx.move.name,
                "effect": "disable",
                "status": "Disabled",
                "move_name": last_move,
                "description": "Memory Wipe disables the target's last move.",
                "target_hp": ctx.defender.hp,
            }
        )
    else:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Memory Wipe",
                "move": ctx.move.name,
                "effect": "no_effect",
                "description": "Memory Wipe finds no recent move to disable.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("memory wipe [errata]")
def _memory_wipe_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Memory Wipe [Errata]"):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    action_type = (ctx.action_type or "").strip().lower()
    if action_type == "standard":
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Flinched",
            effect="flinch",
            description="Memory Wipe [Errata] flinches the target.",
            remaining=1,
        )
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Paralyzed",
            effect="paralysis",
            description="Memory Wipe [Errata] paralyzes the target.",
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Memory Wipe [Errata]",
                "move": ctx.move.name,
                "effect": "flinch_paralyze",
                "description": "Memory Wipe [Errata] flinches and paralyzes the target.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    last_move = ""
    for entry in ctx.defender.get_temporary_effects("last_move"):
        last_move = str(entry.get("name") or "").strip()
        if last_move:
            break
    if last_move:
        ctx.defender.statuses.append({"name": "Disabled", "move": last_move, "remaining": 3})
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Memory Wipe [Errata]",
                "move": ctx.move.name,
                "effect": "disable",
                "status": "Disabled",
                "move_name": last_move,
                "description": "Memory Wipe [Errata] disables the target's last move.",
                "target_hp": ctx.defender.hp,
            }
        )
    else:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Memory Wipe [Errata]",
                "move": ctx.move.name,
                "effect": "no_effect",
                "description": "Memory Wipe [Errata] finds no recent move to disable.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("mini-noses")
def _mini_noses(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Mini-Noses"):
        return
    if not ctx.hit or ctx.attacker.position is None:
        return
    if ctx.battle.grid is None:
        return
    origins: List[tuple] = []
    for coord in movement.neighboring_tiles(ctx.attacker.position):
        if not ctx.battle.grid.in_bounds(coord):
            continue
        if coord in ctx.battle.grid.blockers:
            continue
        if any(mon.position == coord for mon in ctx.battle.pokemon.values()):
            continue
        origins.append(coord)
        if len(origins) >= 3:
            break
    if not origins:
        return
    while ctx.attacker.remove_temporary_effect("mini_noses"):
        continue
    ctx.attacker.add_temporary_effect("mini_noses", origins=origins)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Mini-Noses",
            "move": ctx.move.name,
            "effect": "deploy",
            "origins": origins,
            "description": "Mini-Noses deploy adjacent proxies.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("minus")
def _minus(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Minus"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker_id == ctx.defender_id:
        return
    if ctx.attacker.position is not None and ctx.defender.position is not None:
        if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 10:
            return
    if not (
        ctx.defender.has_ability("Plus")
        or ctx.defender.has_ability("Plus [SwSh]")
    ):
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=2,
        effect="minus",
        description="Minus boosts an allied Plus user's Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Minus",
            "move": ctx.move.name,
            "effect": "spatk_raise",
            "amount": 2,
            "description": "Minus boosts Special Attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("plus")
def _plus(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Plus"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker_id == ctx.defender_id:
        return
    if ctx.attacker.position is not None and ctx.defender.position is not None:
        if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 10:
            return
    if not (
        ctx.defender.has_ability("Minus")
        or ctx.defender.has_ability("Minus [SwSh]")
    ):
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=2,
        effect="plus",
        description="Plus boosts an allied Minus user's Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Plus",
            "move": ctx.move.name,
            "effect": "spatk_raise",
            "amount": 2,
            "description": "Plus boosts Special Attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("illusion mark")
def _illusion_mark(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Illusion"):
        return
    if ctx.defender_id is None:
        return
    ctx.attacker.add_temporary_effect("illusion_mark", target_id=ctx.defender_id)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Illusion",
            "move": ctx.move.name,
            "effect": "mark",
            "description": "Illusion marks a target to mimic.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("illusion shift")
def _illusion_shift(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Illusion"):
        return
    marked = next(iter(ctx.attacker.get_temporary_effects("illusion_mark")), None)
    if marked and marked.get("target_id"):
        ctx.attacker.add_temporary_effect(
            "illusion_active", target_id=marked.get("target_id")
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Illusion",
                "move": ctx.move.name,
                "effect": "shift",
                "description": "Illusion mimics the marked target.",
                "target_hp": ctx.attacker.hp,
            }
        )
    else:
        while ctx.attacker.remove_temporary_effect("illusion_active"):
            continue
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Illusion",
                "move": ctx.move.name,
                "effect": "dismiss",
                "description": "Illusion is dismissed.",
                "target_hp": ctx.attacker.hp,
            }
        )


@register_move_special("growl")
def _growl(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=-1,
        effect="growl",
        description="Growl lowers the target's Attack.",
    )


@register_move_special("healer")
def _healer(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.attacker.has_ability("Healer"):
        return
    if ctx.battle._team_for(ctx.attacker_id) != ctx.battle._team_for(ctx.defender_id):
        return
    if ctx.attacker.position is not None and ctx.defender.position is not None:
        if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 1:
            return
    cured = []
    for status in list(ctx.defender.statuses):
        name = ctx.defender._normalized_status_name(status)
        if name:
            cured.append(name)
        if status in ctx.defender.statuses:
            ctx.defender.statuses.remove(status)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Healer",
            "move": ctx.move.name,
            "effect": "healer",
            "cured": cured,
            "description": "Healer cures adjacent allies.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("hydration [errata]")
def _hydration_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Hydration [Errata]"):
        return
    cured = ctx.battle._remove_statuses_by_set(
        ctx.attacker, _STATUS_CONDITIONS_TO_CURE, limit=1
    )
    if not cured:
        return
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Hydration [Errata]",
            "move": ctx.move.name,
            "effect": "cure",
            "statuses": cured,
            "description": "Hydration [Errata] cures a status affliction.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("drought")
def _drought(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Drought"):
        return
    ctx.battle.weather = "Sunny"
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Drought",
            "move": ctx.move.name,
            "effect": "weather",
            "weather": ctx.battle.weather,
            "description": "Drought summons harsh sunlight.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("drought [errata]")
def _drought_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Drought [Errata]"):
        return
    ctx.battle.weather = "Sunny"
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Drought [Errata]",
            "move": ctx.move.name,
            "effect": "weather",
            "weather": ctx.battle.weather,
            "description": "Drought [Errata] summons harsh sunlight.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("flower gift")
def _flower_gift(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Flower Gift"):
        return
    weather_name = (ctx.battle.weather or "").strip().lower()
    if weather_name not in {"sunny", "sun", "harsh sunlight"}:
        return
    stats = None
    for entry in ctx.attacker.get_temporary_effects("flower_gift_stats"):
        stats = entry.get("stats")
        break
    if not stats:
        stats = ["atk", "spd"]
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if pid == ctx.attacker_id:
            continue
        for stat in stats:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=pid,
                move=ctx.move,
                target=mon,
                stat=str(stat).strip().lower(),
                delta=1,
                effect="flower_gift",
                description="Flower Gift boosts allies in sunlight.",
            )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Flower Gift",
            "move": ctx.move.name,
            "effect": "flower_gift",
            "description": "Flower Gift empowers allies under sunlight.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("flower gift [errata]")
def _flower_gift_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Flower Gift [Errata]"):
        return
    weather_name = (ctx.battle.weather or "").strip().lower()
    max_hp = ctx.attacker.max_hp_with_injuries()
    under_half = (ctx.attacker.hp or 0) * 2 < max_hp
    if weather_name not in {"sunny", "sun", "harsh sunlight"} and not under_half:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Flower Gift [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Flower Gift requires sun or being under 50% HP.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return

    stats = None
    for entry in ctx.attacker.get_temporary_effects("flower_gift_stats"):
        stats = entry.get("stats")
        break
    allowed = {"atk", "def", "spatk", "spdef", "spd", "accuracy", "evasion"}
    chosen: List[str] = []
    if stats:
        for stat in stats:
            raw = str(stat or "").strip().lower()
            if raw in allowed:
                chosen.append(raw)
    if len(chosen) < 2:
        chosen = ["atk", "spatk"]
    else:
        chosen = chosen[:2]

    for stat in chosen:
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=2,
            effect="flower_gift_errata",
            description="Flower Gift raises the user's stats.",
        )

    team = ctx.battle._team_for(ctx.attacker_id)
    attacker_pos = ctx.attacker.position
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.attacker_id:
            continue
        if ctx.battle._team_for(pid) != team:
            continue
        if attacker_pos is None or mon.position is None:
            continue
        if targeting.chebyshev_distance(attacker_pos, mon.position) > 2:
            continue
        for stat in chosen:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=pid,
                move=ctx.move,
                target=mon,
                stat=stat,
                delta=1,
                effect="flower_gift_errata",
                description="Flower Gift boosts nearby allies.",
            )

    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Flower Gift [Errata]",
            "move": ctx.move.name,
            "effect": "flower_gift",
            "description": "Flower Gift empowers the user and allies.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("defy death")
def _defy_death(ctx: MoveSpecialContext) -> None:
    before = int(ctx.attacker.injuries or 0)
    ctx.attacker.injuries = max(0, before - 2)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "defy_death",
            "injuries_removed": before - int(ctx.attacker.injuries or 0),
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("defy death [errata]")
def _defy_death_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Defy Death [Errata]"):
        return
    before = int(ctx.attacker.injuries or 0)
    used_entry = next(iter(ctx.attacker.get_temporary_effects("defy_death_errata_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    remaining = max(0, 3 - used_count)
    removed = min(before, remaining)
    if removed > 0:
        ctx.attacker.injuries = max(0, before - removed)
        healed = ctx.attacker._apply_tick_heal(removed)
        if used_entry is None:
            ctx.attacker.add_temporary_effect("defy_death_errata_used", count=used_count + removed)
        else:
            used_entry["count"] = used_count + removed
    else:
        healed = 0
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "defy_death_errata",
            "injuries_removed": removed,
            "healed": healed,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("stealth rock")
def _stealth_rock(ctx: MoveSpecialContext) -> None:
    if ctx.battle.grid is None:
        return
    hazard = "stealth_rock_fairy" if ctx.attacker.has_ability("Diamond Defense") else "stealth_rock"
    _place_hazard_on_target_tile(ctx, hazard, 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "stealth_rock",
            "hazard": hazard,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("spikes")
def _spikes(ctx: MoveSpecialContext) -> None:
    if ctx.battle.grid is None:
        return
    _place_hazard_on_target_tile(ctx, "spikes", 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "spikes",
            "hazard": "spikes",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("celebrate")
def _celebrate_placeholder(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Celebrate"):
        return
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Celebrate",
            "move": ctx.move.name,
            "effect": "prepare",
            "description": "Celebrate readies a victory surge.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("celebrate [errata]")
def _celebrate_errata_ready(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Celebrate [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "celebrate_errata_ready",
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Celebrate [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Celebrate [Errata] readies a free disengage.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("cherry power")
def _cherry_power(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Cherry Power"):
        return
    cured = []
    for status in list(ctx.attacker.statuses):
        name = ctx.attacker._normalized_status_name(status)
        if name:
            cured.append(name)
        ctx.attacker.statuses.remove(status)
    temp = ctx.attacker.add_temp_hp(ctx.attacker.tick_value())
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Cherry Power",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": temp,
            "cured": cured,
            "description": "Cherry Power grants temp HP and cures ailments.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("clay cannons")
def _clay_cannons(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Clay Cannons"):
        return
    ctx.attacker.add_temporary_effect("clay_cannons", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Clay Cannons",
            "move": ctx.move.name,
            "effect": "origin_shift",
            "description": "Clay Cannons shifts the origin of ranged attacks.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("clay cannons [errata]")
def _clay_cannons_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Clay Cannons [Errata]"):
        return
    ctx.attacker.add_temporary_effect("clay_cannons", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Clay Cannons [Errata]",
            "move": ctx.move.name,
            "effect": "origin_shift",
            "description": "Clay Cannons [Errata] shifts the origin of ranged attacks.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("danger syrup [errata]")
def _danger_syrup_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Danger Syrup [Errata]"):
        return
    ctx.attacker.add_temporary_effect("danger_syrup_errata_ready", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Danger Syrup [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Danger Syrup [Errata] readies a free Sweet Scent.",
            "target_hp": ctx.attacker.hp,
        }
    )

@register_move_special("cloud nine")
def _cloud_nine(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Cloud Nine"):
        return
    ctx.battle.weather = "Clear"
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Cloud Nine",
            "move": ctx.move.name,
            "effect": "weather_clear",
            "description": "Cloud Nine clears the weather.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("electric surge")
def _electric_surge(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Electric Surge"):
        return
    set_terrain(ctx.battle, "Electric Terrain", rounds=1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Electric Surge",
            "move": ctx.move.name,
            "effect": "terrain",
            "terrain": "Electric Terrain",
            "description": "Electric Surge electrifies the field.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("grassy surge")
def _grassy_surge(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Grassy Surge"):
        return
    set_terrain(ctx.battle, "Grassy Terrain", rounds=1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Grassy Surge",
            "move": ctx.move.name,
            "effect": "terrain",
            "terrain": "Grassy Terrain",
            "description": "Grassy Surge spreads lush terrain.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("misty surge")
def _misty_surge(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Misty Surge"):
        return
    set_terrain(ctx.battle, "Misty Terrain", rounds=1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Misty Surge",
            "move": ctx.move.name,
            "effect": "terrain",
            "terrain": "Misty Terrain",
            "description": "Misty Surge shrouds the field.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("psychic surge")
def _psychic_surge(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Psychic Surge"):
        return
    set_terrain(ctx.battle, "Psychic Terrain", rounds=1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Psychic Surge",
            "move": ctx.move.name,
            "effect": "terrain",
            "terrain": "Psychic Terrain",
            "description": "Psychic Surge warps the field.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("accelerate")
def _accelerate(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Accelerate"):
        return
    half_speed = max(1, int(math.floor(calculations.speed_stat(ctx.attacker) / 2)))
    ctx.attacker.add_temporary_effect(
        "accelerate_ready",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
        half_speed=half_speed,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Accelerate",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Accelerate readies a priority STAB strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("gale wings [errata]")
def _gale_wings_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Gale Wings [Errata]"):
        return
    half_speed = max(1, int(math.floor(calculations.speed_stat(ctx.attacker) / 2)))
    ctx.attacker.add_temporary_effect(
        "gale_wings_errata_ready",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
        half_speed=half_speed,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Gale Wings [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Gale Wings readies a priority Flying strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("battery")
def _battery(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Battery"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect(
        "battery_boost",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
        source_id=ctx.attacker_id,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Battery",
            "move": ctx.move.name,
            "effect": "charge",
            "description": "Battery charges the target's next special attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("comatose")
def _comatose(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Comatose"):
        return
    if not ctx.attacker.has_status("Sleep") and not ctx.attacker.has_status("Asleep"):
        ctx.attacker.statuses.append({"name": "Sleep", "remaining": 5})
    ctx.attacker.add_temporary_effect("comatose_active")
    healed = ctx.attacker._apply_tick_heal(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Comatose",
            "move": ctx.move.name,
            "effect": "sleep_heal",
            "amount": healed,
            "description": "Comatose induces sleep and restores a tick of HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("curious medicine")
def _curious_medicine(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Curious Medicine"):
        return
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if mon.position is None or ctx.attacker.position is None:
            continue
        if targeting.chebyshev_distance(mon.position, ctx.attacker.position) > 2:
            continue
        if any(value != 0 for value in mon.combat_stages.values()):
            for stat in mon.combat_stages:
                mon.combat_stages[stat] = 0
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": pid,
                    "ability": "Curious Medicine",
                    "move": ctx.move.name,
                    "effect": "reset_cs",
                    "description": "Curious Medicine resets combat stages.",
                    "target_hp": mon.hp,
                }
            )


@register_move_special("dazzling")
def _dazzling(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Dazzling"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect(
        "priority_blocked",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 999,
        source_id=ctx.attacker_id,
    )
    ctx.defender.add_temporary_effect(
        "initiative_penalty",
        amount=-10,
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 999,
        source_id=ctx.attacker_id,
    )
    ctx.attacker.add_temporary_effect(
        "no_interrupts",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 999,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Dazzling",
            "move": ctx.move.name,
            "effect": "suppress_priority",
            "description": "Dazzling suppresses priority and lowers initiative.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("full guard")
def _full_guard(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Full Guard"):
        return
    ctx.attacker.add_temporary_effect(
        "full_guard_ready",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Full Guard",
            "move": ctx.move.name,
            "effect": "guard",
            "description": "Full Guard braces against the next hit.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("ice face")
def _ice_face(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Ice Face"):
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "hail" not in weather and "snow" not in weather:
        return
    gained = ctx.attacker.add_temp_hp(ctx.attacker.tick_value() * 2)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Ice Face",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": gained,
            "description": "Ice Face restores two ticks of temporary HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("stamina")
def _stamina(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Stamina"):
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        effect="stamina",
        description="Stamina raises Defense.",
    )


@register_move_special("pack hunt")
def _pack_hunt(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Pack Hunt"):
        return
    if not ctx.hit or ctx.defender is None:
        return
    damage = ctx.defender._apply_tick_damage(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Pack Hunt",
            "move": ctx.move.name,
            "effect": "tick_damage",
            "amount": damage,
            "description": "Pack Hunt strikes for a tick of damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("parry")
def _parry_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Parry"):
        return
    ctx.attacker.add_temporary_effect("parry_ready", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Parry",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Parry readies a melee deflection.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("perception")
def _perception_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Perception"):
        return
    ctx.attacker.add_temporary_effect("perception_ready", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Perception",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Perception readies a shift out of area attacks.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("pickup")
def _pickup_roll(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Pickup"):
        return
    roll = ctx.battle.rng.randint(1, 20)
    ctx.attacker.add_temporary_effect("pickup_roll", roll=roll, round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Pickup",
            "move": ctx.move.name,
            "effect": "roll",
            "roll": roll,
            "description": "Pickup rolls on the pickup table.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("pixilate")
def _pixilate_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Pixilate"):
        return
    ctx.attacker.add_temporary_effect("pixilate_ready", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Pixilate",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Pixilate readies a Fairy conversion.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("prime fury")
def _prime_fury(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Prime Fury") or has_errata(ctx.attacker, "Prime Fury"):
        return
    if not ctx.attacker.has_status("Enraged"):
        ctx.attacker.statuses.append({"name": "Enraged", "remaining": 2})
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="prime_fury",
        description="Prime Fury raises Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Prime Fury",
            "move": ctx.move.name,
            "effect": "enraged",
            "description": "Prime Fury enrages the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("prime fury [errata]")
def _prime_fury_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Prime Fury [Errata]"):
        return
    if not ctx.attacker.has_status("Enraged"):
        ctx.attacker.statuses.append({"name": "Enraged", "remaining": 2})
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="prime_fury_errata",
        description="Prime Fury raises Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=1,
        effect="prime_fury_errata",
        description="Prime Fury raises Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Prime Fury [Errata]",
            "move": ctx.move.name,
            "effect": "enraged",
            "description": "Prime Fury enrages the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("pressure [errata]")
def _pressure_errata(ctx: MoveSpecialContext) -> None:
    if ctx.attacker.position is None:
        return
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.attacker_id or mon.fainted or not mon.active:
            continue
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
            continue
        if mon.position is None:
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 3:
            continue
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=pid,
            move=ctx.move,
            target=mon,
            status="Suppressed",
            effect="pressure_errata",
            description="Pressure [Errata] suppresses nearby foes.",
            remaining=1,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Pressure [Errata]",
                "move": ctx.move.name,
                "effect": "suppress",
                "description": "Pressure [Errata] suppresses the target.",
                "target_hp": mon.hp,
            }
        )


@register_move_special("pumpkingrab [errata]")
def _pumpkingrab_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Pumpkingrab [Errata]"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.position is None or ctx.defender.position is None:
        return
    if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 1:
        return
    ctx.battle._set_grapple_link(ctx.attacker_id, ctx.defender_id, ctx.attacker_id)
    if not ctx.attacker.has_status("Grappled"):
        ctx.attacker.statuses.append({"name": "Grappled"})
    if not ctx.defender.has_status("Grappled"):
        ctx.defender.statuses.append({"name": "Grappled"})
    if not ctx.attacker.has_status("Vulnerable"):
        ctx.attacker.statuses.append({"name": "Vulnerable", "remaining": 1})
    if not ctx.defender.has_status("Vulnerable"):
        ctx.defender.statuses.append({"name": "Vulnerable", "remaining": 1})
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Pumpkingrab [Errata]",
            "move": ctx.move.name,
            "effect": "grapple",
            "description": "Pumpkingrab grapples the target and grants dominance.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("probability control")
def _probability_control(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Probability Control"):
        return
    target_id = ctx.defender_id or ctx.attacker_id
    target = ctx.defender or ctx.attacker
    if target is None:
        return
    target.add_temporary_effect("probability_control", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": target_id,
            "ability": "Probability Control",
            "move": ctx.move.name,
            "effect": "reroll_ready",
            "description": "Probability Control allows a reroll on the target's next roll.",
            "target_hp": target.hp,
        }
    )


@register_move_special("protean")
def _protean_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Protean"):
        return
    ctx.attacker.add_temporary_effect("protean_ready", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Protean",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Protean readies a type shift.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("quick cloak")
def _quick_cloak_manual(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Quick Cloak"):
        return
    species = (ctx.attacker.spec.species or "").strip().lower()
    if species != "burmy":
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sand" in weather:
        cloak_type = "Ground"
    elif "hail" in weather or "snow" in weather:
        cloak_type = "Steel"
    else:
        cloak_type = "Grass"
    if cloak_type not in ctx.attacker.spec.types:
        ctx.attacker.spec.types.append(cloak_type)
    ctx.attacker.add_temporary_effect("quick_cloak_manual", type=cloak_type)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Quick Cloak",
            "move": ctx.move.name,
            "effect": "type_change",
            "type": cloak_type,
            "description": "Quick Cloak builds a new Burmy cloak.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("quick curl")
def _quick_curl(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Quick Curl") or has_errata(ctx.attacker, "Quick Curl"):
        return
    ctx.attacker.add_temporary_effect(
        "quick_curl_ready",
        expires_round=ctx.battle.round,
        ability="Quick Curl",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Quick Curl",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Quick Curl readies Defense Curl as a swift action.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("quick curl [errata]")
def _quick_curl_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Quick Curl [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "quick_curl_ready",
        expires_round=ctx.battle.round,
        ability="Quick Curl [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Quick Curl [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Quick Curl readies Defense Curl as an interrupt.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("rattled")
def _rattled(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Rattled"):
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spd",
        delta=1,
        effect="rattled",
        description="Rattled raises Speed.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Rattled",
            "move": ctx.move.name,
            "effect": "speed_raise",
            "description": "Rattled raises Speed.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("refridgerate")
def _refridgerate_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Refridgerate"):
        return
    ctx.attacker.add_temporary_effect("refridgerate_ready", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Refridgerate",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Refridgerate readies an Ice conversion.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("root down")
def _root_down(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Root Down"):
        return
    if not ctx.attacker.has_ability("Root Down"):
        return
    if not ctx.attacker.has_status("Ingrain"):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Root Down",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Root Down requires Ingrain.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    max_hp = ctx.attacker.max_hp()
    gain = max(1, int(max_hp // 16))
    gained = ctx.attacker.add_temp_hp(gain)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Root Down",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": gained,
            "temp_hp": ctx.attacker.temp_hp,
            "description": "Root Down grants temporary hit points.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("root down [errata]")
def _root_down_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Root Down [Errata]"):
        return
    if not ctx.attacker.has_status("Ingrain"):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Root Down [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Root Down requires Ingrain.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.add_temporary_effect(
        "damage_reduction",
        amount=5,
        expires_round=ctx.battle.round + 1,
        source="Root Down [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Root Down [Errata]",
            "move": ctx.move.name,
            "effect": "damage_reduction",
            "amount": 5,
            "description": "Root Down grants damage reduction.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("shackle")
def _shackle(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Shackle") or has_errata(ctx.attacker, "Shackle"):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("movement_halved", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Shackle",
            "move": ctx.move.name,
            "effect": "movement_halved",
            "description": "Shackle halves movement capabilities.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("shackle [errata]")
def _shackle_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Shackle [Errata]"):
        return
    if ctx.attacker.position is None:
        return
    for pid, mon in ctx.battle.pokemon.items():
        if not mon.active or mon.fainted or mon.position is None:
            continue
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 3:
            continue
        mon.add_temporary_effect("movement_halved", expires_round=ctx.battle.round + 1)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Shackle [Errata]",
                "move": ctx.move.name,
                "effect": "movement_halved",
                "description": "Shackle halves movement capabilities.",
                "target_hp": mon.hp,
            }
        )


@register_move_special("shadow tag")
def _shadow_tag_anchor(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Shadow Tag"):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    anchor = ctx.defender.position
    if anchor is not None:
        ctx.defender.add_temporary_effect(
            "shadow_tag_anchor",
            anchor=anchor,
            expires_round=ctx.battle.round + 5,
        )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="shadow_tag",
        description="Shadow Tag slows the target.",
        remaining=5,
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Trapped",
        effect="shadow_tag",
        description="Shadow Tag traps the target.",
        remaining=5,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Shadow Tag",
            "move": ctx.move.name,
            "effect": "anchor",
            "description": "Shadow Tag pins the target's shadow.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("shell cannon")
def _shell_cannon_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Shell Cannon"):
        return
    ctx.attacker.add_temporary_effect("shell_cannon_ready", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Shell Cannon",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Shell Cannon readies a power boost.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("shell shield")
def _shell_shield_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Shell Shield") or has_errata(ctx.attacker, "Shell Shield"):
        return
    ctx.attacker.add_temporary_effect(
        "shell_shield_ready",
        expires_round=ctx.battle.round,
        ability="Shell Shield",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Shell Shield",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Shell Shield readies an interrupting Withdraw.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("shell shield [errata]")
def _shell_shield_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Shell Shield [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "shell_shield_ready",
        expires_round=ctx.battle.round,
        ability="Shell Shield [Errata]",
    )
    ctx.attacker.add_temporary_effect(
        "damage_reduction",
        amount=10,
        expires_round=ctx.battle.round + 1,
        source="Shell Shield [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Shell Shield [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Shell Shield readies an interrupting Withdraw and grants damage reduction.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sonic courtship")
def _sonic_courtship_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Sonic Courtship") or has_errata(ctx.attacker, "Sonic Courtship"):
        return
    ctx.attacker.add_temporary_effect("sonic_courtship_active", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Sonic Courtship",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Sonic Courtship reshapes the next Attract.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sonic courtship [errata]")
def _sonic_courtship_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Sonic Courtship [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "sonic_courtship_active",
        expires_round=ctx.battle.round,
        mode="errata",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Sonic Courtship [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Sonic Courtship reshapes the next Attract.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sound lance")
def _sound_lance_ready(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Sound Lance") or has_errata(ctx.attacker, "Sound Lance"):
        return
    ctx.attacker.add_temporary_effect(
        "sound_lance_ready",
        expires_round=ctx.battle.round,
        mode="base",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Sound Lance",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Sound Lance readies a Supersonic strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sound lance [errata]")
def _sound_lance_errata_ready(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Sound Lance [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "sound_lance_ready",
        expires_round=ctx.battle.round,
        mode="errata",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Sound Lance [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Sound Lance readies a Supersonic strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("strange tempo")
def _strange_tempo(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Strange Tempo"):
        return
    if not (ctx.attacker.has_status("Confused") or ctx.attacker.has_status("Confusion")):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Strange Tempo",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Strange Tempo requires being confused.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.remove_status_by_names({"confused", "confusion"})
    stats = {
        "atk": ctx.attacker.spec.atk,
        "def": ctx.attacker.spec.defense,
        "spatk": ctx.attacker.spec.spatk,
        "spdef": ctx.attacker.spec.spdef,
        "spd": ctx.attacker.spec.spd,
    }
    chosen_stat = max(stats, key=stats.get)
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat=chosen_stat,
        delta=2,
        effect="strange_tempo",
        description="Strange Tempo cures confusion and raises a combat stage.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Strange Tempo",
            "move": ctx.move.name,
            "effect": "cure",
            "stat": chosen_stat,
            "description": "Strange Tempo steadies the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("leafy cloak")
def _leafy_cloak(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Leafy Cloak"):
        return
    choices = []
    for entry in ctx.attacker.get_temporary_effects("leafy_cloak_choice"):
        raw = entry.get("choices")
        if isinstance(raw, list):
            choices = [str(item).strip() for item in raw if item]
        elif isinstance(raw, str):
            choices = [item.strip() for item in raw.split(",") if item.strip()]
        if choices:
            break
    if not choices:
        choices = ["Chlorophyll", "Leaf Guard"]
    while ctx.attacker.remove_temporary_effect("ability_granted"):
        continue
    for ability in choices[:2]:
        ctx.attacker.add_temporary_effect("ability_granted", ability=ability, source="Leafy Cloak")
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Leafy Cloak",
            "move": ctx.move.name,
            "effect": "grant",
            "choices": choices[:2],
            "description": "Leafy Cloak grants chosen abilities.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("leaf rush")
def _leaf_rush(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Leaf Rush"):
        return
    half_speed = max(1, int(math.floor(calculations.speed_stat(ctx.attacker) / 2)))
    ctx.attacker.add_temporary_effect(
        "leaf_rush_ready",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
        half_speed=half_speed,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Leaf Rush",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Leaf Rush readies a priority Grass strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("maelstrom pulse", "maestrom pulse")
def _maelstrom_pulse(ctx: MoveSpecialContext) -> None:
    if not (ctx.attacker.has_ability("Maelstrom Pulse") or ctx.attacker.has_ability("Maestrom Pulse")):
        return
    half_speed = max(1, int(math.floor(calculations.speed_stat(ctx.attacker) / 2)))
    ctx.attacker.add_temporary_effect(
        "maelstrom_pulse_ready",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
        half_speed=half_speed,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Maelstrom Pulse",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Maelstrom Pulse readies a priority Water strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("mimicry")
def _mimicry(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Mimicry"):
        return
    terrain_name = ""
    if isinstance(ctx.battle.terrain, dict):
        terrain_name = (ctx.battle.terrain.get("name") or "").strip().lower()
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    combined = f"{terrain_name} {weather}".strip()
    choices = []
    if "beach" in combined:
        choices = ["Ground", "Water"]
    elif "cave" in combined:
        choices = ["Rock", "Dark"]
    elif "desert" in combined:
        choices = ["Ground", "Rock"]
    elif "forest" in combined:
        choices = ["Grass"]
    elif "ocean" in combined or "fresh water" in combined or "freshwater" in combined:
        choices = ["Water"]
    elif "grassland" in combined:
        choices = ["Normal", "Grass"]
    elif "marsh" in combined:
        choices = ["Water", "Poison"]
    elif "mountain" in combined:
        choices = ["Rock", "Ground"]
    elif "rainforest" in combined:
        choices = ["Grass", "Poison"]
    elif "taiga" in combined:
        choices = ["Ice", "Grass"]
    elif "tundra" in combined:
        choices = ["Ice"]
    elif "urban" in combined:
        choices = ["Normal", "Steel"]
    elif "sun" in combined:
        choices = ["Fire"]
    elif "rain" in combined or "storm" in combined or "downpour" in combined:
        choices = ["Water"]
    elif "hail" in combined or "snow" in combined:
        choices = ["Ice"]
    elif "sandstorm" in combined or "sand" in combined:
        choices = ["Rock"]
    if not choices:
        return
    pick = choices[0]
    for entry in ctx.attacker.get_temporary_effects("mimicry_choice"):
        raw = str(entry.get("choice") or "").strip().title()
        if raw in choices:
            pick = raw
            break
    old_types = list(ctx.attacker.spec.types)
    ctx.attacker.spec.types = [pick]
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Mimicry",
            "move": ctx.move.name,
            "effect": "type_change",
            "from": old_types,
            "to": [pick],
            "description": "Mimicry changes the user's type to match the field.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("missile launch")
def _missile_launch(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Missile Launch"):
        return
    if ctx.battle.grid is None or ctx.attacker.position is None:
        return
    tokens = []
    ax, ay = ctx.attacker.position
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]:
        coord = (ax + dx, ay + dy)
        if not ctx.battle.grid.in_bounds(coord):
            continue
        if coord in ctx.battle.grid.blockers:
            continue
        occupied = {
            mon.position
            for pid, mon in ctx.battle.pokemon.items()
            if mon.position is not None and mon.hp is not None and mon.hp > 0
        }
        if coord in occupied:
            continue
        tokens.append(coord)
        if len(tokens) >= 2:
            break
    ctx.attacker.add_temporary_effect(
        "missile_launch_tokens",
        tokens=tokens,
        round=ctx.battle.round,
    )
    for coord in tokens:
        tile = ctx.battle.grid.tiles.setdefault(coord, {})
        if isinstance(tile, dict):
            hazards = tile.setdefault("hazards", {})
            hazards["dreepy_token"] = hazards.get("dreepy_token", 0) + 1
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Missile Launch",
            "move": ctx.move.name,
            "effect": "deploy_tokens",
            "tokens": tokens,
            "description": "Missile Launch deploys Dreepy tokens.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("mud shield")
def _mud_shield(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Mud Shield"):
        return
    gained = ctx.attacker.add_temp_hp(ctx.attacker.tick_value() * 2)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Mud Shield",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": gained,
            "description": "Mud Shield grants temporary HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("grass pelt [errata]")
def _grass_pelt_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Grass Pelt [Errata]"):
        return
    gained = ctx.attacker.add_temp_hp(ctx.attacker.tick_value() * 2)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Grass Pelt [Errata]",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": gained,
            "description": "Grass Pelt [Errata] grants temporary HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("confidence")
def _confidence(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Confidence"):
        return
    stat = None
    for entry in ctx.attacker.get_temporary_effects("confidence_stat"):
        stat = str(entry.get("stat") or "").strip().lower()
        if stat:
            break
    if not stat:
        return
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if pid == ctx.attacker_id:
            continue
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=pid,
            move=ctx.move,
            target=mon,
            stat=stat,
            delta=1,
            effect="confidence",
            description="Confidence boosts an ally's combat stage.",
        )


@register_move_special("copycat")
def _copy_master(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Copy Master"):
        return
    stat = None
    for entry in ctx.attacker.get_temporary_effects("copy_master_stat"):
        stat = str(entry.get("stat") or "").strip().lower()
        if stat:
            break
    if not stat:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat=stat,
        delta=1,
        effect="copy_master",
        description="Copy Master boosts the chosen combat stage.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Copy Master",
            "move": ctx.move.name,
            "effect": "boost",
            "description": "Copy Master triggers on Copycat.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("whirlwind")
def _blow_away_tick(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not has_ability_exact(ctx.attacker, "Blow Away"):
        return
    damage = ctx.defender._apply_tick_damage(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Blow Away",
            "move": ctx.move.name,
            "effect": "tick",
            "amount": damage,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("whirlwind")
def _blow_away_errata(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not has_ability_exact(ctx.attacker, "Blow Away [Errata]"):
        return
    damage = ctx.defender._apply_tick_damage(1)
    ctx.battle._apply_push(ctx.attacker_id, ctx.defender_id, 2)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Blow Away [Errata]",
            "move": ctx.move.name,
            "effect": "tick",
            "amount": damage,
            "description": "Blow Away [Errata] adds a tick of damage.",
            "target_hp": ctx.defender.hp,
        }
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Blow Away [Errata]",
            "move": ctx.move.name,
            "effect": "push",
            "amount": 2,
            "description": "Blow Away [Errata] pushes the target further.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("swallow")
def _swallow_big_swallow(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if not ctx.attacker.has_ability("Big Swallow"):
        return
    count = ctx.battle._stockpile_count(ctx.attacker)
    if count <= 0:
        return
    boosted = min(3, count + 1)
    if boosted == count:
        return
    ctx.battle._set_stockpile_count(ctx.attacker, boosted)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Big Swallow",
            "move": ctx.move.name,
            "effect": "stockpile_boost",
            "count": boosted,
            "description": "Big Swallow boosts the stockpile count for Swallow.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("fake tears")
def _fake_tears_lower_spdef(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-2,
        effect="fake_tears",
        description="Fake Tears lowers Special Defense by -2 CS.",
    )


@register_move_special("final gambit")
def _final_gambit(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    hp_lost = max(0, int(ctx.attacker.hp or 0))
    if hp_lost <= 0:
        return
    ctx.attacker.apply_damage(hp_lost)
    extra_damage = max(0, hp_lost - int(ctx.damage_dealt or 0))
    if extra_damage > 0:
        ctx.defender.apply_damage(extra_damage)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "final_gambit",
            "hp_lost": hp_lost,
            "damage": hp_lost,
            "attacker_hp": ctx.attacker.hp,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("fishious rend")
def _fishious_rend_bonus(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.battle.current_actor_id != ctx.attacker_id:
        return
    if ctx.battle._initiative_index < 0:
        return
    attacker_index = None
    defender_index = None
    for idx, entry in enumerate(ctx.battle.initiative_order):
        if entry.actor_id == ctx.attacker_id:
            attacker_index = idx
        if entry.actor_id == ctx.defender_id:
            defender_index = idx
    if attacker_index is None or defender_index is None:
        return
    if defender_index <= attacker_index:
        return
    bonus = 10
    ctx.defender.apply_damage(bonus)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "fishious_rend_bonus",
            "amount": bonus,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("fissure")
def _fissure_execute(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = ctx.battle.rng.randint(1, 100)
    level_delta = int(ctx.attacker.spec.level) - int(ctx.defender.spec.level)
    threshold = max(1, min(100, 30 + level_delta))
    if roll > threshold:
        return
    defender_hp = ctx.defender.hp or 0
    if defender_hp > 0:
        ctx.defender.apply_damage(defender_hp)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "fissure",
            "roll": roll,
            "threshold": threshold,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("download")
def _download_analyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    weaker = "spdef" if ctx.defender.spec.spdef < ctx.defender.spec.defense else "def"
    mode = "special" if weaker == "spdef" else "physical"
    ctx.attacker.add_temporary_effect(
        "download",
        target_id=ctx.defender_id,
        mode=mode,
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Download",
            "move": ctx.move.name,
            "effect": "analyze",
            "mode": mode,
            "description": "Download analyzes the target's defenses.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("download [errata]")
def _download_errata(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Download [Errata]"):
        return
    if not ctx.hit or ctx.defender is None:
        return
    defense = int(ctx.defender.spec.defense or 0)
    spdef = int(ctx.defender.spec.spdef or 0)
    if defense < spdef:
        stat = "atk"
        outcome = "def_lower"
    elif spdef < defense:
        stat = "spatk"
        outcome = "spdef_lower"
    else:
        stat = ctx.battle.rng.choice(["atk", "def", "spatk", "spdef", "spd"])
        outcome = "tie"
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat=stat,
        delta=1,
        effect="download_errata",
        description="Download [Errata] raises a stat based on the target's defenses.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Download [Errata]",
            "move": ctx.move.name,
            "effect": "stat_raise",
            "stat": stat,
            "outcome": outcome,
            "description": "Download [Errata] compares defenses and raises a stat.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("dreamspinner")
def _dreamspinner_heal(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    sleeping_targets: List[str] = []
    if ctx.attacker.position is not None:
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id:
                continue
            if mon.hp is None or mon.hp <= 0 or mon.position is None:
                continue
            if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 10:
                continue
            if mon.has_status("Sleep") or mon.has_status("Asleep") or mon.has_status("Bad Sleep"):
                sleeping_targets.append(pid)
    else:
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id:
                continue
            if mon.hp is None or mon.hp <= 0:
                continue
            if mon.has_status("Sleep") or mon.has_status("Asleep") or mon.has_status("Bad Sleep"):
                sleeping_targets.append(pid)
    ticks = len(sleeping_targets)
    healed = ctx.attacker._apply_tick_heal(ticks) if ticks else 0
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Dreamspinner",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "targets": sleeping_targets,
            "description": "Dreamspinner heals for each sleeping foe.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("dreamspinner [errata]")
def _dreamspinner_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Dreamspinner [Errata]"):
        return
    if not ctx.hit:
        return
    sleeping_targets: List[str] = []
    if ctx.attacker.position is not None:
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id:
                continue
            if mon.hp is None or mon.hp <= 0 or mon.position is None:
                continue
            if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 3:
                continue
            if mon.has_status("Sleep") or mon.has_status("Asleep") or mon.has_status("Bad Sleep"):
                sleeping_targets.append(pid)
    else:
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id:
                continue
            if mon.hp is None or mon.hp <= 0:
                continue
            if mon.has_status("Sleep") or mon.has_status("Asleep") or mon.has_status("Bad Sleep"):
                sleeping_targets.append(pid)
    for pid in sleeping_targets:
        mon = ctx.battle.pokemon.get(pid)
        if mon is None:
            continue
        damage = mon._apply_tick_damage(1)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Dreamspinner [Errata]",
                "move": ctx.move.name,
                "effect": "drain",
                "amount": damage,
                "description": "Dreamspinner [Errata] drains sleeping foes.",
                "target_hp": mon.hp,
            }
        )
    temp_hp = ctx.attacker.add_temp_hp(ctx.attacker.tick_value()) if sleeping_targets else 0
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Dreamspinner [Errata]",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": temp_hp,
            "targets": sleeping_targets,
            "description": "Dreamspinner [Errata] grants temporary HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("electrodash")
def _electrodash_sprint(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect("sprint", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Electrodash",
            "move": ctx.move.name,
            "effect": "sprint",
            "description": "Electrodash grants Sprint movement.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("fade away")
def _fade_away(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect("fade_away", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Fade Away",
            "move": ctx.move.name,
            "effect": "fade_away",
            "description": "Fade Away grants temporary invisibility.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("fashion designer", "designer")
def _fashion_designer(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    choice = None
    for entry in ctx.attacker.get_temporary_effects("fashion_designer_choice"):
        choice = str(entry.get("item") or "").strip()
        if choice:
            break
    if choice is None:
        for entry in ctx.attacker.get_temporary_effects("designer_choice"):
            choice = str(entry.get("item") or "").strip()
            if choice:
                break
    mapping = {
        "Dew Cup": "Occa Berry",
        "Thorn Mantle": "Coba Berry",
        "Chewy Cluster": "Leftovers",
        "Lucky Leaf": "Lucky Leaf",
        "Tasty Reeds": "Tasty Reeds",
        "Decorative Twine": "Decorative Twine",
    }
    crafted = mapping.get(choice, choice)
    if crafted:
        ability_name = "Designer" if ctx.attacker.has_ability("Designer") else "Fashion Designer"
        ctx.attacker.spec.items.append({"name": crafted})
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": ability_name,
                "move": ctx.move.name,
                "effect": "craft",
                "item": crafted,
                "description": "Fashion Designer crafts a leaf accessory.",
                "target_hp": ctx.attacker.hp,
            }
        )


@register_move_special("gardener")
def _gardener(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.battle.grid is None or ctx.attacker.position is None:
        return
    tile = ctx.battle.grid.tiles.setdefault(ctx.attacker.position, {})
    tile_type = str(tile.get("type") or "").strip().lower()
    if "yielding plant" not in tile_type:
        return
    tile["soil_quality"] = int(tile.get("soil_quality", 0) or 0) + 1
    tile["gardener_used"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Gardener",
            "move": ctx.move.name,
            "effect": "soil_quality",
            "amount": tile.get("soil_quality"),
            "description": "Gardener improves the soil.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("gentle vibe")
def _gentle_vibe(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    targets: List["PokemonState"] = []
    if ctx.attacker.position is not None:
        for mon in ctx.battle.pokemon.values():
            if mon.position is None:
                continue
            if targeting.chebyshev_distance(ctx.attacker.position, mon.position) <= 2:
                targets.append(mon)
    else:
        targets = list(ctx.battle.pokemon.values())
    for mon in targets:
        for stat in mon.combat_stages:
            mon.combat_stages[stat] = 0
        mon.remove_status_by_names({"confused", "enraged", "infatuated"})
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Gentle Vibe",
            "move": ctx.move.name,
            "effect": "reset",
            "description": "Gentle Vibe resets stages and cures volatile statuses.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("gulp")
def _gulp(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    max_hp = ctx.attacker.max_hp()
    heal_amount = int(max_hp * 0.25)
    before = int(ctx.attacker.injuries or 0)
    if before > 0:
        ctx.attacker.injuries = max(0, before - 1)
    if heal_amount > 0:
        ctx.attacker.heal(heal_amount)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Gulp",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": heal_amount,
            "injuries_removed": before - int(ctx.attacker.injuries or 0),
            "description": "Gulp heals and removes an injury.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("ice shield")
def _ice_shield(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.battle.grid is None or ctx.attacker.position is None:
        return
    placed: List[tuple] = []
    for coord in movement.neighboring_tiles(ctx.attacker.position):
        if not ctx.battle.grid.in_bounds(coord):
            continue
        if coord in ctx.battle.grid.blockers:
            continue
        if any(mon.position == coord for mon in ctx.battle.pokemon.values()):
            continue
        ctx.battle.grid.blockers.add(coord)
        ctx.battle.grid.tiles.setdefault(coord, {})["type"] = "ice_shield"
        placed.append(coord)
        if len(placed) >= 3:
            break
    if placed:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Ice Shield",
                "move": ctx.move.name,
                "effect": "blockers",
                "count": len(placed),
                "description": "Ice Shield creates blocking ice segments.",
                "target_hp": ctx.attacker.hp,
            }
        )


@register_move_special("charge")
def _fluffy_charge(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if not ctx.attacker.has_ability("Fluffy Charge"):
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        effect="fluffy_charge",
        description="Fluffy Charge raises Defense.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Fluffy Charge",
            "move": ctx.move.name,
            "effect": "defense_boost",
            "description": "Fluffy Charge raises Defense after Charge.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("lovely kiss")
def _enfeebling_lips(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.attacker.has_ability("Enfeebling Lips"):
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-2,
        effect="enfeebling_lips",
        description="Enfeebling Lips lowers Defense by -2 CS.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Enfeebling Lips",
            "move": ctx.move.name,
            "effect": "defense_drop",
            "description": "Enfeebling Lips weakens the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("bug bite")
def _honey_thief(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    if not ctx.attacker.has_ability("Honey Thief"):
        return
    if not ctx.defender.food_buffs:
        return
    gained = ctx.attacker.tick_value()
    ctx.attacker.add_temp_hp(gained)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Honey Thief",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": gained,
            "description": "Honey Thief gains temp HP from Bug Bite.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("gore [errata]")
def _gore_errata_ready(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Gore [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "gore_errata_ready",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Gore [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Gore readies an empowered Horn Attack.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("horn attack")
def _gore_push(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender_id is None:
        return
    if has_ability_exact(ctx.attacker, "Gore [Errata]"):
        if not ctx.attacker.get_temporary_effects("gore_errata_ready"):
            return
        if ctx.attacker.get_temporary_effects("gore_errata_followup"):
            return
        ctx.attacker.remove_temporary_effect("gore_errata_ready")
        ctx.attacker.add_temporary_effect("gore_errata_followup", round=ctx.battle.round)
        try:
            if (
                ctx.defender is not None
                and ctx.defender.position is not None
                and ctx.defender.hp is not None
                and ctx.defender.hp > 0
            ):
                ctx.battle.resolve_move_targets(
                    attacker_id=ctx.attacker_id,
                    move=ctx.move,
                    target_id=ctx.defender_id,
                    target_position=ctx.defender.position,
                )
        finally:
            ctx.attacker.remove_temporary_effect("gore_errata_followup")
        ctx.battle._apply_push(ctx.attacker_id, ctx.defender_id, 2)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Gore [Errata]",
                "move": ctx.move.name,
                "effect": "push",
                "description": "Gore pushes the target farther.",
                "target_hp": ctx.defender.hp if ctx.defender else None,
            }
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Gore [Errata]",
                "move": ctx.move.name,
                "effect": "double_strike",
                "description": "Gore triggers a second Horn Attack.",
                "target_hp": ctx.defender.hp if ctx.defender else None,
            }
        )
        return
    if not ctx.attacker.has_ability("Gore"):
        return
    ctx.battle._apply_push(ctx.attacker_id, ctx.defender_id, 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Gore",
            "move": ctx.move.name,
            "effect": "push",
            "description": "Gore pushes the target.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("octazooka")
def _octazooka_accuracy_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll % 2 != 0:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        effect="octazooka",
        description="Octazooka lowers Accuracy on even rolls.",
        roll=roll,
    )


@register_move_special("octolock")
def _octolock_grapple(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._set_grapple_link(ctx.attacker_id, ctx.defender_id, ctx.attacker_id)
    ctx.defender.add_temporary_effect("octolock", source_id=ctx.attacker_id)
    ctx.battle._sync_grapple_status(ctx.attacker_id)
    ctx.battle._sync_grapple_status(ctx.defender_id)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "octolock",
            "description": "Octolock grapples the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("odor sleuth")
def _odor_sleuth_foresight(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect("foresight", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "foresight",
            "description": "Odor Sleuth grants foresight.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("foresight")
def _foresight_grants_foresight(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect("foresight", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "foresight",
            "description": "Foresight grants foresight.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("miracle eye")
def _miracle_eye_grants_focus(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect("miracle_eye", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "miracle_eye",
            "description": "Miracle Eye reveals the target's defenses.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("icy wind")
def _icy_wind_speed_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-1,
        effect="icy_wind",
        description="Icy Wind lowers Speed.",
    )


@register_move_special("leer")
def _leer_def_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if _fearsome_display_active(ctx.attacker):
        ctx.defender.add_temporary_effect(
            "fearsome_display_crit_vuln",
            bonus=2,
            source="Fearsome Display",
            source_id=ctx.attacker_id,
            trainer_id=ctx.attacker.controller_id,
            expires_round=ctx.battle.round + 1,
        )
        ctx.events.append(
            {
                "type": "trainer_feature",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "trainer": ctx.attacker.controller_id,
                "feature": "Fearsome Display",
                "move": ctx.move.name,
                "effect": "crit_range_bonus",
                "amount": 2,
                "description": "Fearsome Display widens critical ranges against the target for 1 full round.",
                "target_hp": ctx.defender.hp,
            }
        )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-1,
        effect="leer",
        description="Leer lowers Defense.",
    )


@register_move_special("metal sound")
def _metal_sound_spdef_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-2,
        effect="metal_sound",
        description="Metal Sound sharply lowers Special Defense.",
    )


@register_move_special("mud shot")
def _mud_shot_speed_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-1,
        effect="mud_shot",
        description="Mud Shot lowers Speed.",
    )


@register_move_special("mud-slap", "mud slap")
def _mud_slap_accuracy_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        effect="mud_slap",
        description="Mud-Slap lowers Accuracy.",
    )


@register_move_special("tail whip")
def _tail_whip_def_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-1,
        effect="tail_whip",
        description="Tail Whip lowers Defense.",
    )


@register_move_special("string shot")
def _string_shot_speed_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-1,
        effect="string_shot",
        description="String Shot lowers Speed.",
    )


@register_move_special("confuse ray")
def _confuse_ray_confusion(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="confuse_ray",
        description="Confuse Ray confuses the target.",
    )


@register_move_special("glare")
def _glare_accuracy_drop(ctx: MoveSpecialContext) -> None:
    if _fearsome_display_active(ctx.attacker) and ctx.defender is not None and ctx.defender_id is not None:
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat="spd",
            delta=-2,
            effect="fearsome_display",
            description="Fearsome Display lowers Speed with Glare.",
        )
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Accuracy Drop",
        effect="acc_drop",
        description="Glare lowers Accuracy.",
        remaining=3,
    )


@register_move_special("hypnosis")
def _hypnosis_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="hypnosis",
        description="Hypnosis puts the target to sleep.",
    )


@register_move_special("thunder wave")
def _thunder_wave_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="thunder_wave",
        description="Thunder Wave paralyzes the target.",
    )


@register_move_special("bite")
def _bite_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    text = _normalize_effects_text(_effects_text_for(ctx.move)).lower()
    threshold = 15
    match = _STATUS_PATTERN.search(text)
    if match and match.group("verb").lower().startswith("flinch"):
        try:
            threshold = int(match.group("threshold"))
        except (TypeError, ValueError):
            threshold = 15
    roll = _effect_roll(ctx)
    if roll < threshold:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinched",
        effect="bite",
        description="Bite flinches the target on a strong hit.",
        roll=roll,
        remaining=1,
    )


@register_move_special("ember")
def _ember_burn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 18:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect="ember",
        description="Ember burns the target on a high roll.",
        roll=roll,
    )


@register_move_special("energy ball")
def _energy_ball_spdef_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        effect="energy_ball",
        description="Energy Ball lowers Special Defense on a high roll.",
        roll=roll,
    )


@register_move_special("ice beam")
def _ice_beam_freeze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Frozen",
        effect="ice_beam",
        description="Ice Beam freezes the target on a high roll.",
        roll=roll,
    )


@register_move_special("spark")
def _spark_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="spark",
        description="Spark paralyzes the target on a high roll.",
        roll=roll,
    )


@register_move_special("thunder punch")
def _thunder_punch_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="thunder_punch",
        description="Thunder Punch paralyzes on a high roll.",
        roll=roll,
    )


@register_move_special("water pulse")
def _water_pulse_confuse(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="water_pulse",
        description="Water Pulse confuses on a high roll.",
        roll=roll,
    )


@register_move_special("flame burst")
def _flame_burst_splash(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    defender_pos = ctx.defender.position
    if defender_pos is None:
        return
    defender_team = ctx.battle._team_for(ctx.defender_id)
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.defender_id or mon.hp is None or mon.hp <= 0:
            continue
        if mon.position is None:
            continue
        if ctx.battle._team_for(pid) != defender_team:
            continue
        if abs(mon.position[0] - defender_pos[0]) + abs(mon.position[1] - defender_pos[1]) != 1:
            continue
        before_hp = mon.hp or 0
        mon.apply_damage(5)
        dealt = max(0, before_hp - (mon.hp or 0))
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": pid,
                "move": ctx.move.name,
                "effect": "flame_burst_splash",
                "amount": dealt,
                "description": "Flame Burst splashes adjacent allies of the target.",
                "target_hp": mon.hp,
            }
        )


@register_move_special("flamethrower")
def _flamethrower_burn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect="flamethrower",
        description="Flamethrower burns the target on a high roll.",
        roll=roll,
    )


@register_move_special("signal beam")
def _signal_beam_confuse(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="signal_beam",
        description="Signal Beam confuses the target on a high roll.",
        roll=roll,
    )


@register_move_special("silver wind")
def _silver_wind_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    for stat in ("atk", "def", "spatk", "spdef", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="silver_wind",
            description="Silver Wind boosts all stats on a high roll.",
            roll=roll,
        )


@register_move_special("sludge")
def _sludge_poison(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="sludge",
        description="Sludge poisons the target on a high roll.",
        roll=roll,
    )


@register_move_special("sludge bomb")
def _sludge_bomb_poison(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="sludge_bomb",
        description="Sludge Bomb poisons the target on a high roll.",
        roll=roll,
    )


@register_move_special("sludge wave")
def _sludge_wave_poison(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="sludge_wave",
        description="Sludge Wave poisons on a high roll.",
        roll=roll,
    )


@register_move_special("steel wing")
def _steel_wing_def_boost(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        effect="steel_wing",
        description="Steel Wing raises Defense on a high roll.",
        roll=roll,
    )


@register_move_special("stomp")
def _stomp_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="stomp",
        description="Stomp flinches the target on a high roll.",
        roll=roll,
    )


@register_move_special("stun spore")
def _stun_spore_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="stun_spore",
        description="Stun Spore paralyzes the target.",
    )


@register_move_special("struggle bug")
def _struggle_bug_spatk_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=-1,
        effect="struggle_bug",
        description="Struggle Bug lowers Special Attack.",
    )


@register_move_special("strange steam")
def _strange_steam_confuse(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="strange_steam",
        description="Strange Steam confuses the target on a high roll.",
        roll=roll,
    )


@register_move_special("bug buzz")
def _bug_buzz_spdef_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        effect="bug_buzz",
        description="Bug Buzz lowers Special Defense on a high roll.",
        roll=roll,
    )


@register_move_special("shadow ball")
def _shadow_ball_spdef_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        effect="shadow_ball",
        description="Shadow Ball lowers Special Defense on a high roll.",
        roll=roll,
    )


@register_move_special("shadow bone")
def _shadow_bone_def_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-1,
        effect="shadow_bone",
        description="Shadow Bone lowers Defense on a high roll.",
        roll=roll,
    )


@register_move_special("snore")
def _snore_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinched",
        effect="snore",
        description="Snore flinches on a high roll.",
        roll=roll,
        remaining=1,
    )


@register_move_special("thunder")
def _thunder_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="thunder",
        description="Thunder paralyzes the target on a high roll.",
        roll=roll,
    )


@register_move_special("sing")
def _sing_sleep(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.has_ability("Wistful Melody"):
        active_entry = next(iter(ctx.attacker.get_temporary_effects("wistful_melody_active")), None)
        if (
            active_entry is None
            or active_entry.get("round") != ctx.battle.round
            or (active_entry.get("move") or "").strip().lower() != (ctx.move.name or "").strip().lower()
        ):
            used_entry = next(iter(ctx.attacker.get_temporary_effects("wistful_melody_used")), None)
            used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
            if used_count < 1:
                if used_entry is None:
                    ctx.attacker.add_temporary_effect("wistful_melody_used", count=used_count + 1)
                else:
                    used_entry["count"] = used_count + 1
                ctx.attacker.add_temporary_effect(
                    "wistful_melody_active",
                    round=ctx.battle.round,
                    move=ctx.move.name,
                )
                active_entry = {"round": ctx.battle.round, "move": ctx.move.name}
        if active_entry and not ctx.defender.has_ability("Soundproof"):
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.defender_id,
                move=ctx.move,
                target=ctx.defender,
                stat="atk",
                delta=-2,
                effect="wistful_melody",
                description="Wistful Melody lowers Attack.",
            )
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.defender_id,
                move=ctx.move,
                target=ctx.defender,
                stat="spatk",
                delta=-2,
                effect="wistful_melody",
                description="Wistful Melody lowers Special Attack.",
            )
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "ability": "Wistful Melody",
                    "move": ctx.move.name,
                    "effect": "debuff",
                    "description": "Wistful Melody weakens targets of Sing.",
                    "target_hp": ctx.defender.hp,
                }
            )
    if not ctx.hit:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="sing",
        description="Sing puts the target to sleep.",
    )


@register_move_special("sleep powder")
def _sleep_powder_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="sleep_powder",
        description="Sleep Powder puts the target to sleep.",
    )


@register_move_special("supersonic")
def _supersonic_confuse(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.has_ability("Sound Lance"):
        entry = next(iter(ctx.attacker.get_temporary_effects("sound_lance_ready")), None)
        if entry is not None:
            ctx.attacker.remove_temporary_effect("sound_lance_ready")
            base_damage = calculations.offensive_stat(ctx.attacker, "special")
            mode = str(entry.get("mode") or "base").strip().lower()
            if mode == "errata":
                damage = int(base_damage)
                ability_name = "Sound Lance [Errata]"
                description = "Sound Lance deals special damage on Supersonic, even on a miss."
            else:
                type_mult = ptu_engine.type_multiplier("Normal", ctx.defender.spec.types)
                damage = int(math.floor(base_damage * type_mult))
                ability_name = "Sound Lance"
                description = "Sound Lance deals special damage on Supersonic."
            before = ctx.defender.hp or 0
            ctx.defender.apply_damage(damage)
            dealt = max(0, before - (ctx.defender.hp or 0))
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "ability": ability_name,
                    "move": ctx.move.name,
                    "effect": "damage",
                    "amount": dealt,
                    "description": description,
                    "target_hp": ctx.defender.hp,
                }
            )
    if not ctx.hit:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="supersonic",
        description="Supersonic confuses the target.",
    )


@register_move_special("sweet kiss")
def _sweet_kiss_confuse(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="sweet_kiss",
        description="Sweet Kiss confuses the target.",
    )


@register_move_special("sunny day")
def _sunny_day(ctx: MoveSpecialContext) -> None:
    ctx.battle.weather = "Sunny"
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "sunny_day",
            "weather": ctx.battle.weather,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("slack off")
def _slack_off_heal(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    before = ctx.attacker.hp or 0
    heal_amount = max(0, ctx.attacker.max_hp() // 2)
    ctx.attacker.heal(heal_amount)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "slack_off",
            "amount": healed,
            "target_hp": ctx.attacker.hp,
        }
    )
    if _fearsome_display_active(ctx.attacker):
        removed = ctx.attacker.remove_status_by_names(_FEARSOME_DISPLAY_CURE_NAMES)
        if removed:
            ctx.events.append(
                {
                    "type": "trainer_feature",
                    "actor": ctx.attacker_id,
                    "target": ctx.attacker_id,
                    "trainer": ctx.attacker.controller_id,
                    "feature": "Fearsome Display",
                    "move": ctx.move.name,
                    "effect": "cure_status",
                    "status": removed,
                    "description": "Fearsome Display cures one status affliction after Slack Off.",
                    "target_hp": ctx.attacker.hp,
                }
            )


@register_move_special("shift gear")
def _shift_gear_boost(ctx: MoveSpecialContext) -> None:
    for stat, delta in (("atk", 1), ("spd", 2)):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=delta,
            effect="shift_gear",
            description="Shift Gear boosts Attack and Speed.",
        )


@register_move_special("superpower")
def _superpower_recoil_stats(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    for stat in ("atk", "def"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=-1,
            effect="superpower",
            description="Superpower lowers the user's Attack and Defense.",
        )


@register_move_special("tail glow")
def _tail_glow_boost(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=3,
        effect="tail_glow",
        description="Tail Glow sharply raises Special Attack.",
    )


@register_move_special("tearful look")
def _tearful_look_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    for stat in ("atk", "spatk"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=-1,
            effect="tearful_look",
            description="Tearful Look lowers Attack and Special Attack.",
        )


@register_move_special("take heart")
def _take_heart_boost(ctx: MoveSpecialContext) -> None:
    for stat in ("atk", "def", "spatk", "spdef", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="take_heart",
            description="Take Heart boosts all stats and cures status conditions.",
        )
    cure_names = {
        "burned",
        "burn",
        "poisoned",
        "poison",
        "badly poisoned",
        "paralyzed",
        "paralyze",
        "frozen",
        "freeze",
        "frostbite",
        "sleep",
        "asleep",
        "drowsy",
        "confused",
        "confusion",
        "enraged",
        "suppressed",
        "charmed",
        "fear",
        "taunted",
    }
    ctx.attacker.remove_status_by_names(cure_names)
    ctx.attacker.clear_volatile_statuses()
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "take_heart",
            "description": "Take Heart cures status conditions.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("taunt")
def _taunt_enrage(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Enraged"):
        ctx.defender.statuses.append({"name": "Enraged", "remaining": 1})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "taunt",
            "status": "Enraged",
            "description": "Taunt enrages the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("aura pulse")
def _aura_pulse_spdef_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        effect="aura_pulse",
        description="Aura Pulse lowers Special Defense on a high roll.",
        roll=roll,
    )


@register_move_special("avalanche")
def _avalanche_delay(ctx: MoveSpecialContext) -> None:
    if ctx.attacker.get_temporary_effects("delayed"):
        return
    if ctx.attacker_id != ctx.battle.current_actor_id:
        return
    ctx.attacker.add_temporary_effect("delayed", move=ctx.move.name)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "avalanche_delay",
            "description": "Avalanche delays until the end of the round.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("double-edge")
def _double_edge_recoil(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.damage_dealt <= 0:
        return
    fraction = 1 / 3
    if (
        ctx.attacker.has_ability("Rock Head")
        or has_ability_exact(ctx.attacker, "Rock Head [Errata]")
        or ctx.attacker.has_ability("Abominable")
        or ctx.attacker.has_ability("Abominable [Errata]")
    ):
        return
    ctx.battle._apply_self_damage_fraction(
        ctx.events,
        attacker_id=ctx.attacker_id,
        move=ctx.move,
        attacker=ctx.attacker,
        fraction=fraction,
        base_damage=ctx.damage_dealt,
        effect="recoil",
        description=f"{ctx.move.name} deals recoil damage.",
    )


@register_move_special("fairy wind")
def _fairy_wind_evasion_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Evasion Drop",
        effect="fairy_wind",
        description="Fairy Wind lowers Evasion on a high roll.",
        remaining=3,
        roll=roll,
    )


@register_move_special("giga impact")
def _giga_impact_exhaust(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect("exhaust_next_turn")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "exhaust",
            "description": "Giga Impact exhausts the user after attacking.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_global_move_special(phase="post_damage")
def _exhaust_moves(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    range_text = (ctx.move.range_text or "").lower()
    if "exhaust" not in range_text and not move_has_keyword(ctx.move, "exhaust"):
        return
    ctx.attacker.add_temporary_effect("exhaust_next_turn")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "exhaust",
            "description": f"{ctx.move.name} exhausts the user after attacking.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("psychic")
def _psychic_spdef_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        effect="psychic",
        description="Psychic lowers Special Defense on a high roll.",
        roll=roll,
    )


@register_move_special("psyshock", phase="end_action")
def _psyshock_defense(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "psyshock",
            "description": "Psyshock uses Defense for damage calculation.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("pursuit", phase="end_action")
def _pursuit_interrupt(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "pursuit",
            "description": "Pursuit can interrupt fleeing targets.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("swift", phase="end_action")
def _swift_always_hits(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "always_hit",
            "description": "Swift cannot miss.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("baton pass", phase="end_action")
def _baton_pass(ctx: MoveSpecialContext) -> None:
    replacement_id = None
    if ctx.defender_id and ctx.defender_id != ctx.attacker_id:
        if ctx.battle._team_for(ctx.defender_id) == ctx.battle._team_for(ctx.attacker_id):
            replacement_id = ctx.defender_id
    ctx.battle._execute_baton_pass(ctx.attacker_id, replacement_id)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": replacement_id,
            "move": ctx.move.name,
            "effect": "baton_pass",
            "description": "Baton Pass swaps the user with a benched ally.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("u-turn", phase="end_action")
def _u_turn_recall(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    _pivot_switch(ctx, effect="u_turn")


@register_move_special("flip turn", phase="end_action")
def _flip_turn_recall(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    _pivot_switch(ctx, effect="flip_turn")


@register_move_special("water gun", phase="end_action")
def _water_gun_fountain(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "fountain",
            "description": "Water Gun grants Fountain.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("wing attack", phase="end_action")
def _wing_attack_guster(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "guster",
            "description": "Wing Attack grants Guster.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("shelter")
def _shelter_boost(ctx: MoveSpecialContext) -> None:
    for stat in ("def", "spdef"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="shelter",
            description="Shelter raises Defense and Special Defense.",
        )
    ctx.attacker.add_temporary_effect(
        "evasion_bonus", amount=2, scope="all", expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "shelter",
            "description": "Shelter raises evasion.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("shore up")
def _shore_up_heal(ctx: MoveSpecialContext) -> None:
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sand" in weather:
        fraction = 2 / 3
    elif any(token in weather for token in ("sun", "rain", "hail")):
        fraction = 1 / 4
    else:
        fraction = 1 / 2
    before = ctx.attacker.hp or 0
    heal_amount = int(math.floor(ctx.attacker.max_hp() * fraction))
    ctx.attacker.heal(heal_amount)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "shore_up",
            "amount": healed,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("simple beam")
def _simple_beam(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.battle._blocks_ability_replace(ctx.defender):
        ctx.events.append(
            {
                "type": "item",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "item": "Ability Shield",
                "effect": "block_ability_replace",
                "description": "Ability Shield prevents ability replacement.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    ctx.defender.add_temporary_effect("entrained_ability", ability="Simple")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "simple_beam",
            "ability": "Simple",
            "description": "Simple Beam replaces the target's ability with Simple.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("sweet scent")
def _sweet_scent_evasion_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect(
        "evasion_bonus", amount=-2, scope="all", expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sweet_scent",
            "description": "Sweet Scent lowers evasion.",
            "target_hp": ctx.defender.hp,
        }
    )
    if has_ability_exact(ctx.attacker, "Danger Syrup [Errata]") and not ctx.defender.has_status("Blinded"):
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Blinded",
            effect="danger_syrup_errata",
            description="Danger Syrup [Errata] blinds the target.",
            remaining=1,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Danger Syrup [Errata]",
                "move": ctx.move.name,
                "effect": "blind",
                "description": "Danger Syrup [Errata] blinds the target.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("tailwind")
def _tailwind(ctx: MoveSpecialContext) -> None:
    team = ctx.battle._team_for(ctx.attacker_id)
    ctx.battle.tailwind_teams.add(team)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "tailwind",
            "description": "Tailwind boosts allied initiative.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("tickle")
def _tickle_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    for stat in ("atk", "def"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=-1,
            effect="tickle",
            description="Tickle lowers Attack and Defense.",
        )


@register_move_special("toxic threads")
@register_move_special("toxic thread")
def _toxic_threads(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    poisoned = ctx.defender.has_status("Poisoned") or ctx.defender.has_status("Badly Poisoned")
    if poisoned:
        tick_damage = ctx.defender._apply_tick_damage(1)
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "toxic_threads_damage",
                "amount": tick_damage,
                "description": "Toxic Threads deals a tick of damage to poisoned targets.",
                "target_hp": ctx.defender.hp,
            }
        )
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat="spd",
            delta=-2,
            effect="toxic_threads",
            description="Toxic Threads sharply lowers Speed on poisoned targets.",
        )
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="toxic_threads",
        description="Toxic Threads poisons the target.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-1,
        effect="toxic_threads",
        description="Toxic Threads lowers Speed.",
    )


@register_move_special("tri attack")
def _tri_attack_status(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    if ctx.attacker.has_ability("Trinity"):
        entry = next(iter(ctx.attacker.get_temporary_effects("trinity_tri_attack")), None)
        count = int(entry.get("count", 0) or 0) if entry else 0
        if entry is None or entry.get("round") != ctx.battle.round:
            while ctx.attacker.remove_temporary_effect("trinity_tri_attack"):
                continue
            ctx.attacker.add_temporary_effect(
                "trinity_tri_attack",
                round=ctx.battle.round,
                count=0,
            )
            count = 0
            entry = next(iter(ctx.attacker.get_temporary_effects("trinity_tri_attack")), None)
        order = ["Frozen", "Burned", "Paralyzed"]
        status = order[count % 3]
        if entry is not None:
            entry["count"] = count + 1
    else:
        outcome = ctx.battle.rng.randint(1, 3)
        status = "Paralyzed" if outcome == 1 else "Burned" if outcome == 2 else "Frozen"
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status=status,
        effect="tri_attack",
        description="Tri Attack inflicts a status on a high roll.",
        roll=roll,
    )


@register_move_special("strength sap")
def _strength_sap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    phys = calculations.offensive_stat(ctx.defender, "physical")
    spec = calculations.offensive_stat(ctx.defender, "special")
    stat = "atk" if phys >= spec else "spatk"
    heal_amount = max(0, phys if stat == "atk" else spec)
    before = ctx.attacker.hp or 0
    ctx.attacker.heal(heal_amount)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat=stat,
        delta=-1,
        effect="strength_sap",
        description="Strength Sap lowers the target's offensive stat.",
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "strength_sap",
            "amount": healed,
            "description": "Strength Sap heals the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("spotlight")
def _spotlight_blind(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Blinded",
        effect="spotlight",
        description="Spotlight blinds the target.",
        remaining=1,
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Vulnerable",
        effect="spotlight",
        description="Spotlight leaves the target vulnerable.",
        remaining=1,
    )


@register_move_special("steamroller")
def _steamroller_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="steamroller",
        description="Steamroller flinches the target on a high roll.",
        roll=roll,
    )


@register_move_special("take aim")
def _take_aim_accuracy(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect(
        "accuracy_bonus", amount=1, expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "take_aim",
            "description": "Take Aim boosts accuracy.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("spirit shackle")
def _spirit_shackle_trap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Trapped",
        effect="spirit_shackle",
        description="Spirit Shackle traps the target.",
        remaining=2,
    )


@register_move_special("stockpile")
def _stockpile(ctx: MoveSpecialContext) -> None:
    current = ctx.battle._stockpile_count(ctx.attacker)
    if current >= 3:
        return
    ctx.battle._set_stockpile_count(ctx.attacker, current + 1)
    for stat in ("def", "spdef"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="stockpile",
            description="Stockpile increases defenses.",
        )


@register_move_special("thunder shock")
def _thunder_shock_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="thunder_shock",
        description="Thunder Shock paralyzes the target on a high roll.",
        roll=roll,
    )


@register_move_special("thunderbolt")
def _thunderbolt_paralyze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="thunderbolt",
        description="Thunderbolt paralyzes the target on a high roll.",
        roll=roll,
    )


@register_move_special("rage")
def _rage_enrage(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if not ctx.attacker.has_status("Enraged"):
        ctx.attacker.statuses.append({"name": "Enraged", "remaining": 1})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "rage",
            "status": "Enraged",
            "description": "Rage enrages the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("scary face")
def _scary_face_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-2,
        effect="scary_face",
        description="Scary Face sharply lowers Speed.",
    )


@register_move_special("screech")
def _screech_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-2,
        effect="screech",
        description="Screech sharply lowers Defense.",
    )


@register_move_special("waterfall")
def _waterfall_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="flinch",
        description="Waterfall flinches on 17+.",
        roll=roll,
    )


@register_move_special("wear down")
def _wear_down_def_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if not roll or roll % 2 != 0:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-1,
        description="Wear Down lowers Defense on even rolls.",
        effect="wear_down",
        roll=roll,
    )


@register_move_special("whirlpool")
def _whirlpool_trap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Vortex"):
        ctx.defender.statuses.append({"name": "Vortex", "remaining": 3})
    if not ctx.defender.has_status("Trapped"):
        ctx.defender.statuses.append({"name": "Trapped", "remaining": 3})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "whirlpool",
            "status": "Vortex",
            "description": "Whirlpool traps the target in a vortex.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("will-o-wisp")
def _will_o_wisp_burn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect="burn",
        description="Will-O-Wisp burns the target.",
    )


@register_move_special("wish")
def _wish_schedule(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    target_id = ctx.defender_id or ctx.attacker_id
    if ctx.attacker.has_ability("Wishmaster"):
        target = ctx.battle.pokemon.get(target_id) if target_id else None
        if target is None:
            return
        choice = None
        choice_stat = None
        entry = next(iter(ctx.attacker.get_temporary_effects("wishmaster_choice")), None)
        if isinstance(entry, dict):
            choice = str(entry.get("choice") or "").strip().lower()
            choice_stat = str(entry.get("stat") or "").strip().lower() or None
        if choice in {"cure", "status"} or (choice is None and target.statuses):
            if target.statuses:
                target.statuses = []
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": target_id,
                    "ability": "Wishmaster",
                    "move": ctx.move.name,
                    "effect": "cure",
                    "description": "Wishmaster cures status ailments immediately.",
                    "target_hp": target.hp,
                }
            )
            return
        if choice in {"boost", "stat"} or choice is None:
            stats = ["atk", "def", "spatk", "spdef", "spd"]
            if choice_stat in stats:
                stat = choice_stat
            else:
                stat = min(stats, key=lambda key: target.combat_stages.get(key, 0))
            before = target.combat_stages.get(stat, 0)
            if before < 6:
                ctx.battle._apply_combat_stage(
                    ctx.events,
                    attacker_id=ctx.attacker_id,
                    target_id=target_id,
                    move=ctx.move,
                    target=target,
                    stat=stat,
                    delta=2,
                    effect="wishmaster",
                    description="Wishmaster grants a combat stage boost.",
                )
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.attacker_id,
                        "target": target_id,
                        "ability": "Wishmaster",
                        "move": ctx.move.name,
                        "effect": "boost",
                        "stat": stat,
                        "description": "Wishmaster boosts a combat stage instead of delaying.",
                        "target_hp": target.hp,
                    }
                )
                return
        max_hp = target.max_hp()
        before = target.hp or 0
        heal_amount = max(1, max_hp // 2)
        target.heal(heal_amount)
        healed = max(0, (target.hp or 0) - before)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": target_id,
                "ability": "Wishmaster",
                "move": ctx.move.name,
                "effect": "instant_heal",
                "amount": healed,
                "description": "Wishmaster resolves Wish immediately.",
                "target_hp": target.hp,
            }
        )
        return
    entry = {"caster_id": ctx.attacker_id, "target_id": target_id, "trigger_round": ctx.battle.round + 1}
    if target_id == ctx.attacker_id and ctx.attacker.position is not None:
        entry["self_target"] = True
        entry["team"] = ctx.battle._team_for(ctx.attacker_id)
        entry["position"] = ctx.attacker.position
    ctx.battle.wishes.append(entry)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": target_id,
            "move": ctx.move.name,
            "effect": "wish",
            "description": "Wish will heal the target at the end of the next turn.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("withdraw")
def _withdraw_defense(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if not ctx.attacker.has_status("Withdrawn"):
        ctx.attacker.statuses.append({"name": "Withdrawn"})
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        description="Withdraw raises Defense by +1 CS.",
        effect="withdraw",
    )
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "withdraw",
            "status": "Withdrawn",
            "description": "Withdrawn grants damage reduction and blocks movement.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("wonder room")
def _wonder_room(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle.room_effects.append(
        {"name": "Wonder Room", "remaining": 5, "starts_round": ctx.battle.round}
    )
    for mon in ctx.battle.pokemon.values():
        if mon.active and not mon.has_status("Wondered"):
            mon.statuses.append({"name": "Wondered", "remaining": 5})
    ctx.events.append(
        {
            "type": "room",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "wonder_room",
            "description": "Wonder Room swaps Defense and Special Defense for 5 rounds.",
            "remaining": 5,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("work up")
def _work_up(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    for stat in ("atk", "spatk"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            description="Work Up raises Attack and Special Attack by +1 CS.",
            effect="work_up",
        )


@register_move_special("worry seed")
def _worry_seed(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.battle._blocks_ability_replace(ctx.defender):
        ctx.events.append(
            {
                "type": "item",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "item": "Ability Shield",
                "effect": "block_ability_replace",
                "description": "Ability Shield prevents ability replacement.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    ctx.defender.add_temporary_effect("entrained_ability", ability="Insomnia")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "worry_seed",
            "ability": "Insomnia",
            "description": "Worry Seed replaces the target's ability with Insomnia.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("wounding strike")
def _wounding_strike(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    tick_damage = ctx.defender._apply_tick_damage(1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "wounding_strike",
            "amount": tick_damage,
            "description": "Wounding Strike deals a tick of damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("wrap")
def _wrap_bonus(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.attacker.add_temporary_effect("wrap_grapple_bonus", expires_round=ctx.battle.round + 2)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "wrap",
            "description": "Wrap grants bonuses to grapple contests.",
            "target_hp": ctx.defender.hp,
        }
    )
    if ctx.attacker.has_ability("Crush Trap") and not ctx.attacker.get_temporary_effects(
        "crush_trap_used"
    ):
        struggle_move = MoveSpec(
            name="Struggle",
            type="Typeless",
            category="Physical",
            db=4,
            ac=None,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
            crit_range=100,
        )
        struggle_result = resolve_move_action(
            rng=ctx.battle.rng,
            attacker=ctx.attacker,
            defender=ctx.defender,
            move=struggle_move,
            weather=ctx.battle.effective_weather(),
            terrain=ctx.battle.terrain,
            force_hit=True,
        )
        before_hp = ctx.defender.hp or 0
        ctx.defender.apply_damage(struggle_result.get("damage", 0))
        struggle_damage = max(0, before_hp - (ctx.defender.hp or 0))
        ctx.attacker.add_temporary_effect("crush_trap_used")
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Crush Trap",
                "move": ctx.move.name,
                "effect": "struggle_damage",
                "amount": struggle_damage,
                "description": "Crush Trap deals Struggle damage on a successful Wrap.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("zap cannon")
def _zap_cannon(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="paralyze",
        description="Zap Cannon paralyzes the target.",
    )


@register_move_special("zen headbutt")
def _zen_headbutt_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="flinch",
        description="Zen Headbutt flinches on 15+.",
        roll=roll,
    )


@register_move_special("zing zap")
def _zing_zap_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="flinch",
        description="Zing Zap flinches on 15+.",
        roll=roll,
    )


@register_move_special("skitter smack")
def _skitter_smack_spatk_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=-1,
        effect="skitter_smack",
        description="Skitter Smack lowers Special Attack by -1 CS.",
    )


@register_move_special("spore")
def _spore_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="spore",
        description="Spore puts the target to sleep.",
    )


@register_move_special("sprint")
def _sprint_boost(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("sprint", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "sprint",
            "description": "Sprint increases movement by 50% this turn.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sprint [errata]")
def _sprint_errata_boost(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("sprint", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "sprint",
            "description": "Sprint increases movement by 50% this turn.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("strength sap")
def _strength_sap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    physical = calculations.offensive_stat(ctx.defender, "physical")
    special = calculations.offensive_stat(ctx.defender, "special")
    heal_amount = max(physical, special)
    before = ctx.attacker.hp or 0
    ctx.attacker.heal(heal_amount)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "strength_sap",
            "amount": healed,
            "description": "Strength Sap restores HP based on the target's stats.",
            "target_hp": ctx.attacker.hp,
        }
    )
    stat = "atk" if physical >= special else "spatk"
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat=stat,
        delta=-1,
        effect="strength_sap",
        description="Strength Sap lowers the target's offensive stat.",
    )


@register_move_special("super fang")
def _super_fang_halve(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    current = max(0, int(ctx.defender.hp or 0))
    damage = current // 2
    if damage <= 0:
        return
    ctx.defender.apply_damage(damage)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "super_fang",
            "amount": damage,
            "description": "Super Fang halves the target's current HP.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("swords dance")
def _swords_dance(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=2,
        effect="swords_dance",
        description="Swords Dance sharply raises Attack.",
    )


@register_move_special("synthesis")
def _synthesis_heal(ctx: MoveSpecialContext) -> None:
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" in weather:
        fraction = 2 / 3
    elif any(token in weather for token in ("rain", "sand", "hail")):
        fraction = 1 / 4
    else:
        fraction = 1 / 2
    before = ctx.attacker.hp or 0
    heal_amount = int(math.floor(ctx.attacker.max_hp() * fraction))
    ctx.attacker.heal(heal_amount)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "synthesis",
            "amount": healed,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("swagger", "swagger [sm]")
def _swagger(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=2,
        effect="swagger",
        description="Swagger sharply raises Attack.",
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="swagger",
        description="Swagger confuses the target.",
    )


@register_move_special("teeter dance")
def _teeter_dance(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="teeter_dance",
        description="Teeter Dance confuses the target.",
    )


@register_move_special("thousand waves")
def _thousand_waves_trap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Trapped",
        effect="thousand_waves",
        description="Thousand Waves traps the target.",
        remaining=2,
    )


@register_move_special("throat chop")
def _throat_chop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect(
        "sonic_blocked", expires_round=ctx.battle.round + 2, source=ctx.move.name
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "throat_chop",
            "description": "Throat Chop blocks Sonic moves for two rounds.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("thunder fang")
def _thunder_fang(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = _effect_roll(ctx)
    if roll < 18:
        return
    if roll >= 20:
        outcomes = ["Paralyzed", "Flinch"]
    else:
        outcomes = ["Paralyzed"] if ctx.battle.rng.randint(1, 2) == 1 else ["Flinch"]
    for status in outcomes:
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status=status,
            effect="thunder_fang",
            description="Thunder Fang inflicts a status on a high roll.",
            roll=roll,
        )


@register_move_special("topsy-turvy")
def _topsy_turvy(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    for stat, stage in ctx.defender.combat_stages.items():
        if not stage:
            continue
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=-2 * int(stage),
            effect="topsy_turvy",
            description="Topsy-Turvy inverts combat stages.",
        )


@register_move_special("torment")
def _torment(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Suppressed",
        effect="torment",
        description="Torment suppresses the target.",
    )


@register_move_special("skill swap")
def _skill_swap(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.battle._blocks_ability_replace(ctx.attacker):
        ctx.events.append(
            {
                "type": "item",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "item": "Ability Shield",
                "effect": "block_ability_replace",
                "description": "Ability Shield prevents ability replacement.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if ctx.battle._blocks_ability_replace(ctx.defender):
        ctx.events.append(
            {
                "type": "item",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "item": "Ability Shield",
                "effect": "block_ability_replace",
                "description": "Ability Shield prevents ability replacement.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    attacker_abilities = [
        str(entry.get("name") or "").strip()
        for entry in (ctx.attacker.spec.abilities or [])
        if str(entry.get("name") or "").strip()
    ]
    defender_abilities = [
        str(entry.get("name") or "").strip()
        for entry in (ctx.defender.spec.abilities or [])
        if str(entry.get("name") or "").strip()
    ]
    if not attacker_abilities or not defender_abilities:
        return
    chosen_attacker = attacker_abilities[0]
    chosen_defender = ctx.battle.rng.choice(defender_abilities)
    while ctx.attacker.remove_temporary_effect("entrained_ability"):
        continue
    while ctx.defender.remove_temporary_effect("entrained_ability"):
        continue
    ctx.attacker.add_temporary_effect("entrained_ability", ability=chosen_defender)
    ctx.defender.add_temporary_effect("entrained_ability", ability=chosen_attacker)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "skill_swap",
            "attacker_ability": chosen_defender,
            "defender_ability": chosen_attacker,
            "description": "Skill Swap exchanges abilities.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("prismatic laser")
def _prismatic_laser_skill_swap(ctx: MoveSpecialContext) -> None:
    _skill_swap(ctx)


@register_move_special("synchronoise", phase="pre_damage")
def _synchronoise_requires_type_match(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    attacker_types = {str(t or "").strip().lower() for t in ctx.attacker.spec.types or []}
    defender_types = {str(t or "").strip().lower() for t in ctx.defender.spec.types or []}
    if attacker_types & defender_types:
        return
    ctx.result["hit"] = False
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "synchronoise_invalid",
            "description": "Synchronoise fails without a shared type.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("tar shot")
def _tar_shot(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("tar_shot", expires_round=ctx.battle.round + 5)
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spd",
        delta=-1,
        effect="tar_shot",
        description="Tar Shot lowers Speed and coats the target.",
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "tar_shot",
            "description": "Tar Shot coats the target against Fire attacks.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("trick-or-treat")
def _trick_or_treat(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Trick-or-Treat"):
        ctx.defender.statuses.append(
            {"name": "Trick-or-Treat", "added": True, "added_type": "Ghost", "remaining": 5}
        )
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "trick_or_treat",
            "status": "Trick-or-Treat",
            "description": "Trick-or-Treat adds the Ghost type.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("twister")
def _twister_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 18:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="twister",
        description="Twister flinches on 18+.",
        roll=roll,
    )


@register_move_special("trop kick")
def _trop_kick(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect(
        "trop_kick_penalty", amount=-5, expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "trop_kick",
            "description": "Trop Kick penalizes damage rolls next round.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("water sport")
def _water_sport(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    targets: List[str] = []
    if ctx.battle.grid is not None and ctx.attacker.position is not None:
        target_pos = ctx.defender.position if ctx.defender and ctx.defender.position is not None else None
        tiles = targeting.affected_tiles(ctx.battle.grid, ctx.attacker.position, target_pos, ctx.move)
        for pid, mon in ctx.battle.pokemon.items():
            if mon.position is None or mon.hp is None or mon.hp <= 0:
                continue
            if mon.position not in tiles:
                continue
            mon.add_temporary_effect("water_sport", expires_round=ctx.battle.round + 5)
            targets.append(pid)
    else:
        for pid, mon in ctx.battle.pokemon.items():
            if mon.hp is None or mon.hp <= 0:
                continue
            mon.add_temporary_effect("water_sport", expires_round=ctx.battle.round + 5)
            targets.append(pid)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "water_sport",
            "targets": targets,
            "description": "Water Sport coats targets with fire resistance.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("triple arrows")
def _triple_arrows_drop(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    for stat in ("def", "spdef"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=-1,
            effect="triple_arrows",
            description="Triple Arrows lowers Defense and Special Defense.",
        )


@register_move_special("thousand arrows", phase="pre_damage")
def _thousand_arrows_override_immunity(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    defender_types = {str(t or "").strip().lower() for t in ctx.defender.spec.types or []}
    if "flying" not in defender_types and not ctx.defender.has_ability("Levitate"):
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", 0) or 0)
    if pre_type_damage > 0 and int(ctx.result.get("damage", 0) or 0) <= 0:
        ctx.result["damage"] = pre_type_damage
        ctx.result["type_multiplier"] = 1.0


@register_move_special("thousand arrows")
def _thousand_arrows_ground(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("force_grounded", expires_round=ctx.battle.round + 3)
    if not ctx.defender.has_status("Grounded"):
        ctx.defender.statuses.append({"name": "Grounded", "remaining": 3})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "thousand_arrows",
            "status": "Grounded",
            "description": "Thousand Arrows grounds the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("sweeping strike")
def _sweeping_strike_trip(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Tripped"):
        ctx.defender.statuses.append({"name": "Tripped"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sweeping_strike",
            "status": "Tripped",
            "description": "Sweeping Strike trips the target.",
            "target_hp": ctx.defender.hp,
        }
    )

@register_move_special("sleep talk")
def _sleep_talk(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if not (ctx.attacker.has_status("Sleep") or ctx.attacker.has_status("Asleep")):
        return
    candidates: List[str] = []
    for move in ctx.attacker.spec.moves:
        name = str(move.name or "").strip()
        if not name or name.lower() == "sleep talk":
            continue
        candidates.append(name)
    if not candidates:
        return
    chosen = ctx.battle.rng.choice(candidates)
    ctx.attacker.add_temporary_effect("sleep_talk_shift", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sleep_talk",
            "selected_move": chosen,
            "description": "Sleep Talk selects a random move.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("stone axe")
def _stone_axe_vortex(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.get_temporary_effects("stone_axe_used"):
        return
    ctx.attacker.add_temporary_effect("stone_axe_used")
    if not ctx.defender.has_status("Vortex"):
        ctx.defender.statuses.append({"name": "Vortex", "remaining": 3})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "stone_axe",
            "status": "Vortex",
            "description": "Stone Axe traps the target in a vortex.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("shell trap")
def _shell_trap_ready(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("shell_trap_ready", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "shell_trap",
            "description": "Shell Trap readies an interrupt trigger.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sky uppercut")
def _sky_uppercut_interrupt(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sky_uppercut",
            "description": "Sky Uppercut may be used as an interrupt.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("sucker punch", "sucker punch [sm]")
def _sucker_punch_interrupt(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sucker_punch",
            "description": "Sucker Punch may be used as an interrupt.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("surging strikes")
def _surging_strikes_log(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "surging_strikes",
            "description": "Surging Strikes can chain attacks and shifts.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("wide guard")
def _wide_guard_ready(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("wide_guard_ready", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "wide_guard",
            "description": "Wide Guard readies an interrupt shield.",
            "target_hp": ctx.attacker.hp,
        }
    )

@register_move_special("sticky web")
def _sticky_web_hazard(ctx: MoveSpecialContext) -> None:
    if ctx.battle.grid is None:
        return
    _place_hazard_on_target_tile(ctx, "sticky_web", 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "sticky_web",
            "hazard": "sticky_web",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("toxic spikes")
def _toxic_spikes_hazard(ctx: MoveSpecialContext) -> None:
    if ctx.battle.grid is None:
        return
    _place_hazard_on_target_tile(ctx, "toxic_spikes", 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "toxic_spikes",
            "hazard": "toxic_spikes",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("trump card", phase="end_action")
def _trump_card_stack(ctx: MoveSpecialContext) -> None:
    entry = next(iter(ctx.attacker.get_temporary_effects("trump_card")), None)
    count = 0
    if entry:
        try:
            count = max(0, int(entry.get("count", 0) or 0))
        except (TypeError, ValueError):
            count = 0
    count += 1
    if entry:
        entry["count"] = count
    else:
        ctx.attacker.add_temporary_effect("trump_card", count=count)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "trump_card",
            "count": count,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("venoshock", phase="end_action")
def _venoshock_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    if not (ctx.defender.has_status("Poisoned") or ctx.defender.has_status("Badly Poisoned")):
        return
    bonus = max(0, 13 - int(ctx.move.db or 0))
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "venoshock",
            "bonus_db": bonus,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("terrain pulse", phase="end_action")
def _terrain_pulse_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    terrain_name = ""
    if isinstance(ctx.battle.terrain, dict):
        terrain_name = (ctx.battle.terrain.get("name") or "").strip().lower()
    if terrain_name.startswith("grassy"):
        terrain_type = "Grass"
    elif terrain_name.startswith("electric"):
        terrain_type = "Electric"
    elif terrain_name.startswith("misty"):
        terrain_type = "Fairy"
    elif terrain_name.startswith("psychic"):
        terrain_type = "Psychic"
    else:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "terrain_pulse",
            "type": terrain_type,
            "db": 10,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("techno blast", phase="end_action")
def _techno_blast_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    item_type = ctx.battle._item_type_from_item(ctx.attacker.equipped_weapon())
    if item_type is None:
        for entry in ctx.attacker.spec.items:
            item_type = ctx.battle._item_type_from_item(entry)
            if item_type:
                break
    if not item_type:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "techno_blast",
            "type": item_type,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("september playtest")
def _september_playtest(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        effect="september_playtest",
        description="September Playtest raises Defense by +1 CS.",
    )


@register_move_special("thunderous kick")
def _thunderous_kick(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-1,
        effect="thunderous_kick",
        description="Thunderous Kick lowers Defense by -1 CS.",
    )


@register_move_special("titanic slam")
def _titanic_slam(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll % 2 != 0:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="titanic_slam",
        description="Titanic Slam slows the target on even rolls.",
        remaining=1,
        roll=roll,
    )


@register_move_special("vine whip", phase="end_action")
def _vine_whip_threaded(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "threaded",
            "description": "Vine Whip grants Threaded.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("slam", phase="end_action")
def _slam_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    sprinting = bool(ctx.attacker.get_temporary_effects("sprint"))
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "slam",
            "smite": sprinting,
            "description": "Slam may gain Smite after Sprint.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("slice", phase="end_action")
def _slice_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "slice",
            "description": "Slice requires a melee weapon.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("spirit lance", phase="end_action")
def _spirit_lance_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    entry = next(
        (
            e
            for e in ctx.attacker.get_temporary_effects("spirit_lance_hits")
            if e.get("round") == ctx.battle.round
        ),
        None,
    )
    count = 0
    if entry:
        try:
            count = max(0, int(entry.get("count", 0) or 0))
        except (TypeError, ValueError):
            count = 0
    count += 1
    if entry:
        entry["count"] = count
    else:
        ctx.attacker.add_temporary_effect("spirit_lance_hits", round=ctx.battle.round, count=count)
    bonus = max(0, (count - 1) * 3)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "spirit_lance",
            "bonus_damage": bonus,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("struggle", phase="end_action")
def _struggle_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "struggle",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("struggle+", phase="end_action")
def _struggle_plus_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "struggle_plus",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("substitute")
def _substitute(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    max_hp = ctx.attacker.max_hp()
    cost = max(1, int(math.floor(max_hp * 0.25)))
    if (ctx.attacker.hp or 0) <= cost:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "move": ctx.move.name,
                "effect": "substitute_failed",
                "description": "Substitute fails without enough HP.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.apply_damage(cost, skip_injury=True)
    substitute_hp = max(1, int(math.floor(max_hp * 0.25)) + 1)
    ctx.attacker.add_temporary_effect("substitute", hp=substitute_hp)
    if not ctx.attacker.has_status("Substitute"):
        ctx.attacker.statuses.append({"name": "Substitute"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "substitute",
            "status": "Substitute",
            "amount": substitute_hp,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("telekinesis")
def _telekinesis(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Lifted"):
        ctx.defender.statuses.append({"name": "Lifted", "remaining": 5})
    if not ctx.defender.has_status("Slowed"):
        ctx.defender.statuses.append({"name": "Slowed", "remaining": 5})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "telekinesis",
            "status": "Lifted",
            "description": "Telekinesis lifts the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("teleport")
def _teleport(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "teleport",
            "description": "Teleport repositions the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("terrorize")
def _terrorize(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    contest = ctx.battle._skill_contest(
        ctx.attacker,
        ctx.defender,
        ["intimidate"],
        ["intimidate", "focus"],
        attacker_id=ctx.attacker_id,
        defender_id=ctx.defender_id,
    )
    if contest["attacker_wins"]:
        ctx.defender.temp_hp = 0
        ctx.defender.add_temporary_effect("at_will_only", until_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "terrorize",
            "result": "success" if contest["attacker_wins"] else "fail",
            "attacker_total": contest["attacker_total"],
            "defender_total": contest["defender_total"],
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("thunder wave [sm]")
def _thunder_wave_sm(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    defender_types = {str(t or "").strip().lower() for t in ctx.defender.spec.types or []}
    if "ground" in defender_types:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "immune",
                "description": "Electric-immune targets ignore Thunder Wave.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="thunder_wave_sm",
        description="Thunder Wave paralyzes the target.",
    )


@register_move_special("triple axel", phase="end_action")
def _triple_axel_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "triple_axel",
            "description": "Triple Axel may chain attacks and shifts.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("triple kick", phase="end_action")
def _triple_kick_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    entry = next(iter(ctx.attacker.get_temporary_effects("triple_kick_stage")), None)
    stage = 1
    if entry:
        try:
            stage = max(1, min(3, int(entry.get("stage", 1) or 1)))
        except (TypeError, ValueError):
            stage = 1
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "triple_kick",
            "stage": stage,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("triple kick [la]", phase="end_action")
def _triple_kick_la_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "triple_kick_la",
            "description": "Triple Kick [LA] may chain attacks and shifts.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("triple threat", phase="end_action")
def _triple_threat_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "triple_threat",
            "description": "Triple Threat requires specific weapon types.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("vacuum wave", phase="end_action")
def _vacuum_wave_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "vacuum_wave",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )

@register_move_special("volt switch", phase="end_action")
def _volt_switch_recall(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    _pivot_switch(ctx, effect="volt_switch")


@register_move_special("vicegrip", phase="end_action")
def _vicegrip_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "vicegrip",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("victory dance")
def _victory_dance(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect(
        "victory_dance_ready", expires_round=ctx.battle.round + 1
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        effect="victory_dance",
        description="Victory Dance raises Defense by +1 CS.",
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "victory_dance",
            "description": "Victory Dance readies extra damage on the next Fighting move.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("x-scissor", phase="end_action")
def _x_scissor_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "x_scissor",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )

@register_move_special("surf", phase="end_action")
def _surf_shift(ctx: MoveSpecialContext) -> None:
    if ctx.battle.grid is None or ctx.attacker.position is None:
        return
    target_pos = None
    if ctx.defender is not None and ctx.defender.position is not None:
        target_pos = ctx.defender.position
    tiles = targeting.affected_tiles(
        ctx.battle.grid, ctx.attacker.position, target_pos, ctx.move
    )
    if not tiles:
        return
    ctx.attacker.add_temporary_effect(
        "surf_shift", tiles=list(tiles), expires_round=ctx.battle.round
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "surf_shift",
            "description": "Surf allows shifting within its area of effect.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sunsteel strike", phase="end_action")
def _sunsteel_strike_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sunsteel_strike",
            "description": "Sunsteel Strike ignores defensive abilities.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )

@register_move_special("trick room")
def _trick_room(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.battle.room_effects.append(
        {"name": "Trick Room", "remaining": 5, "starts_round": ctx.battle.round}
    )
    ctx.events.append(
        {
            "type": "room",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "trick_room",
            "description": "Trick Room reverses initiative order for 5 rounds.",
            "remaining": 5,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("uproar")
def _uproar_cure_sleep(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if any(
        entry.get("round") == ctx.battle.round
        for entry in ctx.attacker.get_temporary_effects("uproar_triggered")
    ):
        return
    ctx.attacker.add_temporary_effect("uproar_triggered", round=ctx.battle.round)
    cured: List[str] = []
    for pid, mon in ctx.battle.pokemon.items():
        if mon.hp is None or mon.hp <= 0:
            continue
        if ctx.battle.grid is not None and ctx.attacker.position is not None and mon.position is not None:
            if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 5:
                continue
        removed = mon.remove_status_by_names({"sleep", "asleep", "bad sleep"})
        if removed:
            cured.append(pid)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "uproar",
            "targets": cured,
            "description": "Uproar wakes nearby sleepers.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("wake-up slap")
def _wake_up_slap_cure(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    removed = ctx.defender.remove_status_by_names({"sleep", "asleep", "bad sleep"})
    if not removed:
        return
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "wake_up_slap",
            "status": "Sleep",
            "description": "Wake-Up Slap cures sleep.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("spite")
def _spite_disable(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    last_entry = next(
        (
            entry
            for entry in ctx.defender.get_temporary_effects("last_move")
            if entry.get("name")
        ),
        None,
    )
    if not last_entry:
        return
    if ctx.defender.has_status("Disabled"):
        return
    ctx.defender.statuses.append(
        {"name": "Disabled", "move": last_entry.get("name"), "remaining": 3}
    )
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "spite",
            "status": "Disabled",
            "description": "Spite disables the target's last move.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("splash")
def _splash(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    ctx.attacker.add_temporary_effect(
        "evasion_bonus", amount=2, scope="all", expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "splash",
            "description": "Splash grants +2 evasion until the end of the next turn.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("thunder cage")
def _thunder_cage(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.has_status("Vortex"):
        ctx.defender.statuses.append({"name": "Vortex", "remaining": 3})
    if not ctx.defender.has_status("Trapped"):
        ctx.defender.statuses.append({"name": "Trapped", "remaining": 3})
    ctx.defender.add_temporary_effect(
        "vortex_dc_bonus", amount=3, expires_round=ctx.battle.round + 3, source=ctx.move.name
    )
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "thunder_cage",
            "status": "Vortex",
            "description": "Thunder Cage traps the target in a vortex.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("slash", phase="end_action")
def _slash_crit_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.result.get("crit"):
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "high_crit",
            "roll": ctx.result.get("roll"),
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("stone edge", phase="end_action")
def _stone_edge_crit_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.result.get("crit"):
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "high_crit",
            "roll": ctx.result.get("roll"),
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("storm throw", phase="end_action")
def _storm_throw_crit_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.result.get("crit"):
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "forced_crit",
            "roll": ctx.result.get("roll"),
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("stored power", phase="end_action")
def _stored_power_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    positive_cs = sum(max(0, stage) for stage in ctx.attacker.combat_stages.values())
    if positive_cs <= 0:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "stored_power",
            "bonus_db": 2 * positive_cs,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("spit up", phase="end_action")
def _spit_up_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    stockpile_count = ctx.battle._stockpile_count(ctx.attacker)
    if stockpile_count <= 0:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "spit_up",
            "count": stockpile_count,
            "bonus_db": 8 * stockpile_count,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("stomping tantrum", phase="end_action")
def _stomping_tantrum_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    entry = next(
        (
            e
            for e in ctx.attacker.get_temporary_effects("last_move_failed")
            if e.get("round") == ctx.battle.round
        ),
        None,
    )
    if entry is None:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "stomping_tantrum",
            "description": "Stomping Tantrum is boosted after a failed move.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("water spout", phase="end_action")
def _water_spout_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    max_hp = ctx.attacker.max_hp()
    missing = max(0, max_hp - (ctx.attacker.hp or 0))
    reduction = int((missing * 10) // max_hp) if max_hp else 0
    if reduction <= 0:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "water_spout",
            "reduction": reduction,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("wring out", phase="end_action")
def _wring_out_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    max_hp = ctx.defender.max_hp()
    missing = max(0, max_hp - (ctx.defender.hp or 0))
    reduction = int((missing * 10) // max_hp) if max_hp else 0
    if reduction <= 0:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "wring_out",
            "reduction": reduction,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("weather ball", phase="end_action")
def _weather_ball_log(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    weather_type = None
    if "sun" in weather:
        weather_type = "Fire"
    elif "rain" in weather:
        weather_type = "Water"
    elif "hail" in weather or "snow" in weather:
        weather_type = "Ice"
    elif "sand" in weather:
        weather_type = "Rock"
    if not weather_type:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "weather_ball",
            "type": weather_type,
            "db": 10,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_global_move_special(phase="post_damage")
def _aftermath_burst(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.damage_dealt <= 0 or not ctx.defender.fainted:
        return
    if not has_ability_exact(ctx.defender, "Aftermath"):
        return
    damp_blockers = ctx.battle._ability_in_radius(ctx.defender.position, "Damp", 10)
    if damp_blockers:
        ctx.events.append(
            {
                "type": "ability",
                "actor": damp_blockers[0],
                "target": ctx.attacker_id,
                "ability": "Damp",
                "move": ctx.move.name,
                "effect": "block_aftermath",
                "description": "Damp blocks Aftermath.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    center = ctx.defender.position
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.defender_id or mon.fainted or mon.hp is None or mon.hp <= 0:
            continue
        if center is not None and mon.position is not None:
            if targeting.chebyshev_distance(center, mon.position) > 1:
                continue
        damage = max(1, mon.max_hp() // 4)
        before = mon.hp or 0
        mon.apply_damage(damage)
        dealt = max(0, before - (mon.hp or 0))
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": pid,
                "ability": "Aftermath",
                "move": ctx.move.name,
                "effect": "burst",
                "amount": dealt,
                "description": "Aftermath bursts for a quarter of each target's max HP.",
                "target_hp": mon.hp,
            }
        )


@register_global_move_special(phase="post_damage")
def _frostbite_freeze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.attacker.has_ability("Frostbite"):
        return
    move_type = (ctx.move.type or "").strip().lower()
    if move_type != "ice":
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll <= 0:
        roll = ctx.battle.rng.randint(1, 20)
    if roll < 18:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="frostbite_slow",
        description="Frostbite slows the target on a high roll.",
        roll=roll,
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Frozen",
        effect="frostbite_freeze",
        description="Frostbite freezes the target on a high roll.",
        roll=roll,
    )


@register_global_move_special(phase="post_damage")
def _hay_fever_status_burst(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.attacker.has_ability("Hay Fever"):
        return
    if (ctx.move.category or "").strip().lower() != "status":
        return
    defender_types = {t.lower().strip() for t in ctx.defender.spec.types if t}
    if "bug" in defender_types:
        return
    block_ability = ctx.defender.indirect_damage_block_ability()
    if block_ability:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": block_ability,
                "move": ctx.move.name,
                "effect": "hay_fever_block",
                "description": f"{block_ability} prevents Hay Fever damage.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    damage = ctx.defender._apply_tick_damage(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Hay Fever",
            "move": ctx.move.name,
            "effect": "hay_fever",
            "amount": damage,
            "description": "Hay Fever harms foes hit by status moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_global_move_special(phase="post_damage")
def _heat_mirage_evasion(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    if not ctx.attacker.has_ability("Heat Mirage"):
        return
    move_type = (ctx.move.type or "").strip().lower()
    if move_type != "fire":
        return
    ctx.attacker.add_temporary_effect(
        "evasion_bonus",
        amount=3,
        expires_round=ctx.battle.round + 1,
        source="Heat Mirage",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Heat Mirage",
            "move": ctx.move.name,
            "effect": "heat_mirage",
            "amount": 3,
            "description": "Heat Mirage grants evasion after Fire moves.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_global_move_special(phase="post_damage")
def _fiery_crash_burn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.attacker.has_ability("Fiery Crash"):
        return
    keywords = {str(k).strip().lower() for k in (ctx.move.keywords or [])}
    if "dash" not in keywords:
        return
    move_type = (ctx.move.type or "").strip().lower()
    if move_type != "fire":
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    if not ctx.defender.has_status("Burned"):
        ctx.defender.statuses.append({"name": "Burned"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Fiery Crash",
            "move": ctx.move.name,
            "effect": "burn",
            "status": "Burned",
            "roll": roll,
            "target_hp": ctx.defender.hp,
        }
    )


@register_global_move_special(phase="post_damage")
def _riposte_ready_on_miss(ctx: MoveSpecialContext) -> None:
    if ctx.hit:
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    if targeting.normalized_target_kind(ctx.move) != "melee":
        return
    if ctx.defender.get_temporary_effects("riposte_ready"):
        return
    ctx.defender.add_temporary_effect(
        "riposte_ready", round=ctx.battle.round, source_id=ctx.attacker_id
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "riposte_ready",
            "description": "Riposte is readied after a missed melee attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_global_move_special
def _helper_accuracy_boost(ctx: MoveSpecialContext) -> None:
    defender = ctx.defender
    defender_id = ctx.defender_id
    if defender is None or defender_id is None:
        return
    if not ctx.attacker.has_ability("Helper"):
        return
    if ctx.attacker_id == defender_id:
        return
    if ctx.battle._team_for(ctx.attacker_id) != ctx.battle._team_for(defender_id):
        return
    target_kind = targeting.normalized_target_kind(ctx.move)
    area_kind = targeting.normalized_area_kind(ctx.move)
    if area_kind or target_kind in {"self", "field"}:
        return
    for entry in list(defender.get_temporary_effects("accuracy_bonus")):
        if str(entry.get("source") or "").strip().lower() == "helper":
            if entry in defender.temporary_effects:
                defender.temporary_effects.remove(entry)
    for entry in list(defender.get_temporary_effects("skill_bonus")):
        if str(entry.get("source") or "").strip().lower() == "helper":
            if entry in defender.temporary_effects:
                defender.temporary_effects.remove(entry)
    defender.add_temporary_effect(
        "accuracy_bonus",
        amount=1,
        expires_round=ctx.battle.round + 1,
        source="Helper",
    )
    defender.add_temporary_effect(
        "skill_bonus",
        amount=1,
        expires_round=ctx.battle.round + 1,
        source="Helper",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": defender_id,
            "ability": "Helper",
            "move": ctx.move.name,
            "effect": "helper",
            "description": "Helper boosts an ally's accuracy and skill checks.",
            "target_hp": defender.hp,
        }
    )


@register_move_special("defog")
def _defog(ctx: MoveSpecialContext) -> None:
    set_weather(ctx.battle, "Clear")
    clear_hazards(ctx.battle)
    for mon in ctx.battle.pokemon.values():
        mon.remove_status_by_names({"mist", "safeguard"})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "defog",
            "description": "Defog clears hazards and field protections.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("court change")
def _court_change(ctx: MoveSpecialContext) -> None:
    swap_hazards(ctx.battle)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "court_change",
            "description": "Court Change swaps hazard control.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("mist")
def _mist(ctx: MoveSpecialContext) -> None:
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        existing = None
        for status in mon.statuses:
            if mon._normalized_status_name(status) == "mist":
                existing = status
                break
        if isinstance(existing, dict):
            existing["charges"] = max(int(existing.get("charges", 0) or 0), 3)
        elif not mon.has_status("Mist"):
            mon.statuses.append({"name": "Mist", "charges": 3})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "mist",
            "description": "Mist protects against combat stage drops.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("electric terrain")
def _electric_terrain(ctx: MoveSpecialContext) -> None:
    set_terrain(ctx.battle, "Electric Terrain", rounds=5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "electric_terrain",
            "description": "Electric Terrain energizes the field.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("misty terrain")
def _misty_terrain(ctx: MoveSpecialContext) -> None:
    set_terrain(ctx.battle, "Misty Terrain", rounds=5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "misty_terrain",
            "description": "Misty Terrain shrouds the field.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("follow me")
def _follow_me(ctx: MoveSpecialContext) -> None:
    apply_follow_me(ctx.attacker, expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "follow_me",
            "description": "Follow Me redirects attacks toward the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("acid armor")
def _acid_armor(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker:
        return
    if ctx.attacker.has_status("Liquefied"):
        ctx.attacker.remove_status_by_names({"Liquefied", "Slowed"})
    stage_events: List[dict] = []
    ctx.battle._apply_combat_stage(
        stage_events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        effect="acid_armor",
        description="Acid Armor hardens the user's defenses.",
    )
    for event in stage_events:
        ctx.events.append(event)


@register_move_special("blizzard")
def _blizzard_freeze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.defender:
        return
    roll = ctx.result.get("roll")
    if roll is None:
        return
    ctx.battle._apply_status_on_roll(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        target=ctx.defender,
        status="Frozen",
        effect="freeze",
        description="Blizzard may freeze on a high roll.",
        roll=int(roll),
        threshold=15,
    )


@register_move_special("bounce")
def _bounce_special(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.defender:
        return
    roll = ctx.result.get("roll")
    if roll is not None:
        ctx.battle._apply_status_on_roll(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id or "",
            move=ctx.move,
            target=ctx.defender,
            status="Paralyzed",
            effect="paralyze",
            description="Bounce may paralyze on a high roll.",
            roll=int(roll),
            threshold=16,
        )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        target=ctx.defender,
        status="Vulnerable",
        effect="vulnerable",
        description="Bounce leaves the target vulnerable.",
        remaining=1,
    )


@register_move_special("expanding force")
def _expanding_force(ctx: MoveSpecialContext) -> None:
    if ctx.attacker.get_temporary_effects("expanding_force_used"):
        return
    ctx.attacker.add_temporary_effect("expanding_force_used")
    set_terrain(ctx.battle, "Psychic Terrain", rounds=5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "psychic_terrain",
            "description": "Expanding Force creates Psychic Terrain.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("fairy lock")
def _fairy_lock(ctx: MoveSpecialContext) -> None:
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) == team:
            continue
        if mon.fainted or not mon.active:
            continue
        mon.statuses.append({"name": "Trapped", "source": "fairy lock", "source_id": ctx.attacker_id})
        mon.statuses.append({"name": "Slowed", "source": "fairy lock", "source_id": ctx.attacker_id})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "fairy_lock",
            "description": "Fairy Lock traps opposing combatants.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("fake out", "first impression")
def _first_strike_flinch(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.defender:
        return
    joined_this_round = any(
        entry.get("round") == ctx.battle.round
        for entry in ctx.attacker.get_temporary_effects("joined_round")
    )
    if not joined_this_round:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="flinch",
        description=f"{ctx.move.name} flinches the target.",
        remaining=1,
    )


@register_move_special("gastro acid")
def _gastro_acid(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    abilities = ctx.defender.ability_names()
    chosen = abilities[0] if abilities else None
    disable_ability(ctx.defender, chosen)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "ability_disabled",
            "description": "Gastro Acid suppresses the target's ability.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("geomancy")
def _geomancy(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker:
        return
    for stat in ("spatk", "spdef", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=2,
            effect="geomancy",
            description="Geomancy empowers the user.",
        )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "geomancy",
            "description": "Geomancy raises Special Attack, Special Defense, and Speed.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("glacial lance")
def _glacial_lance(ctx: MoveSpecialContext) -> None:
    if not ctx.defender or not ctx.hit:
        return
    apply_trap_status(
        ctx.battle,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        stuck=True,
        trapped=True,
        remaining=1,
        effect="trap",
        description="Glacial Lance traps the target.",
        roll=ctx.result.get("roll"),
    )


@register_move_special("grapple")
def _grapple_move(ctx: MoveSpecialContext) -> None:
    if not ctx.defender or not ctx.hit:
        return
    ctx.battle._apply_grapple_contest(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        attacker=ctx.attacker,
        defender=ctx.defender,
        effect="grapple",
        description="Grapple initiates a contest.",
    )


@register_move_special("mean look")
def _mean_look(ctx: MoveSpecialContext) -> None:
    if not ctx.defender or not ctx.hit:
        return
    apply_trap_status(
        ctx.battle,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        stuck=True,
        trapped=True,
        remaining=999,
        effect="trap",
        description="Mean Look traps the target.",
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="slow",
        description="Mean Look slows the target.",
        remaining=999,
    )
    if _fearsome_display_active(ctx.attacker):
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id or "",
            move=ctx.move,
            target=ctx.defender,
            status="Suppressed",
            effect="fearsome_display",
            description="Fearsome Display suppresses the target after Mean Look.",
            remaining=1,
        )


@register_move_special("mist ball")
def _mist_ball(ctx: MoveSpecialContext) -> None:
    if not ctx.defender or not ctx.hit:
        return
    roll = ctx.result.get("roll")
    if roll is None:
        return
    if int(roll) % 2 == 0:
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id or "",
            move=ctx.move,
            target=ctx.defender,
            stat="spatk",
            delta=-1,
            effect="mist_ball",
            description="Mist Ball lowers Special Attack.",
        )


@register_move_special("misty explosion", phase="end_action")
def _misty_explosion(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker:
        return
    ctx.attacker.hp = -int(ctx.attacker.max_hp() * 0.5)
    set_terrain(ctx.battle, "Misty Terrain", rounds=5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "misty_explosion",
            "description": "Misty Explosion leaves the user at -50% HP and sets Misty Terrain.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("roost")
def _roost(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker:
        return
    heal = int(max(1, ctx.attacker.max_hp() // 2))
    before = ctx.attacker.hp or 0
    ctx.attacker.hp = min(ctx.attacker.max_hp(), before + heal)
    if any((t or "").strip().lower() == "flying" for t in ctx.attacker.spec.types):
        ctx.attacker.spec.types = [t for t in ctx.attacker.spec.types if (t or "").strip().lower() != "flying"]
        ctx.attacker.statuses.append({"name": "Roost", "removed_type": "Flying", "remaining": 1})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "roost",
            "amount": ctx.attacker.hp - before,
            "description": "Roost restores health and removes Flying temporarily.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("steel roller")
def _steel_roller(ctx: MoveSpecialContext) -> None:
    clear_hazards(ctx.battle)
    ctx.battle.terrain = None
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "steel_roller",
            "description": "Steel Roller removes hazards and clears terrain.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("power shift")
def _power_shift(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker:
        return
    if not ctx.attacker.has_status("Power Shift"):
        ctx.attacker.statuses.append({"name": "Power Shift"})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "power_shift",
            "description": "Power Shift swaps offensive and defensive stats.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("power trick")
def _power_trick(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker:
        return
    if not ctx.attacker.has_status("Power Trick"):
        ctx.attacker.statuses.append({"name": "Power Trick"})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "power_trick",
            "description": "Power Trick swaps Attack and Defense.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("role play")
def _role_play(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    abilities = ctx.defender.ability_names()
    if not abilities:
        return
    chosen = ctx.battle.rng.choice(abilities)
    while ctx.attacker.remove_temporary_effect("entrained_ability"):
        continue
    ctx.attacker.add_temporary_effect("entrained_ability", ability=chosen, source="role play")
    add_restore_on_switch(ctx.attacker, abilities=list(ctx.attacker.spec.abilities))
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "role_play",
            "description": "Role Play copies the target's ability.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("mimic")
def _mimic(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    last_entries = ctx.defender.get_temporary_effects("last_move")
    last_entries.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
    if not last_entries:
        return
    move_name = str(last_entries[0].get("name") or "")
    if not move_name:
        return
    replacement = ctx.battle._find_known_move(ctx.defender, move_name)
    if replacement is None:
        return
    original_moves = list(ctx.attacker.spec.moves)
    add_restore_on_switch(ctx.attacker, moves=original_moves)
    ctx.attacker.spec.moves = [
        copy.deepcopy(replacement) if (mv.name or "").strip().lower() == "mimic" else mv
        for mv in ctx.attacker.spec.moves
    ]
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "mimic",
            "description": "Mimic copies the target's move.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sketch")
def _sketch(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    last_entries = ctx.defender.get_temporary_effects("last_move")
    last_entries.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
    if not last_entries:
        return
    move_name = str(last_entries[0].get("name") or "")
    if not move_name:
        return
    replacement = ctx.battle._find_known_move(ctx.defender, move_name)
    if replacement is None:
        return
    ctx.attacker.spec.moves = [
        copy.deepcopy(replacement) if (mv.name or "").strip().lower() == "sketch" else mv
        for mv in ctx.attacker.spec.moves
    ]
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sketch",
            "description": "Sketch permanently learns the target's move.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("mirror move")
def _mirror_move(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    last_entries = ctx.defender.get_temporary_effects("last_move")
    last_entries.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
    if not last_entries:
        return
    move_name = str(last_entries[0].get("name") or "")
    if not move_name:
        return
    replacement = ctx.battle._find_known_move(ctx.defender, move_name)
    if replacement is None:
        return
    ctx.battle.resolve_move_targets(
        attacker_id=ctx.attacker_id,
        move=copy.deepcopy(replacement),
        target_id=ctx.defender_id,
        target_position=ctx.defender.position if ctx.defender else None,
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "mirror_move",
            "description": "Mirror Move repeats the target's last move.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("transform")
def _transform(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    add_restore_on_switch(
        ctx.attacker,
        types=list(ctx.attacker.spec.types),
        moves=list(ctx.attacker.spec.moves),
        abilities=list(ctx.attacker.spec.abilities),
    )
    ctx.attacker.spec.types = list(ctx.defender.spec.types)
    ctx.attacker.spec.moves = [copy.deepcopy(mv) for mv in ctx.defender.spec.moves]
    ctx.attacker.spec.abilities = list(ctx.defender.spec.abilities)
    ctx.attacker.add_temporary_effect("transformed", source_id=ctx.defender_id)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "transform",
            "description": "Transform copies the target's moves and abilities.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("camouflage")
def _camouflage(ctx: MoveSpecialContext) -> None:
    terrain = ctx.battle.terrain if isinstance(ctx.battle.terrain, dict) else {}
    terrain_name = (terrain.get("name") or "").strip().lower()
    weather = (ctx.battle.weather or "").strip().lower()
    mapping = {
        "beach": ["Ground", "Water"],
        "cave": ["Rock", "Dark"],
        "desert": ["Ground", "Rock"],
        "forest": ["Grass"],
        "fresh water": ["Water"],
        "ocean": ["Water"],
        "grassland": ["Normal", "Grass"],
        "marsh": ["Water", "Poison"],
        "mountain": ["Rock", "Ground"],
        "rainforest": ["Grass", "Poison"],
        "taiga": ["Ice", "Grass"],
        "tundra": ["Ice"],
        "urban": ["Normal", "Steel"],
        "sunny": ["Fire"],
        "rainy": ["Water"],
        "hailing": ["Ice"],
        "sandstorming": ["Rock"],
    }
    choices = mapping.get(terrain_name, mapping.get(weather, ["Normal"]))
    chosen = choices[0] if choices else "Normal"
    add_restore_on_switch(ctx.attacker, types=list(ctx.attacker.spec.types))
    ctx.attacker.spec.types = [chosen]
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "camouflage",
            "description": f"Camouflage changes the user's type to {chosen}.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("hail")
def _hail(ctx: MoveSpecialContext) -> None:
    set_weather(ctx.battle, "Hail")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "hail",
            "description": "Hail starts.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("gravity")
def _gravity(ctx: MoveSpecialContext) -> None:
    set_terrain(ctx.battle, "Gravity", rounds=5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "gravity",
            "description": "Gravity warps the battlefield.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("grassy glide")
def _grassy_glide(ctx: MoveSpecialContext) -> None:
    set_terrain(ctx.battle, "Grassy Terrain", rounds=5)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "grassy_terrain",
            "description": "Grassy Glide leaves Grassy Terrain.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("heal block")
def _heal_block(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    ctx.defender.statuses.append({"name": "Heal Blocked", "remaining": 999})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "heal_blocked",
            "description": "Heal Block prevents healing.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("ingrain")
def _ingrain(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker:
        return
    if not ctx.attacker.has_status("Ingrain"):
        ctx.attacker.statuses.append({"name": "Ingrain"})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "ingrain",
            "description": "Ingrain roots the user in place.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special(
    "belch",
    "dragon rage",
    "earthquake",
    "flying press",
    "flying press [sm]",
    "gust",
    "hidden power",
    "natural gift",
    "psystrike",
    "secret sword",
    "snipe shot",
    "solar beam",
    "solar blade",
    "sonic boom",
    "dig",
    "dive",
    "fly",
    "phantom force",
    "shadow force",
    "sky drop",
    "last resort",
)
def _core_handled_moves(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "core_handled",
            "description": "This move is resolved by core rules.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("magnitude", phase="end_action")
def _magnitude_log(ctx: MoveSpecialContext) -> None:
    roll = None
    for entry in list(ctx.attacker.get_temporary_effects("magnitude_roll")):
        if entry.get("round") == ctx.battle.round:
            roll = entry.get("roll")
        if entry in ctx.attacker.temporary_effects:
            ctx.attacker.temporary_effects.remove(entry)
    if roll is None:
        return
    try:
        effective_db = 5 + int(roll)
    except (TypeError, ValueError):
        effective_db = None
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "magnitude",
            "roll": roll,
            "effective_db": effective_db,
            "description": "Magnitude's power varies by roll.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("bitter malice")
def _bitter_malice(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or not ctx.defender:
        return
    roll = ctx.result.get("roll")
    if roll is None:
        return
    ctx.battle._apply_status_on_roll(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        target=ctx.defender,
        status="Stuck",
        effect="trap",
        description="Bitter Malice traps the target.",
        roll=int(roll),
        threshold=19,
        remaining=1,
    )
    ctx.battle._apply_status_on_roll(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id or "",
        move=ctx.move,
        target=ctx.defender,
        status="Trapped",
        effect="trap",
        description="Bitter Malice traps the target.",
        roll=int(roll),
        threshold=19,
        remaining=1,
    )


@register_move_special("doom desire")
def _doom_desire_log(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "delayed_hit",
            "description": "Doom Desire will strike next round.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("future sight")
def _future_sight_log(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "delayed_hit",
            "description": "Future Sight will strike next round.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("focus energy")
def _focus_energy(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("crit_range_bonus", bonus=2, source="focus_energy")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "focus_energy",
            "description": "Focus Energy heightens the user's critical range.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("core enforcer")
def _core_enforcer(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    disable_ability(ctx.defender, ctx.defender.primary_ability())
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "ability_disabled",
            "description": "Core Enforcer disables the target's ability.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("embargo")
def _embargo(ctx: MoveSpecialContext) -> None:
    if not ctx.defender:
        return
    disable_items(ctx.defender)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "items_disabled",
            "description": "Embargo disables held items.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("disable")
def _disable(ctx: MoveSpecialContext) -> None:
    if not ctx.defender or not ctx.hit:
        return
    last_entries = ctx.defender.get_temporary_effects("last_move")
    last_entries.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
    move_name = str(last_entries[0].get("name")) if last_entries else ctx.move.name
    disable_move(ctx.defender, move_name, remaining=3)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "disabled",
            "disabled_move": move_name,
            "description": "Disable seals the target's last move.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("eerie spell")
def _eerie_spell(ctx: MoveSpecialContext) -> None:
    if not ctx.defender or not ctx.hit:
        return
    last_entries = ctx.defender.get_temporary_effects("last_move")
    last_entries.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
    move_name = str(last_entries[0].get("name")) if last_entries else ctx.move.name
    disable_move(ctx.defender, move_name, remaining=3)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "eerie_spell",
            "disabled_move": move_name,
            "description": "Eerie Spell disables the target's last move.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("perish song")
def _perish_song(ctx: MoveSpecialContext) -> None:
    for pid, mon in ctx.battle.pokemon.items():
        if not mon.active or mon.fainted:
            continue
        mon.add_temporary_effect("perish_song", count=3)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "perish_song",
            "description": "Perish Song counts down for all active combatants.",
            "target_hp": ctx.attacker.hp,
        }
    )

@register_move_special("destiny bond")
def _destiny_bond(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("destiny_bond", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "destiny_bond",
            "description": "Destiny Bond will faint the attacker if the user faints.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("encore")
def _encore(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = ctx.battle.rng.randint(1, 6)
    if roll <= 2:
        status = "Confused"
        effect = "confused"
        desc = "Encore confuses the target."
    elif roll <= 4:
        status = "Suppressed"
        effect = "suppressed"
        desc = "Encore suppresses the target."
    else:
        status = "Enraged"
        effect = "enraged"
        desc = "Encore enrages the target."
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status=status,
        effect=effect,
        description=desc,
        roll=roll,
        remaining=1 if status in {"Enraged", "Confused"} else None,
    )


@register_move_special("grassy terrain")
def _grassy_terrain(ctx: MoveSpecialContext) -> None:
    ctx.battle.terrain = {"name": "Grassy Terrain", "remaining": 5}
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "terrain",
            "terrain": ctx.battle.terrain,
            "description": "Grassy Terrain spreads across the field.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("guard swap")
def _guard_swap(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    for stat in ("def", "spdef"):
        ctx.attacker.combat_stages[stat], ctx.defender.combat_stages[stat] = (
            ctx.defender.combat_stages.get(stat, 0),
            ctx.attacker.combat_stages.get(stat, 0),
        )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "guard_swap",
            "description": "Guard Swap exchanges Defense and Special Defense stages.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("heart swap")
def _heart_swap(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    for stat in ("atk", "def", "spatk", "spdef", "spd", "accuracy", "evasion"):
        ctx.attacker.combat_stages[stat], ctx.defender.combat_stages[stat] = (
            ctx.defender.combat_stages.get(stat, 0),
            ctx.attacker.combat_stages.get(stat, 0),
        )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "heart_swap",
            "description": "Heart Swap exchanges combat stages.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("speed swap")
def _speed_swap(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.attacker.combat_stages["spd"], ctx.defender.combat_stages["spd"] = (
        ctx.defender.combat_stages.get("spd", 0),
        ctx.attacker.combat_stages.get("spd", 0),
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "speed_swap",
            "description": "Speed Swap exchanges Speed stages.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("haze")
def _haze(ctx: MoveSpecialContext) -> None:
    for mon in ctx.battle.pokemon.values():
        for stat in mon.combat_stages:
            mon.combat_stages[stat] = 0
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "haze",
            "description": "Haze resets all combat stages.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("magic room")
def _magic_room(ctx: MoveSpecialContext) -> None:
    ctx.battle.room_effects.append({"name": "Magic Room", "remaining": 5, "starts_round": ctx.battle.round})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "magic_room",
            "description": "Magic Room disables held items for a time.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("mirror shot")
def _mirror_shot(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-2,
        effect="mirror_shot",
        description="Mirror Shot lowers Accuracy.",
        roll=roll,
    )


@register_move_special("teatime")
def _teatime(ctx: MoveSpecialContext) -> None:
    for pid, mon in ctx.battle.pokemon.items():
        ctx.battle._consume_food_buff(pid, mon, 0, "teatime", "Teatime triggers a food buff.", ctx.events)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "teatime",
            "description": "Teatime allows everyone to consume a food buff.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("bind", "clamp")
def _bind_bonus(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("wrap_grapple_bonus", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "grapple_bonus",
            "description": "Bind grants a grapple bonus and deals damage on dominance.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("blind")
def _blind(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if any(
        entry.get("target") == ctx.defender_id and entry.get("trick") == "blind"
        for entry in ctx.attacker.get_temporary_effects("dirty_trick_used")
    ):
        return
    contest = ctx.battle._skill_contest(
        ctx.attacker,
        ctx.defender,
        ["stealth"],
        ["stealth", "focus"],
        attacker_bonus=_dirty_trick_bonus(ctx.attacker),
        attacker_id=ctx.attacker_id,
        defender_id=ctx.defender_id,
    )
    _dirty_trick_apply_use(ctx, "blind", succeeded=bool(contest["attacker_wins"]))
    if not contest["attacker_wins"]:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Blinded",
        effect="blind",
        description="Blind leaves the target Blinded.",
        remaining=1,
    )


@register_move_special("bon mot")
def _bon_mot(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    contest = ctx.battle._skill_contest(
        ctx.attacker,
        ctx.defender,
        ["guile"],
        ["guile", "focus"],
        attacker_id=ctx.attacker_id,
        defender_id=ctx.defender_id,
    )
    if not contest["attacker_wins"]:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Enraged",
        effect="bon_mot",
        description="Bon Mot enrages the target.",
        remaining=1,
    )


@register_move_special("calm mind")
def _calm_mind(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=1,
        description="Calm Mind raises Special Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spdef",
        delta=1,
        description="Calm Mind raises Special Defense.",
    )


@register_move_special("charge beam")
def _charge_beam(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 7:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=1,
        description="Charge Beam raises Special Attack.",
        roll=roll,
    )


@register_move_special("coil")
def _coil(ctx: MoveSpecialContext) -> None:
    for stat in ("atk", "def", "accuracy"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            description="Coil raises stats.",
        )


@register_move_special("conversion2")
def _conversion2(ctx: MoveSpecialContext) -> None:
    attacker = ctx.attacker
    battle = ctx.battle
    candidates = []
    if hasattr(battle, "_conversion2_type_options"):
        candidates = list(battle._conversion2_type_options(ctx.attacker_id))
    if not candidates:
        return
    chosen = str(ctx.move_params.get("chosen_type") or "").strip().title()
    if chosen not in candidates:
        chosen = str(candidates[0])
    attacker.spec.types = [chosen]
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "conversion2",
            "new_type": attacker.spec.types,
            "description": "Conversion2 changes the user's type.",
            "target_hp": attacker.hp,
        }
    )


@register_move_special("cosmic power")
def _cosmic_power(ctx: MoveSpecialContext) -> None:
    for stat in ("def", "spdef"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            description="Cosmic Power raises defenses.",
        )


@register_move_special("cotton guard")
def _cotton_guard(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=3,
        description="Cotton Guard sharply raises Defense.",
    )


@register_move_special("disengage")
def _disengage(ctx: MoveSpecialContext) -> None:
    battle = ctx.battle
    if battle.grid is None or ctx.attacker.position is None:
        return
    reachable = movement.legal_shift_tiles(battle, ctx.attacker_id)
    if not reachable:
        return
    origin = ctx.attacker.position
    max_distance = 2 if has_ability_exact(ctx.attacker, "Celebrate [Errata]") else 1
    reachable = [
        coord
        for coord in reachable
        if 0 < targeting.chebyshev_distance(origin, coord) <= max_distance
    ]
    if not reachable:
        return
    reachable.sort(key=lambda coord: (targeting.chebyshev_distance(origin, coord), coord))
    destination = reachable[0]
    ctx.attacker.position = destination
    ctx.events.append(
        {
            "type": "shift",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "disengage",
            "from": origin,
            "to": destination,
            "description": "Disengage shifts without provoking.",
        }
    )


@register_move_special("earth power")
def _earth_power(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        description="Earth Power lowers Special Defense.",
        roll=roll,
    )


@register_move_special("fiery dance")
def _fiery_dance(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll % 2 != 0:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=1,
        description="Fiery Dance raises Special Attack.",
        roll=roll,
    )


@register_move_special("hinder")
def _hinder(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if any(
        entry.get("target") == ctx.defender_id and entry.get("trick") == "hinder"
        for entry in ctx.attacker.get_temporary_effects("dirty_trick_used")
    ):
        return
    contest = ctx.battle._skill_contest(
        ctx.attacker,
        ctx.defender,
        ["athletics"],
        ["athletics"],
        attacker_bonus=_dirty_trick_bonus(ctx.attacker),
        attacker_id=ctx.attacker_id,
        defender_id=ctx.defender_id,
    )
    _dirty_trick_apply_use(ctx, "hinder", succeeded=bool(contest["attacker_wins"]))
    if not contest["attacker_wins"]:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="hinder",
        description="Hinder slows the target.",
        remaining=1,
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Hindered",
        effect="hinder",
        description="Hinder leaves the target Hindered.",
        remaining=1,
    )


@register_move_special("laser focus")
def _laser_focus(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("laser_focus")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "laser_focus",
            "description": "Laser Focus readies an automatic critical hit.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("leaf tornado")
def _leaf_tornado(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        description="Leaf Tornado lowers Accuracy.",
        roll=roll,
    )


@register_move_special("branch poke")
def _branch_poke_speed_drop(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="defender", stat="spd", delta=-2, effect="branch_poke")


@register_move_special("leafage")
def _leafage_sleep(ctx: MoveSpecialContext) -> None:
    _apply_simple_status(ctx, status="Sleep", effect="sleep")


@register_move_special("low blow")
def _low_blow(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if any(
        entry.get("target") == ctx.defender_id and entry.get("trick") == "low_blow"
        for entry in ctx.attacker.get_temporary_effects("dirty_trick_used")
    ):
        return
    contest = ctx.battle._skill_contest(
        ctx.attacker,
        ctx.defender,
        ["acrobatics"],
        ["acrobatics"],
        attacker_bonus=_dirty_trick_bonus(ctx.attacker),
        attacker_id=ctx.attacker_id,
        defender_id=ctx.defender_id,
    )
    _dirty_trick_apply_use(ctx, "low_blow", succeeded=bool(contest["attacker_wins"]))
    if not contest["attacker_wins"]:
        return
    ctx.battle._set_initiative_zero_until_next_turn(
        ctx.defender_id,
        source="Low Blow",
        source_id=ctx.attacker_id,
        trainer_id=ctx.attacker.controller_id,
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Vulnerable",
        effect="low_blow",
        description="Low Blow leaves the target vulnerable.",
        remaining=1,
    )


@register_move_special("maul")
def _maul(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinched",
        effect="maul",
        description="Maul flinches the target.",
        remaining=1,
    )


@register_move_special("meditate")
def _meditate(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        description="Meditate raises Attack.",
    )


@register_move_special("mind reader")
def _mind_reader(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.attacker.add_temporary_effect(
        "mind_reader", target_id=ctx.defender_id, expires_round=ctx.battle.round + 1
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "mind_reader",
            "description": "Mind Reader fixes the next attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("minimize")
def _minimize(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("evasion_bonus", amount=4, expires_round=ctx.battle.round + 99)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "minimize",
            "description": "Minimize raises evasion.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("nasty plot")
def _nasty_plot(ctx: MoveSpecialContext) -> None:
    _apply_stage_delta(ctx, target="attacker", stat="spatk", delta=2, effect="nasty_plot")


@register_move_special("needle arm")
def _needle_arm(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinched",
        effect="needle_arm",
        description="Needle Arm flinches the target.",
        roll=roll,
        remaining=1,
    )


@register_move_special("mountain gale")
def _mountain_gale(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinched",
        effect="mountain_gale",
        description="Mountain Gale flinches the target.",
        roll=roll,
        remaining=1,
    )

@register_move_special("mud bomb")
def _mud_bomb(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        description="Mud Bomb lowers Accuracy.",
        roll=roll,
    )


@register_move_special("mystical fire")
def _mystical_fire(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=-1,
        description="Mystical Fire lowers Special Attack.",
    )


@register_move_special("night daze")
def _night_daze(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 13:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        description="Night Daze lowers Accuracy.",
        roll=roll,
    )


@register_move_special("seed flare")
def _seed_flare(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-1,
        description="Seed Flare lowers Special Defense.",
    )


@register_move_special("sheer cold", phase="pre_damage")
def _sheer_cold(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    roll = ctx.battle.rng.randint(1, 100)
    threshold = max(1, 30 + int(ctx.attacker.spec.level) - int(ctx.defender.spec.level))
    if roll > threshold:
        ctx.result["hit"] = False
        ctx.result["damage"] = 0
        return
    ctx.result["hit"] = True
    ctx.result["damage"] = ctx.defender.hp or 0
    ctx.result["type_multiplier"] = 1.0
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "sheer_cold",
            "roll": roll,
            "threshold": threshold,
            "description": "Sheer Cold executes the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("smack down")
def _smack_down(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("force_grounded", expires_round=ctx.battle.round + 3)
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Grounded",
        effect="smack_down",
        description="Smack Down forces the target to the ground.",
        remaining=3,
    )


@register_move_special("smelling salts")
def _smelling_salts(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.defender.has_status("Paralyzed"):
        ctx.defender.remove_status_by_names({"paralyzed", "paralysis"})
        ctx.events.append(
            {
                "type": "status",
                "actor": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "smelling_salts_cure",
                "status": "Paralyzed",
                "description": "Smelling Salts cures paralysis.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("smokescreen")
def _smokescreen(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("evasion_bonus", amount=3, expires_round=ctx.battle.round + 3)
    if ctx.attacker.has_ability("Sticky Smoke"):
        ctx.defender.add_temporary_effect(
            "sticky_smoke",
            expires_round=ctx.battle.round + 3,
            source_id=ctx.attacker_id,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Sticky Smoke",
                "move": ctx.move.name,
                "effect": "sticky_smoke",
                "description": "Sticky Smoke leaves lingering accuracy penalties.",
                "target_hp": ctx.defender.hp,
            }
        )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "smokescreen",
            "description": "Smokescreen obscures the area.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("sparkling aria")
def _sparkling_aria(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    cured = ctx.defender.remove_status_by_names(
        {"burned", "burn", "confused", "infatuated", "rage", "provocation"}
    )
    if cured:
        ctx.events.append(
            {
                "type": "status",
                "actor": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "sparkling_aria",
                "description": "Sparkling Aria cleanses the target.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("spectral thief", phase="pre_damage")
def _spectral_thief(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    for stat, value in ctx.defender.combat_stages.items():
        if value == 0:
            continue
        ctx.attacker.combat_stages[stat] += value
        ctx.defender.combat_stages[stat] = 0
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "spectral_thief",
            "description": "Spectral Thief steals combat stages.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("hidden power flying")
def _hidden_power_flying(ctx: MoveSpecialContext) -> None:
    return


@register_move_special("hurricane")
def _hurricane_confusion(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="hurricane",
        description="Hurricane confuses on a high roll.",
        roll=roll,
    )


def _scene_ready(attacker: "PokemonState", battle: "BattleState", key: str) -> bool:
    kind = f"scene_used_{key}".lower()
    if attacker.get_temporary_effects(kind):
        return False
    attacker.add_temporary_effect(kind, round=battle.round)
    return True


def _once_per_move_use(ctx: MoveSpecialContext, key: str) -> bool:
    kind = f"move_once_{key}".lower()
    for entry in ctx.attacker.get_temporary_effects(kind):
        if entry.get("round") == ctx.battle.round and entry.get("move") == ctx.move.name:
            return False
    ctx.attacker.add_temporary_effect(kind, round=ctx.battle.round, move=ctx.move.name)
    return True


def _apply_heal(
    ctx: MoveSpecialContext,
    *,
    target: "PokemonState",
    target_id: str,
    amount: int,
    effect: str,
    description: Optional[str] = None,
) -> None:
    if amount <= 0:
        return
    before = target.hp or 0
    target.heal(amount)
    healed = max(0, (target.hp or 0) - before)
    if healed <= 0:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": target_id,
            "move": ctx.move.name,
            "effect": effect,
            "amount": healed,
            "description": description,
            "target_hp": target.hp,
        }
    )


def _apply_self_hp_cost(ctx: MoveSpecialContext, *, fraction: float, effect: str) -> None:
    if not _once_per_move_use(ctx, effect):
        return
    max_hp = ctx.attacker.max_hp()
    if max_hp <= 0:
        return
    loss = int(math.floor(max_hp * fraction))
    if loss <= 0:
        return
    before = ctx.attacker.hp or 0
    ctx.attacker.apply_damage(loss, skip_injury=True)
    dealt = max(0, before - (ctx.attacker.hp or 0))
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": effect,
            "amount": dealt,
            "description": f"{ctx.move.name} costs the user HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("astonish")
def _astonish(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.defender.has_status("Unaware") or ctx.defender.has_status("Surprised"):
        if _scene_ready(ctx.attacker, ctx.battle, "astonish_unaware"):
            ctx.battle._apply_status(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.defender_id,
                move=ctx.move,
                target=ctx.defender,
                status="Flinched",
                effect="astonish_unaware",
                description="Astonish auto-flinches an unaware target.",
                remaining=1,
            )


@register_move_special("barb barrage", phase="pre_damage")
def _barb_barrage_strike(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    if not ctx.defender.statuses:
        return
    if not _scene_ready(ctx.attacker, ctx.battle, "barb_barrage_strike"):
        return
    ctx.result["strike_hits_override"] = 8
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "barb_barrage_strike",
            "description": "Barb Barrage maximizes its strike count.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("barb barrage")
def _barb_barrage_poison(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Poisoned",
        effect="barb_barrage",
        description="Barb Barrage poisons on a high roll.",
        roll=roll,
    )


@register_move_special("beat up")
def _beat_up(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    struggle = _lookup_move_spec("Struggle")
    if struggle is None:
        return
    struggle = copy.deepcopy(struggle)
    struggle.type = "Dark"
    participants = [ctx.attacker_id]
    if ctx.attacker.position is not None and ctx.defender.position is not None:
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id or pid == ctx.defender_id:
                continue
            if mon.fainted or not mon.active:
                continue
            if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
                continue
            if mon.position is None:
                continue
            if targeting.chebyshev_distance(mon.position, ctx.defender.position) == 1:
                participants.append(pid)
            if len(participants) >= 3:
                break
    for pid in participants:
        try:
            ctx.battle.resolve_move_targets(
                attacker_id=pid,
                move=struggle,
                target_id=ctx.defender_id,
                target_position=ctx.defender.position,
            )
        except Exception:
            continue


@register_move_special("bleed!")
def _bleed(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Bleed",
        effect="bleed",
        description="Bleed causes the target to lose HP each turn.",
        remaining=3,
    )


@register_move_special("burning jealousy")
def _burning_jealousy(ctx: MoveSpecialContext) -> None:
    if not _scene_ready(ctx.attacker, ctx.battle, "burning_jealousy"):
        return
    if ctx.attacker.position is None:
        return
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or not mon.active or mon.position is None:
            continue
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 5:
            continue
        if not mon.get_temporary_effects("cs_raised"):
            continue
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=pid,
            move=ctx.move,
            target=mon,
            status="Burned",
            effect="burning_jealousy",
            description="Burning Jealousy burns foes that raised stats.",
        )


@register_move_special("chloroblast")
def _chloroblast(ctx: MoveSpecialContext) -> None:
    _apply_self_hp_cost(ctx, fraction=0.5, effect="chloroblast")


@register_move_special("clangorous soul")
def _clangorous_soul(ctx: MoveSpecialContext) -> None:
    _apply_self_hp_cost(ctx, fraction=1 / 3, effect="clangorous_soul")
    for stat in ("atk", "def", "spatk", "spdef", "spd", "accuracy", "evasion"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=1,
            effect="clangorous_soul",
            description="Clangorous Soul raises all stats.",
        )


@register_move_special("clear smog", phase="pre_damage")
def _clear_smog_cannot_miss(ctx: MoveSpecialContext) -> None:
    ctx.result["hit"] = True


@register_move_special("clear smog")
def _clear_smog(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    for stat in ctx.defender.combat_stages:
        ctx.defender.combat_stages[stat] = 0
    removed = []
    coat_names = {
        "aqua ring",
        "reflect",
        "light screen",
        "safeguard",
        "mist",
        "lucky chant",
        "aurora veil",
        "mud sport",
        "water sport",
    }
    for entry in list(ctx.defender.statuses):
        name = ctx.defender._normalized_status_name(entry)
        if name in coat_names:
            ctx.defender.statuses.remove(entry)
            removed.append(name)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "clear_smog",
            "removed": removed,
            "description": "Clear Smog resets combat stages and clears coats.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("corrosive gas")
def _corrosive_gas(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    disable_items(ctx.defender)
    types = {str(t).strip().lower() for t in (ctx.defender.spec.types or [])}
    if "steel" in types:
        ctx.defender.add_temporary_effect("poison_immunity_suppressed")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "corrosive_gas",
            "description": "Corrosive Gas disables items and corrodes Steel.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("counter")
def _counter(ctx: MoveSpecialContext) -> None:
    battle = ctx.battle
    damage_taken = int(battle.damage_received_this_round.get(ctx.attacker_id, 0) or 0)
    if damage_taken <= 0:
        return
    candidates: List[str] = []
    for attacker_id in battle.damage_taken_from.get(ctx.attacker_id, set()):
        attacker = battle.pokemon.get(attacker_id)
        if attacker is None or attacker.fainted:
            continue
        last_moves = attacker.get_temporary_effects("last_move")
        last_moves.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
        move_name = str(last_moves[0].get("name") or "") if last_moves else ""
        spec = _lookup_move_spec(move_name)
        if spec and (spec.category or "").strip().lower() == "physical":
            candidates.append(attacker_id)
    if not candidates:
        return
    target_id = ctx.defender_id if ctx.defender_id in candidates else candidates[0]
    defender = battle.pokemon.get(target_id) if target_id else None
    if defender is None or defender.fainted:
        return
    if ptu_engine.type_multiplier("Fighting", defender.spec.types) <= 0:
        return
    before = defender.hp or 0
    defender.apply_damage(damage_taken * 2)
    dealt = max(0, before - (defender.hp or 0))
    if dealt > 0:
        battle.damage_received_this_round[target_id] = (
            battle.damage_received_this_round.get(target_id, 0) + dealt
        )
        battle._record_damage_exchange(ctx.attacker_id, target_id)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": target_id,
            "move": ctx.move.name,
            "effect": "counter",
            "damage": dealt,
            "description": "Counter reflects physical damage.",
            "target_hp": defender.hp,
        }
    )


@register_move_special("crafty shield")
def _crafty_shield(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Crafty Shield"):
        ctx.attacker.statuses.append({"name": "Crafty Shield"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "crafty_shield",
            "status": "Crafty Shield",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("curse")
def _curse(ctx: MoveSpecialContext) -> None:
    types = {str(t).strip().lower() for t in (ctx.attacker.spec.types or [])}
    if "ghost" in types:
        if ctx.defender is None or ctx.defender_id is None:
            return
        _apply_self_hp_cost(ctx, fraction=1 / 3, effect="curse")
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Cursed",
            effect="curse",
            description="Curse afflicts the target.",
            remaining=3,
        )
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spd",
        delta=-1,
        effect="curse",
        description="Curse lowers Speed.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="curse",
        description="Curse raises Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=1,
        effect="curse",
        description="Curse raises Defense.",
    )


@register_move_special("dark void", "dark void [sm]")
def _dark_void(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        if _scene_ready(ctx.attacker, ctx.battle, "dark_void_burst"):
            if ctx.attacker.position is None:
                return
            team = ctx.battle._team_for(ctx.attacker_id)
            for pid, mon in ctx.battle.pokemon.items():
                if mon.fainted or not mon.active or mon.position is None:
                    continue
                if ctx.battle._team_for(pid) == team:
                    continue
                if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 5:
                    continue
                ctx.battle._apply_status(
                    ctx.events,
                    attacker_id=ctx.attacker_id,
                    target_id=pid,
                    move=ctx.move,
                    target=mon,
                    status="Sleep",
                    effect="dark_void_burst",
                    description="Dark Void spreads sleep.",
                )
        return
    if not ctx.hit:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Sleep",
        effect="dark_void",
        description="Dark Void puts the target to sleep.",
    )


@register_move_special("defense curl")
def _defense_curl(ctx: MoveSpecialContext) -> None:
    entry = next(iter(ctx.attacker.get_temporary_effects("quick_curl_ready")), None)
    if entry is not None:
        ctx.attacker.remove_temporary_effect("quick_curl_ready")
        ability_name = str(entry.get("ability") or "Quick Curl")
        description = (
            "Quick Curl readies Defense Curl as an interrupt."
            if "[errata]" in ability_name.lower()
            else "Quick Curl lets Defense Curl be used as a Swift Action."
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": ability_name,
                "move": ctx.move.name,
                "effect": "interrupt" if "[errata]" in ability_name.lower() else "swift",
                "description": description,
                "target_hp": ctx.attacker.hp,
            }
        )
    if not ctx.attacker.has_status("Curled Up"):
        ctx.attacker.statuses.append({"name": "Curled Up"})
    has_rollout = any((mv.name or "").strip().lower() == "rollout" for mv in ctx.attacker.spec.moves)
    has_ice_ball = any((mv.name or "").strip().lower() == "ice ball" for mv in ctx.attacker.spec.moves)
    if not (has_rollout or has_ice_ball):
        if not ctx.attacker.has_status("Slowed"):
            ctx.attacker.statuses.append({"name": "Slowed", "remaining": 999})
    ctx.attacker.add_temporary_effect("damage_reduction", amount=10, consume=False)
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "defense_curl",
            "status": "Curled Up",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("detect")
def _detect(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Detect"):
        ctx.attacker.statuses.append({"name": "Detect"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "detect",
            "status": "Detect",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("dire claw", phase="pre_damage")
def _dire_claw_crit(ctx: MoveSpecialContext) -> None:
    if ctx.result.get("roll") is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll >= 19:
        ctx.result["crit"] = True


@register_move_special("dire claw")
def _dire_claw_status(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = _effect_roll(ctx)
    if roll < 15:
        return
    status_roll = ctx.battle.rng.randint(1, 3)
    status_map = {1: ("Poisoned", "poison"), 2: ("Paralyzed", "paralysis"), 3: ("Flinched", "flinch")}
    status, effect = status_map.get(status_roll, ("Poisoned", "poison"))
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status=status,
        effect="dire_claw",
        description="Dire Claw inflicts a random ailment.",
        remaining=1 if status == "Flinched" else None,
    )


@register_move_special("dirty trick")
def _dirty_trick(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    for trick in ("hinder", "blind", "low_blow"):
        if any(
            entry.get("target") == ctx.defender_id and entry.get("trick") == trick
            for entry in ctx.attacker.get_temporary_effects("dirty_trick_used")
        ):
            continue
        dirty_trick_move = copy.copy(ctx.move)
        dirty_trick_move.name = trick.replace("_", " ").title()
        dirty_ctx = MoveSpecialContext(
            battle=ctx.battle,
            attacker_id=ctx.attacker_id,
            attacker=ctx.attacker,
            defender_id=ctx.defender_id,
            defender=ctx.defender,
            move=dirty_trick_move,
            result=ctx.result,
            damage_dealt=ctx.damage_dealt,
            events=ctx.events,
            move_name=trick,
            hit=ctx.hit,
            phase=ctx.phase,
            action_type=ctx.action_type,
        )
        if trick == "hinder":
            _hinder(dirty_ctx)
        elif trick == "blind":
            _blind(dirty_ctx)
        else:
            _low_blow(dirty_ctx)
        break


@register_move_special("electrify")
def _electrify(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("electrify", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "electrify",
            "description": "Electrify changes the target's next attacks to Electric.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("endeavor")
def _endeavor(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    injuries = max(0, int(ctx.attacker.injuries or 0))
    if injuries <= 0:
        return
    damage = ctx.defender._apply_tick_damage(injuries)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "endeavor",
            "amount": damage,
            "description": "Endeavor deals damage based on injuries.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("endure")
def _endure(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Endure"):
        ctx.attacker.statuses.append({"name": "Endure"})
    if _fearsome_display_active(ctx.attacker):
        gained = ctx.attacker.add_temp_hp(ctx.attacker.tick_value() * 2)
        ctx.events.append(
            {
                "type": "trainer_feature",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "trainer": ctx.attacker.controller_id,
                "feature": "Fearsome Display",
                "move": ctx.move.name,
                "effect": "temp_hp",
                "amount": gained,
                "description": "Fearsome Display grants two ticks of temporary hit points after Endure.",
                "target_hp": ctx.attacker.hp,
            }
        )
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "endure",
            "status": "Endure",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("headbutt")
def _headbutt_fearsome_display(ctx: MoveSpecialContext) -> None:
    if not _fearsome_display_active(ctx.attacker):
        return
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._set_initiative_zero_until_next_turn(
        ctx.defender_id,
        source="Fearsome Display",
        source_id=ctx.attacker_id,
        trainer_id=ctx.attacker.controller_id,
    )
    ctx.events.append(
        {
            "type": "trainer_feature",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "trainer": ctx.attacker.controller_id,
            "feature": "Fearsome Display",
            "move": ctx.move.name,
            "effect": "initiative_zero",
            "description": "Fearsome Display lowers the target's Initiative to 0 until their next turn.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("energy vortex", "fire spin", "infestation", "magma storm", "ceaseless edge")
def _vortex_moves(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.move_name != "magma storm" and not ctx.hit:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Vortex",
        effect=ctx.move_name.replace(" ", "_"),
        description="The target is trapped in a vortex.",
        remaining=3,
    )


@register_move_special("feint")
def _feint(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    removed = ctx.defender.remove_status_by_names(
        {"protect", "detect", "obstruct", "king's shield", "spiky shield", "baneful bunker", "crafty shield", "mat block"}
    )
    if removed:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "feint",
                "description": "Feint breaks protective moves.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("freeze shock")
def _freeze_shock(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Paralyzed",
        effect="freeze_shock",
        description="Freeze Shock paralyzes on a high roll.",
        roll=roll,
    )


@register_move_special("gouge")
def _gouge(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    strike_hits = int(ctx.result.get("strike_hits") or 0)
    if strike_hits < 2:
        return
    ctx.defender.injuries = max(0, int(ctx.defender.injuries or 0)) + 1
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "gouge",
            "injuries": ctx.defender.injuries,
            "description": "Gouge inflicts an injury on a double hit.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("guard split")
def _guard_split(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_stat_modifier(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=-5,
        effect="guard_split",
        description="Guard Split lowers Defense.",
    )
    ctx.battle._apply_stat_modifier(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spdef",
        delta=-5,
        effect="guard_split",
        description="Guard Split lowers Special Defense.",
    )
    ctx.attacker.add_temporary_effect("damage_reduction", amount=5, consume=False)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "guard_split",
            "description": "Guard Split grants damage reduction.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("guillotine")
def _guillotine(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = ctx.battle.rng.randint(1, 100)
    level_delta = int(ctx.attacker.spec.level) - int(ctx.defender.spec.level)
    threshold = max(1, min(100, 30 + level_delta))
    if roll > threshold:
        return
    defender_hp = ctx.defender.hp or 0
    if defender_hp > 0:
        ctx.defender.apply_damage(defender_hp)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "guillotine",
            "roll": roll,
            "threshold": threshold,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("headlong rush")
def _headlong_rush(ctx: MoveSpecialContext) -> None:
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=-1,
        effect="headlong_rush",
        description="Headlong Rush lowers Defense.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spdef",
        delta=-1,
        effect="headlong_rush",
        description="Headlong Rush lowers Special Defense.",
    )


@register_move_special("heal order")
def _heal_order(ctx: MoveSpecialContext) -> None:
    max_hp = ctx.attacker.max_hp()
    _apply_heal(ctx, target=ctx.attacker, target_id=ctx.attacker_id, amount=max_hp // 2, effect="heal_order")


@register_move_special("heal pulse")
def _heal_pulse(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.defender_id == ctx.attacker_id:
        return
    _apply_heal(
        ctx,
        target=ctx.defender,
        target_id=ctx.defender_id,
        amount=ctx.defender.max_hp() // 2,
        effect="heal_pulse",
    )


@register_move_special("hold hands")
def _hold_hands(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    for pid, mon in ((ctx.attacker_id, ctx.attacker), (ctx.defender_id, ctx.defender)):
        if not mon.has_status("Cheered"):
            mon.statuses.append({"name": "Cheered"})
        mon.add_temporary_effect("cheered", charges=1)
        ctx.events.append(
            {
                "type": "status",
                "actor": pid,
                "target": pid,
                "move": ctx.move.name,
                "effect": "cheered",
                "status": "Cheered",
                "target_hp": mon.hp,
            }
        )


@register_move_special("horn drill")
def _horn_drill(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = ctx.battle.rng.randint(1, 100)
    level_delta = int(ctx.attacker.spec.level) - int(ctx.defender.spec.level)
    threshold = max(1, min(100, 30 + level_delta))
    if roll > threshold:
        return
    defender_hp = ctx.defender.hp or 0
    if defender_hp > 0:
        ctx.defender.apply_damage(defender_hp)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "horn_drill",
            "roll": roll,
            "threshold": threshold,
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("ice burn")
def _ice_burn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 15:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect="ice_burn",
        description="Ice Burn burns on a high roll.",
        roll=roll,
    )


@register_move_special("instruct")
def _instruct(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.defender.get_temporary_effects("exhaust_next_turn"):
        return
    last_moves = ctx.defender.get_temporary_effects("last_move")
    last_moves.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
    move_name = str(last_moves[0].get("name") or "") if last_moves else ""
    if not move_name:
        return
    move = _lookup_move_spec(move_name)
    if move is None or move_has_keyword(move, "interrupt") or move_has_keyword(move, "trigger"):
        return
    if is_setup_move(move):
        return
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.defender_id,
            move=move,
            target_id=last_moves[0].get("target_id") if last_moves else None,
            target_position=None,
        )
    except Exception:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "instruct",
            "description": "Instruct forces the target to repeat its last move.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("jaw lock")
def _jaw_lock(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._set_grapple_link(ctx.attacker_id, ctx.defender_id, ctx.attacker_id)
    ctx.battle._sync_grapple_status(ctx.attacker_id)
    ctx.battle._sync_grapple_status(ctx.defender_id)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "jaw_lock",
            "description": "Jaw Lock grapples the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("jungle healing")
def _jungle_healing(ctx: MoveSpecialContext) -> None:
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if mon.fainted or not mon.active:
            continue
        _apply_heal(
            ctx,
            target=mon,
            target_id=pid,
            amount=mon.max_hp() // 4,
            effect="jungle_healing",
        )
        mon.clear_volatile_statuses()
        mon.remove_status_by_names({"burned", "poisoned", "badly poisoned", "paralyzed", "frozen", "sleep", "asleep"})


@register_move_special("kinesis")
def _kinesis(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Kinesis",
        effect="kinesis",
        description="Kinesis readies an accuracy penalty.",
        remaining=1,
    )


@register_move_special("king's shield", "kings shield")
def _kings_shield(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("King's Shield"):
        ctx.attacker.statuses.append({"name": "King's Shield"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "kings_shield",
            "status": "King's Shield",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("life dew")
def _life_dew(ctx: MoveSpecialContext) -> None:
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if mon.fainted or not mon.active:
            continue
        _apply_heal(
            ctx,
            target=mon,
            target_id=pid,
            amount=mon.max_hp() // 4,
            effect="life_dew",
        )


@register_move_special("lucky chant")
def _lucky_chant(ctx: MoveSpecialContext) -> None:
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if ctx.battle._team_for(pid) != team:
            continue
        if mon.fainted or not mon.active:
            continue
        if not mon.has_status("Lucky Chant"):
            mon.statuses.append({"name": "Lucky Chant", "charges": 3})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "lucky_chant",
            "status": "Lucky Chant",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("lunar blessing")
def _lunar_blessing(ctx: MoveSpecialContext) -> None:
    max_hp = ctx.attacker.max_hp()
    _apply_heal(ctx, target=ctx.attacker, target_id=ctx.attacker_id, amount=max_hp // 2, effect="lunar_blessing")
    ctx.attacker.clear_volatile_statuses()
    ctx.attacker.remove_status_by_names({"burned", "poisoned", "badly poisoned", "paralyzed", "frozen", "sleep", "asleep"})
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="evasion",
        delta=2,
        effect="lunar_blessing",
        description="Lunar Blessing raises evasion.",
    )


@register_move_special("magic coat")
def _magic_coat(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Magic Coat"):
        ctx.attacker.statuses.append({"name": "Magic Coat"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "magic_coat",
            "status": "Magic Coat",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("magnetic flux [ss]")
def _magnetic_flux(ctx: MoveSpecialContext) -> None:
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        types = {str(t).strip().lower() for t in (mon.spec.types or [])}
        if "electric" not in types and not mon.has_capability("Magnetic"):
            continue
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=pid,
            move=ctx.move,
            target=mon,
            stat="def",
            delta=1,
            effect="magnetic_flux",
            description="Magnetic Flux raises Defense.",
        )
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=pid,
            move=ctx.move,
            target=mon,
            stat="spdef",
            delta=1,
            effect="magnetic_flux",
            description="Magnetic Flux raises Special Defense.",
        )


@register_move_special("mat block")
def _mat_block(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Mat Block"):
        ctx.attacker.statuses.append({"name": "Mat Block", "round": ctx.battle.round})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "mat_block",
            "status": "Mat Block",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("memento")
def _memento(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    for stat in ("atk", "def", "spatk", "spdef", "spd"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=-2,
            effect="memento",
            description="Memento lowers stats.",
        )
    if ctx.attacker.hp and ctx.attacker.hp > 0:
        ctx.attacker.apply_damage(ctx.attacker.hp, skip_injury=True)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "memento",
            "description": "Memento causes the user to faint.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("milk drink")
def _milk_drink(ctx: MoveSpecialContext) -> None:
    target = ctx.defender if ctx.defender is not None else ctx.attacker
    target_id = ctx.defender_id if ctx.defender_id is not None else ctx.attacker_id
    _apply_heal(ctx, target=target, target_id=target_id, amount=target.max_hp() // 2, effect="milk_drink")


@register_move_special("mind blown")
def _mind_blown(ctx: MoveSpecialContext) -> None:
    _apply_self_hp_cost(ctx, fraction=0.5, effect="mind_blown")


@register_move_special("moongeist beam", phase="pre_damage")
def _moongeist_beam(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("ignore_ability_immunity", round=ctx.battle.round, move=ctx.move.name)


@register_move_special("moongeist beam", phase="end_action")
def _moongeist_beam_cleanup(ctx: MoveSpecialContext) -> None:
    while ctx.attacker.remove_temporary_effect("ignore_ability_immunity"):
        continue


@register_move_special("moonlight")
def _moonlight(ctx: MoveSpecialContext) -> None:
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" in weather:
        fraction = 2 / 3
    elif any(token in weather for token in ("rain", "sand", "hail")):
        fraction = 1 / 4
    else:
        fraction = 1 / 2
    amount = int(math.floor(ctx.attacker.max_hp() * fraction))
    _apply_heal(ctx, target=ctx.attacker, target_id=ctx.attacker_id, amount=amount, effect="moonlight")


@register_move_special("morning sun")
def _morning_sun(ctx: MoveSpecialContext) -> None:
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" in weather:
        fraction = 2 / 3
    elif any(token in weather for token in ("rain", "sand", "hail")):
        fraction = 1 / 4
    else:
        fraction = 1 / 2
    amount = int(math.floor(ctx.attacker.max_hp() * fraction))
    _apply_heal(ctx, target=ctx.attacker, target_id=ctx.attacker_id, amount=amount, effect="morning_sun")


@register_move_special("muddy water")
def _muddy_water(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 16:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="accuracy",
        delta=-1,
        effect="muddy_water",
        description="Muddy Water lowers Accuracy.",
        roll=roll,
    )


@register_move_special("nature's madness")
@register_move_special("nature’s madness")
def _natures_madness(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    current = max(0, int(ctx.defender.hp or 0))
    damage = current // 2
    if damage <= 0:
        return
    ctx.defender.apply_damage(damage)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "natures_madness",
            "amount": damage,
            "description": "Nature's Madness halves the target's current HP.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("magnet rise")
def _magnet_rise(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Magnet Rise"):
        ctx.attacker.statuses.append({"name": "Magnet Rise", "remaining": 5})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "magnet_rise",
            "status": "Magnet Rise",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("manipulate")
def _manipulate(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    tricks = [
        ("bon_mot", "Enraged"),
        ("flirt", "Infatuated"),
        ("terrorize", "Fear"),
    ]
    for effect, status in tricks:
        key = f"manipulate_{effect}"
        if ctx.defender.get_temporary_effects(key):
            continue
        ctx.defender.add_temporary_effect(key, round=ctx.battle.round, source=ctx.attacker_id)
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status=status,
            effect=effect,
            description=f"Manipulate inflicts {status}.",
            remaining=1,
        )
        break


@register_move_special("me first")
def _me_first(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.spec.spd <= ctx.defender.spec.spd:
        return
    last_moves = ctx.defender.get_temporary_effects("last_move")
    last_moves.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
    move_name = str(last_moves[0].get("name") or "") if last_moves else ""
    if not move_name:
        return
    move = _lookup_move_spec(move_name)
    if move is None or (move.category or "").strip().lower() == "status":
        return
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.attacker_id,
            move=move,
            target_id=ctx.defender_id,
            target_position=ctx.defender.position,
        )
    except Exception:
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "me_first",
            "description": "Me First copies the target's last attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("snatch")
def _snatch(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Snatch"):
        ctx.attacker.statuses.append({"name": "Snatch"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "snatch",
            "status": "Snatch",
            "target_hp": ctx.attacker.hp,
        }
    )

@register_move_special("plasma fists")
def _plasma_fists(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("plasma_fists")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "plasma_fists",
            "description": "Plasma Fists electrifies normal moves.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_move_special("psycho shift", phase="pre_damage")
def _psycho_shift_cannot_miss(ctx: MoveSpecialContext) -> None:
    ctx.result["hit"] = True


@register_move_special("psycho shift")
def _psycho_shift(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    status_names = {"burned", "poisoned", "badly poisoned", "paralyzed", "frozen", "sleep", "asleep"}
    source_status = None
    for entry in list(ctx.attacker.statuses):
        name = ctx.attacker._normalized_status_name(entry)
        if name in status_names:
            source_status = entry
            break
    if source_status is None:
        return
    target_name = ctx.attacker._normalized_status_name(source_status)
    if ctx.defender.has_status(target_name):
        return
    ctx.attacker.statuses.remove(source_status)
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status=target_name.title(),
        effect="psycho_shift",
        description="Psycho Shift transfers a status ailment.",
    )


@register_move_special("sky attack")
def _sky_attack(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 17:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinched",
        effect="sky_attack",
        description="Sky Attack flinches on a high roll.",
        roll=roll,
        remaining=1,
    )


@register_move_special("soft-boiled")
def _soft_boiled(ctx: MoveSpecialContext) -> None:
    target = ctx.defender if ctx.defender is not None else ctx.attacker
    target_id = ctx.defender_id if ctx.defender_id is not None else ctx.attacker_id
    _apply_heal(ctx, target=target, target_id=target_id, amount=target.max_hp() // 2, effect="soft_boiled")


@register_move_special("spiky shield")
def _spiky_shield(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_status("Spiky Shield"):
        ctx.attacker.statuses.append({"name": "Spiky Shield"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "spiky_shield",
            "status": "Spiky Shield",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("steel beam")
def _steel_beam(ctx: MoveSpecialContext) -> None:
    _apply_self_hp_cost(ctx, fraction=0.5, effect="steel_beam")


@register_move_special("strength")
def _strength(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    contest = ctx.battle._skill_contest(
        ctx.attacker,
        ctx.defender,
        ["combat", "athletics"],
        ["combat", "athletics"],
        attacker_id=ctx.attacker_id,
        defender_id=ctx.defender_id,
    )
    if contest["attacker_wins"]:
        ctx.battle.apply_forced_movement(
            ctx.attacker_id,
            ctx.defender_id,
            {"kind": "push", "distance": 1},
        )
    ctx.events.append(
        {
            "type": "maneuver",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "strength_push",
            "result": "success" if contest["attacker_wins"] else "fail",
            "attacker_total": contest["attacker_total"],
            "defender_total": contest["defender_total"],
            "description": "Strength attempts to push the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("take down")
def _take_down(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    contest = ctx.battle._skill_contest(
        ctx.attacker,
        ctx.defender,
        ["combat", "acrobatics"],
        ["combat", "acrobatics"],
        attacker_id=ctx.attacker_id,
        defender_id=ctx.defender_id,
    )
    if contest["attacker_wins"] and not ctx.defender.has_status("Tripped"):
        ctx.defender.statuses.append({"name": "Tripped", "remaining": 1})
    ctx.events.append(
        {
            "type": "maneuver",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "take_down_trip",
            "result": "success" if contest["attacker_wins"] else "fail",
            "attacker_total": contest["attacker_total"],
            "defender_total": contest["defender_total"],
            "description": "Take Down attempts to trip the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("vital throw", phase="pre_damage")
def _vital_throw(ctx: MoveSpecialContext) -> None:
    ctx.result["hit"] = True


@register_move_special("inferno")
def _inferno_burn(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Burned",
        effect="inferno",
        description="Inferno burns the target.",
    )


@register_move_special("imprison", phase="pre_damage")
def _imprison_cannot_miss(ctx: MoveSpecialContext) -> None:
    ctx.result["hit"] = True


@register_move_special("imprison")
def _imprison_lock(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    locked_moves = [str(move.name or "").strip() for move in ctx.attacker.spec.moves if move.name]
    ctx.defender.add_temporary_effect(
        "imprisoned_moves",
        moves=locked_moves,
        source=ctx.attacker_id,
    )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "imprison",
            "locked_moves": locked_moves,
            "description": "Imprison locks the target out of the user's moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("grudge")
def _grudge_ready(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("grudge_ready")
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "grudge_ready",
            "description": "Grudge will suppress the next attacker that causes the user to faint.",
            "target_hp": ctx.attacker.hp,
        }
    )


def _resolve_wish(ctx: MoveSpecialContext, *, label: str) -> None:
    battle = ctx.battle
    attacker = ctx.attacker
    target = ctx.defender
    target_id = ctx.defender_id
    if target is None or target_id is None:
        candidates = battle._bench_candidates(attacker.controller_id)
        if candidates:
            target_id = candidates[0]
            target = battle.pokemon.get(target_id)
    if target is None or target_id is None:
        return
    before_injuries = int(target.injuries or 0)
    target.injuries = max(0, before_injuries - 3)
    if target.hp is not None:
        target.heal(target.max_hp())
    usage = battle.frequency_usage.get(target_id, {})
    for move_name in list(usage.keys()):
        if move_name.strip().lower() in {"healing wish", "lunar dance"}:
            continue
        usage.pop(move_name, None)
    if not usage and target_id in battle.frequency_usage:
        battle.frequency_usage.pop(target_id, None)
    if attacker.hp is not None:
        attacker.apply_damage(attacker.hp, skip_injury=True)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": target_id,
            "move": ctx.move.name,
            "effect": label,
            "description": f"{ctx.move.name} restores the target and the user faints.",
            "target_hp": target.hp,
            "injuries_removed": before_injuries - int(target.injuries or 0),
        }
    )


@register_move_special("healing wish")
def _healing_wish(ctx: MoveSpecialContext) -> None:
    _resolve_wish(ctx, label="healing_wish")


@register_move_special("lunar dance")
def _lunar_dance(ctx: MoveSpecialContext) -> None:
    _resolve_wish(ctx, label="lunar_dance")


@register_move_special("metronome")
def _metronome(ctx: MoveSpecialContext) -> None:
    pool = _metronome_pool()
    if not pool:
        return
    candidates = list(pool)
    while candidates:
        chosen = ctx.battle.rng.choice(candidates)
        candidates.remove(chosen)
        target_id = ctx.defender_id
        if targeting.move_requires_target(chosen):
            if target_id is None or target_id not in ctx.battle.pokemon:
                team = ctx.battle._team_for(ctx.attacker_id)
                foes = [
                    pid
                    for pid, mon in ctx.battle.pokemon.items()
                    if mon.active and not mon.fainted and ctx.battle._team_for(pid) != team
                ]
                if foes:
                    target_id = ctx.battle.rng.choice(foes)
            if target_id is None:
                continue
        try:
            ctx.battle.resolve_move_targets(
                attacker_id=ctx.attacker_id,
                move=chosen,
                target_id=target_id,
            )
        except ValueError:
            continue
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": target_id,
                "move": ctx.move.name,
                "effect": "metronome",
                "selected_move": chosen.name,
                "description": "Metronome calls a random move.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return


@register_move_special("mirror coat")
def _mirror_coat(ctx: MoveSpecialContext) -> None:
    battle = ctx.battle
    damage_taken = int(battle.damage_received_this_round.get(ctx.attacker_id, 0) or 0)
    if damage_taken <= 0:
        return
    candidates: List[str] = []
    for attacker_id in battle.damage_taken_from.get(ctx.attacker_id, set()):
        attacker = battle.pokemon.get(attacker_id)
        if attacker is None or attacker.fainted:
            continue
        last_moves = attacker.get_temporary_effects("last_move")
        last_moves.sort(key=lambda entry: int(entry.get("round", 0) or 0), reverse=True)
        move_name = str(last_moves[0].get("name") or "") if last_moves else ""
        spec = _lookup_move_spec(move_name)
        if spec and (spec.category or "").strip().lower() == "special":
            candidates.append(attacker_id)
    if not candidates:
        return
    target_id = ctx.defender_id if ctx.defender_id in candidates else candidates[0]
    defender = battle.pokemon.get(target_id) if target_id else None
    if defender is None or defender.fainted:
        return
    if ptu_engine.type_multiplier("Psychic", defender.spec.types) <= 0:
        return
    before = defender.hp or 0
    defender.apply_damage(damage_taken * 2)
    dealt = max(0, before - (defender.hp or 0))
    if dealt > 0:
        battle.damage_received_this_round[target_id] = (
            battle.damage_received_this_round.get(target_id, 0) + dealt
        )
        battle._record_damage_exchange(ctx.attacker_id, target_id)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": target_id,
            "move": ctx.move.name,
            "effect": "mirror_coat",
            "damage": dealt,
            "description": "Mirror Coat reflects special damage.",
            "target_hp": defender.hp,
        }
    )


@register_move_special("hyperspace hole")
def _hyperspace_hole(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "hyperspace_hole",
            "description": "Hyperspace Hole resolves each target separately.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )
    _create_dimensional_rift(ctx)


def _create_dimensional_rift(ctx: MoveSpecialContext) -> None:
    origin = ctx.defender.position if ctx.defender is not None else ctx.attacker.position
    ctx.battle._create_dimensional_rift(
        ctx.attacker_id,
        origin,
        source_move=ctx.move.name,
    )


@register_move_special("razor wind")
def _razor_wind_log(ctx: MoveSpecialContext) -> None:
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "razor_wind",
            "description": "Razor Wind lashes out after its setup.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


_PLEDGE_PAIRS = {
    frozenset({"fire pledge", "grass pledge"}): "fire_hazards",
    frozenset({"fire pledge", "water pledge"}): "rainbow",
    frozenset({"grass pledge", "water pledge"}): "swamp",
}


def _apply_pledge_combo(ctx: MoveSpecialContext, other_move: str) -> None:
    combo = _PLEDGE_PAIRS.get(frozenset({ctx.move_name, other_move}))
    if not combo:
        return
    if combo == "fire_hazards":
        if ctx.defender is None or ctx.defender.position is None:
            return
        if ctx.battle.grid is None:
            return
        cx, cy = ctx.defender.position
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                coord = (cx + dx, cy + dy)
                if not ctx.battle.grid.in_bounds(coord):
                    continue
                if targeting.chebyshev_distance(coord, ctx.defender.position) <= 1:
                    ctx.battle._place_hazard(coord, "fire_hazards", 1)
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "pledge_fire_hazards",
                "description": "Pledge combo creates Fire Hazards around the target.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if combo == "rainbow":
        ctx.battle.terrain = {"name": "Rainbow", "remaining": 5}
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "move": ctx.move.name,
                "effect": "pledge_rainbow",
                "terrain": ctx.battle.terrain,
                "description": "Pledge combo creates a Rainbow.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if combo == "swamp":
        if ctx.defender is None or ctx.defender.position is None:
            return
        team = ctx.battle._team_for(ctx.attacker_id)
        for pid, mon in ctx.battle.pokemon.items():
            if mon.fainted or not mon.active or ctx.battle._team_for(pid) == team:
                continue
            if mon.position is None:
                continue
            if targeting.chebyshev_distance(mon.position, ctx.defender.position) <= 1:
                ctx.battle._apply_status(
                    ctx.events,
                    attacker_id=ctx.attacker_id,
                    target_id=pid,
                    move=ctx.move,
                    target=mon,
                    status="Slowed",
                    effect="pledge_swamp",
                    description="Pledge combo slows the target.",
                    remaining=1,
                )
                ctx.battle._apply_combat_stage(
                    ctx.events,
                    attacker_id=ctx.attacker_id,
                    target_id=pid,
                    move=ctx.move,
                    target=mon,
                    stat="spd",
                    delta=-2,
                    effect="pledge_swamp",
                    description="Pledge combo lowers Speed.",
                )
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "pledge_swamp",
                "description": "Pledge combo slows foes around the target.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("fire pledge", "grass pledge", "water pledge")
def _pledge_combo(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect(
        "pledge_used",
        move=ctx.move.name,
        round=ctx.battle.round,
        target_id=ctx.defender_id,
    )
    if ctx.defender_id is None:
        return
    team = ctx.battle._team_for(ctx.attacker_id)
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.attacker_id or mon.fainted or not mon.active:
            continue
        if ctx.battle._team_for(pid) != team:
            continue
        for entry in mon.get_temporary_effects("pledge_used"):
            if entry.get("round") != ctx.battle.round:
                continue
            if entry.get("combo_resolved"):
                continue
            if entry.get("target_id") != ctx.defender_id:
                continue
            other_move = str(entry.get("move") or "").strip().lower()
            if not other_move or other_move == ctx.move_name:
                continue
            entry["combo_resolved"] = True
            _apply_pledge_combo(ctx, other_move)
            return


@register_move_special("omen")
def _omen(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect(
        "accuracy_penalty", amount=2, expires_round=ctx.battle.round + 1, source="Omen", source_id=ctx.attacker_id
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Omen",
            "move": ctx.move.name,
            "effect": "accuracy_penalty",
            "amount": -2,
            "description": "Omen lowers the target's accuracy.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("rally")
def _rally(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Rally"):
        return
    battle = ctx.battle
    attacker = ctx.attacker
    if attacker.position is None or battle.grid is None:
        return
    team = battle._team_for(ctx.attacker_id)
    for pid, mon in battle.pokemon.items():
        if pid == ctx.attacker_id or mon.fainted or not mon.active:
            continue
        if battle._team_for(pid) != team:
            continue
        if mon.position is None:
            continue
        if targeting.chebyshev_distance(attacker.position, mon.position) > 10:
            continue
        if mon.has_status("Sleep") or mon.has_status("Asleep") or mon.has_status("Flinched"):
            continue
        reachable = movement.legal_shift_tiles(battle, pid)
        if not reachable:
            continue
        origin = mon.position
        enemies = []
        for foe_id, foe in battle.pokemon.items():
            if not foe.active or foe.fainted or foe.position is None:
                continue
            if battle._team_for(foe_id) == team:
                continue
            enemies.append(foe)

        def score(coord):
            if not enemies:
                return targeting.chebyshev_distance(origin, coord)
            return min(targeting.chebyshev_distance(coord, foe.position) for foe in enemies)

        destination = max(reachable, key=score)
        mon.position = destination
        battle.log_event(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Rally",
                "effect": "shift",
                "from": origin,
                "to": destination,
                "description": "Rally shifts an ally.",
                "target_hp": mon.hp,
            }
        )


@register_move_special("rally [errata]")
def _rally_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Rally [Errata]"):
        return
    battle = ctx.battle
    attacker = ctx.attacker
    if attacker.position is None:
        return
    team = battle._team_for(ctx.attacker_id)
    for pid, mon in battle.pokemon.items():
        if not mon.active or mon.fainted or mon.position is None:
            continue
        if battle._team_for(pid) != team:
            continue
        if targeting.chebyshev_distance(attacker.position, mon.position) > 10:
            continue
        if mon.has_status("Sleep") or mon.has_status("Asleep") or mon.has_status("Flinched"):
            continue
        reachable = movement.legal_shift_tiles(battle, pid)
        if not reachable:
            continue
        origin = mon.position
        enemies = []
        for foe_id, foe in battle.pokemon.items():
            if not foe.active or foe.fainted or foe.position is None:
                continue
            if battle._team_for(foe_id) == team:
                continue
            enemies.append(foe)

        def score(coord):
            if not enemies:
                return targeting.chebyshev_distance(origin, coord)
            return min(targeting.chebyshev_distance(coord, foe.position) for foe in enemies)

        destination = max(reachable, key=score)
        mon.position = destination
        battle.log_event(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Rally [Errata]",
                "effect": "disengage",
                "from": origin,
                "to": destination,
                "description": "Rally lets allies disengage.",
                "target_hp": mon.hp,
            }
        )


@register_move_special("regal challenge")
def _regal_challenge(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Regal Challenge"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    move_stub = MoveSpec(name="Regal Challenge", type="Normal", category="Status")
    if ctx.hit:
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=move_stub,
            target=ctx.defender,
            stat="spd",
            delta=-1,
            effect="regal_challenge",
            description="Regal Challenge lowers Speed.",
        )
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=move_stub,
            target=ctx.defender,
            status="Slowed",
            effect="regal_challenge",
            description="Regal Challenge slows the target.",
            remaining=1,
        )
    else:
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=move_stub,
            target=ctx.attacker,
            stat="atk",
            delta=1,
            effect="regal_challenge_miss",
            description="Regal Challenge empowers the user.",
        )
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=move_stub,
            target=ctx.attacker,
            stat="spatk",
            delta=1,
            effect="regal_challenge_miss",
            description="Regal Challenge empowers the user.",
        )


@register_move_special("regal challenge [errata]")
def _regal_challenge_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Regal Challenge [Errata]"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    move_stub = MoveSpec(name="Regal Challenge [Errata]", type="Normal", category="Status")
    # Default to deference when no player choice is available.
    choice = "deference"
    if choice == "deference":
        # Consume the target's next Shift action.
        try:
            from ..battle_state import ActionType

            ctx.defender.mark_action(ActionType.SHIFT, "Regal Challenge")
        except Exception:
            pass
        # Lower the target's highest combat stage by 3.
        stage_order = ["atk", "def", "spatk", "spdef", "spd", "accuracy", "evasion"]
        best_stat = None
        best_value = None
        for stat in stage_order:
            value = int(ctx.defender.combat_stages.get(stat, 0) or 0)
            if best_value is None or value > best_value:
                best_value = value
                best_stat = stat
        if best_stat:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.defender_id,
                move=move_stub,
                target=ctx.defender,
                stat=best_stat,
                delta=-3,
                effect="regal_challenge_errata",
                description="Regal Challenge demands deference.",
            )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Regal Challenge [Errata]",
                "move": ctx.move.name,
                "effect": "deference",
                "description": "Regal Challenge forces deference.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    ctx.attacker.add_temporary_effect(
        "damage_bonus",
        amount=10,
        category="all",
        expires_round=ctx.battle.round + 999,
        source="Regal Challenge [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Regal Challenge [Errata]",
            "move": ctx.move.name,
            "effect": "defiance",
            "description": "Regal Challenge rewards defiance with extra damage.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("rocket")
def _rocket(ctx: MoveSpecialContext) -> None:
    attacker = ctx.attacker
    battle = ctx.battle
    attacker.add_temporary_effect(
        "rocket_speed_bonus", amount=3, expires_round=battle.round + 1
    )
    attacker.add_temporary_effect("rocket_initiative", round=battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Rocket",
            "move": ctx.move.name,
            "effect": "initiative_boost",
            "description": "Rocket boosts sky speed and guarantees first initiative next round.",
            "target_hp": attacker.hp,
        }
    )


@register_move_special("rocket [errata]")
def _rocket_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Rocket [Errata]"):
        return
    battle = ctx.battle
    ctx.attacker.add_temporary_effect(
        "rocket_initiative",
        round=battle.round + 1,
    )
    ctx.attacker.add_temporary_effect(
        "no_interrupts",
        expires_round=battle.round + 1,
        source="Rocket [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Rocket [Errata]",
            "move": ctx.move.name,
            "effect": "initiative_boost",
            "description": "Rocket [Errata] jumps to the top of next round and blocks responses.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sand stream")
def _sand_stream(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Sand Stream"):
        return
    if not ctx.hit:
        return
    set_weather(ctx.battle, "Sandstorm")
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Sand Stream",
            "move": ctx.move.name,
            "effect": "weather",
            "weather": "Sandstorm",
            "description": "Sand Stream summons a sandstorm.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sand stream [errata]")
def _sand_stream_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Sand Stream [Errata]"):
        return
    if not ctx.hit:
        return
    set_weather(ctx.battle, "Sandstorm")
    ctx.attacker.add_temporary_effect(
        "weather_immunity",
        weather="sandstorm",
        expires_round=ctx.battle.round + 1,
        source="Sand Stream [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Sand Stream [Errata]",
            "move": ctx.move.name,
            "effect": "weather",
            "weather": "Sandstorm",
            "description": "Sand Stream summons a sandstorm.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("snow warning")
def _snow_warning(ctx: MoveSpecialContext) -> None:
    if not ctx.hit:
        return
    set_weather(ctx.battle, "Hail")
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Snow Warning",
            "move": ctx.move.name,
            "effect": "weather",
            "weather": "Hail",
            "description": "Snow Warning summons hail.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("poison gas")
def _poison_gas_odious(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    if not ctx.attacker.has_ability("Odious Spray"):
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="odious_spray",
        description="Odious Spray flinches the target.",
        remaining=1,
    )


@register_move_special("string shot")
def _string_shot_silk_threads(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None:
        return
    if not ctx.attacker.has_ability("Silk Threads"):
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Slowed",
        effect="silk_threads",
        description="Silk Threads slows the target.",
        remaining=1,
    )


@register_move_special("power construct")
def _power_construct(ctx: MoveSpecialContext) -> None:
    attacker = ctx.attacker
    max_hp = attacker.max_hp()
    if max_hp <= 0 or attacker.hp is None:
        return
    if attacker.hp * 2 > max_hp:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Power Construct",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Power Construct requires being below half HP.",
                "target_hp": attacker.hp,
            }
        )
        return
    if attacker.get_temporary_effects("power_construct_active"):
        return
    temp = max(1, int(max_hp // 2))
    attacker.temp_hp = max(attacker.temp_hp, temp)
    attacker.add_temporary_effect("temp_hp_locked", source="Power Construct")
    attacker.add_temporary_effect("power_construct_active")
    ctx.battle._set_power_construct_form(ctx.attacker_id, attacker, source=ctx.move.name)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Power Construct",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": temp,
            "description": "Power Construct grants temporary HP and changes form.",
            "target_hp": attacker.hp,
        }
    )


@register_move_special("schooling")
def _schooling(ctx: MoveSpecialContext) -> None:
    attacker = ctx.attacker
    max_hp = attacker.max_hp()
    if max_hp <= 0:
        return
    if attacker.get_temporary_effects("schooling_active"):
        return
    temp = max(1, int(max_hp // 2))
    attacker.temp_hp = max(attacker.temp_hp, temp)
    attacker.add_temporary_effect("temp_hp_locked", source="Schooling")
    attacker.add_temporary_effect("schooling_active")
    ctx.battle._set_schooling_form(ctx.attacker_id, attacker, form="school", source=ctx.move.name)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Schooling",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": temp,
            "description": "Schooling grants temporary HP and changes form.",
            "target_hp": attacker.hp,
        }
    )


@register_move_special("screen cleaner")
def _screen_cleaner(ctx: MoveSpecialContext) -> None:
    removed = []
    for pid, mon in ctx.battle.pokemon.items():
        if not mon.statuses:
            continue
        before = list(mon.statuses)
        mon.statuses = [
            entry
            for entry in mon.statuses
            if "blessing" not in mon._normalized_status_name(entry)
            and mon._normalized_status_name(entry) != "safeguard"
        ]
        if mon.statuses != before:
            removed.append(pid)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Screen Cleaner",
            "move": ctx.move.name,
            "effect": "blessings_cleared",
            "cleared": removed,
            "description": "Screen Cleaner clears all blessings.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("propeller tail")
def _propeller_tail(ctx: MoveSpecialContext) -> None:
    ctx.attacker.add_temporary_effect("sprint", expires_round=ctx.battle.round + 1)
    ctx.attacker.add_temporary_effect("no_intercept", expires_round=ctx.battle.round + 1)
    ctx.attacker.add_temporary_effect("target_lock", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Propeller Tail",
            "move": ctx.move.name,
            "effect": "sprint",
            "description": "Propeller Tail grants Sprint and prevents redirection.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("snuggle")
def _snuggle(ctx: MoveSpecialContext) -> None:
    tick = ctx.attacker.tick_value() * 2
    gained = ctx.attacker.add_temp_hp(tick)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Snuggle",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": gained,
            "description": "Snuggle grants temporary HP.",
            "target_hp": ctx.attacker.hp,
        }
    )
    if ctx.defender is not None and ctx.defender_id is not None:
        gained_def = ctx.defender.add_temp_hp(tick)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Snuggle",
                "move": ctx.move.name,
                "effect": "temp_hp",
                "amount": gained_def,
                "description": "Snuggle grants temporary HP.",
                "target_hp": ctx.defender.hp,
            }
        )


@register_move_special("starlight")
def _starlight(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Starlight"):
        return
    ctx.attacker.add_temporary_effect("luminous", expires_round=ctx.battle.round + 999)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Starlight",
            "move": ctx.move.name,
            "effect": "luminous",
            "description": "Starlight makes the user luminous.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("starlight [errata]")
def _starlight_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Starlight [Errata]"):
        return
    if ctx.attacker.get_temporary_effects("luminous"):
        while ctx.attacker.remove_temporary_effect("luminous"):
            continue
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat="spdef",
            delta=2,
            effect="starlight_errata",
            description="Starlight boosts Special Defense.",
        )
        ctx.attacker.add_temporary_effect(
            "evasion_bonus",
            amount=2,
            scope="all",
            expires_round=ctx.battle.round + 999,
            source="Starlight [Errata]",
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Starlight [Errata]",
                "move": ctx.move.name,
                "effect": "buff",
                "description": "Starlight expends Luminous for defensive bonuses.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.add_temporary_effect("luminous", expires_round=ctx.battle.round + 999)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Starlight [Errata]",
            "move": ctx.move.name,
            "effect": "luminous",
            "description": "Starlight makes the user luminous.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("starswirl")
def _starswirl(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Starswirl"):
        return
    for status_name in ("trapped", "leech seed"):
        ctx.attacker.remove_status_by_names({status_name})
    if ctx.battle.grid is not None:
        for coord, tile in list(ctx.battle.grid.tiles.items()):
            if isinstance(tile, dict) and "hazards" in tile:
                tile.pop("hazards", None)
                ctx.battle.grid.tiles[coord] = tile
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Starswirl",
            "move": ctx.move.name,
            "effect": "rapid_spin",
            "description": "Starswirl clears hazards and bindings.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("starswirl [errata]")
def _starswirl_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Starswirl [Errata]"):
        return
    ctx.battle._remove_statuses_by_set(ctx.attacker, _STATUS_CONDITIONS_TO_CURE, limit=None)
    for status_name in ("trapped", "leech seed"):
        ctx.attacker.remove_status_by_names({status_name})
    if ctx.battle.grid is not None:
        for coord, tile in list(ctx.battle.grid.tiles.items()):
            if isinstance(tile, dict) and "hazards" in tile:
                tile.pop("hazards", None)
                ctx.battle.grid.tiles[coord] = tile
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Starswirl [Errata]",
            "move": ctx.move.name,
            "effect": "rapid_spin",
            "description": "Starswirl clears hazards and conditions.",
            "target_hp": ctx.attacker.hp,
        }
    )
    ctx.attacker.add_temporary_effect(
        "action_override",
        action="swift",
        move="Rapid Spin",
        consume=True,
        source="Starswirl [Errata]",
        round=ctx.battle.round,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Starswirl [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Starswirl readies Rapid Spin as a Swift Action.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("stance change")
def _stance_change_toggle(ctx: MoveSpecialContext) -> None:
    entry = ctx.battle._stance_entry(ctx.attacker)
    current = str(entry.get("stance") or "shield").strip().lower()
    next_stance = "sword" if current == "shield" else "shield"
    ctx.battle._set_stance(ctx.attacker_id, ctx.attacker, next_stance, source=ctx.move.name)


@register_move_special("zen mode")
def _zen_mode_toggle(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Zen Mode"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("zen_mode_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Zen Mode",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Zen Mode can only be toggled once per scene.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    max_hp = ctx.attacker.max_hp()
    hp = ctx.attacker.hp or 0
    entry = next(iter(ctx.attacker.get_temporary_effects("zen_mode")), None)
    active = bool(entry.get("active")) if entry else False
    if not active and hp > max(1, max_hp // 2):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Zen Mode",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Zen Mode requires being below half HP to activate.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if active and hp < max(1, max_hp // 2):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Zen Mode",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Zen Mode requires at least half HP to deactivate.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("zen_mode_used", count=used_count + 1)
    else:
        used_entry["count"] = used_count + 1
    ctx.battle._set_zen_mode(ctx.attacker_id, ctx.attacker, active=not active, source=ctx.move.name)


@register_move_special("zen mode [errata]")
def _zen_mode_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Zen Mode [Errata]"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("zen_mode_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Zen Mode [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Zen Mode can only be activated once per scene.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("zen_mode_used", count=used_count + 1)
    else:
        used_entry["count"] = used_count + 1
    ctx.battle._set_zen_mode(ctx.attacker_id, ctx.attacker, active=True, source=ctx.move.name)
    added = []
    for move_name in ("Flamethrower", "Psychic"):
        if all((mv.name or "").strip().lower() != move_name.lower() for mv in ctx.attacker.spec.moves):
            spec = _lookup_move_spec(move_name)
            if spec:
                ctx.attacker.spec.moves.append(copy.deepcopy(spec))
                added.append(move_name)
    if added:
        ctx.attacker.add_temporary_effect("zen_mode_errata_moves", moves=added)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Zen Mode [Errata]",
            "move": ctx.move.name,
            "effect": "activate",
            "description": "Zen Mode activates and unlocks Flamethrower and Psychic.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("zen snowed")
def _zen_snowed_activate(ctx: MoveSpecialContext) -> None:
    used_entry = next(iter(ctx.attacker.get_temporary_effects("zen_snowed_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Zen Snowed",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Zen Snowed can only be activated once per scene.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("zen_snowed_used", count=used_count + 1)
    else:
        used_entry["count"] = used_count + 1
    ctx.battle._set_zen_mode(ctx.attacker_id, ctx.attacker, active=True, source=ctx.move.name, snowed=True)
    added = []
    for move_name in ("Ice Punch", "Fire Punch"):
        if all((mv.name or "").strip().lower() != move_name.lower() for mv in ctx.attacker.spec.moves):
            spec = _lookup_move_spec(move_name)
            if spec:
                ctx.attacker.spec.moves.append(copy.deepcopy(spec))
                added.append(move_name)
    if added:
        ctx.attacker.add_temporary_effect("zen_snowed_moves", moves=added)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Zen Snowed",
            "move": ctx.move.name,
            "effect": "activate",
            "description": "Zen Snowed unlocks Ice Punch and Fire Punch.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("splendorous rider")
def _splendorous_rider(ctx: MoveSpecialContext) -> None:
    mount_moves = []
    for entry in ctx.attacker.get_temporary_effects("mount_moves"):
        moves = entry.get("moves")
        if isinstance(moves, list):
            mount_moves.extend(moves)
    if not mount_moves:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Splendorous Rider",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "No mount moves are available.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    known = {str(m.name or "").strip().lower() for m in ctx.attacker.spec.moves}
    chosen = None
    for move in mount_moves:
        if isinstance(move, MoveSpec):
            name = (move.name or "").strip().lower()
            if name and name not in known:
                chosen = copy.deepcopy(move)
                break
    if chosen is None:
        return
    ctx.attacker.spec.moves.append(chosen)
    ctx.attacker.add_temporary_effect(
        "splendorous_rider_move",
        name=chosen.name,
        round=ctx.battle.round,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Splendorous Rider",
            "move": ctx.move.name,
            "effect": "borrow_move",
            "borrowed": chosen.name,
            "description": "Splendorous Rider borrows a mount move for the turn.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("power of alchemy")
def _power_of_alchemy(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None:
        return
    abilities = []
    for entry in ctx.defender.spec.abilities:
        if isinstance(entry, dict):
            name = str(entry.get("name") or "").strip()
            if name:
                abilities.append(name)
    if not abilities:
        return
    chosen = abilities[0]
    ctx.attacker.add_temporary_effect(
        "ability_granted",
        ability=chosen,
        expires_round=ctx.battle.round + 999,
        source="Power of Alchemy",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Power of Alchemy",
            "move": ctx.move.name,
            "effect": "ability_copy",
            "copied": chosen,
            "description": "Power of Alchemy copies a foe's ability.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("anti-materiel rifle (set up)", phase="post_damage")
def _anti_materiel_rifle_set_up(ctx: MoveSpecialContext) -> None:
    if ctx.attacker is None:
        return
    ctx.attacker.add_temporary_effect("amr_set_up", round=ctx.battle.round)
    if not ctx.attacker.has_status("Braced"):
        ctx.attacker.statuses.append({"name": "Braced", "remaining": 2})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "amr_set_up",
            "description": "Anti-Materiel Rifle braces the user for a follow-up shot.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("anti-materiel rifle (resolution)", phase="pre_damage")
def _anti_materiel_rifle_resolution(ctx: MoveSpecialContext) -> None:
    if ctx.attacker is None:
        return
    if not ctx.attacker.get_temporary_effects("amr_set_up"):
        ctx.result["hit"] = False
        ctx.result["damage"] = 0
        ctx.result["type_multiplier"] = 0.0
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "move": ctx.move.name,
                "effect": "amr_no_setup",
                "description": "Anti-Materiel Rifle (Resolution) requires Set Up first.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.remove_temporary_effect("amr_set_up")


@register_move_special("heal bell")
def _heal_bell(ctx: MoveSpecialContext) -> None:
    cured_targets = []
    targets: List[tuple[str, PokemonState]] = []
    range_kind = (ctx.move.range_kind or ctx.move.target_kind or "").strip().lower()
    if range_kind == "burst" and ctx.attacker is not None:
        center = None
        if ctx.defender is not None and ctx.defender.position is not None:
            center = ctx.defender.position
        elif ctx.attacker.position is not None:
            center = ctx.attacker.position
        radius = max(0, int(ctx.move.range_value or ctx.move.area_value or 0))
        if center is not None:
            for pid, mon in ctx.battle.pokemon.items():
                if mon.position is None or mon.fainted:
                    continue
                if targeting.chebyshev_distance(center, mon.position) <= radius:
                    targets.append((pid, mon))
    if not targets:
        if ctx.defender is not None and ctx.defender_id is not None:
            targets.append((ctx.defender_id, ctx.defender))
        elif ctx.attacker is not None:
            targets.append((ctx.attacker_id, ctx.attacker))
    for pid, mon in targets:
        removed = []
        for entry in list(mon.statuses):
            normalized = mon._normalized_status_name(entry)
            if normalized in _STATUS_CONDITIONS_TO_CURE:
                mon.statuses.remove(entry)
                removed.append(normalized)
        if not removed:
            continue
        cured_targets.append(pid)
        if ctx.attacker.has_ability("Soothing Tone"):
            before = mon.hp or 0
            mon.heal(mon.tick_value())
            healed = max(0, (mon.hp or 0) - before)
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": pid,
                    "ability": "Soothing Tone",
                    "move": ctx.move.name,
                    "effect": "heal",
                    "amount": healed,
                    "description": "Soothing Tone heals those cured by Heal Bell.",
                    "target_hp": mon.hp,
                }
            )
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "move": ctx.move.name,
            "effect": "heal_bell",
            "cured": cured_targets,
        }
    )


@register_move_special("growth")
def _growth(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker or not ctx.hit:
        return
    weather = ""
    if hasattr(ctx.battle, "effective_weather"):
        weather = str(ctx.battle.effective_weather() or "")
    else:
        weather = str(getattr(ctx.battle, "weather", "") or "")
    amount = 2 if "sun" in weather.strip().lower() else 1
    for stat in ("atk", "spatk"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat=stat,
            delta=amount,
            description=f"{ctx.move.name} raises {stat}.",
        )


@register_move_special("sunglow")
def _sunglow_radiant(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Sunglow") or has_errata(ctx.attacker, "Sunglow"):
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" not in weather:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "ability": "Sunglow",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Sunglow requires sunlight.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if not ctx.attacker.get_temporary_effects("radiant"):
        ctx.attacker.add_temporary_effect("radiant", source="Sunglow")
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Sunglow",
            "move": ctx.move.name,
            "effect": "radiant",
            "description": "Sunglow makes the user Radiant.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sunglow [errata]")
def _sunglow_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Sunglow [Errata]"):
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" not in weather:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "ability": "Sunglow [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Sunglow requires sunlight.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if ctx.attacker.get_temporary_effects("radiant"):
        while ctx.attacker.remove_temporary_effect("radiant"):
            continue
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat="atk",
            delta=2,
            effect="sunglow_errata",
            description="Sunglow boosts Attack.",
        )
        ctx.attacker.add_temporary_effect(
            "accuracy_bonus",
            amount=2,
            expires_round=ctx.battle.round + 999,
            source="Sunglow [Errata]",
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "ability": "Sunglow [Errata]",
                "move": ctx.move.name,
                "effect": "buff",
                "description": "Sunglow expends Radiance for offensive bonuses.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.add_temporary_effect("radiant", source="Sunglow [Errata]")
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Sunglow [Errata]",
            "move": ctx.move.name,
            "effect": "radiant",
            "description": "Sunglow makes the user Radiant.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("symbiosis")
def _symbiosis(ctx: MoveSpecialContext) -> None:
    if has_errata(ctx.attacker, "Symbiosis"):
        return
    if not ctx.attacker.has_ability("Symbiosis"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    if not items:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Symbiosis",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Symbiosis fails without a held item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if isinstance(ctx.defender.spec.items, list) and ctx.defender.spec.items:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Symbiosis",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Symbiosis fails because the ally already holds an item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item = items.pop(ctx.battle._delivery_bird_item_index(ctx.attacker, items))
    if isinstance(ctx.defender.spec.items, list):
        ctx.defender.spec.items.append(item)
    else:
        ctx.defender.spec.items = [item]
    ctx.attacker._sync_source_items()
    ctx.defender._sync_source_items()
    item_name = item.get("name") if isinstance(item, dict) else str(item)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Symbiosis",
            "move": ctx.move.name,
            "effect": "transfer",
            "item": item_name,
            "description": "Symbiosis passes a held item to an ally.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("symbiosis [errata]")
def _symbiosis_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Symbiosis [Errata]"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    if not items:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "ability": "Symbiosis [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Symbiosis fails without a held item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item = copy.deepcopy(items[ctx.battle._delivery_bird_item_index(ctx.attacker, items)])
    if isinstance(item, dict):
        item["shared"] = True
        item["source"] = "Symbiosis [Errata]"
    if isinstance(ctx.defender.spec.items, list):
        ctx.defender.spec.items.append(item)
    else:
        ctx.defender.spec.items = [item]
    ctx.attacker._sync_source_items()
    ctx.defender._sync_source_items()
    item_name = item.get("name") if isinstance(item, dict) else str(item)
    ctx.attacker.add_temporary_effect(
        "symbiosis_shared",
        target=ctx.defender_id,
        item=item_name,
        expires_round=ctx.battle.round + 999,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Symbiosis [Errata]",
            "move": ctx.move.name,
            "effect": "share",
            "item": item_name,
            "description": "Symbiosis shares a held item's effects with an ally.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("targeting system")
def _targeting_system(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Targeting System"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("targeting_system_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("targeting_system_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    ctx.attacker.add_temporary_effect("lock_on_swift", expires_round=ctx.battle.round + 999)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Targeting System",
            "move": ctx.move.name,
            "effect": "lock_on",
            "description": "Targeting System readies Lock-On as a Swift Action.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("toxic nourishment")
def _toxic_nourishment(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Toxic Nourishment"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    cured = ctx.battle._remove_statuses_by_set(
        ctx.defender, {"poisoned", "badly poisoned", "poison"}
    )
    gained = ctx.attacker.add_temp_hp(ctx.attacker.tick_value() * 3)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Toxic Nourishment",
            "move": ctx.move.name,
            "effect": "cure",
            "statuses": cured,
            "amount": gained,
            "description": "Toxic Nourishment cures poison and grants temporary HP.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("trace")
def _trace(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Trace"):
        return
    if ctx.defender is None:
        return
    abilities = ctx.defender.ability_names()
    if not abilities:
        return
    chosen = ctx.battle.rng.choice(abilities)
    while ctx.attacker.remove_temporary_effect("entrained_ability"):
        continue
    ctx.attacker.add_temporary_effect("entrained_ability", ability=chosen, source="trace")
    add_restore_on_switch(ctx.attacker, abilities=list(ctx.attacker.spec.abilities))
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Trace",
            "move": ctx.move.name,
            "effect": "copy",
            "description": "Trace copies the target's ability.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("lick", phase="pre_damage")
def _lick_pre_damage(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.result is None:
        return
    if ctx.attacker.has_ability("Tingly Tongue"):
        used_entry = next(iter(ctx.attacker.get_temporary_effects("tingly_tongue_used")), None)
        used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
        if used_count < 2:
            if used_entry is None:
                ctx.attacker.add_temporary_effect("tingly_tongue_used", count=1)
            else:
                used_entry["count"] = used_count + 1
            bonus = 10
            pre_type = int(ctx.result.get("pre_type_damage", ctx.result.get("damage", 0) or 0) or 0)
            ctx.result["pre_type_damage"] = pre_type + bonus
            ctx.result["damage_roll"] = int(ctx.result.get("damage_roll", 0) or 0) + bonus
            type_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
            ctx.result["damage"] = int((pre_type + bonus) * type_mult)
            ctx.result["tingly_tongue_used"] = True


@register_move_special("lick")
def _lick_post_damage(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker.has_ability("Tingly Tongue") and ctx.result.get("tingly_tongue_used"):
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            status="Paralyzed",
            effect="tingly_tongue",
            description="Tingly Tongue paralyzes the target.",
        )
        roll = int(ctx.result.get("roll") or 0)
        if roll >= 15:
            ctx.defender.add_temporary_effect(
                "paralysis_auto_fail",
                expires_round=ctx.battle.round + 1,
            )
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "ability": "Tingly Tongue",
                    "move": ctx.move.name,
                    "effect": "paralysis_fail",
                    "roll": roll,
                    "description": "Tingly Tongue guarantees paralysis failure next turn.",
                    "target_hp": ctx.defender.hp,
                }
            )
    if ctx.attacker.has_ability("Tonguelash"):
        used_entry = next(iter(ctx.attacker.get_temporary_effects("tonguelash_used")), None)
        used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
        if used_count < 2:
            if used_entry is None:
                ctx.attacker.add_temporary_effect("tonguelash_used", count=1)
            else:
                used_entry["count"] = used_count + 1
            ctx.battle._apply_status(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.defender_id,
                move=ctx.move,
                target=ctx.defender,
                status="Paralyzed",
                effect="tonguelash",
                description="Tonguelash paralyzes the target.",
            )
            if not ctx.defender.has_status("Flinched"):
                ctx.defender.statuses.append({"name": "Flinched", "remaining": 1})
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "ability": "Tonguelash",
                    "move": ctx.move.name,
                    "effect": "flinch",
                    "description": "Tonguelash flinches the target.",
                    "target_hp": ctx.defender.hp,
                }
            )
    if ctx.attacker.has_ability("Flame Tongue"):
        if not ctx.attacker.get_temporary_effects("flame_tongue_used"):
            ctx.battle._apply_status(
                ctx.events,
                attacker_id=ctx.attacker_id,
                target_id=ctx.defender_id,
                move=ctx.move,
                target=ctx.defender,
                status="Burned",
                effect="flame_tongue",
                description="Flame Tongue burns the target.",
            )
            ctx.defender.injuries = max(0, ctx.defender.injuries) + 1
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "ability": "Flame Tongue",
                    "move": ctx.move.name,
                    "effect": "injury",
                    "amount": 1,
                    "injuries": ctx.defender.injuries,
                    "description": "Flame Tongue inflicts an injury.",
                    "target_hp": ctx.defender.hp,
                }
            )
            ctx.attacker.add_temporary_effect(
                "flame_tongue_used",
                expires_round=ctx.battle.round + 999,
            )


@register_move_special("hone claws")
def _hone_claws_vicious(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Vicious"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("vicious_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("vicious_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    choice = "extra_action"
    for entry in list(ctx.attacker.get_temporary_effects("vicious_choice")):
        raw = str(entry.get("choice") or entry.get("mode") or "").strip().lower()
        if raw in {"crit", "critical", "crit_range", "crit-range"}:
            choice = "crit_range"
        ctx.attacker.remove_temporary_effect("vicious_choice")
        break
    if choice == "crit_range":
        ctx.attacker.add_temporary_effect(
            "crit_range_bonus",
            bonus=2,
            source="Vicious",
            expires_round=ctx.battle.round + 999,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": ctx.attacker_id,
                "ability": "Vicious",
                "move": ctx.move.name,
                "effect": "crit_range",
                "amount": 2,
                "description": "Vicious widens critical ranges.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.attacker.add_temporary_effect("extra_action", action="standard", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Vicious",
            "move": ctx.move.name,
            "effect": "extra_action",
            "description": "Vicious grants an extra Standard Action.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("curse")
def _voodoo_doll(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Voodoo Doll"):
        return
    types = {str(t).strip().lower() for t in (ctx.attacker.spec.types or [])}
    if "ghost" not in types:
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("voodoo_doll_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        return
    if ctx.attacker.position is None:
        return
    candidates = []
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or mon.hp is None or mon.hp <= 0:
            continue
        if pid == ctx.defender_id:
            continue
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
            continue
        if mon.position is None:
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 8:
            continue
        candidates.append(pid)
    if not candidates:
        return
    target_id = sorted(candidates)[0]
    target = ctx.battle.pokemon.get(target_id)
    if target is None:
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("voodoo_doll_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=target_id,
        move=ctx.move,
        target=target,
        status="Cursed",
        effect="voodoo_doll",
        description="Voodoo Doll curses an additional target.",
        remaining=3,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": target_id,
            "ability": "Voodoo Doll",
            "move": ctx.move.name,
            "effect": "curse",
            "description": "Voodoo Doll spreads the curse.",
            "target_hp": target.hp,
        }
    )


@register_move_special("barrier")
def _wallmaster_bonus(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Wallmaster"):
        return
    if ctx.battle.grid is not None and ctx.attacker.position is not None:
        x, y = ctx.attacker.position
        extra = []
        for coord in ((x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)):
            if not ctx.battle.grid.in_bounds(coord):
                continue
            if coord in ctx.battle.grid.blockers:
                continue
            extra.append(coord)
        for coord in extra[:2]:
            ctx.battle._place_barrier_segment(coord, source_id=ctx.attacker_id, move_name=ctx.move.name, source_name="Wallmaster")
        if extra:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.attacker_id,
                    "target": ctx.attacker_id,
                    "ability": "Wallmaster",
                    "move": ctx.move.name,
                    "effect": "barrier_extend",
                    "description": "Wallmaster adds extra Barrier segments.",
                    "target_hp": ctx.attacker.hp,
                }
            )
            return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="def",
        delta=2,
        effect="wallmaster",
        description="Wallmaster raises Defense when using Barrier.",
    )


@register_move_special("teleport")
def _transporter(ctx: MoveSpecialContext) -> None:
    has_base = ctx.attacker.has_ability("Transporter") and not has_errata(ctx.attacker, "Transporter")
    has_errata_variant = has_ability_exact(ctx.attacker, "Transporter [Errata]")
    if not (has_base or has_errata_variant):
        return
    if has_errata_variant:
        ready = next(iter(ctx.attacker.get_temporary_effects("transporter_ready")), None)
        if ready is None:
            return
        ctx.attacker.remove_temporary_effect("transporter_ready")
    used_entry = next(iter(ctx.attacker.get_temporary_effects("transporter_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 3:
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("transporter_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    ability_name = "Transporter [Errata]" if has_errata_variant else "Transporter"
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "teleport_boost",
            "description": "Transporter empowers Teleport.",
            "target_hp": ctx.attacker.hp,
        }
    )
@register_global_move_special(phase="end_action")
def _type_strategist(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Type Strategist"):
        return
    move_type = (ctx.move.type or "").strip().lower()
    primary = (ctx.attacker.spec.types[0] if ctx.attacker.spec.types else "").strip().lower()
    if not primary or move_type != primary:
        return
    max_hp = ctx.attacker.max_hp()
    amount = 10 if (max_hp > 0 and (ctx.attacker.hp or 0) * 3 <= max_hp) else 5
    ctx.attacker.add_temporary_effect(
        "damage_reduction",
        amount=amount,
        expires_round=ctx.battle.round + 1,
        source="Type Strategist",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Type Strategist",
            "move": ctx.move.name,
            "effect": "damage_reduction",
            "amount": amount,
            "description": "Type Strategist grants damage reduction after a matching move.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("rain dish [errata]")
def _rain_dish_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Rain Dish [Errata]"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("rain_dish_errata_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 5:
        return
    max_hp = ctx.attacker.max_hp()
    hp = ctx.attacker.hp or 0
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    rainy = "rain" in weather
    if hp * 2 > max_hp and not rainy:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Rain Dish [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Rain Dish requires rain or being below half HP.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("rain_dish_errata_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    heal_amount = ctx.attacker.tick_value()
    before = ctx.attacker.hp or 0
    ctx.attacker.heal(heal_amount)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Rain Dish [Errata]",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": "Rain Dish restores a tick of HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("solar power [errata]")
def _solar_power_errata_ready(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Solar Power [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "solar_power_errata_ready",
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Solar Power [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Solar Power readies a damage bonus.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("suction cups [errata]")
def _suction_cups_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Suction Cups [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "damage_reduction",
        amount=5,
        expires_round=ctx.battle.round + 1,
        source="Suction Cups [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Suction Cups [Errata]",
            "move": ctx.move.name,
            "effect": "damage_reduction",
            "amount": 5,
            "description": "Suction Cups grants damage reduction.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("sumo stance [errata]")
def _sumo_stance_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Sumo Stance [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "sumo_stance_ready",
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Sumo Stance [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Sumo Stance readies a shove on the next melee hit.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("flare boost [errata]")
def _flare_boost_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Flare Boost [Errata]"):
        return
    if not (ctx.attacker.has_status("Burned") or ctx.attacker.has_status("Burn")):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Flare Boost [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Flare Boost requires being Burned.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=3,
        effect="flare_boost_errata",
        description="Flare Boost raises Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=3,
        effect="flare_boost_errata",
        description="Flare Boost raises Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Flare Boost [Errata]",
            "move": ctx.move.name,
            "effect": "buff",
            "description": "Flare Boost empowers the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("toxic boost [errata]")
def _toxic_boost_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Toxic Boost [Errata]"):
        return
    if not (ctx.attacker.has_status("Poisoned") or ctx.attacker.has_status("Badly Poisoned")):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Toxic Boost [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Toxic Boost requires being Poisoned or Badly Poisoned.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="atk",
        delta=3,
        effect="toxic_boost_errata",
        description="Toxic Boost raises Attack.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=3,
        effect="toxic_boost_errata",
        description="Toxic Boost raises Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Toxic Boost [Errata]",
            "move": ctx.move.name,
            "effect": "buff",
            "description": "Toxic Boost empowers the user.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("transporter [errata]")
def _transporter_errata_action(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Transporter [Errata]"):
        return
    ctx.attacker.add_temporary_effect(
        "transporter_ready",
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Transporter [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Transporter empowers the next Teleport.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("ambush [errata]")
def _ambush_errata_ready(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Ambush [Errata]"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("ambush_errata_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Ambush [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Ambush [Errata] can only be used once per scene.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("ambush_errata_used", count=used_count + 1)
    else:
        used_entry["count"] = used_count + 1
    ctx.attacker.add_temporary_effect("ambush_errata_ready", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Ambush [Errata]",
            "move": ctx.move.name,
            "effect": "ready",
            "description": "Ambush [Errata] readies a priority strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("arena trap [errata]")
def _arena_trap_errata_toggle(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Arena Trap [Errata]"):
        return
    active_entry = next(iter(ctx.attacker.get_temporary_effects("arena_trap_errata_active")), None)
    if active_entry is None:
        ctx.attacker.add_temporary_effect("arena_trap_errata_active")
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Arena Trap [Errata]",
                "move": ctx.move.name,
                "effect": "activate",
                "description": "Arena Trap [Errata] activates.",
                "target_hp": ctx.attacker.hp,
            }
        )
    else:
        ctx.attacker.remove_temporary_effect("arena_trap_errata_active")
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Arena Trap [Errata]",
                "move": ctx.move.name,
                "effect": "end",
                "description": "Arena Trap [Errata] ends.",
                "target_hp": ctx.attacker.hp,
            }
        )


@register_move_special("aura break [errata]")
def _aura_break_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Aura Break [Errata]"):
        return
    if ctx.defender is None or ctx.defender_id is None:
        return
    choice_entry = next(iter(ctx.attacker.get_temporary_effects("aura_break_choice")), None)
    choice = None
    if isinstance(choice_entry, dict):
        choice = str(choice_entry.get("ability") or choice_entry.get("choice") or "").strip()
    if choice_entry is not None:
        ctx.attacker.remove_temporary_effect("aura_break_choice")
    if not choice:
        abilities = ctx.defender.ability_names()
        choice = abilities[0] if abilities else ""
    if not choice:
        return
    ctx.defender.add_temporary_effect(
        "aura_break_errata",
        ability=choice,
        source_id=ctx.attacker_id,
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Aura Break [Errata]",
            "move": ctx.move.name,
            "effect": "invert",
            "chosen": choice,
            "description": "Aura Break [Errata] inverts the target's damage bonuses.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("bad dreams [errata]")
def _bad_dreams_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Bad Dreams [Errata]"):
        return
    if ctx.attacker.position is None:
        return
    slept = False
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or mon.hp is None or mon.hp <= 0:
            continue
        if mon.position is None:
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 5:
            continue
        if not (mon.has_status("Sleep") or mon.has_status("Asleep")):
            continue
        amount = mon._apply_tick_damage(1)
        if amount > 0:
            slept = True
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Bad Dreams [Errata]",
                "move": ctx.move.name,
                "effect": "tick",
                "amount": amount,
                "description": "Bad Dreams [Errata] drains sleeping targets.",
                "target_hp": mon.hp,
            }
        )
    if slept:
        gained = ctx.attacker.add_temp_hp(ctx.attacker.tick_value())
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Bad Dreams [Errata]",
                "move": ctx.move.name,
                "effect": "temp_hp",
                "amount": gained,
                "description": "Bad Dreams [Errata] grants temporary hit points.",
                "target_hp": ctx.attacker.hp,
            }
        )


@register_move_special("beautiful [errata]")
def _beautiful_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Beautiful [Errata]"):
        return
    choice_entry = next(iter(ctx.attacker.get_temporary_effects("beautiful_choice")), None)
    choice = ""
    if isinstance(choice_entry, dict):
        choice = str(choice_entry.get("choice") or "").strip().lower()
    if choice_entry is not None:
        ctx.attacker.remove_temporary_effect("beautiful_choice")
    if choice == "contest":
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Beautiful [Errata]",
                "move": ctx.move.name,
                "effect": "contest",
                "description": "Beautiful [Errata] grants beauty dice.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        stat="spatk",
        delta=1,
        effect="beautiful_errata",
        description="Beautiful [Errata] boosts Special Attack.",
    )
    if ctx.attacker.position is not None:
        for pid, mon in ctx.battle.pokemon.items():
            if mon.fainted or not mon.active:
                continue
            if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
                continue
            if mon.position is None:
                continue
            if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 5:
                continue
            if mon.remove_status_by_names({"enraged"}):
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.attacker_id,
                        "target": pid,
                        "ability": "Beautiful [Errata]",
                        "move": ctx.move.name,
                        "effect": "cure_enraged",
                        "description": "Beautiful [Errata] cures Enraged.",
                        "target_hp": mon.hp,
                    }
                )


def _move_specials_registry_loaded() -> bool:
    return _MOVE_SPECIALS_INITIALIZED
