import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.hooks import move_specials


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b


def _pokemon_spec(
    name,
    *,
    ability=None,
    abilities=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
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
    )


def _build_battle(attacker_spec, defender_spec):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="foes")
    attacker = PokemonState(
        spec=attacker_spec,
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=defender_spec,
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20] * 200)
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch32AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_ice_face_grants_temp_hp_in_hail(self):
        ice_face = MoveSpec(
            name="Ice Face",
            type="Ice",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Eiscue", ability="Ice Face", moves=[ice_face])
        defender_spec = _pokemon_spec("Target", moves=[ice_face])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Hail"
        attacker = battle.pokemon[attacker_id]
        attacker.temp_hp = 0
        battle.resolve_move_targets(attacker_id, ice_face, defender_id, attacker.position)
        self.assertEqual(attacker.temp_hp, attacker.tick_value() * 2)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Ice Face"
                and event.get("effect") == "temp_hp"
                for event in battle.log
            )
        )

    def test_imposter_copies_stages_and_ability_on_switch(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        outgoing = PokemonState(
            spec=_pokemon_spec("Outgoing", moves=[move]),
            controller_id="a",
            position=(2, 2),
            active=True,
        )
        replacement = PokemonState(
            spec=_pokemon_spec("Imposter", ability="Imposter", moves=[move]),
            controller_id="a",
            position=None,
            active=False,
        )
        target = PokemonState(
            spec=_pokemon_spec("Target", abilities=["Pressure"], moves=[move]),
            controller_id="b",
            position=(2, 3),
            active=True,
        )
        target.combat_stages["atk"] = 2
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": outgoing, "a-2": replacement, "b-1": target},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 50)
        battle.round = 1
        battle._apply_switch(
            outgoing_id="a-1",
            replacement_id="a-2",
            initiator_id="a",
            allow_replacement_turn=False,
            allow_immediate=False,
        )
        self.assertEqual(replacement.combat_stages.get("atk"), 2)
        entrained = replacement.get_temporary_effects("entrained_ability")
        self.assertTrue(entrained)
        self.assertEqual(entrained[0].get("ability"), "Pressure")
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Impostor"
                and event.get("effect") == "transform"
                for event in battle.log
            )
        )

    def test_innards_out_resists_and_retaliates(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Defender", ability="Innards Out", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        attacker_before = attacker.hp
        defender_before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        defender_damage = defender_before - defender.hp
        attacker_damage = attacker_before - attacker.hp
        self.assertGreater(defender_damage, 0)
        self.assertEqual(attacker_damage, defender_damage * 2)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Innards Out"
                and event.get("effect") == "resist"
                for event in battle.log
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Innards Out"
                and event.get("effect") == "retaliate"
                for event in battle.log
            )
        )

    def test_inner_focus_grants_flinch_immunity(self):
        spec = _pokemon_spec("Lucario", ability="Inner Focus")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        self.assertTrue(mon.get_temporary_effects("flinch_immunity"))

    def test_interference_applies_accuracy_penalty(self):
        interference = MoveSpec(
            name="Interference",
            type="Electric",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Interferer", ability="Interference", moves=[interference])
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, interference, defender_id, battle.pokemon[attacker_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.get_temporary_effects("accuracy_penalty"))
        battle.log = []
        battle.resolve_move_targets(defender_id, tackle, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Interference"
                and event.get("effect") == "accuracy_penalty"
                for event in battle.log
            )
        )

    def test_intimidate_lowers_adjacent_on_switch(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        outgoing = PokemonState(
            spec=_pokemon_spec("Outgoing", moves=[move]),
            controller_id="a",
            position=(2, 2),
            active=True,
        )
        replacement = PokemonState(
            spec=_pokemon_spec("Intimidate", ability="Intimidate", moves=[move]),
            controller_id="a",
            position=None,
            active=False,
        )
        opponent = PokemonState(
            spec=_pokemon_spec("Opponent", moves=[move]),
            controller_id="b",
            position=(2, 3),
            active=True,
        )
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": outgoing, "a-2": replacement, "b-1": opponent},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 50)
        battle.round = 1
        battle._apply_switch(
            outgoing_id="a-1",
            replacement_id="a-2",
            initiator_id="a",
            allow_replacement_turn=False,
            allow_immediate=False,
        )
        self.assertEqual(opponent.combat_stages.get("atk"), -1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Intimidate"
                and event.get("effect") == "attack_drop"
                for event in battle.log
            )
        )

    def test_intrepid_sword_raises_attack_on_init(self):
        spec = _pokemon_spec("Zacian", ability="Intrepid Sword")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(mon.combat_stages.get("atk"), 1)

    def test_juicy_energy_uses_level_for_berry_juice(self):
        spec = _pokemon_spec("Applin", ability="Juicy Energy", level=20)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.food_buffs.append({"effect": "Restores 30 HP"})
        max_hp = mon.max_hp()
        mon.hp = max(1, max_hp // 2)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        before = mon.hp
        battle._apply_food_buff_start("a-1")
        healed = mon.hp - before
        self.assertEqual(healed, min(20, max_hp - before))

    def test_justified_raises_attack_after_dark_hit(self):
        bite = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[bite], atk=14)
        defender_spec = _pokemon_spec("Justified", ability="Justified", moves=[bite])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets(attacker_id, bite, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].combat_stages.get("atk"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Justified"
                and event.get("effect") == "attack_raise"
                for event in battle.log
            )
        )

    def test_kampfgeist_grants_fighting_stab(self):
        move = MoveSpec(
            name="Karate Chop",
            type="Fighting",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Brawler", ability="Kampfgeist", moves=[move], types=["Normal"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        move_events = [event for event in battle.log if event.get("type") == "move" and event.get("move") == "Karate Chop"]
        self.assertTrue(move_events)
        self.assertEqual(move_events[-1].get("effective_db"), 8)
