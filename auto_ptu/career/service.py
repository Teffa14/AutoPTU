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
from .items import buy_product, complete_training, item_catalog, shop_catalog, training_catalog, use_item
from .models import CURRENT_CAREER_VERSION, BattleTranscript, CareerRun, utc_now
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
            "items": item_catalog(),
            "shop": shop_catalog(),
            "training_methods": training_catalog(),
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

    def use_item(self, player_id: str, run_id: str, payload: Dict[str, object]) -> dict:
        run = self._owned_run(player_id, run_id)
        expected = int(payload.get("expected_revision", -1))
        if expected != run.revision:
            raise RuntimeError(f"Revision conflict: expected {expected}, current {run.revision}.")
        use_item(
            run,
            str(payload.get("item") or ""),
            pokemon_id=str(payload.get("pokemon_id") or ""),
            stat=str(payload.get("stat") or ""),
        )
        run.revision += 1
        run.updated_at = utc_now()
        self.store.save_run(run)
        return run.to_dict()

    def train(self, player_id: str, run_id: str, payload: Dict[str, object]) -> dict:
        run = self._owned_run(player_id, run_id)
        expected = int(payload.get("expected_revision", -1))
        if expected != run.revision:
            raise RuntimeError(f"Revision conflict: expected {expected}, current {run.revision}.")
        complete_training(
            run,
            str(payload.get("method") or ""),
            str(payload.get("pokemon_id") or ""),
        )
        run.revision += 1
        run.updated_at = utc_now()
        self.store.save_run(run)
        return run.to_dict()

    def purchase(self, player_id: str, run_id: str, payload: Dict[str, object]) -> dict:
        run = self._owned_run(player_id, run_id)
        expected = int(payload.get("expected_revision", -1))
        if expected != run.revision:
            raise RuntimeError(f"Revision conflict: expected {expected}, current {run.revision}.")
        buy_product(run, str(payload.get("product_id") or ""))
        run.revision += 1
        run.updated_at = utc_now()
        self.store.save_run(run)
        return run.to_dict()

    def decide(self, player_id: str, run_id: str, payload: Dict[str, object], idempotency_key: str) -> dict:
        if not idempotency_key:
            raise ValueError("An idempotency key is required.")
        if hasattr(self.store, "load_command_context"):
            cached, run = self.store.load_command_context(run_id, idempotency_key)
        else:
            cached = self.store.idempotent_response(run_id, idempotency_key)
            run = None
        if cached is not None:
            return cached
        run = self._validate_owned_run(player_id, run) if run is not None else self._owned_run(player_id, run_id)
        expected = int(payload.get("expected_revision", -1))
        if expected != run.revision:
            raise RuntimeError(f"Revision conflict: expected {expected}, current {run.revision}.")
        run, specs = self.engine.prepare_season(run, option_id=str(payload.get("option_id") or ""))
        battle_ids = [entry.id for entry in specs]
        featured = None
        if specs:
            # Only the broadcast match blocks the transition into the arena.
            # Calendar summaries, progression, salary and the next season are
            # finalized while the player watches the replay.
            featured_spec = next((entry for entry in specs if entry.featured), specs[-1])
            try:
                started_at = time.perf_counter()
                featured = self.engine.battle_runner(featured_spec)
                self.store.save_battle(featured)
                LOGGER.info(
                    "career featured battle ready run=%s season=%s seconds=%.3f",
                    run.id,
                    run.season_number,
                    time.perf_counter() - started_at,
                )
            except Exception:
                LOGGER.exception("career featured battle generation failed run=%s", run.id)
            self.store.save_run(run)
        else:
            self.store.save_run(run)
        response = {"run": run.to_dict(), "battle_ids": battle_ids, "season_resolved": False}
        if featured is not None:
            response["featured_battle"] = featured.to_dict()
            response["featured_battle_id"] = featured.battle_id
        self.store.record_idempotency(run_id, idempotency_key, response)
        return response

    def finalize_season(self, player_id: str, run_id: str, battle_id: str) -> dict:
        run = self._owned_run(player_id, run_id)
        if run.season is None or run.season.status != "battle":
            return run.to_dict()
        specs = list(run.season.battles)
        if not any(entry.id == battle_id for entry in specs):
            raise PermissionError("Battle does not belong to the prepared career calendar.")
        started_at = time.perf_counter()
        existing: Dict[str, dict] = {}
        for spec in specs:
            try:
                existing[spec.id] = self.store.load_battle(spec.id)
            except KeyError:
                pass
        generated: list[BattleTranscript] = []
        featured_spec = next((entry for entry in specs if entry.featured), specs[-1])
        if featured_spec.id not in existing:
            featured = self.engine.battle_runner(featured_spec)
            self.store.save_battle(featured)
            generated.append(featured)
        missing_summaries = [
            entry for entry in specs
            if entry.id != featured_spec.id and entry.id not in existing
        ]
        for summary in simulate_calendar_summaries(missing_summaries):
            self.store.save_battle(summary)
            generated.append(summary)
        generated_by_id = {entry.battle_id: entry for entry in generated}
        transcripts = [
            BattleTranscript.from_dict(existing[spec.id]) if spec.id in existing
            else generated_by_id[spec.id]
            for spec in specs
        ]
        resolved_season = run.season_number
        run, _ = self.engine.resolve_prepared_season(run, transcripts)
        self.store.save_run(run)
        if run.status == "retired" and hasattr(self.store, "finalize_ranked"):
            self.store.finalize_ranked(run)
        LOGGER.info(
            "career season finalized run=%s season=%s seconds=%.3f",
            run.id,
            resolved_season,
            time.perf_counter() - started_at,
        )
        return run.to_dict()

    def retire(self, player_id: str, run_id: str, payload: Dict[str, object]) -> dict:
        run = self._owned_run(player_id, run_id)
        self.engine.retire(run, str(payload.get("reason") or "voluntary"))
        self.store.save_run(run)
        if hasattr(self.store, "finalize_ranked"):
            self.store.finalize_ranked(run)
        return run.to_dict()

    def battle(self, player_id: str, run_id: str, battle_id: str) -> dict:
        if hasattr(self.store, "load_owned_battle"):
            try:
                return self.store.load_owned_battle(player_id, run_id, battle_id)
            except KeyError:
                pass
        run = self._owned_run(player_id, run_id)
        if run.season is not None and run.season.status == "battle":
            specs = list(run.season.battles)
            requested = next((entry for entry in specs if entry.id == battle_id), None)
            if requested is None:
                raise PermissionError("Battle does not belong to the prepared career calendar.")
            if requested.featured:
                generated = self.engine.battle_runner(requested)
            else:
                generated = simulate_calendar_summaries([requested])[0]
            self.store.save_battle(generated)
            return generated.to_dict()
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
        return self._validate_owned_run(player_id, self.store.load_run(run_id))

    def _validate_owned_run(self, player_id: str, run: CareerRun) -> CareerRun:
        if run.player_id != player_id:
            raise PermissionError("Career run belongs to another account.")
        if self.engine.ensure_roster(run):
            run.revision += 1
            self.store.save_run(run)
        return run
