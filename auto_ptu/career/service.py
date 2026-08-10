from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Dict, Optional

from .catalogs import REGIONS, region_catalog
from .class_adapters import compile_class_adapters
from .content_compiler import validate_compiled_content
from .engine import CareerEngine
from .models import CareerRun
from .postgres_store import career_store_from_environment
from .store import CareerStore


class CareerService:
    def __init__(self, store: Optional[CareerStore] = None, engine: Optional[CareerEngine] = None) -> None:
        self.store = store or career_store_from_environment()
        battle_runner = getattr(self.store, "run_battle", None)
        if engine is not None:
            self.engine = engine
        elif battle_runner is not None:
            self.engine = CareerEngine(battle_runner=battle_runner)
        else:
            self.engine = CareerEngine()

    def catalog(self, locale: str = "es") -> dict:
        adapters = compile_class_adapters()
        content = validate_compiled_content()
        return {
            "version": "career-0.1.0",
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
        starter = str(payload.get("starter") or REGIONS[challenge.region].underdogs[0])
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
        run.seed = challenge.seed + attempt_no * 1009
        run.season = self.engine._open_season(run)
        self.store.save_run(run)
        return {"challenge": asdict(challenge), "run": run.to_dict(), "attempt_no": attempt_no}

    def get_run(self, player_id: str, run_id: str) -> dict:
        run = self._owned_run(player_id, run_id)
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
        run, transcripts = self.engine.advance_season(run, option_id=str(payload.get("option_id") or ""))
        for transcript in transcripts:
            self.store.save_battle(transcript)
        self.store.save_run(run)
        if run.status == "retired" and hasattr(self.store, "finalize_ranked"):
            self.store.finalize_ranked(run)
        response = {"run": run.to_dict(), "battle_ids": [entry.battle_id for entry in transcripts]}
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
        self._owned_run(player_id, run_id)
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
        return self.store.create_share(run, bool(payload.get("include_replay")))

    def public_share(self, share_id: str) -> dict:
        return self.store.load_share(share_id)

    def _owned_run(self, player_id: str, run_id: str) -> CareerRun:
        run = self.store.load_run(run_id)
        if run.player_id != player_id:
            raise PermissionError("Career run belongs to another account.")
        return run
