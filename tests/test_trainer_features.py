import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec, TrainerSideSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState


def _mon(name: str, moves: list[MoveSpec] | None = None) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=12,
        atk=12,
        defense=12,
        spatk=12,
        spdef=12,
        spd=12,
        moves=moves or [],
    )


def _battle_with_feature(
    feature: dict,
    *,
    resources: dict | None = None,
    trainer_class: dict | None = None,
    extra_features: list[dict] | None = None,
    edges: list[dict | str] | None = None,
) -> BattleState:
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
        freq="At-Will",
    )
    player = TrainerState(
        identifier="player",
        name="Player",
        controller_kind="player",
        team="players",
        features=[dict(feature)] + [dict(entry) for entry in (extra_features or [])],
        edges=list(edges or []),
        feature_resources=dict(resources or {}),
        trainer_class=dict(trainer_class or {}),
    )
    foe = TrainerState(
        identifier="foe",
        name="Foe",
        controller_kind="ai",
        team="foes",
    )
    mons = {
        "player-1": PokemonState(spec=_mon("PlayerMon", [tackle]), controller_id="player", position=(1, 1)),
        "foe-1": PokemonState(spec=_mon("FoeMon", [tackle]), controller_id="foe", position=(1, 2)),
    }
    battle = BattleState(
        trainers={"player": player, "foe": foe},
        pokemon=mons,
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    return battle


class TrainerFeatureTests(unittest.TestCase):
    def test_round_start_feature_triggers_and_grants_ap(self) -> None:
        feature = {
            "feature_id": "battle-prep",
            "name": "Battle Prep",
            "trigger": "round_start",
            "frequency": "EOT",
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature)
        player = battle.trainers["player"]
        self.assertEqual(5, player.ap)
        battle.start_round()
        self.assertEqual(6, player.ap)
        battle.start_round()
        self.assertEqual(7, player.ap)
        events = [entry for entry in battle.log if entry.get("type") == "trainer_feature"]
        self.assertEqual(2, len(events))

    def test_scene_frequency_feature_only_applies_once(self) -> None:
        feature = {
            "feature_id": "once-per-scene",
            "name": "Once Per Scene",
            "trigger": "action_resolved",
            "frequency": "Scene",
            "effect_payload": {"type": "grant_temp_hp", "amount": 5},
        }
        battle = _battle_with_feature(feature)
        mon = battle.pokemon["player-1"]
        self.assertEqual(0, mon.temp_hp)
        battle.trainer_feature_dispatcher.trigger("action_resolved", actor_id="player-1")
        self.assertEqual(5, mon.temp_hp)
        battle.trainer_feature_dispatcher.trigger("action_resolved", actor_id="player-1")
        self.assertEqual(5, mon.temp_hp)

    def test_resource_cost_consumes_pool(self) -> None:
        feature = {
            "feature_id": "focus-guard",
            "name": "Focus Guard",
            "trigger": "phase_change",
            "frequency": "At-Will",
            "resource_cost": {"focus": 1},
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature, resources={"focus": 1})
        player = battle.trainers["player"]
        self.assertEqual(1, player.feature_resources.get("focus"))
        battle.trainer_feature_dispatcher.trigger("phase_change", actor_id="player-1")
        self.assertEqual(0, player.feature_resources.get("focus"))
        # No remaining resource, so second trigger should not apply.
        ap_after_first = player.ap
        battle.trainer_feature_dispatcher.trigger("phase_change", actor_id="player-1")
        self.assertEqual(ap_after_first, player.ap)

    def test_trainer_side_parses_class_and_feature_payloads(self) -> None:
        payload = {
            "id": "ace",
            "name": "Ace Trainer",
            "controller": "player",
            "team": "players",
            "pokemon": [_mon("Eevee").to_engine_dict()],
            "trainer_class": {
                "class_id": "ace-trainer",
                "subclass_id": "striker",
                "level": 20,
                "feature_slots": 2,
                "known_features": [
                    {
                        "feature_id": "battle-prep",
                        "name": "Battle Prep",
                        "trigger": "round_start",
                        "frequency": "EOT",
                        "min_trainer_level": 5,
                        "required_classes": ["ace-trainer"],
                    }
                ],
                "resources": {"focus": 2},
            },
            "feature_resources": {"focus": 3},
        }
        side = TrainerSideSpec.from_dict(payload)
        self.assertIsNotNone(side.trainer_class)
        assert side.trainer_class is not None
        self.assertEqual("ace-trainer", side.trainer_class.class_id)
        self.assertEqual(1, len(side.trainer_features))
        self.assertEqual("battle-prep", side.trainer_features[0].feature_id)
        self.assertEqual(5, side.trainer_features[0].min_trainer_level)
        self.assertEqual(["ace-trainer"], side.trainer_features[0].required_classes)
        self.assertEqual(3, side.feature_resources["focus"])

    def test_trainer_side_parses_trainer_runtime_stats(self) -> None:
        payload = {
            "id": "ace",
            "name": "Ace Trainer",
            "controller": "player",
            "team": "players",
            "pokemon": [_mon("Eevee").to_engine_dict()],
            "trainer_skills": {"guile": 4, "focus": 3},
            "trainer_save_bonus": 2,
            "trainer_evasion_phys": 1,
            "trainer_evasion_spec": 2,
            "trainer_evasion_spd": 3,
        }
        side = TrainerSideSpec.from_dict(payload)
        self.assertEqual(4, side.skills["guile"])
        self.assertEqual(3, side.skills["focus"])
        self.assertEqual(2, side.save_bonus)
        self.assertEqual(1, side.evasion_phys)
        self.assertEqual(2, side.evasion_spec)
        self.assertEqual(3, side.evasion_spd)

    def test_action_condition_move_name_filters_feature(self) -> None:
        feature = {
            "feature_id": "trigger-by-move",
            "name": "Trigger By Move",
            "trigger": "action_resolved",
            "frequency": "At-Will",
            "conditions": {"move_name": "thunderbolt"},
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature)
        player = battle.trainers["player"]
        self.assertEqual(5, player.ap)
        battle.trainer_feature_dispatcher.trigger(
            "action_resolved",
            actor_id="player-1",
            payload={"action_type": "standard", "move_name": "Tackle"},
        )
        self.assertEqual(5, player.ap)
        battle.trainer_feature_dispatcher.trigger(
            "action_resolved",
            actor_id="player-1",
            payload={"action_type": "standard", "move_name": "Thunderbolt"},
        )
        self.assertEqual(6, player.ap)

    def test_min_trainer_level_prerequisite_blocks_feature(self) -> None:
        feature = {
            "feature_id": "late-game-engine",
            "name": "Late Game Engine",
            "trigger": "round_start",
            "frequency": "At-Will",
            "min_trainer_level": 20,
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature, trainer_class={"class_id": "ace", "level": 10})
        player = battle.trainers["player"]
        battle.start_round()
        self.assertEqual(5, player.ap)

        battle2 = _battle_with_feature(feature, trainer_class={"class_id": "ace", "level": 20})
        player2 = battle2.trainers["player"]
        battle2.start_round()
        self.assertEqual(6, player2.ap)

    def test_required_class_prerequisite_blocks_feature(self) -> None:
        feature = {
            "feature_id": "ace-only",
            "name": "Ace Only",
            "trigger": "round_start",
            "frequency": "At-Will",
            "required_classes": ["ace-trainer"],
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature, trainer_class={"class_id": "medic", "level": 20})
        player = battle.trainers["player"]
        battle.start_round()
        self.assertEqual(5, player.ap)

        battle2 = _battle_with_feature(feature, trainer_class={"class_id": "ace-trainer", "level": 20})
        player2 = battle2.trainers["player"]
        battle2.start_round()
        self.assertEqual(6, player2.ap)

    def test_required_feature_prerequisite(self) -> None:
        base_feature = {
            "feature_id": "foundation",
            "name": "Foundation",
            "trigger": "round_start",
            "frequency": "At-Will",
            "effect_payload": {"type": "log_only"},
        }
        gated_feature = {
            "feature_id": "advanced",
            "name": "Advanced",
            "trigger": "round_start",
            "frequency": "At-Will",
            "required_features": ["foundation"],
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(gated_feature)
        player = battle.trainers["player"]
        battle.start_round()
        self.assertEqual(5, player.ap)

        battle2 = _battle_with_feature(gated_feature, extra_features=[base_feature])
        player2 = battle2.trainers["player"]
        battle2.start_round()
        self.assertEqual(6, player2.ap)

    def test_edge_entries_trigger_in_generic_dispatcher(self) -> None:
        feature = {
            "feature_id": "baseline",
            "name": "Baseline",
            "trigger": "",
            "frequency": "At-Will",
            "effect_payload": {"type": "log_only"},
        }
        edge = {
            "feature_id": "tactical-edge",
            "name": "Tactical Edge",
            "trigger": "round_start",
            "frequency": "At-Will",
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature, edges=[edge])
        player = battle.trainers["player"]
        battle.start_round()
        self.assertEqual(6, player.ap)
        edge_events = [
            entry for entry in battle.log
            if entry.get("type") == "trainer_feature" and entry.get("feature") == "Tactical Edge"
        ]
        self.assertEqual(1, len(edge_events))
        self.assertEqual("edge", edge_events[0].get("feature_kind"))

    def test_edge_can_satisfy_required_feature_prerequisite(self) -> None:
        feature = {
            "feature_id": "advanced-engine",
            "name": "Advanced Engine",
            "trigger": "round_start",
            "frequency": "At-Will",
            "required_features": ["foundation-edge"],
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature)
        player = battle.trainers["player"]
        battle.start_round()
        self.assertEqual(5, player.ap)

        battle2 = _battle_with_feature(feature, edges=[{"feature_id": "foundation-edge", "name": "Foundation Edge"}])
        player2 = battle2.trainers["player"]
        battle2.start_round()
        self.assertEqual(6, player2.ap)

    def test_target_rules_can_affect_active_enemy(self) -> None:
        feature = {
            "feature_id": "hex-mark",
            "name": "Hex Mark",
            "trigger": "round_start",
            "frequency": "Scene",
            "target_rules": {"scope": "active_enemies"},
            "effect_payload": {"type": "apply_status", "status": "Cursed", "duration": 2},
        }
        battle = _battle_with_feature(feature)
        battle.start_round()
        self.assertTrue(battle.pokemon["foe-1"].has_status("Cursed"))
        self.assertFalse(battle.pokemon["player-1"].has_status("Cursed"))

    def test_multi_effect_payload_applies_heal_and_combat_stage(self) -> None:
        feature = {
            "feature_id": "rallying-call",
            "name": "Rallying Call",
            "trigger": "phase_change",
            "frequency": "Scene",
            "effect_payload": [
                {"type": "heal", "amount": 7},
                {"type": "raise_cs", "stat": "atk", "amount": 1},
            ],
        }
        battle = _battle_with_feature(feature)
        player = battle.pokemon["player-1"]
        player.lose_hp(10)
        self.assertEqual(player.max_hp() - 10, player.hp)
        self.assertEqual(0, player.combat_stages.get("atk", 0))
        battle.trainer_feature_dispatcher.trigger("phase_change", actor_id="player-1", payload={"phase": "command"})
        self.assertEqual(player.max_hp() - 3, player.hp)
        self.assertEqual(1, player.combat_stages.get("atk", 0))

    def test_once_per_actor_per_round_condition(self) -> None:
        feature = {
            "feature_id": "actor-gated-feature",
            "name": "Actor Gated Feature",
            "trigger": "action_resolved",
            "frequency": "At-Will",
            "conditions": {"once_per_actor_per_round": True},
            "effect_payload": {"type": "grant_ap", "amount": 1},
        }
        battle = _battle_with_feature(feature)
        player = battle.trainers["player"]
        self.assertEqual(5, player.ap)
        battle.trainer_feature_dispatcher.trigger("action_resolved", actor_id="player-1")
        self.assertEqual(6, player.ap)
        battle.trainer_feature_dispatcher.trigger("action_resolved", actor_id="player-1")
        self.assertEqual(6, player.ap)
        battle.start_round()
        battle.trainer_feature_dispatcher.trigger("action_resolved", actor_id="player-1")
        self.assertEqual(7, player.ap)

    def test_trainer_side_accepts_string_features_and_edges(self) -> None:
        payload = {
            "id": "ace",
            "name": "Ace Trainer",
            "controller": "player",
            "team": "players",
            "pokemon": [_mon("Eevee").to_engine_dict()],
            "features": ["Battle Prep"],
            "edges": ["Novice Edge"],
        }
        side = TrainerSideSpec.from_dict(payload)
        self.assertEqual(["Battle Prep"], [entry.name for entry in side.trainer_features])
        self.assertEqual(["Novice Edge"], [entry.name for entry in side.trainer_edges])


if __name__ == "__main__":
    unittest.main()
