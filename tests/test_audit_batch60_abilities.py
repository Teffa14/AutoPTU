import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, calculations


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b

    def choice(self, seq):
        return seq[0]


def _pokemon_spec(
    name,
    *,
    ability=None,
    abilities=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=10,
    defense=10,
    spatk=10,
    spdef=10,
    spd=10,
    level=20,
):
    ability_list = abilities if abilities is not None else ([ability] if ability else [])
    return PokemonSpec(
        species=name,
        level=level,
        types=types or ["Normal"],
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=moves or [],
        abilities=[{"name": entry} for entry in ability_list],
        items=[],
        movement={"overland": 4},
        weight=5,
        gender="",
    )


def _build_battle(attacker_spec, defender_spec, *, attacker_pos=(2, 2), defender_pos=(2, 3)):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="foes")
    attacker = PokemonState(
        spec=attacker_spec,
        controller_id=trainer_a.identifier,
        position=attacker_pos,
        active=True,
    )
    defender = PokemonState(
        spec=defender_spec,
        controller_id=trainer_b.identifier,
        position=defender_pos,
        active=True,
    )
    battle = BattleState(
        trainers={trainer_a.identifier: trainer_a, trainer_b.identifier: trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20] * 50)
    return battle, "a-1", "b-1"


class AuditBatch60AbilityTests(unittest.TestCase):
    def test_quick_curl_errata_readies_defense_curl_interrupt(self):
        boost = MoveSpec(
            name="Quick Curl [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        curl = MoveSpec(
            name="Defense Curl",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Curl", abilities=["Quick Curl [Errata]"], moves=[boost, curl])
        defender_spec = _pokemon_spec("Target", moves=[curl])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        battle.resolve_move_targets(attacker_id, boost, attacker_id, attacker.position)
        entries = attacker.get_temporary_effects("quick_curl_ready")
        self.assertTrue(entries)
        self.assertEqual(entries[0].get("ability"), "Quick Curl [Errata]")
        battle.resolve_move_targets(attacker_id, curl, attacker_id, attacker.position)
        self.assertFalse(attacker.get_temporary_effects("quick_curl_ready"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Quick Curl [Errata]"
                and event.get("effect") == "interrupt"
                for event in battle.log
            )
        )

    def test_quick_feet_errata_boosts_speed_and_ignores_paralysis(self):
        spec = _pokemon_spec("Swift", abilities=["Quick Feet [Errata]"], spd=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(1, 1), active=True)
        base_speed = calculations.speed_stat(mon)
        mon.statuses.append({"name": "Paralyzed"})
        boosted_speed = calculations.speed_stat(mon)
        expected = int(mon.spec.spd * calculations.stage_multiplier(2))
        self.assertEqual(boosted_speed, expected)
        mon.statuses.clear()
        self.assertEqual(calculations.speed_stat(mon), base_speed)

    def test_reckless_errata_adds_db_for_keyword_moves(self):
        move = MoveSpec(
            name="Brash Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            keywords=["Recoil"],
        )
        attacker_spec = _pokemon_spec("Reckless", abilities=["Reckless [Errata]"], moves=[move], atk=20)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        defender = battle.pokemon[defender_id]
        before_defender = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        reckless_damage = before_defender - defender.hp

        normal_spec = _pokemon_spec("Normal", moves=[move], atk=20)
        battle2, a2, d2 = _build_battle(normal_spec, defender_spec)
        battle2.rng = SequenceRNG([20] + [3] * 50)
        defender2 = battle2.pokemon[d2]
        before_defender2 = defender2.hp
        battle2.resolve_move_targets(a2, move, d2, defender2.position)
        normal_damage = before_defender2 - defender2.hp

        self.assertGreater(reckless_damage, normal_damage)
