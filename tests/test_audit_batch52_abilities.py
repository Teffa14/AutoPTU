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
    weight=5,
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
        weight=weight,
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


class AuditBatch52AbilityTests(unittest.TestCase):
    def test_inner_focus_errata_blocks_initiative_penalty(self):
        defender_spec = _pokemon_spec("Focus", abilities=["Inner Focus [Errata]"], spd=10)
        attacker_spec = _pokemon_spec("Attacker", moves=[])
        battle, _, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.add_temporary_effect(
            "initiative_penalty",
            amount=-10,
            expires_round=battle.round + 1,
            source_id="a-1",
        )
        entries = battle._build_initiative_order()
        target = next(entry for entry in entries if entry.actor_id == defender_id)
        self.assertEqual(target.total, 10)

    def test_interference_errata_penalizes_accuracy(self):
        move = MoveSpec(
            name="Interference [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Burst 3, Foes",
        )
        attacker_spec = _pokemon_spec("Interferer", abilities=["Interference [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(
            any(entry.get("amount") == 2 for entry in defender.get_temporary_effects("accuracy_penalty"))
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Interference [Errata]"
                for event in battle.log
            )
        )

    def test_intimidate_errata_once_per_target(self):
        move = MoveSpec(
            name="Intimidate [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_value=5,
            target_kind="Ranged",
            target_range=5,
            range_text="Range 5, 1 Target",
        )
        attacker_spec = _pokemon_spec("Intimidator", abilities=["Intimidate [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("atk"), -1)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(defender.combat_stages.get("atk"), -1)

    def test_lightning_kicks_errata_grants_accuracy_bonus(self):
        boost = MoveSpec(
            name="Lightning Kicks [Errata]",
            type="Electric",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        kick = MoveSpec(
            name="Low Kick",
            type="Fighting",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Kicker", abilities=["Lightning Kicks [Errata]"], moves=[boost, kick])
        defender_spec = _pokemon_spec("Target", moves=[kick])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, boost, attacker_id, battle.pokemon[attacker_id].position)
        attacker = battle.pokemon[attacker_id]
        entries = attacker.get_temporary_effects("kick_priority")
        self.assertTrue(entries)
        self.assertEqual(entries[0].get("accuracy_bonus"), 4)
        battle.resolve_move_targets(attacker_id, kick, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(attacker.get_temporary_effects("kick_priority"))

    def test_life_force_errata_heals_tick(self):
        move = MoveSpec(
            name="Life Force [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Healer", abilities=["Life Force [Errata]"], moves=[move], hp_stat=10)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - attacker.tick_value())
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertEqual(attacker.hp, before + attacker.tick_value())
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Life Force [Errata]"
                for event in battle.log
            )
        )

    def test_light_metal_errata_adjusts_stats(self):
        errata_spec = _pokemon_spec("Metal", abilities=["Light Metal [Errata]"], defense=12, spd=10, weight=5)
        base_spec = _pokemon_spec("Base", defense=12, spd=10, weight=5)
        errata_mon = PokemonState(spec=errata_spec, controller_id="a", position=(0, 0), active=True)
        base_mon = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(
            calculations.defensive_stat(errata_mon, "physical"),
            calculations.defensive_stat(base_mon, "physical") - 2,
        )
        self.assertEqual(
            calculations.speed_stat(errata_mon),
            calculations.speed_stat(base_mon) + 2,
        )
        self.assertEqual(errata_mon.weight_class(), base_mon.weight_class() - 2)


if __name__ == "__main__":
    unittest.main()
