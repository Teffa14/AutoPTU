import unittest

from auto_ptu.data_loader import default_campaign
from auto_ptu.matchmaker import AutoMatchPlanner


class CampaignLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.campaign = default_campaign()

    def test_demo_campaign_loads(self) -> None:
        self.assertEqual(self.campaign.name, "Rainy Training Grounds")
        self.assertEqual(len(self.campaign.players), 1)
        self.assertEqual(self.campaign.default_weather.lower(), "rain")

    def test_auto_planner_creates_plan(self) -> None:
        planner = AutoMatchPlanner(self.campaign, seed=42)
        plan = planner.create_plan(team_size=1)
        self.assertEqual(len(plan.matchups), 1)
        self.assertEqual(plan.weather.lower(), "rain")


if __name__ == "__main__":
    unittest.main()
