import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.ai import aai_port
from auto_ptu.rules import BattleState, DisengageAction, GridState, PokemonState, ShiftAction, UseMoveAction
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

    def test_prefers_highest_expected_damage_move_as_baseline(self) -> None:
        weak = MoveSpec(
            name="Scratch",
            type="Normal",
            category="Physical",
            db=2,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        strong = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[weak, strong]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", defense=12, moves=[weak]), controller_id="b", position=(1, 2))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(46),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Slash")
        self.assertEqual(info.get("reason"), "attack_in_range")

    def test_shift_scoring_penalizes_recent_position_loops(self) -> None:
        move = MoveSpec(
            name="Punch",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", moves=[move]), controller_id="a", position=(5, 5))
        foe = PokemonState(spec=_make_mon("Foe", moves=[move]), controller_id="b", position=(8, 5))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=10, height=10),
            rng=random.Random(31),
        )
        battle.start_round()
        battle.log_event({"type": "shift", "actor": "a-1", "from": [4, 5], "to": [5, 5], "round": 1})
        battle.log_event({"type": "shift", "actor": "a-1", "from": [5, 5], "to": [4, 5], "round": 2})
        loop_score = ai_hybrid.score_action(battle, "a-1", ShiftAction(actor_id="a-1", destination=(4, 5)))
        progress_score = ai_hybrid.score_action(battle, "a-1", ShiftAction(actor_id="a-1", destination=(6, 5)))
        self.assertLess(loop_score, progress_score)

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

    def test_prefers_accuracy_pressure_setup_when_followup_exists(self) -> None:
        sand_attack = MoveSpec(
            name="Sand Attack",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Lower the target's Accuracy by 1 Combat Stage.",
        )
        weak_hit = MoveSpec(
            name="Scratch",
            type="Normal",
            category="Physical",
            db=2,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        finisher = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[sand_attack, weak_hit, finisher]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", atk=18, defense=35, moves=[finisher]), controller_id="b", position=(1, 2))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(41),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Sand Attack")

    def test_strong_damage_baseline_blocks_setup_choice(self) -> None:
        sand_attack = MoveSpec(
            name="Sand Attack",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Lower the target's Accuracy by 1 Combat Stage.",
        )
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=14, moves=[sand_attack, slash]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", defense=8, moves=[slash]), controller_id="b", position=(1, 2))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(47),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Slash")
        self.assertEqual(info.get("reason"), "attack_in_range")

    def test_knock_off_scores_above_peer_damage_when_target_has_item(self) -> None:
        knock_off = MoveSpec(
            name="Knock Off",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="If the target is hit, remove one of its held items.",
        )
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
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[knock_off, tackle]), controller_id="a", position=(2, 2))
        foe_spec = _make_mon("Foe", defense=12, moves=[tackle])
        foe_spec.items = [{"name": "Oran Berry"}]
        foe = PokemonState(spec=foe_spec, controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(42),
        )
        battle.start_round()
        knock_action = UseMoveAction(actor_id="a-1", move_name="Knock Off", target_id="b-1")
        tackle_action = UseMoveAction(actor_id="a-1", move_name="Tackle", target_id="b-1")
        self.assertGreater(ai_hybrid.score_action(battle, "a-1", knock_action), ai_hybrid.score_action(battle, "a-1", tackle_action))

    def test_knock_off_can_beat_higher_raw_damage_when_item_value_is_high(self) -> None:
        knock_off = MoveSpec(
            name="Knock Off",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="If the target is hit, remove one of its held items.",
        )
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[knock_off, slash]), controller_id="a", position=(2, 2))
        foe_spec = _make_mon("Foe", defense=12, moves=[slash])
        foe_spec.items = [{"name": "Leftovers"}]
        foe = PokemonState(spec=foe_spec, controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(60),
        )
        battle.start_round()
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Knock Off")
        self.assertEqual(info.get("reason"), "item_denial")

    def test_hidden_simulation_outcome_tracks_item_removal(self) -> None:
        knock_off = MoveSpec(
            name="Knock Off",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="If the target is hit, remove one of its held items.",
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[knock_off]), controller_id="a", position=(2, 2))
        foe_spec = _make_mon("Foe", defense=12, moves=[])
        foe_spec.items = [{"name": "Oran Berry"}]
        foe = PokemonState(spec=foe_spec, controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(48),
        )
        battle.start_round()
        action = UseMoveAction(actor_id="a-1", move_name="Knock Off", target_id="b-1")
        outcome = ai_hybrid._simulated_action_outcome(battle, "a-1", action)
        self.assertGreaterEqual(float(outcome.get("damage", 0.0) or 0.0), 0.0)
        self.assertGreater(float(outcome.get("item_removed", 0.0) or 0.0), 0.0)

    def test_damage_followup_scores_higher_after_accuracy_drop_combo(self) -> None:
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
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[tackle]), controller_id="a", position=(3, 3))
        foe = PokemonState(spec=_make_mon("Foe", defense=12, moves=[tackle]), controller_id="b", position=(3, 4))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(43),
        )
        battle.start_round()
        action = UseMoveAction(actor_id="a-1", move_name="Tackle", target_id="b-1")
        base_score = ai_hybrid.score_action(battle, "a-1", action)
        battle.pokemon["b-1"].combat_stages["accuracy"] = -2
        combo_score = ai_hybrid.score_action(battle, "a-1", action)
        self.assertGreater(combo_score, base_score)

    def test_accuracy_pressure_intent_biases_followup_attack_next_turn(self) -> None:
        sand_attack = MoveSpec(
            name="Sand Attack",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Lower the target's Accuracy by 1 Combat Stage.",
        )
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[sand_attack, slash]), controller_id="a", position=(1, 1))
        foe = PokemonState(spec=_make_mon("Foe", atk=18, defense=14, moves=[slash]), controller_id="b", position=(1, 2))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(44),
        )
        battle.start_round()
        ai_hybrid.observe_action(battle, "a-1", UseMoveAction(actor_id="a-1", move_name="Sand Attack", target_id="b-1"))
        battle.pokemon["b-1"].combat_stages["accuracy"] = -1
        slash_action = UseMoveAction(actor_id="a-1", move_name="Slash", target_id="b-1")
        sand_action = UseMoveAction(actor_id="a-1", move_name="Sand Attack", target_id="b-1")
        self.assertGreater(ai_hybrid.score_action(battle, "a-1", slash_action), ai_hybrid.score_action(battle, "a-1", sand_action))

    def test_self_setup_intent_biases_payoff_attack_next_turn(self) -> None:
        agility = MoveSpec(
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
        actor = PokemonState(spec=_make_mon("Actor", atk=12, moves=[agility, tackle]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=12, moves=[tackle]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(45),
        )
        battle.start_round()
        ai_hybrid.observe_action(battle, "a-1", UseMoveAction(actor_id="a-1", move_name="Agility", target_id="a-1"))
        tackle_action = UseMoveAction(actor_id="a-1", move_name="Tackle", target_id="b-1")
        agility_action = UseMoveAction(actor_id="a-1", move_name="Agility", target_id="a-1")
        self.assertGreater(ai_hybrid.score_action(battle, "a-1", tackle_action), ai_hybrid.score_action(battle, "a-1", agility_action))

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

    def test_struggle_scores_below_real_attack_when_available(self) -> None:
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
            rng=random.Random(25),
        )
        battle.start_round()
        struggle_action = UseMoveAction(actor_id="a-1", move_name="Struggle", target_id="b-1")
        tackle_action = UseMoveAction(actor_id="a-1", move_name="Tackle", target_id="b-1")
        self.assertLess(
            ai_hybrid.score_action(battle, "a-1", struggle_action),
            ai_hybrid.score_action(battle, "a-1", tackle_action),
        )

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

    def test_repeated_zero_damage_same_target_penalizes_attack_score(self) -> None:
        poison_sting = MoveSpec(
            name="Poison Sting",
            type="Poison",
            category="Physical",
            db=2,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Poison Sting poisons on a high roll.",
        )
        sand_attack = MoveSpec(
            name="Sand Attack",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Lower the target's Accuracy by 1 Combat Stage.",
        )
        actor = PokemonState(spec=_make_mon("Gligar", atk=10, moves=[poison_sting, sand_attack]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Shuckle", defense=30, moves=[]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(58),
        )
        battle.start_round()
        action = UseMoveAction(actor_id="a-1", move_name="Poison Sting", target_id="b-1")
        baseline = ai_hybrid.score_action(battle, "a-1", action)
        battle.log.append({"type": "move", "actor": "a-1", "move": "Poison Sting", "target": "b-1", "damage": 0})
        battle.log.append({"type": "move", "actor": "a-1", "move": "Poison Sting", "target": "b-1", "damage": 0})
        penalized = ai_hybrid.score_action(battle, "a-1", action)
        self.assertLess(penalized, baseline - 3.0)

    def test_repeated_zero_damage_same_target_prefers_status_over_loop(self) -> None:
        poison_sting = MoveSpec(
            name="Poison Sting",
            type="Poison",
            category="Physical",
            db=2,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Poison Sting poisons on a high roll.",
        )
        sand_attack = MoveSpec(
            name="Sand Attack",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            effects_text="Lower the target's Accuracy by 1 Combat Stage.",
        )
        actor = PokemonState(spec=_make_mon("Gligar", atk=10, moves=[poison_sting, sand_attack]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Shuckle", defense=30, moves=[]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=6, height=6),
            rng=random.Random(59),
        )
        battle.start_round()
        battle.log.append({"type": "move", "actor": "a-1", "move": "Poison Sting", "target": "b-1", "damage": 0})
        battle.log.append({"type": "move", "actor": "a-1", "move": "Poison Sting", "target": "b-1", "damage": 0})
        action, info = ai_hybrid.choose_action(battle, "a-1")
        self.assertIsInstance(action, UseMoveAction)
        assert isinstance(action, UseMoveAction)
        self.assertEqual(action.move_name, "Sand Attack")
        self.assertIn(info.get("reason"), {"stale_setup", "weak_damage_setup", "status_value"})

    def test_withdraw_is_penalized_when_withdrawn_is_already_active(self) -> None:
        withdraw = MoveSpec(
            name="Withdraw",
            type="Water",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_value=0,
            target_kind="Self",
            target_range=0,
            effects_text="Withdraw raises Defense by +1 CS. Withdrawn grants damage reduction and blocks movement.",
        )
        ember = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=5,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Torkoal", defense=10, moves=[withdraw, ember]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Foe", defense=7, moves=[ember]), controller_id="b", position=(2, 4))
        actor.statuses.append({"name": "Withdrawn"})
        actor.combat_stages["def"] = 2
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=8, height=8),
            rng=random.Random(61),
        )
        battle.start_round()
        withdraw_action = UseMoveAction(actor_id="a-1", move_name="Withdraw", target_id="a-1")
        ember_action = UseMoveAction(actor_id="a-1", move_name="Ember", target_id="b-1")
        self.assertLess(ai_hybrid.score_action(battle, "a-1", withdraw_action), ai_hybrid.score_action(battle, "a-1", ember_action))

    def test_repeated_low_impact_damage_same_target_is_penalized(self) -> None:
        ember = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=5,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Actor", atk=9, moves=[ember]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Torkoal", hp=58, defense=10, moves=[]), controller_id="b", position=(2, 4))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=8, height=8),
            rng=random.Random(62),
        )
        battle.start_round()
        action = UseMoveAction(actor_id="a-1", move_name="Ember", target_id="b-1")
        baseline = ai_hybrid.score_action(battle, "a-1", action)
        battle.log.append({"type": "move", "actor": "a-1", "move": "Ember", "target": "b-1", "damage": 4})
        battle.log.append({"type": "move", "actor": "a-1", "move": "Ember", "target": "b-1", "damage": 6})
        penalized = ai_hybrid.score_action(battle, "a-1", action)
        self.assertLess(penalized, baseline - 2.5)

    def test_disengage_is_penalized_when_foe_keeps_ranged_pressure(self) -> None:
        thunder_shock = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        rock_throw = MoveSpec(
            name="Rock Throw",
            type="Rock",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Pikachu", atk=8, moves=[thunder_shock]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Cranidos", atk=12, moves=[rock_throw]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(63),
        )
        battle.start_round()
        attack_action = UseMoveAction(actor_id="a-1", move_name="Thunder Shock", target_id="b-1")
        disengage_action = DisengageAction(actor_id="a-1", destination=(1, 2))
        self.assertGreater(
            ai_hybrid.score_action(battle, "a-1", attack_action),
            ai_hybrid.score_action(battle, "a-1", disengage_action),
        )

    def test_choose_action_does_not_prefer_disengage_when_destination_stays_threatened(self) -> None:
        thunder_shock = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=1,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        stone_edge = MoveSpec(
            name="Stone Edge",
            type="Rock",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
        )
        actor = PokemonState(spec=_make_mon("Pikachu", atk=6, moves=[thunder_shock]), controller_id="a", position=(2, 2))
        foe = PokemonState(spec=_make_mon("Cranidos", atk=15, moves=[stone_edge]), controller_id="b", position=(2, 3))
        battle = BattleState(
            trainers={},
            pokemon={"a-1": actor, "b-1": foe},
            grid=GridState(width=7, height=7),
            rng=random.Random(64),
        )
        battle.start_round()

        action, _info = ai_hybrid.choose_action(battle, "a-1")
        self.assertFalse(isinstance(action, DisengageAction))

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
