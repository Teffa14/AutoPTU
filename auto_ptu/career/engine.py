from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Callable, Dict, List, Optional

from .battle import simulate_battle
from .catalogs import (
    FRANCHISE_TRAINERS,
    LEAGUES,
    LEAGUE_ORDER,
    REGIONS,
    choose_encounter_rarity,
    encounter_pool,
)
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
    grant_pokemon_levels,
    grant_stat_training,
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
        if run.season and run.season.status == "decision" and run.season.decision and run.season.decision.family == "evolution":
            run.season.decision = build_season_decision(run, run.season.decisions_completed)
            run.timeline.append({
                "type": "decision.migrated",
                "season": run.season_number,
                "age": run.age,
                "from": "evolution",
                "to": run.season.decision.family,
                "label": "Evolution now happens automatically at the required level.",
            })
            changed = True
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
        salary_outcome = self._pay_season_salary(run)
        outcome = self._apply_competitive_progression(run, season)
        relationship_outcome = self._apply_health_and_contract(run, wins=wins, losses=losses)
        roster_outcome = progress_after_season(run, specs, transcripts)
        class_outcome = self._apply_class_progression(run)
        incident_outcome = self._apply_season_incident(run)
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
                "opponent_species": list(dict.fromkeys(species for spec in specs for species in spec.away_team_species)),
                "opponent_rarities": list(dict.fromkeys(rarity for spec in specs for rarity in spec.away_team_rarities)),
                "featured_opponent": next((spec.away_club for spec in specs if spec.featured), specs[-1].away_club),
                "score_delta": season.score_delta,
                "lineup": list(run.active_roster),
                **roster_outcome,
                "class_effects": class_outcome,
                "relationship_effects": relationship_outcome,
                "incident": incident_outcome,
                "salary": salary_outcome,
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
            pokemon_owned=sum(1 for entry in run.pokemon if entry.ownership == "owned"),
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
        home_bonus = min(3, max(0, run.development) // 3)
        home_bonus += min(1, max(0, run.finances) // 4)
        home_bonus -= int(run.health < 45)
        home_bonus -= min(3, max(0, -run.finances))
        away_bonus = -min(2, max(0, run.scouting) // 3)
        class_effects = selected_class_effects(run.build.classes)
        home_bonus += int(class_effects["battle"].get("home_level_bonus", 0))
        away_bonus += int(class_effects["battle"].get("away_level_bonus", 0))
        relationship_effects = refresh_relationship_effects(run)
        home_bonus += int(relationship_effects.get("home_level_bonus", 0))
        away_bonus -= int(relationship_effects.get("rival_scouting_bonus", 0))
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
        recent_opponents = {
            str(species).casefold()
            for event in run.timeline[-80:]
            if event.get("type") == "season.completed"
            for species in event.get("opponent_species", [])
        }
        rarity_level_adjustment = {
            "common": 0, "rare": -1, "very_rare": -2,
            "epic": -3, "legendary": -5, "mythical": -6,
        }
        for index in range(league.matches):
            away_club = scheduled_clubs[index]
            rotation = index % len(lineup)
            match_lineup = lineup[rotation:] + lineup[:rotation]
            pokemon = match_lineup[0]
            opponent_team: List[str] = []
            opponent_levels: List[int] = []
            opponent_rarities: List[str] = []
            unavailable = {member.species.casefold() for member in match_lineup}
            while len(opponent_team) < len(match_lineup):
                rarity = choose_encounter_rarity(
                    run.build.region,
                    run.league,
                    rng,
                    pokedex_level=max(0, run.pokedex_level - 1),
                )
                pool = list(encounter_pool(run.build.region, rarity))
                rng.shuffle(pool)
                base_species = next(
                    (
                        entry for entry in pool
                        if entry.casefold() not in unavailable | recent_opponents
                        and entry.casefold() not in {value.casefold() for value in opponent_team}
                    ),
                    next((entry for entry in pool if entry.casefold() not in unavailable), pool[0]),
                )
                member_level = max(1, competitive_level + rarity_level_adjustment[rarity])
                evolved = evolve_species_for_level(
                    base_species,
                    member_level,
                    seed=stable_seed(run.seed, run.season_number, index, len(opponent_team), away_club),
                    region=run.build.region,
                )
                opponent_team.append(evolved)
                opponent_levels.append(member_level)
                opponent_rarities.append(rarity)
            opponent = opponent_team[0]
            home_visible_level = sum(member.level + home_bonus for member in match_lineup) / len(match_lineup)
            away_visible_level = sum(level + away_bonus for level in opponent_levels) / len(opponent_levels)
            difficulty = "favored" if home_visible_level >= away_visible_level + 2 else "dangerous" if away_visible_level >= home_visible_level + 2 else "even"
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
                    home_team_stat_training=[dict(member.stat_training) for member in match_lineup],
                    home_team_gimmicks=_battle_gimmicks(match_lineup),
                    away_team_species=opponent_team,
                    away_team_levels=opponent_levels,
                    away_team_rarities=opponent_rarities,
                    away_team_gimmicks=_rival_gimmicks(run.build.region, run.league, len(opponent_team), specs_seed=stable_seed(run.seed, run.season_number, index, "rival-gimmick")),
                    difficulty_label=difficulty,
                )
            )
        return specs

    def _apply_season_incident(self, run: CareerRun) -> dict:
        lineup = active_pokemon(run)
        pokemon = lineup[stable_seed(run.seed, run.season_number, "incident-pokemon") % len(lineup)]
        variant = stable_seed(run.seed, run.season_number, "incident") % 8
        if variant == 0:
            stat = ("atk", "spatk", "spd")[stable_seed(run.seed, run.season_number, "incident-stat") % 3]
            trained = grant_stat_training(run, pokemon.id, stat, 1, source="season_incident")
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "breakthrough", "pokemon": pokemon.species,
                "title_es": f"{pokemon.species} pidió quedarse después del entrenamiento",
                "title_en": f"{pokemon.species} asked to stay after training",
                "detail_es": f"La sesión extra dejó una mejora permanente de +1 en {stat}.",
                "detail_en": f"The extra session produced a permanent +1 {stat} improvement.",
                "effects": {"stat": stat, "amount": int(trained["amount"]) if trained else 0},
            }
        elif variant == 1:
            before = run.health
            run.health = max(0, run.health - 3)
            trained = grant_stat_training(run, pokemon.id, "hp", 2, source="season_incident")
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "hard_match", "pokemon": pokemon.species,
                "title_es": f"{pokemon.species} terminó golpeado, pero más resistente",
                "title_en": f"{pokemon.species} finished bruised but tougher",
                "detail_es": "El cuerpo médico registró el desgaste y una mejora permanente de resistencia.",
                "detail_en": "Medical staff recorded the strain and a permanent endurance gain.",
                "effects": {"health": run.health - before, "stat": "hp", "amount": int(trained["amount"]) if trained else 0},
            }
        elif variant == 2:
            rivals = FRANCHISE_TRAINERS[run.build.region]["rival"]
            contact = f"{rivals[stable_seed(run.seed, run.season_number, 'incident-rival') % len(rivals)]} · rival · {run.build.region.title()}"
            run.relationships[contact] = run.relationships.get(contact, 0) + 1
            refresh_relationship_effects(run)
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "rival_visit", "pokemon": pokemon.species, "contact": contact,
                "title_es": f"{contact.split(' · ')[0]} apareció sin avisar en el entrenamiento",
                "title_en": f"{contact.split(' · ')[0]} arrived at training unannounced",
                "detail_es": "La conversación abrió una rivalidad que puede convertirse en información táctica.",
                "detail_en": "The conversation started a rivalry that can become tactical information.",
                "effects": {"relationship": 1},
            }
        elif variant == 3:
            run.inventory["Training Kit"] = run.inventory.get("Training Kit", 0) + 1
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "equipment_find", "pokemon": pokemon.species,
                "title_es": f"{pokemon.species} encontró material olvidado en el estadio",
                "title_en": f"{pokemon.species} found equipment left in the stadium",
                "detail_es": "El equipo recuperó un Training Kit para futuras sesiones.",
                "detail_en": "The squad recovered a Training Kit for future sessions.",
                "effects": {"item": "Training Kit", "quantity": 1},
            }
        elif variant == 4:
            before = pokemon.level
            evolutions = grant_pokemon_levels(run, pokemon.id, 1, source="informal_scrimmage")
            run.health = max(0, run.health - 1)
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "informal_scrimmage", "pokemon": pokemon.species,
                "title_es": f"{pokemon.species} aceptó un combate informal en la plaza",
                "title_en": f"{pokemon.species} accepted an informal match in the town square",
                "detail_es": "El combate no contó para la liga, pero dejó experiencia real y algo de cansancio.",
                "detail_en": "The match did not count for the league, but produced real experience and some fatigue.",
                "effects": {"levels": pokemon.level - before, "health": -1, "evolutions": evolutions},
            }
        elif variant == 5:
            before = run.health
            run.health = min(100, run.health + 5)
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "family_day", "pokemon": pokemon.species,
                "title_es": "Una visita familiar cambió el ritmo de la semana",
                "title_en": "A family visit changed the rhythm of the week",
                "detail_es": "Elegiste desconectar del club durante un día. No hubo entrenamiento, pero recuperaste energía.",
                "detail_en": "You stepped away from the club for a day. There was no training, but you recovered energy.",
                "effects": {"health": run.health - before},
            }
        elif variant == 6:
            run.reputation += 2
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "regional_festival", "pokemon": pokemon.species,
                "title_es": f"{pokemon.species} fue la sorpresa del festival regional",
                "title_en": f"{pokemon.species} became the regional festival surprise",
                "detail_es": "La exhibición acercó al equipo a la comunidad y mejoró tu valor público.",
                "detail_en": "The exhibition brought the team closer to the community and improved your public value.",
                "effects": {"reputation": 2},
            }
        else:
            run.scouting += 2
            run.finances -= 1
            event = {
                "type": "season.incident", "season": run.season_number, "age": run.age,
                "kind": "travel_disruption", "pokemon": pokemon.species,
                "title_es": "Una conexión perdida obligó a improvisar el viaje",
                "title_en": "A missed connection forced the team to improvise its travel",
                "detail_es": "El cambio costó recursos, pero permitió observar una ruta y rivales que no estaban en el informe.",
                "detail_en": "The change cost resources, but revealed a route and opponents missing from the report.",
                "effects": {"finances": -1, "scouting": 2},
            }
        run.timeline.append(event)
        return event

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
            "label": "Trainer class effects changed preparation and career progression.",
        }
        run.timeline.append(event)
        return event

    def _pay_season_salary(self, run: CareerRun) -> dict:
        salary = max(0, int(run.contract.salary)) if run.contract else 0
        finance_gain = salary // 240 + int(salary > 0)
        if salary:
            run.career_earnings += salary
            run.money += salary
            run.finances += finance_gain
            run.contract.seasons_remaining = max(0, run.contract.seasons_remaining - 1)
        event = {
            "type": "contract.salary_paid",
            "season": run.season_number,
            "age": run.age,
            "club": run.contract.club_name if run.contract else "Independent",
            "salary": salary,
            "finance_gain": finance_gain,
            "career_earnings": run.career_earnings,
            "money": run.money,
            "label": f"Season salary paid: {salary}." if salary else "No club salary was paid this season.",
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
        recovery = int(relationship_effects.get("season_recovery", 0)) + int(relationship_effects.get("owner_recovery_bonus", 0))
        run.health = max(0, min(100, run.health - age_strain - result_strain + (1 if wins > losses else 0) + recovery))
        mentor_training = None
        mentor_bonus = int(relationship_effects.get("mentor_training_bonus", 0))
        if mentor_bonus > 0:
            partner = next((entry for entry in run.pokemon if entry.is_partner), None)
            if partner:
                stat = ("atk", "def", "spatk", "spdef", "spd")[stable_seed(run.seed, run.season_number, "mentor-stat") % 5]
                mentor_training = grant_stat_training(run, partner.id, stat, mentor_bonus, source="mentor_relationship")
                mentor = next((entry for entry in relationship_effects.get("contact_effects", []) if entry.get("role") == "mentor"), None)
                if mentor_training and mentor:
                    run.timeline.append({
                        "type": "relationship.mentor_training", "season": run.season_number, "age": run.age,
                        "name": mentor["name"], "pokemon": partner.species, "stat": stat,
                        "amount": mentor_training["amount"],
                        "label": f"{str(mentor['name']).split(' · ')[0]} trained {partner.species}.",
                    })
        guard_used = False
        poor_season = losses > wins * 2 and run.league != "junior"
        if poor_season:
            if run.contract is not None and run.contract.seasons_remaining > 0:
                run.seasons_without_contract = 0
            elif relationship_effects.get("contract_guard") and relationship_effects.get("best_contact"):
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
            if run.contract is None or run.contract.seasons_remaining <= 0:
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
            else:
                run.contract.league = run.league
                run.contract.salary = 120 * LEAGUES[run.league].weight + max(0, run.reputation * 5)
        outcome = {
            **relationship_effects,
            "recovery_applied": recovery,
            "mentor_training": mentor_training,
            "contract_guard_used": guard_used,
            "poor_season": poor_season,
            "contract_warning": run.seasons_without_contract,
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


def _battle_gimmicks(lineup: List) -> List[str]:
    equipped = False
    result: List[str] = []
    for pokemon in lineup:
        gimmick = str(pokemon.gimmicks[0]) if not equipped and pokemon.gimmicks else ""
        result.append(gimmick)
        equipped = equipped or bool(gimmick)
    return result


def _rival_gimmicks(region: str, league: str, team_size: int, *, specs_seed: int) -> List[str]:
    result = ["" for _ in range(team_size)]
    chance = {"junior": 0, "rookie": 8, "regular": 25, "elite": 50}.get(league, 0)
    if team_size and specs_seed % 100 < chance:
        result[0] = {
            "kalos": "mega_evolution", "alola": "z_move", "galar": "dynamax", "paldea": "terastallization",
        }.get(region, ("mega_evolution", "z_move", "dynamax", "terastallization")[specs_seed % 4])
    return result
