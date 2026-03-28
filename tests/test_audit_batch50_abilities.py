import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules import targeting


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
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
    level=20,
    items=None,
    movement=None,
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
        items=items or [],
        movement=movement or {"overland": 4},
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
    battle.rng = SequenceRNG([20] * 200)
    return battle, "a-1", "b-1"


class AuditBatch50AbilityTests(unittest.TestCase):
    def test_blow_away_errata_pushes_and_ticks(self):
        move = MoveSpec(
            name="Whirlwind",
            type="Normal",
            category="Status",
            db=8,
            ac=2,
            range_kind="Line",
            range_value=6,
            target_kind="Self",
            area_kind="Line",
            area_value=6,
            range_text="Line 6",
            effects_text="Push 1",
        )
        attacker_spec = _pokemon_spec("Blow", abilities=["Blow Away [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec, attacker_pos=(2, 2), defender_pos=(2, 4))
        defender = battle.pokemon[defender_id]
        before_hp = defender.hp
        before_pos = defender.position
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(before_hp - defender.hp, defender.tick_value())
        self.assertEqual(targeting.chebyshev_distance(before_pos, defender.position), 2)

    def test_bodyguard_errata_intercepts_and_reduces_damage(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Striker", moves=[move], spatk=14)
        target_spec = _pokemon_spec("Ally", moves=[move])
        bodyguard_spec = _pokemon_spec("Guard", abilities=["Bodyguard [Errata]"], moves=[move])
        battle, attacker_id, target_id = _build_battle(attacker_spec, target_spec, attacker_pos=(2, 5), defender_pos=(2, 3))
        bodyguard = PokemonState(spec=bodyguard_spec, controller_id="b", position=(2, 2), active=True)
        battle.pokemon["b-2"] = bodyguard
        target_before = battle.pokemon[target_id].hp
        guard_before = bodyguard.hp
        battle.resolve_move_targets(attacker_id, move, target_id, battle.pokemon[target_id].position)
        self.assertEqual(battle.pokemon[target_id].hp, target_before)
        self.assertLess(bodyguard.hp, guard_before)
        self.assertEqual(bodyguard.position, (2, 3))

    def test_bone_lord_errata_bone_club_drops_def_and_spatk(self):
        move = MoveSpec(
            name="Bone Club",
            type="Ground",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Clubber", abilities=["Bone Lord [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("def", 0), -1)
        self.assertEqual(defender.combat_stages.get("spatk", 0), -1)

    def test_bone_lord_errata_bonemerang_no_double_strike(self):
        move = MoveSpec(
            name="Bonemerang",
            type="Ground",
            category="Physical",
            db=5,
            ac=3,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            range_text="6, 1 Target, Doublestrike",
        )
        attacker_spec = _pokemon_spec("Boomer", abilities=["Bone Lord [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        entry = next(payload for payload in battle.log if payload.get("type") == "move" and payload.get("move") == "Bonemerang")
        self.assertIsNone(entry.get("strike_hits"))

    def test_bone_lord_errata_bone_rush_hits_four_times(self):
        move = MoveSpec(
            name="Bone Rush",
            type="Ground",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Five Strike",
        )
        attacker_spec = _pokemon_spec("Rusher", abilities=["Bone Lord [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        entry = next(payload for payload in battle.log if payload.get("type") == "move" and payload.get("move") == "Bone Rush")
        self.assertEqual(entry.get("strike_hits"), 4)

    def test_bone_wielder_errata_ignores_ground_immunity(self):
        move = MoveSpec(
            name="Bone Club",
            type="Ground",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Wielder", abilities=["Bone Wielder [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Flyer", moves=[move], types=["Flying"])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(battle.pokemon[defender_id].hp, before)

    def test_brimstone_errata_applies_both_statuses(self):
        fire_move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        poison_move = MoveSpec(
            name="Poison Sting",
            type="Poison",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Brim", abilities=["Brimstone [Errata]"], moves=[fire_move, poison_move])
        defender_spec = _pokemon_spec("Target", moves=[fire_move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle._apply_status(
            [],
            attacker_id=attacker_id,
            target_id=defender_id,
            move=fire_move,
            target=battle.pokemon[defender_id],
            status="Burned",
            effect="test",
            description="",
        )
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Burned"))
        self.assertTrue(defender.has_status("Poisoned"))
        defender.statuses = []
        battle._apply_status(
            [],
            attacker_id=attacker_id,
            target_id=defender_id,
            move=poison_move,
            target=battle.pokemon[defender_id],
            status="Poisoned",
            effect="test",
            description="",
        )
        self.assertTrue(defender.has_status("Burned"))
        self.assertTrue(defender.has_status("Poisoned"))

    def test_celebrate_errata_disengages_after_hit(self):
        celebrate = MoveSpec(
            name="Celebrate [Errata]",
            type="Normal",
            category="Status",
            ac=None,
            range_kind="Self",
            target_kind="Self",
        )
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Party", abilities=["Celebrate [Errata]"], moves=[celebrate, move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        origin = battle.pokemon[attacker_id].position
        battle.resolve_move_targets(attacker_id, celebrate, attacker_id, origin)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        new_pos = battle.pokemon[attacker_id].position
        self.assertNotEqual(origin, new_pos)
        self.assertLessEqual(targeting.chebyshev_distance(origin, new_pos), 2)

    def test_chlorophyll_errata_doubles_initiative(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Sun", abilities=["Chlorophyll [Errata]"], moves=[move], spd=8)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sunny"
        entry = battle._initiative_entry_for_pokemon(attacker_id)
        self.assertEqual(entry.speed, 16)

    def test_clay_cannons_errata_extends_origin(self):
        clay = MoveSpec(
            name="Clay Cannons [Errata]",
            type="Ground",
            category="Status",
            ac=None,
            range_kind="Self",
            target_kind="Self",
        )
        move = MoveSpec(
            name="Mud Shot",
            type="Ground",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=2,
            target_kind="Ranged",
            target_range=2,
            range_text="Range 2, 1 Target",
        )
        attacker_spec = _pokemon_spec("Clay", abilities=["Clay Cannons [Errata]"], moves=[clay, move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec, attacker_pos=(2, 2), defender_pos=(5, 2))
        battle.resolve_move_targets(attacker_id, clay, attacker_id, battle.pokemon[attacker_id].position)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(battle.pokemon[defender_id].hp, before)
        self.assertTrue(
            any(
                entry.get("type") == "ability" and entry.get("ability") == "Clay Cannons [Errata]"
                for entry in battle.log
            )
        )

    def test_damp_errata_adds_water_damage_bonus(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        errata_spec = _pokemon_spec("Dampy", abilities=["Damp [Errata]"], moves=[move])
        base_spec = _pokemon_spec("Base", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(errata_spec, defender_spec)
        battle.rng = SequenceRNG([18] + [6] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp
        base_battle, base_attacker_id, base_defender_id = _build_battle(base_spec, defender_spec)
        base_battle.rng = SequenceRNG([18] + [6] * 20)
        before_base = base_battle.pokemon[base_defender_id].hp
        base_battle.resolve_move_targets(base_attacker_id, move, base_defender_id, base_battle.pokemon[base_defender_id].position)
        base_damage = before_base - base_battle.pokemon[base_defender_id].hp
        self.assertGreater(errata_damage, base_damage)

    def test_danger_syrup_errata_blinds_on_sweet_scent(self):
        sweet_scent = MoveSpec(
            name="Sweet Scent",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Syrup", abilities=["Danger Syrup [Errata]"], moves=[sweet_scent])
        defender_spec = _pokemon_spec("Target", moves=[sweet_scent])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, sweet_scent, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Blinded"))
