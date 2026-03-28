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


class AuditBatch43AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_sprint_grants_sprint_effect(self):
        sprint = MoveSpec(
            name="Sprint",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Runner", ability="Sprint", moves=[sprint])
        defender_spec = _pokemon_spec("Target", moves=[sprint])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, sprint, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("sprint"))

    def test_sprint_errata_grants_sprint_effect(self):
        sprint = MoveSpec(
            name="Sprint [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Runner", abilities=["Sprint [Errata]"], moves=[sprint])
        defender_spec = _pokemon_spec("Target", moves=[sprint])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, sprint, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("sprint"))

    def test_stakeout_adds_damage_against_newcomer(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Hunter", ability="Stakeout", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_stake, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_stake.pokemon[defender_id].add_temporary_effect("joined_round", round=battle_stake.round + 1)
        battle_stake.rng = SequenceRNG([19, 6, 6] + [3] * 20)
        before = battle_stake.pokemon[defender_id].hp
        battle_stake.resolve_move_targets(attacker_id, move, defender_id, battle_stake.pokemon[defender_id].position)
        damage_stake = before - battle_stake.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Hunter", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19, 6, 6] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_stake, damage_base)

    def test_stall_reduces_priority(self):
        move = MoveSpec(
            name="Quick Attack",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            priority=2,
        )
        attacker_spec = _pokemon_spec("Slow", ability="Stall", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        effective = battle._apply_move_priority_overrides(attacker_id, move)
        self.assertLess(effective, move.priority)

    def test_stalwart_raises_stats_after_damage(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Defender", ability="Stalwart", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("atk"), 1)
        self.assertEqual(defender.combat_stages.get("spatk"), 1)

    def test_stance_change_switches_on_attack(self):
        move = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        stance = MoveSpec(
            name="Stance Change",
            type="Steel",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Aegis", ability="Stance Change", moves=[stance, move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Stance Change"
                and event.get("effect") == "stance"
                for event in battle.log
            )
        )

    def test_starlight_confuses_on_luminous_hit(self):
        starlight = MoveSpec(
            name="Starlight",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        strike = MoveSpec(
            name="Dazzling Gleam",
            type="Fairy",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Star", ability="Starlight", moves=[starlight, strike], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, starlight, attacker_id, battle.pokemon[attacker_id].position)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, strike, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Confused"))

    def test_starlight_errata_grants_defensive_buff(self):
        starlight = MoveSpec(
            name="Starlight [Errata]",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Star", abilities=["Starlight [Errata]"], moves=[starlight])
        defender_spec = _pokemon_spec("Target", moves=[starlight])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, starlight, attacker_id, battle.pokemon[attacker_id].position)
        battle.resolve_move_targets(attacker_id, starlight, attacker_id, battle.pokemon[attacker_id].position)
        bonus = battle.pokemon[attacker_id].get_temporary_effects("evasion_bonus")
        self.assertTrue(any(entry.get("amount") == 2 for entry in bonus))

    def test_starswirl_cleans_hazards(self):
        starswirl = MoveSpec(
            name="Starswirl",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Swirl", ability="Starswirl", moves=[starswirl])
        defender_spec = _pokemon_spec("Target", moves=[starswirl])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.grid.tiles[(2, 2)] = {"hazards": ["spikes"]}
        battle.resolve_move_targets(attacker_id, starswirl, attacker_id, battle.pokemon[attacker_id].position)
        self.assertNotIn("hazards", battle.grid.tiles[(2, 2)])

    def test_starswirl_errata_cleans_hazards_and_cures(self):
        starswirl = MoveSpec(
            name="Starswirl [Errata]",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Swirl", abilities=["Starswirl [Errata]"], moves=[starswirl])
        defender_spec = _pokemon_spec("Target", moves=[starswirl])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.grid.tiles[(2, 2)] = {"hazards": ["spikes"]}
        battle.pokemon[attacker_id].statuses.append({"name": "Poisoned"})
        battle.resolve_move_targets(attacker_id, starswirl, attacker_id, battle.pokemon[attacker_id].position)
        self.assertNotIn("hazards", battle.grid.tiles[(2, 2)])
        self.assertFalse(battle.pokemon[attacker_id].statuses)
