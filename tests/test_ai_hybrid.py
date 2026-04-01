import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.ai import aai_port
from auto_ptu.rules import BattleState, GridState, PokemonState, ShiftAction, UseMoveAction
from auto_ptu.rules.battle_state import _load_maneuver_moves
from auto_ptu.rules import ai_hybrid, ai


def _make_mon(name: str, *, hp: int = 20, atk: int = 10, defense: int = 10, spd: int = 10, moves=None):
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=hp,
        atk=atk,
        defense=defense,
        spatk=atk,
        spdef=defense,
        spd=spd,
        moves=moves or [],
    )


class HybridAITests(unittest.TestCase):
    def test_aai_port_tendencies(self) -> None:
        defend = aai_port.protect_tendency({"attack": 2.0, "defend": 6.0, "other": 0.0})
        retreat = aai_port.retreat_tendency({"retreats": 5.0, "stays_in_danger": 1.0})
        self.assertGreater(defend, 0.7)
        self.assertGreater(retreat, 0.8)

    def test_aai_port_adaptive_adjustment_rewards_hazard_when_retreat_likely(self) -> None:
        hazard = MoveSpec(
            name="Stealth Rocks",
            type="Rock",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            keywords=["Hazard"],
            effects_text="Sets a lingering hazard on the field.",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=8, moves=[hazard, tackle]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=20, moves=[tackle]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(9),
        )
        battle.start_round()
        store = ai_hybrid.ProfileStore()
        sig = ai_hybrid._actor_signature(battle, "b-1")
        profile = store.profile_for(sig)
        profile.risk_tolerance["retreats"] = 9.0
        profile.risk_tolerance["stays_in_danger"] = 1.0
        hazard_action = UseMoveAction(actor_id="a-1", move_name="Stealth Rocks", target_id="b-1")
        tackle_action = UseMoveAction(actor_id="a-1", move_name="Tackle", target_id="b-1")
        base = [
            (ai_hybrid.score_action(battle, "a-1", hazard_action), hazard_action),
            (ai_hybrid.score_action(battle, "a-1", tackle_action), tackle_action),
        ]
        strategic = ai_hybrid._apply_aai_port_adjustments(
            battle,
            "a-1",
            base,
            store,
            ai_level="strategic",
        )
        standard = ai_hybrid._apply_aai_port_adjustments(
            battle,
            "a-1",
            base,
            store,
            ai_level="standard",
        )
        strategic_scores = {entry[1].move_name: entry[0] for entry in strategic if isinstance(entry[1], UseMoveAction)}
        standard_scores = {entry[1].move_name: entry[0] for entry in standard if isinstance(entry[1], UseMoveAction)}
        self.assertGreater(strategic_scores["Stealth Rocks"], standard_scores["Stealth Rocks"])
        self.assertGreaterEqual(strategic_scores["Tackle"], standard_scores["Tackle"] - 0.25)

    def test_determinism_same_seed(self) -> None:
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[tackle]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", moves=[tackle]), controller_id="b", position=(1, 2))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=5, height=5),
            rng=random.Random(1),
        )
        battle.start_round()
        action1, _ = ai_hybrid.choose_action(battle, "a-1")
        battle2 = ai_hybrid._clone_battle(battle)
        action2, _ = ai_hybrid.choose_action(battle2, "a-1")
        self.assertEqual(type(action1), type(action2))
        if isinstance(action1, UseMoveAction) and isinstance(action2, UseMoveAction):
            self.assertEqual(action1.move_name, action2.move_name)
            self.assertEqual(action1.target_id, action2.target_id)

    def test_generate_candidates_legal(self) -> None:
        move = MoveSpec(
            name="Punch",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[move]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", moves=[move]), controller_id="b", position=(3, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(2),
        )
        battle.start_round()
        candidates = ai_hybrid.generate_candidates(battle, "a-1")
        for action in candidates:
            action.validate(battle)

    def test_profile_updates(self) -> None:
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[move]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", moves=[move]), controller_id="b", position=(1, 2))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        battle.start_round()
        store = ai_hybrid.ProfileStore()
        action = UseMoveAction(actor_id="a-1", move_name="Tackle", target_id="b-1")
        ai_hybrid.observe_action(battle, "a-1", action, store=store)
        profile = store.profile_for(ai_hybrid._actor_signature(battle, "a-1"))
        self.assertGreater(profile.action_type.get("attack", 0.0), 0.0)
        self.assertGreater(profile.move_usage.get("Tackle", 0.0), 0.0)

    def test_lookahead_defensive_choice(self) -> None:
        weak = MoveSpec(
            name="Peck",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        strong = MoveSpec(
            name="Mega Punch",
            type="Normal",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        actor_spec = _make_mon("Actor", hp=5, defense=6, moves=[weak])
        foe_spec = _make_mon("Foe", atk=18, moves=[strong])
        actor = PokemonState(spec=actor_spec, controller_id="a", position=(2, 2))
        foe = PokemonState(spec=foe_spec, controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(4),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)

    def test_prefers_one_self_setup_before_closing_distance(self) -> None:
        setup = MoveSpec(
            name="Agility",
            type="Psychic",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_value=0,
            target_kind="Self",
            target_range=0,
            effects_text="Raise the user's Speed Combat Stages by +2.",
        )
        ranged = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[setup, ranged], spd=12), controller_id="a", position=(0, 0))
        foe = PokemonState(spec=_make_mon("Foe", moves=[ranged]), controller_id="b", position=(9, 9))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=12, height=12),
            rng=random.Random(17),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Agility")
        self.assertEqual(info.get("reason"), "pre_engage_setup")

    def test_does_not_treat_self_debuff_status_as_setup(self) -> None:
        bad_setup = MoveSpec(
            name="Tail Whip",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Burst",
            range_value=1,
            target_kind="Self",
            target_range=0,
            area_kind="Burst",
            area_value=1,
            effects_text="Tail Whip lowers Defense.",
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[bad_setup]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", moves=[]), controller_id="b", position=(5, 5))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=8, height=8),
            rng=random.Random(18),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertFalse(any(isinstance(candidate, UseMoveAction) and candidate.move_name == "Tail Whip" for candidate in ai_hybrid.generate_candidates(battle, "a-1")))
        if isinstance(action, UseMoveAction):
            self.assertNotEqual(action.move_name, "Tail Whip")

    def test_generate_candidates_skips_harmful_friendly_fire_move(self) -> None:
        smog = MoveSpec(
            name="Smog",
            type="Poison",
            category="Special",
            db=3,
            ac=2,
            range_kind="Ranged",
            range_value=4,
            target_kind="Ally",
            target_range=4,
            effects_text="Inflicts Poisoned on the target on an even roll.",
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=10, moves=[smog]), controller_id="a", position=(2, 2))
        ally = PokemonState(spec=_make_mon("Ally"), controller_id="a", position=(2, 3))
        foe = PokemonState(spec=_make_mon("Foe"), controller_id="b", position=(4, 4))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "a-2": ally, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(17),
        )
        battle.start_round()

        candidates = ai_hybrid.generate_candidates(battle, "a-1")
        self.assertFalse(
            any(
                isinstance(action, UseMoveAction)
                and action.move_name == "Smog"
                and action.target_id in {"a-1", "a-2"}
                for action in candidates
            )
        )

    def test_prefers_non_struggle_damage_when_available(self) -> None:
        struggle = MoveSpec(
            name="Struggle",
            type="Typeless",
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
        actor = PokemonState(spec=_make_mon("Actor", moves=[struggle, tackle]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", moves=[tackle]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(5),
        )
        battle.start_round()
        action, _ = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Tackle")

    def test_stale_prefers_non_struggle_damaging_move(self) -> None:
        struggle = MoveSpec(
            name="Struggle",
            type="Typeless",
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
        actor = PokemonState(spec=_make_mon("Actor", moves=[struggle, tackle]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", moves=[tackle]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(6),
        )
        battle.start_round()
        battle.log.append({"type": "move", "actor": "a-1", "move": "Tackle", "damage": 0})
        battle.log.append({"type": "move", "actor": "a-1", "move": "Tackle", "damage": 0})
        action, _ = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Tackle")

    def test_stale_uses_struggle_as_last_resort(self) -> None:
        growl = MoveSpec(
            name="Growl",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
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
        actor = PokemonState(spec=_make_mon("Actor", moves=[growl]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", moves=[tackle]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            rng=random.Random(7),
        )
        battle.start_round()
        battle.log.append({"type": "move", "actor": "a-1", "move": "Growl", "damage": 0})
        battle.log.append({"type": "move", "actor": "a-1", "move": "Growl", "damage": 0})
        action, _ = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Struggle")

    def test_stale_prefers_struggle_over_shift_when_attack_deals_no_damage(self) -> None:
        wrap = MoveSpec(
            name="Wrap",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=1, moves=[wrap]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=50, moves=[wrap]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(17),
        )
        battle.start_round()
        battle.log.append({"type": "move", "actor": "a-1", "move": "Wrap", "damage": 0})
        battle.log.append({"type": "move", "actor": "a-1", "move": "Wrap", "damage": 0})
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Struggle")
        self.assertEqual(info.get("reason"), "stale_ineffective_struggle")

    def test_stale_does_not_loop_into_switch_when_attack_is_available(self) -> None:
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[tackle]), controller_id="a", position=(2, 2))
        bench = PokemonState(spec=_make_mon("Bench", moves=[tackle]), controller_id="a", position=(0, 0))
        foe = PokemonState(spec=_make_mon("Foe", moves=[tackle]), controller_id="b", position=(2, 3))
        bench.active = False
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "a-2": bench, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(18),
        )
        battle.start_round()
        battle.log.append({"type": "action", "actor": "a-1", "action_type": "switch"})
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Tackle")
        self.assertNotEqual(info.get("reason"), "stale_switch")

    def test_reaction_only_move_is_not_used_proactively(self) -> None:
        counter = MoveSpec(
            name="Counter",
            type="Fighting",
            category="Physical",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            effects_text="Trigger: The user is damaged by a Physical damaging attack.",
        )
        actor = PokemonState(spec=_make_mon("Wobbuffet", moves=[counter]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe"), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(8),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertFalse(isinstance(action, UseMoveAction) and action.move_name == "Counter")
        self.assertNotEqual(info.get("reason"), "attack_in_range")

    def test_wrap_description_bonus_prefers_wrap_before_plain_attack(self) -> None:
        wrap = MoveSpec(
            name="Wrap",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Wrap deals a tick of damage when gaining dominance in a grapple.",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[wrap, tackle]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", moves=[tackle]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(19),
        )
        battle.start_round()
        action, _ = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Wrap")

    def test_grapple_maneuver_gets_bonus_after_recent_wrap(self) -> None:
        actor = PokemonState(spec=_make_mon("Actor"), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe"), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(20),
        )
        battle.start_round()
        grapple = _load_maneuver_moves()["grapple"]
        base_score = ai_hybrid._score_maneuver_action(battle, "a-1", grapple, foe)
        battle.log.append({"type": "move", "actor": "a-1", "move": "Wrap", "damage": 3})
        boosted_score = ai_hybrid._score_maneuver_action(battle, "a-1", grapple, foe)
        self.assertGreater(boosted_score, base_score)

    def test_legacy_rules_ai_reaction_only_move_is_not_used_proactively(self) -> None:
        counter = MoveSpec(
            name="Counter",
            type="Fighting",
            category="Physical",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            effects_text="This text is intentionally sparse.",
        )
        actor = PokemonState(spec=_make_mon("Wobbuffet", moves=[counter]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe"), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(13),
        )
        battle.start_round()
        original = ai._USE_HYBRID_AI
        ai._USE_HYBRID_AI = False
        try:
            move, target_id, _score = ai.choose_best_move(battle, "a-1", ai_level="standard")
            self.assertIsNotNone(move)
            assert move is not None
            self.assertEqual(move.name, "Struggle")
            self.assertEqual(target_id, "b-1")
        finally:
            ai._USE_HYBRID_AI = original

    def test_generate_candidates_excludes_noop_shift(self) -> None:
        actor = PokemonState(spec=_make_mon("Actor"), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe"), controller_id="b", position=(5, 5))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(10),
        )
        battle.start_round()
        candidates = ai_hybrid.generate_candidates(battle, "a-1")
        self.assertFalse(
            any(isinstance(action, ShiftAction) and action.destination == (2, 2) for action in candidates)
        )

    def test_generate_candidates_include_battle_maneuver_in_melee(self) -> None:
        actor = PokemonState(spec=_make_mon("Actor"), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe"), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(11),
        )
        battle.start_round()
        candidates = ai_hybrid.generate_candidates(battle, "a-1")
        maneuver_names = {
            action.move_name
            for action in candidates
            if isinstance(action, UseMoveAction)
        }
        self.assertIn("Trip", maneuver_names)

    def test_opening_can_choose_setup_status_over_weak_damage(self) -> None:
        setup = MoveSpec(
            name="Howl",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_value=0,
            target_kind="Self",
            target_range=0,
            effects_text="Raises the user's Attack Combat Stage by +2.",
        )
        weak_hit = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=1,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=10, moves=[setup, weak_hit]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=18, moves=[weak_hit]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(8),
        )
        battle.start_round()
        action, _ = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Howl")

    def test_generate_candidates_includes_conversion_with_chosen_type(self) -> None:
        conversion = MoveSpec(
            name="Conversion",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
            target_kind="Self",
            target_range=0,
        )
        psybeam = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=7,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Porygon2", moves=[conversion, psybeam]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Machoke", moves=[psybeam]), controller_id="b", position=(2, 4))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(44),
        )
        battle.start_round()

        candidates = ai_hybrid.generate_candidates(battle, "a-1")
        conversion_actions = [
            action for action in candidates
            if isinstance(action, UseMoveAction) and action.move_name == "Conversion"
        ]
        self.assertTrue(conversion_actions)
        self.assertTrue(any(action.chosen_type for action in conversion_actions))

    def test_choose_action_can_prefer_conversion2_after_typed_hit(self) -> None:
        conversion2 = MoveSpec(
            name="Conversion2",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
            target_kind="Self",
            target_range=0,
            effects_text="Conversion2 changes the user's type.",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        ember = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Porygon2", moves=[conversion2, tackle], defense=18), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", atk=12, defense=18, moves=[ember]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(45),
        )
        battle.start_round()
        battle.last_damage_taken["a-1"] = {
            "attacker_id": "b-1",
            "move_name": "Ember",
            "move_type": "Fire",
            "round": battle.round,
            "damage": 10,
        }

        action, _info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Conversion2")
        self.assertTrue(action.chosen_type)

    def test_choose_action_uses_conversion_once_even_with_attack_available(self) -> None:
        conversion = MoveSpec(
            name="Conversion",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
            target_kind="Self",
            target_range=0,
            effects_text="Change the user's type to one of its moves.",
        )
        psybeam = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=7,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Porygon", moves=[conversion, psybeam], atk=16), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Machoke", moves=[psybeam]), controller_id="b", position=(2, 4))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(46),
        )
        battle.start_round()

        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Conversion")
        self.assertEqual(info.get("reason"), "conversion_once")

    def test_choose_action_prefers_grapple_after_recent_wrap_setup(self) -> None:
        wrap = MoveSpec(
            name="Wrap",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Wrap deals a tick of damage when gaining dominance in a grapple.",
        )
        actor = PokemonState(spec=_make_mon("Shuckle", atk=1, moves=[wrap]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=18), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(46),
        )
        battle.start_round()
        foe.statuses.append({"name": "Trapped", "remaining": 1})
        battle.log.append({"type": "move", "actor": "a-1", "move": "Wrap", "damage": 3})

        action, _info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Grapple")

    def test_choose_action_prefers_poison_payoff_move_on_poisoned_target(self) -> None:
        venom_drench = MoveSpec(
            name="Venom Drench",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            effects_text="Venom Drench lowers poisoned targets' stats.",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=1,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[venom_drench, tackle]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=16, moves=[tackle]), controller_id="b", position=(2, 3))
        foe.statuses.append({"name": "Poisoned"})
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(47),
        )
        battle.start_round()

        action, _info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Venom Drench")

    def test_choose_action_prefers_sleep_payoff_move_on_sleeping_target(self) -> None:
        dream_eater = MoveSpec(
            name="Dream Eater",
            type="Psychic",
            category="Special",
            db=5,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            effects_text="Dream Eater deals bonus damage to sleeping targets and heals the user.",
        )
        psybeam = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[dream_eater, psybeam]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=14, moves=[psybeam]), controller_id="b", position=(2, 4))
        foe.statuses.append({"name": "Sleep", "remaining": 2})
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(48),
        )
        battle.start_round()

        action, _info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Dream Eater")


if __name__ == "__main__":
    unittest.main()
