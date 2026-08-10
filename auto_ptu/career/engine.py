from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Callable, Dict, List, Optional

from .battle import simulate_battle
from .catalogs import LEAGUES, LEAGUE_ORDER, REGIONS
from .class_adapters import validate_selected_classes
from .decisions import apply_option, build_season_decision
from .models import (
    BattleSpec,
    BattleTranscript,
    CareerRun,
    CareerSummary,
    ClubContract,
    ContentVersion,
    CURRENT_CAREER_VERSION,
    CURRENT_NARRATIVE_VERSION,
    DailyChallenge,
    SeasonState,
    TrainerCareerBuild,
    utc_now,
)


BattleRunner = Callable[[BattleSpec], BattleTranscript]


def stable_seed(*parts: object) -> int:
    payload = ":".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0x7FFFFFFF


class CareerEngine:
    def __init__(self, battle_runner: BattleRunner = simulate_battle) -> None:
        self.battle_runner = battle_runner

    def new_run(
        self,
        *,
        player_id: str,
        name: str,
        region: str,
        starter: str,
        classes: List[str],
        mode: str = "simple",
        locale: str = "es",
        seed: Optional[int] = None,
        ranked: bool = False,
        daily_challenge_id: str = "",
        attempt_no: int = 0,
    ) -> CareerRun:
        region_key = str(region).strip().lower()
        if region_key not in REGIONS:
            raise ValueError(f"Unknown career region: {region}")
        mode_key = str(mode).strip().lower()
        if mode_key not in {"simple", "advanced"}:
            raise ValueError("Career mode must be 'simple' or 'advanced'.")
        canonical_starter = next(
            (entry for entry in REGIONS[region_key].underdogs if entry.lower() == str(starter).strip().lower()),
            None,
        )
        if canonical_starter is None:
            raise ValueError(f"{starter} is not an eligible {REGIONS[region_key].label} underdog.")
        canonical_classes = validate_selected_classes(classes)
        run_id = str(uuid.uuid4())
        run_seed = int(seed if seed is not None else stable_seed(run_id, player_id))
        club = REGIONS[region_key].clubs[0]
        run = CareerRun(
            id=run_id,
            player_id=str(player_id or "guest"),
            seed=run_seed,
            mode=mode_key,
            locale="es" if str(locale).lower().startswith("es") else "en",
            build=TrainerCareerBuild(
                name=str(name).strip() or "Rookie Trainer",
                region=region_key,
                starter=canonical_starter,
                classes=canonical_classes,
            ),
            ranked=ranked,
            daily_challenge_id=daily_challenge_id,
            attempt_no=attempt_no,
            contract=ClubContract(
                club_id=_slug(club),
                club_name=club,
                region=region_key,
                league="junior",
                salary=120,
                seasons_remaining=1,
            ),
            roster=[canonical_starter],
            versions=ContentVersion.from_environment(),
        )
        run.timeline.append(
            {
                "type": "career.started",
                "season": 1,
                "age": 12,
                "label": f"{run.build.name} joined {club} with {canonical_starter}.",
            }
        )
        run.season = self._open_season(run)
        return run

    def advance_season(self, run: CareerRun, *, option_id: str) -> tuple[CareerRun, List[BattleTranscript]]:
        if run.status != "active" or run.season is None:
            raise ValueError("This career cannot advance.")
        decision = run.season.decision
        if decision is None:
            raise ValueError("The season has no pending decision.")
        option = next((entry for entry in decision.options if entry.id == option_id), None)
        if option is None:
            raise ValueError(f"Decision option is not legal for this season: {option_id}")
        if run.versions.career != CURRENT_CAREER_VERSION:
            run.timeline.append(
                {
                    "type": "career.version_migrated",
                    "season": run.season_number,
                    "age": run.age,
                    "from": run.versions.career,
                    "to": CURRENT_CAREER_VERSION,
                }
            )
            run.versions.career = CURRENT_CAREER_VERSION
            run.versions.narrative = CURRENT_NARRATIVE_VERSION
        decision_result = apply_option(run, option)
        run.season.decision_history.append(
            {"decision_id": decision.id, "option_id": option.id, "label": option.label, "effects": decision_result}
        )
        run.season.decisions_completed += 1
        if run.season.decisions_completed < run.season.decisions_required:
            run.season.decision = build_season_decision(run, run.season.decisions_completed)
            run.revision += 1
            run.updated_at = utc_now()
            return run, []
        specs = self._schedule(run)
        transcripts = [self.battle_runner(spec) for spec in specs]
        wins = sum(1 for transcript in transcripts if transcript.winner_team == "career-home")
        losses = sum(1 for transcript in transcripts if transcript.winner_team == "career-away")
        draws = len(transcripts) - wins - losses
        season = run.season
        season.status = "complete"
        season.wins = wins
        season.losses = losses
        season.draws = draws
        season.battles = specs
        season.battle_ids = [entry.battle_id for entry in transcripts]
        run.totals["wins"] += wins
        run.totals["losses"] += losses
        run.totals["draws"] += draws
        outcome = self._apply_competitive_progression(run, season)
        self._apply_health_and_contract(run, wins=wins, losses=losses)
        run.timeline.append(
            {
                "type": "season.completed",
                "season": run.season_number,
                "age": run.age,
                "league": season.league,
                "club": season.club_name,
                "record": f"{wins}-{losses}-{draws}",
                "decision": option.label,
                "decision_effects": decision_result,
                "battle_ids": list(season.battle_ids),
                "score_delta": season.score_delta,
                **outcome,
            }
        )
        run.revision += 1
        if self._forced_retirement_reason(run):
            self.retire(run, self._forced_retirement_reason(run))
            return run, transcripts
        run.age += 1
        run.season_number += 1
        run.season = self._open_season(run)
        run.updated_at = utc_now()
        return run, transcripts

    def retire(self, run: CareerRun, reason: str = "voluntary") -> CareerRun:
        if run.status == "retired":
            return run
        run.status = "retired"
        run.retirement_reason = str(reason or "voluntary")
        highest = max(
            (str(entry.get("league") or "junior") for entry in run.timeline if entry.get("type") == "season.completed"),
            key=lambda value: LEAGUE_ORDER.index(value) if value in LEAGUE_ORDER else 0,
            default=run.league,
        )
        run.summary = CareerSummary(
            seasons=sum(1 for entry in run.timeline if entry.get("type") == "season.completed"),
            final_age=run.age,
            highest_league=highest,
            wins=run.totals["wins"],
            losses=run.totals["losses"],
            titles=run.totals["titles"],
            score=run.score,
            retirement_reason=run.retirement_reason,
            achievements=list(run.achievements),
        )
        run.timeline.append(
            {
                "type": "career.retired",
                "season": run.season_number,
                "age": run.age,
                "reason": run.retirement_reason,
                "score": run.score,
            }
        )
        run.revision += 1
        run.updated_at = utc_now()
        return run

    def daily_challenge(self, day: date) -> DailyChallenge:
        region_ids = tuple(REGIONS)
        region = region_ids[day.toordinal() % len(region_ids)]
        return DailyChallenge(
            id=f"daily-{day.isoformat()}",
            date=day.isoformat(),
            region=region,
            seed=stable_seed("daily", day.isoformat(), CURRENT_CAREER_VERSION),
            content_version=CURRENT_CAREER_VERSION,
            rules_version="ptu-1.05-autoptu",
        )

    def _open_season(self, run: CareerRun) -> SeasonState:
        club = run.contract.club_name if run.contract else "Independent"
        required = 1 if run.mode == "simple" else 3
        season = SeasonState(
            number=run.season_number,
            age=run.age,
            league=run.league,
            club_name=club,
            decisions_required=required,
        )
        season.decision = build_season_decision(run, 0)
        return season

    def _schedule(self, run: CareerRun) -> List[BattleSpec]:
        league = LEAGUES[run.league]
        region = REGIONS[run.build.region]
        clubs = list(region.clubs)
        home = run.contract.club_name if run.contract else clubs[0]
        rng = random.Random(stable_seed(run.seed, run.season_number, "schedule"))
        candidates = [entry for entry in region.underdogs if entry != run.build.starter]
        # Career choices alter preparation without bypassing PTU stats or rolls.
        # Development and facilities raise the partner's generated PTU level;
        # scouting reduces the opponent's preparation. Low health/finances have a
        # visible competitive cost. All thresholds are deterministic.
        home_bonus = min(3, max(0, run.development) // 3)
        home_bonus += min(1, max(0, run.finances) // 4)
        home_bonus -= int(run.health < 45)
        home_bonus -= int(run.finances <= -4)
        away_bonus = -min(2, max(0, run.scouting) // 3)
        specs = []
        for index in range(league.matches):
            away_club = clubs[(index + 1) % len(clubs)]
            if away_club == home:
                away_club = f"{region.label} Academy {index + 1}"
            opponent = candidates[rng.randrange(len(candidates))]
            specs.append(
                BattleSpec(
                    id=f"{run.id}-s{run.season_number}-m{index + 1}",
                    seed=stable_seed(run.seed, run.season_number, index + 1, "battle"),
                    region=run.build.region,
                    league=run.league,
                    season=run.season_number,
                    home_club=home,
                    away_club=away_club,
                    home_species=run.build.starter,
                    away_species=opponent,
                    level=league.min_level + min(15, max(0, run.season_number - 1)),
                    featured=index == league.matches - 1,
                    home_level_bonus=home_bonus,
                    away_level_bonus=away_bonus,
                )
            )
        return specs

    def _apply_competitive_progression(self, run: CareerRun, season: SeasonState) -> dict:
        league = LEAGUES[run.league]
        matches = max(1, season.wins + season.losses + season.draws)
        win_rate = season.wins / matches
        title = win_rate >= 0.75
        promotion = False
        relegation = False
        score_delta = league.weight * (season.wins * 3 - season.losses)
        if title:
            score_delta += league.weight * 20
            run.totals["titles"] += 1
            season.title_won = True
            achievement = f"{league.label} champion"
            if achievement not in run.achievements:
                run.achievements.append(achievement)
        if run.league == "junior":
            if run.age >= 15:
                run.league = "rookie"
                promotion = True
        elif win_rate >= 0.65 and run.league != "elite":
            run.league = LEAGUE_ORDER[LEAGUE_ORDER.index(run.league) + 1]
            promotion = True
        elif win_rate < 0.30 and run.league not in {"junior", "rookie"}:
            run.league = LEAGUE_ORDER[LEAGUE_ORDER.index(run.league) - 1]
            relegation = True
        if promotion:
            score_delta += league.weight * 10
        if relegation:
            score_delta -= league.weight * 8
        season.promoted = promotion
        season.relegated = relegation
        season.score_delta = score_delta
        run.score = max(0, run.score + score_delta)
        if run.contract:
            run.contract.league = run.league
            run.contract.salary = 120 * LEAGUES[run.league].weight + max(0, run.reputation * 5)
        return {"title": title, "promoted": promotion, "relegated": relegation}

    def _apply_health_and_contract(self, run: CareerRun, *, wins: int, losses: int) -> None:
        age_strain = max(0, run.age - 28) // 4
        result_strain = max(0, losses - wins) // 2
        run.health = max(0, min(100, run.health - age_strain - result_strain + (1 if wins > losses else 0)))
        if losses > wins * 2 and run.league != "junior":
            run.seasons_without_contract += 1
            run.contract = None
        else:
            run.seasons_without_contract = 0
            region = REGIONS[run.build.region]
            club = region.clubs[(run.season_number + LEAGUE_ORDER.index(run.league)) % len(region.clubs)]
            run.contract = ClubContract(
                club_id=_slug(club),
                club_name=club,
                region=run.build.region,
                league=run.league,
                salary=120 * LEAGUES[run.league].weight + max(0, run.reputation * 5),
                seasons_remaining=1,
                loan_slots=1 + int(run.league in {"regular", "elite"}),
            )

    @staticmethod
    def _forced_retirement_reason(run: CareerRun) -> str:
        if run.health <= 0:
            return "health"
        if run.license_status != "active":
            return "license"
        if run.seasons_without_contract >= 2:
            return "no_contract"
        return ""


def _slug(value: str) -> str:
    return "-".join(part for part in "".join(char.lower() if char.isalnum() else " " for char in value).split() if part)
