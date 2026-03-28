import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.optimizer import (
    BuildGenome,
    EncounterModel,
    ScoreWeights,
    default_encounter_model,
    score_build_genome,
)
from auto_ptu import optimizer as optimizer_module
from auto_ptu.rules.battle_state import PokemonState


def _damaging_move(name: str, *, db: int = 8, category: str = "Physical", freq: str = "At-Will") -> MoveSpec:
    return MoveSpec(
        name=name,
        type="Normal",
        category=category,
        db=db,
        ac=2,
        range_kind="Melee" if category == "Physical" else "Ranged",
        range_value=1 if category == "Physical" else 6,
        target_kind="Melee" if category == "Physical" else "Ranged",
        target_range=1 if category == "Physical" else 6,
        freq=freq,
    )


class OptimizerTests(unittest.TestCase):
    def test_schema_round_trip(self) -> None:
        encounter = default_encounter_model("doubles")
        cloned = EncounterModel.from_dict(encounter.to_dict())
        self.assertEqual(encounter.format, cloned.format)
        self.assertEqual(len(encounter.archetypes), len(cloned.archetypes))
        self.assertAlmostEqual(encounter.weights.offense, cloned.weights.offense, places=5)

        genome = BuildGenome(
            species="Testmon",
            level=50,
            types=["Normal"],
            hp_stat=14,
            atk=16,
            defense=10,
            spatk=8,
            spdef=10,
            spd=15,
            nature="Adamant",
            ability="Guts",
            moves=[_damaging_move("Slash"), _damaging_move("Body Slam", db=7)],
        )
        payload = genome.to_dict()
        rebuilt = BuildGenome.from_dict(payload)
        self.assertEqual(genome.species, rebuilt.species)
        self.assertEqual(len(genome.moves), len(rebuilt.moves))
        self.assertEqual(genome.ability, rebuilt.ability)

    def test_aggro_weights_prefer_offense(self) -> None:
        encounter = default_encounter_model("singles")
        encounter.weights = ScoreWeights(offense=0.80, defense=0.10, tempo=0.05, consistency=0.05)

        offense = BuildGenome(
            species="OffenseMon",
            level=50,
            types=["Normal"],
            hp_stat=10,
            atk=20,
            defense=8,
            spatk=10,
            spdef=8,
            spd=18,
            moves=[_damaging_move("Crush", db=11), _damaging_move("Quick Hit", db=7)],
        )
        bulk = BuildGenome(
            species="BulkMon",
            level=50,
            types=["Normal"],
            hp_stat=20,
            atk=10,
            defense=18,
            spatk=10,
            spdef=18,
            spd=8,
            moves=[_damaging_move("Tap", db=5), _damaging_move("Chip", db=5)],
        )
        offensive_score = score_build_genome(offense, encounter)
        bulky_score = score_build_genome(bulk, encounter)
        self.assertGreater(offensive_score.total, bulky_score.total)

    def test_defense_weights_prefer_bulk(self) -> None:
        encounter = default_encounter_model("raid")
        encounter.weights = ScoreWeights(offense=0.20, defense=0.65, tempo=0.10, consistency=0.05)

        offense = BuildGenome(
            species="OffenseMon",
            level=50,
            types=["Normal"],
            hp_stat=10,
            atk=20,
            defense=8,
            spatk=10,
            spdef=8,
            spd=18,
            moves=[_damaging_move("Crush", db=11), _damaging_move("Quick Hit", db=7)],
        )
        bulk = BuildGenome(
            species="BulkMon",
            level=50,
            types=["Normal"],
            hp_stat=20,
            atk=10,
            defense=18,
            spatk=10,
            spdef=18,
            spd=8,
            moves=[_damaging_move("Tap", db=5), _damaging_move("Chip", db=5)],
        )
        offensive_score = score_build_genome(offense, encounter)
        bulky_score = score_build_genome(bulk, encounter)
        self.assertGreater(bulky_score.total, offensive_score.total)

    def test_hit_probability_respects_plus_nine_evasion_cap(self) -> None:
        attacker = PokemonState(
            spec=PokemonSpec(
                species="Attacker",
                level=50,
                types=["Normal"],
                hp_stat=10,
                atk=14,
                defense=10,
                spatk=10,
                spdef=10,
                spd=10,
                moves=[],
            ),
            controller_id="a",
        )
        defender = PokemonState(
            spec=PokemonSpec(
                species="Defender",
                level=50,
                types=["Normal"],
                hp_stat=10,
                atk=10,
                defense=100,
                spatk=10,
                spdef=100,
                spd=100,
                moves=[],
            ),
            controller_id="b",
        )
        move = _damaging_move("CapTest", db=6, category="Physical")
        p_hit = optimizer_module._hit_probability_for_policy(
            attacker,
            defender,
            move,
            "best_available",
        )
        self.assertAlmostEqual(0.50, p_hit, places=2)


if __name__ == "__main__":
    unittest.main()
