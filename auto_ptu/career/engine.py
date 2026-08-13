from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Callable, Dict, List, Optional

from .battle import simulate_battle
from .catalogs import LEAGUES, LEAGUE_ORDER, REGIONS
from .class_adapters import selected_class_effects, validate_selected_classes
from .decisions import apply_option, build_season_decision
from .evolutions import evolve_species_for_level
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
from .roster import (
    active_pokemon,
    career_level_cap,
    grant_partner_levels,
    initialize_roster,
    progress_after_season,
    set_active_roster,
)
from .relationships import calculate_relationship_effects, refresh_relationship_effects


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
            (entry for entry in REGIONS[region_key].partner_choices if entry.lower() == str(starter).strip().lower()),
            None,
        )
        if canonical_starter is None:
            raise ValueError(f"{starter} is not an eligible {REGIONS[region_key].label} starter or underdog.")
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
            class_effects=selected_class_effects(canonical_classes),
            versions=ContentVersion.from_environment(),
        )
        run.timeline.append(
            {
                "type": "career.started",
                "season": 1,
                "age": 12,
                "trainer": run.build.name,
                "club": club,
                "starter": canonical_starter,
                "label": f"{run.build.name} joined {club} with {canonical_starter}.",
            }
        )
        initialize_roster(run, stable_seed(run.seed, "academy-intake"))
        refresh_relationship_effects(run)
        run.season = self._open_season(run)
        return run

    def ensure_roster(self, run: CareerRun) -> bool:
        changed = initialize_roster(run, stable_seed(run.seed, run.season_number, "academy-intake"))
        current = selected_class_effects(run.build.classes)
        if run.class_effects != current:
            run.class_effects = current
            changed = True
        relationship_effects = calculate_relationship_effects(run.relationships)
        if run.relationship_effects != relationship_effects:
            run.relationship_effects = relationship_effects
            changed = True
        return changed

    def update_lineup(self, run: CareerRun, pokemon_ids: List[str]) -> CareerRun:
        if run.status != "active":
            raise ValueError("A retired career cannot change its active team.")
        self.ensure_roster(run)
        set_active_roster(run, pokemon_ids)
        run.timeline.append(
            {
                "type": "roster.lineup_changed",
                "season": run.season_number,
                "age": run.age,
                "pokemon_ids": list(run.active_roster),
                "label": "The six-Pokémon active lineup was registered for the next schedule.",
            }
        )
        run.revision += 1
        run.updated_at = utc_now()
        return run

    def prepare_season(self, run: CareerRun, *, option_id: str) -> tuple[CareerRun, List[BattleSpec]]:
        if run.status != "active" or run.season is None:
            raise ValueError("This career cannot advance.")
        if run.season.status == "battle":
            raise ValueError("This season is already waiting for its featured battle.")
        self.ensure_roster(run)
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
        run.season.status = "battle"
        run.season.decision = None
        run.season.battles = specs
        run.season.battle_ids = [entry.id for entry in specs]
        run.timeline.append({
            "type": "season.schedule_ready",
            "season": run.season_number,
            "age": run.age,
            "battle_ids": list(run.season.battle_ids),
            "featured_battle_id": next((entry.id for entry in specs if entry.featured), specs[-1].id),
            "label": "The calendar is locked and the featured match is ready for broadcast.",
        })
        run.revision += 1
        run.updated_at = utc_now()
        return run, specs

    def resolve_prepared_season(
        self,
        run: CareerRun,
        transcripts: List[BattleTranscript],
    ) -> tuple[CareerRun, List[BattleTranscript]]:
        if run.status != "active" or run.season is None or run.season.status != "battle":
            raise ValueError("This season has no prepared calendar to resolve.")
        expected_ids = [entry.id for entry in run.season.battles]
        by_id = {entry.battle_id: entry for entry in transcripts}
        if set(by_id) != set(expected_ids):
            missing = sorted(set(expected_ids) - set(by_id))
            raise ValueError(f"The prepared calendar is incomplete: {', '.join(missing)}")
        transcripts = [by_id[battle_id] for battle_id in expected_ids]
        wins = sum(1 for transcript in transcripts if transcript.winner_team == "career-home")
        losses = sum(1 for transcript in transcripts if transcript.winner_team == "career-away")
        draws = len(transcripts) - wins - losses
        season = run.season
        season.status = "complete"
        season.wins = wins
        season.losses = losses
        season.draws = draws
        specs = list(season.battles)
        season.battle_ids = [entry.battle_id for entry in transcripts]
        run.totals["wins"] += wins
        run.totals["losses"] += losses
        run.totals["draws"] += draws
        achievements_before = set(run.achievements)
        outcome = self._apply_competitive_progression(run, season)
        relationship_outcome = self._apply_health_and_contract(run, wins=wins, losses=losses)
        roster_outcome = progress_after_season(run, specs, transcripts)
        class_outcome = self._apply_class_progression(run)
        self._unlock_achievements(run, season, outcome)
        new_achievements = [entry for entry in run.achievements if entry not in achievements_before]
        run.timeline.append(
            {
                "type": "season.completed",
                "season": run.season_number,
                "age": run.age,
                "league": season.league,
                "club": season.club_name,
                "record": f"{wins}-{losses}-{draws}",
                "decision": str(season.decision_history[-1].get("label") or "") if season.decision_history else "",
                "decision_effects": dict(season.decision_history[-1].get("effects") or {}) if season.decision_history else {},
                "decisions": list(season.decision_history),
                "battle_hashes": [
                    {"id": transcript.battle_id, "sha256": transcript.sha256}
                    for transcript in transcripts
                ],
                "opponents": [spec.away_club for spec in specs],
                "featured_opponent": next((spec.away_club for spec in specs if spec.featured), specs[-1].away_club),
                "score_delta": season.score_delta,
                "lineup": list(run.active_roster),
                **roster_outcome,
                "class_effects": class_outcome,
                "relationship_effects": relationship_outcome,
                "new_achievements": new_achievements,
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

    def advance_season(self, run: CareerRun, *, option_id: str) -> tuple[CareerRun, List[BattleTranscript]]:
        """Compatibility path for simulations and tests that resolve a season at once."""
        run, specs = self.prepare_season(run, option_id=option_id)
        if not specs:
            return run, []
        transcripts = [self.battle_runner(spec) for spec in specs]
        return self.resolve_prepared_season(run, transcripts)

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
            pokemon_owned=len(run.pokemon),
            evolutions=sum(len(entry.evolution_history) for entry in run.pokemon),
            partner_species=run.build.starter,
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
        self.ensure_roster(run)
        league = LEAGUES[run.league]
        region = REGIONS[run.build.region]
        clubs = list(region.clubs)
        home = run.contract.club_name if run.contract else clubs[0]
        rng = random.Random(stable_seed(run.seed, run.season_number, "schedule"))
        lineup = active_pokemon(run)
        candidates = list(region.underdogs)
        # Career choices alter preparation without bypassing PTU stats or rolls.
        # Development and facilities raise the partner's generated PTU level;
        # scouting reduces the opponent's preparation. Low health/finances have a
        # visible competitive cost. All thresholds are deterministic.
        home_bonus = min(3, max(0, run.development) // 3)
        home_bonus += min(1, max(0, run.finances) // 4)
        home_bonus -= int(run.health < 45)
        home_bonus -= int(run.finances <= -4)
        away_bonus = -min(2, max(0, run.scouting) // 3)
        class_effects = selected_class_effects(run.build.classes)
        home_bonus += int(class_effects["battle"].get("home_level_bonus", 0))
        away_bonus += int(class_effects["battle"].get("away_level_bonus", 0))
        relationship_effects = refresh_relationship_effects(run)
        home_bonus += int(relationship_effects.get("home_level_bonus", 0))
        league_floor = league.min_level + min(15, max(0, run.season_number - 1))
        competitive_level = min(career_level_cap(run), max(league_floor, round(sum(entry.level for entry in lineup) / len(lineup))))
        specs = []
        away_clubs = [club for club in clubs if club != home]
        rng.shuffle(away_clubs)
        if not away_clubs:
            away_clubs = [f"{region.label} League Select"]
        rotation = (run.season_number - 1) % len(away_clubs)
        away_clubs = away_clubs[rotation:] + away_clubs[:rotation]
        scheduled_clubs = [away_clubs[index % len(away_clubs)] for index in range(league.matches)]
        previous_featured = next(
            (
                str(entry.get("featured_opponent") or "")
                for entry in reversed(run.timeline)
                if entry.get("type") == "season.completed" and entry.get("featured_opponent")
            ),
            "",
        )
        if len(scheduled_clubs) > 1 and scheduled_clubs[-1] == previous_featured:
            replacement = next(
                (index for index, club in enumerate(scheduled_clubs[:-1]) if club != previous_featured),
                None,
            )
            if replacement is not None:
                scheduled_clubs[replacement], scheduled_clubs[-1] = scheduled_clubs[-1], scheduled_clubs[replacement]
        for index in range(league.matches):
            away_club = scheduled_clubs[index]
            rotation = index % len(lineup)
            match_lineup = lineup[rotation:] + lineup[:rotation]
            pokemon = match_lineup[0]
            eligible_opponents = [entry for entry in candidates if entry not in {member.species for member in match_lineup}] or candidates
            opponent_team: List[str] = []
            pool = list(eligible_opponents)
            rng.shuffle(pool)
            while len(opponent_team) < len(match_lineup):
                if not pool:
                    pool = list(eligible_opponents)
                    rng.shuffle(pool)
                base_species = pool.pop()
                opponent_team.append(
                    evolve_species_for_level(
                        base_species,
                        competitive_level,
                        seed=stable_seed(run.seed, run.season_number, index, len(opponent_team), away_club),
                        region=run.build.region,
                    )
                )
            opponent = opponent_team[0]
            specs.append(
                BattleSpec(
                    id=f"{run.id}-s{run.season_number}-m{index + 1}",
                    seed=stable_seed(run.seed, run.season_number, index + 1, "battle"),
                    region=run.build.region,
                    league=run.league,
                    season=run.season_number,
                    home_club=home,
                    away_club=away_club,
                    home_species=pokemon.species,
                    away_species=opponent,
                    level=competitive_level,
                    home_pokemon_id=pokemon.id,
                    featured=index == league.matches - 1,
                    home_level_bonus=home_bonus,
                    away_level_bonus=away_bonus,
                    home_team_species=[member.species for member in match_lineup],
                    home_pokemon_ids=[member.id for member in match_lineup],
                    home_team_levels=[member.level for member in match_lineup],
                    home_team_moves=[list(member.taught_moves) for member in match_lineup],
                    home_team_natures=[member.nature for member in match_lineup],
                    home_team_abilities=[list(member.abilities) for member in match_lineup],
                    away_team_species=opponent_team,
                    away_team_levels=[competitive_level for _ in opponent_team],
                )
            )
        return specs

    def _apply_class_progression(self, run: CareerRun) -> dict:
        effects = selected_class_effects(run.build.classes)
        applied: Dict[str, int] = {}
        for key, value in effects["season"].items():
            amount = int(value)
            if key == "health":
                before = run.health
                run.health = min(100, max(0, run.health + amount))
                applied[key] = run.health - before
            elif key == "partner_levels":
                partner = next((entry for entry in run.pokemon if entry.is_partner), None)
                before = partner.level if partner else 0
                grant_partner_levels(run, amount, source="trainer_class")
                applied[key] = (partner.level - before) if partner else 0
            elif hasattr(run, key):
                setattr(run, key, int(getattr(run, key)) + amount)
                applied[key] = amount
        event = {
            "type": "class.effect_applied",
            "season": run.season_number,
            "age": run.age,
            "classes": list(run.build.classes),
            "battle": dict(effects["battle"]),
            "season_effects": applied,
            "focus": [entry["focus"] for entry in effects["adapters"]],
            "label": "Trainer class effects changed PTU preparation and career progression.",
        }
        run.timeline.append(event)
        return event

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

    def _unlock_achievements(self, run: CareerRun, season: SeasonState, outcome: dict) -> None:
        """Grant stable career milestones after every fully resolved season."""
        evolution_count = sum(len(entry.evolution_history) for entry in run.pokemon)
        candidates = []
        if run.totals["wins"] >= 1:
            candidates.append("First victory")
        if len(run.pokemon) >= 6:
            candidates.append("Full squad")
        if season.wins > 0 and season.losses == 0:
            candidates.append("Perfect season")
        if evolution_count >= 3:
            candidates.append("Evolution specialist")
        if outcome.get("promoted"):
            candidates.append("Rising star")
        if run.league == "elite":
            candidates.append("Elite contender")
        if run.season_number >= 5:
            candidates.append("Veteran")
        for achievement in candidates:
            if achievement not in run.achievements:
                run.achievements.append(achievement)

    def _apply_health_and_contract(self, run: CareerRun, *, wins: int, losses: int) -> dict:
        relationship_effects = refresh_relationship_effects(run)
        age_strain = max(0, run.age - 28) // 4
        result_strain = max(0, losses - wins) // 2
        recovery = int(relationship_effects.get("season_recovery", 0))
        run.health = max(0, min(100, run.health - age_strain - result_strain + (1 if wins > losses else 0) + recovery))
        guard_used = False
        if losses > wins * 2 and run.league != "junior":
            if relationship_effects.get("contract_guard") and relationship_effects.get("best_contact"):
                contact = str(relationship_effects["best_contact"])
                run.relationships[contact] = max(0, int(run.relationships.get(contact, 0)) - 2)
                relationship_effects = refresh_relationship_effects(run)
                guard_used = True
                run.seasons_without_contract = 0
                run.timeline.append({
                    "type": "relationship.contract_saved",
                    "season": run.season_number,
                    "age": run.age,
                    "name": contact,
                    "cost": 2,
                    "label": f"{contact} used their influence to protect the club contract.",
                })
            else:
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
        outcome = {
            **relationship_effects,
            "recovery_applied": recovery,
            "contract_guard_used": guard_used,
        }
        run.timeline.append({
            "type": "relationship.effect_applied",
            "season": run.season_number,
            "age": run.age,
            **outcome,
            "label": "Career contacts contributed preparation, recovery, and contract support.",
        })
        return outcome

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
