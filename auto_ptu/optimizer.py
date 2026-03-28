"""Build optimizer models and scoring contract for Pokemon-only AutoPTU builds.

This module defines stable JSON-serializable schema objects and a deterministic
proxy scorer. It does not replace battle resolution; it uses existing rules
math as the scoring backend.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List, Literal, Optional

from .data_models import MoveSpec, PokemonSpec
from .rules import calculations
from .rules.battle_state import PokemonState

EncounterFormat = Literal["singles", "doubles", "raid"]
EvasionPolicy = Literal["best_available", "speed_only", "category_only"]


@dataclass
class ScoreWeights:
    offense: float = 0.42
    defense: float = 0.33
    tempo: float = 0.15
    consistency: float = 0.10

    @classmethod
    def from_dict(cls, data: dict) -> "ScoreWeights":
        return cls(
            offense=float(data.get("offense", 0.42)),
            defense=float(data.get("defense", 0.33)),
            tempo=float(data.get("tempo", 0.15)),
            consistency=float(data.get("consistency", 0.10)),
        )

    def to_dict(self) -> dict:
        return {
            "offense": self.offense,
            "defense": self.defense,
            "tempo": self.tempo,
            "consistency": self.consistency,
        }


@dataclass
class EnemyArchetype:
    name: str
    types: List[str]
    level: int
    hp_stat: int
    atk: int
    defense: int
    spatk: int
    spdef: int
    spd: int
    weight: float = 1.0

    @classmethod
    def from_dict(cls, data: dict) -> "EnemyArchetype":
        return cls(
            name=str(data.get("name", "archetype")),
            types=[str(entry) for entry in data.get("types", ["Normal"]) if str(entry).strip()],
            level=int(data.get("level", 50)),
            hp_stat=int(data.get("hp_stat", 12)),
            atk=int(data.get("atk", 12)),
            defense=int(data.get("defense", 12)),
            spatk=int(data.get("spatk", 12)),
            spdef=int(data.get("spdef", 12)),
            spd=int(data.get("spd", 12)),
            weight=float(data.get("weight", 1.0)),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "types": list(self.types),
            "level": self.level,
            "hp_stat": self.hp_stat,
            "atk": self.atk,
            "defense": self.defense,
            "spatk": self.spatk,
            "spdef": self.spdef,
            "spd": self.spd,
            "weight": self.weight,
        }

    def to_state(self) -> PokemonState:
        spec = PokemonSpec(
            species=self.name,
            level=self.level,
            types=list(self.types) or ["Normal"],
            hp_stat=self.hp_stat,
            atk=self.atk,
            defense=self.defense,
            spatk=self.spatk,
            spdef=self.spdef,
            spd=self.spd,
            moves=[],
        )
        return PokemonState(spec=spec, controller_id="enemy", position=(0, 1))


@dataclass
class EncounterModel:
    name: str
    format: EncounterFormat = "singles"
    rounds_horizon: int = 4
    map_melee_access: float = 0.75
    average_targets_hit: float = 1.0
    evasion_policy: EvasionPolicy = "best_available"
    weights: ScoreWeights = field(default_factory=ScoreWeights)
    archetypes: List[EnemyArchetype] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "EncounterModel":
        return cls(
            name=str(data.get("name", "Encounter")),
            format=str(data.get("format", "singles")).strip().lower(),  # type: ignore[arg-type]
            rounds_horizon=max(1, int(data.get("rounds_horizon", 4))),
            map_melee_access=max(0.1, min(1.0, float(data.get("map_melee_access", 0.75)))),
            average_targets_hit=max(0.5, float(data.get("average_targets_hit", 1.0))),
            evasion_policy=str(data.get("evasion_policy", "best_available")).strip().lower(),  # type: ignore[arg-type]
            weights=ScoreWeights.from_dict(dict(data.get("weights", {}))),
            archetypes=[EnemyArchetype.from_dict(entry) for entry in data.get("archetypes", [])],
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "format": self.format,
            "rounds_horizon": self.rounds_horizon,
            "map_melee_access": self.map_melee_access,
            "average_targets_hit": self.average_targets_hit,
            "evasion_policy": self.evasion_policy,
            "weights": self.weights.to_dict(),
            "archetypes": [entry.to_dict() for entry in self.archetypes],
        }


@dataclass
class BuildGenome:
    species: str
    level: int
    types: List[str]
    hp_stat: int
    atk: int
    defense: int
    spatk: int
    spdef: int
    spd: int
    nature: str = ""
    ability: str = ""
    moves: List[MoveSpec] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "BuildGenome":
        return cls(
            species=str(data.get("species", "Pokemon")),
            level=int(data.get("level", 20)),
            types=[str(entry) for entry in data.get("types", ["Normal"]) if str(entry).strip()],
            hp_stat=int(data.get("hp_stat", 10)),
            atk=int(data.get("atk", 10)),
            defense=int(data.get("defense", 10)),
            spatk=int(data.get("spatk", 10)),
            spdef=int(data.get("spdef", 10)),
            spd=int(data.get("spd", 10)),
            nature=str(data.get("nature", "")),
            ability=str(data.get("ability", "")),
            moves=[MoveSpec.from_dict(entry) for entry in data.get("moves", [])],
        )

    @classmethod
    def from_pokemon_spec(
        cls,
        spec: PokemonSpec,
        *,
        ability: Optional[str] = None,
    ) -> "BuildGenome":
        chosen_ability = ability or ""
        if not chosen_ability and spec.abilities:
            first = spec.abilities[0]
            if isinstance(first, dict):
                chosen_ability = str(first.get("name") or "")
            elif isinstance(first, str):
                chosen_ability = first
        return cls(
            species=spec.species,
            level=int(spec.level),
            types=list(spec.types),
            hp_stat=int(spec.hp_stat),
            atk=int(spec.atk),
            defense=int(spec.defense),
            spatk=int(spec.spatk),
            spdef=int(spec.spdef),
            spd=int(spec.spd),
            nature=str(spec.nature or ""),
            ability=str(chosen_ability or ""),
            moves=list(spec.moves),
        )

    def to_pokemon_spec(self) -> PokemonSpec:
        abilities = [{"name": self.ability}] if self.ability else []
        return PokemonSpec(
            species=self.species,
            level=self.level,
            types=list(self.types) or ["Normal"],
            hp_stat=self.hp_stat,
            atk=self.atk,
            defense=self.defense,
            spatk=self.spatk,
            spdef=self.spdef,
            spd=self.spd,
            nature=self.nature,
            abilities=abilities,
            moves=list(self.moves),
        )

    def to_dict(self) -> dict:
        return {
            "species": self.species,
            "level": self.level,
            "types": list(self.types),
            "hp_stat": self.hp_stat,
            "atk": self.atk,
            "defense": self.defense,
            "spatk": self.spatk,
            "spdef": self.spdef,
            "spd": self.spd,
            "nature": self.nature,
            "ability": self.ability,
            "moves": [move.to_engine_dict() for move in self.moves],
        }


@dataclass
class BuildScore:
    offense: float
    defense: float
    tempo: float
    consistency: float
    total: float
    details: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "offense": self.offense,
            "defense": self.defense,
            "tempo": self.tempo,
            "consistency": self.consistency,
            "total": self.total,
            "details": dict(self.details),
        }


def default_encounter_model(format_name: EncounterFormat = "singles") -> EncounterModel:
    format_key = str(format_name or "singles").strip().lower()
    if format_key == "doubles":
        return EncounterModel(
            name="Doubles Default",
            format="doubles",
            rounds_horizon=5,
            map_melee_access=0.70,
            average_targets_hit=1.35,
            evasion_policy="best_available",
            weights=ScoreWeights(offense=0.45, defense=0.25, tempo=0.20, consistency=0.10),
            archetypes=_default_archetypes(),
        )
    if format_key == "raid":
        return EncounterModel(
            name="Raid Default",
            format="raid",
            rounds_horizon=6,
            map_melee_access=0.80,
            average_targets_hit=1.10,
            evasion_policy="best_available",
            weights=ScoreWeights(offense=0.34, defense=0.40, tempo=0.16, consistency=0.10),
            archetypes=_default_archetypes(),
        )
    return EncounterModel(
        name="Singles Default",
        format="singles",
        rounds_horizon=4,
        map_melee_access=0.75,
        average_targets_hit=1.0,
        evasion_policy="best_available",
        weights=ScoreWeights(offense=0.42, defense=0.33, tempo=0.15, consistency=0.10),
        archetypes=_default_archetypes(),
    )


def score_build_genome(genome: BuildGenome, encounter: EncounterModel) -> BuildScore:
    attacker = PokemonState(spec=genome.to_pokemon_spec(), controller_id="self", position=(0, 0))
    enemies = list(encounter.archetypes) if encounter.archetypes else _default_archetypes()
    weighted_total = max(1e-6, sum(max(0.0, entry.weight) for entry in enemies))

    offense_parts: List[float] = []
    offense_by_archetype: Dict[str, float] = {}
    for archetype in enemies:
        defender = archetype.to_state()
        value = _offense_vs_archetype(attacker, defender, encounter)
        offense_parts.append(value * max(0.0, archetype.weight))
        offense_by_archetype[archetype.name] = value
    offense = sum(offense_parts) / weighted_total

    defense_parts: List[float] = []
    for archetype in enemies:
        defender = archetype.to_state()
        value = _defense_vs_archetype(attacker, defender, encounter)
        defense_parts.append(value * max(0.0, archetype.weight))
    defense = sum(defense_parts) / weighted_total

    tempo = _tempo_score(attacker, encounter)
    consistency = _consistency_score(attacker, enemies, encounter)

    weights = encounter.weights
    total = (
        (weights.offense * offense)
        + (weights.defense * defense)
        + (weights.tempo * tempo)
        + (weights.consistency * consistency)
    )
    details = {
        "weighted_offense": weights.offense * offense,
        "weighted_defense": weights.defense * defense,
        "weighted_tempo": weights.tempo * tempo,
        "weighted_consistency": weights.consistency * consistency,
        "horizon": float(encounter.rounds_horizon),
        "map_melee_access": float(encounter.map_melee_access),
        "average_targets_hit": float(encounter.average_targets_hit),
    }
    for name, value in offense_by_archetype.items():
        details[f"offense_vs_{name}"] = float(value)
    return BuildScore(
        offense=float(offense),
        defense=float(defense),
        tempo=float(tempo),
        consistency=float(consistency),
        total=float(total),
        details=details,
    )


def _offense_vs_archetype(attacker: PokemonState, defender: PokemonState, encounter: EncounterModel) -> float:
    moves = [move for move in attacker.spec.moves if _is_damaging_move(move)]
    if not moves:
        return 0.0
    weighted_scores: List[float] = []
    for move in moves:
        default_hit = calculations.hit_probability(attacker, defender, move) if move.ac is not None else 1.0
        policy_hit = _hit_probability_for_policy(attacker, defender, move, encounter.evasion_policy)
        damage = calculations.expected_damage(attacker, defender, move)
        if default_hit > 0:
            damage *= policy_hit / default_hit
        elif policy_hit <= 0:
            damage = 0.0
        frequency = _frequency_multiplier(move.freq)
        range_factor = _range_factor(move, encounter)
        aoe_factor = _aoe_factor(move, encounter)
        weighted_scores.append(damage * frequency * range_factor * aoe_factor)
    if not weighted_scores:
        return 0.0
    ranked = sorted(weighted_scores, reverse=True)
    top = ranked[0]
    top_two = mean(ranked[: min(2, len(ranked))])
    horizon_scale = 0.8 + min(0.4, max(0.0, (encounter.rounds_horizon - 3) * 0.08))
    return (0.68 * top + 0.32 * top_two) * horizon_scale


def _defense_vs_archetype(attacker: PokemonState, defender: PokemonState, encounter: EncounterModel) -> float:
    incoming_moves = _archetype_threat_moves(defender.spec.types)
    incoming_values: List[float] = []
    for move in incoming_moves:
        incoming_values.append(calculations.expected_damage(defender, attacker, move))
    if not incoming_values:
        return 0.0
    incoming = max(0.5, max(incoming_values))
    turns_to_faint = attacker.max_hp() / incoming
    defensive_evasion = float(max(
        calculations.evasion_value(attacker, "physical"),
        calculations.evasion_value(attacker, "special"),
        calculations.evasion_value(attacker, "status"),
    ))
    breakpoint_value = (
        float(attacker.spec.defense // 5)
        + float(attacker.spec.spdef // 5)
        + float(attacker.spec.spd // 5)
    )
    horizon_factor = min(1.4, 0.7 + encounter.rounds_horizon * 0.1)
    return max(0.0, turns_to_faint * horizon_factor + defensive_evasion * 0.45 + breakpoint_value * 0.35)


def _tempo_score(attacker: PokemonState, encounter: EncounterModel) -> float:
    setup_moves = 0
    control_moves = 0
    for move in attacker.spec.moves:
        if _is_damaging_move(move):
            continue
        text = f"{move.name} {move.effects_text}".strip().lower()
        if any(token in text for token in ("raise", "boost", "combat stage", "speed")):
            setup_moves += 1
        if any(token in text for token in ("sleep", "paraly", "poison", "burn", "flinch", "trap", "taunt")):
            control_moves += 1
    horizon = max(1, encounter.rounds_horizon)
    setup_roi = max(0.45, min(1.4, (horizon - 1) / 3.0))
    return (setup_moves * 1.2 + control_moves * 1.0) * setup_roi


def _consistency_score(
    attacker: PokemonState,
    enemies: List[EnemyArchetype],
    encounter: EncounterModel,
) -> float:
    damaging = [move for move in attacker.spec.moves if _is_damaging_move(move)]
    if not damaging:
        return 0.0
    repeatable = [move for move in damaging if _is_repeatable_frequency(move.freq)]
    coverage_types = {str(move.type or "").strip().lower() for move in damaging if str(move.type or "").strip()}
    accuracy_scores: List[float] = []
    default_enemy = enemies[0].to_state() if enemies else _default_archetypes()[0].to_state()
    for move in repeatable or damaging:
        accuracy_scores.append(_hit_probability_for_policy(attacker, default_enemy, move, encounter.evasion_policy))
    avg_accuracy = mean(accuracy_scores) if accuracy_scores else 0.0
    return len(repeatable) * 1.7 + len(coverage_types) * 0.9 + avg_accuracy * 5.0


def _hit_probability_for_policy(
    attacker: PokemonState,
    defender: PokemonState,
    move: MoveSpec,
    policy: EvasionPolicy,
) -> float:
    if move.ac is None:
        return 1.0
    evasion = _select_defender_evasion(attacker, defender, move, policy)
    if evasion > 0:
        evasion = min(9, evasion)
    accuracy_stage = calculations.accuracy_stage_value(
        attacker.combat_stages.get("accuracy", 0) + attacker.spec.accuracy_cs
    )
    needed = max(2, int(move.ac) + evasion - accuracy_stage)
    if needed <= 2:
        return 0.95
    if needed > 20:
        return 1.0 / 20.0
    success_faces = max(0, 21 - needed)
    return max(0.0, min(0.95, success_faces / 20.0))


def _select_defender_evasion(
    attacker: PokemonState,
    defender: PokemonState,
    move: MoveSpec,
    policy: EvasionPolicy,
) -> int:
    physical = calculations.evasion_value(defender, "physical")
    special = calculations.evasion_value(defender, "special")
    speed = calculations.evasion_value(defender, "status")
    category = str(move.category or "").strip().lower()
    if policy == "speed_only":
        return speed
    if policy == "category_only":
        if category == "physical":
            return physical
        if category == "special":
            return special
        return speed
    if category == "physical":
        return max(physical, speed)
    if category == "special":
        return max(special, speed)
    return speed


def _is_damaging_move(move: MoveSpec) -> bool:
    return str(move.category or "").strip().lower() != "status" and int(move.db or 0) > 0


def _is_repeatable_frequency(frequency: str) -> bool:
    text = str(frequency or "").strip().lower()
    if "at-will" in text or "eot" in text:
        return True
    return text in {"standard", "free", "shift", "action"}


def _frequency_multiplier(frequency: str) -> float:
    text = str(frequency or "").strip().lower()
    if "at-will" in text:
        return 1.0
    if "eot" in text:
        return 0.9
    if "scene x3" in text:
        return 0.74
    if "scene x2" in text:
        return 0.66
    if "scene" in text:
        return 0.56
    if "daily x3" in text:
        return 0.45
    if "daily x2" in text:
        return 0.36
    if "daily" in text:
        return 0.28
    if text in {"standard", "free", "shift", "action"}:
        return 0.86
    return 0.72


def _range_factor(move: MoveSpec, encounter: EncounterModel) -> float:
    kind = str(move.range_kind or "").strip().lower()
    if kind == "melee":
        return max(0.55, min(1.0, encounter.map_melee_access))
    return 1.0


def _aoe_factor(move: MoveSpec, encounter: EncounterModel) -> float:
    kind = str(move.area_kind or "").strip().lower()
    if kind in {"burst", "cone", "line", "closeblast"}:
        return max(1.0, encounter.average_targets_hit)
    return 1.0


def _archetype_threat_moves(types: List[str]) -> List[MoveSpec]:
    primary_type = str(types[0] if types else "Normal")
    return [
        MoveSpec(
            name=f"{primary_type} Slash",
            type=primary_type,
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        ),
        MoveSpec(
            name=f"{primary_type} Pulse",
            type=primary_type,
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        ),
    ]


def _default_archetypes() -> List[EnemyArchetype]:
    return [
        EnemyArchetype(
            name="balanced_brawler",
            types=["Normal"],
            level=50,
            hp_stat=14,
            atk=14,
            defense=14,
            spatk=12,
            spdef=12,
            spd=12,
            weight=1.0,
        ),
        EnemyArchetype(
            name="fast_sweeper",
            types=["Electric"],
            level=50,
            hp_stat=10,
            atk=15,
            defense=9,
            spatk=16,
            spdef=9,
            spd=18,
            weight=1.0,
        ),
        EnemyArchetype(
            name="bulky_wall",
            types=["Rock"],
            level=50,
            hp_stat=18,
            atk=10,
            defense=18,
            spatk=10,
            spdef=18,
            spd=8,
            weight=1.0,
        ),
    ]


__all__ = [
    "BuildGenome",
    "BuildScore",
    "EvasionPolicy",
    "EncounterFormat",
    "EncounterModel",
    "EnemyArchetype",
    "ScoreWeights",
    "default_encounter_model",
    "score_build_genome",
]
