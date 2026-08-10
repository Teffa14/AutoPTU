from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional


CURRENT_CAREER_VERSION = "career-0.6.0"
CURRENT_NARRATIVE_VERSION = "career-hooks-0.5.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)


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
    away_team_species: List[str] = field(default_factory=list)
    away_team_levels: List[int] = field(default_factory=list)
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
        raw["spec"] = BattleSpec(**dict(raw["spec"]))
        return cls(**raw)


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
        build = TrainerCareerBuild(**dict(payload["build"]))
        contract = ClubContract(**dict(payload["contract"])) if payload.get("contract") else None
        versions = ContentVersion(**dict(payload.get("versions") or {}))
        season_payload = payload.get("season")
        season = None
        if season_payload:
            raw = dict(season_payload)
            decision_payload = raw.pop("decision", None)
            battles_payload = raw.pop("battles", [])
            decision = None
            if decision_payload:
                options = [CareerDecisionOption(**dict(entry)) for entry in decision_payload.get("options", [])]
                decision = CareerDecision(**{**dict(decision_payload), "options": options})
            season = SeasonState(
                **raw,
                decision=decision,
                battles=[BattleSpec(**dict(entry)) for entry in battles_payload],
            )
        pokemon_payload = payload.get("pokemon") or []
        pokemon = [CareerPokemon(**dict(entry)) for entry in pokemon_payload]
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
        active_roster = [str(value) for value in payload.get("active_roster") or []]
        if not active_roster:
            active_roster = [entry.id for entry in pokemon[:6]]
        summary = CareerSummary(**dict(payload["summary"])) if payload.get("summary") else None
        fields = dict(payload)
        for key in ("build", "contract", "versions", "season", "summary", "pokemon", "active_roster"):
            fields.pop(key, None)
        return cls(
            **fields,
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
