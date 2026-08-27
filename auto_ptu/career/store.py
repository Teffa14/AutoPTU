from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from ..config import RUNTIME_ROOT
from .models import BattleTranscript, CareerRun, LeaderboardEntry


def default_career_root() -> Path:
    runtime = os.environ.get("AUTO_PTU_RUNTIME_ROOT")
    base = Path(runtime) if runtime else RUNTIME_ROOT
    return base / "portable_data" / "career"


class CareerStore:
    """Small local store used in development; production implements the same contract in Postgres."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = root or default_career_root()
        self.runs_dir = self.root / "runs"
        self.battles_dir = self.root / "battles"
        self.meta_dir = self.root / "meta"
        for directory in (self.runs_dir, self.battles_dir, self.meta_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def save_run(self, run: CareerRun) -> None:
        with self._lock:
            self._atomic_write(self.runs_dir / f"{run.id}.json", run.to_dict())

    def load_run(self, run_id: str) -> CareerRun:
        path = self.runs_dir / f"{_safe_id(run_id)}.json"
        if not path.exists():
            raise KeyError(f"Career run not found: {run_id}")
        with self._lock:
            return CareerRun.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_runs(self) -> List[CareerRun]:
        """Return every readable career without letting one corrupt record poison the registry.

        Explicit ``load_run`` calls still surface corruption for the requested save. Aggregate
        consumers such as leaderboards and ranked-attempt accounting must remain available when
        an unrelated local JSON file is truncated or structurally invalid.
        """
        runs: List[CareerRun] = []
        with self._lock:
            for path in sorted(self.runs_dir.glob("*.json")):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if not isinstance(payload, dict):
                        continue
                    runs.append(CareerRun.from_dict(payload))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError):
                    continue
        return runs

    def save_battle(self, transcript: BattleTranscript) -> None:
        with self._lock:
            self._atomic_write(self.battles_dir / f"{_safe_id(transcript.battle_id)}.json", transcript.to_dict())

    def save_season_resolution(
        self,
        run: CareerRun,
        transcripts: List[BattleTranscript],
        idempotency_key: str,
        response: dict,
    ) -> None:
        with self._lock:
            for transcript in transcripts:
                self.save_battle(transcript)
            self.save_run(run)
            self.record_idempotency(run.id, idempotency_key, response)

    def load_battle(self, battle_id: str) -> dict:
        path = self.battles_dir / f"{_safe_id(battle_id)}.json"
        if not path.exists():
            raise KeyError(f"Battle transcript not found: {battle_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def record_idempotency(self, run_id: str, key: str, response: dict) -> None:
        with self._lock:
            path = self.meta_dir / f"idem-{_safe_id(run_id)}.json"
            payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            payload[str(key)] = response
            self._atomic_write(path, payload)

    def idempotent_response(self, run_id: str, key: str) -> Optional[dict]:
        path = self.meta_dir / f"idem-{_safe_id(run_id)}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8")).get(str(key))

    def attempt_count(self, challenge_id: str, player_id: str, mode: str) -> int:
        return sum(
            1 for run in self.list_runs()
            if run.daily_challenge_id == challenge_id and run.player_id == player_id and run.mode == mode
        )

    def create_daily_run(self, run: CareerRun, challenge: object) -> int:
        with self._lock:
            count = self.attempt_count(run.daily_challenge_id, run.player_id, run.mode)
            attempts = int(getattr(challenge, "attempts_per_mode", 3))
            if count >= attempts:
                raise PermissionError("All three ranked attempts for this mode are already committed.")
            run.attempt_no = count + 1
            self.save_run(run)
            return run.attempt_no

    def leaderboard(self, challenge_id: str, mode: str) -> List[LeaderboardEntry]:
        best: Dict[str, CareerRun] = {}
        for run in self.list_runs():
            if run.daily_challenge_id != challenge_id or run.mode != mode or run.status != "retired":
                continue
            current = best.get(run.player_id)
            if current is None or (run.score, -run.attempt_no, run.id) > (current.score, -current.attempt_no, current.id):
                best[run.player_id] = run
        entries = [
            LeaderboardEntry(
                challenge_id=challenge_id,
                mode=mode,
                player_id=run.player_id,
                handle=run.build.name,
                score=run.score,
                achievements=list(run.achievements),
                run_id=run.id,
                attempt_no=run.attempt_no,
                completed_at=run.updated_at,
            )
            for run in best.values()
        ]
        return sorted(entries, key=lambda entry: (-entry.score, entry.completed_at, entry.player_id))

    def create_share(self, run: CareerRun, include_replay: bool) -> dict:
        share_id = f"share-{uuid.uuid4().hex[:20]}"
        public_summary = {
            "trainer": run.build.name,
            "region": run.build.region,
            "starter": run.build.starter,
            "final_age": run.age,
            "score": run.score,
            "totals": run.totals,
            "achievements": run.achievements,
            "retirement_reason": run.retirement_reason,
        }
        payload = {
            "share_id": share_id,
            "run_id": run.id,
            "summary": public_summary,
            "timeline": run.timeline,
            "include_replay": include_replay,
            "battle_ids": [
                battle_id for entry in run.timeline if entry.get("type") == "season.completed"
                for battle_id in (entry.get("battle_ids") or [])
            ],
        }
        with self._lock:
            self._atomic_write(self.meta_dir / f"{share_id}.json", payload)
        return {"share_id": share_id, "url": f"/career-game/share/{share_id}", "published": True, "include_replay": include_replay}

    def load_share(self, share_id: str) -> dict:
        path = self.meta_dir / f"{_safe_id(share_id)}.json"
        if not path.exists():
            raise KeyError(f"Career share not found: {share_id}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {"share_id": payload["share_id"], "summary": payload["summary"], "has_replay": bool(payload["include_replay"])}

    @staticmethod
    def _atomic_write(path: Path, payload: dict) -> None:
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(path)


def _safe_id(value: str) -> str:
    safe = "".join(char for char in str(value) if char.isalnum() or char in "-_")
    if not safe:
        raise ValueError("A non-empty identifier is required.")
    return safe
