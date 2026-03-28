import unittest

from auto_ptu.data_models import CampaignSpec, GridSpec, PokemonSpec
from auto_ptu.matchmaker import AutoMatchPlanner


def _pokemon(name: str) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=["Electric"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=10,
        moves=[],
    )


class AutoMatchPlannerTests(unittest.TestCase):
    def test_metadata_creates_multi_trainer_sides(self) -> None:
        campaign = CampaignSpec(
            name="Multi-Trainer Demo",
            grid=GridSpec(width=10, height=8),
            default_weather="Clear",
            players=[_pokemon("Pikachu"), _pokemon("Eevee")],
            foes=[_pokemon("Meowth"), _pokemon("Koffing")],
            metadata={
                "player_trainers": [
                    {"identifier": "ash", "name": "Ash", "controller": "player"},
                    {"identifier": "misty", "name": "Misty", "controller": "player"},
                ],
                "foe_trainers": [{"identifier": "rocket", "name": "Team Rocket", "controller": "ai"}],
            },
        )
        planner = AutoMatchPlanner(campaign, seed=5)
        plan = planner.create_plan(team_size=2)
        sides = plan.matchups[0].sides_or_default()
        player_controllers = [side for side in sides if side.controller == "player"]
        foe_controllers = [side for side in sides if side.controller != "player"]
        self.assertEqual(len(player_controllers), 2)
        self.assertEqual(len(foe_controllers), 1)
        for side in player_controllers:
            self.assertEqual(len(side.pokemon), 1, "Each trainer should control exactly one Pokémon.")

    def test_default_single_trainer_when_metadata_missing(self) -> None:
        campaign = CampaignSpec(
            name="Default Campaign",
            grid=GridSpec(width=6, height=6),
            default_weather="Clear",
            players=[_pokemon("Pikachu")],
            foes=[_pokemon("Meowth")],
            metadata={},
        )
        planner = AutoMatchPlanner(campaign, seed=1)
        plan = planner.create_plan(team_size=1)
        sides = plan.matchups[0].sides_or_default()
        self.assertEqual(len(sides), 2)
        self.assertEqual(sides[0].controller, "player")
        self.assertEqual(len(sides[0].pokemon), 1)


__all__ = ["AutoMatchPlannerTests"]
