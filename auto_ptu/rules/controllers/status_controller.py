"""Status ticking, duration changes, and end-of-turn status hooks.

This is a placeholder boundary for extracting status flow from BattleState.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..battle_state import BattleState, TurnPhase, ActionType, _FREEZE_STATUS_NAMES


@dataclass
class StatusController:
    battle: BattleState

    def run_phase_effects(self, phase) -> None:
        actor_id = self.battle.current_actor_id
        if not actor_id:
            return
        actor = self.battle.pokemon.get(actor_id)
        if actor is None or not actor.active:
            return
        if phase == TurnPhase.START:
            for payload in self.battle._apply_held_item_start(actor_id):
                self.battle.log_event(payload)
            for payload in self.battle._apply_food_regen(actor_id):
                self.battle.log_event(payload)
            for payload in self.battle._apply_food_buff_start(actor_id):
                self.battle.log_event(payload)
        events = actor.handle_phase_effects(self.battle, phase, actor_id)
        for payload in events:
            self.battle.log_event(payload)
            if payload.get("skip_turn"):
                self.battle._pending_status_skip = payload
        if phase == TurnPhase.END:
            for payload in self.battle._apply_held_item_end(actor_id):
                self.battle.log_event(payload)

    def consume_pending_status_skip(self) -> bool:
        pending = self.battle._pending_status_skip
        if not pending:
            return False
        self.battle._pending_status_skip = None
        actor_id = self.battle.current_actor_id
        actor = self.battle.pokemon.get(actor_id) if actor_id else None
        if actor is not None:
            pending_status = str(pending.get("status") or "").strip().lower()
            signature = (getattr(actor.spec, "poke_edge_choices", {}) or {}).get("signature_technique")
            signature_mod = ""
            signature_move = ""
            if isinstance(signature, dict):
                signature_mod = str(signature.get("modification_key") or signature.get("modification") or "").strip().lower()
                signature_mod = "".join(ch for ch in signature_mod if ch.isalnum())
                signature_move = str(signature.get("move") or signature.get("move_name") or "").strip()
            if signature_mod == "supremeconcentration" and pending_status in {"paralyzed", "flinch", "flinched", "enraged", "rage", "confusion", "confused"}:
                actor.add_temporary_effect(
                    "signature_supreme_concentration_ready",
                    move=signature_move,
                    status=pending_status,
                    round=self.battle.round,
                )
                self.battle.log_event(
                    {
                        "type": "trainer_feature",
                        "actor": actor_id,
                        "trainer": actor.controller_id,
                        "feature": "Signature Technique",
                        "effect": "supreme_concentration",
                        "move": signature_move,
                        "status": pending.get("status"),
                        "description": "Supreme Concentration allows the Signature Technique move despite the status skip.",
                        "target_hp": actor.hp,
                    }
                )
                self.battle._pending_status_skip = None
                return False
            if (
                actor.get_temporary_effects("duelist_manual_ignore_status")
                and pending_status in {"confusion", "confused", "enraged", "rage", "infatuated", "suppressed"}
            ):
                self.battle.log_event(
                    {
                        "type": "trainer_feature",
                        "actor": actor_id,
                        "trainer": actor.controller_id,
                        "feature": "Duelist's Manual",
                        "effect": "ignore_status_skip",
                        "status": pending.get("status"),
                        "description": "Duelist's Manual allows the Pokemon to act through the volatile status.",
                        "target_hp": actor.hp,
                    }
                )
                self.battle._pending_status_skip = None
                return False
            if pending_status in _FREEZE_STATUS_NAMES:
                end_events = actor.handle_phase_effects(self.battle, TurnPhase.END, actor_id)
                for payload in end_events:
                    self.battle.log_event(payload)
            if ActionType.STANDARD not in actor.actions_taken:
                actor.mark_action(ActionType.STANDARD, "Status skip")
            if ActionType.SHIFT not in actor.actions_taken:
                actor.mark_action(ActionType.SHIFT, "Status skip")
        self.battle.log_event(
            {
                "type": "status_skip",
                "actor": actor_id,
                "status": pending.get("status"),
                "phase": pending.get("phase", self.battle.phase.value),
                "reason": pending.get("effect"),
            }
        )
        return True
