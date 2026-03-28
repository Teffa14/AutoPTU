import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import (
    ActionType,
    BattleState,
    DisengageAction,
    DirtyFightingFollowUpAction,
    EnchantingGazeAction,
    EquipWeaponAction,
    InterceptAction,
    GridState,
    JumpAction,
    PokemonState,
    ShiftAction,
    QuickWitManipulateAction,
    QuickWitMoveAction,
    create_trainer_feature_action,
    FlightAction,
    TricksterFollowUpAction,
    TrainerState,
    TurnPhase,
    UseMoveAction,
    InitiativeEntry,
    WeaponFinesseFollowUpAction,
    PlayThemLikeAFiddleFollowUpAction,
    PsychicResonanceFollowUpAction,
    QuickSwitchAction,
    movement,
)
from auto_ptu.rules.controllers.phase_controller import PhaseController
from auto_ptu.rules.calculations import defensive_stat, offensive_stat, speed_stat
from auto_ptu.rules import calculations
from auto_ptu.rules.hooks.move_specials import MoveSpecialContext, _effect_roll


class _FixedRng(random.Random):
    def __init__(self, rolls: list[int]) -> None:
        super().__init__()
        self._rolls = list(rolls)

    def randint(self, a: int, b: int) -> int:
        if self._rolls:
            return self._rolls.pop(0)
        return super().randint(a, b)


def _mon(
    name: str,
    *,
    features: list[dict] | None = None,
    capabilities: list[dict | str] | None = None,
    types: list[str] | None = None,
    level: int = 20,
    tags: list[str] | None = None,
    moves: list[MoveSpec] | None = None,
) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=level,
        types=list(types or ["Normal"]),
        hp_stat=12,
        atk=12,
        defense=12,
        spatk=12,
        spdef=12,
        spd=12,
        moves=moves
        or [
            MoveSpec(
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
        ],
        trainer_features=list(features or []),
        capabilities=list(capabilities or []),
        tags=list(tags or []),
    )


