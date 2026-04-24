"""Item system extraction from BattleState."""

from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from ..battle_state import (
    BattleState,
    PokemonState,
    MoveSpec,
    ItemHookContext,
    _MAJOR_AFFLICTIONS,
    _MINOR_AFFLICTIONS,
    _item_name_text,
    _item_entry_for,
    _food_buffs_from_items,
    _load_move_specs,
    _species_form_data,
)
from ..item_effects import parse_item_effects
from ..abilities.ability_variants import has_ability_exact
from ...foundry_loader import load_foundry_species_abilities, pick_abilities_for_level
from ...learnsets import normalize_species_key
from .. import calculations, targeting, movement
from ..hooks.move_effect_tools import clear_hazards


CAPTURE_BALLS = {
    "air ball",
    "basic ball",
    "beacon ball",
    "beast ball",
    "cherish ball",
    "coolant ball",
    "dark ball",
    "dive ball",
    "dream ball",
    "dusk ball",
    "earth ball",
    "fabulous ball",
    "fast ball",
    "feather ball",
    "friend ball",
    "gigaton ball",
    "gossamer ball",
    "great ball",
    "hail ball",
    "haunt ball",
    "heal ball",
    "heat ball",
    "heavy ball",
    "hefty ball",
    "jet ball",
    "leaden ball",
    "learning ball",
    "level ball",
    "love ball",
    "lure ball",
    "luxury ball",
    "master ball",
    "mold ball",
    "moon ball",
    "mystic ball",
    "nest ball",
    "net ball",
    "park ball",
    "power ball",
    "premier ball",
    "quick ball",
    "rain ball",
    "repeat ball",
    "safari ball",
    "sand ball",
    "smog ball",
    "solid ball",
    "sport ball",
    "strange ball",
    "sun ball",
    "tiller ball",
    "timer ball",
    "ultra ball",
    "vane ball",
    "wing ball",
}

Z_CRYSTAL_TYPES = {
    "buginium": "Bug",
    "darkinium": "Dark",
    "dragonium": "Dragon",
    "electrium": "Electric",
    "fairium": "Fairy",
    "fightinium": "Fighting",
    "firium": "Fire",
    "flyinium": "Flying",
    "ghostium": "Ghost",
    "grassium": "Grass",
    "groundium": "Ground",
    "icium": "Ice",
    "normalium": "Normal",
    "poisonium": "Poison",
    "psychium": "Psychic",
    "rockium": "Rock",
    "steelium": "Steel",
    "waterium": "Water",
}


