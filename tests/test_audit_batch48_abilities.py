import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import (
    ActionType,
    BattleState,
    GridState,
    PokemonState,
    TrainerState,
    TurnPhase,
    UseMoveAction,
)


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
    gender="",
    capabilities=None,
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
        gender=gender,
        capabilities=capabilities or [],
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


class AuditBatch48AbilityTests(unittest.TestCase):
    def test_voodoo_doll_curses_additional_target(self):
        curse = MoveSpec(
            name="Curse",
            type="Ghost",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Hex", abilities=["Voodoo Doll"], types=["Ghost"], moves=[curse]
        )
        defender_spec = _pokemon_spec("Target", moves=[curse])
        extra_spec = _pokemon_spec("Extra", moves=[curse])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        extra = PokemonState(
            spec=extra_spec,
            controller_id="b",
            position=(3, 2),
            active=True,
        )
        battle.pokemon["b-2"] = extra
        battle.rng = SequenceRNG([20] + [3] * 20)
        battle.resolve_move_targets(attacker_id, curse, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon["b-2"].has_status("Cursed"))
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("voodoo_doll_used"))

    def test_wallmaster_adds_barrier_diagonals(self):
        barrier = MoveSpec(
            name="Barrier",
            type="Psychic",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker = PokemonState(
            spec=_pokemon_spec("Mr. Mime", abilities=["Wallmaster"], moves=[barrier]),
            controller_id=trainer.identifier,
            position=(2, 2),
        )
        grid = GridState(width=5, height=5)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker},
            grid=grid,
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=barrier,
            result={"hit": False},
            damage_dealt=0,
        )
        self.assertEqual(len(grid.blockers), 6)
        self.assertIn((3, 3), grid.blockers)
        self.assertIn((3, 1), grid.blockers)
        self.assertTrue([evt for evt in events if evt.get("effect") == "barrier_extend"])

    def test_wash_away_resets_stages_and_clears_coats(self):
        splash = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Washer", abilities=["Wash Away"], moves=[splash])
        defender_spec = _pokemon_spec("Target", moves=[splash])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.combat_stages["atk"] = 2
        defender.combat_stages["def"] = 1
        defender.statuses.append({"name": "Reflect"})
        defender.statuses.append({"name": "Aqua Ring"})
        battle.rng = SequenceRNG([20] + [3] * 20)
        battle.resolve_move_targets(attacker_id, splash, defender_id, defender.position)
        self.assertEqual(defender.combat_stages["atk"], 0)
        self.assertEqual(defender.combat_stages["def"], 0)
        self.assertFalse(defender.has_status("Reflect"))
        self.assertFalse(defender.has_status("Aqua Ring"))

    def test_wave_rider_boosts_speed_in_water(self):
        move = MoveSpec(
            name="Splash",
            type="Normal",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        attacker_spec = _pokemon_spec("Surfer", abilities=["Wave Rider"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.grid.tiles[(2, 2)] = {"type": "water"}
        attacker = battle.pokemon[attacker_id]
        attacker._handle_ability_phase_effects(battle, TurnPhase.START, attacker_id)
        self.assertEqual(attacker.combat_stages.get("spd", 0), 4)
        self.assertTrue(attacker.get_temporary_effects("wave_rider_active"))

    def test_weak_armor_shifts_defense_and_speed(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Striker", moves=[tackle])
        defender_spec = _pokemon_spec("Target", abilities=["Weak Armor"], moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 20)
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("def", 0), -1)
        self.assertEqual(defender.combat_stages.get("spd", 0), 1)

    def test_weaponize_intercepts_for_living_weapon(self):
        strike = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(
            spec=_pokemon_spec("Archer", moves=[strike], spatk=14),
            controller_id=trainer_a.identifier,
            position=(2, 2),
            active=True,
        )
        defender = PokemonState(
            spec=_pokemon_spec("Target", moves=[strike]),
            controller_id=trainer_b.identifier,
            position=(2, 5),
            active=True,
        )
        weapon = PokemonState(
            spec=_pokemon_spec(
                "Weapon",
                abilities=["Weaponize"],
                moves=[strike],
                capabilities=[{"name": "Living Weapon"}],
            ),
            controller_id=trainer_b.identifier,
            position=(2, 4),
            active=True,
        )
        battle = BattleState(
            trainers={trainer_a.identifier: trainer_a, trainer_b.identifier: trainer_b},
            pokemon={"a": attacker, "b": defender, "b-weapon": weapon},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 200)
        before_defender = defender.hp
        before_weapon = weapon.hp
        battle.resolve_move_targets("a", strike, "b", defender.position)
        self.assertEqual(defender.hp, before_defender)
        self.assertLess(weapon.hp, before_weapon)

    def test_weeble_counters_melee_hit(self):
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[slash], atk=14)
        defender_spec = _pokemon_spec("Weeble", abilities=["Weeble"], moves=[slash])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].combat_stages["accuracy"] = 6
        battle.rng = SequenceRNG([20] + [3] * 40)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        before_attacker = attacker.hp
        before_defender = defender.hp
        battle.resolve_move_targets(attacker_id, slash, defender_id, defender.position)
        damage_to_defender = before_defender - defender.hp
        damage_to_attacker = before_attacker - attacker.hp
        expected = max(1, int(damage_to_defender / 3))
        self.assertEqual(damage_to_attacker, expected)
        self.assertFalse(defender.has_action_available(ActionType.STANDARD))

    def test_whirlwind_kicks_turns_rapid_spin_into_burst(self):
        rapid = MoveSpec(
            name="Rapid Spin",
            type="Normal",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Spinner", abilities=["Whirlwind Kicks"], moves=[rapid])
        defender_spec = _pokemon_spec("Target", moves=[rapid])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name=rapid.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[attacker_id], rapid)
        self.assertEqual(effective.area_kind, "Burst")
        self.assertEqual(effective.area_value, 1)
        self.assertEqual(effective.range_text, "Burst 1")
        self.assertGreaterEqual(effective.priority, 1)

    def test_windveiled_blocks_flying_and_charges_bonus(self):
        gust = MoveSpec(
            name="Gust",
            type="Flying",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Bird", moves=[gust], spatk=14)
        defender_spec = _pokemon_spec("Veil", abilities=["Windveiled"], moves=[gust])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, gust, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].hp, before)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("windveiled_boost"))
        action = UseMoveAction(actor_id=defender_id, move_name=gust.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[defender_id], gust, consume=True)
        self.assertEqual(effective.db, (gust.db or 0) + 1)

    def test_winters_kiss_blocks_ice_and_heals(self):
        ice = MoveSpec(
            name="Ice Beam",
            type="Ice",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Caster", moves=[ice], spatk=14)
        defender_spec = _pokemon_spec("Chill", abilities=["Winter's Kiss"], moves=[ice])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.hp = max(1, (defender.hp or 0) - defender.tick_value())
        before = defender.hp
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, ice, defender_id, defender.position)
        expected = min(defender.max_hp(), before + defender.tick_value())
        self.assertEqual(defender.hp, expected)

    def test_winters_kiss_heals_when_using_ice_moves(self):
        ice = MoveSpec(
            name="Ice Beam",
            type="Ice",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Chill", abilities=["Winter's Kiss"], moves=[ice], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[ice])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, (attacker.hp or 0) - attacker.tick_value())
        before = attacker.hp
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, ice, defender_id, battle.pokemon[defender_id].position)
        expected = min(attacker.max_hp(), before + attacker.tick_value())
        self.assertEqual(attacker.hp, expected)

    def test_wishmaster_cures_status_immediately(self):
        wish = MoveSpec(
            name="Wish",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Jirachi", abilities=["Wishmaster"], moves=[wish])
        defender_spec = _pokemon_spec("Target", moves=[wish])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Burned"})
        battle.rng = SequenceRNG([20] + [3] * 20)
        battle.resolve_move_targets(attacker_id, wish, defender_id, defender.position)
        self.assertFalse(defender.statuses)
        self.assertFalse(battle.wishes)

    def test_wistful_melody_lowers_attack_and_spatk(self):
        sing = MoveSpec(
            name="Sing",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Song", abilities=["Wistful Melody"], moves=[sing])
        defender_spec = _pokemon_spec("Target", moves=[sing])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 20)
        battle.resolve_move_targets(attacker_id, sing, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("atk", 0), -2)
        self.assertEqual(defender.combat_stages.get("spatk", 0), -2)

    def test_wobble_reflects_damage(self):
        jab = MoveSpec(
            name="Pound",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[jab], atk=14)
        defender_spec = _pokemon_spec("Wobble", abilities=["Wobble"], moves=[jab])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 40)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        before_attacker = attacker.hp
        before_defender = defender.hp
        battle.resolve_move_targets(attacker_id, jab, defender_id, defender.position)
        damage_to_defender = before_defender - defender.hp
        damage_to_attacker = before_attacker - attacker.hp
        self.assertEqual(damage_to_attacker, damage_to_defender * 2)

    def test_zen_mode_toggles_below_half_hp(self):
        zen = MoveSpec(
            name="Zen Mode",
            type="Psychic",
            category="Status",
            ac=None,
            range_kind="Self",
            target_kind="Self",
        )
        attacker_spec = _pokemon_spec("Zen", abilities=["Zen Mode"], moves=[zen])
        defender_spec = _pokemon_spec("Target", moves=[zen])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, (attacker.max_hp() // 2) - 1)
        battle.resolve_move_targets(attacker_id, zen, attacker_id, attacker.position)
        entry = next(iter(attacker.get_temporary_effects("zen_mode")), None)
        self.assertIsNotNone(entry)
        self.assertTrue(entry.get("active"))

    def test_needles_adds_tick_damage(self):
        jab = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Needler", abilities=["Needles"], moves=[jab], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[jab])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 40)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, jab, defender_id, battle.pokemon[defender_id].position)
        with_needles = before - battle.pokemon[defender_id].hp

        base_battle, base_attacker_id, base_defender_id = _build_battle(
            _pokemon_spec("Base", moves=[jab], atk=14), defender_spec
        )
        base_battle.rng = SequenceRNG([20] + [3] * 40)
        base_before = base_battle.pokemon[base_defender_id].hp
        base_battle.resolve_move_targets(
            base_attacker_id,
            jab,
            base_defender_id,
            base_battle.pokemon[base_defender_id].position,
        )
        without_needles = base_before - base_battle.pokemon[base_defender_id].hp
        tick = base_battle.pokemon[base_defender_id].tick_value()
        self.assertEqual(with_needles - without_needles, tick)
