import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules import calculations
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
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
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
        movement={"overland": 4},
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
    battle.round = 0
    return battle, "a-1", "b-1"


class AuditBatch24AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_abominable_blocks_recoil(self):
        move = MoveSpec(
            name="Recoil Strike",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Recoil 1/3",
        )
        attacker_spec = _pokemon_spec("Abomi", ability="Abominable", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(attacker.hp, before)

    def test_abominable_blocks_massive_damage_injury(self):
        move = MoveSpec(
            name="Heavy Slam",
            type="Steel",
            category="Physical",
            db=20,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Attacker",
            types=["Steel"],
            moves=[move],
            atk=30,
            defense=5,
            spd=10,
        )
        defender_spec_normal = _pokemon_spec(
            "Defender",
            types=["Normal"],
            moves=[move],
            hp_stat=1,
            defense=5,
        )
        defender_spec_abomi = _pokemon_spec(
            "Defender",
            ability="Abominable",
            types=["Normal"],
            moves=[move],
            hp_stat=1,
            defense=5,
        )
        battle_normal, a_id, d_id = _build_battle(attacker_spec, defender_spec_normal)
        battle_normal.rng = SequenceRNG([20] + [1] * 200)
        battle_normal.resolve_move_targets(a_id, move, d_id, battle_normal.pokemon[d_id].position)
        normal_injuries = battle_normal.pokemon[d_id].injuries

        battle_abomi, a2_id, d2_id = _build_battle(attacker_spec, defender_spec_abomi)
        battle_abomi.rng = SequenceRNG([20] + [1] * 200)
        battle_abomi.resolve_move_targets(a2_id, move, d2_id, battle_abomi.pokemon[d2_id].position)
        abomi_injuries = battle_abomi.pokemon[d2_id].injuries

        self.assertEqual(normal_injuries, abomi_injuries + 1)

    def test_accelerate_adds_priority_damage_bonus(self):
        accel = MoveSpec(
            name="Accelerate",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            target_kind="Self",
            freq="Scene x2",
            range_text="Self",
            effects_text="Ability action: your next STAB damaging move gains Priority and bonus damage.",
            priority=1,
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
        attacker_spec = _pokemon_spec(
            "Speedster",
            ability="Accelerate",
            moves=[accel, tackle],
            spd=14,
        )
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        half_speed = max(1, int(calculations.speed_stat(attacker) / 2))

        battle.resolve_move_targets(attacker_id, accel, attacker_id, attacker.position)
        self.assertTrue(attacker.get_temporary_effects("accelerate_ready"))

        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(attacker.get_temporary_effects("accelerate_ready"))
        bonus_events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Accelerate"
            and event.get("effect") == "damage_bonus"
        ]
        self.assertTrue(bonus_events)
        self.assertEqual(bonus_events[-1].get("amount"), half_speed)

    def test_adaptability_adds_db_to_stab(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Adapter", ability="Adaptability", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Adaptability"
            and event.get("effect") == "db_bonus"
        ]
        self.assertTrue(events)

    def test_aftermath_deals_quarter_max_hp(self):
        move = MoveSpec(
            name="Power Hit",
            type="Normal",
            category="Physical",
            db=15,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=20)
        defender_spec = _pokemon_spec("Aftermath", ability="Aftermath", moves=[move], hp_stat=1)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.hp = 1
        attacker = battle.pokemon[attacker_id]
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        expected = max(1, attacker.max_hp() // 4)
        self.assertEqual(before - attacker.hp, expected)

    def test_ambush_flinches_on_light_melee(self):
        move = MoveSpec(
            name="Quick Jab",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Sneak", ability="Ambush", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Flinch"))

    def test_anchored_places_anchor_token(self):
        attacker_spec = _pokemon_spec("Dhelmise", ability="Anchored")
        defender_spec = _pokemon_spec("Target")
        battle, attacker_id, _defender_id = _build_battle(attacker_spec, defender_spec)
        battle.start_round()
        self.assertTrue(battle.has_anchor_token(attacker_id))

    def test_aqua_bullet_shifts_before_water_move(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Shooter", ability="Aqua Bullet", moves=[move], types=["Water"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].position = (0, 0)
        battle.pokemon[defender_id].position = (0, 5)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[attacker_id].position, (0, 4))

    def test_arena_trap_slows_nearby_foes(self):
        attacker_spec = _pokemon_spec("Trapper", ability="Arena Trap")
        defender_spec = _pokemon_spec("Target")
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.start_round()
        self.assertTrue(battle.pokemon[defender_id].has_status("Slowed"))

    def test_aroma_veil_blocks_confusion(self):
        move = MoveSpec(
            name="Confuse Ray",
            type="Ghost",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        veil_spec = _pokemon_spec("Veil", ability="Aroma Veil")
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        veil = PokemonState(
            spec=veil_spec,
            controller_id="b",
            position=(2, 4),
            active=True,
        )
        battle.pokemon["b-2"] = veil
        events = []
        battle._apply_status(
            events,
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=battle.pokemon[defender_id],
            status="Confused",
            effect="test",
            description="Test confusion.",
        )
        self.assertFalse(battle.pokemon[defender_id].has_status("Confused"))
        self.assertTrue(any(event.get("ability") == "Aroma Veil" for event in events))

    def test_aura_break_suppresses_adaptability(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Adapter", ability="Adaptability", moves=[move])
        defender_spec = _pokemon_spec("Breaker", ability="Aura Break", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        aura_events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Aura Break"
            and event.get("effect") == "suppress"
        ]
        self.assertTrue(aura_events)
        adaptability_events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Adaptability"
            and event.get("effect") == "db_bonus"
        ]
        self.assertFalse(adaptability_events)
