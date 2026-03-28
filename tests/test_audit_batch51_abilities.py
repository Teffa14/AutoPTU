import random
import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import (
    ActionType,
    BattleState,
    GridState,
    PokemonState,
    ShiftAction,
    SprintAction,
    TrainerState,
    TurnPhase,
    UseItemAction,
    calculations,
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


class AuditBatch51AbilityTests(unittest.TestCase):
    def test_download_errata_raises_attack_when_def_lower(self):
        download = MoveSpec(
            name="Download [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pory", abilities=["Download [Errata]"], moves=[download])
        defender_spec = _pokemon_spec("Target", defense=6, spdef=12, moves=[download])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, download, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("atk"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Download [Errata]"
                and event.get("stat") == "atk"
                for event in battle.log
            )
        )

    def test_download_errata_tie_uses_choice(self):
        download = MoveSpec(
            name="Download [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pory", abilities=["Download [Errata]"], moves=[download])
        defender_spec = _pokemon_spec("Target", defense=10, spdef=10, moves=[download])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, download, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("atk"), 1)

    def test_defeatist_errata_bonus_above_half(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        errata_spec = _pokemon_spec("Defeatist", abilities=["Defeatist [Errata]"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=20)
        battle, attacker_id, defender_id = _build_battle(errata_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 30)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([20] + [3] * 30)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertGreater(errata_damage, base_damage)

    def test_defeatist_errata_penalty_and_initiative_bonus(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        errata_spec = _pokemon_spec("Defeatist", abilities=["Defeatist [Errata]"], moves=[move], atk=14, spd=8)
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=10)
        battle, attacker_id, defender_id = _build_battle(errata_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() // 2)
        attacker._handle_ability_phase_effects(battle, "start", attacker_id)
        entry = battle._initiative_entry_for_pokemon(attacker_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.total, entry.speed + 10)

        battle.rng = SequenceRNG([20] + [3] * 30)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([20] + [3] * 30)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertEqual(base_damage - errata_damage, 5)

    def test_defy_death_errata_heals_injuries_and_hp(self):
        move = MoveSpec(
            name="Defy Death [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Life", abilities=["Defy Death [Errata]"], moves=[move], hp_stat=10)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.injuries = 4
        attacker.hp = max(1, attacker.max_hp_with_injuries() - attacker.tick_value() * 3)
        before_hp = attacker.hp
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertEqual(attacker.injuries, 1)
        self.assertEqual(attacker.hp, before_hp + attacker.tick_value() * 3)

    def test_defy_death_errata_caps_three_injuries_per_day(self):
        move = MoveSpec(
            name="Defy Death [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Life", abilities=["Defy Death [Errata]"], moves=[move], hp_stat=10)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.injuries = 5
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertEqual(attacker.injuries, 2)
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertEqual(attacker.injuries, 2)

    def test_desert_weather_errata_grants_temp_hp_in_rain(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Rainy", abilities=["Desert Weather [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Rain"
        attacker = battle.pokemon[attacker_id]
        before = attacker.temp_hp
        attacker._handle_ability_phase_effects(battle, "end", attacker_id)
        self.assertEqual(attacker.temp_hp, before + attacker.tick_value())

    def test_desert_weather_errata_resists_fire_in_sun(self):
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], types=["Fire"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        defender_weather_spec = _pokemon_spec("Target", abilities=["Desert Weather [Errata]"], moves=[move])

        battle_normal, a_id, d_id = _build_battle(attacker_spec, defender_spec)
        battle_normal.weather = "Sunny"
        battle_normal.rng = SequenceRNG([20] + [3] * 50)
        defender = battle_normal.pokemon[d_id]
        before = defender.hp
        battle_normal.resolve_move_targets(a_id, move, d_id, defender.position)
        normal_damage = before - defender.hp

        battle_weather, a2_id, d2_id = _build_battle(attacker_spec, defender_weather_spec)
        battle_weather.weather = "Sunny"
        battle_weather.rng = SequenceRNG([20] + [3] * 50)
        defender2 = battle_weather.pokemon[d2_id]
        before2 = defender2.hp
        battle_weather.resolve_move_targets(a2_id, move, d2_id, defender2.position)
        weather_damage = before2 - defender2.hp

        self.assertLess(weather_damage, normal_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Desert Weather [Errata]"
                and event.get("effect") == "fire_resist"
                for event in battle_weather.log
            )
        )

    def test_dreamspinner_errata_drains_sleeping_foes(self):
        move = MoveSpec(
            name="Dreamspinner [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Burst 3",
        )
        attacker_spec = _pokemon_spec("Spinner", abilities=["Dreamspinner [Errata]"], moves=[move])
        foe_spec = _pokemon_spec("Sleeper", moves=[move])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        defender_close = PokemonState(spec=foe_spec, controller_id="b", position=(2, 4), active=True)
        defender_far = PokemonState(spec=foe_spec, controller_id="b", position=(2, 7), active=True)
        defender_close.statuses.append({"name": "Sleep", "remaining": 3})
        defender_far.statuses.append({"name": "Sleep", "remaining": 3})
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": defender_close, "b-2": defender_far},
            grid=GridState(width=10, height=10),
        )
        before_close = defender_close.hp
        before_far = defender_far.hp
        before_temp = attacker.temp_hp
        battle.resolve_move_targets("a-1", move, "a-1", attacker.position)
        self.assertEqual(before_close - defender_close.hp, defender_close.tick_value())
        self.assertEqual(before_far - defender_far.hp, 0)
        self.assertEqual(attacker.temp_hp, before_temp + attacker.tick_value())

    def test_drizzle_errata_sets_rain(self):
        move = MoveSpec(
            name="Drizzle [Errata]",
            type="Water",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Politoed", abilities=["Drizzle [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Clear"
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual(battle.weather, "Rain")

    def test_drought_errata_sets_sun(self):
        move = MoveSpec(
            name="Drought [Errata]",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Torkoal", abilities=["Drought [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Clear"
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual(battle.weather, "Sunny")

    def test_drown_out_errata_blocks_sonic_twice(self):
        move = MoveSpec(
            name="Uproar",
            type="Normal",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            keywords=["Sonic"],
        )
        attacker_spec = _pokemon_spec("Singer", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Drowner", abilities=["Drown Out [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 80)

        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(before - battle.pokemon[defender_id].hp, 0)
        self.assertEqual(
            battle.pokemon[defender_id].get_temporary_effects("drown_out_errata_used")[0].get("count"),
            1,
        )

        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(before - battle.pokemon[defender_id].hp, 0)
        self.assertEqual(
            battle.pokemon[defender_id].get_temporary_effects("drown_out_errata_used")[0].get("count"),
            2,
        )

        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(before - battle.pokemon[defender_id].hp, 0)

    def test_dust_cloud_errata_expands_powder_moves(self):
        move = MoveSpec(
            name="Test Powder",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            effects_text="The target falls Asleep on 16+.",
            keywords=["Powder"],
        )
        attacker_spec = _pokemon_spec("Dusty", abilities=["Dust Cloud [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].position = (2, 3)
        extra = PokemonState(
            spec=_pokemon_spec("Extra", moves=[move]),
            controller_id="b",
            position=(3, 2),
            active=True,
        )
        battle.pokemon["b-2"] = extra
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Sleep"))
        self.assertTrue(extra.has_status("Sleep"))

    def test_early_bird_errata_grants_initiative_bonus(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        errata_spec = _pokemon_spec("Bird", abilities=["Early Bird [Errata]"], moves=[move], spd=10)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(errata_spec, defender_spec)
        entry = battle._initiative_entry_for_pokemon(attacker_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.total, entry.speed + 5)

    def test_early_bird_errata_adds_sleep_save_bonus(self):
        spec = _pokemon_spec("Bird", abilities=["Early Bird [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.rng = SequenceRNG([10])
        status_entry = {"name": "Sleep", "remaining": 1}
        events = mon.sleep_save_events(battle, "a-1", status_entry, "Sleep")
        self.assertTrue(events)
        self.assertEqual(events[0].get("total"), 13)

    def test_electrodash_errata_sprint_is_free(self):
        spec = _pokemon_spec("Runner", abilities=["Electrodash [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=4, height=4),
        )
        action = SprintAction(actor_id="a-1")
        action.validate(battle)
        self.assertEqual(action.action_type, ActionType.FREE)
        action.resolve(battle)
        self.assertTrue(mon.get_temporary_effects("sprint"))

    def test_electrodash_errata_clears_stuck_on_shift(self):
        spec = _pokemon_spec("Runner", abilities=["Electrodash [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(1, 1), active=True)
        mon.statuses.append({"name": "Stuck"})
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=4, height=4),
        )
        action = ShiftAction(actor_id="a-1", destination=(1, 2))
        action.validate(battle)
        action.resolve(battle)
        self.assertFalse(mon.has_status("Stuck"))

    def test_electrodash_errata_blocks_aoo_while_sprinting(self):
        spec = _pokemon_spec("Runner", abilities=["Electrodash [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(1, 1), active=True)
        foe_spec = _pokemon_spec("Foe")
        foe = PokemonState(spec=foe_spec, controller_id="b", position=(1, 2), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A"), "b": TrainerState(identifier="b", name="B")},
            pokemon={"a-1": mon, "b-1": foe},
            grid=GridState(width=4, height=4),
        )
        mon.add_temporary_effect("sprint")
        action = ShiftAction(actor_id="a-1", destination=(1, 0))
        action.validate(battle)
        action.resolve(battle)
        self.assertFalse(any(evt.get("type") == "attack_of_opportunity" for evt in battle.log))

    def test_flare_boost_errata_requires_burned(self):
        move = MoveSpec(
            name="Flare Boost [Errata]",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Boost", abilities=["Flare Boost [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("atk", 0), 0)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("spatk", 0), 0)

    def test_flare_boost_errata_grants_attack_boosts(self):
        move = MoveSpec(
            name="Flare Boost [Errata]",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Boost", abilities=["Flare Boost [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].statuses.append({"name": "Burned"})
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("atk"), 3)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("spatk"), 3)

    def test_flash_fire_errata_absorbs_and_boosts(self):
        fire = MoveSpec(
            name="Flame Burst",
            type="Fire",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[fire], types=["Fire"])
        defender_spec = _pokemon_spec("Houndour", abilities=["Flash Fire [Errata]"], moves=[fire], types=["Fire"])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, fire, defender_id, defender.position)
        self.assertEqual(defender.hp, before)
        self.assertEqual(defender.combat_stages.get("atk"), 1)

    def test_flower_gift_errata_requires_condition(self):
        move = MoveSpec(
            name="Flower Gift [Errata]",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Burst 2, Allies",
        )
        attacker_spec = _pokemon_spec("Flower", abilities=["Flower Gift [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertEqual(attacker.combat_stages.get("atk", 0), 0)
        self.assertEqual(attacker.combat_stages.get("spatk", 0), 0)

    def test_flower_gift_errata_boosts_user_and_allies(self):
        move = MoveSpec(
            name="Flower Gift [Errata]",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Burst 2, Allies",
        )
        attacker_spec = _pokemon_spec("Flower", abilities=["Flower Gift [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.add_temporary_effect("flower_gift_stats", stats=["atk", "spatk"])
        attacker.hp = max(1, attacker.max_hp_with_injuries() // 2 - 1)
        ally = PokemonState(
            spec=_pokemon_spec("Ally", moves=[move]),
            controller_id="a",
            position=(3, 2),
            active=True,
        )
        battle.pokemon["a-2"] = ally
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertEqual(attacker.combat_stages.get("atk"), 2)
        self.assertEqual(attacker.combat_stages.get("spatk"), 2)
        self.assertEqual(ally.combat_stages.get("atk"), 1)
        self.assertEqual(ally.combat_stages.get("spatk"), 1)

    def test_flower_power_errata_swaps_grass_category(self):
        move = MoveSpec(
            name="Leaf Blade",
            type="Grass",
            category="Physical",
            db=9,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Gardener", abilities=["Flower Power [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].add_temporary_effect("flower_power_choice", category="special")
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Flower Power [Errata]"
                and event.get("effect") == "category_swap"
                for event in battle.log
            )
        )

    def test_flower_veil_errata_blocks_within_five(self):
        move = MoveSpec(name="Growl", type="Normal", category="Status", db=0, ac=2)
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        grass_target = _pokemon_spec("Target", moves=[move], types=["Grass"])
        veil_spec = _pokemon_spec("Veil", abilities=["Flower Veil [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, grass_target)
        veil = PokemonState(
            spec=veil_spec,
            controller_id="b",
            position=(2, 8),
            active=True,
        )
        battle.pokemon["b-2"] = veil
        defender = battle.pokemon[defender_id]
        battle._apply_combat_stage(
            [],
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=defender,
            stat="atk",
            delta=-1,
            description="Test drop.",
            effect="test",
        )
        self.assertEqual(defender.combat_stages.get("atk", 0), 0)

    def test_flower_veil_errata_allows_drop_outside_five(self):
        move = MoveSpec(name="Growl", type="Normal", category="Status", db=0, ac=2)
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        grass_target = _pokemon_spec("Target", moves=[move], types=["Grass"])
        veil_spec = _pokemon_spec("Veil", abilities=["Flower Veil [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, grass_target)
        veil = PokemonState(
            spec=veil_spec,
            controller_id="b",
            position=(2, 9),
            active=True,
        )
        battle.pokemon["b-2"] = veil
        defender = battle.pokemon[defender_id]
        battle._apply_combat_stage(
            [],
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=defender,
            stat="atk",
            delta=-1,
            description="Test drop.",
            effect="test",
        )
        self.assertEqual(defender.combat_stages.get("atk"), -1)

    def test_fox_fire_errata_triggers_ember_followup(self):
        fox_fire = MoveSpec(
            name="Fox Fire [Errata]",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        strike = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[strike])
        defender_spec = _pokemon_spec("Fennekin", abilities=["Fox Fire [Errata]"], moves=[fox_fire, strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        battle.resolve_move_targets(defender_id, fox_fire, defender_id, defender.position)
        battle.resolve_move_targets(attacker_id, strike, defender_id, defender.position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Fox Fire [Errata]"
                and event.get("effect") == "followup"
                for event in battle.log
            )
        )
        fox_entries = defender.get_temporary_effects("fox_fire_errata")
        self.assertTrue(fox_entries)
        self.assertEqual(int(fox_entries[0].get("charges", 0) or 0), 2)

    def test_frisk_feb_errata_reveals_target(self):
        frisk = MoveSpec(
            name="Frisk [Feb Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Scout", abilities=["Frisk [Feb Errata]"], moves=[frisk])
        defender_spec = _pokemon_spec("Target", moves=[frisk])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, frisk, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Frisk [Feb Errata]"
                and event.get("effect") == "frisk"
                for event in battle.log
            )
        )

    def test_frisk_sumo_errata_adjacent_accuracy_bonus(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=6,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Scout", abilities=["Frisk [SuMo Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(0, 0), active=True)
        defender = PokemonState(spec=defender_spec, controller_id="b", position=(0, 1), active=True)
        hit_with_bonus = calculations.attack_hits(SequenceRNG([6]), attacker, defender, move)
        self.assertTrue(hit_with_bonus.get("hit"))

        attacker_no_ability = PokemonState(spec=_pokemon_spec("Scout", moves=[move]), controller_id="a", position=(0, 0), active=True)
        miss_without_bonus = calculations.attack_hits(SequenceRNG([6]), attacker_no_ability, defender, move)
        self.assertFalse(miss_without_bonus.get("hit"))

    def test_gale_wings_errata_priority_and_bonus(self):
        action = MoveSpec(
            name="Gale Wings [Errata]",
            type="Flying",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        move = MoveSpec(
            name="Gust",
            type="Flying",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Bird", abilities=["Gale Wings [Errata]"], moves=[action, move], spd=10, spatk=12)
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=10)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, action, attacker_id, battle.pokemon[attacker_id].position)
        battle.rng = SequenceRNG([15] * 40)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gale Wings [Errata]"
                and event.get("effect") == "priority"
                for event in battle.log
            )
        )

        base_spec = _pokemon_spec("Base", moves=[move], spd=10, spatk=12)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertEqual(errata_damage - base_damage, 5)

    def test_gore_errata_double_strike_and_push(self):
        action = MoveSpec(
            name="Gore [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        horn_attack = MoveSpec(
            name="Horn Attack",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Rhino",
            abilities=["Gore [Errata]"],
            moves=[action, horn_attack],
            atk=14,
        )
        defender_spec = _pokemon_spec("Target", moves=[horn_attack], hp_stat=20)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, action, attacker_id, battle.pokemon[attacker_id].position)
        battle.rng = SequenceRNG([15] * 40)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(
            attacker_id, horn_attack, defender_id, battle.pokemon[defender_id].position
        )
        errata_damage = before - battle.pokemon[defender_id].hp
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gore [Errata]"
                and event.get("effect") == "double_strike"
                for event in battle.log
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gore [Errata]"
                and event.get("effect") == "push"
                for event in battle.log
            )
        )

        base_spec = _pokemon_spec("Base", moves=[horn_attack], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, horn_attack, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertGreater(errata_damage, base_damage)

    def test_grass_pelt_errata_grants_temp_hp(self):
        action = MoveSpec(
            name="Grass Pelt [Errata]",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Clover", abilities=["Grass Pelt [Errata]"], moves=[action])
        defender_spec = _pokemon_spec("Target", moves=[action])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        before = attacker.temp_hp
        battle.resolve_move_targets(attacker_id, action, attacker_id, attacker.position)
        self.assertEqual(attacker.temp_hp, before + attacker.tick_value() * 2)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Grass Pelt [Errata]"
                and event.get("effect") == "temp_hp"
                for event in battle.log
            )
        )

    def test_grass_pelt_errata_reduces_damage_on_rough_grass(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=12)
        defender_spec = _pokemon_spec("Defender", abilities=["Grass Pelt [Errata]"], moves=[move], hp_stat=20)
        grid = GridState(width=2, height=2, tiles={(0, 0): {"type": "rough grass"}})
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(0, 1), active=True)
        defender = PokemonState(spec=defender_spec, controller_id="b", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": defender},
            grid=grid,
        )
        battle.rng = SequenceRNG([15] * 40)
        before = defender.hp
        battle.resolve_move_targets("a-1", move, "b-1", defender.position)
        reduced_damage = before - defender.hp
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Grass Pelt [Errata]"
                and event.get("effect") == "damage_reduction"
                for event in battle.log
            )
        )

        base_defender_spec = _pokemon_spec("Defender", moves=[move], hp_stat=20)
        base_attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(0, 1), active=True)
        base_defender = PokemonState(spec=base_defender_spec, controller_id="b", position=(0, 0), active=True)
        base_battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": base_attacker, "b-1": base_defender},
            grid=grid,
        )
        base_battle.rng = SequenceRNG([15] * 40)
        before_base = base_defender.hp
        base_battle.resolve_move_targets("a-1", move, "b-1", base_defender.position)
        base_damage = before_base - base_defender.hp
        self.assertEqual(base_damage - reduced_damage, 5)

    def test_heatproof_errata_resists_fire(self):
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Caster", moves=[move], spatk=12, types=["Fire"])
        errata_defender_spec = _pokemon_spec(
            "Target", abilities=["Heatproof [Errata]"], moves=[move], types=["Grass"], hp_stat=20
        )
        base_defender_spec = _pokemon_spec("Target", moves=[move], types=["Grass"], hp_stat=20)

        battle, attacker_id, defender_id = _build_battle(attacker_spec, errata_defender_spec)
        battle.rng = SequenceRNG([15] * 40)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Heatproof [Errata]"
                and event.get("effect") == "type_resist"
                for event in battle.log
            )
        )

        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, base_defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertLess(errata_damage, base_damage)

    def test_heatproof_errata_blocks_burn_damage(self):
        spec = _pokemon_spec("Hot", abilities=["Heatproof [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Burned"})
        mon.mark_action(ActionType.STANDARD, "Test")
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=4, height=4),
        )
        before = mon.hp
        events = mon._handle_status_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertEqual(mon.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Heatproof [Errata]"
                and event.get("effect") == "status_block"
                for event in events
            )
        )

    def test_heavy_metal_errata_adjusts_defense_and_speed(self):
        errata_spec = _pokemon_spec("Heavy", abilities=["Heavy Metal [Errata]"], defense=12, spd=10)
        base_spec = _pokemon_spec("Base", defense=12, spd=10)
        errata_mon = PokemonState(spec=errata_spec, controller_id="a", position=(0, 0), active=True)
        base_mon = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(
            calculations.defensive_stat(errata_mon, "physical"),
            calculations.defensive_stat(base_mon, "physical") + 2,
        )
        self.assertEqual(calculations.speed_stat(errata_mon), calculations.speed_stat(base_mon) - 2)
        self.assertEqual(errata_mon.weight_class(), base_mon.weight_class() + 2)

    def test_honey_paws_errata_ignores_food_buff_limit(self):
        trainer = TrainerState(identifier="a", name="A")
        spec = _pokemon_spec("Teddiursa", abilities=["Honey Paws [Errata]"])
        spec.items = [{"name": "Honey"}]
        mon = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0), active=True)
        mon.food_buffs = [{"name": "Digestion Buff", "effect": ""} for _ in range(3)]
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"a-1": mon})
        battle.queue_action(UseItemAction(actor_id="a-1", item_index=0, target_id="a-1"))
        battle.resolve_next_action()
        self.assertEqual(len(mon.food_buffs), 4)
        self.assertTrue(any(buff.get("item") == "Leftovers" for buff in mon.food_buffs))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Honey Paws [Errata]"
                for event in battle.log
            )
        )

    def test_huge_power_errata_adds_base_attack(self):
        errata_spec = _pokemon_spec("Buff", abilities=["Huge Power / Pure Power [Errata]"], atk=10, level=20)
        base_spec = _pokemon_spec("Base", atk=10, level=20)
        errata_mon = PokemonState(spec=errata_spec, controller_id="a", position=(0, 0), active=True)
        base_mon = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(
            calculations.offensive_stat(errata_mon, "physical"),
            calculations.offensive_stat(base_mon, "physical") + 7,
        )

    def test_hunger_switch_full_belly_accuracy_bonus(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=6,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Morpeko", abilities=["Hunger Switch"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(0, 0), active=True)
        defender = PokemonState(spec=defender_spec, controller_id="b", position=(0, 1), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A"), "b": TrainerState(identifier="b", name="B")},
            pokemon={"a-1": attacker, "b-1": defender},
            grid=GridState(width=4, height=4),
        )
        attacker.add_temporary_effect("hunger_switch_choice", mode="full")
        attacker._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        hit_with_bonus = calculations.attack_hits(SequenceRNG([6]), attacker, defender, move)
        self.assertTrue(hit_with_bonus.get("hit"))

        attacker_no_ability = PokemonState(spec=_pokemon_spec("Morpeko", moves=[move]), controller_id="a", position=(0, 0), active=True)
        miss_without_bonus = calculations.attack_hits(SequenceRNG([6]), attacker_no_ability, defender, move)
        self.assertFalse(miss_without_bonus.get("hit"))

    def test_hunger_switch_hangry_damage_bonus(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Morpeko", abilities=["Hunger Switch"], moves=[move], atk=12)
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=20)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.add_temporary_effect("hunger_switch_choice", mode="hangry")
        attacker._handle_ability_phase_effects(battle, TurnPhase.START, attacker_id)
        battle.rng = SequenceRNG([15] * 40)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Hunger Switch"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

        base_spec = _pokemon_spec("Base", moves=[move], atk=12)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertEqual(errata_damage - base_damage, 5)

    def test_hustle_errata_penalizes_all_accuracy(self):
        class FixedRNG(random.Random):
            def randint(self, _a, _b):
                return 4

        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_with = PokemonState(
            spec=_pokemon_spec("Bagon", abilities=["Hustle [Errata]"], moves=[move]),
            controller_id="a",
            position=(0, 0),
            active=True,
        )
        defender = PokemonState(
            spec=_pokemon_spec("Target", moves=[move]),
            controller_id="b",
            position=(0, 1),
            active=True,
        )
        result_with = calculations.attack_hits(FixedRNG(), attacker_with, defender, move)

        attacker_without = PokemonState(
            spec=_pokemon_spec("Bagon", moves=[move]),
            controller_id="a",
            position=(0, 0),
            active=True,
        )
        result_without = calculations.attack_hits(FixedRNG(), attacker_without, defender, move)
        self.assertFalse(result_with.get("hit"))
        self.assertTrue(result_without.get("hit"))

    def test_hustle_errata_boosts_all_damage(self):
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Bagon", abilities=["Hustle [Errata]"], moves=[move], spatk=12)
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=20)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([15] * 40)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        errata_damage = before - battle.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move], spatk=12)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(
            attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position
        )
        base_damage = before_base - battle_base.pokemon[defender_base_id].hp
        self.assertEqual(errata_damage - base_damage, 10)

    def test_hydration_errata_cures_status(self):
        move = MoveSpec(
            name="Hydration [Errata]",
            type="Water",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Vaporeon", abilities=["Hydration [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.statuses.append({"name": "Burned"})
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertFalse(attacker.has_status("Burned"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Hydration [Errata]"
                and event.get("effect") == "cure"
                for event in battle.log
            )
        )

    def test_ice_body_errata_heals_under_half(self):
        spec = _pokemon_spec("Snorunt", abilities=["Ice Body [Errata]"], hp_stat=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=4, height=4),
        )
        mon.hp = max(1, mon.max_hp() // 2)
        events = mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Ice Body [Errata]"
                and event.get("effect") == "heal"
                for event in events
            )
        )

    def test_ice_body_errata_heals_in_hail(self):
        spec = _pokemon_spec("Snorunt", abilities=["Ice Body [Errata]"], hp_stat=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=4, height=4),
        )
        battle.weather = "Hail"
        mon.hp = max(1, mon.max_hp() - 1)
        events = mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Ice Body [Errata]"
                and event.get("effect") == "heal"
                for event in events
            )
        )

    def test_imposter_errata_interrupts_with_transform(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=12)
        defender_spec = _pokemon_spec("Ditto", abilities=["Imposter [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 40)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.get_temporary_effects("transformed"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Imposter [Errata]"
                and event.get("effect") == "transform_interrupt"
                for event in battle.log
            )
        )

    def test_gluttony_errata_food_buff_limit(self):
        spec = _pokemon_spec("Eater", abilities=["Gluttony [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.food_buffs = [{"name": "Test Buff", "effect": "Restores 5 HP."} for _ in range(4)]
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=4, height=4),
        )
        for _ in range(4):
            battle._consume_food_buff("a-1", mon, 0, "heal_fixed", "Restores 5 HP.", [])
        consumed = [entry for entry in mon.consumed_items if entry.get("kind") == "food_buff"]
        self.assertEqual(len(consumed), 3)
        self.assertEqual(len(mon.food_buffs), 1)

    def test_filter_errata_reduces_super_effective_damage(self):
        move = MoveSpec(
            name="Flame Burst",
            type="Fire",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14, types=["Fire"])
        base_defender_spec = _pokemon_spec("Target", moves=[move], types=["Grass"])
        errata_defender_spec = _pokemon_spec("Target", abilities=["Filter [Errata]"], moves=[move], types=["Grass"])

        battle_base, attacker_id, defender_id = _build_battle(attacker_spec, base_defender_spec)
        battle_base.rng = SequenceRNG([20] + [3] * 40)
        before_base = battle_base.pokemon[defender_id].hp
        battle_base.resolve_move_targets(attacker_id, move, defender_id, battle_base.pokemon[defender_id].position)
        base_damage = before_base - battle_base.pokemon[defender_id].hp

        battle_errata, attacker_id2, defender_id2 = _build_battle(attacker_spec, errata_defender_spec)
        battle_errata.rng = SequenceRNG([20] + [3] * 40)
        before_errata = battle_errata.pokemon[defender_id2].hp
        battle_errata.resolve_move_targets(attacker_id2, move, defender_id2, battle_errata.pokemon[defender_id2].position)
        errata_damage = before_errata - battle_errata.pokemon[defender_id2].hp

        self.assertEqual(base_damage - errata_damage, 5)


if __name__ == "__main__":
    unittest.main()
