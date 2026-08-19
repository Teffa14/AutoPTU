from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Dict

from .service import CareerService
from .trainer_sprites import apply_trainer_sprite, trainer_sprite_catalog


class AdvancedCareerService(CareerService):
    """Career presentation extensions that do not alter competitive mechanics."""

    def catalog(self, locale: str = "es") -> dict:
        payload = super().catalog(locale)
        payload["trainer_sprites"] = trainer_sprite_catalog()
        return payload

    def create_run(self, player_id: str, payload: Dict[str, object]) -> dict:
        created = super().create_run(player_id, payload)
        run = self.store.load_run(str(created["id"]))
        apply_trainer_sprite(run, payload.get("trainer_sprite"))
        self.store.save_run(run)
        return run.to_dict()

    def create_daily_attempt(self, player_id: str, payload: Dict[str, object], day: date) -> dict:
        result = super().create_daily_attempt(player_id, payload, day)
        run_id = str(result["run"]["id"])
        run = self.store.load_run(run_id)
        apply_trainer_sprite(run, payload.get("trainer_sprite"))
        self.store.save_run(run)
        result["run"] = run.to_dict()
        return result

    def leaderboard(self, day: date, mode: str) -> dict:
        challenge = self.engine.daily_challenge(day)
        if hasattr(self.store, "_connect"):
            return self._postgres_leaderboard(day, challenge, mode)
        entries = self.store.leaderboard(challenge.id, mode)
        rows = []
        for index, entry in enumerate(entries):
            trainer_name = entry.handle
            if entry.run_id:
                try:
                    trainer_name = self.store.load_run(entry.run_id).build.name
                except (KeyError, ValueError):
                    pass
            rows.append(
                {
                    "rank": index + 1,
                    "handle": trainer_name,
                    "trainer_name": trainer_name,
                    "score": entry.score,
                    "achievements": entry.achievements,
                    "completed_at": entry.completed_at,
                }
            )
        return {"challenge": asdict(challenge), "mode": mode, "entries": rows}

    def _postgres_leaderboard(self, day: date, challenge, mode: str) -> dict:
        with self.store._connect() as connection:
            rows = connection.execute(
                """
                select
                  coalesce(best.state #>> '{build,name}', e.handle) as trainer_name,
                  e.score,
                  e.achievements,
                  e.completed_at
                from public.leaderboard_entries e
                join public.daily_challenges c on c.id = e.challenge_id
                left join lateral (
                  select cr.state
                  from private.competitive_results r
                  join private.career_runs cr on cr.id = r.run_id
                  where r.challenge_id = e.challenge_id
                    and r.user_id = e.owner_id
                    and r.mode = e.mode
                    and r.score = e.score
                  order by r.verified_at asc
                  limit 1
                ) best on true
                where c.challenge_date = %s and e.mode = %s
                order by e.score desc, e.completed_at, e.id
                limit 100
                """,
                (day.isoformat(), mode),
            ).fetchall()
        entries = [
            {
                "rank": index + 1,
                "handle": str(row[0]),
                "trainer_name": str(row[0]),
                "score": int(row[1]),
                "achievements": list(row[2]),
                "completed_at": row[3].isoformat(),
            }
            for index, row in enumerate(rows)
        ]
        return {"challenge": asdict(challenge), "mode": mode, "entries": entries}
