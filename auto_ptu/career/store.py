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
        with self._lock:
            return [CareerRun.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in sorted(self.runs_dir.glob("*.json"))]

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

    def create_share(self, run: CareerRun, include_replay: bool = False) -> dict:
        share_id = uuid.uuid4().hex[:16]
        payload = {
            "share_id": share_id,
            "run_id": run.id,
            "include_replay": bool(include_replay),
            "summary": run.summary(),
        }
        self._atomic_write(self.meta_dir / f"share-{share_id}.json", payload)
        return {"share_id": share_id, "url": f"/career-game/share/{share_id}", "include_replay": bool(include_replay)}

    def load_share(self, share_id: str) -> dict:
        path = self.meta_dir / f"share-{_safe_id(share_id)}.json"
        if not path.exists():
            raise KeyError(f"Career share not found: {share_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def create_daily_run(self, run: CareerRun, challenge) -> int:
        meta_path = self.meta_dir / f"daily-{_safe_id(challenge.id)}.json"
        with self._lock:
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {"attempts": {}}
            attempts = meta.setdefault("attempts", {})
            user_attempts = int(attempts.get(run.player_id, 0)) + 1
            if user_attempts > 3:
                raise PermissionError("Daily ranked attempt limit reached.")
            attempts[run.player_id] = user_attempts
            run.attempt_no = user_attempts
            run.ranked = True
            run.daily_challenge_id = challenge.id
            self._atomic_write(meta_path, meta)
            self.save_run(run)
            return user_attempts

    def finalize_ranked(self, run: CareerRun) -> None:
        if not run.ranked or not run.daily_challenge_id:
            return
        path = self.meta_dir / f"leaderboard-{_safe_id(run.daily_challenge_id)}-{_safe_id(run.build.mode)}.json"
        with self._lock:
            rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
            rows = [entry for entry in rows if entry.get("run_id") != run.id]
            rows.append({
                "run_id": run.id,
                "user_id": run.player_id,
                "handle": run.build.name,
                "score": run.score,
                "achievements": list(run.achievements),
                "completed_at": run.updated_at,
            })
            rows.sort(key=lambda entry: (-int(entry.get("score", 0)), str(entry.get("completed_at", ""))))
            self._atomic_write(path, rows[:100])

    def leaderboard(self, challenge_id: str, mode: str, limit: int = 100) -> List[LeaderboardEntry]:
        path = self.meta_dir / f"leaderboard-{_safe_id(challenge_id)}-{_safe_id(mode)}.json"
        if not path.exists():
            return []
        rows = json.loads(path.read_text(encoding="utf-8"))[:limit]
        return [LeaderboardEntry.from_dict(entry) for entry in rows]

    @staticmethod
    def _atomic_write(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)


def _safe_id(value: str) -> str:
    return "".join(ch for ch in str(value) if ch.isalnum() or ch in {"-", "_"})
