from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ContentVersion:
    rules: str = "ptu-1.05-autoptu"
    career: str = "career-0.1.0"
    scoring: str = "competitive-0.1.0"
    narrative: str = "career-hooks-0.1.0"
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
    gamble: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CareerDecision:
    id: str
    family: str
    title: str
    body: str
    npc_name: str
    options: List[CareerDecisionOption]


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
    featured: bool = False


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
    relationships: Dict[str, int] = field(default_factory=dict)
    totals: Dict[str, int] = field(default_factory=lambda: {"wins": 0, "losses": 0, "draws": 0, "titles": 0})
    achievements: List[str] = field(default_factory=list)
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
        summary = CareerSummary(**dict(payload["summary"])) if payload.get("summary") else None
        fields = dict(payload)
        for key in ("build", "contract", "versions", "season", "summary"):
            fields.pop(key, None)
        return cls(**fields, build=build, contract=contract, versions=versions, season=season, summary=summary)


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
