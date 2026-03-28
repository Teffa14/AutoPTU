"""Dataclasses describing campaigns, rosters, grids and match plans."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(v).strip() for v in value if str(v).strip()]


def _int_field(value: Any, default: int = 0) -> int:
    try:
        if value in ("", None):
            return default
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def _opt_int(value: Any) -> Optional[int]:
    try:
        if value in ("", None):
            return None
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


@dataclass
class MoveSpec:
    name: str
    type: str
    category: str = "Special"
    db: int = 8
    ac: Optional[int] = 2
    range_kind: str = "Ranged"
    range_value: Optional[int] = 6
    target_kind: str = ""
    target_range: Optional[int] = None
    area_kind: Optional[str] = None
    area_value: Optional[int] = None
    freq: str = "At-Will"
    keywords: List[str] = field(default_factory=list)
    priority: int = 0
    crit_range: int = 20
    effects_text: str = ""
    range_text: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MoveSpec":
        range_kind = str(data.get("range_kind", data.get("range", "Ranged")) or "Ranged")
        range_value = data.get("range_value")
        area_kind = data.get("area_kind")
        area_value = data.get("area_value")
        target_kind = data.get("target_kind")
        target_range = data.get("target_range")
        if area_kind is None and range_kind in {"Burst", "Cone", "Line", "CloseBlast"}:
            area_kind = range_kind
            area_value = range_value if area_value is None else area_value
        if target_kind is None:
            if area_kind in {"Burst", "Cone", "Line", "CloseBlast"}:
                target_kind = "Self"
            else:
                target_kind = range_kind or "Ranged"
        if target_range is None:
            if area_kind in {"Burst", "Cone", "Line", "CloseBlast"}:
                target_range = 0
            else:
                target_range = range_value
        return cls(
            name=data["name"],
            type=data.get("type", "Normal"),
            category=data.get("category", "Special"),
            db=int(data.get("db", 8)),
            ac=int(data["ac"]) if data.get("ac") not in (None, "") else None,
            range_kind=range_kind,
            range_value=_opt_int(range_value),
            target_kind=str(target_kind or "Ranged"),
            target_range=_opt_int(target_range),
            area_kind=area_kind,
            area_value=_opt_int(area_value),
            freq=data.get("freq", data.get("frequency", "EOT")),
            range_text=str(data.get("range_text", data.get("range_detail", data.get("range_label", data.get("range", "")))) or ""),
            keywords=list(data.get("keywords", [])),
            priority=int(data.get("priority", 0)),
            crit_range=int(data.get("crit_range", 20)),
            effects_text=data.get("effects_text", data.get("effects", data.get("text", ""))),
        )

    def __post_init__(self) -> None:
        if not self.target_kind:
            self.target_kind = self.range_kind or "Ranged"
        kind = (self.target_kind or "Ranged").lower()
        if self.target_range is None:
            if kind == "self":
                self.target_range = 0
            elif kind == "field":
                self.target_range = None
            elif self.range_value not in (None, "", 0):
                try:
                    self.target_range = int(self.range_value)  # type: ignore[assignment]
                except (TypeError, ValueError):
                    pass
            elif kind == "melee":
                self.target_range = 1
        if self.area_kind and self.area_value is None and self.range_value not in (None, "", 0):
            try:
                self.area_value = int(self.range_value)  # type: ignore[assignment]
            except (TypeError, ValueError):
                self.area_value = None

    def to_engine_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "db": self.db,
            "ac": self.ac,
            "range_kind": self.range_kind,
            "range_value": self.range_value,
            "target_kind": self.target_kind,
            "target_range": self.target_range,
            "area_kind": self.area_kind,
            "area_value": self.area_value,
            "freq": self.freq,
            "keywords": list(self.keywords),
            "priority": self.priority,
            "crit_range": self.crit_range,
            "effects_text": self.effects_text,
            "range_text": self.range_text,
        }


@dataclass
class PokemonSpec:
    species: str
    level: int
    types: List[str]
    hp_stat: int
    atk: int
    defense: int
    spatk: int
    spdef: int
    spd: int
    name: Optional[str] = None
    accuracy_cs: int = 0
    evasion_phys: int = 0
    evasion_spec: int = 0
    evasion_spd: int = 0
    tags: List[str] = field(default_factory=list)
    moves: List[MoveSpec] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)
    abilities: List[Dict[str, Any]] = field(default_factory=list)
    statuses: List[Dict[str, Any]] = field(default_factory=list)
    trainer_features: List[Dict[str, Any]] = field(default_factory=list)
    poke_edges: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: List[Dict[str, Any]] = field(default_factory=list)
    movement: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    gender: str = ""
    size: str = ""
    weight: Optional[float] = None
    loyalty: Optional[int] = None
    nature: str = ""
    stat_mode: str = "pre_nature"
    tutor_points: int = 0
    move_sources: Dict[str, str] = field(default_factory=dict)
    poke_edge_choices: Dict[str, Any] = field(default_factory=dict)
    _nature_applied: bool = field(default=False, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PokemonSpec":
        moves = [MoveSpec.from_dict(m) for m in data.get("moves", [])]
        types = _listify(data.get("types", []))
        if not types:
            raise ValueError(f"Pokemon {data.get('name', data.get('species'))} missing types")
        movement_source = data.get("movement", {})
        movement = {}
        for key in ("overland", "sky", "swim", "levitate", "burrow", "h_jump", "l_jump", "power"):
            if isinstance(movement_source, dict) and movement_source.get(key) not in (None, ""):
                movement[key] = _int_field(movement_source.get(key, 0), 0)
            else:
                movement[key] = _int_field(data.get(key, 0), 0)
        return cls(
            species=data.get("species", data.get("name", "Pokemon")),
            level=int(data.get("level", 20)),
            types=types,
            hp_stat=int(data.get("hp_stat", data.get("hp", 10))),
            atk=int(data.get("atk", data.get("attack", 10))),
            defense=int(data.get("def", data.get("defense", 10))),
            spatk=int(data.get("spatk", data.get("sp_atk", 10))),
            spdef=int(data.get("spdef", data.get("sp_def", 10))),
            spd=int(data.get("spd", data.get("speed", 10))),
            name=data.get("name") or data.get("nickname"),
            accuracy_cs=int(data.get("accuracy_cs", 0)),
            evasion_phys=int(data.get("evasion_phys", data.get("evasion_physical", 0))),
            evasion_spec=int(data.get("evasion_spec", data.get("evasion_special", 0))),
            evasion_spd=int(data.get("evasion_spd", data.get("evasion_speed", 0))),
            tags=list(data.get("tags", [])),
            moves=moves,
            items=list(data.get("items", [])),
            abilities=list(data.get("abilities", [])),
            statuses=list(data.get("statuses", [])),
            trainer_features=list(data.get("trainer_features", [])),
            poke_edges=list(data.get("poke_edges", [])),
            capabilities=list(data.get("capabilities", [])),
            movement=movement,
            skills={str(k).lower(): int(v) for k, v in dict(data.get("skills", {})).items()},
            gender=str(data.get("gender", data.get("sex", "")) or ""),
            size=str(data.get("size", "")),
            weight=data.get("weight"),
            loyalty=_opt_int(data.get("loyalty")),
            nature=str(data.get("nature", "")),
            stat_mode=str(data.get("stat_mode", data.get("statMode", "pre_nature")) or "pre_nature"),
            tutor_points=_int_field(data.get("tutor_points", data.get("tutorPoints", 0)), 0),
            move_sources={str(k): str(v) for k, v in dict(data.get("move_sources", data.get("moveSources", {})) or {}).items() if str(k).strip() and str(v).strip()},
            poke_edge_choices=dict(data.get("poke_edge_choices", data.get("pokeEdgeChoices", {})) or {}),
        )

    def to_engine_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name or self.species,
            "species": self.species,
            "level": self.level,
            "types": self.types,
            "hp_stat": self.hp_stat,
            "atk": self.atk,
            "def": self.defense,
            "spatk": self.spatk,
            "spdef": self.spdef,
            "spd": self.spd,
            "accuracy_cs": self.accuracy_cs,
            "evasion_phys": self.evasion_phys,
            "evasion_spec": self.evasion_spec,
            "evasion_spd": self.evasion_spd,
            "moves": [m.to_engine_dict() for m in self.moves],
            "items": self.items,
            "abilities": self.abilities,
            "statuses": self.statuses,
            "trainer_features": self.trainer_features,
            "poke_edges": self.poke_edges,
            "capabilities": self.capabilities,
            "movement": dict(self.movement),
            "skills": dict(self.skills),
            "gender": self.gender,
            "size": self.size,
            "weight": self.weight,
            "loyalty": self.loyalty,
            "nature": self.nature,
            "stat_mode": self.stat_mode,
            "tutor_points": self.tutor_points,
            "move_sources": dict(self.move_sources),
            "poke_edge_choices": dict(self.poke_edge_choices),
        }

    def level_score(self) -> int:
        return self.level


@dataclass
class TrainerFeatureSpec:
    """Serializable trainer feature definition for future hook-based execution."""

    feature_id: str
    name: str
    frequency: str = "At-Will"
    action_cost: str = "Free"
    trigger: str = ""
    min_trainer_level: int = 0
    required_classes: List[str] = field(default_factory=list)
    required_subclasses: List[str] = field(default_factory=list)
    required_features: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    target_rules: Dict[str, Any] = field(default_factory=dict)
    effect_payload: Any = field(default_factory=dict)
    description: str = ""
    enabled: bool = True
    cooldown_rounds: int = 0
    league_legal: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainerFeatureSpec":
        fid = (
            data.get("feature_id")
            or data.get("id")
            or str(data.get("name", "feature")).strip().lower().replace(" ", "-")
        )
        raw_conditions = data.get("conditions", data.get("condition", {}))
        conditions = dict(raw_conditions) if isinstance(raw_conditions, dict) else {}
        raw_target_rules = data.get("target_rules", {})
        target_rules = dict(raw_target_rules) if isinstance(raw_target_rules, dict) else {}
        raw_prereq = data.get("prerequisites", {})
        prereq = dict(raw_prereq) if isinstance(raw_prereq, dict) else {}
        min_level = _int_field(
            data.get("min_trainer_level", data.get("level_required", prereq.get("min_trainer_level", prereq.get("level", 0)))),
            0,
        )
        required_classes = _listify(
            data.get("required_classes", prereq.get("classes", prereq.get("class", [])))
        )
        required_subclasses = _listify(
            data.get("required_subclasses", prereq.get("subclasses", prereq.get("subclass", [])))
        )
        required_features = _listify(
            data.get("required_features", prereq.get("features", prereq.get("feature", [])))
        )
        raw_effect = data.get("effect_payload", data.get("effect", {}))
        if isinstance(raw_effect, list):
            effect_payload: Any = [dict(entry) for entry in raw_effect if isinstance(entry, dict)]
        elif isinstance(raw_effect, dict):
            effect_payload = dict(raw_effect)
        else:
            effect_payload = {}
        return cls(
            feature_id=str(fid),
            name=str(data.get("name", fid)),
            frequency=str(data.get("frequency", "At-Will")),
            action_cost=str(data.get("action_cost", data.get("cost", "Free"))),
            trigger=str(data.get("trigger", "")),
            min_trainer_level=min_level,
            required_classes=required_classes,
            required_subclasses=required_subclasses,
            required_features=required_features,
            conditions=conditions,
            target_rules=target_rules,
            effect_payload=effect_payload,
            description=str(data.get("description", "")),
            enabled=bool(data.get("enabled", True)),
            cooldown_rounds=int(data.get("cooldown_rounds", data.get("cooldown", 0)) or 0),
            league_legal=bool(data.get("league_legal", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "name": self.name,
            "frequency": self.frequency,
            "action_cost": self.action_cost,
            "trigger": self.trigger,
            "min_trainer_level": self.min_trainer_level,
            "required_classes": list(self.required_classes),
            "required_subclasses": list(self.required_subclasses),
            "required_features": list(self.required_features),
            "conditions": dict(self.conditions),
            "target_rules": dict(self.target_rules),
            "effect_payload": (
                [dict(entry) for entry in self.effect_payload if isinstance(entry, dict)]
                if isinstance(self.effect_payload, list)
                else dict(self.effect_payload)
                if isinstance(self.effect_payload, dict)
                else {}
            ),
            "description": self.description,
            "enabled": self.enabled,
            "cooldown_rounds": self.cooldown_rounds,
            "league_legal": self.league_legal,
        }


@dataclass
class TrainerClassSpec:
    """Serializable trainer class bundle (class/subclass/features/resources)."""

    class_id: str
    subclass_id: str = ""
    level: int = 1
    feature_slots: int = 0
    known_features: List[TrainerFeatureSpec] = field(default_factory=list)
    passives: List[str] = field(default_factory=list)
    resources: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainerClassSpec":
        features = [TrainerFeatureSpec.from_dict(entry) for entry in data.get("known_features", [])]
        resources_raw = dict(data.get("resources", {}))
        resources = {str(key): int(value) for key, value in resources_raw.items() if key is not None}
        class_id = (
            data.get("class_id")
            or data.get("id")
            or str(data.get("name", "trainer-class")).strip().lower().replace(" ", "-")
        )
        return cls(
            class_id=str(class_id),
            subclass_id=str(data.get("subclass_id", data.get("subclass", ""))),
            level=int(data.get("level", 1)),
            feature_slots=int(data.get("feature_slots", 0)),
            known_features=features,
            passives=[str(entry) for entry in data.get("passives", []) if str(entry).strip()],
            resources=resources,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_id": self.class_id,
            "subclass_id": self.subclass_id,
            "level": self.level,
            "feature_slots": self.feature_slots,
            "known_features": [entry.to_dict() for entry in self.known_features],
            "passives": list(self.passives),
            "resources": dict(self.resources),
        }


@dataclass
class TrainerSideSpec:
    """Describes one trainer (or faction) participating in a matchup."""

    identifier: str
    name: str
    controller: str = "ai"
    team: str = "neutral"
    ai_level: str = "standard"
    pokemon: List[PokemonSpec] = field(default_factory=list)
    start_positions: List[Tuple[int, int]] = field(default_factory=list)
    initiative_modifier: int = 0
    speed: Optional[int] = None
    skills: Dict[str, int] = field(default_factory=dict)
    save_bonus: int = 0
    evasion_phys: int = 0
    evasion_spec: int = 0
    evasion_spd: int = 0
    trainer_class: Optional[TrainerClassSpec] = None
    trainer_features: List[TrainerFeatureSpec] = field(default_factory=list)
    trainer_edges: List[TrainerFeatureSpec] = field(default_factory=list)
    feature_resources: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainerSideSpec":
        pokemon_entries = [PokemonSpec.from_dict(entry) for entry in data.get("pokemon", [])]
        positions = [tuple(pos) for pos in data.get("start_positions", []) if isinstance(pos, (list, tuple))]
        identifier = data.get("identifier") or data.get("id") or (data.get("name", "trainer").lower().replace(" ", "-"))
        name = data.get("name") or identifier.title()
        controller = data.get("controller", "ai")
        team = data.get("team", controller)
        speed_value = data.get("speed", data.get("trainer_speed"))
        raw_skills = dict(data.get("skills", data.get("trainer_skills", {})) or {})
        class_payload = data.get("trainer_class") or data.get("class_spec")
        trainer_class = TrainerClassSpec.from_dict(class_payload) if isinstance(class_payload, dict) else None
        features_payload = data.get("trainer_features", data.get("features", []))
        features: List[TrainerFeatureSpec] = []
        for entry in features_payload:
            if isinstance(entry, TrainerFeatureSpec):
                features.append(entry)
                continue
            if isinstance(entry, dict):
                features.append(TrainerFeatureSpec.from_dict(entry))
                continue
            if isinstance(entry, str) and entry.strip():
                features.append(TrainerFeatureSpec.from_dict({"name": entry.strip()}))
        if trainer_class and trainer_class.known_features:
            existing_ids = {entry.feature_id for entry in features}
            for entry in trainer_class.known_features:
                if entry.feature_id not in existing_ids:
                    features.append(entry)
        edges_payload = data.get("trainer_edges", data.get("edges", []))
        edges: List[TrainerFeatureSpec] = []
        for entry in edges_payload:
            if isinstance(entry, TrainerFeatureSpec):
                edges.append(entry)
                continue
            if isinstance(entry, dict):
                edges.append(TrainerFeatureSpec.from_dict(entry))
                continue
            if isinstance(entry, str) and entry.strip():
                edges.append(TrainerFeatureSpec.from_dict({"name": entry.strip()}))
        resources_payload = dict(data.get("feature_resources", data.get("resources", {})))
        feature_resources = {
            str(key): int(value)
            for key, value in resources_payload.items()
            if key is not None
        }
        if trainer_class:
            for key, value in trainer_class.resources.items():
                feature_resources.setdefault(str(key), int(value))
        return cls(
            identifier=str(identifier),
            name=str(name),
            controller=str(controller),
            team=str(team),
            ai_level=str(data.get("ai_level", "standard")),
            pokemon=pokemon_entries,
            start_positions=positions,
            initiative_modifier=int(data.get("initiative_modifier", data.get("initiative", 0))),
            speed=int(speed_value) if speed_value is not None else None,
            skills={str(key).lower(): int(value) for key, value in raw_skills.items() if key is not None},
            save_bonus=int(data.get("save_bonus", data.get("trainer_save_bonus", 0)) or 0),
            evasion_phys=int(data.get("evasion_phys", data.get("trainer_evasion_phys", 0)) or 0),
            evasion_spec=int(data.get("evasion_spec", data.get("trainer_evasion_spec", 0)) or 0),
            evasion_spd=int(data.get("evasion_spd", data.get("trainer_evasion_spd", 0)) or 0),
            trainer_class=trainer_class,
            trainer_features=features,
            trainer_edges=edges,
            feature_resources=feature_resources,
        )


@dataclass
class GridSpec:
    width: int = 15
    height: int = 10
    scale: float = 1.0
    blockers: List[Tuple[int, int]] = field(default_factory=list)
    tiles: Dict[Tuple[int, int], Dict[str, object]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridSpec":
        blockers = [tuple(pair) for pair in data.get("blockers", [])]
        raw_tiles = data.get("tiles", {})
        tiles: Dict[Tuple[int, int], Dict[str, object]] = {}

        def normalize_hazards(raw: Any) -> Dict[str, int]:
            out: Dict[str, int] = {}
            if not raw:
                return out
            if isinstance(raw, dict):
                for name, count in raw.items():
                    if name is None:
                        continue
                    try:
                        layers = int(count)
                    except (TypeError, ValueError):
                        continue
                    if layers <= 0:
                        continue
                    out[str(name).strip().lower()] = layers
            return out

        for key, value in raw_tiles.items():
            coord: Optional[Tuple[int, int]] = None
            if isinstance(key, (list, tuple)) and len(key) == 2:
                try:
                    coord = (int(key[0]), int(key[1]))
                except (TypeError, ValueError):
                    coord = None
            else:
                parts = str(key).split(",")
                if len(parts) == 2:
                    try:
                        coord = (int(parts[0]), int(parts[1]))
                    except ValueError:
                        coord = None
            if coord is None:
                continue
            tile_meta: Dict[str, object]
            if isinstance(value, dict):
                tile_meta = {str(k): v for k, v in value.items()}
                if "type" in tile_meta and tile_meta["type"] is not None:
                    tile_meta["type"] = str(tile_meta["type"])
            else:
                tile_meta = {"type": str(value)}
            hazards = normalize_hazards(tile_meta.get("hazards"))
            if hazards:
                tile_meta["hazards"] = hazards
            else:
                tile_meta.pop("hazards", None)
            tiles[coord] = tile_meta
        return cls(
            width=int(data.get("width", 15)),
            height=int(data.get("height", 10)),
            scale=float(data.get("scale", 1.0)),
            blockers=blockers,
            tiles=tiles,
        )

    def to_engine_grid(self):  # type: ignore[override]
        from . import ptu_engine

        return ptu_engine.Grid(
            width=self.width,
            height=self.height,
            scale=self.scale,
            blockers=list(self.blockers),
        )


@dataclass
class CampaignSpec:
    name: str
    description: str = ""
    default_weather: str = "Clear"
    grid: GridSpec = field(default_factory=GridSpec)
    players: List[PokemonSpec] = field(default_factory=list)
    foes: List[PokemonSpec] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignSpec":
        players = [PokemonSpec.from_dict(p) for p in data.get("players", [])]
        foes = [PokemonSpec.from_dict(p) for p in data.get("foes", [])]
        if not players or not foes:
            raise ValueError("Campaign needs at least one player and one foe entry")
        grid = GridSpec.from_dict(data.get("grid", {}))
        return cls(
            name=data.get("name", "Unnamed Campaign"),
            description=data.get("description", ""),
            default_weather=data.get("default_weather", data.get("weather", "Clear")),
            grid=grid,
            players=players,
            foes=foes,
            metadata=data.get("metadata", {}),
        )

    def summary(self) -> str:
        return (
            f"{self.name}: {len(self.players)} player mons vs {len(self.foes)} foes. "
            f"Weather={self.default_weather}, grid={self.grid.width}x{self.grid.height}."
        )


@dataclass
class MatchupSpec:
    you: PokemonSpec
    foe: PokemonSpec
    label: str = ""
    you_start: Optional[Tuple[int, int]] = None
    foe_start: Optional[Tuple[int, int]] = None
    sides: List[TrainerSideSpec] = field(default_factory=list)

    def sides_or_default(self) -> List[TrainerSideSpec]:
        if self.sides:
            return copy.deepcopy(self.sides)
        player_side = TrainerSideSpec(
            identifier="player",
            name=self.you.name or self.you.species,
            controller="player",
            team="players",
            ai_level="standard",
            pokemon=[self.you],
            start_positions=[self.you_start] if self.you_start else [],
        )
        foe_side = TrainerSideSpec(
            identifier="foe",
            name=self.foe.name or self.foe.species,
            controller="ai",
            team="foes",
            ai_level="standard",
            pokemon=[self.foe],
            start_positions=[self.foe_start] if self.foe_start else [],
        )
        return [player_side, foe_side]

    def player_side(self) -> TrainerSideSpec:
        for side in self.sides_or_default():
            if side.controller == "player":
                return side
        return self.sides_or_default()[0]

    def foe_side(self) -> TrainerSideSpec:
        for side in self.sides_or_default():
            if side.controller != "player":
                return side
        return self.sides_or_default()[-1]


@dataclass
class MatchPlan:
    matchups: List[MatchupSpec]
    weather: str
    grid: GridSpec
    battle_context: str = "full_contact"
    active_slots: int = 1
    description: str = ""
    seed: Optional[int] = None
    default_you_start: Tuple[int, int] = (3, 3)
    default_foe_start: Tuple[int, int] = (11, 3)

    def __post_init__(self) -> None:
        if not self.matchups:
            raise ValueError("Match plan needs at least one matchup")

    def each_matchup(self) -> Iterable[Tuple[int, MatchupSpec]]:
        for idx, matchup in enumerate(self.matchups, start=1):
            yield idx, matchup

    def describe(self) -> str:
        sides = self.matchups[0].sides_or_default()
        summary = " vs ".join(f"{side.name}:{len(side.pokemon)}" for side in sides)
        return (
            f"{len(self.matchups)} duel(s) | {summary} | weather={self.weather} "
            f"| context={self.battle_context} | active={self.active_slots}"
        )
