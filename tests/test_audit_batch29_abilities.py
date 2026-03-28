import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, calculations
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
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch29AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_electrodash_grants_sprint(self):
        move = MoveSpec(
            name="Electrodash",
            type="Electric",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Elec", ability="Electrodash", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("sprint"))

    def test_emergency_exit_switches_below_half(self):
        move = MoveSpec(
            name="Strike",
            type="Normal",
            category="Physical",
            db=3,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=12)
        defender_spec = _pokemon_spec("Golisopod", ability="Emergency Exit", moves=[move], hp_stat=2, defense=12)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        replacement = PokemonState(
            spec=_pokemon_spec("Bench", moves=[move]),
            controller_id="b",
            position=None,
            active=False,
        )
        battle.pokemon["b-2"] = replacement
        defender = battle.pokemon[defender_id]
        defender.hp = defender.max_hp() // 2 + 1
        battle.rng = SequenceRNG([20, 1, 1, 1, 1])
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertFalse(defender.active)
        self.assertTrue(replacement.active)
        self.assertEqual(replacement.position, (2, 3))

    def test_filter_reduces_super_effective_damage(self):
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
        defender_spec = _pokemon_spec("Grass", moves=[move], types=["Grass"])
        filter_spec = _pokemon_spec("Grass", ability="Filter", moves=[move], types=["Grass"])

        battle_normal, a_id, d_id = _build_battle(attacker_spec, defender_spec)
        battle_normal.rng = SequenceRNG([20] + [3] * 50)
        before = battle_normal.pokemon[d_id].hp
        battle_normal.resolve_move_targets(a_id, move, d_id, battle_normal.pokemon[d_id].position)
        normal_damage = before - battle_normal.pokemon[d_id].hp

        battle_filter, a2_id, d2_id = _build_battle(attacker_spec, filter_spec)
        battle_filter.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle_filter.pokemon[d2_id].hp
        battle_filter.resolve_move_targets(a2_id, move, d2_id, battle_filter.pokemon[d2_id].position)
        filter_damage = before2 - battle_filter.pokemon[d2_id].hp

        self.assertLess(filter_damage, normal_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Filter"
                and event.get("effect") == "reduce_super"
                for event in battle_filter.log
            )
        )

    def test_flare_boost_raises_special_attack_when_burned(self):
        move = MoveSpec(
            name="Flamethrower",
            type="Fire",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        base_spec = _pokemon_spec("Base", moves=[move], types=["Fire"], spatk=12)
        boost_spec = _pokemon_spec("Boost", ability="Flare Boost", moves=[move], types=["Fire"], spatk=12)
        base = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        boosted = PokemonState(spec=boost_spec, controller_id="a", position=(0, 0), active=True)
        base.statuses.append({"name": "Burned"})
        boosted.statuses.append({"name": "Burned"})
        base_stat = calculations.offensive_stat(base, "special")
        boosted_stat = calculations.offensive_stat(boosted, "special")
        self.assertGreater(boosted_stat, base_stat)

    def test_flash_fire_absorbs_and_boosts(self):
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
        defender_spec = _pokemon_spec("Houndour", ability="Flash Fire", moves=[fire], types=["Fire"])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, fire, defender_id, defender.position)
        self.assertEqual(defender.hp, before)
        self.assertTrue(defender.get_temporary_effects("flash_fire"))
        battle.resolve_move_targets(defender_id, fire, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Flash Fire"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_flavorful_aroma_buffs_ally(self):
        move = MoveSpec(
            name="Aromatic Mist",
            type="Fairy",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 2, 1 Ally",
        )
        attacker_spec = _pokemon_spec("Chef", ability="Flavorful Aroma", moves=[move])
        ally_spec = _pokemon_spec("Ally", moves=[move])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="players")
        attacker = PokemonState(
            spec=attacker_spec,
            controller_id="a",
            position=(2, 2),
            active=True,
        )
        ally = PokemonState(
            spec=ally_spec,
            controller_id="b",
            position=(2, 3),
            active=True,
        )
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": ally},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets("a-1", move, "b-1", ally.position)
        self.assertTrue(ally.get_temporary_effects("accuracy_bonus"))
        self.assertTrue(ally.get_temporary_effects("damage_bonus"))

    def test_flower_gift_boosts_allies_in_sun(self):
        move = MoveSpec(
            name="Flower Gift",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Cherrim", ability="Flower Gift", moves=[move])
        ally_spec = _pokemon_spec("Ally", moves=[move])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="players")
        attacker = PokemonState(
            spec=attacker_spec,
            controller_id="a",
            position=(2, 2),
            active=True,
        )
        ally = PokemonState(
            spec=ally_spec,
            controller_id="b",
            position=(2, 3),
            active=True,
        )
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": ally},
            grid=GridState(width=10, height=10),
        )
        battle.weather = "Sunny"
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets("a-1", move, "b-1", ally.position)
        self.assertEqual(ally.combat_stages.get("atk"), 1)
        self.assertEqual(ally.combat_stages.get("spd"), 1)

    def test_flower_power_swaps_grass_move_category(self):
        move = MoveSpec(
            name="Leaf Blade",
            type="Grass",
            category="Physical",
            db=9,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Gardener", ability="Flower Power", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].add_temporary_effect("flower_power_choice", category="special")
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Flower Power"
                and event.get("effect") == "category_swap"
                for event in battle.log
            )
        )

    def test_flower_veil_blocks_stat_drop(self):
        move = MoveSpec(name="Growl", type="Normal", category="Status", db=0, ac=2)
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        grass_target = _pokemon_spec("Target", moves=[move], types=["Grass"])
        veil_spec = _pokemon_spec("Veil", ability="Flower Veil", moves=[move])
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
        self.assertEqual(defender.combat_stages.get("atk"), 0)

    def test_fox_fire_triggers_interrupt(self):
        fox_fire = MoveSpec(
            name="Fox Fire",
            type="Fire",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        strike = MoveSpec(
            name="Strike",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[strike])
        defender_spec = _pokemon_spec("Fennekin", ability="Fox Fire", moves=[fox_fire, strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(defender_id, fox_fire, defender_id, battle.pokemon[defender_id].position)
        battle.resolve_move_targets(attacker_id, strike, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Fox Fire"
                and event.get("effect") == "interrupt"
                for event in battle.log
            )
        )
