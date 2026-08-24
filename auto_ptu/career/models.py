from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields as dataclass_fields
from datetime import datetime, timezone
import math
import os
from typing import Any, Dict, List, Optional, Type, TypeVar


CURRENT_CAREER_VERSION = "career-0.11.0"
CURRENT_NARRATIVE_VERSION = "career-hooks-0.8.0"


T = TypeVar("T")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _known_dataclass_values(model_cls: Type[T], payload: Dict[str, Any]) -> Dict[str, Any]:
    known_fields = {entry.name for entry in dataclass_fields(model_cls)}
    return {key: value for key, value in dict(payload).items() if key in known_fields}


def _load_dataclass(model_cls: Type[T], payload: Dict[str, Any]) -> T:
    return model_cls(**_known_dataclass_values(model_cls, payload))


def _safe_nonnegative_int(value: Any, default: int = 0) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return max(0, int(number))


def _safe_relationships(value: Any) -> Dict[str, int]:
    """Recover durable social memory without trusting malformed save payloads."""
    if not isinstance(value, dict):
        return {}
    relationships: Dict[str, int] = {}
    for raw_name, raw_bond in value.items():
        name = str(raw_name).strip()
        if not name:
            continue
        relationships[name] = _safe_nonnegative_int(raw_bond)
    return relationships


def _safe_inventory(value: Any) -> Dict[str, int]:
    """Recover bag state while preserving forward-compatible item names."""
    if not isinstance(value, dict):
        return {}
    inventory: Dict[str, int] = {}
    for raw_name, raw_quantity in value.items():
        name = str(raw_name).strip()
        if not name:
            continue
        inventory[name] = _safe_nonnegative_int(raw_quantity)
    return inventory


def _safe_pokemon_payloads(value: Any) -> List[Dict[str, Any]]:
    """Keep valid persisted Pokémon records and discard malformed container entries."""
    if not isinstance(value, list):
        return []
    return [dict(entry) for entry in value if isinstance(entry, dict)]


def _safe_active_roster(value: Any, pokemon: List["CareerPokemon"]) -> List[str]:
    """Recover a complete legal active team from persisted roster identifiers."""
    eligible_order = [
        entry.id
        for entry in pokemon
        if entry.status != "retired" and entry.career_health > 0
    ]
    eligible_ids = set(eligible_order)
    requested: List[str] = []
    if isinstance(value, list):
        for raw_id in value:
            if not isinstance(raw_id, str):
                continue
            pokemon_id = raw_id.strip()
            if pokemon_id in eligible_ids and pokemon_id not in requested:
                requested.append(pokemon_id)
            if len(requested) >= 6:
                break
    target_size = min(6, len(eligible_order))
    if len(requested) < target_size:
        requested.extend(
            pokemon_id
            for pokemon_id in eligible_order
            if pokemon_id not in requested
        )
    return requested[:target_size]


@dataclass
class ContentVersion:
    rules: str = "ptu-1.05-autoptu"
    career: str = CURRENT_CAREER_VERSION
    scoring: str = "competitive-0.1.0"
    narrative: str = CURRENT_NARRATIVE_VERSION
    model_digest: str = "authorial-fallback:sha256:5d81ab17f14dd65ec7a398ffb88d97b48670c74f9319ee4c392bf7077dca5da2"

    @classmethod
    def from_environment(cls) -> "ContentVersion":
        digest = os.environ.get("OLLAMA_MODEL_DIGEST", "").strip()
        if digest.startswith("sha256:") and len(digest) == 71:
            return cls(model_digest=digest)
        return cls()


@dataclass
class TrainerCareerBuild:
    name: str
    region: str
    starter: str
    classes: List[str] = field(default_factory=list)
    pokeballs: int = 10


@dataclass
class ClubContract:
    club_id: str
    club_name: str
    region: str
    league: str
    salary: int
    seasons_remaining: int = 1
    loan_slots: int = 1


@dataclass
class CareerDecisionOption:
    id: str
    label: str
    description: str
    risk: str
    transparency: str
    guaranteed: Dict[str, int]
    rewards: List[Dict[str, Any]] = field(default_factory=list)
    gamble: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CareerDecision:
    id: str
    family: str
    title: str
    body: str
    npc_name: str
    options: List[CareerDecisionOption]
    variant: str = ""


