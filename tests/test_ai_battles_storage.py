import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from auto_ptu.ai_battles import BattleResult, _persist_results, run_ai_battles


class AIBatchStorageTests(unittest.TestCase):
    def test_persist_results_writes_summary_and_jsonl(self) -> None:
        results = [
            BattleResult(
                seed=8,
                team_size=2,
                min_level=20,
                max_level=30,
                turns=14,
                ok=True,
                winner="players",
                summary={"moves": {"Tackle": 4}},
                roster={"player": ["Pikachu"], "foe": ["Bulbasaur"]},
            ),
            BattleResult(
                seed=3,
                team_size=2,
                min_level=20,
                max_level=30,
                turns=22,
                ok=False,
                winner="unfinished",
                error="turn limit 22 exceeded",
                summary={"moves": {"Struggle": 8}},
                roster={"player": ["Charmander"], "foe": ["Squirtle"]},
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _persist_results(
                results,
                root_dir=Path(tmp),
                include_full_log=False,
                metadata={"randomize": False},
            )
            self.assertTrue(run_dir.exists())
            results_path = run_dir / "results.jsonl"
            summary_path = run_dir / "summary.json"
            self.assertTrue(results_path.exists())
            self.assertTrue(summary_path.exists())

            lines = [line for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(2, len(lines))
            first_record = json.loads(lines[0])
            second_record = json.loads(lines[1])
            self.assertEqual(3, first_record["seed"])
            self.assertEqual(8, second_record["seed"])
            self.assertNotIn("log", first_record)

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(2, summary["totals"]["battles"])
            self.assertEqual(1, summary["totals"]["failed"])
            self.assertEqual({"randomize": False}, summary["metadata"])

    def test_persist_results_can_include_full_log(self) -> None:
        result = BattleResult(
            seed=1,
            team_size=1,
            min_level=10,
            max_level=10,
            turns=3,
            ok=True,
            winner="players",
            summary={"moves": {"Quick Attack": 1}},
            roster={"player": ["Eevee"], "foe": ["Rattata"]},
            log=[{"type": "move", "move": "Quick Attack"}],
        )
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = _persist_results(
                [result],
                root_dir=Path(tmp),
                include_full_log=True,
                metadata={},
            )
            payload = (run_dir / "results.jsonl").read_text(encoding="utf-8").strip()
            record = json.loads(payload)
            self.assertIn("log", record)
            self.assertEqual("Quick Attack", record["log"][0]["move"])

    def test_windows_parallel_is_clamped_to_safe_limit(self) -> None:
        captured: dict[str, int] = {}

        class DummyPool:
            def __init__(self, *, processes: int) -> None:
                captured["processes"] = processes

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def imap_unordered(self, _func, jobs):
                for job in jobs:
                    yield BattleResult(
                        seed=job.seed,
                        team_size=job.team_size,
                        min_level=job.min_level,
                        max_level=job.max_level,
                        turns=1,
                        ok=True,
                        winner="players",
                        summary={"moves": {}},
                        roster={"player": ["A"], "foe": ["B"]},
                    )

        with mock.patch("auto_ptu.ai_battles.mp.Pool", DummyPool), mock.patch(
            "auto_ptu.ai_battles.os.name", "nt"
        ), mock.patch("auto_ptu.ai_battles.os.cpu_count", return_value=64), mock.patch(
            "auto_ptu.ai_battles._persist_results"
        ) as persist_mock:
            code = run_ai_battles(
                total=64,
                parallel=64,
                team_size=1,
                min_level=10,
                max_level=10,
                store_results=False,
            )
            self.assertEqual(0, code)
            self.assertEqual(16, captured["processes"])
            persist_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
