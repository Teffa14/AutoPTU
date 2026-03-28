"""Parsing utilities for shared item mechanics."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from .item_catalog import ItemEntry

_ITEM_EFFECT_CACHE: Dict[str, dict] = {}


def parse_item_effects(entry: ItemEntry) -> dict:
    """Best-effort parse of item effect text for shared mechanics."""
    key = f"{entry.normalized_name()}::{str(entry.description or '').strip()}"
    cached = _ITEM_EFFECT_CACHE.get(key)
    if cached is not None:
        return cached
    text = (entry.description or "").strip().lower()
    effects: dict = {}

    def _extract_afflictions(raw_text: str) -> Set[str]:
        names = set()
        for match in re.findall(r"@affliction\[([^\]]+)\]", raw_text):
            names.add(match.strip().lower())
        return names

    def _map_affliction(name: str) -> Optional[str]:
        mapping = {
            "poison": "Poisoned",
            "poisoned": "Poisoned",
            "blight": "Badly Poisoned",
            "badly poisoned": "Badly Poisoned",
            "burn": "Burned",
            "burned": "Burned",
            "paralysis": "Paralyzed",
            "paralyzed": "Paralyzed",
            "tased": "Paralyzed",
            "frozen": "Frozen",
            "freeze": "Frozen",
            "frostbite": "Frostbite",
            "sleep": "Sleep",
            "asleep": "Sleep",
            "drowsy": "Drowsy",
            "nightmares": "Bad Sleep",
            "confused": "Confused",
            "confusion": "Confused",
            "charmed": "Charmed",
            "fear": "Fear",
            "taunted": "Taunted",
            "disabled": "Disabled",
            "nullified": "Nullified",
            "suppressed": "Suppressed",
            "enraged": "Enraged",
            "cursed": "Cursed",
            "splinter": "Splinter",
        }
        return mapping.get(name)

    if text:
        heal_match = re.search(
            r"recover\s+(\d+)\s*/\s*(\d+)(?:th)?\s+of\s+max\s+hit\s+points?\s+at\s+the\s+beginning\s+of\s+each\s+turn",
            text,
        )
        if heal_match:
            effects["start_heal_fraction"] = (
                int(heal_match.group(1)),
                max(1, int(heal_match.group(2))),
            )
        heal_end_match = re.search(
            r"recover\s+(\d+)\s*/\s*(\d+)(?:th)?\s+of\s+max\s+hit\s+points?\s+at\s+the\s+end\s+of\s+each\s+turn",
            text,
        )
        if heal_end_match:
            effects["end_heal_fraction"] = (
                int(heal_end_match.group(1)),
                max(1, int(heal_end_match.group(2))),
            )
        fraction_match = re.search(
            r"recover\s+(\d+)\s*/\s*(\d+)(?:th)?\s+of\s+max\s+hit\s+points?",
            text,
        )
        if fraction_match and "turn" not in text:
            effects["use_heal_fraction"] = (
                int(fraction_match.group(1)),
                max(1, int(fraction_match.group(2))),
            )
        if "healed to its max hp" in text or "healed to its max hit points" in text:
            effects["use_heal_full"] = True
        hp_match = re.search(r"@hp\[(\d+)\]", text)
        if hp_match:
            effects["use_heal_hp"] = int(hp_match.group(1))
        pp_match = re.search(r"@pp\[(\d+)\]", text)
        if pp_match and "use_heal_hp" not in effects:
            name_key = entry.normalized_name()
            if name_key not in {"ether", "max ether", "elixir", "max elixir"}:
                effects["use_heal_hp"] = int(pp_match.group(1))
        if "once a scene" in text or "once per scene" in text:
            effects["scene_once"] = True
        evasion_round_match = re.search(
            r"gain\s+\+?(\d+)\s+evasion.*full round", text
        )
        if evasion_round_match:
            effects["evasion_bonus_round"] = int(evasion_round_match.group(1))
        injury_match = re.search(r"inflicts?\s+(\d+)\s+injur", text)
        if injury_match:
            effects["injury_on_use"] = int(injury_match.group(1))
        if "immune to flinch" in text:
            effects["flinch_immunity"] = True
        if "immune to secondary effects" in text:
            effects["secondary_immunity"] = True
        save_bonus_match = re.search(r"\+?(\d+)\s+bonus to save rolls", text)
        if save_bonus_match:
            effects["save_bonus"] = int(save_bonus_match.group(1))
        damage_bonus_match = re.search(r"adds?\s+(\d+)\s+to all damage rolls", text)
        if damage_bonus_match:
            effects["damage_bonus_scene"] = int(damage_bonus_match.group(1))
        if "duration of the scene" in text or "for the duration of the scene" in text:
            effects["scene_duration"] = True
        if "enraged" in text and ("become" in text or "they are" in text or "user is" in text):
            effects["self_status"] = "Enraged"
        restore_match = re.search(r"restores?\s+(\d+)\s+hit\s+points?", text)
        if restore_match and "use_heal_hp" not in effects:
            effects["use_heal_hp"] = int(restore_match.group(1))
        tick_matches = re.findall(r"@tick\[(-?\d+)\]", text)
        tick_values = [int(val) for val in tick_matches] if tick_matches else []
        if tick_values:
            if "end of" in text or "end of each activation" in text or "end of each turn" in text:
                if "type" not in text and len(tick_values) == 1:
                    effects["end_ticks"] = tick_values[0]
            elif "beginning of" in text or "start of" in text:
                effects["start_ticks"] = tick_values[0]
            else:
                if any(word in text for word in ("revive", "revival", "fainted")) or "revive" in entry.normalized_name():
                    effects["revive_ticks"] = tick_values[0]
                else:
                    effects["use_heal_ticks"] = tick_values[0]
        if "cures all volatile status effects" in text:
            effects["cure_volatile"] = True
        if "eliminates the set-up turn" in text:
            effects["setup_skip"] = True
        if "any negative combat stages are set to 0" in text:
            effects["clear_negative_stages"] = True
        if "desperation threshold" in text:
            effects["desperation_trigger"] = True
        if "hp-stealing moves restore double" in text or "hp-stealing moves restore double hp" in text:
            effects["drain_multiplier"] = 2.0
        healing_match = re.search(
            r"heals?\s+\+?(\d+)%\s+more\s+hp\s+from\s+@?trait\[healing\]",
            text,
        )
        if healing_match:
            effects["healing_multiplier"] = 1 + (int(healing_match.group(1)) / 100.0)
        if "choice-locked" in text:
            duration_match = re.search(r"choice-locked\s*(\d+)", text)
            effects["choice_lock_duration"] = int(duration_match.group(1)) if duration_match else 3
        choice_match = re.search(
            r"default\s+([a-z. ]+?)\s+stage\s*\+?(\d+)",
            text,
        )
        if choice_match:
            stat_raw = choice_match.group(1).strip().lower()
            stat_map = {
                "atk": "atk",
                "attack": "atk",
                "def": "def",
                "defense": "def",
                "spatk": "spatk",
                "sp. atk": "spatk",
                "sp. atk.": "spatk",
                "special attack": "spatk",
                "spdef": "spdef",
                "sp. def": "spdef",
                "sp. def.": "spdef",
                "special defense": "spdef",
                "spd": "spd",
                "speed": "spd",
            }
            stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
            effects["choice_stat"] = (stat, int(choice_match.group(2)))
            if "suppressed" in text:
                effects["choice_suppressed"] = True
        stage_changes: List[Tuple[str, int]] = []
        for match in re.findall(r"([+-]\d+)\s*([a-z ]+?)\s+stage", text):
            amount = int(match[0])
            stat_raw = match[1].strip().lower()
            stat_map = {
                "attack": "atk",
                "defense": "def",
                "special attack": "spatk",
                "special defense": "spdef",
                "speed": "spd",
                "accuracy": "accuracy",
                "evasion": "evasion",
            }
            stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
            stage_changes.append((stat, amount))
        if stage_changes:
            effects["stage_changes"] = stage_changes
        base_stat_changes: List[Tuple[str, int]] = []
        for match in re.findall(r"base\s+([a-z. ]+?)\s+by\s+([+-]\d+)", text):
            stat_raw = match[0].strip().lower()
            stat_map = {
                "atk": "atk",
                "attack": "atk",
                "def": "def",
                "defense": "def",
                "spatk": "spatk",
                "sp. atk": "spatk",
                "sp. atk.": "spatk",
                "spdef": "spdef",
                "sp. def": "spdef",
                "sp. def.": "spdef",
                "spd": "spd",
                "speed": "spd",
            }
            stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
            base_stat_changes.append((stat, int(match[1])))
        improve_pair_match = re.search(
            r"improves?\s+(?:your\s+)?base\s+([a-z. ]+?)\s+by\s+(\d+)\s*(?:,|and)\s*base\s+([a-z. ]+?)\s+by\s+(\d+)",
            text,
        )
        if improve_pair_match:
            for idx in (0, 2):
                stat_raw = improve_pair_match.group(1 + idx).strip().lower()
                amount = int(improve_pair_match.group(2 + idx))
                stat_map = {
                    "atk": "atk",
                    "attack": "atk",
                    "def": "def",
                    "defense": "def",
                    "spatk": "spatk",
                    "sp. atk": "spatk",
                    "sp. atk.": "spatk",
                    "special attack": "spatk",
                    "spdef": "spdef",
                    "sp. def": "spdef",
                    "sp. def.": "spdef",
                    "special defense": "spdef",
                    "spd": "spd",
                    "speed": "spd",
                }
                stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
                base_stat_changes.append((stat, amount))
        generic_base_stat_matches = re.findall(
            r"(?:improves?|increases?|raises?)\s+(?:your\s+)?base\s+([a-z. ]+?)\s+by\s+(\d+)",
            text,
        )
        for match in generic_base_stat_matches:
            stat_raw = match[0].strip().lower()
            amount = int(match[1])
            if " and " in stat_raw and "special defense" in stat_raw:
                split_stats = [part.strip() for part in stat_raw.split(" and ")]
            else:
                split_stats = [stat_raw]
            stat_map = {
                "atk": "atk",
                "attack": "atk",
                "def": "def",
                "defense": "def",
                "special defense stats": "spdef",
                "special defense stat": "spdef",
                "special defense": "spdef",
                "spdef": "spdef",
                "sp. def": "spdef",
                "sp. def.": "spdef",
                "spatk": "spatk",
                "sp. atk": "spatk",
                "sp. atk.": "spatk",
                "special attack": "spatk",
                "spd": "spd",
                "speed": "spd",
            }
            for split_stat in split_stats:
                normalized_split = split_stat.replace(" stats", "").replace(" stat", "").strip()
                stat = stat_map.get(split_stat, stat_map.get(normalized_split, normalized_split.replace(" ", "")))
                base_stat_changes.append((stat, amount))
        for match in re.findall(
            r"(?:your\s+)?(attack|defense|special attack|special defense|sp\. atk\.?|sp\. def\.?|spatk|spdef|speed|spd)\s+base\s+stat\s+by\s+(\d+)",
            text,
        ):
            stat_raw = match[0].strip().lower()
            amount = int(match[1])
            stat_map = {
                "atk": "atk",
                "attack": "atk",
                "def": "def",
                "defense": "def",
                "spatk": "spatk",
                "sp. atk": "spatk",
                "sp. atk.": "spatk",
                "special attack": "spatk",
                "spdef": "spdef",
                "sp. def": "spdef",
                "sp. def.": "spdef",
                "special defense": "spdef",
                "spd": "spd",
                "speed": "spd",
            }
            stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
            base_stat_changes.append((stat, amount))
        for match in re.findall(
            r"(?:reduces?|lowers?)\s+(?:your\s+)?base\s+([a-z. ]+?)\s+by\s+(\d+)",
            text,
        ):
            stat_raw = match[0].strip().lower()
            amount = -int(match[1])
            stat_map = {
                "atk": "atk",
                "attack": "atk",
                "def": "def",
                "defense": "def",
                "spatk": "spatk",
                "sp. atk": "spatk",
                "sp. atk.": "spatk",
                "special attack": "spatk",
                "spdef": "spdef",
                "sp. def": "spdef",
                "sp. def.": "spdef",
                "special defense": "spdef",
                "spd": "spd",
                "speed": "spd",
            }
            stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
            base_stat_changes.append((stat, amount))
        if base_stat_changes:
            deduped_changes: List[Tuple[str, int]] = []
            seen_changes: Set[Tuple[str, int]] = set()
            for stat_change in base_stat_changes:
                if stat_change in seen_changes:
                    continue
                seen_changes.add(stat_change)
                deduped_changes.append(stat_change)
            effects["base_stat_changes"] = deduped_changes
        base_scalars: List[Tuple[str, float]] = []
        base_pair_match = re.search(
            r"base\s+def\s+and\s+spdef\s+are\s+increased\s+by\s+(\d+)%",
            text,
        )
        if base_pair_match:
            multiplier = 1 + (int(base_pair_match.group(1)) / 100.0)
            base_scalars.extend([("def", multiplier), ("spdef", multiplier)])
        base_pair_stats_match = re.search(
            r"base\s+defense\s+and\s+special\s+defense\s+stats?\s+by\s+(\d+)",
            text,
        )
        if base_pair_stats_match:
            amount = int(base_pair_stats_match.group(1))
            base_stat_changes.extend([("def", amount), ("spdef", amount)])
        atk_pair_match = re.search(
            r"base\s+atk\s+and\s+sp(?:atk|\. atk\.?)\s+are\s+increased\s+by\s+(\d+)%",
            text,
        )
        if atk_pair_match:
            multiplier = 1 + (int(atk_pair_match.group(1)) / 100.0)
            base_scalars.extend([("atk", multiplier), ("spatk", multiplier)])
        base_scalar_match = re.search(
            r"base\s+([a-z. ]+?)\s+is\s+increased\s+by\s+(\d+)%",
            text,
        )
        if base_scalar_match:
            stat_raw = base_scalar_match.group(1).strip().lower()
            stat_map = {
                "atk": "atk",
                "attack": "atk",
                "def": "def",
                "defense": "def",
                "spatk": "spatk",
                "sp. atk": "spatk",
                "sp. atk.": "spatk",
                "spdef": "spdef",
                "sp. def": "spdef",
                "sp. def.": "spdef",
                "spd": "spd",
                "speed": "spd",
            }
            stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
            multiplier = 1 + (int(base_scalar_match.group(2)) / 100.0)
            base_scalars.append((stat, multiplier))
        if base_scalars:
            deduped_scalars: List[Tuple[str, float]] = []
            seen_scalars: Set[Tuple[str, float]] = set()
            for scalar_entry in base_scalars:
                if scalar_entry in seen_scalars:
                    continue
                seen_scalars.add(scalar_entry)
                deduped_scalars.append(scalar_entry)
            effects["base_stat_scalars"] = deduped_scalars
        post_stage_bonuses: List[Tuple[str, int]] = []
        post_stage_pair_match = re.search(
            r"grants?\s+a\s+\+?(\d+)\s+bonus\s+to\s+base\s+defense\s+and\s+special\s+defense,\s+after\s+combat\s+stages",
            text,
        )
        if post_stage_pair_match:
            amount = int(post_stage_pair_match.group(1))
            post_stage_bonuses.extend([("def", amount), ("spdef", amount)])
        if post_stage_bonuses:
            deduped_post_stage: List[Tuple[str, int]] = []
            seen_post_stage: Set[Tuple[str, int]] = set()
            for bonus_entry in post_stage_bonuses:
                if bonus_entry in seen_post_stage:
                    continue
                seen_post_stage.add(bonus_entry)
                deduped_post_stage.append(bonus_entry)
            effects["post_stage_stat_bonus"] = deduped_post_stage
        stat_scalars: List[Tuple[str, float]] = []
        stat_scalar_match = re.search(
            r"increases?\s+the\s+user'?s?\s+([a-z. ]+?)\s+stat\s+by\s+(\d+)%",
            text,
        )
        if stat_scalar_match:
            stat_raw = stat_scalar_match.group(1).strip().lower()
            stat_map = {
                "attack": "atk",
                "defense": "def",
                "special attack": "spatk",
                "special defense": "spdef",
                "speed": "spd",
            }
            stat = stat_map.get(stat_raw, stat_raw.replace(" ", ""))
            multiplier = 1 + (int(stat_scalar_match.group(2)) / 100.0)
            stat_scalars.append((stat, multiplier))
        if stat_scalars:
            effects["stat_scalars"] = stat_scalars
        if "move" in text and ("frequency one level" in text or "frequency one step" in text):
            effects["frequency_step_up"] = 1
        type_bonus_match = re.search(
            r"damage rolls? for\s+([a-z]+)-type\s+attacks?\s+(?:gain|are increased by)\s+\+?(\d+)",
            text,
        )
        if type_bonus_match:
            effects["type_damage_bonus"] = (
                type_bonus_match.group(1).title(),
                int(type_bonus_match.group(2)),
            )
        type_damage_flat_match = re.search(
            r"grants?\s+a\s+\+?(\d+)\s+damage bonus to all direct-damage\s+([a-z]+)\s+moves",
            text,
        )
        if type_damage_flat_match:
            effects["type_damage_flat"] = (
                type_damage_flat_match.group(2).title(),
                int(type_damage_flat_match.group(1)),
            )
        type_damage_reduction_match = re.search(
            r"grants?\s+the\s+holder\s+(\d+)\s+damage reduction against all direct-damage\s+([a-z]+)\s+moves",
            text,
        )
        if type_damage_reduction_match:
            effects["type_damage_reduction"] = (
                type_damage_reduction_match.group(2).title(),
                int(type_damage_reduction_match.group(1)),
            )
        multi_type_scalar_match = re.search(
            r"(?:boosts?|gain[s]?)\s+the\s+user'?s?\s+([a-z]+)\s+and\s+([a-z]+)-type\s+attack\s+power\s+by\s+(\d+)%",
            text,
        )
        if multi_type_scalar_match:
            multiplier = 1 + (int(multi_type_scalar_match.group(3)) / 100.0)
            effects["type_damage_scalars"] = [
                (multi_type_scalar_match.group(1).title(), multiplier),
                (multi_type_scalar_match.group(2).title(), multiplier),
            ]
        type_scalar_match = re.search(
            r"(?:boosts?|gain[s]?)\s+the\s+user'?s?\s+([a-z]+)-type\s+attack\s+power\s+by\s+(\d+)%",
            text,
        )
        if type_scalar_match:
            effects["type_damage_scalar"] = (
                type_scalar_match.group(1).title(),
                1 + (int(type_scalar_match.group(2)) / 100.0),
            )
        type_more_match = re.search(
            r"deals?\s+(\d+)%\s+more\s+damage\s+with\s+([a-z]+)-type",
            text,
        )
        if type_more_match:
            effects["type_damage_scalar"] = (
                type_more_match.group(2).title(),
                1 + (int(type_more_match.group(1)) / 100.0),
            )
        type_less_match = re.search(
            r"takes?\s+(\d+)%\s+less\s+damage\s+from\s+([a-z]+)-type",
            text,
        )
        if type_less_match:
            percent = int(type_less_match.group(1))
            multiplier = max(0.0, 1 - (percent / 100.0))
            effects["type_damage_scalar_defender"] = (
                type_less_match.group(2).title(),
                multiplier,
            )
        type_power_acc_match = re.search(
            r"increases?\s+the\s+power\s+and\s+accuracy\s+of\s+\[?([a-z]+)\]?\s+attacks?\s+by\s+(\d+)%",
            text,
        )
        if type_power_acc_match:
            type_name = type_power_acc_match.group(1).title()
            percent = int(type_power_acc_match.group(2))
            effects["type_damage_scalar"] = (type_name, 1 + (percent / 100.0))
            effects["type_accuracy_bonus"] = (type_name, max(1, int(round(percent / 5))))
        type_power_match = re.search(
            r"declares a\s+@trait\[([a-z]+)\]-type\s+attack.*?gains\s+\+?(\d+)%\s+power",
            text,
        )
        if type_power_match:
            effects["trigger_declare_type"] = type_power_match.group(1).title()
            effects["type_damage_scalar"] = (
                type_power_match.group(1).title(),
                1 + (int(type_power_match.group(2)) / 100.0),
            )
        category_scalar_match = re.search(
            r"(physical|special)-category\s+(?:attacks|actions)\s+deals?\s+(\d+)%\s+more\s+damage",
            text,
        )
        if category_scalar_match:
            category = category_scalar_match.group(1).strip().lower()
            multiplier = 1 + (int(category_scalar_match.group(2)) / 100.0)
            effects.setdefault("category_damage_scalars", []).append((category, multiplier))
        category_defender_match = re.search(
            r"takes?\s+(\d+)%\s+less\s+damage\s+from\s+(physical|special)-category\s+(?:attacks|actions)",
            text,
        )
        if category_defender_match:
            category = category_defender_match.group(2).strip().lower()
            multiplier = max(0.0, 1 - (int(category_defender_match.group(1)) / 100.0))
            effects["category_damage_scalar_defender"] = (category, multiplier)
        crit_match = re.search(r"critical\s+stages?\s*\+\s*(\d+)", text)
        if crit_match:
            effects["crit_range_bonus"] = int(crit_match.group(1))
        crit_range_match = re.search(
            r"critical\s+(?:hit\s+)?range(?:\s+extended)?\s+by\s+\+?(\d+)",
            text,
        )
        if crit_range_match and "crit_range_bonus" not in effects:
            effects["crit_range_bonus"] = int(crit_range_match.group(1))
        resist_match = re.search(
            r"super\s+effective\s+([a-z]+)-type\s+attack.*?(\d+)\s*%\s+less\s+damage",
            text,
        )
        if resist_match:
            effects["super_effective_resist"] = (
                resist_match.group(1).title(),
                max(1, int(resist_match.group(2))),
            )
        accuracy_percent_match = re.search(
            r"accuracy of the user'?s? attacks is increased by\s+\+?(\d+)%",
            text,
        )
        if accuracy_percent_match:
            percent = int(accuracy_percent_match.group(1))
            effects["accuracy_bonus"] = max(1, int(round(percent / 5)))
        accuracy_rolls_match = re.search(
            r"grants?\s+\+?(\d+)\s+bonus to all accuracy rolls",
            text,
        )
        if accuracy_rolls_match and "accuracy_bonus" not in effects:
            effects["accuracy_bonus"] = int(accuracy_rolls_match.group(1))
        accuracy_bonus_match = re.search(r"\baccuracy\s*\+(\d+)", text)
        if accuracy_bonus_match and "accuracy_bonus" not in effects:
            effects["accuracy_bonus"] = int(accuracy_bonus_match.group(1))
        accuracy_flat_match = re.search(r"gains?\s+\+?(\d+)\s+accuracy\b", text)
        if accuracy_flat_match and "accuracy_bonus" not in effects:
            raw_bonus = int(accuracy_flat_match.group(1))
            effects["accuracy_bonus"] = max(1, int(round(raw_bonus / 5)))
        accuracy_lower_av_match = re.search(
            r"gains?\s+\+?(\d+)\s+accuracy on attacks targeting creatures with a lower",
            text,
        )
        if accuracy_lower_av_match:
            raw_bonus = int(accuracy_lower_av_match.group(1))
            effects["accuracy_bonus_vs_lower_av"] = max(1, int(round(raw_bonus / 5)))
        evasion_speed_match = re.search(r"speed\s+evasion\s*\+(\d+)", text)
        if evasion_speed_match:
            effects["evasion_bonus_spd"] = int(evasion_speed_match.group(1))
        evasion_all_match = re.search(r"all stat evasions?\s*\+(\d+)", text)
        if evasion_all_match:
            effects["evasion_bonus_all"] = int(evasion_all_match.group(1))
        evasion_match = re.search(r"\bevasion\s*\+(\d+)", text)
        if (
            evasion_match
            and "evasion_bonus_all" not in effects
            and "evasion_bonus_spd" not in effects
        ):
            effects["evasion_bonus_all"] = int(evasion_match.group(1))
        if "would gain @affliction[fainted]" in text or "would gain @affliction[fainted]." in text:
            if "75% of its hp" in text:
                effects["focus_sash"] = True
            if "20% chance" in text:
                effects["focus_band_chance"] = 20
        if "focus sash" in entry.normalized_name() and "max to 0 or less" in text:
            effects["focus_sash"] = True
        if "focus band" in entry.normalized_name() and "roll" in text and "does not faint" in text:
            effects["focus_band_chance"] = 20
        if "increase the damage by" in text:
            bonus_match = re.search(r"increase the damage by\s+\+?(\d+)", text)
            if bonus_match:
                effects["damage_bonus_on_hit"] = int(bonus_match.group(1))
        if "super effective damage" in text and "additional" in text:
            bonus_match = re.search(r"additional\s+(\d+)\s+damage", text)
            if bonus_match:
                effects["damage_bonus_on_super_effective"] = int(bonus_match.group(1))
        loss_match = re.search(
            r"loses hit points equal to\s+(\d+)\s*/\s*(\d+)(?:th)?\s+of their max hit points",
            text,
        )
        if loss_match:
            effects["self_damage_fraction"] = (
                int(loss_match.group(1)),
                max(1, int(loss_match.group(2))),
            )
        if "tick of temporary hit points" in text:
            effects["temp_hp_on_damage_tick"] = 1
        if "adds +10 to their initiative" in text:
            effects["initiative_bonus"] = 10
        if "speed stat is halved" in text:
            effects["speed_scalar"] = 0.5
        if "immunity to ground type is lost" in text:
            effects["force_grounded"] = True
        if "does not take damage from sandstorm" in text:
            effects.setdefault("weather_immunity", set()).add("sandstorm")
        if "does not take damage from hail" in text:
            effects.setdefault("weather_immunity", set()).add("hail")
        if "snowy weather" in text or "intense snowfall" in text:
            effects.setdefault("weather_immunity", set()).add("snow")
        if "shady weather" in text or "intense enshrouding" in text:
            effects.setdefault("weather_immunity", set()).add("shady")
        if "assigned weather type" in text:
            effects["weather_immunity_assigned"] = True
        if "immune to moves with the powder keyword" in text:
            effects["powder_immunity"] = True
        status_match = re.search(r"induces?\s+([a-z ]+)\s+on holder", text)
        if status_match:
            status_name = _map_affliction(status_match.group(1).strip().lower())
            if status_name:
                effects["self_status"] = status_name
        if "gains the stall ability" in text:
            effects["grant_ability"] = "Stall"
        connected_match = re.search(
            r"connected ability:\s*(?:@uuid\[[^\]]+\]\{([^}]+)\}|([a-z0-9 '\\-]+))",
            text,
        )
        if connected_match:
            ability_name = connected_match.group(1) or connected_match.group(2) or ""
            effects["grant_ability"] = ability_name.strip().title()
        if "contact" in text and "@tick[" in text:
            contact_tick = tick_values[0] if tick_values else None
            if contact_tick is not None:
                effects["contact_ticks"] = contact_tick
        if "trigger:" in text and "super-effective" in text:
            effects["trigger_super_effective"] = True
        if "trigger:" in text and "hit" in text and "-type attack" in text:     
            type_match = re.search(r"hit\s+(?:by|with)\s+an?\s+([a-z]+)-type\s+attack", text)
            if not type_match:
                type_match = re.search(r"@trait\[([a-z]+)\]-type\s+attack", text)
            if type_match:
                effects["trigger_hit_type"] = type_match.group(1).title()
        if "trigger:" in text and "misses with an attack" in text:
            effects["trigger_on_miss"] = True
        if ("cured of all" in text or "healed of all" in text) and "major affliction" in text:
            effects["cure_major_all"] = True
        if ("cured of all" in text or "healed of all" in text) and "minor affliction" in text:
            effects["cure_minor_all"] = True
        count_match = re.search(r"cured of up to\s+(\d+)\s+.*major affliction", text)
        if count_match:
            effects["cure_major_count"] = int(count_match.group(1))
        minor_count_match = re.search(r"cured of up to\s+(\d+)\s+.*minor affliction", text)
        if minor_count_match:
            effects["cure_minor_count"] = int(minor_count_match.group(1))
        if "cured of burn" in text or "cured of paralysis" in text or "cured of poison" in text:
            cured = set(effects.get("cure_statuses", []))
            if "burn" in text:
                cured.add("Burned")
            if "paralysis" in text:
                cured.add("Paralyzed")
            if "poison" in text:
                cured.add("Poisoned")
            if cured:
                effects["cure_statuses"] = sorted(cured)
        if "cures disabled" in text:
            cured = set(effects.get("cure_statuses", []))
            cured.add("Disabled")
            effects["cure_statuses"] = sorted(cured)
        if "lose 1 combat stage" in text and "random stat" in text:
            effects["random_stage_loss"] = 1
        if "@affliction" in text:
            mapped = {_map_affliction(name) for name in _extract_afflictions(text)}
            mapped = {name for name in mapped if name}
            if mapped:
                effects["cure_statuses"] = sorted(mapped)
                if "trigger:" in text:
                    effects["trigger_on_status"] = True
        if "hover" in text and "air balloon" in entry.normalized_name():
            effects["air_balloon"] = True
        if "cannot have any of its abilities replaced" in text:
            effects["block_ability_replace"] = True
        if "cannot have any of its abilities" in text and "nullified" in text:
            effects["block_nullified"] = True
        if "would take damage" in text and "50% less damage" in text:
            effects["damage_scalar_on_trigger"] = 0.5
        if "poison-type" in text and "end of" in text and "@tick[" in text:
            effects["end_tick_type"] = ("poison", tick_values[0])
        non_type_match = re.search(r"non\s+([a-z]+)-type\s+creatures\s+take\s+@tick\[(-?\d+)\]", text)
        if non_type_match:
            effects["end_tick_non_type"] = (non_type_match.group(1).lower(), int(non_type_match.group(2)))
        if "consumed" in text:
            effects["consumable"] = True
    if "consumable" in entry.traits or "berry" in entry.traits:
        effects.setdefault("consumable", True)
    # PTU CSV text for some X-items is brief and may omit explicit "stage" wording.
    # Apply canonical defaults by item name when parser patterns cannot infer them.
    if "stage_changes" not in effects:
        compact_name = re.sub(r"[^a-z0-9]+", "", entry.normalized_name())
        x_stage_defaults = {
            "xattack": ("atk", 2),
            "xdefense": ("def", 2),
            "xspecialattack": ("spatk", 2),
            "xspatk": ("spatk", 2),
            "xspecialdefense": ("spdef", 2),
            "xspdef": ("spdef", 2),
            "xspeed": ("spd", 2),
            "xaccuracy": ("accuracy", 2),
        }
        default_change = x_stage_defaults.get(compact_name)
        if default_change:
            effects["stage_changes"] = [default_change]
    _ITEM_EFFECT_CACHE[key] = effects
    return effects


__all__ = ["parse_item_effects"]
