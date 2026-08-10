from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
import uuid
from dataclasses import asdict
from typing import Dict, List, Optional

from .catalogs import REGIONS
from .models import BattleSpec, BattleTranscript, CareerRun, DailyChallenge, LeaderboardEntry


class PostgresCareerStore:
    """Authoritative production store. The browser never writes scores or run state."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or os.environ.get("DATABASE_URL", "")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required for PostgresCareerStore.")
        import psycopg

        self.psycopg = psycopg

    def save_run(self, run: CareerRun) -> None:
        challenge_date = run.daily_challenge_id.removeprefix("daily-") if run.daily_challenge_id else None
        with self.psycopg.connect(self.database_url) as connection:
            connection.execute(
                """
                insert into private.career_runs
                  (id, user_id, mode, ranked, challenge_id, seed, revision, status, state, score,
                   rules_version, content_version, scoring_version, updated_at)
                values
                  (%s, %s, %s, %s,
                   (select id from public.daily_challenges where challenge_date = %s),
                   %s, %s, %s, %s, %s, %s, %s, %s, now())
                on conflict (id) do update set
                  revision = excluded.revision, status = excluded.status, state = excluded.state,
                  score = excluded.score, updated_at = now()
                """,
                (
                    uuid.UUID(run.id), uuid.UUID(run.player_id), run.mode, run.ranked, challenge_date,
                    run.seed, run.revision, run.status, self.psycopg.types.json.Jsonb(run.to_dict()), run.score,
                    run.versions.rules, run.versions.career, run.versions.scoring,
                ),
            )

    def create_daily_run(self, run: CareerRun, challenge: DailyChallenge) -> int:
        region = REGIONS[challenge.region]
        with self.psycopg.connect(self.database_url, autocommit=False) as connection:
            challenge_id = connection.execute(
                """
                insert into public.daily_challenges
                  (challenge_date, region, seed, catalog, rules_version, content_version, scoring_version)
                values (%s, %s, %s, %s, %s, %s, %s)
                on conflict (challenge_date) do update set challenge_date = excluded.challenge_date
                returning id
                """,
                (
                    challenge.date, challenge.region, challenge.seed,
                    self.psycopg.types.json.Jsonb({"underdogs": list(region.underdogs), "clubs": list(region.clubs)}),
                    challenge.rules_version, challenge.content_version, run.versions.scoring,
                ),
            ).fetchone()[0]
            connection.execute(
                """
                insert into private.career_runs
                  (id, user_id, mode, ranked, challenge_id, seed, revision, status, state, score,
                   rules_version, content_version, scoring_version)
                values (%s, %s, %s, true, %s, %s, 0, 'active', %s, 0, %s, %s, %s)
                """,
                (
                    uuid.UUID(run.id), uuid.UUID(run.player_id), run.mode, challenge_id, run.seed,
                    self.psycopg.types.json.Jsonb(run.to_dict()), run.versions.rules,
                    run.versions.career, run.versions.scoring,
                ),
            )
            attempt = connection.execute(
                "select private.reserve_daily_attempt(%s, %s, %s, %s)",
                (challenge_id, uuid.UUID(run.player_id), run.mode, uuid.UUID(run.id)),
            ).fetchone()[0]
            run.attempt_no = int(attempt)
            connection.execute(
                "update private.career_runs set state = %s where id = %s",
                (self.psycopg.types.json.Jsonb(run.to_dict()), uuid.UUID(run.id)),
            )
            connection.commit()
        return run.attempt_no

    def load_run(self, run_id: str) -> CareerRun:
        with self.psycopg.connect(self.database_url) as connection:
            row = connection.execute("select state from private.career_runs where id = %s", (uuid.UUID(run_id),)).fetchone()
        if not row:
            raise KeyError(f"Career run not found: {run_id}")
        return CareerRun.from_dict(row[0])

    def save_battle(self, transcript: BattleTranscript) -> None:
        run_id = transcript.battle_id.split("-s", 1)[0]
        with self.psycopg.connect(self.database_url) as connection:
            connection.execute(
                """
                insert into private.battle_results
                  (run_id, battle_key, spec, result, transcript_sha256, rules_version, status, updated_at)
                values (%s, %s, %s, %s, %s, %s, 'complete', now())
                on conflict (run_id, battle_key) do update set
                  result = excluded.result, transcript_sha256 = excluded.transcript_sha256,
                  status = 'complete', updated_at = now()
                """,
                (
                    uuid.UUID(run_id), transcript.battle_id,
                    self.psycopg.types.json.Jsonb(asdict(transcript.spec)),
                    self.psycopg.types.json.Jsonb(transcript.to_dict()), transcript.sha256,
                    transcript.engine_version,
                ),
            )

    def run_battle(self, spec: BattleSpec, timeout_seconds: float = 90.0) -> BattleTranscript:
        """Enqueue a battle in PGMQ and wait for an isolated worker's authoritative result."""
        run_id = spec.id.split("-s", 1)[0]
        with self.psycopg.connect(self.database_url, autocommit=False) as connection:
            row = connection.execute(
                """
                insert into private.battle_results
                  (run_id, battle_key, spec, rules_version, status)
                values (%s, %s, %s, 'ptu-1.05-autoptu', 'queued')
                on conflict (run_id, battle_key) do update set battle_key = excluded.battle_key
                returning id, status, result
                """,
                (uuid.UUID(run_id), spec.id, self.psycopg.types.json.Jsonb(asdict(spec))),
            ).fetchone()
            if row[1] == "complete" and row[2]:
                connection.commit()
                return BattleTranscript.from_dict(row[2])
            connection.execute(
                "select pgmq.send('career_battle_jobs', %s)",
                (self.psycopg.types.json.Jsonb({"battle_result_id": str(row[0])}),),
            )
            connection.commit()
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            with self.psycopg.connect(self.database_url) as connection:
                current = connection.execute(
                    "select status, result from private.battle_results where id = %s", (row[0],)
                ).fetchone()
            if current and current[0] == "complete" and current[1]:
                return BattleTranscript.from_dict(current[1])
            if current and current[0] == "failed":
                time.sleep(0.5)
            else:
                time.sleep(0.25)
        raise RuntimeError(f"Battle worker timed out for {spec.id}; the durable job remains queued.")

    def load_battle(self, battle_id: str) -> dict:
        with self.psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                "select result from private.battle_results where battle_key = %s and status = 'complete'",
                (battle_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Battle transcript not found: {battle_id}")
        return row[0]

    def record_idempotency(self, run_id: str, key: str, response: dict) -> None:
        revision = int(response.get("run", {}).get("revision", 0))
        with self.psycopg.connect(self.database_url) as connection:
            connection.execute(
                """
                insert into private.run_commands
                  (run_id, idempotency_key, expected_revision, command_type, payload, response)
                values (%s, %s, %s, 'season.advance', '{}'::jsonb, %s)
                on conflict (run_id, idempotency_key) do nothing
                """,
                (uuid.UUID(run_id), key, max(0, revision - 1), self.psycopg.types.json.Jsonb(response)),
            )

    def idempotent_response(self, run_id: str, key: str) -> Optional[dict]:
        with self.psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                "select response from private.run_commands where run_id = %s and idempotency_key = %s",
                (uuid.UUID(run_id), key),
            ).fetchone()
        return row[0] if row else None

    def attempt_count(self, challenge_id: str, player_id: str, mode: str) -> int:
        challenge_date = challenge_id.removeprefix("daily-")
        with self.psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                """
                select count(*) from private.daily_attempts a
                join public.daily_challenges c on c.id = a.challenge_id
                where c.challenge_date = %s and a.user_id = %s and a.mode = %s
                """,
                (challenge_date, uuid.UUID(player_id), mode),
            ).fetchone()
        return int(row[0])

    def leaderboard(self, challenge_id: str, mode: str) -> List[LeaderboardEntry]:
        day = challenge_id.removeprefix("daily-")
        with self.psycopg.connect(self.database_url) as connection:
            rows = connection.execute(
                """
                select e.handle, e.score, e.achievements, e.completed_at
                from public.leaderboard_entries e
                join public.daily_challenges c on c.id = e.challenge_id
                where c.challenge_date = %s and e.mode = %s
                order by e.score desc, e.completed_at, e.id limit 100
                """,
                (day, mode),
            ).fetchall()
        return [
            LeaderboardEntry(challenge_id=challenge_id, mode=mode, player_id="", handle=row[0], score=row[1],
                             achievements=list(row[2]), run_id="", attempt_no=0, completed_at=row[3].isoformat())
            for row in rows
        ]

    def finalize_ranked(self, run: CareerRun) -> None:
        if not run.ranked or run.status != "retired":
            return
        with self.psycopg.connect(self.database_url, autocommit=False) as connection:
            challenge_id = connection.execute(
                "select challenge_id from private.career_runs where id = %s", (uuid.UUID(run.id),)
            ).fetchone()[0]
            hashes = [row[0] for row in connection.execute(
                "select transcript_sha256 from private.battle_results where run_id = %s order by battle_key",
                (uuid.UUID(run.id),),
            ).fetchall()]
            root = hashlib.sha256(json.dumps(hashes, separators=(",", ":")).encode("utf-8")).hexdigest()
            achievements = self.psycopg.types.json.Jsonb(run.achievements)
            connection.execute(
                """
                insert into private.competitive_results
                  (run_id, challenge_id, user_id, mode, attempt_no, score, achievements, transcript_root_sha256)
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (run_id) do nothing
                """,
                (uuid.UUID(run.id), challenge_id, uuid.UUID(run.player_id), run.mode, run.attempt_no, run.score, achievements, root),
            )
            handle_row = connection.execute("select handle from public.profiles where id = %s", (uuid.UUID(run.player_id),)).fetchone()
            handle = handle_row[0] if handle_row else f"Trainer-{run.player_id[:8]}"
            connection.execute(
                """
                insert into public.leaderboard_entries
                  (owner_id, challenge_id, mode, handle, score, achievements, completed_at)
                values (%s, %s, %s, %s, %s, %s, now())
                on conflict (challenge_id, owner_id, mode) do update set
                  handle = excluded.handle, score = excluded.score, achievements = excluded.achievements,
                  completed_at = excluded.completed_at
                where excluded.score > public.leaderboard_entries.score
                """,
                (uuid.UUID(run.player_id), challenge_id, run.mode, handle, run.score, achievements),
            )
            connection.commit()

    def create_share(self, run: CareerRun, include_replay: bool) -> dict:
        share_id = f"share-{run.id[:16]}"
        replay_path = self._upload_shared_replay(run, share_id) if include_replay else None
        summary = {
            "trainer": run.build.name,
            "region": run.build.region,
            "starter": run.build.starter,
            "final_age": run.age,
            "score": run.score,
            "achievements": run.achievements,
            "totals": run.totals,
            "retirement_reason": run.retirement_reason,
        }
        with self.psycopg.connect(self.database_url) as connection:
            connection.execute(
                """
                insert into public.career_shares (share_slug, owner_id, summary, replay_path)
                values (%s, %s, %s, %s)
                on conflict (share_slug) do update set
                  summary = excluded.summary, replay_path = excluded.replay_path, revoked_at = null
                """,
                (share_id, uuid.UUID(run.player_id), self.psycopg.types.json.Jsonb(summary), replay_path),
            )
        return {
            "share_id": share_id,
            "url": f"/career-game/share/{share_id}",
            "published": True,
            "include_replay": bool(replay_path),
        }

    def _upload_shared_replay(self, run: CareerRun, share_id: str) -> str:
        supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not supabase_url or not service_key:
            raise RuntimeError("Replay sharing requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the backend.")
        with self.psycopg.connect(self.database_url) as connection:
            rows = connection.execute(
                "select battle_key, result from private.battle_results where run_id = %s and status = 'complete' order by battle_key",
                (uuid.UUID(run.id),),
            ).fetchall()
        payload = json.dumps(
            {"run_id": run.id, "timeline": run.timeline, "battles": [{"id": row[0], "transcript": row[1]} for row in rows]},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        path = f"{share_id}/replay.json"
        request = urllib.request.Request(
            f"{supabase_url}/storage/v1/object/career-shares/{path}",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "Content-Type": "application/json",
                "x-upsert": "true",
            },
        )
        with urllib.request.urlopen(request, timeout=30):
            pass
        return path

    def load_share(self, share_id: str) -> dict:
        with self.psycopg.connect(self.database_url) as connection:
            row = connection.execute(
                "select share_slug, summary, replay_path from public.career_shares where share_slug = %s and revoked_at is null",
                (share_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Career share not found: {share_id}")
        return {"share_id": row[0], "summary": row[1], "has_replay": bool(row[2])}


def career_store_from_environment():
    if os.environ.get("DATABASE_URL", "").strip():
        return PostgresCareerStore()
    from .store import CareerStore

    return CareerStore()
