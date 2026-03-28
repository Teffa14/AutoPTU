"""Core accuracy and damage calculations for PTU battles."""
from __future__ import annotations

import collections
import enum
import math
from . import targeting
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

from .. import ptu_engine
from ..data_models import MoveSpec
from .move_traits import move_has_crash_trait, move_has_punch_trait, recoil_fraction, move_has_keyword
from .abilities.ability_variants import has_ability_exact
from .abilities.constants import COLOR_THEORY_STAT_KEYS

if TYPE_CHECKING:
    from .battle_state import PokemonState

STAGE_MIN = -6
STAGE_MAX = 6
_ACE_FEATURE_BY_STAT = {
    "atk": "Attack Ace",
    "def": "Defense Ace",
    "spatk": "Special Attack Ace",
    "spdef": "Special Defense Ace",
    "spd": "Speed Ace",
}
_STAT_ACE_VALUE_ALIASES = {
    "attack": "atk",
    "atk": "atk",
    "defense": "def",
    "def": "def",
    "special attack": "spatk",
    "special_attack": "spatk",
    "special-attack": "spatk",
    "spatk": "spatk",
    "special defense": "spdef",
    "special_defense": "spdef",
    "special-defense": "spdef",
    "spdef": "spdef",
    "speed": "spd",
    "spd": "spd",
}

WEATHER_DB_MODIFIERS: Dict[str, Dict[str, int]] = {
    "rain": {"electric": 1, "water": 1, "fire": -1},
    "storm": {"electric": 1, "water": 1, "fire": -1},
    "downpour": {"electric": 1, "water": 1, "fire": -1},
    "sun": {"fire": 1, "water": -1},
    "sunny": {"fire": 1, "water": -1},
    "harsh sunlight": {"fire": 1, "water": -1},
    "hail": {"ice": 1},
    "sandstorm": {"rock": 1},
}
_ALWAYS_HIT_MOVES: Set[str] = {"false surrender", "feint attack", "future sight"}
_STRONG_JAW_MOVES: Set[str] = {
    "bite",
    "bug bite",
    "crunch",
    "fire fang",
    "hyper fang",
    "ice fang",
    "jaw lock",
    "poison fang",
    "psychic fangs",
    "super fang",
    "thunder fang",
}

def clamp_stage(value: int) -> int:
    return max(STAGE_MIN, min(STAGE_MAX, value))


def stage_multiplier(stage: int) -> float:
    stage = clamp_stage(stage)
    if stage >= 0:
        return (2 + stage) / 2
    return 2 / (2 - stage)


def accuracy_stage_value(stage: int) -> int:
    """Accuracy stages add a flat bonus to accuracy rolls."""
    return clamp_stage(stage)


def _temporary_stat_modifier(pokemon: PokemonState, stat: str) -> int:
    total = 0
    if not stat:
        return total
    for entry in pokemon.get_temporary_effects("color_theory"):
        color = str(entry.get("color") or "").strip()
        if not color:
            continue
        parts = [segment.strip().title() for segment in color.split("-") if segment.strip()]
        if not parts:
            continue
        matched = [COLOR_THEORY_STAT_KEYS.get(part, "") for part in parts]
        if stat not in matched:
            continue
        total += 6 if len(parts) == 1 else 3
    for entry in pokemon.get_temporary_effects("stat_modifier"):
        if entry.get("stat") != stat:
            continue
        try:
            total += int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
    battle = getattr(pokemon, "battle", None)
    if battle is None or not getattr(battle, "_magic_room_active", lambda: False)():
        from .battle_state import _item_entry_for
        from .item_effects import parse_item_effects

        for item in getattr(pokemon.spec, "items", []) or []:
            entry = _item_entry_for(item)
            if entry is None:
                continue
            effects = parse_item_effects(entry)
            for effect_stat, amount in effects.get("base_stat_changes", []):
                if effect_stat != stat:
                    continue
                try:
                    total += int(amount or 0)
                except (TypeError, ValueError):
                    continue
    return total


def _normalized_stat_ace_value(value: object) -> str:
    return _STAT_ACE_VALUE_ALIASES.get(str(value or "").strip().lower(), "")


