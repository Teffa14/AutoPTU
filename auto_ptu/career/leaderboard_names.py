from __future__ import annotations

from typing import Dict, List

from .models import CareerRun, LeaderboardEntry


def trainer_display_name(value: object, fallback: object = "Trainer") -> str:
    """Return a stable visible leaderboard name from persisted or legacy data."""

    def clean(candidate: object) -> str:
        if candidate is None:
            return ""
        try:
            text = str(candidate)
        except Exception:
            return ""
        text = " ".join(text.split())
        if text.casefold() in {"", "none", "null", "nan"}:
            return ""
        return text

    return clean(value) or clean(fallback) or "Trainer"


def _local_leaderboard(self, challenge_id: str, mode: str) -> List[LeaderboardEntry]:
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
            handle=trainer_display_name(getattr(run.build, "name", None)),
            score=run.score,
            achievements=list(run.achievements),
            run_id=run.id,
            attempt_no=run.attempt_no,
            completed_at=run.updated_at,
        )
        for run in best.values()
    ]
    return sorted(entries, key=lambda entry: (-entry.score, entry.completed_at, entry.player_id))


def _postgres_leaderboard(self, challenge_id: str, mode: str) -> List[LeaderboardEntry]:
    """Return the in-game trainer name, including for leaderboard rows created before this fix."""
    day = challenge_id.removeprefix("daily-")
    with self._connect() as connection:
        rows = connection.execute(
            """
            select
              coalesce(
                nullif(btrim((
                  select r.state #>> '{build,name}'
                  from private.competitive_results cr
                  join private.career_runs r on r.id = cr.run_id
                  where cr.challenge_id = e.challenge_id
                    and cr.user_id = e.owner_id
                    and cr.mode = e.mode
                    and cr.score = e.score
                  order by cr.verified_at desc
                  limit 1
                )), ''),
                nullif(btrim(e.handle), ''),
                'Trainer'
              ) as trainer_name,
              e.score,
              e.achievements,
              e.completed_at
            from public.leaderboard_entries e
            join public.daily_challenges c on c.id = e.challenge_id
            where c.challenge_date = %s and e.mode = %s
            order by e.score desc, e.completed_at, e.id
            limit 100
            """,
            (day, mode),
        ).fetchall()
    return [
        LeaderboardEntry(
            challenge_id=challenge_id,
            mode=mode,
            player_id="",
            handle=trainer_display_name(row[0]),
            score=row[1],
            achievements=list(row[2]),
            run_id="",
            attempt_no=0,
            completed_at=row[3].isoformat(),
        )
        for row in rows
    ]


def install_leaderboard_name_fix() -> None:
    # Keep the public service contract unchanged while correcting the display
    # projection in both development and production stores.
    from .store import CareerStore
    from .postgres_store import PostgresCareerStore

    CareerStore.leaderboard = _local_leaderboard
    PostgresCareerStore.leaderboard = _postgres_leaderboard
