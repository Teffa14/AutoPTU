from __future__ import annotations

import json
import os
import socket
import time
import traceback

import psycopg
from psycopg.types.json import Jsonb

from auto_ptu.career.battle import simulate_battle
from auto_ptu.career.models import BattleSpec


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for the Career battle worker.")
    worker_name = f"{socket.gethostname()}:{os.getpid()}"
    while True:
        worked = _process_one(database_url, worker_name)
        if not worked:
            time.sleep(1.0)


def _process_one(database_url: str, worker_name: str) -> bool:
    job = None
    queue_message_id = None
    with psycopg.connect(database_url, autocommit=False) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select * from pgmq.read('career_battle_jobs', 60, 1)")
            row = cursor.fetchone()
            if row:
                queue_columns = [description.name for description in cursor.description]
                message = dict(zip(queue_columns, row))
                body = message.get("message") or {}
                if isinstance(body, str):
                    body = json.loads(body)
                queue_message_id = message.get("msg_id")
                cursor.execute(
                    """
                    update private.battle_results
                    set status = 'running', updated_at = now()
                    where id = %s and status in ('queued', 'failed') and retry_count < 10
                    returning *
                    """,
                    (body.get("battle_result_id"),),
                )
                row = cursor.fetchone()
            if not row:
                cursor.execute("select * from private.claim_battle_job(%s)", (worker_name,))
                row = cursor.fetchone()
            if row:
                columns = [description.name for description in cursor.description]
                job = dict(zip(columns, row))
        connection.commit()
    if not job:
        return False
    try:
        raw_spec = job["spec"] if isinstance(job["spec"], dict) else json.loads(job["spec"])
        transcript = simulate_battle(BattleSpec(**raw_spec))
        with psycopg.connect(database_url) as connection:
            connection.execute(
                """
                update private.battle_results
                set status = 'complete', result = %s, transcript_sha256 = %s, updated_at = now()
                where id = %s and status = 'running'
                """,
                (Jsonb(transcript.to_dict()), transcript.sha256, job["id"]),
            )
            if queue_message_id is not None:
                connection.execute("select pgmq.delete('career_battle_jobs', %s)", (queue_message_id,))
        return True
    except Exception:
        error = traceback.format_exc(limit=8)
        with psycopg.connect(database_url) as connection:
            connection.execute(
                """
                update private.battle_results
                set status = 'failed', retry_count = retry_count + 1,
                    result = %s, updated_at = now()
                where id = %s
                """,
                (Jsonb({"error": error[-4000:]}), job["id"]),
            )
        return True


if __name__ == "__main__":
    raise SystemExit(main())