@dataclass
class CareerPokemon:
    id: str
    species: str
    caught_species: str
    level: int
    acquired_season: int
    acquired_age: int
    capture_region: str
    is_partner: bool = False
    status: str = "pc"
    matches: int = 0
    wins: int = 0
    taught_moves: List[str] = field(default_factory=list)
    nature: str = ""
    abilities: List[str] = field(default_factory=list)
    stat_training: Dict[str, int] = field(default_factory=dict)
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)
    gimmicks: List[str] = field(default_factory=list)
    ownership: str = "owned"
    loan_club_id: str = ""
    loan_expires_season: int = 0
    career_health: int = 100
    training_wear: int = 0
    retired_season: int = 0
    retired_reason: str = ""


@dataclass
class BattleSpec:
    id: str
    seed: int
    region: str
    league: str
    season: int
    home_club: str
    away_club: str
    home_species: str
    away_species: str
    level: int
    home_pokemon_id: str = ""
    featured: bool = False
    home_level_bonus: int = 0
    away_level_bonus: int = 0
    home_team_species: List[str] = field(default_factory=list)
    home_pokemon_ids: List[str] = field(default_factory=list)
    home_team_levels: List[int] = field(default_factory=list)
    home_team_moves: List[List[str]] = field(default_factory=list)
    home_team_natures: List[str] = field(default_factory=list)
    home_team_abilities: List[List[str]] = field(default_factory=list)
    home_team_stat_training: List[Dict[str, int]] = field(default_factory=list)
    home_team_gimmicks: List[str] = field(default_factory=list)
    away_team_species: List[str] = field(default_factory=list)
    away_team_levels: List[int] = field(default_factory=list)
    away_team_rarities: List[str] = field(default_factory=list)
    away_team_gimmicks: List[str] = field(default_factory=list)
    difficulty_label: str = "even"
    home_ai_level: str = "tactical"
    away_ai_level: str = "tactical"


@dataclass
class BattleTranscript:
    battle_id: str
    spec: BattleSpec
    winner_team: Optional[str]
    winner_label: Optional[str]
    rounds: int
    events: List[Dict[str, Any]]
    initial_state: Dict[str, Any]
    final_state: Dict[str, Any]
    sha256: str
    engine_version: str = "ptu-1.05-autoptu"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "BattleTranscript":
        raw = dict(payload)
        raw["spec"] = _load_dataclass(BattleSpec, raw["spec"])
        return cls(**_known_dataclass_values(cls, raw))


@dataclass
class SeasonState:
    number: int
    age: int
    league: str
    club_name: str
    status: str = "decision"
    wins: int = 0
    losses: int = 0
    draws: int = 0
    score_delta: int = 0
    title_won: bool = False
    promoted: bool = False
    relegated: bool = False
    decision: Optional[CareerDecision] = None
    battles: List[BattleSpec] = field(default_factory=list)
    battle_ids: List[str] = field(default_factory=list)
    decisions_required: int = 1
    decisions_completed: int = 0
    decision_history: List[Dict[str, Any]] = field(default_factory=list)
    training_completed: bool = False
    training_method: str = ""
    training_completed_ids: List[str] = field(default_factory=list)


@dataclass
class CareerSummary:
    seasons: int
    final_age: int
    highest_league: str
    wins: int
    losses: int
    titles: int
    score: int
    retirement_reason: str
    achievements: List[str]
    pokemon_owned: int = 0
    evolutions: int = 0
    partner_species: str = ""