def _trainer_stat_ace_bonus(pokemon: PokemonState, stat: str) -> int:
    if not stat:
        return 0
    feature_name = _ACE_FEATURE_BY_STAT.get(stat, "")
    has_bonus = bool(feature_name and pokemon.has_trainer_feature(feature_name))
    if not has_bonus:
        for entry in getattr(pokemon.spec, "trainer_features", []) or []:
            if not isinstance(entry, dict):
                continue
            entry_name = str(
                entry.get("name") or entry.get("feature_id") or entry.get("id") or ""
            ).strip().lower()
            if entry_name != "stat ace":
                continue
            chosen = (
                entry.get("chosen_stat")
                or entry.get("stat")
                or entry.get("chosen_base_stat")
                or entry.get("selected_stat")
            )
            if _normalized_stat_ace_value(chosen) == stat:
                has_bonus = True
                break
    if not has_bonus:
        return 0
    try:
        level = int(getattr(pokemon.spec, "level", 0) or 0)
    except (TypeError, ValueError):
        level = 0
    return 1 + max(0, level // 10)


def _temporary_stat_scalar(pokemon: PokemonState, stat: str) -> float:
    multiplier = 1.0
    if not stat:
        return multiplier
    if stat == "atk" and pokemon.has_ability("Huge Power") and not has_ability_exact(
        pokemon, "Huge Power [Errata]"
    ):
        multiplier *= 2.0
    if stat == "atk" and pokemon.has_ability("Pure Power") and not has_ability_exact(
        pokemon, "Pure Power [Errata]"
    ):
        multiplier *= 2.0
    for entry in pokemon.get_temporary_effects("stat_scalar"):
        if entry.get("stat") != stat:
            continue
        try:
            multiplier *= float(entry.get("multiplier", 1.0) or 1.0)
        except (TypeError, ValueError):
            continue
    battle = getattr(pokemon, "battle", None)
    if battle is None or not getattr(battle, "_magic_room_active", lambda: False)():
        from .battle_state import _item_entry_for
        from .item_effects import parse_item_effects

        for item in getattr(pokemon.spec, "items", []) or []:
            entry = _item_entry_for(item)
            if entry is None:
                continue
            effects = parse_item_effects(entry)
            for effect_stat, value in effects.get("base_stat_scalars", []):
                if effect_stat != stat:
                    continue
                try:
                    multiplier *= float(value or 1.0)
                except (TypeError, ValueError):
                    continue
            for effect_stat, value in effects.get("stat_scalars", []):
                if effect_stat != stat:
                    continue
                try:
                    multiplier *= float(value or 1.0)
                except (TypeError, ValueError):
                    continue
    return multiplier


def _post_stage_stat_bonus(pokemon: PokemonState, stat: str) -> int:
    bonus = 0
    for entry in pokemon.get_temporary_effects("post_stage_stat_bonus"):
        if entry.get("stat") != stat:
            continue
        try:
            bonus += int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
    battle = getattr(pokemon, "battle", None)
    if battle is None or not getattr(battle, "_magic_room_active", lambda: False)():
        from .battle_state import _item_entry_for
        from .item_effects import parse_item_effects

        for item in getattr(pokemon.spec, "items", []) or []:
            entry = _item_entry_for(item)
            if entry is None:
                continue
            effects = parse_item_effects(entry)
            for effect_stat, amount in effects.get("post_stage_stat_bonus", []):
                if effect_stat != stat:
                    continue
                try:
                    bonus += int(amount or 0)
                except (TypeError, ValueError):
                    continue
            if not isinstance(item, dict):
                continue
            normalized_name = str(item.get("name") or "").strip().lower()
            if normalized_name != "eviolite":
                continue
            chosen_stats = item.get("chosen_stats")
            if not isinstance(chosen_stats, list):
                continue
            normalized = {
                str(value or "").strip().lower()
                for value in chosen_stats
                if str(value or "").strip()
            }
            if stat in normalized:
                bonus += 5
    return bonus


def _errata_attack_bonus(pokemon: PokemonState) -> int:
    if not (
        has_ability_exact(pokemon, "Huge Power [Errata]")
        or has_ability_exact(pokemon, "Pure Power [Errata]")
    ):
        return 0
    try:
        level = int(getattr(pokemon.spec, "level", 0) or 0)
    except (TypeError, ValueError):
        level = 0
    return 5 + max(0, level // 10)


def _temporary_accuracy_bonus(
    attacker: PokemonState, defender: PokemonState, move: MoveSpec
) -> int:
    bonus = 0
    if attacker.has_ability("Compound Eyes"):
        bonus += 3
    if attacker.has_ability("Keen Eye"):
        bonus += 1
    if has_ability_exact(attacker, "No Guard [Errata]"):
        bonus += 3
    if has_ability_exact(defender, "No Guard [Errata]"):
        bonus += 3
    if has_ability_exact(attacker, "Hustle [Errata]"):
        bonus -= 2
    elif (move.category or "").strip().lower() == "physical" and attacker.has_ability("Hustle"):
        bonus -= 2
    if has_ability_exact(attacker, "Frisk [SuMo Errata]"):
        if attacker.position is not None and defender.position is not None:
            if targeting.chebyshev_distance(attacker.position, defender.position) <= 1:
                bonus += 2
    if has_ability_exact(attacker, "Bone Wielder") and attacker.has_item_named("Thick Club"):
        move_name = (move.name or "").strip().lower()
        if move_name in {"bone club", "bonemerang", "bone rush"}:
            bonus += 1
    if attacker.has_ability("Shell Cannon") and attacker.get_temporary_effects("shell_cannon_ready"):
        move_name = (move.name or "").strip().lower()
        if move_name in {
            "aqua jet",
            "dive",
            "flash cannon",
            "hydro cannon",
            "hydro pump",
            "tackle",
            "waterfall",
            "water gun",
            "water spout",
        }:
            bonus += 2
    move_type = (move.type or "").strip().lower()
    for entry in attacker.get_temporary_effects("accuracy_bonus"):
        entry_type = str(entry.get("type") or "").strip().lower()
        if entry_type and entry_type != move_type:
            continue
        try:
            bonus += int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
    for entry in attacker.get_temporary_effects("accuracy_bonus_vs_lower_av"):
        entry_type = str(entry.get("type") or "").strip().lower()
        if entry_type and entry_type != move_type:
            continue
        try:
            amount = int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        if evasion_value(defender, move.category) < evasion_value(attacker, move.category):
            bonus += amount
    return bonus


def defender_gender(attacker: PokemonState, defender: PokemonState) -> bool:
    try:
        attacker_gender = attacker.gender()
    except Exception:
        attacker_gender = "unknown"
    try:
        defender_gender = defender.gender()
    except Exception:
        defender_gender = "unknown"
    if attacker_gender not in {"male", "female"}:
        return False
    return attacker_gender == defender_gender


def _temporary_evasion_bonus(pokemon: PokemonState, category: str) -> int:
    bonus = 0
    normalized = category.lower()
    for entry in pokemon.get_temporary_effects("evasion_bonus"):
        scope = str(entry.get("scope") or "").strip().lower()
        if scope and scope != normalized and scope != "all":
            continue
        try:
            bonus += int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
    return bonus


def offensive_stat(
    pokemon: PokemonState,
    category: str,
    *,
    ignore_positive_stage: bool = False,
) -> int:
    category = category.lower()
    if category == "physical":
        base = pokemon.spec.atk
        stage = pokemon.combat_stages["atk"]
        modifier_stat = "atk"
        if pokemon.has_status("Power Shift") or pokemon.has_status("Power Trick"):
            base = pokemon.spec.defense
            stage = pokemon.combat_stages["def"]
            modifier_stat = "def"
        if modifier_stat == "def" and has_ability_exact(pokemon, "Heavy Metal [Errata]"):
            base += 2
        if modifier_stat == "def" and has_ability_exact(pokemon, "Light Metal [Errata]"):
            base = max(1, base - 2)
        if modifier_stat == "atk":
            base += _errata_attack_bonus(pokemon)
    else:
        base = pokemon.spec.spatk
        stage = pokemon.combat_stages["spatk"]
        modifier_stat = "spatk"
        if pokemon.has_status("Power Shift"):
            base = pokemon.spec.spdef
            stage = pokemon.combat_stages["spdef"]
            modifier_stat = "spdef"
        if has_ability_exact(pokemon, "Flare Boost") and (
            pokemon.has_status("Burned") or pokemon.has_status("Burn")
        ):
            stage = min(6, stage + 2)
    base = max(1, base + _trainer_stat_ace_bonus(pokemon, modifier_stat) + _temporary_stat_modifier(pokemon, modifier_stat))
    base = int(math.floor(base * _temporary_stat_scalar(pokemon, modifier_stat)))
    if ignore_positive_stage and stage > 0:
        stage = 0
    return int(math.floor(base * stage_multiplier(stage))) + _post_stage_stat_bonus(pokemon, modifier_stat)


def defensive_stat(
    pokemon: PokemonState,
    category: str,
    *,
    ignore_positive_stage: bool = False,
) -> int:
    category = category.lower()
    wonder_room_active = pokemon.has_status("Wonder Room") or pokemon.has_status("Wondered")
    if category == "physical":
        if wonder_room_active:
            base = pokemon.spec.spdef
            stage = pokemon.combat_stages["spdef"]
            modifier_stat = "spdef"
        else:
            base = pokemon.spec.defense
            stage = pokemon.combat_stages["def"]
            modifier_stat = "def"
        if pokemon.has_status("Power Shift") or pokemon.has_status("Power Trick"):
            base = pokemon.spec.atk
            stage = pokemon.combat_stages["atk"]
            modifier_stat = "atk"
        if modifier_stat == "def" and has_ability_exact(pokemon, "Heavy Metal [Errata]"):
            base += 2
        if modifier_stat == "def" and has_ability_exact(pokemon, "Light Metal [Errata]"):
            base = max(1, base - 2)
        if modifier_stat == "atk":
            base += _errata_attack_bonus(pokemon)
        base = max(1, base + _trainer_stat_ace_bonus(pokemon, modifier_stat) + _temporary_stat_modifier(pokemon, modifier_stat))
        base = int(math.floor(base * _temporary_stat_scalar(pokemon, modifier_stat)))
        if pokemon.has_status("Burned") or pokemon.has_status("Burn"):
            stage -= 2
    else:
        if wonder_room_active:
            base = pokemon.spec.defense
            stage = pokemon.combat_stages["def"]
            modifier_stat = "def"
        else:
            base = pokemon.spec.spdef
            stage = pokemon.combat_stages["spdef"]
            modifier_stat = "spdef"
        if pokemon.has_status("Power Shift"):
            base = pokemon.spec.spatk
            stage = pokemon.combat_stages["spatk"]
            modifier_stat = "spatk"
        if modifier_stat == "def" and has_ability_exact(pokemon, "Heavy Metal [Errata]"):
            base += 2
        base = max(1, base + _trainer_stat_ace_bonus(pokemon, modifier_stat) + _temporary_stat_modifier(pokemon, modifier_stat))
        base = int(math.floor(base * _temporary_stat_scalar(pokemon, modifier_stat)))
        if (
            pokemon.has_status("Poisoned")
            or pokemon.has_status("Badly Poisoned")
            or pokemon.has_status("Poison")
        ):
            stage -= 2
    if ignore_positive_stage and stage > 0:
        stage = 0
    return int(math.floor(base * stage_multiplier(stage))) + _post_stage_stat_bonus(pokemon, modifier_stat)


def speed_stat(pokemon: PokemonState) -> int:
    base = pokemon.spec.spd
    stage = pokemon.combat_stages.get("spd", 0)
    quick_feet_active = pokemon.has_ability("Quick Feet") and any(
        pokemon.has_status(name)
        for name in ("Poisoned", "Badly Poisoned", "Burned", "Paralyzed", "Frozen", "Sleep", "Asleep")
    )
    if quick_feet_active:
        stage += 2
    if has_ability_exact(pokemon, "Heavy Metal [Errata]"):
        base = max(1, base - 2)
    if has_ability_exact(pokemon, "Light Metal [Errata]"):
        base = max(1, base + 2)
    base = max(1, base + _trainer_stat_ace_bonus(pokemon, "spd") + _temporary_stat_modifier(pokemon, "spd"))
    base = int(math.floor(base * _temporary_stat_scalar(pokemon, "spd")))
    if (pokemon.has_status("Paralyzed") or pokemon.has_status("Paralyze")) and not quick_feet_active:
        stage -= 4
    return int(math.floor(base * stage_multiplier(stage))) + _post_stage_stat_bonus(pokemon, "spd")


def evasion_value(pokemon: PokemonState, category: str, *, ignore_non_stat: bool = False) -> int:
    no_bonus = (
        pokemon.has_status("Frozen")
        or pokemon.has_status("Freeze")
        or pokemon.has_status("Sleep")
        or pokemon.has_status("Asleep")
    )
    tangled_bonus = 3 if pokemon.has_ability("Tangled Feet") and (
        pokemon.has_status("Confused") or pokemon.has_status("Confusion")
    ) else 0
    instinct_bonus = 2 if pokemon.has_ability("Instinct") else 0
    perception_bonus = 1 if has_ability_exact(pokemon, "Perception [Errata]") else 0
    sand_veil_bonus = 1 if has_ability_exact(pokemon, "Sand Veil [Errata]") else 0
    bonus = 0
    base = 0
    if category.lower() == "physical":
        bonus = (
            pokemon.spec.evasion_phys
            + _temporary_evasion_bonus(pokemon, "physical")
            + instinct_bonus
            + tangled_bonus
            + perception_bonus
            + sand_veil_bonus
            + pokemon.hardened_evasion_bonus(getattr(pokemon, "battle", None))
        )
        if no_bonus:
            bonus = min(0, bonus)
        stat_base = pokemon.spec.defense
        if has_ability_exact(pokemon, "Heavy Metal [Errata]"):
            stat_base += 2
        if has_ability_exact(pokemon, "Light Metal [Errata]"):
            stat_base = max(1, stat_base - 2)
        stat_base += _trainer_stat_ace_bonus(pokemon, "def") + _temporary_stat_modifier(pokemon, "def")
        stat_base = int(math.floor(stat_base * _temporary_stat_scalar(pokemon, "def")))
        base = stat_base // 5
    elif category.lower() == "special":
        bonus = (
            pokemon.spec.evasion_spec
            + _temporary_evasion_bonus(pokemon, "special")
            + instinct_bonus
            + tangled_bonus
            + perception_bonus
            + sand_veil_bonus
            + pokemon.hardened_evasion_bonus(getattr(pokemon, "battle", None))
        )
        if no_bonus:
            bonus = min(0, bonus)
        stat_base = pokemon.spec.spdef + _trainer_stat_ace_bonus(pokemon, "spdef") + _temporary_stat_modifier(pokemon, "spdef")
        stat_base = int(math.floor(stat_base * _temporary_stat_scalar(pokemon, "spdef")))
        base = stat_base // 5
    else:
        bonus = (
            pokemon.spec.evasion_spd
            + _temporary_evasion_bonus(pokemon, "status")
            + instinct_bonus
            + tangled_bonus
            + perception_bonus
            + pokemon.hardened_evasion_bonus(getattr(pokemon, "battle", None))
        )
        if no_bonus:
            bonus = min(0, bonus)
        stat_base = pokemon.spec.spd
        if has_ability_exact(pokemon, "Heavy Metal [Errata]"):
            stat_base = max(1, stat_base - 2)
        if has_ability_exact(pokemon, "Light Metal [Errata]"):
            stat_base = max(1, stat_base + 2)
        stat_base += _trainer_stat_ace_bonus(pokemon, "spd") + _temporary_stat_modifier(pokemon, "spd")
        stat_base = int(math.floor(stat_base * _temporary_stat_scalar(pokemon, "spd")))
        base = stat_base // 5
    stage = pokemon.combat_stages["spd"] if category.lower() == "status" else 0
    if category.lower() == "status" and (
        pokemon.has_status("Paralyzed") or pokemon.has_status("Paralyze")
    ):
        stage -= 4
    if ignore_non_stat:
        bonus = 0
    return base + bonus + stage


def evasion_value_for_attack(attacker: PokemonState, defender: PokemonState, category: str) -> int:
    return evasion_value(defender, category, ignore_non_stat=attacker.has_ability("Keen Eye"))


def attack_hits(
    rng: random.Random,
    attacker: PokemonState,
    defender: PokemonState,
    move: MoveSpec,
) -> Dict[str, object]:
    move_name = (move.name or "").strip().lower()
    roll = rng.randint(1, 20)
    def _apply_merciless(result: Dict[str, object]) -> Dict[str, object]:
        if (
            result.get("hit")
            and attacker.has_ability("Merciless")
            and (
                defender.has_status("Poisoned")
                or defender.has_status("Badly Poisoned")
                or defender.has_status("Poison")
            )
        ):
            result["crit"] = True
        return result
    if move_name == "hypnosis" and attacker.has_ability("Hypnotic"):
        return _apply_merciless(
            {
            "hit": True,
            "crit": False,
            "roll": roll,
            "needed": move.ac or 1,
        }
        )
    melee_no_guard = (
        targeting.normalized_target_kind(move) == "melee"
        and (attacker.has_ability("No Guard") or defender.has_ability("No Guard"))
    )
    if move.ac is None:
        if defender.has_ability("Blur") or (
            getattr(defender, "is_trainer_combatant", None)
            and defender.is_trainer_combatant()
            and getattr(defender, "has_trainer_feature", None)
            and defender.has_trainer_feature("Blur")
        ):
            evasion = int(math.floor(evasion_value(defender, move.category) / 2))
            accuracy_bonus = _temporary_accuracy_bonus(attacker, defender, move)
            accuracy_stage = accuracy_stage_value(
                attacker.combat_stages.get("accuracy", 0)
                + attacker.spec.accuracy_cs
                + accuracy_bonus
            )
            needed = max(2, 2 + evasion - accuracy_stage)
            if roll == 1:
                if attacker.get_temporary_effects("probability_control"):
                    reroll = rng.randint(1, 20)
                    attacker.remove_temporary_effect("probability_control")
                    if reroll == 20 or reroll >= needed:
                        crit_threshold = move.crit_range or 20
                        return _apply_merciless(
                            {
                            "hit": True,
                            "crit": reroll >= crit_threshold,
                            "roll": reroll,
                            "needed": needed,
                        }
                        )
                    return _apply_merciless({"hit": False, "crit": False, "roll": reroll, "needed": needed})
                return _apply_merciless({"hit": False, "crit": False, "roll": roll, "needed": needed})
            if roll == 20 or roll >= needed:
                crit_threshold = move.crit_range or 20
                return _apply_merciless(
                    {"hit": True, "crit": roll >= crit_threshold, "roll": roll, "needed": needed}
                )
            if attacker.get_temporary_effects("probability_control"):
                reroll = rng.randint(1, 20)
                attacker.remove_temporary_effect("probability_control")
                if reroll == 20 or reroll >= needed:
                    crit_threshold = move.crit_range or 20
                    return _apply_merciless(
                        {"hit": True, "crit": reroll >= crit_threshold, "roll": reroll, "needed": needed}
                    )
                return _apply_merciless({"hit": False, "crit": False, "roll": reroll, "needed": needed})
            return _apply_merciless({"hit": False, "crit": False, "roll": roll, "needed": needed})
        return _apply_merciless(
            {"hit": True, "crit": roll >= (move.crit_range or 20), "roll": roll, "needed": 1}
        )
    evasion = 0 if melee_no_guard else evasion_value(defender, move.category)
    accuracy_bonus = _temporary_accuracy_bonus(attacker, defender, move)
    accuracy_stage = accuracy_stage_value(
        attacker.combat_stages.get("accuracy", 0) + attacker.spec.accuracy_cs + accuracy_bonus
    )
    needed = max(2, move.ac + evasion - accuracy_stage)
    if roll == 1:
        if attacker.get_temporary_effects("probability_control"):
            reroll = rng.randint(1, 20)
            attacker.remove_temporary_effect("probability_control")
            if reroll == 20 or reroll >= needed:
                crit_threshold = move.crit_range or 20
                return _apply_merciless(
                    {"hit": True, "crit": reroll >= crit_threshold, "roll": reroll, "needed": needed}
                )
            return _apply_merciless({"hit": False, "crit": False, "roll": reroll, "needed": needed})
        return _apply_merciless({"hit": False, "crit": False, "roll": roll, "needed": needed})
    if roll == 20 or roll >= needed:
        crit_threshold = move.crit_range or 20
        return _apply_merciless(
            {"hit": True, "crit": roll >= crit_threshold, "roll": roll, "needed": needed}
        )
    if attacker.get_temporary_effects("probability_control"):
        reroll = rng.randint(1, 20)
        attacker.remove_temporary_effect("probability_control")
        if reroll == 20 or reroll >= needed:
            crit_threshold = move.crit_range or 20
            return _apply_merciless(
                {"hit": True, "crit": reroll >= crit_threshold, "roll": reroll, "needed": needed}
            )
        return _apply_merciless({"hit": False, "crit": False, "roll": reroll, "needed": needed})
    return _apply_merciless({"hit": False, "crit": False, "roll": roll, "needed": needed})


def hit_probability(attacker: PokemonState, defender: PokemonState, move: MoveSpec) -> float:
    if move.ac is None:
        return 1.0
    melee_no_guard = (
        targeting.normalized_target_kind(move) == "melee"
        and (attacker.has_ability("No Guard") or defender.has_ability("No Guard"))
    )
    evasion = 0 if melee_no_guard else evasion_value(defender, move.category)
    accuracy_bonus = _temporary_accuracy_bonus(attacker, defender, move)
    accuracy_stage = accuracy_stage_value(
        attacker.combat_stages.get("accuracy", 0) + attacker.spec.accuracy_cs + accuracy_bonus
    )
    needed = max(2, move.ac + evasion - accuracy_stage)
    if needed <= 2:
        return 0.95
    if needed > 20:
        return 1.0 / 20.0
    success_faces = max(0, 21 - needed)
    probability = success_faces / 20.0
    return max(0.0, min(0.95, probability))


def crit_probability(move: MoveSpec, hit_chance: float) -> float:
    threshold = move.crit_range or 20
    success_faces = max(0, 21 - threshold)
    probability = success_faces / 20.0
    return min(probability, hit_chance)


class ModifierTiming(str, enum.Enum):
    PRE_ACCURACY = "pre_accuracy"
    POST_ACCURACY = "post_accuracy"
    PRE_DAMAGE = "pre_damage"
    POST_DAMAGE = "post_damage"


@dataclass
class AttackModifier:
    slug: str
    kind: str
    value: float
    timing: ModifierTiming = ModifierTiming.PRE_DAMAGE
    source: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "slug": self.slug,
            "kind": self.kind,
            "value": self.value,
            "timing": self.timing.value,
            "source": self.source,
        }


@dataclass
class AttackContext:
    attacker: "PokemonState"
    defender: "PokemonState"
    move: MoveSpec
    weather: Optional[str] = None
    terrain: Optional[dict] = None
    domains: Set[str] = field(default_factory=set)
    roll_options: Set[str] = field(default_factory=set)
    modifiers: List[AttackModifier] = field(default_factory=list)

    def add_domain(self, *labels: str) -> None:
        for label in labels:
            if label:
                self.domains.add(label.strip().lower())

    def add_roll_option(self, *labels: str) -> None:
        for label in labels:
            if label:
                self.roll_options.add(label.strip().lower())

    def add_modifier(
        self,
        slug: str,
        kind: str,
        value: float,
        *,
        timing: ModifierTiming = ModifierTiming.PRE_DAMAGE,
        source: str = "",
    ) -> None:
        self.modifiers.append(
            AttackModifier(slug=slug, kind=kind, value=value, timing=timing, source=source)
        )

    def summary(self) -> Dict[str, object]:
        return {
            "domains": sorted(self.domains),
            "roll_options": sorted(self.roll_options),
            "modifiers": [mod.as_dict() for mod in self.modifiers],
        }


def build_attack_context(
    attacker: "PokemonState",
    defender: "PokemonState",
    move: MoveSpec,
    *,
    weather: Optional[str] = None,
    terrain: Optional[dict] = None,
) -> AttackContext:
    """Create an AttackContext mirroring Foundry's AttackStatistic setup."""
    context = AttackContext(
        attacker=attacker,
        defender=defender,
        move=move,
        weather=weather,
        terrain=terrain,
    )
    if attacker.has_ability("Water Bubble"):
        current_weather = (context.weather or "").strip().lower()
        if "rain" not in current_weather and "storm" not in current_weather and "downpour" not in current_weather:
            context.weather = "Rain"
    _seed_domains(context)
    _seed_roll_options(context)
    _seed_status_domains(context)
    _seed_weather(context)
    _seed_builtin_modifiers(context)
    return context


def resolve_move_action(
    rng: random.Random,
    attacker: PokemonState,
    defender: PokemonState,
    move: MoveSpec,
    weather: str | None = None,
    terrain: dict | None = None,
    *,
    context: AttackContext | None = None,
    force_hit: bool = False,
    ignore_defender_abilities: bool = False,
    present_roll_override: int | None = None,
) -> Dict[str, object]:
    if context is None:
        context = build_attack_context(attacker, defender, move, weather=weather, terrain=terrain)
    move_name = (move.name or "").strip().lower()
    guaranteed_hit = move_name in _ALWAYS_HIT_MOVES
    is_dragon_rage = move_name == "dragon rage"
    is_sonic_boom = move_name in {"sonic boom", "sonicboom"}
    water_bubble_bonus = 0
    present_roll = None
    present_db = None
    present_heal = False
    if move_name == "present":
        if present_roll_override in {1, 2, 3, 4, 5, 6}:
            present_roll = int(present_roll_override)
        else:
            next_value = None
            if hasattr(rng, "_values"):
                values = getattr(rng, "_values", None)
                if isinstance(values, list):
                    if values:
                        next_value = values[0]
                elif isinstance(values, collections.deque):
                    if values:
                        next_value = values[0]
            if next_value is not None and 1 <= int(next_value) <= 6:
                present_roll = rng.randint(1, 6)
    if force_hit:
        accuracy = {"hit": True, "crit": False, "roll": None}
        if move.ac is not None:
            accuracy["needed"] = move.ac
    else:
        accuracy = attack_hits(rng, attacker, defender, move)
    if move_name == "blizzard":
        weather_name = (weather or "").strip().lower()
        if weather_name in {"hail", "hailing"} and not force_hit:
            accuracy = {**accuracy, "hit": True}
    if move_name == "hurricane":
        weather_name = (weather or "").strip().lower()
        if weather_name in {"rain", "rainy", "storm", "downpour"} and not force_hit:
            accuracy = {**accuracy, "hit": True}
        elif weather_name in {"sun", "sunny", "harsh sunlight"} and accuracy.get("roll") is not None:
            roll_value = int(accuracy.get("roll") or 0)
            accuracy = {**accuracy, "needed": 11, "hit": roll_value >= 11}
        for entry in defender.get_temporary_effects("semi_invulnerable"):
            if str(entry.get("mode") or "").strip().lower() == "airborne":
                accuracy = {**accuracy, "hit": True}
                break
    if move_name == "frost breath" and accuracy.get("hit"):
        accuracy = {**accuracy, "crit": True}
    if move_name == "wicked blow" and accuracy.get("hit"):
        accuracy = {**accuracy, "crit": True}
    if move_name == "aeroblast":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value % 2 == 0 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "air cutter":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "attack order":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "night slash":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "crabhammer":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "spacial rend":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value % 2 == 0 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "snipe shot":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "shadow claw":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "cross chop":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 16 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "cross poison":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "poison tail":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if (
        accuracy.get("hit")
        and attacker.has_ability("Merciless")
        and (defender.has_status("Poisoned") or defender.has_status("Badly Poisoned"))
    ):
        accuracy = {**accuracy, "crit": True}
    if move_name == "razor leaf":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "razor wind":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "esper wing":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "drill run":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "deadly strike" and accuracy.get("hit"):
        accuracy = {**accuracy, "crit": True}
    if accuracy.get("crit") and (defender.has_status("Curled Up") or defender.has_status("Withdrawn")):
        accuracy = {**accuracy, "crit": False}
    if move_name == "bullseye":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 16 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "ceaseless edge":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 19 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "psycho cut":
        roll_value = accuracy.get("roll")
        if roll_value is not None and roll_value >= 18 and accuracy.get("hit"):
            accuracy = {**accuracy, "crit": True}
    if move_name == "present" and present_roll is None:
        present_roll = rng.randint(1, 6)
    if move_name == "present":
        present_db = int(present_roll or 0) * 2 if present_roll is not None else None
        present_heal = present_roll == 1
        move = MoveSpec(**{**move.__dict__, "db": 0 if present_heal else present_db})
        context.move = move
    terrain_name = ""
    if context.terrain and isinstance(context.terrain, dict):
        terrain_name = (context.terrain.get("name") or "").strip().lower()
    gravity_active = "gravity" in terrain_name or "warped" in terrain_name
    bone_wielder_errata = bool(
        attacker
        and has_ability_exact(attacker, "Bone Wielder [Errata]")
        and move_name in {"bone club", "bonemerang", "bone rush"}
    )
    if (
        move.type
        and move.type.lower() == "ground"
        and (defender.has_ability("Levitate") or defender.has_status("Magnet Rise"))
        and not force_hit
        and not ignore_defender_abilities
        and not gravity_active
        and not bone_wielder_errata
    ):
        return {
            **accuracy,
            "hit": False,
            "crit": False,
            "damage": 0,
            "damage_roll": 0,
            "effective_db": move.db or 0,
            "type_multiplier": 0.0,
            "db_components": (0, 0, 0),
            "immune_to": "Levitate",
            "context": context.summary(),
        }
    if move.category.lower() == "physical" and defender.has_status("Liquefied"):
        return {
            **accuracy,
            "hit": True,
            "crit": False,
            "damage": 0,
            "damage_roll": 0,
            "effective_db": move.db or 0,
            "type_multiplier": 0.0,
            "db_components": (0, 0, 0),
            "immune_to": "Liquefied",
            "context": context.summary(),
        }
    if (not accuracy["hit"]) and not force_hit:
        if not guaranteed_hit:
            return {
                "hit": False,
                "crit": False,
                "damage": 0,
                "damage_roll": 0,
                "effective_db": move.db or 0,
                "db_components": (0, 0, 0),
                **accuracy,
                "context": context.summary(),
            }
        accuracy = {**accuracy, "hit": True}
    if move.category.lower() == "status":
        return {
            "hit": bool(accuracy.get("hit")),
            "crit": False,
            "damage": 0,
            "damage_roll": 0,
            "effective_db": move.db or 0,
            "db_components": (0, 0, 0),
            **accuracy,
            "context": context.summary(),
        }

    if is_dragon_rage or is_sonic_boom:
        effective_db_value = 15
        stab_bonus = 0
        weather_bonus = 0
        n, s, p = (0, 0, 0)
        roll = 0
        crit_extra_roll = 0
        attack_value = 0
        defense_value = 0
        base_damage = 15
        type_mult = 1.0
    else:
        effective_db_value, stab_bonus, weather_bonus, _ = _effective_db_components(context, attacker)
        n, s, p = ptu_engine.db_to_dice(effective_db_value)
        roll = sum(rng.randint(1, s) for _ in range(n)) + p
        water_bubble_bonus = 0
        if attacker.has_ability("Water Bubble"):
            for entry in attacker.get_temporary_effects("water_bubble_melee"):
                entry_move = str(entry.get("move") or "").strip().lower()
                if entry_move and entry_move != move_name:
                    continue
                water_bubble_bonus = rng.randint(1, 6) + 2
                roll += water_bubble_bonus
                break
        crit_extra_roll = 0
        if accuracy["crit"]:
            crit_extra_roll = sum(rng.randint(1, s) for _ in range(n))
            roll += crit_extra_roll
            if attacker.has_ability("Sniper"):
                roll += crit_extra_roll
        ignore_defender_positive = attacker.has_ability("Unaware")
        ignore_attacker_positive = defender.has_ability("Unaware") and not attacker.has_ability("Mold Breaker")
        attack_value = offensive_stat(
            attacker,
            move.category,
            ignore_positive_stage=ignore_attacker_positive,
        )
        if move_name == "shell side arm":
            physical_attack = offensive_stat(
                attacker,
                "physical",
                ignore_positive_stage=ignore_attacker_positive,
            )
            special_attack = offensive_stat(
                attacker,
                "special",
                ignore_positive_stage=ignore_attacker_positive,
            )
            attack_value = max(physical_attack, special_attack)
        if move_name == "photon geyser":
            attack_value = max(
                offensive_stat(attacker, "physical", ignore_positive_stage=ignore_attacker_positive),
                offensive_stat(attacker, "special", ignore_positive_stage=ignore_attacker_positive),
            )
        if move_name == "foul play":
            attack_value = offensive_stat(defender, "physical")
        if (move.name or "").strip().lower() == "body press":
            attack_value = defensive_stat(
                attacker,
                "physical",
                ignore_positive_stage=ignore_attacker_positive,
            )
        defense_value = defensive_stat(
            defender,
            move.category,
            ignore_positive_stage=ignore_defender_positive,
        )
        effects_text = (move.effects_text or "").lower()
        if "calculates damage against the target's def" in effects_text:
            defense_value = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
        if move_name in {"psyshock", "psystrike"}:
            defense_value = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
        if move_name == "secret force":
            defense_value = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
        if move_name == "secret sword":
            defense_value = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
        if move_name == "shell side arm":
            physical_defense = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
            special_defense = defensive_stat(defender, "special", ignore_positive_stage=ignore_defender_positive)
            if physical_defense < special_defense:
                defense_value = physical_defense
        if move_name == "electro ball":
            attack_value += speed_stat(attacker)
            defense_value += speed_stat(defender)
        base_damage = max(0, roll + attack_value - defense_value)
        base_damage = apply_context_damage_modifiers(base_damage, context)
        type_mult = ptu_engine.type_multiplier(move.type, defender.spec.types)
        if move_name == "freeze-dry" and any(
            (t or "").strip().lower() == "water" for t in defender.spec.types
        ):
            other_types = [
                t for t in defender.spec.types if (t or "").strip().lower() != "water"
            ]
            type_mult = ptu_engine.type_multiplier(move.type, other_types) if other_types else 1.0
            type_mult *= 2.0
        if (
            type_mult == 0
            and move.type
            and move.type.lower() == "ground"
            and gravity_active
            and any((t or "").strip().lower() == "flying" for t in defender.spec.types)
        ):
            type_mult = 1.0
        if type_mult == 0 and bone_wielder_errata and move.type and move.type.lower() == "ground":
            type_mult = 1.0
        if type_mult != 0:
            normalize_attacker = has_ability_exact(attacker, "Normalize [Errata]")
            normalize_defender = (
                not ignore_defender_abilities and has_ability_exact(defender, "Normalize [Errata]")
            )
            if normalize_attacker or normalize_defender:
                type_mult = 1.0
        if type_mult == 0:
            if (
                move.type
                and move.type.lower() == "ghost"
                and any((t or "").strip().lower() == "normal" for t in defender.spec.types)
                and attacker.has_ability("Mojo")
            ):
                type_mult = 1.0
            elif (
                move.type
                and move.type.lower() in {"normal", "fighting"}
                and any((t or "").strip().lower() == "ghost" for t in defender.spec.types)
                and attacker.has_ability("Scrappy")
            ):
                type_mult = 1.0
            elif (
                move.type
                and move.type.lower() == "poison"
                and defender.get_temporary_effects("poison_immunity_suppressed")
            ):
                type_mult = 1.0
            elif (
                move.type
                and move.type.lower() in {"normal", "fighting"}
                and any((t or "").strip().lower() == "ghost" for t in defender.spec.types)
                and attacker.get_temporary_effects("foresight")
            ):
                type_mult = 1.0
            elif (
                move.type
                and move.type.lower() == "psychic"
                and any((t or "").strip().lower() == "dark" for t in defender.spec.types)
                and attacker.get_temporary_effects("miracle_eye")
            ):
                type_mult = 1.0
            else:
                result = {
                    "hit": True,
                    "crit": accuracy["crit"],
                    "damage": 0,
                    "type_multiplier": 0.0,
                    "damage_roll": roll,
                    "effective_db": effective_db_value,
                    "stab_db": stab_bonus,
                    "weather_db": weather_bonus,
                    "db_components": (n, s, p),
                    "attack_value": attack_value,
                    "defense_value": defense_value,
                    "pre_type_damage": base_damage,
                    "water_bubble_bonus": water_bubble_bonus,
                    **accuracy,
                }
                if present_roll is not None:
                    result["present_roll"] = present_roll
                    result["present_db"] = present_db
                    result["present_heal"] = present_heal
                return result
        if move_name in {"seismic toss", "night shade"}:
            level_damage = max(0, attacker.spec.level or 0)
            base_damage = level_damage
            type_mult = 1.0
            attack_value = 0
            defense_value = 0
            n = s = p = 0
            roll = 0
            crit_extra_roll = 0
            effective_db_value = 0
            stab_bonus = 0
            weather_bonus = 0
        damage = int(math.floor(base_damage * type_mult))

    if is_dragon_rage or is_sonic_boom:
        damage = 15
    result = {
        "hit": True,
        "crit": accuracy["crit"],
        "damage": damage,
        "type_multiplier": type_mult,
        "damage_roll": roll,
        "effective_db": effective_db_value,
        "stab_db": stab_bonus,
        "weather_db": weather_bonus,
        "db_components": (n, s, p),
        "attack_value": attack_value,
        "defense_value": defense_value,
        "pre_type_damage": base_damage,
        "crit_extra_roll": crit_extra_roll,
        "water_bubble_bonus": water_bubble_bonus,
        **accuracy,
        "context": context.summary(),
    }
    if present_roll is not None:
        result["present_roll"] = present_roll
        result["present_db"] = present_db
        result["present_heal"] = present_heal
    return result


def expected_damage(
    attacker: PokemonState,
    defender: PokemonState,
    move: MoveSpec,
    weather: str | None = None,
    terrain: dict | None = None,
) -> float:
    move_name = (move.name or "").strip().lower()
    attacker_level = max(0, attacker.spec.level or 0)
    if move_name == "judgement":
        candidate_types = sorted({atk for atk, _ in ptu_engine.TYPE_STEPS.keys()})
        if candidate_types:
            best_type = move.type
            best_mult = ptu_engine.type_multiplier(move.type, defender.spec.types)
            for candidate in candidate_types:
                mult = ptu_engine.type_multiplier(candidate, defender.spec.types)
                if mult > best_mult:
                    best_mult = mult
                    best_type = candidate
            if best_type != move.type:
                move = MoveSpec(**{**move.__dict__, "type": best_type})
    context = build_attack_context(attacker, defender, move, weather=weather, terrain=terrain)
    if move.category.lower() == "status":
        return 0.0
    if move_name in {"seismic toss", "night shade"}:
        return float(attacker_level)
    hit_chance = hit_probability(attacker, defender, move)
    if move_name == "blizzard":
        weather_name = (weather or "").strip().lower()
        if weather_name in {"hail", "hailing"}:
            hit_chance = 1.0
    if hit_chance <= 0:
        return 0.0
    effective_db_value, _, _, _ = _effective_db_components(context, attacker)
    n, s, p = ptu_engine.db_to_dice(effective_db_value)
    expected_roll = n * (s + 1) / 2.0 + p
    ignore_defender_positive = attacker.has_ability("Unaware")
    ignore_attacker_positive = defender.has_ability("Unaware") and not attacker.has_ability("Mold Breaker")
    attack_value = offensive_stat(
        attacker,
        move.category,
        ignore_positive_stage=ignore_attacker_positive,
    )
    if move_name == "shell side arm":
        physical_attack = offensive_stat(
            attacker,
            "physical",
            ignore_positive_stage=ignore_attacker_positive,
        )
        special_attack = offensive_stat(
            attacker,
            "special",
            ignore_positive_stage=ignore_attacker_positive,
        )
        attack_value = max(physical_attack, special_attack)
    if move_name == "photon geyser":
        attack_value = max(
            offensive_stat(attacker, "physical", ignore_positive_stage=ignore_attacker_positive),
            offensive_stat(attacker, "special", ignore_positive_stage=ignore_attacker_positive),
        )
    if (move.name or "").strip().lower() == "foul play":
        attack_value = offensive_stat(defender, "physical")
    if (move.name or "").strip().lower() == "body press":
        attack_value = defensive_stat(
            attacker,
            "physical",
            ignore_positive_stage=ignore_attacker_positive,
        )
    defense_value = defensive_stat(
        defender,
        move.category,
        ignore_positive_stage=ignore_defender_positive,
    )
    if move_name in {"psyshock", "psystrike"}:
        defense_value = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
    if (move.name or "").strip().lower() == "secret force":
        defense_value = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
    if move_name == "secret sword":
        defense_value = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
    if move_name == "shell side arm":
        physical_defense = defensive_stat(defender, "physical", ignore_positive_stage=ignore_defender_positive)
        special_defense = defensive_stat(defender, "special", ignore_positive_stage=ignore_defender_positive)
        if physical_defense < special_defense:
            defense_value = physical_defense
    base = max(0.0, expected_roll + attack_value - defense_value)
    base = float(apply_context_damage_modifiers(int(base), context))
    crit_bonus = expected_roll * crit_probability(move, hit_chance)
    if move_name == "wicked blow":
        crit_bonus = expected_roll * hit_chance
    pre_type = (base + crit_bonus) * hit_chance
    terrain_name = ""
    if terrain and isinstance(terrain, dict):
        terrain_name = (terrain.get("name") or "").strip().lower()
    gravity_active = "gravity" in terrain_name or "warped" in terrain_name
    type_mult = ptu_engine.type_multiplier(move.type, defender.spec.types)
    if (move.name or "").strip().lower() == "freeze-dry" and any(
        (t or "").strip().lower() == "water" for t in defender.spec.types
    ):
        other_types = [
            t for t in defender.spec.types if (t or "").strip().lower() != "water"
        ]
        type_mult = ptu_engine.type_multiplier(move.type, other_types) if other_types else 1.0
        type_mult *= 2.0
    if (
        type_mult == 0
        and move.type
        and move.type.lower() == "ground"
        and gravity_active
        and any((t or "").strip().lower() == "flying" for t in defender.spec.types)
    ):
        type_mult = 1.0
    if (
        type_mult == 0
        and move.type
        and move.type.lower() in {"normal", "fighting"}
        and any((t or "").strip().lower() == "ghost" for t in defender.spec.types)
        and attacker.get_temporary_effects("foresight")
    ):
        type_mult = 1.0
    if (
        type_mult == 0
        and move.type
        and move.type.lower() == "ghost"
        and any((t or "").strip().lower() == "normal" for t in defender.spec.types)
        and attacker.has_ability("Mojo")
    ):
        type_mult = 1.0
    if (
        type_mult == 0
        and move.type
        and move.type.lower() in {"normal", "fighting"}
        and any((t or "").strip().lower() == "ghost" for t in defender.spec.types)
        and attacker.has_ability("Scrappy")
    ):
        type_mult = 1.0
    return max(0.0, pre_type * type_mult)


def stab_db(move: MoveSpec, attacker: PokemonState) -> int:
    base_db = move.db or 0
    move_name = (move.name or "").strip().lower()
    # PTU RAW: Struggle Attacks never gain STAB.
    if move_name in {"struggle", "struggle+"}:
        return base_db
    move_type = (move.type or "Normal").lower()
    stab = 2 if any(move_type == t.lower() for t in attacker.spec.types) else 0
    if stab == 0 and move_type == "fighting" and attacker.has_ability("Kampfgeist"):
        stab = 2
    if stab == 0 and move_type == "psychic" and attacker.has_ability("Migraine"):
        max_hp = attacker.max_hp()
        current_hp = attacker.hp or 0
        if max_hp > 0 and current_hp * 2 <= max_hp:
            stab = 2
    if stab == 0 and move_type == "steel" and attacker.has_ability("Steelworker"):
        if attacker.has_status("Anchored") or attacker.get_temporary_effects("anchor_token"):
            stab = 2
    return base_db + stab


def weather_db_modifier(move: MoveSpec, weather: str | None) -> int:
    if not weather:
        return 0
    normalized = weather.strip().lower()
    return WEATHER_DB_MODIFIERS.get(normalized, {}).get((move.type or "Normal").lower(), 0)


def effective_db(move: MoveSpec, attacker: PokemonState, weather: str | None) -> int:
    """Deprecated helper retained for backwards compatibility."""
    return stab_db(move, attacker) + weather_db_modifier(move, weather)


def apply_status_modifiers(base_damage: int, attacker: PokemonState, move: MoveSpec) -> int:
    if move.category.lower() == "physical" and attacker.has_status("Burned"):
        return int(math.floor(base_damage * 0.5))
    return base_damage


def _seed_domains(context: AttackContext) -> None:
    move = context.move
    move_type = (move.type or "normal").lower()
    category = move.category.lower()
    melee_or_ranged = _normalized_range_kind(move)
    move_name_slug = (move.name or "").strip().lower().replace(" ", "-")
    context.add_domain(
        "all",
        "check",
        category,
        f"{category}-{move_type}",
        f"{melee_or_ranged}-{move_type}",
        f"{move_name_slug}-{move_type}" if move_name_slug else "",
        f"{move_type}-{category}",
    )
    if move_type:
        context.add_roll_option(f"type:{move_type}")
    if melee_or_ranged:
        context.add_roll_option(f"range:{melee_or_ranged}")
    if move.area_kind:
        context.add_roll_option(f"area:{move.area_kind.lower()}")


def _seed_roll_options(context: AttackContext) -> None:
    attacker = context.attacker
    move = context.move
    for pokemon_type in attacker.spec.types:
        context.add_roll_option(f"attacker-type:{pokemon_type.lower()}")
    for keyword in move.keywords:
        context.add_roll_option(f"keyword:{str(keyword).strip().lower()}")
    for status in attacker.statuses:
        label = attacker._normalized_status_name(status)
        if label:
            context.add_roll_option(f"status:{label}")


def _seed_status_domains(context: AttackContext) -> None:
    attacker = context.attacker
    if attacker.has_status("Paralyzed"):
        context.add_domain("status-paralyzed")
    if attacker.has_status("Burned"):
        context.add_domain("status-burned")
    if attacker.has_status("Poisoned") or attacker.has_status("Badly Poisoned"):
        context.add_domain("status-poisoned")


def _seed_weather(context: AttackContext) -> None:
    if not context.weather:
        return
    weather = context.weather.strip().lower()
    if not weather:
        return
    context.add_domain(f"weather-{weather}")
    context.add_roll_option(f"weather:{weather}")


def _seed_builtin_modifiers(context: AttackContext) -> None:
    move = context.move
    attacker = context.attacker
    move_type = (move.type or "normal").lower()
    if move_type and any(move_type == t.lower() for t in attacker.spec.types):
        context.add_modifier(
            slug="stab",
            kind="power",
            value=2,
            source="Same Type Attack Bonus",
        )
        context.add_roll_option(f"stab-{move_type}", "stab")
    if attacker.has_ability("Eggscellence"):
        move_name = (move.name or "").strip().lower()
        if move_name in {"barrage", "egg bomb"}:
            context.add_modifier(
                slug="eggscellence",
                kind="power",
                value=2,
                source="Eggscellence STAB",
            )
    if context.weather:
        modifier = weather_db_modifier(move, context.weather)
        if modifier:
            context.add_modifier(
                slug=f"weather-{context.weather.lower()}",
                kind="power",
                value=modifier,
                source=f"Weather ({context.weather})",
            )
    if move.category.lower() == "physical" and attacker.has_status("Burned"):
        context.add_modifier(
            slug="burned",
            kind="damage_scalar",
            value=0.5,
            timing=ModifierTiming.POST_DAMAGE,
            source="Burn halves physical damage",
        )
    if move.category.lower() != "status" and has_ability_exact(attacker, "Hustle [Errata]"):
        context.add_modifier(
            slug="hustle-errata",
            kind="damage_flat",
            value=10,
            source="Hustle [Errata] damage bonus",
        )
    elif move.category.lower() == "physical" and attacker.has_ability("Hustle"):
        context.add_modifier(
            slug="hustle",
            kind="damage_flat",
            value=10,
            source="Hustle physical damage bonus",
        )
    if attacker.has_ability("Technician") and (move.db or 0) <= 6:
        context.add_modifier(
            slug="technician",
            kind="damage_scalar",
            value=1.5,
            source="Technician low-power bonus",
        )
    if (
        attacker.has_ability("Tough Claws")
        and targeting.normalized_target_kind(move) == "melee"
        and move.category.lower() != "status"
    ):
        context.add_modifier(
            slug="tough-claws",
            kind="power",
            value=2,
            source="Tough Claws melee DB bonus",
        )
    if attacker.has_ability("Punk Rock") and move_has_keyword(move, "sonic") and move.category.lower() != "status":
        context.add_modifier(
            slug="punk-rock",
            kind="power",
            value=2,
            source="Punk Rock sonic DB bonus",
        )
    if attacker.has_ability("Strong Jaw"):
        move_name = (move.name or "").strip().lower()
        if move_name in _STRONG_JAW_MOVES:
            context.add_modifier(
                slug="strong-jaw",
                kind="power",
                value=2,
                source="Strong Jaw bite bonus",
            )
    if attacker.has_ability("Iron Fist") and move_has_punch_trait(move):
        context.add_modifier(
            slug="iron-fist",
            kind="damage_scalar",
            value=1.3,
            source="Iron Fist punch power",
        )
    if has_ability_exact(attacker, "Reckless [Errata]") and (
        move_has_keyword(move, "exhaust")
        or move_has_keyword(move, "recoil")
        or move_has_keyword(move, "reckless")
    ):
        context.add_modifier(
            slug="reckless-errata",
            kind="power",
            value=3,
            source="Reckless [Errata] DB bonus",
        )
    elif attacker.has_ability("Reckless") and not has_ability_exact(attacker, "Reckless [Errata]") and (
        recoil_fraction(move) or move_has_crash_trait(move)
    ):
        context.add_modifier(
            slug="reckless",
            kind="damage_scalar",
            value=1.3,
            source="Reckless recoil/crash bonus",
        )
    if attacker.has_ability("Sheer Force") and move.category.lower() != "status" and move.effects_text:
        context.add_modifier(
            slug="sheer-force",
            kind="power",
            value=2,
            source="Sheer Force power boost",
        )
    if attacker.has_ability("Shell Cannon") and attacker.get_temporary_effects("shell_cannon_ready"):
        move_name = (move.name or "").strip().lower()
        if move_name in {
            "aqua jet",
            "dive",
            "flash cannon",
            "hydro cannon",
            "hydro pump",
            "tackle",
            "waterfall",
            "water gun",
            "water spout",
        }:
            context.add_modifier(
                slug="shell-cannon",
                kind="damage_flat",
                value=4,
                source="Shell Cannon damage bonus",
            )
    if attacker.has_ability("Rivalry") and defender_gender(attacker, context.defender):
        context.add_modifier(
            slug="rivalry",
            kind="damage_flat",
            value=5,
            source="Rivalry damage bonus",
        )
    if attacker.has_ability("Sand Force") and context.weather:
        weather_name = context.weather.strip().lower()
        if "sand" in weather_name and move.category.lower() != "status":
            move_type = (move.type or "").strip().lower()
            if move_type in {"ground", "rock", "steel"}:
                context.add_modifier(
                    slug="sand-force",
                    kind="damage_flat",
                    value=5,
                    source="Sand Force weather bonus",
                )
    if attacker.has_ability("Courage"):
        max_hp = attacker.max_hp()
        current_hp = attacker.hp or 0
        if max_hp > 0 and current_hp * 3 <= max_hp:
            context.add_modifier(
                slug="courage",
                kind="damage_flat",
                value=5,
                source="Courage damage bonus",
            )
    move_name = (move.name or "").strip().lower()
    if move_name == "acrobatics":
        no_item = not attacker.is_holding_item()
        if not no_item and attacker.has_ability("Leek Mastery"):
            if any(attacker.has_item_named(name) for name in ("Rare Leek", "Leek", "Big Leek")):
                no_item = True
        if no_item:
            context.add_modifier(
                slug="acrobatics-no-item",
                kind="power",
                value=5,
                source="Acrobatics no item bonus",
            )
            context.add_roll_option("acrobatics:no-item")
    if move_name in {"behemoth bash", "behemoth blade"}:
        positive_cs = sum(max(0, value) for value in context.defender.combat_stages.values())
        if positive_cs > 0:
            context.add_modifier(
                slug="behemoth-positive-cs",
                kind="power",
                value=min(10, 2 * positive_cs),
                source="Behemoth vs positive combat stages",
            )
    if move_name == "dragon energy":
        hp_max = attacker.max_hp()
        if hp_max > 0:
            current_hp = attacker.hp or 0
            missing_hp = max(0, hp_max - current_hp)
            missing_ratio = missing_hp / hp_max
            penalty_steps = int(missing_ratio * 10)
            if penalty_steps > 0:
                context.add_modifier(
                    slug="dragon-energy-missing-hp",
                    kind="power",
                    value=-penalty_steps,
                    source="Dragon Energy missing HP",
                )
    terrain = context.terrain or {}
    terrain_name = (terrain.get("name") or "").strip().lower()
    if terrain_name.startswith("electric") and not attacker.can_fly():
        if (move.type or "").strip().lower() == "electric":
            context.add_modifier(
                slug="terrain-electric",
                kind="damage_flat",
                value=10,
                source="Electric Terrain damage bonus",
            )
    if terrain_name.startswith("grassy") and not attacker.can_fly():
        if (move.type or "").strip().lower() == "grass":
            context.add_modifier(
                slug="terrain-grassy",
                kind="damage_flat",
                value=10,
                source="Grassy Terrain damage bonus",
            )
    if terrain_name.startswith("psychic") and not attacker.can_fly():
        if (move.type or "").strip().lower() == "psychic":
            context.add_modifier(
                slug="terrain-psychic",
                kind="damage_flat",
                value=10,
                source="Psychic Terrain damage bonus",
            )
    if terrain_name.startswith("misty"):
        if (move.type or "").strip().lower() == "dragon":
            defender_grounded = (
                not context.defender.can_fly()
                and not context.defender.has_status("Magnet Rise")
            )
            if defender_grounded:
                context.add_modifier(
                    slug="terrain-misty",
                    kind="damage_scalar",
                    value=0.5,
                    source="Misty Terrain dragon reduction",
                )


def _effective_db_components(context: AttackContext, attacker: PokemonState) -> tuple[int, int, int, int]:
    """Return effective DB plus breakdown (stab_db, weather_db, other)."""
    base_with_stab = stab_db(context.move, attacker)
    weather_bonus = weather_db_modifier(context.move, context.weather)
    other_bonus = 0
    for modifier in context.modifiers:
        if modifier.kind != "power":
            continue
        if modifier.slug == "stab" or modifier.slug.startswith("weather-"):
            continue
        other_bonus += int(modifier.value)
    effective = max(1, base_with_stab + weather_bonus + other_bonus)
    return effective, base_with_stab, weather_bonus, other_bonus


def apply_context_damage_modifiers(base_damage: int, context: AttackContext) -> int:
    damage = base_damage
    for modifier in context.modifiers:
        if modifier.kind == "damage_flat":
            damage += int(modifier.value)
    for modifier in context.modifiers:
        if modifier.kind == "damage_scalar":
            damage = int(math.floor(damage * modifier.value))
    return damage


def _normalized_range_kind(move: MoveSpec) -> str:
    kind = (move.range_kind or move.target_kind or "ranged").lower()
    if "melee" in kind:
        return "melee"
    return "ranged"