def _normalize_trait(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")


def _pokemon_has_trait(pokemon: PokemonState, *traits: str) -> bool:
    trait_set = {_normalize_trait(tag) for tag in (pokemon.spec.tags or []) if tag}
    trait_set.update(_normalize_trait(cap) for cap in pokemon.capability_names())
    return any(_normalize_trait(trait) in trait_set for trait in traits)


def _capture_tool_accuracy(battle: BattleState, actor: PokemonState, target: PokemonState, *, ac: int) -> Dict[str, object]:
    roll = battle.rng.randint(1, 20)
    evasion = calculations.evasion_value(target, "Status")
    accuracy_bonus = 0
    if actor.has_trainer_feature("Tools of the Trade"):
        accuracy_bonus += 2
    accuracy_stage = calculations.accuracy_stage_value(
        actor.combat_stages.get("accuracy", 0) + actor.spec.accuracy_cs + accuracy_bonus
    )
    needed = max(2, int(ac) + evasion - accuracy_stage)
    hit = roll == 20 or (roll != 1 and roll >= needed)
    return {
        "roll": roll,
        "needed": needed,
        "hit": hit,
        "crit": roll == 20,
        "accuracy_bonus": accuracy_bonus,
        "tools_of_the_trade": actor.has_trainer_feature("Tools of the Trade"),
    }


def _capture_tool_size_rank(value: object) -> int:
    label = str(value or "").strip().lower()
    order = {
        "tiny": 0,
        "small": 1,
        "medium": 2,
        "large": 3,
        "huge": 4,
        "gigantic": 5,
    }
    return order.get(label, 2 if label else 1)

@dataclass
class ItemSystem:
    battle: BattleState

    def apply_defender_item_triggers(
        self,
        defender_id: str,
        defender: PokemonState,
        attacker_id: str,
        attacker: PokemonState,
        move: MoveSpec,
        result: Dict[str, object],
        damage_dealt: int,
        has_contact: bool,
    ) -> List[dict]:
        ctx = ItemHookContext(
            battle=self.battle,
            events=[],
            holder_id=defender_id,
            holder=defender,
            attacker_id=attacker_id,
            attacker=attacker,
            move=move,
            result=result,
            phase="defender_triggers",
            damage_dealt=damage_dealt,
            has_contact=has_contact,
        )
        return self.battle.hook_dispatcher.apply_item_hooks("defender_triggers", ctx)

    def apply_attacker_item_miss_triggers(self, attacker_id: str, attacker: PokemonState) -> List[dict]:
        ctx = ItemHookContext(
            battle=self.battle,
            events=[],
            holder_id=attacker_id,
            holder=attacker,
            attacker_id=attacker_id,
            attacker=attacker,
            move=MoveSpec(name="Miss Trigger", type="Normal", category="Status"),
            result={},
            phase="attacker_miss_triggers",
        )
        return self.battle.hook_dispatcher.apply_item_hooks("attacker_miss_triggers", ctx)

    def apply_held_item_start(self, actor_id: str) -> List[dict]:
        battle = self.battle
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return []
        if battle._magic_room_active():
            return []
        events: List[dict] = []

        def _has_temp_effect(kind: str, **match: object) -> bool:
            for entry in actor.get_temporary_effects(kind):
                if not isinstance(entry, dict):
                    continue
                if all(entry.get(key) == value for key, value in match.items()):
                    return True
            return False

        def _normalize_stat_key(raw: object) -> str:
            value = str(raw or "").strip().lower()
            mapping = {
                "attack": "atk",
                "atk": "atk",
                "defense": "def",
                "def": "def",
                "special attack": "spatk",
                "spatk": "spatk",
                "special defense": "spdef",
                "spdef": "spdef",
                "speed": "spd",
                "spd": "spd",
                "accuracy": "accuracy",
                "evasion": "evasion",
            }
            return mapping.get(value, "")

        held_items = sorted(battle._iter_held_items(actor), key=lambda row: row[0], reverse=True)
        for idx, item, entry in held_items:
            effects = parse_item_effects(entry)
            name = _item_name_text(item)
            normalized = entry.normalized_name()
            species_name = str(actor.spec.species or "").strip().lower()
            species_key = normalize_species_key(species_name).replace("'", "").replace("\u2019", "")
            item_event_start = len(events)
            applied_effects: List[str] = []
            base_stat_changes = effects.get("base_stat_changes") or []
            for stat, amount in base_stat_changes:
                if not _has_temp_effect("stat_modifier", stat=stat, source=name):
                    actor.add_temporary_effect("stat_modifier", stat=stat, amount=amount, source=name)
                    applied_effects.append(f"stat_modifier:{stat}")
            if normalized in {"chipped pot", "cracked pot"}:
                species = str(actor.spec.species or "").strip().lower()
                if species in {"sinistea", "polteageist"}:
                    stat_bonuses = {"chipped pot": [("def", 5), ("spdef", 5)], "cracked pot": [("spd", 10)]}
                    for stat, amount in stat_bonuses.get(normalized, []):
                        if not _has_temp_effect("stat_modifier", stat=stat, source=name):
                            actor.add_temporary_effect("stat_modifier", stat=stat, amount=amount, source=name)
                            applied_effects.append(f"stat_modifier:{stat}")
            base_stat_scalars = effects.get("base_stat_scalars") or []
            for stat, multiplier in base_stat_scalars:
                if not _has_temp_effect("stat_scalar", stat=stat, source=name):
                    actor.add_temporary_effect("stat_scalar", stat=stat, multiplier=multiplier, source=name)
                    applied_effects.append(f"stat_scalar:{stat}")
            stat_scalars = effects.get("stat_scalars") or []
            if normalized == "cornerstone mask":
                if species_name != "ogerpon":
                    stat_scalars = []
                else:
                    stat_scalars = list(stat_scalars) + [("def", 1.2)]
            for stat, multiplier in stat_scalars:
                if not _has_temp_effect("stat_scalar", stat=stat, source=name):
                    actor.add_temporary_effect("stat_scalar", stat=stat, multiplier=multiplier, source=name)
                    applied_effects.append(f"stat_scalar:{stat}")
            if normalized == "rock incense" and species_key in {"bonsly", "sudowoodo"}:
                if not _has_temp_effect("stat_modifier", stat="spdef", source=name):
                    actor.add_temporary_effect("stat_modifier", stat="spdef", amount=20, source=name)
                    applied_effects.append("stat_modifier:spdef")
            if normalized == "odd incense" and species_key in {
                "mime jr.",
                "mr. mime",
                "mr. mime galarian",
                "mr. rime",
            }:
                if not _has_temp_effect("stat_modifier", stat="spatk", source=name):
                    actor.add_temporary_effect("stat_modifier", stat="spatk", amount=10, source=name)
                    applied_effects.append("stat_modifier:spatk")
            if normalized == "rose incense" and species_key in {"budew", "roselia", "roserade"}:
                if not _has_temp_effect("stat_modifier", stat="spatk", source=name):
                    actor.add_temporary_effect("stat_modifier", stat="spatk", amount=10, source=name)
                    applied_effects.append("stat_modifier:spatk")
            accuracy_bonus = effects.get("accuracy_bonus")
            if accuracy_bonus is not None:
                if not _has_temp_effect("accuracy_bonus", amount=int(accuracy_bonus), type=None, source=name):
                    actor.add_temporary_effect("accuracy_bonus", amount=int(accuracy_bonus), type=None, source=name)
                    applied_effects.append("accuracy_bonus")
            accuracy_lower = effects.get("accuracy_bonus_vs_lower_av")
            if accuracy_lower is not None:
                if not _has_temp_effect(
                    "accuracy_bonus_vs_lower_av", amount=int(accuracy_lower), type=None, source=name
                ):
                    actor.add_temporary_effect(
                        "accuracy_bonus_vs_lower_av", amount=int(accuracy_lower), type=None, source=name
                    )
                    applied_effects.append("accuracy_bonus_vs_lower_av")
            type_accuracy = effects.get("type_accuracy_bonus")
            if type_accuracy:
                acc_type, amount = type_accuracy
                if not _has_temp_effect("accuracy_bonus", amount=int(amount), type=acc_type, source=name):
                    actor.add_temporary_effect("accuracy_bonus", amount=int(amount), type=acc_type, source=name)
                    applied_effects.append(f"accuracy_bonus:{acc_type}")
            evasion_spd = effects.get("evasion_bonus_spd")
            if evasion_spd is not None:
                if not _has_temp_effect(
                    "evasion_bonus", scope="status", amount=int(evasion_spd), source=name
                ):
                    actor.add_temporary_effect(
                        "evasion_bonus", scope="status", amount=int(evasion_spd), source=name
                    )
                    applied_effects.append("evasion_bonus:status")
            evasion_all = effects.get("evasion_bonus_all")
            if evasion_all is not None:
                if not _has_temp_effect(
                    "evasion_bonus", scope="all", amount=int(evasion_all), source=name
                ):
                    actor.add_temporary_effect("evasion_bonus", scope="all", amount=int(evasion_all), source=name)
                    applied_effects.append("evasion_bonus:all")
            initiative_bonus = effects.get("initiative_bonus")
            if initiative_bonus is not None:
                if not _has_temp_effect("initiative_bonus", amount=int(initiative_bonus), source=name):
                    actor.add_temporary_effect("initiative_bonus", amount=int(initiative_bonus), source=name)
                    applied_effects.append("initiative_bonus")
            speed_scalar = effects.get("speed_scalar")
            if speed_scalar is not None:
                if not _has_temp_effect("stat_scalar", stat="spd", multiplier=float(speed_scalar), source=name):
                    actor.add_temporary_effect("stat_scalar", stat="spd", multiplier=float(speed_scalar), source=name)
                    applied_effects.append("stat_scalar:spd")
            if normalized == "quick powder":
                if species_name == "ditto":
                    if not _has_temp_effect("stat_scalar", stat="spd", multiplier=2.0, source=name):
                        actor.add_temporary_effect("stat_scalar", stat="spd", multiplier=2.0, source=name)
                        applied_effects.append("stat_scalar:spd")
            drain_multiplier = effects.get("drain_multiplier")
            if drain_multiplier is not None:
                if not _has_temp_effect("drain_multiplier", multiplier=float(drain_multiplier), source=name):
                    actor.add_temporary_effect("drain_multiplier", multiplier=float(drain_multiplier), source=name)
                    applied_effects.append("drain_multiplier")
            healing_multiplier = effects.get("healing_multiplier")
            if healing_multiplier is not None:
                if not _has_temp_effect("healing_multiplier", multiplier=float(healing_multiplier), source=name):
                    actor.add_temporary_effect(
                        "healing_multiplier", multiplier=float(healing_multiplier), source=name
                    )
                    applied_effects.append("healing_multiplier")
            if effects.get("powder_immunity"):
                if not _has_temp_effect("powder_immunity", source=name):
                    actor.add_temporary_effect("powder_immunity", source=name)
                    applied_effects.append("powder_immunity")
            if effects.get("secondary_immunity"):
                if not _has_temp_effect("secondary_immunity", source=name):
                    actor.add_temporary_effect("secondary_immunity", source=name)
                    applied_effects.append("secondary_immunity")
            if normalized == "heavy-duty boots":
                if not _has_temp_effect("hazard_immunity", source=name):
                    actor.add_temporary_effect("hazard_immunity", source=name)
                    applied_effects.append("hazard_immunity")
            weather_immunity = effects.get("weather_immunity") or set()
            for weather in weather_immunity:
                weather_name = str(weather).strip().lower()
                if not weather_name:
                    continue
                if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                    actor.add_temporary_effect("weather_immunity", weather=weather_name, source=name)
                    applied_effects.append(f"weather_immunity:{weather_name}")
            if normalized == "alkaline clay":
                for weather_name in ("smoggy", "acid rain"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "boggy clay":
                for weather_name in ("foggy", "intense fog"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "blue orb" and species_name == "kyogre":
                if not _has_temp_effect("primal_reversion_ready", source=name):
                    actor.add_temporary_effect("primal_reversion_ready", source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "primal_reversion_ready",
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "red orb" and species_name == "groudon":
                if not _has_temp_effect("primal_reversion_ready", source=name):
                    actor.add_temporary_effect("primal_reversion_ready", source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "primal_reversion_ready",
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "buckler shield":
                if not _has_temp_effect("ability_granted", ability="Parry", source=name):
                    actor.add_temporary_effect("ability_granted", ability="Parry", source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "grant_ability",
                            "ability": "Parry",
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "breastplate":
                if not _has_temp_effect("stat_scalar", stat="spd", multiplier=0.85, source=name):
                    actor.add_temporary_effect("stat_scalar", stat="spd", multiplier=0.85, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "armor_speed_scalar",
                            "stat": "spd",
                            "multiplier": 0.85,
                            "target_hp": actor.hp,
                        }
                    )
                if not _has_temp_effect("resistance_bonus", amount=5, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=5, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": 5,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "buff coat":
                if not _has_temp_effect("stat_scalar", stat="spd", multiplier=0.9, source=name):
                    actor.add_temporary_effect("stat_scalar", stat="spd", multiplier=0.9, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "armor_speed_scalar",
                            "stat": "spd",
                            "multiplier": 0.9,
                            "target_hp": actor.hp,
                        }
                    )
                if not _has_temp_effect("resistance_bonus", amount=10, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=10, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": 10,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "heavy clothing":
                if not _has_temp_effect("stat_scalar", stat="spd", multiplier=0.9, source=name):
                    actor.add_temporary_effect("stat_scalar", stat="spd", multiplier=0.9, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "armor_speed_scalar",
                            "stat": "spd",
                            "multiplier": 0.9,
                            "target_hp": actor.hp,
                        }
                    )
                if not _has_temp_effect("resistance_bonus", amount=5, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=5, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": 5,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "husarine plate":
                if not _has_temp_effect("stat_scalar", stat="spd", multiplier=0.8, source=name):
                    actor.add_temporary_effect("stat_scalar", stat="spd", multiplier=0.8, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "armor_speed_scalar",
                            "stat": "spd",
                            "multiplier": 0.8,
                            "target_hp": actor.hp,
                        }
                    )
                if not _has_temp_effect("resistance_bonus", amount=15, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=15, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": 15,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "pure incense":
                if not _has_temp_effect("resistance_bonus", amount=10, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=10, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": 10,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "robes of thaumaturgy":
                for stat, amount in (("spdef", 20), ("spatk", 10)):
                    if not _has_temp_effect("stat_modifier", stat=stat, amount=amount, source=name):
                        actor.add_temporary_effect("stat_modifier", stat=stat, amount=amount, source=name)
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "stat_modifier",
                                "stat": stat,
                                "amount": amount,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "sandy clay":
                for weather_name in ("dusty", "intense dust storm"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "skyloft clay":
                for weather_name in ("windy", "intense winds"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "soggy clay":
                for weather_name in ("rainy", "intense downpour"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "sunny clay":
                for weather_name in ("sunny", "intense heat"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "umbra clay":
                for weather_name in ("gloomy", "intense umbra"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "smooth rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="dusty", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="dusty",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "dusty",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "tenebrous rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="shady", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="shady",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "shady",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "unremarkable teacup":
                if not _has_temp_effect("drain_multiplier", multiplier=1.15, source=name):
                    actor.add_temporary_effect("drain_multiplier", multiplier=1.15, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "drain_multiplier",
                            "multiplier": 1.15,
                            "target_hp": actor.hp,
                        }
                    )
                if species_name in {"poltchageist", "sinischa"}:
                    if not _has_temp_effect("stat_modifier", stat="hp_stat", amount=10, source=name):
                        actor.add_temporary_effect("stat_modifier", stat="hp_stat", amount=10, source=name)
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "stat_modifier",
                                "stat": "hp_stat",
                                "amount": 10,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "wellspring mask" and "ogerpon" in species_name:
                if not _has_temp_effect("stat_scalar", stat="spdef", multiplier=1.2, source=name):
                    actor.add_temporary_effect("stat_scalar", stat="spdef", multiplier=1.2, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "stat_scalar",
                            "stat": "spdef",
                            "multiplier": 1.2,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized in {"sweet apple", "tart apple", "syrupy apple"}:
                stat_map = {
                    "sweet apple": "spd",
                    "tart apple": "def",
                    "syrupy apple": "spdef",
                }
                stat = stat_map.get(normalized)
                if stat:
                    multiplier = 1.15
                    if "grass" in {t.lower().strip() for t in actor.spec.types if t}:
                        multiplier = 1.3
                    if not _has_temp_effect("stat_scalar", stat=stat, multiplier=multiplier, source=name):
                        actor.add_temporary_effect("stat_scalar", stat=stat, multiplier=multiplier, source=name)
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "stat_scalar",
                                "stat": stat,
                                "multiplier": multiplier,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "teal mask" and "ogerpon" in species_name:
                if not _has_temp_effect("stat_scalar", stat="spd", multiplier=1.2, source=name):
                    actor.add_temporary_effect("stat_scalar", stat="spd", multiplier=1.2, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "stat_scalar",
                            "stat": "spd",
                            "multiplier": 1.2,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "terrain extender":
                if not _has_temp_effect("terrain_duration_bonus", bonus=2, source=name):
                    actor.add_temporary_effect("terrain_duration_bonus", bonus=2, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "terrain_duration_bonus",
                            "bonus": 2,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "type booster":
                item_type = battle._item_type_from_item(item)
                if item_type and not _has_temp_effect(
                    "accuracy_bonus", amount=2, type=item_type, source=name
                ):
                    actor.add_temporary_effect(
                        "accuracy_bonus", amount=2, type=item_type, source=name
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "accuracy_bonus",
                            "amount": 2,
                            "item_type": item_type,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "type capacitor":
                item_type = battle._item_type_from_item(item)
                if item_type and not _has_temp_effect(
                    "type_capacitor", type=item_type, source=name
                ):
                    actor.add_temporary_effect(
                        "type_capacitor", type=item_type, source=name
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "type_capacitor",
                            "item_type": item_type,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "utility umbrella":
                weather_names = {
                    "sun",
                    "sunny",
                    "harsh sunlight",
                    "rain",
                    "rainy",
                    "downpour",
                    "intense downpour",
                    "hail",
                    "snow",
                    "snowy",
                    "sand",
                    "sandstorm",
                    "dusty",
                    "intense dust storm",
                    "windy",
                    "intense winds",
                    "gloomy",
                    "intense umbra",
                    "shady",
                    "intense enshrouding",
                    "foggy",
                    "intense fog",
                    "smoggy",
                    "acid rain",
                }
                for weather_name in weather_names:
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "item": name,
                        "effect": "weather_immunity",
                        "weather": "all",
                        "target_hp": actor.hp,
                    }
                )
            if normalized in {"scroll of darkness", "scroll of waters"} and "urshifu" in species_name:
                stat = "atk" if normalized == "scroll of darkness" else "spd"
                if not _has_temp_effect("stat_modifier", stat=stat, amount=10, source=name):
                    actor.add_temporary_effect("stat_modifier", stat=stat, amount=10, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "stat_modifier",
                            "stat": stat,
                            "amount": 10,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "shed shell":
                for status in ("Hindered", "Stuck", "Bound", "Grappled"):
                    if not _has_temp_effect("status_immunity", status=status, source=name):
                        actor.add_temporary_effect("status_immunity", status=status, source=name)
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "status_immunity",
                                "status": status,
                                "target_hp": actor.hp,
                            }
                        )
                if not _has_temp_effect("resistance_bonus", amount=15, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=15, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": 15,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "lysandre labs fire rescue armour":
                for stat, amount in (("def", 10), ("spdef", 5), ("spd", -10)):
                    if not _has_temp_effect("stat_modifier", stat=stat, amount=amount, source=name):
                        actor.add_temporary_effect("stat_modifier", stat=stat, amount=amount, source=name)
                if not _has_temp_effect("status_immunity", status="Burned", source=name):
                    actor.add_temporary_effect("status_immunity", status="Burned", source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "status_immunity",
                            "status": "Burned",
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "protective pads":
                if not _has_temp_effect("contact_ability_block", source=name):
                    actor.add_temporary_effect("contact_ability_block", source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "contact_ability_block",
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "macro-galaxy pioneer armor":
                for stat, amount in (("def", 5), ("spdef", 5)):
                    if not _has_temp_effect("stat_modifier", stat=stat, amount=amount, source=name):
                        actor.add_temporary_effect("stat_modifier", stat=stat, amount=amount, source=name)
            if normalized == "metal coat":
                resistance = 20 if "steel" in {t.lower().strip() for t in actor.spec.types if t} else 10
                if not _has_temp_effect("resistance_bonus", amount=resistance, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=resistance, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": resistance,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "pink pearl" and species_name == "spoink":
                if not _has_temp_effect("stat_modifier", stat="spatk", amount=1, source=name):
                    actor.add_temporary_effect("stat_modifier", stat="spatk", amount=1, source=name)
            if normalized == "masterpiece teacup":
                if not _has_temp_effect("drain_multiplier", multiplier=1.3, source=name):
                    actor.add_temporary_effect("drain_multiplier", multiplier=1.3, source=name)
                if species_name in {"poltchageist", "sinischa"}:
                    if not _has_temp_effect("stat_modifier", stat="spatk", amount=10, source=name):
                        actor.add_temporary_effect("stat_modifier", stat="spatk", amount=10, source=name)
            if normalized == "float stone":
                if not _has_temp_effect("weight_class_scalar", multiplier=0.5, source=name):
                    actor.add_temporary_effect("weight_class_scalar", multiplier=0.5, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weight_class_scalar",
                            "multiplier": 0.5,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "heat rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="sun", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="sun",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "Sunny",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "icy rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="snowy", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="snowy",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "Snowy",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "misty rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="foggy", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="foggy",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "Foggy",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "porous rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="windy", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="windy",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "Windy",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "light clay":
                if not _has_temp_effect("effect_duration_bonus", amount=2, source=name):
                    actor.add_temporary_effect("effect_duration_bonus", amount=2, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "effect_duration_bonus",
                            "amount": 2,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "jetpack":
                if not _has_temp_effect("movement_override", mode="sky", value=15, source=name):
                    actor.add_temporary_effect("movement_override", mode="sky", value=15, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "movement_override",
                            "mode": "sky",
                            "value": 15,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "damp rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="rain", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="rain",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "Rain",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
                if not _has_temp_effect("resistance_bonus", amount=10, source=name):
                    actor.add_temporary_effect("resistance_bonus", amount=10, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "resistance_bonus",
                            "amount": 10,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "geiger clay":
                for weather_name in ("glowy", "intense radstorm"):
                    if not _has_temp_effect("weather_immunity", weather=weather_name, source=name):
                        actor.add_temporary_effect(
                            "weather_immunity", weather=weather_name, source=name
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "weather_immunity",
                                "weather": weather_name,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "glassy rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="gloomy", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="gloomy",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "Gloomy",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "glowing rock":
                if not _has_temp_effect(
                    "weather_duration_bonus", weather="glowy", bonus=3, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_duration_bonus",
                        weather="glowy",
                        bonus=3,
                        source=name,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "weather_duration_bonus",
                            "weather": "Glowy",
                            "bonus": 3,
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "hearthflame mask":
                if species_name == "ogerpon":
                    if not _has_temp_effect("stat_scalar", stat="atk", multiplier=1.2, source=name):
                        actor.add_temporary_effect("stat_scalar", stat="atk", multiplier=1.2, source=name)
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "stat_scalar",
                                "stat": "atk",
                                "multiplier": 1.2,
                                "target_hp": actor.hp,
                            }
                        )
            if effects.get("weather_immunity_assigned") and isinstance(item, dict):
                raw_weather = (
                    item.get("weather")
                    or item.get("weather_type")
                    or item.get("assigned_weather")
                    or ""
                )
                weather_text = str(raw_weather).strip().lower()
                weather_name = ""
                if "sand" in weather_text:
                    weather_name = "sandstorm"
                elif "hail" in weather_text:
                    weather_name = "hail"
                elif "snow" in weather_text:
                    weather_name = "snow"
                elif "rain" in weather_text or "storm" in weather_text or "downpour" in weather_text:
                    weather_name = "rain"
                elif "sun" in weather_text:
                    weather_name = "sun"
                if weather_name and not _has_temp_effect(
                    "weather_immunity", weather=weather_name, source=name
                ):
                    actor.add_temporary_effect(
                        "weather_immunity", weather=weather_name, source=name
                    )
            if effects.get("force_grounded"):
                if not _has_temp_effect("force_grounded", source=name):
                    actor.add_temporary_effect("force_grounded", source=name)
            grant_ability = effects.get("grant_ability")
            if grant_ability:
                if not _has_temp_effect("ability_granted", ability=grant_ability, source=name):
                    actor.add_temporary_effect("ability_granted", ability=grant_ability, source=name)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "grant_ability",
                            "ability": grant_ability,
                            "target_hp": actor.hp,
                        }
                    )
            self_status = effects.get("self_status")
            if self_status and not actor.has_status(self_status):
                actor.statuses.append({"name": self_status, "source": name})
                events.append(
                    {
                        "type": "status",
                        "actor": actor_id,
                        "status": self_status,
                        "effect": "item_status",
                        "item": name,
                        "description": f"{name} inflicts {self_status}.",
                        "target_hp": actor.hp,
                    }
                )
            if normalized == "pokey orb" and not actor.has_status("Splinter"):
                actor.statuses.append({"name": "Splinter", "source": name})
                events.append(
                    {
                        "type": "status",
                        "actor": actor_id,
                        "status": "Splinter",
                        "effect": "item_status",
                        "item": name,
                        "description": f"{name} inflicts Splinter.",
                        "target_hp": actor.hp,
                    }
                )
            start_ticks = effects.get("start_ticks")
            if start_ticks:
                if not actor.has_status("Heal Blocked") and not actor.has_status("Heal Block"):
                    amount = int(start_ticks) * actor.tick_value()
                    if amount != 0:
                        before = actor.hp or 0
                        if amount > 0:
                            actor.heal(amount)
                        else:
                            actor.apply_damage(abs(amount))
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "start_ticks",
                                "amount": (actor.hp or 0) - before,
                                "target_hp": actor.hp,
                            }
                        )
            if effects.get("clear_negative_stages"):
                negative = {k: v for k, v in actor.combat_stages.items() if v < 0}
                if negative:
                    for stat in negative:
                        actor.combat_stages[stat] = 0
                    battle._consume_held_item(
                        actor_id,
                        actor,
                        idx,
                        item,
                        "clear_negative_stages",
                        f"{name} clears negative combat stages.",
                        events,
                    )
                    continue
            if effects.get("cure_volatile"):
                removed = actor.clear_volatile_statuses()
                if removed:
                    battle._consume_held_item(
                        actor_id,
                        actor,
                        idx,
                        item,
                        "cure_volatile",
                        f"{name} cures volatile status conditions.",
                        events,
                    )
                    events[-1]["statuses"] = removed
                    continue
            if effects.get("trigger_on_status") and effects.get("cure_statuses"):
                status_set = {str(s).lower() for s in effects.get("cure_statuses", [])}
                if any(actor.has_status(status) for status in status_set):
                    status_events = battle._apply_item_effects_to_target(actor_id, actor_id, item, effects)
                    if status_events:
                        battle._consume_held_item(
                            actor_id,
                            actor,
                            idx,
                            item,
                            "trigger_on_status",
                            f"{name} cures status conditions.",
                            status_events,
                        )
                        events.extend(status_events)
                        continue
            if effects.get("desperation_trigger"):
                events.extend(battle._apply_desperation_item_trigger(actor_id, actor, idx, item))
            start_fraction = effects.get("start_heal_fraction")
            if start_fraction and not actor.has_status("Heal Blocked") and not actor.has_status("Heal Block"):
                numerator, denominator = start_fraction
                amount = int(math.floor(actor.max_hp() * numerator / max(1, denominator)))
                if amount > 0:
                    before = actor.hp or 0
                    actor.heal(amount)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "start_heal",
                            "amount": (actor.hp or 0) - before,
                            "target_hp": actor.hp,
                        }
                    )
            choice_stat = effects.get("choice_stat")
            if choice_stat:
                stat, amount = choice_stat
                current = actor.combat_stages.get(stat, 0)
                if current < amount:
                    actor.combat_stages[stat] = amount
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": name,
                            "effect": "choice_stat",
                            "stat": stat,
                            "amount": amount - current,
                            "new_stage": amount,
                            "target_hp": actor.hp,
                        }
                    )
                if effects.get("choice_suppressed") and not actor.has_status("Suppressed"):
                    actor.statuses.append({"name": "Suppressed", "source": name})
                    events.append(
                        {
                            "type": "status",
                            "actor": actor_id,
                            "status": "Suppressed",
                            "effect": "choice_item",
                            "item": name,
                            "description": "Choice item suppresses the holder.",
                            "target_hp": actor.hp,
                        }
                    )
            if normalized == "stat boosters":
                chosen_stat = ""
                if isinstance(item, dict):
                    chosen_stat = _normalize_stat_key(item.get("chosen_stat") or item.get("stat"))
                if chosen_stat:
                    current = actor.combat_stages.get(chosen_stat, 0)
                    if current < 1:
                        actor.combat_stages[chosen_stat] = 1
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "chosen_stat_boost",
                                "stat": chosen_stat,
                                "amount": 1 - current,
                                "new_stage": 1,
                                "target_hp": actor.hp,
                            }
                        )
            if normalized == "eviolite":
                chosen_stats: List[str] = []
                if isinstance(item, dict):
                    raw_stats = item.get("chosen_stats")
                    if isinstance(raw_stats, list):
                        chosen_stats = [_normalize_stat_key(value) for value in raw_stats]
                chosen_stats = [stat for stat in chosen_stats if stat in {"atk", "def", "spatk", "spdef", "spd"}]
                chosen_stats = list(dict.fromkeys(chosen_stats))[:2]
                for chosen_stat in chosen_stats:
                    if not _has_temp_effect("post_stage_stat_bonus", stat=chosen_stat, amount=5, source=name):
                        actor.add_temporary_effect(
                            "post_stage_stat_bonus",
                            stat=chosen_stat,
                            amount=5,
                            source=name,
                        )
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": name,
                                "effect": "chosen_post_stage_bonus",
                                "stat": chosen_stat,
                                "amount": 5,
                                "target_hp": actor.hp,
                            }
                        )
            crit_bonus = effects.get("crit_range_bonus")
            if crit_bonus:
                existing = any(
                    entry.get("kind") == "crit_range_bonus" and entry.get("source") == name
                    for entry in actor.get_temporary_effects("crit_range_bonus")
                )
                if not existing:
                    actor.add_temporary_effect("crit_range_bonus", bonus=crit_bonus, source=name)
                    applied_effects.append("crit_range_bonus")
            if len(events) == item_event_start and applied_effects:
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "item": name,
                        "effect": "held_item_active",
                        "applied_effects": sorted(set(applied_effects)),
                        "target_hp": actor.hp,
                    }
                )
        return events

    def apply_held_item_end(self, actor_id: str) -> List[dict]:
        battle = self.battle
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return []
        if battle._magic_room_active():
            return []
        events: List[dict] = []
        held_items = battle._iter_held_items(actor)
        for _idx, item, entry in held_items:
            effects = parse_item_effects(entry)
            end_ticks = effects.get("end_ticks")
            if end_ticks:
                amount = int(end_ticks) * actor.tick_value()
                before = actor.hp or 0
                if amount > 0:
                    actor.heal(amount)
                elif amount < 0:
                    actor.apply_damage(abs(amount))
                if amount != 0:
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "item": _item_name_text(item),
                            "effect": "end_ticks",
                            "amount": (actor.hp or 0) - before,
                            "target_hp": actor.hp,
                        }
                    )
            type_tick = effects.get("end_tick_type")
            if type_tick:
                type_name, tick_amount = type_tick
                actor_types = {t.lower().strip() for t in actor.spec.types if t}
                if type_name in actor_types:
                    amount = int(tick_amount) * actor.tick_value()
                    before = actor.hp or 0
                    if amount > 0:
                        actor.heal(amount)
                    elif amount < 0:
                        actor.apply_damage(abs(amount))
                    if amount != 0:
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": _item_name_text(item),
                                "effect": "end_ticks",
                                "amount": (actor.hp or 0) - before,
                                "target_hp": actor.hp,
                            }
                        )
            non_type_tick = effects.get("end_tick_non_type")
            if non_type_tick:
                type_name, tick_amount = non_type_tick
                actor_types = {t.lower().strip() for t in actor.spec.types if t}
                if type_name not in actor_types:
                    amount = int(tick_amount) * actor.tick_value()
                    before = actor.hp or 0
                    if amount > 0:
                        actor.heal(amount)
                    elif amount < 0:
                        actor.apply_damage(abs(amount))
                    if amount != 0:
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "item": _item_name_text(item),
                                "effect": "end_ticks",
                                "amount": (actor.hp or 0) - before,
                                "target_hp": actor.hp,
                            }
                        )
            end_fraction = effects.get("end_heal_fraction")
            if not end_fraction:
                continue
            if actor.has_status("Heal Blocked") or actor.has_status("Heal Block"):
                continue
            numerator, denominator = end_fraction
            amount = int(math.floor(actor.max_hp() * numerator / max(1, denominator)))
            if amount <= 0:
                continue
            before = actor.hp or 0
            actor.heal(amount)
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "item": _item_name_text(item),
                    "effect": "end_heal",
                    "amount": (actor.hp or 0) - before,
                    "target_hp": actor.hp,
                }
            )
        return events

    def apply_attacker_item_modifiers(
        self,
        attacker_id: str,
        attacker: PokemonState,
        move: MoveSpec,
        context,
    ) -> List[dict]:
        ctx = ItemHookContext(
            battle=self.battle,
            events=[],
            holder_id=attacker_id,
            holder=attacker,
            attacker_id=attacker_id,
            attacker=attacker,
            move=move,
            result={},
            phase="attacker_modifiers",
            attack_context=context,
        )
        return self.battle.hook_dispatcher.apply_item_hooks("attacker_modifiers", ctx)

    def apply_attacker_item_damage_bonus(
        self,
        attacker_id: str,
        attacker: PokemonState,
        move: MoveSpec,
        result: Dict[str, object],
        events: List[dict],
    ) -> None:
        ctx = ItemHookContext(
            battle=self.battle,
            events=events,
            holder_id=attacker_id,
            holder=attacker,
            attacker_id=attacker_id,
            attacker=attacker,
            move=move,
            result=result,
            phase="attacker_damage_bonus",
        )
        self.battle.hook_dispatcher.apply_item_hooks("attacker_damage_bonus", ctx)

    def apply_attacker_item_post_damage(
        self,
        attacker_id: str,
        attacker: PokemonState,
        target_id: str,
        target: PokemonState,
        move: MoveSpec,
        damage_dealt: int,
        result: Dict[str, object],
    ) -> List[dict]:
        ctx = ItemHookContext(
            battle=self.battle,
            events=[],
            holder_id=attacker_id,
            holder=attacker,
            attacker_id=attacker_id,
            attacker=attacker,
            target_id=target_id,
            target=target,
            move=move,
            result=result,
            phase="attacker_post_damage",
            damage_dealt=damage_dealt,
        )
        return self.battle.hook_dispatcher.apply_item_hooks("attacker_post_damage", ctx)

    def apply_defender_item_mitigation(
        self,
        defender_id: str,
        defender: PokemonState,
        attacker_id: str,
        move: MoveSpec,
        result: Dict[str, object],
        events: List[dict],
    ) -> None:
        ctx = ItemHookContext(
            battle=self.battle,
            events=events,
            holder_id=defender_id,
            holder=defender,
            attacker_id=attacker_id,
            attacker=self.battle.pokemon.get(attacker_id),
            move=move,
            result=result,
            phase="defender_mitigation",
        )
        self.battle.hook_dispatcher.apply_item_hooks("defender_mitigation", ctx)

    def apply_item_use(self, actor_id: str, target_id: str, item: object) -> List[dict]:
        battle = self.battle
        target = battle.pokemon.get(target_id)
        if target is None:
            return []
        name = _item_name_text(item)
        if not name:
            return []
        normalized = name.lower()
        actor_state = battle.pokemon.get(actor_id)
        events: List[dict] = []
        if normalized == "guard spec":
            target.add_temporary_effect(
                "combat_stage_guard",
                expires_round=battle.round + 5,
                source=name,
            )
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "combat_stage_guard",
                    "rounds": 5,
                    "target_hp": target.hp,
                }
            )
            return events
        if normalized == "honey" and target.has_ability("Honey Paws"):
            ability_name = "Honey Paws"
            if has_ability_exact(target, "Honey Paws [Errata]"):
                ability_name = "Honey Paws [Errata]"
            buffs = _food_buffs_from_items([{"name": "Leftovers"}])
            if buffs:
                target.add_food_buff(buffs[0], ignore_limit=True)
            else:
                target.add_food_buff(
                    {"name": "Leftovers", "effect": "Leftovers", "item": "Honey"},
                    ignore_limit=True,
                )
            events.append(
                {
                    "type": "ability",
                    "actor": actor_id,
                    "target": target_id,
                    "ability": ability_name,
                    "item": name,
                    "effect": "food_buff",
                    "description": "Honey Paws turns Honey into a Leftovers-style food buff.",
                    "target_hp": target.hp,
                }
            )
            return events
        entry = _item_entry_for(item)
        if entry is not None:
            effects = parse_item_effects(entry)
            parsed_events = battle._apply_item_effects_to_target(actor_id, target_id, item, effects)
            if parsed_events:
                return parsed_events

        def _iter_allies(max_distance: int | None = None) -> List[tuple[str, PokemonState]]:
            actor_team = battle._team_for(actor_id)
            actor_state = battle.pokemon.get(actor_id)
            origin = actor_state.position if actor_state is not None else None
            allies: List[tuple[str, PokemonState]] = []
            for pid, mon in battle.pokemon.items():
                if mon.hp is None or mon.hp <= 0 or not mon.active:
                    continue
                if actor_team:
                    mon_team = battle._team_for(pid)
                    if not mon_team or mon_team != actor_team:
                        continue
                if (
                    max_distance is not None
                    and battle.grid is not None
                    and origin is not None
                    and mon.position is not None
                    and targeting.chebyshev_distance(origin, mon.position) > max_distance
                ):
                    continue
                allies.append((pid, mon))
            return allies

        def _load_foundry_move_spec(slug: str) -> Optional[MoveSpec]:
            root = Path(__file__).resolve().parents[3]
            path = (
                root
                / "Foundry"
                / "ptr2e-Stable"
                / "ptr2e-Stable"
                / "packs"
                / "core-moves"
                / slug
            )
            if not path.exists():
                return None
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
            system = payload.get("system", {}) if isinstance(payload, dict) else {}
            actions = system.get("actions") or []
            action = actions[0] if isinstance(actions, list) and actions else {}
            move_type = "Normal"
            types = action.get("types") or []
            if isinstance(types, list) and types:
                move_type = str(types[0] or "Normal").title()
            category = str(action.get("category") or "status").strip().title()
            power = action.get("power")
            db = 0
            if isinstance(power, (int, float)):
                db = max(0, int(round(float(power) / 15.0)))
            accuracy = action.get("accuracy")
            ac = 2 if accuracy in (None, "", 100) else 4
            range_info = action.get("range") or {}
            distance = int(range_info.get("distance") or 1)
            range_kind = "Melee" if distance <= 1 else "Ranged"
            range_value = distance if distance > 1 else 1
            return MoveSpec(
                name=str(payload.get("name") or "").strip() or slug.replace("-", " ").title(),
                type=move_type,
                category=category or "Special",
                db=db,
                ac=ac,
                range_kind=range_kind,
                range_value=range_value,
                target_kind=range_kind,
                target_range=range_value,
                effects_text=str(action.get("description") or ""),
            )

        non_combat_items = {
            "batch pending item 1",
            "batch pending item 2",
            "waterproof flashlight",
            "waterproof lighter",
            "whipped dream",
            "white apricorn",
            "white light",
            "yellow apricorn",
            "yellow shard",
            "zap case",
            "thunder stone",
            "tinfoil gospel: your primer on thwarting the conspiracies of the new world order [5-15 playtest]",
            "tm - <attack name>",
            "tough fashion",
            "tough poffin",
            "traditional medicine reference [5-15 playtest]",
            "travel guide [5-15 playtest]",
            "type study manual [5-15 playtest]",
            "up-grade",
            "utility rope",
            "violet shard",
            "water filter",
            "water stone",
            "warp rigging",
            "sleeping bag",
            "sleeping bag (double)",
            "smart fashion",
            "smart poffin",
            "soldier pill",
            "soothe bell",
            "spray case",
            "stairs orb",
            "stat suppressants",
            "storage case",
            "study manual [5-15 playtest]",
            "sturdy rope",
            "sun stone",
            "super bait",
            "super repel",
            "tent",
            "tera orb",
            "the joy of cooking [5-15 playtest]",
            "pure seed",
            "radar orb",
            "rambo roids",
            "rare quality orb",
            "reaper cloth",
            "red apricorn",
            "red shard",
            "repel",
            "running shoes",
            "sachet",
            "saddle",
            "scanner orb",
            "scroll of masteries",
            "sealed air supply",
            "see-trap orb",
            "shiny stone",
            "shock syringe",
        }
        if normalized in non_combat_items:
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "non_combat_placeholder",
                    "description": "Non-combat item placeholder; resolved outside combat.",
                }
            ]
        if normalized == "quick orb":
            allies = _iter_allies()
            if not allies:
                return []
            expires_round = battle.round + 3
            for pid, mon in allies:
                mon.add_temporary_effect(
                    "movement_bonus",
                    mode="overland",
                    amount=4,
                    expires_round=expires_round,
                    source=name,
                )
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "movement_bonus",
                        "mode": "overland",
                        "amount": 4,
                        "expires_round": expires_round,
                        "target_hp": mon.hp,
                    }
                )
            return events
        if normalized == "rainy orb":
            battle.weather = "Rainy"
            return [
                {
                    "type": "weather",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "weather",
                    "weather": battle.weather,
                    "rounds": 3,
                    "description": "Rainy Orb sets Rainy weather for 3 rounds.",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "sunny orb":
            battle.weather = "Sunny"
            return [
                {
                    "type": "weather",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "weather",
                    "weather": battle.weather,
                    "rounds": 3,
                    "description": "Sunny Orb sets Sunny weather for 3 rounds.",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "sandy orb":
            battle.weather = "Dusty"
            return [
                {
                    "type": "weather",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "weather",
                    "weather": battle.weather,
                    "rounds": 3,
                    "description": "Sandy Orb sets Dusty weather for 3 rounds.",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "weather lock orb":
            battle.weather = "Clear"
            return [
                {
                    "type": "weather",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "weather",
                    "weather": battle.weather,
                    "rounds": 0,
                    "description": "Weather Lock Orb clears the weather.",
                    "target_hp": target.hp,
                }
            ]
        if normalized in {"z-crystal", "z-power-crystal"}:
            z_type = battle._item_type_from_item(item)
            if not target.get_temporary_effects("z_crystal_ready"):
                target.add_temporary_effect(
                    "z_crystal_ready",
                    z_type=z_type,
                    item=name,
                    round=battle.round,
                    source=name,
                )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "z_crystal_ready",
                    "z_type": z_type,
                    "target_hp": target.hp,
                }
            ]
        if normalized in {"wishing star", "zenith core"}:
            if not target.get_temporary_effects("zenith_core_ready"):
                target.add_temporary_effect(
                    "zenith_core_ready",
                    item=name,
                    round=battle.round,
                    source=name,
                )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "zenith_core_ready",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "trapper orb":
            if battle.grid is None:
                return []
            max_x = max(0, battle.grid.width - 2)
            max_y = max(0, battle.grid.height - 2)
            x = battle.rng.randint(0, max_x) if max_x > 0 else 0
            y = battle.rng.randint(0, max_y) if max_y > 0 else 0
            affected = []
            for dx in (0, 1):
                for dy in (0, 1):
                    coord = (x + dx, y + dy)
                    tile = battle.grid.tiles.setdefault(coord, {})
                    traps = tile.get("traps")
                    if not isinstance(traps, dict):
                        traps = {}
                        tile["traps"] = traps
                    traps["trap"] = 1
                    affected.append(coord)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "trapper_orb",
                    "tiles": affected,
                    "target_hp": target.hp,
                }
            ]
        if normalized == "two-edge orb":
            events = []
            for pid, mon in battle.pokemon.items():
                if mon.hp is None or mon.hp <= 0 or not mon.active:
                    continue
                before = mon.hp or 0
                damage = max(0, before // 2)
                if damage:
                    mon.apply_damage(damage)
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "two_edge_orb",
                        "amount": damage,
                        "target_hp": mon.hp,
                    }
                )
            return events
        if normalized == "warp orb":
            if battle.grid is None or target.position is None:
                return []
            open_tiles = [
                coord
                for coord in battle.grid.tiles.keys()
                if coord not in battle.grid.blockers
                and str(battle.grid.tiles.get(coord, {}).get("type") or "").lower() != "void"
            ]
            if not open_tiles:
                return []
            coord = battle.rng.choice(open_tiles)
            target.position = coord
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "warp_orb",
                    "position": coord,
                    "target_hp": target.hp,
                }
            ]
        if normalized == "warp seed":
            if battle.grid is None or target.position is None:
                return []
            open_tiles = [
                coord
                for coord in battle.grid.tiles.keys()
                if coord not in battle.grid.blockers
                and str(battle.grid.tiles.get(coord, {}).get("type") or "").lower() != "void"
            ]
            if not open_tiles:
                return []
            coord = battle.rng.choice(open_tiles)
            target.position = coord
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "warp_seed",
                    "position": coord,
                    "target_hp": target.hp,
                }
            ]
        if normalized == "reset urge":
            for stat in target.combat_stages:
                target.combat_stages[stat] = 0
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "reset_urge",
                    "description": "Reset Urge clears combat stages.",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "reset orb":
            actor_team = battle._team_for(actor_id)
            target_team = battle._team_for(target_id)
            affect_allies = actor_team and target_team and actor_team == target_team
            affected: List[str] = []
            for pid, mon in battle.pokemon.items():
                if mon.hp is None or mon.hp <= 0 or not mon.active:
                    continue
                mon_team = battle._team_for(pid)
                if actor_team and mon_team:
                    if affect_allies and mon_team != actor_team:
                        continue
                    if not affect_allies and mon_team == actor_team:
                        continue
                for stat in mon.combat_stages:
                    mon.combat_stages[stat] = 0
                affected.append(pid)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "reset_orb",
                    "targets": affected,
                    "description": "Reset Orb clears combat stages.",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "rollcall orb":
            actor_state = battle.pokemon.get(actor_id)
            origin = actor_state.position if actor_state is not None else None
            if battle.grid is None or origin is None:
                return [
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": target_id,
                        "item": name,
                        "effect": "rollcall_orb",
                        "description": "Rollcall Orb calls allies.",
                        "target_hp": target.hp,
                    }
                ]
            occupied = {
                mon.position
                for pid, mon in battle.pokemon.items()
                if mon.active and not mon.fainted and mon.position is not None
            }
            open_tiles: List[tuple[int, tuple[int, int]]] = []
            for x in range(battle.grid.width):
                for y in range(battle.grid.height):
                    coord = (x, y)
                    if coord in occupied:
                        continue
                    tile_info = battle.grid.tiles.get(coord, {})
                    if str(tile_info.get("type") or "").lower() == "void":
                        continue
                    if coord in battle.grid.blockers:
                        continue
                    dist = abs(coord[0] - origin[0]) + abs(coord[1] - origin[1])
                    open_tiles.append((dist, coord))
            open_tiles.sort(key=lambda entry: (entry[0], entry[1]))
            allies = [pair for pair in _iter_allies() if pair[0] != actor_id]
            for pid, mon in allies:
                if not open_tiles:
                    break
                _dist, coord = open_tiles.pop(0)
                mon.position = coord
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "rollcall_orb",
                        "position": coord,
                        "target_hp": mon.hp,
                    }
                )
            return events
        if normalized == "shock collar":
            if target.hp is None or target.hp <= 0:
                return []
            amount = max(1, int(math.floor(target.max_hp() / 6)))
            target.apply_damage(amount)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "shock_collar",
                    "amount": amount,
                    "target_hp": target.hp,
                }
            ]
        if normalized == "reveal glass":
            species_name = str(target.spec.species or "").strip().lower()
            therian_map = {
                "landorus": "Landorus Therian",
                "thundurus": "Thundurus Therian",
                "tornadus": "Tornadus Therian",
                "enamorus": "Enamorus Therian",
            }
            base_species = next((key for key in therian_map if key in species_name), "")
            if not base_species:
                return []
            form_name = therian_map[base_species]
            form_data = _species_form_data(form_name)
            if not form_data:
                return []
            target.add_temporary_effect(
                "form_change",
                species=form_name,
                base={
                    "atk": target.spec.atk,
                    "def": target.spec.defense,
                    "spatk": target.spec.spatk,
                    "spdef": target.spec.spdef,
                    "spd": target.spec.spd,
                    "hp_stat": target.spec.hp_stat,
                },
                types=list(target.spec.types),
                source=name,
            )
            battle._apply_form_stats(target, form_data, preserve_hp=True)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "form_change",
                    "form": form_name,
                    "target_hp": target.hp,
                }
            ]
        if normalized == "sizebust orb":
            if target.hp is None or target.hp <= 0:
                return []
            wc = target.weight_class()
            if wc <= 1:
                damage = 20
            elif wc <= 3:
                damage = 40
            elif wc <= 4:
                damage = 60
            elif wc <= 7:
                damage = 80
            elif wc <= 10:
                damage = 100
            else:
                damage = 120
            target.apply_damage(damage)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "sizebust_orb",
                    "damage": damage,
                    "weight_class": wc,
                    "target_hp": target.hp,
                }
            ]
        if normalized == "snatch orb":
            move_spec = next(
                (move for move in _load_move_specs() if str(move.name or "").strip().lower() == "snatch"),
                None,
            )
            if move_spec is None:
                move_spec = _load_foundry_move_spec("snatch.json")
            if move_spec is None:
                return []
            move_spec = copy.deepcopy(move_spec)
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "snatch_orb",
                    "move": move_spec.name,
                }
            )
            battle.resolve_move_targets(
                attacker_id=actor_id,
                move=move_spec,
                target_id=target_id,
                target_position=None,
            )
            return events
        if normalized == "soothing seed":
            for stat in target.combat_stages:
                target.combat_stages[stat] = 0
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "soothing_seed",
                    "description": "Soothing Seed clears combat stages.",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "spritz spray":
            if target.hp is None or target.hp <= 0:
                return []
            expires_round = battle.round + 5
            target.add_temporary_effect(
                "initiative_bonus",
                amount=5,
                expires_round=expires_round,
                source=name,
            )
            target.add_temporary_effect(
                "evasion_bonus",
                scope="all",
                amount=1,
                expires_round=expires_round,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "spritz_spray",
                    "initiative_bonus": 5,
                    "evasion_bonus": 1,
                    "expires_round": expires_round,
                    "target_hp": target.hp,
                }
            ]
        if normalized == "surround orb":
            actor_state = battle.pokemon.get(actor_id)
            origin = actor_state.position if actor_state is not None else None
            if battle.grid is None or target.position is None:
                return [
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": target_id,
                        "item": name,
                        "effect": "surround_orb",
                        "description": "Surround Orb teleports allies adjacent to the target.",
                        "target_hp": target.hp,
                    }
                ]
            if origin is not None and targeting.chebyshev_distance(origin, target.position) > 10:
                return []
            occupied = {
                mon.position
                for pid, mon in battle.pokemon.items()
                if mon.active and not mon.fainted and mon.position is not None
            }
            neighbors = list(movement.neighboring_tiles(target.position))
            open_tiles = [
                coord
                for coord in neighbors
                if battle.grid.in_bounds(coord)
                and coord not in occupied
                and str(battle.grid.tiles.get(coord, {}).get("type") or "").lower() != "void"
            ]
            allies = [pair for pair in _iter_allies() if pair[0] != actor_id]
            for pid, mon in allies:
                if not open_tiles:
                    break
                coord = open_tiles.pop(0)
                mon.position = coord
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "surround_orb",
                        "position": coord,
                        "target_hp": mon.hp,
                    }
                )
            return events
        if normalized == "switcher orb":
            actor_state = battle.pokemon.get(actor_id)
            if battle.grid is None or actor_state is None or actor_state.position is None:
                return []
            if target.position is None:
                return []
            actor_pos = actor_state.position
            target_pos = target.position
            actor_state.position, target.position = target_pos, actor_pos
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "switcher_orb",
                    "actor_position": actor_state.position,
                    "target_position": target.position,
                    "target_hp": target.hp,
                }
            ]

        if normalized in {"all-hit orb", "all-dodge orb", "align orb"}:
            allies = _iter_allies()
            if not allies:
                return []
            if normalized == "align orb":
                total_hp = sum(int(mon.hp or 0) for _pid, mon in allies)
                shared = int(total_hp // max(1, len(allies)))
                for pid, mon in allies:
                    before = mon.hp or 0
                    if shared > before:
                        mon.heal(shared - before)
                    elif shared < before:
                        mon.apply_damage(before - shared)
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "target": pid,
                            "item": name,
                            "effect": "align_orb",
                            "amount": (mon.hp or 0) - before,
                            "target_hp": mon.hp,
                        }
                    )
                return events
            expires_round = battle.round + 4
            if normalized == "all-hit orb":
                for pid, mon in allies:
                    mon.add_temporary_effect(
                        "crit_range_bonus",
                        bonus=1,
                        source=name,
                        expires_round=expires_round,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "target": pid,
                            "item": name,
                            "effect": "crit_range",
                            "amount": 1,
                            "target_hp": mon.hp,
                        }
                    )
                return events
            if normalized == "all-dodge orb":
                for pid, mon in allies:
                    mon.add_temporary_effect(
                        "evasion_bonus",
                        scope="all",
                        amount=2,
                        source=name,
                        expires_round=expires_round,
                    )
                    events.append(
                        {
                            "type": "item",
                            "actor": actor_id,
                            "target": pid,
                            "item": name,
                            "effect": "evasion_bonus",
                            "amount": 2,
                            "target_hp": mon.hp,
                        }
                    )
                return events

        if normalized == "all-mach orb":
            allies = _iter_allies()
            if not allies:
                return []
            for pid, mon in allies:
                mon.add_temporary_effect("extra_action", action="shift", round=battle.round, source=name)
                mon.add_temporary_effect("extra_action", action="swift", round=battle.round, source=name)
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "all_mach_orb",
                        "actions": ["shift", "swift"],
                        "target_hp": mon.hp,
                    }
                )
            return events

        if normalized == "lob orb":
            move_spec = MoveSpec(
                name="Lob Orb",
                type="Normal",
                category="Physical",
                db=7,
                ac=2,
                range_kind="Ranged",
                range_value=16,
                target_kind="Ranged",
                target_range=16,
                effects_text="Lob Orb attack.",
            )
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "lob_orb_attack",
                    "move": move_spec.name,
                }
            )
            battle.resolve_move_targets(
                attacker_id=actor_id,
                move=move_spec,
                target_id=target_id,
                target_position=None,
            )
            return events

        if normalized == "pounce orb":
            move_spec = next(
                (move for move in _load_move_specs() if str(move.name or "").strip().lower() == "pounce"),
                None,
            )
            if move_spec is None:
                move_spec = _load_foundry_move_spec("pounce.json")
            if move_spec is None:
                return []
            move_spec = copy.deepcopy(move_spec)
            if battle.grid is not None and actor.position is not None and target.position is not None:
                for coord in movement.neighboring_tiles(target.position):
                    if coord in battle.grid.tiles:
                        actor.position = coord
                        events.append(
                            {
                                "type": "item",
                                "actor": actor_id,
                                "target": target_id,
                                "item": name,
                                "effect": "pounce_orb_teleport",
                                "position": coord,
                                "target_hp": target.hp,
                            }
                        )
                        break
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "pounce_orb",
                    "move": move_spec.name,
                }
            )
            battle.resolve_move_targets(
                attacker_id=actor_id,
                move=move_spec,
                target_id=target_id,
                target_position=None,
            )
            return events

        if normalized == "mug orb":
            move_spec = next(
                (move for move in _load_move_specs() if str(move.name or "").strip().lower() == "thief"),
                None,
            )
            if move_spec is None:
                move_spec = _load_foundry_move_spec("thief.json")
            if move_spec is None:
                return []
            move_spec = copy.deepcopy(move_spec)
            move_spec.range_kind = "Ranged"
            move_spec.range_value = 10
            move_spec.target_kind = "Ranged"
            move_spec.target_range = 10
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "mug_orb_thief",
                    "move": move_spec.name,
                }
            )
            battle.resolve_move_targets(
                attacker_id=actor_id,
                move=move_spec,
                target_id=target_id,
                target_position=None,
            )
            return events

        if normalized == "one-shot orb":
            move_spec = next(
                (move for move in _load_move_specs() if str(move.name or "").strip().lower() == "guillotine"),
                None,
            )
            if move_spec is None:
                move_spec = _load_foundry_move_spec("guillotine.json")
            if move_spec is None:
                return []
            move_spec = copy.deepcopy(move_spec)
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "one_shot_orb",
                    "move": move_spec.name,
                }
            )
            battle.resolve_move_targets(
                attacker_id=actor_id,
                move=move_spec,
                target_id=target_id,
                target_position=None,
            )
            return events

        if normalized == "pierce orb":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None:
                return []
            apply_target.add_temporary_effect(
                "fling_pierce",
                remaining=1,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "fling_pierce",
                    "remaining": 1,
                    "range_mode": "line",
                    "target_hp": apply_target.hp,
                }
            ]

        if normalized == "puissance pellet":
            target.add_temporary_effect(
                "puissance_pellet",
                expires_round=battle.round + 5,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "puissance_pellet",
                    "expires_round": battle.round + 5,
                    "target_hp": target.hp,
                }
            ]

        if normalized == "aloraichium-z":
            species_name = str(target.spec.species or "").strip().lower()
            if species_name not in {"raichu alolan", "alolan raichu"}:
                return []
            move_spec = next(
                (move for move in _load_move_specs() if str(move.name or "").strip().lower() == "stoked sparksurfer"),
                None,
            )
            if move_spec is None:
                move_spec = _load_foundry_move_spec("stoked-sparksurfer.json")
            if move_spec is None:
                return []
            known = {str(mv.name or "").strip().lower() for mv in target.spec.moves}
            if str(move_spec.name or "").strip().lower() not in known:
                target.spec.moves.append(copy.deepcopy(move_spec))
                target.add_temporary_effect(
                    "z_move_granted",
                    name=move_spec.name,
                    round=battle.round,
                    source=name,
                )
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "z_move_unlocked",
                    "move": move_spec.name,
                    "target_hp": target.hp,
                }
            )
            return events

        if normalized == "jade orb":
            species_name = str(target.spec.species or "").strip().lower()
            if species_name != "rayquaza":
                return []
            existing = next(iter(target.get_temporary_effects("mega_form")), None)
            if existing is not None:
                return []
            form_data = _species_form_data("Mega Rayquaza")
            if not form_data:
                return []
            target.add_temporary_effect(
                "mega_form",
                species="Mega Rayquaza",
                base={
                    "atk": target.spec.atk,
                    "def": target.spec.defense,
                    "spatk": target.spec.spatk,
                    "spdef": target.spec.spdef,
                    "spd": target.spec.spd,
                    "hp_stat": target.spec.hp_stat,
                },
                types=list(target.spec.types),
                source=name,
            )
            battle._apply_form_stats(target, form_data, preserve_hp=True)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "mega_evolution",
                    "mega_form": "Mega Rayquaza",
                    "target_hp": target.hp,
                }
            ]

        if normalized == "prison bottle":
            species_name = str(target.spec.species or "").strip().lower()
            if "hoopa" not in species_name or "unbound" in species_name:
                return []
            form_data = {}
            for candidate in ("Hoopa Unbound", "Hoopa-Unbound", "Hoopa (Unbound)"):
                form_data = _species_form_data(candidate)
                if form_data:
                    break
            if not form_data:
                return []
            target.add_temporary_effect(
                "form_change",
                species="Hoopa Unbound",
                base={
                    "atk": target.spec.atk,
                    "def": target.spec.defense,
                    "spatk": target.spec.spatk,
                    "spdef": target.spec.spdef,
                    "spd": target.spec.spd,
                    "hp_stat": target.spec.hp_stat,
                },
                types=list(target.spec.types),
                source=name,
            )
            battle._apply_form_stats(target, form_data, preserve_hp=True)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "form_change",
                    "form": "Hoopa Unbound",
                    "target_hp": target.hp,
                }
            ]

        if normalized == "mega stone":
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "non_combat_placeholder",
                    "description": "Non-combat item placeholder; resolved outside combat.",
                }
            ]

        if normalized in {"altarianite", "ampharosite", "audinite", "banettite"} or (
            entry is not None
            and (
                "mega-stone" in (entry.description or "").lower()
                or "mega stone" in (entry.description or "").lower()
                or "mega evolves" in (entry.description or "").lower()
            )
        ):
            mega_map = {
                "altarianite": ("altaria", "Mega Altaria"),
                "ampharosite": ("ampharos", "Mega Ampharos"),
                "audinite": ("audino", "Mega Audino"),
                "banettite": ("banette", "Mega Banette"),
                "charizardite x": ("charizard", "Mega Charizard X"),
                "charizardite y": ("charizard", "Mega Charizard Y"),
                "manectite": ("manectric", "Mega Manectric"),
                "mawilite": ("mawile", "Mega Mawile"),
                "medichamite": ("medicham", "Mega Medicham"),
                "metagrossite": ("metagross", "Mega Metagross"),
                "mewtwonite x": ("mewtwo", "Mega Mewtwo X"),
                "mewtwonite y": ("mewtwo", "Mega Mewtwo Y"),
                "pidgeotite": ("pidgeot", "Mega Pidgeot"),
                "pinsirite": ("pinsir", "Mega Pinsir"),
            }
            base_species = ""
            mega_species = ""
            if normalized in mega_map:
                base_species, mega_species = mega_map[normalized]
            else:
                desc = entry.description or ""
                match = re.search(
                    r"mega[- ]stone attuned to the ([a-z0-9 '\\-]+) species",
                    desc,
                    re.IGNORECASE,
                )
                if not match:
                    match = re.search(
                        r"mega evolves (.+?) when",
                        desc,
                        re.IGNORECASE,
                    )
                if match:
                    base_species = match.group(1).strip()
                    mega_species = f"Mega {base_species}".strip()
            if not base_species or not mega_species:
                return []
            species_name = str(target.spec.species or "").strip().lower()
            if species_name != base_species.strip().lower():
                return []
            existing = next(iter(target.get_temporary_effects("mega_form")), None)
            if existing is not None:
                return []
            form_data = _species_form_data(mega_species)
            if not form_data:
                return []
            target.add_temporary_effect(
                "mega_form",
                species=mega_species,
                base={
                    "atk": target.spec.atk,
                    "def": target.spec.defense,
                    "spatk": target.spec.spatk,
                    "spdef": target.spec.spdef,
                    "spd": target.spec.spd,
                    "hp_stat": target.spec.hp_stat,
                },
                types=list(target.spec.types),
                source=name,
            )
            battle._apply_form_stats(target, form_data, preserve_hp=True)
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "mega_evolution",
                    "mega_form": mega_species,
                    "target_hp": target.hp,
                }
            )
            return events

        def _apply_status_item(
            *,
            status: str,
            apply_target_id: str,
            remaining: int | None = None,
            mode: str | None = None,
        ) -> List[dict]:
            apply_target = battle.pokemon.get(apply_target_id)
            if apply_target is None:
                return []
            if apply_target.hp is None or apply_target.hp <= 0:
                return []
            mode_key = str(mode or "").strip().lower()
            if mode_key == "disable_move":
                move_names = [
                    str(move.name).strip()
                    for move in (apply_target.spec.moves or [])
                    if isinstance(move, MoveSpec) and str(move.name or "").strip()
                ]
                if not move_names:
                    return []
                already_disabled = {
                    str((entry or {}).get("move") or "").strip().lower()
                    for entry in apply_target.statuses
                    if isinstance(entry, dict)
                    and str((entry or {}).get("name") or "").strip().lower() == "disabled"
                }
                choices = [move for move in move_names if move.lower() not in already_disabled] or move_names
                disabled_move = battle.rng.choice(choices)
                status_payload = {"name": "Disabled", "move": disabled_move}
                if remaining is not None:
                    status_payload["remaining"] = int(remaining)
                apply_target.statuses.append(status_payload)
                return [
                    {
                        "type": "status",
                        "actor": actor_id,
                        "target": apply_target_id,
                        "status": "Disabled",
                        "move": disabled_move,
                        "effect": "item_status",
                        "item": name,
                        "description": f"{name} disables {disabled_move}.",
                        "target_hp": apply_target.hp,
                    }
                ]
            if mode_key == "nullify_ability":
                status_events: List[dict] = []
                battle._apply_status(
                    status_events,
                    attacker_id=actor_id,
                    target_id=apply_target_id,
                    move=MoveSpec(name=name, type="Normal", category="Status"),
                    target=apply_target,
                    status=status,
                    effect="item_status",
                    description=f"{name} inflicts {status}.",
                    remaining=remaining,
                )
                ability_names = [str(choice).strip() for choice in apply_target.ability_names() if str(choice).strip()]
                if ability_names:
                    already_disabled = {
                        str((entry or {}).get("ability") or "").strip().lower()
                        for entry in apply_target.get_temporary_effects("ability_disabled")
                        if isinstance(entry, dict)
                    }
                    choices = [choice for choice in ability_names if choice.lower() not in already_disabled] or ability_names
                    chosen = battle.rng.choice(choices)
                    expires_round = battle.round + max(1, int(remaining or 5))
                    apply_target.add_temporary_effect(
                        "ability_disabled",
                        ability=chosen,
                        expires_round=expires_round,
                        source=name,
                    )
                    status_events.append(
                        {
                            "type": "ability",
                            "actor": actor_id,
                            "target": apply_target_id,
                            "ability": chosen,
                            "effect": "ability_disabled",
                            "item": name,
                            "description": f"{name} nullifies {chosen}.",
                            "target_hp": apply_target.hp,
                        }
                    )
                return status_events
            status_events: List[dict] = []
            battle._apply_status(
                status_events,
                attacker_id=actor_id,
                target_id=apply_target_id,
                move=MoveSpec(name=name, type="Normal", category="Status"),
                target=apply_target,
                status=status,
                effect="item_status",
                description=f"{name} inflicts {status}.",
                remaining=remaining,
            )
            if status_events:
                return status_events
            return []

        if normalized == "doom seed":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None or apply_target.hp is None or apply_target.hp <= 0:
                return []
            apply_target.add_temporary_effect("perish_song", count=3)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "perish_song",
                    "count": 3,
                    "description": "Doom Seed applies a Perish count.",
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "blast seed":
            if target is None or target.hp is None or target.hp <= 0:
                return []
            base_damage = 35
            hit_ids: List[str] = []
            actor_state = battle.pokemon.get(actor_id)
            if (
                battle.grid is not None
                and actor_state is not None
                and actor_state.position is not None
                and target.position is not None
            ):
                blast_move = MoveSpec(
                    name=name,
                    type="Fire",
                    category="Physical",
                    target_kind="Ranged",
                    target_range=3,
                    area_kind="Cone",
                    area_value=3,
                )
                affected = targeting.affected_tiles(
                    battle.grid,
                    actor_state.position,
                    target.position,
                    blast_move,
                )
                for pid, mon in sorted(battle.pokemon.items()):
                    if pid == actor_id:
                        continue
                    if not mon.active or mon.hp is None or mon.hp <= 0:
                        continue
                    if mon.position is None:
                        continue
                    if mon.position in affected:
                        hit_ids.append(pid)
            if not hit_ids and target_id and target_id != actor_id:
                hit_ids.append(target_id)
            events: List[dict] = []
            for pid in hit_ids:
                mon = battle.pokemon.get(pid)
                if mon is None or mon.hp is None or mon.hp <= 0:
                    continue
                before = mon.hp or 0
                mon.apply_damage(base_damage)
                dealt = max(0, before - (mon.hp or 0))
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "blast_seed_fling",
                        "move_type": "Fire",
                        "power": 35,
                        "accuracy": 100,
                        "area": "cone",
                        "area_value": 3,
                        "damage": dealt,
                        "description": "Blast Seed uses its fling stats in a 3m cone.",
                        "target_hp": mon.hp,
                    }
                )
            return events
        if normalized == "ability urge":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None or apply_target.hp is None or apply_target.hp <= 0:
                return []
            apply_target.add_temporary_effect("ability_urge", remaining=1, source=name)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "ability_urge",
                    "remaining": 1,
                    "description": "Ability Urge readies a triggered ability.",
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "acidic rock":
            apply_target = battle.pokemon.get(actor_id)
            if apply_target is None:
                return []
            apply_target.add_temporary_effect(
                "weather_duration_bonus",
                weather="smoggy",
                bonus=3,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": actor_id,
                    "item": name,
                    "effect": "weather_duration_bonus",
                    "weather": "Smoggy",
                    "bonus": 3,
                    "description": "Acidic Rock boosts Smoggy Weather duration.",
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "drought orb":
            apply_target = battle.pokemon.get(actor_id)
            if apply_target is None:
                return []
            move = MoveSpec(name="Drought Orb", type="Fire", category="Status")
            battle._apply_terrain(
                events,
                attacker_id=actor_id,
                move=move,
                name="Scorched Terrain",
                remaining=5,
                description="Drought Orb scorches the terrain.",
            )
            return events
        if normalized == "hail orb":
            apply_target = battle.pokemon.get(actor_id)
            if apply_target is None:
                return []
            battle.weather = "Snowy"
            return [
                {
                    "type": "weather",
                    "actor": actor_id,
                    "target": actor_id,
                    "item": name,
                    "effect": "weather",
                    "weather": battle.weather,
                    "rounds": 3,
                    "description": "Hail Orb sets Snowy weather for 3 rounds.",
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "encourage seed":
            return _apply_status_item(status="Amped", apply_target_id=target_id, remaining=5)
        if normalized == "heal seed":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None:
                return []
            cured = battle._remove_statuses_by_set(apply_target, _MAJOR_AFFLICTIONS)
            if not cured:
                return []
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "cure_status",
                    "statuses": sorted(set(cured)),
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "health orb":
            allies = _iter_allies()
            if not allies:
                return []
            events: List[dict] = []
            for pid, mon in allies:
                cured = battle._remove_statuses_by_set(mon, _MAJOR_AFFLICTIONS | _MINOR_AFFLICTIONS)
                if not cured:
                    continue
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "cure_status",
                        "statuses": sorted(set(cured)),
                        "target_hp": mon.hp,
                    }
                )
            return events
        if normalized == "evasion orb":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None or apply_target.hp is None or apply_target.hp <= 0:
                return []
            expires_round = battle.round + 5
            apply_target.add_temporary_effect(
                "evasion_bonus",
                scope="all",
                amount=1,
                source=name,
                expires_round=expires_round,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "evasion_bonus",
                    "amount": 1,
                    "expires_round": expires_round,
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "eject pack":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None:
                return []
            apply_target.add_temporary_effect(
                "eject_pack_ready",
                expires_round=battle.round + 1,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "eject_pack_ready",
                    "expires_round": battle.round + 1,
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized.endswith("-z"):
            z_type = None
            prefix = normalized[:-2]
            if prefix.endswith("ium"):
                z_type = Z_CRYSTAL_TYPES.get(prefix)
            if not target.get_temporary_effects("z_crystal_ready"):
                target.add_temporary_effect(
                    "z_crystal_ready",
                    z_type=z_type,
                    item=name,
                    round=battle.round,
                    source=name,
                )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "z_crystal_ready",
                    "z_type": z_type,
                    "target_hp": target.hp,
                }
            ]
        if normalized in CAPTURE_BALLS:
            if target_id == actor_id:
                return [
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": target_id,
                        "item": name,
                        "effect": "non_combat_placeholder",
                        "description": "Capture balls require a separate target in combat.",
                    }
                ]
            desc = (entry.description or "").strip() if entry is not None else ""
            base_modifier = 0
            multiplier = 1.0
            reasons: List[str] = []
            if desc:
                numeric = desc.strip()
                if re.fullmatch(r"[+-]?\d+", numeric):
                    base_modifier = int(numeric)
                else:
                    match = re.search(r"(\d+(?:\.\d+)?)x\s+catch rate", desc, re.IGNORECASE)
                    if match:
                        try:
                            multiplier = float(match.group(1))
                        except ValueError:
                            multiplier = 1.0
            weather = (battle.effective_weather() or battle.weather or "").strip().lower()
            has_flight = target.can_fly() or target.has_status("Flying") or target.has_status("In Flight")
            has_teleport = target.has_status("Teleporting") or target.has_status("Teleported")
            has_burrow = target.can_burrow() or target.has_status("Burrowed") or target.has_status("Underground")
            has_sleep = target.has_status("Sleep") or target.has_status("Drowsy") or target.has_status("Bad Sleep")
            if normalized == "dream ball":
                if has_sleep:
                    multiplier = 4.0
                    reasons.append("sleeping")
                else:
                    multiplier = 1.0
            if normalized == "beast ball":
                if _pokemon_has_trait(target, "ultra-beast", "ultra beast"):
                    multiplier = 5.0
                    reasons.append("ultra beast")
                else:
                    multiplier = 1.0
            if normalized == "dark ball":
                if _pokemon_has_trait(target, "closed-heart", "closed heart"):
                    multiplier = 5.0
                    reasons.append("closed-heart")
                else:
                    multiplier = 1.0
            if normalized == "strange ball":
                if _pokemon_has_trait(target, "paradox"):
                    multiplier = 5.0
                    reasons.append("paradox")
                else:
                    multiplier = 1.0
            if normalized == "vane ball":
                if "wind" in weather:
                    multiplier = 3.5
                    reasons.append("windy weather")
                else:
                    multiplier = 1.0
            if normalized == "beacon ball":
                if "fog" in weather:
                    multiplier = 3.5
                    reasons.append("foggy weather")
                else:
                    multiplier = 1.0
            if normalized == "smog ball":
                if "smog" in weather:
                    multiplier = 3.5
                    reasons.append("smoggy weather")
                else:
                    multiplier = 1.0
            if normalized == "coolant ball":
                if "nuclear" in [t.lower() for t in target.spec.types] or "glow" in weather:
                    multiplier = 3.5
                    reasons.append("nuclear or glowy weather")
                else:
                    multiplier = 1.0
            if normalized == "tiller ball":
                if has_burrow:
                    multiplier = 4.0
                    reasons.append("burrowing")
                else:
                    multiplier = 1.0
            if normalized == "wing ball":
                if has_flight or has_teleport:
                    multiplier = 2.0
                    reasons.append("flight/teleport")
                else:
                    multiplier = 1.0
            if normalized == "jet ball":
                if has_flight or has_teleport:
                    multiplier = 3.0
                    reasons.append("flight/teleport")
                else:
                    multiplier = 1.0
            if normalized == "feather ball":
                if has_flight:
                    multiplier = 1.25
                    reasons.append("flight")
                else:
                    multiplier = 1.0
            if normalized == "master ball":
                reasons.append("auto capture")
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_attempt",
                    "base_modifier": base_modifier,
                    "multiplier": multiplier,
                    "reasons": reasons,
                    "auto_success": normalized == "master ball",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "lasso orb":
            target_team = battle._team_for(target_id)
            targets: List[str] = []
            for pid, mon in battle.pokemon.items():
                if mon.hp is None or mon.hp <= 0 or not mon.active:
                    continue
                if target_team:
                    mon_team = battle._team_for(pid)
                    if not mon_team or mon_team != target_team:
                        continue
                targets.append(pid)
            if target_id not in targets:
                targets.append(target_id)
            events: List[dict] = []
            for pid in targets:
                events.extend(
                    _apply_status_item(status="Bound", apply_target_id=pid, remaining=5)
                )
            return events
        if normalized in {"hand net", "hand nets"}:
            if actor_state is None or target_id == actor_id:
                return []
            if _capture_tool_size_rank(getattr(target.spec, "size", "")) > 1:
                return [
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": target_id,
                        "item": name,
                        "effect": "capture_tool_size_blocked",
                        "tool": "hand net",
                        "description": "Hand Net may only net Small or smaller Pokemon.",
                        "target_hp": target.hp,
                    }
                ]
            accuracy = _capture_tool_accuracy(battle, actor_state, target, ac=6)
            events = [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_accuracy",
                    "tool": "hand net",
                    **accuracy,
                    "description": "Hand Net hits." if accuracy.get("hit") else "Hand Net misses.",
                    "target_hp": target.hp,
                }
            ]
            if not accuracy.get("hit"):
                return events
            target.add_temporary_effect(
                "capture_tool_trap",
                tool="hand net",
                source=name,
                capture_roll_modifier=-20,
            )
            events.extend(_apply_status_item(status="Trapped", apply_target_id=target_id))
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_trap",
                    "tool": "hand net",
                    "capture_roll_modifier": -20,
                    "description": "Hand Net traps the target; capture rolls against it gain a -20 bonus.",
                    "target_hp": target.hp,
                }
            )
            return events
        if normalized in {"weighted net", "weighted nets"}:
            if actor_state is None or target_id == actor_id:
                return []
            accuracy = _capture_tool_accuracy(battle, actor_state, target, ac=8)
            events = [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_accuracy",
                    "tool": "weighted net",
                    **accuracy,
                    "description": "Weighted Net hits." if accuracy.get("hit") else "Weighted Net misses.",
                    "target_hp": target.hp,
                }
            ]
            if not accuracy.get("hit"):
                return events
            target.add_temporary_effect(
                "capture_tool_trap",
                tool="weighted net",
                source=name,
                capture_roll_modifier=-20,
            )
            target.add_temporary_effect("force_grounded", source=name)
            events.extend(_apply_status_item(status="Slowed", apply_target_id=target_id))
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_trap",
                    "tool": "weighted net",
                    "capture_roll_modifier": -20,
                    "description": "Weighted Net slows and grounds the target; capture rolls against it gain a -20 bonus.",
                    "target_hp": target.hp,
                }
            )
            return events
        if normalized == "glue cannon":
            if actor_state is None or target_id == actor_id:
                return []
            accuracy = _capture_tool_accuracy(battle, actor_state, target, ac=8)
            events = [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_accuracy",
                    "tool": "glue cannon",
                    **accuracy,
                    "description": "Glue Cannon hits." if accuracy.get("hit") else "Glue Cannon misses.",
                    "target_hp": target.hp,
                }
            ]
            if not accuracy.get("hit"):
                return events
            target.add_temporary_effect("capture_tool_trap", tool="glue cannon", source=name)
            if accuracy.get("crit"):
                events.extend(_apply_status_item(status="Stuck", apply_target_id=target_id))
                events.extend(_apply_status_item(status="Trapped", apply_target_id=target_id))
                description = "Glue Cannon critically hits; the target is Stuck and Trapped."
            else:
                events.extend(_apply_status_item(status="Slowed", apply_target_id=target_id))
                description = "Glue Cannon slows the target."
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_trap",
                    "tool": "glue cannon",
                    "critical": bool(accuracy.get("crit")),
                    "description": description,
                    "target_hp": target.hp,
                }
            )
            return events
        if normalized in {"lasso", "lassos"}:
            if actor_state is None or target_id == actor_id:
                return []
            accuracy = _capture_tool_accuracy(battle, actor_state, target, ac=6)
            events = [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_accuracy",
                    "tool": "lasso",
                    **accuracy,
                    "description": "Lasso hits." if accuracy.get("hit") else "Lasso misses.",
                    "target_hp": target.hp,
                }
            ]
            if not accuracy.get("hit"):
                return events
            target.add_temporary_effect("capture_tool_trap", tool="lasso", source=name)
            events.extend(_apply_status_item(status="Trapped", apply_target_id=target_id))
            events.append(
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "capture_tool_trap",
                    "tool": "lasso",
                    "description": "Lasso traps the target.",
                    "target_hp": target.hp,
                }
            )
            return events
        if normalized == "trapbust orb":
            if battle.grid is None:
                return []
            hazards_cleared = False
            traps_cleared = False
            for tile in battle.grid.tiles.values():
                if not isinstance(tile, dict):
                    continue
                if "hazards" in tile and tile.get("hazards"):
                    tile["hazards"] = {}
                    hazards_cleared = True
                if "traps" in tile and tile.get("traps"):
                    tile["traps"] = {}
                    traps_cleared = True
            if not hazards_cleared and not traps_cleared:
                return []
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "trapbust",
                    "hazards_cleared": hazards_cleared,
                    "traps_cleared": traps_cleared,
                }
            ]
        if normalized == "blowback orb":
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "blowback_orb",
                    "move": "Whirlwind",
                    "description": "Blowback Orb lets the user freely use Whirlwind.",
                    "target_hp": target.hp,
                }
            ]
        if normalized in {
            "--",
            "a field guide to fungi [5-15 playtest]",
            "accessory",
            "body",
            "body + head",
            "bounce case",
            "black apricorn",
            "blank tm",
            "beauty fashion",
            "beauty poffin",
            "basic digivice",
            "blue apricorn",
            "blue shard",
            "camera kit",
            "chemistry set",
            "collection jar",
            "consumable",
            "cooking set",
            "cuirass",
            "pink apricorn",
            "poffin mixer",
            "poké ball alarm",
            "poké ball technical manual [5-15 playtest]",
            "poké ball tool box",
            "poké ball tracking chip",
            "pokédex",
            "pokémon daycare licensing guide [5-15 playtest]",
            "portable grower",
            "poultices",
            "protector",
            "cute fashion",
            "cute poffin",
            "dawn stone",
            "deep sea scale",
            "deep sea tooth",
            "deepseascale",
            "deepseatooth",
            "devil case",
            "devoncorp exo-rig",
            "devoncorp impact glove",
            "diy engineering [5-15 playtest]",
            "doctor's bag",
            "dowsing for dummies [5-15 playtest]",
            "dowsing rod",
            "dragon scale",
            "dubious disc",
            "dubious disk",
            "dusk stone",
            "egg warmer",
            "electirizer",
            "escape orb",
            "eva suit",
            "everstone",
            "feet",
            "first aid manual [5-15 playtest]",
            "fire stone",
            "fishing 101 [5-15 playtest]",
            "fishing lure",
            "flash case",
            "flashlight",
            "flippers",
            "galarica cuff",
            "galarica wreath",
            "green apricorn",
            "green shard",
            "groomer's kit",
            "hearty meal",
            "how berries?? [5-15 playtest]",
            "how to avoid being spooked [5-15 playtest]",
            "ice stone",
            "item",
            "key stone",
            "leaf stone",
            "lighter",
            "linking cord",
            "lock case",
            "locus lozenge",
            "magmarizer",
            "main + off hand",
            "main hand",
            "max repel",
            "medicine case",
            "mega stone",
            "memory",
            "microphone",
            "moon stone",
            "mulch",
            "nightvision goggles",
            "hands",
            "head",
            "heart booster",
            "heart scale",
            "off-hand",
            "old rod",
            "orange shard",
            "oval stone",
            "oxygenation vial",
            "personal forcefield",
        }:
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "non_combat_placeholder",
                    "description": "Non-combat item placeholder; resolved outside combat.",
                }
            ]
        if normalized == "revive all orb":
            actor_team = battle._team_for(actor_id)
            events: List[dict] = []
            for pid, mon in battle.pokemon.items():
                if mon.hp is None:
                    continue
                if actor_team:
                    mon_team = battle._team_for(pid)
                    if not mon_team or mon_team != actor_team:
                        continue
                if mon.hp > 0:
                    continue
                revived = max(1, int(math.floor(mon.max_hp() * 0.25)))
                mon.heal(revived)
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "revive_all",
                        "amount": revived,
                        "target_hp": mon.hp,
                    }
                )
            return events
        if normalized == "stayaway orb":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None:
                return []
            apply_target.active = False
            apply_target.position = None
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "stayaway",
                    "description": "Stayaway Orb removes the target from combat.",
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "spurn orb":
            actor_team = battle._team_for(actor_id)
            events: List[dict] = []
            for pid, mon in battle.pokemon.items():
                if mon.hp is None or mon.hp <= 0 or not mon.active:
                    continue
                if actor_team:
                    mon_team = battle._team_for(pid)
                    if mon_team and mon_team == actor_team:
                        continue
                mon.active = False
                mon.position = None
                events.append(
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": pid,
                        "item": name,
                        "effect": "spurn",
                        "description": "Spurn Orb removes the target from combat.",
                        "target_hp": mon.hp,
                    }
                )
            return events

        if normalized == "all-protect orb":
            allies = _iter_allies(max_distance=5)
            if not allies:
                return []
            for pid, _mon in allies:
                events.extend(
                    _apply_status_item(
                        status="Protect",
                        apply_target_id=pid,
                    )
                )
            return events
        if normalized == "cleanse orb":
            if battle.grid is None:
                return []
            clear_hazards(battle)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "hazard_clear",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "bait":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None:
                return []
            if apply_target.hp is None or apply_target.hp <= 0:
                return []
            roll = battle.rng.randint(1, 20)
            focus_bonus = apply_target.skill_rank("focus")
            total = roll + focus_bonus
            if total < 12:
                apply_target.add_temporary_effect(
                    "bait_distracted",
                    source=name,
                    expires_round=battle.round + 1,
                    dc=12,
                    roll=roll,
                    total=total,
                )
                status_events = _apply_status_item(
                    status="Flinched",
                    apply_target_id=target_id,
                    remaining=1,
                )
                if status_events:
                    for evt in status_events:
                        evt["roll"] = roll
                        evt["total"] = total
                        evt["dc"] = 12
                    return status_events
                return [
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": target_id,
                        "item": name,
                        "effect": "bait_blocked",
                        "roll": roll,
                        "total": total,
                        "dc": 12,
                        "target_hp": apply_target.hp,
                    }
                ]
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "bait_resisted",
                    "roll": roll,
                    "total": total,
                    "dc": 12,
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "baby food":
            if target.spec.level > 15:
                return []
            for entry in list(target.get_temporary_effects("exp_gain_multiplier")):
                if entry.get("source") == name and entry in target.temporary_effects:
                    target.temporary_effects.remove(entry)
            target.add_temporary_effect(
                "exp_gain_multiplier",
                multiplier=1.2,
                duration="day",
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "exp_gain_multiplier",
                    "multiplier": 1.2,
                    "duration": "day",
                    "target_hp": target.hp,
                }
            ]
        if normalized == "bandages":
            if target.hp is None or target.hp <= 0:
                return []
            for entry in list(target.get_temporary_effects("bandages")):
                if entry in target.temporary_effects:
                    target.temporary_effects.remove(entry)
            target.add_temporary_effect(
                "bandages",
                healing_multiplier=2.0,
                duration_hours=6,
                heal_injury_on_expire=True,
                break_on_damage=True,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "bandages_applied",
                    "duration_hours": 6,
                    "healing_multiplier": 2.0,
                    "target_hp": target.hp,
                }
            ]
        if normalized in {"bank orb", "bait attachment"}:
            trainer_id = actor_id if actor_id in battle.trainers else target.controller_id
            trainer = battle.trainers.get(trainer_id)
            if trainer is None:
                return []
            resources = trainer.feature_resources
            if normalized == "bank orb":
                resources["IP"] = int(resources.get("IP", 0) or 0) + 5
                trainer.feature_resources = resources
                return [
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": trainer_id,
                        "item": name,
                        "effect": "ip_recovered",
                        "amount": 5,
                    }
                ]
            resources["bait_attachment"] = int(resources.get("bait_attachment", 0) or 0) + 1
            trainer.feature_resources = resources
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": trainer_id,
                    "item": name,
                    "effect": "bait_attachment_loaded",
                    "amount": 1,
                }
            ]

        def _apply_status_scope(config: Dict[str, object]) -> List[dict]:
            status = str(config.get("status") or "").strip()
            if not status:
                return []
            remaining = config.get("remaining")
            remaining_value = int(remaining) if remaining is not None else None
            mode = str(config.get("mode") or "").strip().lower() or None
            scope = str(config.get("scope") or "target")
            scope_key = str(scope or "target").strip().lower()
            if scope_key == "target":
                return _apply_status_item(
                    status=status,
                    apply_target_id=target_id,
                    remaining=remaining_value,
                    mode=mode,
                )
            if scope_key == "self":
                return _apply_status_item(
                    status=status,
                    apply_target_id=actor_id,
                    remaining=remaining_value,
                    mode=mode,
                )
            if scope_key == "all_foes":
                actor_team = battle._team_for(actor_id)
                foe_ids: List[str] = []
                for pid, mon in battle.pokemon.items():
                    if pid == actor_id:
                        continue
                    if mon.hp is None or mon.hp <= 0 or not mon.active:
                        continue
                    if actor_team:
                        mon_team = battle._team_for(pid)
                        if mon_team and mon_team == actor_team:
                            continue
                    foe_ids.append(pid)
                events: List[dict] = []
                for foe_id in foe_ids:
                    events.extend(
                        _apply_status_item(
                            status=status,
                            apply_target_id=foe_id,
                            remaining=remaining_value,
                            mode=mode,
                        )
                    )
                return events
            return []

        # PMD-style consumables can be handled generically as direct status
        # inflictors even when Foundry text is terse.
        status_item_map: Dict[str, Dict[str, object]] = {
            "active camouflage": {"status": "Invisible", "scope": "self", "remaining": 5},
            "allure seed": {"status": "Charmed", "scope": "target", "remaining": 3},
            "decoy orb": {"status": "Marked", "scope": "target", "remaining": 5},
            "decoy seed": {"status": "Marked", "scope": "target", "remaining": 5},
            "destiny orb": {"status": "Destined", "scope": "target", "remaining": 5},
            "empowerment seed": {"status": "Boosted", "scope": "target", "remaining": 3},
            "identify orb": {"status": "True-Sight", "scope": "self", "remaining": 5},
            "invisify orb": {"status": "Invisible", "scope": "self", "remaining": 5},
            "sleep seed": {"status": "Drowsy", "scope": "target", "remaining": 3},
            "slumber orb": {"status": "Drowsy", "scope": "all_foes", "remaining": 5},
            "stun seed": {"status": "Paralyzed", "scope": "target", "remaining": 3},
            "shocker orb": {"status": "Paralyzed", "scope": "target", "remaining": 5},
            "rebound orb": {"status": "Rebound", "scope": "self", "remaining": 5},
            "rocky orb": {"status": "Splinter", "scope": "target", "remaining": 5},
            "totter seed": {"status": "Confused", "scope": "target", "remaining": 3},
            "totter orb": {"status": "Confused", "scope": "all_foes", "remaining": 5},
            "terror orb": {"status": "Bad Sleep", "scope": "all_foes", "remaining": 5},
            "slow orb": {"status": "Slowed", "scope": "all_foes", "remaining": 5},
            "silence orb": {"status": "Gagged", "scope": "target", "remaining": 5},
            "vanish seed": {"status": "Invisible", "scope": "target", "remaining": 3},
            "vile bait": {"status": "Poisoned", "scope": "target"},
            "foe-fear orb": {"status": "Fear", "scope": "all_foes", "remaining": 3},
            "ban seed": {"status": "Disabled", "scope": "target", "remaining": 5, "mode": "disable_move"},
            "foe-hold orb": {"status": "Trapped", "scope": "all_foes", "remaining": 3},
            "foe-seal orb": {"status": "Disabled", "scope": "all_foes", "remaining": 5, "mode": "disable_move"},
            "nullify orb": {"status": "Nullified", "scope": "all_foes", "remaining": 5, "mode": "nullify_ability"},
        }
        direct_status = status_item_map.get(normalized)
        if direct_status:
            return _apply_status_scope(direct_status)
        pester_match = re.match(r"^pester ball \(([^)]+)\)$", normalized)
        if pester_match:
            pester_token = pester_match.group(1).strip().lower()
            pester_status_map = {
                "burn": "Burned",
                "charmed": "Charmed",
                "confused": "Confused",
                "drowsy": "Drowsy",
                "enraged": "Enraged",
                "fear": "Fear",
                "frostbite": "Frostbite",
                "gagged": "Gagged",
                "grounded": "Grounded",
                "infested": "Infested",
                "blinded": "Blinded",
                "nullified": "Nullified",
                "paralysis": "Paralyzed",
                "paralyze": "Paralyzed",
                "poison": "Poisoned",
                "powder": "Powdered",
                "slow": "Slowed",
                "splinter": "Splinter",
                "stuck": "Stuck",
                "stunted": "Stunted",
                "suppressed": "Suppressed",
                "taunted": "Taunted",
            }
            pester_status = pester_status_map.get(pester_token)
            if pester_status:
                return _apply_status_item(
                    status=pester_status,
                    apply_target_id=target_id,
                    remaining=5,
                )
        if normalized == "pester ball":
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "pester_ball_choice_required",
                    "description": "Pester Ball requires an affliction selection.",
                    "target_hp": target.hp,
                }
            ]

        def _modify_base_stat(stat: str, delta: int, effect: str) -> List[dict]:
            if target.hp is None or target.hp <= 0:
                return []
            choices = dict(getattr(target.spec, "poke_edge_choices", {}) or {})
            vitamin_data = choices.get("vitamins_used", {})
            if not isinstance(vitamin_data, dict):
                vitamin_data = {}
            vitamin_stats = vitamin_data.get("stats", {})
            if not isinstance(vitamin_stats, dict):
                vitamin_stats = {}
            vitamin_total = max(0, int(vitamin_data.get("total", 0) or 0))
            trainer = battle.trainers.get(target.controller_id)
            vitamin_cap = 7 if trainer is not None and trainer.has_trainer_feature("Dietician") else 5
            if int(delta) > 0 and vitamin_total >= vitamin_cap:
                return [
                    {
                        "type": "item",
                        "actor": actor_id,
                        "target": target_id,
                        "item": name,
                        "effect": "vitamin_cap",
                        "stat": stat,
                        "cap": vitamin_cap,
                        "vitamins_used": vitamin_total,
                        "target_hp": target.hp,
                    }
                ]
            current = int(getattr(target.spec, stat))
            new_value = max(1, current + int(delta))
            if new_value == current:
                return []
            setattr(target.spec, stat, new_value)
            if int(delta) > 0:
                vitamin_stats[stat] = max(0, int(vitamin_stats.get(stat, 0) or 0)) + 1
                vitamin_total += 1
            elif int(delta) < 0:
                used_for_stat = max(0, int(vitamin_stats.get(stat, 0) or 0))
                if used_for_stat > 0:
                    next_used = used_for_stat - 1
                    if next_used > 0:
                        vitamin_stats[stat] = next_used
                    else:
                        vitamin_stats.pop(stat, None)
                    vitamin_total = max(0, vitamin_total - 1)
            choices["vitamins_used"] = {
                "total": vitamin_total,
                "stats": vitamin_stats,
            }
            target.spec.poke_edge_choices = choices
            if stat == "hp_stat":
                max_hp = target.max_hp()
                if (target.hp or 0) > max_hp:
                    target.hp = max_hp
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": effect,
                    "stat": stat,
                    "amount": new_value - current,
                    "vitamin_cap": vitamin_cap,
                    "vitamins_used": vitamin_total,
                    "target_hp": target.hp,
                }
            ]

        def _restore_frequency_usage(*, restore_all: bool, full: bool, effect: str) -> List[dict]:
            usage = battle.frequency_usage.get(target_id)
            if not usage:
                return []
            restored: List[dict] = []
            move_names = sorted(list(usage.keys()))
            if not restore_all:
                move_names = sorted(
                    move_names,
                    key=lambda move_name: (-int(usage.get(move_name, 0) or 0), move_name),
                )
            for move_name in move_names:
                current = int(usage.get(move_name, 0) or 0)
                if current <= 0:
                    continue
                new_usage = 0 if full else max(0, current - 1)
                if new_usage == current:
                    continue
                if new_usage <= 0:
                    usage.pop(move_name, None)
                else:
                    usage[move_name] = new_usage
                restored.append(
                    {
                        "move": move_name,
                        "restored": current - new_usage,
                    }
                )
                if not restore_all:
                    break
            if not usage:
                battle.frequency_usage.pop(target_id, None)
            if not restored:
                return []
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": effect,
                    "restored_moves": restored,
                    "target_hp": target.hp,
                }
            ]

        def _frequency_step_up(steps: int, *, effect: str) -> List[dict]:
            if target.hp is None or target.hp <= 0:
                return []
            upgrades: List[dict] = []
            for _ in range(max(0, int(steps))):
                move = battle._select_frequency_upgrade(target)
                if move is None:
                    break
                new_freq = battle._frequency_step_up_value(move.freq)
                if not new_freq:
                    break
                move.freq = new_freq
                battle.frequency_usage.get(target_id, {}).pop(move.name, None)
                upgrades.append({"move": move.name, "frequency": new_freq})
            if not upgrades:
                return []
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": effect,
                    "upgrades": upgrades,
                    "target_hp": target.hp,
                }
            ]

        def _increase_frequency_usage(*, amount: int, effect: str) -> List[dict]:
            if target.hp is None or target.hp <= 0:
                return []
            if not target.spec.moves:
                return []
            move = target.spec.moves[0]
            usage = battle.frequency_usage.setdefault(target_id, {})
            current = int(usage.get(move.name, 0) or 0)
            usage[move.name] = current + int(amount)
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": effect,
                    "move": move.name,
                    "amount": int(amount),
                    "target_hp": target.hp,
                }
            ]

        if normalized == "golden apple":
            events: List[dict] = []
            events.extend(
                _restore_frequency_usage(
                    restore_all=True,
                    full=False,
                    effect="pp_restore_all",
                )
            )
            events.extend(_frequency_step_up(1, effect="pp_up"))
            return events
        if normalized == "huge apple":
            return _restore_frequency_usage(
                restore_all=True,
                full=True,
                effect="pp_restore_all",
            )
        if normalized == "hunger seed":
            return _increase_frequency_usage(amount=3, effect="pp_loss")
        if normalized == "longtoss orb":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None:
                return []
            apply_target.add_temporary_effect(
                "fling_range_scalar",
                multiplier=2,
                remaining=5,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "fling_range_scalar",
                    "multiplier": 2,
                    "remaining": 5,
                    "target_hp": apply_target.hp,
                }
            ]
        if normalized == "herbal restorative":
            apply_target = battle.pokemon.get(target_id)
            if apply_target is None:
                return []
            apply_target.add_temporary_effect(
                "save_bonus",
                amount=2,
                expires_round=battle.round + 1,
                source=name,
            )
            return [
                {
                    "type": "item",
                    "actor": actor_id,
                    "target": target_id,
                    "item": name,
                    "effect": "save_bonus",
                    "amount": 2,
                    "target_hp": apply_target.hp,
                }
            ]

        heal_map = {
            "potion": 20,
            "super potion": 35,
            "hyper potion": 70,
            "enriched water": 20,
            "super soda pop": 30,
            "moomoo milk": 50,
            "lemonade": 40,
            "fresh water": 50,
            "full restore": 9999,
            "revive": "revive",
            "max revive": "revive_max",
            "reviver orb": "revive_max",
            "rare candy": "level_up",
            "hp up": "hp_up",
            "protein": "atk_up",
            "iron": "def_up",
            "calcium": "spatk_up",
            "zinc": "spdef_up",
            "carbos": "spd_up",
            "hp suppressant": "hp_down",
            "attack suppressant": "atk_down",
            "defense suppressant": "def_down",
            "special attack suppressant": "spatk_down",
            "special defense suppressant": "spdef_down",
            "speed suppressant": "spd_down",
            "pp up": "pp_up",
            "pp max": "pp_max",
            "ether": "ether",
            "max ether": "max_ether",
            "elixir": "elixir",
            "max elixir": "max_elixir",
            "medicinal leek": 5,
        }
        for key, value in heal_map.items():
            if normalized == key:
                if value == "revive":
                    if target.hp and target.hp > 0:
                        return []
                    amount = max(1, int(math.floor(target.max_hp() * 0.5)))
                    target.heal(amount)
                    return [
                        {
                            "type": "item",
                            "actor": actor_id,
                            "target": target_id,
                            "item": name,
                            "effect": "revive",
                            "amount": amount,
                            "target_hp": target.hp,
                        }
                    ]
                if value == "revive_max":
                    if target.hp and target.hp > 0:
                        return []
                    amount = target.max_hp()
                    target.heal(amount)
                    return [
                        {
                            "type": "item",
                            "actor": actor_id,
                            "target": target_id,
                            "item": name,
                            "effect": "revive",
                            "amount": amount,
                            "target_hp": target.hp,
                        }
                    ]
                if value == "level_up":
                    if target.hp is None or target.hp <= 0:
                        return []
                    target.spec.level += 1
                    gained: List[str] = []
                    top_percentage_bonus = 0
                    top_percentage_uses = 0
                    top_percentage_base_stats_applied = False
                    pools = load_foundry_species_abilities().get(
                        normalize_species_key(target.spec.species or target.spec.name or "")
                    )
                    if pools:
                        existing_names: List[str] = []
                        for entry in target.spec.abilities:
                            if isinstance(entry, dict):
                                name = entry.get("name")
                            else:
                                name = entry
                            if name:
                                existing_names.append(str(name))
                        updated_names, added = pick_abilities_for_level(
                            pools, target.spec.level, battle.rng, existing=existing_names
                        )
                        if added:
                            gained = added
                            target.spec.abilities = [{"name": name} for name in updated_names]
                    trainer = battle.trainers.get(target.controller_id)
                    if (
                        trainer is not None
                        and trainer.has_trainer_feature("Top Percentage")
                        and target.spec.level % 5 == 0
                    ):
                        choices = getattr(target.spec, "poke_edge_choices", {}) or {}
                        top_percentage_data = choices.get("top_percentage", {})
                        if not isinstance(top_percentage_data, dict):
                            top_percentage_data = {}
                        use_count = max(0, int(top_percentage_data.get("count", 0) or 0))
                        if use_count < 4:
                            use_count += 1
                            target.spec.tutor_points = max(
                                0,
                                int(getattr(target.spec, "tutor_points", 0) or 0) + 1,
                            )
                            top_percentage_bonus = 1
                            top_percentage_uses = use_count
                            top_percentage_data["count"] = use_count
                            if use_count >= 4 and not bool(
                                top_percentage_data.get("base_stats_applied", False)
                            ):
                                for attr in ("hp_stat", "atk", "defense", "spatk", "spdef", "spd"):
                                    setattr(
                                        target.spec,
                                        attr,
                                        max(1, int(getattr(target.spec, attr, 1) or 1) + 1),
                                    )
                                top_percentage_data["base_stats_applied"] = True
                                top_percentage_base_stats_applied = True
                            choices["top_percentage"] = top_percentage_data
                            target.spec.poke_edge_choices = choices
                    return [
                        {
                            "type": "item",
                            "actor": actor_id,
                            "target": target_id,
                            "item": name,
                            "effect": "level_up",
                            "new_level": target.spec.level,
                            "gained_abilities": gained,
                            "tutor_points_awarded": top_percentage_bonus,
                            "top_percentage_uses": top_percentage_uses,
                            "top_percentage_base_stats_applied": top_percentage_base_stats_applied,
                            "target_hp": target.hp,
                        }
                    ]
                if value == "hp_up":
                    return _modify_base_stat("hp_stat", 1, "hp_up")
                if value == "atk_up":
                    return _modify_base_stat("atk", 1, "stat_up")
                if value == "def_up":
                    return _modify_base_stat("defense", 1, "stat_up")
                if value == "spatk_up":
                    return _modify_base_stat("spatk", 1, "stat_up")
                if value == "spdef_up":
                    return _modify_base_stat("spdef", 1, "stat_up")
                if value == "spd_up":
                    return _modify_base_stat("spd", 1, "stat_up")
                if value == "hp_down":
                    return _modify_base_stat("hp_stat", -1, "stat_down")
                if value == "atk_down":
                    return _modify_base_stat("atk", -1, "stat_down")
                if value == "def_down":
                    return _modify_base_stat("defense", -1, "stat_down")
                if value == "spatk_down":
                    return _modify_base_stat("spatk", -1, "stat_down")
                if value == "spdef_down":
                    return _modify_base_stat("spdef", -1, "stat_down")
                if value == "spd_down":
                    return _modify_base_stat("spd", -1, "stat_down")
                if value == "ether":
                    return _restore_frequency_usage(
                        restore_all=False,
                        full=False,
                        effect="pp_restore",
                    )
                if value == "max_ether":
                    return _restore_frequency_usage(
                        restore_all=False,
                        full=True,
                        effect="pp_restore",
                    )
                if value == "elixir":
                    return _restore_frequency_usage(
                        restore_all=True,
                        full=False,
                        effect="pp_restore_all",
                    )
                if value == "max_elixir":
                    return _restore_frequency_usage(
                        restore_all=True,
                        full=True,
                        effect="pp_restore_all",
                    )
                if value == "pp_up":
                    return _frequency_step_up(1, effect="pp_up")
                if value == "pp_max":
                    return _frequency_step_up(2, effect="pp_max")
                if isinstance(value, int):
                    if target.hp is None or target.hp <= 0:
                        return []
                    if target.has_status("Heal Blocked") or target.has_status("Heal Block"):
                        return []
                    before = target.hp or 0
                    target.heal(int(value))
                    return [
                        {
                            "type": "item",
                            "actor": actor_id,
                            "target": target_id,
                            "item": name,
                            "effect": "heal",
                            "amount": (target.hp or 0) - before,
                            "target_hp": target.hp,
                        }
                    ]
        return events
