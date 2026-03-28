import unittest

from auto_ptu.data_loader import default_campaign
from auto_ptu.engine import MatchEngine
from auto_ptu.matchmaker import AutoMatchPlanner


class MatchEngineTests(unittest.TestCase):
    def test_match_engine_expectimax_runs(self) -> None:
        campaign = default_campaign()
        planner = AutoMatchPlanner(campaign, seed=7)
        plan = planner.create_plan(team_size=1)
        engine = MatchEngine(plan)
        results = engine.run(mode="expectimax", depth=2)
        self.assertTrue(results, "engine should return at least one matchup result")
        first = results[0]
        self.assertIn("best_first_move", first.payload)
        self.assertTrue(first.discord_post)


if __name__ == "__main__":
    unittest.main()
