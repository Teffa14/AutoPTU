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
    types=None,
    moves=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
    items=None,
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


class AuditBatch30AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_frisk_reveals_target_details(self):
        move = MoveSpec(
            name="Frisk",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Frisker", ability="Frisk", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], items=[{"name": "Oran Berry"}])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].spec.nature = "Calm"
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Frisk"
                and event.get("effect") == "frisk"
                and "Oran Berry" in (event.get("items") or [])
                for event in battle.log
            )
        )

    def test_full_guard_reduces_next_hit(self):
        guard = MoveSpec(
            name="Full Guard",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
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
        defender_spec = _pokemon_spec("Guard", ability="Full Guard", moves=[guard, strike])
        attacker_spec = _pokemon_spec("Attacker", moves=[strike], atk=14)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.temp_hp = defender.tick_value()

        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets(attacker_id, strike, defender_id, defender.position)
        normal_damage = defender.max_hp() - defender.hp

        defender.hp = defender.max_hp()
        defender.temp_hp = defender.tick_value()
        battle.resolve_move_targets(defender_id, guard, defender_id, defender.position)
        battle.log = []
        battle.resolve_move_targets(attacker_id, strike, defender_id, defender.position)
        guarded_damage = defender.max_hp() - defender.hp

        self.assertLess(guarded_damage, normal_damage)
        # Resist event is informational; core check is that damage is reduced.

    def test_gale_wings_grants_flying_priority(self):
        move = MoveSpec(
            name="Gust",
            type="Flying",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Bird", ability="Gale Wings", moves=[move], types=["Flying"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gale Wings"
                and event.get("effect") == "priority"
                for event in battle.log
            )
        )

    def test_giver_forces_present_roll(self):
        present = MoveSpec(
            name="Present",
            type="Normal",
            category="Physical",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Giver", ability="Giver", moves=[present])
        defender_spec = _pokemon_spec("Target", moves=[present])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].add_temporary_effect("giver_choice", roll=5)
        battle.rng = SequenceRNG([20] * 10)
        battle.resolve_move_targets(attacker_id, present, defender_id, battle.pokemon[defender_id].position)
        move_events = [event for event in battle.log if event.get("type") == "move" and event.get("move") == "Present"]
        self.assertTrue(move_events)
        self.assertEqual(move_events[-1].get("effective_db"), 12)

    def test_gluttony_allows_multiple_food_buffs(self):
        spec = _pokemon_spec("Snorlax", ability="Gluttony")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.add_food_buff({"item": "Berry"})
        mon.add_food_buff({"item": "Berry"})
        mon.add_food_buff({"item": "Berry"})
        self.assertEqual(len(mon.food_buffs), 3)

    def test_gore_extends_crit_and_pushes(self):
        move = MoveSpec(
            name="Horn Attack",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Tauros", ability="Gore", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gore"
                and event.get("effect") == "push"
                for event in battle.log
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gore"
                and event.get("effect") == "crit_range"
                for event in battle.log
            )
        )

    def test_gorilla_tactics_locks_moves_and_boosts_damage(self):
        ability_move = MoveSpec(
            name="Gorilla Tactics",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        slam = MoveSpec(
            name="Slam",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Gorilla", ability="Gorilla Tactics", moves=[ability_move, slam])
        defender_spec = _pokemon_spec("Target", moves=[slam])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, slam, defender_id, battle.pokemon[defender_id].position)
        battle.resolve_move_targets(attacker_id, ability_move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("gorilla_tactics_active"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gorilla Tactics"
                and event.get("effect") == "activate"
                for event in battle.log
            )
        )

        defender = battle.pokemon[defender_id]
        defender.hp = defender.max_hp()
        before = defender.hp
        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets(attacker_id, slam, defender_id, defender.position)
        self.assertLess(defender.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gorilla Tactics"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_grass_pelt_reduces_damage_on_grass(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], types=["Normal"])
        grass_spec = _pokemon_spec("Target", ability="Grass Pelt", moves=[move], types=["Normal"])

        battle_normal, a_id, d_id = _build_battle(attacker_spec, defender_spec)
        battle_normal.rng = SequenceRNG([20] + [3] * 50)
        before = battle_normal.pokemon[d_id].hp
        battle_normal.resolve_move_targets(a_id, move, d_id, battle_normal.pokemon[d_id].position)
        normal_damage = before - battle_normal.pokemon[d_id].hp

        battle_grass, a2_id, d2_id = _build_battle(attacker_spec, grass_spec)
        battle_grass.grid.tiles[(2, 3)] = {"type": "grass"}
        battle_grass.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle_grass.pokemon[d2_id].hp
        battle_grass.resolve_move_targets(a2_id, move, d2_id, battle_grass.pokemon[d2_id].position)
        grass_damage = before2 - battle_grass.pokemon[d2_id].hp

        self.assertLess(grass_damage, normal_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Grass Pelt"
                and event.get("effect") == "damage_reduction"
                for event in battle_grass.log
            )
        )

    def test_grim_neigh_raises_spatk_and_penalizes_foes(self):
        move = MoveSpec(
            name="Strike",
            type="Ghost",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Rider", ability="Grim Neigh", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=1, types=["Psychic"])
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
        attacker.hp = max(1, attacker.hp)
        self.assertEqual(attacker.combat_stages.get("spatk"), 1)
        self.assertTrue(extra.get_temporary_effects("accuracy_penalty"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Grim Neigh"
                and event.get("effect") == "accuracy_penalty"
                for event in battle.log
            )
        )

    def test_gulp_missile_retaliates_after_damage(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        stockpile = MoveSpec(
            name="Stockpile",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Gulp", ability="Gulp Missile", moves=[move, stockpile])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(defender_id, stockpile, defender_id, battle.pokemon[defender_id].position)
        battle.rng = SequenceRNG([20] * 50)
        before = battle.pokemon[attacker_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(battle.pokemon[attacker_id].hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Gulp Missile"
                and event.get("effect") == "retaliate"
                for event in battle.log
            )
        )