def _battle_with_feature(feature: dict, *, ap: int = 5, battle_context: str = "full_contact") -> BattleState:
    player = TrainerState(
        identifier="player",
        name="Player",
        controller_kind="player",
        team="players",
        ap=ap,
        features=[dict(feature)],
    )
    foe = TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes")
    return BattleState(
        trainers={"player": player, "foe": foe},
        pokemon={
            "player-1": PokemonState(spec=_mon("PlayerMon"), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
        battle_context=battle_context,
    )


def _advance_to_end_phase(battle: BattleState) -> None:
    battle.start_round()
    entry = battle.advance_turn()
    while entry and (entry.actor_id in battle.trainers or entry.actor_id != "player-1"):
        battle.end_turn()
        entry = battle.advance_turn()
    while battle.phase != TurnPhase.END:
        battle.advance_phase()


class TrainerPassivePerkTests(unittest.TestCase):
    def test_basic_martial_arts_intimidating_presence_and_leader_grant_moves(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                ),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "martial-1": PokemonState(
                    spec=_mon("Martial", features=[{"name": "Basic Martial Arts"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "presence-1": PokemonState(
                    spec=_mon("Presence", features=[{"name": "Intimidating Presence"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 2),
                ),
                "leader-1": PokemonState(
                    spec=_mon("Leader", features=[{"name": "Leader"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 3),
                ),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(4, 4)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(1),
        )
        martial_moves = {str(move.name or "").strip() for move in battle.pokemon["martial-1"].spec.moves}
        presence_moves = {str(move.name or "").strip() for move in battle.pokemon["presence-1"].spec.moves}
        leader_moves = {str(move.name or "").strip() for move in battle.pokemon["leader-1"].spec.moves}
        self.assertIn("Rock Smash", martial_moves)
        self.assertIn("Leer", presence_moves)
        self.assertIn("After You", leader_moves)

    def test_athletic_initiative_grants_agility(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    edges=[{"name": "Athletic Initiative"}],
                ),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Runner", tags=["trainer"]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(1),
        )
        move_names = {str(move.name or "").strip() for move in battle.pokemon["player-1"].spec.moves}
        self.assertIn("Agility", move_names)

    def test_demoralize_makes_crit_target_vulnerable(self) -> None:
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
            crit_range=1,
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Bully", features=[{"name": "Demoralize"}], tags=["trainer"], moves=[slash]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target", level=50), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 20, 20, 20]),
        )
        battle.pokemon["foe-1"].spec.hp_stat = 40
        battle.pokemon["foe-1"].hp = battle.pokemon["foe-1"].max_hp()
        UseMoveAction(actor_id="player-1", move_name="Slash", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Vulnerable"))

    def test_bad_mood_stacks_crit_range_for_persistent_and_volatile_statuses(self) -> None:
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
            crit_range=20,
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Bruiser", features=[{"name": "Bad Mood"}], tags=["trainer"], moves=[slash]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([18]),
        )
        actor = battle.pokemon["player-1"]
        actor.statuses.append({"name": "Burned"})
        actor.statuses.append({"name": "Confused"})
        UseMoveAction(actor_id="player-1", move_name="Slash", target_id="foe-1").resolve(battle)
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("actor") == "player-1")
        self.assertTrue(move_event.get("crit"))

    def test_strike_of_the_whip_can_add_injury_temp_hp_and_cure_statuses(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Taskmaster", features=[{"name": "Press"}, {"name": "Strike of the Whip"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Ally"), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(4, 4)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(2),
        )
        ally = battle.pokemon["player-2"]
        ally.statuses.extend([{"name": "Confused"}, {"name": "Infatuated"}])
        battle.out_of_turn_prompt = lambda prompt: {"injury_temp_hp": True, "cure_statuses": True} if prompt.get("feature") == "Strike of the Whip" else True
        create_trainer_feature_action("press", actor_id="player-1", target_id="player-2", stats=["atk", "def"]).resolve(battle)
        self.assertEqual(1, ally.injuries)
        self.assertEqual(ally.tick_value(), ally.temp_hp)
        self.assertFalse(ally.has_status("Confused"))
        self.assertFalse(ally.has_status("Infatuated"))
        self.assertEqual(2, battle.trainers["player"].ap)

    def test_strike_of_the_whip_can_apply_reckless_advance_order(self) -> None:
        scratch = MoveSpec(
            name="Scratch",
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
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=4),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Taskmaster",
                        features=[{"name": "Press"}, {"name": "Strike of the Whip"}, {"name": "Reckless Advance"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Ally", moves=[scratch]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([18, 18]),
        )
        battle.out_of_turn_prompt = lambda prompt: {"order": "reckless advance"} if prompt.get("feature") == "Strike of the Whip" else True
        create_trainer_feature_action("press", actor_id="player-1", target_id="player-2", stats=["atk", "def"]).resolve(battle)
        self.assertTrue(battle.pokemon["player-2"].get_temporary_effects("reckless_advance_bound"))
        self.assertEqual(2, battle.trainers["player"].ap)
        UseMoveAction(actor_id="player-2", move_name="Scratch", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Tripped"))
        self.assertTrue(battle.pokemon["player-2"].has_status("Vulnerable"))

    def test_target_order_long_shot_extends_range_and_adds_damage(self) -> None:
        water_gun = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=3,
            target_kind="Ranged",
            target_range=3,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Long Shot"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Sniper", moves=[water_gun]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(1, 8)),
            },
            grid=GridState(width=10, height=10),
            rng=_FixedRng([20, 14]),
        )
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="player-2", move_name="Water Gun", target_id="foe-1").validate(battle)
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="player-2", order_name="Long Shot").resolve(battle)
        action = UseMoveAction(actor_id="player-2", move_name="Water Gun", target_id="foe-1")
        action.validate(battle)
        before_hp = battle.pokemon["foe-1"].hp
        action.resolve(battle)
        self.assertLess(battle.pokemon["foe-1"].hp, before_hp)
        self.assertTrue(any(evt.get("feature") == "Long Shot" and evt.get("effect") == "damage_bonus" for evt in battle.log))

    def test_target_order_sentinel_stance_intercepts_with_shift_budget(self) -> None:
        water_gun = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=5),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Sentinel Stance"}, {"name": "Brace for Impact"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Guardian"), controller_id="player", position=(6, 3)),
                "player-3": PokemonState(spec=_mon("Ally"), controller_id="player", position=(4, 3)),
                "foe-1": PokemonState(spec=_mon("Shooter", moves=[water_gun]), controller_id="foe", position=(8, 3)),
            },
            grid=GridState(width=10, height=10),
            rng=_FixedRng([20, 14]),
        )
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="player-2", order_name="Brace for Impact").resolve(battle)
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="player-2", order_name="Sentinel Stance").resolve(battle)
        guardian = battle.pokemon["player-2"]
        ally = battle.pokemon["player-3"]
        before_hp = guardian.hp
        ally_before_hp = ally.hp
        UseMoveAction(actor_id="foe-1", move_name="Water Gun", target_id="player-3").resolve(battle)
        self.assertLessEqual(guardian.hp, before_hp)
        self.assertEqual(ally_before_hp, ally.hp)
        self.assertFalse(guardian.has_action_available(ActionType.SHIFT))
        intercept_event = next(evt for evt in battle.log if evt.get("type") == "maneuver" and evt.get("effect") == "intercept")
        self.assertEqual("Sentinel Stance", intercept_event.get("source"))

    def test_target_order_dazzling_dervish_adds_movement_and_penalizes_rolls_once_per_round(self) -> None:
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=4,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=5),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Dazzling Dervish"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Dervish", moves=[tackle]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[tackle]), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([20, 3]),
        )
        battle.pokemon["player-2"].spec.movement["overland"] = 2
        battle.pokemon["player-2"].spec.evasion_phys = 2
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="player-2", order_name="Dazzling Dervish").resolve(battle)
        self.assertEqual(4, battle.pokemon["player-2"].movement_speed("overland"))
        ShiftAction(actor_id="player-2", destination=(1, 4)).resolve(battle)
        penalty_entries = battle.pokemon["foe-1"].get_temporary_effects("all_roll_penalty")
        self.assertEqual(1, len(penalty_entries))
        self.assertEqual(3, int(penalty_entries[0].get("amount", 0) or 0))
        UseMoveAction(actor_id="player-2", move_name="Tackle", target_id="foe-1").resolve(battle)
        self.assertEqual(1, len(battle.pokemon["foe-1"].get_temporary_effects("all_roll_penalty")))
        self.assertEqual(-3, battle.pokemon["foe-1"].save_bonus(battle, "burned"))
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-2").resolve(battle)
        self.assertEqual(3, battle._roll_penalty(battle.pokemon["foe-1"]))
        self.assertTrue(
            any(
                evt.get("feature") == "Dazzling Dervish" and evt.get("effect") == "roll_penalty"
                for evt in battle.log
            )
        )

    def test_focused_command_inserts_extra_turn_and_applies_round_restrictions(self) -> None:
        at_will = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        scene_move = MoveSpec(
            name="Big Hit",
            type="Normal",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="Scene",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Focused Command"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally1", moves=[at_will, scene_move]), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Ally2", moves=[at_will, scene_move]), controller_id="player", position=(3, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[at_will]), controller_id="foe", position=(4, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([20, 11, 11, 11]),
        )
        battle.round = 1
        battle.current_actor_id = "player"
        battle.phase = TurnPhase.ACTION
        battle.initiative_order = [
            InitiativeEntry(actor_id="player", trainer_id="player", speed=20, trainer_modifier=0, roll=0, total=20),
            InitiativeEntry(actor_id="ally-1", trainer_id="player", speed=10, trainer_modifier=0, roll=0, total=10),
            InitiativeEntry(actor_id="foe-1", trainer_id="foe", speed=9, trainer_modifier=0, roll=0, total=9),
            InitiativeEntry(actor_id="ally-2", trainer_id="player", speed=8, trainer_modifier=0, roll=0, total=8),
        ]
        battle._initiative_index = 0
        create_trainer_feature_action(
            "focused_command",
            actor_id="player-1",
            primary_target_id="ally-1",
            secondary_target_id="ally-2",
        ).resolve(battle)
        self.assertFalse(battle.trainers["player"].has_action_available(ActionType.SWIFT))
        ordered_ids = [entry.actor_id for entry in battle.initiative_order]
        self.assertEqual(["player", "ally-2", "ally-1", "foe-1", "ally-2"], ordered_ids)
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="ally-1", move_name="Big Hit", target_id="foe-1").validate(battle)
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="ally-2", move_name="Big Hit", target_id="foe-1").validate(battle)
        before_hp = battle.pokemon["foe-1"].hp
        UseMoveAction(actor_id="ally-1", move_name="Tackle", target_id="foe-1").resolve(battle)
        self.assertLess(battle.pokemon["foe-1"].hp, before_hp)
        self.assertTrue(
            any(
                evt.get("ability") == "Focused Command" and evt.get("effect") == "damage_penalty"
                for evt in battle.log
            )
        )

    def test_focused_command_can_lift_both_restrictions_with_two_ap(self) -> None:
        at_will = MoveSpec(
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
        scene_move = MoveSpec(
            name="Big Hit",
            type="Normal",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="Scene",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Focused Command"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally1", moves=[at_will, scene_move]), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Ally2", moves=[at_will, scene_move]), controller_id="player", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(7),
        )
        battle.round = 1
        battle.current_actor_id = "player"
        battle.phase = TurnPhase.ACTION
        battle.initiative_order = [InitiativeEntry(actor_id="player", trainer_id="player", speed=20, trainer_modifier=0, roll=0, total=20)]
        battle._initiative_index = 0
        create_trainer_feature_action(
            "focused_command",
            actor_id="player-1",
            primary_target_id="ally-1",
            secondary_target_id="ally-2",
            lift_option="both",
        ).resolve(battle)
        self.assertEqual(0, battle.trainers["player"].ap)
        UseMoveAction(actor_id="ally-1", move_name="Big Hit", target_id="ally-2").validate(battle)
        self.assertFalse(battle.pokemon["ally-1"].get_temporary_effects("damage_penalty"))
        self.assertFalse(battle.pokemon["ally-2"].get_temporary_effects("damage_penalty"))

    def test_commanders_voice_can_use_single_order_as_swift_action(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Commander's Voice"}, {"name": "Long Shot"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Archer"), controller_id="player", position=(2, 1)),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(5, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(7),
        )
        battle.round = 1
        battle.current_actor_id = "player"
        battle.phase = TurnPhase.ACTION
        action = create_trainer_feature_action(
            "commanders_voice",
            actor_id="player-1",
            mode="swift_order",
            order_name="Long Shot",
            target_id="ally-1",
        )
        self.assertEqual(ActionType.SWIFT, action.action_type)
        action.resolve(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("long_shot"))
        self.assertTrue(any(evt.get("feature") == "Commander's Voice" and evt.get("effect") == "swift_order" for evt in battle.log))

    def test_commanders_voice_can_pair_focused_command_with_targeted_order(self) -> None:
        at_will = MoveSpec(
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
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Commander's Voice"}, {"name": "Focused Command"}, {"name": "Long Shot"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally1", moves=[at_will]), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Ally2", moves=[at_will]), controller_id="player", position=(3, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[at_will]), controller_id="foe", position=(6, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(11),
        )
        battle.round = 1
        battle.current_actor_id = "player"
        battle.phase = TurnPhase.ACTION
        battle.initiative_order = [
            InitiativeEntry(actor_id="player", trainer_id="player", speed=20, trainer_modifier=0, roll=0, total=20),
            InitiativeEntry(actor_id="ally-1", trainer_id="player", speed=10, trainer_modifier=0, roll=0, total=10),
            InitiativeEntry(actor_id="foe-1", trainer_id="foe", speed=9, trainer_modifier=0, roll=0, total=9),
            InitiativeEntry(actor_id="ally-2", trainer_id="player", speed=8, trainer_modifier=0, roll=0, total=8),
        ]
        battle._initiative_index = 0
        action = create_trainer_feature_action(
            "commanders_voice",
            actor_id="player-1",
            mode="double_order",
            order_name="Focused Command",
            primary_target_id="ally-1",
            secondary_target_id="ally-2",
            secondary_order_name="Long Shot",
            second_target_id="ally-1",
        )
        action.resolve(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("long_shot"))
        self.assertTrue(battle.pokemon["ally-2"].get_temporary_effects("long_shot"))
        self.assertTrue(battle._focused_command_extra_turn_pending("ally-2"))
        self.assertTrue(battle.trainers["player"].has_action_available(ActionType.SWIFT))
        self.assertTrue(any(evt.get("feature") == "Commander's Voice" and evt.get("effect") == "double_order" for evt in battle.log))

    def test_commanders_voice_rejects_focused_command_as_swift_action(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Commander's Voice"}, {"name": "Focused Command"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally1"), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Ally2"), controller_id="player", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(11),
        )
        battle.round = 1
        battle.current_actor_id = "player"
        battle.phase = TurnPhase.ACTION
        action = create_trainer_feature_action(
            "commanders_voice",
            actor_id="player-1",
            mode="swift_order",
            order_name="Focused Command",
            primary_target_id="ally-1",
            secondary_target_id="ally-2",
        )
        with self.assertRaises(ValueError):
            action.validate(battle)

    def test_leadership_allows_target_orders_on_team_allies(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "ally": TrainerState(identifier="ally", name="Ally", team="players"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Leadership"}, {"name": "Long Shot"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Borrowed"), controller_id="ally", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(5),
        )
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="ally-1", order_name="Long Shot").resolve(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("long_shot"))

    def test_battle_conductor_spreads_at_will_order_and_consumes_cost_once(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Battle Conductor"}, {"name": "Brace for Impact"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Tank1"), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Tank2"), controller_id="player", position=(3, 1)),
                "ally-3": PokemonState(spec=_mon("Tank3"), controller_id="player", position=(4, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(6),
        )
        create_trainer_feature_action(
            "battle_conductor",
            actor_id="player-1",
            order_name="Brace for Impact",
            target_ids=["ally-1", "ally-2", "ally-3"],
        ).resolve(battle)
        for target_id in ("ally-1", "ally-2", "ally-3"):
            self.assertTrue(battle.pokemon[target_id].get_temporary_effects("brace_for_impact_bound"))
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(any(evt.get("feature") == "Battle Conductor" and evt.get("effect") == "spread_order" for evt in battle.log))

    def test_scheme_twist_spreads_scene_order_and_tracks_scene_use_once(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=0)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Scheme Twist"}, {"name": "Long Shot"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Archer1"), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Archer2"), controller_id="player", position=(3, 1)),
                "ally-3": PokemonState(spec=_mon("Archer3"), controller_id="player", position=(4, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(7),
        )
        create_trainer_feature_action(
            "scheme_twist",
            actor_id="player-1",
            order_name="Long Shot",
            target_ids=["ally-1", "ally-2", "ally-3"],
        ).resolve(battle)
        for target_id in ("ally-1", "ally-2", "ally-3"):
            self.assertTrue(battle.pokemon[target_id].get_temporary_effects("long_shot"))
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Long Shot"))
        self.assertTrue(any(evt.get("feature") == "Scheme Twist" and evt.get("effect") == "spread_order" for evt in battle.log))

    def test_tip_the_scales_targets_all_allies_within_ten_meters(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=4),
                "ally": TrainerState(identifier="ally", name="Ally", team="players"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Tip the Scales"}, {"name": "Brace for Impact"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Tank1"), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Tank2"), controller_id="ally", position=(5, 1)),
                "ally-3": PokemonState(spec=_mon("FarTank"), controller_id="player", position=(12, 1)),
            },
            grid=GridState(width=20, height=6),
            rng=random.Random(8),
        )
        create_trainer_feature_action(
            "tip_the_scales",
            actor_id="player-1",
            order_name="Brace for Impact",
        ).resolve(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("brace_for_impact_bound"))
        self.assertTrue(battle.pokemon["ally-2"].get_temporary_effects("brace_for_impact_bound"))
        self.assertFalse(battle.pokemon["ally-3"].get_temporary_effects("brace_for_impact_bound"))
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(any(evt.get("feature") == "Tip the Scales" and evt.get("effect") == "spread_order" for evt in battle.log))

    def test_mobilize_prevents_attacks_of_opportunity_on_targets_next_turn_only(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "ally": TrainerState(identifier="ally", name="Ally", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Mobilize"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Runner"), controller_id="ally", position=(2, 1)),
                "foe-1": PokemonState(spec=_mon("Guard"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(9),
        )
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="ally-1", order_name="Mobilize").resolve(battle)
        battle.current_actor_id = "ally-1"
        origin = battle.pokemon["ally-1"].position
        battle._trigger_attack_of_opportunity_on_shift("ally-1", origin, (1, 2))
        self.assertFalse(any(evt.get("type") == "attack_of_opportunity" for evt in battle.log))
        battle.end_turn()
        battle.current_actor_id = "ally-1"
        battle.pokemon["ally-1"].position = (2, 1)
        battle._trigger_attack_of_opportunity_on_shift("ally-1", (2, 1), (1, 2))
        self.assertTrue(any(evt.get("type") == "attack_of_opportunity" for evt in battle.log))

    def test_mobilize_can_only_target_each_ally_once_per_encounter(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Mobilize"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Runner"), controller_id="player", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(10),
        )
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="ally-1", order_name="Mobilize").resolve(battle)
        with self.assertRaises(ValueError):
            create_trainer_feature_action("target_order", actor_id="player-1", target_id="ally-1", order_name="Mobilize").resolve(battle)

    def test_complex_orders_applies_different_orders_to_different_targets(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Complex Orders"}, {"name": "Brace for Impact"}, {"name": "Mobilize"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Tank"), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Runner"), controller_id="player", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(11),
        )
        battle.current_actor_id = "player"
        battle.phase = TurnPhase.ACTION
        create_trainer_feature_action(
            "complex_orders",
            actor_id="player-1",
            target_orders=[
                {"order_name": "Brace for Impact", "target_id": "ally-1"},
                {"order_name": "Mobilize", "target_id": "ally-2"},
            ],
        ).resolve(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("brace_for_impact_bound"))
        self.assertTrue(battle.pokemon["ally-2"].get_temporary_effects("mobilize_ready"))
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(any(evt.get("feature") == "Complex Orders" and evt.get("effect") == "multi_order" for evt in battle.log))

    def test_cheerleader_triggers_after_orders_and_applies_selected_condition(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Cheerleader"}, {"name": "Battle Conductor"}, {"name": "Brace for Impact"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Tank1"), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Tank2"), controller_id="player", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(12),
        )
        battle.out_of_turn_prompt = lambda payload: "motivated" if payload.get("feature") == "Cheerleader" else True
        create_trainer_feature_action(
            "battle_conductor",
            actor_id="player-1",
            order_name="Brace for Impact",
            target_ids=["ally-1", "ally-2"],
        ).resolve(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("motivated"))
        self.assertTrue(battle.pokemon["ally-2"].get_temporary_effects("motivated"))
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(any(evt.get("feature") == "Cheerleader" and evt.get("condition") == "motivated" for evt in battle.log))

    def test_cheers_playtest_makes_order_targets_cheered_and_blocks_foe_stage_drop(self) -> None:
        leer = MoveSpec(
            name="Leer",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Commander",
                        features=[{"name": "Cheers [Playtest]"}, {"name": "Long Shot"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Archer"), controller_id="player", position=(2, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[leer]), controller_id="foe", position=(5, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(13),
        )
        battle.out_of_turn_prompt = lambda payload: True if str(payload.get("feature", "")).startswith("Cheers") else False
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="ally-1", order_name="Long Shot").resolve(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("cheered"))
        battle._apply_combat_stage(
            [],
            attacker_id="foe-1",
            target_id="ally-1",
            move=leer,
            target=battle.pokemon["ally-1"],
            stat="def",
            delta=-1,
            description="Leer lowers Defense.",
        )
        self.assertEqual(0, battle.pokemon["ally-1"].combat_stages.get("def", 0))

    def test_strike_again_grants_extra_standard_for_at_will_attack(self) -> None:
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
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Strike Again!"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally", moves=[tackle]), controller_id="player", position=(2, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[tackle]), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(15),
        )
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="ally-1", order_name="Strike Again!").resolve(battle)
        self.assertEqual(1, battle._extra_action_count(battle.pokemon["ally-1"], ActionType.STANDARD))
        UseMoveAction(actor_id="ally-1", move_name="Tackle", target_id="foe-1").validate(battle)
        self.assertTrue(battle.pokemon["ally-1"].get_temporary_effects("strike_again_ready"))

    def test_strike_again_rejects_non_at_will_or_status_follow_up(self) -> None:
        blast = MoveSpec(
            name="Hyper Beam",
            type="Normal",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="Scene",
        )
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
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Commander", features=[{"name": "Strike Again!"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally", moves=[blast, growl]), controller_id="player", position=(2, 1)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(16),
        )
        create_trainer_feature_action("target_order", actor_id="player-1", target_id="ally-1", order_name="Strike Again!").resolve(battle)
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="ally-1", move_name="Hyper Beam").validate(battle)
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="ally-1", move_name="Growl").validate(battle)

    def test_ghost_step_phases_and_reappears_next_turn(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Ghost", features=[{"name": "Ghost Step"}], tags=["trainer"], types=["Ghost"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Foe", types=["Psychic"]), controller_id="foe", position=(4, 4)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(3),
        )
        battle.start_round()
        while battle.advance_turn() and battle.current_actor_id != "player-1":
            battle.end_turn()
        destination = next(iter(movement.legal_shift_tiles(battle, "player-1")))
        action = create_trainer_feature_action("ghost_step", actor_id="player-1", destination=destination)
        action.validate(battle)
        action.resolve(battle)
        self.assertTrue(battle.pokemon["player-1"].get_temporary_effects("semi_invulnerable"))
        battle.end_turn()
        while battle.advance_turn() and battle.current_actor_id != "player-1":
            battle.end_turn()
        self.assertEqual(destination, battle.pokemon["player-1"].position)
        self.assertFalse(battle.pokemon["player-1"].get_temporary_effects("ghost_step_pending"))

    def test_boo_primes_next_ghost_attack_after_ghost_step_and_bypasses_protect(self) -> None:
        shadow_sneak = MoveSpec(
            name="Shadow Sneak",
            type="Ghost",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Ghost",
                        features=[{"name": "Ghost Step"}, {"name": "Boo!"}],
                        tags=["trainer"],
                        types=["Ghost"],
                        moves=[shadow_sneak],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Foe", types=["Psychic"]), controller_id="foe", position=(4, 4)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([20, 20, 20]),
        )
        battle.out_of_turn_prompt = lambda prompt: {"accept": True} if prompt.get("feature") == "Boo!" else True
        battle.start_round()
        while battle.advance_turn() and battle.current_actor_id != "player-1":
            battle.end_turn()
        destination = (3, 4)
        create_trainer_feature_action("ghost_step", actor_id="player-1", destination=destination).resolve(battle)
        battle.end_turn()
        while battle.advance_turn() and battle.current_actor_id != "player-1":
            battle.end_turn()
        actor = battle.pokemon["player-1"]
        defender = battle.pokemon["foe-1"]
        self.assertEqual(destination, actor.position)
        self.assertTrue(actor.get_temporary_effects("boo_ready"))
        defender.statuses.append({"name": "Protect"})
        before_hp = defender.hp
        UseMoveAction(actor_id="player-1", move_name="Shadow Sneak", target_id="foe-1").resolve(battle)
        self.assertLess(defender.hp, before_hp)
        self.assertTrue(any(evt.get("type") == "smite" and evt.get("actor") == "player-1" for evt in battle.log))
        self.assertTrue(
            any(evt.get("feature") == "Boo!" and evt.get("effect") == "ghost_attack_ready" for evt in battle.log)
        )

    def test_shrug_off_recovers_injury_on_take_a_breather(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Tank", features=[{"name": "Shrug Off"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        battle.pokemon["player-1"].injuries = 2
        battle.apply_take_breather("player-1")
        self.assertEqual(1, battle.pokemon["player-1"].injuries)
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Shrug Off"))

    def test_staying_power_prevents_shift_trip_and_stage_reset_on_take_a_breather(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Tank", features=[{"name": "Staying Power"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        actor = battle.pokemon["player-1"]
        actor.combat_stages["atk"] = 2
        actor.combat_stages["def"] = -1
        actor.statuses.append({"name": "Enraged"})
        battle.out_of_turn_prompt = (
            lambda prompt: {"accept": True, "reset_combat_stages": False}
            if prompt.get("feature") == "Staying Power"
            else True
        )
        battle.apply_take_breather("player-1")
        self.assertEqual((1, 1), actor.position)
        self.assertEqual(2, actor.combat_stages["atk"])
        self.assertEqual(-1, actor.combat_stages["def"])
        self.assertFalse(actor.has_status("Tripped"))
        self.assertFalse(actor.has_status("Vulnerable"))
        self.assertFalse(actor.has_status("Enraged"))
        self.assertEqual(1, battle._feature_scene_use_count(actor, "Staying Power"))

    def test_boo_can_be_declined(self) -> None:
        shadow_sneak = MoveSpec(
            name="Shadow Sneak",
            type="Ghost",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Ghost",
                        features=[{"name": "Ghost Step"}, {"name": "Boo!"}],
                        tags=["trainer"],
                        types=["Ghost"],
                        moves=[shadow_sneak],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Foe", types=["Psychic"]), controller_id="foe", position=(4, 4)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([20, 20, 20]),
        )
        battle.out_of_turn_prompt = lambda prompt: {"accept": False} if prompt.get("feature") == "Boo!" else True
        battle.start_round()
        while battle.advance_turn() and battle.current_actor_id != "player-1":
            battle.end_turn()
        create_trainer_feature_action("ghost_step", actor_id="player-1", destination=(3, 4)).resolve(battle)
        battle.end_turn()
        while battle.advance_turn() and battle.current_actor_id != "player-1":
            battle.end_turn()
        self.assertFalse(battle.pokemon["player-1"].get_temporary_effects("boo_ready"))
        self.assertEqual(0, battle._feature_scene_use_count(battle.pokemon["player-1"], "Boo!"))

    def test_staying_power_can_be_declined(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Tank", features=[{"name": "Staying Power"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        actor = battle.pokemon["player-1"]
        actor.combat_stages["atk"] = 2
        battle.out_of_turn_prompt = (
            lambda prompt: {"accept": False}
            if prompt.get("feature") == "Staying Power"
            else True
        )
        battle.apply_take_breather("player-1")
        self.assertEqual(0, actor.combat_stages["atk"])
        self.assertTrue(actor.has_status("Tripped"))
        self.assertTrue(actor.has_status("Vulnerable"))
        self.assertEqual(0, battle._feature_scene_use_count(actor, "Staying Power"))

    def test_hardened_caps_hp_loss_after_five_injuries(self) -> None:
        actor = PokemonState(spec=_mon("Tank"), controller_id="player", position=(1, 1))
        actor.injuries = 9
        baseline = actor.max_hp_with_injuries()
        actor.add_temporary_effect("hardened")
        hardened_max = actor.max_hp_with_injuries()
        self.assertLess(baseline, hardened_max)
        self.assertEqual(actor.max_hp() - actor.tick_value() * 5, hardened_max)

    def test_hardened_ignores_standard_action_injury_backlash(self) -> None:
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
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Tank", moves=[tackle]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 14]),
        )
        actor = battle.pokemon["player-1"]
        actor.injuries = 5
        actor.add_temporary_effect("hardened")
        before_hp = actor.hp
        action = UseMoveAction(actor_id="player-1", move_name="Tackle", target_id="foe-1")
        action.validate(battle)
        battle._resolve_action(action)
        self.assertEqual(before_hp, actor.hp)
        self.assertTrue(
            any(evt.get("feature") == "Hardened" and evt.get("effect") == "injury_backlash_ignored" for evt in battle.log)
        )

    def test_hardened_grants_crit_effect_initiative_and_evasion_bonuses(self) -> None:
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
            crit_range=20,
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Bruiser", moves=[slash]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([19]),
        )
        actor = battle.pokemon["player-1"]
        actor.injuries = 3
        actor.add_temporary_effect("hardened")
        entry = battle._initiative_entry_for_pokemon("player-1")
        assert entry is not None
        self.assertEqual(17, entry.total)
        self.assertEqual(3, calculations.evasion_value(actor, "physical"))
        UseMoveAction(actor_id="player-1", move_name="Slash", target_id="foe-1").resolve(battle)
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("actor") == "player-1")
        self.assertTrue(move_event.get("crit"))
        ctx = MoveSpecialContext(
            battle=battle,
            attacker_id="player-1",
            attacker=actor,
            defender_id="foe-1",
            defender=battle.pokemon["foe-1"],
            move=slash,
            result={"roll": 15},
            damage_dealt=0,
            events=[],
            move_name="Slash",
            hit=True,
            phase="post_damage",
            action_type="standard",
        )
        self.assertEqual(16, _effect_roll(ctx))

    def test_hardened_grants_damage_reduction_and_resistance_step(self) -> None:
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
            freq="At-Will",
        )
        baseline = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Tank"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[tackle], level=40), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 14]),
        )
        hardened = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Tank"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[tackle], level=40), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 14]),
        )
        baseline.pokemon["player-1"].injuries = 5
        baseline.pokemon["player-1"].hp = baseline.pokemon["player-1"].max_hp_with_injuries()
        dr_target = hardened.pokemon["player-1"]
        dr_target.injuries = 5
        dr_target.hp = dr_target.max_hp_with_injuries()
        dr_target.add_temporary_effect("hardened")
        dr_target.hp = dr_target.max_hp_with_injuries()
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-1").resolve(baseline)
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-1").resolve(hardened)
        self.assertFalse(
            any(evt.get("feature") == "Hardened" and evt.get("effect") == "damage_reduction" for evt in baseline.log)
        )
        self.assertTrue(
            any(evt.get("feature") == "Hardened" and evt.get("effect") == "damage_reduction" for evt in hardened.log)
        )

        baseline_resist = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Tank"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[tackle], level=40), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 14]),
        )
        baseline_resist.pokemon["player-1"].injuries = 9
        baseline_resist.pokemon["player-1"].hp = baseline_resist.pokemon["player-1"].max_hp_with_injuries()
        hardened_resist = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Tank"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Foe", moves=[tackle], level=40), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 11, 11, 11]),
        )
        resist_target = hardened_resist.pokemon["player-1"]
        resist_target.injuries = 9
        resist_target.add_temporary_effect("hardened")
        resist_target.hp = resist_target.max_hp_with_injuries()
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-1").resolve(baseline_resist)
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-1").resolve(hardened_resist)
        baseline_resist_move = next(evt for evt in reversed(baseline_resist.log) if evt.get("type") == "move")
        hardened_resist_move = next(evt for evt in reversed(hardened_resist.log) if evt.get("type") == "move")
        self.assertEqual(1.0, baseline_resist_move["type_multiplier"])
        self.assertEqual(0.5, hardened_resist_move["type_multiplier"])
        self.assertTrue(
            any(evt.get("feature") == "Hardened" and evt.get("effect") == "resistance_bonus" for evt in hardened_resist.log)
        )

    def test_brutal_training_grants_crit_and_effect_bonus(self) -> None:
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
            crit_range=20,
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Coach", features=[{"name": "Brutal Training"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(
                    spec=_mon("Bruiser", moves=[slash]),
                    controller_id="player",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([19]),
        )
        action = create_trainer_feature_action("brutal_training", actor_id="player-1", target_id="player-2")
        action.validate(battle)
        action.resolve(battle)
        target = battle.pokemon["player-2"]
        self.assertTrue(target.get_temporary_effects("brutal_training"))
        dummy = PokemonState(spec=_mon("Dummy"), controller_id="player", position=(1, 3))
        ctx = MoveSpecialContext(
            battle=battle,
            attacker_id="player-2",
            attacker=target,
            defender_id="dummy",
            defender=dummy,
            move=slash,
            result={"roll": 15},
            damage_dealt=0,
            events=[],
            move_name="Slash",
            hit=True,
            phase="post_damage",
            action_type="standard",
        )
        self.assertEqual(16, _effect_roll(ctx))
        battle.pokemon["foe-1"] = PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 3))
        UseMoveAction(actor_id="player-2", move_name="Slash", target_id="foe-1").resolve(battle)
        move_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("actor") == "player-2")
        self.assertTrue(move_event.get("crit"))
        self.assertTrue(
            any(evt.get("feature") == "Brutal Training" and evt.get("effect") == "apply_training" for evt in battle.log)
        )

    def test_taskmaster_brutal_training_adds_injuries_and_hardens_target(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Coach",
                        features=[{"name": "Brutal Training"}, {"name": "Taskmaster"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Bruiser"), controller_id="player", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(7),
        )
        target = battle.pokemon["player-2"]
        target.hp = target.max_hp()
        create_trainer_feature_action(
            "brutal_training",
            actor_id="player-1",
            target_id="player-2",
            injuries_to_add=3,
        ).resolve(battle)
        self.assertEqual(3, target.injuries)
        self.assertTrue(target.is_hardened())
        self.assertLessEqual(target.hp, target.max_hp_with_injuries())
        self.assertTrue(
            any(evt.get("feature") == "Taskmaster" and evt.get("effect") == "harden" for evt in battle.log)
        )

    def test_quick_healing_removes_injuries_heals_ticks_and_clears_hardened_at_zero(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Medic", features=[{"name": "Quick Healing"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Bruiser"), controller_id="player", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(9),
        )
        target = battle.pokemon["player-2"]
        target.injuries = 2
        target.add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
        target.hp = max(1, target.max_hp_with_injuries() - target.tick_value() * 5)
        before_hp = target.hp
        action = create_trainer_feature_action(
            "quick_healing",
            actor_id="player-1",
            target_id="player-2",
            injuries_to_remove=2,
        )
        action.validate(battle)
        action.resolve(battle)
        self.assertEqual(0, target.injuries)
        self.assertEqual(min(target.max_hp(), before_hp + target.tick_value() * 4), target.hp)
        self.assertFalse(target.is_hardened())
        self.assertTrue(
            any(evt.get("feature") == "Quick Healing" and evt.get("effect") == "injury_recovery" for evt in battle.log)
        )

    def test_press_on_spends_ap_and_keeps_hardened_pokemon_active_below_zero(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    team="players",
                    ap=2,
                    skills={"intimidate": 4},
                )
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Bruiser", features=[{"name": "Press On!"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                )
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(11),
        )
        actor = battle.pokemon["player-1"]
        actor.injuries = 1
        actor.add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
        battle.out_of_turn_prompt = lambda prompt: {"accept": True} if prompt.get("feature") == "Press On!" else True
        actor.apply_damage((actor.hp or 0) + 1, skip_injury=True, skip_massive_injury=True)
        self.assertEqual(-1, actor.hp)
        self.assertFalse(actor.fainted)
        self.assertTrue(actor.is_pressing_on())
        self.assertEqual(1, battle.trainers["player"].ap)
        self.assertTrue(
            any(evt.get("feature") == "Press On!" and evt.get("effect") == "press_on" for evt in battle.log)
        )

    def test_press_on_does_not_prevent_faint_past_negative_thirty_percent(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    team="players",
                    ap=2,
                    skills={"intimidate": 4},
                )
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Bruiser", features=[{"name": "Press On!"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                )
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(12),
        )
        actor = battle.pokemon["player-1"]
        actor.injuries = 1
        actor.add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
        battle.out_of_turn_prompt = lambda prompt: {"accept": True} if prompt.get("feature") == "Press On!" else True
        floor = -max(1, int((actor.max_hp() * 0.3) + 0.999999))
        actor.apply_damage((actor.hp or 0) + abs(floor), skip_injury=True, skip_massive_injury=True)
        self.assertTrue(actor.fainted)
        self.assertFalse(actor.is_pressing_on())
        self.assertEqual(2, battle.trainers["player"].ap)

    def test_press_on_master_doubles_hardened_bonuses_while_pressing_on(self) -> None:
        actor = PokemonState(
            spec=_mon("Bruiser", features=[{"name": "Press On!"}], tags=["trainer"]),
            controller_id="player",
            position=(1, 1),
        )
        actor.injuries = 5
        actor.add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
        actor.add_temporary_effect("press_on_active", faint_floor=-12, source="Press On!", source_id="player-1")
        actor.hp = -1
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", skills={"intimidate": 6})},
            pokemon={"player-1": actor},
            grid=GridState(width=5, height=5),
            rng=random.Random(13),
        )
        self.assertEqual(2, actor.hardened_crit_effect_bonus(battle))
        self.assertEqual(2, actor.hardened_evasion_bonus(battle))
        self.assertEqual(10, actor.hardened_initiative_bonus(battle))
        self.assertEqual(10, actor.hardened_damage_reduction(battle))

    def test_not_yet_triggers_last_move_before_fainting(self) -> None:
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
        slash = MoveSpec(
            name="Scratch",
            type="Normal",
            category="Physical",
            db=1,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Soul", moves=[tackle], features=[{"name": "Not Yet!"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Attacker", moves=[slash], level=20),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 20, 20]),
        )
        actor = battle.pokemon["player-1"]
        actor.hp = 1
        before_foe_hp = battle.pokemon["foe-1"].hp
        prompts: list[dict] = []
        battle.out_of_turn_prompt = (
            lambda payload: prompts.append(dict(payload)) or {"accept": True, "choice": "Tackle||foe-1"}
            if payload.get("feature") == "Not Yet!"
            else True
        )
        UseMoveAction(actor_id="foe-1", move_name="Scratch", target_id="player-1").resolve(battle)
        self.assertTrue(actor.fainted)
        self.assertEqual(1, battle._feature_scene_use_count(actor, "Not Yet!"))
        self.assertGreater(actor.injuries, 0)
        self.assertTrue(
            any(evt.get("type") == "move" and evt.get("actor") == "player-1" and evt.get("move") == "Tackle" for evt in battle.log)
        )
        self.assertTrue(any(prompt.get("feature") == "Not Yet!" for prompt in prompts))
        self.assertTrue(
            any(evt.get("feature") == "Not Yet!" and evt.get("effect") == "last_move" for evt in battle.log)
        )

    def test_not_yet_ignores_banned_last_stand_moves(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Soul",
                        moves=[
                            MoveSpec(name="Explosion", type="Normal", category="Physical", db=12, ac=2, range_kind="Burst", range_value=1, target_kind="Self", target_range=0, freq="Daily"),
                            MoveSpec(name="Flail", type="Normal", category="Physical", db=4, ac=2, range_kind="Melee", range_value=1, target_kind="Melee", target_range=1, freq="At-Will"),
                        ],
                        features=[{"name": "Not Yet!"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(14),
        )
        self.assertEqual([], battle._not_yet_move_options("player-1"))

    def test_press_damages_ally_cures_sleep_and_raises_two_stats(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", skills={"intimidate": 4})},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Coach", features=[{"name": "Press"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Bruiser"), controller_id="player", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(15),
        )
        target = battle.pokemon["player-2"]
        target.statuses.append({"name": "Sleep"})
        before_hp = target.hp
        action = create_trainer_feature_action("press", actor_id="player-1", target_id="player-2", stats=["atk", "spd"])
        action.validate(battle)
        action.resolve(battle)
        self.assertLess(target.hp, before_hp)
        self.assertFalse(target.has_status("Sleep"))
        self.assertEqual(1, target.combat_stages["atk"])
        self.assertEqual(1, target.combat_stages["spd"])
        self.assertTrue(target.get_temporary_effects("press_obedience_bonus"))
        self.assertTrue(any(evt.get("feature") == "Press" and evt.get("effect") == "pressure" for evt in battle.log))

    def test_savage_strike_spends_tutor_points_and_grants_cruelty(self) -> None:
        bite = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Coach", features=[{"name": "Savage Strike"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("Bruiser", moves=[bite]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 11, 11, 11]),
        )
        target = battle.pokemon["player-2"]
        target.spec.tutor_points = 3
        action = create_trainer_feature_action("savage_strike", actor_id="player-1", target_id="player-2")
        action.validate(battle)
        action.resolve(battle)
        self.assertEqual(1, target.spec.tutor_points)
        self.assertIn("Cruelty", target.ability_names())
        before_injuries = battle.pokemon["foe-1"].injuries
        UseMoveAction(actor_id="player-2", move_name="Bite", target_id="foe-1").resolve(battle)
        self.assertGreater(battle.pokemon["foe-1"].injuries, before_injuries)
        self.assertTrue(any(evt.get("feature") == "Savage Strike" and evt.get("ability") == "Cruelty" for evt in battle.log))

    def test_shocking_speed_primes_electric_move_priority(self) -> None:
        shock = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Spark", features=[{"name": "Shocking Speed"}], tags=["trainer"], types=["Electric"], moves=[shock]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(5),
        )
        create_trainer_feature_action("shocking_speed", actor_id="player-1", move_name="Thunder Shock").resolve(battle)
        UseMoveAction(actor_id="player-1", move_name="Thunder Shock", target_id="foe-1").resolve(battle)
        matching = [
            event for event in battle.log
            if event.get("feature") == "Shocking Speed" and event.get("effect") == "priority"
        ]
        self.assertTrue(matching)

    def test_dynamism_adds_guile_rank_to_trainer_initiative(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    skills={"guile": 4},
                    edges=[{"feature_id": "dynamism", "name": "Dynamism"}],
                ),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("PlayerMon"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
            battle_context="league",
        )
        battle.start_round()
        trainer_entry = next(entry for entry in battle.initiative_order if entry.actor_id == "player")
        self.assertEqual(16, trainer_entry.total)

    def test_trainer_features_are_synced_onto_controlled_pokemon(self) -> None:
        battle = _battle_with_feature({"feature_id": "attack-ace", "name": "Attack Ace"})
        actor = battle.pokemon["player-1"]
        self.assertTrue(actor.has_trainer_feature("Attack Ace"))

    def test_attack_ace_increases_physical_attack_by_level_scaled_bonus(self) -> None:
        battle = _battle_with_feature({"feature_id": "attack-ace", "name": "Attack Ace"})
        actor = battle.pokemon["player-1"]
        self.assertEqual(15, offensive_stat(actor, "physical"))

    def test_trainer_edges_are_synced_onto_controlled_pokemon(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    edges=[{"feature_id": "awareness", "name": "Awareness"}],
                ),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("PlayerMon"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        self.assertTrue(battle.pokemon["player-1"].has_trainer_feature("Awareness"))

    def test_awareness_adds_to_pokemon_save_checks(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    edges=[{"feature_id": "awareness", "name": "Awareness"}],
                ),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("PlayerMon"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        self.assertEqual(2, battle.pokemon["player-1"].save_bonus(battle))

    def test_smooth_applies_trainer_save_and_social_evasion_bonuses(self) -> None:
        trainer = TrainerState(
            identifier="player",
            name="Player",
            controller_kind="player",
            team="players",
            save_bonus_base=1,
            edges=[{"feature_id": "smooth", "name": "Smooth"}],
        )
        self.assertEqual(1, trainer.save_bonus())
        self.assertEqual(3, trainer.save_bonus("Enraged"))
        self.assertEqual(3, trainer.save_bonus("Infatuated"))
        self.assertEqual(4, trainer.social_evasion_bonus())

    def test_trainer_avatar_with_smooth_gets_social_move_evasion(self) -> None:
        social_move = MoveSpec(
            name="Cutting Remark",
            type="Normal",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
            keywords=["Social"],
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players"),
                "foe": TrainerState(
                    identifier="foe",
                    name="Foe",
                    controller_kind="ai",
                    team="foes",
                    edges=[{"feature_id": "smooth", "name": "Smooth"}],
                ),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Attacker", moves=[social_move]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"]),
                    controller_id="foe",
                    position=(1, 3),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4]),
        )
        target = battle.pokemon["foe-1"]
        before_hp = target.hp
        UseMoveAction(actor_id="player-1", move_name="Cutting Remark", target_id="foe-1").resolve(battle)
        self.assertEqual(before_hp, target.hp)

    def test_trainer_avatar_inherits_trainer_save_bonus(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    save_bonus_base=1,
                    edges=[{"feature_id": "smooth", "name": "Smooth"}],
                ),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        self.assertEqual(1, battle.pokemon["player-1"].save_bonus(battle))
        self.assertEqual(3, battle.pokemon["player-1"].save_bonus(battle, "Enraged"))

    def test_trainer_avatar_with_blur_requires_accuracy_roll(self) -> None:
        attacker = PokemonState(
            spec=_mon(
                "Attacker",
                moves=[
                    MoveSpec(
                        name="Slam",
                        type="Normal",
                        category="Physical",
                        db=8,
                        ac=None,
                        range_kind="Melee",
                        range_value=1,
                        target_kind="Melee",
                        target_range=1,
                    )
                ],
            ),
            controller_id="player",
            position=(1, 1),
        )
        defender = PokemonState(
            spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Blur"}]),
            controller_id="foe",
            position=(1, 2),
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={"player-1": attacker, "foe-1": defender},
            rng=_FixedRng([2]),
        )
        before_hp = defender.hp
        UseMoveAction(actor_id="player-1", move_name="Slam", target_id="foe-1").resolve(battle)
        self.assertEqual(before_hp, defender.hp)

    def test_flustering_charisma_applies_volatile_save_penalty_on_social_hit(self) -> None:
        social_move = MoveSpec(
            name="Needling Joke",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
            keywords=["Social"],
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Flustering Charisma"}], moves=[social_move]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([12]),
        )
        target = battle.pokemon["foe-1"]
        UseMoveAction(actor_id="player-1", move_name="Needling Joke", target_id="foe-1").resolve(battle)
        self.assertEqual(-2, target.save_bonus(battle, "Infatuated"))
        self.assertTrue(
            any(
                evt.get("feature") == "Flustering Charisma" and evt.get("effect") == "save_penalty"
                for evt in battle.log
            )
        )

    def test_powerful_motivator_leer_applies_slowed_on_miss(self) -> None:
        leer = MoveSpec(
            name="Leer",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Cone",
            range_value=2,
            target_kind="Cone",
            target_range=2,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Powerful Motivator"}], moves=[leer]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([1]),
        )
        UseMoveAction(actor_id="player-1", move_name="Leer", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Slowed"))

    def test_powerful_motivator_baby_doll_eyes_blocks_critical_strikes_on_miss(self) -> None:
        baby_doll_eyes = MoveSpec(
            name="Baby-Doll Eyes",
            type="Fairy",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
            crit_range=18,
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Powerful Motivator"}], moves=[baby_doll_eyes]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon", moves=[slash]), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([1, 20]),
        )
        UseMoveAction(actor_id="player-1", move_name="Baby-Doll Eyes", target_id="foe-1").resolve(battle)
        UseMoveAction(actor_id="foe-1", move_name="Slash", target_id="player-1").resolve(battle)
        move_event = next(
            evt for evt in battle.log if evt.get("type") == "move" and evt.get("actor") == "foe-1" and evt.get("move") == "Slash"
        )
        self.assertFalse(move_event.get("crit"))

    def test_powerful_motivator_lovely_kiss_applies_save_penalty_on_miss(self) -> None:
        lovely_kiss = MoveSpec(
            name="Lovely Kiss",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Powerful Motivator"}], moves=[lovely_kiss]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([1]),
        )
        UseMoveAction(actor_id="player-1", move_name="Lovely Kiss", target_id="foe-1").resolve(battle)
        self.assertEqual(-3, battle.pokemon["foe-1"].save_bonus(battle, "Infatuated"))

    def test_powerful_motivator_torment_penalizes_damage_only_against_attacker_allies(self) -> None:
        torment = MoveSpec(
            name="Torment",
            type="Dark",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
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
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Powerful Motivator"}], moves=[torment]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("AllyMon"), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("FoeMon", moves=[tackle]), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([1, 12]),
        )
        UseMoveAction(actor_id="player-1", move_name="Torment", target_id="foe-1").resolve(battle)
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-2").resolve(battle)
        self.assertTrue(
            any(
                evt.get("effect") == "damage_penalty"
                and evt.get("ability") == "Powerful Motivator"
                and evt.get("actor") == "foe-1"
                for evt in battle.log
            )
        )

    def test_menace_terrorize_sets_target_initiative_to_zero_until_next_turn(self) -> None:
        actor_spec = _mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Menace"}])
        actor_spec.skills["intimidate"] = 5
        target_spec = _mon("FoeMon")
        target_spec.skills["intimidate"] = 0
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=actor_spec, controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=target_spec, controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([12, 2]),
        )
        battle.start_round()
        battle.resolve_manipulate_action("player-1", "Terrorize", "foe-1")
        self.assertTrue(battle.pokemon["foe-1"].get_temporary_effects("initiative_zero_until_turn"))
        foe_entry = next(entry for entry in battle.initiative_order if entry.actor_id == "foe-1")
        self.assertEqual(0, foe_entry.total)

    def test_menace_causes_attacks_against_target_to_flinch_on_seventeen_plus(self) -> None:
        actor_spec = _mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Menace"}])
        actor_spec.skills["intimidate"] = 5
        target_spec = _mon("FoeMon")
        target_spec.skills["intimidate"] = 0
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
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=actor_spec, controller_id="player", position=(1, 1)),
                "player-2": PokemonState(spec=_mon("AllyMon", moves=[tackle]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=target_spec, controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([12, 2, 17]),
        )
        battle.resolve_manipulate_action("player-1", "Terrorize", "foe-1")
        UseMoveAction(actor_id="player-2", move_name="Tackle", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Flinch"))
        self.assertTrue(
            any(
                evt.get("feature") == "Menace" and evt.get("effect") == "flinch"
                for evt in battle.log
            )
        )

    def test_manipulate_uses_trainer_state_skills_for_trainer_avatars(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    skills={"guile": 5},
                ),
                "foe": TrainerState(
                    identifier="foe",
                    name="Foe",
                    controller_kind="ai",
                    team="foes",
                    skills={"focus": 0},
                ),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("FoeTrainer", tags=["trainer"]),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([8, 10]),
        )
        battle.resolve_manipulate_action("player-1", "Bon Mot", "foe-1")
        self.assertTrue(battle.pokemon["foe-1"].has_status("Enraged"))
        self.assertTrue(
            any(
                evt.get("effect") == "bon_mot" and evt.get("result") == "success"
                for evt in battle.log
            )
        )

    def test_manipulate_is_once_per_scene_per_target_without_expert_manipulator(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    skills={"guile": 5},
                ),
                "foe": TrainerState(
                    identifier="foe",
                    name="Foe",
                    controller_kind="ai",
                    team="foes",
                    skills={"focus": 0},
                ),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("FoeTrainer", tags=["trainer"]),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([1, 20]),
        )
        battle.resolve_manipulate_action("player-1", "Bon Mot", "foe-1")
        battle.resolve_manipulate_action("player-1", "Bon Mot", "foe-1")
        self.assertTrue(
            any(
                evt.get("effect") == "bon_mot" and evt.get("result") == "blocked"
                for evt in battle.log
            )
        )

    def test_expert_manipulator_adds_bonus_and_failure_does_not_consume_use(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    skills={"guile": 0},
                    edges=[{"name": "Expert Manipulator"}],
                ),
                "foe": TrainerState(
                    identifier="foe",
                    name="Foe",
                    controller_kind="ai",
                    team="foes",
                    skills={"focus": 2},
                ),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("FoeTrainer", tags=["trainer"]),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([10, 11, 12, 1]),
        )
        battle.resolve_manipulate_action("player-1", "Bon Mot", "foe-1")
        self.assertFalse(
            any(
                entry.get("target") == "foe-1" and entry.get("trick") == "bon mot"
                for entry in battle.pokemon["player-1"].get_temporary_effects("manipulate_used")
            )
        )
        battle.resolve_manipulate_action("player-1", "Bon Mot", "foe-1")
        self.assertTrue(battle.pokemon["foe-1"].has_status("Enraged"))
        success_event = next(
            evt for evt in battle.log if evt.get("effect") == "bon_mot" and evt.get("result") == "success"
        )
        self.assertEqual(14, success_event.get("attacker_total"))

    def test_quick_wit_allows_swift_manipulate_with_scene_limit(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Quick Wit"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeTrainer", tags=["trainer"]), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 1, 20, 1, 20, 1]),
        )
        for _ in range(3):
            action = QuickWitManipulateAction("player-1", "Bon Mot", "foe-1")
            action.resolve(battle)
            battle.pokemon["player-1"].actions_taken.clear()
            battle.pokemon["foe-1"].remove_status_by_names({"enraged"})
            battle.pokemon["player-1"].temporary_effects = [
                entry for entry in battle.pokemon["player-1"].temporary_effects if entry.get("kind") != "manipulate_used"
            ]
        self.assertEqual(3, battle._feature_scene_use_count(battle.pokemon["player-1"], "Quick Wit"))
        with self.assertRaises(ValueError):
            QuickWitManipulateAction("player-1", "Bon Mot", "foe-1").validate(battle)

    def test_quick_wit_allows_social_move_as_swift_action(self) -> None:
        confide = MoveSpec(
            name="Confide",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
            keywords=["Social"],
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Quick Wit"}], moves=[confide]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4]),
        )
        action = QuickWitMoveAction("player-1", "Confide", target_id="foe-1")
        action.resolve(battle)
        self.assertTrue(
            any(evt.get("feature") == "Quick Wit" and evt.get("effect") == "swift_social_move" for evt in battle.log)
        )

    def test_trainer_feature_action_factory_builds_quick_wit_move(self) -> None:
        action = create_trainer_feature_action(
            "quick_wit_move",
            actor_id="player-1",
            move_name="Confide",
            target_id="foe-1",
        )
        self.assertIsInstance(action, QuickWitMoveAction)

    def test_enchanting_gaze_applies_manipulate_to_all_foes_in_cone(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Enchanting Gaze"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeA", tags=["trainer"]), controller_id="foe", position=(2, 1)),
                "foe-2": PokemonState(spec=_mon("FoeB", tags=["trainer"]), controller_id="foe", position=(3, 1)),
                "foe-3": PokemonState(spec=_mon("FoeC", tags=["trainer"]), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=random.Random(3),
        )
        action = EnchantingGazeAction("player-1", "Bon Mot", "foe-1")
        action.resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Enraged"))
        self.assertTrue(battle.pokemon["foe-2"].has_status("Enraged"))
        self.assertFalse(battle.pokemon["foe-3"].has_status("Enraged"))
        self.assertEqual(1, battle.trainers["player"].ap)

    def test_trickster_grants_follow_up_after_status_move_hit(self) -> None:
        confide = MoveSpec(
            name="Confide",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
            keywords=["Social"],
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", skills={"guile": 5}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes", skills={"focus": 0}),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Partner", moves=[confide], features=[{"name": "Trickster"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeTrainer", tags=["trainer"]), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4, 10, 1]),
        )
        UseMoveAction(actor_id="player-1", move_name="Confide", target_id="foe-1").resolve(battle)
        self.assertTrue(any(entry.get("target") == "foe-1" for entry in battle.pokemon["player-1"].get_temporary_effects("trickster_ready")))
        TricksterFollowUpAction("player-1", "Bon Mot", "foe-1", "manipulate").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Enraged"))

    def test_trickster_follow_up_uses_trainer_guile_for_manipulate(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", skills={"guile": 5}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes", skills={"focus": 0}),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Partner", features=[{"name": "Trickster"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeTrainer", tags=["trainer"]), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([8, 10]),
        )
        battle.pokemon["player-1"].add_temporary_effect("trickster_ready", target="foe-1", trigger="status_move", expires_round=0)
        TricksterFollowUpAction("player-1", "Bon Mot", "foe-1", "manipulate").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Enraged"))

    def test_trickster_grants_follow_up_after_hazard_trigger(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Partner", features=[{"name": "Trickster"}]), controller_id="player", position=(0, 0)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 1)),
            },
            grid=GridState(width=3, height=3, tiles={(1, 1): {"hazards": {"spikes": 1}, "hazard_sources": {"spikes": "player-1"}}}),
            rng=random.Random(3),
        )
        battle.pokemon["foe-1"].handle_phase_effects(battle, TurnPhase.START, "foe-1")
        self.assertTrue(any(entry.get("target") == "foe-1" for entry in battle.pokemon["player-1"].get_temporary_effects("trickster_ready")))

    def test_trickster_dirty_trick_follow_up_applies_hindered(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Partner", features=[{"name": "Trickster"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([10, 1]),
        )
        battle.pokemon["player-1"].add_temporary_effect("trickster_ready", target="foe-1", trigger="status_move", expires_round=0)
        TricksterFollowUpAction("player-1", "Hinder", "foe-1", "dirty_trick").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Hindered"))

    def test_dirty_fighting_grants_follow_up_after_weapon_attack_hit(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Dirty Fighting"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([5, 10, 10]),
        )
        battle.pokemon["player-1"].spec.items = [{"name": "Axe"}]
        EquipWeaponAction(actor_id="player-1", item_index=0).resolve(battle)
        UseMoveAction(actor_id="player-1", move_name="Axe Swing", target_id="foe-1").resolve(battle)
        self.assertTrue(
            any(
                entry.get("target") == "foe-1"
                for entry in battle.pokemon["player-1"].get_temporary_effects("dirty_fighting_ready")
            )
        )

    def test_dirty_fighting_follow_up_spends_ap_and_applies_hinder(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Dirty Fighting"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([10, 1]),
        )
        battle.pokemon["player-1"].add_temporary_effect("dirty_fighting_ready", target="foe-1", expires_round=0)
        DirtyFightingFollowUpAction("player-1", "Hinder", "foe-1").resolve(battle)
        self.assertEqual(1, battle.trainers["player"].ap)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Hindered"))
        self.assertFalse(battle.pokemon["player-1"].get_temporary_effects("dirty_fighting_ready"))

    def test_malice_grants_mean_look_and_chip_away_to_trainer_avatar(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Malice"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        move_names = {str(move.name or "").strip() for move in battle.pokemon["player-1"].spec.moves}
        self.assertIn("Mean Look", move_names)
        self.assertIn("Chip Away", move_names)

    def test_cruel_gaze_grants_glare_and_headbutt_to_trainer_avatar(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Cruel Gaze"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        move_names = {str(move.name or "").strip() for move in battle.pokemon["player-1"].spec.moves}
        self.assertIn("Glare", move_names)
        self.assertIn("Headbutt", move_names)

    def test_mixed_messages_grants_lovely_kiss_and_torment(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Mixed Messages"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        move_names = {str(move.name or "").strip() for move in battle.pokemon["player-1"].spec.moves}
        self.assertIn("Lovely Kiss", move_names)
        self.assertIn("Torment", move_names)

    def test_weapon_finesse_grants_follow_up_after_weapon_attack_hit(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Weapon Finesse"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([5, 10, 10]),
        )
        battle.pokemon["player-1"].spec.items = [{"name": "Axe"}]
        EquipWeaponAction(actor_id="player-1", item_index=0).resolve(battle)
        UseMoveAction(actor_id="player-1", move_name="Axe Swing", target_id="foe-1").resolve(battle)
        self.assertTrue(
            any(
                entry.get("target") == "foe-1"
                for entry in battle.pokemon["player-1"].get_temporary_effects("weapon_finesse_ready")
            )
        )

    def test_weapon_finesse_follow_up_spends_ap_and_uses_trip(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Weapon Finesse"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([1, 10]),
        )
        battle.pokemon["player-1"].add_temporary_effect("weapon_finesse_ready", target="foe-1", expires_round=0)
        WeaponFinesseFollowUpAction("player-1", "Trip", "foe-1").resolve(battle)
        self.assertEqual(1, battle.trainers["player"].ap)
        self.assertFalse(battle.pokemon["player-1"].get_temporary_effects("weapon_finesse_ready"))
        self.assertTrue(any(evt.get("move") == "Trip" for evt in battle.log if evt.get("type") == "move"))

    def test_play_them_like_a_fiddle_grants_follow_up_after_confide_hit(self) -> None:
        confide = MoveSpec(
            name="Confide",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
            keywords=["Social"],
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Play Them Like a Fiddle"}], moves=[confide]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4]),
        )
        UseMoveAction(actor_id="player-1", move_name="Confide", target_id="foe-1").resolve(battle)
        ready = battle.pokemon["player-1"].get_temporary_effects("play_them_like_a_fiddle_ready")
        self.assertTrue(any(str(entry.get("move") or "").strip().lower() == "confide" for entry in ready))

    def test_play_them_like_a_fiddle_confide_disables_chosen_move(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Play Them Like a Fiddle"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        battle.pokemon["foe-1"].add_temporary_effect("move_used", name="Tackle")
        battle.pokemon["player-1"].add_temporary_effect(
            "play_them_like_a_fiddle_ready",
            target="foe-1",
            move="Confide",
            expires_round=0,
        )
        PlayThemLikeAFiddleFollowUpAction("player-1", "foe-1", "Confide", chosen_move="Tackle").resolve(battle)
        disabled = [
            status
            for status in battle.pokemon["foe-1"].statuses
            if isinstance(status, dict) and str(status.get("name") or "").strip().lower() == "disabled"
        ]
        self.assertTrue(any(str(status.get("move") or "").strip().lower() == "tackle" for status in disabled))

    def test_play_them_like_a_fiddle_baby_doll_eyes_infatuation_survives_take_breather(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Play Them Like a Fiddle"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        battle.pokemon["player-1"].add_temporary_effect(
            "play_them_like_a_fiddle_ready",
            target="foe-1",
            move="Baby-Doll Eyes",
            expires_round=0,
        )
        PlayThemLikeAFiddleFollowUpAction("player-1", "foe-1", "Baby-Doll Eyes").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Infatuated"))
        battle.apply_take_breather("foe-1")
        self.assertTrue(battle.pokemon["foe-1"].has_status("Infatuated"))

    def test_play_them_like_a_fiddle_sweet_kiss_blocks_disengage_while_confused(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Play Them Like a Fiddle"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        battle.pokemon["foe-1"].statuses.append({"name": "Confused", "remaining": 1})
        battle.pokemon["player-1"].add_temporary_effect("play_them_like_a_fiddle_ready", target="foe-1", move="Sweet Kiss", expires_round=0)
        PlayThemLikeAFiddleFollowUpAction("player-1", "foe-1", "Sweet Kiss").resolve(battle)
        with self.assertRaises(ValueError):
            PokemonState.DisengageAction("foe-1", (2, 2)).validate(battle)

    def test_play_them_like_a_fiddle_taunt_boosts_next_damage_hit(self) -> None:
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
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Play Them Like a Fiddle"}]), controller_id="player", position=(1, 1)),
                "ally-1": PokemonState(spec=_mon("AllyMon", moves=[tackle]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([10, 1, 1, 1]),
        )
        battle.pokemon["player-1"].add_temporary_effect("play_them_like_a_fiddle_ready", target="foe-1", move="Taunt", expires_round=0)
        PlayThemLikeAFiddleFollowUpAction("player-1", "foe-1", "Taunt").resolve(battle)
        UseMoveAction(actor_id="ally-1", move_name="Tackle", target_id="foe-1").resolve(battle)
        self.assertFalse(battle.pokemon["foe-1"].get_temporary_effects("play_them_like_a_fiddle_taunt"))
        taunt_event = next(evt for evt in battle.log if evt.get("effect") == "taunt_damage_bonus")
        self.assertGreaterEqual(int(taunt_event.get("amount", 0) or 0), 13)

    def test_psychic_resonance_grants_follow_up_after_psychic_status_hit(self) -> None:
        psychic_move = MoveSpec(
            name="Mind Glint",
            type="Psychic",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Caster", features=[{"name": "Psychic Resonance"}], moves=[psychic_move]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4]),
        )
        UseMoveAction(actor_id="player-1", move_name="Mind Glint", target_id="foe-1").resolve(battle)
        self.assertTrue(any(entry.get("target") == "foe-1" for entry in battle.pokemon["player-1"].get_temporary_effects("psychic_resonance_ready")))

    def test_psychic_resonance_follow_up_uses_encore(self) -> None:
        encore = MoveSpec(
            name="Encore",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Caster", features=[{"name": "Psychic Resonance"}], moves=[encore]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4]),
        )
        battle.pokemon["player-1"].add_temporary_effect("psychic_resonance_ready", target="foe-1", expires_round=0)
        PsychicResonanceFollowUpAction("player-1", "foe-1").resolve(battle)
        self.assertTrue(any(evt.get("feature") == "Psychic Resonance" for evt in battle.log))
        self.assertEqual(battle._feature_scene_use_count(battle.pokemon["player-1"], "Psychic Resonance"), 1)

    def test_phantom_menace_grants_moves_and_weapon_tags_with_melee_weapon(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Phantom Menace"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.items.append({"name": "Practice Sword", "weapon": True, "weapon_type": "melee"})
        actor.equip_weapon(0)
        move_names = {str(move.name or "").strip() for move in actor.spec.moves}
        self.assertIn("Shadow Claw", move_names)
        self.assertIn("Phantom Force", move_names)
        granted = {
            str(entry.get("name") or "").strip()
            for entry in actor.get_temporary_effects("weapon_move_granted")
        }
        self.assertIn("Shadow Claw", granted)
        self.assertIn("Phantom Force", granted)

    def test_shadow_arms_uses_shared_weaponized_move_grant_path(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Shadow Arms"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.items.append({"name": "Knife", "weapon": True, "weapon_type": "melee"})
        actor.equip_weapon(0)
        granted = {
            str(entry.get("name") or "").strip()
            for entry in actor.get_temporary_effects("weapon_move_granted")
        }
        self.assertIn("Shadow Punch", granted)
        self.assertIn("Shadow Sneak", granted)

    def test_berserker_uses_shared_weaponized_move_grant_path(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Berserker"}, {"name": "Crash and Smash"}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.items.append({"name": "Greataxe", "weapon": True, "weapon_type": "melee"})
        actor.equip_weapon(0)
        move_names = {str(move.name or "").strip() for move in actor.spec.moves}
        self.assertIn("Rage", move_names)
        self.assertIn("Flail", move_names)
        self.assertIn("Double-Edge", move_names)
        self.assertIn("Thrash", move_names)
        granted = {
            str(entry.get("name") or "").strip()
            for entry in actor.get_temporary_effects("weapon_move_granted")
        }
        self.assertIn("Rage", granted)
        self.assertIn("Flail", granted)
        self.assertIn("Double-Edge", granted)
        self.assertIn("Thrash", granted)

    def test_static_move_grant_features_add_expected_moves(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[
                            {"name": "Provocateur"},
                            {"name": "Tough as Nails"},
                            {"name": "Prism"},
                            {"name": "Sparkle"},
                            {"name": "Glamour Weaver"},
                            {"name": "Passionato Harmony"},
                            {"name": "Miasmic"},
                            {"name": "Miasma's Call"},
                            {"name": "Miasma Unleashed"},
                            {"name": "Mt. Moon Blues"},
                            {"name": "Ninja"},
                            {"name": "Kinjutsu"},
                            {"name": "Mystic Defense"},
                            {"name": "Sacred Shield"},
                            {"name": "PK Alpha"},
                            {"name": "Honed Mind"},
                            {"name": "Mental Assault"},
                            {"name": "Stone Warrior"},
                            {"name": "Shards of Stone"},
                            {"name": "Stone Cold Finish"},
                            {"name": "Item Mastery"},
                            {"name": "Wall of Iron"},
                            {"name": "Cacophony"},
                            {"name": "Noise Complaint"},
                            {"name": "Rainbow Surge"},
                            {"name": "PK Omega"},
                            {"name": "Aerialist"},
                            {"name": "Death From Above"},
                            {"name": "Space Distortion"},
                            {"name": "Warping Ground"},
                            {"name": "Strange Energy"},
                            {"name": "Null Error"},
                            {"name": "Glitch Shuffle"},
                            {"name": "Lucky Clover Grand Finale"},
                            {"name": "Hidden Power"},
                        ],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(5),
        )
        battle._sync_trainer_features_to_pokemon()
        battle._sync_trainer_feature_moves_to_pokemon()
        move_names = {str(move.name or "").strip() for move in battle.pokemon["player-1"].spec.moves}
        self.assertIn("Sweet Kiss", move_names)
        self.assertIn("Taunt", move_names)
        self.assertIn("Endure", move_names)
        self.assertIn("Slack Off", move_names)
        self.assertIn("Flash", move_names)
        self.assertIn("Swift", move_names)
        self.assertIn("Tri Attack", move_names)
        self.assertIn("Weather Ball", move_names)
        self.assertIn("Disarming Voice", move_names)
        self.assertIn("Dazzling Gleam", move_names)
        self.assertIn("Draining Kiss", move_names)
        self.assertIn("Acid", move_names)
        self.assertIn("Clear Smog", move_names)
        self.assertIn("Acid Armor", move_names)
        self.assertIn("Sludge Bomb", move_names)
        self.assertIn("Sludge Wave", move_names)
        self.assertIn("Toxic", move_names)
        self.assertIn("Sing", move_names)
        self.assertIn("Supersonic", move_names)
        self.assertIn("Double Team", move_names)
        self.assertIn("Poison Powder", move_names)
        self.assertIn("Substitute", move_names)
        self.assertIn("Light Screen", move_names)
        self.assertIn("Safeguard", move_names)
        self.assertIn("Reflect", move_names)
        self.assertIn("Lucky Chant", move_names)
        self.assertIn("Kinesis", move_names)
        self.assertIn("Barrier", move_names)
        self.assertIn("Mind Reader", move_names)
        self.assertIn("Calm Mind", move_names)
        self.assertIn("Extrasensory", move_names)
        self.assertIn("Psyshock", move_names)
        self.assertIn("Rock Tomb", move_names)
        self.assertIn("Wide Guard", move_names)
        self.assertIn("Rock Slide", move_names)
        self.assertIn("Stealth Rock", move_names)
        self.assertIn("Stone Edge", move_names)
        self.assertIn("Head Smash", move_names)
        self.assertIn("Fling", move_names)
        self.assertIn("Recycle", move_names)
        self.assertIn("Iron Defense", move_names)
        self.assertIn("Protect", move_names)
        self.assertIn("Screech", move_names)
        self.assertIn("Metal Sound", move_names)
        self.assertIn("Uproar", move_names)
        self.assertIn("Hyper Voice", move_names)
        self.assertIn("Hyper Beam", move_names)
        self.assertIn("Morning Sun", move_names)
        self.assertIn("Telekinesis", move_names)
        self.assertIn("Psychic", move_names)
        self.assertIn("Aerial Ace", move_names)
        self.assertIn("Splash", move_names)
        self.assertIn("Acrobatics", move_names)
        self.assertIn("Bounce", move_names)
        self.assertIn("Teleport", move_names)
        self.assertIn("Ally Switch", move_names)
        self.assertIn("Gravity", move_names)
        self.assertIn("Trick", move_names)
        self.assertIn("Heal Block", move_names)
        self.assertIn("Magic Coat", move_names)
        self.assertIn("Snatch", move_names)
        self.assertIn("Disable", move_names)
        self.assertIn("Metronome", move_names)
        self.assertIn("Topsy-Turvy", move_names)
        self.assertIn("Moonblast", move_names)
        self.assertIn("Aromatic Mist", move_names)
        self.assertIn("Hidden Power", move_names)

    def test_flight_action_grants_temporary_sky_speed(self) -> None:
        trainer = TrainerState(
            identifier="player",
            name="Player",
            team="players",
            ap=3,
            skills={"acrobatics": 4, "perception": 2},
        )
        battle = BattleState(
            trainers={"player": trainer},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Flight"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(6),
        )
        battle.pokemon["player-1"].spec.movement["levitate"] = 3
        FlightAction("player-1").resolve(battle)
        self.assertEqual(trainer.ap, 2)
        self.assertEqual(battle.pokemon["player-1"].movement_speed("sky"), 7)

    def test_dive_interrupt_shifts_target_and_avoids_ranged_attack(self) -> None:
        water_gun = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Diver", features=[{"name": "Dive"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Shooter", moves=[water_gun]),
                    controller_id="foe",
                    position=(1, 4),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([10]),
        )
        battle.pokemon["player-1"].spec.movement["overland"] = 3
        before_hp = battle.pokemon["player-1"].hp
        battle.out_of_turn_prompt = lambda payload: str(payload.get("feature") or "") == "Dive"
        UseMoveAction(actor_id="foe-1", move_name="Water Gun", target_id="player-1").resolve(battle)
        self.assertEqual(before_hp, battle.pokemon["player-1"].hp)
        self.assertNotEqual((1, 1), battle.pokemon["player-1"].position)
        self.assertTrue(battle.pokemon["player-1"].has_status("Tripped"))
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Dive"))

    def test_coaching_can_force_attack_of_opportunity_to_hit(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=1),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("CoachMon", features=[{"name": "Coaching"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([1]),
        )
        before_hp = battle.pokemon["foe-1"].hp
        battle.out_of_turn_prompt = lambda payload: str(payload.get("feature") or "") == "Coaching"
        battle._perform_attack_of_opportunity("player-1", "foe-1", "maneuver")
        self.assertLess(battle.pokemon["foe-1"].hp, before_hp)
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Coaching"))

    def test_coaching_can_override_intercept_loyalty_with_prompt(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=1),
                "ally": TrainerState(identifier="ally", name="Ally", team="players"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("CoachMon", features=[{"name": "Coaching"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("AllyMon"), controller_id="ally", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(7),
        )
        battle.pokemon["player-1"].spec.loyalty = 4
        battle.out_of_turn_prompt = lambda payload: str(payload.get("feature") or "") == "Coaching"
        action = InterceptAction(actor_id="player-1", kind="ranged", ally_id="ally-1")
        action.validate(battle)
        action.resolve(battle)
        self.assertTrue(battle.pokemon["player-1"].get_temporary_effects("intercept_ready"))
        self.assertEqual(0, battle.trainers["player"].ap)

    def test_defender_reduces_intercept_to_shift_action(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Guardian", features=[{"name": "Defender"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally"), controller_id="player", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(8),
        )
        action = InterceptAction(actor_id="player-1", kind="ranged", ally_id="ally-1")
        action.validate(battle)
        self.assertEqual(ActionType.SHIFT, action.action_type)

    def test_counter_stance_triggers_attack_of_opportunity_after_adjacent_miss(self) -> None:
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
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("CounterMon", features=[{"name": "Counter Stance"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Attacker", moves=[tackle]),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([1, 20]),
        )
        before_hp = battle.pokemon["foe-1"].hp
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-1").resolve(battle)
        self.assertLess(battle.pokemon["foe-1"].hp, before_hp)
        self.assertTrue(any(prompt.get("feature") == "Counter Stance" for prompt in prompts))
        self.assertTrue(
            any(
                event.get("feature") == "Counter Stance" and event.get("effect") == "attack_of_opportunity"
                for event in battle.log
            )
        )

    def test_telepathic_warning_shifts_allied_target_out_of_area_and_spends_ap(self) -> None:
        burst = MoveSpec(
            name="Shockwave Pulse",
            type="Electric",
            category="Special",
            db=6,
            ac=2,
            range_kind="Burst",
            range_value=1,
            target_kind="Self",
            target_range=0,
            area_kind="Burst",
            area_value=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Telepath",
                        moves=[burst],
                        features=[{"name": "Telepathic Warning"}],
                        capabilities=["Telepath"],
                    ),
                    controller_id="player",
                    position=(2, 2),
                ),
                "player-2": PokemonState(
                    spec=_mon("Ally", moves=[burst]),
                    controller_id="player",
                    position=(2, 3),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Foe", moves=[burst]),
                    controller_id="foe",
                    position=(4, 4),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([20]),
        )
        ally = battle.pokemon["player-2"]
        ally.spec.movement["overland"] = 3
        before_hp = ally.hp
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        UseMoveAction(actor_id="player-1", move_name="Shockwave Pulse", target_id="player-1").resolve(battle)
        self.assertEqual(before_hp, ally.hp)
        self.assertNotEqual((2, 3), ally.position)
        self.assertEqual(1, battle.trainers["player"].ap)
        self.assertTrue(ally.get_temporary_effects("psychic_residue"))
        self.assertTrue(any(prompt.get("feature") == "Telepathic Warning" for prompt in prompts))

    def test_harrier_blocks_priority_and_interrupt_actions_after_hit(self) -> None:
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
            freq="At-Will",
        )
        quick_attack = MoveSpec(
            name="Quick Attack",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
            priority=1,
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Harrier", moves=[tackle], features=[{"name": "Harrier"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Target", moves=[quick_attack]),
                    controller_id="foe",
                    position=(1, 2),
                ),
                "foe-2": PokemonState(spec=_mon("Ally"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20]),
        )
        UseMoveAction(actor_id="player-1", move_name="Tackle", target_id="foe-1").resolve(battle)
        target = battle.pokemon["foe-1"]
        self.assertTrue(target.get_temporary_effects("forced_flanked"))
        self.assertTrue(target.get_temporary_effects("priority_blocked"))
        self.assertTrue(target.get_temporary_effects("interrupt_blocked"))
        with self.assertRaises(ValueError):
            UseMoveAction(actor_id="foe-1", move_name="Quick Attack", target_id="player-1").validate(battle)
        with self.assertRaises(ValueError):
            InterceptAction(actor_id="foe-1", kind="melee", ally_id="foe-2").validate(battle)

    def test_mettle_reduces_massive_damage_and_drops_attack_stage(self) -> None:
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=16,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Bruiser", features=[{"name": "Mettle"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Attacker", moves=[slash], level=50),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20]),
        )
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        defender = battle.pokemon["player-1"]
        attacker = battle.pokemon["foe-1"]
        baseline = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Bruiser"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Attacker", moves=[slash], level=50), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20]),
        )
        before_hp = defender.hp
        baseline_before_hp = baseline.pokemon["player-1"].hp
        UseMoveAction(actor_id="foe-1", move_name="Slash", target_id="player-1").resolve(baseline)
        UseMoveAction(actor_id="foe-1", move_name="Slash", target_id="player-1").resolve(battle)
        self.assertLess(defender.hp, before_hp)
        self.assertGreater(defender.hp, baseline.pokemon["player-1"].hp)
        self.assertLess(baseline.pokemon["player-1"].hp, baseline_before_hp)
        self.assertEqual(-2, attacker.combat_stages.get("atk", 0))
        self.assertEqual(1, battle._feature_scene_use_count(defender, "Mettle"))
        self.assertTrue(any(prompt.get("feature") == "Mettle" for prompt in prompts))

    def test_pain_resistance_reduces_damage_based_on_injuries(self) -> None:
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Tank", features=[{"name": "Pain Resistance"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Attacker", moves=[tackle], level=35),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20]),
        )
        baseline = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Tank"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Attacker", moves=[tackle], level=35), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20]),
        )
        battle.pokemon["player-1"].injuries = 2
        baseline.pokemon["player-1"].injuries = 2
        baseline.pokemon["player-1"].hp = baseline.pokemon["player-1"].max_hp_with_injuries()
        battle.pokemon["player-1"].hp = battle.pokemon["player-1"].max_hp_with_injuries()
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-1").resolve(baseline)
        UseMoveAction(actor_id="foe-1", move_name="Tackle", target_id="player-1").resolve(battle)
        self.assertGreater(battle.pokemon["player-1"].hp, baseline.pokemon["player-1"].hp)
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Pain Resistance"))
        self.assertTrue(any(prompt.get("feature") == "Pain Resistance" for prompt in prompts))

    def test_perseverance_prevents_triggering_injury_once_per_scene(self) -> None:
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=16,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Protege", features=[{"name": "Perseverance"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Attacker", moves=[slash], level=50),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20]),
        )
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        UseMoveAction(actor_id="foe-1", move_name="Slash", target_id="player-1").resolve(battle)
        defender = battle.pokemon["player-1"]
        self.assertEqual(0, defender.injuries)
        self.assertEqual(1, battle._feature_scene_use_count(defender, "Perseverance"))
        self.assertTrue(any(prompt.get("feature") == "Perseverance" for prompt in prompts))

    def test_false_strike_leaves_wild_target_at_one_hp(self) -> None:
        finisher = MoveSpec(
            name="Finisher",
            type="Normal",
            category="Physical",
            db=18,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "wild": TrainerState(identifier="wild", name="Wild", team="wild"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Hunter", features=[{"name": "False Strike"}], moves=[finisher]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "wild-1": PokemonState(
                    spec=_mon("Wildling", level=10),
                    controller_id="wild",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20]),
        )
        UseMoveAction(actor_id="player-1", move_name="Finisher", target_id="wild-1").resolve(battle)
        wild_target = battle.pokemon["wild-1"]
        self.assertEqual(1, wild_target.hp)
        self.assertFalse(wild_target.fainted)
        self.assertTrue(any(evt.get("feature") == "False Strike" for evt in battle.log))

    def test_slippery_uses_stealth_to_break_grapple_attempt(self) -> None:
        grapple = MoveSpec(
            name="Grapple",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", skills={"stealth": 4}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes", skills={"combat": 1}),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Sneak", features=[{"name": "Slippery"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Grappler"),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([5, 5]),
        )
        events: list[dict] = []
        success = battle._apply_grapple_contest(
            events,
            attacker_id="foe-1",
            target_id="player-1",
            move=grapple,
            attacker=battle.pokemon["foe-1"],
            defender=battle.pokemon["player-1"],
            effect="grapple",
            description="Grapple attempts to seize the target.",
        )
        self.assertFalse(success)
        self.assertIsNone(battle.grapple_status("player-1"))
        self.assertIsNone(battle.grapple_status("foe-1"))
        self.assertEqual("escape", events[-1]["result"])
        self.assertTrue(events[-1]["defender_used_slippery"])

    def test_tumbler_grants_run_away_ability(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Acrobat", features=[{"name": "Tumbler"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        self.assertTrue(battle.pokemon["player-1"].has_ability("Run Away"))

    def test_chitin_shield_blocks_status_move_and_grants_move_immunity(self) -> None:
        wisp = MoveSpec(
            name="Will-O-Wisp",
            type="Fire",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Beetle", features=[{"name": "Chitin Shield"}], types=["Bug"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Hexer", moves=[wisp], level=30),
                    controller_id="foe",
                    position=(1, 3),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([20, 20]),
        )
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        UseMoveAction(actor_id="foe-1", move_name="Will-O-Wisp", target_id="player-1").resolve(battle)
        defender = battle.pokemon["player-1"]
        self.assertFalse(defender.has_status("Burned"))
        self.assertEqual(1, battle._feature_scene_use_count(defender, "Chitin Shield"))
        self.assertTrue(any(prompt.get("feature") == "Chitin Shield" for prompt in prompts))
        prompt_count = len(prompts)
        UseMoveAction(actor_id="foe-1", move_name="Will-O-Wisp", target_id="player-1").resolve(battle)
        self.assertFalse(defender.has_status("Burned"))
        self.assertEqual(prompt_count, len(prompts))
        self.assertTrue(any(evt.get("feature") == "Chitin Shield" and evt.get("effect") == "move_immunity" for evt in battle.log))

    def test_brightest_flame_adds_burn_on_high_roll(self) -> None:
        ember = MoveSpec(
            name="Flame Jab",
            type="Fire",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Blazer", features=[{"name": "Brightest Flame"}], moves=[ember]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Target", level=30),
                    controller_id="foe",
                    position=(1, 3),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([20] * 12),
        )
        UseMoveAction(actor_id="player-1", move_name="Flame Jab", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Burned"))
        self.assertTrue(any(evt.get("feature") == "Brightest Flame" for evt in battle.log))

    def test_corrosive_blight_inflicts_blight_on_poison_hit(self) -> None:
        acid = MoveSpec(
            name="Acid",
            type="Poison",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Venomer", features=[{"name": "Corrosive Blight"}], moves=[acid]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Target", level=30),
                    controller_id="foe",
                    position=(1, 3),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([20, 20]),
        )
        UseMoveAction(actor_id="player-1", move_name="Acid", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Blight"))
        self.assertTrue(any(evt.get("feature") == "Corrosive Blight" for evt in battle.log))

    def test_nimble_steps_makes_disengage_a_swift_action(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Skirmisher", features=[{"name": "Nimble Steps"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        battle.pokemon["player-1"].spec.movement["overland"] = 3
        action = DisengageAction(actor_id="player-1", destination=(1, 2))
        action.validate(battle)
        self.assertEqual(ActionType.SWIFT, action.action_type)

    def test_deadly_gambit_counters_melee_attack_before_damage_resolves(self) -> None:
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
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Gambler", moves=[slash], features=[{"name": "Deadly Gambit"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Attacker", moves=[slash], level=40),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 20]),
        )
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        defender_before_hp = battle.pokemon["player-1"].hp
        attacker_before_hp = battle.pokemon["foe-1"].hp
        UseMoveAction(actor_id="foe-1", move_name="Slash", target_id="player-1").resolve(battle)
        self.assertLess(battle.pokemon["player-1"].hp, defender_before_hp)
        self.assertLess(battle.pokemon["foe-1"].hp, attacker_before_hp)
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Deadly Gambit"))
        self.assertTrue(any(prompt.get("feature") == "Deadly Gambit" for prompt in prompts))
        self.assertTrue(
            any(
                event.get("feature") == "Deadly Gambit" and event.get("effect") == "counterattack"
                for event in battle.log
            )
        )

    def test_quick_gymnastics_on_stand_skips_aoo_and_grants_immunity(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=1),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Gymnast", features=[{"name": "Quick Gymnastics"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Threat"),
                    controller_id="foe",
                    position=(1, 2),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["overland"] = 3
        actor.statuses.append({"name": "Tripped"})
        before_hp = actor.hp
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        ShiftAction(actor_id="player-1", destination=(1, 1)).resolve(battle)
        self.assertEqual(before_hp, actor.hp)
        self.assertFalse(actor.has_status("Tripped"))
        self.assertTrue(actor.get_temporary_effects("aoo_immunity"))
        self.assertTrue(actor.get_temporary_effects("flank_immunity"))
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(any(prompt.get("feature") == "Quick Gymnastics" for prompt in prompts))

    def test_quick_switch_action_swaps_to_benched_ally(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Lead", features=[{"name": "Quick Switch"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                    active=True,
                ),
                "player-2": PokemonState(
                    spec=_mon("Bench"),
                    controller_id="player",
                    position=None,
                    active=False,
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(5),
        )
        action = QuickSwitchAction(actor_id="player-1", replacement_id="player-2")
        action.validate(battle)
        action.resolve(battle)
        self.assertFalse(battle.pokemon["player-1"].active)
        self.assertTrue(battle.pokemon["player-2"].active)
        self.assertEqual((1, 1), battle.pokemon["player-2"].position)
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(battle.pokemon["player-2"].get_temporary_effects("quick_switch_sent_out"))

    def test_quick_switch_triggers_when_ally_faints(self) -> None:
        slash = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Lead", features=[{"name": "Quick Switch"}], tags=["trainer"], moves=[slash]),
                    controller_id="player",
                    position=(1, 1),
                    active=True,
                ),
                "player-ally": PokemonState(
                    spec=_mon("Ally"),
                    controller_id="player",
                    position=(1, 2),
                    active=True,
                    hp=10,
                ),
                "player-2": PokemonState(
                    spec=_mon("Bench"),
                    controller_id="player",
                    position=None,
                    active=False,
                ),
                "foe-1": PokemonState(
                    spec=_mon("Target", moves=[slash]),
                    controller_id="foe",
                    position=(2, 2),
                    active=True,
                ),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([20, 20]),
        )
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or {"accept": True, "choice": "player-2"}
        UseMoveAction(actor_id="foe-1", move_name="Slash", target_id="player-ally").resolve(battle)
        self.assertTrue(battle.pokemon["player-ally"].fainted)
        self.assertFalse(battle.pokemon["player-1"].active)
        self.assertTrue(battle.pokemon["player-2"].active)
        self.assertEqual((1, 1), battle.pokemon["player-2"].position)
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(any(prompt.get("feature") == "Quick Switch" and prompt.get("trigger") == "ally_faint" for prompt in prompts))

    def test_long_jump_action_triggers_quick_gymnastics(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=1),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Gymnast", features=[{"name": "Quick Gymnastics"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Threat"),
                    controller_id="foe",
                    position=(4, 4),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(7),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["l_jump"] = 2
        actor.spec.movement["overland"] = 3
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        JumpAction(actor_id="player-1", destination=(3, 1), jump_kind="long").resolve(battle)
        self.assertNotEqual((3, 1), actor.position)
        self.assertEqual(0, battle.trainers["player"].ap)
        self.assertTrue(actor.get_temporary_effects("aoo_immunity"))
        self.assertTrue(any(prompt.get("feature") == "Quick Gymnastics" and prompt.get("trigger") == "jump" for prompt in prompts))

    def test_high_jump_action_uses_high_jump_range(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Jumper"), controller_id="player", position=(1, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(9),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["h_jump"] = 2
        actor.spec.movement["l_jump"] = 0
        action = JumpAction(actor_id="player-1", destination=(1, 3), jump_kind="high")
        action.validate(battle)
        action.resolve(battle)
        self.assertEqual((1, 3), actor.position)

    def test_telepath_action_grants_capability_for_scene(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Telepath", features=[{"name": "Telepath"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(10),
        )
        action = create_trainer_feature_action("telepath", actor_id="player-1")
        action.validate(battle)
        action.resolve(battle)
        self.assertTrue(battle.pokemon["player-1"].has_capability("Telepath"))
        self.assertEqual(0, battle.trainers["player"].ap)

    def test_telepathic_awareness_grants_chosen_ability(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Telepath",
                        features=[{"name": "Telepathic Awareness", "choice": "Gentle Vibe"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(11),
        )
        self.assertTrue(battle.pokemon["player-1"].has_ability("Gentle Vibe"))

    def test_thought_detection_counts_nearby_living_minds(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2, skills={"focus": 2})},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Telepath",
                        features=[{"name": "Telepath"}, {"name": "Thought Detection"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally"), controller_id="player", position=(3, 1)),
                "foe-1": PokemonState(spec=_mon("Foe"), controller_id="foe", position=(5, 1)),
                "foe-2": PokemonState(spec=_mon("Mindlocked", capabilities=["Mindlock"]), controller_id="foe", position=(2, 2)),
            },
            grid=GridState(width=8, height=8),
            rng=random.Random(12),
        )
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        action = create_trainer_feature_action("thought_detection", actor_id="player-1")
        action.validate(battle)
        action.resolve(battle)
        event = next(evt for evt in reversed(battle.log) if evt.get("feature") == "Thought Detection")
        self.assertEqual(2, event.get("count"))
        self.assertEqual(0, battle._feature_scene_use_count(battle.pokemon["player-1"], "Telepath"))
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Thought Detection"))

    def test_kip_up_makes_standing_a_swift_action(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Acrobat", features=[{"name": "Kip Up"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(13),
        )
        battle.pokemon["player-1"].statuses.append({"name": "Tripped"})
        action = ShiftAction(actor_id="player-1", destination=(1, 1))
        action.validate(battle)
        self.assertEqual(ActionType.SWIFT, action.action_type)

    def test_suggestion_binds_text_and_leaves_psychic_residue(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3, skills={"focus": 1})},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Telepath",
                        features=[{"name": "Telepath"}, {"name": "Suggestion"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(14),
        )
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        action = create_trainer_feature_action(
            "suggestion",
            actor_id="player-1",
            target_id="foe-1",
            suggestion_text="Retreat from the chokepoint.",
        )
        action.validate(battle)
        action.resolve(battle)
        target = battle.pokemon["foe-1"]
        self.assertTrue(target.get_temporary_effects("suggestion_bound"))
        self.assertTrue(target.get_temporary_effects("psychic_residue"))
        self.assertEqual(0, battle.trainers["player"].ap)

    def test_suggestion_rebinds_and_release_clears_binding(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=5, skills={"focus": 1})},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Telepath", features=[{"name": "Telepath"}, {"name": "Suggestion"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("TargetA"), controller_id="foe", position=(2, 1)),
                "foe-2": PokemonState(spec=_mon("TargetB"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(14),
        )
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        create_trainer_feature_action("suggestion", actor_id="player-1", target_id="foe-1", suggestion_text="First thought.").resolve(battle)
        create_trainer_feature_action("suggestion", actor_id="player-1", target_id="foe-2", suggestion_text="Second thought.").resolve(battle)
        self.assertFalse(battle.pokemon["foe-1"].get_temporary_effects("suggestion_bound"))
        self.assertTrue(battle.pokemon["foe-2"].get_temporary_effects("suggestion_bound"))
        create_trainer_feature_action("release_suggestion", actor_id="player-1").resolve(battle)
        self.assertFalse(battle.pokemon["foe-2"].get_temporary_effects("suggestion_bound"))
        self.assertFalse(battle.pokemon["player-1"].get_temporary_effects("feature_bound"))
        self.assertTrue(any(evt.get("feature") == "Suggestion" and evt.get("effect") == "release" for evt in battle.log))

    def test_thought_detection_surfaces_bound_suggestion(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3, skills={"focus": 1})},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Telepath",
                        features=[{"name": "Telepath"}, {"name": "Suggestion"}, {"name": "Thought Detection"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(14),
        )
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        create_trainer_feature_action(
            "suggestion",
            actor_id="player-1",
            target_id="foe-1",
            suggestion_text="Retreat from the chokepoint.",
        ).resolve(battle)
        create_trainer_feature_action("thought_detection", actor_id="player-1").resolve(battle)
        event = next(evt for evt in reversed(battle.log) if evt.get("feature") == "Thought Detection")
        self.assertEqual(["foe-1"], event.get("residue_targets"))
        surfaced = event.get("surface_thoughts") or []
        self.assertEqual("foe-1", surfaced[0].get("target"))
        self.assertEqual("Retreat from the chokepoint.", surfaced[0].get("suggestion"))

    def test_psionic_analysis_identifies_psionic_source(self) -> None:
        extrasensory = MoveSpec(
            name="Extrasensory",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3, skills={"focus": 1})},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Telepath",
                        features=[{"name": "Telepath"}, {"name": "Suggestion"}, {"name": "Psionic Analysis"}],
                        tags=["trainer"],
                        moves=[extrasensory],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(21),
        )
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        create_trainer_feature_action(
            "suggestion",
            actor_id="player-1",
            target_id="foe-1",
            suggestion_text="Retreat from the chokepoint.",
        ).resolve(battle)
        create_trainer_feature_action("psionic_analysis", actor_id="player-1", target_id="foe-1").resolve(battle)
        event = next(evt for evt in reversed(battle.log) if evt.get("feature") == "Psionic Analysis")
        analysis = (event.get("analyses") or [])[0]
        self.assertEqual("Human", analysis.get("origin_kind"))
        self.assertIn("Extrasensory", analysis.get("psychic_moves") or [])
        self.assertIn("Telepath", analysis.get("class_features") or [])
        self.assertIn("Suggestion", analysis.get("source_feature") or "")

    def test_immutable_mind_makes_status_move_fail(self) -> None:
        status_move = MoveSpec(
            name="Hex Pulse",
            type="Ghost",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        prompts: list[dict] = []
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Caster", moves=[status_move]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(
                    spec=_mon("Immutable", features=[{"name": "Immutable Mind"}], tags=["trainer"]),
                    controller_id="foe",
                    position=(1, 3),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([12]),
            out_of_turn_prompt=lambda payload: prompts.append(dict(payload)) or True,
        )
        UseMoveAction(actor_id="player-1", move_name="Hex Pulse", target_id="foe-1").resolve(battle)
        self.assertTrue(any(prompt.get("feature") == "Immutable Mind" for prompt in prompts))
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["foe-1"], "Immutable Mind"))
        self.assertTrue(any(evt.get("effect") == "immutable_mind_fail" for evt in battle.log))

    def test_immutable_mind_blocks_roll_based_secondary_effect(self) -> None:
        damaging_move = MoveSpec(
            name="Psychic Blast",
            type="Psychic",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
            effects_text="Confuses on 15+.",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Caster", moves=[damaging_move]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(
                    spec=_mon("Immutable", features=[{"name": "Immutable Mind"}], tags=["trainer"]),
                    controller_id="foe",
                    position=(1, 3),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([20]),
            out_of_turn_prompt=lambda payload: True,
        )
        UseMoveAction(actor_id="player-1", move_name="Psychic Blast", target_id="foe-1").resolve(battle)
        target = battle.pokemon["foe-1"]
        self.assertFalse(target.has_status("Confused"))
        self.assertFalse(target.get_temporary_effects("immutable_mind_block"))

    def test_ambient_aura_grants_blessing_and_barrier(self) -> None:
        aura_move = MoveSpec(
            name="Aura Burst",
            type="Fighting",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
            keywords=["Aura"],
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    controller_kind="player",
                    team="players",
                    skills={"intuition": 3},
                ),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "AuraTrainer",
                        moves=[aura_move],
                        features=[{"name": "Ambient Aura"}],
                        capabilities=["Aura Pulse"],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(spec=_mon("Ally"), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 4)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([12]),
        )
        UseMoveAction(actor_id="player-1", move_name="Aura Burst", target_id="foe-1").resolve(battle)
        actor = battle.pokemon["player-1"]
        self.assertTrue(actor.get_temporary_effects("ambient_aura_blessing"))
        create_trainer_feature_action("ambient_aura", actor_id="player-1", mode="barrier", target_id="ally-1").resolve(battle)
        barrier = next(iter(battle.pokemon["ally-1"].get_temporary_effects("damage_reduction")), None)
        self.assertIsNotNone(barrier)
        self.assertEqual(9, int(barrier.get("amount") or 0))

    def test_acrobat_increases_jump_range(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Acrobat", features=[{"name": "Acrobat"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(15),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["l_jump"] = 1
        actor.spec.movement["h_jump"] = 1
        self.assertIn((3, 1), movement.legal_long_jump_tiles(battle, "player-1"))
        self.assertIn((1, 3), movement.legal_high_jump_tiles(battle, "player-1"))

    def test_nimble_movement_extends_disengage_to_two(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Nimble", features=[{"name": "Nimble Movement"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(16),
        )
        battle.pokemon["player-1"].spec.movement["overland"] = 3
        action = DisengageAction(actor_id="player-1", destination=(3, 1))
        action.validate(battle)

    def test_long_jump_cannot_cross_blocked_path(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Jumper"), controller_id="player", position=(1, 1)),
            },
            grid=GridState(width=6, height=6, blockers={(2, 1)}),
            rng=random.Random(17),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["l_jump"] = 2
        actor.spec.movement["h_jump"] = 2
        self.assertNotIn((3, 1), movement.legal_long_jump_tiles(battle, "player-1"))
        self.assertIn((3, 1), movement.legal_high_jump_tiles(battle, "player-1"))

    def test_traveler_uses_survival_for_overland_and_jump(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    team="players",
                    skills={"survival": 5, "acrobatics": 1, "athletics": 2},
                )
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Traveler", features=[{"name": "Traveler"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=10, height=10),
            rng=random.Random(18),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["overland"] = 3
        actor.spec.movement["l_jump"] = 1
        actor.spec.movement["h_jump"] = 1
        self.assertEqual(7, actor.movement_speed("overland"))
        self.assertIn((5, 1), movement.legal_long_jump_tiles(battle, "player-1"))
        self.assertIn((1, 4), movement.legal_high_jump_tiles(battle, "player-1"))

    def test_wallrunner_allows_running_along_blockers_and_jumping_off(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    team="players",
                    skills={"acrobatics": 3},
                )
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Runner", features=[{"name": "Wallrunner"}], tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=7, height=5, blockers={(2, 1), (3, 1)}),
            rng=random.Random(19),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["overland"] = 3
        actor.spec.movement["l_jump"] = 2
        shift_tiles = movement.legal_shift_tiles(battle, "player-1")
        self.assertIn((4, 1), shift_tiles)
        self.assertNotIn((2, 1), shift_tiles)
        self.assertIn((4, 1), movement.legal_long_jump_tiles(battle, "player-1"))

    def test_stamina_grants_temp_hp_after_take_a_breather(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(
                    identifier="player",
                    name="Player",
                    team="players",
                    features=[{"name": "Stamina"}],
                    skills={"athletics": 4, "combat": 2},
                )
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Bulky"), controller_id="player", position=(1, 1)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(20),
        )
        battle.apply_take_breather("player-1")
        actor = battle.pokemon["player-1"]
        self.assertEqual(4, actor.temp_hp)
        event = next(evt for evt in reversed(battle.log) if evt.get("feature") == "Stamina")
        self.assertIn("take_breather", event.get("reasons", []))

    def test_naturewalk_ignores_rough_terrain_and_blocks_slowed(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Ranger", capabilities=[{"name": "Naturewalk (Forest)"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(
                width=6,
                height=6,
                tiles={
                    (2, 1): {"type": "forest difficult"},
                    (3, 1): {"type": "forest difficult"},
                },
            ),
            terrain={"name": "Forest"},
            rng=random.Random(22),
        )
        actor = battle.pokemon["player-1"]
        actor.spec.movement["overland"] = 2
        self.assertIn((3, 1), movement.legal_shift_tiles(battle, "player-1"))
        events = []
        battle._apply_status(
            events,
            attacker_id="player-1",
            target_id="player-1",
            move=MoveSpec(name="Mud Trap", type="Ground", category="Status"),
            target=actor,
            status="Slowed",
            effect="test",
            description="test",
        )
        self.assertFalse(actor.has_status("Slowed"))
        self.assertTrue(any(evt.get("effect") in {"misty_terrain_block", "naturewalk_block"} for evt in events))

    def test_fearsome_display_leer_grants_crit_range_against_target(self) -> None:
        leer = MoveSpec(
            name="Leer",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
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
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Fearsome Display"}], moves=[leer]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("AllyMon", moves=[tackle]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4, 18]),
        )
        UseMoveAction(actor_id="player-1", move_name="Leer", target_id="foe-1").resolve(battle)
        UseMoveAction(actor_id="player-2", move_name="Tackle", target_id="foe-1").resolve(battle)
        attack_event = next(evt for evt in battle.log if evt.get("type") == "move" and evt.get("actor") == "player-2")
        self.assertTrue(attack_event.get("crit"))

    def test_fearsome_display_glare_applies_speed_drop_on_miss(self) -> None:
        glare = MoveSpec(
            name="Glare",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player"),
                "foe": TrainerState(identifier="foe", name="Foe"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "TrainerAvatar",
                        tags=["trainer"],
                        features=[{"name": "Fearsome Display"}, {"name": "Cruel Gaze"}],
                        moves=[glare],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([1]),
        )
        UseMoveAction(actor_id="player-1", move_name="Glare", target_id="foe-1").resolve(battle)
        self.assertEqual(-2, battle.pokemon["foe-1"].combat_stages["spd"])

    def test_fearsome_display_headbutt_sets_initiative_to_zero(self) -> None:
        headbutt = MoveSpec(
            name="Headbutt",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Fearsome Display"}], moves=[headbutt]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([4]),
        )
        battle.start_round()
        UseMoveAction(actor_id="player-1", move_name="Headbutt", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].get_temporary_effects("initiative_zero_until_turn"))

    def test_fearsome_display_mean_look_applies_suppressed(self) -> None:
        mean_look = MoveSpec(
            name="Mean Look",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Fearsome Display"}], moves=[mean_look]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([4]),
        )
        UseMoveAction(actor_id="player-1", move_name="Mean Look", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Suppressed"))

    def test_fearsome_display_endure_grants_two_ticks_temp_hp(self) -> None:
        endure = MoveSpec(name="Endure", type="Normal", category="Status", ac=None, target_kind="Self", freq="At-Will")
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Fearsome Display"}], moves=[endure]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        UseMoveAction(actor_id="player-1", move_name="Endure", target_id="player-1").resolve(battle)
        self.assertEqual(battle.pokemon["player-1"].tick_value() * 2, battle.pokemon["player-1"].temp_hp)

    def test_fearsome_display_slack_off_cures_one_status_affliction(self) -> None:
        slack_off = MoveSpec(name="Slack Off", type="Normal", category="Status", ac=None, target_kind="Self", freq="At-Will")
        actor = PokemonState(
            spec=_mon("TrainerAvatar", tags=["trainer"], features=[{"name": "Fearsome Display"}], moves=[slack_off]),
            controller_id="player",
            position=(1, 1),
        )
        actor.statuses.append({"name": "Burned"})
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": actor,
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(3),
        )
        UseMoveAction(actor_id="player-1", move_name="Slack Off", target_id="player-1").resolve(battle)
        self.assertFalse(battle.pokemon["player-1"].has_status("Burned"))

    def test_dirty_trick_rotates_through_hinder_blind_and_low_blow(self) -> None:
        dirty_trick = MoveSpec(
            name="Dirty Trick",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": PokemonState(spec=_mon("TrainerAvatar", tags=["trainer"], moves=[dirty_trick]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([4, 10, 1, 4, 10, 1, 4, 10, 1]),
        )
        UseMoveAction(actor_id="player-1", move_name="Dirty Trick", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Hindered"))
        UseMoveAction(actor_id="player-1", move_name="Dirty Trick", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Blinded"))
        UseMoveAction(actor_id="player-1", move_name="Dirty Trick", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].get_temporary_effects("initiative_zero_until_turn"))

    def test_hinder_applies_hindered_status(self) -> None:
        hinder = MoveSpec(
            name="Hinder",
            type="Normal",
            category="Status",
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": PokemonState(spec=_mon("TrainerAvatar", tags=["trainer"], moves=[hinder]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([4, 10, 1]),
        )
        UseMoveAction(actor_id="player-1", move_name="Hinder", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Hindered"))

    def test_generic_stat_ace_uses_chosen_stat_payload(self) -> None:
        actor = PokemonState(
            spec=_mon("PlayerMon", features=[{"name": "Stat Ace", "chosen_stat": "special defense"}]),
            controller_id="player",
            position=(1, 1),
        )
        self.assertEqual(15, defensive_stat(actor, "special"))

    def test_speed_ace_affects_speed_stat(self) -> None:
        battle = _battle_with_feature({"feature_id": "speed-ace", "name": "Speed Ace"})
        actor = battle.pokemon["player-1"]
        self.assertEqual(15, speed_stat(actor))

    def test_attack_link_spends_ap_and_raises_attack_at_turn_end(self) -> None:
        battle = _battle_with_feature({"feature_id": "attack-link", "name": "Attack Link"}, ap=2)
        actor = battle.pokemon["player-1"]
        _advance_to_end_phase(battle)
        self.assertEqual(1, actor.combat_stages["atk"])
        self.assertEqual(1, battle.trainers["player"].ap)

    def test_attack_link_does_not_spend_ap_when_attack_is_already_positive(self) -> None:
        battle = _battle_with_feature({"feature_id": "attack-link", "name": "Attack Link"}, ap=2)
        actor = battle.pokemon["player-1"]
        actor.combat_stages["atk"] = 1
        _advance_to_end_phase(battle)
        self.assertEqual(1, actor.combat_stages["atk"])
        self.assertEqual(2, battle.trainers["player"].ap)

    def test_juggler_grants_opening_round_initiative_bonus_only_for_that_round(self) -> None:
        battle = _battle_with_feature(
            {"feature_id": "juggler", "name": "Juggler"},
            battle_context="league",
        )
        actor = battle.pokemon["player-1"]
        battle.start_round()
        opening_entry = next(entry for entry in battle.initiative_order if entry.actor_id == "player-1")
        self.assertEqual(22, opening_entry.total)
        battle.round = 2
        round_two_entry = battle._initiative_entry_for_pokemon("player-1")
        assert round_two_entry is not None
        self.assertEqual(12, round_two_entry.total)
        self.assertTrue(
            any(
                evt.get("feature") == "Juggler" and evt.get("effect") == "initiative_bonus"
                for evt in battle.log
            )
        )

    def test_psionic_analysis_is_scene_limited(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Seer", tags=["trainer"], features=[{"name": "Psionic Analysis"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(4),
        )
        battle.pokemon["foe-1"].add_temporary_effect("psychic_residue", source="Suggestion", source_id="player-1")
        create_trainer_feature_action("psionic_analysis", actor_id="player-1", target_id="foe-1").resolve(battle)
        with self.assertRaises(ValueError):
            create_trainer_feature_action("psionic_analysis", actor_id="player-1", target_id="foe-1").validate(battle)

    def test_adaptive_geography_aliases_adjacent_terrain_until_turn_end(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", controller_kind="player"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes", controller_kind="ai"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "Scout",
                        features=[{"name": "Adaptive Geography"}],
                        capabilities=[{"name": "Naturewalk (Forest)"}],
                        tags=["trainer"],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(3, 3)),
            },
            grid=GridState(width=5, height=5),
            terrain={"name": "Wetlands"},
            rng=random.Random(5),
        )
        battle.out_of_turn_prompt = lambda prompt: {"accept": True, "choice": "forest"} if prompt.get("feature") == "Adaptive Geography" else True
        battle.start_round()
        entry = battle.advance_turn()
        while entry and entry.actor_id != "player-1":
            battle.end_turn()
            entry = battle.advance_turn()
        actor = battle.pokemon["player-1"]
        self.assertTrue(actor.get_temporary_effects("terrain_alias"))
        self.assertTrue(battle._matches_naturewalk_terrain(actor))
        battle.end_turn()
        self.assertFalse(actor.get_temporary_effects("terrain_alias"))

    def test_survivalist_grants_naturewalk_and_terrain_skill_bonus(self) -> None:
        actor = PokemonState(
            spec=_mon(
                "Ranger",
                tags=["trainer"],
                features=[{"name": "Survivalist", "chosen_terrain": "Forest"}],
            ),
            controller_id="player",
            position=(1, 1),
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
            pokemon={
                "player-1": actor,
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=5, height=5),
            terrain={"name": "Forest"},
            rng=random.Random(6),
        )
        self.assertIn("Forest", actor.naturewalk_labels())
        self.assertEqual(2, battle._terrain_skill_check_bonus(actor, "survival"))
        self.assertTrue(battle._matches_naturewalk_terrain(actor))

    def test_natural_fighter_uses_terrain_mapped_move(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Scout", tags=["trainer"], features=[{"name": "Natural Fighter"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=6, height=6),
            terrain={"name": "Forest"},
            rng=_FixedRng([10, 10]),
        )
        create_trainer_feature_action("natural_fighter", actor_id="player-1", target_id="foe-1").resolve(battle)
        self.assertTrue(any(evt.get("feature") == "Natural Fighter" and evt.get("move") == "Grass Whistle" for evt in battle.log))
        self.assertEqual(1, battle.trainers["player"].ap)

    def test_wilderness_guide_applies_urban_buffs(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Guide", tags=["trainer"], features=[{"name": "Wilderness Guide"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "player-2": PokemonState(spec=_mon("AllyMon"), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("FoeMon"), controller_id="foe", position=(3, 3)),
            },
            grid=GridState(width=6, height=6),
            terrain={"name": "Urban"},
            rng=random.Random(7),
        )
        create_trainer_feature_action("wilderness_guide", actor_id="player-1").resolve(battle)
        ally = battle.pokemon["player-2"]
        self.assertTrue(ally.get_temporary_effects("evasion_bonus"))
        self.assertTrue(ally.get_temporary_effects("accuracy_bonus"))
        self.assertTrue(ally.get_temporary_effects("wilderness_guide_urban"))

    def test_psionic_sponge_borrows_psychic_move_until_turn_end(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", skills={"focus": 4})},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("PsychicMon", features=[{"name": "Psionic Sponge"}], moves=[MoveSpec(name="Confusion", type="Psychic", category="Special", db=4, ac=2, range_kind="Ranged", range_value=6, target_kind="Ranged", target_range=6, freq="At-Will")]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "ally-1": PokemonState(
                    spec=_mon("AllyMon", moves=[MoveSpec(name="Psybeam", type="Psychic", category="Special", db=6, ac=2, range_kind="Ranged", range_value=6, target_kind="Ranged", target_range=6, freq="At-Will")]),
                    controller_id="player",
                    position=(1, 3),
                ),
            },
            grid=GridState(width=7, height=7),
            rng=random.Random(5),
        )
        battle.pokemon["player-1"].spec.types = ["Psychic"]
        create_trainer_feature_action("psionic_sponge", actor_id="player-1", ally_id="ally-1", move_name="Psybeam").resolve(battle)
        self.assertIsNotNone(battle._find_known_move(battle.pokemon["player-1"], "Psybeam"))
        battle.current_actor_id = "player-1"
        PhaseController(battle).end_turn()
        self.assertIsNone(battle._find_known_move(battle.pokemon["player-1"], "Psybeam"))
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Psionic Sponge"))

    def test_basic_psionics_and_psychic_navigator_sync_static_grants(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("PsychicTrainer", tags=["trainer"]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(12),
        )
        battle.pokemon["player-1"].spec.trainer_edges = [{"name": "Basic Psionics"}, {"name": "Psychic Navigator"}]
        battle._sync_trainer_feature_moves_to_pokemon()
        battle._sync_static_trainer_feature_capabilities_to_pokemon()
        self.assertIsNotNone(battle._find_known_move(battle.pokemon["player-1"], "Confusion"))
        self.assertTrue(battle.pokemon["player-1"].has_capability("Psychic Navigator"))

    def test_mindbreak_adds_damage_for_listed_afflictions(self) -> None:
        psychic_attack = MoveSpec(
            name="Psyshock",
            type="Psychic",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Trainer", tags=["trainer"], features=[{"name": "Mindbreak"}]), controller_id="player", position=(1, 1)),
                "ally-1": PokemonState(spec=_mon("PsychicMon", moves=[psychic_attack]), controller_id="player", position=(1, 2)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 4)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([10, 10]),
        )
        battle.pokemon["ally-1"].spec.types = ["Psychic"]
        battle.pokemon["ally-1"].statuses.extend([{"name": "Confused"}, {"name": "Suppressed"}])
        create_trainer_feature_action("mindbreak", actor_id="player-1", target_id="ally-1").resolve(battle)
        UseMoveAction(actor_id="ally-1", move_name="Psyshock", target_id="foe-1").resolve(battle)
        self.assertTrue(any(evt.get("feature") == "Mindbreak" and evt.get("amount") == 6 for evt in battle.log))

    def test_mindbreak_rebinds_and_release_clears_binding(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=5)},
            pokemon={
                "player-1": PokemonState(spec=_mon("Trainer", tags=["trainer"], features=[{"name": "Mindbreak"}]), controller_id="player", position=(1, 1)),
                "ally-1": PokemonState(spec=_mon("PsychicA"), controller_id="player", position=(1, 2)),
                "ally-2": PokemonState(spec=_mon("PsychicB"), controller_id="player", position=(2, 2)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(18),
        )
        battle.pokemon["ally-1"].spec.types = ["Psychic"]
        battle.pokemon["ally-2"].spec.types = ["Psychic"]
        create_trainer_feature_action("mindbreak", actor_id="player-1", target_id="ally-1").resolve(battle)
        create_trainer_feature_action("mindbreak", actor_id="player-1", target_id="ally-2").resolve(battle)
        self.assertFalse(battle.pokemon["ally-1"].get_temporary_effects("mindbreak_bound"))
        self.assertTrue(battle.pokemon["ally-2"].get_temporary_effects("mindbreak_bound"))
        create_trainer_feature_action("release_mindbreak", actor_id="player-1").resolve(battle)
        self.assertFalse(battle.pokemon["ally-2"].get_temporary_effects("mindbreak_bound"))
        self.assertTrue(any(evt.get("feature") == "Mindbreak" and evt.get("effect") == "release" for evt in battle.log))

    def test_force_of_will_grants_follow_up_after_psychic_status_move(self) -> None:
        trigger_move = MoveSpec(
            name="Barrier",
            type="Psychic",
            category="Status",
            ac=2,
            range_kind="Self",
            target_kind="Self",
            freq="At-Will",
        )
        follow_move = MoveSpec(
            name="Calm Mind",
            type="Psychic",
            category="Status",
            ac=2,
            range_kind="Self",
            target_kind="Self",
            freq="At-Will",
        )
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("PsychicMon", features=[{"name": "Force of Will"}], moves=[trigger_move, follow_move]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([10, 10]),
        )
        battle.pokemon["player-1"].spec.types = ["Psychic"]
        UseMoveAction(actor_id="player-1", move_name="Barrier", target_id="player-1").resolve(battle)
        self.assertTrue(battle.pokemon["player-1"].get_temporary_effects("force_of_will_ready"))
        create_trainer_feature_action("force_of_will_follow_up", actor_id="player-1", move_name="Calm Mind").resolve(battle)
        self.assertFalse(battle.pokemon["player-1"].get_temporary_effects("force_of_will_ready"))
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "Force of Will"))

    def test_psionic_overload_psychic_makes_target_vulnerable(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("PsychicTrainer", features=[{"name": "Psionic Overload"}], moves=[MoveSpec(name="Psychic", type="Psychic", category="Special", db=8, ac=2, range_kind="Ranged", range_value=8, target_kind="Ranged", target_range=8, freq="At-Will")]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 4)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([10, 10]),
        )
        UseMoveAction(actor_id="player-1", move_name="Psychic", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["player-1"].get_temporary_effects("psionic_overload_ready"))
        create_trainer_feature_action("psionic_overload_follow_up", actor_id="player-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Vulnerable"))

    def test_psionic_overload_barrier_adds_two_segments(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("PsychicTrainer", features=[{"name": "Psionic Overload"}], moves=[MoveSpec(name="Barrier", type="Psychic", category="Status", ac=2, range_kind="Self", target_kind="Self", freq="At-Will")]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([10]),
        )
        UseMoveAction(actor_id="player-1", move_name="Barrier", target_id="player-1").resolve(battle)
        create_trainer_feature_action(
            "psionic_overload_follow_up",
            actor_id="player-1",
            barrier_tiles=[(3, 1), (3, 2)],
        ).resolve(battle)
        self.assertIn((3, 1), battle.grid.blockers)
        self.assertIn((3, 2), battle.grid.blockers)
        self.assertTrue((battle.grid.tiles.get((3, 1), {}) or {}).get("barriers"))

    def test_psionic_overload_telekinesis_ticks_lifted_target(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=2),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("PsychicTrainer", features=[{"name": "Psionic Overload"}], moves=[MoveSpec(name="Telekinesis", type="Psychic", category="Status", ac=2, range_kind="Ranged", range_value=6, target_kind="Ranged", target_range=6, freq="At-Will")]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 4)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([10]),
        )
        UseMoveAction(actor_id="player-1", move_name="Telekinesis", target_id="foe-1").resolve(battle)
        hp_before = battle.pokemon["foe-1"].hp
        create_trainer_feature_action("psionic_overload_follow_up", actor_id="player-1").resolve(battle)
        battle.current_actor_id = "player-1"
        PhaseController(battle).end_turn()
        self.assertLess(battle.pokemon["foe-1"].hp, hp_before)

    def test_trapper_deploys_and_triggers_tangle_trap(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Ranger", tags=["trainer"], features=[{"name": "Trapper"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(4, 4)),
            },
            grid=GridState(width=10, height=10),
            terrain={"name": "Forest"},
            rng=random.Random(9),
        )
        create_trainer_feature_action("trapper", actor_id="player-1", target_position=(3, 3)).resolve(battle)
        trap_tiles = [
            coord for coord, meta in battle.grid.tiles.items()
            if isinstance(meta, dict) and meta.get("traps")
        ]
        self.assertGreaterEqual(len(trap_tiles), 8)
        destination = trap_tiles[0]
        ShiftAction("foe-1", destination).resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Stuck"))
        self.assertFalse((battle.grid.tiles.get(destination, {}) or {}).get("traps"))

    def test_trapper_accepts_exact_tile_layout(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Ranger", tags=["trainer"], features=[{"name": "Trapper"}]), controller_id="player", position=(1, 1)),
            },
            grid=GridState(width=10, height=10),
            terrain={"name": "Forest"},
            rng=random.Random(10),
        )
        exact_tiles = [(2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3), (3, 4), (4, 4)]
        create_trainer_feature_action("trapper", actor_id="player-1", target_positions=exact_tiles).resolve(battle)
        trap_tiles = {
            coord for coord, meta in battle.grid.tiles.items()
            if isinstance(meta, dict) and meta.get("traps")
        }
        self.assertEqual(set(exact_tiles), trap_tiles)

    def test_frozen_domain_deploys_and_trips_on_failed_entry(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3, skills={"survival": 4}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Cryomancer", tags=["trainer"], features=[{"name": "Frozen Domain"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(4, 4)),
            },
            grid=GridState(width=10, height=10),
            rng=_FixedRng([1]),
        )
        tiles = [(2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3)]
        create_trainer_feature_action("frozen_domain", actor_id="player-1", target_positions=tiles).resolve(battle)
        self.assertEqual(1, battle.trainers["player"].ap)
        self.assertEqual(set(tiles), {coord for coord, meta in battle.grid.tiles.items() if isinstance(meta, dict) and meta.get("frozen_domain")})
        ShiftAction("foe-1", (4, 3)).resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Tripped"))

    def test_frozen_domain_grants_hail_weather_and_melts_on_fire(self) -> None:
        ice_move = MoveSpec(
            name="Powder Snow",
            type="Ice",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        fire_move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=4,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=3, skills={"survival": 2}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Cryomancer", tags=["trainer"], features=[{"name": "Frozen Domain"}], moves=[ice_move, fire_move]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=8, height=8),
            weather="Clear",
            rng=_FixedRng([10, 10]),
        )
        create_trainer_feature_action("frozen_domain", actor_id="player-1", target_positions=[(1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2)]).resolve(battle)
        self.assertEqual("Hail", battle.effective_weather_for_actor(battle.pokemon["player-1"]))
        UseMoveAction(actor_id="player-1", move_name="Ember", target_id="foe-1").resolve(battle)
        self.assertFalse((battle.grid.tiles.get((1, 1), {}) or {}).get("frozen_domain"))
        self.assertFalse((battle.grid.tiles.get((3, 1), {}) or {}).get("frozen_domain"))

    def test_mental_resistance_grants_mindlock_and_special_damage_reduction(self) -> None:
        move = MoveSpec(name="Shadow Ball", type="Ghost", category="Special", db=8, ac=2, range_kind="Ranged", range_value=6, target_kind="Ranged", target_range=6, freq="At-Will")
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Occultist", tags=["trainer"], features=[{"name": "Mental Resistance"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Hexer", moves=[move]), controller_id="foe", position=(1, 4)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([10, 10]),
        )
        control = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("Occultist", tags=["trainer"]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Hexer", moves=[move]), controller_id="foe", position=(1, 4)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([10, 10]),
        )
        battle.pokemon["player-1"].spec.types = ["Psychic"]
        control.pokemon["player-1"].spec.types = ["Psychic"]
        battle._sync_static_trainer_feature_capabilities_to_pokemon()
        self.assertTrue(battle.pokemon["player-1"].has_capability("Mindlock"))
        hp_before = battle.pokemon["player-1"].hp
        control_hp_before = control.pokemon["player-1"].hp
        UseMoveAction(actor_id="foe-1", move_name="Shadow Ball", target_id="player-1").resolve(battle)
        UseMoveAction(actor_id="foe-1", move_name="Shadow Ball", target_id="player-1").resolve(control)
        defended_loss = (hp_before or 0) - (battle.pokemon["player-1"].hp or 0)
        control_loss = (control_hp_before or 0) - (control.pokemon["player-1"].hp or 0)
        self.assertLess(defended_loss, control_loss)

    def test_winter_is_coming_grants_frostbite_ability(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("WinterAce", tags=["trainer"], features=[{"name": "Winter is Coming"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(14),
        )
        battle._sync_static_trainer_feature_abilities_to_pokemon()
        self.assertTrue(battle.pokemon["player-1"].has_ability("Frostbite"))

    def test_winters_herald_rank_move_grants_sync_to_trainer(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "WinterAce",
                        tags=["trainer"],
                        features=[
                            {"name": "Winter's Herald Rank 1", "choices": ["Freeze-Dry", "Ice Punch"]},
                            {"name": "Winter's Herald Rank 2", "choices": ["Blizzard", "Icicle Spear"]},
                        ],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(18),
        )
        battle._sync_trainer_feature_moves_to_pokemon()
        self.assertIsNotNone(battle._find_known_move(battle.pokemon["player-1"], "Freeze-Dry"))
        self.assertIsNotNone(battle._find_known_move(battle.pokemon["player-1"], "Blizzard"))
        self.assertIsNone(battle._find_known_move(battle.pokemon["player-1"], "Ice Beam"))

    def test_frost_touched_grants_only_chosen_moves(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon(
                        "WinterAce",
                        tags=["trainer"],
                        features=[{"name": "Frost Touched", "choices": ["Haze", "Mist"]}],
                    ),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(22),
        )
        battle._sync_trainer_feature_moves_to_pokemon()
        self.assertIsNotNone(battle._find_known_move(battle.pokemon["player-1"], "Haze"))
        self.assertIsNotNone(battle._find_known_move(battle.pokemon["player-1"], "Mist"))
        self.assertIsNone(battle._find_known_move(battle.pokemon["player-1"], "Powder Snow"))

    def test_cold_never_bothered_me_anyway_grants_tundra_and_blocks_frozen(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("WinterAce", tags=["trainer"], features=[{"name": "The Cold Never Bothered Me Anyway"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Attacker"), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            weather="Hail",
            rng=random.Random(19),
        )
        battle._sync_static_trainer_feature_capabilities_to_pokemon()
        self.assertTrue(any("naturewalk" in str(name).lower() and "tundra" in str(name).lower() for name in battle.pokemon["player-1"].capability_names()))
        hp_before = battle.pokemon["player-1"].hp
        battle._apply_status(
            [],
            attacker_id="foe-1",
            target_id="player-1",
            move=MoveSpec(name="Ice Beam", type="Ice", category="Special"),
            target=battle.pokemon["player-1"],
            status="Frozen",
            effect="freeze",
            description="Freeze test.",
        )
        self.assertFalse(battle.pokemon["player-1"].has_status("Frozen"))
        events = battle.pokemon["player-1"].handle_phase_effects(battle, TurnPhase.START, "player-1")
        self.assertEqual(hp_before, battle.pokemon["player-1"].hp)
        self.assertFalse(any(evt.get("effect") == "hail_damage" for evt in events))

    def test_glacial_defense_grants_chosen_ability(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("WinterAce", tags=["trainer"], features=[{"name": "Glacial Defense", "choice": "Winter's Kiss"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(20),
        )
        battle._sync_static_trainer_feature_abilities_to_pokemon()
        self.assertTrue(battle.pokemon["player-1"].has_ability("Winter's Kiss"))

    def test_glacial_ice_reduces_super_effective_fire_damage_against_ice_type(self) -> None:
        flamethrower = MoveSpec(
            name="Flamethrower",
            type="Fire",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        winter_spec = _mon("WinterAce", features=[{"name": "Glacial Ice"}])
        winter_spec.types = ["Ice"]
        baseline_spec = _mon("WinterBaseline")
        baseline_spec.types = ["Ice"]
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", skills={"athletics": 4, "survival": 2}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=winter_spec, controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Attacker", moves=[flamethrower], level=35), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([20]),
        )
        baseline = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", skills={"athletics": 4, "survival": 2}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=baseline_spec, controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Attacker", moves=[flamethrower], level=35), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([20]),
        )
        self.assertEqual(4, battle._glacial_ice_rank(battle.pokemon["player-1"], "player-1"))
        UseMoveAction(actor_id="foe-1", move_name="Flamethrower", target_id="player-1").resolve(baseline)
        UseMoveAction(actor_id="foe-1", move_name="Flamethrower", target_id="player-1").resolve(battle)
        self.assertLessEqual(battle.pokemon["player-1"].hp, battle.pokemon["player-1"].max_hp())

    def test_arctic_zeal_triggers_mist_blessing_on_ice_move(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("WinterAce", features=[{"name": "Arctic Zeal"}], moves=[MoveSpec(name="Ice Beam", type="Ice", category="Special", db=8, ac=2, range_kind="Ranged", range_value=6, target_kind="Ranged", target_range=6, freq="At-Will")]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            weather="Clear",
            rng=_FixedRng([20]),
        )
        battle.pokemon["player-1"].spec.types = ["Ice"]
        battle.out_of_turn_prompt = lambda payload: payload.get("feature") == "Arctic Zeal"
        UseMoveAction(actor_id="player-1", move_name="Ice Beam", target_id="foe-1").resolve(battle)
        self.assertEqual("Hail", battle.effective_weather_for_actor(battle.pokemon["player-1"]))
        self.assertEqual(3, battle._arctic_zeal_blessing_charges(battle.pokemon["player-1"]))
        self.assertTrue(battle.pokemon["player-1"].has_status("Mist"))
        self.assertTrue(any(evt.get("feature") == "Arctic Zeal" for evt in battle.log))

    def test_arctic_zeal_blessing_action_spends_charge_and_slows_target(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
            pokemon={
                "player-1": PokemonState(spec=_mon("WinterAce", features=[{"name": "Arctic Zeal"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(24),
        )
        battle.pokemon["player-1"].add_temporary_effect("arctic_zeal_blessing", charges=2, expires_round=1)
        create_trainer_feature_action("arctic_zeal", actor_id="player-1", mode="slow", target_id="foe-1").resolve(battle)
        self.assertEqual(1, battle._arctic_zeal_blessing_charges(battle.pokemon["player-1"]))
        self.assertTrue(battle.pokemon["foe-1"].has_status("Slowed"))
        self.assertTrue(any(evt.get("feature") == "Arctic Zeal" and evt.get("effect") == "mist_slow" for evt in battle.log))

    def test_arctic_zeal_guard_adds_tick_value_to_glacial_ice(self) -> None:
        flamethrower = MoveSpec(
            name="Flamethrower",
            type="Fire",
            category="Special",
            db=9,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("WinterAce", features=[{"name": "Glacial Ice"}, {"name": "Arctic Zeal"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Attacker", moves=[flamethrower]), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([20]),
        )
        battle.pokemon["player-1"].spec.types = ["Ice"]
        battle.pokemon["player-1"].add_temporary_effect("arctic_zeal_blessing", charges=1, expires_round=1)
        battle.out_of_turn_prompt = lambda payload: payload.get("feature") == "Arctic Zeal"
        bonus = battle._maybe_apply_arctic_zeal_guard(
            "player-1",
            battle.pokemon["player-1"],
            "foe-1",
            flamethrower,
            type_multiplier=2.0,
            glacial_ice_rank=4,
        )
        self.assertEqual(battle.pokemon["player-1"].tick_value(), bonus)
        self.assertEqual(0, battle._arctic_zeal_blessing_charges(battle.pokemon["player-1"]))
        self.assertTrue(any(evt.get("feature") == "Arctic Zeal" and evt.get("effect") == "damage_reduction" for evt in battle.log))

    def test_polar_vortex_binds_hail_to_user(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
            pokemon={
                "player-1": PokemonState(spec=_mon("WinterAce", features=[{"name": "Polar Vortex"}]), controller_id="player", position=(1, 1)),
                "ally-1": PokemonState(spec=_mon("Glaceon"), controller_id="player", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            weather="Clear",
            rng=random.Random(24),
        )
        create_trainer_feature_action("polar_vortex", actor_id="player-1", target_id="ally-1").resolve(battle)
        self.assertEqual("Hail", battle.effective_weather_for_actor(battle.pokemon["ally-1"]))
        self.assertTrue(any(evt.get("feature") == "Polar Vortex" for evt in battle.log))

    def test_polar_vortex_rebinds_and_release_clears_binding(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=5)},
            pokemon={
                "player-1": PokemonState(spec=_mon("WinterAce", features=[{"name": "Polar Vortex"}]), controller_id="player", position=(1, 1)),
                "ally-1": PokemonState(spec=_mon("Glaceon"), controller_id="player", position=(2, 1)),
                "ally-2": PokemonState(spec=_mon("Froslass"), controller_id="player", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            weather="Clear",
            rng=random.Random(25),
        )
        create_trainer_feature_action("polar_vortex", actor_id="player-1", target_id="ally-1").resolve(battle)
        create_trainer_feature_action("polar_vortex", actor_id="player-1", target_id="ally-2").resolve(battle)
        self.assertNotEqual("Hail", battle.effective_weather_for_actor(battle.pokemon["ally-1"]))
        self.assertEqual("Hail", battle.effective_weather_for_actor(battle.pokemon["ally-2"]))
        create_trainer_feature_action("release_polar_vortex", actor_id="player-1").resolve(battle)
        self.assertNotEqual("Hail", battle.effective_weather_for_actor(battle.pokemon["ally-2"]))
        self.assertTrue(any(evt.get("feature") == "Polar Vortex" and evt.get("effect") == "release" for evt in battle.log))

    def test_polished_shine_adds_effect_range_roll_bonus_for_steel_moves(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("SteelAce", features=[{"name": "Polished Shine"}], moves=[MoveSpec(name="Steel Pulse", type="Steel", category="Special", db=6, ac=2, range_kind="Ranged", range_value=6, target_kind="Ranged", target_range=6, freq="At-Will")]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=5, height=5),
            rng=random.Random(26),
        )
        ctx = MoveSpecialContext(
            battle=battle,
            attacker_id="player-1",
            attacker=battle.pokemon["player-1"],
            defender_id="foe-1",
            defender=battle.pokemon["foe-1"],
            move=battle.pokemon["player-1"].spec.moves[0],
            result={"roll": 13},
            damage_dealt=0,
            events=[],
            move_name="Steel Pulse",
            hit=True,
            phase="post_damage",
            action_type="standard",
        )
        self.assertEqual(15, _effect_roll(ctx))

    def test_true_steel_reduces_damage_and_uses_mono_steel_effectiveness(self) -> None:
        flamethrower = MoveSpec(
            name="Flamethrower",
            type="Fire",
            category="Special",
            db=9,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", controller_kind="ai", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("SteelMon", features=[{"name": "True Steel"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("FireMon", moves=[flamethrower]), controller_id="foe", position=(1, 3)),
            },
            grid=GridState(width=7, height=7),
            rng=_FixedRng([10]),
            out_of_turn_prompt=lambda payload: True,
        )
        battle.pokemon["player-1"].spec.types = ["Steel", "Grass"]
        battle.pokemon["player-1"].spec.skills["athletics"] = 2
        before = battle.pokemon["player-1"].hp
        UseMoveAction(actor_id="foe-1", move_name="Flamethrower", target_id="player-1").resolve(battle)
        after = battle.pokemon["player-1"].hp
        self.assertLess(after, before)
        self.assertEqual(1, battle._feature_scene_use_count(battle.pokemon["player-1"], "True Steel"))
        event = next(evt for evt in reversed(battle.log) if evt.get("feature") == "True Steel")
        self.assertEqual("type_reduction", event.get("effect"))
        self.assertGreaterEqual(int(event.get("amount", 0) or 0), 1)

    def test_deep_cold_freezes_and_drops_stats_once_per_target(self) -> None:
        ice_beam = MoveSpec(
            name="Ice Beam",
            type="Ice",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("WinterAce", features=[{"name": "Deep Cold"}], moves=[ice_beam]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([20]),
        )
        battle.pokemon["player-1"].spec.types = ["Ice"]
        prompts: list[dict] = []
        battle.out_of_turn_prompt = lambda payload: prompts.append(dict(payload)) or True
        UseMoveAction(actor_id="player-1", move_name="Ice Beam", target_id="foe-1").resolve(battle)
        target = battle.pokemon["foe-1"]
        self.assertTrue(target.has_status("Frozen"))
        self.assertEqual(-1, target.combat_stages["atk"])
        self.assertEqual(-1, target.combat_stages["spatk"])
        self.assertEqual(-1, target.combat_stages["spd"])
        self.assertTrue(any(prompt.get("feature") == "Deep Cold" for prompt in prompts))
        before_log_count = len([evt for evt in battle.log if evt.get("feature") == "Deep Cold"])
        UseMoveAction(actor_id="player-1", move_name="Ice Beam", target_id="foe-1").resolve(battle)
        after_log_count = len([evt for evt in battle.log if evt.get("feature") == "Deep Cold"])
        self.assertEqual(before_log_count, after_log_count)

    def test_gneiss_aim_grants_smite_on_rock_move_miss(self) -> None:
        stone_edge = MoveSpec(
            name="Stone Edge",
            type="Rock",
            category="Physical",
            db=10,
            ac=6,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("RockAce", features=[{"name": "Gneiss Aim"}], moves=[stone_edge]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=5, height=5),
            rng=_FixedRng([1, 12]),
        )
        before = battle.pokemon["foe-1"].hp
        UseMoveAction(actor_id="player-1", move_name="Stone Edge", target_id="foe-1").resolve(battle)
        self.assertLess(battle.pokemon["foe-1"].hp, before)
        self.assertTrue(any(evt.get("feature") == "Gneiss Aim" and evt.get("effect") == "smite" for evt in battle.log))
        self.assertTrue(any(evt.get("type") == "smite" for evt in battle.log))

    def test_gravel_before_me_places_stealth_rock_on_miss_and_injury(self) -> None:
        rock_slide = MoveSpec(
            name="Rock Slide",
            type="Rock",
            category="Physical",
            db=8,
            ac=6,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players"),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("RockAce", features=[{"name": "Gravel Before Me"}], moves=[rock_slide]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([1, 12]),
        )
        UseMoveAction(actor_id="player-1", move_name="Rock Slide", target_id="foe-1").resolve(battle)
        hazard_tiles = {
            coord for coord, meta in battle.grid.tiles.items()
            if isinstance(meta, dict) and (meta.get("hazards") or {}).get("stealth_rock")
        }
        self.assertTrue(any(abs(coord[0] - 1) + abs(coord[1] - 1) == 1 for coord in hazard_tiles))
        battle.pokemon["player-1"].apply_damage(max(1, battle.pokemon["player-1"].max_hp() // 2))
        hazard_layers = sum(
            int((meta.get("hazards") or {}).get("stealth_rock", 0))
            for meta in battle.grid.tiles.values()
            if isinstance(meta, dict)
        )
        self.assertGreaterEqual(hazard_layers, 2)
        self.assertTrue(any(evt.get("feature") == "Gravel Before Me" and evt.get("trigger") == "injury" for evt in battle.log))

    def test_bigger_and_boulder_pushes_vulnerable_and_places_stealth_rock(self) -> None:
        stone_edge = MoveSpec(
            name="Stone Edge",
            type="Rock",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", skills={"combat": 3}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("RockAce", features=[{"name": "Bigger and Boulder"}], moves=[stone_edge]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(1, 2)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([10]),
        )
        UseMoveAction(actor_id="player-1", move_name="Stone Edge", target_id="foe-1").resolve(battle)
        self.assertTrue(battle.pokemon["foe-1"].has_status("Vulnerable"))
        self.assertEqual((1, 3), battle.pokemon["foe-1"].position)
        hazard_tiles = {
            coord for coord, meta in battle.grid.tiles.items()
            if isinstance(meta, dict) and (meta.get("hazards") or {}).get("stealth_rock")
        }
        self.assertTrue(any(abs(coord[0] - 1) + abs(coord[1] - 3) == 1 for coord in hazard_tiles))
        self.assertTrue(any(evt.get("feature") == "Bigger and Boulder" for evt in battle.log))

    def test_tough_as_schist_binds_releases_and_preserves_stealth_rock(self) -> None:
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=4),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("RockTrainer", tags=["trainer"], features=[{"name": "Tough as Schist"}]), controller_id="player", position=(1, 1)),
                "player-2": PokemonState(spec=_mon("RockMon"), controller_id="player", position=(2, 1)),
                "foe-1": PokemonState(spec=_mon("Target"), controller_id="foe", position=(3, 1)),
            },
            grid=GridState(width=7, height=7),
            rng=random.Random(31),
        )
        battle.pokemon["player-2"].spec.types = ["Rock"]
        create_trainer_feature_action("tough_as_schist", actor_id="player-1", target_id="player-2").resolve(battle)
        battle._place_hazard((3, 2), "stealth_rock", 1, source_id="player-1")
        battle.out_of_turn_prompt = lambda payload: {"accept": True, "choice": "preserve"} if payload.get("feature") == "Tough as Schist" else True
        ShiftAction("foe-1", (3, 2)).resolve(battle)
        battle.pokemon["foe-1"].handle_phase_effects(battle, TurnPhase.START, "foe-1")
        hazard_layers = int(((battle.grid.tiles.get((3, 2), {}) or {}).get("hazards") or {}).get("stealth_rock", 0) or 0)
        self.assertEqual(1, hazard_layers)
        self.assertTrue(any(evt.get("feature") == "Tough as Schist" and evt.get("effect") == "hazard_preserve" for evt in battle.log))
        create_trainer_feature_action("release_tough_as_schist", actor_id="player-1").resolve(battle)
        self.assertFalse(battle.pokemon["player-2"].get_temporary_effects("tough_as_schist_bound"))

    def test_tough_as_schist_consumes_nearby_stealth_rock_for_damage_reduction(self) -> None:
        surf = MoveSpec(
            name="Surf",
            type="Water",
            category="Special",
            db=10,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            freq="At-Will",
        )
        battle = BattleState(
            trainers={
                "player": TrainerState(identifier="player", name="Player", team="players", ap=4, skills={"combat": 3}),
                "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
            },
            pokemon={
                "player-1": PokemonState(spec=_mon("RockTrainer", tags=["trainer"], features=[{"name": "Tough as Schist"}]), controller_id="player", position=(1, 1)),
                "player-2": PokemonState(spec=_mon("RockMon"), controller_id="player", position=(2, 1)),
                "foe-1": PokemonState(spec=_mon("WaterMon", moves=[surf]), controller_id="foe", position=(2, 4)),
            },
            grid=GridState(width=8, height=8),
            rng=_FixedRng([10]),
        )
        battle.pokemon["player-2"].spec.types = ["Rock"]
        create_trainer_feature_action("tough_as_schist", actor_id="player-1", target_id="player-2").resolve(battle)
        battle._place_hazard((2, 2), "stealth_rock", 1, source_id="player-1")
        battle.out_of_turn_prompt = lambda payload: {"accept": True, "choice": "2,2|stealth_rock"} if payload.get("feature") == "Tough as Schist" else True
        before = battle.pokemon["player-2"].hp
        UseMoveAction(actor_id="foe-1", move_name="Surf", target_id="player-2").resolve(battle)
        after = battle.pokemon["player-2"].hp
        self.assertLess(after, before)
        self.assertTrue(any(evt.get("feature") == "Tough as Schist" and evt.get("effect") == "damage_reduction" for evt in battle.log))
        hazard_layers = int(((battle.grid.tiles.get((2, 2), {}) or {}).get("hazards") or {}).get("stealth_rock", 0) or 0)
        self.assertEqual(0, hazard_layers)

    def test_iron_mind_logs_telepathy_awareness_for_suggestion(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
            pokemon={
                "player-1": PokemonState(spec=_mon("Telepath", tags=["trainer"], features=[{"name": "Telepath"}, {"name": "Suggestion"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target", features=[{"name": "Iron Mind"}]), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(15),
        )
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        create_trainer_feature_action("suggestion", actor_id="player-1", target_id="foe-1", suggestion_text="Look left.").resolve(battle)
        self.assertTrue(any(evt.get("feature") == "Iron Mind" and evt.get("trigger") == "Suggestion" for evt in battle.log))

    def test_suggestion_is_blocked_by_mindlock_but_still_alerts_iron_mind(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
            pokemon={
                "player-1": PokemonState(spec=_mon("Telepath", tags=["trainer"], features=[{"name": "Telepath"}, {"name": "Suggestion"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target", features=[{"name": "Iron Mind"}]), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(15),
        )
        battle.pokemon["foe-1"].add_temporary_effect("capability_granted", capability="Mindlock", source="Test")
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        create_trainer_feature_action("suggestion", actor_id="player-1", target_id="foe-1", suggestion_text="Look left.").resolve(battle)
        self.assertFalse(battle.pokemon["foe-1"].get_temporary_effects("suggestion_bound"))
        self.assertTrue(any(evt.get("feature") == "Iron Mind" and evt.get("trigger") == "Suggestion" for evt in battle.log))
        self.assertTrue(any(evt.get("feature") == "Suggestion" and evt.get("effect") == "blocked" for evt in battle.log))

    def test_iron_mind_logs_telepathy_awareness_for_thought_detection(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2, skills={"focus": 2})},
            pokemon={
                "player-1": PokemonState(spec=_mon("Telepath", tags=["trainer"], features=[{"name": "Telepath"}, {"name": "Thought Detection"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target", features=[{"name": "Iron Mind"}]), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(16),
        )
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        create_trainer_feature_action("thought_detection", actor_id="player-1").resolve(battle)
        self.assertTrue(any(evt.get("feature") == "Iron Mind" and evt.get("trigger") == "Thought Detection" for evt in battle.log))

    def test_iron_mind_logs_failed_thought_detection_through_mindlock(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2, skills={"focus": 2})},
            pokemon={
                "player-1": PokemonState(spec=_mon("Telepath", tags=["trainer"], features=[{"name": "Telepath"}, {"name": "Thought Detection"}]), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target", features=[{"name": "Iron Mind"}]), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(17),
        )
        battle.pokemon["foe-1"].add_temporary_effect("capability_granted", capability="Mindlock", source="Test")
        create_trainer_feature_action("telepath", actor_id="player-1").resolve(battle)
        create_trainer_feature_action("thought_detection", actor_id="player-1").resolve(battle)
        self.assertTrue(any(evt.get("feature") == "Iron Mind" and evt.get("trigger") == "Thought Detection" for evt in battle.log))
        event = next(evt for evt in reversed(battle.log) if evt.get("feature") == "Thought Detection")
        self.assertEqual(["foe-1"], event.get("blocked_targets"))

    def test_iron_mind_logs_when_suggestion_is_used_in_skill_contest(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Telepath"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target", features=[{"name": "Iron Mind"}]), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=_FixedRng([10, 5]),
        )
        battle.pokemon["foe-1"].add_temporary_effect("suggestion_bound", source_id="player-1", suggestion="Hesitate.")
        battle._skill_contest(
            battle.pokemon["player-1"],
            battle.pokemon["foe-1"],
            ["guile"],
            ["intuition"],
            attacker_id="player-1",
            defender_id="foe-1",
        )
        self.assertTrue(any(evt.get("feature") == "Iron Mind" and evt.get("trigger") == "Suggestion Follow-Through" for evt in battle.log))

    def test_iron_mind_logs_psionic_analysis_awareness(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
            pokemon={
                "player-1": PokemonState(
                    spec=_mon("Seer", tags=["trainer"], features=[{"name": "Telepath"}, {"name": "Psionic Analysis"}]),
                    controller_id="player",
                    position=(1, 1),
                ),
                "foe-1": PokemonState(
                    spec=_mon("Target", features=[{"name": "Iron Mind"}]),
                    controller_id="foe",
                    position=(2, 1),
                ),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(26),
        )
        battle.pokemon["foe-1"].add_temporary_effect("psychic_residue", source="Suggestion", source_id="player-1")
        create_trainer_feature_action("psionic_analysis", actor_id="player-1", target_id="foe-1").resolve(battle)
        self.assertTrue(any(evt.get("feature") == "Iron Mind" and evt.get("trigger") == "Psionic Analysis" for evt in battle.log))

    def test_iron_mind_alert_dedupes_same_source_and_trigger(self) -> None:
        battle = BattleState(
            trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
            pokemon={
                "player-1": PokemonState(spec=_mon("Telepath"), controller_id="player", position=(1, 1)),
                "foe-1": PokemonState(spec=_mon("Target", features=[{"name": "Iron Mind"}]), controller_id="foe", position=(2, 1)),
            },
            grid=GridState(width=6, height=6),
            rng=random.Random(23),
        )
        battle._notify_iron_mind("foe-1", source_id="player-1", trigger="Suggestion", detail="One.")
        battle._notify_iron_mind("foe-1", source_id="player-1", trigger="Suggestion", detail="Two.")
        alerts = [evt for evt in battle.log if evt.get("feature") == "Iron Mind" and evt.get("trigger") == "Suggestion"]
        self.assertEqual(1, len(alerts))


if __name__ == "__main__":
    unittest.main()
