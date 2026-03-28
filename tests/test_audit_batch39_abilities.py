import random
import unittest
from unittest import mock

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


class AuditBatch39AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_sequence_boosts_damage_with_adjacent_allies(self):
        move = MoveSpec(
            name="Thunder Punch",
            type="Electric",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("User", ability="Sequence", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move], types=["Water"])
        battle_seq, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        ally1 = PokemonState(
            spec=_pokemon_spec("Ally1", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        ally2 = PokemonState(
            spec=_pokemon_spec("Ally2", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(3, 2),
            active=True,
        )
        battle_seq.pokemon["a-2"] = ally1
        battle_seq.pokemon["a-3"] = ally2
        battle_seq.rng = SequenceRNG([18] + [3] * 50)
        before = battle_seq.pokemon[defender_id].hp
        battle_seq.resolve_move_targets(attacker_id, move, defender_id, battle_seq.pokemon[defender_id].position)
        damage_seq = before - battle_seq.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("User", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.pokemon["a-2"] = PokemonState(
            spec=_pokemon_spec("Ally1", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle_base.pokemon["a-3"] = PokemonState(
            spec=_pokemon_spec("Ally2", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(3, 2),
            active=True,
        )
        battle_base.rng = SequenceRNG([18] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_seq, damage_base)
        self.assertEqual(battle_seq.pokemon[attacker_id].combat_stages.get("atk"), 0)
        self.assertEqual(battle_seq.pokemon[attacker_id].combat_stages.get("spatk"), 0)

    def test_sequence_errata_adds_flat_damage_per_adjacent_ally(self):
        move = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("User", abilities=["Sequence [Errata]"], moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[move], types=["Water"])
        battle_seq, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_seq.pokemon["a-2"] = PokemonState(
            spec=_pokemon_spec("Ally1", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle_seq.pokemon["a-3"] = PokemonState(
            spec=_pokemon_spec("Ally2", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(3, 2),
            active=True,
        )
        battle_seq.rng = SequenceRNG([19] + [3] * 50)
        before = battle_seq.pokemon[defender_id].hp
        battle_seq.resolve_move_targets(attacker_id, move, defender_id, battle_seq.pokemon[defender_id].position)
        damage_seq = before - battle_seq.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("User", moves=[move], spatk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.pokemon["a-2"] = PokemonState(
            spec=_pokemon_spec("Ally1", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle_base.pokemon["a-3"] = PokemonState(
            spec=_pokemon_spec("Ally2", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(3, 2),
            active=True,
        )
        battle_base.rng = SequenceRNG([19] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertEqual(damage_seq - damage_base, 6)

    def test_serene_grace_boosts_effect_roll(self):
        move = MoveSpec(
            name="Ember Test",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            effects_text="Burns on 18+.",
        )
        attacker_spec = _pokemon_spec("Grace", ability="Serene Grace", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([17] + [4] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Burned"))

    def test_serpents_mark_grants_pattern_abilities(self):
        with mock.patch("auto_ptu.rules.abilities.ability_moves.random.randint", return_value=3):
            mon = PokemonState(
                spec=_pokemon_spec("Arbok", ability="Serpent's Mark"),
                controller_id="a",
                position=(0, 0),
                active=True,
            )
        effects = mon.get_temporary_effects("serpents_mark")
        self.assertTrue(effects)
        self.assertEqual(effects[0].get("pattern"), "Fear Pattern")
        granted = [
            entry
            for entry in mon.get_temporary_effects("ability_granted")
            if entry.get("source") == "Serpent's Mark"
        ]
        abilities = {entry.get("ability") for entry in granted}
        self.assertIn("Frighten", abilities)
        self.assertIn("Regal Challenge", abilities)

    def test_serpents_mark_errata_grants_pattern_abilities(self):
        with mock.patch("auto_ptu.rules.abilities.ability_moves.random.randint", return_value=5):
            mon = PokemonState(
                spec=_pokemon_spec("Arbok", abilities=["Serpent's Mark [Errata]"]),
                controller_id="a",
                position=(0, 0),
                active=True,
            )
        effects = mon.get_temporary_effects("serpents_mark")
        self.assertTrue(effects)
        self.assertEqual(effects[0].get("pattern"), "Speed Pattern")
        granted = [
            entry
            for entry in mon.get_temporary_effects("ability_granted")
            if entry.get("source") == "Serpent's Mark"
        ]
        abilities = {entry.get("ability") for entry in granted}
        self.assertIn("Run Away", abilities)
        self.assertIn("Speed Boost", abilities)

    def test_shackle_errata_halves_foe_movement_in_burst(self):
        shackle = MoveSpec(
            name="Shackle [Errata]",
            type="Ghost",
            category="Status",
            db=0,
            ac=None,
            range_kind="Burst",
            range_value=3,
            target_kind="Burst",
            target_range=3,
            area_kind="Burst",
            area_value=3,
            freq="Scene",
            range_text="Burst 3",
            effects_text="Ability action: foes in Burst 3 have movement halved until end of next turn.",
        )
        attacker_spec = _pokemon_spec("User", abilities=["Shackle [Errata]"], moves=[shackle])
        defender_spec = _pokemon_spec("Foe", moves=[shackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        foe_far = PokemonState(
            spec=_pokemon_spec("FoeFar", moves=[shackle]),
            controller_id="b",
            position=(7, 7),
            active=True,
        )
        ally = PokemonState(
            spec=_pokemon_spec("Ally", moves=[shackle]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle.pokemon["b-2"] = foe_far
        battle.pokemon["a-2"] = ally
        battle.resolve_move_targets(attacker_id, shackle, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("movement_halved"))
        self.assertFalse(foe_far.get_temporary_effects("movement_halved"))
        self.assertFalse(ally.get_temporary_effects("movement_halved"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Shackle [Errata]"
                and event.get("effect") == "movement_halved"
                for event in battle.log
            )
        )

    def test_shadow_shield_reduces_damage_at_full_hp(self):
        move = MoveSpec(
            name="Shadow Ball",
            type="Ghost",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Lunar", ability="Shadow Shield", moves=[move], types=["Psychic"])
        battle_shield, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_shield.rng = SequenceRNG([19] + [3] * 50)
        before = battle_shield.pokemon[defender_id].hp
        battle_shield.resolve_move_targets(attacker_id, move, defender_id, battle_shield.pokemon[defender_id].position)
        damage_shield = before - battle_shield.pokemon[defender_id].hp

        defender_base_spec = _pokemon_spec("Lunar", moves=[move], types=["Psychic"])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, defender_base_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_shield, damage_base)

    def test_sheer_force_boosts_moves_with_effects(self):
        move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            effects_text="Burns on 18+.",
        )
        attacker_spec = _pokemon_spec("Attacker", ability="Sheer Force", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_force, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_force.rng = SequenceRNG([19] + [3] * 50)
        before = battle_force.pokemon[defender_id].hp
        battle_force.resolve_move_targets(attacker_id, move, defender_id, battle_force.pokemon[defender_id].position)
        damage_force = before - battle_force.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("Attacker", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_force, damage_base)

    def test_sheer_force_errata_boosts_moves_with_effects(self):
        move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            effects_text="Burns on 18+.",
        )
        attacker_spec = _pokemon_spec("Attacker", abilities=["Sheer Force [Errata]"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_force, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_force.rng = SequenceRNG([19] + [3] * 50)
        before = battle_force.pokemon[defender_id].hp
        battle_force.resolve_move_targets(attacker_id, move, defender_id, battle_force.pokemon[defender_id].position)
        damage_force = before - battle_force.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("Attacker", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_force, damage_base)

    def test_shell_armor_blocks_critical_hits(self):
        move = MoveSpec(
            name="Slash Test",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            crit_range=16,
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Shelly", ability="Shell Armor", moves=[move])
        battle_shell, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_shell.rng = SequenceRNG([18] + [3] * 50)
        before = battle_shell.pokemon[defender_id].hp
        battle_shell.resolve_move_targets(attacker_id, move, defender_id, battle_shell.pokemon[defender_id].position)
        damage_shell = before - battle_shell.pokemon[defender_id].hp

        defender_base_spec = _pokemon_spec("Shelly", moves=[move])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, defender_base_spec)
        battle_base.rng = SequenceRNG([18] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_shell, damage_base)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Shell Armor"
                and event.get("effect") == "crit_block"
                for event in battle_shell.log
            )
        )
