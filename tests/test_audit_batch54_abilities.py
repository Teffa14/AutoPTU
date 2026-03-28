import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase, calculations


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


class AuditBatch54AbilityTests(unittest.TestCase):
    def test_justified_errata_triggers_on_dark_hit(self):
        bite = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Biter", moves=[bite], atk=14)
        defender_spec = _pokemon_spec("Justified", abilities=["Justified [Errata]"], moves=[bite])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, bite, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("atk"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Justified [Errata]"
                for event in battle.log
            )
        )

    def test_justified_errata_triggers_on_aoo(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Runner", moves=[move], atk=12)
        defender_spec = _pokemon_spec("Guard", abilities=["Justified [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 50)
        battle._perform_attack_of_opportunity(attacker_id, defender_id, "test")
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("atk"), 1)

    def test_kampfgeist_errata_resists_damage_once_per_scene(self):
        move = MoveSpec(
            name="Rock Slide",
            type="Rock",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14, types=["Rock"])
        base_defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=20)
        errata_defender_spec = _pokemon_spec("Target", abilities=["Kampfgeist [Errata]"], moves=[move], hp_stat=20)

        battle_base, attacker_id, defender_id = _build_battle(attacker_spec, base_defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_id].hp
        battle_base.resolve_move_targets(attacker_id, move, defender_id, battle_base.pokemon[defender_id].position)
        base_damage = before_base - battle_base.pokemon[defender_id].hp

        battle_errata, attacker_id2, defender_id2 = _build_battle(attacker_spec, errata_defender_spec)
        battle_errata.rng = SequenceRNG([15] * 40)
        before_errata = battle_errata.pokemon[defender_id2].hp
        battle_errata.resolve_move_targets(attacker_id2, move, defender_id2, battle_errata.pokemon[defender_id2].position)
        errata_damage = before_errata - battle_errata.pokemon[defender_id2].hp
        self.assertLess(errata_damage, base_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Kampfgeist [Errata]"
                and event.get("effect") == "type_resist"
                for event in battle_errata.log
            )
        )

        before_second = battle_errata.pokemon[defender_id2].hp
        battle_errata.resolve_move_targets(attacker_id2, move, defender_id2, battle_errata.pokemon[defender_id2].position)
        second_damage = before_second - battle_errata.pokemon[defender_id2].hp
        self.assertEqual(second_damage, base_damage)

    def test_lightning_rod_errata_redirects_once_per_scene(self):
        zap = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[zap], spatk=14, types=["Electric"])
        target_spec = _pokemon_spec("Target", moves=[zap])
        rod_spec = _pokemon_spec("Rod", abilities=["Lightning Rod [Errata]"], moves=[zap])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(0, 0), active=True)
        target = PokemonState(spec=target_spec, controller_id="b", position=(0, 4), active=True)
        rod = PokemonState(spec=rod_spec, controller_id="b", position=(0, 2), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": target, "b-2": rod},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 200)

        before_rod = rod.hp
        battle.resolve_move_targets("a-1", zap, "b-1", target.position)
        self.assertLess(rod.hp, before_rod + 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Lightning Rod [Errata]"
                and event.get("effect") == "redirect"
                for event in battle.log
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Lightning Rod [Errata]"
                and event.get("effect") == "absorb"
                for event in battle.log
            )
        )

        before_target = target.hp
        battle.resolve_move_targets("a-1", zap, "b-1", target.position)
        self.assertLess(target.hp, before_target)

    def test_liquid_ooze_errata_poison_resist(self):
        move = MoveSpec(
            name="Sludge",
            type="Poison",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14, types=["Poison"])
        base_defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=20)
        errata_defender_spec = _pokemon_spec("Target", abilities=["Liquid Ooze [Errata]"], moves=[move], hp_stat=20)

        battle_base, attacker_id, defender_id = _build_battle(attacker_spec, base_defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_id].hp
        battle_base.resolve_move_targets(attacker_id, move, defender_id, battle_base.pokemon[defender_id].position)
        base_damage = before_base - battle_base.pokemon[defender_id].hp

        battle_errata, attacker_id2, defender_id2 = _build_battle(attacker_spec, errata_defender_spec)
        battle_errata.rng = SequenceRNG([15] * 40)
        before_errata = battle_errata.pokemon[defender_id2].hp
        battle_errata.resolve_move_targets(attacker_id2, move, defender_id2, battle_errata.pokemon[defender_id2].position)
        errata_damage = before_errata - battle_errata.pokemon[defender_id2].hp
        self.assertLess(errata_damage, base_damage)

    def test_liquid_ooze_errata_reverses_leech_seed(self):
        seed = MoveSpec(
            name="Leech Seed",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Seeder", moves=[seed])
        defender_spec = _pokemon_spec("Ooze", abilities=["Liquid Ooze [Errata]"], moves=[seed])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, seed, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        before_attacker = attacker.hp
        before_defender = defender.hp
        defender._handle_status_phase_effects(battle, TurnPhase.START, defender_id)
        self.assertLess(attacker.hp, before_attacker)
        self.assertEqual(defender.hp, before_defender)

    def test_lunchbox_errata_grants_temp_hp_once_per_scene(self):
        spec = _pokemon_spec("Snacker", abilities=["Lunchbox [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.food_buffs.append({"effect": "Restores 30 HP"})
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon.hp = max(1, mon.max_hp() // 2)
        before = mon.temp_hp
        battle._apply_food_buff_start("a-1")
        self.assertEqual(mon.temp_hp, before + mon.tick_value())
        battle._apply_food_buff_start("a-1")
        self.assertEqual(mon.temp_hp, before + mon.tick_value())


if __name__ == "__main__":
    unittest.main()
