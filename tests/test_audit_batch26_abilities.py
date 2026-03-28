import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, calculations
from auto_ptu.rules.battle_state import TurnPhase
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
    types=None,
    moves=None,
    items=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
    gender="",
):
    abilities = [{"name": ability}] if ability else []
    return PokemonSpec(
        species=name,
        level=20,
        types=types or ["Normal"],
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=moves or [],
        abilities=abilities,
        items=items or [],
        movement={"overland": 4},
        gender=gender,
    )


def _build_battle(attacker_spec, defender_spec, *, grid=True):
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
        grid=GridState(width=10, height=10) if grid else None,
    )
    battle.rng = SequenceRNG([20] * 200)
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch26AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_bone_wielder_thick_club_accuracy_bonus(self):
        move = MoveSpec(
            name="Bone Club",
            type="Ground",
            category="Physical",
            db=8,
            ac=6,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Cubone",
            ability="Bone Wielder",
            moves=[move],
            items=[{"name": "Thick Club"}],
        )
        defender_spec = _pokemon_spec("Target", moves=[move], defense=5)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        battle.rng = SequenceRNG([6])
        result = calculations.attack_hits(battle.rng, attacker, defender, move)
        self.assertTrue(result.get("hit"))
        self.assertEqual(result.get("needed"), 6)

    def test_brimstone_adds_poison_on_fire_burn(self):
        move = MoveSpec(
            name="Sacred Fire",
            type="Fire",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Blazer", ability="Brimstone", moves=[move], types=["Fire"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Burned"))
        self.assertTrue(battle.pokemon[defender_id].has_status("Poisoned"))

    def test_celebrate_triggers_after_ko(self):
        move = MoveSpec(
            name="Strike",
            type="Normal",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Celebi", ability="Celebrate", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=1)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.hp = 1
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("spd"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Celebrate"
                and event.get("effect") == "boost"
                for event in battle.log
            )
        )

    def test_chemical_romance_infatuates_male_target(self):
        move = MoveSpec(
            name="Poison Gas",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 2, Burst 1",
        )
        attacker_spec = _pokemon_spec("Nidoqueen", ability="Chemical Romance", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], gender="male")
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Infatuated"))

    def test_chilling_neigh_raises_attack_and_chills_nearby(self):
        move = MoveSpec(
            name="Strike",
            type="Ice",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Rider", ability="Chilling Neigh", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=1)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        extra = PokemonState(
            spec=_pokemon_spec("Foe", moves=[move]),
            controller_id="b",
            position=(2, 5),
            active=True,
        )
        battle.pokemon["b-2"] = extra
        defender = battle.pokemon[defender_id]
        defender.hp = 1
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("atk"), 1)
        self.assertTrue(extra.get_temporary_effects("evasion_bonus"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Chilling Neigh"
                and event.get("effect") == "evasion_penalty"
                for event in battle.log
            )
        )

    def test_chlorophyll_adds_overland_in_sun(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        spec = _pokemon_spec("Sunflora", ability="Chlorophyll", moves=[move])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(mon.movement_speed("overland", "Sunny"), 6)

    def test_clay_cannons_origin_shift_for_ranged(self):
        clay = MoveSpec(
            name="Clay Cannons",
            type="Ground",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        shot = MoveSpec(
            name="Mud Shot",
            type="Ground",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=1,
            range_text="Range 1, 1 Target",
        )
        attacker_spec = _pokemon_spec("Clay", ability="Clay Cannons", moves=[clay, shot])
        defender_spec = _pokemon_spec("Target", moves=[shot])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].position = (2, 2)
        battle.pokemon[defender_id].position = (4, 2)
        battle.resolve_move_targets(attacker_id, clay, attacker_id, battle.pokemon[attacker_id].position)
        battle.resolve_move_targets(attacker_id, shot, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Clay Cannons"
                and event.get("effect") == "origin_shift"
                for event in battle.log
            )
        )

    def test_comatose_sleep_and_heal(self):
        move = MoveSpec(
            name="Comatose",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Komala", ability="Comatose", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.hp - attacker.tick_value())
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, attacker.position)
        self.assertTrue(attacker.has_status("Sleep"))
        self.assertGreater(attacker.hp, before)

    def test_combo_striker_triggers_struggle_followup(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Striker", ability="Combo Striker", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([10] + [20] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Combo Striker"
                and event.get("effect") == "followup"
                for event in battle.log
            )
        )
        self.assertTrue(
            any(event.get("type") == "move" and event.get("move") == "Struggle" for event in battle.log)
        )

    def test_corrosion_allows_toxic_on_steel(self):
        move = MoveSpec(
            name="Toxic",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Salazzle", ability="Corrosion", moves=[move])
        defender_spec = _pokemon_spec("Steelix", moves=[move], types=["Steel"])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Badly Poisoned"))
