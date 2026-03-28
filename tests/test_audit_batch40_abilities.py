import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase
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


class AuditBatch40AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_shell_shield_errata_readies_withdraw_and_reduction(self):
        shell_shield = MoveSpec(
            name="Shell Shield [Errata]",
            type="Water",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Shelly", abilities=["Shell Shield [Errata]"], moves=[shell_shield])
        defender_spec = _pokemon_spec("Target", moves=[shell_shield])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, shell_shield, attacker_id, battle.pokemon[attacker_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.get_temporary_effects("shell_shield_ready"))
        reductions = [
            entry
            for entry in attacker.get_temporary_effects("damage_reduction")
            if entry.get("source") == "Shell Shield [Errata]"
        ]
        self.assertTrue(reductions)

    def test_shield_dust_blocks_post_damage_effects(self):
        move = MoveSpec(
            name="Ember Dust",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            effects_text="Burns on 18+.",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Dusty", ability="Shield Dust", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([18] + [3] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(battle.pokemon[defender_id].has_status("Burned"))

        base_battle, base_attacker, base_defender = _build_battle(attacker_spec, _pokemon_spec("Target", moves=[move]))
        base_battle.rng = SequenceRNG([18] + [3] * 50)
        base_battle.resolve_move_targets(base_attacker, move, base_defender, base_battle.pokemon[base_defender].position)
        self.assertTrue(base_battle.pokemon[base_defender].has_status("Burned"))

    def test_shields_down_switches_to_core_form(self):
        spec = _pokemon_spec("Minior", ability="Shields Down")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon.hp = mon.max_hp() // 2
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        effects = mon.get_temporary_effects("shields_down_form")
        self.assertTrue(effects)
        self.assertTrue(any(entry.get("form") == "core" for entry in effects))

    def test_silk_threads_slows_on_string_shot(self):
        move = MoveSpec(
            name="String Shot",
            type="Bug",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Spinner", ability="Silk Threads", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Slowed"))

    def test_silk_threads_errata_slows_on_string_shot(self):
        move = MoveSpec(
            name="String Shot",
            type="Bug",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Spinner", abilities=["Silk Threads [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Slowed"))

    def test_simple_doubles_combat_stage_changes(self):
        spec = _pokemon_spec("Simple", ability="Simple")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle._apply_combat_stage(
            [],
            attacker_id="a-1",
            target_id="a-1",
            move=MoveSpec(name="Growl", type="Normal", category="Status"),
            target=mon,
            stat="atk",
            delta=1,
            effect="test",
            description="test",
        )
        self.assertEqual(mon.combat_stages.get("atk"), 2)

    def test_slow_start_applies_stat_scalars(self):
        spec = _pokemon_spec("Regi", ability="Slow Start", atk=14, spd=12)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.add_temporary_effect("joined_round", round=1)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.round = 1
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        scalars = [entry for entry in mon.get_temporary_effects("stat_scalar") if entry.get("source") == "Slow Start"]
        reductions = [entry for entry in mon.get_temporary_effects("damage_reduction") if entry.get("source") == "Slow Start"]
        self.assertTrue(scalars)
        self.assertTrue(reductions)

    def test_slush_rush_doubles_speed_in_hail(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        spec = _pokemon_spec("Frost", ability="Slush Rush", moves=[move], spd=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Hail"
        entry_hail = battle._initiative_entry_for_pokemon("a-1")

        base_battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)},
            grid=GridState(width=6, height=6),
        )
        entry_base = base_battle._initiative_entry_for_pokemon("a-1")
        self.assertGreater(entry_hail.total, entry_base.total)

    def _run_sniper_comparison(self, ability_name):
        move = MoveSpec(
            name="Night Slash",
            type="Dark",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            crit_range=20,
        )
        attacker_spec = _pokemon_spec("Shooter", abilities=[ability_name], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_sniper, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_sniper.rng = SequenceRNG([20, 6, 6, 6, 6, 6, 6])
        before = battle_sniper.pokemon[defender_id].hp
        battle_sniper.resolve_move_targets(attacker_id, move, defender_id, battle_sniper.pokemon[defender_id].position)
        damage_sniper = before - battle_sniper.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("Shooter", moves=[move], atk=14)
        battle_base, base_attacker_id, base_defender_id = _build_battle(base_attacker, defender_spec)
        battle_base.rng = SequenceRNG([20, 6, 6, 6, 6, 6, 6])
        before_base = battle_base.pokemon[base_defender_id].hp
        battle_base.resolve_move_targets(base_attacker_id, move, base_defender_id, battle_base.pokemon[base_defender_id].position)
        damage_base = before_base - battle_base.pokemon[base_defender_id].hp

        self.assertGreater(damage_sniper, damage_base)

    def test_sniper_boosts_critical_damage(self):
        self._run_sniper_comparison("Sniper")

    def test_sniper_errata_boosts_critical_damage(self):
        self._run_sniper_comparison("Sniper [Errata]")
