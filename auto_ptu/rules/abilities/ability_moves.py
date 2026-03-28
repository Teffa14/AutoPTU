"""Ability move definitions and post-init effects."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from ...data_models import MoveSpec
from .constants import COLOR_THEORY_COLORS
from .ability_variants import has_ability_exact, has_errata

if TYPE_CHECKING:
    from ..battle_state import PokemonState


_MOVE_SPEC_CACHE: Optional[Dict[str, MoveSpec]] = None


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
    return _MOVE_SPEC_CACHE


def _lookup_move_spec(name: str) -> Optional[MoveSpec]:
    if not name:
        return None
    return _load_move_spec_cache().get(name.strip().lower())


def _rotom_form_key(species: str) -> Optional[str]:
    text = (species or "").strip().lower()
    if "rotom" not in text:
        return None
    if "heat" in text or "rotom h" in text or "rotom-h" in text or "rotom (h)" in text:
        return "heat"
    if "wash" in text or "rotom w" in text or "rotom-w" in text or "rotom (w)" in text:
        return "wash"
    if "frost" in text or "rotom fr" in text or "rotom-fr" in text or "rotom (fr)" in text:
        return "frost"
    if "fan" in text or "rotom fn" in text or "rotom-fn" in text or "rotom (fn)" in text:
        return "fan"
    if "mow" in text or "rotom m" in text or "rotom-m" in text or "rotom (m)" in text:
        return "mow"
    return None


def build_ability_moves(pokemon: "PokemonState") -> List[MoveSpec]:
    ability_moves: List[MoveSpec] = []
    if pokemon.has_ability("Blessed Touch"):
        ability_moves.append(
            MoveSpec(
                name="Blessed Touch",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Daily x2",
                range_text="Melee, 1 Target",
                effects_text="Ability action: restore 1/4 max HP to an adjacent ally.",
            )
        )
    if pokemon.has_ability("Cherry Power"):
        ability_moves.append(
            MoveSpec(
                name="Cherry Power",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: gain 15 temp HP and cure persistent status afflictions.",
            )
        )
    if has_ability_exact(pokemon, "Clay Cannons"):
        ability_moves.append(
            MoveSpec(
                name="Clay Cannons",
                type="Ground",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: originate ranged moves from adjacent squares this round.",
            )
        )
    if has_ability_exact(pokemon, "Clay Cannons [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Clay Cannons [Errata]",
                type="Ground",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: originate ranged moves within 2 meters this round.",
            )
        )
    if has_ability_exact(pokemon, "Celebrate [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Celebrate [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: ready a free Disengage after a damaging hit.",
            )
        )
    if has_ability_exact(pokemon, "Danger Syrup [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Danger Syrup [Errata]",
                type="Poison",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: use Sweet Scent as a free action.",
            )
        )
    if pokemon.has_ability("Cloud Nine"):
        ability_moves.append(
            MoveSpec(
                name="Cloud Nine",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: reset the weather to normal.",
            )
        )
    if pokemon.has_ability("Accelerate"):
        ability_moves.append(
            MoveSpec(
                name="Accelerate",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: your next STAB damaging move gains Priority and bonus damage.",
                priority=1,
            )
        )
    if pokemon.has_ability("Battery"):
        ability_moves.append(
            MoveSpec(
                name="Battery",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene x2",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: the target's next special attack gains bonus damage.",
            )
        )
    if pokemon.has_ability("Comatose"):
        ability_moves.append(
            MoveSpec(
                name="Comatose",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: fall asleep and heal a tick, while still acting normally.",
            )
        )
    if pokemon.has_ability("Curious Medicine"):
        ability_moves.append(
            MoveSpec(
                name="Curious Medicine",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 2, Allies",
                effects_text="Ability action: reset allies' combat stages in Burst 2.",
            )
        )
    if pokemon.has_ability("Dazzling"):
        ability_moves.append(
            MoveSpec(
                name="Dazzling",
                type="Fairy",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene x2",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: suppress priority and lower initiative.",
            )
        )
    if pokemon.has_ability("Full Guard"):
        ability_moves.append(
            MoveSpec(
                name="Full Guard",
                type="Fighting",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: resist the next hit one step further.",
            )
        )
    if pokemon.has_ability("Ice Face"):
        ability_moves.append(
            MoveSpec(
                name="Ice Face",
                type="Ice",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: in hail, gain two ticks of temporary HP.",
            )
        )
    if pokemon.has_ability("Stamina"):
        ability_moves.append(
            MoveSpec(
                name="Stamina",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: raise Defense by 1 Combat Stage.",
            )
        )
    if pokemon.has_ability("Leafy Cloak"):
        ability_moves.append(
            MoveSpec(
                name="Leafy Cloak",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: choose two of Chlorophyll, Leaf Guard, Overcoat.",
            )
        )
    if pokemon.has_ability("Pack Hunt"):
        ability_moves.append(
            MoveSpec(
                name="Pack Hunt",
                type="Normal",
                category="Status",
                db=0,
                ac=5,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="At-Will",
                range_text="Melee, 1 Target",
                effects_text="Ability action: make an AC 5 strike that deals a tick on hit.",
            )
        )
    if pokemon.has_ability("Parry"):
        ability_moves.append(
            MoveSpec(
                name="Parry",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: ready a parry to negate a melee hit.",
            )
        )
    if pokemon.has_ability("Perception"):
        ability_moves.append(
            MoveSpec(
                name="Perception",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: ready to shift out of an area attack.",
            )
        )
    if pokemon.has_ability("Pickup"):
        ability_moves.append(
            MoveSpec(
                name="Pickup",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: roll 1d20 and consult the Pickup keyword.",
            )
        )
    if pokemon.has_ability("Pixilate"):
        ability_moves.append(
            MoveSpec(
                name="Pixilate",
                type="Fairy",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: your next Normal move becomes Fairy-type.",
            )
        )
    if has_ability_exact(pokemon, "Prime Fury [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Prime Fury [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: become Enraged and raise Attack and Special Attack by 1 CS.",
            )
        )
    elif pokemon.has_ability("Prime Fury") and not has_errata(pokemon, "Prime Fury"):
        ability_moves.append(
            MoveSpec(
                name="Prime Fury",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: become Enraged and raise Attack by 1 CS.",
            )
        )
    if pokemon.has_ability("Probability Control"):
        ability_moves.append(
            MoveSpec(
                name="Probability Control",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: allow a reroll for the target's next roll.",
            )
        )
    if has_ability_exact(pokemon, "Pumpkingrab [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Pumpkingrab [Errata]",
                type="Ghost",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Scene",
                range_text="Melee, 1 Target",
                effects_text="Ability action: automatically Grapple an adjacent foe and gain dominance.",
            )
        )
    if pokemon.has_ability("Protean"):
        ability_moves.append(
            MoveSpec(
                name="Protean",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: your next move changes your type to match it.",
            )
        )
    if pokemon.has_ability("Quick Cloak"):
        ability_moves.append(
            MoveSpec(
                name="Quick Cloak",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: Burmy builds a cloak that changes its type.",
            )
        )
    if has_ability_exact(pokemon, "Quick Curl [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Quick Curl [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: ready Defense Curl as an interrupt and gain +10 damage reduction for 1 round.",
            )
        )
    elif pokemon.has_ability("Quick Curl") and not has_errata(pokemon, "Quick Curl"):
        ability_moves.append(
            MoveSpec(
                name="Quick Curl",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: ready Defense Curl as a Swift Action.",
            )
        )
    if has_ability_exact(pokemon, "Rattled [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Rattled [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: when hit by Bug/Dark/Ghost, raise Speed by 1 CS and Disengage.",
            )
        )
    elif pokemon.has_ability("Rattled") and not has_errata(pokemon, "Rattled"):
        ability_moves.append(
            MoveSpec(
                name="Rattled",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: raise Speed by 1 CS.",
            )
        )
    if pokemon.has_ability("Refridgerate"):
        ability_moves.append(
            MoveSpec(
                name="Refridgerate",
                type="Ice",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: your next Normal move becomes Ice-type.",
            )
        )
    if has_ability_exact(pokemon, "Root Down [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Root Down [Errata]",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: while Ingrained, gain +5 damage reduction for 1 round.",
            )
        )
    elif pokemon.has_ability("Root Down") and not has_errata(pokemon, "Root Down"):
        ability_moves.append(
            MoveSpec(
                name="Root Down",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: while Ingrained, gain 1/16 max HP as temp HP.",
            )
        )
    if has_ability_exact(pokemon, "Shackle [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Shackle [Errata]",
                type="Ghost",
                category="Status",
                db=0,
                ac=None,
                range_kind="Burst",
                range_value=3,
                target_kind="Burst",
                target_range=3,
                area_kind="Burst",
                area_value=3,
                freq="Scene",
                range_text="Burst 3",
                effects_text="Ability action: foes in Burst 3 have movement halved until end of next turn.",
            )
        )
    elif pokemon.has_ability("Shackle") and not has_errata(pokemon, "Shackle"):
        ability_moves.append(
            MoveSpec(
                name="Shackle",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Burst",
                range_value=3,
                area_kind="Burst",
                area_value=3,
                target_kind="Self",
                freq="Scene",
                range_text="Burst 3, Enemies",
                effects_text="Ability action: halve foes' movement in Burst 3.",
            )
        )
    if pokemon.has_ability("Shadow Tag"):
        ability_moves.append(
            MoveSpec(
                name="Shadow Tag",
                type="Ghost",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Scene",
                range_text="Melee, 1 Target",
                effects_text="Ability action: pin a target's shadow in place.",
            )
        )
    if pokemon.has_ability("Shell Cannon"):
        ability_moves.append(
            MoveSpec(
                name="Shell Cannon",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: boost accuracy and damage on select moves.",
            )
        )
    if has_ability_exact(pokemon, "Shell Shield [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Shell Shield [Errata]",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: ready Withdraw as an interrupt and gain +10 damage reduction for 1 round.",
            )
        )
    elif pokemon.has_ability("Shell Shield") and not has_errata(pokemon, "Shell Shield"):
        ability_moves.append(
            MoveSpec(
                name="Shell Shield",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: ready Withdraw as an interrupt.",
            )
        )
    if has_ability_exact(pokemon, "Solar Power [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Solar Power [Errata]",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: on your next damage roll, lose a tick and add 5 + tick value to damage.",
            )
        )
    if has_ability_exact(pokemon, "Sonic Courtship [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Sonic Courtship [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: Attract becomes Burst 3, Sonic, Friendly this round.",
            )
        )
    elif pokemon.has_ability("Sonic Courtship") and not has_errata(pokemon, "Sonic Courtship"):
        ability_moves.append(
            MoveSpec(
                name="Sonic Courtship",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: Attract becomes a sonic cone this round.",
            )
        )
    if has_ability_exact(pokemon, "Sound Lance [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Sound Lance [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: Supersonic deals special damage even if it misses.",
            )
        )
    elif pokemon.has_ability("Sound Lance") and not has_errata(pokemon, "Sound Lance"):
        ability_moves.append(
            MoveSpec(
                name="Sound Lance",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: Supersonic deals bonus damage.",
            )
        )
    if has_ability_exact(pokemon, "Suction Cups [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Suction Cups [Errata]",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: gain +5 damage reduction for 1 round.",
            )
        )
    if has_ability_exact(pokemon, "Sumo Stance [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Sumo Stance [Errata]",
                type="Fighting",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: after a melee hit, push the target 1m and gain push immunity for 1 round.",
            )
        )
    if pokemon.has_ability("Strange Tempo"):
        ability_moves.append(
            MoveSpec(
                name="Strange Tempo",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: cure confusion and boost a combat stage.",
            )
        )
    if pokemon.has_ability("Leaf Rush"):
        ability_moves.append(
            MoveSpec(
                name="Leaf Rush",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: your next Grass move gains Priority and bonus damage.",
                priority=1,
            )
        )
    if pokemon.has_ability("Maelstrom Pulse") or pokemon.has_ability("Maestrom Pulse"):
        ability_moves.append(
            MoveSpec(
                name="Maelstrom Pulse",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: your next Water move gains Priority and bonus damage.",
                priority=1,
            )
        )
    if pokemon.has_ability("Mimicry"):
        ability_moves.append(
            MoveSpec(
                name="Mimicry",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: change type to match the field.",
            )
        )
    if pokemon.has_ability("Missile Launch"):
        ability_moves.append(
            MoveSpec(
                name="Missile Launch",
                type="Dragon",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene x2",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: deploy Dreepy tokens.",
            )
        )
    if pokemon.has_ability("Mud Shield"):
        ability_moves.append(
            MoveSpec(
                name="Mud Shield",
                type="Ground",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: gain two ticks of temporary HP.",
            )
        )
    if pokemon.has_ability("Electric Surge"):
        ability_moves.append(
            MoveSpec(
                name="Electric Surge",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Self",
                effects_text="Ability action: set Electric Terrain for one round.",
            )
        )
    if pokemon.has_ability("Grassy Surge"):
        ability_moves.append(
            MoveSpec(
                name="Grassy Surge",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Self",
                effects_text="Ability action: set Grassy Terrain for one round.",
            )
        )
    if pokemon.has_ability("Misty Surge"):
        ability_moves.append(
            MoveSpec(
                name="Misty Surge",
                type="Fairy",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Self",
                effects_text="Ability action: set Misty Terrain for one round.",
            )
        )
    if pokemon.has_ability("Psychic Surge"):
        ability_moves.append(
            MoveSpec(
                name="Psychic Surge",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Self",
                effects_text="Ability action: set Psychic Terrain for one round.",
            )
        )
    if pokemon.has_ability("Confidence"):
        ability_moves.append(
            MoveSpec(
                name="Confidence",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 5, Allies",
                effects_text="Ability action: allies within 5 gain +1 CS in a chosen stat.",
            )
        )
    if has_ability_exact(pokemon, "Download"):
        ability_moves.append(
            MoveSpec(
                name="Download",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: analyze a foe to boost damage against its weaker defense.",
            )
        )
    if has_ability_exact(pokemon, "Download [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Download [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text=(
                    "Ability action: compare the target's Defense and Special Defense; "
                    "gain +1 CS to Attack or Special Attack (or any stat on a tie)."
                ),
            )
        )
    if pokemon.has_ability("Daze"):
        ability_moves.append(
            MoveSpec(
                name="Daze",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: inflict Sleep on a hit target.",
            )
        )
    if pokemon.has_ability("Decoy"):
        ability_moves.append(
            MoveSpec(
                name="Decoy",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: use Follow Me and gain +2 evasion until the end of the next turn.",
            )
        )
    if pokemon.has_ability("Defy Death"):
        ability_moves.append(
            MoveSpec(
                name="Defy Death",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: heal up to 2 injuries and raise the death threshold.",
            )
        )
    if has_ability_exact(pokemon, "Defy Death [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Defy Death [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: heal up to 3 injuries and gain a tick of HP per injury.",
            )
        )
    if pokemon.has_ability("Dreamspinner"):
        ability_moves.append(
            MoveSpec(
                name="Dreamspinner",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Burst 10",
                effects_text="Ability action: heal a tick for each sleeping foe within 10 meters.",
            )
        )
    if has_ability_exact(pokemon, "Dreamspinner [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Dreamspinner [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Burst 3",
                effects_text="Ability action: drain a tick from sleeping foes within 3 meters and gain temp HP.",
            )
        )
    if pokemon.has_ability("Drizzle"):
        ability_moves.append(
            MoveSpec(
                name="Drizzle",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: set rainy weather for 5 rounds.",
            )
        )
    if has_ability_exact(pokemon, "Drizzle [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Drizzle [Errata]",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Self",
                effects_text="Ability action: set rainy weather for 1 round.",
            )
        )
    if has_ability_exact(pokemon, "Drought [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Drought [Errata]",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Self",
                effects_text="Ability action: set sunny weather for 1 round.",
            )
        )
    if pokemon.has_ability("Drought"):
        ability_moves.append(
            MoveSpec(
                name="Drought",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: set sunny weather for 5 rounds.",
            )
        )
    if has_ability_exact(pokemon, "Sand Stream [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Sand Stream [Errata]",
                type="Rock",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x3",
                range_text="Self",
                effects_text="Ability action: summon Sandstorm for 1 round; you are immune to sandstorm damage.",
            )
        )
    elif pokemon.has_ability("Sand Stream") and not has_errata(pokemon, "Sand Stream"):
        ability_moves.append(
            MoveSpec(
                name="Sand Stream",
                type="Rock",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: set sandstorm weather for 5 rounds.",
            )
        )
    if pokemon.has_ability("Snow Warning"):
        ability_moves.append(
            MoveSpec(
                name="Snow Warning",
                type="Ice",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: set hail weather for 5 rounds.",
            )
        )
    if has_ability_exact(pokemon, "Electrodash"):
        ability_moves.append(
            MoveSpec(
                name="Electrodash",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: gain Sprint movement for the round.",
            )
        )
    if pokemon.has_ability("Fade Away"):
        ability_moves.append(
            MoveSpec(
                name="Fade Away",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: become invisible until next turn and shift.",
            )
        )
    if pokemon.has_ability("Fashion Designer"):
        ability_moves.append(
            MoveSpec(
                name="Fashion Designer",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: craft a leaf accessory (Lucky Leaf, Tasty Reeds, Dew Cup, Thorn Mantle, Chewy Cluster, Decorative Twine).",
            )
        )
    if pokemon.has_ability("Designer"):
        ability_moves.append(
            MoveSpec(
                name="Designer",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: craft a leaf accessory (Lucky Leaf, Tasty Reeds, Dew Cup, Thorn Mantle, Chewy Cluster, Decorative Twine).",
            )
        )
    if has_ability_exact(pokemon, "Flare Boost [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Flare Boost [Errata]",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: while Burned, gain +3 Attack and +3 Special Attack CS.",
            )
        )
    if has_ability_exact(pokemon, "Flower Gift [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Flower Gift [Errata]",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 2, Allies",
                effects_text=(
                    "Ability action: in sun or under 50% HP, pick two stats; gain +2 CS and allies in Burst 2 gain +1."
                ),
            )
        )
    elif pokemon.has_ability("Flower Gift") and not has_errata(pokemon, "Flower Gift"):
        ability_moves.append(
            MoveSpec(
                name="Flower Gift",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 4, Allies",
                effects_text="Ability action: in sunlight, allies in Burst 4 gain +2 CS divided as chosen.",
            )
        )
    if pokemon.has_ability("Flutter"):
        ability_moves.append(
            MoveSpec(
                name="Flutter",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: gain +3 evasion and cannot be flanked until next turn.",
            )
        )
    if pokemon.has_ability("Forest Lord"):
        ability_moves.append(
            MoveSpec(
                name="Forest Lord",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: originate Grass/Ghost moves from nearby trees with +2 accuracy this turn.",
            )
        )
    if pokemon.has_ability("Forewarn"):
        ability_moves.append(
            MoveSpec(
                name="Forewarn",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: reveal the target's strongest moves and penalize their accuracy.",
            )
        )
    if has_ability_exact(pokemon, "Fox Fire [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Fox Fire [Errata]",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: create 3 Ember wisps that trigger after being targeted within 6 meters.",
            )
        )
    elif pokemon.has_ability("Fox Fire") and not has_errata(pokemon, "Fox Fire"):
        ability_moves.append(
            MoveSpec(
                name="Fox Fire",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: create 3 wisps that can fire Ember as interrupts.",
            )
        )
    if pokemon.has_ability("Frighten"):
        ability_moves.append(
            MoveSpec(
                name="Frighten",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: lower the target's Speed by -2 CS.",
            )
        )
    if has_ability_exact(pokemon, "Frisk [Feb Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Frisk [Feb Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Scene",
                range_text="Melee, 1 Target",
                effects_text="Ability action: learn the target's types, ability, nature, level, and held items.",
            )
        )
    elif (
        pokemon.has_ability("Frisk")
        and not has_ability_exact(pokemon, "Frisk [Feb Errata]")
        and not has_ability_exact(pokemon, "Frisk [SuMo Errata]")
    ):
        ability_moves.append(
            MoveSpec(
                name="Frisk",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: learn the target's types, ability, nature, level, and held items.",
            )
        )
    if has_ability_exact(pokemon, "Gale Wings [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Gale Wings [Errata]",
                type="Flying",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text=(
                    "Ability action: ready a Flying move with Priority; damaging moves add half Speed to damage."
                ),
            )
        )
    if has_ability_exact(pokemon, "Gore [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Gore [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: ready Horn Attack to strike twice and push 2 meters.",
            )
        )
    if has_ability_exact(pokemon, "Grass Pelt [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Grass Pelt [Errata]",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: gain two ticks of temporary HP.",
            )
        )
    if pokemon.has_ability("Gardener"):
        ability_moves.append(
            MoveSpec(
                name="Gardener",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily x3",
                range_text="Self",
                effects_text="Ability action: improve soil quality for a yielding plant.",
            )
        )
    if pokemon.has_ability("Gulp"):
        ability_moves.append(
            MoveSpec(
                name="Gulp",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: heal 25% max HP and remove one injury after submerging in water.",
            )
        )
    if pokemon.has_ability("Gentle Vibe"):
        ability_moves.append(
            MoveSpec(
                name="Gentle Vibe",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 2",
                effects_text="Ability action: reset combat stages and cure volatile statuses in Burst 2.",
            )
        )
    if pokemon.has_ability("Hay Fever"):
        ability_moves.append(
            MoveSpec(
                name="Hay Fever",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Burst 2 or Close Blast 3",
                effects_text="Ability action: release allergenic pollen in Burst 2 or Close Blast 3.",
            )
        )
    if pokemon.has_ability("Ice Shield"):
        ability_moves.append(
            MoveSpec(
                name="Ice Shield",
                type="Ice",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text=(
                    "Ability action: place up to three contiguous ice wall segments adjacent to the user."
                ),
            )
        )
    if pokemon.has_ability("Illusion"):
        ability_moves.append(
            MoveSpec(
                name="Illusion Mark",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="At-Will",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: mark a target for Illusion.",
            )
        )
        ability_moves.append(
            MoveSpec(
                name="Illusion Shift",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="At-Will",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: mimic a marked target or dismiss Illusion.",
            )
        )
    if has_ability_exact(pokemon, "Interference"):
        ability_moves.append(
            MoveSpec(
                name="Interference",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Burst 3, Foes",
                effects_text="Ability action: foes within 3 gain -2 accuracy until the end of the next turn.",
            )
        )
    if has_ability_exact(pokemon, "Interference [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Interference [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 3, Foes",
                effects_text="Ability action: foes within 3 gain -2 accuracy for 1 full round.",
            )
        )
    if has_ability_exact(pokemon, "Intimidate [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Intimidate [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=5,
                target_kind="Ranged",
                target_range=5,
                freq="At-Will",
                range_text="Range 5, 1 Target",
                effects_text="Ability action: lower the target's Attack by -1 CS (once per scene per target).",
            )
        )
    if pokemon.has_ability("Leaf Gift"):
        ability_moves.append(
            MoveSpec(
                name="Leaf Gift",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: craft a Leaf Gift suit (Nourishing, Heavy, or Vibrant).",
            )
        )
    if has_ability_exact(pokemon, "Leaf Guard [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Leaf Guard [Errata]",
                type="Grass",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: cure one status affliction; ignores frequency in sun.",
            )
        )
    if has_ability_exact(pokemon, "Life Force"):
        ability_moves.append(
            MoveSpec(
                name="Life Force",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily x5",
                range_text="Self",
                effects_text="Ability action: restore a tick of HP.",
            )
        )
    if has_ability_exact(pokemon, "Life Force [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Life Force [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily x5",
                range_text="Self",
                effects_text="Ability action: restore a tick of HP.",
            )
        )
    if has_ability_exact(pokemon, "Lightning Kicks"):
        ability_moves.append(
            MoveSpec(
                name="Lightning Kicks",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: the next Kick move this round gains Priority.",
            )
        )
    if has_ability_exact(pokemon, "Lightning Kicks [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Lightning Kicks [Errata]",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: the next Kick move this round gains Priority and +4 Accuracy.",
            )
        )
    if pokemon.has_ability("Lullaby"):
        ability_moves.append(
            MoveSpec(
                name="Lullaby",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: your next Sing this round automatically hits.",
            )
        )
    if has_ability_exact(pokemon, "Magnet Pull"):
        ability_moves.append(
            MoveSpec(
                name="Magnet Pull",
                type="Steel",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="At-Will",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: restrict a Steel-type target's movement for 1 round.",
            )
        )
    if has_ability_exact(pokemon, "Magnet Pull [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Magnet Pull [Errata]",
                type="Steel",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene x3",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: pick two magnet pull effects for a Steel target.",
            )
        )
    if has_ability_exact(pokemon, "Memory Wipe"):
        ability_moves.append(
            MoveSpec(
                name="Memory Wipe",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=10,
                target_kind="Ranged",
                target_range=10,
                freq="Scene",
                range_text="Range 10, 1 Target",
                effects_text="Ability action: disable the target's last move.",
            )
        )
    if has_ability_exact(pokemon, "Memory Wipe [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Memory Wipe [Errata]",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=10,
                target_kind="Ranged",
                target_range=10,
                freq="Scene",
                range_text="Range 10, 1 Target",
                effects_text="Ability action: swift disables the last move, standard flinches and paralyzes.",
            )
        )
    if pokemon.has_ability("Mini-Noses"):
        ability_moves.append(
            MoveSpec(
                name="Mini-Noses",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: deploy up to three Mini-Noses adjacent to the user.",
            )
        )
    if pokemon.has_ability("Power Construct"):
        ability_moves.append(
            MoveSpec(
                name="Power Construct",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: enter Complete Forme and gain temporary HP while below half HP.",
            )
        )
    if pokemon.has_ability("Power of Alchemy"):
        ability_moves.append(
            MoveSpec(
                name="Power of Alchemy",
                type="Dark",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: copy a target's ability for the scene.",
            )
        )
    if pokemon.has_ability("Propeller Tail"):
        ability_moves.append(
            MoveSpec(
                name="Propeller Tail",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: Sprint as a free action without intercept or redirection.",
            )
        )
    if pokemon.has_ability("Minus"):
        ability_moves.append(
            MoveSpec(
                name="Minus",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=10,
                target_kind="Ranged",
                target_range=10,
                freq="Scene",
                range_text="Range 10, 1 Ally",
                effects_text="Ability action: raise an allied Plus user's Special Attack by +2 CS.",
            )
        )
    if pokemon.has_ability("Plus"):
        ability_moves.append(
            MoveSpec(
                name="Plus",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=10,
                target_kind="Ranged",
                target_range=10,
                freq="Scene",
                range_text="Range 10, 1 Ally",
                effects_text="Ability action: raise an allied Minus user's Special Attack by +2 CS.",
            )
        )
    if pokemon.has_ability("Pickpocket"):
        ability_moves.append(
            MoveSpec(
                name="Thief",
                type="Dark",
                category="Physical",
                db=6,
                ac=2,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="At-Will",
                range_text="Melee, 1 Target",
                effects_text="Ability action: use Thief to steal a held item.",
            )
        )
    if pokemon.has_ability("Healer"):
        ability_moves.append(
            MoveSpec(
                name="Healer",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Scene",
                range_text="Melee, 1 Target",
                effects_text="Ability action: cure an adjacent ally of status conditions.",
            )
        )
    if has_ability_exact(pokemon, "Hydration [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Hydration [Errata]",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: cure one status affliction (ignored in rain).",
            )
        )
    if pokemon.has_ability("Omen"):
        ability_moves.append(
            MoveSpec(
                name="Omen",
                type="Ghost",
                category="Status",
                db=0,
                ac=2,
                range_kind="Ranged",
                range_value=5,
                target_kind="Ranged",
                target_range=5,
                freq="Scene",
                range_text="Range 5, 1 Target",
                effects_text="Ability action: lower the target's Accuracy by 2.",
            )
        )
    if has_ability_exact(pokemon, "Rain Dish [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Rain Dish [Errata]",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily x5",
                range_text="Self",
                effects_text="Ability action: heal a tick if below half HP or in rain.",
            )
        )
    if has_ability_exact(pokemon, "Rally [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Rally [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                area_kind="Burst",
                area_value=10,
                range_text="Burst 10",
                freq="Scene",
                effects_text="Ability action: you and allies in Burst 10 may Disengage 1 meter.",
            )
        )
    elif pokemon.has_ability("Rally") and not has_errata(pokemon, "Rally"):
        ability_moves.append(
            MoveSpec(
                name="Rally",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                area_kind="Burst",
                area_value=10,
                range_text="Burst 10",
                freq="Scene",
                effects_text="Ability action: allies in Burst 10 shift 1.",
            )
        )
    if has_ability_exact(pokemon, "Regal Challenge [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Regal Challenge [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=5,
                target_kind="Ranged",
                target_range=5,
                freq="Scene",
                range_text="Range 5, 1 Target",
                effects_text="Ability action: demand deference or defiance from the target.",
            )
        )
    elif pokemon.has_ability("Regal Challenge") and not has_errata(pokemon, "Regal Challenge"):
        ability_moves.append(
            MoveSpec(
                name="Regal Challenge",
                type="Normal",
                category="Status",
                db=0,
                ac=4,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: challenge a foe and alter Speed/Attack.",
            )
        )
    if pokemon.has_ability("Schooling"):
        ability_moves.append(
            MoveSpec(
                name="Schooling",
                type="Water",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: enter School Forme and gain temporary HP.",
            )
        )
    if pokemon.has_ability("Screen Cleaner"):
        ability_moves.append(
            MoveSpec(
                name="Screen Cleaner",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Field",
                effects_text="Ability action: clear all blessings and screen effects from the field.",
            )
        )
    if pokemon.has_ability("Snuggle"):
        ability_moves.append(
            MoveSpec(
                name="Snuggle",
                type="Fairy",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Scene",
                range_text="Melee, 1 Target",
                effects_text="Ability action: grant two ticks of temp HP to user and target.",
            )
        )
    if has_ability_exact(pokemon, "Sunglow [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Sunglow [Errata]",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: become Radiant; if already Radiant, expend it for +2 Attack and +2 Accuracy this scene.",
            )
        )
    elif pokemon.has_ability("Sunglow") and not has_errata(pokemon, "Sunglow"):
        ability_moves.append(
            MoveSpec(
                name="Sunglow",
                type="Fire",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: in sunlight, become Radiant for bonus damage.",
            )
        )
    if has_ability_exact(pokemon, "Symbiosis [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Symbiosis [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Scene",
                range_text="Melee, 1 Target",
                effects_text="Ability action: share one held item’s effects with an adjacent ally for the scene.",
            )
        )
    elif pokemon.has_ability("Symbiosis") and not has_errata(pokemon, "Symbiosis"):
        ability_moves.append(
            MoveSpec(
                name="Symbiosis",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="At-Will",
                range_text="Melee, 1 Ally",
                effects_text="Ability action: pass a held item to an adjacent ally.",
            )
        )
    if pokemon.has_ability("Targeting System"):
        ability_moves.append(
            MoveSpec(
                name="Targeting System",
                type="Steel",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: Lock-On may be used as a Swift Action this scene.",
            )
        )
    if has_ability_exact(pokemon, "Toxic Boost [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Toxic Boost [Errata]",
                type="Poison",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: while Poisoned, gain +3 Attack and +3 Special Attack CS.",
            )
        )
    if has_ability_exact(pokemon, "Transporter [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Transporter [Errata]",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily x3",
                range_text="Self",
                effects_text="Ability action: empower Teleport to triple range and/or carry an adjacent ally.",
            )
        )
    if pokemon.has_ability("Toxic Nourishment"):
        ability_moves.append(
            MoveSpec(
                name="Toxic Nourishment",
                type="Poison",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Scene",
                range_text="Melee, 1 Target",
                effects_text="Ability action: cure poison and gain temporary HP.",
            )
        )
    if pokemon.has_ability("Trace"):
        ability_moves.append(
            MoveSpec(
                name="Trace",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: copy a target's ability for the encounter.",
            )
        )
    if pokemon.has_ability("Rocket"):
        ability_moves.append(
            MoveSpec(
                name="Rocket",
                type="Flying",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: gain sky speed and act first next round.",
            )
        )
    if has_ability_exact(pokemon, "Rocket [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Rocket [Errata]",
                type="Flying",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: act first next round and prevent responses.",
            )
        )
    if pokemon.has_ability("Splendorous Rider"):
        ability_moves.append(
            MoveSpec(
                name="Splendorous Rider",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: borrow a mount move for this turn.",
            )
        )
    if pokemon.has_ability("Stance Change"):
        ability_moves.append(
            MoveSpec(
                name="Stance Change",
                type="Steel",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: switch between Shield and Sword stances.",
            )
        )
    if has_ability_exact(pokemon, "Zen Mode [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Zen Mode [Errata]",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: enter Zen Mode for the scene and gain Flamethrower/Psychic.",
            )
        )
    elif pokemon.has_ability("Zen Mode") and not has_errata(pokemon, "Zen Mode"):
        ability_moves.append(
            MoveSpec(
                name="Zen Mode",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: toggle Zen Mode while below/above half HP.",
            )
        )
    if pokemon.has_ability("Zen Snowed"):
        ability_moves.append(
            MoveSpec(
                name="Zen Snowed",
                type="Ice",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: activate Zen Mode and gain Ice Punch/Fire Punch.",
            )
        )
    if has_ability_exact(pokemon, "Starlight [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Starlight [Errata]",
                type="Fairy",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily",
                range_text="Self",
                effects_text="Ability action: become Luminous; if already Luminous, expend it for +2 SpDef and +2 Evasion this scene.",
            )
        )
    elif pokemon.has_ability("Starlight") and not has_errata(pokemon, "Starlight"):
        ability_moves.append(
            MoveSpec(
                name="Starlight",
                type="Fairy",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: become Luminous to penalize enemy accuracy.",
            )
        )
    if has_ability_exact(pokemon, "Starswirl [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Starswirl [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: your next Rapid Spin may be used as a Swift Action.",
            )
        )
    elif pokemon.has_ability("Starswirl") and not has_errata(pokemon, "Starswirl"):
        ability_moves.append(
            MoveSpec(
                name="Starswirl",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: Rapid Spin as a Swift Action without damage.",
            )
        )
    if pokemon.has_ability("Empower"):
        ability_moves.append(
            MoveSpec(
                name="Empower",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: next self-targeting Status move may be used as a Free Action.",
            )
        )
    if has_ability_exact(pokemon, "Sun Blanket [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Sun Blanket [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Daily x5",
                range_text="Self",
                effects_text="Ability action: heal a tick when you gain initiative if below half HP or in sun.",
            )
        )
    if has_ability_exact(pokemon, "Unnerve [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Unnerve [Errata]",
                type="Dark",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="At-Will",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: target cannot gain positive CS or trade digestion buffs for 1 round.",
            )
        )
    if pokemon.has_ability("Spinning Dance"):
        ability_moves.append(
            MoveSpec(
                name="Spinning Dance",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: gain +1 Evasion and Shift 1 meter if able.",
            )
        )
    if pokemon.has_ability("Heliovolt"):
        ability_moves.append(
            MoveSpec(
                name="Heliovolt",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Self",
                effects_text="Ability action: gain +1 Evasion and Sunny resonance for 1 round.",
            )
        )
    if pokemon.has_ability("Gorilla Tactics"):
        ability_moves.append(
            MoveSpec(
                name="Gorilla Tactics",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: gain +10 damage and lock to previously used moves this scene.",
            )
        )
    if pokemon.has_ability("Psionic Screech"):
        ability_moves.append(
            MoveSpec(
                name="Psionic Screech",
                type="Psychic",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene x2",
                range_text="Self",
                effects_text="Ability action: next move becomes Psychic and flinches targets hit.",
            )
        )
    if has_ability_exact(pokemon, "Ambush [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Ambush [Errata]",
                type="Dark",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: next DB 6 or lower move gains Priority and debuffs accuracy on hit.",
            )
        )
    if has_ability_exact(pokemon, "Arena Trap [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Arena Trap [Errata]",
                type="Ground",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Self",
                effects_text="Ability action: toggle Arena Trap to slow and trap nearby foes.",
            )
        )
    if has_ability_exact(pokemon, "Aura Break [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Aura Break [Errata]",
                type="Dark",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                freq="Scene",
                range_text="Range 6, 1 Target",
                effects_text="Ability action: invert one of the target's damage-boosting abilities.",
            )
        )
    if has_ability_exact(pokemon, "Bad Dreams [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Bad Dreams [Errata]",
                type="Dark",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="At-Will",
                range_text="Burst 5",
                effects_text="Ability action: drain ticks from sleeping foes in Burst 5 and gain temp HP.",
            )
        )
    if has_ability_exact(pokemon, "Beautiful [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Beautiful [Errata]",
                type="Fairy",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 5, Allies",
                effects_text="Ability action: gain +1 SpAtk CS and cure allies of Enraged.",
            )
        )
    if has_ability_exact(pokemon, "Pressure [Errata]"):
        ability_moves.append(
            MoveSpec(
                name="Pressure [Errata]",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
                range_text="Burst 3, Foes",
                effects_text="Ability action: suppress foes within 3 meters for 1 round.",
            )
        )
    return ability_moves


def apply_post_init_ability_effects(pokemon: "PokemonState") -> None:
    def _ability_key(value: object) -> str:
        return "".join(ch for ch in str(value or "").strip().lower().replace("’", "'").replace("*", "") if ch.isalnum())

    if pokemon.has_ability("Diamond Defense"):
        for move in pokemon.spec.moves:
            if (move.name or "").strip().lower() == "stealth rock":
                move.freq = "Scene x2"
                break
    if pokemon.has_ability("Cluster Mind"):
        pokemon.add_temporary_effect("move_pool_bonus", amount=2)
    if pokemon.has_ability("Color Theory") and not pokemon.get_temporary_effects("color_theory"):
        previous_max_hp = pokemon.max_hp()
        roll = None
        color = ""
        for entry in pokemon.spec.abilities or []:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("name") or "").strip().lower() != "color theory":
                continue
            try:
                stored_roll = int(entry.get("color_theory_roll"))
            except (TypeError, ValueError):
                stored_roll = 0
            stored_color = str(entry.get("color_theory_color") or "").strip()
            if 1 <= stored_roll <= 12:
                roll = stored_roll
            if stored_color:
                color = stored_color
            if roll and not color:
                color = COLOR_THEORY_COLORS.get(roll, "Red")
            if not roll and color:
                for color_roll, label in COLOR_THEORY_COLORS.items():
                    if str(label).strip().lower() == color.lower():
                        roll = color_roll
                        color = label
                        break
            if not roll:
                roll = random.randint(1, 12)
                color = COLOR_THEORY_COLORS.get(roll, "Red")
            entry["color_theory_roll"] = roll
            entry["color_theory_color"] = color
            break
        if not roll:
            roll = random.randint(1, 12)
            color = COLOR_THEORY_COLORS.get(roll, "Red")
        pokemon.add_temporary_effect("color_theory", roll=roll, color=color)
        if pokemon.hp is not None:
            new_max_hp = pokemon.max_hp()
            if pokemon.hp >= previous_max_hp:
                pokemon.hp = new_max_hp
            else:
                pokemon.hp = min(new_max_hp, pokemon.hp)
    if has_ability_exact(pokemon, "Early Bird"):
        pokemon.add_temporary_effect("save_bonus", amount=3, source="Early Bird")
    if pokemon.has_ability("Fabulous Trim") and (pokemon.spec.species or "").strip().lower() == "furfrou":
        style = ""
        for entry in pokemon.spec.abilities or []:
            if not isinstance(entry, dict):
                continue
            if _ability_key(entry.get("name")) != _ability_key("fabulous trim"):
                continue
            style = str(entry.get("fabulous_trim_style") or "").strip()
            break
        if not style:
            style = (pokemon.spec.name or pokemon.spec.species).strip()
        pokemon.add_temporary_effect("fabulous_trim", style=style, source="Fabulous Trim")
    if pokemon.has_ability("Serpent's Mark") and not pokemon.get_temporary_effects("serpents_mark"):
        patterns = {
            1: ("Attack Pattern", "Rivalry", "Strong Jaw"),
            2: ("Crush Pattern", "Unnerve", "Crush Trap"),
            3: ("Fear Pattern", "Frighten", "Regal Challenge"),
            4: ("Life Pattern", "Regenerator", "Defy Death"),
            5: ("Speed Pattern", "Run Away", "Speed Boost"),
            6: ("Stealth Pattern", "Instinct", "Infiltrator"),
        }
        roll = None
        pattern_name = ""
        for entry in pokemon.spec.abilities or []:
            if not isinstance(entry, dict):
                continue
            ability_name = _ability_key(entry.get("name"))
            if ability_name not in {_ability_key("serpent's mark"), _ability_key("serpent's mark [errata]")}:
                continue
            try:
                stored_roll = int(entry.get("serpents_mark_roll"))
            except (TypeError, ValueError):
                stored_roll = 0
            stored_pattern = str(entry.get("serpents_mark_pattern") or "").strip()
            if 1 <= stored_roll <= 6:
                roll = stored_roll
            if stored_pattern:
                pattern_name = stored_pattern
            if not roll and pattern_name:
                for pattern_roll, pattern_tuple in patterns.items():
                    if pattern_tuple[0].lower() == pattern_name.lower():
                        roll = pattern_roll
                        pattern_name = pattern_tuple[0]
                        break
            if not roll:
                roll = random.randint(1, 6)
            if not pattern_name:
                pattern_name = patterns.get(roll, patterns[1])[0]
            entry["serpents_mark_roll"] = roll
            entry["serpents_mark_pattern"] = pattern_name
            break
        if not roll:
            roll = random.randint(1, 6)
        pattern_name, adv_ability, high_ability = patterns.get(roll, ("Attack Pattern", "Rivalry", "Strong Jaw"))
        pokemon.add_temporary_effect("serpents_mark", roll=roll, pattern=pattern_name)
        pokemon.add_temporary_effect("ability_granted", ability=adv_ability, source="Serpent's Mark")
        pokemon.add_temporary_effect("ability_granted", ability=high_ability, source="Serpent's Mark")
    if pokemon.has_ability("Inner Focus"):
        pokemon.add_temporary_effect("flinch_immunity", source="Inner Focus")
    if pokemon.has_ability("Quick Draw"):
        pokemon.add_temporary_effect("flinch_immunity", source="Quick Draw")
    if pokemon.has_ability("Super Luck") and not pokemon.get_temporary_effects("crit_range_bonus"):
        pokemon.add_temporary_effect("crit_range_bonus", bonus=2, source="Super Luck")
    if pokemon.has_ability("Anchored") and not pokemon.get_temporary_effects("anchor_token"):
        pokemon.add_temporary_effect("anchor_token", source="Anchored")
    if pokemon.has_ability("Dauntless Shield"):
        pokemon.combat_stages["def"] = pokemon.combat_stages.get("def", 0) + 1
    if pokemon.has_ability("Intrepid Sword"):
        pokemon.combat_stages["atk"] = pokemon.combat_stages.get("atk", 0) + 1
    if pokemon.has_ability("Ice Face"):
        pokemon.temp_hp += pokemon.tick_value() * 2
    if pokemon.has_ability("Sorcery"):
        level = int(pokemon.spec.level or 0)
        bonus = 5 + max(0, level // 10)
        pokemon.add_temporary_effect("stat_modifier", stat="spatk", amount=bonus, source="Sorcery")
    if pokemon.has_ability("Seasonal") and not pokemon.get_temporary_effects("seasonal"):
        season = "spring"
        pokemon.add_temporary_effect("seasonal", season=season)
        season_map = {
            "spring": "Run Away",
            "summer": "Grass Pelt",
            "autumn": "Rivalry",
            "winter": "Thick Fat",
        }
        ability = season_map.get(season)
        if ability:
            pokemon.add_temporary_effect("ability_granted", ability=ability, source="Seasonal")
    if pokemon.has_ability("RKS System") and not pokemon.get_temporary_effects("rks_system"):
        memory_type = ""
        for item in pokemon.spec.items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("item") or "").strip()
            if "memory" in name.lower():
                memory_type = name.replace("Memory", "").strip()
                memory_type = memory_type or str(item.get("type") or "").strip()
                break
            if item.get("type"):
                memory_type = str(item.get("type") or "").strip()
                break
        if memory_type:
            pokemon.add_temporary_effect("rks_system", type=memory_type)
            pokemon.spec.types = [memory_type]
    if has_ability_exact(pokemon, "Poltergeist [Errata]"):
        species_name = pokemon.spec.species or pokemon.spec.name or ""
        form_key = _rotom_form_key(species_name)
        if form_key:
            if not any(
                entry.get("ability") == "Phantom Body"
                and (entry.get("source") or "") == "Poltergeist [Errata]"
                for entry in pokemon.get_temporary_effects("ability_granted")
            ):
                pokemon.add_temporary_effect(
                    "ability_granted",
                    ability="Phantom Body",
                    source="Poltergeist [Errata]",
                )
            try:
                level = int(pokemon.spec.level or 0)
            except (TypeError, ValueError):
                level = 0
            if level >= 40:
                move_map = {
                    "heat": "Overheat",
                    "wash": "Hydro Pump",
                    "frost": "Blizzard",
                    "fan": "Hurricane",
                    "mow": "Leaf Storm",
                }
                move_name = move_map.get(form_key)
                if move_name:
                    known = {str(move.name or "").strip().lower() for move in pokemon.spec.moves}
                    if move_name.lower() not in known:
                        spec = _lookup_move_spec(move_name)
                        if spec:
                            pokemon.spec.moves.append(copy.deepcopy(spec))
                            pokemon.add_temporary_effect(
                                "poltergeist_errata_move",
                                name=move_name,
                            )