@dataclass
class CareerRun:
    id: str
    player_id: str
    seed: int
    mode: str
    locale: str
    build: TrainerCareerBuild
    ranked: bool = False
    daily_challenge_id: str = ""
    attempt_no: int = 0
    age: int = 12
    league: str = "junior"
    season_number: int = 1
    health: int = 100
    reputation: int = 0
    development: int = 0
    scouting: int = 0
    finances: int = 0
    career_earnings: int = 0
    money: int = 0
    pokedex_level: int = 0
    license_status: str = "active"
    seasons_without_contract: int = 0
    score: int = 0
    status: str = "active"
    retirement_reason: str = ""
    revision: int = 0
    contract: Optional[ClubContract] = None
    roster: List[str] = field(default_factory=list)
    pokemon: List[CareerPokemon] = field(default_factory=list)
    active_roster: List[str] = field(default_factory=list)
    relationships: Dict[str, int] = field(default_factory=dict)
    relationship_effects: Dict[str, Any] = field(default_factory=dict)
    inventory: Dict[str, int] = field(default_factory=dict)
    totals: Dict[str, int] = field(default_factory=lambda: {"wins": 0, "losses": 0, "draws": 0, "titles": 0})
    achievements: List[str] = field(default_factory=list)
    class_effects: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    season: Optional[SeasonState] = None
    versions: ContentVersion = field(default_factory=ContentVersion)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    summary: Optional[CareerSummary] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CareerRun":
        build = _load_dataclass(TrainerCareerBuild, payload["build"])
        contract = _load_dataclass(ClubContract, payload["contract"]) if payload.get("contract") else None
        versions = _load_dataclass(ContentVersion, payload.get("versions") or {})
        season_payload = payload.get("season")
        season = None
        if isinstance(season_payload, dict):
            raw = dict(season_payload)
            decision_payload = raw.pop("decision", None)
            battles_payload = raw.pop("battles", [])
            decision = None
            if isinstance(decision_payload, dict):
                options_payload = decision_payload.get("options", [])
                if not isinstance(options_payload, list):
                    options_payload = []
                options = [
                    _load_dataclass(CareerDecisionOption, entry)
                    for entry in options_payload
                    if isinstance(entry, dict)
                ]
                decision_values = _known_dataclass_values(CareerDecision, decision_payload)
                decision_values["options"] = options
                decision = CareerDecision(**decision_values)
            season_values = _known_dataclass_values(SeasonState, raw)
            season_values["decision"] = decision
            if not isinstance(battles_payload, list):
                battles_payload = []
            season_values["battles"] = [
                _load_dataclass(BattleSpec, entry)
                for entry in battles_payload
                if isinstance(entry, dict)
            ]
            season = SeasonState(**season_values)
        pokemon_payload = _safe_pokemon_payloads(payload.get("pokemon"))
        pokemon = [_load_dataclass(CareerPokemon, entry) for entry in pokemon_payload]
        if not pokemon:
            legacy_roster = list(payload.get("roster") or [build.starter])
            pokemon = [
                CareerPokemon(
                    id=f"{payload['id']}-p{index + 1:03d}",
                    species=str(species),
                    caught_species=str(species),
                    level=5,
                    acquired_season=1,
                    acquired_age=12,
                    capture_region=build.region,
                    is_partner=index == 0,
                    status="active" if index < 6 else "pc",
                )
                for index, species in enumerate(legacy_roster)
            ]
        active_roster = _safe_active_roster(payload.get("active_roster"), pokemon)
        summary = _load_dataclass(CareerSummary, payload["summary"]) if payload.get("summary") else None
        values = dict(payload)
        for key in ("build", "contract", "versions", "season", "summary", "pokemon", "active_roster"):
            values.pop(key, None)
        if "money" in values:
            values["money"] = _safe_nonnegative_int(values["money"])
        else:
            values["money"] = _safe_nonnegative_int(values.get("career_earnings", 0))
        raw_totals = values.get("totals")
        if not isinstance(raw_totals, dict):
            raw_totals = {}
        values["totals"] = {
            key: _safe_nonnegative_int(raw_totals.get(key, 0))
            for key in ("wins", "losses", "draws", "titles")
        }
        values["relationships"] = _safe_relationships(values.get("relationships"))
        values["inventory"] = _safe_inventory(values.get("inventory"))
        values = _known_dataclass_values(cls, values)
        return cls(
            **values,
            build=build,
            contract=contract,
            versions=versions,
            season=season,
            summary=summary,
            pokemon=pokemon,
            active_roster=active_roster,
        )


@dataclass
class DailyChallenge:
    id: str
    date: str
    region: str
    seed: int
    content_version: str
    rules_version: str
    modes: List[str] = field(default_factory=lambda: ["simple", "advanced"])
    attempts_per_mode: int = 3


@dataclass
class LeaderboardEntry:
    challenge_id: str
    mode: str
    player_id: str
    handle: str
    score: int
    achievements: List[str]
    run_id: str
    attempt_no: int
    completed_at: str = field(default_factory=utc_now)
