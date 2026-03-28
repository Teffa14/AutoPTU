import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase
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


class AuditBatch44AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_steadfast_errata_raises_speed_on_flinch(self):
        spec = _pokemon_spec("Steady", abilities=["Steadfast [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Flinched"})
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon._handle_status_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("spd"), 1)
        self.assertTrue(mon.get_temporary_effects("initiative_penalty"))

    def test_steam_engine_grants_evasion_on_fire_hit(self):
        move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Defender", ability="Steam Engine", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        bonuses = [
            entry
            for entry in battle.pokemon[defender_id].get_temporary_effects("evasion_bonus")
            if entry.get("source") == "Steam Engine"
        ]
        self.assertTrue(bonuses)

    def test_steelworker_adds_stab_when_anchored(self):
        move = MoveSpec(
            name="Iron Head",
            type="Steel",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Worker", ability="Steelworker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_worker, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_worker.pokemon[attacker_id].add_temporary_effect("anchor_token")
        battle_worker.rng = SequenceRNG([19] + [3] * 20)
        before = battle_worker.pokemon[defender_id].hp
        battle_worker.resolve_move_targets(attacker_id, move, defender_id, battle_worker.pokemon[defender_id].position)
        damage_worker = before - battle_worker.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Worker", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_worker, damage_base)

    def test_stench_adds_flinch_chance(self):
        move = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            effects_text="Flinches on 18+.",
        )
        attacker_spec = _pokemon_spec("Skunk", ability="Stench", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([17] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Flinched"))

    def test_stench_errata_adds_flinch_chance(self):
        move = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            effects_text="Flinches on 18+.",
        )
        attacker_spec = _pokemon_spec("Skunk", abilities=["Stench [Errata]"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([17] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Flinched"))

    def test_sticky_hold_blocks_theft(self):
        move = MoveSpec(
            name="Thief",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        defender_items = [{"name": "Berry"}]
        attacker_spec = _pokemon_spec("Thief", moves=[move])
        defender_spec = _pokemon_spec("Holder", ability="Sticky Hold", moves=[move], items=defender_items)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(len(battle.pokemon[defender_id].spec.items), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sticky Hold"
                and event.get("effect") == "item_block"
                for event in battle.log
            )
        )

    def test_storm_drain_errata_absorbs_water(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Drain", abilities=["Storm Drain [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].hp, before)
        self.assertEqual(battle.pokemon[defender_id].combat_stages.get("spatk"), 1)

    def test_strong_jaw_boosts_bite_damage(self):
        move = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Biter", ability="Strong Jaw", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_strong, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_strong.rng = SequenceRNG([19] + [3] * 20)
        before = battle_strong.pokemon[defender_id].hp
        battle_strong.resolve_move_targets(attacker_id, move, defender_id, battle_strong.pokemon[defender_id].position)
        damage_strong = before - battle_strong.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Biter", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_strong, damage_base)

    def test_sturdy_errata_prevents_full_hp_ko(self):
        move = MoveSpec(
            name="Hyper Beam",
            type="Normal",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=16)
        defender_spec = _pokemon_spec("Tank", abilities=["Sturdy [Errata]"], moves=[move], hp_stat=10)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [6] * 40)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].hp, 1)

    def test_suction_cups_blocks_push(self):
        move = MoveSpec(
            name="Push",
            type="Normal",
            category="Physical",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pusher", moves=[move])
        defender_spec = _pokemon_spec("Cup", ability="Suction Cups", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        origin = battle.pokemon[defender_id].position
        moved = battle.apply_forced_movement(attacker_id, defender_id, {"kind": "push", "distance": 1})
        self.assertFalse(moved)
        self.assertEqual(battle.pokemon[defender_id].position, origin)

    def test_suction_cups_errata_blocks_push(self):
        move = MoveSpec(
            name="Push",
            type="Normal",
            category="Physical",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pusher", moves=[move])
        defender_spec = _pokemon_spec("Cup", abilities=["Suction Cups [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        origin = battle.pokemon[defender_id].position
        moved = battle.apply_forced_movement(attacker_id, defender_id, {"kind": "push", "distance": 1})
        self.assertFalse(moved)
        self.assertEqual(battle.pokemon[defender_id].position, origin)

    def test_sumo_stance_blocks_push(self):
        move = MoveSpec(
            name="Push",
            type="Normal",
            category="Physical",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pusher", moves=[move])
        defender_spec = _pokemon_spec("Sumo", ability="Sumo Stance", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        origin = battle.pokemon[defender_id].position
        moved = battle.apply_forced_movement(attacker_id, defender_id, {"kind": "push", "distance": 1})
        self.assertFalse(moved)
        self.assertEqual(battle.pokemon[defender_id].position, origin)

    def test_sumo_stance_errata_shoves_on_melee_hit(self):
        stance = MoveSpec(
            name="Sumo Stance [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
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
        attacker_spec = _pokemon_spec("Sumo", abilities=["Sumo Stance [Errata]"], moves=[stance, tackle])
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, stance, attacker_id, battle.pokemon[attacker_id].position)
        origin = battle.pokemon[defender_id].position
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        self.assertNotEqual(battle.pokemon[defender_id].position, origin)

    def test_sun_blanket_errata_heals_when_low(self):
        sun_blanket = MoveSpec(
            name="Sun Blanket [Errata]",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Blanket", abilities=["Sun Blanket [Errata]"], moves=[sun_blanket])
        defender_spec = _pokemon_spec("Target", moves=[sun_blanket])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].hp = 1
        before = battle.pokemon[attacker_id].hp
        battle.resolve_move_targets(attacker_id, sun_blanket, attacker_id, battle.pokemon[attacker_id].position)
        self.assertGreater(battle.pokemon[attacker_id].hp, before)

    def test_sunglow_grants_radiant_in_sun(self):
        sunglow = MoveSpec(
            name="Sunglow",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Glow", ability="Sunglow", moves=[sunglow])
        defender_spec = _pokemon_spec("Target", moves=[sunglow])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sunny"
        battle.resolve_move_targets(attacker_id, sunglow, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("radiant"))

    def test_sunglow_errata_grants_radiant_in_sun(self):
        sunglow = MoveSpec(
            name="Sunglow [Errata]",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Glow", abilities=["Sunglow [Errata]"], moves=[sunglow])
        defender_spec = _pokemon_spec("Target", moves=[sunglow])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sunny"
        battle.resolve_move_targets(attacker_id, sunglow, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("radiant"))

    def test_super_luck_adds_crit_range_bonus(self):
        spec = _pokemon_spec("Lucky", ability="Super Luck")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        bonus = mon.get_temporary_effects("crit_range_bonus")
        self.assertTrue(bonus)

    def test_surge_surfer_doubles_speed_in_electric_terrain(self):
        spec = _pokemon_spec("Surfer", ability="Surge Surfer", spd=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.terrain = {"name": "Electric"}
        entry = battle._initiative_entry_for_pokemon("a-1")
        base_battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)},
            grid=GridState(width=6, height=6),
        )
        base_entry = base_battle._initiative_entry_for_pokemon("a-1")
        self.assertGreater(entry.total, base_entry.total)

    def test_sway_redirects_melee_attack(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Dancer", ability="Sway", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sway"
                and event.get("effect") == "redirect"
                for event in battle.log
            )
        )

    def test_swift_swim_errata_doubles_swim_speed(self):
        spec = _pokemon_spec("Swimmer", abilities=["Swift Swim [Errata]"], movement={"swim": 4})
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        base = mon.movement_speed("swim", weather="rain")
        self.assertEqual(base, 8)

    def test_symbiosis_transfers_item(self):
        move = MoveSpec(
            name="Symbiosis",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Giver", ability="Symbiosis", moves=[move], items=[{"name": "Berry"}])
        defender_spec = _pokemon_spec("Ally", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(battle.pokemon[attacker_id].spec.items)
        self.assertTrue(battle.pokemon[defender_id].spec.items)

    def test_symbiosis_errata_shares_item(self):
        move = MoveSpec(
            name="Symbiosis [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Giver", abilities=["Symbiosis [Errata]"], moves=[move], items=[{"name": "Berry"}])
        defender_spec = _pokemon_spec("Ally", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].spec.items)
        self.assertTrue(battle.pokemon[defender_id].spec.items)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("symbiosis_shared"))

    def test_synchronize_passes_status(self):
        move = MoveSpec(
            name="Thunder Wave",
            type="Electric",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Caster", moves=[move])
        defender_spec = _pokemon_spec("Sync", ability="Synchronize", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        events = []
        battle._apply_status(
            events,
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=battle.pokemon[defender_id],
            status="Burned",
            effect="test",
            description="Test",
            remaining=1,
        )
        self.assertTrue(battle.pokemon[attacker_id].has_status("Burned"))

    def test_tangled_feet_increases_evasion_when_confused(self):
        spec = _pokemon_spec("Tangled", ability="Tangled Feet", spd=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Confused"})
        value = calculations.evasion_value(mon, "physical")
        base_spec = _pokemon_spec("Base", spd=10)
        base = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        base.statuses.append({"name": "Confused"})
        base_value = calculations.evasion_value(base, "physical")
        self.assertGreater(value, base_value)

    def test_tangled_feet_errata_increases_evasion_when_confused(self):
        spec = _pokemon_spec("Tangled", abilities=["Tangled Feet [Errata]"], spd=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Confused"})
        value = calculations.evasion_value(mon, "physical")
        base_spec = _pokemon_spec("Base", spd=10)
        base = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        base.statuses.append({"name": "Confused"})
        base_value = calculations.evasion_value(base, "physical")
        self.assertGreater(value, base_value)

    def test_tangling_hair_slows_melee_attacker(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Hair", ability="Tangling Hair", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].has_status("Slowed"))
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("spd"), -1)

    def test_targeting_system_readies_lock_on(self):
        move = MoveSpec(
            name="Targeting System",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Targeter", ability="Targeting System", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("lock_on_swift"))

    def test_teamwork_boosts_melee_accuracy(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        ally = PokemonState(
            spec=_pokemon_spec("Ally", ability="Teamwork", moves=[move]),
            controller_id="a",
            position=(2, 4),
            active=True,
        )
        battle.pokemon["a-2"] = ally
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Teamwork"
                and event.get("effect") == "accuracy_bonus"
                for event in battle.log
            )
        )

    def test_telepathy_shifts_out_of_ally_area(self):
        move = MoveSpec(
            name="Surf",
            type="Water",
            category="Special",
            db=8,
            ac=2,
            range_kind="Burst",
            range_value=2,
            area_kind="Burst",
            area_value=2,
            target_kind="Self",
            target_range=0,
            range_text="Burst 2",
        )
        attacker_spec = _pokemon_spec("Ally", moves=[move])
        defender_spec = _pokemon_spec("Mind", ability="Telepathy", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].position = (3, 2)
        battle.pokemon[attacker_id].controller_id = "a"
        battle.pokemon[defender_id].controller_id = "a"
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Telepathy"
                and event.get("effect") == "shift"
                for event in battle.log
            )
        )

    def test_telepathy_errata_shifts_out_of_ally_area(self):
        move = MoveSpec(
            name="Surf",
            type="Water",
            category="Special",
            db=8,
            ac=2,
            range_kind="Burst",
            range_value=2,
            area_kind="Burst",
            area_value=2,
            target_kind="Self",
            target_range=0,
            range_text="Burst 2",
        )
        attacker_spec = _pokemon_spec("Ally", moves=[move])
        defender_spec = _pokemon_spec("Mind", abilities=["Telepathy [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].position = (3, 2)
        battle.pokemon[attacker_id].controller_id = "a"
        battle.pokemon[defender_id].controller_id = "a"
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Telepathy"
                and event.get("effect") == "shift"
                for event in battle.log
            )
        )
