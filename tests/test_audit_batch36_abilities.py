import copy
import random
import unittest
from unittest import mock

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase, UseMoveAction
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


class AuditBatch36AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_power_spot_boosts_ally_damage(self):
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
        defender_spec = _pokemon_spec("Target", moves=[move])

        battle_plain, a_id, d_id = _build_battle(attacker_spec, defender_spec)
        battle_plain.rng = SequenceRNG([20] + [3] * 50)
        before = battle_plain.pokemon[d_id].hp
        battle_plain.resolve_move_targets(a_id, move, d_id, battle_plain.pokemon[d_id].position)
        normal_damage = before - battle_plain.pokemon[d_id].hp

        battle_power, a2, d2 = _build_battle(attacker_spec, defender_spec)
        power_spot = PokemonState(
            spec=_pokemon_spec("Duraludon", ability="Power Spot", moves=[move]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle_power.pokemon["a-2"] = power_spot
        battle_power.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle_power.pokemon[d2].hp
        battle_power.resolve_move_targets(a2, move, d2, battle_power.pokemon[d2].position)
        boosted_damage = before2 - battle_power.pokemon[d2].hp

        self.assertGreater(boosted_damage, normal_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Power Spot"
                and event.get("effect") == "damage_bonus"
                for event in battle_power.log
            )
        )

    def test_prankster_grants_status_priority(self):
        growl = MoveSpec(
            name="Growl",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Imp", ability="Prankster", moves=[growl])
        defender_spec = _pokemon_spec("Target", moves=[growl])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)

        captured = []
        original = copy.deepcopy

        def spy(obj):
            cloned = original(obj)
            if isinstance(cloned, MoveSpec) and cloned.name == "Growl":
                captured.append(cloned)
            return cloned

        with mock.patch("auto_ptu.rules.battle_state.copy.deepcopy", side_effect=spy):
            battle.resolve_move_targets(attacker_id, growl, defender_id, battle.pokemon[defender_id].position)

        self.assertTrue(any((move.priority or 0) > 0 for move in captured))

    def test_pressure_increases_frequency_usage(self):
        move = MoveSpec(
            name="Quick Attack",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            freq="Scene",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Defender", ability="Pressure", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name="Quick Attack", target_id=defender_id)
        action.resolve(battle)
        usage = battle.frequency_usage.get(attacker_id, {}).get("Quick Attack", 0)
        self.assertEqual(usage, 2)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Pressure"
                and event.get("effect") == "pressure"
                for event in battle.log
            )
        )

    def test_pride_raises_spatk_when_afflicted(self):
        spec = _pokemon_spec("Prideful", ability="Pride")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Burned"})
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        events = mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("spatk"), 2)
        self.assertTrue(
            any(
                event.get("type") == "combat_stage"
                and event.get("effect") == "pride"
                for event in events
            )
        )

    def test_prime_fury_errata_raises_atk_and_spatk(self):
        prime = MoveSpec(
            name="Prime Fury [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Rager", abilities=["Prime Fury [Errata]"], moves=[prime])
        defender_spec = _pokemon_spec("Target", moves=[prime])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, prime, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("atk"), 1)
        self.assertEqual(attacker.combat_stages.get("spatk"), 1)
        self.assertTrue(attacker.has_status("Enraged"))

    def test_propeller_tail_grants_sprint_and_lock(self):
        propeller = MoveSpec(
            name="Propeller Tail",
            type="Water",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Tails", ability="Propeller Tail", moves=[propeller])
        defender_spec = _pokemon_spec("Target", moves=[propeller])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, propeller, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.get_temporary_effects("sprint"))
        self.assertTrue(attacker.get_temporary_effects("no_intercept"))
        self.assertTrue(attacker.get_temporary_effects("target_lock"))

    def test_psionic_screech_converts_and_flinches(self):
        screech = MoveSpec(
            name="Psionic Screech",
            type="Psychic",
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
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Screech", ability="Psionic Screech", moves=[screech, strike], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        UseMoveAction(actor_id=attacker_id, move_name="Psionic Screech", target_id=attacker_id).resolve(battle)
        battle.log = []
        UseMoveAction(actor_id=attacker_id, move_name="Tackle", target_id=defender_id).resolve(battle)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Flinch"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Psionic Screech"
                and event.get("effect") == "type_shift"
                for event in battle.log
            )
        )

    def test_pumpkingrab_bonus_grapple_contest(self):
        grapple = MoveSpec(
            name="Grapple",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pumpkin", ability="Pumpkingrab", moves=[grapple])
        defender_spec = _pokemon_spec("Target", moves=[grapple])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([10, 12])
        events = []
        battle._apply_grapple_contest(
            events,
            attacker_id=attacker_id,
            target_id=defender_id,
            move=grapple,
            attacker=battle.pokemon[attacker_id],
            defender=battle.pokemon[defender_id],
            effect="grapple",
            description="Grapple contest",
        )
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.get_temporary_effects("grapple_link"))
        self.assertTrue(
            any(event.get("effect") == "wrap_tick" for event in events)
        )

    def test_pumpkingrab_errata_grapples(self):
        pump = MoveSpec(
            name="Pumpkingrab [Errata]",
            type="Ghost",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pumpkin", abilities=["Pumpkingrab [Errata]"], moves=[pump])
        defender_spec = _pokemon_spec("Target", moves=[pump])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, pump, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        self.assertTrue(attacker.has_status("Grappled"))
        self.assertTrue(defender.has_status("Grappled"))
        self.assertTrue(attacker.has_status("Vulnerable"))
        self.assertTrue(defender.has_status("Vulnerable"))

    def test_pure_blooded_boosts_dragon_damage_low_hp(self):
        move = MoveSpec(
            name="Dragon Claw",
            type="Dragon",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Dragon", ability="Pure Blooded", moves=[move], atk=14, types=["Dragon"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() // 3)
        battle.rng = SequenceRNG([20] + [3] * 50)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        boosted = before - battle.pokemon[defender_id].hp

        normal_spec = _pokemon_spec("Normal", moves=[move], atk=14, types=["Dragon"])
        battle2, a2, d2 = _build_battle(normal_spec, defender_spec)
        battle2.pokemon[a2].hp = max(1, battle2.pokemon[a2].max_hp() // 3)
        battle2.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle2.pokemon[d2].hp
        battle2.resolve_move_targets(a2, move, d2, battle2.pokemon[d2].position)
        normal = before2 - battle2.pokemon[d2].hp

        self.assertGreater(boosted, normal)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Pure Blooded"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )
