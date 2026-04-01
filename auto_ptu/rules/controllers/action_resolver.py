"""Action validation + resolution boundary.

This is a placeholder boundary for extracting action resolution from BattleState.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..battle_state import (
    BattleState,
    Action,
    ActionType,
    TrainerAction,
    TrainerSwitchAction,
    UseMoveAction,
    ShiftAction,
    SwitchAction,
)
from ..helpers.parental_bond import parental_bond_child_for_turn


@dataclass
class ActionResolver:
    battle: BattleState

    def _validate_for_turn(self, action: Action) -> None:
        battle = self.battle
        if battle.current_actor_id and action.actor_id != battle.current_actor_id:
            trainer_turn_match = False
            if isinstance(action, TrainerAction):
                actor_state = battle.pokemon.get(action.actor_id)
                trainer_turn_match = actor_state is not None and actor_state.controller_id == battle.current_actor_id
            if not trainer_turn_match:
                if not parental_bond_child_for_turn(
                    battle, action.actor_id, battle.current_actor_id
                ):
                    raise ValueError(f"It's not {action.actor_id}'s turn.")
        entry = battle.current_initiative_entry()
        if entry is not None:
            if battle._is_trainer_entry(entry) and not isinstance(action, TrainerAction):
                raise ValueError("Trainer turns can only use trainer actions.")
            if not battle._is_trainer_entry(entry) and isinstance(action, TrainerAction):
                raise ValueError("Trainer actions can only be used on trainer turns.")
        if isinstance(action, TrainerAction):
            trainer = battle.trainers.get(action.actor_id)
            if trainer is None:
                actor_state = battle.pokemon.get(action.actor_id)
                if actor_state is not None:
                    trainer = battle.trainers.get(actor_state.controller_id)
            if trainer is None:
                raise ValueError("Unknown trainer.")
            if isinstance(action, TrainerSwitchAction):
                battle._sync_grapple_status(action.outgoing_id)
            self.validate(action)
            return
        actor = battle.pokemon.get(action.actor_id)
        if actor and actor.has_status("Liquefied") and action.action_type == ActionType.STANDARD:
            if isinstance(action, UseMoveAction):
                move_name = (action.move_name or "").strip().lower()
                if move_name == "acid armor":
                    pass
                else:
                    raise ValueError("Liquefied combatants cannot take Standard Actions.")
            else:
                raise ValueError("Liquefied combatants cannot take Standard Actions.")
        if actor and actor.fainted and not isinstance(action, SwitchAction):
            raise ValueError("Fainted combatants can only switch out.")
        if action.actor_id:
            battle._sync_grapple_status(action.actor_id)
        self.validate(action)
        if actor and battle._sleep_restriction_active(actor):
            sleep_talk_allowed = False
            if isinstance(action, UseMoveAction):
                move_name = (action.move_name or "").strip().lower()
                sleep_talk_allowed = move_name in {"sleep talk", "snore"}
            if isinstance(action, ShiftAction) and actor.get_temporary_effects("sleep_talk_shift"):
                sleep_talk_allowed = True
            if not sleep_talk_allowed:
                if action.action_type not in {ActionType.FREE, ActionType.SWIFT}:
                    raise ValueError(
                        "Sleeping combatants can only take Free or Swift actions that would cure Sleep."
                    )
                if not action.cures_sleep(battle):
                    raise ValueError(
                        "Sleeping combatants can only take Free or Swift actions that would cure Sleep."
                    )

    def declare_action(self, action: Action) -> None:
        self._validate_for_turn(action)
        self.battle._declare_action(action)

    def validate(self, action: Action) -> None:
        action.validate(self.battle)

    def resolve(self, action: Action) -> None:
        action.resolve(self.battle)

    def queue_action(self, action: Action) -> None:
        battle = self.battle
        self._validate_for_turn(action)
        if isinstance(action, TrainerAction):
            trainer = battle.trainers.get(action.actor_id)
            if trainer is None:
                actor_state = battle.pokemon.get(action.actor_id)
                if actor_state is not None:
                    trainer = battle.trainers.get(actor_state.controller_id)
            if trainer is None:
                raise ValueError("Unknown trainer.")
            if battle.is_league_battle() and action.action_type != ActionType.FREE:
                battle._declare_action(action)
                return
            battle._action_queue.append(action)
            return
        battle._action_queue.append(action)

    def resolve_next_action(self) -> Optional[Action]:
        battle = self.battle
        if not battle._action_queue:
            return None
        action = battle._action_queue.popleft()

        def _emit_feature_trigger() -> None:
            dispatcher = getattr(battle, "trainer_feature_dispatcher", None)
            if dispatcher is None:
                return
            payload = {
                "action_type": action.action_type.value if isinstance(action.action_type, ActionType) else str(action.action_type),
                "detail": action.describe_action(),
            }
            target_id = getattr(action, "target_id", None)
            if target_id:
                payload["target_id"] = target_id
            if isinstance(action, UseMoveAction):
                payload["move_name"] = action.move_name
                actor_state = battle.pokemon.get(action.actor_id)
                if actor_state is not None:
                    move_match = next(
                        (
                            move
                            for move in actor_state.spec.moves
                            if (move.name or "").strip().lower() == (action.move_name or "").strip().lower()
                        ),
                        None,
                    )
                    if move_match is not None:
                        payload["move_category"] = move_match.category
                        payload["move_type"] = move_match.type
            dispatcher.trigger(
                "action_resolved",
                actor_id=action.actor_id,
                payload=payload,
            )

        if isinstance(action, TrainerAction):
            trainer = battle.trainers.get(action.actor_id)
            if trainer is None:
                actor_state = battle.pokemon.get(action.actor_id)
                if actor_state is not None:
                    trainer = battle.trainers.get(actor_state.controller_id)
            if trainer is None:
                return None
            if action.action_type == ActionType.FREE:
                battle.log_event(
                    {
                        "type": "action",
                        "actor": action.actor_id,
                        "action_type": action.action_type.value,
                        "detail": action.describe_action(),
                    }
                )
                self.resolve(action)
                _emit_feature_trigger()
                return action
            if not trainer.has_action_available(action.action_type):
                action_label = action.action_type.value.capitalize()
                detail = trainer.action_consumed_detail(action.action_type) or "a previous action"
                raise ValueError(
                    f"Your {action_label} action was already consumed by {detail}."
                )
            detail = action.describe_action()
            trainer.mark_action(action.action_type, detail)
            battle.log_event(
                {
                    "type": "action",
                    "actor": action.actor_id,
                    "action_type": action.action_type.value,
                    "detail": detail,
                }
            )
            self.resolve(action)
            _emit_feature_trigger()
            return action
        mon_state = battle.pokemon.get(action.actor_id)
        if mon_state:
            if battle.current_actor_id is None:
                if battle._last_action_actor_id == action.actor_id and mon_state.actions_taken:
                    mon_state.reset_actions()
                elif battle._last_action_actor_id is not None and battle._last_action_actor_id != action.actor_id:
                    mon_state.reset_actions()
                elif not mon_state.actions_taken:
                    mon_state.reset_actions()
            if action.action_type == ActionType.FREE:
                battle.log_event(
                    {
                        "type": "action",
                        "actor": action.actor_id,
                        "action_type": action.action_type.value,
                        "detail": action.describe_action(),
                    }
                )
                self.resolve(action)
                _emit_feature_trigger()
                return action
            if not mon_state.has_action_available(action.action_type):
                if not battle._consume_extra_action(mon_state, action.action_type):
                    action_label = action.action_type.value.capitalize()
                    detail = mon_state.action_consumed_detail(action.action_type) or "a previous action"
                    raise ValueError(
                        f"Your {action_label} action was already consumed by {detail}."
                    )
            detail = mon_state.action_consumed_detail(action.action_type) or "a previous action"
            if mon_state.has_action_available(action.action_type):
                detail = action.describe_action()
                mon_state.mark_action(action.action_type, detail)
                battle.log_event(
                    {
                        "type": "action",
                        "actor": action.actor_id,
                        "action_type": action.action_type.value,
                        "detail": detail,
                    }
                )
        self.resolve(action)
        battle._last_action_actor_id = action.actor_id
        _emit_feature_trigger()
        return action
