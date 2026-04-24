from __future__ import annotations

import copy
import math
import random
from collections import deque
from typing import List, Sequence

import unittest

from auto_ptu import ptu_engine
from auto_ptu.csv_repository import PTUCsvRepository
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import (
    ActionType,
    BattleState,
    DelayAction,
    EquipWeaponAction,
    GridState,
    InitiativeEntry,
    InterceptAction,
    PokemonState,
    CreativeAction,
    ShiftAction,
    SwitchAction,
    TrainerSwitchAction,
    WakeAllyAction,
    TradeStandardForAction,
    TrainerState,
    TurnPhase,
    UseItemAction,
    UseMoveAction,
    movement,
    targeting,
    ai as rules_ai,
)
from auto_ptu.rules import battle_state as battle_state_module
from auto_ptu.rules.calculations import (
    attack_hits,
    build_attack_context,
    _effective_db_components,
    defensive_stat,
    offensive_stat,
    evasion_value,
    speed_stat,
    stab_db,
)
from auto_ptu.rules.calculations import resolve_move_action
from auto_ptu.rules.hooks.item_hooks import ItemHookContext, apply_item_hooks


def _pokemon_spec(name: str = "Pikachu", *, size: str = "Medium") -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=["Electric"],
        size=size,
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=12,
        moves=[
            MoveSpec(name="Thunder Shock", type="Electric"),
        ],
    )


def _ptu_move_from_spec(move: MoveSpec) -> ptu_engine.Move:
    return ptu_engine.Move(
        name=move.name,
        type=move.type,
        category=move.category,
        db=move.db,
        ac=move.ac,
        range_kind=move.range_kind or "Melee",
        range_value=move.range_value,
        keywords=list(move.keywords),
        priority=move.priority,
        crit_range=move.crit_range,
        freq=move.freq,
        effects_text=move.effects_text,
    )


def _ptu_pokemon_from_spec(spec: PokemonSpec) -> ptu_engine.Pokemon:
    return ptu_engine.Pokemon(
        name=spec.name or spec.species,
        species=spec.species,
        level=spec.level,
        types=list(spec.types),
        hp_stat=spec.hp_stat,
        atk=spec.atk,
        def_=spec.defense,
        spatk=spec.spatk,
        spdef=spec.spdef,
        spd=spec.spd,
        accuracy_cs=spec.accuracy_cs,
        evasion_bonus_phys=spec.evasion_phys,
        evasion_bonus_spec=spec.evasion_spec,
        evasion_bonus_spd=spec.evasion_spd,
        capabilities=[],
        abilities=[],
        items=[],
        statuses=[],
        trainer_features=[],
        known_moves=[],
    )


def _contact_move_spec(name: str = "Tackle") -> MoveSpec:
    return MoveSpec(
        name=name,
        type="Normal",
        category="Physical",
        db=6,
        ac=None,
        range_kind="Melee",
        range_value=1,
        freq="At-Will",
    )


class SequenceRNG(random.Random):
    def __init__(self, values: Sequence[int]) -> None:
        super().__init__()
        self._values = deque(values)

    def randint(self, a: int, b: int) -> int:
        if self._values:
            return self._values.popleft()
        return super().randint(a, b)


class MaxRNG(random.Random):
    def randint(self, _a: int, b: int) -> int:
        return b


class MinRNG(random.Random):
    def randint(self, a: int, _b: int) -> int:
        return a


def _advance_to_pokemon_turn(battle: BattleState) -> InitiativeEntry:
    entry = battle.advance_turn()
    while entry and entry.actor_id in battle.trainers:
        battle.end_turn()
        entry = battle.advance_turn()
    if entry is None:
        raise AssertionError("Expected an active Pokemon turn.")
    return entry


def _two_pokemon_battle(
    attacker_moves: Sequence[MoveSpec],
    defender_moves: Sequence[MoveSpec],
    *,
    attacker_species: str = "Machop",
    defender_species: str = "Wobbuffet",
    attacker_types: Sequence[str] | None = None,
    defender_types: Sequence[str] | None = None,
    attacker_spd: int = 12,
    defender_spd: int = 10,
    rng: random.Random | None = None,
) -> BattleState:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec(attacker_species)
    attacker_spec.types = list(attacker_types or ["Normal"])
    attacker_spec.spd = attacker_spd
    attacker_spec.moves = list(attacker_moves)
    defender_spec = _pokemon_spec(defender_species)
    defender_spec.types = list(defender_types or ["Normal"])
    defender_spec.spd = defender_spd
    defender_spec.moves = list(defender_moves)
    return BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier, position=(0, 0)),
            "gary-1": PokemonState(spec=defender_spec, controller_id=gary.identifier, position=(0, 1)),
        },
        rng=rng or SequenceRNG([20] * 20),
    )


class BattleStateTests(unittest.TestCase):
    def test_switch_action_swaps_active_combatant(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", position=(1, 1))
        active = _pokemon_spec("Pikachu")
        bench = _pokemon_spec("Bulbasaur")
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": PokemonState(spec=active, controller_id="ash", position=(1, 1), active=True),
                "ash-2": PokemonState(spec=bench, controller_id="ash", position=None, active=False),
            },
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(SwitchAction(actor_id="ash-1", replacement_id="ash-2"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].active)
        self.assertTrue(battle.pokemon["ash-2"].active)
        self.assertIsNone(battle.pokemon["ash-1"].position)
        self.assertEqual(battle.pokemon["ash-2"].position, (1, 1))

    def test_switch_action_places_replacement_within_trainer_throw_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", position=(0, 0))
        active = _pokemon_spec("Pikachu")
        bench = _pokemon_spec("Bulbasaur")
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": PokemonState(spec=active, controller_id="ash", position=(5, 5), active=True),
                "ash-2": PokemonState(spec=bench, controller_id="ash", position=None, active=False),
            },
            grid=GridState(width=8, height=8),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(SwitchAction(actor_id="ash-1", replacement_id="ash-2"))
        battle.resolve_next_action()
        replacement_pos = battle.pokemon["ash-2"].position
        self.assertIsNotNone(replacement_pos)
        self.assertNotEqual(replacement_pos, (5, 5))
        self.assertLessEqual(
            targeting.footprint_distance((0, 0), "Medium", replacement_pos, "Medium", battle.grid),
            4,
        )

    def test_switch_action_rejects_explicit_tile_outside_throw_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", position=(0, 0))
        active = _pokemon_spec("Pikachu")
        bench = _pokemon_spec("Bulbasaur")
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": PokemonState(spec=active, controller_id="ash", position=(1, 1), active=True),
                "ash-2": PokemonState(spec=bench, controller_id="ash", position=None, active=False),
            },
            grid=GridState(width=8, height=8),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        with self.assertRaises(ValueError):
            battle.queue_action(
                SwitchAction(
                    actor_id="ash-1",
                    replacement_id="ash-2",
                    target_position=(7, 7),
                )
            )

    def test_blessing_move_cannot_target_enemy(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        caster = _pokemon_spec("MrMime")
        caster.moves = [MoveSpec(name="Light Screen", type="Psychic", category="Status", range_kind="Blessing", range_value=0)]
        battle = BattleState(
            trainers={"ash": trainer, "gary": foe},
            pokemon={
                "ash-1": PokemonState(spec=caster, controller_id="ash", position=(0, 0), active=True),
                "gary-1": PokemonState(spec=_pokemon_spec("Machop"), controller_id="gary", position=(1, 0), active=True),
            },
            grid=GridState(width=4, height=4),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        with self.assertRaises(ValueError):
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Light Screen", target_id="gary-1"))

    def test_creative_action_rolls_skill_check_and_logs_result(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[_contact_move_spec("Tackle")],
            defender_moves=[_contact_move_spec("Tackle")],
            rng=SequenceRNG([14]),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        actor = battle.pokemon["ash-1"]
        actor.spec.skills["athletics"] = 4

        battle.queue_action(
            CreativeAction(
                actor_id="ash-1",
                title="Vault Past Cover",
                description="Leap over debris to threaten the defender.",
                skill="athletics",
                dc=12,
                capability="",
            )
        )
        battle.resolve_next_action()

        event = next(evt for evt in reversed(battle.log) if evt.get("type") == "creative_action")
        self.assertEqual(event["title"], "Vault Past Cover")
        self.assertEqual(event["skill"], "athletics")
        self.assertEqual(event["dc"], 12)
        self.assertTrue(event["success"])

    def test_creative_action_supports_opposed_skill_checks(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[_contact_move_spec("Tackle")],
            defender_moves=[_contact_move_spec("Tackle")],
            rng=SequenceRNG([12, 5]),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.pokemon["ash-1"].spec.skills["acrobatics"] = 4
        battle.pokemon["gary-1"].spec.skills["acrobatics"] = 1

        battle.queue_action(
            CreativeAction(
                actor_id="ash-1",
                title="Outmaneuver",
                description="Slip around the foe with a sudden feint.",
                skill="acrobatics",
                target_id="gary-1",
                opposed_skill="acrobatics",
            )
        )
        battle.resolve_next_action()

        event = next(evt for evt in reversed(battle.log) if evt.get("type") == "creative_action")
        self.assertTrue(event["success"])
        self.assertEqual(event["opposed_check"]["target"], "gary-1")
        self.assertEqual(event["opposed_check"]["skill"], "acrobatics")

    def test_creative_action_explicit_opposed_check_mode(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[_contact_move_spec("Tackle")],
            defender_moves=[_contact_move_spec("Tackle")],
            rng=SequenceRNG([11, 7]),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.pokemon["ash-1"].spec.skills["focus"] = 3
        battle.pokemon["gary-1"].spec.skills["focus"] = 1

        battle.queue_action(
            CreativeAction(
                actor_id="ash-1",
                title="Hold the Line",
                description="Match wills to keep footing.",
                skill="focus",
                target_id="gary-1",
                opposed_skill="focus",
                check_mode="opposed",
            )
        )
        battle.resolve_next_action()

        event = next(evt for evt in reversed(battle.log) if evt.get("type") == "creative_action")
        self.assertEqual(event["check_mode"], "opposed")
        self.assertTrue(event["success"])
        self.assertEqual(event["opposed_check"]["skill"], "focus")

    def test_creative_action_can_trip_target_as_consequence(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[_contact_move_spec("Tackle")],
            defender_moves=[_contact_move_spec("Tackle")],
            rng=SequenceRNG([18]),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.pokemon["ash-1"].spec.skills["combat"] = 4

        battle.queue_action(
            CreativeAction(
                actor_id="ash-1",
                title="Hook the Ankle",
                description="Kick low to drop the foe.",
                skill="combat",
                dc=8,
                target_id="gary-1",
                consequence="trip_target",
            )
        )
        battle.resolve_next_action()

        self.assertTrue(battle.pokemon["gary-1"].has_status("Tripped"))
        event = next(evt for evt in reversed(battle.log) if evt.get("type") == "creative_action")
        self.assertEqual(event["consequence_applied"], "trip_target")

    def test_creative_action_can_grant_cover_as_damage_reduction(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[_contact_move_spec("Tackle")],
            defender_moves=[_contact_move_spec("Tackle")],
            rng=SequenceRNG([16]),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.pokemon["ash-1"].spec.skills["survival"] = 3

        battle.queue_action(
            CreativeAction(
                actor_id="ash-1",
                title="Duck Behind Rubble",
                description="Use battlefield debris as cover.",
                skill="survival",
                dc=8,
                consequence="grant_cover_self",
                consequence_value=7,
            )
        )
        battle.resolve_next_action()

        reductions = battle.pokemon["ash-1"].get_temporary_effects("damage_reduction")
        self.assertTrue(any(int(entry.get("amount", 0) or 0) == 7 for entry in reductions))

    def test_creative_action_can_reposition_actor(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[_contact_move_spec("Tackle")],
            defender_moves=[_contact_move_spec("Tackle")],
            rng=SequenceRNG([17]),
        )
        battle.grid = GridState(width=5, height=5)
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.pokemon["ash-1"].spec.skills["acrobatics"] = 4

        battle.queue_action(
            CreativeAction(
                actor_id="ash-1",
                title="Swing to Flank",
                description="Use terrain to reposition.",
                skill="acrobatics",
                dc=8,
                target_position=(1, 1),
                consequence="self_reposition",
            )
        )
        battle.resolve_next_action()

        self.assertEqual(battle.pokemon["ash-1"].position, (1, 1))

    def test_creative_action_can_push_target_to_selected_tile(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[_contact_move_spec("Tackle")],
            defender_moves=[_contact_move_spec("Tackle")],
            rng=SequenceRNG([17, 8]),
        )
        battle.grid = GridState(width=6, height=6)
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.pokemon["ash-1"].spec.skills["athletics"] = 4
        battle.pokemon["gary-1"].spec.skills["athletics"] = 1

        battle.queue_action(
            CreativeAction(
                actor_id="ash-1",
                title="Shoulder Check",
                description="Win the contest and shove the foe aside.",
                skill="athletics",
                target_id="gary-1",
                target_position=(1, 2),
                opposed_skill="athletics",
                check_mode="opposed",
                consequence="push_target",
            )
        )
        battle.resolve_next_action()

        self.assertEqual(battle.pokemon["gary-1"].position, (1, 2))
        event = next(evt for evt in reversed(battle.log) if evt.get("type") == "creative_action")
        self.assertEqual(event["consequence_applied"], "push_target")

    def test_regenerator_heals_on_switch(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        active = _pokemon_spec("Slowpoke")
        active.abilities = [{"name": "Regenerator"}]
        bench = _pokemon_spec("Bulbasaur")
        active_state = PokemonState(spec=active, controller_id="ash", position=(1, 1), active=True)
        bench_state = PokemonState(spec=bench, controller_id="ash", position=None, active=False)
        active_state.hp = max(1, active_state.max_hp() // 2)
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={"ash-1": active_state, "ash-2": bench_state},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        before = active_state.hp
        heal_amount = max(1, active_state.max_hp() // 3)
        battle.queue_action(SwitchAction(actor_id="ash-1", replacement_id="ash-2"))
        battle.resolve_next_action()
        self.assertEqual(active_state.hp, min(active_state.max_hp(), before + heal_amount))
        self.assertTrue(any(evt.get("ability") == "Regenerator" for evt in battle.log))

    def test_switch_action_blocked_when_trapped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        active = _pokemon_spec("Pikachu")
        bench = _pokemon_spec("Bulbasaur")
        active_state = PokemonState(spec=active, controller_id="ash", position=(0, 0), active=True)
        active_state.statuses.append({"name": "Trapped"})
        bench_state = PokemonState(spec=bench, controller_id="ash", position=None, active=False)
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": active_state,
                "ash-2": bench_state,
            },
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        with self.assertRaises(ValueError):
            battle.queue_action(SwitchAction(actor_id="ash-1", replacement_id="ash-2"))

    def test_intercept_loyalty_blocks_other_trainer(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", team="players")
        ally_trainer = TrainerState(identifier="misty", name="Misty", team="players")
        interceptor_spec = _pokemon_spec("Pikachu")
        interceptor_spec.spd = 20
        interceptor_spec.loyalty = 4
        ally_spec = _pokemon_spec("Eevee")
        ally_spec.spd = 5
        interceptor = PokemonState(
            spec=interceptor_spec,
            controller_id=trainer.identifier,
            position=(0, 0),
        )
        ally = PokemonState(
            spec=ally_spec,
            controller_id=ally_trainer.identifier,
            position=(1, 0),
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, ally_trainer.identifier: ally_trainer},
            pokemon={"ash-1": interceptor, "misty-1": ally},
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "ash-1")
        with self.assertRaises(ValueError):
            battle.queue_action(InterceptAction(actor_id="ash-1", kind="melee", ally_id="misty-1"))

    def test_intercept_loyalty_allows_other_trainer(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", team="players")
        ally_trainer = TrainerState(identifier="misty", name="Misty", team="players")
        interceptor_spec = _pokemon_spec("Pikachu")
        interceptor_spec.spd = 20
        interceptor_spec.loyalty = 6
        ally_spec = _pokemon_spec("Eevee")
        ally_spec.spd = 5
        interceptor = PokemonState(
            spec=interceptor_spec,
            controller_id=trainer.identifier,
            position=(0, 0),
        )
        ally = PokemonState(
            spec=ally_spec,
            controller_id=ally_trainer.identifier,
            position=(1, 0),
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, ally_trainer.identifier: ally_trainer},
            pokemon={"ash-1": interceptor, "misty-1": ally},
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "ash-1")
        battle.queue_action(InterceptAction(actor_id="ash-1", kind="melee", ally_id="misty-1"))
        battle.resolve_next_action()
        self.assertTrue(interceptor.get_temporary_effects("intercept_ready"))

    def test_trainer_switch_inserts_replacement_in_full_contact(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        active = _pokemon_spec("Pikachu")
        active.spd = 10
        bench = _pokemon_spec("Bulbasaur")
        bench.spd = 12
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": PokemonState(spec=active, controller_id="ash", position=(0, 0), active=True),
                "ash-2": PokemonState(spec=bench, controller_id="ash", position=None, active=False),
            },
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "ash-1")
        battle.end_turn()
        trainer_entry = battle.advance_turn()
        self.assertEqual(trainer_entry.actor_id, "ash")
        action = TrainerSwitchAction(actor_id="ash", outgoing_id="ash-1", replacement_id="ash-2")
        battle.queue_action(action)
        battle.resolve_next_action()
        battle.end_turn()
        next_entry = battle.advance_turn()
        self.assertEqual(next_entry.actor_id, "ash-2")

    def test_trainer_switch_declares_and_blocks_turn_in_league(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        active = _pokemon_spec("Pikachu")
        active.spd = 6
        bench = _pokemon_spec("Bulbasaur")
        bench.spd = 12
        foe_mon = _pokemon_spec("Eevee")
        foe_mon.spd = 8
        battle = BattleState(
            trainers={"ash": trainer, "gary": foe},
            pokemon={
                "ash-1": PokemonState(spec=active, controller_id="ash", position=(0, 0), active=True),
                "ash-2": PokemonState(spec=bench, controller_id="ash", position=None, active=False),
                "gary-1": PokemonState(spec=foe_mon, controller_id="gary", position=(1, 0), active=True),
            },
            battle_context="league",
        )
        battle.start_round()
        entry = battle.advance_turn()
        self.assertEqual(entry.actor_id, "ash")
        action = TrainerSwitchAction(actor_id="ash", outgoing_id="ash-1", replacement_id="ash-2")
        battle.queue_action(action)
        self.assertTrue(battle.declared_actions)
        self.assertTrue(battle.pokemon["ash-1"].active)
        battle.end_turn()
        entry = battle.advance_turn()
        self.assertEqual(entry.actor_id, "gary")
        battle.end_turn()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "gary-1")
        self.assertTrue(battle.pokemon["ash-2"].active)
        self.assertFalse(battle.pokemon["ash-1"].active)

    def test_trainer_switch_respects_explicit_throw_tile(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", position=(0, 0), speed=1)
        active = _pokemon_spec("Pikachu")
        bench = _pokemon_spec("Bulbasaur")
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": PokemonState(spec=active, controller_id="ash", position=(0, 0), active=True),
                "ash-2": PokemonState(spec=bench, controller_id="ash", position=None, active=False),
            },
            grid=GridState(width=8, height=8),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "ash-1")
        battle.end_turn()
        trainer_entry = battle.advance_turn()
        self.assertEqual(trainer_entry.actor_id, "ash")
        action = TrainerSwitchAction(
            actor_id="ash",
            outgoing_id="ash-1",
            replacement_id="ash-2",
            target_position=(2, 2),
        )
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-2"].position, (2, 2))

    def test_trainer_switch_uses_shift_when_fainted(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        active = _pokemon_spec("Pikachu")
        bench = _pokemon_spec("Bulbasaur")
        active_state = PokemonState(spec=active, controller_id="ash", position=(0, 0), active=True)
        active_state.hp = 0
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": active_state,
                "ash-2": PokemonState(spec=bench, controller_id="ash", position=None, active=False),
            },
        )
        battle.start_round()
        entry = battle.advance_turn()
        if entry and entry.actor_id != "ash":
            battle.end_turn()
            entry = battle.advance_turn()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.actor_id, "ash")
        action = TrainerSwitchAction(actor_id="ash", outgoing_id="ash-1", replacement_id="ash-2")
        battle.queue_action(action)
        self.assertEqual(action.action_type, ActionType.SHIFT)

    def test_initiative_skips_inactive_bench(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="ash", position=(0, 0), active=True),
                "ash-2": PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id="ash", position=None, active=False),
            },
        )
        battle.start_round()
        order = [entry.actor_id for entry in battle.initiative_order]
        self.assertIn("ash-1", order)
        self.assertNotIn("ash-2", order)
    def test_trade_standard_grants_extra_shift(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        grid = GridState(width=5, height=5, blockers=set(), tiles={})
        actor = PokemonState(
            spec=_pokemon_spec("Pikachu"),
            controller_id="ash",
            position=(2, 2),
        )
        actor.spec.movement["overland"] = 3
        battle = BattleState(trainers={"ash": trainer}, pokemon={"ash-1": actor}, grid=grid)
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertIsNotNone(entry)
        battle.queue_action(TradeStandardForAction(actor_id="ash-1", target_action="shift"))
        battle.resolve_next_action()
        battle.queue_action(ShiftAction(actor_id="ash-1", destination=(2, 3)))
        battle.resolve_next_action()
        battle.queue_action(ShiftAction(actor_id="ash-1", destination=(2, 4)))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].position, (2, 4))

    def test_delay_moves_initiative_order(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        fast = _pokemon_spec("Rapidash")
        slow = _pokemon_spec("Slowpoke")
        fast.spd = 12
        slow.spd = 6
        battle = BattleState(
            trainers={"ash": trainer},
            pokemon={
                "fast-1": PokemonState(spec=fast, controller_id="ash", position=(0, 0)),
                "slow-1": PokemonState(spec=slow, controller_id="ash", position=(1, 0)),
            },
            rng=SequenceRNG([10, 10]),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "fast-1")
        battle.queue_action(DelayAction(actor_id="fast-1", target_total=4))
        battle.resolve_next_action()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "slow-1")

    def test_league_initiative_orders_trainers_before_pokemon(self) -> None:
        trainer_a = TrainerState(identifier="alice", name="Alice", speed=6)
        trainer_b = TrainerState(identifier="bob", name="Bob", speed=12)
        fighter = _pokemon_spec("Machop")
        fighter.spd = 10
        partner = _pokemon_spec("Mankey")
        partner.spd = 8
        battle = BattleState(
            trainers={"alice": trainer_a, "bob": trainer_b},
            pokemon={
                "alice-1": PokemonState(spec=fighter, controller_id="alice", position=(0, 0)),
                "bob-1": PokemonState(spec=partner, controller_id="bob", position=(1, 0)),
            },
            battle_context="league",
            rng=SequenceRNG([5, 6]),
        )
        battle.start_round()
        order = [entry.actor_id for entry in battle.initiative_order]
        self.assertEqual(order[:2], ["alice", "bob"])
        self.assertEqual(set(order[2:]), {"alice-1", "bob-1"})

    def test_setup_move_delays_resolution(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        solar_beam = MoveSpec(
            name="Solar Beam",
            type="Grass",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            range_text="Line 6, Set-Up",
            effects_text="Set-Up Effect: Charge. Resolution Effect: Fire Solar Beam.",
        )
        attacker_spec = _pokemon_spec("Bulbasaur")
        attacker_spec.moves = [solar_beam]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.rng = SequenceRNG([20, 20, 20])
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        action = UseMoveAction(actor_id="ash-1", move_name="Solar Beam", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertTrue(battle.has_pending_resolution("ash-1"))
        defender_before = battle.pokemon["gary-1"].hp
        self.assertIsNotNone(defender_before)
        battle.execute_pending_resolution("ash-1")
        self.assertLess(battle.pokemon["gary-1"].hp or 0, defender_before or 0)

    def test_double_strike_deals_two_hits(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        double_strike = MoveSpec(
            name="Double Kick",
            type="Fighting",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            range_text="Melee, 1 Target, Double Strike",
        )
        attacker_spec = _pokemon_spec("Riolu")
        attacker_spec.moves = [double_strike]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        # accuracy, damage die #1, damage die #2
        battle.rng = SequenceRNG([10, 4, 5])
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        action = UseMoveAction(actor_id="ash-1", move_name="Double Kick", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()

        event = battle.log[-1]
        self.assertEqual(event["strike_max"], 2)
        self.assertEqual(event["strike_hits"], 2)
        self.assertEqual(event["damage"], event["strike_damage_per_hit"] * event["strike_hits"])

    def test_five_strike_roll_uses_rng_for_hit_count(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", position=(0, 0), speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        five_strike = MoveSpec(
            name="Pin Missile",
            type="Bug",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            range_text="6, 1 Target, Five Strike",
        )
        attacker_spec = _pokemon_spec("Heracross")
        attacker_spec.moves = [five_strike]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Togepi"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        # accuracy, damage die #1, damage die #2, strike roll (1-4) -> 4 hits
        battle.rng = SequenceRNG([12, 3, 6, 3])
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 3)
        action = UseMoveAction(actor_id="ash-1", move_name="Pin Missile", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()

        event = battle.log[-1]
        self.assertEqual(event["strike_max"], 5)
        self.assertEqual(event["strike_hits"], 4)
        self.assertEqual(event["damage"], event["strike_damage_per_hit"] * event["strike_hits"])

    def test_skill_link_forces_max_strike_hits(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        five_strike = MoveSpec(
            name="Pin Missile",
            type="Bug",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            range_text="6, 1 Target, Five Strike",
        )
        attacker_spec = _pokemon_spec("Heracross")
        attacker_spec.abilities = [{"name": "Skill Link"}]
        attacker_spec.moves = [five_strike]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Togepi"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        # accuracy, damage die #1, damage die #2, strike roll (1-4) -> would be 2 hits without Skill Link
        battle.rng = SequenceRNG([12, 3, 6, 1])
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 3)
        action = UseMoveAction(actor_id="ash-1", move_name="Pin Missile", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()

        event = battle.log[-1]
        self.assertEqual(event["strike_max"], 5)
        self.assertEqual(event["strike_hits"], 5)
        self.assertEqual(event["damage"], event["strike_damage_per_hit"] * event["strike_hits"])

    def test_scene_frequency_blocks_second_use(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        scene_move = MoveSpec(
            name="Scene Strike",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            freq="Scene",
        )
        attacker_spec = _pokemon_spec("Bulbasaur")
        attacker_spec.moves = [scene_move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name=scene_move.name, target_id="gary-1"))
        battle.resolve_next_action()
        with self.assertRaises(ValueError) as ctx:
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name=scene_move.name, target_id="gary-1"))
        self.assertIn("Scene", str(ctx.exception))
        self.assertEqual(battle.log[-1]["type"], "frequency_violation")

    def test_daily_x2_frequency_allows_two_uses_then_blocks(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        daily_move = MoveSpec(
            name="Daily Strike",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            freq="Daily x2",
        )
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [daily_move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Teddiursa"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        for _ in range(2):
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name=daily_move.name, target_id="gary-1"))
            battle.resolve_next_action()
            battle.pokemon["ash-1"].reset_actions()
        with self.assertRaises(ValueError):
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name=daily_move.name, target_id="gary-1"))
        self.assertTrue(any(evt.get("type") == "frequency_violation" for evt in battle.log))

    def test_at_will_frequency_allows_unlimited_use(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        at_will_move = MoveSpec(
            name="At-Will Strike",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            freq="At-Will",
        )
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.moves = [at_will_move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        for _ in range(3):
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name=at_will_move.name, target_id="gary-1"))
            battle.resolve_next_action()
            battle.pokemon["ash-1"].reset_actions()
        self.assertFalse(any(evt.get("type") == "frequency_violation" for evt in battle.log))

    def test_shift_action_message_reports_consumer(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        grid = GridState(width=3, height=3)
        attacker = PokemonState(spec=_pokemon_spec("Charmander"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=foe.identifier)
        attacker.position = (0, 0)
        defender.position = (1, 0)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            grid=grid,
        )
        battle.pokemon["ash-1"].mark_action(ActionType.SHIFT, "Shift to (0,0)")
        battle.queue_action(ShiftAction(actor_id="ash-1", destination=(0, 0)))
        with self.assertRaises(ValueError) as ctx:
            battle.resolve_next_action()
        self.assertIn("Shift to (0,0)", str(ctx.exception))

    def test_standard_action_message_reports_previous_move(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        grid = GridState(width=3, height=3)
        attacker_spec = _pokemon_spec("Bulbasaur")
        tackle_move = MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2, range_kind="Melee", range_value=1, freq="At-Will")
        attacker_spec.moves = [tackle_move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=foe.identifier)
        attacker.position = (0, 0)
        defender.position = (1, 0)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            grid=grid,
        )
        battle.pokemon["ash-1"].mark_action(ActionType.STANDARD, "Move Tackle")
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        with self.assertRaises(ValueError) as ctx:
            battle.resolve_next_action()
        self.assertIn("Move Tackle", str(ctx.exception))

    def test_recoil_damage_applies_fraction_of_damage(self) -> None:       
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        double_edge = MoveSpec(
            name="Double-Edge",
            type="Normal",
            category="Physical",
            db=9,
            ac=None,
            range_kind="Melee",
            range_value=1,
            range_text="Melee, 1 Target, Recoil 1/3",
        )
        attacker_spec = _pokemon_spec("Tauros")
        attacker_spec.moves = [double_edge]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        # accuracy roll + damage dice
        battle.rng = SequenceRNG([12, 6, 5])
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        action = UseMoveAction(actor_id="ash-1", move_name="Double-Edge", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()

        recoil_event = battle.log[-1]
        move_event = next(evt for evt in reversed(battle.log) if evt.get("type") == "move")
        self.assertEqual(recoil_event["type"], "recoil")
        self.assertEqual(recoil_event["fraction"], "1/3")
        expected = int(math.ceil(move_event["damage"] / 3))
        self.assertEqual(recoil_event["amount"], expected)
        self.assertEqual(recoil_event["target_hp"], attacker.hp)

    def test_struggle_does_not_apply_recoil(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Tauros")
        attacker_spec.moves = [
            MoveSpec(
                name="Struggle",
                type="Normal",
                category="Physical",
                db=4,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="At-Will",
                range_text="Melee, 1 Target",
            )
        ]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.rng = SequenceRNG([12, 6, 5])
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        start_hp = attacker.hp
        action = UseMoveAction(actor_id="ash-1", move_name="Struggle", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()

        recoil_events = [
            evt for evt in battle.log if evt.get("type") == "recoil" and evt.get("effect") == "struggle_recoil"
        ]
        self.assertFalse(recoil_events)
        self.assertEqual(attacker.hp, start_hp)

    def test_struggle_uses_combat_expert_profile(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.skills["combat"] = 4
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )

        move = UseMoveAction(actor_id="ash-1", move_name="Struggle", target_id="gary-1")._resolve_move(battle, attacker)

        self.assertEqual(move.name, "Struggle")
        self.assertEqual(move.ac, 3)
        self.assertEqual(move.db, 5)

    def test_struggle_ignores_long_reach_move_tweaks(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.abilities = [{"name": "Long Reach"}]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )

        action = UseMoveAction(actor_id="ash-1", move_name="Struggle", target_id="gary-1")
        move = action._resolve_move(battle, attacker)
        tweaked = action._apply_ability_move_tweaks(battle, attacker, move, consume=False)

        self.assertEqual(tweaked.range_kind, "Melee")
        self.assertEqual(tweaked.target_kind, "Melee")
        self.assertEqual(tweaked.range_value, 1)
        self.assertEqual(tweaked.target_range, 1)

    def test_smite_miss_deals_partial_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        smite_move = MoveSpec(
            name="Smite Bolt",
            type="Electric",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            range_text="Ranged 6, Smite",
        )
        attacker_spec = _pokemon_spec("Luxio")
        attacker_spec.moves = [smite_move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Totodile")
        defender_spec.types = ["Normal"]
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        # accuracy miss, followed by two damage dice for smite resolution
        battle.rng = SequenceRNG([2, 4, 5])
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        starting_hp = defender.hp
        action = UseMoveAction(actor_id="ash-1", move_name="Smite Bolt", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()

        move_event = next(evt for evt in battle.log if evt.get("type") == "move")
        smite_event = next(evt for evt in battle.log if evt.get("type") == "smite")
        self.assertFalse(move_event["hit"])
        self.assertEqual(smite_event["actor"], "ash-1")
        self.assertEqual(smite_event["target"], "gary-1")
        self.assertEqual(smite_event["move"], "Smite Bolt")
        self.assertGreater(smite_event["damage"], 0)
        self.assertAlmostEqual(smite_event["base_multiplier"], 1.0)
        self.assertAlmostEqual(smite_event["smite_multiplier"], 0.5)
        expected_damage = math.floor(smite_event["pre_type_damage"] * 0.5)
        self.assertEqual(smite_event["damage"], expected_damage)
        self.assertEqual(smite_event["prev_hp"], starting_hp)
        self.assertEqual(smite_event["target_hp"], defender.hp)
        self.assertEqual(defender.hp, (starting_hp or 0) - expected_damage)

    def test_battle_state_queue_and_resolve(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        pokemon = PokemonState(spec=_pokemon_spec(), controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": pokemon, "gary-1": PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)

        action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        battle.queue_action(action)
        resolved = battle.resolve_next_action()

        self.assertIs(resolved, action)
        self.assertEqual(battle.log[-1]["move"], "Thunder Shock")

    def test_real_data_damage_scenario(self) -> None:
        repo = PTUCsvRepository()
        pikachu = repo.build_pokemon_spec("Pikachu", level=20, move_names=["Thunder Shock"])
        squirtle = repo.build_pokemon_spec("Squirtle", level=20, move_names=["Tackle"])

        player = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        pikachu_state = PokemonState(spec=pikachu, controller_id=player.identifier)
        squirtle_state = PokemonState(spec=squirtle, controller_id=foe.identifier)

        battle = BattleState(
            trainers={player.identifier: player, foe.identifier: foe},
            pokemon={"ash-1": pikachu_state, "gary-1": squirtle_state},
            rng=random.Random(42),
        )
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["gary-1"].position = (0, 1)
        action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()

        event = battle.log[-1]
        self.assertTrue(event["hit"])
        self.assertEqual(event["damage"], 21)
        self.assertEqual(battle.pokemon["gary-1"].hp, squirtle_state.max_hp() - 21)

    def test_weather_increases_damage(self) -> None:
        repo = PTUCsvRepository()
        pikachu = repo.build_pokemon_spec("Pikachu", level=20, move_names=["Thunder Shock"])
        squirtle = repo.build_pokemon_spec("Squirtle", level=20, move_names=["Tackle"])

        player = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        clear_battle = BattleState(
            trainers={player.identifier: player, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=pikachu, controller_id=player.identifier),
                "gary-1": PokemonState(spec=squirtle, controller_id=foe.identifier),
            },
            rng=random.Random(42),
        )
        clear_battle.pokemon["ash-1"].position = (0, 0)
        clear_battle.pokemon["gary-1"].position = (0, 1)
        clear_action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        clear_battle.queue_action(clear_action)
        clear_battle.resolve_next_action()
        clear_damage = clear_battle.log[-1]["damage"]
        player.reset_actions()
        foe.reset_actions()

        rain_battle = BattleState(
            trainers={player.identifier: player, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=pikachu, controller_id=player.identifier),
                "gary-1": PokemonState(spec=squirtle, controller_id=foe.identifier),
            },
            weather="Rain",
            rng=random.Random(42),
        )
        rain_battle.pokemon["ash-1"].position = (0, 0)
        rain_battle.pokemon["gary-1"].position = (0, 1)
        action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        rain_battle.queue_action(action)
        rain_battle.resolve_next_action()
        event = rain_battle.log[-1]
        self.assertGreater(event["damage"], clear_damage)

    def test_burn_halves_physical_damage(self) -> None:
        repo = PTUCsvRepository()
        pikachu = repo.build_pokemon_spec("Pikachu", level=20, move_names=["Quick Attack"])
        geodude = repo.build_pokemon_spec("Geodude", level=15, move_names=["Tackle"])

        player = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="brock", name="Brock")
        attacker = PokemonState(spec=pikachu, controller_id=player.identifier)
        attacker.statuses.append({"name": "Burned"})
        defender = PokemonState(spec=geodude, controller_id=foe.identifier)
        battle = BattleState(
            trainers={player.identifier: player, foe.identifier: foe},
            pokemon={"ash-1": attacker, "brock-1": defender},
            rng=random.Random(13),
        )
        battle.pokemon["ash-1"].position = (0, 0)
        battle.pokemon["brock-1"].position = (0, 1)
        action = UseMoveAction(actor_id="ash-1", move_name="Quick Attack", target_id="brock-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        event = battle.log[-1]
        self.assertTrue(event["hit"])
        self.assertEqual(event["damage"], 3)

    def test_initiative_prefers_faster_pokemon(self) -> None:
        fast = _pokemon_spec("Jolteon")
        fast.spd = 35
        slow = _pokemon_spec("Snorlax")
        slow.spd = 5
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=fast, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=slow, controller_id=foe.identifier),
            },
            rng=random.Random(3),
        )
        battle.start_round()
        self.assertTrue(battle.initiative_order, "Expected initiative order to be generated.")
        pokemon_order = [
            entry.actor_id
            for entry in battle.initiative_order
            if entry.actor_id not in battle.trainers
        ]
        self.assertEqual(pokemon_order[0], "ash-1")

    def test_initiative_uses_trainer_modifier(self) -> None:
        speedy = _pokemon_spec("Ditto")
        speedy.spd = 10
        slow = _pokemon_spec("Ditto")
        slow.spd = 10
        trainer = TrainerState(identifier="ash", name="Ash", initiative_modifier=15)
        foe = TrainerState(identifier="gary", name="Gary", initiative_modifier=0)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=speedy, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=slow, controller_id=foe.identifier),
            },
            rng=random.Random(7),
        )
        battle.start_round()
        pokemon_order = [
            entry.actor_id
            for entry in battle.initiative_order
            if entry.actor_id not in battle.trainers
        ]
        self.assertEqual(pokemon_order[0], "ash-1")

    def test_advance_turn_skips_fainted_combatants(self) -> None:
        pikachu = _pokemon_spec("Pikachu")
        eevee = _pokemon_spec("Eevee")
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        player_state = PokemonState(spec=pikachu, controller_id=trainer.identifier)
        foe_state = PokemonState(spec=eevee, controller_id=foe.identifier)
        player_state.hp = 0
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": player_state, "gary-1": foe_state},
            rng=random.Random(11),
        )
        battle.start_round()
        turn = _advance_to_pokemon_turn(battle)
        self.assertIsNotNone(turn)
        self.assertEqual(turn.actor_id, "gary-1")

    def test_phase_progression_follows_start_command_action_end(self) -> None:
        pikachu = _pokemon_spec("Pikachu")
        eevee = _pokemon_spec("Eevee")
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=pikachu, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=eevee, controller_id=foe.identifier),
            },
            rng=random.Random(5),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        self.assertEqual(battle.phase, TurnPhase.START)
        battle.advance_phase()
        self.assertEqual(battle.phase, TurnPhase.COMMAND)
        battle.advance_phase()
        self.assertEqual(battle.phase, TurnPhase.ACTION)
        battle.advance_phase()
        self.assertEqual(battle.phase, TurnPhase.END)

    def test_burn_status_ticks_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        burned = PokemonState(spec=_pokemon_spec("Charmander"), controller_id=trainer.identifier)
        burned.statuses.append({"name": "Burned"})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: burned},
            rng=random.Random(5),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        battle.advance_phase()
        battle.advance_phase()
        battle.advance_phase()
        tick_value = burned.tick_value()
        self.assertEqual(burned.hp, burned.max_hp() - tick_value)
        burn_events = [evt for evt in battle.log if evt.get("type") == "status"]
        self.assertTrue(burn_events, "Expected a burn status log entry.")
        self.assertEqual(burn_events[-1]["amount"], tick_value)

    def test_burned_status_lowers_defense_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Charmander"), controller_id=trainer.identifier)
        target.statuses.append({"name": "Burned"})
        self.assertEqual(defensive_stat(target, "physical"), 5)

    def test_poisoned_status_lowers_spdef_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=trainer.identifier)
        target.statuses.append({"name": "Poisoned"})
        self.assertEqual(defensive_stat(target, "special"), 5)

    def test_paralyzed_status_lowers_speed_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        target.statuses.append({"name": "Paralyzed"})
        self.assertEqual(speed_stat(target), 4)

    def test_paralyzed_speed_affects_initiative_order(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        slowed = _pokemon_spec("Magnemite")
        slowed.spd = 12
        slowed_state = PokemonState(spec=slowed, controller_id=trainer.identifier)
        slowed_state.statuses.append({"name": "Paralyzed"})
        quick = _pokemon_spec("Eevee")
        quick.spd = 10
        quick_state = PokemonState(spec=quick, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": slowed_state, "gary-1": quick_state},
        )
        battle.start_round()
        pokemon_order = [
            entry.actor_id
            for entry in battle.initiative_order
            if entry.actor_id not in battle.trainers
        ]
        self.assertEqual(pokemon_order[0], "gary-1")

    def test_frozen_status_skips_turn_and_saves_at_end(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        frozen_spec = _pokemon_spec("Eevee")
        frozen_spec.spd = 10
        frozen_state = PokemonState(
            spec=frozen_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        frozen_state.statuses.append({"name": "Frozen"})
        foe_spec = _pokemon_spec("Pikachu")
        foe_spec.spd = 5
        foe_state = PokemonState(
            spec=foe_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": frozen_state, "gary-1": foe_state},
            rng=SequenceRNG([16]),
        )
        battle.start_round()
        entry = battle.advance_turn()
        self.assertEqual(entry.actor_id, "gary-1")
        save_events = [evt for evt in battle.log if evt.get("effect") == "freeze_save"]
        self.assertTrue(save_events)
        self.assertEqual(save_events[-1]["phase"], "end")
        self.assertEqual(save_events[-1]["dc"], 16)
        self.assertEqual(save_events[-1]["roll"], 16)
        self.assertEqual(save_events[-1]["total"], 16)
        self.assertFalse(frozen_state.has_status("Frozen"))

    def test_frozen_fire_type_uses_lower_dc(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        frozen_spec = _pokemon_spec("Vulpix")
        frozen_spec.types = ["Fire"]
        frozen_spec.spd = 9
        frozen_state = PokemonState(
            spec=frozen_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        frozen_state.statuses.append({"name": "Frozen"})
        foe_spec = _pokemon_spec("Pichu")
        foe_spec.spd = 5
        foe_state = PokemonState(
            spec=foe_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": frozen_state, "gary-1": foe_state},
            rng=SequenceRNG([11]),
        )
        battle.start_round()
        entry = battle.advance_turn()
        self.assertEqual(entry.actor_id, "gary-1")
        save_events = [evt for evt in battle.log if evt.get("effect") == "freeze_save"]
        self.assertTrue(save_events)
        self.assertEqual(save_events[-1]["dc"], 11)
        self.assertEqual(save_events[-1]["roll"], 11)
        self.assertEqual(save_events[-1]["total"], 11)
        self.assertFalse(frozen_state.has_status("Frozen"))

    def test_frozen_thaws_only_on_specific_damage_types(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.moves = [
            MoveSpec(
                name="Water Pulse",
                type="Water",
                category="Special",
                db=1,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="At-Will",
            ),
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=1,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="At-Will",
            ),
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_spec = _pokemon_spec("Eevee")
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        defender_state.statuses.append({"name": "Frozen"})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=MaxRNG(),
        )
        battle.queue_action(
            UseMoveAction(actor_id="ash-1", move_name="Water Pulse", target_id="gary-1")
        )
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Frozen"))
        attacker_state.reset_actions()
        battle.queue_action(
            UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1")
        )
        battle.resolve_next_action()
        self.assertFalse(defender_state.has_status("Frozen"))

    def test_round_start_logs_initial_states(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        subject = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=trainer.identifier)
        subject.statuses.append({"name": "Paralyzed"})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: subject},
            rng=random.Random(1),
        )
        battle.start_round()
        event = battle.log[-1]
        self.assertEqual(event["type"], "round_start")
        initial = event.get("initial_states", [])
        self.assertTrue(initial)
        actor_entry = next((entry for entry in initial if entry["actor"] == actor_id), None)
        self.assertIsNotNone(actor_entry)
        self.assertEqual(actor_entry["hp"], actor_entry["max_hp"])
        self.assertIn("paralyzed", actor_entry["statuses"])

    def test_poison_heal_converts_damage_to_heal(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        poisoned = PokemonState(spec=_pokemon_spec("Breloom"), controller_id=trainer.identifier)
        poisoned.statuses.append({"name": "Poisoned"})
        poisoned.spec.abilities = [{"name": "Poison Heal"}]
        poisoned.hp = poisoned.max_hp() - 10
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: poisoned},
            rng=random.Random(8),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        battle.advance_phase()
        battle.advance_phase()
        battle.advance_phase()
        ability_events = [evt for evt in battle.log if evt.get("ability") == "Poison Heal"]
        self.assertTrue(ability_events, "Poison Heal should have logged a heal event.")
        healed = ability_events[-1]["amount"]
        self.assertGreater(healed, 0)
        self.assertEqual(poisoned.hp, min(poisoned.max_hp(), poisoned.max_hp() - 10 + healed))

    def test_swift_swim_doubles_swim_movement_in_rain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        swimmer = _pokemon_spec("Buizel")
        swimmer.movement["swim"] = 3
        swimmer.abilities = [{"name": "Swift Swim"}]
        swimmer_state = PokemonState(spec=swimmer, controller_id=trainer.identifier)
        self.assertEqual(swimmer_state.movement_speed("swim", weather="Clear"), 3)
        self.assertEqual(swimmer_state.movement_speed("swim", weather="Rain"), 6)
        self.assertEqual(swimmer_state.movement_speed("swim", weather="Storm"), 6)
        self.assertEqual(swimmer_state.movement_speed("swim", weather="Downpour"), 6)

    def test_chlorophyll_boosts_overland_in_sun(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        sprinter = _pokemon_spec("Bellossom")
        sprinter.movement["overland"] = 4
        sprinter.abilities = [{"name": "Chlorophyll"}]
        sprinter_state = PokemonState(spec=sprinter, controller_id=trainer.identifier)
        self.assertEqual(sprinter_state.movement_speed("overland", weather="Clear"), 4)
        self.assertEqual(sprinter_state.movement_speed("overland", weather="Sun"), 6)
        self.assertEqual(sprinter_state.movement_speed("overland", weather="Harsh Sunlight"), 6)

    def test_dragon_energy_scales_db_with_missing_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Dragonite")
        attacker_spec.types = ["Dragon"]
        move = MoveSpec(
            name="Dragon Energy",
            type="Dragon",
            category="Special",
            db=15,
            ac=2,
            range_kind="Cone",
            range_value=3,
            freq="Daily x2",
        )
        attacker_spec.moves = [move]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        penalty_missing = math.ceil(attacker_state.max_hp() * 0.3)
        attacker_state.hp = attacker_state.max_hp() - penalty_missing
        defender_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id="gary")
        context = build_attack_context(attacker_state, defender_state, move)
        effective_db_value, base_with_stab, weather_bonus, other_bonus = _effective_db_components(
            context, attacker_state
        )
        expected_penalty = int(
            ((attacker_state.max_hp() - attacker_state.hp) / attacker_state.max_hp()) * 10
        )
        self.assertEqual(expected_penalty, 3)
        self.assertEqual(other_bonus, -expected_penalty)
        self.assertTrue(
            any(mod.slug == "dragon-energy-missing-hp" for mod in context.modifiers)
        )
        self.assertEqual(effective_db_value, base_with_stab + weather_bonus + other_bonus)

    def test_dragon_breath_paralyzes_on_high_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Dragonite")
        attacker_spec.moves = [
            MoveSpec(
                name="Dragon Breath",
                type="Dragon",
                category="Special",
                db=6,
                ac=2,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([16])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=attacker_spec.moves[0],
            result={"hit": True},
            damage_dealt=1,
        )
        status_events = [evt for evt in events if evt.get("status") == "Paralyzed"]
        self.assertTrue(status_events)
        self.assertTrue(defender_state.has_status("Paralyzed"))

    def test_dragon_dance_increases_attack_and_speed(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Garchomp")
        move = MoveSpec(
            name="Dragon Dance",
            type="Dragon",
            category="Status",
            db=8,
            ac=None,
            range_kind="Self",
            range_value=0,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        attacker_key = f"{trainer.identifier}-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={attacker_key: attacker_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id=attacker_key,
            attacker=attacker_state,
            defender_id=attacker_key,
            defender=attacker_state,
            move=move,
            result={"hit": False},
            damage_dealt=0,
        )
        stage_events = [evt for evt in events if evt.get("type") == "combat_stage"]
        self.assertEqual(attacker_state.combat_stages["atk"], 1)
        self.assertEqual(attacker_state.combat_stages["spd"], 1)
        self.assertEqual(len(stage_events), 2)

    def test_dragon_ascent_lowers_defenses(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Salamence")
        move = MoveSpec(
            name="Dragon Ascent",
            type="Flying",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id="gary")
        foe = TrainerState(identifier="gary", name="Gary")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=1,
        )
        self.assertEqual(attacker_state.combat_stages["def"], -1)
        self.assertEqual(attacker_state.combat_stages["spdef"], -1)
        self.assertGreaterEqual(len(events), 2)

    def test_false_swipe_leaves_target_at_one_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Scyther")
        move = MoveSpec(
            name="False Swipe",
            type="Normal",
            category="Physical",
            db=5,
            ac=4,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        defender_state.hp = 0
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 12},
            damage_dealt=defender_state.max_hp(),
        )
        self.assertEqual(defender_state.hp, 1)
        swipe_events = [evt for evt in events if evt.get("effect") == "false_swipe"]
        self.assertTrue(swipe_events)

    def test_false_surrender_cannot_miss(self) -> None:
        attacker_spec = _pokemon_spec("Umbreon")
        defender_spec = _pokemon_spec("Bulbasaur")
        move = MoveSpec(
            name="False Surrender",
            type="Dark",
            category="Physical",
            db=8,
            ac=12,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        defender_state = PokemonState(spec=defender_spec, controller_id="gary")
        rng = SequenceRNG([1])
        result = resolve_move_action(
            rng=rng,
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertTrue(result["hit"])
        self.assertEqual(result["roll"], 1)

    def test_fire_fang_burns_and_flinches_on_20(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Fennekin")
        move = MoveSpec(
            name="Fire Fang",
            type="Fire",
            category="Physical",
            db=7,
            ac=3,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 20},
            damage_dealt=5,
        )
        status_events = [evt for evt in events if evt.get("type") == "status"]
        self.assertEqual({evt.get("status") for evt in status_events}, {"Burned", "Flinch"})
        self.assertTrue(defender_state.has_status("Burned"))
        self.assertTrue(defender_state.has_status("Flinch"))

    def test_burn_moves_apply_burn_on_high_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        burn_moves = {
            "Sacred Fire": "Fire",
            "Scald": "Water",
            "Scorching Sands": "Ground",
            "Searing Shot": "Fire",
        }
        for move_name, move_type in burn_moves.items():
            move = MoveSpec(
                name=move_name,
                type=move_type,
                category="Special",
                db=7,
                ac=3,
                range_kind="Melee",
                range_value=1,
            )
            attacker_state = PokemonState(spec=_pokemon_spec("Charizard"), controller_id=trainer.identifier)
            defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
            battle = BattleState(
                trainers={trainer.identifier: trainer, defender.identifier: defender},
                pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            )
            events = battle._handle_move_special_effects(
                attacker_id="ash-1",
                attacker=attacker_state,
                defender_id="gary-1",
                defender=defender_state,
                move=move,
                result={"hit": True, "roll": 16},
                damage_dealt=6,
            )
            self.assertTrue(defender_state.has_status("Burned"))
            effect_tag = f"{move_name.lower().replace(' ', '_')}_burn"
            self.assertIn(effect_tag, {evt.get("effect") for evt in events})

    def test_sand_attack_lowers_accuracy(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Sand Attack",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Sandshrew"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(defender_state.combat_stages["accuracy"], -1)
        self.assertTrue(any(evt.get("effect") == "sand_attack" for evt in events))

    def test_scary_face_and_screech_lower_stages(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        for move_name, stat, expected in [
            ("Scary Face", "spd", -2),
            ("Screech", "def", -2),
        ]:
            move = MoveSpec(
                name=move_name,
                type="Normal",
                category="Status",
                db=0,
                ac=2,
                range_kind="Melee",
                range_value=1,
            )
            attacker_state = PokemonState(spec=_pokemon_spec("Mew"), controller_id=trainer.identifier)
            defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier)
            battle = BattleState(
                trainers={trainer.identifier: trainer, foe.identifier: foe},
                pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            )
            battle._handle_move_special_effects(
                attacker_id="ash-1",
                attacker=attacker_state,
                defender_id="gary-1",
                defender=defender_state,
                move=move,
                result={"hit": True},
                damage_dealt=0,
            )
            self.assertEqual(defender_state.combat_stages[stat], expected)

    def test_sand_tomb_traps_targets_in_vortex(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Sand Tomb",
            type="Ground",
            category="Physical",
            db=4,
            ac=4,
            range_kind="Ranged",
            range_value=4,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Hippowdon"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=4,
        )
        self.assertTrue(defender_state.has_status("Vortex"))
        self.assertTrue(defender_state.has_status("Trapped"))

    def test_sandstorm_sets_weather_and_damages_foes(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Sandstorm",
            type="Rock",
            category="Status",
            db=0,
            ac=0,
            range_kind="Field",
            range_value=0,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Tyranitar"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(battle.weather, "Sandstorm")
        self.assertTrue(any(evt.get("effect") == "sandstorm" for evt in events))
        before_hp = defender_state.hp
        damage_events = defender_state.handle_phase_effects(battle, TurnPhase.START, "gary-1")
        self.assertTrue(any(evt.get("effect") == "sandstorm_damage" for evt in damage_events))
        self.assertLess(defender_state.hp, before_hp)

    def test_secret_power_applies_environment_status(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Secret Power",
            type="Normal",
            category="Special",
            db=7,
            ac=2,
            range_kind="Ranged",
            range_value=4,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Lucario"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier)
        attacker_state.position = (0, 0)
        grid = GridState(width=1, height=1)
        grid.tiles[(0, 0)] = {"type": "long grass"}
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            grid=grid,
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 17},
            damage_dealt=7,
        )
        self.assertTrue(defender_state.has_status("Drowsy"))
        self.assertTrue(any(evt.get("status") == "Drowsy" for evt in events))

    def test_safeguard_blocks_statuses_three_times(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        move = MoveSpec(
            name="Safeguard",
            type="Normal",
            category="Status",
            db=0,
            ac=0,
            range_kind="Blessing",
            range_value=0,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Clefairy"), controller_id=trainer.identifier)
        ally_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state, "ash-2": ally_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="ash-1",
            defender=attacker_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(ally_state.has_status("Safeguard"))
        fake_move = MoveSpec(
            name="Fake Burn",
            type="Fire",
            category="Special",
            db=6,
            ac=3,
            range_kind="Melee",
            range_value=1,
        )
        for expected_remaining in [2, 1, 0]:
            events: List[dict] = []
            battle._apply_status(
                events,
                attacker_id="ash-1",
                target_id="ash-2",
                move=fake_move,
                target=ally_state,
                status="Burned",
                effect="status",
                description="Test burn",
                roll=20,
            )
            block_events = [evt for evt in events if evt.get("effect") == "safeguard_block"]
            self.assertTrue(block_events)
            self.assertEqual(block_events[-1].get("remaining"), expected_remaining)
            self.assertFalse(ally_state.has_status("Burned"))
        self.assertFalse(ally_state.has_status("Safeguard"))

    def test_feather_dance_lowers_attack_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Xatu")
        move = MoveSpec(
            name="Feather Dance",
            type="Flying",
            category="Status",
            db=0,
            ac=3,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=defender.identifier)
        defender_state.combat_stages["atk"] = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(defender_state.combat_stages["atk"], -1)
        stage_events = [evt for evt in events if evt.get("stat") == "atk"]
        self.assertTrue(stage_events)
        self.assertEqual(stage_events[0].get("amount"), 2)

    def test_force_palm_paralyzes_on_18(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Lucario")
        move = MoveSpec(
            name="Force Palm",
            type="Fighting",
            category="Physical",
            db=6,
            ac=3,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 18},
            damage_dealt=5,
        )
        status_events = [evt for evt in events if evt.get("status") == "Paralyzed"]
        self.assertTrue(status_events)
        self.assertTrue(defender_state.has_status("Paralyzed"))

    def test_fire_punch_burns_on_19(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Arcanine")
        move = MoveSpec(
            name="Fire Punch",
            type="Fire",
            category="Physical",
            db=7,
            ac=3,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 19},
            damage_dealt=6,
        )
        status_events = [evt for evt in events if evt.get("status") == "Burned"]
        self.assertTrue(status_events)
        self.assertTrue(defender_state.has_status("Burned"))

    def test_flirt_infatuates_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Flirt",
            type="Normal",
            category="Status",
            db=0,
            ac=1,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(defender_state.has_status("Infatuated"))
        status_events = [evt for evt in events if evt.get("status") == "Infatuated"]
        self.assertTrue(status_events)

    def test_floral_healing_heals_more_on_grassy_terrain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Floral Healing",
            type="Normal",
            category="Status",
            db=0,
            ac=1,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Bellossom"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        defender_state.hp = 5
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.terrain = {"name": "Grassy Terrain"}
        target_max = defender_state.max_hp()
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        heal_events = [evt for evt in events if evt.get("effect") == "floral_healing"]
        expected_amount = int(math.floor(target_max * (2 / 3)))
        self.assertTrue(heal_events)
        self.assertEqual(heal_events[0].get("amount"), expected_amount)
        self.assertGreater(defender_state.hp, 5)

    def test_flower_shield_boosts_grass_allies(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Bellossom")
        move = MoveSpec(
            name="Flower Shield",
            type="Grass",
            category="Status",
            db=0,
            ac=1,
            range_kind="Social",
            range_value=8,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        ally_grass = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier)
        ally_grass.spec.types = ["Grass"]
        ally_grass.combat_stages["def"] = 0
        ally_normal = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state, "ally-grass": ally_grass, "ally-normal": ally_normal},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(ally_grass.combat_stages["def"], 2)
        shield_events = [evt for evt in events if evt.get("effect") == "increase" and evt.get("stat") == "def"]
        self.assertTrue(shield_events)

    def test_future_sight_requires_setup(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Future Sight",
            type="Psychic",
            category="Special",
            db=12,
            ac=None,
            range_kind="Ranged",
            range_value=10,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        self.assertTrue(battle.move_requires_setup(move))

    def test_future_sight_resolves_after_setup(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Future Sight",
            type="Psychic",
            category="Special",
            db=12,
            ac=None,
            range_kind="Ranged",
            range_value=10,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        defender_hp_before = defender_state.hp
        battle.schedule_setup_move(
            actor_id="ash-1",
            move=move,
            target_id="gary-1",
            target_position=defender_state.position,
        )
        self.assertTrue(battle.has_pending_resolution("ash-1"))
        battle.rng = SequenceRNG([20, 20, 20, 20])
        executed = battle.execute_pending_resolution("ash-1")
        self.assertTrue(executed)
        self.assertFalse(battle.has_pending_resolution("ash-1"))
        self.assertLess(defender_state.hp, defender_hp_before)
        move_events = [
            evt
            for evt in battle.log
            if evt.get("type") == "move" and evt.get("move") == "Future Sight"
        ]
        self.assertTrue(move_events)

    def test_absorb_heals_half_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Sceptile")
        move = MoveSpec(
            name="Absorb",
            type="Grass",
            category="Special",
            db=2,
            ac=2,
            range_kind="Ranged",
            range_value=4,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        attacker_state.hp = 10
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        defender_state.hp = 30
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=11,
        )
        self.assertEqual(attacker_state.hp, 10 + 11 // 2)
        absorb_events = [evt for evt in events if evt.get("effect") == "absorb"]
        self.assertTrue(absorb_events)
        self.assertEqual(absorb_events[0].get("amount"), 11 // 2)

    def test_accelerock_logs_dash_priority(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Accelerock",
            type="Rock",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            priority=10,
            keywords=["Dash"],
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Lucario"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        defender_state.hp = 22
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=8,
        )
        dash_events = [evt for evt in events if evt.get("effect") == "accelerock_dash"]
        self.assertTrue(dash_events)
        event = dash_events[0]
        self.assertEqual(event.get("priority"), 10)
        self.assertTrue(event.get("dash"))
        self.assertEqual(event.get("target_hp"), defender_state.hp)       

    def test_aeroblast_even_roll_triggers_critical(self) -> None:
        attacker = PokemonState(spec=_pokemon_spec("Skarmory"), controller_id="player")
        defender = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id="foe")
        move = MoveSpec(
            name="Aeroblast",
            type="Flying",
            category="Special",
            db=10,
            ac=3,
            range_kind="Line",
            range_value=6,
        )
        rng = SequenceRNG([18] + [1] * 16)
        result = resolve_move_action(rng, attacker, defender, move)
        self.assertTrue(result.get("hit"))
        self.assertIn("crit", result)
        self.assertTrue(result["crit"])

    def test_attack_order_crit_on_18(self) -> None:
        attacker = PokemonState(spec=_pokemon_spec("Beedrill"), controller_id="player")
        defender = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id="foe")
        move = MoveSpec(
            name="Attack Order",
            type="Bug",
            category="Physical",
            db=9,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        rng = SequenceRNG([18] + [1] * 16)
        result = resolve_move_action(rng, attacker, defender, move)
        self.assertTrue(result.get("hit"))
        self.assertIn("crit", result)
        self.assertTrue(result["crit"])

    def test_night_slash_crit_on_18(self) -> None:
        attacker = PokemonState(spec=_pokemon_spec("Absol"), controller_id="player")
        defender = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id="foe")
        move = MoveSpec(
            name="Night Slash",
            type="Dark",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        rng = SequenceRNG([18] + [1] * 16)
        result = resolve_move_action(rng, attacker, defender, move)
        self.assertTrue(result.get("hit"))
        self.assertTrue(result.get("crit"))

    def test_nightmare_requires_sleeping_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Darkrai"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Nightmare",
            type="Ghost",
            category="Status",
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state.spec.moves = [move]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="ash-1", move_name="Nightmare", target_id="gary-1").validate(battle)

    def test_nightmare_applies_bad_sleep_and_ticks_on_sleep_save(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Darkrai"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        sleep_entry = {"name": "Sleep"}
        defender_state.statuses.append(sleep_entry)
        defender_state.hp = defender_state.max_hp()
        move = MoveSpec(
            name="Nightmare",
            type="Ghost",
            category="Status",
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(defender_state.has_status("Bad Sleep"))
        self.assertTrue([evt for evt in events if evt.get("effect") == "nightmare"])
        battle.rng = SequenceRNG([10])
        before = defender_state.hp
        save_events = defender_state.sleep_save_events(battle, "gary-1", sleep_entry, "sleep")
        self.assertTrue([evt for evt in save_events if evt.get("effect") == "bad_sleep"])
        self.assertEqual(before - defender_state.hp, 2 * defender_state.tick_value())

    def test_noble_roar_lowers_attack_and_spatk(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Litleo"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Noble Roar",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Burst",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(defender_state.combat_stages["atk"], -1)
        self.assertEqual(defender_state.combat_stages["spatk"], -1)
        self.assertTrue([evt for evt in events if evt.get("effect") == "noble_roar"])

    def test_nuzzle_paralyzes_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Dedenne"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Nuzzle",
            type="Electric",
            category="Physical",
            db=2,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        self.assertTrue(defender_state.has_status("Paralyzed"))
        self.assertTrue([evt for evt in events if evt.get("effect") == "nuzzle"])

    def test_no_retreat_raises_stats_and_prevents_switching(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Falinks"), controller_id=trainer.identifier)
        replacement_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)
        attacker_state.active = True
        replacement_state.active = False
        move = MoveSpec(
            name="No Retreat",
            type="Fighting",
            category="Status",
            ac=None,
            range_kind="Self",
            range_value=0,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state, "ash-2": replacement_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        for stat in ("atk", "def", "spatk", "spdef", "spd"):
            self.assertEqual(attacker_state.combat_stages[stat], 1)
        self.assertTrue(attacker_state.has_status("No Retreat"))
        with self.assertRaises(ValueError):
            SwitchAction(actor_id="ash-1", replacement_id="ash-2").validate(battle)

    def test_oblivion_wing_heals_damage_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Yveltal"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker_state.hp = max(1, attacker_state.max_hp() - 20)
        move = MoveSpec(
            name="Oblivion Wing",
            type="Flying",
            category="Special",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        before = attacker_state.hp
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "damage_roll": 12},
            damage_dealt=5,
        )
        self.assertEqual(attacker_state.hp, min(attacker_state.max_hp(), before + 12))

    def test_obstruct_blocks_melee_attack_and_lowers_defense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        tackle_move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            freq="At-Will",
        )
        obstruct_move = MoveSpec(
            name="Obstruct",
            type="Dark",
            category="Status",
            ac=None,
            range_kind="Self",
            range_value=0,
            freq="Scene",
            range_text="Self, Interrupt, Shield, Trigger",
        )
        attacker_spec = _pokemon_spec("Bulbasaur")
        attacker_spec.moves = [tackle_move]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.hp_stat = 200
        defender_spec.moves = [obstruct_move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        attacker.position = (0, 0)
        defender.position = (0, 1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.rng = SequenceRNG([20, 6, 6])
        defender.statuses.append({"name": "Obstruct"})
        starting_hp = defender.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender.hp, starting_hp)
        self.assertEqual(attacker.combat_stages["def"], -2)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "obstruct"])

    def test_octazooka_even_roll_lowers_accuracy(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Octazooka",
            type="Water",
            category="Special",
            db=7,
            ac=3,
            range_kind="Ranged",
            range_value=6,
            freq="At-Will",
        )
        attacker_spec = _pokemon_spec("Octillery")
        attacker_spec.moves = [move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker.position = (0, 0)
        defender.position = (0, 1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.rng = SequenceRNG([12, 6, 6])
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Octazooka", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender.combat_stages["accuracy"], -1)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "octazooka"])

    def test_octolock_grapples_and_lowers_defenses_each_turn(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Octolock",
            type="Fighting",
            category="Status",
            ac=2,
            range_kind="Melee",
            range_value=1,
            freq="Scene",
        )
        attacker_spec = _pokemon_spec("Grapploct")
        attacker_spec.moves = [move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker.position = (0, 0)
        defender.position = (0, 1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.rng = SequenceRNG([20, 20, 20, 20])
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Octolock", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(attacker.has_temporary_effect("grapple_link"))
        self.assertTrue(defender.has_temporary_effect("grapple_link"))
        self.assertTrue(defender.has_temporary_effect("octolock"))
        events = defender.handle_phase_effects(battle, TurnPhase.END, "gary-1")
        self.assertEqual(defender.combat_stages["def"], -1)
        self.assertEqual(defender.combat_stages["spdef"], -1)
        self.assertTrue([evt for evt in events if evt.get("effect") == "octolock"])

    def test_odor_sleuth_is_swift_and_grants_foresight(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Stoutland")
        move = MoveSpec(
            name="Odor Sleuth",
            type="Normal",
            category="Status",
            ac=None,
            range_kind="Self",
            range_value=0,
            freq="Scene x2",
            range_text="Self, Swift Action",
        )
        attacker_spec.moves = [move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})
        action = UseMoveAction(actor_id="ash-1", move_name="Odor Sleuth")
        action.validate(battle)
        self.assertEqual(action.action_type, ActionType.SWIFT)
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertTrue(attacker.get_temporary_effects("foresight"))

    def test_ominous_wind_raises_stats_on_19(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Misdreavus"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Ominous Wind",
            type="Ghost",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True, "roll": 19},
            damage_dealt=0,
        )
        for stat in ("atk", "def", "spatk", "spdef", "spd", "accuracy"):
            self.assertEqual(attacker_state.combat_stages[stat], 1)
        self.assertTrue([evt for evt in events if evt.get("effect") == "ominous_wind"])

    def test_pain_split_redistributes_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Gastly"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker_state.hp = 40
        defender_state.hp = 20
        move = MoveSpec(
            name="Pain Split",
            type="Normal",
            category="Status",
            ac=None,
            range_kind="Ranged",
            range_value=4,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.hp, 35)
        self.assertEqual(defender_state.hp, 25)

    def test_parabolic_charge_heals_half_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Dedenne"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker_state.hp = max(1, attacker_state.max_hp() - 10)
        move = MoveSpec(
            name="Parabolic Charge",
            type="Electric",
            category="Special",
            db=5,
            ac=4,
            range_kind="Cone",
            range_value=2,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        before = attacker_state.hp
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=10,
        )
        self.assertEqual(attacker_state.hp, min(attacker_state.max_hp(), before + 5))

    def test_parting_shot_lowers_stats_and_switches(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Purrloin"), controller_id=trainer.identifier)
        replacement_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier)
        attacker_state.active = True
        replacement_state.active = False
        attacker_state.position = (0, 0)
        defender_state.position = (0, 1)
        move = MoveSpec(
            name="Parting Shot",
            type="Dark",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_state,
                "ash-2": replacement_state,
                "gary-1": defender_state,
            },
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(defender_state.combat_stages["atk"], -1)
        self.assertEqual(defender_state.combat_stages["spatk"], -1)
        self.assertFalse(attacker_state.active)
        self.assertTrue(replacement_state.active)
        self.assertTrue([evt for evt in events if evt.get("effect") == "parting_shot"])

    def test_pay_day_logs_coin_value(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Meowth"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Pay Day",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Cone",
            range_value=2,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle.rng = SequenceRNG([5])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        pay_day_events = [evt for evt in events if evt.get("effect") == "pay_day"]
        self.assertTrue(pay_day_events)
        self.assertEqual(pay_day_events[0]["coins"], 5 * attacker_state.spec.level)

    def test_payback_boosts_when_hit_last_round(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        payback = MoveSpec(
            name="Payback",
            type="Dark",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_value=1,
            freq="EOT",
        )
        attacker_spec = _pokemon_spec("Absol")
        attacker_spec.moves = [payback]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker.position = (0, 0)
        defender.position = (0, 1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.damage_taken_from_last_round["ash-1"] = {"gary-1"}
        battle.rng = SequenceRNG([18, 6, 6])
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Payback", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in reversed(battle.log) if evt.get("type") == "move")
        self.assertEqual(move_event.get("effective_db"), 10)

    def test_photon_geyser_uses_highest_attack_stat(self) -> None:
        spec = _pokemon_spec("Necrozma")
        spec.atk = 20
        spec.spatk = 5
        attacker = PokemonState(spec=spec, controller_id="player")
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="foe")
        move = MoveSpec(
            name="Photon Geyser",
            type="Psychic",
            category="Special",
            db=10,
            ac=2,
            range_kind="Burst",
            range_value=2,
        )
        rng = SequenceRNG([18] + [1] * 10)
        result = resolve_move_action(rng, attacker, defender, move)
        self.assertEqual(result.get("attack_value"), 20)

    def test_pierce_adds_bonus_vs_damage_reduction(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Pierce!",
            type="Normal",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_spec = _pokemon_spec("Farfetch'd")
        attacker_spec.moves = [move]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        defender.add_temporary_effect("damage_reduction", amount=5)
        attacker.position = (0, 0)
        defender.position = (0, 1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.rng = SequenceRNG([18, 6, 6])
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Pierce!", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in reversed(battle.log) if evt.get("type") == "move")
        self.assertEqual(move_event.get("pierce_bonus"), 10)

    def test_play_nice_lowers_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Play Nice",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(defender_state.combat_stages["atk"], -1)

    def test_play_rough_lowers_attack_on_17(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Granbull"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Play Rough",
            type="Fairy",
            category="Physical",
            db=9,
            ac=4,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 17},
            damage_dealt=5,
        )
        self.assertEqual(defender_state.combat_stages["atk"], -1)

    def test_pluck_steals_item_when_user_empty(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgey")
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.items = [{"name": "Oran Berry"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        move = MoveSpec(
            name="Pluck",
            type="Flying",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        self.assertTrue(attacker_state.spec.items)
        self.assertFalse(defender_state.spec.items)

    def test_poison_fang_badly_poisons_on_17(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Seviper"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Poison Fang",
            type="Poison",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 17},
            damage_dealt=5,
        )
        self.assertTrue(defender_state.has_status("Badly Poisoned"))

    def test_poison_gas_poisons_targets(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Koffing"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Poison Gas",
            type="Poison",
            category="Status",
            ac=6,
            range_kind="Burst",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(defender_state.has_status("Poisoned"))

    def test_poison_jab_poisons_on_15(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Nidoking"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Poison Jab",
            type="Poison",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 15},
            damage_dealt=5,
        )
        self.assertTrue(defender_state.has_status("Poisoned"))

    def test_poison_powder_poisons_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Oddish"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Poison Powder",
            type="Poison",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(defender_state.has_status("Poisoned"))

    def test_poison_sting_poisons_on_17(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Weedle"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Poison Sting",
            type="Poison",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 17},
            damage_dealt=4,
        )
        self.assertTrue(defender_state.has_status("Poisoned"))

    def test_poison_tail_poisons_on_19(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Seviper"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Poison Tail",
            type="Poison",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 19},
            damage_dealt=7,
        )
        self.assertTrue(defender_state.has_status("Poisoned"))

    def test_poison_tail_crits_on_18(self) -> None:
        attacker_state = PokemonState(spec=_pokemon_spec("Seviper"), controller_id="ash")
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Poison Tail",
            type="Poison",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        result = resolve_move_action(
            rng=SequenceRNG([18, 1, 1, 1]),
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertTrue(result["crit"])

    def test_pollen_puff_heals_ally_once(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        pollen_puff = MoveSpec(
            name="Pollen Puff",
            type="Bug",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_spec = _pokemon_spec("Ribombee")
        attacker_spec.moves = [pollen_puff]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = [pollen_puff]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1))
        defender_state.hp = defender_state.max_hp() - 20
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state, "ash-2": defender_state},
            rng=SequenceRNG([10, 1, 1]),
        )
        battle.resolve_move_targets("ash-1", pollen_puff, "ash-2", defender_state.position)
        self.assertTrue(attacker_state.get_temporary_effects("pollen_puff_used"))
        self.assertGreater(defender_state.hp, defender_state.max_hp() - 20)

    def test_powder_explodes_on_fire_move(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        powder = MoveSpec(
            name="Powder",
            type="Bug",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        ember = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        grid = GridState(width=5, height=5)
        attacker_state = PokemonState(spec=_pokemon_spec("Vivillon"), controller_id=trainer.identifier, position=(2, 2))
        defender_state = PokemonState(spec=_pokemon_spec("Charmander"), controller_id=foe.identifier, position=(2, 3))
        bystander_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier, position=(3, 3))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state, "ash-2": bystander_state},
            rng=SequenceRNG([10, 3, 3, 3, 3, 3, 3]),
            grid=grid,
        )
        battle.resolve_move_targets("ash-1", powder, "gary-1", defender_state.position)
        self.assertTrue(defender_state.has_status("Powdered"))
        hp_before = {
            "ash-1": attacker_state.hp,
            "gary-1": defender_state.hp,
            "ash-2": bystander_state.hp,
        }
        battle.resolve_move_targets("gary-1", ember, "ash-1", attacker_state.position)
        self.assertFalse(defender_state.has_status("Powdered"))
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "powder_blast"])
        self.assertLess(attacker_state.hp, hp_before["ash-1"])
        self.assertLessEqual(defender_state.hp, hp_before["gary-1"])

    def test_powder_snow_freezes_on_19(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Swinub"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Powder Snow",
            type="Ice",
            category="Special",
            db=4,
            ac=2,
            range_kind="Line",
            range_value=4,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 19},
            damage_dealt=4,
        )
        self.assertTrue(defender_state.has_status("Frozen"))

    def test_power_shift_uses_special_defense_as_attack(self) -> None:
        attacker_spec = _pokemon_spec("Mr. Mime")
        attacker_spec.spatk = 7
        attacker_spec.spdef = 25
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        attacker_state.statuses.append({"name": "Power Shift"})
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Psychic",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        result = resolve_move_action(
            rng=SequenceRNG([10, 1, 1, 1]),
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertEqual(result["attack_value"], attacker_spec.spdef)

    def test_power_trick_uses_defense_as_attack(self) -> None:
        attacker_spec = _pokemon_spec("Hitmonchan")
        attacker_spec.atk = 5
        attacker_spec.defense = 20
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        attacker_state.statuses.append({"name": "Power Trick"})
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        result = resolve_move_action(
            rng=SequenceRNG([10, 1, 1, 1]),
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertEqual(result["attack_value"], attacker_spec.defense)

    def test_power_split_applies_stat_modifiers_and_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Power Split",
            type="Psychic",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(defender_state.get_temporary_effects("stat_modifier"))
        self.assertTrue(attacker_state.get_temporary_effects("power_split_bonus"))

    def test_power_swap_trades_attack_stages(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker_state.combat_stages["atk"] = 2
        defender_state.combat_stages["atk"] = -1
        attacker_state.combat_stages["spatk"] = 1
        defender_state.combat_stages["spatk"] = -2
        move = MoveSpec(
            name="Power Swap",
            type="Psychic",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["atk"], -1)
        self.assertEqual(defender_state.combat_stages["atk"], 2)
        self.assertEqual(attacker_state.combat_stages["spatk"], -2)
        self.assertEqual(defender_state.combat_stages["spatk"], 1)

    def test_power_trip_scales_db(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Power Trip",
            type="Dark",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_spec = _pokemon_spec("Absol")
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        attacker_state.combat_stages["atk"] = 2
        attacker_state.combat_stages["spatk"] = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([10, 1, 1, 1]),
        )
        battle.resolve_move_targets("ash-1", move, "gary-1", defender_state.position)
        move_event = next(evt for evt in battle.log if evt.get("effect") == "power_trip")
        self.assertEqual(move_event.get("bonus_db"), 6)

    def test_power_up_punch_raises_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Power-Up Punch",
            type="Fighting",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=4,
        )
        self.assertEqual(attacker_state.combat_stages["atk"], 1)

    def test_present_heals_on_roll_1(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        present = MoveSpec(
            name="Present",
            type="Normal",
            category="Physical",
            db=4,
            ac=3,
            range_kind="Ranged",
            range_value=4,
        )
        attacker_spec = _pokemon_spec("Delibird")
        attacker_spec.moves = [present]
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        defender_state.hp = defender_state.max_hp() - 30
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([1, 10, 1, 1, 1]),
        )
        battle.resolve_move_targets("ash-1", present, "gary-1", defender_state.position)
        self.assertGreater(defender_state.hp, defender_state.max_hp() - 30)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "present_heal"])

    def test_giver_uses_stored_present_choice_and_tracks_state(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        present = MoveSpec(
            name="Present",
            type="Normal",
            category="Physical",
            db=4,
            ac=3,
            range_kind="Ranged",
            range_value=4,
        )
        attacker_spec = _pokemon_spec("Delibird")
        attacker_spec.abilities = [{"name": "Giver", "giver_choice_roll": 5}]
        attacker_spec.moves = [present]
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([20] * 10),
        )
        battle.resolve_move_targets("ash-1", present, "gary-1", defender_state.position)
        giver_state = next(iter(attacker_state.get_temporary_effects("giver_state")), None)
        self.assertIsNotNone(giver_state)
        self.assertEqual(giver_state.get("roll"), 5)
        self.assertEqual(giver_state.get("mode"), "Damage")

    def test_protect_blocks_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        protect = MoveSpec(
            name="Protect",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Self",
            range_value=0,
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = [protect]
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [tackle]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([10, 1, 1]),
        )
        defender_state.statuses.append({"name": "Protect"})
        hp_before = defender_state.hp
        battle.resolve_move_targets("ash-1", tackle, "gary-1", defender_state.position)
        self.assertEqual(defender_state.hp, hp_before)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "protect"])

    def test_psybeam_confuses_on_19(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Abra"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 19},
            damage_dealt=6,
        )
        self.assertTrue(defender_state.has_status("Confused"))

    def test_psychic_fangs_logs_effect(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Boltund"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Psychic Fangs",
            type="Psychic",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=8,
        )
        self.assertTrue([evt for evt in events if evt.get("effect") == "psychic_fangs"])

    def test_psychic_terrain_sets_terrain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Indeedee"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Psychic Terrain",
            type="Psychic",
            category="Status",
            ac=2,
            range_kind="Field",
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertIsNotNone(battle.terrain)
        self.assertEqual((battle.terrain or {}).get("name"), "Psychic Terrain")

    def test_psycho_cut_crits_on_18(self) -> None:
        attacker_state = PokemonState(spec=_pokemon_spec("Gallade"), controller_id="ash")
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Psycho Cut",
            type="Psychic",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        result = resolve_move_action(
            rng=SequenceRNG([18, 1, 1, 1]),
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertTrue(result["crit"])

    def test_psyshield_bash_grants_damage_reduction(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Wyrdeer"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Psyshield Bash",
            type="Psychic",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=7,
        )
        reduction = attacker_state.get_temporary_effects("damage_reduction")
        self.assertTrue(reduction)
        self.assertEqual(reduction[0].get("amount"), 5)

    def test_psyshock_uses_defense_value(self) -> None:
        attacker_spec = _pokemon_spec("Alakazam")
        defender_spec = _pokemon_spec("Onix")
        defender_spec.defense = 25
        defender_spec.spdef = 5
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        defender_state = PokemonState(spec=defender_spec, controller_id="gary")
        move = MoveSpec(
            name="Psyshock",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        result = resolve_move_action(
            rng=SequenceRNG([10, 1, 1, 1]),
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertEqual(result["defense_value"], defender_spec.defense)

    def test_psywave_deals_fixed_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Psywave",
            type="Psychic",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_spec = _pokemon_spec("Alakazam")
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([10, 1, 1, 4]),
        )
        battle.resolve_move_targets("ash-1", move, "gary-1", defender_state.position)
        event = next(evt for evt in battle.log if evt.get("effect") == "psywave")
        self.assertEqual(event.get("amount"), 40)

    def test_punishment_scales_db(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Punishment",
            type="Dark",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_spec = _pokemon_spec("Absol")
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        defender_state.combat_stages["atk"] = 2
        defender_state.combat_stages["spdef"] = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([10, 1, 1, 1]),
        )
        battle.resolve_move_targets("ash-1", move, "gary-1", defender_state.position)
        move_event = next(evt for evt in battle.log if evt.get("move") == "Punishment")
        self.assertEqual(move_event.get("effective_db"), 11)

    def test_purify_clears_statuses_and_heals(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Misdreavus"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        defender_state.statuses.append({"name": "Poisoned"})
        defender_state.statuses.append({"name": "Confused", "remaining": 1})
        attacker_state.hp = attacker_state.max_hp() - 20
        move = MoveSpec(
            name="Purify",
            type="Poison",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertFalse(defender_state.statuses)
        self.assertEqual(attacker_state.hp, attacker_state.max_hp() - 20 + attacker_state.tick_value() * 2)

    def test_pursuit_interrupt_triggers_on_switch(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        pursuit = MoveSpec(
            name="Pursuit",
            type="Dark",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_spec = _pokemon_spec("Absol")
        attacker_spec.moves = [pursuit]
        defender_spec = _pokemon_spec("Eevee")
        replacement_spec = _pokemon_spec("Vulpix")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0), active=True)
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1), active=True)
        replacement_state = PokemonState(spec=replacement_spec, controller_id=foe.identifier, position=None, active=False)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state, "gary-2": replacement_state},
            rng=SequenceRNG([10, 1, 1, 1]),
            grid=GridState(width=3, height=3),
        )
        hp_before = defender_state.hp
        battle._apply_switch(
            outgoing_id="gary-1",
            replacement_id="gary-2",
            initiator_id="gary-1",
            allow_replacement_turn=False,
            allow_immediate=False,
        )
        self.assertLess(defender_state.hp, hp_before)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "pursuit_interrupt"])

    def test_quash_moves_target_to_end(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        ally = TrainerState(identifier="misty", name="Misty")
        attacker_spec = _pokemon_spec("Sableye")
        attacker_spec.spd = 20
        target_spec = _pokemon_spec("Eevee")
        target_spec.spd = 10
        other_spec = _pokemon_spec("Pidgey")
        other_spec.spd = 5
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        target_state = PokemonState(spec=target_spec, controller_id=foe.identifier, position=(0, 1))
        other_state = PokemonState(spec=other_spec, controller_id=ally.identifier, position=(1, 0))
        move = MoveSpec(
            name="Quash",
            type="Dark",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe, ally.identifier: ally},
            pokemon={"ash-1": attacker_state, "gary-1": target_state, "misty-1": other_state},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=target_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(battle.initiative_order[-1].actor_id, "gary-1")

    def test_quick_attack_logs_priority(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Quick Attack",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=4,
        )
        self.assertTrue([evt for evt in events if evt.get("effect") == "priority_attack"])

    def test_quick_guard_blocks_priority(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        quick_guard = MoveSpec(
            name="Quick Guard",
            type="Fighting",
            category="Status",
            ac=2,
            range_kind="Self",
            range_value=0,
        )
        quick_attack = MoveSpec(
            name="Quick Attack",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            priority=1,
        )
        defender_spec = _pokemon_spec("Blaziken")
        defender_spec.moves = [quick_guard]
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.moves = [quick_attack]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([10, 1, 1]),
        )
        defender_state.statuses.append({"name": "Quick Guard"})
        hp_before = defender_state.hp
        battle.resolve_move_targets("ash-1", quick_attack, "gary-1", defender_state.position)
        self.assertEqual(defender_state.hp, hp_before)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "quick_guard"])

    def test_quiver_dance_raises_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Butterfree"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Quiver Dance",
            type="Bug",
            category="Status",
            ac=2,
            range_kind="Self",
            range_value=0,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["spatk"], 1)
        self.assertEqual(attacker_state.combat_stages["spdef"], 1)
        self.assertEqual(attacker_state.combat_stages["spd"], 1)

    def test_rage_enrages_and_raises_attack_on_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        rage = MoveSpec(
            name="Rage",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Charmander"), controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([10, 1, 10, 1]),
        )
        battle.resolve_move_targets("ash-1", rage, "gary-1", defender_state.position)
        self.assertTrue(attacker_state.has_status("Enraged"))
        battle.resolve_move_targets("gary-1", tackle, "ash-1", attacker_state.position)
        self.assertEqual(attacker_state.combat_stages["atk"], 1)

    def test_rage_powder_enrages_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Volcarona"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Rage Powder",
            type="Bug",
            category="Status",
            ac=2,
            range_kind="Burst",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(attacker_state.get_temporary_effects("follow_me"))
        self.assertTrue(defender_state.has_status("Enraged"))

    def test_raging_fury_enrages_target_on_16(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Arcanine"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Raging Fury",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 16},
            damage_dealt=6,
        )
        self.assertTrue(attacker_state.has_status("Enraged"))
        self.assertTrue(defender_state.has_status("Enraged"))

    def test_rain_dance_sets_weather(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Politoed"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Rain Dance",
            type="Water",
            category="Status",
            ac=2,
            range_kind="Field",
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(battle.weather, "Rain")

    def test_rapid_spin_clears_hazards_and_statuses(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Starmie"), controller_id=trainer.identifier, position=(0, 0))
        attacker_state.statuses.append({"name": "Trapped"})
        attacker_state.statuses.append({"name": "Leech Seed"})
        move = MoveSpec(
            name="Rapid Spin",
            type="Normal",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        grid = GridState(width=6, height=1, tiles={(2, 0): {"hazards": {"spikes": 1}}})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
            grid=grid,
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        self.assertFalse(attacker_state.has_status("Trapped"))
        self.assertFalse(attacker_state.has_status("Leech Seed"))
        self.assertNotIn("hazards", battle.grid.tiles.get((2, 0), {}))

    def test_rapid_spin_ss_raises_speed_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Starmie"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Rapid Spin [SS]",
            type="Normal",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        self.assertEqual(attacker_state.combat_stages["spd"], 1)

    def test_razor_leaf_crits_on_18(self) -> None:
        attacker_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id="ash")
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Razor Leaf",
            type="Grass",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        result = resolve_move_action(
            rng=SequenceRNG([18, 1, 1, 1]),
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertTrue(result["crit"])

    def test_razor_shell_lowers_defense_on_even(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Oshawott"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Razor Shell",
            type="Water",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 10},
            damage_dealt=7,
        )
        self.assertEqual(defender_state.combat_stages["def"], -1)

    def test_recover_heals_half_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Chansey"), controller_id=trainer.identifier)
        attacker_state.hp = attacker_state.max_hp() - 30
        move = MoveSpec(
            name="Recover",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Self",
            range_value=0,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        expected = min(attacker_state.max_hp(), attacker_state.max_hp() - 30 + attacker_state.max_hp() // 2)
        self.assertEqual(attacker_state.hp, expected)

    def test_attract_infatuates_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Clefairy"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        attacker_state.spec.gender = "male"
        defender_state.spec.gender = "female"
        move = MoveSpec(
            name="Attract",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=3,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": False},
            damage_dealt=0,
        )
        self.assertTrue(defender_state.has_status("Infatuated"))
        self.assertTrue([evt for evt in events if evt.get("status") == "Infatuated"])

    def test_aura_wheel_raises_speed_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Morpeko"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Aura Wheel",
            type="Electric",
            category="Physical",
            db=11,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state, "ash-2": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="ash-2",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=12,
        )
        self.assertEqual(attacker_state.combat_stages["spd"], 1)
        self.assertTrue([evt for evt in events if evt.get("effect") == "aura_wheel"])

    def test_aurora_beam_lowers_attack_on_18(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Seel"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Aurora Beam",
            type="Ice",
            category="Special",
            db=7,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 18},
            damage_dealt=8,
        )
        self.assertEqual(defender_state.combat_stages["atk"], -1)
        self.assertTrue([evt for evt in events if evt.get("effect") == "aurora_beam"])

    def test_aurora_veil_requires_hail(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally_state = PokemonState(spec=_pokemon_spec("Glaceon"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Aurora Veil",
            type="Ice",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": ally_state},
            weather="Clear",
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=ally_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": False},
            damage_dealt=0,
        )
        self.assertFalse(ally_state.has_status("Aurora Veil"))
        self.assertTrue([evt for evt in events if evt.get("effect") == "aurora_veil_fail"])

    def test_aurora_veil_applies_to_allies_in_hail(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally_one = PokemonState(spec=_pokemon_spec("Glaceon"), controller_id=trainer.identifier)
        ally_two = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Aurora Veil",
            type="Ice",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": ally_one, "ash-2": ally_two},
            weather="Hail",
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=ally_one,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": False},
            damage_dealt=0,
        )
        self.assertTrue(ally_one.has_status("Aurora Veil"))
        self.assertTrue(ally_two.has_status("Aurora Veil"))
        self.assertTrue([evt for evt in events if evt.get("effect") == "aurora_veil"])

    def test_autotomize_raises_speed_by_two(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_state = PokemonState(spec=_pokemon_spec("Magnemite"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Autotomize",
            type="Steel",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": False},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["spd"], 2)
        self.assertTrue([evt for evt in events if evt.get("effect") == "autotomize"])

    def test_avalanche_boosts_db_after_taking_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        avalanche = MoveSpec(
            name="Avalanche",
            type="Ice",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_spec = _pokemon_spec("Snover")
        attacker_spec.moves = [avalanche]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = [MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2, range_kind="Melee", range_value=1)]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([10, 1, 1, 1]),
        )
        battle.damage_taken_from = {"ash-1": {"gary-1"}}
        battle.resolve_move_targets("ash-1", avalanche, "gary-1", defender_state.position)
        move_event = next(evt for evt in battle.log if evt.get("move") == "Avalanche")
        self.assertEqual(move_event.get("effective_db"), 12)

    def test_baby_doll_eyes_lowers_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Spritzee"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Baby-Doll Eyes",
            type="Fairy",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=4,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(defender_state.combat_stages["atk"], -1)
        self.assertTrue([evt for evt in events if evt.get("effect") == "baby_doll_eyes"])

    def test_bane_ticks_for_three_turns(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Misdreavus"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Bane",
            type="Normal",
            category="Special",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([20]),
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        hp_before = defender_state.hp
        events = defender_state.handle_phase_effects(battle, TurnPhase.START, "gary-1")
        self.assertLess(defender_state.hp or 0, hp_before or 0)
        self.assertTrue([evt for evt in events if evt.get("effect") == "bane"])

    def test_baneful_bunker_blocks_and_poisons(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        bunker = MoveSpec(
            name="Baneful Bunker",
            type="Poison",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        defender_state = PokemonState(spec=_pokemon_spec("Seviper"), controller_id=foe.identifier, position=(0, 0))
        attacker_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier, position=(0, 1))
        attacker_state.spec.moves = [tackle]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([20, 1, 1]),
        )
        battle._handle_move_special_effects(
            attacker_id="gary-1",
            attacker=defender_state,
            defender_id=None,
            defender=None,
            move=bunker,
            result={"hit": False},
            damage_dealt=0,
        )
        hp_before = defender_state.hp
        battle.resolve_move_targets("ash-1", tackle, "gary-1", defender_state.position)
        self.assertEqual(defender_state.hp, hp_before)
        self.assertTrue(attacker_state.has_status("Poisoned"))
        self.assertFalse(defender_state.has_status("Baneful Bunker"))
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "baneful_bunker_block"])

    def test_barrier_places_segments_on_grid(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        barrier = MoveSpec(
            name="Barrier",
            type="Psychic",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Abra"), controller_id=trainer.identifier, position=(2, 2))
        grid = GridState(width=5, height=5)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
            grid=grid,
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=barrier,
            result={"hit": False},
            damage_dealt=0,
        )
        self.assertEqual(len(grid.blockers), 4)
        self.assertTrue([evt for evt in events if evt.get("effect") == "barrier"])

    def test_bash_sets_bashed_status_on_15(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Makuhita"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(
            name="Bash!",
            type="Normal",
            category="Physical",
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 15},
            damage_dealt=8,
        )
        self.assertTrue(defender_state.has_status("Bashed"))
        self.assertTrue([evt for evt in events if evt.get("effect") == "bash"])

    def test_after_you_reschedules_target_next_and_logs_event(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Charizard"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier)
        ally_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_state,
                "gary-1": defender_state,
                "ally-1": ally_state,
            },
        )
        battle.round = 7
        attacker_entry = InitiativeEntry(
            actor_id="ash-1",
            trainer_id=trainer.identifier,
            speed=15,
            trainer_modifier=0,
            roll=16,
            total=31,
        )
        ally_entry = InitiativeEntry(
            actor_id="ally-1",
            trainer_id=trainer.identifier,
            speed=12,
            trainer_modifier=0,
            roll=10,
            total=22,
        )
        defender_entry = InitiativeEntry(
            actor_id="gary-1",
            trainer_id=foe.identifier,
            speed=9,
            trainer_modifier=0,
            roll=8,
            total=17,
        )
        battle.initiative_order = [attacker_entry, ally_entry, defender_entry]
        battle._initiative_index = 0
        battle.current_actor_id = attacker_entry.actor_id
        move = MoveSpec(
            name="After You",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_value=1,
            freq="At-Will",
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        after_events = [evt for evt in events if evt.get("effect") == "after_you"]
        self.assertTrue(after_events)
        event = after_events[0]
        self.assertEqual(event.get("round"), 7)
        self.assertEqual(event.get("actor"), "ash-1")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(battle.initiative_order[1].actor_id, "gary-1")
        self.assertEqual(battle.initiative_order[2].actor_id, "ally-1")
        self.assertEqual(event.get("target_hp"), defender_state.hp)

    def test_acid_spray_lowers_spdef_by_two_stages(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Alb"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        move = MoveSpec(
            name="Acid Spray",
            type="Poison",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=4,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=6,
        )
        self.assertEqual(defender_state.combat_stages["spdef"], -2)
        acid_spray_events = [evt for evt in events if evt.get("effect") == "acid_spray_lower_spdef"]
        self.assertTrue(acid_spray_events)
        event = acid_spray_events[0]
        self.assertEqual(event.get("amount"), 2)
        self.assertEqual(event.get("duration"), 5)
        self.assertEqual(event.get("target"), "gary-1")

    def test_acid_chance_lowers_special_defense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Acid",
            type="Poison",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=4,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Haunter"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([5])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        self.assertEqual(defender_state.combat_stages["spdef"], -1)
        acid_events = [evt for evt in events if evt.get("effect") == "acid_lower_spdef"]
        self.assertTrue(acid_events)
        event = acid_events[0]
        self.assertEqual(event.get("roll"), 5)
        self.assertEqual(event.get("duration"), 5)

    def test_acid_fails_when_roll_full(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Acid",
            type="Poison",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=4,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Haunter"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([99])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        acid_events = [evt for evt in events if evt.get("effect") == "acid_lower_spdef"]
        self.assertFalse(acid_events)
        self.assertEqual(defender_state.combat_stages["spdef"], 0)

    def test_amnesia_raises_special_defense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Amnesia",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["spdef"], 2)
        self.assertTrue(any(evt.get("effect") == "amnesia" for evt in events))

    def test_apple_acid_lowers_target_spdef(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Apple Acid",
            type="Poison",
            category="Special",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Venusaur"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        self.assertEqual(defender_state.combat_stages["spdef"], -1)
        self.assertTrue(any(evt.get("effect") == "apple_acid" for evt in events))

    def test_ancient_power_raises_all_stats_on_high_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Ancient Power",
            type="Rock",
            category="Special",
            db=5,
            ac=3,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Tyranitar"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 19},
            damage_dealt=4,
        )
        self.assertTrue(all(stage == 1 for stage in attacker_state.combat_stages.values()))
        self.assertTrue(any(evt.get("effect") == "ancient_power" for evt in events))

    def test_anchor_shot_traps_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Anchor Shot",
            type="Steel",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Dhelmise"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=6,
        )
        trapped = [status for status in defender_state.statuses if isinstance(status, dict) and status.get("name", "").lower() == "trapped"]
        self.assertTrue(trapped)
        self.assertTrue(any(evt.get("effect") == "trapped" for evt in events))

    def test_air_cutter_crit_on_high_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Air Cutter",
            type="Flying",
            category="Special",
            db=6,
            ac=2,
            range_kind="Cone",
            range_value=2,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        rng = SequenceRNG([18, 3, 4, 2, 2])
        result = resolve_move_action(rng, attacker_state, defender_state, move)
        self.assertTrue(result.get("crit"))
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={**result, "hit": True},
            damage_dealt=10,
        )
        crit_events = [evt for evt in events if evt.get("effect") == "air_cutter_crit"]
        self.assertTrue(crit_events)
        self.assertEqual(crit_events[0].get("roll"), 18)

    def test_air_slash_applies_flinch_on_high_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Air Slash",
            type="Flying",
            category="Special",
            db=8,
            ac=3,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        rng = SequenceRNG([15, 4, 4, 4])
        result = resolve_move_action(rng, attacker_state, defender_state, move)
        self.assertTrue(result.get("hit"))
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result=result,
            damage_dealt=5,
        )
        self.assertTrue(defender_state.has_status("Flinch"))
        flinch_events = [evt for evt in events if evt.get("effect") == "flinch"]
        self.assertTrue(flinch_events)
        self.assertEqual(flinch_events[0].get("roll"), 15)

    def test_ally_switch_moves_user_and_ally_positions(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Ally Switch",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier)
        attacker_state.position = (0, 0)
        defender_state.position = (1, 0)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "ally-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="ally-1",
            defender=defender_state,
            move=move,
            result={"hit": False},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.position, (1, 0))
        self.assertEqual(defender_state.position, (0, 0))
        switch_events = [evt for evt in events if evt.get("effect") == "ally_switch"]
        self.assertTrue(switch_events)
        event = switch_events[0]
        self.assertEqual(event.get("from_position"), (0, 0))
        self.assertEqual(event.get("to_position"), (1, 0))
        self.assertEqual(event.get("target"), "ally-1")

    def test_aqua_jet_logs_priority(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Aqua Jet",
            type="Water",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        result = {"hit": True, "roll": 18}
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result=result,
            damage_dealt=5,
        )
        priority_events = [evt for evt in events if evt.get("effect") == "priority_attack"]
        self.assertTrue(priority_events)
        self.assertEqual(priority_events[0].get("move"), "Aqua Jet")

    def test_aqua_ring_heals_each_turn(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(name="Aqua Ring", type="Water", category="Status")
        attacker_state = PokemonState(spec=_pokemon_spec("Vaporeon"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        aqua_events = [evt for evt in events if evt.get("effect") == "aqua_ring"]
        self.assertTrue(aqua_events)
        heal_events = attacker_state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertTrue(any(evt.get("effect") == "aqua_ring" and evt.get("amount") >= 1 for evt in heal_events))

    def test_aqua_tail_pass_event(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Aqua Tail",
            type="Water",
            category="Physical",
            db=9,
            ac=4,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Blastoise"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=9,
        )
        pass_events = [evt for evt in events if evt.get("effect") == "aqua_tail_pass"]
        self.assertTrue(pass_events)

    def test_assist_chooses_ally_move(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Assist",
            type="Normal",
            category="Status",
            freq="Scene",
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        ally_state = PokemonState(spec=_pokemon_spec("Charizard"), controller_id=trainer.identifier)
        ally_state.spec.moves.append(MoveSpec(name="Flamethrower", type="Fire"))
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "ally-1": ally_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="ally-1",
            defender=ally_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        assist_events = [evt for evt in events if evt.get("effect") == "assist"]
        self.assertTrue(assist_events)
        self.assertIn(assist_events[0].get("selected_move"), {"Flamethrower", "Thunder Shock"})

    def test_aromatherapy_cures_allies(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(name="Aromatherapy", type="Grass", category="Status", freq="Scene")
        attacker_state = PokemonState(spec=_pokemon_spec("Breloom"), controller_id=trainer.identifier)
        ally_state = PokemonState(spec=_pokemon_spec("Blissey"), controller_id=trainer.identifier)
        ally_state.statuses = [{"name": "Poisoned"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "ally-1": ally_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="ally-1",
            defender=ally_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertFalse(ally_state.statuses)
        self.assertTrue(any(evt.get("effect") == "aromatherapy" for evt in events))

    def test_aromatic_mist_queue_spdef_boost(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(name="Aromatic Mist", type="Grass", category="Status")
        attacker_state = PokemonState(spec=_pokemon_spec("Venusaur"), controller_id=trainer.identifier)
        ally_state = PokemonState(spec=_pokemon_spec("Leafeon"), controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "ally-1": ally_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="ally-1",
            defender=ally_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["spdef"], 1)
        self.assertEqual(ally_state.combat_stages["spdef"], 1)
        self.assertTrue(any(evt.get("effect") == "aromatic_mist" for evt in events))

    def test_assurance_boost_triggers_event(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Assurance",
            type="Dark",
            category="Physical",
            db=6,
            ac=3,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Zoroark"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.damage_this_round.add("gary-1")
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 12},
            damage_dealt=5,
        )
        self.assertTrue(any(evt.get("effect") == "assurance_bonus" for evt in events))

    def test_arcane_fury_creates_vulnerable(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Arcane Fury",
            type="Normal",
            category="Special",
            db=3,
            ac=3,
            range_kind="Cone",
            range_value=2,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Espeon"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 19},
            damage_dealt=5,
        )
        self.assertTrue(any(evt.get("effect") == "vulnerable" for evt in events))
        self.assertTrue(defender_state.has_status("Vulnerable"))

    def test_arcane_storm_slows_and_vulnerable(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Arcane Storm",
            type="Normal",
            category="Special",
            db=6,
            ac=2,
            range_kind="WR",
            range_value=3,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Espeon"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True, "roll": 15},
            damage_dealt=8,
        )
        self.assertTrue(defender_state.has_status("Vulnerable"))
        self.assertTrue(defender_state.has_status("Slowed"))
        self.assertTrue(any(evt.get("effect") == "arcane_storm" for evt in events))
    def test_acrobatics_applies_no_item_damage_base(self) -> None:
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="player")
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id="foe")
        move = MoveSpec(
            name="Acrobatics",
            type="Flying",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        rng = SequenceRNG([10, 11, 12, 13, 14])
        result = resolve_move_action(
            rng=rng,
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertEqual(result.get("effective_db"), 11)
        roll_options = result.get("context", {}).get("roll_options", [])
        self.assertIn("acrobatics:no-item", roll_options)

    def test_acrobatics_no_bonus_when_holding_item(self) -> None:
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="player")
        attacker_state.spec.items.append({"name": "Choice Band"})
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id="foe")
        move = MoveSpec(
            name="Acrobatics",
            type="Flying",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        rng = SequenceRNG([10, 11, 12, 13, 14])
        result = resolve_move_action(
            rng=rng,
            attacker=attacker_state,
            defender=defender_state,
            move=move,
        )
        self.assertEqual(result.get("effective_db"), 6)
        roll_options = result.get("context", {}).get("roll_options", [])
        self.assertNotIn("acrobatics:no-item", roll_options)

    def test_reaction_move_cannot_be_declared_as_normal_turn_action(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Wobbuffet")
        attacker_spec.moves = [
            MoveSpec(
                name="Counter",
                type="Fighting",
                category="Physical",
                db=0,
                ac=None,
                freq="Scene x2",
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                range_text="Melee, 1 Target, Reaction, Trigger",
            )
        ]
        defender_spec = _pokemon_spec("Scyther")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="ash-1", move_name="Counter", target_id="gary-1").validate(battle)

    def test_counter_triggers_as_reaction_after_physical_hit(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[
                MoveSpec(
                    name="Tackle",
                    type="Normal",
                    category="Physical",
                    db=8,
                    ac=2,
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                )
            ],
            defender_moves=[
                MoveSpec(
                    name="Counter",
                    type="Fighting",
                    category="Physical",
                    db=0,
                    ac=None,
                    freq="Scene x2",
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                    range_text="Melee, 1 Target, Reaction, Trigger",
                )
            ],
            attacker_species="Scyther",
            defender_species="Wobbuffet",
            rng=MaxRNG(),
        )

        attacker_before = battle.pokemon["ash-1"].hp
        UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1").resolve(battle)

        self.assertLess(battle.pokemon["ash-1"].hp or 0, attacker_before or 0)
        self.assertTrue(any(evt.get("effect") == "counter" for evt in battle.log))

    def test_mirror_coat_triggers_as_reaction_after_special_hit(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[
                MoveSpec(
                    name="Ember",
                    type="Fire",
                    category="Special",
                    db=6,
                    ac=2,
                    range_kind="Range",
                    range_value=6,
                    target_kind="Ranged",
                    target_range=6,
                )
            ],
            defender_moves=[
                MoveSpec(
                    name="Mirror Coat",
                    type="Psychic",
                    category="Special",
                    db=0,
                    ac=None,
                    freq="Scene x2",
                    range_kind="Range",
                    range_value=6,
                    target_kind="Ranged",
                    target_range=6,
                    range_text="Range 6, 1 Target, Reaction, Trigger",
                )
            ],
            attacker_species="Charmander",
            defender_species="Wobbuffet",
            attacker_types=["Fire"],
            defender_types=["Normal"],
            rng=MaxRNG(),
        )

        attacker_before = battle.pokemon["ash-1"].hp
        UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1").resolve(battle)

        self.assertLess(battle.pokemon["ash-1"].hp or 0, attacker_before or 0)
        self.assertTrue(any(evt.get("effect") == "mirror_coat" for evt in battle.log))

    def test_endure_triggers_as_reaction_before_damage_applies(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[
                MoveSpec(
                    name="Mega Punch",
                    type="Normal",
                    category="Physical",
                    db=10,
                    ac=2,
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                )
            ],
            defender_moves=[
                MoveSpec(
                    name="Endure",
                    type="Normal",
                    category="Status",
                    db=0,
                    ac=None,
                    freq="Scene x2",
                    range_kind="Self",
                    range_value=None,
                    target_kind="Self",
                    target_range=0,
                    range_text="Self, Reaction, Trigger",
                )
            ],
            rng=MaxRNG(),
        )
        battle.pokemon["gary-1"].hp = 4

        UseMoveAction(actor_id="ash-1", move_name="Mega Punch", target_id="gary-1").resolve(battle)

        self.assertEqual(battle.pokemon["gary-1"].hp, 1)
        self.assertTrue(any(evt.get("status") == "Endure" for evt in battle.log))

    def test_vital_throw_triggers_as_reaction_before_defender_turn(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[
                MoveSpec(
                    name="Scratch",
                    type="Normal",
                    category="Physical",
                    db=6,
                    ac=2,
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                )
            ],
            defender_moves=[
                MoveSpec(
                    name="Vital Throw",
                    type="Fighting",
                    category="Physical",
                    db=8,
                    ac=20,
                    freq="At-Will",
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                    range_text="Melee, 1 Target, Reaction, Trigger",
                )
            ],
            attacker_spd=14,
            defender_spd=8,
            rng=MaxRNG(),
        )

        attacker_before = battle.pokemon["ash-1"].hp
        UseMoveAction(actor_id="ash-1", move_name="Scratch", target_id="gary-1").resolve(battle)

        self.assertLess(battle.pokemon["ash-1"].hp or 0, attacker_before or 0)
        self.assertTrue(
            any(evt.get("move") == "Vital Throw" and evt.get("actor") == "gary-1" for evt in battle.log)
        )

    def test_riposte_triggers_as_reaction_after_melee_miss(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[
                MoveSpec(
                    name="Slash",
                    type="Normal",
                    category="Physical",
                    db=7,
                    ac=2,
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                )
            ],
            defender_moves=[
                MoveSpec(
                    name="Riposte",
                    type="Steel",
                    category="Physical",
                    db=7,
                    ac=20,
                    freq="At-Will",
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                    range_text="Melee, 1 Target, Reaction, Trigger",
                )
            ],
            rng=SequenceRNG([1, 20, 20, 20, 20]),
        )

        attacker_before = battle.pokemon["ash-1"].hp
        UseMoveAction(actor_id="ash-1", move_name="Slash", target_id="gary-1").resolve(battle)

        self.assertLess(battle.pokemon["ash-1"].hp or 0, attacker_before or 0)
        self.assertTrue(any(evt.get("move") == "Riposte" and evt.get("actor") == "gary-1" for evt in battle.log))

    def test_bide_triggers_as_reaction_and_stores_triggering_damage(self) -> None:
        battle = _two_pokemon_battle(
            attacker_moves=[
                MoveSpec(
                    name="Tackle",
                    type="Normal",
                    category="Physical",
                    db=8,
                    ac=2,
                    range_kind="Melee",
                    range_value=1,
                    target_kind="Melee",
                    target_range=1,
                )
            ],
            defender_moves=[
                MoveSpec(
                    name="Bide",
                    type="Normal",
                    category="Status",
                    db=0,
                    ac=None,
                    freq="Scene x2",
                    range_kind="Self",
                    range_value=None,
                    target_kind="Self",
                    target_range=0,
                    range_text="Self, Reaction, Trigger",
                )
            ],
            rng=MaxRNG(),
        )

        UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1").resolve(battle)

        charges = battle.pokemon["gary-1"].get_temporary_effects("bide_charge")
        self.assertTrue(charges)
        self.assertGreater(int(charges[0].get("damage", 0) or 0), 0)

    def test_eot_move_cannot_be_used_twice_in_same_round(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rampardos")
        attacker_spec.moves = [
            MoveSpec(
                name="Stone Edge",
                type="Rock",
                category="Physical",
                db=10,
                ac=2,
                freq="EOT",
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                range_text="Melee, 1 Target",
            )
        ]
        defender_spec = _pokemon_spec("Scyther")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20]),
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Stone Edge", target_id="gary-1")
        action.resolve(battle)
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="ash-1", move_name="Stone Edge", target_id="gary-1").validate(battle)
        battle.start_round()
        UseMoveAction(actor_id="ash-1", move_name="Stone Edge", target_id="gary-1").validate(battle)

    def test_choice_suppressed_item_blocks_consecutive_limited_move_rounds(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rampardos")
        attacker_spec.items = [{"name": "Choice Band"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Stone Edge",
                type="Rock",
                category="Physical",
                db=10,
                ac=2,
                freq="EOT",
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                range_text="Melee, 1 Target",
            )
        ]
        defender_spec = _pokemon_spec("Scyther")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20, 20]),
        )
        original_get_item_entry = battle_state_module.get_item_entry
        battle_state_module.get_item_entry = lambda name: battle_state_module.ItemEntry(
            name=name,
            description="Default Attack stage +2. Choice-Locked 3. Suppressed.",
        )
        try:
            UseMoveAction(actor_id="ash-1", move_name="Stone Edge", target_id="gary-1").resolve(battle)
            self.assertTrue(battle.pokemon["ash-1"].has_status("Suppressed"))
            battle.start_round()
            with self.assertRaises(ValueError):
                UseMoveAction(actor_id="ash-1", move_name="Stone Edge", target_id="gary-1").validate(battle)
        finally:
            battle_state_module.get_item_entry = original_get_item_entry

    def test_eviolite_applies_held_item_defense_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        base_spec = _pokemon_spec("Dusclops")
        base_spec.defense = 10
        base_spec.spdef = 10
        battle_plain = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=copy.deepcopy(base_spec), controller_id=trainer.identifier, position=(0, 0))},
        )
        plain = battle_plain.pokemon["ash-1"]
        original_get_item_entry = battle_state_module.get_item_entry
        battle_state_module.get_item_entry = lambda name: battle_state_module.ItemEntry(
            name=name,
            description="Improves base Defense by 2 and base Special Defense by 2.",
        )
        try:
            held_spec = copy.deepcopy(base_spec)
            held_spec.items = [{"name": "Eviolite"}]
            battle_held = BattleState(
                trainers={trainer.identifier: trainer},
                pokemon={"ash-2": PokemonState(spec=held_spec, controller_id=trainer.identifier, position=(0, 0))},
            )
            held = battle_held.pokemon["ash-2"]
            self.assertEqual(defensive_stat(held, "physical"), defensive_stat(plain, "physical") + 2)
            self.assertEqual(defensive_stat(held, "special"), defensive_stat(plain, "special") + 2)
        finally:
            battle_state_module.get_item_entry = original_get_item_entry

    # Legacy Acrobatics checks were replaced by the new coverage above.

    def test_acupressure_raises_specific_stat_via_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Acupressure",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([3])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["spatk"], 2)
        effect_events = [evt for evt in events if evt.get("effect") == "acupressure_boost"]
        self.assertTrue(effect_events)
        self.assertEqual(effect_events[0].get("stat"), "spatk")

    def test_acupressure_roll_eight_chooses_lowest_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Acupressure",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        attacker_state.combat_stages["spd"] = 1
        attacker_state.combat_stages["accuracy"] = -2
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([8])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["accuracy"], 0)
        effect_events = [evt for evt in events if evt.get("effect") == "acupressure_boost"]
        self.assertTrue(effect_events)
        self.assertEqual(effect_events[0].get("stat"), "accuracy")

    def test_acid_spray_lowers_spdef_by_two(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Acid Spray",
            type="Poison",
            category="Special",
            db=4,
            ac=2,
            range_kind="Cone",
            range_value=3,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Haunter"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=6,
        )
        self.assertEqual(defender_state.combat_stages["spdef"], -2)
        acid_spray_events = [evt for evt in events if evt.get("effect") == "acid_spray_lower_spdef"]
        self.assertTrue(acid_spray_events)
        event = acid_spray_events[0]
        self.assertEqual(event.get("amount"), 2)
        self.assertEqual(event.get("duration"), 5)

    def test_acid_spray_clamps_stage_lower_bound(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Acid Spray",
            type="Poison",
            category="Special",
            db=4,
            ac=2,
            range_kind="Cone",
            range_value=3,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Haunter"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        defender_state.combat_stages["spdef"] = -5
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=6,
        )
        self.assertEqual(defender_state.combat_stages["spdef"], -6)
        acid_spray_events = [evt for evt in events if evt.get("effect") == "acid_spray_lower_spdef"]
        self.assertTrue(acid_spray_events)
        self.assertEqual(acid_spray_events[0].get("amount"), 1)

    def test_fissure_instantly_faints_on_successful_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Garchomp")
        move = MoveSpec(
            name="Fissure",
            type="Ground",
            category="Status",
            db=None,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        defender_state.hp = 25
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([15])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue(defender_state.fainted)
        fissure_events = [evt for evt in events if evt.get("effect") == "fissure"]
        self.assertTrue(fissure_events)
        self.assertEqual(fissure_events[0].get("roll"), 15)

    def test_fissure_fails_on_high_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Garchomp")
        move = MoveSpec(
            name="Fissure",
            type="Ground",
            category="Status",
            db=None,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        defender_state.hp = 25
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([99])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertFalse(defender_state.fainted)
        fissure_events = [evt for evt in events if evt.get("effect") == "fissure"]
        self.assertFalse(fissure_events)

    def test_agility_boosts_speed_two_stages(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Agility",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
        )
        attacker_state = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([5])
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker_state.combat_stages["spd"], 2)
        agility_events = [evt for evt in events if evt.get("effect") == "agility"]
        self.assertTrue(agility_events)
        event = agility_events[0]
        self.assertEqual(event.get("stat"), "spd")
        self.assertEqual(event.get("amount"), 2)
        self.assertEqual(event.get("new_stage"), 2)
        self.assertEqual(event.get("target_hp"), attacker_state.hp)

    def test_fishious_rend_bonuses_targets_who_act_later(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Greninja")
        move = MoveSpec(
            name="Fishious Rend",
            type="Water",
            category="Physical",
            db=9,
            ac=3,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        defender_state.hp = 25
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.initiative_order = [
            InitiativeEntry(
                actor_id="ash-1",
                trainer_id=trainer.identifier,
                speed=15,
                trainer_modifier=0,
                roll=12,
                total=27,
            ),
            InitiativeEntry(
                actor_id="gary-1",
                trainer_id=defender.identifier,
                speed=10,
                trainer_modifier=0,
                roll=3,
                total=13,
            ),
        ]
        battle._initiative_index = 0
        battle.current_actor_id = "ash-1"
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=5,
        )
        self.assertEqual(defender_state.hp, 15)
        bonus_events = [evt for evt in events if evt.get("effect") == "fishious_rend_bonus"]
        self.assertTrue(bonus_events)
        self.assertEqual(bonus_events[0].get("amount"), 10)

    def test_fake_tears_lowers_special_defense_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Umbreon")
        move = MoveSpec(
            name="Fake Tears",
            type="Dark",
            category="Status",
            db=0,
            ac=3,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Squirtle"), controller_id=defender.identifier)
        defender_state.combat_stages["spdef"] = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(defender_state.combat_stages["spdef"], -1)
        stage_events = [evt for evt in events if evt.get("stat") == "spdef"]
        self.assertTrue(stage_events)
        self.assertEqual(stage_events[0].get("amount"), 2)

    def test_final_gambit_self_destructs_and_deals_hp_lost_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        defender = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Hawlucha")
        move = MoveSpec(
            name="Final Gambit",
            type="Fighting",
            category="Special",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=defender.identifier)
        attacker_state.hp = 8
        defender_state.hp = 30
        battle = BattleState(
            trainers={trainer.identifier: trainer, defender.identifier: defender},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        defender_state.apply_damage(3)
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
            result={"hit": True},
            damage_dealt=3,
        )
        self.assertEqual(attacker_state.hp, 0)
        self.assertEqual(defender_state.hp, 22)
        final_events = [evt for evt in events if evt.get("effect") == "final_gambit"]
        self.assertTrue(final_events)
        event = final_events[0]
        self.assertEqual(event.get("hp_lost"), 8)
        self.assertEqual(event.get("damage"), 8)
        self.assertEqual(event.get("attacker_hp"), 0)

    def test_flame_body_burns_attacker_on_contact(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Charizard")
        defender_spec.abilities = [{"name": "Flame Body"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([5])
        battle.rng.seed(0)
        move = _contact_move_spec()
        events = battle._handle_contact_ability_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
        )
        flame_events = [evt for evt in events if evt.get("ability") == "Flame Body"]
        self.assertTrue(flame_events)
        flame_event = flame_events[-1]
        self.assertEqual(flame_event["effect"], "status")
        self.assertEqual(flame_event["status"], "Burned")
        self.assertEqual(flame_event["move"], "Tackle")
        self.assertEqual(flame_event["target"], "ash-1")
        self.assertEqual(flame_event["actor"], "gary-1")
        self.assertEqual(flame_event["roll"], 5)
        self.assertTrue(attacker_state.has_status("Burned"))

    def test_static_paralyzes_attacker_on_contact(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Gastrodon")
        defender_spec.abilities = [{"name": "Static"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([12])
        battle.rng.seed(1)
        move = _contact_move_spec()
        events = battle._handle_contact_ability_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
        )
        static_events = [evt for evt in events if evt.get("ability") == "Static"]
        self.assertTrue(static_events)
        static_event = static_events[-1]
        self.assertEqual(static_event["effect"], "status")
        self.assertEqual(static_event["status"], "Paralyzed")
        self.assertEqual(static_event["move"], "Tackle")
        self.assertTrue(attacker_state.has_status("Paralyzed"))

    def test_poison_point_poisons_attacker_on_contact(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Nidorino")
        defender_spec.abilities = [{"name": "Poison Point"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([9])
        battle.rng.seed(2)
        move = _contact_move_spec()
        events = battle._handle_contact_ability_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
        )
        poison_events = [evt for evt in events if evt.get("ability") == "Poison Point"]
        self.assertTrue(poison_events)
        poison_event = poison_events[-1]
        self.assertEqual(poison_event["effect"], "status")
        self.assertEqual(poison_event["status"], "Poisoned")
        self.assertEqual(poison_event["move"], "Tackle")
        self.assertTrue(attacker_state.has_status("Poisoned"))

    def test_rough_skin_triggers_contact_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Rhydon")
        defender_spec.abilities = [{"name": "Rough Skin"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.rng = SequenceRNG([])
        move = _contact_move_spec()
        before_hp = attacker_state.hp or 0
        events = battle._handle_contact_ability_effects(
            attacker_id="ash-1",
            attacker=attacker_state,
            defender_id="gary-1",
            defender=defender_state,
            move=move,
        )
        damage_events = [evt for evt in events if evt.get("effect") == "contact_damage"]
        self.assertTrue(damage_events)
        damage_event = damage_events[-1]
        self.assertEqual(damage_event["ability"], "Rough Skin")
        self.assertGreater(damage_event["amount"], 0)
        self.assertEqual(damage_event["target"], "ash-1")
        self.assertEqual(damage_event["actor"], "gary-1")
        self.assertEqual(before_hp - (attacker_state.hp or 0), damage_event["amount"])

    def test_badly_poisoned_damage_increases_each_turn(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier)
        target.statuses.append({"name": "Badly Poisoned"})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            rng=random.Random(2),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        for _ in range(3):
            battle.advance_phase()
        first_hp = target.hp
        start_hp = target.max_hp()
        self.assertEqual(first_hp, start_hp - 5)
        battle.end_turn()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        for _ in range(3):
            battle.advance_phase()
        second_hp = target.hp
        self.assertEqual(second_hp, (first_hp or 0) - 10)

    def test_badly_poisoned_stacks_increment_each_cycle(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier, position=(0, 0))
        target.statuses.append({"name": "Badly Poisoned"})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            rng=random.Random(3),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        for _ in range(3):
            battle.advance_phase()
        battle.end_turn()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        for _ in range(3):
            battle.advance_phase()
        stack_events = [
            evt for evt in battle.log if evt.get("status") == "badly poisoned" and evt.get("effect") == "damage"
        ]
        self.assertGreaterEqual(len(stack_events), 2)
        self.assertEqual(stack_events[0].get("stacks"), 1)
        self.assertEqual(stack_events[1].get("stacks"), 2)

    def test_badly_poisoned_damage_doubles_each_round(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier, position=(0, 0))
        target.statuses.append({"name": "Badly Poisoned"})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            rng=random.Random(4),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        start_hp = target.hp
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        for _ in range(3):
            battle.advance_phase()
        first_hp = target.hp
        self.assertEqual(start_hp - (first_hp or 0), 5)
        battle.end_turn()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action="shift"))
        battle.resolve_next_action()
        for _ in range(3):
            battle.advance_phase()
        second_hp = target.hp
        self.assertEqual((first_hp or 0) - (second_hp or 0), 10)

    def test_volatile_statuses_clear_on_faint(self) -> None:
        target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="ash")
        target.statuses.append({"name": "Confused"})
        target.statuses.append({"name": "Flinch"})
        target.apply_damage(target.max_hp())
        self.assertFalse(target.has_status("Confused"))
        self.assertFalse(target.has_status("Flinch"))

    def test_volatile_statuses_clear_on_switch(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        active = _pokemon_spec("Pikachu")
        bench = _pokemon_spec("Bulbasaur")
        active_state = PokemonState(
            spec=active,
            controller_id=trainer.identifier,
            position=(1, 1),
            active=True,
        )
        active_state.statuses.append({"name": "Confused"})
        bench_state = PokemonState(spec=bench, controller_id=trainer.identifier, position=None, active=False)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": active_state, "ash-2": bench_state},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(SwitchAction(actor_id="ash-1", replacement_id="ash-2"))
        battle.resolve_next_action()
        self.assertFalse(active_state.has_status("Confused"))

    def test_spikes_damage_applies_once_per_turn(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Onix"), controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"spikes": 2}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        damage = math.ceil(target.max_hp() * 0.16666666666666666)
        self.assertEqual(target.hp, target.max_hp() - damage)
        hazard_events = [
            evt for evt in battle.log if evt.get("type") == "hazard" and evt.get("hazard") == "spikes"
        ]
        self.assertTrue(hazard_events)
        self.assertEqual(hazard_events[-1]["amount"], damage)
        battle.end_turn()
        _advance_to_pokemon_turn(battle)
        self.assertEqual(target.hp, target.max_hp() - damage)

    def test_toxic_spikes_apply_badly_poisoned_with_two_layers(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"toxic_spikes": 2}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        self.assertTrue(target.has_status("Badly Poisoned"))
        status_events = [
            evt for evt in battle.log if evt.get("status") == "badly poisoned" and evt.get("hazard") == "toxic_spikes"
        ]
        self.assertTrue(status_events)

    def test_toxic_spikes_logs_when_no_new_status_is_applied(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier, position=(0, 0))
        target.statuses.append({"name": "Poisoned"})
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"toxic_spikes": 1}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        hazard_events = [
            evt for evt in battle.log if evt.get("hazard") == "toxic_spikes" and evt.get("effect") == "no_effect"
        ]
        self.assertTrue(hazard_events)

    def test_toxic_applies_badly_poisoned_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Toxic",
                type="Poison",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Rattata")
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(1, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Toxic", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender.has_status("Badly Poisoned"))
        status_events = [
            evt
            for evt in battle.log
            if evt.get("status") == "Badly Poisoned" and evt.get("move") == "Toxic"
        ]
        self.assertTrue(status_events)

    def test_toxic_skips_poisoned_targets_through_immunity(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Toxic",
                type="Poison",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Grimer")
        defender_spec.types = ["Poison"]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(1, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Toxic", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(defender.has_status("Badly Poisoned"))
        status_events = [
            evt
            for evt in battle.log
            if evt.get("status") == "Badly Poisoned" and evt.get("move") == "Toxic"
        ]
        self.assertFalse(status_events)

    def test_sticky_web_drops_speed_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"sticky_web": 1}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        self.assertEqual(target.combat_stages["spd"], -1)
        hazard_events = [
            evt for evt in battle.log if evt.get("hazard") == "sticky_web" and evt.get("effect") == "speed_drop"
        ]
        self.assertTrue(hazard_events)

    def test_sticky_web_logs_when_speed_cannot_drop_further(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier, position=(0, 0))
        target.combat_stages["spd"] = -6
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"sticky_web": 1}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        self.assertEqual(target.combat_stages["spd"], -6)
        hazard_events = [
            evt for evt in battle.log if evt.get("hazard") == "sticky_web" and evt.get("effect") == "speed_floor"
        ]
        self.assertTrue(hazard_events)

    def test_sticky_web_logs_when_already_triggered_on_same_tile(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier, position=(0, 0))
        target.add_temporary_effect("hazard_coord", coord=(0, 0))
        target.add_temporary_effect("hazard", hazard="sticky_web", coord=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"sticky_web": 1}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        hazard_events = [
            evt for evt in battle.log if evt.get("hazard") == "sticky_web" and evt.get("effect") == "already_triggered"
        ]
        self.assertTrue(hazard_events)

    def test_ground_hazard_logs_when_target_is_ungrounded(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=trainer.identifier, position=(0, 0))
        target.statuses.append({"name": "Magnet Rise"})
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"sticky_web": 1}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        hazard_events = [
            evt for evt in battle.log if evt.get("hazard") == "sticky_web" and evt.get("effect") == "hazard_block"
        ]
        self.assertTrue(hazard_events)

    def test_levitate_ignores_ground_hazards(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Rotom")
        spec.abilities = [{"name": "Levitate"}]
        target = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"spikes": 1}}})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        self.assertEqual(target.hp, target.max_hp())
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Levitate"
        ]
        self.assertTrue(ability_events)

    def test_area_line_respects_wall_blocking(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.spd = 20
        attacker_spec.moves = [
            MoveSpec(
                name="Line Test",
                type="Normal",
                category="Special",
                db=4,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                area_kind="Line",
                area_value=4,
                freq="At-Will",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec,
            controller_id=trainer.identifier,
            position=(0, 0),
        )
        target_state = PokemonState(
            spec=_pokemon_spec("Bulbasaur"),
            controller_id=foe.identifier,
            position=(1, 0),
        )
        target_state.spec.spd = 5
        blocked_state = PokemonState(
            spec=_pokemon_spec("Charmander"),
            controller_id=foe.identifier,
            position=(3, 0),
        )
        blocked_state.spec.spd = 5
        grid = GridState(width=5, height=1, tiles={(2, 0): {"type": "wall"}})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_state,
                "gary-1": target_state,
                "gary-2": blocked_state,
            },
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        action = UseMoveAction(actor_id="ash-1", move_name="Line Test", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertLess(target_state.hp or 0, target_state.max_hp())
        self.assertEqual(blocked_state.hp, blocked_state.max_hp())

    def test_levitate_blocks_ground_moves(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        ground_attacker = _pokemon_spec("Rhyhorn")
        ground_attacker.moves = [
            MoveSpec(name="Rock Slide", type="Ground", category="Physical", range_kind="Melee", freq="At-Will")
        ]
        attacker_state = PokemonState(spec=ground_attacker, controller_id=trainer.identifier, position=(0, 0))
        defender_spec = _pokemon_spec("Rotom")
        defender_spec.abilities = [{"name": "Levitate"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Rock Slide", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        move_events = [
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Rock Slide"
        ]
        self.assertTrue(move_events)
        self.assertFalse(move_events[-1]["hit"])
        self.assertEqual(defender_state.hp, defender_state.max_hp())
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Levitate"
        ]
        self.assertTrue(ability_events)

    def test_lightning_rod_redirects_and_boosts_spatk(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Thunder Shock",
                type="Electric",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        target_state = PokemonState(
            spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)
        )
        rod_spec = _pokemon_spec("Raichu")
        rod_spec.abilities = [{"name": "Lightning Rod"}]
        rod_state = PokemonState(
            spec=rod_spec, controller_id=foe.identifier, position=(0, 2)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": target_state, "gary-2": rod_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(target_state.hp, target_state.max_hp())
        self.assertEqual(rod_state.hp, rod_state.max_hp())
        self.assertEqual(rod_state.combat_stages["spatk"], 1)
        move_events = [
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Thunder Shock"
        ]
        self.assertTrue(move_events)
        self.assertEqual(move_events[-1]["target"], "gary-2")
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Lightning Rod"
        ]
        self.assertTrue(ability_events)

    def test_water_absorb_heals_and_blocks_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Squirtle")
        attacker_spec.moves = [
            MoveSpec(
                name="Water Pulse",
                type="Water",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_spec = _pokemon_spec("Vaporeon")
        defender_spec.abilities = [{"name": "Water Absorb"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        defender_state.hp = defender_state.max_hp() - defender_state.tick_value()
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Water Pulse", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, defender_state.max_hp())
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Water Absorb"
        ]
        self.assertTrue(ability_events)

    def test_volt_absorb_heals_and_blocks_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Thunder Shock",
                type="Electric",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_spec = _pokemon_spec("Chinchou")
        defender_spec.abilities = [{"name": "Volt Absorb"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        defender_state.hp = defender_state.max_hp() - defender_state.tick_value()
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, defender_state.max_hp())
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Volt Absorb"
        ]
        self.assertTrue(ability_events)

    def test_soundproof_blocks_sonic_moves(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Whismur")
        attacker_spec.moves = [
            MoveSpec(
                name="Echoed Voice",
                type="Normal",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
                keywords=["Sonic"],
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_spec = _pokemon_spec("Mr. Mime")
        defender_spec.abilities = [{"name": "Soundproof"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Echoed Voice", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, defender_state.max_hp())
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Soundproof"
        ]
        self.assertTrue(ability_events)

    def test_wonder_guard_blocks_neutral_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="At-Will",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_spec = _pokemon_spec("Shedinja")
        defender_spec.types = ["Bug"]
        defender_spec.abilities = [{"name": "Wonder Guard"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, defender_state.max_hp())
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Wonder Guard"
        ]
        self.assertTrue(ability_events)

    def test_mirror_armor_reflects_combat_stage_drop(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgey")
        defender_spec = _pokemon_spec("Corviknight")
        defender_spec.abilities = [{"name": "Mirror Armor"}]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._apply_combat_stage(
            [],
            attacker_id="ash-1",
            target_id="gary-1",
            move=MoveSpec(name="Screech", type="Normal", category="Status"),
            target=defender_state,
            stat="def",
            delta=-2,
            description="Test drop.",
        )
        self.assertEqual(defender_state.combat_stages["def"], 0)
        self.assertEqual(attacker_state.combat_stages["def"], -2)

    def test_full_metal_body_blocks_combat_stage_drop(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Magnemite")
        defender_spec = _pokemon_spec("Metagross")
        defender_spec.abilities = [{"name": "Full Metal Body"}]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle._apply_combat_stage(
            [],
            attacker_id="ash-1",
            target_id="gary-1",
            move=MoveSpec(name="Growl", type="Normal", category="Status"),
            target=defender_state,
            stat="atk",
            delta=-1,
            description="Test drop.",
        )
        self.assertEqual(defender_state.combat_stages["atk"], 0)

    def test_electric_surge_sets_terrain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Tapu Koko")
        attacker_spec.abilities = [{"name": "Electric Surge"}]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Electric Surge", target_id="ash-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(battle.terrain.get("name"), "Electric Terrain")
        self.assertEqual(battle.terrain.get("remaining"), 1)

    def test_sturdy_prevents_full_hp_ko(self) -> None:
        class MidRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machamp")
        attacker_spec.atk = 12
        attacker_spec.moves = [
            MoveSpec(
                name="Giga Impact",
                type="Normal",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="Daily",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_spec = _pokemon_spec("Geodude")
        defender_spec.defense = 2
        defender_spec.abilities = [{"name": "Sturdy"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=MidRNG(),
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Giga Impact", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, 1)
        self.assertFalse(defender_state.fainted)
        self.assertEqual(defender_state.injuries, 0)
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Sturdy"
        ]
        self.assertTrue(ability_events)

    def test_intimidate_triggers_on_entry(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        intimidator_spec = _pokemon_spec("Arbok")
        intimidator_spec.abilities = [{"name": "Intimidate"}]
        intimidator_state = PokemonState(
            spec=intimidator_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        foe_state = PokemonState(
            spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": intimidator_state, "gary-1": foe_state},
        )
        battle.start_round()
        self.assertEqual(foe_state.combat_stages["atk"], -1)
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Intimidate"
        ]
        self.assertTrue(ability_events)

    def test_multiple_intimidates_trigger_in_same_round(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")

        intimidator_a_spec = _pokemon_spec("Arbok")
        intimidator_a_spec.abilities = [{"name": "Intimidate"}]
        intimidator_b_spec = _pokemon_spec("Mightyena")
        intimidator_b_spec.abilities = [{"name": "Intimidate"}]

        intimidator_a = PokemonState(
            spec=intimidator_a_spec,
            controller_id=trainer.identifier,
            position=(0, 0),
            active=True,
        )
        intimidator_b = PokemonState(
            spec=intimidator_b_spec,
            controller_id=trainer.identifier,
            position=(0, 1),
            active=True,
        )
        foe_a = PokemonState(
            spec=_pokemon_spec("Rattata"),
            controller_id=foe.identifier,
            position=(1, 0),
            active=True,
        )
        foe_b = PokemonState(
            spec=_pokemon_spec("Pidgey"),
            controller_id=foe.identifier,
            position=(1, 1),
            active=True,
        )

        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": intimidator_a,
                "ash-2": intimidator_b,
                "gary-1": foe_a,
                "gary-2": foe_b,
            },
            active_slots=2,
        )
        battle.start_round()

        self.assertEqual(foe_a.combat_stages["atk"], -2)
        self.assertEqual(foe_b.combat_stages["atk"], -2)

        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Intimidate"
        ]
        pairs = {(evt.get("actor"), evt.get("target")) for evt in ability_events}
        self.assertSetEqual(
            pairs,
            {
                ("ash-1", "gary-1"),
                ("ash-1", "gary-2"),
                ("ash-2", "gary-1"),
                ("ash-2", "gary-2"),
            },
        )

    def test_soul_heart_triggers_for_multiple_allies_on_same_faint(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")

        attacker_spec = _pokemon_spec("Kirlia")
        attacker_spec.abilities = [{"name": "Soul Heart"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Soul Slash",
                type="Normal",
                category="Physical",
                db=14,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        ally_spec = _pokemon_spec("Ralts")
        ally_spec.abilities = [{"name": "Soul Heart"}]
        defender_spec = _pokemon_spec("Machop")
        defender_spec.defense = 1

        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        ally = PokemonState(spec=ally_spec, controller_id=trainer.identifier, position=(1, 0))
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        defender.hp = 1

        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "ash-2": ally, "gary-1": defender},
            active_slots=2,
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Soul Slash", target_id="gary-1"))
        battle.resolve_next_action()

        self.assertTrue(defender.fainted)
        self.assertEqual(attacker.combat_stages["spatk"], 2)
        self.assertEqual(ally.combat_stages["spatk"], 2)

        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Soul Heart"
        ]
        triggered_actors = {evt.get("actor") for evt in ability_events}
        self.assertSetEqual(triggered_actors, {"ash-1", "ash-2"})

    def test_pressure_adds_extra_frequency_usage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Quick Jab",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="Scene",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_spec = _pokemon_spec("Duskull")
        defender_spec.abilities = [{"name": "Pressure"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Quick Jab", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(battle.frequency_usage["ash-1"]["Quick Jab"], 2)
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Pressure"
        ]
        self.assertTrue(ability_events)

    def test_abominable_ignores_recoil(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        class MidRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Tauros")
        attacker_spec.abilities = [{"name": "Abominable"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Double-Edge",
                type="Normal",
                category="Physical",
                db=12,
                ac=None,
                range_kind="Melee",
                range_value=1,
                effects_text="Recoil 1/3",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=MaxRNG(),
        )
        before_hp = attacker_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Double-Edge", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.hp, before_hp)
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Abominable"
        ]
        self.assertTrue(ability_events)

    def test_rock_head_ignores_recoil(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Tauros")
        attacker_spec.abilities = [{"name": "Rock Head"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Double-Edge",
                type="Normal",
                category="Physical",
                db=12,
                ac=None,
                range_kind="Melee",
                range_value=1,
                effects_text="Recoil 1/3",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=MaxRNG(),
        )
        before_hp = attacker_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Double-Edge", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.hp, before_hp)
        ability_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Rock Head"
        ]
        self.assertTrue(ability_events)

    def test_abominable_blocks_massive_damage_injury(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machamp")
        attacker_spec.atk = 25
        attacker_spec.moves = [
            MoveSpec(
                name="Power Strike",
                type="Normal",
                category="Physical",
                db=10,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Snorlax")
        defender_spec.hp_stat = 20
        defender_spec.defense = 10
        defender_spec.abilities = [{"name": "Abominable"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Power Strike", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.injuries, 1)

        defender_spec_no_ability = _pokemon_spec("Snorlax")
        defender_spec_no_ability.hp_stat = 20
        defender_spec_no_ability.defense = 10
        defender_state_no_ability = PokemonState(
            spec=defender_spec_no_ability, controller_id=foe.identifier, position=(0, 1)
        )
        battle_no_ability = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state_no_ability,
            },
            rng=MaxRNG(),
        )
        battle_no_ability.queue_action(
            UseMoveAction(actor_id="ash-1", move_name="Power Strike", target_id="gary-1")
        )
        battle_no_ability.resolve_next_action()
        self.assertEqual(defender_state_no_ability.injuries, 2)

    def test_absorb_force_reduces_effectiveness(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b - 1

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.moves = [
            MoveSpec(
                name="Fire Fang",
                type="Fire",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Bulbasaur")
        defender_spec.types = ["Grass"]
        defender_spec.abilities = [{"name": "Absorb Force"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Fire Fang", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Fire Fang")
        base_mult = ptu_engine.type_multiplier("Fire", defender_spec.types)
        base_stage = battle._type_stage_from_multiplier(base_mult)
        expected_mult = battle._multiplier_from_stage(base_stage - 1)
        self.assertEqual(move_event.get("type_multiplier"), expected_mult)

    def test_adaptability_adds_db_to_stab(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b - 2

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Spark",
                type="Electric",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_with = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_with.spec.abilities = [{"name": "Adaptability"}]
        defender_state = PokemonState(
            spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)
        )
        battle_with = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_with, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle_with.queue_action(UseMoveAction(actor_id="ash-1", move_name="Spark", target_id="gary-1"))
        battle_with.resolve_next_action()
        move_with = next(evt for evt in battle_with.log if evt.get("type") == "move" and evt.get("move") == "Spark")

        attacker_without = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        battle_without = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_without,
                "gary-1": PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle_without.queue_action(UseMoveAction(actor_id="ash-1", move_name="Spark", target_id="gary-1"))
        battle_without.resolve_next_action()
        move_without = next(evt for evt in battle_without.log if evt.get("type") == "move" and evt.get("move") == "Spark")
        self.assertGreater(move_with.get("damage", 0), move_without.get("damage", 0))

    def test_aerilate_changes_normal_moves(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Swellow")
        attacker_spec.abilities = [{"name": "Aerilate"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Machop")
        defender_spec.types = ["Fighting"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle")
        expected = ptu_engine.type_multiplier("Flying", defender_spec.types)
        self.assertEqual(move_event.get("type_multiplier"), expected)

    def test_galvanize_changes_normal_moves(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Manectric")
        attacker_spec.abilities = [{"name": "Galvanize"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Quick Attack",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Squirtle")
        defender_spec.types = ["Water"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Quick Attack", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "move"
            and evt.get("move") == "Quick Attack"
            and "type_multiplier" in evt
        )
        expected = ptu_engine.type_multiplier("Electric", defender_spec.types)
        self.assertEqual(move_event.get("type_multiplier"), expected)

    def test_liquid_voice_converts_sonic_to_water(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Primarina")
        attacker_spec.abilities = [{"name": "Liquid Voice"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Hyper Voice",
                type="Normal",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                keywords=["Sonic"],
            )
        ]
        defender_spec = _pokemon_spec("Vulpix")
        defender_spec.types = ["Fire"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Hyper Voice", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Hyper Voice"
        )
        expected = ptu_engine.type_multiplier("Water", defender_spec.types)
        self.assertEqual(move_event.get("type_multiplier"), expected)

    def test_long_reach_allows_melee_at_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Noivern")
        attacker_spec.atk = 20
        attacker_spec.abilities = [{"name": "Long Reach"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Scratch",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.defense = 5
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 6))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            grid=GridState(width=10, height=10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Scratch", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Scratch"
        )
        self.assertIsNotNone(move_event)
        self.assertLess(defender_state.hp, defender_state.max_hp())

    def test_strength_stays_adjacent_even_with_long_reach(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Noivern")
        attacker_spec.abilities = [{"name": "Long Reach"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Strength",
                type="Normal",
                category="Physical",
                db=8,
                ac=2,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="EOT",
                range_text="Melee, 1 Target, Push",
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 6)),
            },
            grid=GridState(width=10, height=10),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        with self.assertRaisesRegex(ValueError, "adjacent|range"):
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Strength", target_id="gary-1"))

    def test_glisten_blocks_fairy_and_boosts_def(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Clefairy")
        attacker_spec.moves = [
            MoveSpec(
                name="Dazzling Gleam",
                type="Fairy",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Goomy")
        defender_spec.abilities = [{"name": "Glisten"}]
        defender_spec.defense = 12
        defender_spec.spdef = 8
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Dazzling Gleam", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, before_hp)
        self.assertEqual(defender_state.combat_stages.get("spdef"), 1)

    def test_merciless_crits_poisoned_targets(self) -> None:
        attacker_spec = _pokemon_spec("Toxapex")
        attacker_spec.abilities = [{"name": "Merciless"}]
        attacker = PokemonState(spec=attacker_spec, controller_id="ash")
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        defender.statuses.append({"name": "Poisoned"})
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        rng = SequenceRNG([10] + [1] * 10)
        result = resolve_move_action(rng, attacker, defender, move)
        self.assertTrue(result.get("crit"))

    def test_fluffy_adjusts_melee_and_fire(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        melee_attacker_spec = _pokemon_spec("Machop")
        melee_attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        fluffy_defender_spec = _pokemon_spec("Squirtle")
        fluffy_defender_spec.abilities = [{"name": "Fluffy"}]
        fluffy_defender_spec.types = ["Water"]
        melee_battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=melee_attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=fluffy_defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        melee_battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        melee_battle.resolve_next_action()
        melee_event = next(
            evt for evt in melee_battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle"
        )
        self.assertEqual(melee_event.get("type_multiplier"), 0.5)

        fire_attacker_spec = _pokemon_spec("Charmander")
        fire_attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        fluffy_fire_spec = _pokemon_spec("Squirtle")
        fluffy_fire_spec.abilities = [{"name": "Fluffy"}]
        fluffy_fire_spec.types = ["Water"]
        fire_battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=fire_attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=fluffy_fire_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        fire_battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        fire_battle.resolve_next_action()
        fire_event = next(
            evt for evt in fire_battle.log if evt.get("type") == "move" and evt.get("move") == "Ember"
        )
        self.assertEqual(fire_event.get("type_multiplier"), 1.0)

    def test_mold_breaker_ignores_levitate(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Earthquake",
            type="Ground",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_spec = _pokemon_spec("Excadrill")
        attacker_spec.abilities = [{"name": "Mold Breaker"}]
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Rotom")
        defender_spec.abilities = [{"name": "Levitate"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Earthquake", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertLess(defender_state.hp, defender_state.max_hp())

        attacker_spec_no = _pokemon_spec("Excadrill")
        attacker_spec_no.moves = [move]
        defender_spec_no = _pokemon_spec("Rotom")
        defender_spec_no.abilities = [{"name": "Levitate"}]
        defender_no = PokemonState(spec=defender_spec_no, controller_id=foe.identifier, position=(0, 1))
        battle_no = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec_no, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_no,
            },
            rng=SequenceRNG([20] * 10),
        )
        battle_no.queue_action(UseMoveAction(actor_id="ash-1", move_name="Earthquake", target_id="gary-1"))
        battle_no.resolve_next_action()
        self.assertEqual(defender_no.hp, defender_no.max_hp())

    def test_moody_changes_stats_on_end(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Smeargle")
        spec.abilities = [{"name": "Moody"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            rng=SequenceRNG([1, 3]),
        )
        state.handle_phase_effects(battle, TurnPhase.END, "ash-1")
        self.assertEqual(state.combat_stages.get("atk"), 2)
        self.assertEqual(state.combat_stages.get("def"), -2)
        moody_state = next(iter(state.get_temporary_effects("moody_state")), None)
        self.assertIsNotNone(moody_state)
        self.assertEqual(moody_state.get("up_stat"), "atk")
        self.assertEqual(moody_state.get("down_stat"), "def")

    def test_truant_tracks_roll_and_skip_state(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Slakoth")
        spec.abilities = [{"name": "Truant"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            rng=SequenceRNG([1]),
        )
        state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        truant_state = next(iter(state.get_temporary_effects("truant_state")), None)
        self.assertIsNotNone(truant_state)
        self.assertEqual(truant_state.get("roll"), 1)
        self.assertTrue(truant_state.get("skipped"))

    def test_mountain_peak_bonus_at_low_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Onix")
        attacker_spec.abilities = [{"name": "Mountain Peak"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Rock Throw",
                type="Rock",
                category="Physical",
                db=6,
                ac=2,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.hp = max(1, attacker_state.max_hp() // 3)
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Rock Throw", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Mountain Peak" for evt in battle.log))

    def test_overcharge_bonus_at_low_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Luxray")
        attacker_spec.abilities = [{"name": "Overcharge"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Thunder Fang",
                type="Electric",
                category="Physical",
                db=6,
                ac=2,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.hp = max(1, attacker_state.max_hp() // 3)
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Thunder Fang", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Overcharge" for evt in battle.log))

    def test_mud_dweller_resists_ground_and_water(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Marowak")
        attacker_spec.atk = 20
        attacker_spec.moves = [
            MoveSpec(
                name="High Horsepower",
                type="Ground",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.hp_stat = 200
        defender_spec.abilities = [{"name": "Mud Dweller"}]
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender,
            },
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(
            UseMoveAction(actor_id="ash-1", move_name="High Horsepower", target_id="gary-1")
        )
        battle.resolve_next_action()
        resisted_damage = next(
            evt.get("damage", 0)
            for evt in battle.log
            if evt.get("type") == "move" and evt.get("move") == "High Horsepower"
        )

        defender_base_spec = _pokemon_spec("Eevee")
        defender_base_spec.hp_stat = 200
        defender_base = PokemonState(
            spec=defender_base_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle_base = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_base,
            },
            rng=SequenceRNG([20] * 10),
        )
        battle_base.queue_action(
            UseMoveAction(actor_id="ash-1", move_name="High Horsepower", target_id="gary-1")
        )
        battle_base.resolve_next_action()
        base_damage = next(
            evt.get("damage", 0)
            for evt in battle_base.log
            if evt.get("type") == "move" and evt.get("move") == "High Horsepower"
        )
        self.assertLess(resisted_damage, base_damage)

    def test_multiscale_halves_damage_at_full_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Garchomp")
        attacker_spec.atk = 20
        attacker_spec.moves = [
            MoveSpec(
                name="Dragon Claw",
                type="Dragon",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Dragonite")
        defender_spec.abilities = [{"name": "Multiscale"}]
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender,
            },
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Dragon Claw", target_id="gary-1"))
        battle.resolve_next_action()
        multiscale_damage = next(
            evt.get("damage", 0)
            for evt in battle.log
            if evt.get("type") == "move" and evt.get("move") == "Dragon Claw"
        )

        defender_base = PokemonState(spec=_pokemon_spec("Dragonite"), controller_id=foe.identifier, position=(0, 1))
        battle_base = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_base,
            },
            rng=SequenceRNG([20] * 10),
        )
        battle_base.queue_action(UseMoveAction(actor_id="ash-1", move_name="Dragon Claw", target_id="gary-1"))
        battle_base.resolve_next_action()
        base_damage = next(
            evt.get("damage", 0)
            for evt in battle_base.log
            if evt.get("type") == "move" and evt.get("move") == "Dragon Claw"
        )
        self.assertLess(multiscale_damage, base_damage)

    def test_multitype_changes_type_from_item(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Arceus")
        spec.abilities = [{"name": "Multitype"}]
        spec.items = [{"name": "Fire Memory"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.spec.types, ["Fire"])

    def test_mummy_replaces_attacker_ability_on_contact(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Cofagrigus")
        defender_spec.abilities = [{"name": "Mummy"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        attacker_state = battle.pokemon["ash-1"]
        effects = attacker_state.get_temporary_effects("entrained_ability")
        self.assertTrue(any(entry.get("ability") == "Mummy" for entry in effects))

    def test_natural_cure_cleanses_on_switch(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        active_spec = _pokemon_spec("Starmie")
        active_spec.abilities = [{"name": "Natural Cure"}]
        bench_spec = _pokemon_spec("Pidgey")
        active_state = PokemonState(spec=active_spec, controller_id=trainer.identifier, position=(0, 0), active=True)
        active_state.statuses.append({"name": "Burned"})
        bench_state = PokemonState(spec=bench_spec, controller_id=trainer.identifier, position=None, active=False)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": active_state, "ash-2": bench_state},
        )
        battle.queue_action(SwitchAction(actor_id="ash-1", replacement_id="ash-2"))
        battle.resolve_next_action()
        self.assertFalse(active_state.has_status("Burned"))

    def test_no_guard_forces_hit(self) -> None:
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.abilities = [{"name": "No Guard"}]
        attacker = PokemonState(spec=attacker_spec, controller_id="ash")
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Stone Edge",
            type="Rock",
            category="Physical",
            db=8,
            ac=8,
            range_kind="Melee",
            range_value=1,
        )
        rng = SequenceRNG([20] * 10)
        result = resolve_move_action(rng, attacker, defender, move)
        self.assertTrue(result.get("hit"))

    def test_normalize_changes_move_type(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Delcatty")
        attacker_spec.abilities = [{"name": "Normalize"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Oddish")
        defender_spec.types = ["Grass"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Ember")
        expected = ptu_engine.type_multiplier("Normal", defender_spec.types)
        self.assertEqual(move_event.get("type_multiplier"), expected)

    def test_oblivious_blocks_infatuation(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Lopunny")
        attacker_spec.gender = "female"
        attacker_spec.moves = [
            MoveSpec(
                name="Attract",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Slowpoke")
        defender_spec.gender = "male"
        defender_spec.abilities = [{"name": "Oblivious"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Attract", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["gary-1"].has_status("Infatuated"))

    def test_odious_spray_flinches_on_poison_gas(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Skuntank")
        attacker_spec.abilities = [{"name": "Odious Spray"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Poison Gas",
                type="Poison",
                category="Status",
                db=0,
                ac=2,
                range_kind="Ranged",
                range_value=4,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Poison Gas", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Flinch"))

    def test_omen_lowers_accuracy(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Misdreavus")
        attacker_spec.abilities = [{"name": "Omen"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Omen",
                type="Ghost",
                category="Status",
                ac=None,
                range_kind="Ranged",
                range_value=5,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Omen", target_id="gary-1"))
        battle.resolve_next_action()
        effects = battle.pokemon["gary-1"].get_temporary_effects("accuracy_penalty")
        self.assertTrue(effects)
        self.assertEqual(effects[-1].get("amount"), 2)

    def test_overcoat_blocks_powder_and_weather(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Vileplume")
        attacker_spec.moves = [
            MoveSpec(
                name="Sleep Powder",
                type="Grass",
                category="Status",
                ac=2,
                range_kind="Ranged",
                range_value=4,
                keywords=["Powder"],
            )
        ]
        defender_spec = _pokemon_spec("Beldum")
        defender_spec.abilities = [{"name": "Overcoat"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            weather="Hail",
            rng=SequenceRNG([20] * 10),
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Sleep Powder", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(defender_state.has_status("Sleep"))
        defender_state.handle_phase_effects(battle, TurnPhase.START, "gary-1")
        self.assertEqual(defender_state.hp, before_hp)

    def test_effect_spore_rolls_status(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Paras")
        defender_spec.abilities = [{"name": "Effect Spore"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([5] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].has_status("Sleep"))

    def test_flame_tongue_lick_burns_and_injures(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Lickitung")
        attacker_spec.abilities = [{"name": "Flame Tongue"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Lick",
                type="Ghost",
                category="Physical",
                db=4,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Lick", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Burned"))
        self.assertEqual(defender_state.injuries, 1)

    def test_iron_barbs_deals_tick(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_spec = _pokemon_spec("Ferrothorn")
        defender_spec.abilities = [{"name": "Iron Barbs"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        before_hp = attacker_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(before_hp - attacker_state.hp, attacker_state.tick_value())

    def test_pack_hunt_ability_move_deals_tick(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Mightyena")
        attacker_spec.abilities = [{"name": "Pack Hunt"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Pack Hunt",
                type="Normal",
                category="Status",
                db=0,
                ac=5,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([20] * 5),
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Pack Hunt", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(before_hp - defender_state.hp, defender_state.tick_value())

    def test_parry_blocks_melee_attack_when_ready(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Farfetch'd")
        defender_spec.abilities = [{"name": "Parry"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1))
        defender_state.add_temporary_effect("parry_ready", expires_round=1)
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": defender_state, "gary-1": attacker_state},
            rng=SequenceRNG([20] * 5),
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, before_hp)

    def test_perception_shifts_out_of_area(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Pidgey")
        defender_spec.abilities = [{"name": "Perception"}]
        defender_spec.movement = {"overland": 6}
        defender_state = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(1, 1))
        defender_state.add_temporary_effect("perception_ready", expires_round=1)
        attacker_spec = _pokemon_spec("Geodude")
        attacker_spec.moves = [
            MoveSpec(
                name="Rock Slide",
                type="Rock",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                area_kind="Burst",
                area_value=1,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": defender_state,
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Rock Slide", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertNotEqual(defender_state.position, (1, 1))

    def test_pickup_roll_logged(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Meowth")
        spec.abilities = [{"name": "Pickup"}]
        spec.moves = [
            MoveSpec(
                name="Pickup",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            )
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            rng=SequenceRNG([12, 7]),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Pickup", target_id="ash-1"))
        battle.resolve_next_action()
        pickup_events = [evt for evt in battle.log if evt.get("ability") == "Pickup"]
        self.assertTrue(pickup_events)
        self.assertEqual(pickup_events[-1].get("roll"), 12)

    def test_pixilate_ready_converts_normal_to_fairy(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Sylveon")
        attacker_spec.abilities = [{"name": "Pixilate"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Machop")
        defender_spec.types = ["Fighting"]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.add_temporary_effect("pixilate_ready", expires_round=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_state,
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle")
        expected = ptu_engine.type_multiplier("Fairy", defender_spec.types)
        self.assertEqual(move_event.get("type_multiplier"), expected)

    def test_refridgerate_ready_converts_normal_to_ice(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Glaceon")
        attacker_spec.abilities = [{"name": "Refridgerate"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Bulbasaur")
        defender_spec.types = ["Grass"]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.add_temporary_effect("refridgerate_ready", expires_round=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_state,
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle")
        expected = ptu_engine.type_multiplier("Ice", defender_spec.types)
        self.assertEqual(move_event.get("type_multiplier"), expected)

    def test_prime_fury_enrages_and_raises_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Primeape")
        spec.abilities = [{"name": "Prime Fury"}]
        spec.moves = [
            MoveSpec(
                name="Prime Fury",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            )
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Prime Fury", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(state.has_status("Enraged"))
        self.assertEqual(state.combat_stages.get("atk"), 1)

    def test_root_down_grants_temp_hp_with_ingrain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Cherrim")
        spec.abilities = [{"name": "Root Down"}]
        spec.moves = [MoveSpec(name="Root Down", type="Grass", category="Status", ac=None, range_kind="Self")]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.statuses.append({"name": "Ingrain"})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        before_temp = state.temp_hp
        expected = max(1, state.max_hp() // 16)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Root Down", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(state.temp_hp, before_temp + expected)

    def test_shackle_halves_movement(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Chandelure")
        attacker_spec.abilities = [{"name": "Shackle"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Shackle",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Burst",
                range_value=3,
                area_kind="Burst",
                area_value=3,
                target_kind="Self",
                range_text="Burst 3, Enemies",
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.movement = {"overland": 6}
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(2, 2)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(2, 4)),
            },
            grid=GridState(width=6, height=6),
        )
        defender_state = battle.pokemon["gary-1"]
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shackle", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.movement_speed("overland"), 3)

    def test_shadow_tag_applies_anchor_and_statuses(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Gengar")
        attacker_spec.abilities = [{"name": "Shadow Tag"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Shadow Tag",
                type="Ghost",
                category="Status",
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shadow Tag", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Slowed"))
        self.assertTrue(defender_state.has_status("Trapped"))
        self.assertTrue(defender_state.get_temporary_effects("shadow_tag_anchor"))

    def test_shell_cannon_ready_boosts_damage(self) -> None:
        attacker_with = PokemonState(spec=_pokemon_spec("Blastoise"), controller_id="ash")
        attacker_with.spec.abilities = [{"name": "Shell Cannon"}]
        attacker_with.add_temporary_effect("shell_cannon_ready", expires_round=1)
        attacker_without = PokemonState(spec=_pokemon_spec("Blastoise"), controller_id="ash")
        attacker_without.spec.abilities = [{"name": "Shell Cannon"}]
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=4,
            range_kind="Ranged",
            range_value=6,
        )
        result_with = resolve_move_action(SequenceRNG([20] * 10), attacker_with, defender, move)
        result_without = resolve_move_action(SequenceRNG([20] * 10), attacker_without, defender, move)
        self.assertGreater(result_with.get("damage", 0), result_without.get("damage", 0))

    def test_shell_shield_interrupt_applies_withdraw(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Blastoise")
        defender_spec.abilities = [{"name": "Shell Shield"}]
        defender_spec.moves = [MoveSpec(name="Shell Shield", type="Water", category="Status", ac=None, range_kind="Self")]
        defender_state = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1))
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": defender_state, "gary-1": attacker_state},
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shell Shield", target_id="ash-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Withdrawn"))
        self.assertEqual(defender_state.combat_stages.get("def"), 1)

    def test_sonic_courtship_ignores_gender(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Meloetta")
        attacker_spec.abilities = [{"name": "Sonic Courtship"}]
        attacker_spec.gender = "male"
        attacker_spec.moves = [
            MoveSpec(name="Sonic Courtship", type="Normal", category="Status", ac=None, range_kind="Self"),
            MoveSpec(name="Attract", type="Normal", category="Status", ac=None, range_kind="Ranged", range_value=6),
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.gender = "male"
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Sonic Courtship", target_id="ash-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Attract", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Infatuated"))

    def test_soulstealer_heals_on_ko(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Marowak")
        attacker_spec.abilities = [{"name": "Soulstealer"}]
        attacker_spec.atk = 20
        attacker_spec.moves = [
            MoveSpec(
                name="Bonemerang",
                type="Ground",
                category="Physical",
                db=10,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.injuries = 2
        attacker_state.hp = 5
        defender_spec = _pokemon_spec("Eevee")
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([20] * 10),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bonemerang", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.injuries, 0)
        self.assertEqual(attacker_state.hp, attacker_state.max_hp_with_injuries())

    def test_sound_lance_deals_damage_when_ready(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Noivern")
        attacker_spec.abilities = [{"name": "Sound Lance"}]
        attacker_spec.spatk = 15
        attacker_spec.moves = [
            MoveSpec(name="Sound Lance", type="Normal", category="Status", ac=None, range_kind="Self"),
            MoveSpec(name="Supersonic", type="Normal", category="Status", ac=2, range_kind="Ranged", range_value=6),
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.hp_stat = 50
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([1] * 5),
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Sound Lance", target_id="ash-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Supersonic", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(before_hp - defender_state.hp, attacker_spec.spatk)

    def test_spinning_dance_triggers_on_miss(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Ludicolo")
        defender_spec.abilities = [{"name": "Spinning Dance"}]
        defender_spec.movement = {"overland": 6}
        defender_state = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(1, 1))
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=4,
                range_kind="Melee",
                range_value=1,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": defender_state, "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(1, 2))},
            grid=GridState(width=4, height=4),
            rng=SequenceRNG([1] * 5),
        )
        before_pos = defender_state.position
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.combat_stages.get("evasion"), 1)
        self.assertNotEqual(defender_state.position, before_pos)

    def test_spray_down_knocks_airborne_targets(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgeot")
        attacker_spec.abilities = [{"name": "Spray Down"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Gust",
                type="Flying",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Charizard")
        defender_spec.movement = {"sky": 6}
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Gust", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.get_temporary_effects("spray_down"))
        self.assertEqual(defender_state.movement_speed("sky"), 0)

    def test_steadfast_raises_speed_on_flinch(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Machamp")
        spec.abilities = [{"name": "Steadfast"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.statuses.append({"name": "Flinch"})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.combat_stages.get("spd"), 1)

    def test_sticky_smoke_lowers_accuracy_on_start(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Koffing")
        attacker_spec.abilities = [{"name": "Sticky Smoke"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Smokescreen",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Smokescreen", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state.handle_phase_effects(battle, TurnPhase.START, "gary-1")
        self.assertEqual(defender_state.combat_stages.get("accuracy"), -1)

    def test_storm_drain_absorbs_water_and_boosts_spatk(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Squirtle")
        attacker_spec.moves = [
            MoveSpec(
                name="Water Gun",
                type="Water",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Gastrodon")
        defender_spec.abilities = [{"name": "Storm Drain"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=SequenceRNG([20] * 5),
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Water Gun", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, before_hp)
        self.assertEqual(defender_state.combat_stages.get("spatk"), 1)

    def test_strange_tempo_cures_confusion_and_raises_stat(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Linoone")
        spec.abilities = [{"name": "Strange Tempo"}]
        spec.atk = 12
        spec.moves = [MoveSpec(name="Strange Tempo", type="Normal", category="Status", ac=None, range_kind="Self")]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.statuses.append({"name": "Confused"})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Strange Tempo", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(state.has_status("Confused"))
        self.assertEqual(state.combat_stages.get("atk"), 2)

    def test_probability_control_reroll(self) -> None:
        attacker = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id="ash")
        attacker.add_temporary_effect("probability_control", expires_round=1)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        move = MoveSpec(
            name="Psychic",
            type="Psychic",
            category="Special",
            db=8,
            ac=8,
            range_kind="Ranged",
            range_value=6,
        )
        rng = SequenceRNG([1, 20])
        result = resolve_move_action(rng, attacker, defender, move)
        self.assertTrue(result.get("hit"))

    def test_protean_ready_changes_type(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Greninja")
        attacker_spec.abilities = [{"name": "Protean"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Flamethrower",
                type="Fire",
                category="Special",
                db=8,
                ac=2,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.add_temporary_effect("protean_ready", expires_round=1)
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=SequenceRNG([20] * 5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Flamethrower", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.spec.types, ["Fire"])

    def test_quick_cloak_builds_burmy_cloak(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Burmy")
        spec.abilities = [{"name": "Quick Cloak"}]
        spec.types = ["Bug"]
        spec.moves = [
            MoveSpec(
                name="Quick Cloak",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            )
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state}, weather="Hail")
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Quick Cloak", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertIn("Steel", state.spec.types)

    def test_quick_curl_marks_defense_curl_swift(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Sentret")
        spec.abilities = [{"name": "Quick Curl"}]
        spec.moves = [
            MoveSpec(
                name="Quick Curl",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            ),
            MoveSpec(
                name="Defense Curl",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            ),
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Quick Curl", target_id="ash-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Defense Curl", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Quick Curl" for evt in battle.log))

    def test_rattled_ability_move_raises_speed(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Whismur")
        spec.abilities = [{"name": "Rattled"}]
        spec.moves = [
            MoveSpec(
                name="Rattled",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            )
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Rattled", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(state.combat_stages.get("spd"), 1)

    def test_refreshing_veil_cures_on_aqua_ring(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Milotic")
        spec.abilities = [{"name": "Refreshing Veil"}]
        spec.moves = [
            MoveSpec(
                name="Aqua Ring",
                type="Water",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            )
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.statuses.append({"name": "Burned"})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Aqua Ring", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(state.has_status("Burned"))

    def test_empower_allows_self_status_free_action(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Eevee")
        spec.abilities = [{"name": "Empower"}]
        spec.moves = [
            MoveSpec(
                name="Empower",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            ),
            MoveSpec(
                name="Agility",
                type="Psychic",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            ),
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Empower", target_id="ash-1"))
        battle.resolve_next_action()
        agility_action = UseMoveAction(actor_id="ash-1", move_name="Agility", target_id="ash-1")
        battle.queue_action(agility_action)
        self.assertEqual(agility_action.action_type, ActionType.FREE)

    def test_sun_blanket_heals_on_low_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Vulpix")
        spec.abilities = [{"name": "Sun Blanket"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.hp = max(1, state.max_hp() // 2)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        before = state.hp
        battle.weather = "Sun"
        state._handle_ability_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertGreater(state.hp, before)

    def test_unnerve_blocks_positive_combat_stages(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Zoroark")
        attacker_spec.abilities = [{"name": "Unnerve"}]
        defender_spec = _pokemon_spec("Pikachu")
        defender_spec.moves = [
            MoveSpec(
                name="Agility",
                type="Psychic",
                category="Status",
                ac=None,
                range_kind="Self",
                target_kind="Self",
                range_text="Self",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        attacker_state._handle_ability_phase_effects(battle, TurnPhase.START, "ash-1")
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Agility", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.combat_stages.get("spd", 0), 0)

    def test_aftermath_burst_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Gengar")
        attacker_spec.spatk = 30
        attacker_spec.moves = [
            MoveSpec(
                name="Shadow Ball",
                type="Ghost",
                category="Special",
                db=12,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(2, 3)
        )
        defender_spec = _pokemon_spec("Drifloon")
        defender_spec.abilities = [{"name": "Aftermath"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(2, 2)
        )
        ally_state = PokemonState(
            spec=_pokemon_spec("Zubat"), controller_id=trainer.identifier, position=(1, 2)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "ash-2": ally_state, "gary-1": defender_state},
            grid=GridState(width=6, height=6),
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shadow Ball", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertLess(attacker_state.hp, attacker_state.max_hp())
        self.assertLess(ally_state.hp, ally_state.max_hp())
        aftermath_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Aftermath"
        ]
        self.assertTrue(aftermath_events)

    def test_air_lock_suppresses_weather_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        air_lock_spec = _pokemon_spec("Rayquaza")
        air_lock_spec.abilities = [{"name": "Air Lock"}]
        air_lock_state = PokemonState(
            spec=air_lock_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        target_spec = _pokemon_spec("Eevee")
        target_spec.types = ["Normal"]
        target_state = PokemonState(
            spec=target_spec, controller_id=foe.identifier, position=(1, 0)
        )
        target_state.spec.spd = 30
        air_lock_state.spec.spd = 5
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": air_lock_state, "gary-1": target_state},
            weather="Hail",
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        before_hp = target_state.hp
        battle.advance_phase()
        self.assertEqual(target_state.hp, before_hp)

    def test_ambush_flinches_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Zangoose")
        attacker_spec.abilities = [{"name": "Ambush"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Quick Slash",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Sandshrew"), controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Quick Slash", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Flinch"))

    def test_analytic_bonus_damage(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b - 3

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Porygon")
        attacker_spec.abilities = [{"name": "Analytic"}]
        attacker_spec.spd = 5
        attacker_spec.moves = [
            MoveSpec(
                name="Shock Pulse",
                type="Electric",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Abra")
        defender_spec.spd = 20
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.end_turn()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shock Pulse", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Shock Pulse")
        self.assertEqual(move_event.get("analytic_bonus"), 5)

    def test_anger_point_triggers_on_crit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pinsir")
        attacker_spec.moves = [
            MoveSpec(
                name="Slash",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Tauros")
        defender_spec.abilities = [{"name": "Anger Point"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20, 10, 10, 10, 10]),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Slash", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state = battle.pokemon["gary-1"]
        self.assertTrue(defender_state.has_status("Enraged"))
        self.assertEqual(defender_state.combat_stages["atk"], 6)

    def test_anticipation_reveals_super_effective_once(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.types = ["Fire"]
        attacker_spec.abilities = [{"name": "Anticipation"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Scratch",
                type="Normal",
                category="Physical",
                db=4,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Squirtle")
        defender_spec.moves = [
            MoveSpec(
                name="Water Gun",
                type="Water",
                category="Special",
                db=4,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Scratch", target_id="gary-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Scratch", target_id="gary-1"))
        battle.resolve_next_action()
        anticipation_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Anticipation"
        ]
        self.assertEqual(len(anticipation_events), 1)
        self.assertEqual(anticipation_events[0].get("result"), "super_effective")

    def test_aqua_boost_adds_damage(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b - 3

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Squirtle")
        attacker_spec.moves = [
            MoveSpec(
                name="Water Gun",
                type="Water",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        ally_spec = _pokemon_spec("Vaporeon")
        ally_spec.abilities = [{"name": "Aqua Boost"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=ally_spec, controller_id=trainer.identifier, position=(0, 1)),
                "gary-1": PokemonState(spec=_pokemon_spec("Growlithe"), controller_id=foe.identifier, position=(0, 2)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Water Gun", target_id="gary-1"))
        battle.resolve_next_action()
        boosted_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Water Gun")
        self.assertEqual(boosted_event.get("aqua_boost_bonus"), 5)

    def test_arena_trap_slows_nearby_foes(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        trap_spec = _pokemon_spec("Diglett")
        trap_spec.abilities = [{"name": "Arena Trap"}]
        trapper = PokemonState(spec=trap_spec, controller_id=trainer.identifier, position=(0, 0))
        slowed = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(3, 0))
        immune_spec = _pokemon_spec("Pidgey")
        immune_spec.types = ["Flying"]
        immune = PokemonState(spec=immune_spec, controller_id=foe.identifier, position=(2, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": trapper, "gary-1": slowed, "gary-2": immune},
        )
        battle.start_round()
        self.assertTrue(slowed.has_status("Slowed"))
        self.assertFalse(immune.has_status("Slowed"))

    def test_aroma_veil_blocks_confusion(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        veil_spec = _pokemon_spec("Slurpuff")
        veil_spec.abilities = [{"name": "Aroma Veil"}]
        veil_state = PokemonState(spec=veil_spec, controller_id=trainer.identifier, position=(0, 0))
        target_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": veil_state, "gary-1": target_state},
        )
        move = MoveSpec(name="Confuse Ray", type="Ghost", category="Status")
        events: List[dict] = []
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=target_state,
            status="Confused",
            effect="confusion",
            description="Confuse Ray confuses the target.",
        )
        self.assertFalse(target_state.has_status("Confused"))
        self.assertTrue(any(evt.get("ability") == "Aroma Veil" for evt in events))

    def test_own_tempo_blocks_confusion(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier, position=(0, 0))
        target_spec = _pokemon_spec("Slowpoke")
        target_spec.abilities = [{"name": "Own Tempo"}]
        target_state = PokemonState(spec=target_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": target_state},
        )
        move = MoveSpec(name="Confuse Ray", type="Ghost", category="Status")
        events: List[dict] = []
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=target_state,
            status="Confused",
            effect="confusion",
            description="Confuse Ray confuses the target.",
        )
        self.assertFalse(target_state.has_status("Confused"))
        self.assertTrue(any(evt.get("ability") == "Own Tempo" for evt in events))

    def test_aura_break_suppresses_adaptability(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b - 2

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.abilities = [{"name": "Adaptability"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Thunder Shock",
                type="Electric",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        aura_break_spec = _pokemon_spec("Xerneas")
        aura_break_spec.abilities = [{"name": "Aura Break"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=aura_break_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Thunder Shock")
        self.assertIsNone(move_event.get("adaptability_bonus"))
        self.assertTrue(any(evt.get("ability") == "Aura Break" for evt in battle.log))

    def test_aura_storm_scales_with_injuries(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b - 2

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Lucario")
        attacker_spec.abilities = [{"name": "Aura Storm"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Aura Pulse",
                type="Fighting",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                keywords=["Aura"],
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.injuries = 2
        attacker_state.hp = attacker_state.max_hp() // 2
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_state,
                "gary-1": PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Aura Pulse", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Aura Pulse")
        self.assertEqual(move_event.get("aura_storm_bonus"), 9)

    def test_bad_dreams_hits_sleeping_targets(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        sleeper = PokemonState(
            spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)
        )
        sleeper.statuses.append({"name": "Sleep"})
        bad_dreams_spec = _pokemon_spec("Darkrai")
        bad_dreams_spec.abilities = [{"name": "Bad Dreams"}]
        dreamer = PokemonState(
            spec=bad_dreams_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": dreamer, "gary-1": sleeper},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        before_hp = sleeper.hp
        battle.advance_phase()
        self.assertLess(sleeper.hp, before_hp)

    def test_battle_armor_blocks_crit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Scyther")
        attacker_spec.moves = [
            MoveSpec(
                name="Slash",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Bastiodon")
        defender_spec.abilities = [{"name": "Battle Armor"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([20, 10, 10, 10]),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Slash", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Slash")
        self.assertFalse(move_event.get("crit"))
        self.assertTrue(any(evt.get("ability") == "Battle Armor" for evt in battle.log))

    def test_beam_cannon_extends_crit_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Xatu")
        attacker_spec.abilities = [{"name": "Beam Cannon"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Psybeam",
                type="Psychic",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_state = PokemonState(
            spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)
        )
        battle_with = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)), "gary-1": defender_state},
            rng=SequenceRNG([17, 10, 10, 10]),
        )
        battle_with.queue_action(UseMoveAction(actor_id="ash-1", move_name="Psybeam", target_id="gary-1"))
        battle_with.resolve_next_action()
        move_with = next(evt for evt in battle_with.log if evt.get("type") == "move" and evt.get("move") == "Psybeam")

        attacker_spec_no = _pokemon_spec("Xatu")
        attacker_spec_no.moves = attacker_spec.moves
        battle_without = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec_no, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=SequenceRNG([17, 10, 10, 10]),
        )
        battle_without.queue_action(UseMoveAction(actor_id="ash-1", move_name="Psybeam", target_id="gary-1"))
        battle_without.resolve_next_action()
        move_without = next(evt for evt in battle_without.log if evt.get("type") == "move" and evt.get("move") == "Psybeam")
        self.assertTrue(move_with.get("crit"))
        self.assertFalse(move_without.get("crit"))

    def test_beautiful_cures_enraged_once(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        beauty_spec = _pokemon_spec("Milotic")
        beauty_spec.abilities = [{"name": "Beautiful"}]
        beauty_state = PokemonState(
            spec=beauty_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        target_state = PokemonState(
            spec=_pokemon_spec("Ekans"), controller_id=foe.identifier, position=(0, 1)
        )
        target_state.statuses.append({"name": "Enraged"})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": beauty_state, "gary-1": target_state},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.advance_phase()
        self.assertFalse(target_state.has_status("Enraged"))
        beauty_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Beautiful"
        ]
        self.assertTrue(beauty_events)

    def test_berry_storage_triples_berry_buffs(self) -> None:
        spec = _pokemon_spec("Bidoof")
        spec.items = [{"name": "Oran Berry"}]
        state = PokemonState(spec=spec, controller_id="ash")
        self.assertEqual(len(state.food_buffs), 1)

        spec_storage = _pokemon_spec("Bidoof")
        spec_storage.items = [{"name": "Oran Berry"}]
        spec_storage.abilities = [{"name": "Berry Storage"}]
        storage_state = PokemonState(spec=spec_storage, controller_id="ash")    
        self.assertEqual(len(storage_state.food_buffs), 3)

    def test_big_pecks_blocks_defense_drops(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(
            spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier
        )
        defender_spec = _pokemon_spec("Pidgey")
        defender_spec.abilities = [{"name": "Big Pecks"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Tail Whip", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            stat="def",
            delta=-1,
            description="Tail Whip lowers Defense.",
        )
        self.assertEqual(defender_state.combat_stages["def"], 0)
        self.assertTrue(any(evt.get("ability") == "Big Pecks" for evt in events))

    def test_big_swallow_boosts_swallow_count(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Lickitung")
        attacker_spec.abilities = [{"name": "Big Swallow"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Swallow",
                type="Normal",
                category="Status",
                range_kind="Self",
                target_kind="Self",
                ac=None,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, (attacker_state.hp or 1) - 10)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle._set_stockpile_count(attacker_state, 1)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Swallow", target_id="ash-1"))
        battle.resolve_next_action()
        ability_events = [
            evt for evt in battle.log if evt.get("ability") == "Big Swallow"
        ]
        self.assertTrue(ability_events)
        self.assertEqual(ability_events[-1].get("count"), 2)

    def test_blaze_boosts_fire_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.abilities = [{"name": "Blaze"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Flame Burst",
                type="Fire",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Bulbasaur"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Flame Burst", target_id="gary-1"))
        battle.resolve_next_action()
        blaze_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Blaze"
        ]
        self.assertTrue(blaze_events)

    def test_overgrow_boosts_grass_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Bulbasaur")
        attacker_spec.abilities = [{"name": "Overgrow"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Razor Leaf",
                type="Grass",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Squirtle"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Razor Leaf", target_id="gary-1"))
        battle.resolve_next_action()
        overgrow_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Overgrow"
        ]
        self.assertTrue(overgrow_events)

    def test_torrent_boosts_water_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Squirtle")
        attacker_spec.abilities = [{"name": "Torrent"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Water Gun",
                type="Water",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Charmander"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Water Gun", target_id="gary-1"))
        battle.resolve_next_action()
        torrent_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Torrent"
        ]
        self.assertTrue(torrent_events)

    def test_swarm_boosts_bug_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Beedrill")
        attacker_spec.abilities = [{"name": "Swarm"}]
        attacker_spec.moves = [
            MoveSpec(
                name="U-Turn",
                type="Bug",
                category="Physical",
                db=7,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="U-Turn", target_id="gary-1"))
        battle.resolve_next_action()
        swarm_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Swarm"
        ]
        self.assertTrue(swarm_events)

    def test_iron_fist_boosts_punch_damage(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return (a + b) // 2

        attacker_spec = _pokemon_spec("Hitmonchan")
        attacker_spec.atk = 16
        attacker_spec.abilities = [{"name": "Iron Fist"}]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.defense = 6
        move = MoveSpec(
            name="Thunder Punch",
            type="Electric",
            category="Physical",
            db=8,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        with_ability = resolve_move_action(
            FixedRNG(),
            PokemonState(spec=attacker_spec, controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        baseline_spec = _pokemon_spec("Hitmonchan")
        baseline_spec.atk = 16
        without_ability = resolve_move_action(
            FixedRNG(),
            PokemonState(spec=baseline_spec, controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        self.assertGreater(with_ability["damage"], without_ability["damage"])

    def test_technician_boosts_low_power_damage(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return (a + b) // 2

        attacker_spec = _pokemon_spec("Scizor")
        attacker_spec.atk = 16
        attacker_spec.abilities = [{"name": "Technician"}]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.defense = 6
        move = MoveSpec(
            name="Quick Attack",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        with_ability = resolve_move_action(
            FixedRNG(),
            PokemonState(spec=attacker_spec, controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        baseline_spec = _pokemon_spec("Scizor")
        baseline_spec.atk = 16
        without_ability = resolve_move_action(
            FixedRNG(),
            PokemonState(spec=baseline_spec, controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        self.assertGreater(with_ability["damage"], without_ability["damage"])

    def test_reckless_boosts_recoil_damage(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return (a + b) // 2

        attacker_spec = _pokemon_spec("Staraptor")
        attacker_spec.atk = 18
        attacker_spec.abilities = [{"name": "Reckless"}]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.defense = 6
        move = MoveSpec(
            name="Double-Edge",
            type="Normal",
            category="Physical",
            db=9,
            ac=None,
            range_kind="Melee",
            range_value=1,
            effects_text="Recoil 1/3",
        )
        with_ability = resolve_move_action(
            FixedRNG(),
            PokemonState(spec=attacker_spec, controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        baseline_spec = _pokemon_spec("Staraptor")
        baseline_spec.atk = 18
        without_ability = resolve_move_action(
            FixedRNG(),
            PokemonState(spec=baseline_spec, controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        self.assertGreater(with_ability["damage"], without_ability["damage"])

    def test_justified_raises_attack_on_dark_hit(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Umbreon")
        attacker_spec.types = ["Dark"]
        attacker_spec.moves = [
            MoveSpec(
                name="Bite",
                type="Dark",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Lucario")
        defender_spec.abilities = [{"name": "Justified"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages["atk"], 1)
        self.assertTrue(any(evt.get("move") == "Justified" for evt in battle.log))

    def test_last_chance_boosts_normal_damage_under_low_hp(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.abilities = [{"name": "Last Chance"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 3)
        defender_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        last_chance_events = [
            evt for evt in battle.log if evt.get("type") == "ability" and evt.get("ability") == "Last Chance"
        ]
        self.assertTrue(last_chance_events)

    def test_leaf_guard_blocks_major_status_in_sun(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Charmander"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Chikorita")
        defender_spec.abilities = [{"name": "Leaf Guard"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.weather = "Sunny"
        events: List[dict] = []
        move = MoveSpec(name="Will-O-Wisp", type="Fire", category="Status")
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            status="Burned",
            effect="status",
            description="Will-O-Wisp burns the target.",
        )
        self.assertFalse(defender_state.has_status("Burned"))
        self.assertTrue(any(evt.get("ability") == "Leaf Guard" for evt in events))

    def test_limber_blocks_paralysis(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.abilities = [{"name": "Limber"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Thunder Wave", type="Electric", category="Status")
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            status="Paralyzed",
            effect="status",
            description="Thunder Wave paralyzes the target.",
        )
        self.assertFalse(defender_state.has_status("Paralyzed"))
        self.assertTrue(any(evt.get("ability") == "Limber" for evt in events))

    def test_liquid_ooze_reverses_drain_healing(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Oddish")
        attacker_spec.moves = [
            MoveSpec(
                name="Absorb",
                type="Grass",
                category="Special",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 2)
        defender_spec = _pokemon_spec("Grimer")
        defender_spec.abilities = [{"name": "Liquid Ooze"}]
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        starting_hp = attacker_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Absorb", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertLess(attacker_state.hp, starting_hp)
        self.assertTrue(any(evt.get("ability") == "Liquid Ooze" for evt in battle.log))

    def test_kampfgeist_grants_fighting_stab(self) -> None:
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.types = ["Normal"]
        attacker_spec.abilities = [{"name": "Kampfgeist"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        move = MoveSpec(name="Low Kick", type="Fighting", category="Physical", db=6)
        self.assertEqual(stab_db(move, attacker_state), 8)

    def test_keen_eye_adds_accuracy_and_blocks_accuracy_drop(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        move = MoveSpec(name="Swift", type="Normal", category="Special", db=6, ac=10)
        attacker_spec = _pokemon_spec("Pidgey")
        attacker_spec.abilities = [{"name": "Keen Eye"}]
        defender_spec = _pokemon_spec("Rattata")
        result = attack_hits(
            FixedRNG(),
            PokemonState(spec=attacker_spec, controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        baseline = attack_hits(
            FixedRNG(),
            PokemonState(spec=_pokemon_spec("Pidgey"), controller_id="ash"),
            PokemonState(spec=defender_spec, controller_id="gary"),
            move,
        )
        self.assertEqual(result.get("needed"), baseline.get("needed") - 1)
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        target_spec = _pokemon_spec("Hoothoot")
        target_spec.abilities = [{"name": "Keen Eye"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=target_spec, controller_id=foe.identifier),
            },
        )
        events: List[dict] = []
        move = MoveSpec(name="Sand Attack", type="Ground", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=battle.pokemon["gary-1"],
            stat="accuracy",
            delta=-1,
            description="Sand Attack lowers Accuracy.",
        )
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("accuracy", 0), 0)
        self.assertTrue(any(evt.get("ability") == "Keen Eye" for evt in events))

    def test_keen_eye_extends_accuracy_drop_duration(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        target_spec = _pokemon_spec("Noctowl")
        target_spec.abilities = [{"name": "Keen Eye"}]
        target_state = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": target_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Glare", type="Normal", category="Status")
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=target_state,
            status="Accuracy Drop",
            effect="acc_drop",
            description="Glare lowers Accuracy.",
            remaining=3,
        )
        status_entries = [
            status
            for status in target_state.statuses
            if isinstance(status, dict) and status.get("name") == "Accuracy Drop"
        ]
        self.assertTrue(status_entries)
        self.assertEqual(status_entries[0].get("remaining"), 5)

    def test_klutz_ignores_air_balloon(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        klutz_spec = _pokemon_spec("Pikachu")
        klutz_spec.items = [{"name": "Air Balloon"}]
        klutz_spec.abilities = [{"name": "Klutz"}]
        klutz_state = PokemonState(spec=klutz_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": klutz_state})
        self.assertTrue(battle._is_actor_grounded(klutz_state))
        balloon_spec = _pokemon_spec("Pikachu")
        balloon_spec.items = [{"name": "Air Balloon"}]
        balloon_state = PokemonState(spec=balloon_spec, controller_id=trainer.identifier)
        balloon_battle = BattleState(
            trainers={trainer.identifier: trainer}, pokemon={"ash-2": balloon_state}
        )
        self.assertFalse(balloon_battle._is_actor_grounded(balloon_state))

    def test_klutz_swsh_knocks_item(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Aipom")
        attacker_spec.abilities = [{"name": "Klutz [SwSh]"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.items = [{"name": "Oran Berry"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["gary-1"].spec.items)
        self.assertTrue(any(evt.get("ability") == "Klutz [SwSh]" for evt in battle.log))

    def test_leek_mastery_blocks_item_theft(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Meowth")
        attacker_spec.moves = [
            MoveSpec(
                name="Knock Off",
                type="Dark",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Farfetch'd")
        defender_spec.abilities = [{"name": "Leek Mastery"}]
        defender_spec.items = [{"name": "Stick"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Knock Off", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].spec.items)
        self.assertTrue(any(evt.get("ability") == "Leek Mastery" for evt in battle.log))

    def test_rare_leek_grants_farfetchd_crit_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )

        attacker_spec = _pokemon_spec("Farfetch'd")
        attacker_spec.moves = [move]
        attacker_spec.items = [{"name": "Rare Leek"}]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = [move]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.rng = SequenceRNG([18] + [6] * 10)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle"
        )
        self.assertTrue(move_event.get("crit"))

        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.moves = [move]
        attacker_spec.items = [{"name": "Rare Leek"}]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = [move]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.rng = SequenceRNG([18] + [6] * 10)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle"
        )
        self.assertFalse(move_event.get("crit"))

    def test_thick_club_grants_pure_power(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )

        def _attack_value(items: list[dict]) -> int:
            attacker_spec = _pokemon_spec("Cubone")
            attacker_spec.moves = [move]
            attacker_spec.items = list(items)
            defender_spec = _pokemon_spec("Eevee")
            defender_spec.moves = [move]
            battle = BattleState(
                trainers={trainer.identifier: trainer, foe.identifier: foe},
                pokemon={
                    "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                    "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
                },
            )
            battle.rng = SequenceRNG([10] + [6] * 10)
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
            battle.resolve_next_action()
            move_event = next(
                evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle"
            )
            return int(move_event.get("attack_value") or 0)

        base_attack = _attack_value([])
        boosted_attack = _attack_value([{"name": "Thick Club"}])
        self.assertEqual(boosted_attack, base_attack * 2)

    def test_kings_rock_flinches_on_high_accuracy_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "King's Rock"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=2,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = list(attacker_spec.moves)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.rng = SequenceRNG([19] + [10] * 10)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state = battle.pokemon["gary-1"]
        self.assertTrue(defender_state.has_status("Flinched"))
        flinch_events = [
            evt
            for evt in battle.log
            if evt.get("effect") == "item_status" and "King's Rock" in (evt.get("description") or "")
        ]
        self.assertEqual(len(flinch_events), 1)

    def test_razor_fang_applies_injury_on_high_accuracy_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "Razor Fang"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=2,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = list(attacker_spec.moves)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.rng = SequenceRNG([19] + [10] * 10)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state = battle.pokemon["gary-1"]
        self.assertEqual(defender_state.injuries, 1)
        injury_events = [
            evt
            for evt in battle.log
            if evt.get("effect") == "injury" and evt.get("item") == "Razor Fang"
        ]
        self.assertEqual(len(injury_events), 1)

    def test_scope_lens_expands_crit_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "Scope Lens"}]
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = [move]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.rng = SequenceRNG([19] + [10] * 10)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle"
        )
        self.assertTrue(move_event.get("crit"))

        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.moves = [move]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.rng = SequenceRNG([19] + [10] * 10)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        move_event = next(
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Tackle"
        )
        self.assertFalse(move_event.get("crit"))

    def test_orb_items_apply_multi_type_damage_scalar(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")

        def _assert_scalar(item_name: str, move_type: str) -> None:
            move = MoveSpec(
                name="Test Move",
                type=move_type,
                category="Physical",
                db=6,
                ac=2,
                range_kind="Melee",
                range_value=1,
            )
            attacker_spec = _pokemon_spec("Pikachu")
            attacker_spec.items = [{"name": item_name}]
            attacker_spec.moves = [move]
            defender_spec = _pokemon_spec("Eevee")
            defender_spec.moves = [move]
            battle = BattleState(
                trainers={trainer.identifier: trainer, foe.identifier: foe},
                pokemon={
                    "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                    "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
                },
            )
            battle.rng = SequenceRNG([12] + [10] * 10)
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Test Move", target_id="gary-1"))
            battle.resolve_next_action()
            move_event = next(
                evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == "Test Move"
            )
            modifiers = (move_event.get("context") or {}).get("modifiers", [])
            matches = [
                mod
                for mod in modifiers
                if mod.get("kind") == "damage_scalar"
                and mod.get("source") == item_name
                and abs(float(mod.get("value") or 0) - 1.2) < 0.0001
            ]
            self.assertTrue(matches)

        _assert_scalar("Adamant Orb", "Dragon")
        _assert_scalar("Griseous Orb", "Ghost")
        _assert_scalar("Lustrous Orb", "Water")
        _assert_scalar("Soul Dew", "Psychic")

    def test_all_hit_orb_grants_team_crit_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally = TrainerState(identifier="misty", name="Misty")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "All-Hit Orb"}]
        ally_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer, ally.identifier: ally},
            pokemon={
                "ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier),
                "misty-1": PokemonState(spec=ally_spec, controller_id=trainer.identifier),
            },
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        for pid in ("ash-1", "misty-1"):
            mon = battle.pokemon[pid]
            entries = [
                entry
                for entry in mon.get_temporary_effects("crit_range_bonus")
                if entry.get("source") == "All-Hit Orb"
            ]
            self.assertTrue(entries)

    def test_all_dodge_orb_grants_team_evasion(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally = TrainerState(identifier="misty", name="Misty")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "All-Dodge Orb"}]
        ally_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer, ally.identifier: ally},
            pokemon={
                "ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier),
                "misty-1": PokemonState(spec=ally_spec, controller_id=trainer.identifier),
            },
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        for pid in ("ash-1", "misty-1"):
            mon = battle.pokemon[pid]
            entries = [
                entry
                for entry in mon.get_temporary_effects("evasion_bonus")
                if entry.get("source") == "All-Dodge Orb" and entry.get("amount") == 2
            ]
            self.assertTrue(entries)

    def test_all_mach_orb_grants_team_extra_actions(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally = TrainerState(identifier="misty", name="Misty")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "All-Mach Orb"}]
        ally_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer, ally.identifier: ally},
            pokemon={
                "ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier),
                "misty-1": PokemonState(spec=ally_spec, controller_id=trainer.identifier),
            },
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        for pid in ("ash-1", "misty-1"):
            mon = battle.pokemon[pid]
            entries = [
                entry
                for entry in mon.get_temporary_effects("extra_action")
                if entry.get("source") == "All-Mach Orb" and entry.get("round") == battle.round
            ]
            actions = {entry.get("action") for entry in entries}
            self.assertTrue({"shift", "swift"}.issubset(actions))

    def test_all_protect_orb_applies_protect_to_nearby_allies(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally = TrainerState(identifier="misty", name="Misty")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "All-Protect Orb"}]
        ally_spec = _pokemon_spec("Eevee")
        far_spec = _pokemon_spec("Psyduck")
        grid = GridState(width=10, height=10)
        battle = BattleState(
            trainers={trainer.identifier: trainer, ally.identifier: ally},
            pokemon={
                "ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier, position=(0, 0)),
                "misty-1": PokemonState(spec=ally_spec, controller_id=trainer.identifier, position=(0, 5)),
                "misty-2": PokemonState(spec=far_spec, controller_id=trainer.identifier, position=(0, 6)),
            },
            grid=grid,
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].has_status("Protect"))
        self.assertTrue(battle.pokemon["misty-1"].has_status("Protect"))
        self.assertFalse(battle.pokemon["misty-2"].has_status("Protect"))

    def test_aloraichium_z_grants_stoked_sparksurfer_for_round(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Raichu Alolan")
        user_spec.items = [{"name": "Aloraichium-Z"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        names = {str(move.name or "").strip().lower() for move in battle.pokemon["ash-1"].spec.moves}
        self.assertIn("stoked sparksurfer", names)
        entries = [
            entry
            for entry in battle.pokemon["ash-1"].get_temporary_effects("z_move_granted")
            if entry.get("source") == "Aloraichium-Z"
        ]
        self.assertTrue(entries)

    def test_altarianite_triggers_mega_altaria_form_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Altaria")
        user_spec.items = [{"name": "Altarianite"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        mon = battle.pokemon["ash-1"]
        self.assertEqual(mon.spec.atk, 11)
        self.assertEqual(mon.spec.defense, 11)
        self.assertEqual(mon.spec.spatk, 11)
        self.assertEqual(mon.spec.spdef, 11)
        self.assertEqual(mon.spec.spd, 8)
        self.assertIn("Dragon", mon.spec.types)
        self.assertIn("Fairy", mon.spec.types)
        self.assertTrue(mon.get_temporary_effects("mega_form"))

    def test_ampharosite_triggers_mega_ampharos_form_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Ampharos")
        user_spec.items = [{"name": "Ampharosite"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        mon = battle.pokemon["ash-1"]
        self.assertEqual(mon.spec.atk, 10)
        self.assertEqual(mon.spec.defense, 10)
        self.assertEqual(mon.spec.spatk, 17)
        self.assertEqual(mon.spec.spdef, 11)
        self.assertEqual(mon.spec.spd, 5)
        self.assertIn("Electric", mon.spec.types)
        self.assertIn("Dragon", mon.spec.types)
        self.assertTrue(mon.get_temporary_effects("mega_form"))

    def test_equipping_auto_pistol_adds_weapon_actions(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Auto Pistol", "tags": ["weapon", "ranged", "short"]}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        move_names = {str(move.name or "") for move in battle.pokemon["ash-1"].spec.moves}
        self.assertIn("Auto Pistol", move_names)
        self.assertIn("Auto Pistol (Double Tap)", move_names)
        self.assertIn("Auto Pistol (Hip Fire)", move_names)

    def test_equipping_axe_adds_weapon_actions(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Axe"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        move_names = {str(move.name or "") for move in battle.pokemon["ash-1"].spec.moves}
        self.assertIn("Axe Swing", move_names)
        self.assertIn("Axe Cleave", move_names)
        self.assertIn("Axe Chop", move_names)

    def test_weapon_def_override_uses_defense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "Auto Pistol", "tags": ["weapon", "ranged", "short"]}]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.defense = 4
        defender_spec.spdef = 14
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=defender_spec, controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker, "ash-2": defender},
        )
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        move = next(m for m in attacker.spec.moves if (m.name or "") == "Auto Pistol")
        result_def = resolve_move_action(SequenceRNG([20]), attacker, defender, move)
        move_no_override = copy.deepcopy(move)
        move_no_override.effects_text = ""
        result_spdef = resolve_move_action(SequenceRNG([20]), attacker, defender, move_no_override)
        self.assertGreater(result_def.get("damage", 0), result_spdef.get("damage", 0))

    def test_align_orb_evenly_shares_team_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Align Orb"}]
        ally_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={
                "ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier),
                "ash-2": PokemonState(spec=ally_spec, controller_id=trainer.identifier),
            },
        )
        battle.pokemon["ash-1"].hp = 10
        battle.pokemon["ash-2"].hp = 30
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].hp, 20)
        self.assertEqual(battle.pokemon["ash-2"].hp, 20)

    def test_apple_heals_fixed_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Apple"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].hp = 5
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].hp, 20)

    def test_big_apple_heals_fixed_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Big Apple"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].hp = 10
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].hp, 40)
        event = next(evt for evt in battle.log if evt.get("effect") == "heal" and evt.get("item") == "Big Apple")
        self.assertEqual(event.get("amount"), 30)
        self.assertEqual(event.get("target_hp"), 40)

    def test_tiny_apple_heals_fixed_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Tiny Apple"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].hp = 20
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].hp, 25)
        event = next(evt for evt in battle.log if evt.get("effect") == "heal" and evt.get("item") == "Tiny Apple")
        self.assertEqual(event.get("amount"), 5)
        self.assertEqual(event.get("target_hp"), 25)

    def test_hopo_berry_heals_fixed_hp(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Hopo Berry"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].hp = 10
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].hp, 15)
        event = next(evt for evt in battle.log if evt.get("effect") == "heal" and evt.get("item") == "Hopo Berry")
        self.assertEqual(event.get("amount"), 5)
        self.assertEqual(event.get("target_hp"), 15)

    def test_drash_berry_cures_splinter(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Drash Berry"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].statuses.append({"name": "Splinter", "source": "test"})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].has_status("Splinter"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("effect") == "cure_status" and evt.get("item") == "Drash Berry"
        )
        self.assertEqual(event.get("statuses"), ["splinter"])

    def test_basic_rope_has_no_combat_effect(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Basic Rope"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].spec.items)
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "item" and evt.get("item") == "Basic Rope"
        )
        self.assertEqual(event.get("effect"), "use_failed")
        self.assertEqual(event.get("round"), 0)
        self.assertEqual(event.get("phase"), "start")

    def test_bicycle_has_no_combat_effect(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Bicycle"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].spec.items)
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "item" and evt.get("item") == "Bicycle"
        )
        self.assertEqual(event.get("effect"), "use_failed")
        self.assertEqual(event.get("round"), 0)
        self.assertEqual(event.get("phase"), "start")

    def test_light_ball_boosts_attack_and_spatk(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Light Ball"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_scalar")
        self.assertTrue(any(entry.get("stat") == "atk" and abs(float(entry.get("multiplier") or 0) - 1.5) < 0.0001 for entry in effects))
        self.assertTrue(any(entry.get("stat") == "spatk" and abs(float(entry.get("multiplier") or 0) - 1.5) < 0.0001 for entry in effects))

    def test_turn_start_applies_and_logs_held_item_effects(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Light Ball"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )

        battle.start_round()
        while battle.current_actor_id != "ash-1":
            self.assertIsNotNone(battle.advance_turn())

        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_scalar")
        self.assertTrue(any(entry.get("stat") == "atk" for entry in effects))
        self.assertTrue(
            any(
                evt.get("type") == "item"
                and evt.get("item") == "Light Ball"
                and evt.get("effect") == "held_item_active"
                for evt in battle.log
            )
        )

    def test_quick_powder_doubles_ditto_speed(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        cases = [("Ditto", True), ("Pikachu", False)]
        for species, expect in cases:
            with self.subTest(species=species):
                user_spec = _pokemon_spec(species)
                user_spec.items = [{"name": "Quick Powder"}]
                battle = BattleState(
                    trainers={trainer.identifier: trainer},
                    pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
                )
                battle.item_system.apply_held_item_start("ash-1")
                effects = battle.pokemon["ash-1"].get_temporary_effects("stat_scalar")
                matches = [
                    entry
                    for entry in effects
                    if entry.get("stat") == "spd"
                    and abs(float(entry.get("multiplier") or 0) - 2.0) < 0.0001
                ]
                self.assertEqual(bool(matches), expect)

    def test_incense_boosts_matching_category_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        cases = [
            ("Sea Incense", "Water", "Physical"),
            ("Rock Incense", "Rock", "Physical"),
            ("Odd Incense", "Psychic", "Special"),
            ("Rose Incense", "Grass", "Special"),
        ]
        for item_name, mon_type, category in cases:
            with self.subTest(item=item_name):
                attacker_spec = _pokemon_spec("Pikachu")
                attacker_spec.types = [mon_type]
                attacker_spec.items = [{"name": item_name}]
                defender_spec = _pokemon_spec("Eevee")
                move = MoveSpec(
                    name="Test Move",
                    type=mon_type,
                    category=category,
                    db=6,
                    ac=None,
                    range_kind="Melee",
                    range_value=1,
                )
                battle = BattleState(
                    trainers={trainer.identifier: trainer, foe.identifier: foe},
                    pokemon={
                        "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                        "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
                    },
                )
                attacker = battle.pokemon["ash-1"]
                defender = battle.pokemon["gary-1"]
                context = build_attack_context(attacker, defender, move)
                battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
                scalars = [
                    mod
                    for mod in context.modifiers
                    if mod.kind == "damage_scalar"
                    and mod.source == item_name
                    and abs(float(mod.value) - 1.1) < 0.0001
                ]
                self.assertTrue(scalars)

    def test_incense_reduces_matching_category_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        cases = [
            ("Sea Incense", "Water", "Physical"),
            ("Rock Incense", "Rock", "Physical"),
            ("Odd Incense", "Psychic", "Special"),
            ("Rose Incense", "Grass", "Special"),
        ]
        for item_name, mon_type, category in cases:
            with self.subTest(item=item_name):
                defender_spec = _pokemon_spec("Pikachu")
                defender_spec.types = [mon_type]
                defender_spec.items = [{"name": item_name}]
                attacker_spec = _pokemon_spec("Eevee")
                move = MoveSpec(
                    name="Test Move",
                    type=mon_type,
                    category=category,
                    db=6,
                    ac=None,
                    range_kind="Melee",
                    range_value=1,
                )
                battle = BattleState(
                    trainers={trainer.identifier: trainer, foe.identifier: foe},
                    pokemon={
                        "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                        "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
                    },
                )
                defender = battle.pokemon["ash-1"]
                attacker = battle.pokemon["gary-1"]
                result = {"damage": 100, "type_multiplier": 1.0}
                ctx = ItemHookContext(
                    battle=battle,
                    events=[],
                    holder_id="ash-1",
                    holder=defender,
                    attacker_id="gary-1",
                    attacker=attacker,
                    move=move,
                    result=result,
                    phase="defender_mitigation",
                )
                apply_item_hooks("defender_mitigation", ctx)
                self.assertEqual(result["damage"], 90)
                event = next(
                    evt
                    for evt in ctx.events
                    if evt.get("effect") == "category_damage_scalar_defender"
                    and evt.get("item") == item_name
                )
                self.assertEqual(event.get("amount"), 90)

    def test_sea_incense_contact_bonus_for_azumarill(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Azumarill")
        attacker_spec.types = ["Water"]
        attacker_spec.items = [{"name": "Sea Incense"}]
        defender_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
            },
        )
        attacker = battle.pokemon["ash-1"]
        defender = battle.pokemon["gary-1"]
        context = build_attack_context(attacker, defender, move)
        battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
        scalars = [
            mod
            for mod in context.modifiers
            if mod.kind == "damage_scalar"
            and mod.source == "Sea Incense"
            and abs(float(mod.value) - 1.3) < 0.0001
        ]
        self.assertTrue(scalars)

    def test_rock_incense_bonsly_spdef_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Bonsly")
        user_spec.items = [{"name": "Rock Incense"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "spdef" and entry.get("amount") == 20 for entry in effects))

    def test_odd_incense_mr_mime_spatk_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Mr. Mime")
        user_spec.items = [{"name": "Odd Incense"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "spatk" and entry.get("amount") == 10 for entry in effects))

    def test_rose_incense_roselia_spatk_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Roselia")
        user_spec.items = [{"name": "Rose Incense"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "spatk" and entry.get("amount") == 10 for entry in effects))

    def test_megaphone_boosts_sonic_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "Megaphone"}]
        defender_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Sonic Boom",
            type="Normal",
            category="Special",
            db=6,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            keywords=["sonic"],
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
            },
        )
        attacker = battle.pokemon["ash-1"]
        defender = battle.pokemon["gary-1"]
        context = build_attack_context(attacker, defender, move)
        battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
        scalars = [
            mod
            for mod in context.modifiers
            if mod.kind == "damage_scalar"
            and mod.source == "Megaphone"
            and abs(float(mod.value) - 1.2) < 0.0001
        ]
        self.assertTrue(scalars)

    def test_loaded_dice_boosts_x_strike_power_and_crit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "Loaded Dice"}]
        defender_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Fury Swipes",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            keywords=["x-strike"],
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
            },
        )
        attacker = battle.pokemon["ash-1"]
        defender = battle.pokemon["gary-1"]
        context = build_attack_context(attacker, defender, move)
        events = battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
        power_mods = [
            mod
            for mod in context.modifiers
            if mod.kind == "power" and mod.source == "Loaded Dice" and int(mod.value) == 5
        ]
        self.assertTrue(power_mods)
        self.assertEqual(move.crit_range, 19)
        event = next(evt for evt in events if evt.get("effect") == "x_strike_bonus")
        self.assertEqual(event.get("power_bonus"), 5)
        self.assertEqual(event.get("crit_range"), 19)

    def test_wooloo_gambeson_increases_def_and_spdef(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Wooloo Gambeson"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "def" and entry.get("amount") == 5 for entry in effects))
        self.assertTrue(any(entry.get("stat") == "spdef" and entry.get("amount") == 5 for entry in effects))

    def test_leather_armour_increases_def(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Leather Armour"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "def" and entry.get("amount") == 10 for entry in effects))

    def test_pokey_orb_applies_splinter_status(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Pokey Orb"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        events = battle.item_system.apply_held_item_start("ash-1")
        self.assertTrue(battle.pokemon["ash-1"].has_status("Splinter"))
        event = next(evt for evt in events if evt.get("status") == "Splinter")
        self.assertEqual(event.get("item"), "Pokey Orb")
        self.assertEqual(event.get("effect"), "item_status")

    def test_guard_spec_blocks_negative_stage_changes(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Guard Spec"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        events: List[dict] = []
        move = MoveSpec(name="Tail Whip", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="ash-1",
            move=move,
            target=battle.pokemon["ash-1"],
            stat="def",
            delta=-1,
            description="Tail Whip lowers Defense.",
        )
        self.assertEqual(battle.pokemon["ash-1"].combat_stages.get("def"), 0)
        event = next(evt for evt in events if evt.get("effect") == "combat_stage_block")
        self.assertEqual(event.get("item"), "Guard Spec")
        self.assertEqual(event.get("stat"), "def")

    def test_dampening_foam_reduces_sonic_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Pikachu")
        defender_spec.items = [{"name": "Dampening Foam"}]
        attacker_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Sonic Boom",
            type="Normal",
            category="Special",
            db=6,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            keywords=["sonic"],
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
            },
        )
        defender = battle.pokemon["ash-1"]
        attacker = battle.pokemon["gary-1"]
        result = {"damage": 100, "type_multiplier": 1.0}
        ctx = ItemHookContext(
            battle=battle,
            events=[],
            holder_id="ash-1",
            holder=defender,
            attacker_id="gary-1",
            attacker=attacker,
            move=move,
            result=result,
            phase="defender_mitigation",
        )
        apply_item_hooks("defender_mitigation", ctx)
        self.assertEqual(result["damage"], 75)
        event = next(evt for evt in ctx.events if evt.get("effect") == "sonic_damage_scalar")
        self.assertEqual(event.get("amount"), 75)

    def test_dampening_foam_increases_fire_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Pikachu")
        defender_spec.items = [{"name": "Dampening Foam"}]
        attacker_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=4,
            ac=None,
            range_kind="Ranged",
            range_value=6,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
            },
        )
        defender = battle.pokemon["ash-1"]
        attacker = battle.pokemon["gary-1"]
        result = {"damage": 100, "type_multiplier": 1.0}
        ctx = ItemHookContext(
            battle=battle,
            events=[],
            holder_id="ash-1",
            holder=defender,
            attacker_id="gary-1",
            attacker=attacker,
            move=move,
            result=result,
            phase="defender_mitigation",
        )
        apply_item_hooks("defender_mitigation", ctx)
        self.assertEqual(result["damage"], 140)
        event = next(evt for evt in ctx.events if evt.get("effect") == "fire_vulnerability")
        self.assertEqual(event.get("amount"), 140)

    def test_heavy_duty_boots_blocks_hazard_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target_spec = _pokemon_spec("Pikachu")
        target_spec.items = [{"name": "Heavy-Duty Boots"}]
        target = PokemonState(spec=target_spec, controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"spikes": 2}}})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": target},
            grid=grid,
        )
        battle.item_system.apply_held_item_start("ash-1")
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        self.assertEqual(target.hp, target.max_hp())
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "item" and evt.get("effect") == "hazard_block"
        )
        self.assertEqual(event.get("item"), "Heavy-Duty Boots")
        self.assertEqual(event.get("hazard"), "spikes")

    def test_heavy_duty_boots_reduces_earthbound_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Pikachu")
        defender_spec.items = [{"name": "Heavy-Duty Boots"}]
        attacker_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Earthbound Slam",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            keywords=["earthbound"],
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
            },
        )
        defender = battle.pokemon["ash-1"]
        attacker = battle.pokemon["gary-1"]
        result = {"damage": 100, "type_multiplier": 1.0}
        ctx = ItemHookContext(
            battle=battle,
            events=[],
            holder_id="ash-1",
            holder=defender,
            attacker_id="gary-1",
            attacker=attacker,
            move=move,
            result=result,
            phase="defender_mitigation",
        )
        apply_item_hooks("defender_mitigation", ctx)
        self.assertEqual(result["damage"], 80)
        event = next(evt for evt in ctx.events if evt.get("effect") == "earthbound_resistance")
        self.assertEqual(event.get("amount"), 80)

    def test_abomasite_triggers_mega_abomasnow_form_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Abomasnow")
        user_spec.items = [{"name": "Abomasite"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        mon = battle.pokemon["ash-1"]
        self.assertEqual(mon.spec.atk, 13)
        self.assertEqual(mon.spec.defense, 11)
        self.assertEqual(mon.spec.spatk, 13)
        self.assertEqual(mon.spec.spdef, 11)
        self.assertEqual(mon.spec.spd, 3)
        self.assertIn("Grass", mon.spec.types)
        self.assertIn("Ice", mon.spec.types)
        self.assertTrue(mon.get_temporary_effects("mega_form"))

    def test_baby_food_applies_exp_multiplier_to_low_level(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Baby Food"}]
        user_spec.level = 10
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        effects = battle.pokemon["ash-1"].get_temporary_effects("exp_gain_multiplier")
        self.assertTrue(any(abs(float(entry.get("multiplier") or 0) - 1.2) < 0.0001 for entry in effects))

    def test_baby_food_ignored_for_high_level(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Baby Food"}]
        user_spec.level = 20
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].get_temporary_effects("exp_gain_multiplier"))

    def test_bandages_apply_and_break_on_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Bandages"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].get_temporary_effects("bandages"))
        before = battle.pokemon["ash-1"].hp
        battle.pokemon["ash-1"].apply_damage(1)
        self.assertLess(battle.pokemon["ash-1"].hp or 0, before or 0)
        self.assertFalse(battle.pokemon["ash-1"].get_temporary_effects("bandages"))

    def test_coagulant_cures_splinter(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Coagulant"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].statuses.append({"name": "Splinter"})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].has_status("Splinter"))

    def test_cornn_berry_cures_disabled(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Cornn Berry"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].statuses.append({"name": "Disabled", "move": "Tackle"})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].has_status("Disabled"))

    def test_cornerstone_mask_boosts_ogerpon_defense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Ogerpon")
        user_spec.items = [{"name": "Cornerstone Mask"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        base = defensive_stat(battle.pokemon["ash-1"], "physical")
        battle.item_system.apply_held_item_start("ash-1")
        boosted = defensive_stat(battle.pokemon["ash-1"], "physical")
        self.assertEqual(boosted, int(math.floor(base * 1.2)))

    def test_corrupted_clay_adds_shady_weather_immunity(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Corrupted Clay"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("weather_immunity")
        self.assertTrue(any(entry.get("weather") == "shady" for entry in effects))

    def test_cotton_down_padded_armour_increases_defense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Cotton Down Padded Armour"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "def" and entry.get("amount") == 5 for entry in effects))

    def test_covert_cloak_blocks_secondary_status(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Pikachu")
        defender_spec.items = [{"name": "Covert Cloak"}]
        attacker_spec = _pokemon_spec("Eevee")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
            },
        )
        battle.item_system.apply_held_item_start("ash-1")
        events: List[dict] = []
        move = MoveSpec(name="Bite", type="Dark", category="Physical", db=6)
        battle._apply_status(
            events,
            attacker_id="gary-1",
            target_id="ash-1",
            move=move,
            target=battle.pokemon["ash-1"],
            status="Flinched",
            effect="flinch",
            description="Secondary flinch.",
        )
        self.assertFalse(battle.pokemon["ash-1"].has_status("Flinched"))
        self.assertTrue(any(evt.get("effect") == "secondary_block" for evt in events))

    def test_cracked_pot_boosts_sinistea_speed_and_healing(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Sinistea")
        user_spec.items = [{"name": "Cracked Pot"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        mon = battle.pokemon["ash-1"]
        stat_mods = mon.get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "spd" and entry.get("amount") == 10 for entry in stat_mods))
        healing = mon.get_temporary_effects("healing_multiplier")
        self.assertTrue(any(abs(float(entry.get("multiplier") or 0) - 1.1) < 0.0001 for entry in healing))
        mon.hp = max(1, mon.max_hp() - 20)
        before = mon.hp or 0
        mon.heal(10)
        self.assertEqual(mon.hp, before + 11)

    def test_chitin_breastplate_modifies_base_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Chitin Breastplate"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "def" and entry.get("amount") == 20 for entry in effects))
        self.assertTrue(any(entry.get("stat") == "spdef" and entry.get("amount") == 5 for entry in effects))
        self.assertTrue(any(entry.get("stat") == "spd" and entry.get("amount") == -5 for entry in effects))

    def test_cleanse_orb_clears_hazards(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Cleanse Orb"}]
        grid = GridState(
            width=2,
            height=1,
            tiles={
                (0, 0): {"hazards": {"spikes": 1}},
                (1, 0): {"hazards": {"toxic_spikes": 2}},
            },
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
            grid=grid,
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        for tile in battle.grid.tiles.values():
            self.assertFalse(tile.get("hazards"))

    def test_cleanse_tag_cures_cursed(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Cleanse Tag"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.pokemon["ash-1"].statuses.append({"name": "Cursed"})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].has_status("Cursed"))

    def test_clear_amulet_grants_clear_body(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Clear Amulet"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        self.assertTrue(battle.pokemon["ash-1"].has_ability("Clear Body"))

    def test_climate_clay_assigned_weather_immunity(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Climate Clay", "weather": "Snow"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.weather = "Snowy Weather"
        battle.item_system.apply_held_item_start("ash-1")
        mon = battle.pokemon["ash-1"]
        before = mon.hp
        mon._handle_status_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(mon.hp, before)

    def test_equipping_club_adds_weapon_actions(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Club"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        move_names = {str(move.name or "") for move in battle.pokemon["ash-1"].spec.moves}
        self.assertIn("Club Swing", move_names)

    def test_chaos_plate_boosts_shadow_damage_scalar(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Gengar")
        attacker_spec.items = [{"name": "Chaos Plate"}]
        defender_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Shadow Jab",
            type="Shadow",
            category="Physical",
            db=8,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
            },
        )
        attacker = battle.pokemon["ash-1"]
        defender = battle.pokemon["gary-1"]
        context = build_attack_context(attacker, defender, move)
        battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
        scalars = [mod for mod in context.modifiers if mod.kind == "damage_scalar"]
        self.assertTrue(any(abs(float(mod.value) - 1.2) < 0.0001 for mod in scalars))

    def test_chaos_plate_reduces_shadow_damage_taken(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.items = [{"name": "Chaos Plate"}]
        attacker_spec = _pokemon_spec("Gengar")
        move = MoveSpec(
            name="Shadow Jab",
            type="Shadow",
            category="Physical",
            db=8,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
            },
        )
        defender = battle.pokemon["ash-1"]
        attacker = battle.pokemon["gary-1"]
        result = {"damage": 100, "type_multiplier": 1.0}
        ctx = ItemHookContext(
            battle=battle,
            events=[],
            holder_id="ash-1",
            holder=defender,
            attacker_id="gary-1",
            attacker=attacker,
            move=move,
            result=result,
            phase="defender_mitigation",
        )
        apply_item_hooks("defender_mitigation", ctx)
        self.assertEqual(result["damage"], 80)

    def test_prism_scale_reduces_category_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        cases = [
            ("Pikachu", "Special", 90),
            ("Feebas", "Special", 80),
            ("Feebas", "Physical", 90),
        ]
        for species, category, expected in cases:
            with self.subTest(species=species, category=category):
                defender_spec = _pokemon_spec(species)
                defender_spec.items = [{"name": "Prism Scale"}]
                attacker_spec = _pokemon_spec("Eevee")
                move = MoveSpec(
                    name="Test Move",
                    type="Water",
                    category=category,
                    db=8,
                    ac=None,
                    range_kind="Melee",
                    range_value=1,
                )
                battle = BattleState(
                    trainers={trainer.identifier: trainer, foe.identifier: foe},
                    pokemon={
                        "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                        "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
                    },
                )
                defender = battle.pokemon["ash-1"]
                attacker = battle.pokemon["gary-1"]
                result = {"damage": 100, "type_multiplier": 1.0}
                ctx = ItemHookContext(
                    battle=battle,
                    events=[],
                    holder_id="ash-1",
                    holder=defender,
                    attacker_id="gary-1",
                    attacker=attacker,
                    move=move,
                    result=result,
                    phase="defender_mitigation",
                )
                apply_item_hooks("defender_mitigation", ctx)
                self.assertEqual(result["damage"], expected)
                if expected != 100:
                    event = next(
                        evt
                        for evt in ctx.events
                        if evt.get("effect") == "category_damage_scalar_defender"
                        and evt.get("item") == "Prism Scale"
                    )
                    self.assertEqual(event.get("amount"), expected)

    def test_metal_alloy_reduces_special_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        cases = [
            (["Electric"], 90),
            (["Steel"], 80),
        ]
        for types, expected in cases:
            with self.subTest(types=types):
                defender_spec = _pokemon_spec("Pikachu")
                defender_spec.types = types
                defender_spec.items = [{"name": "Metal Alloy"}]
                attacker_spec = _pokemon_spec("Eevee")
                move = MoveSpec(
                    name="Test Move",
                    type="Fire",
                    category="Special",
                    db=8,
                    ac=None,
                    range_kind="Melee",
                    range_value=1,
                )
                battle = BattleState(
                    trainers={trainer.identifier: trainer, foe.identifier: foe},
                    pokemon={
                        "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                        "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
                    },
                )
                defender = battle.pokemon["ash-1"]
                attacker = battle.pokemon["gary-1"]
                result = {"damage": 100, "type_multiplier": 1.0}
                ctx = ItemHookContext(
                    battle=battle,
                    events=[],
                    holder_id="ash-1",
                    holder=defender,
                    attacker_id="gary-1",
                    attacker=attacker,
                    move=move,
                    result=result,
                    phase="defender_mitigation",
                )
                apply_item_hooks("defender_mitigation", ctx)
                self.assertEqual(result["damage"], expected)
                event = next(
                    evt
                    for evt in ctx.events
                    if evt.get("effect") == "category_damage_scalar_defender"
                    and evt.get("item") == "Metal Alloy"
                )
                self.assertEqual(event.get("amount"), expected)

    def test_frosterizer_reduces_physical_damage_for_jynx_line(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        cases = [
            ("Jynx", 75),
            ("Pikachu", 100),
        ]
        for species, expected in cases:
            with self.subTest(species=species):
                defender_spec = _pokemon_spec(species)
                defender_spec.items = [{"name": "Frosterizer"}]
                attacker_spec = _pokemon_spec("Eevee")
                move = MoveSpec(
                    name="Test Move",
                    type="Normal",
                    category="Physical",
                    db=8,
                    ac=None,
                    range_kind="Melee",
                    range_value=1,
                )
                battle = BattleState(
                    trainers={trainer.identifier: trainer, foe.identifier: foe},
                    pokemon={
                        "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                        "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
                    },
                )
                defender = battle.pokemon["ash-1"]
                attacker = battle.pokemon["gary-1"]
                result = {"damage": 100, "type_multiplier": 1.0}
                ctx = ItemHookContext(
                    battle=battle,
                    events=[],
                    holder_id="ash-1",
                    holder=defender,
                    attacker_id="gary-1",
                    attacker=attacker,
                    move=move,
                    result=result,
                    phase="defender_mitigation",
                )
                apply_item_hooks("defender_mitigation", ctx)
                self.assertEqual(result["damage"], expected)
                if expected != 100:
                    event = next(
                        evt
                        for evt in ctx.events
                        if evt.get("effect") == "category_damage_scalar_defender"
                        and evt.get("item") == "Frosterizer"
                    )
                    self.assertEqual(event.get("amount"), expected)

    def test_blank_and_warm_plate_apply_damage_scalar(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        cases = [("Blank Plate", "Normal"), ("Warm Plate", "Nuclear")]
        for item_name, move_type in cases:
            with self.subTest(item=item_name):
                attacker_spec = _pokemon_spec("Pikachu")
                attacker_spec.items = [{"name": item_name}]
                defender_spec = _pokemon_spec("Eevee")
                move = MoveSpec(
                    name="Plate Strike",
                    type=move_type,
                    category="Physical",
                    db=8,
                    ac=None,
                    range_kind="Melee",
                    range_value=1,
                )
                battle = BattleState(
                    trainers={trainer.identifier: trainer, foe.identifier: foe},
                    pokemon={
                        "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                        "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
                    },
                )
                attacker = battle.pokemon["ash-1"]
                defender = battle.pokemon["gary-1"]
                context = build_attack_context(attacker, defender, move)
                battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
                scalars = [
                    mod
                    for mod in context.modifiers
                    if mod.kind == "damage_scalar"
                    and mod.source == item_name
                    and abs(float(mod.value) - 1.2) < 0.0001
                ]
                self.assertTrue(scalars)

    def test_blank_and_warm_plate_reduce_damage_taken(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        cases = [("Blank Plate", "Normal"), ("Warm Plate", "Nuclear")]
        for item_name, move_type in cases:
            with self.subTest(item=item_name):
                defender_spec = _pokemon_spec("Eevee")
                defender_spec.items = [{"name": item_name}]
                attacker_spec = _pokemon_spec("Pikachu")
                move = MoveSpec(
                    name="Plate Strike",
                    type=move_type,
                    category="Physical",
                    db=8,
                    ac=None,
                    range_kind="Melee",
                    range_value=1,
                )
                battle = BattleState(
                    trainers={trainer.identifier: trainer, foe.identifier: foe},
                    pokemon={
                        "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                        "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
                    },
                )
                defender = battle.pokemon["ash-1"]
                attacker = battle.pokemon["gary-1"]
                result = {"damage": 100, "type_multiplier": 1.0}
                ctx = ItemHookContext(
                    battle=battle,
                    events=[],
                    holder_id="ash-1",
                    holder=defender,
                    attacker_id="gary-1",
                    attacker=attacker,
                    move=move,
                    result=result,
                    phase="defender_mitigation",
                )
                apply_item_hooks("defender_mitigation", ctx)
                self.assertEqual(result["damage"], 80)

    def test_big_leek_grants_hustle(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Farfetchd")
        user_spec.items = [{"name": "Big Leek"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        mon = battle.pokemon["ash-1"]
        self.assertTrue(mon.has_ability("Hustle"))

    def test_scale_mail_modifies_base_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Scale Mail"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "def" and entry.get("amount") == 15 for entry in effects))
        self.assertTrue(any(entry.get("stat") == "spdef" and entry.get("amount") == 5 for entry in effects))
        self.assertTrue(any(entry.get("stat") == "spd" and entry.get("amount") == -5 for entry in effects))

    def test_luck_incense_grants_accuracy_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Luck Incense"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("accuracy_bonus")
        self.assertTrue(any(entry.get("amount") == 1 for entry in effects))

    def test_razor_claw_grants_crit_range_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Razor Claw"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        effects = battle.pokemon["ash-1"].get_temporary_effects("crit_range_bonus")
        self.assertTrue(any(entry.get("bonus") == 1 for entry in effects))

    def test_wise_glasses_boosts_special_damage_scalar(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "Wise Glasses"}]
        defender_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
            },
        )
        attacker = battle.pokemon["ash-1"]
        defender = battle.pokemon["gary-1"]
        context = build_attack_context(attacker, defender, move)
        battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
        scalars = [
            mod
            for mod in context.modifiers
            if mod.kind == "damage_scalar"
            and mod.source == "Wise Glasses"
            and abs(float(mod.value) - 1.1) < 0.0001
        ]
        self.assertTrue(scalars)

    def test_muscle_band_boosts_physical_damage_scalar(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.items = [{"name": "Muscle Band"}]
        defender_spec = _pokemon_spec("Eevee")
        move = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
            },
        )
        attacker = battle.pokemon["ash-1"]
        defender = battle.pokemon["gary-1"]
        context = build_attack_context(attacker, defender, move)
        battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
        scalars = [
            mod
            for mod in context.modifiers
            if mod.kind == "damage_scalar"
            and mod.source == "Muscle Band"
            and abs(float(mod.value) - 1.1) < 0.0001
        ]
        self.assertTrue(scalars)

    def test_chilly_clay_blocks_snow_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Chilly Clay"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.weather = "Snowy Weather"
        battle.item_system.apply_held_item_start("ash-1")
        mon = battle.pokemon["ash-1"]
        before = mon.hp
        mon._handle_status_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(mon.hp, before)

    def test_chipped_pot_boosts_sinistea_and_healing(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Sinistea")
        user_spec.items = [{"name": "Chipped Pot"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.item_system.apply_held_item_start("ash-1")
        mon = battle.pokemon["ash-1"]
        stat_mods = mon.get_temporary_effects("stat_modifier")
        self.assertTrue(any(entry.get("stat") == "def" and entry.get("amount") == 5 for entry in stat_mods))
        self.assertTrue(any(entry.get("stat") == "spdef" and entry.get("amount") == 5 for entry in stat_mods))
        healing = mon.get_temporary_effects("healing_multiplier")
        self.assertTrue(any(abs(float(entry.get("multiplier") or 0) - 1.2) < 0.0001 for entry in healing))
        mon.hp = max(1, mon.max_hp() - 20)
        before = mon.hp or 0
        mon.heal(10)
        self.assertEqual(mon.hp, before + 12)

    def test_bank_orb_restores_ip_resource(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Bank Orb"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.trainers["ash"].feature_resources.get("IP"), 5)

    def test_bait_attachment_tracks_resource(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Bait Attachment"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.trainers["ash"].feature_resources.get("bait_attachment"), 1)

    def test_bait_distracts_on_failed_focus_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Bait"}]
        target_spec = _pokemon_spec("Eevee")
        target_spec.skills = {"focus": 0}
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=target_spec, controller_id=foe.identifier),
            },
            rng=SequenceRNG([1]),
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Flinched"))

    def test_bait_resisted_on_successful_focus_roll(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Pikachu")
        user_spec.items = [{"name": "Bait"}]
        target_spec = _pokemon_spec("Eevee")
        target_spec.skills = {"focus": 2}
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=target_spec, controller_id=foe.identifier),
            },
            rng=SequenceRNG([20]),
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["gary-1"].has_status("Flinched"))

    def test_audinite_triggers_mega_audino_form_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Audino")
        user_spec.items = [{"name": "Audinite"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        mon = battle.pokemon["ash-1"]
        self.assertEqual(mon.spec.atk, 6)
        self.assertEqual(mon.spec.defense, 13)
        self.assertEqual(mon.spec.spatk, 8)
        self.assertEqual(mon.spec.spdef, 13)
        self.assertEqual(mon.spec.spd, 5)
        self.assertIn("Normal", mon.spec.types)
        self.assertIn("Fairy", mon.spec.types)
        self.assertTrue(mon.get_temporary_effects("mega_form"))

    def test_banettite_triggers_mega_banette_form_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Banette")
        user_spec.items = [{"name": "Banettite"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        mon = battle.pokemon["ash-1"]
        self.assertEqual(mon.spec.atk, 17)
        self.assertEqual(mon.spec.defense, 8)
        self.assertEqual(mon.spec.spatk, 9)
        self.assertEqual(mon.spec.spdef, 8)
        self.assertEqual(mon.spec.spd, 8)
        self.assertIn("Ghost", mon.spec.types)
        self.assertTrue(mon.get_temporary_effects("mega_form"))

    def test_charizardite_x_triggers_mega_charizard_x_form_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Charizard")
        user_spec.items = [{"name": "Charizardite X"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        mon = battle.pokemon["ash-1"]
        self.assertEqual(mon.spec.atk, 13)
        self.assertEqual(mon.spec.defense, 11)
        self.assertEqual(mon.spec.spatk, 13)
        self.assertEqual(mon.spec.spdef, 9)
        self.assertEqual(mon.spec.spd, 10)
        self.assertIn("Fire", mon.spec.types)
        self.assertIn("Dragon", mon.spec.types)
        self.assertTrue(mon.get_temporary_effects("mega_form"))

    def test_charizardite_y_triggers_mega_charizard_y_form_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Charizard")
        user_spec.items = [{"name": "Charizardite Y"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        mon = battle.pokemon["ash-1"]
        self.assertEqual(mon.spec.atk, 10)
        self.assertEqual(mon.spec.defense, 8)
        self.assertEqual(mon.spec.spatk, 16)
        self.assertEqual(mon.spec.spdef, 12)
        self.assertEqual(mon.spec.spd, 10)
        self.assertIn("Fire", mon.spec.types)
        self.assertIn("Flying", mon.spec.types)
        self.assertTrue(mon.get_temporary_effects("mega_form"))

    def test_focus_sash_prevents_knockout(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.items = [{"name": "Focus Sash"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier),
            },
        )
        defender = battle.pokemon["gary-1"]
        move = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6)
        result = {"damage": defender.hp, "type_multiplier": 1.0}
        events: List[dict] = []
        battle._apply_defender_item_mitigation(
            "gary-1", defender, "ash-1", move, result, events
        )
        self.assertEqual(result.get("damage"), (defender.hp or 0) - 1)
        self.assertFalse(defender.spec.items)
        self.assertTrue(any(evt.get("effect") == "focus_sash" for evt in events))

    def test_landslide_boosts_ground_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Sandshrew")
        attacker_spec.abilities = [{"name": "Landslide"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Mud Shot",
                type="Ground",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mud Shot", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Landslide" for evt in battle.log))

    def test_mach_speed_boosts_flying_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgeotto")
        attacker_spec.abilities = [{"name": "Mach Speed"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Wing Attack",
                type="Flying",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Caterpie"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Wing Attack", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Mach Speed" for evt in battle.log))

    def test_leaf_gift_grants_chosen_suit_abilities(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Leafeon")
        spec.abilities = [{"name": "Leaf Gift"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.add_temporary_effect("leaf_gift_suit_choice", suit="vibrant")
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Leaf Gift", target_id="ash-1"))
        battle.resolve_next_action()
        granted = [entry.get("ability") for entry in state.get_temporary_effects("ability_granted")]
        self.assertIn("Chlorophyll", granted)
        self.assertIn("Photosynthesis", granted)

    def test_life_force_restores_tick(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Chansey")
        spec.abilities = [{"name": "Life Force"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.hp = max(1, state.max_hp() - state.tick_value())
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        starting_hp = state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Life Force", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertGreater(state.hp, starting_hp)
        self.assertTrue(any(evt.get("ability") == "Life Force" for evt in battle.log))

    def test_lightning_kicks_grants_priority(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Hitmonlee")
        attacker_spec.abilities = [{"name": "Lightning Kicks"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Low Kick",
                type="Fighting",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Lightning Kicks", target_id="ash-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Low Kick", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Lightning Kicks" for evt in battle.log))

    def test_lullaby_makes_sing_auto_hit(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 1

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Jigglypuff")
        attacker_spec.abilities = [{"name": "Lullaby"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Sing",
                type="Normal",
                category="Status",
                db=0,
                ac=20,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Lullaby", target_id="ash-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Sing", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Sleep") or defender_state.has_status("Asleep"))
        self.assertTrue(any(evt.get("ability") == "Lullaby" for evt in battle.log))

    def test_lunchbox_adds_temp_hp_on_food_buff_trade(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        actor_spec = _pokemon_spec("Snorlax")
        actor_spec.abilities = [{"name": "Lunchbox"}]
        actor = PokemonState(spec=actor_spec, controller_id=trainer.identifier)
        actor.food_buffs = [{"name": "Digestion", "effect": "digestion"}]
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": actor})
        events: List[dict] = []
        battle._consume_food_buff(
            "ash-1",
            actor,
            0,
            "digestion",
            "Consumed digestion buff.",
            events,
        )
        self.assertEqual(actor.temp_hp, 5)
        self.assertTrue(any(evt.get("ability") == "Lunchbox" for evt in events))

    def test_magic_bounce_reflects_status(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Thunder Wave",
                type="Electric",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Espeon")
        defender_spec.abilities = [{"name": "Magic Bounce"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Thunder Wave", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].has_status("Paralyzed"))
        self.assertFalse(battle.pokemon["gary-1"].has_status("Paralyzed"))
        self.assertTrue(any(evt.get("ability") == "Magic Bounce" for evt in battle.log))

    def test_magic_guard_blocks_hazard_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target_spec = _pokemon_spec("Clefairy")
        target_spec.abilities = [{"name": "Magic Guard"}]
        target = PokemonState(spec=target_spec, controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"spikes": 1}}})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": target},
            grid=grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        self.assertEqual(target.hp, target.max_hp())
        self.assertTrue(any(evt.get("ability") == "Magic Guard" for evt in battle.log))

    def test_magic_guard_blocks_poison_tick_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target_spec = _pokemon_spec("Clefairy")
        target_spec.abilities = [{"name": "Magic Guard"}]
        target_spec.statuses = [{"name": "Poisoned"}]
        target = PokemonState(spec=target_spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": target},
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.advance_phase()
        battle.advance_phase()
        battle.advance_phase()
        self.assertEqual(target.hp, target.max_hp())

    def test_magic_guard_blocks_solar_power_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target_spec = _pokemon_spec("Heliolisk")
        target_spec.abilities = [{"name": "Magic Guard"}, {"name": "Solar Power"}]
        target = PokemonState(spec=target_spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": target},
            weather="Sunny",
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.advance_phase()
        battle.advance_phase()
        battle.advance_phase()
        self.assertEqual(target.hp, target.max_hp())
        self.assertTrue(any(evt.get("ability") == "Magic Guard" for evt in battle.log))

    def test_magician_steals_item_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Delphox")
        attacker_spec.abilities = [{"name": "Magician"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Bidoof")
        defender_spec.items = [{"name": "Potion"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].spec.items)
        self.assertFalse(battle.pokemon["gary-1"].spec.items)
        self.assertTrue(any(evt.get("ability") == "Magician" for evt in battle.log))

    def test_magnet_pull_restricts_shift_distance(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Magnemite")
        attacker_spec.abilities = [{"name": "Magnet Pull"}]
        defender_spec = _pokemon_spec("Magnemite")
        defender_spec.types = ["Steel"]
        grid = GridState(width=12, height=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(4, 0)),
            },
            grid=grid,
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Magnet Pull", target_id="gary-1"))
        battle.resolve_next_action()
        with self.assertRaises(ValueError):
            ShiftAction(actor_id="gary-1", destination=(9, 0)).validate(battle)

    def test_marvel_scale_boosts_defense_while_afflicted(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Milotic")
        spec.abilities = [{"name": "Marvel Scale"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        events: List[dict] = []
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="ash-1",
            move=MoveSpec(name="Will-O-Wisp", type="Fire", category="Status"),
            target=state,
            status="Burned",
            effect="burn",
            description="Burn applied.",
        )
        state._handle_status_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.combat_stages.get("def", 0), 2)
        state.remove_status_by_names({"burn", "burned"})
        state._handle_status_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.combat_stages.get("def", 0), 0)

    def test_mega_launcher_boosts_pulse_move_db(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Blastoise")
        attacker_spec.abilities = [{"name": "Mega Launcher"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Water Pulse",
                type="Water",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Geodude"), controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Water Pulse", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Mega Launcher" for evt in battle.log))

    def test_memory_wipe_disables_last_move(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Porygon")
        attacker_spec.abilities = [{"name": "Memory Wipe"}]
        defender_state = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
        )
        defender_state.add_temporary_effect("last_move", name="Tackle", round=battle.round)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Memory Wipe", target_id="gary-1"))
        battle.resolve_next_action()
        disabled = [
            status
            for status in defender_state.statuses
            if isinstance(status, dict) and status.get("name") == "Disabled"
        ]
        self.assertTrue(disabled)
        self.assertEqual(disabled[0].get("move"), "Tackle")
        self.assertTrue(any(evt.get("ability") == "Memory Wipe" for evt in battle.log))

    def test_migraine_grants_telekinetic_capability(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Abra")
        spec.abilities = [{"name": "Migraine"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.hp = max(1, state.max_hp() // 2)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        events = state._handle_status_phase_effects(battle, TurnPhase.START, "ash-1")
        granted = [
            entry
            for entry in state.get_temporary_effects("capability_granted")
            if entry.get("capability") == "Telekinetic"
        ]
        self.assertTrue(granted)
        self.assertTrue(any(evt.get("ability") == "Migraine" for evt in events))

    def test_mimitree_ignores_mimic_frequency(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Sudowoodo")
        attacker_spec.abilities = [{"name": "Mimitree"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Mimic",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mimic", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertNotIn("Mimic", battle.frequency_usage.get("ash-1", {}))
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mimic", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Mimitree" for evt in battle.log))

    def test_mind_mold_boosts_psychic_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Espeon")
        attacker_spec.abilities = [{"name": "Mind Mold"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Psychic",
                type="Psychic",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Psychic", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Mind Mold" for evt in battle.log))

    def test_mini_noses_deploys_adjacent_origins(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Porygon")
        spec.abilities = [{"name": "Mini-Noses"}]
        grid = GridState(width=3, height=3)
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(1, 1))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state}, grid=grid)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mini-Noses", target_id="ash-1"))
        battle.resolve_next_action()
        entries = state.get_temporary_effects("mini_noses")
        self.assertTrue(entries)
        origins = entries[0].get("origins", [])
        self.assertTrue(origins)
        self.assertTrue(any(evt.get("ability") == "Mini-Noses" for evt in battle.log))

    def test_minus_boosts_plus_user_special_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Minun")
        attacker_spec.abilities = [{"name": "Minus"}]
        defender_spec = _pokemon_spec("Plusle")
        defender_spec.abilities = [{"name": "Plus"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Minus", target_id="ash-2"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-2"].combat_stages.get("spatk", 0), 2)
        self.assertTrue(any(evt.get("ability") == "Minus" for evt in battle.log))

    def test_plus_boosts_minus_user_special_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Plusle")
        attacker_spec.abilities = [{"name": "Plus"}]
        defender_spec = _pokemon_spec("Minun")
        defender_spec.abilities = [{"name": "Minus"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Plus", target_id="ash-2"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-2"].combat_stages.get("spatk", 0), 2)
        self.assertTrue(any(evt.get("ability") == "Plus" for evt in battle.log))

    def test_minus_swsh_intensifies_stat_drop(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(
            spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier, position=(0, 2)
        )
        holder_spec = _pokemon_spec("Minun")
        holder_spec.abilities = [{"name": "Minus [SwSh]"}]
        holder_state = PokemonState(
            spec=holder_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        target_state = PokemonState(
            spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "ash-2": holder_state, "gary-1": target_state},
        )
        events: List[dict] = []
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=MoveSpec(name="Growl", type="Normal", category="Status"),
            target=target_state,
            stat="atk",
            delta=-1,
            description="Growl lowers Attack.",
        )
        self.assertEqual(target_state.combat_stages.get("atk", 0), -2)
        self.assertTrue(any(evt.get("ability") == "Minus [SwSh]" for evt in events))

    def test_plus_swsh_intensifies_stat_raise(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally = TrainerState(identifier="misty", name="Misty")
        attacker_state = PokemonState(
            spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier, position=(0, 2)
        )
        holder_spec = _pokemon_spec("Plusle")
        holder_spec.abilities = [{"name": "Plus [SwSh]"}]
        holder_state = PokemonState(
            spec=holder_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        target_state = PokemonState(
            spec=_pokemon_spec("Staryu"), controller_id=trainer.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, ally.identifier: ally},
            pokemon={"ash-1": attacker_state, "ash-2": holder_state, "ash-3": target_state},
        )
        events: List[dict] = []
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="ash-3",
            move=MoveSpec(name="Tail Whip", type="Normal", category="Status"),
            target=target_state,
            stat="def",
            delta=1,
            description="Test raise.",
        )
        self.assertEqual(target_state.combat_stages.get("def", 0), 2)
        self.assertTrue(any(evt.get("ability") == "Plus [SwSh]" for evt in events))

    def test_rocket_grants_first_initiative_next_round(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Rocket",
            type="Flying",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Jet")
        attacker_spec.moves = [move]
        attacker_spec.abilities = [{"name": "Rocket"}]
        defender_spec = _pokemon_spec("Slowpoke")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Rocket", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].get_temporary_effects("rocket_initiative"))
        battle.start_round()
        first_pokemon_entry = next(
            entry for entry in battle.initiative_order if entry.actor_id not in battle.trainers
        )
        self.assertEqual(first_pokemon_entry.actor_id, "ash-1")

    def test_miracle_mile_boosts_fairy_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Clefable")
        attacker_spec.abilities = [{"name": "Miracle Mile"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Fairy Wind",
                type="Fairy",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        defender_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Fairy Wind", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Miracle Mile" for evt in battle.log))

    def test_mojo_allows_ghost_damage_on_normal_targets(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Gengar")
        attacker_spec.abilities = [{"name": "Mojo"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Shadow Ball",
                type="Ghost",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.types = ["Normal"]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=FixedRNG(),
        )
        starting_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shadow Ball", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertLess(defender_state.hp, starting_hp)

    def test_light_metal_reduces_weight_class(self) -> None:
        spec = _pokemon_spec("Scizor")
        spec.weight = 5
        spec.abilities = [{"name": "Light Metal"}]
        state = PokemonState(spec=spec, controller_id="ash")
        self.assertEqual(state.weight_class(), 3)

    def test_magma_armor_contact_tick_and_freeze_immunity(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Zigzagoon")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Slugma")
        defender_spec.abilities = [{"name": "Magma Armor"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        attacker_state.hp = attacker_state.max_hp()
        move = _contact_move_spec("Tackle")
        events = battle._handle_contact_ability_effects(
            "ash-1",
            attacker_state,
            "gary-1",
            defender_state,
            move,
        )
        self.assertTrue(any(evt.get("ability") == "Magma Armor" for evt in events))
        self.assertLess(attacker_state.hp, attacker_state.max_hp())
        events = []
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=MoveSpec(name="Ice Beam", type="Ice", category="Special"),
            target=defender_state,
            status="Frozen",
            effect="freeze",
            description="Ice Beam freezes the target.",
        )
        self.assertFalse(defender_state.has_status("Frozen"))
        self.assertTrue(any(evt.get("ability") == "Magma Armor" for evt in events))

    def test_motor_drive_absorbs_electric_and_boosts_speed(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Thunder Shock",
                type="Electric",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Jolteon")
        defender_spec.abilities = [{"name": "Motor Drive"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages["spd"], 1)
        self.assertTrue(any(evt.get("ability") == "Motor Drive" for evt in battle.log))
        self.assertEqual(battle.pokemon["gary-1"].hp, battle.pokemon["gary-1"].max_hp())

    def test_moxie_raises_attack_on_ko(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 20

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Gyarados")
        attacker_spec.abilities = [{"name": "Moxie"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Bite",
                type="Dark",
                category="Physical",
                db=10,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Caterpie"), controller_id=foe.identifier, position=(0, 1)
        )
        defender_state.hp = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.combat_stages["atk"], 1)
        self.assertTrue(any(evt.get("ability") == "Moxie" for evt in battle.log))

    def test_blessed_touch_heals_adjacent_ally(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Audino")
        attacker_spec.abilities = [{"name": "Blessed Touch"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Blessed Touch",
                type="Normal",
                category="Status",
                range_kind="Melee",
                range_value=1,
                ac=None,
            )
        ]
        healer = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        ally_spec = _pokemon_spec("Pikachu")
        ally_state = PokemonState(
            spec=ally_spec, controller_id=trainer.identifier, position=(0, 1)
        )
        ally_state.hp = max(1, ally_state.max_hp() // 2)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": healer, "ash-2": ally_state},
        )
        before_hp = ally_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Blessed Touch", target_id="ash-2"))
        battle.resolve_next_action()
        self.assertGreater(ally_state.hp, before_hp)
        move_events = [
            evt for evt in battle.log if evt.get("move") == "Blessed Touch"
        ]
        self.assertTrue(move_events)

    def test_blow_away_adds_tick_after_whirlwind(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgeot")
        attacker_spec.abilities = [{"name": "Blow Away"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Whirlwind",
                type="Normal",
                category="Status",
                range_kind="Melee",
                range_value=1,
                ac=None,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Whirlwind", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertLess(defender_state.hp, before_hp)
        ability_events = [
            evt for evt in battle.log if evt.get("ability") == "Blow Away"
        ]
        self.assertTrue(ability_events)

    def test_blur_requires_accuracy_roll(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 4

        attacker_spec = _pokemon_spec("Rattata")
        defender_spec = _pokemon_spec("Kadabra")
        defender_spec.defense = 30
        defender_spec.abilities = [{"name": "Blur"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        defender_state = PokemonState(spec=defender_spec, controller_id="gary")
        move = MoveSpec(
            name="Slam",
            type="Normal",
            category="Physical",
            db=8,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        result = resolve_move_action(FixedRNG(), attacker_state, defender_state, move)
        self.assertFalse(result["hit"])

    def test_bodyguard_intercepts_and_resists(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=foe.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier, position=(0, 1)
        )
        guard_spec = _pokemon_spec("Blissey")
        guard_spec.abilities = [{"name": "Bodyguard"}]
        guard_state = PokemonState(
            spec=guard_spec, controller_id=trainer.identifier, position=(0, 2)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "foe-1": attacker_state,
                "ash-1": defender_state,
                "ash-2": guard_state,
            },
        )
        battle.queue_action(UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        bodyguard_events = [
            evt for evt in battle.log if evt.get("ability") == "Bodyguard"
        ]
        self.assertTrue(any(evt.get("effect") == "redirect" for evt in bodyguard_events))
        self.assertTrue(any(evt.get("effect") == "resist" for evt in bodyguard_events))

    def test_bone_lord_forces_flinch_on_bone_club(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Marowak")
        attacker_spec.abilities = [{"name": "Bone Lord"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Bone Club",
                type="Ground",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Zubat"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bone Club", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Flinch"))
        ability_events = [
            evt for evt in battle.log if evt.get("ability") == "Bone Lord"
        ]
        self.assertTrue(ability_events)

    def test_bone_wielder_adds_accuracy_for_bone_moves(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 2

        attacker_spec = _pokemon_spec("Marowak")
        attacker_spec.abilities = [{"name": "Bone Wielder"}]
        attacker_spec.items = [{"name": "Thick Club"}]
        defender_spec = _pokemon_spec("Meowth")
        defender_spec.defense = 5
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        defender_state = PokemonState(spec=defender_spec, controller_id="gary")
        move = MoveSpec(
            name="Bone Club",
            type="Ground",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        result = resolve_move_action(FixedRNG(), attacker_state, defender_state, move)
        self.assertTrue(result["hit"])

    def test_brimstone_adds_poison_on_fire_burn(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Houndour")
        attacker_spec.abilities = [{"name": "Brimstone"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(
            spec=_pokemon_spec("Oddish"), controller_id=foe.identifier
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=None,
        )
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            status="Burned",
            effect="status",
            description="Ember burns the target.",
        )
        self.assertTrue(defender_state.has_status("Poisoned"))
        self.assertTrue(any(evt.get("status") == "Poisoned" for evt in events))

    def test_bulletproof_resists_ranged_attacks(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Shock Pulse",
                type="Normal",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.abilities = [{"name": "Bulletproof"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shock Pulse", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shock Pulse", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - battle.pokemon["gary-1"].hp
        damage_without = baseline.pokemon["gary-1"].max_hp() - baseline.pokemon["gary-1"].hp
        self.assertLess(damage_with, damage_without)
        self.assertTrue(any(evt.get("ability") == "Bulletproof" for evt in battle.log))

    def test_bully_trips_and_injures_on_super_effective_melee(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.abilities = [{"name": "Bully"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Karate Chop",
                type="Fighting",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.types = ["Normal"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            grid=GridState(width=4, height=4),
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Karate Chop", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state = battle.pokemon["gary-1"]
        self.assertTrue(defender_state.has_status("Tripped"))
        self.assertEqual(defender_state.injuries, 1)
        self.assertTrue(any(evt.get("ability") == "Bully" for evt in battle.log))

    def test_cave_crasher_resists_ground_attacks(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Diglett")
        attacker_spec.moves = [
            MoveSpec(
                name="Mud Slap",
                type="Ground",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Geodude")
        defender_spec.abilities = [{"name": "Cave Crasher"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Geodude"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mud Slap", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mud Slap", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - battle.pokemon["gary-1"].hp
        damage_without = baseline.pokemon["gary-1"].max_hp() - baseline.pokemon["gary-1"].hp
        self.assertLess(damage_with, damage_without)
        self.assertTrue(any(evt.get("ability") == "Cave Crasher" for evt in battle.log))

    def test_celebrate_boosts_speed_and_shifts_on_ko(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.abilities = [{"name": "Celebrate"}]
        attacker_spec.movement["overland"] = 4
        attacker_spec.moves = [
            MoveSpec(
                name="Power Strike",
                type="Normal",
                category="Physical",
                db=12,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(1, 0)
        )
        defender_state.hp = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            grid=GridState(width=4, height=4),
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Power Strike", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.combat_stages["spd"], 1)
        self.assertNotEqual(attacker_state.position, (0, 0))
        self.assertTrue(any(evt.get("ability") == "Celebrate" for evt in battle.log))

    def test_cherry_power_grants_temp_hp_and_cures(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Cherrim")
        attacker_spec.abilities = [{"name": "Cherry Power"}]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.statuses.append({"name": "Poisoned"})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Cherry Power", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertGreater(attacker_state.temp_hp, 0)
        self.assertFalse(attacker_state.has_status("Poisoned"))

    def test_healer_cures_adjacent_target_status_conditions(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Chansey")
        attacker_spec.abilities = [{"name": "Healer"}]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        ally_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=trainer.identifier, position=(1, 0)
        )
        ally_state.statuses.append({"name": "Poisoned"})
        ally_state.statuses.append({"name": "Burned"})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state, "ash-2": ally_state},
            grid=GridState(width=4, height=4),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Healer", target_id="ash-2"))
        battle.resolve_next_action()
        self.assertFalse(ally_state.statuses)
        healer_events = [evt for evt in battle.log if evt.get("effect") == "healer"]
        self.assertTrue(healer_events)
        cured = healer_events[-1].get("cured", [])
        self.assertEqual(set(cured), {"poisoned", "burned"})

    def test_pickpocket_grants_thief_move(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Sneasel")
        attacker_spec.abilities = [{"name": "Pickpocket"}]
        attacker_spec.moves = [
            move for move in attacker_spec.moves if (move.name or "").strip().lower() != "thief"
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        move_names = {str(move.name or "").strip().lower() for move in attacker_state.spec.moves}
        self.assertIn("thief", move_names)

    def test_heat_mirage_grants_evasion_after_fire_move(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmeleon")
        attacker_spec.abilities = [{"name": "Heat Mirage"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=4,
                ac=None,
                range_kind="Ranged",
                range_value=4,
                target_kind="Ranged",
                target_range=4,
                freq="At-Will",
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(2, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        effects = [
            entry
            for entry in attacker_state.get_temporary_effects("evasion_bonus")
            if entry.get("source") == "Heat Mirage"
        ]
        self.assertTrue(effects)
        self.assertEqual(int(effects[-1].get("amount", 0) or 0), 3)
        heat_events = [evt for evt in battle.log if evt.get("effect") == "heat_mirage"]
        self.assertTrue(heat_events)

    def test_heatproof_resists_fire_attacks(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Vulpix")
        attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=8,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Bronzor")
        defender_spec.abilities = [{"name": "Heatproof"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Bronzor"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertLess(damage_with, damage_without)
        self.assertTrue(any(evt.get("ability") == "Heatproof" for evt in battle.log))

    def test_heavy_metal_increases_weight_class(self) -> None:
        spec = _pokemon_spec("Onix")
        spec.abilities = [{"name": "Heavy Metal"}]
        spec.weight = 4
        state = PokemonState(spec=spec, controller_id="ash")
        self.assertEqual(state.weight_class(), 6)

    def test_helper_grants_accuracy_and_skill_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Audino")
        attacker_spec.abilities = [{"name": "Helper"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Support Test",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        ally_state = PokemonState(
            spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier, position=(1, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state, "ash-2": ally_state},
            grid=GridState(width=4, height=4),
        )
        battle.queue_action(
            UseMoveAction(actor_id="ash-1", move_name="Support Test", target_id="ash-2")
        )
        battle.resolve_next_action()
        accuracy_bonus = ally_state.get_temporary_effects("accuracy_bonus")
        skill_bonus = ally_state.get_temporary_effects("skill_bonus")
        self.assertTrue(any(entry.get("amount") == 1 for entry in accuracy_bonus))
        self.assertTrue(any(entry.get("amount") == 1 for entry in skill_bonus))

    def test_honey_paws_consumes_honey_for_leftovers_buff(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Teddiursa")
        spec.abilities = [{"name": "Honey Paws"}]
        spec.items = [{"name": "Honey"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.food_buffs = [{"name": "Digestion Buff", "effect": ""}]
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(len(state.food_buffs), 2)
        self.assertTrue(any(buff.get("item") == "Leftovers" for buff in state.food_buffs))
        self.assertTrue(any(evt.get("ability") == "Honey Paws" for evt in battle.log))

    def test_x_accuracy_csv_alias_applies_stage_boost(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Pikachu")
        spec.items = [{"name": "X Accuracy"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})

        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()

        self.assertEqual(state.combat_stages["accuracy"], 2)
        self.assertTrue(
            any(
                evt.get("type") == "combat_stage"
                and evt.get("effect") == "stage_change"
                and evt.get("stat") == "accuracy"
                for evt in battle.log
            )
        )

    def test_stat_vitamins_raise_correct_base_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        cases = [
            ("Protein", "atk"),
            ("Iron", "defense"),
            ("Calcium", "spatk"),
            ("Zinc", "spdef"),
            ("Carbos", "spd"),
            ("HP Up", "hp_stat"),
        ]
        tracked = ["hp_stat", "atk", "defense", "spatk", "spdef", "spd"]

        for item_name, expected_stat in cases:
            with self.subTest(item=item_name):
                spec = _pokemon_spec("Eevee")
                spec.items = [{"name": item_name}]
                state = PokemonState(spec=spec, controller_id=trainer.identifier)
                before = {stat: int(getattr(state.spec, stat)) for stat in tracked}
                battle = BattleState(
                    trainers={trainer.identifier: trainer},
                    pokemon={"ash-1": state},
                )
                battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
                battle.resolve_next_action()
                after = {stat: int(getattr(state.spec, stat)) for stat in tracked}

                self.assertEqual(after[expected_stat], before[expected_stat] + 1)
                for stat in tracked:
                    if stat == expected_stat:
                        continue
                    self.assertEqual(after[stat], before[stat])

    def test_stat_suppressants_lower_correct_base_stats(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        cases = [
            ("Attack Suppressant", "atk"),
            ("Defense Suppressant", "defense"),
            ("Special Attack Suppressant", "spatk"),
            ("Special Defense Suppressant", "spdef"),
            ("Speed Suppressant", "spd"),
            ("HP Suppressant", "hp_stat"),
        ]
        tracked = ["hp_stat", "atk", "defense", "spatk", "spdef", "spd"]

        for item_name, expected_stat in cases:
            with self.subTest(item=item_name):
                spec = _pokemon_spec("Umbreon")
                spec.items = [{"name": item_name}]
                # Keep stats above the floor to verify the decrement path.
                spec.hp_stat = 8
                spec.atk = 8
                spec.defense = 8
                spec.spatk = 8
                spec.spdef = 8
                spec.spd = 8
                state = PokemonState(spec=spec, controller_id=trainer.identifier)
                before = {stat: int(getattr(state.spec, stat)) for stat in tracked}
                battle = BattleState(
                    trainers={trainer.identifier: trainer},
                    pokemon={"ash-1": state},
                )
                battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
                battle.resolve_next_action()
                after = {stat: int(getattr(state.spec, stat)) for stat in tracked}

                self.assertEqual(after[expected_stat], before[expected_stat] - 1)
                for stat in tracked:
                    if stat == expected_stat:
                        continue
                    self.assertEqual(after[stat], before[stat])

    def test_pp_restore_items_adjust_frequency_usage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Pikachu")
        spec.moves = [
            MoveSpec(
                name="Scene Hit",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="Scene x2",
            ),
            MoveSpec(
                name="Daily Hit",
                type="Normal",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="Daily",
            ),
        ]
        spec.items = [{"name": "Ether"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.frequency_usage["ash-1"] = {"Scene Hit": 2, "Daily Hit": 1}

        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.frequency_usage.get("ash-1", {}).get("Daily Hit"), 1)
        self.assertEqual(battle.frequency_usage.get("ash-1", {}).get("Scene Hit"), 1)

        state.spec.items = [{"name": "Max Elixir"}]
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertNotIn("ash-1", battle.frequency_usage)
        self.assertTrue(
            any(evt.get("effect") in {"pp_restore", "pp_restore_all"} for evt in battle.log)
        )

    def test_status_seeds_and_pester_balls_apply_expected_statuses(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        cases = [
            ("Allure Seed", "Charmed"),
            ("Decoy Orb", "Marked", "foe"),
            ("Decoy Seed", "Marked", "foe"),
            ("Destiny Orb", "Destined", "foe"),
            ("Empowerment Seed", "Boosted", "foe"),
            ("Identify Orb", "True-Sight"),
            ("Invisify Orb", "Invisible"),
            ("Rebound Orb", "Rebound"),
            ("Sleep Seed", "Drowsy"),
            ("Stun Seed", "Paralyzed"),
            ("Shocker Orb", "Paralyzed"),
            ("Totter Seed", "Confused"),
            ("Silence Orb", "Gagged"),
            ("Pester Ball (Burn)", "Burned"),
            ("Pester Ball (Charmed)", "Charmed"),
            ("Pester Ball (Confused)", "Confused"),
            ("Pester Ball (Drowsy)", "Drowsy"),
            ("Pester Ball (Enraged)", "Enraged"),
            ("Pester Ball (Fear)", "Fear"),
            ("Pester Ball (Frostbite)", "Frostbite"),
            ("Pester Ball (Gagged)", "Gagged"),
            ("Pester Ball (Grounded)", "Grounded"),
            ("Pester Ball (Infested)", "Infested"),
            ("Pester Ball (Paralysis)", "Paralyzed"),
            ("Pester Ball (Poison)", "Poisoned"),
            ("Pester Ball (Powder)", "Powdered"),
            ("Pester Ball (Slow)", "Slowed"),
            ("Pester Ball (Stunted)", "Stunted"),
            ("Pester Ball (Suppressed)", "Suppressed"),
            ("Pester Ball (Taunted)", "Taunted"),
        ]

        for case in cases:
            if len(case) == 2:
                item_name, expected_status = case
                target_kind = "self"
            else:
                item_name, expected_status, target_kind = case
            with self.subTest(item=item_name):
                spec = _pokemon_spec("Eevee")
                spec.items = [{"name": item_name}]
                state = PokemonState(spec=spec, controller_id=trainer.identifier)
                if target_kind == "foe":
                    foe = TrainerState(identifier="gary", name="Gary")
                    foe_spec = _pokemon_spec("Pidgey")
                    foe_state = PokemonState(spec=foe_spec, controller_id=foe.identifier)
                    battle = BattleState(
                        trainers={trainer.identifier: trainer, foe.identifier: foe},
                        pokemon={"ash-1": state, "gary-1": foe_state},
                    )
                    target_id = "gary-1"
                    target_state = foe_state
                else:
                    battle = BattleState(
                        trainers={trainer.identifier: trainer},
                        pokemon={"ash-1": state},
                    )
                    target_id = "ash-1"
                    target_state = state
                battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id=target_id))
                battle.resolve_next_action()

                self.assertTrue(target_state.has_status(expected_status))
                self.assertTrue(
                    any(
                        evt.get("type") == "status"
                        and evt.get("effect") == "item_status"
                        and str(evt.get("status", "")).lower() == expected_status.lower()
                        for evt in battle.log
                    )
                )

    def test_decoy_orb_applies_marked_to_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Decoy Orb"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(target.has_status("Marked"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Decoy Orb status event: {event}")
        self.assertEqual(event.get("move"), "Decoy Orb")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Marked")
        self.assertEqual(event.get("remaining"), 5)

    def test_decoy_seed_applies_marked_to_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Decoy Seed"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(target.has_status("Marked"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Decoy Seed status event: {event}")
        self.assertEqual(event.get("move"), "Decoy Seed")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Marked")
        self.assertEqual(event.get("remaining"), 5)

    def test_destiny_orb_applies_destined_to_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Destiny Orb"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(target.has_status("Destined"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Destiny Orb status event: {event}")
        self.assertEqual(event.get("move"), "Destiny Orb")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Destined")
        self.assertEqual(event.get("remaining"), 5)

    def test_empowerment_seed_applies_boosted_to_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Empowerment Seed"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(target.has_status("Boosted"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Empowerment Seed status event: {event}")
        self.assertEqual(event.get("move"), "Empowerment Seed")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Boosted")
        self.assertEqual(event.get("remaining"), 3)

    def test_identify_orb_grants_true_sight(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Identify Orb"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(user.has_status("True-Sight"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Identify Orb status event: {event}")
        self.assertEqual(event.get("move"), "Identify Orb")
        self.assertEqual(event.get("target"), "ash-1")
        self.assertEqual(event.get("status"), "True-Sight")
        self.assertEqual(event.get("remaining"), 5)

    def test_invisify_orb_grants_invisible(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Invisify Orb"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(user.has_status("Invisible"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Invisify Orb status event: {event}")
        self.assertEqual(event.get("move"), "Invisify Orb")
        self.assertEqual(event.get("target"), "ash-1")
        self.assertEqual(event.get("status"), "Invisible")
        self.assertEqual(event.get("remaining"), 5)

    def test_rebound_orb_grants_rebound(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Rebound Orb"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(user.has_status("Rebound"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Rebound Orb status event: {event}")
        self.assertEqual(event.get("move"), "Rebound Orb")
        self.assertEqual(event.get("target"), "ash-1")
        self.assertEqual(event.get("status"), "Rebound")
        self.assertEqual(event.get("remaining"), 5)

    def test_active_camouflage_grants_invisible(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Active Camouflage"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(user.has_status("Invisible"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Active Camouflage status event: {event}")
        self.assertEqual(event.get("move"), "Active Camouflage")
        self.assertEqual(event.get("target"), "ash-1")
        self.assertEqual(event.get("status"), "Invisible")
        self.assertEqual(event.get("remaining"), 5)

    def test_rocky_orb_applies_splinter(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Rocky Orb"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(target.has_status("Splinter"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Rocky Orb status event: {event}")
        self.assertEqual(event.get("move"), "Rocky Orb")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Splinter")
        self.assertEqual(event.get("remaining"), 5)

    def test_vanish_seed_applies_invisible(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Vanish Seed"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(target.has_status("Invisible"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Vanish Seed status event: {event}")
        self.assertEqual(event.get("move"), "Vanish Seed")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Invisible")
        self.assertEqual(event.get("remaining"), 3)

    def test_vile_bait_applies_poisoned(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Vile Bait"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(target.has_status("Poisoned"))
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Vile Bait status event: {event}")
        self.assertEqual(event.get("move"), "Vile Bait")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Poisoned")
        self.assertIsNone(event.get("remaining"))

    def test_doom_seed_applies_perish_song(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Doom Seed"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        target = PokemonState(spec=target_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        perish_entries = target.get_temporary_effects("perish_song")
        self.assertTrue(perish_entries)
        self.assertEqual(perish_entries[0].get("count"), 3)
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "perish_song")
        print(f"Doom Seed perish event: {event}")
        self.assertEqual(event.get("item"), "Doom Seed")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("count"), 3)

    def test_lasso_orb_bounds_target_and_allies(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", team="player")
        foe = TrainerState(identifier="gary", name="Gary", team="foe")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Lasso Orb"}]
        foe_spec = _pokemon_spec("Pidgey")
        ally_spec = _pokemon_spec("Rattata")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        foe_target = PokemonState(spec=foe_spec, controller_id=foe.identifier)
        foe_ally = PokemonState(spec=ally_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": foe_target, "gary-2": foe_ally},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(foe_target.has_status("Bound"))
        self.assertTrue(foe_ally.has_status("Bound"))
        events = [
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        ]
        print(f"Lasso Orb status events: {events}")
        self.assertEqual(
            sum(1 for evt in events if evt.get("status") == "Bound" and evt.get("remaining") == 5),
            2,
        )

    def test_trapbust_orb_clears_hazards_and_traps(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Trapbust Orb"}]
        grid = GridState(
            width=2,
            height=1,
            tiles={
                (0, 0): {"hazards": {"spikes": 1}, "traps": {"pitfall": True}},
                (1, 0): {"hazards": {"toxic_spikes": 2}, "traps": {"web": True}},
            },
        )
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": user},
            grid=grid,
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        for tile in battle.grid.tiles.values():
            self.assertFalse(tile.get("hazards"))
            self.assertFalse(tile.get("traps"))
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "trapbust")
        print(f"Trapbust Orb event: {event}")
        self.assertEqual(event.get("item"), "Trapbust Orb")
        self.assertTrue(event.get("hazards_cleared"))
        self.assertTrue(event.get("traps_cleared"))

    def test_revive_all_orb_revives_allies(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", team="player")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Revive All Orb"}]
        ally_a_spec = _pokemon_spec("Pidgey")
        ally_b_spec = _pokemon_spec("Rattata")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        ally_a = PokemonState(spec=ally_a_spec, controller_id=trainer.identifier)
        ally_b = PokemonState(spec=ally_b_spec, controller_id=trainer.identifier)
        ally_a.hp = 0
        ally_b.hp = 0
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": user, "ash-2": ally_a, "ash-3": ally_b},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        expected_a = max(1, int(ally_a.max_hp() * 0.25))
        expected_b = max(1, int(ally_b.max_hp() * 0.25))
        self.assertEqual(ally_a.hp, expected_a)
        self.assertEqual(ally_b.hp, expected_b)
        events = [evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "revive_all"]
        print(f"Revive All Orb events: {events}")
        self.assertEqual(len(events), 2)

    def test_stayaway_orb_removes_target_from_combat(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Stayaway Orb"}]
        target_spec = _pokemon_spec("Pidgey")
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier, position=(0, 0))
        target = PokemonState(spec=target_spec, controller_id=foe.identifier, position=(1, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
            grid=GridState(width=3, height=1),
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(target.active)
        self.assertIsNone(target.position)
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "stayaway")
        print(f"Stayaway Orb event: {event}")
        self.assertEqual(event.get("item"), "Stayaway Orb")
        self.assertEqual(event.get("target"), "gary-1")

    def test_spurn_orb_removes_all_foes(self) -> None:
        player = TrainerState(identifier="ash", name="Ash", team="player")
        foe = TrainerState(identifier="gary", name="Gary", team="foe")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Spurn Orb"}]
        user = PokemonState(spec=user_spec, controller_id=player.identifier, position=(0, 0))
        foe_a = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(1, 0))
        foe_b = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(2, 0))
        ally = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=player.identifier, position=(0, 1))
        battle = BattleState(
            trainers={player.identifier: player, foe.identifier: foe},
            pokemon={"ash-1": user, "ash-2": ally, "gary-1": foe_a, "gary-2": foe_b},
            grid=GridState(width=3, height=2),
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(foe_a.active)
        self.assertFalse(foe_b.active)
        self.assertTrue(ally.active)
        events = [evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "spurn"]
        print(f"Spurn Orb events: {events}")
        self.assertEqual(len(events), 2)

    def test_placeholder_item_non_combat_dash(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "--"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Non-combat '--' event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "--")

    def test_field_guide_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "A Field Guide to Fungi [5-15 Playtest]"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Field Guide placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "A Field Guide to Fungi [5-15 Playtest]")

    def test_ability_urge_sets_ready_effect(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Ability Urge"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        effects = user.get_temporary_effects("ability_urge")
        self.assertTrue(effects)
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "ability_urge")
        print(f"Ability Urge event: {event}")
        self.assertEqual(event.get("item"), "Ability Urge")
        self.assertEqual(event.get("remaining"), 1)

    def test_accessory_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Accessory"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Accessory placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Accessory")

    def test_acidic_rock_grants_weather_bonus_effect(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Acidic Rock"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        effects = user.get_temporary_effects("weather_duration_bonus")
        self.assertTrue(effects)
        event = next(
            evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "weather_duration_bonus"
        )
        print(f"Acidic Rock event: {event}")
        self.assertEqual(event.get("item"), "Acidic Rock")
        self.assertEqual(event.get("weather"), "Smoggy")
        self.assertEqual(event.get("bonus"), 3)

    def test_air_ball_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Air Ball"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Air Ball placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Air Ball")

    def test_alkaline_clay_grants_weather_immunity(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Alkaline Clay"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        events = battle.item_system.apply_held_item_start("ash-1")
        print(f"Alkaline Clay held events: {events}")
        immunities = user.get_temporary_effects("weather_immunity")
        weathers = {entry.get("weather") for entry in immunities if isinstance(entry, dict)}
        self.assertTrue({"smoggy", "acid rain"}.issubset(weathers))
        self.assertTrue(any(evt.get("item") == "Alkaline Clay" for evt in events))

    def test_basic_ball_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Basic Ball"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Basic Ball placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Basic Ball")

    def test_basic_digivice_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Basic Digivice"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Basic Digivice placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Basic Digivice")

    def test_bat_aluminium_can_be_equipped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Bat (Aluminium)", "tags": ["weapon", "melee"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Bat (Aluminium) equip event: {event}")
        self.assertEqual(event.get("item"), "Bat (Aluminium)")

    def test_bat_wood_can_be_equipped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Bat (Wood)", "tags": ["weapon", "melee"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Bat (Wood) equip event: {event}")
        self.assertEqual(event.get("item"), "Bat (Wood)")

    def test_battle_rifle_can_be_equipped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Battle Rifle", "tags": ["weapon", "ranged"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Battle Rifle equip event: {event}")
        self.assertEqual(event.get("item"), "Battle Rifle")

    def test_bayonet_can_be_equipped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Bayonet", "tags": ["weapon", "melee"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Bayonet equip event: {event}")
        self.assertEqual(event.get("item"), "Bayonet")

    def test_beacon_ball_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Beacon Ball"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Beacon Ball placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Beacon Ball")

    def test_beam_drive_sets_psychic_type(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Beam Drive"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        resolved_type = battle._item_type_from_item({"name": "Beam Drive"})
        print(f"Beam Drive type mapping: {resolved_type}")
        self.assertEqual(resolved_type, "Psychic")

    def test_beartic_mace_applies_blinded(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Beartic Mace", "tags": ["weapon", "melee"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Beartic Mace equip event: {event}")
        self.assertEqual(event.get("item"), "Beartic Mace")

    def test_beast_ball_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Beast Ball"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Beast Ball placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Beast Ball")

    def test_beauty_fashion_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Beauty Fashion"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Beauty Fashion placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Beauty Fashion")

    def test_beauty_poffin_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Beauty Poffin"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Beauty Poffin placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Beauty Poffin")

    def test_black_apricorn_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Black Apricorn"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Black Apricorn placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Black Apricorn")

    def test_black_augurite_splinters_on_contact(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.items = [{"name": "Black Augurite"}]
        defender_spec = _pokemon_spec("Pidgey")
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        move = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=4,
            ac=None,
            keywords=["Contact", "Sharp"],
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([1]),
        )
        events = battle.item_system.apply_attacker_item_post_damage(
            attacker_id="ash-1",
            attacker=attacker,
            target_id="gary-1",
            target=defender,
            move=move,
            damage_dealt=10,
            result={},
        )
        print(f"Black Augurite events: {events}")
        self.assertTrue(defender.has_status("Splinter"))
        status_event = next(evt for evt in events if evt.get("type") == "status")
        self.assertEqual(status_event.get("status"), "Splinter")
        self.assertEqual(status_event.get("move"), "Black Augurite")

    def test_blank_tm_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Blank TM"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Blank TM placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Blank TM")

    def test_blast_seed_fling_event(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Blast Seed"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        foe_spec = _pokemon_spec("Pidgey")
        foe_mon = PokemonState(spec=foe_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": foe_mon},
        )
        before_hp = foe_mon.hp
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Blast Seed item event: {event}")
        self.assertEqual(event.get("effect"), "blast_seed_fling")
        self.assertEqual(event.get("move_type"), "Fire")
        self.assertEqual(event.get("power"), 35)
        self.assertEqual(event.get("area"), "cone")
        self.assertIsNotNone(before_hp)
        self.assertLess(foe_mon.hp, before_hp)
        self.assertEqual(event.get("damage"), 35)

    def test_blast_seed_hits_cone_targets_on_grid(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Blast Seed"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier, position=(1, 1), active=True)
        front = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(1, 2), active=True)
        flank = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 2), active=True)
        rear = PokemonState(spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(2, 3), active=True)
        outsider = PokemonState(spec=_pokemon_spec("Zubat"), controller_id=foe.identifier, position=(4, 4), active=True)
        grid = GridState(width=5, height=5)
        front_before = front.hp
        flank_before = flank.hp
        rear_before = rear.hp
        outsider_before = outsider.hp
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": user,
                "gary-1": front,
                "gary-2": flank,
                "gary-3": rear,
                "gary-4": outsider,
            },
            grid=grid,
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        blast_events = [evt for evt in battle.log if evt.get("effect") == "blast_seed_fling"]
        hit_ids = sorted(evt.get("target") for evt in blast_events)
        self.assertEqual(hit_ids, ["gary-1", "gary-2", "gary-3"])
        self.assertEqual(front.hp, max(0, (front_before or 0) - 35))
        self.assertEqual(flank.hp, max(0, (flank_before or 0) - 35))
        self.assertEqual(rear.hp, max(0, (rear_before or 0) - 35))
        self.assertEqual(outsider.hp, outsider_before)

    def test_blastoisinite_triggers_mega_evolution(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Blastoise")
        user_spec.items = [{"name": "Blastoisinite"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(user.get_temporary_effects("mega_form"))
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "mega_evolution")
        print(f"Blastoisinite mega event: {event}")
        self.assertEqual(event.get("mega_form"), "Mega Blastoise")

    def test_blazikenite_triggers_mega_evolution(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Blaziken")
        user_spec.items = [{"name": "Blazikenite"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(user.get_temporary_effects("mega_form"))
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "mega_evolution")
        print(f"Blazikenite mega event: {event}")
        self.assertEqual(event.get("mega_form"), "Mega Blaziken")

    def test_blowback_orb_logs_whirlwind(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Blowback Orb"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        foe_spec = _pokemon_spec("Pidgey")
        foe_mon = PokemonState(spec=foe_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": foe_mon},
        )
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Blowback Orb item event: {event}")
        self.assertEqual(event.get("effect"), "blowback_orb")
        self.assertEqual(event.get("move"), "Whirlwind")

    def test_blue_apricorn_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Blue Apricorn"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Blue Apricorn placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Blue Apricorn")

    def test_blue_orb_primal_ready_for_kyogre(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Kyogre")
        user_spec.items = [{"name": "Blue Orb"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        events = battle.item_system.apply_held_item_start("ash-1")
        print(f"Blue Orb held events: {events}")
        self.assertTrue(user.get_temporary_effects("primal_reversion_ready"))
        event = next(evt for evt in events if evt.get("effect") == "primal_reversion_ready")
        self.assertEqual(event.get("item"), "Blue Orb")

    def test_blue_shard_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Blue Shard"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Blue Shard placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Blue Shard")

    def test_body_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Body"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Body placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Body")

    def test_body_plus_head_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Body + Head"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Body + Head placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Body + Head")

    def test_boggy_clay_grants_weather_immunity(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Boggy Clay"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        events = battle.item_system.apply_held_item_start("ash-1")
        print(f"Boggy Clay held events: {events}")
        immunities = user.get_temporary_effects("weather_immunity")
        weathers = {entry.get("weather") for entry in immunities if isinstance(entry, dict)}
        self.assertTrue({"foggy", "intense fog"}.issubset(weathers))
        self.assertTrue(any(evt.get("item") == "Boggy Clay" for evt in events))

    def test_bolt_action_rifle_can_be_equipped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Bolt-Action Rifle", "tags": ["weapon", "ranged"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Bolt-Action Rifle equip event: {event}")
        self.assertEqual(event.get("item"), "Bolt-Action Rifle")

    def test_bounce_case_non_combat_placeholder(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Bounce Case"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item")
        print(f"Bounce Case placeholder event: {event}")
        self.assertEqual(event.get("effect"), "non_combat_placeholder")
        self.assertEqual(event.get("item"), "Bounce Case")

    def test_bow_can_be_equipped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Bow", "tags": ["weapon", "ranged"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Bow equip event: {event}")
        self.assertEqual(event.get("item"), "Bow")

    def test_break_action_shotgun_can_be_equipped(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Break-Action Shotgun", "tags": ["weapon", "ranged"]}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
        battle.resolve_next_action()
        event = next(evt for evt in battle.log if evt.get("type") == "item" and evt.get("effect") == "equip_weapon")
        print(f"Break-Action Shotgun equip event: {event}")
        self.assertEqual(event.get("item"), "Break-Action Shotgun")

    def test_breastplate_grants_speed_scalar(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Breastplate"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        events = battle.item_system.apply_held_item_start("ash-1")
        print(f"Breastplate held events: {events}")
        effects = user.get_temporary_effects("stat_scalar")
        self.assertTrue(any(entry.get("stat") == "spd" and entry.get("multiplier") == 0.85 for entry in effects))
        speed_event = next(evt for evt in events if evt.get("item") == "Breastplate" and evt.get("effect") == "armor_speed_scalar")
        self.assertEqual(speed_event.get("multiplier"), 0.85)
        res_event = next(evt for evt in events if evt.get("item") == "Breastplate" and evt.get("effect") == "resistance_bonus")
        self.assertEqual(res_event.get("amount"), 5)
        self.assertEqual(user.save_bonus(battle), 5)

    def test_buckler_shield_grants_parry(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Buckler Shield"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        events = battle.item_system.apply_held_item_start("ash-1")
        print(f"Buckler Shield held events: {events}")
        effects = user.get_temporary_effects("ability_granted")
        self.assertTrue(any(entry.get("ability") == "Parry" for entry in effects))
        event = next(evt for evt in events if evt.get("effect") == "grant_ability")
        self.assertEqual(event.get("ability"), "Parry")
        self.assertEqual(event.get("item"), "Buckler Shield")

    def test_buff_coat_grants_speed_scalar(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Buff Coat"}]
        user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
        events = battle.item_system.apply_held_item_start("ash-1")
        print(f"Buff Coat held events: {events}")
        effects = user.get_temporary_effects("stat_scalar")
        self.assertTrue(any(entry.get("stat") == "spd" and entry.get("multiplier") == 0.9 for entry in effects))
        speed_event = next(evt for evt in events if evt.get("item") == "Buff Coat" and evt.get("effect") == "armor_speed_scalar")
        self.assertEqual(speed_event.get("multiplier"), 0.9)
        res_event = next(evt for evt in events if evt.get("item") == "Buff Coat" and evt.get("effect") == "resistance_bonus")
        self.assertEqual(res_event.get("amount"), 10)
        self.assertEqual(user.save_bonus(battle), 10)

    def test_breastplate_reduces_missile_sharp_physical_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.items = [{"name": "Breastplate"}]
        attacker_spec = _pokemon_spec("Pidgey")
        move = MoveSpec(
            name="Arrow Shot",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            keywords=["Missile", "Sharp"],
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
            },
        )
        defender = battle.pokemon["ash-1"]
        attacker = battle.pokemon["gary-1"]
        result = {"damage": 100, "type_multiplier": 1.0}
        ctx = ItemHookContext(
            battle=battle,
            events=[],
            holder_id="ash-1",
            holder=defender,
            attacker_id="gary-1",
            attacker=attacker,
            move=move,
            result=result,
            phase="defender_mitigation",
        )
        battle.hook_dispatcher.apply_item_hooks("defender_mitigation", ctx)
        print(f"Breastplate mitigation events: {ctx.events}")
        self.assertEqual(result.get("damage"), 72)

    def test_buff_coat_increases_firearm_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.items = [{"name": "Buff Coat"}]
        attacker_spec = _pokemon_spec("Pidgey")
        move = MoveSpec(
            name="Gun Shot",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            keywords=["Firearm"],
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier),
            },
        )
        defender = battle.pokemon["ash-1"]
        attacker = battle.pokemon["gary-1"]
        result = {"damage": 100, "type_multiplier": 1.0}
        ctx = ItemHookContext(
            battle=battle,
            events=[],
            holder_id="ash-1",
            holder=defender,
            attacker_id="gary-1",
            attacker=attacker,
            move=move,
            result=result,
            phase="defender_mitigation",
        )
        battle.hook_dispatcher.apply_item_hooks("defender_mitigation", ctx)
        print(f"Buff Coat mitigation events: {ctx.events}")
        self.assertEqual(result.get("damage"), 103)

    def test_binding_band_inflicts_bleed_on_bound_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.items = [{"name": "Binding Band"}]
        attacker_spec.moves = [MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=None)]
        defender_spec = _pokemon_spec("Pidgey")
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        defender.statuses.append({"name": "Bound", "remaining": 5})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([20]),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender.has_status("Bleed"))
        bleed_status = next(
            entry
            for entry in defender.statuses
            if str(entry.get("name") if isinstance(entry, dict) else entry).strip().lower() == "bleed"
        )
        self.assertEqual(bleed_status.get("source"), "Binding Band")
        self.assertEqual(bleed_status.get("source_id"), "ash-1")
        event = next(
            evt
            for evt in battle.log
            if evt.get("type") == "status" and evt.get("effect") == "item_status"
        )
        print(f"Binding Band status event: {event}")
        self.assertEqual(event.get("move"), "Binding Band")
        self.assertEqual(event.get("target"), "gary-1")
        self.assertEqual(event.get("status"), "Bleed")
        self.assertEqual(event.get("remaining"), 3)
        self.assertEqual(event.get("source"), "Binding Band")
        bleed_events = defender.handle_phase_effects(battle, TurnPhase.START, "gary-1")
        bleed_tick = next(evt for evt in bleed_events if evt.get("effect") == "bleed")
        self.assertEqual(bleed_tick.get("source"), "Binding Band")
        self.assertIn("Binding Band", str(bleed_tick.get("description") or ""))

    def test_large_footprint_blocks_shift_destinations(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        actor = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier, position=(0, 0), active=True)
        large_foe = PokemonState(spec=_pokemon_spec("Steelix", size="Large"), controller_id=foe.identifier, position=(2, 1), active=True)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": actor, "gary-1": large_foe},
            grid=GridState(width=6, height=6),
        )

        with self.assertRaises(ValueError):
            ShiftAction(actor_id="ash-1", destination=(2, 2)).validate(battle)

    def test_melee_move_can_target_huge_footprint_when_adjacent_to_edge(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=None, range_kind="Melee", target_kind="Melee", target_range=1)]
        defender_spec = _pokemon_spec("Wailord", size="Huge")
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 2), active=True)
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(2, 2), active=True)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            grid=GridState(width=8, height=8),
        )

        UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1").validate(battle)

    def test_burst_area_hits_large_target_when_any_footprint_tile_overlaps(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Shock Burst",
                type="Electric",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
                area_kind="Burst",
                area_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Steelix", size="Large")
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 1), active=True)
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(2, 1), active=True)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            grid=GridState(width=8, height=8),
        )

        battle.resolve_move_targets(attacker_id="ash-1", move=attacker_spec.moves[0], target_id="gary-1", target_position=(1, 1))
        self.assertTrue(any(evt.get("target") == "gary-1" and evt.get("move") == "Shock Burst" for evt in battle.log))

    def test_large_footprint_cannot_fit_if_any_tile_would_leave_grid(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        actor = PokemonState(
            spec=_pokemon_spec("Steelix", size="Large"),
            controller_id=trainer.identifier,
            position=(0, 0),
            active=True,
        )
        opponent = PokemonState(
            spec=_pokemon_spec("Pikachu"),
            controller_id=foe.identifier,
            position=(4, 4),
            active=True,
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": actor, "gary-1": opponent},
            grid=GridState(width=6, height=6),
        )

        self.assertFalse(battle._position_can_fit("ash-1", (5, 5)))
        self.assertFalse(battle._position_can_fit("ash-1", (5, 4)))
        self.assertFalse(battle._position_can_fit("ash-1", (4, 5)))
        self.assertTrue(battle._position_can_fit("ash-1", (4, 4), exclude_id="gary-1"))

    def test_room_orbs_apply_status_to_all_active_foes(self) -> None:
        player = TrainerState(identifier="ash", name="Ash", team="player")
        foe = TrainerState(identifier="gary", name="Gary", team="foe")
        cases = [
            ("Foe-Fear Orb", "Fear"),
            ("Foe-Hold Orb", "Trapped"),
            ("Foe-Seal Orb", "Disabled"),
            ("Nullify Orb", "Nullified"),
            ("Slumber Orb", "Drowsy"),
            ("Slow Orb", "Slowed"),
            ("Terror Orb", "Bad Sleep"),
            ("Totter Orb", "Confused"),
        ]

        for item_name, expected_status in cases:
            with self.subTest(item=item_name):
                user_spec = _pokemon_spec("Eevee")
                user_spec.items = [{"name": item_name}]
                user = PokemonState(spec=user_spec, controller_id=player.identifier)
                foe_a_spec = _pokemon_spec("Pidgey")
                foe_b_spec = _pokemon_spec("Rattata")
                if item_name == "Nullify Orb":
                    foe_a_spec.abilities = [{"name": "Run Away"}]
                    foe_b_spec.abilities = [{"name": "Run Away"}]
                else:
                    foe_a_spec.abilities = [{"name": "Keen Eye"}]
                    foe_b_spec.abilities = [{"name": "Keen Eye"}]
                foe_a = PokemonState(spec=foe_a_spec, controller_id=foe.identifier)
                foe_b = PokemonState(spec=foe_b_spec, controller_id=foe.identifier)
                battle = BattleState(
                    trainers={player.identifier: player, foe.identifier: foe},
                    pokemon={"ash-1": user, "gary-1": foe_a, "gary-2": foe_b},
                )

                battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
                battle.resolve_next_action()

                self.assertTrue(foe_a.has_status(expected_status))
                self.assertTrue(foe_b.has_status(expected_status))
                status_events = [
                    evt
                    for evt in battle.log
                    if evt.get("type") == "status" and evt.get("effect") == "item_status"
                ]
                self.assertGreaterEqual(
                    sum(1 for evt in status_events if str(evt.get("status", "")).lower() == expected_status.lower()),
                    2,
                )
                if item_name == "Foe-Seal Orb":
                    disabled_a = [
                        entry
                        for entry in foe_a.statuses
                        if isinstance(entry, dict) and str(entry.get("name", "")).strip().lower() == "disabled"
                    ]
                    disabled_b = [
                        entry
                        for entry in foe_b.statuses
                        if isinstance(entry, dict) and str(entry.get("name", "")).strip().lower() == "disabled"
                    ]
                    self.assertTrue(disabled_a and disabled_a[0].get("move"))
                    self.assertTrue(disabled_b and disabled_b[0].get("move"))
                if item_name == "Nullify Orb":
                    self.assertTrue(foe_a.get_temporary_effects("ability_disabled"))
                    self.assertTrue(foe_b.get_temporary_effects("ability_disabled"))

    def test_ban_seed_disables_move_and_prevents_use(self) -> None:
        player = TrainerState(identifier="ash", name="Ash", team="player")
        foe = TrainerState(identifier="gary", name="Gary", team="foe")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Ban Seed"}]
        foe_spec = _pokemon_spec("Pikachu")
        foe_spec.moves = [
            MoveSpec(
                name="Thunder Shock",
                type="Electric",
                category="Special",
                db=4,
                ac=None,
                range_kind="Ranged",
                range_value=4,
            ),
            MoveSpec(
                name="Quick Attack",
                type="Normal",
                category="Physical",
                db=4,
                ac=None,
                range_kind="Melee",
                range_value=1,
            ),
        ]
        user = PokemonState(spec=user_spec, controller_id=player.identifier)
        target = PokemonState(spec=foe_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={player.identifier: player, foe.identifier: foe},
            pokemon={"ash-1": user, "gary-1": target},
        )

        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
        battle.resolve_next_action()

        disabled_entries = [
            entry
            for entry in target.statuses
            if isinstance(entry, dict) and str(entry.get("name", "")).strip().lower() == "disabled"
        ]
        self.assertTrue(disabled_entries)
        disabled_move = str(disabled_entries[0].get("move") or "").strip()
        self.assertTrue(disabled_move)

        with self.assertRaises(ValueError):
            battle.queue_action(UseMoveAction(actor_id="gary-1", move_name=disabled_move, target_id="ash-1"))
            battle.resolve_next_action()

    def test_reviver_orb_fully_revives_fainted_target(self) -> None:
        player = TrainerState(identifier="ash", name="Ash", team="player")
        ally = TrainerState(identifier="misty", name="Misty", team="player")
        user_spec = _pokemon_spec("Eevee")
        user_spec.items = [{"name": "Reviver Orb"}]
        user = PokemonState(spec=user_spec, controller_id=player.identifier)
        fainted_spec = _pokemon_spec("Psyduck")
        fainted = PokemonState(spec=fainted_spec, controller_id=ally.identifier)
        fainted.hp = 0
        battle = BattleState(
            trainers={player.identifier: player, ally.identifier: ally},
            pokemon={"ash-1": user, "misty-1": fainted},
        )

        battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="misty-1"))
        battle.resolve_next_action()

        self.assertEqual(fainted.hp, fainted.max_hp())
        self.assertTrue(
            any(
                evt.get("type") == "item"
                and evt.get("item") == "Reviver Orb"
                and evt.get("effect") == "revive"
                for evt in battle.log
            )
        )

    def test_honey_thief_grants_temp_hp_on_bug_bite(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Ribombee")
        attacker_spec.abilities = [{"name": "Honey Thief"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Bug Bite",
                type="Bug",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_state = PokemonState(
            spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(0, 1)
        )
        defender_state.food_buffs.append({"name": "Digestion Buff", "effect": ""})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_state,
            },
            rng=MaxRNG(),
        )
        attacker_state = battle.pokemon["ash-1"]
        temp_before = attacker_state.temp_hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bug Bite", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.temp_hp, temp_before + attacker_state.tick_value())
        self.assertTrue(any(evt.get("ability") == "Honey Thief" for evt in battle.log))

    def test_huge_power_doubles_attack_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        defender_spec = _pokemon_spec("Eevee")
        attacker_with_spec = _pokemon_spec("Azumarill")
        attacker_with = PokemonState(spec=attacker_with_spec, controller_id="ash")
        attacker_with.spec.abilities = [{"name": "Huge Power"}]
        defender_with = PokemonState(spec=defender_spec, controller_id="gary")
        result_with = resolve_move_action(MaxRNG(), attacker_with, defender_with, move)

        attacker_without = PokemonState(spec=_pokemon_spec("Azumarill"), controller_id="ash")
        defender_without = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        result_without = resolve_move_action(MaxRNG(), attacker_without, defender_without, move)
        self.assertGreater(result_with["damage"], result_without["damage"])

    def test_pure_power_doubles_attack_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        defender_spec = _pokemon_spec("Eevee")
        attacker_with_spec = _pokemon_spec("Medicham")
        attacker_with = PokemonState(spec=attacker_with_spec, controller_id="ash")
        attacker_with.spec.abilities = [{"name": "Pure Power"}]
        defender_with = PokemonState(spec=defender_spec, controller_id="gary")
        result_with = resolve_move_action(MaxRNG(), attacker_with, defender_with, move)

        attacker_without = PokemonState(spec=_pokemon_spec("Medicham"), controller_id="ash")
        defender_without = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        result_without = resolve_move_action(MaxRNG(), attacker_without, defender_without, move)
        self.assertGreater(result_with["damage"], result_without["damage"])

    def test_rivalry_boosts_damage_against_same_gender(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        attacker_spec = _pokemon_spec("Nidoran")
        attacker_spec.gender = "Male"
        attacker_with = PokemonState(spec=attacker_spec, controller_id="ash")
        attacker_with.spec.abilities = [{"name": "Rivalry"}]
        defender_same_spec = _pokemon_spec("Rattata")
        defender_same_spec.gender = "Male"
        defender_same = PokemonState(spec=defender_same_spec, controller_id="gary")
        result_same = resolve_move_action(MaxRNG(), attacker_with, defender_same, move)

        attacker_without = PokemonState(spec=_pokemon_spec("Nidoran"), controller_id="ash")
        attacker_without.spec.gender = "Male"
        defender_no = PokemonState(spec=defender_same_spec, controller_id="gary")
        result_no = resolve_move_action(MaxRNG(), attacker_without, defender_no, move)
        self.assertGreaterEqual(result_same["damage"], result_no["damage"] + 5)

        defender_diff_spec = _pokemon_spec("Rattata")
        defender_diff_spec.gender = "Female"
        defender_diff = PokemonState(spec=defender_diff_spec, controller_id="gary")
        result_diff = resolve_move_action(MaxRNG(), attacker_with, defender_diff, move)
        self.assertEqual(result_diff["damage"], result_no["damage"])

    def test_quick_feet_boosts_speed_and_ignores_paralysis(self) -> None:
        spec = _pokemon_spec("Linoone")
        spec.abilities = [{"name": "Quick Feet"}]
        mon = PokemonState(spec=spec, controller_id="ash")
        base_speed = speed_stat(mon)
        mon.statuses.append({"name": "Paralyzed"})
        boosted_speed = speed_stat(mon)
        self.assertGreater(boosted_speed, base_speed)
        mon.statuses = []
        mon.statuses.append({"name": "Paralyzed"})
        mon_no_ability = PokemonState(spec=_pokemon_spec("Linoone"), controller_id="ash")
        mon_no_ability.statuses.append({"name": "Paralyzed"})
        self.assertGreater(boosted_speed, speed_stat(mon_no_ability))

    def test_hustle_penalizes_physical_accuracy(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 2

        move = MoveSpec(
            name="Scratch",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        attacker_with = PokemonState(spec=_pokemon_spec("Bagon"), controller_id="ash")
        attacker_with.spec.abilities = [{"name": "Hustle"}]
        defender_spec = _pokemon_spec("Eevee")
        defender_spec.defense = 1
        defender = PokemonState(spec=defender_spec, controller_id="gary")
        result_with = resolve_move_action(FixedRNG(), attacker_with, defender, move)

        attacker_without = PokemonState(spec=_pokemon_spec("Bagon"), controller_id="ash")
        defender_without = PokemonState(spec=defender_spec, controller_id="gary")
        result_without = resolve_move_action(FixedRNG(), attacker_without, defender_without, move)
        self.assertFalse(result_with["hit"])
        self.assertTrue(result_without["hit"])

    def test_hustle_boosts_physical_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        defender_spec = _pokemon_spec("Eevee")
        attacker_with = PokemonState(spec=_pokemon_spec("Tauros"), controller_id="ash")
        attacker_with.spec.abilities = [{"name": "Hustle"}]
        defender_with = PokemonState(spec=defender_spec, controller_id="gary")
        result_with = resolve_move_action(MaxRNG(), attacker_with, defender_with, move)

        attacker_without = PokemonState(spec=_pokemon_spec("Tauros"), controller_id="ash")
        defender_without = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        result_without = resolve_move_action(MaxRNG(), attacker_without, defender_without, move)
        self.assertGreater(result_with["damage"], result_without["damage"])

    def test_hydration_cures_status_in_rain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Vaporeon")
        spec.abilities = [{"name": "Hydration"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.statuses.append({"name": "Burned"})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.weather = "Rain"
        events = state.handle_phase_effects(battle, TurnPhase.END, "ash-1")
        self.assertFalse(state.has_status("Burned"))
        self.assertTrue(any(evt.get("ability") == "Hydration" for evt in events))

    def test_hyper_cutter_blocks_attack_drop(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Krabby")
        defender_spec.abilities = [{"name": "Hyper Cutter"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Growl", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            stat="atk",
            delta=-1,
            description="Growl lowers Attack.",
        )
        self.assertEqual(defender_state.combat_stages["atk"], 0)
        self.assertTrue(any(evt.get("ability") == "Hyper Cutter" for evt in events))

    def test_hypnotic_makes_hypnosis_hit(self) -> None:
        class LowRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 1

        move = MoveSpec(
            name="Hypnosis",
            type="Psychic",
            category="Status",
            db=0,
            ac=8,
            range_kind="Ranged",
            range_value=6,
        )
        attacker_with = PokemonState(spec=_pokemon_spec("Hypno"), controller_id="ash")
        attacker_with.spec.abilities = [{"name": "Hypnotic"}]
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        result_with = resolve_move_action(LowRNG(), attacker_with, defender, move)

        attacker_without = PokemonState(spec=_pokemon_spec("Hypno"), controller_id="ash")
        defender_without = PokemonState(spec=_pokemon_spec("Eevee"), controller_id="gary")
        result_without = resolve_move_action(LowRNG(), attacker_without, defender_without, move)
        self.assertTrue(result_with["hit"])
        self.assertFalse(result_without["hit"])

    def test_clay_cannons_origin_shift(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Claydol")
        attacker_spec.abilities = [{"name": "Clay Cannons"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Shock Pulse",
                type="Electric",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=2,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(2, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            grid=GridState(width=5, height=5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Clay Cannons", target_id="ash-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shock Pulse", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Clay Cannons" for evt in battle.log))

    def test_dimensional_rifts_origin_shift(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Hoopa")
        attacker_spec.abilities = [{"name": "Dimensional Rift"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Psybeam",
                type="Psychic",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=4,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(8, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            grid=GridState(width=12, height=12),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Psybeam", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(
            any(
                evt.get("ability") == "Dimensional Rifts"
                and evt.get("effect") == "origin_shift"
                for evt in battle.log
            )
        )

    def test_hyperspace_hole_creates_dimensional_rift(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Hoopa")
        attacker_spec.abilities = [{"name": "Dimensional Rift"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Hyperspace Hole",
                type="Psychic",
                category="Special",
                db=8,
                ac=4,
                range_kind="Ranged",
                range_value=8,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(4, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            grid=GridState(width=8, height=8),
        )
        battle.queue_action(
            UseMoveAction(
                actor_id="ash-1",
                move_name="Hyperspace Hole",
                target_id="gary-1",
                allow_reaction_declared=True,
            )
        )
        battle.resolve_next_action()
        rifts = attacker_state.get_temporary_effects("dimensional_rift")
        self.assertTrue(rifts)
        self.assertEqual(tuple(rifts[0].get("origin") or ()), defender_state.position)

    def test_clear_body_blocks_stage_drops(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Beldum")
        defender_spec.abilities = [{"name": "Clear Body"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Tail Whip", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            stat="def",
            delta=-1,
            description="Tail Whip lowers Defense.",
        )
        self.assertEqual(defender_state.combat_stages["def"], 0)
        self.assertTrue(any(evt.get("ability") == "Clear Body" for evt in events))

    def test_cloud_nine_clears_weather(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Golduck")
        user_spec.abilities = [{"name": "Cloud Nine"}]
        user_state = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": user_state},
            weather="Rain",
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Cloud Nine", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.weather, "Clear")

    def test_stamina_raises_defense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Mudsdale")
        user_spec.abilities = [{"name": "Stamina"}]
        user_state = PokemonState(spec=user_spec, controller_id=trainer.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": user_state},
        )
        self.assertEqual(user_state.combat_stages.get("def"), 0)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Stamina", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(user_state.combat_stages.get("def"), 1)

    def test_cluster_mind_adds_move_pool_bonus(self) -> None:
        spec = _pokemon_spec("Alakazam")
        spec.abilities = [{"name": "Cluster Mind"}]
        state = PokemonState(spec=spec, controller_id="ash")
        bonuses = state.get_temporary_effects("move_pool_bonus")
        self.assertTrue(bonuses)
        self.assertEqual(bonuses[0].get("amount"), 2)

    def test_color_change_shifts_type_on_hit(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Vulpix")
        attacker_spec.moves = [
            MoveSpec(
                name="Flame Burst",
                type="Fire",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Kecleon")
        defender_spec.abilities = [{"name": "Color Change"}]
        defender_spec.types = ["Normal"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=random.Random(5),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Flame Burst", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].spec.types, ["Fire"])
        self.assertTrue(any(evt.get("ability") == "Color Change" for evt in battle.log))

    def test_color_theory_sets_color_effect(self) -> None:
        spec = _pokemon_spec("Kecleon")
        spec.abilities = [{"name": "Color Theory"}]
        state = PokemonState(spec=spec, controller_id="ash")
        effects = state.get_temporary_effects("color_theory")
        self.assertTrue(effects)
        self.assertTrue(effects[0].get("color"))

    def test_color_theory_pure_color_adds_single_stat_bonus(self) -> None:
        spec = _pokemon_spec("Smeargle")
        spec.abilities = [{"name": "Color Theory", "color_theory_roll": 1, "color_theory_color": "Red"}]
        state = PokemonState(spec=spec, controller_id="ash")

        self.assertEqual(offensive_stat(state, "physical"), spec.atk + 6)
        effects = state.get_temporary_effects("color_theory")
        self.assertEqual(effects[0].get("color"), "Red")

    def test_color_theory_mixed_color_adds_split_bonuses_and_hp(self) -> None:
        spec = _pokemon_spec("Smeargle")
        spec.level = 20
        spec.abilities = [{"name": "Color Theory", "color_theory_roll": 10, "color_theory_color": "Blue-Violet"}]
        state = PokemonState(spec=spec, controller_id="ash")

        self.assertEqual(speed_stat(state), spec.spd + 3)
        expected_hp = spec.level + 3 * (spec.hp_stat + 3) + 10
        self.assertEqual(state.max_hp(), expected_hp)
        self.assertEqual(state.hp, expected_hp)

    def test_competitive_boosts_spatk_on_drop(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Milotic")
        defender_spec.abilities = [{"name": "Competitive"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Screech", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            stat="def",
            delta=-1,
            description="Screech lowers Defense.",
        )
        self.assertEqual(defender_state.combat_stages["spatk"], 2)
        self.assertTrue(any(evt.get("effect") == "competitive" for evt in events))

    def test_compound_eyes_adds_accuracy_bonus(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 5

        attacker_spec = _pokemon_spec("Butterfree")
        attacker_spec.abilities = [{"name": "Compound Eyes"}]
        defender_spec = _pokemon_spec("Onix")
        defender_spec.defense = 30
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        defender_state = PokemonState(spec=defender_spec, controller_id="gary")
        move = MoveSpec(
            name="String Shot",
            type="Bug",
            category="Physical",
            db=2,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        result = resolve_move_action(FixedRNG(), attacker_state, defender_state, move)
        self.assertTrue(result["hit"])

    def test_confidence_boosts_allies(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        user_spec = _pokemon_spec("Furfrou")
        user_spec.abilities = [{"name": "Confidence"}]
        ally_spec = _pokemon_spec("Eevee")
        user_state = PokemonState(spec=user_spec, controller_id=trainer.identifier, position=(0, 0))
        ally_state = PokemonState(spec=ally_spec, controller_id=trainer.identifier, position=(0, 1))
        user_state.add_temporary_effect("confidence_stat", stat="def")
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": user_state, "ash-2": ally_state},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Confidence", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(ally_state.combat_stages["def"], 1)

    def test_contrary_inverts_stage_changes(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Snivy")
        defender_spec.abilities = [{"name": "Contrary"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Growl", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            stat="atk",
            delta=-1,
            description="Growl lowers Attack.",
        )
        self.assertEqual(defender_state.combat_stages["atk"], 1)
        self.assertTrue(any(evt.get("ability") == "Contrary" for evt in events))

    def test_conqueror_triggers_on_ko(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Lucario")
        attacker_spec.abilities = [{"name": "Conqueror"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Aura Strike",
                type="Fighting",
                category="Physical",
                db=10,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=_pokemon_spec("Zubat"), controller_id=foe.identifier, position=(0, 1)
        )
        defender_state.hp = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Aura Strike", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.combat_stages["atk"], 1)
        self.assertEqual(attacker_state.combat_stages["spatk"], 1)
        self.assertEqual(attacker_state.combat_stages["spd"], 1)
        self.assertTrue(any(evt.get("ability") == "Conqueror" for evt in battle.log))

    def test_copy_master_boosts_chosen_stat(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Smeargle")
        attacker_spec.abilities = [{"name": "Copy Master"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Copycat",
                type="Normal",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
            )
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        attacker_state.add_temporary_effect("copy_master_stat", stat="spd")
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Copycat", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.combat_stages["spd"], 1)
        self.assertTrue(any(evt.get("ability") == "Copy Master" for evt in battle.log))

    def test_corrosive_toxins_bypasses_poison_heal(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Crobat")
        attacker_spec.abilities = [{"name": "Corrosive Toxins"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Toxic",
                type="Poison",
                category="Status",
                db=0,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        defender_spec = _pokemon_spec("Breloom")
        defender_spec.abilities = [{"name": "Poison Heal"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        defender_state.hp = defender_state.max_hp() - 5
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=random.Random(4),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Toxic", target_id="gary-1"))
        battle.resolve_next_action()
        before_hp = defender_state.hp
        battle.advance_phase()
        battle.advance_phase()
        battle.advance_phase()
        self.assertLess(defender_state.hp, before_hp)
        self.assertTrue(any(evt.get("ability") == "Corrosive Toxins" for evt in battle.log))

    def test_courage_adds_damage_bonus(self) -> None:
        attacker_spec = _pokemon_spec("Braviary")
        attacker_spec.abilities = [{"name": "Courage"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id="ash")
        defender_state = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id="gary")
        attacker_state.hp = max(1, attacker_state.max_hp() // 3)
        base_attacker_state = PokemonState(spec=_pokemon_spec("Braviary"), controller_id="ash")
        base_attacker_state.hp = attacker_state.hp
        move = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
        )
        base_rng = random.Random(2)
        bonus_rng = random.Random(2)
        base_result = resolve_move_action(base_rng, base_attacker_state, defender_state, move)
        bonus_result = resolve_move_action(bonus_rng, attacker_state, defender_state, move)
        self.assertGreater(bonus_result["damage"], base_result["damage"])

    def test_courage_reduces_damage_taken(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Braviary")
        defender_spec.abilities = [{"name": "Courage"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1))
        defender_state.hp = max(1, defender_state.max_hp() // 3)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": defender_state,
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Braviary"), controller_id=trainer.identifier, position=(0, 1)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        baseline.resolve_next_action()
        damage_with = defender_state.max_hp() - battle.pokemon["ash-1"].hp
        damage_without = baseline.pokemon["ash-1"].max_hp() - baseline.pokemon["ash-1"].hp
        self.assertLess(damage_with, damage_without)
        self.assertTrue(any(evt.get("ability") == "Courage" for evt in battle.log))

    def test_shed_skin_cures_status_at_end_phase(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Dragonite"), controller_id=trainer.identifier)
        target.statuses.append({"name": "Burned"})
        target.spec.abilities = [{"name": "Shed Skin"}]

        class FixedRNG:
            def randint(self, _a: int, b: int) -> int:
                return b

        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": target},
            rng=FixedRNG(),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.advance_phase()
        battle.advance_phase()
        battle.advance_phase()
        self.assertFalse(target.statuses, "Shed Skin should have cured the Burned status.")
        ability_events = [evt for evt in battle.log if evt.get("ability") == "Shed Skin"]
        self.assertTrue(ability_events)
        self.assertEqual(ability_events[-1]["result"], "cure")

    def test_max_hp_matches_ptu_engine_formula(self) -> None:
        spec = _pokemon_spec("Eevee")
        state = PokemonState(spec=spec, controller_id="ash")
        legacy = _ptu_pokemon_from_spec(spec)
        self.assertEqual(state.max_hp(), legacy.max_hp())

    def test_damage_matches_ptu_engine_calc(self) -> None:
        repo = PTUCsvRepository()
        pikachu = repo.build_pokemon_spec("Pikachu", level=20, move_names=["Thunder Shock"])
        squirtle = repo.build_pokemon_spec("Squirtle", level=20, move_names=["Tackle"])
        attacker = PokemonState(spec=pikachu, controller_id="ash")
        defender = PokemonState(spec=squirtle, controller_id="gary")
        move = pikachu.moves[0]

        rng_rules = random.Random(99)
        result = resolve_move_action(rng_rules, attacker, defender, move, weather="Clear")
        self.assertTrue(result["hit"])

        rng_ptu = random.Random(99)
        rng_ptu.randint(1, 20)  # consume the accuracy roll to match the interactive engine
        legacy_attacker = _ptu_pokemon_from_spec(pikachu)
        legacy_defender = _ptu_pokemon_from_spec(squirtle)
        legacy_move = _ptu_move_from_spec(move)
        terrain = ptu_engine.Terrain(name="Clear")
        packet = ptu_engine.calc_damage(legacy_attacker, legacy_defender, legacy_move, result["crit"], terrain, rng_ptu)
        self.assertEqual(result["damage"], packet["damage"])

    def test_melee_move_cannot_hit_out_of_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        pikachu = _pokemon_spec("Pikachu")
        pikachu.moves = [
            MoveSpec(name="Quick Attack", type="Normal", category="Physical", range_kind="Melee", range_value=None),
        ]
        eevee = _pokemon_spec("Eevee")
        player = PokemonState(spec=pikachu, controller_id=trainer.identifier, position=(0, 0))
        foe_mon = PokemonState(spec=eevee, controller_id=foe.identifier, position=(4, 4))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": player, "gary-1": foe_mon},
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Quick Attack", target_id="gary-1")
        with self.assertRaises(ValueError):
            battle.queue_action(action)

    def test_burst_move_hits_adjacent_targets(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Raichu")
        attacker_spec.moves = [
            MoveSpec(
                name="Shock Pulse",
                type="Electric",
                category="Special",
                db=6,
                range_kind="Self",
                target_kind="Self",
                area_kind="Burst",
                area_value=1,
            )
        ]
        foe_one = _pokemon_spec("Geodude")
        foe_two = _pokemon_spec("Onix")
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(2, 2))
        target_a = PokemonState(spec=foe_one, controller_id=foe.identifier, position=(3, 2))
        target_b = PokemonState(spec=foe_two, controller_id=foe.identifier, position=(2, 3))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": target_a, "gary-2": target_b},
            rng=random.Random(7),
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Shock Pulse")
        battle.queue_action(action)
        battle.resolve_next_action()
        move_events = [
            evt for evt in battle.log if evt.get("move") == "Shock Pulse" and evt.get("target") != "ash-1"
        ]
        self.assertEqual(len(move_events), 2)
        self.assertCountEqual({evt["target"] for evt in move_events}, {"gary-1", "gary-2"})

    def test_ai_prefers_ranged_when_melee_out_of_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = PokemonSpec(
            species="Testmon",
            level=20,
            types=["Electric"],
            hp_stat=10,
            atk=8,
            defense=8,
            spatk=10,
            spdef=8,
            spd=10,
            moves=[
                MoveSpec(name="Quick Attack", type="Normal", category="Physical", range_kind="Melee"),
                MoveSpec(name="Thunder Shock", type="Electric", category="Special", range_kind="Ranged", range_value=6),
            ],
        )
        defender_spec = _pokemon_spec("Eevee")
        foe_state = PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0))
        player_state = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 4))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"player-1": player_state, "foe-1": foe_state},
            weather="Rain",
        )
        move, target_id, _ = rules_ai.choose_best_move(battle, "foe-1")
        self.assertIsNotNone(move)
        self.assertEqual(move.name, "Thunder Shock")
        self.assertEqual(target_id, "player-1")

    def test_ai_ignores_benched_targets(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = PokemonSpec(
            species="Testmon",
            level=20,
            types=["Electric"],
            hp_stat=10,
            atk=8,
            defense=8,
            spatk=10,
            spdef=8,
            spd=10,
            moves=[
                MoveSpec(name="Thunder Shock", type="Electric", category="Special", range_kind="Ranged", range_value=6),
            ],
        )
        foe_state = PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0))
        active_target = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier, position=(0, 4))
        bench_target = PokemonState(spec=_pokemon_spec("Pichu"), controller_id=trainer.identifier, position=None, active=False)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"player-1": active_target, "player-2": bench_target, "foe-1": foe_state},
            weather="Rain",
        )
        move, target_id, _ = rules_ai.choose_best_move(battle, "foe-1")
        self.assertIsNotNone(move)
        self.assertEqual(target_id, "player-1")

    def test_ranged_move_rejected_when_los_blocked(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        pikachu = _pokemon_spec("Pikachu")
        eevee = _pokemon_spec("Eevee")
        player_state = PokemonState(spec=pikachu, controller_id=trainer.identifier, position=(0, 0))
        foe_state = PokemonState(spec=eevee, controller_id=foe.identifier, position=(4, 0))
        grid = GridState(width=5, height=1, blockers={(2, 0)})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": player_state, "gary-1": foe_state},
            grid=grid,
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        with self.assertRaises(ValueError):
            battle.queue_action(action)

    def test_difficult_tile_costs_additional_movement(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Pikachu")
        spec.movement["overland"] = 2
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(
            width=4,
            height=1,
            tiles={
                (1, 0): {"type": "difficult"},
            },
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            grid=grid,
        )
        reachable = movement.legal_shift_tiles(battle, "ash-1")
        self.assertIn((1, 0), reachable)
        self.assertNotIn((2, 0), reachable)

    def test_push_forced_movement_respects_blockers(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier, position=(1, 0))
        target = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(2, 0))
        grid = GridState(width=5, height=1, blockers={(4, 0)})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": target},
            grid=grid,
        )
        result = battle.apply_forced_movement("ash-1", "gary-1", {"kind": "push", "distance": 3})
        self.assertTrue(result)
        self.assertEqual(battle.pokemon["gary-1"].position, (3, 0))

    def test_pull_forced_movement_moves_toward_attacker(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier, position=(2, 0))
        target = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(4, 0))
        grid = GridState(width=6, height=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": target},
            grid=grid,
        )
        result = battle.apply_forced_movement("ash-1", "gary-1", {"kind": "pull", "distance": 2})
        self.assertTrue(result)
        self.assertEqual(battle.pokemon["gary-1"].position, (2, 0))

    def test_paralyzed_pokemon_skips_turn(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 1

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        paralyzed = _pokemon_spec("Pikachu")
        normal = _pokemon_spec("Eevee")
        paralyzed.moves[0].priority = 0
        paralyzed.spd = 20
        normal.spd = 5
        player_state = PokemonState(spec=paralyzed, controller_id=trainer.identifier, position=(0, 0))
        player_state.statuses.append({"name": "Paralyzed"})
        foe_state = PokemonState(spec=normal, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": player_state, "gary-1": foe_state},
            rng=FixedRNG(),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "gary-1")
        skip_events = [evt for evt in battle.log if evt.get("status") == "paralyzed" and evt.get("reason") == "skip"]
        self.assertTrue(skip_events, "Paralysis skip should be logged.")

    def test_sleep_status_saves_at_end_of_turn(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        sleeper_state = PokemonState(
            spec=_pokemon_spec("Snorlax"), controller_id=trainer.identifier, position=(0, 0)
        )
        sleeper_state.statuses.append({"name": "Sleep"})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": sleeper_state},
            rng=SequenceRNG([16]),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        battle.advance_phase()
        battle.advance_phase()
        battle.advance_phase()
        save_events = [evt for evt in battle.log if evt.get("effect") == "sleep_save"]
        self.assertTrue(save_events)
        self.assertEqual(save_events[-1]["dc"], 16)
        self.assertEqual(save_events[-1]["roll"], 16)
        self.assertEqual(save_events[-1]["total"], 16)
        self.assertFalse(sleeper_state.has_status("Sleep"))

    def test_sleep_blocks_standard_actions(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        sleeper_state = PokemonState(
            spec=_pokemon_spec("Snorlax"), controller_id=trainer.identifier, position=(0, 0)
        )
        sleeper_state.spec.spd = 20
        sleeper_state.statuses.append({"name": "Sleep"})
        foe_state = PokemonState(
            spec=_pokemon_spec("Eevee"), controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": sleeper_state, "gary-1": foe_state},
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "ash-1")
        with self.assertRaises(ValueError):
            battle.queue_action(
                UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
            )

    def test_wake_ally_action_cures_sleep(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        waker_spec = _pokemon_spec("Pikachu")
        waker_spec.spd = 12
        sleeper_spec = _pokemon_spec("Bulbasaur")
        sleeper_spec.spd = 6
        waker_state = PokemonState(
            spec=waker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        sleeper_state = PokemonState(
            spec=sleeper_spec, controller_id=trainer.identifier, position=(1, 0)
        )
        sleeper_state.statuses.append({"name": "Sleep"})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": waker_state, "ash-2": sleeper_state},
            grid=GridState(width=3, height=1),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "ash-1")
        battle.queue_action(WakeAllyAction(actor_id="ash-1", target_id="ash-2"))
        battle.resolve_next_action()
        self.assertFalse(sleeper_state.has_status("Sleep"))
        wake_events = [
            evt for evt in battle.log if evt.get("effect") == "wake" and evt.get("reason") == "ally"
        ]
        self.assertTrue(wake_events)

    def test_damage_wakes_sleeping_target(self) -> None:
        class FixedHitRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b  # always hit and roll max damage

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=_pokemon_spec("Snorlax"), controller_id=foe.identifier, position=(0, 1))
        defender_state.statuses.append({"name": "Sleep", "remaining": 2})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedHitRNG(),
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Thunder Shock", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertFalse(defender_state.has_status("Sleep"))
        wake_events = [
            evt
            for evt in battle.log
            if evt.get("status") == "sleep" and evt.get("effect") == "wake" and evt.get("reason") == "damage"
        ]
        self.assertTrue(wake_events, "Sleep should log a wake event when damage interrupts it.")

    def test_move_that_preserves_sleep_does_not_wake_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Gengar")
        attacker_spec.moves = [
            MoveSpec(
                name="Dream Eater",
                type="Psychic",
                category="Special",
                range_kind="Melee",
                range_value=1,
                effects_text="Dream Eater does not wake sleeping targets.",
            )
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender_state = PokemonState(spec=_pokemon_spec("Snorlax"), controller_id=foe.identifier, position=(0, 1))
        defender_state.statuses.append({"name": "Sleep", "remaining": 2})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=random.Random(2),
        )
        action = UseMoveAction(actor_id="ash-1", move_name="Dream Eater", target_id="gary-1")
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Sleep"))

    def test_flinch_status_skips_start_phase(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        flinched = PokemonState(spec=_pokemon_spec("Hitmonlee"), controller_id=trainer.identifier)
        flinched.statuses.append({"name": "Flinch"})
        flinched.spd = 20
        normal = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        normal.spd = 5
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": flinched, "gary-1": normal},
            rng=random.Random(1),
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        _advance_to_pokemon_turn(battle)
        skip_events = [evt for evt in battle.log if evt.get("type") == "status_skip"]
        self.assertTrue(any(evt.get("status") == "flinch" for evt in skip_events))
        self.assertFalse(flinched.statuses)

    def test_flinch_expires_at_round_boundary_for_faster_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        fast = PokemonState(spec=_pokemon_spec("Scyther"), controller_id=trainer.identifier)
        fast.statuses.append({"name": "Flinch", "applied_round": 0})
        fast.spd = 20
        slow = PokemonState(spec=_pokemon_spec("Tyrunt"), controller_id=foe.identifier)
        slow.spd = 5
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": fast, "gary-1": slow},
            rng=random.Random(1),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.actor_id, "ash-1")
        skip_events = [evt for evt in battle.log if evt.get("type") == "status_skip"]
        self.assertFalse(any(evt.get("status") == "flinch" for evt in skip_events))
        self.assertFalse(fast.has_status("Flinch"))

    def test_confusion_roll_hits_self_with_struggle(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        confused_spec = _pokemon_spec("Hypno")
        confused_spec.spd = 20
        confused = PokemonState(spec=confused_spec, controller_id=trainer.identifier, position=(0, 0))
        confused.statuses.append({"name": "Confused"})
        foe_spec = _pokemon_spec("Eevee")
        foe_spec.spd = 10
        foe_state = PokemonState(spec=foe_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": confused, "gary-1": foe_state},
            rng=SequenceRNG([8, 1, 5]),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "gary-1")
        confusion_events = [
            evt for evt in battle.log if evt.get("status") == "confused" and evt.get("effect") == "confusion"
        ]
        self.assertTrue(confusion_events)
        event = confusion_events[-1]
        self.assertEqual(event.get("outcome"), "hit_self")
        self.assertEqual(event.get("type_multiplier"), 0.5)
        expected_damage = int(math.floor((event.get("pre_type_damage") or 0) * 0.5))
        self.assertEqual(event.get("amount"), expected_damage)
        skip_events = [evt for evt in battle.log if evt.get("type") == "status_skip"]
        self.assertTrue(any(evt.get("status") == "confused" for evt in skip_events))
        self.assertTrue(confused.has_status("Confused"))

    def test_confusion_roll_cures_on_16(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash", speed=1)
        foe = TrainerState(identifier="gary", name="Gary", speed=2)
        confused_spec = _pokemon_spec("Hypno")
        confused_spec.spd = 20
        confused = PokemonState(spec=confused_spec, controller_id=trainer.identifier, position=(0, 0))
        confused.statuses.append({"name": "Confused"})
        foe_spec = _pokemon_spec("Eevee")
        foe_spec.spd = 10
        foe_state = PokemonState(spec=foe_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": confused, "gary-1": foe_state},
            rng=SequenceRNG([16]),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, "ash-1")
        self.assertFalse(confused.has_status("Confused"))
        confusion_events = [
            evt for evt in battle.log if evt.get("status") == "confused" and evt.get("effect") == "confusion"
        ]
        self.assertTrue(confusion_events)
        self.assertEqual(confusion_events[-1].get("outcome"), "cured")

    def test_trapped_status_logs_command_phase(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        trapped = PokemonState(spec=_pokemon_spec("Golem"), controller_id=trainer.identifier)
        trapped.statuses.append({"name": "Trapped"})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: trapped},
            rng=random.Random(2),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, actor_id)
        battle.advance_phase()  # move into Command phase
        trapped_events = [
            evt for evt in battle.log if evt.get("status") == "trapped" and evt.get("effect") == "trapped"
        ]
        self.assertTrue(trapped_events)

    def test_rage_status_logs_action_phase(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        raged = PokemonState(spec=_pokemon_spec("Primeape"), controller_id=trainer.identifier)
        raged.statuses.append({"name": "Rage"})
        actor_id = "ash-1"
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={actor_id: raged},
            rng=SequenceRNG([11]),
        )
        battle.start_round()
        entry = _advance_to_pokemon_turn(battle)
        self.assertEqual(entry.actor_id, actor_id)
        battle.advance_phase()  # command
        battle.advance_phase()  # action
        rage_events = [evt for evt in battle.log if evt.get("status") == "rage" and evt.get("effect") == "rage"]
        self.assertTrue(rage_events)
        self.assertEqual(rage_events[-1].get("roll"), 11)

    def test_recycle_reuses_item(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker = PokemonState(spec=_pokemon_spec("Chansey"), controller_id=trainer.identifier)
        attacker.hp = attacker.max_hp() - 20
        attacker.record_consumed_item("item", {"name": "Potion"})
        move = MoveSpec(name="Recycle", type="Normal", category="Status", ac=None)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertGreater(attacker.hp, attacker.max_hp() - 20)
        self.assertTrue([evt for evt in events if evt.get("effect") == "recycle_item"])

    def test_recycle_reuses_food_buff(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker = PokemonState(spec=_pokemon_spec("Chansey"), controller_id=trainer.identifier)
        attacker.hp = attacker.max_hp() - 10
        attacker.record_consumed_item(
            "food_buff",
            {"name": "Oran Berry", "effect": "Restores 5 Hit Points."},
        )
        move = MoveSpec(name="Recycle", type="Normal", category="Status", ac=None)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertGreater(attacker.hp, attacker.max_hp() - 10)
        self.assertTrue([evt for evt in events if evt.get("effect") == "recycle_food_buff"])

    def test_reflect_reduces_physical_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2, range_kind="Melee", range_value=1)
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Eevee")
        attacker_1 = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_1 = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle_1 = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_1, "gary-1": defender_1},
            rng=SequenceRNG([10] * 10),
        )
        battle_1.resolve_move_targets("ash-1", move, "gary-1", None)
        damage_plain = defender_1.max_hp() - (defender_1.hp or 0)
        attacker_2 = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_2 = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        defender_2.statuses.append({"name": "Reflect", "charges": 2})
        battle_2 = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_2, "gary-1": defender_2},
            rng=SequenceRNG([10] * 10),
        )
        battle_2.resolve_move_targets("ash-1", move, "gary-1", None)
        damage_reflect = defender_2.max_hp() - (defender_2.hp or 0)
        self.assertGreater(damage_plain, damage_reflect)
        reflect_entry = next(
            (entry for entry in defender_2.statuses if defender_2._normalized_status_name(entry) == "reflect"),
            None,
        )
        self.assertIsNotNone(reflect_entry)
        self.assertEqual(reflect_entry.get("charges"), 1)

    def test_light_screen_reduces_special_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=6,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            freq="At-Will",
        )
        attacker_spec = _pokemon_spec("Abra")
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Machop")
        attacker_1 = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_1 = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle_1 = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_1, "gary-1": defender_1},
            rng=SequenceRNG([10] * 10),
        )
        battle_1.resolve_move_targets("ash-1", move, "gary-1", None)
        damage_plain = defender_1.max_hp() - (defender_1.hp or 0)
        attacker_2 = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_2 = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        defender_2.statuses.append({"name": "Light Screen", "charges": 2})
        battle_2 = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_2, "gary-1": defender_2},
            rng=SequenceRNG([10] * 10),
        )
        battle_2.resolve_move_targets("ash-1", move, "gary-1", None)
        damage_screen = defender_2.max_hp() - (defender_2.hp or 0)
        self.assertGreater(damage_plain, damage_screen)
        screen_entry = next(
            (entry for entry in defender_2.statuses if defender_2._normalized_status_name(entry) == "light screen"),
            None,
        )
        self.assertIsNotNone(screen_entry)
        self.assertEqual(screen_entry.get("charges"), 1)

    def test_aurora_veil_reduces_damage_and_consumes_charges(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=5,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            freq="At-Will",
        )
        attacker_spec = _pokemon_spec("Squirtle")
        attacker_spec.moves = [move]
        defender_spec = _pokemon_spec("Eevee")
        attacker_1 = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_1 = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle_1 = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_1, "gary-1": defender_1},
            rng=SequenceRNG([10] * 10),
        )
        battle_1.resolve_move_targets("ash-1", move, "gary-1", None)
        damage_plain = defender_1.max_hp() - (defender_1.hp or 0)
        attacker_2 = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_2 = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        defender_2.statuses.append({"name": "Aurora Veil", "charges": 2})
        battle_2 = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_2, "gary-1": defender_2},
            rng=SequenceRNG([10] * 10),
        )
        battle_2.resolve_move_targets("ash-1", move, "gary-1", None)
        damage_veil = defender_2.max_hp() - (defender_2.hp or 0)
        self.assertGreater(damage_plain, damage_veil)
        veil_entry = next(
            (entry for entry in defender_2.statuses if defender_2._normalized_status_name(entry) == "aurora veil"),
            None,
        )
        self.assertIsNotNone(veil_entry)
        self.assertEqual(veil_entry.get("charges"), 1)

    def test_aurora_veil_applies_two_charges_in_hail(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        ally_one = PokemonState(spec=_pokemon_spec("Glaceon"), controller_id=trainer.identifier)
        ally_two = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=trainer.identifier)
        move = MoveSpec(
            name="Aurora Veil",
            type="Ice",
            category="Status",
            ac=None,
            range_kind="Self",
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": ally_one, "ash-2": ally_two},
            weather="Hail",
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=ally_one,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": False},
            damage_dealt=0,
        )
        for mon in (ally_one, ally_two):
            veil_entry = next(
                (entry for entry in mon.statuses if mon._normalized_status_name(entry) == "aurora veil"),
                None,
            )
            self.assertIsNotNone(veil_entry)
            self.assertEqual(veil_entry.get("charges"), 2)

    def test_reflect_type_changes_primary_type(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charizard")
        attacker_spec.types = ["Fire", "Flying"]
        defender_spec = _pokemon_spec("Vaporeon")
        defender_spec.types = ["Water", "Ice"]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        move = MoveSpec(name="Reflect Type", type="Normal", category="Status", ac=2)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker.spec.types[0], "Water")

    def test_conversion_uses_explicit_type_choice(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Porygon")
        attacker_spec.types = ["Normal"]
        attacker_spec.moves = [
            MoveSpec(name="Conversion", type="Normal", category="Status", ac=None),
            MoveSpec(name="Thunderbolt", type="Electric", category="Special", ac=2),
            MoveSpec(name="Psychic", type="Psychic", category="Special", ac=2),
        ]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})

        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=attacker_spec.moves[0],
            result={"hit": True},
            damage_dealt=0,
            move_params={"chosen_type": "Psychic"},
        )

        self.assertEqual(attacker.spec.types, ["Psychic"])

    def test_conversion_rejects_illegal_type_choice(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Porygon")
        attacker_spec.moves = [
            MoveSpec(name="Conversion", type="Normal", category="Status", ac=None),
            MoveSpec(name="Thunderbolt", type="Electric", category="Special", ac=2),
        ]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})

        with self.assertRaisesRegex(ValueError, "Chosen type is not legal for Conversion"):
            UseMoveAction(actor_id="ash-1", move_name="Conversion", target_id="ash-1", chosen_type="Water").validate(battle)

    def test_conversion2_uses_last_damaging_move_type_choice(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Porygon2")
        attacker_spec.types = ["Normal"]
        attacker_spec.moves = [
            MoveSpec(name="Conversion2", type="Normal", category="Status", ac=None),
        ]
        defender_spec = _pokemon_spec("Squirtle")
        defender_spec.moves = [
            MoveSpec(name="Flamethrower", type="Fire", category="Special", ac=2),
        ]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        defender.add_temporary_effect("last_move", name="Flamethrower", round=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.last_damage_taken["ash-1"] = {
            "attacker_id": "gary-1",
            "move_name": "Water Gun",
            "move_type": "Water",
            "round": 1,
            "damage": 12,
        }

        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=attacker_spec.moves[0],
            result={"hit": True},
            damage_dealt=0,
            move_params={"chosen_type": "Grass"},
        )

        self.assertEqual(attacker.spec.types, ["Grass"])

    def test_refresh_cures_statuses(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker = PokemonState(spec=_pokemon_spec("Snorlax"), controller_id=trainer.identifier)
        attacker.statuses.extend([{"name": "Poisoned"}, {"name": "Burned"}, {"name": "Paralyzed"}])
        move = MoveSpec(name="Refresh", type="Normal", category="Status", ac=None)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertFalse(attacker.has_status("Poisoned"))
        self.assertFalse(attacker.has_status("Burned"))
        self.assertFalse(attacker.has_status("Paralyzed"))

    def test_relic_song_sleeps_on_16(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Meloetta"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Ralts"), controller_id=foe.identifier)
        move = MoveSpec(name="Relic Song", type="Normal", category="Special", ac=2)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True, "roll": 16},
            damage_dealt=0,
        )
        self.assertTrue(defender.has_status("Sleep"))

    def test_rending_spell_deals_tick_on_16(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Alakazam"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Gastly"), controller_id=foe.identifier)
        before_hp = defender.hp
        move = MoveSpec(name="Rending Spell", type="Normal", category="Special", ac=2)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True, "roll": 16},
            damage_dealt=0,
        )
        self.assertLess(defender.hp, before_hp)

    def test_resonance_beam_lowers_spdef_on_20(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Noivern"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Wailmer"), controller_id=foe.identifier)
        move = MoveSpec(name="Resonance Beam", type="Normal", category="Special", ac=3)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True, "roll": 20},
            damage_dealt=0,
        )
        self.assertEqual(defender.combat_stages["spdef"], -1)

    def test_rest_heals_and_sets_rest_sleep(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker = PokemonState(spec=_pokemon_spec("Snorlax"), controller_id=trainer.identifier)
        attacker.hp = attacker.max_hp() - 30
        attacker.statuses.extend([{"name": "Burned"}, {"name": "Confused"}])
        move = MoveSpec(name="Rest", type="Psychic", category="Status", ac=None)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker.hp, attacker.max_hp())
        self.assertTrue(attacker.has_status("Sleep"))
        self.assertFalse(attacker.has_status("Burned"))
        sleep_entry = next(
            (entry for entry in attacker.statuses if attacker._normalized_status_name(entry) == "sleep"),
            {},
        )
        self.assertTrue(sleep_entry.get("rest_sleep"))

    def test_retaliate_boosts_after_ally_faint(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Pidgeot"), controller_id=trainer.identifier)
        ally = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Gengar"), controller_id=foe.identifier)
        move = MoveSpec(name="Retaliate", type="Normal", category="Physical", db=7, ac=2, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "ash-2": ally, "gary-1": defender},
            rng=SequenceRNG([10] * 10),
        )
        battle.round = 1
        battle.fainted_history.append({"round": 1, "attacker": "gary-1", "defender": "ash-2"})
        battle.resolve_move_targets("ash-1", move, "gary-1", None)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "retaliate_boost"])

    def test_return_sets_db_from_loyalty(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Eevee")
        attacker_spec.loyalty = 6
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Ditto"), controller_id=foe.identifier)
        move = MoveSpec(name="Return", type="Normal", category="Physical", db=8, ac=2, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([10] * 10),
        )
        battle.resolve_move_targets("ash-1", move, "gary-1", None)
        return_events = [evt for evt in battle.log if evt.get("effect") == "return_db"]
        self.assertTrue(return_events)
        self.assertEqual(return_events[-1].get("db"), 9)

    def test_revelation_dance_bonus_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Ludicolo")
        attacker_spec.types = ["Grass", "Water"]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Psyduck"), controller_id=foe.identifier)
        move = MoveSpec(name="Revelation Dance", type="Normal", category="Special", db=9, ac=2, range_kind="Ranged", range_value=6)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([10] * 10),
        )
        battle.dance_moves_used_this_round["ash-1"] = 2
        battle.resolve_move_targets("ash-1", move, "gary-1", None)
        bonus_events = [evt for evt in battle.log if evt.get("effect") == "revelation_dance_bonus"]
        self.assertTrue(bonus_events)
        self.assertEqual(bonus_events[-1].get("amount"), 10)
        type_events = [evt for evt in battle.log if evt.get("effect") == "revelation_dance_type"]
        self.assertTrue(type_events)
        self.assertEqual(type_events[-1].get("move_type"), "Grass")

    def test_revenge_boosts_after_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Machoke"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Zubat"), controller_id=foe.identifier)
        move = MoveSpec(name="Revenge", type="Fighting", category="Physical", db=6, ac=2, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([10] * 10),
        )
        battle.damage_taken_from = {"ash-1": {"gary-1"}}
        battle.resolve_move_targets("ash-1", move, "gary-1", None)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "revenge_boost"])

    def test_reversal_scales_with_injuries(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Machoke"), controller_id=trainer.identifier)
        attacker.injuries = 2
        defender = PokemonState(spec=_pokemon_spec("Zubat"), controller_id=foe.identifier)
        move = MoveSpec(name="Reversal", type="Fighting", category="Physical", db=7, ac=2, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([10] * 10),
        )
        battle.resolve_move_targets("ash-1", move, "gary-1", None)
        reversal_events = [evt for evt in battle.log if evt.get("effect") == "reversal_bonus"]
        self.assertTrue(reversal_events)
        self.assertEqual(reversal_events[-1].get("bonus_db"), 2)

    def test_riposte_ready_on_miss(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        miss_move = MoveSpec(name="Scratch", type="Normal", category="Physical", db=4, ac=2, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([1]),
        )
        battle.resolve_move_targets("ash-1", miss_move, "gary-1", None)
        self.assertTrue(defender.get_temporary_effects("riposte_ready"))

    def test_riposte_requires_trigger(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Eevee"), controller_id=foe.identifier)
        move = MoveSpec(name="Riposte", type="Normal", category="Physical", db=12, ac=2, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=SequenceRNG([10] * 10),
        )
        battle.resolve_move_targets("ash-1", move, "gary-1", None)
        self.assertTrue([evt for evt in battle.log if evt.get("effect") == "riposte_invalid"])

    def test_rising_voltage_sets_terrain_once(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
        move = MoveSpec(name="Rising Voltage", type="Electric", category="Special", db=7, ac=2, range_kind="Burst", range_value=2)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual((battle.terrain or {}).get("name"), "Electric Terrain")
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertTrue([evt for evt in events if evt.get("effect") == "rising_voltage_spent"])

    def test_roar_forces_movement(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Arcanine")
        defender_spec = _pokemon_spec("Rattata")
        defender_spec.movement = {"overland": 4}
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        attacker.position = (2, 2)
        defender.position = (2, 1)
        move = MoveSpec(name="Roar", type="Normal", category="Status", ac=2)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            grid=GridState(width=6, height=6),
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertNotEqual(defender.position, (2, 1))

    def test_rock_climb_confuses_on_17(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Machoke"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Zubat"), controller_id=foe.identifier)
        move = MoveSpec(name="Rock Climb", type="Normal", category="Physical", db=8, ac=5, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True, "roll": 17},
            damage_dealt=0,
        )
        self.assertTrue(defender.has_status("Confused"))

    def test_rock_polish_raises_speed(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker = PokemonState(spec=_pokemon_spec("Onix"), controller_id=trainer.identifier)
        move = MoveSpec(name="Rock Polish", type="Rock", category="Status", ac=None)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": attacker})
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=move,
            result={"hit": True},
            damage_dealt=0,
        )
        self.assertEqual(attacker.combat_stages["spd"], 2)

    def test_rock_slide_flinches_on_17(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Onix"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier)
        move = MoveSpec(name="Rock Slide", type="Rock", category="Physical", db=8, ac=4, range_kind="Ranged", range_value=6)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True, "roll": 17},
            damage_dealt=0,
        )
        self.assertTrue(defender.has_status("Flinch"))

    def test_rock_smash_lowers_defense_on_17(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker = PokemonState(spec=_pokemon_spec("Machoke"), controller_id=trainer.identifier)
        defender = PokemonState(spec=_pokemon_spec("Geodude"), controller_id=foe.identifier)
        move = MoveSpec(name="Rock Smash", type="Fighting", category="Physical", db=4, ac=2, range_kind="Melee", range_value=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id="gary-1",
            defender=defender,
            move=move,
            result={"hit": True, "roll": 17},
            damage_dealt=0,
        )
        self.assertEqual(defender.combat_stages["def"], -1)

    def test_covert_grants_evasion_bonus_in_habitat(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Pikachu")
        spec.abilities = [{"name": "Covert"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            terrain={"name": "Forest"},
        )
        events = state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        bonuses = state.get_temporary_effects("evasion_bonus")
        self.assertTrue(any(entry.get("source") == "Covert" for entry in bonuses))
        self.assertTrue(any(evt.get("ability") == "Covert" for evt in events))

    def test_cruelty_adds_injury_on_hit(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Seviper")
        attacker_spec.abilities = [{"name": "Cruelty"}]
        attacker_spec.moves = [
            MoveSpec(name="Bite", type="Dark", category="Physical", db=6, ac=None, range_kind="Melee", range_value=1)
        ]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state = battle.pokemon["gary-1"]
        self.assertEqual(defender_state.injuries, 1)
        self.assertTrue(any(evt.get("ability") == "Cruelty" for evt in battle.log))

    def test_crush_trap_adds_struggle_damage_on_wrap(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Ekans")
        attacker_spec.abilities = [{"name": "Crush Trap"}]
        attacker_spec.moves = [
            MoveSpec(name="Wrap", type="Normal", category="Physical", db=4, ac=None, range_kind="Melee", range_value=1)
        ]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Ekans"), controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline.pokemon["ash-1"].spec.moves = [attacker_spec.moves[0]]
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Wrap", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Wrap", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)
        self.assertTrue(any(evt.get("ability") == "Crush Trap" for evt in battle.log))

    def test_cursed_body_disables_move(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Gastly")
        defender_spec.abilities = [{"name": "Cursed Body"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        attacker_state = battle.pokemon["ash-1"]
        self.assertTrue(
            any(
                isinstance(status, dict)
                and status.get("name") == "Disabled"
                and status.get("move") == "Tackle"
                for status in attacker_state.statuses
            )
        )
        self.assertTrue(any(evt.get("ability") == "Cursed Body" for evt in battle.log))

    def test_cute_charm_infatuates_melee(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.gender = "Male"
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Clefairy")
        defender_spec.gender = "Female"
        defender_spec.abilities = [{"name": "Cute Charm"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].has_status("Infatuated"))

    def test_cute_tears_lowers_attack_stat(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Clefairy")
        defender_spec.abilities = [{"name": "Cute Tears"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].combat_stages["atk"], -2)

    def test_damp_blocks_explosion(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Koffing")
        attacker_spec.moves = [MoveSpec(name="Explosion", type="Normal", category="Physical", db=10, ac=None)]
        damp_spec = _pokemon_spec("Psyduck")
        damp_spec.abilities = [{"name": "Damp"}]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=damp_spec, controller_id=trainer.identifier, position=(0, 2)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            grid=GridState(width=6, height=6),
        )
        hp_before = battle.pokemon["ash-1"].hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Explosion", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].hp, hp_before)
        self.assertTrue(any(evt.get("ability") == "Damp" for evt in battle.log))

    def test_damp_blocks_aftermath(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Voltorb")
        defender_spec.abilities = [{"name": "Aftermath"}]
        damp_spec = _pokemon_spec("Psyduck")
        damp_spec.abilities = [{"name": "Damp"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        defender_state.hp = 1
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=damp_spec, controller_id=trainer.identifier, position=(0, 2)),
                "gary-1": defender_state,
            },
            grid=GridState(width=6, height=6),
            rng=MaxRNG(),
        )
        attacker_state = battle.pokemon["ash-1"]
        hp_before = attacker_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(attacker_state.hp, hp_before)
        self.assertTrue(any(evt.get("effect") == "block_aftermath" for evt in battle.log))

    def test_danger_syrup_triggers_sweet_scent(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Appletun")
        defender_spec.abilities = [{"name": "Danger Syrup"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        attacker_state = battle.pokemon["ash-1"]
        self.assertTrue(any(entry.get("amount") == -2 for entry in attacker_state.get_temporary_effects("evasion_bonus")))

    def test_dark_art_boosts_dark_damage_under_last_chance(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Umbreon")
        attacker_spec.abilities = [{"name": "Dark Art"}]
        attacker_spec.moves = [
            MoveSpec(name="Bite", type="Dark", category="Physical", db=6, ac=None, range_kind="Melee", range_value=1)
        ]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Umbreon"), controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.pokemon["ash-1"].spec.moves = attacker_spec.moves
        baseline.pokemon["ash-1"].spec.moves = attacker_spec.moves
        battle.pokemon["ash-1"].hp = 1
        baseline.pokemon["ash-1"].hp = 1
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)
        self.assertTrue(any(evt.get("ability") == "Dark Art" for evt in battle.log))

    def test_dark_aura_adds_db_for_allies(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Houndour")
        attacker_spec.moves = [
            MoveSpec(name="Bite", type="Dark", category="Physical", db=6, ac=None, range_kind="Melee", range_value=1)
        ]
        aura_spec = _pokemon_spec("Absol")
        aura_spec.abilities = [{"name": "Dark Aura"}]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=aura_spec, controller_id=trainer.identifier, position=(0, 2)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Houndour"), controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=MaxRNG(),
        )
        baseline.pokemon["ash-1"].spec.moves = attacker_spec.moves
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)
        self.assertTrue(any(evt.get("ability") == "Dark Aura" for evt in battle.log))

    def test_daze_puts_target_to_sleep(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Drowzee")
        attacker_spec.abilities = [{"name": "Daze"}]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Daze", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Sleep"))

    def test_deadly_poison_upgrades_poison(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Seviper")
        attacker_spec.abilities = [{"name": "Deadly Poison"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
        defender_state = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Poison Sting", type="Poison", category="Physical", db=2, ac=None)
        battle._apply_status(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            status="Poisoned",
            effect="poison",
            description="Poison Sting poisons the target.",
        )
        self.assertTrue(defender_state.has_status("Badly Poisoned"))

    def test_decoy_uses_follow_me_and_evasion(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        attacker_spec = _pokemon_spec("Pachirisu")
        attacker_spec.abilities = [{"name": "Decoy"}]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": attacker_state},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Decoy", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(attacker_state.get_temporary_effects("follow_me"))
        self.assertTrue(any(entry.get("amount") == 2 for entry in attacker_state.get_temporary_effects("evasion_bonus")))

    def test_deep_sleep_heals_tick(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Snorlax")
        spec.abilities = [{"name": "Deep Sleep"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.statuses.append({"name": "Sleep"})
        state.hp = max(1, state.max_hp() - 5)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        hp_before = state.hp
        state.handle_phase_effects(battle, TurnPhase.END, "ash-1")
        self.assertGreater(state.hp, hp_before)

    def test_defeatist_adjusts_stages_below_half(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Archen")
        spec.abilities = [{"name": "Defeatist"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.hp = max(1, state.max_hp() // 2 - 1)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        events = battle._sync_defeatist_threshold("ash-1")
        self.assertEqual(state.combat_stages["atk"], -1)
        self.assertEqual(state.combat_stages["spatk"], -1)
        self.assertEqual(state.combat_stages["spd"], 2)
        self.assertTrue(any(evt.get("ability") == "Defeatist" for evt in events))

    def test_defiant_raises_attack_on_drop(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_state = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=trainer.identifier)
        defender_spec = _pokemon_spec("Braviary")
        defender_spec.abilities = [{"name": "Defiant"}]
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        events: List[dict] = []
        move = MoveSpec(name="Growl", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="ash-1",
            target_id="gary-1",
            move=move,
            target=defender_state,
            stat="atk",
            delta=-1,
            description="Growl lowers Attack.",
        )
        self.assertEqual(defender_state.combat_stages["atk"], 2)
        self.assertTrue(any(evt.get("effect") == "defiant" for evt in events))

    def test_defy_death_heals_injuries(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Zubat")
        spec.abilities = [{"name": "Defy Death"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.injuries = 3
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Defy Death", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(state.injuries, 1)

    def test_delayed_reaction_defers_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Slowpoke")
        defender_spec.abilities = [{"name": "Delayed Reaction"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Slowpoke"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.round = 1
        baseline.round = 1
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        baseline.resolve_next_action()
        delayed_defender = battle.pokemon["gary-1"]
        normal_defender = baseline.pokemon["gary-1"]
        self.assertGreater(delayed_defender.hp, normal_defender.hp)
        battle.round = 2
        delayed_defender.handle_phase_effects(battle, TurnPhase.END, "gary-1")
        self.assertLessEqual(delayed_defender.hp, normal_defender.hp)

    def test_delivery_bird_prefers_equipped_item(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [_contact_move_spec("Knock Off")]
        defender_spec = _pokemon_spec("Delibird")
        defender_spec.abilities = [{"name": "Delivery Bird"}]
        defender_spec.items = [
            {"name": "Oran Berry"},
            {"name": "Sitrus Berry", "equipped": True},
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Knock Off", target_id="gary-1"))
        battle.resolve_next_action()
        remaining = [item.get("name") for item in defender_spec.items if isinstance(item, dict)]
        self.assertEqual(remaining, ["Oran Berry"])
        self.assertTrue(any(evt.get("item") == "Sitrus Berry" for evt in battle.log))

    def test_desert_weather_heals_in_rain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Cacturne")
        spec.abilities = [{"name": "Desert Weather"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.hp = max(1, state.max_hp() - 5)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            weather="Rain",
        )
        hp_before = state.hp
        state.handle_phase_effects(battle, TurnPhase.END, "ash-1")
        self.assertGreater(state.hp, hp_before)

    def test_desert_weather_resists_fire_in_sun(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Vulpix")
        attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Sandshrew")
        defender_spec.abilities = [{"name": "Desert Weather"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            weather="Sunny",
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Sandshrew"), controller_id=foe.identifier, position=(0, 1)),
            },
            weather="Sunny",
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertLess(damage_with, damage_without)

    def test_diamond_defense_places_fairy_stealth_rock(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Carbink")
        spec.abilities = [{"name": "Diamond Defense"}]
        spec.moves = [
            MoveSpec(
                name="Stealth Rock",
                type="Rock",
                category="Status",
                db=0,
                ac=None,
                range_kind="Self",
                target_kind="Self",
                freq="Scene",
            )
        ]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {}})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            grid=grid,
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Stealth Rock", target_id="ash-1"))
        battle.resolve_next_action()
        hazards = battle.grid.tiles[(0, 0)].get("hazards", {})
        self.assertIn("stealth_rock_fairy", hazards)

    def test_diamond_defense_stealth_rock_uses_best_type(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target_spec = _pokemon_spec("Dratini")
        target = PokemonState(spec=target_spec, controller_id=trainer.identifier, position=(0, 0))
        base = PokemonState(spec=_pokemon_spec("Dratini"), controller_id=trainer.identifier, position=(0, 0))
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"stealth_rock_fairy": 1}}})
        base_grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"stealth_rock": 1}}})
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": target},
            grid=grid,
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": base},
            grid=base_grid,
        )
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        baseline.start_round()
        _advance_to_pokemon_turn(baseline)
        damage_with = target.max_hp() - (target.hp or 0)
        damage_without = base.max_hp() - (base.hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_dig_away_avoids_attack_and_sets_pending_dig(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Sandshrew")
        defender_spec.abilities = [{"name": "Dig Away"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        defender_state = battle.pokemon["gary-1"]
        hp_before = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, hp_before)
        self.assertIsNotNone(defender_state.pending_resolution)
        pending_move = defender_state.pending_resolution.get("move") if defender_state.pending_resolution else None
        self.assertEqual((pending_move.name if pending_move else ""), "Dig")

    def test_discipline_cures_afflictions_on_start(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Machamp")
        spec.abilities = [{"name": "Discipline"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        state.statuses.append({"name": "Confused"})
        state.statuses.append({"name": "Enraged"})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertFalse(state.has_status("Confused"))
        self.assertFalse(state.has_status("Enraged"))

    def test_dire_spore_adds_poison_on_spore(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Breloom")
        attacker_spec.abilities = [{"name": "Dire Spore"}]
        attacker_spec.moves = [
            MoveSpec(name="Spore", type="Grass", category="Status", db=0, ac=None, range_kind="Ranged", range_value=6)
        ]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Spore", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state = battle.pokemon["gary-1"]
        self.assertTrue(defender_state.has_status("Sleep"))
        self.assertTrue(defender_state.has_status("Poisoned"))

    def test_dodge_avoids_damaging_move(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Abra")
        defender_spec.abilities = [{"name": "Dodge"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        defender_state = battle.pokemon["gary-1"]
        hp_before = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, hp_before)
        self.assertTrue(any(evt.get("ability") == "Dodge" for evt in battle.log))

    def test_download_boosts_damage_against_target(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Porygon")
        attacker_spec.abilities = [{"name": "Download"}]
        attacker_spec.moves = [
            MoveSpec(name="Download", type="Normal", category="Status", db=0, ac=None, range_kind="Ranged", range_value=6),
            _contact_move_spec("Tackle"),
        ]
        baseline_spec = _pokemon_spec("Porygon")
        baseline_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Geodude")
        defender_spec.defense = 5
        defender_spec.spdef = 20
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=baseline_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Download", target_id="gary-1"))
        battle.resolve_next_action()
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_dreamspinner_heals_per_sleeping_target(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        user_spec = _pokemon_spec("Cresselia")
        user_spec.abilities = [{"name": "Dreamspinner"}]
        user_state = PokemonState(spec=user_spec, controller_id=trainer.identifier, position=(0, 0))
        user_state.hp = max(1, user_state.max_hp() - user_state.tick_value() * 2)
        sleeper_1 = PokemonState(spec=_pokemon_spec("Gastly"), controller_id=foe.identifier, position=(0, 1))
        sleeper_2 = PokemonState(spec=_pokemon_spec("Drowzee"), controller_id=foe.identifier, position=(1, 0))
        sleeper_1.statuses.append({"name": "Sleep"})
        sleeper_2.statuses.append({"name": "Asleep"})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": user_state, "gary-1": sleeper_1, "gary-2": sleeper_2},
        )
        hp_before = user_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Dreamspinner", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertGreater(user_state.hp, hp_before)

    def test_drizzle_sets_rain(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Kyogre")
        spec.abilities = [{"name": "Drizzle"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Drizzle", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.weather, "Rain")

    def test_drought_sets_sun(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Groudon")
        spec.abilities = [{"name": "Drought"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Drought", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.weather, "Sunny")

    def test_drown_out_blocks_sonic_move(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Noivern")
        attacker_spec.moves = [
            MoveSpec(
                name="Sonic Test",
                type="Normal",
                category="Special",
                db=6,
                ac=2,
                range_kind="Ranged",
                range_value=6,
                keywords=["Sonic"],
            )
        ]
        defender_spec = _pokemon_spec("Jigglypuff")
        defender_spec.abilities = [{"name": "Drown Out"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        defender_state = battle.pokemon["gary-1"]
        hp_before = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Sonic Test", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, hp_before)
        self.assertTrue(any(evt.get("ability") == "Drown Out" for evt in battle.log))

    def test_dry_skin_blocks_water_and_heals(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Squirtle")
        attacker_spec.moves = [MoveSpec(name="Water Gun", type="Water", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Houndour")
        defender_spec.abilities = [{"name": "Dry Skin"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        defender_state = battle.pokemon["gary-1"]
        defender_state.hp = max(1, defender_state.max_hp() - defender_state.tick_value())
        hp_before = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Water Gun", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertGreater(defender_state.hp, hp_before)

    def test_dry_skin_takes_fire_tick_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Croagunk")
        defender_spec.abilities = [{"name": "Dry Skin"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Croagunk"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_dust_cloud_turns_powder_into_burst(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Oddish")
        attacker_spec.abilities = [{"name": "Dust Cloud"}]
        attacker_spec.moves = [
            MoveSpec(name="Poison Powder", type="Poison", category="Status", db=0, ac=None, range_kind="Ranged", range_value=6)
        ]
        defender_1 = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1))
        defender_2 = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(1, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender_1,
                "gary-2": defender_2,
            },
            grid=GridState(width=3, height=3),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Poison Powder", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_1.has_status("Poisoned"))
        self.assertTrue(defender_2.has_status("Poisoned"))

    def test_early_bird_adds_save_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Pidgey")
        spec.abilities = [{"name": "Early Bird"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        self.assertEqual(state.save_bonus(battle), 3)

    def test_enfeebling_lips_lowers_stat_on_lovely_kiss(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Jynx")
        attacker_spec.abilities = [{"name": "Enfeebling Lips"}]
        attacker_spec.moves = [MoveSpec(name="Lovely Kiss", type="Normal", category="Status", db=0, ac=None, range_kind="Melee", range_value=1)]
        defender_spec = _pokemon_spec("Onix")
        defender_spec.defense = 50
        defender_spec.atk = 10
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Lovely Kiss", target_id="gary-1"))
        battle.resolve_next_action()
        defender_state = battle.pokemon["gary-1"]
        self.assertEqual(defender_state.combat_stages["def"], -2)

    def test_electrodash_grants_sprint(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Raichu")
        spec.abilities = [{"name": "Electrodash"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Electrodash", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(state.get_temporary_effects("sprint"))

    def test_enduring_rage_reduces_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machoke")
        attacker_spec.moves = [_contact_move_spec("Tackle")]
        defender_spec = _pokemon_spec("Primeape")
        defender_spec.abilities = [{"name": "Enduring Rage"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.pokemon["gary-1"].statuses.append({"name": "Enraged"})
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Primeape"), controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertLess(damage_with, damage_without)

    def test_exploit_adds_damage_on_super_effective_hit(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Houndour")
        attacker_spec.abilities = [{"name": "Exploit"}]
        attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Oddish")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Houndour"), controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_fabulous_trim_sets_style_effect(self) -> None:
        spec = _pokemon_spec("Furfrou")
        spec.abilities = [{"name": "Fabulous Trim"}]
        state = PokemonState(spec=spec, controller_id="ash")
        effects = state.get_temporary_effects("fabulous_trim")
        self.assertTrue(effects)

    def test_fade_away_grants_invisibility(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Gengar")
        spec.abilities = [{"name": "Fade Away"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Fade Away", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(state.get_temporary_effects("fade_away"))

    def test_fairy_aura_boosts_fairy_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Sylveon")
        attacker_spec.moves = [MoveSpec(name="Fairy Wind", type="Fairy", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        aura_spec = _pokemon_spec("Xerneas")
        aura_spec.abilities = [{"name": "Fairy Aura"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=aura_spec, controller_id=trainer.identifier, position=(0, 1)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 2)),
            },
            rng=MaxRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 2)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Fairy Wind", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Fairy Wind", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_fashion_designer_crafts_item(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Leafeon")
        spec.abilities = [{"name": "Fashion Designer"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.add_temporary_effect("fashion_designer_choice", item="Dew Cup")
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Fashion Designer", target_id="ash-1"))
        battle.resolve_next_action()
        crafted = [item for item in state.spec.items if isinstance(item, dict)]
        crafted_names = {item.get("name") for item in crafted}
        self.assertIn("Occa Berry", crafted_names)

    def test_fiery_crash_changes_dash_moves_and_burns(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 19

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rapidash")
        attacker_spec.abilities = [{"name": "Fiery Crash"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Horn Charge",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
                keywords=["Dash"],
            )
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.add_temporary_effect("fiery_crash_choice", mode="fire")
        defender_state = PokemonState(spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Horn Charge", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender_state.has_status("Burned"))
        self.assertTrue(any(evt.get("ability") == "Fiery Crash" for evt in battle.log))

    def test_fiery_crash_db_mode_logs(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rapidash")
        attacker_spec.abilities = [{"name": "Fiery Crash"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Horn Charge",
                type="Fire",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
                keywords=["Dash"],
            )
        ]
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.add_temporary_effect("fiery_crash_choice", mode="db")
        defender_state = PokemonState(spec=_pokemon_spec("Oddish"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Horn Charge", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Fiery Crash" and evt.get("mode") == "db" for evt in battle.log))

    def test_filter_reduces_super_effective_damage(self) -> None:
        class MaxRNG(random.Random):
            def randint(self, _a: int, b: int) -> int:
                return b

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Growlithe")
        attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Oddish")
        defender_spec.abilities = [{"name": "Filter"}]
        defender_spec.types = ["Grass"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        baseline_spec = _pokemon_spec("Oddish")
        baseline_spec.types = ["Grass"]
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=baseline_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=MaxRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertLess(damage_with, damage_without)

    def test_flare_boost_raises_special_attack_when_burned(self) -> None:
        class MidRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Houndour")
        attacker_spec.abilities = [{"name": "Flare Boost"}]
        attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Rattata")
        burned = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        burned.statuses.append({"name": "Burned"})
        normal = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": burned, "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))},
            rng=MidRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": normal, "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))},
            rng=MidRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_flash_fire_immunity_and_bonus(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Growlithe")
        attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Vulpix")
        defender_spec.abilities = [{"name": "Flash Fire"}]
        defender_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        before_hp = battle.pokemon["gary-1"].hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(before_hp, battle.pokemon["gary-1"].hp)
        self.assertTrue(any(evt.get("ability") == "Flash Fire" and evt.get("effect") == "absorb" for evt in battle.log))
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Ember", target_id="ash-1"))
        battle.resolve_next_action()
        bonus_events = [evt for evt in battle.log if evt.get("ability") == "Flash Fire" and evt.get("effect") == "damage_bonus"]
        self.assertTrue(bonus_events)

    def test_fluffy_charge_adds_defense_stage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Mareep")
        spec.abilities = [{"name": "Fluffy Charge"}]
        spec.moves = [MoveSpec(name="Charge", type="Electric", category="Status", ac=None, range_kind="Self", range_value=0)]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Charge", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(state.combat_stages["def"], 1)
        self.assertTrue(any(evt.get("ability") == "Fluffy Charge" for evt in battle.log))

    def test_flower_gift_boosts_allies_in_sun(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Cherrim")
        spec.abilities = [{"name": "Flower Gift"}]
        leader = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        leader.add_temporary_effect("flower_gift_stats", stats=["atk", "spd"])
        ally = PokemonState(spec=_pokemon_spec("Bulbasaur"), controller_id=trainer.identifier, position=(0, 2))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": leader, "ash-2": ally},
        )
        battle.weather = "Sunny"
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Flower Gift", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(ally.combat_stages["atk"], 1)
        self.assertEqual(ally.combat_stages["spd"], 1)

    def test_flower_power_swaps_grass_move_category(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        spec = _pokemon_spec("Bellossom")
        spec.abilities = [{"name": "Flower Power"}]
        spec.moves = [MoveSpec(name="Energy Ball", type="Grass", category="Special", db=8, ac=None, range_kind="Ranged", range_value=6)]
        attacker = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        attacker.add_temporary_effect("flower_power_choice", category="physical")
        defender = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Energy Ball", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Flower Power" and evt.get("effect") == "category_swap" for evt in battle.log))

    def test_flower_veil_blocks_stat_drops(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        target_spec = _pokemon_spec("Bulbasaur")
        target_spec.types = ["Grass"]
        target = PokemonState(spec=target_spec, controller_id=trainer.identifier, position=(0, 0))
        veil_spec = _pokemon_spec("Cherrim")
        veil_spec.abilities = [{"name": "Flower Veil"}]
        veil = PokemonState(spec=veil_spec, controller_id=trainer.identifier, position=(0, 3))
        attacker = PokemonState(spec=_pokemon_spec("Pidgey"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": target, "ash-2": veil, "gary-1": attacker},
        )
        events: List[dict] = []
        move = MoveSpec(name="Tail Whip", type="Normal", category="Status")
        battle._apply_combat_stage(
            events,
            attacker_id="gary-1",
            target_id="ash-1",
            move=move,
            target=target,
            stat="def",
            delta=-1,
            description="Tail Whip lowers Defense.",
        )
        self.assertEqual(target.combat_stages["def"], 0)
        self.assertTrue(any(evt.get("ability") == "Flower Veil" for evt in events))

    def test_flutter_prevents_flanking(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        spec = _pokemon_spec("Butterfree")
        spec.abilities = [{"name": "Flutter"}]
        defender = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        attacker = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(1, 0))
        flanker = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(-1, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": defender, "gary-1": attacker, "gary-2": flanker},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Flutter", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(defender.get_temporary_effects("flank_immunity"))
        self.assertFalse(battle._is_flanked("ash-1", "gary-1"))

    def test_flying_fly_trap_blocks_ground_and_bug(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Diglett")
        attacker_spec.moves = [
            MoveSpec(name="Mud Slap", type="Ground", category="Special", db=4, ac=None, range_kind="Ranged", range_value=6),
            MoveSpec(name="Bug Buzz", type="Bug", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6),
        ]
        defender_spec = _pokemon_spec("Carnivine")
        defender_spec.abilities = [{"name": "Flying Fly Trap"}]
        defender = PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1))
        attacker = PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": defender, "gary-1": attacker},
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Mud Slap", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Flying Fly Trap" for evt in battle.log))
        before = defender.hp
        battle.pokemon["gary-1"].reset_actions()
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Bug Buzz", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertEqual(before, defender.hp)

    def test_focus_boosts_fighting_damage_under_last_chance(self) -> None:
        class MidRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.abilities = [{"name": "Focus"}]
        attacker_spec.moves = [MoveSpec(name="Karate Chop", type="Fighting", category="Physical", db=8, ac=None, range_kind="Melee", range_value=1)]
        defender_spec = _pokemon_spec("Rattata")
        boosted = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        boosted.hp = max(1, boosted.max_hp() // 4)
        normal = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": boosted, "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))},
            rng=MidRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": normal, "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))},
            rng=MidRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Karate Chop", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Karate Chop", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_forecast_updates_type_on_start_phase(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Castform")
        spec.abilities = [{"name": "Forecast"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        battle.weather = "Rain"
        events = state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.spec.types, ["Water"])
        self.assertTrue(any(evt.get("ability") == "Forecast" for evt in events))

    def test_forest_lord_adds_accuracy_bonus(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        spec = _pokemon_spec("Trevenant")
        spec.abilities = [{"name": "Forest Lord"}]
        spec.moves = [
            MoveSpec(name="Forest Lord", type="Grass", category="Status", ac=None, range_kind="Self", range_value=0),
            MoveSpec(name="Giga Drain", type="Grass", category="Special", db=8, ac=4, range_kind="Ranged", range_value=6),
        ]
        attacker = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        defender = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 2))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Forest Lord", target_id="ash-1"))
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Giga Drain", target_id="gary-1"))
        battle.resolve_next_action()
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Forest Lord" and evt.get("effect") == "accuracy_bonus" for evt in battle.log))

    def test_forewarn_penalizes_target_accuracy(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        seer_spec = _pokemon_spec("Hypno")
        seer_spec.abilities = [{"name": "Forewarn"}]
        seer = PokemonState(spec=seer_spec, controller_id=trainer.identifier, position=(0, 0))
        target_spec = _pokemon_spec("Pidgey")
        target_spec.moves = [
            MoveSpec(name="Wing Attack", type="Flying", category="Physical", db=8, ac=4, range_kind="Melee", range_value=1),
            MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=4, range_kind="Melee", range_value=1),
        ]
        target = PokemonState(spec=target_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": seer, "gary-1": target},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Forewarn", target_id="gary-1"))
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Wing Attack", target_id="ash-1"))
        battle.resolve_next_action()
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Forewarn" and evt.get("effect") == "accuracy_penalty" for evt in battle.log))

    def test_fox_fire_triggers_ember_interrupt(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        fox_spec = _pokemon_spec("Ninetales")
        fox_spec.abilities = [{"name": "Fox Fire"}]
        fox_spec.moves = [
            MoveSpec(name="Fox Fire", type="Fire", category="Status", ac=None, range_kind="Self", range_value=0),
        ]
        fox = PokemonState(spec=fox_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=None, range_kind="Melee", range_value=1)]
        attacker = PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": fox, "gary-1": attacker},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Fox Fire", target_id="ash-1"))
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Fox Fire" and evt.get("effect") == "interrupt" for evt in battle.log))
        fox_effects = fox.get_temporary_effects("fox_fire")
        if fox_effects:
            self.assertEqual(fox_effects[0].get("charges"), 2)

    def test_freezing_point_boosts_ice_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Snover")
        attacker_spec.abilities = [{"name": "Freezing Point"}]
        attacker_spec.moves = [
            MoveSpec(name="Ice Beam", type="Ice", category="Special", db=8, ac=4, range_kind="Ranged", range_value=6)
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.hp = max(1, attacker_state.max_hp() // 4)
        baseline_spec = _pokemon_spec("Snover")
        baseline_spec.abilities = []
        baseline_spec.moves = list(attacker_spec.moves)
        baseline_state = PokemonState(
            spec=baseline_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1))},
            rng=FixedRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": baseline_state, "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1))},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ice Beam", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ice Beam", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_friend_guard_resists_adjacent_ally_hit(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=6, ac=None, range_kind="Ranged", range_value=6)]
        defender_spec = _pokemon_spec("Bulbasaur")
        defender_spec.types = ["Grass"]
        friend_spec = _pokemon_spec("Clefairy")
        friend_spec.abilities = [{"name": "Friend Guard"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=friend_spec, controller_id=trainer.identifier, position=(0, 1)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 3)),
            },
            rng=FixedRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 3)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Ember", target_id="ash-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="gary-1", move_name="Ember", target_id="ash-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["ash-1"].max_hp() - (battle.pokemon["ash-1"].hp or 0)
        damage_without = baseline.pokemon["ash-1"].max_hp() - (baseline.pokemon["ash-1"].hp or 0)
        self.assertLess(damage_with, damage_without)

    def test_frighten_lowers_speed(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Houndour")
        attacker_spec.abilities = [{"name": "Frighten"}]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        target = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 2))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": target},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Frighten", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(target.combat_stages["spd"], -2)

    def test_frisk_reveals_target_details(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Sentret")
        attacker_spec.abilities = [{"name": "Frisk"}]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        target_spec = _pokemon_spec("Pidgey")
        target_spec.types = ["Normal", "Flying"]
        target_spec.abilities = [{"name": "Keen Eye"}]
        target_spec.nature = "Brave"
        target_spec.level = 12
        target_spec.items = [{"name": "Oran Berry"}]
        target = PokemonState(spec=target_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": target},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Frisk", target_id="gary-1"))
        battle.resolve_next_action()
        frisk_event = next(evt for evt in battle.log if evt.get("effect") == "frisk")
        self.assertIn("Normal", frisk_event.get("types", []))
        self.assertIn("Keen Eye", frisk_event.get("abilities", []))
        self.assertEqual(frisk_event.get("nature"), "Brave")
        self.assertEqual(frisk_event.get("level"), 12)
        self.assertIn("Oran Berry", frisk_event.get("items", []))

    def test_frostbite_slows_and_extends_freeze(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 18

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Spheal")
        attacker_spec.abilities = [{"name": "Frostbite"}]
        attacker_spec.moves = [
            MoveSpec(name="Ice Beam", type="Ice", category="Special", db=8, ac=4, range_kind="Ranged", range_value=6)
        ]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ice Beam", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(defender.has_status("Slowed"))
        self.assertTrue(defender.has_status("Frozen"))

    def test_fur_coat_resists_physical_attacks(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=None, range_kind="Melee", range_value=1)]
        defender_spec = _pokemon_spec("Furfrou")
        defender_spec.abilities = [{"name": "Fur Coat"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 1)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0)),
            },
            rng=FixedRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Furfrou"), controller_id=trainer.identifier, position=(0, 1)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 0)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["ash-1"].max_hp() - (battle.pokemon["ash-1"].hp or 0)
        damage_without = baseline.pokemon["ash-1"].max_hp() - (baseline.pokemon["ash-1"].hp or 0)
        self.assertLess(damage_with, damage_without)

    def test_gale_wings_grants_priority_to_flying_moves(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgey")
        attacker_spec.abilities = [{"name": "Gale Wings"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Gust",
                type="Flying",
                category="Special",
                db=4,
                ac=None,
                range_kind="Ranged",
                range_value=6,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Gust", target_id="gary-1"))
        battle.resolve_next_action()
        priority_event = next(
            evt for evt in battle.log if evt.get("ability") == "Gale Wings" and evt.get("effect") == "priority"
        )
        self.assertEqual(priority_event.get("move"), "Gust")

    def test_gale_wings_sumo_turns_quick_attack_flying(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgey")
        attacker_spec.abilities = [{"name": "Gale Wings [SuMo Errata]"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Quick Attack",
                type="Normal",
                category="Physical",
                db=4,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Quick Attack", target_id="gary-1"))
        battle.resolve_next_action()
        type_event = next(
            evt
            for evt in battle.log
            if evt.get("effect") == "type_change" and "gale wings" in str(evt.get("ability", "")).lower()
        )
        self.assertEqual(type_event.get("from"), "Normal")
        self.assertEqual(type_event.get("to"), "Flying")

    def test_gardener_improves_soil_quality(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        grid = GridState(width=1, height=1, tiles={(0, 0): {"type": "yielding plant"}})
        attacker_spec = _pokemon_spec("Eldegoss")
        attacker_spec.abilities = [{"name": "Gardener"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=None),
            },
            grid=grid,
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Gardener"))
        battle.resolve_next_action()
        tile_meta = battle.grid.tiles.get((0, 0), {})
        self.assertEqual(tile_meta.get("soil_quality"), 1)
        self.assertTrue(tile_meta.get("gardener_used"))

    def test_gentle_vibe_resets_stages_and_cures_volatile(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Mew")
        attacker_spec.abilities = [{"name": "Gentle Vibe"}]
        defender_spec = _pokemon_spec("Rattata")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(1, 0)),
            },
        )
        battle.pokemon["ash-1"].combat_stages["atk"] = 2
        battle.pokemon["gary-1"].combat_stages["def"] = -1
        battle.pokemon["ash-1"].statuses.append({"name": "Confused"})
        battle.pokemon["gary-1"].statuses.append({"name": "Enraged"})
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Gentle Vibe"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].combat_stages["atk"], 0)
        self.assertEqual(battle.pokemon["gary-1"].combat_stages["def"], 0)
        self.assertFalse(battle.pokemon["ash-1"].has_status("Confused"))
        self.assertFalse(battle.pokemon["gary-1"].has_status("Enraged"))

    def test_gluttony_allows_three_food_buffs(self) -> None:
        spec = _pokemon_spec("Snorlax")
        spec.abilities = [{"name": "Gluttony"}]
        state = PokemonState(spec=spec, controller_id="ash")
        state.add_food_buff({"name": "Buff 1", "effect": ""})
        state.add_food_buff({"name": "Buff 2", "effect": ""})
        state.add_food_buff({"name": "Buff 3", "effect": ""})
        state.add_food_buff({"name": "Buff 4", "effect": ""})
        self.assertEqual(len(state.food_buffs), 3)

    def test_gooey_lowers_speed_on_contact(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=4,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Goomy")
        defender_spec.abilities = [{"name": "Gooey"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].combat_stages["spd"], -1)

    def test_gore_pushes_and_extends_crit_range(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Tauros")
        attacker_spec.abilities = [{"name": "Gore"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Horn Attack",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        grid = GridState(width=3, height=1)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(1, 0)),
            },
            grid=grid,
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Horn Attack", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].position, (2, 0))
        self.assertTrue(
            any(
                evt.get("ability") == "Gore" and evt.get("effect") == "crit_range"
                for evt in battle.log
            )
        )

    def test_grass_pelt_reduces_damage_on_grassy_rough_tile(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        defender_spec = _pokemon_spec("Gogoat")
        defender_spec.abilities = [{"name": "Grass Pelt"}]
        grid = GridState(width=1, height=2, tiles={(0, 0): {"type": "rough grass"}})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            grid=grid,
            rng=FixedRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Gogoat"), controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            grid=grid,
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="gary-1", move_name="Tackle", target_id="ash-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["ash-1"].max_hp() - (battle.pokemon["ash-1"].hp or 0)
        damage_without = baseline.pokemon["ash-1"].max_hp() - (baseline.pokemon["ash-1"].hp or 0)
        self.assertLess(damage_with, damage_without)

    def test_gulp_heals_and_removes_injury(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Wailord")
        attacker_spec.abilities = [{"name": "Gulp"}]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker.injuries = 1
        max_hp = attacker.max_hp()
        attacker.hp = max(1, max_hp - 20)
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker,
                "gary-1": PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(0, 1)),
            },
        )
        before_hp = attacker.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Gulp"))
        battle.resolve_next_action()
        expected_heal = int(max_hp * 0.25)
        expected_hp = min(max_hp, before_hp + expected_heal)
        self.assertEqual(attacker.hp, expected_hp)
        self.assertEqual(attacker.injuries, 0)

    def test_guts_boosts_attack_while_afflicted(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Machop")
        spec.abilities = [{"name": "Guts"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.statuses.append({"name": "Burned"})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state})
        state._handle_ability_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.combat_stages["atk"], 2)
        state.remove_status_by_names({"burned"})
        state._handle_ability_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.combat_stages["atk"], 0)

    def test_harvest_preserves_berry_buff_on_heads(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 1

        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Tropius")
        spec.abilities = [{"name": "Harvest"}]
        spec.items = [{"name": "Oran Berry"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state}, rng=FixedRNG())
        events: List[dict] = []
        battle._consume_food_buff("ash-1", state, 0, "heal", "Heals.", events)
        self.assertEqual(len(state.food_buffs), 1)
        self.assertFalse(state.get_temporary_effects("harvest_failed"))

    def test_harvest_consumes_berry_buff_on_tails(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 2

        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Tropius")
        spec.abilities = [{"name": "Harvest"}]
        spec.items = [{"name": "Oran Berry"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier)
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": state}, rng=FixedRNG())
        events: List[dict] = []
        battle._consume_food_buff("ash-1", state, 0, "heal", "Heals.", events)
        self.assertEqual(len(state.food_buffs), 0)
        self.assertTrue(state.get_temporary_effects("harvest_failed"))

    def test_haunt_boosts_ghost_damage_under_last_chance(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Misdreavus")
        attacker_spec.abilities = [{"name": "Haunt"}]
        attacker_spec.moves = [
            MoveSpec(
                name="Shadow Claw",
                type="Ghost",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
            )
        ]
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker.hp = max(1, attacker.max_hp() // 3)
        defender_spec = _pokemon_spec("Rattata")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker,
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=_pokemon_spec("Misdreavus"), controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        baseline.pokemon["ash-1"].spec.moves = list(attacker_spec.moves)
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shadow Claw", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shadow Claw", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertGreater(damage_with, damage_without)

    def test_hay_fever_triggers_on_status_move(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Shaymin")
        attacker_spec.abilities = [{"name": "Hay Fever"}]
        attacker_spec.moves = [MoveSpec(name="Growl", type="Normal", category="Status", ac=None)]
        target_spec = _pokemon_spec("Rattata")
        bug_spec = _pokemon_spec("Caterpie")
        bug_spec.types = ["Bug"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=target_spec, controller_id=foe.identifier, position=(1, 0)),
                "gary-2": PokemonState(spec=bug_spec, controller_id=foe.identifier, position=(1, 1)),
            },
        )
        before_hp = battle.pokemon["gary-1"].hp
        bug_before = battle.pokemon["gary-2"].hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Growl", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertLess(battle.pokemon["gary-1"].hp, before_hp)
        self.assertEqual(battle.pokemon["gary-2"].hp, bug_before)

    def test_ice_body_heals_and_ignores_hail(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Eevee")
        spec.types = ["Normal"]
        spec.abilities = [{"name": "Ice Body"}]
        state = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        state.hp = state.max_hp() - state.tick_value()
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": state},
            weather="Hail",
        )
        before_hp = state.hp
        events = state.handle_phase_effects(battle, TurnPhase.START, "ash-1")
        self.assertEqual(state.hp, before_hp + state.tick_value())
        self.assertFalse(any(evt.get("effect") == "hail_damage" for evt in events))

    def test_ice_shield_places_blocking_segments(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Glaceon")
        spec.abilities = [{"name": "Ice Shield"}]
        grid = GridState(width=3, height=3)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={
                "ash-1": PokemonState(spec=spec, controller_id=trainer.identifier, position=(1, 1)),
            },
            grid=grid,
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ice Shield"))
        battle.resolve_next_action()
        self.assertTrue(grid.blockers)
        self.assertLessEqual(len(grid.blockers), 3)
        self.assertTrue(
            any(grid.tiles[coord].get("type") == "ice_shield" for coord in grid.blockers)
        )

    def test_ignition_boost_adds_damage_for_adjacent_fire_move(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return min(10, _b)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Vulpix")
        attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=4,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
            )
        ]
        ally_spec = _pokemon_spec("Magby")
        ally_spec.abilities = [{"name": "Ignition Boost"}]
        defender_spec = _pokemon_spec("Rattata")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "ash-2": PokemonState(spec=ally_spec, controller_id=trainer.identifier, position=(0, 1)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(2, 0)),
            },
            rng=FixedRNG(),
        )
        baseline = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(2, 0)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        baseline.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        baseline.resolve_next_action()
        damage_with = battle.pokemon["gary-1"].max_hp() - (battle.pokemon["gary-1"].hp or 0)
        damage_without = baseline.pokemon["gary-1"].max_hp() - (baseline.pokemon["gary-1"].hp or 0)
        self.assertEqual(damage_with, damage_without + 5)

    def test_illuminate_accuracy_penalty_respects_blindsense(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgey")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=4,
                ac=4,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
            )
        ]
        defender_spec = _pokemon_spec("Chinchou")
        defender_spec.abilities = [{"name": "Illuminate"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(any(evt.get("ability") == "Illuminate" for evt in battle.log))
        attacker_spec.capabilities = ["Blindsense"]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(any(evt.get("ability") == "Illuminate" for evt in battle.log))

    def test_illusion_marks_shift_and_breaks_on_damage(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Zorua")
        attacker_spec.abilities = [{"name": "Illusion"}]
        attacker_spec.skills = {"focus": 2}
        attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        defender = PokemonState(spec=_pokemon_spec("Rattata"), controller_id=foe.identifier, position=(1, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker, "gary-1": defender},
        )
        mark_move = battle._find_known_move(attacker, "Illusion Mark")
        shift_move = battle._find_known_move(attacker, "Illusion Shift")
        self.assertIsNotNone(mark_move)
        self.assertIsNotNone(shift_move)
        battle.resolve_move_targets(
            attacker_id="ash-1",
            move=mark_move,
            target_id="gary-1",
            target_position=defender.position,
        )
        battle.resolve_move_targets(
            attacker_id="ash-1",
            move=shift_move,
            target_id="gary-1",
            target_position=defender.position,
        )
        self.assertTrue(attacker.get_temporary_effects("illusion_active"))
        hit_move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        battle.resolve_move_targets(
            attacker_id="gary-1",
            move=hit_move,
            target_id="ash-1",
            target_position=attacker.position,
        )
        self.assertFalse(attacker.get_temporary_effects("illusion_active"))

    def test_immunity_blocks_poison_status(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Oddish")
        attacker_spec.moves = [MoveSpec(name="Poison Powder", type="Poison", category="Status", ac=None)]
        defender_spec = _pokemon_spec("Snorlax")
        defender_spec.abilities = [{"name": "Immunity"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Poison Powder", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["gary-1"].has_status("Poisoned"))

    def test_impostor_copies_stages_and_ability_on_entry(self) -> None:
        class FixedRNG(random.Random):
            def choice(self, seq):  # type: ignore[override]
                return seq[0]

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        ditto_spec = _pokemon_spec("Ditto")
        ditto_spec.abilities = [{"name": "Impostor"}]
        foe_spec = _pokemon_spec("Gengar")
        foe_spec.abilities = [{"name": "Levitate"}]
        foe_state = PokemonState(spec=foe_spec, controller_id=foe.identifier, position=(1, 0))
        foe_state.combat_stages["atk"] = 2
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=ditto_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": foe_state,
            },
            rng=FixedRNG(),
        )
        battle.start_round()
        ditto = battle.pokemon["ash-1"]
        self.assertEqual(ditto.combat_stages.get("atk"), 2)
        entrained = ditto.get_temporary_effects("entrained_ability")
        self.assertTrue(entrained)
        self.assertEqual(entrained[-1].get("ability"), "Levitate")

    def test_infiltrator_bypasses_substitute_for_status_moves(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Zubat")
        attacker_spec.abilities = [{"name": "Infiltrator"}]
        attacker_spec.moves = [MoveSpec(name="Growl", type="Normal", category="Status", ac=None)]
        defender_spec = _pokemon_spec("Rattata")
        defender = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        defender.statuses.append({"name": "Substitute"})
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": defender,
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Growl", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender.combat_stages["atk"], -1)

    def test_inner_focus_blocks_flinch(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 1

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Zigzagoon")
        attacker_spec.moves = [
            MoveSpec(
                name="Bite",
                type="Dark",
                category="Physical",
                db=6,
                ac=None,
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
            )
        ]
        defender_spec = _pokemon_spec("Lucario")
        defender_spec.abilities = [{"name": "Inner Focus"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Bite", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["gary-1"].has_status("Flinch"))

    def test_insomnia_blocks_rest(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Noctowl")
        spec.abilities = [{"name": "Insomnia"}]
        spec.moves = [MoveSpec(name="Rest", type="Psychic", category="Status", ac=None)]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={
                "ash-1": PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0)),
            },
        )
        battle.advance_turn()
        with self.assertRaises(ValueError):
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Rest"))

    def test_instinct_increases_evasion(self) -> None:
        spec = _pokemon_spec("Stantler")
        spec.abilities = [{"name": "Instinct"}]
        instinct_mon = PokemonState(spec=spec, controller_id="ash")
        baseline = PokemonState(spec=_pokemon_spec("Stantler"), controller_id="ash")
        self.assertEqual(
            evasion_value(instinct_mon, "physical"),
            evasion_value(baseline, "physical") + 2,
        )

    def test_interference_applies_accuracy_penalty(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Electrode")
        attacker_spec.abilities = [{"name": "Interference"}]
        defender_spec = _pokemon_spec("Rattata")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(2, 0)),
                "gary-2": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(3, 0)),
            },
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Interference"))
        battle.resolve_next_action()
        for pid in ("gary-1", "gary-2"):
            effects = battle.pokemon[pid].get_temporary_effects("accuracy_penalty")
            self.assertTrue(effects)
            self.assertEqual(effects[-1].get("amount"), 2)

    def test_disguise_blocks_damage_and_boosts(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machop")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Mimikyu")
        defender_spec.abilities = [{"name": "Disguise"}]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        defender_state = PokemonState(
            spec=defender_spec, controller_id=foe.identifier, position=(0, 1)
        )
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
        )
        before_hp = defender_state.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(defender_state.hp, before_hp)
        self.assertEqual(defender_state.combat_stages.get("def"), 1)
        self.assertTrue(defender_state.get_temporary_effects("disguise_used"))

    def test_emergency_exit_forces_switch(self) -> None:
        class MidRNG(random.Random):
            def randint(self, _a: int, _b: int) -> int:
                return 10

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Machamp")
        attacker_spec.atk = 12
        attacker_spec.moves = [
            MoveSpec(
                name="Giga Impact",
                type="Normal",
                category="Physical",
                db=8,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="Daily",
            )
        ]
        defender_spec = _pokemon_spec("Golisopod")
        defender_spec.abilities = [{"name": "Emergency Exit"}]
        bench_spec = _pokemon_spec("Wimpod")
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=foe.identifier, position=(0, 1)
        )
        defender_state = PokemonState(
            spec=defender_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        bench_state = PokemonState(
            spec=bench_spec, controller_id=trainer.identifier, position=None
        )
        bench_state.active = False
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": defender_state,
                "ash-2": bench_state,
                "gary-1": attacker_state,
            },
            rng=MidRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Giga Impact", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(defender_state.active)
        self.assertTrue(bench_state.active)

    def test_poison_touch_poison_on_contact(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pikachu")
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=4,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Grimer")
        defender_spec.abilities = [{"name": "Poison Touch"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["ash-1"].has_status("Poisoned"))
        self.assertTrue(any(evt.get("ability") == "Poison Touch" for evt in battle.log))

    def test_sweet_veil_blocks_sleep(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Foongus")
        attacker_spec.moves = [
            MoveSpec(
                name="Spore",
                type="Grass",
                category="Status",
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        target_spec = _pokemon_spec("Eevee")
        veil_spec = _pokemon_spec("Slurpuff")
        veil_spec.abilities = [{"name": "Sweet Veil"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=target_spec, controller_id=trainer.identifier, position=(1, 0)),
                "ash-2": PokemonState(spec=veil_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(1, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Spore", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].has_status("Sleep"))
        self.assertTrue(
            any(
                evt.get("ability") == "Sweet Veil" and evt.get("effect") == "status_block"
                for evt in battle.log
            )
        )

    def test_water_veil_blocks_burn(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Vulpix")
        attacker_spec.moves = [
            MoveSpec(
                name="Will-O-Wisp",
                type="Fire",
                category="Status",
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Horsea")
        defender_spec.abilities = [{"name": "Water Veil"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Will-O-Wisp", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].has_status("Burned"))
        self.assertTrue(any(evt.get("ability") == "Water Veil" for evt in battle.log))

    def test_thick_fat_resists_fire(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=6,
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Snorlax")
        defender_spec.abilities = [{"name": "Thick Fat"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Ember", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertTrue(
            any(
                evt.get("ability") == "Thick Fat" and evt.get("effect") == "type_resist" and evt.get("to_multiplier") == 0.5
                for evt in battle.log
            )
        )

    def test_tough_claws_adds_melee_power(self) -> None:
        attacker_spec = _pokemon_spec("Zangoose")
        attacker_spec.abilities = [{"name": "Tough Claws"}]
        defender_spec = _pokemon_spec("Eevee")
        attacker = PokemonState(spec=attacker_spec, controller_id="ash")
        defender = PokemonState(spec=defender_spec, controller_id="gary")
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=None,
            range_kind="Melee",
            range_value=1,
            freq="At-Will",
        )
        context = build_attack_context(attacker, defender, move, weather=None, terrain=None)
        self.assertTrue(any(mod.slug == "tough-claws" and mod.value == 2 for mod in context.modifiers))

    def test_moonlight_heals_more_in_sun(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Clefairy")
        spec.moves = [
            MoveSpec(name="Moonlight", type="Fairy", category="Status", ac=None, range_kind="Self")
        ]
        mon = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": mon},
            rng=FixedRNG(),
        )
        battle.weather = "Sunny"
        mon.hp = max(1, mon.max_hp() // 4)
        before = mon.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Moonlight"))
        battle.resolve_next_action()
        expected = min(mon.max_hp(), before + (mon.max_hp() * 2 // 3))
        self.assertEqual(mon.hp, expected)
        self.assertTrue(any(evt.get("effect") == "moonlight" for evt in battle.log))

    def test_morning_sun_heals_less_in_rain(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Bellossom")
        spec.moves = [
            MoveSpec(name="Morning Sun", type="Normal", category="Status", ac=None, range_kind="Self")
        ]
        mon = PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": mon},
            rng=FixedRNG(),
        )
        battle.weather = "Rainy"
        mon.hp = max(1, mon.max_hp() // 4)
        before = mon.hp
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Morning Sun"))
        battle.resolve_next_action()
        expected = min(mon.max_hp(), before + (mon.max_hp() // 4))
        self.assertEqual(mon.hp, expected)
        self.assertTrue(any(evt.get("effect") == "morning_sun" for evt in battle.log))

    def test_mountain_gale_flinches_on_15(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 15)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Avalugg")
        attacker_spec.moves = [
            MoveSpec(
                name="Mountain Gale",
                type="Ice",
                category="Physical",
                db=10,
                ac=None,
                range_kind="Melee",
                range_value=1,
                freq="EOT",
            )
        ]
        defender_spec = _pokemon_spec("Pidgey")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mountain Gale", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Flinched"))

    def test_mud_bomb_lowers_accuracy_on_16(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 16)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Mudkip")
        attacker_spec.moves = [
            MoveSpec(
                name="Mud Bomb",
                type="Ground",
                category="Special",
                db=7,
                ac=4,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mud Bomb", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("accuracy"), -1)

    def test_mud_shot_lowers_speed(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Mudkip")
        attacker_spec.moves = [
            MoveSpec(
                name="Mud Shot",
                type="Ground",
                category="Special",
                db=6,
                ac=3,
                range_kind="Ranged",
                range_value=3,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mud Shot", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("spd"), -1)

    def test_white_smoke_blocks_stage_drop(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 20)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rattata")
        attacker_spec.moves = [
            MoveSpec(
                name="Tail Whip",
                type="Normal",
                category="Status",
                ac=2,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Torkoal")
        defender_spec.abilities = [{"name": "White Smoke"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tail Whip", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("def"), 0)
        self.assertTrue(any(evt.get("ability") == "White Smoke" for evt in battle.log))

    def test_wonder_skin_penalizes_status_accuracy(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 20)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Pidgey")
        attacker_spec.moves = [
            MoveSpec(
                name="Tail Whip",
                type="Normal",
                category="Status",
                ac=2,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Skitty")
        defender_spec.abilities = [{"name": "Wonder Skin"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tail Whip", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(
            any(
                evt.get("ability") == "Wonder Skin" and evt.get("effect") == "accuracy_penalty" and evt.get("amount") == -6
                for evt in battle.log
            )
        )

    def test_prism_armor_reduces_super_effective_damage(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 15)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Charmander")
        attacker_spec.moves = [
            MoveSpec(
                name="Ember",
                type="Fire",
                category="Special",
                db=8,
                ac=2,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Bulbasaur")
        defender_spec.types = ["Grass"]
        defender_spec.abilities = [{"name": "Prism Armor"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(
            any(
                evt.get("ability") == "Prism Armor" and evt.get("effect") == "resist" and evt.get("amount") == 5
                for evt in battle.log
            )
        )

    def test_water_bubble_blocks_burn(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Vulpix")
        attacker_spec.moves = [
            MoveSpec(
                name="Will-O-Wisp",
                type="Fire",
                category="Status",
                ac=None,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Araquanid")
        defender_spec.abilities = [{"name": "Water Bubble"}]
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=defender_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=attacker_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="gary-1", move_name="Will-O-Wisp", target_id="ash-1"))
        battle.resolve_next_action()
        self.assertFalse(battle.pokemon["ash-1"].has_status("Burned"))
        self.assertTrue(any(evt.get("ability") == "Water Bubble" for evt in battle.log))

    def test_punk_rock_adds_sonic_power(self) -> None:
        attacker_spec = _pokemon_spec("Noivern")
        attacker_spec.abilities = [{"name": "Punk Rock"}]
        defender_spec = _pokemon_spec("Eevee")
        attacker = PokemonState(spec=attacker_spec, controller_id="ash")
        defender = PokemonState(spec=defender_spec, controller_id="gary")
        move = MoveSpec(
            name="Echoed Voice",
            type="Normal",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            freq="At-Will",
            keywords=["Sonic"],
        )
        context = build_attack_context(attacker, defender, move, weather=None, terrain=None)
        self.assertTrue(any(mod.slug == "punk-rock" and mod.value == 2 for mod in context.modifiers))

    def test_mud_slap_lowers_accuracy(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Sandshrew")
        attacker_spec.moves = [
            MoveSpec(
                name="Mud-Slap",
                type="Ground",
                category="Special",
                db=2,
                ac=2,
                range_kind="Ranged",
                range_value=3,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mud-Slap", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("accuracy"), -1)

    def test_muddy_water_lowers_accuracy_on_16(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 16)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Squirtle")
        attacker_spec.moves = [
            MoveSpec(
                name="Muddy Water",
                type="Water",
                category="Special",
                db=8,
                ac=4,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Muddy Water", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("accuracy"), -1)

    def test_mystical_fire_lowers_spatk(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Delphox")
        attacker_spec.moves = [
            MoveSpec(
                name="Mystical Fire",
                type="Fire",
                category="Special",
                db=7,
                ac=4,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mystical Fire", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("spatk"), -1)

    def test_mystical_power_raises_best_stat(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Meowstic")
        spec.spatk = 12
        spec.spdef = 18
        spec.moves = [
            MoveSpec(
                name="Mystical Power",
                type="Psychic",
                category="Special",
                db=6,
                ac=2,
                range_kind="Ranged",
                range_value=6,
                freq="At-Will",
            )
        ]
        foe = TrainerState(identifier="gary", name="Gary")
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Mystical Power", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].combat_stages.get("spdef"), 1)

    def test_night_daze_lowers_accuracy_on_13(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 13)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Zoroark")
        attacker_spec.moves = [
            MoveSpec(
                name="Night Daze",
                type="Dark",
                category="Special",
                db=7,
                ac=3,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Night Daze", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("accuracy"), -1)

    def test_white_flame_adds_damage_while_enraged(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Rapidash")
        attacker_spec.atk = 14
        attacker_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                db=6,
                ac=2,
                range_kind="Melee",
                range_value=1,
                freq="At-Will",
            )
        ]
        attacker_spec.abilities = [{"name": "White Flame"}]
        defender_spec = _pokemon_spec("Eevee")
        attacker_state = PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0))
        attacker_state.statuses.append({"name": "Enraged"})
        defender_state = PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(
            any(evt.get("ability") == "White Flame" and evt.get("amount") == 5 for evt in battle.log)
        )

    def test_nasty_plot_raises_spatk(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Houndour")
        spec.moves = [
            MoveSpec(
                name="Nasty Plot",
                type="Dark",
                category="Status",
                ac=None,
                range_kind="Self",
                freq="EOT",
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))},
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Nasty Plot"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].combat_stages.get("spatk"), 2)

    def test_needle_arm_flinches_on_15(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 15)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Cacturne")
        attacker_spec.moves = [
            MoveSpec(
                name="Needle Arm",
                type="Grass",
                category="Physical",
                db=6,
                ac=2,
                range_kind="Melee",
                range_value=1,
                freq="At-Will",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Needle Arm", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Flinched"))

    def test_rock_tomb_lowers_speed(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 10)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Geodude")
        attacker_spec.moves = [
            MoveSpec(
                name="Rock Tomb",
                type="Rock",
                category="Physical",
                db=6,
                ac=5,
                range_kind="Ranged",
                range_value=6,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Rock Tomb", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("spd"), -1)

    def test_rolling_kick_flinches_on_15(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 15)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Hitmonlee")
        attacker_spec.moves = [
            MoveSpec(
                name="Rolling Kick",
                type="Fighting",
                category="Physical",
                db=6,
                ac=4,
                range_kind="Melee",
                range_value=1,
                freq="Scene",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Rolling Kick", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Flinched"))

    def test_sharpen_raises_attack(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Sandslash")
        spec.moves = [
            MoveSpec(
                name="Sharpen",
                type="Normal",
                category="Status",
                ac=None,
                range_kind="Self",
                freq="Scene",
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))},
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Sharpen"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["ash-1"].combat_stages.get("atk"), 1)

    def test_shadow_bone_lowers_def_on_17(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 17)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Marowak")
        attacker_spec.moves = [
            MoveSpec(
                name="Shadow Bone",
                type="Ghost",
                category="Physical",
                db=9,
                ac=2,
                range_kind="Melee",
                range_value=1,
                freq="EOT",
            )
        ]
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)),
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Shadow Bone", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertEqual(battle.pokemon["gary-1"].combat_stages.get("def"), -1)

    def test_snore_requires_sleep(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        spec = _pokemon_spec("Snorlax")
        spec.moves = [
            MoveSpec(
                name="Snore",
                type="Normal",
                category="Special",
                db=5,
                ac=2,
                range_kind="Burst",
                range_value=1,
                freq="EOT",
                keywords=["Sonic"],
            )
        ]
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": PokemonState(spec=spec, controller_id=trainer.identifier, position=(0, 0))},
        )
        battle.advance_turn()
        with self.assertRaises(ValueError):
            battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Snore"))

    def test_snore_flinches_on_15(self) -> None:
        class FixedRNG(random.Random):
            def randint(self, a: int, b: int) -> int:
                return min(b, 15)

        trainer = TrainerState(identifier="ash", name="Ash")
        foe = TrainerState(identifier="gary", name="Gary")
        attacker_spec = _pokemon_spec("Snorlax")
        attacker_spec.moves = [
            MoveSpec(
                name="Snore",
                type="Normal",
                category="Special",
                db=5,
                ac=2,
                range_kind="Burst",
                range_value=1,
                freq="EOT",
                keywords=["Sonic"],
            )
        ]
        attacker_state = PokemonState(
            spec=attacker_spec, controller_id=trainer.identifier, position=(0, 0)
        )
        attacker_state.statuses.append({"name": "Sleep"})
        defender_spec = _pokemon_spec("Pikachu")
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={
                "ash-1": attacker_state,
                "gary-1": PokemonState(spec=defender_spec, controller_id=foe.identifier, position=(0, 1)),
            },
            rng=FixedRNG(),
        )
        battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Snore", target_id="gary-1"))
        battle.resolve_next_action()
        self.assertTrue(battle.pokemon["gary-1"].has_status("Flinched"))
