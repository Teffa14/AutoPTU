import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, ShiftAction, TrainerState, TurnPhase
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
        weight=5,
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


class AuditBatch34AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_maelstrom_pulse_grants_priority_and_damage_bonus(self):
        maelstrom = MoveSpec(
            name="Maelstrom Pulse",
            type="Water",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        strike = MoveSpec(
            name="Water Pulse",
            type="Water",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Caster", ability="Maelstrom Pulse", moves=[maelstrom, strike], spd=12)
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, maelstrom, defender_id, battle.pokemon[defender_id].position)
        battle.log = []
        battle.resolve_move_targets(attacker_id, strike, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Maelstrom Pulse"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_magma_armor_blocks_freeze(self):
        attacker_move = MoveSpec(
            name="Ice Beam",
            type="Ice",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            effects_text="Ice Beam Freezes the target.",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[attacker_move], spatk=14)
        defender_spec = _pokemon_spec("Defender", ability="Magma Armor", moves=[attacker_move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, attacker_move, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(battle.pokemon[defender_id].has_status("Frozen"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Magma Armor"
                and event.get("effect") == "status_block"
                for event in battle.log
            )
        )

    def test_magnet_pull_restricts_steel_targets(self):
        magnet_pull = MoveSpec(
            name="Magnet Pull",
            type="Steel",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Magnet", ability="Magnet Pull", moves=[magnet_pull], types=["Steel"])
        defender_spec = _pokemon_spec("Steel", moves=[magnet_pull], types=["Steel"])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, magnet_pull, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.get_temporary_effects("magnet_pull"))
        action = ShiftAction(actor_id=defender_id, destination=(2, 2))
        with self.assertRaises(ValueError):
            action.validate(battle)

    def test_mega_launcher_boosts_pulse_moves(self):
        pulse = MoveSpec(
            name="Water Pulse",
            type="Water",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Blaster", ability="Mega Launcher", moves=[pulse], spatk=14, types=["Water"])
        defender_spec = _pokemon_spec("Target", moves=[pulse])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, pulse, defender_id, battle.pokemon[defender_id].position)
        move_events = [event for event in battle.log if event.get("type") == "move" and event.get("move") == "Water Pulse"]
        self.assertTrue(move_events)
        self.assertEqual(move_events[-1].get("effective_db"), 12)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Mega Launcher"
                and event.get("effect") == "db_bonus"
                for event in battle.log
            )
        )

    def test_memory_wipe_disables_last_move(self):
        wipe = MoveSpec(
            name="Memory Wipe",
            type="Psychic",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
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
        attacker_spec = _pokemon_spec("Wiper", ability="Memory Wipe", moves=[wipe, tackle])
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].add_temporary_effect("last_move", name="Tackle", round=battle.round)
        battle.resolve_move_targets(attacker_id, wipe, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Disabled"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Memory Wipe"
                and event.get("effect") == "disable"
                for event in battle.log
            )
        )

    def test_migraine_grants_telekinetic_below_half_hp(self):
        spec = _pokemon_spec("Psychic", ability="Migraine", level=20)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon.hp = max(1, mon.max_hp() // 2)
        events = mon._handle_status_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertTrue(mon.get_temporary_effects("capability_granted"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Migraine"
                and event.get("effect") == "capability"
                for event in events
            )
        )

    def test_mimicry_changes_type_based_on_weather(self):
        mimicry = MoveSpec(
            name="Mimicry",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Caster", ability="Mimicry", moves=[mimicry], types=["Normal"])
        defender_spec = _pokemon_spec("Target", moves=[mimicry])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Rain"
        battle.resolve_move_targets(attacker_id, mimicry, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[attacker_id].spec.types, ["Water"])
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Mimicry"
                and event.get("effect") == "type_change"
                for event in battle.log
            )
        )

    def test_missile_launch_deploys_tokens(self):
        missile = MoveSpec(
            name="Missile Launch",
            type="Dragon",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Launcher", ability="Missile Launch", moves=[missile])
        defender_spec = _pokemon_spec("Target", moves=[missile])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, missile, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        tokens = attacker.get_temporary_effects("missile_launch_tokens")
        self.assertTrue(tokens)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Missile Launch"
                and event.get("effect") == "deploy_tokens"
                for event in battle.log
            )
        )

    def test_moody_adjusts_two_stats(self):
        spec = _pokemon_spec("Moody", ability="Moody")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.rng = SequenceRNG([1, 3])
        events = mon._handle_ability_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertEqual(mon.combat_stages.get("atk"), 2)
        self.assertEqual(mon.combat_stages.get("def"), -2)
        self.assertTrue(
            any(
                event.get("type") == "combat_stage"
                and event.get("effect") == "moody_up"
                for event in events
            )
        )

    def test_mud_shield_grants_temp_hp_and_reduction(self):
        mud_shield = MoveSpec(
            name="Mud Shield",
            type="Ground",
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
        attacker_spec = _pokemon_spec("Mud", ability="Mud Shield", moves=[mud_shield])
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, mud_shield, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertGreater(attacker.temp_hp, 0)

        battle.grid.tiles[(2, 2)] = {"type": "mud"}
        battle.log = []
        battle.rng = SequenceRNG([20] + [3] * 50)
        before = attacker.hp
        battle.resolve_move_targets(defender_id, tackle, attacker_id, attacker.position)
        reduced_damage = before - attacker.hp
        mud_events = list(battle.log)

        attacker.hp = attacker.max_hp()
        battle.grid.tiles[(2, 2)] = {"type": "plain"}
        battle.log = []
        battle.rng = SequenceRNG([20] + [3] * 50)
        before_plain = attacker.hp
        battle.resolve_move_targets(defender_id, tackle, attacker_id, attacker.position)
        normal_damage = before_plain - attacker.hp

        self.assertLess(reduced_damage, normal_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Mud Shield"
                and event.get("effect") == "damage_reduction"
                for event in mud_events
            )
        )
