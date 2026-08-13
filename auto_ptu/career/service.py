from __future__ import annotations

import os
import logging
import time
from dataclasses import asdict
from datetime import date
from typing import Dict, Optional

from .catalogs import REGIONS, region_catalog
from .class_adapters import compile_class_adapters
from .battle import simulate_calendar_summaries
from .content_compiler import validate_compiled_content
from .engine import CareerEngine
from .models import CURRENT_CAREER_VERSION, BattleTranscript, CareerRun
from .postgres_store import career_store_from_environment
from .store import CareerStore


LOGGER = logging.getLogger("autoptu.career")


class CareerService:
    def __init__(self, store: Optional[CareerStore] = None, engine: Optional[CareerEngine] = None) -> None:
        self.store = store or career_store_from_environment()
        battle_runner = getattr(self.store, "run_battle", None)
        if engine is not None:
            self.engine = engine
        elif battle_runner is not None and os.environ.get("CAREER_BATTLE_EXECUTION", "inline").lower() == "queue":
            self.engine = CareerEngine(battle_runner=battle_runner)
        else:
            self.engine = CareerEngine()

    def catalog(self, locale: str = "es") -> dict:
        adapters = compile_class_adapters()
        content = validate_compiled_content()
        return {
            "version": CURRENT_CAREER_VERSION,
            "locale": "es" if str(locale).lower().startswith("es") else "en",
            "regions": region_catalog(),
            "classes": adapters["classes"],
            "class_count": adapters["class_count"],
            "feature_count": adapters["feature_count"],
            "decision_family_count": content["family_count"],
            "decision_signature_count": content["node_count"],
            "decision_content_sha256": content["sha256"],
            "modes": [
                {"id": "simple", "target_minutes": "15–20", "decisions_per_season": 1},
                {"id": "advanced", "target_minutes": "30–45", "decisions_per_season": 3},
            ],
        }

    def create_run(self, player_id: str, payload: Dict[str, object]) -> dict:
        run = self.engine.new_run(
            player_id=player_id,
            name=str(payload.get("name") or ""),
            region=str(payload.get("region") or "kanto"),
            starter=str(payload.get("starter") or "Rattata"),
            classes=[str(value) for value in payload.get("classes") or []],
            mode=str(payload.get("mode") or "simple"),
            locale=str(payload.get("locale") or "es"),
            seed=int(payload["seed"]) if payload.get("seed") not in (None, "") else None,
        )
        self.store.save_run(run)
        return run.to_dict()

    def create_daily_attempt(self, player_id: str, payload: Dict[str, object], day: date) -> dict:
        challenge = self.engine.daily_challenge(day)
        mode = str(payload.get("mode") or "simple").lower()
        starter = str(payload.get("starter") or REGIONS[challenge.region].partner_choices[0])
        run = self.engine.new_run(
            player_id=player_id,
            name=str(payload.get("name") or "Ranked Trainer"),
            region=challenge.region,
            starter=starter,
            classes=[str(value) for value in payload.get("classes") or []],
            mode=mode,
            locale=str(payload.get("locale") or "es"),
            seed=challenge.seed,
            ranked=True,
            daily_challenge_id=challenge.id,
            attempt_no=0,
        )
        attempt_no = self.store.create_daily_run(run, challenge)
        # Every ranked attempt receives the exact committed world. The player may
        # change build choices, but schedule, decisions, rolls and rival AI remain
        # tied to the published daily seed.
        run.seed = challenge.seed
        self.store.save_run(run)
        return {"challenge": asdict(challenge), "run": run.to_dict(), "attempt_no": attempt_no}

    def get_run(self, player_id: str, run_id: str) -> dict:
        run = self._owned_run(player_id, run_id)
        return run.to_dict()

    def lineup(self, player_id: str, run_id: str, payload: Dict[str, object]) -> dict:
        run = self._owned_run(player_id, run_id)
        expected = int(payload.get("expected_revision", -1))
        if expected != run.revision:
            raise RuntimeError(f"Revision conflict: expected {expected}, current {run.revision}.")
        pokemon_ids = payload.get("pokemon_ids") or []
        if not isinstance(pokemon_ids, list):
            raise ValueError("pokemon_ids must be a list.")
        self.engine.update_lineup(run, [str(value) for value in pokemon_ids])
        self.store.save_run(run)
        return run.to_dict()

    def decide(self, player_id: str, run_id: str, payload: Dict[str, object], idempotency_key: str) -> dict:
        if not idempotency_key:
            raise ValueError("An idempotency key is required.")
        cached = self.store.idempotent_response(run_id, idempotency_key)
        if cached is not None:
            return cached
        run = self._owned_run(player_id, run_id)
        expected = int(payload.get("expected_revision", -1))
        if expected != run.revision:
            raise RuntimeError(f"Revision conflict: expected {expected}, current {run.revision}.")
        run, specs = self.engine.prepare_season(run, option_id=str(payload.get("option_id") or ""))
        battle_ids = [entry.id for entry in specs]
        season_resolved = False
        season_transcripts = []
        persisted_atomically = False
        prepared_run = CareerRun.from_dict(run.to_dict())
        if specs:
            # The client has already switched to the stadium transition. Resolve
            # the immutable calendar during that transition so /battle only has
            # to fetch a cached transcript instead of starting a cold PTU engine.
            try:
                started_at = time.perf_counter()
                featured_spec = next((entry for entry in specs if entry.featured), specs[-1])
                featured = self.engine.battle_runner(featured_spec)
                featured_seconds = time.perf_counter() - started_at
                summaries = simulate_calendar_summaries([entry for entry in specs if entry.id != featured_spec.id])
                summaries_seconds = time.perf_counter() - started_at - featured_seconds
                season_transcripts = [*summaries, featured]
                run, _ = self.engine.resolve_prepared_season(run, season_transcripts)
                season_resolved = True
                LOGGER.info(
                    "career calendar ready run=%s season=%s featured=%.3fs summaries=%.3fs total=%.3fs",
                    run.id,
                    max(1, run.season_number - 1),
                    featured_seconds,
                    summaries_seconds,
                    time.perf_counter() - started_at,
                )
            except Exception:
                LOGGER.exception("career eager battle generation failed run=%s", run.id)
                # A prepared season is recoverable: /battle retains the same
                # deterministic fallback if eager generation ever fails.
                run = prepared_run
                self.store.save_run(run)
        response = {"run": run.to_dict(), "battle_ids": battle_ids, "season_resolved": season_resolved}
        if season_resolved and hasattr(self.store, "save_season_resolution"):
            self.store.save_season_resolution(run, season_transcripts, idempotency_key, response)
            persisted_atomically = True
        elif not specs:
            self.store.save_run(run)
        if not persisted_atomically:
            self.store.record_idempotency(run_id, idempotency_key, response)
        return response

    def retire(self, player_id: str, run_id: str, payload: Dict[str, object]) -> dict:
        run = self._owned_run(player_id, run_id)
        self.engine.retire(run, str(payload.get("reason") or "voluntary"))
        self.store.save_run(run)
        if hasattr(self.store, "finalize_ranked"):
            self.store.finalize_ranked(run)
        return run.to_dict()

    def battle(self, player_id: str, run_id: str, battle_id: str) -> dict:
        run = self._owned_run(player_id, run_id)
        if run.season is not None and run.season.status == "battle":
            specs = list(run.season.battles)
            requested = next((entry for entry in specs if entry.id == battle_id), None)
            if requested is None:
                raise PermissionError("Battle does not belong to the prepared career calendar.")
            existing: Dict[str, dict] = {}
            for spec in specs:
                try:
                    existing[spec.id] = self.store.load_battle(spec.id)
                except KeyError:
                    pass
            generated = []
            if battle_id not in existing:
                featured = self.engine.battle_runner(requested)
                self.store.save_battle(featured)
                generated.append(featured)
            missing_summaries = [entry for entry in specs if entry.id != battle_id and entry.id not in existing]
            for summary in simulate_calendar_summaries(missing_summaries):
                self.store.save_battle(summary)
                generated.append(summary)
            transcripts = [
                BattleTranscript.from_dict(existing[spec.id]) if spec.id in existing
                else next(entry for entry in generated if entry.battle_id == spec.id)
                for spec in specs
            ]
            run, _ = self.engine.resolve_prepared_season(run, transcripts)
            self.store.save_run(run)
            if run.status == "retired" and hasattr(self.store, "finalize_ranked"):
                self.store.finalize_ranked(run)
        transcript = self.store.load_battle(battle_id)
        if str(transcript.get("spec", {}).get("id") or "") != battle_id or not battle_id.startswith(f"{run_id}-"):
            raise PermissionError("Battle does not belong to this career.")
        return transcript

    def daily(self, day: date) -> dict:
        return asdict(self.engine.daily_challenge(day))

    def leaderboard(self, day: date, mode: str) -> dict:
        challenge = self.engine.daily_challenge(day)
        entries = self.store.leaderboard(challenge.id, mode)
        return {
            "challenge": asdict(challenge),
            "mode": mode,
            "entries": [
                {
                    "rank": index + 1,
                    "handle": entry.handle,
                    "score": entry.score,
                    "achievements": entry.achievements,
                    "completed_at": entry.completed_at,
                }
                for index, entry in enumerate(entries)
            ],
        }

    def share(self, player_id: str, run_id: str, payload: Dict[str, object]) -> dict:
        run = self._owned_run(player_id, run_id)
        if run.status != "retired":
            raise ValueError("Only a retired career can be shared.")
        return self.store.create_share(run, False)

    def public_share(self, share_id: str) -> dict:
        return self.store.load_share(share_id)

    def _owned_run(self, player_id: str, run_id: str) -> CareerRun:
        run = self.store.load_run(run_id)
        if run.player_id != player_id:
            raise PermissionError("Career run belongs to another account.")
        if self.engine.ensure_roster(run):
            run.revision += 1
            self.store.save_run(run)
        return run
