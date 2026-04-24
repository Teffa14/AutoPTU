"""Phase sequencing and transitions.

This is a placeholder boundary for extracting phase flow from BattleState.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..battle_state import BattleState, TurnPhase, _PHASE_SEQUENCE


@dataclass
class PhaseController:
    battle: BattleState

    def current_phase(self) -> Optional[TurnPhase]:
        return getattr(self.battle, "phase", None)

    def advance_phase(self) -> None:
        if self.battle.current_actor_id is None:
            raise ValueError("No active combatant to advance phase for.")
        try:
            idx = _PHASE_SEQUENCE.index(self.battle.phase)
        except ValueError:
            idx = 0
        if idx >= len(_PHASE_SEQUENCE) - 1:
            return
        self.battle.phase = _PHASE_SEQUENCE[idx + 1]
        self.battle.log_event(
            {
                "type": "phase",
                "round": self.battle.round,
                "actor": self.battle.current_actor_id,
                "phase": self.battle.phase.value,
            }
        )
        if getattr(self.battle, "trainer_feature_dispatcher", None) is not None:
            self.battle.trainer_feature_dispatcher.trigger(
                "phase_change",
                actor_id=self.battle.current_actor_id,
                payload={"phase": self.battle.phase.value},
            )
        self.battle.status_controller.run_phase_effects(self.battle.phase)
        if self.battle.phase == TurnPhase.END:
            for pid, mon in self.battle.pokemon.items():
                entry = next(iter(mon.get_temporary_effects("corrosive_tick")), None)
                if not entry:
                    continue
                if entry.get("round") != self.battle.round:
                    mon.remove_temporary_effect("corrosive_tick")
                    continue
                if not (mon.has_status("Poisoned") or mon.has_status("Badly Poisoned")):
                    mon.remove_temporary_effect("corrosive_tick")
                    continue
                damage = mon._apply_tick_damage(1)
                self.battle.log_event(
                    {
                        "type": "ability",
                        "actor": self.battle.current_actor_id,
                        "target": pid,
                        "ability": "Corrosive Toxins",
                        "phase": self.battle.phase.value,
                        "effect": "tick",
                        "amount": damage,
                        "description": "Corrosive Toxins applies a poison tick.",
                        "target_hp": mon.hp,
                    }
                )
                mon.remove_temporary_effect("corrosive_tick")
        if self.battle.status_controller.consume_pending_status_skip():
            return

    def start_round(self) -> None:
        battle = self.battle
        if battle.round >= 1:
            battle._resolve_dimensional_rifts_end_of_round()
            if hasattr(battle, "_gain_duelist_momentum"):
                for actor_id, pokemon in list(battle.pokemon.items()):
                    if pokemon.active and not pokemon.fainted and not pokemon.is_trainer_combatant():
                        battle._gain_duelist_momentum(actor_id, reason="round_end")
        battle.round += 1
        battle.round_uses = 0
        battle.dance_moves_used_this_round = {}
        battle.fainted_history = [
            entry
            for entry in battle.fainted_history
            if int(entry.get("round", 0) or 0) >= battle.round - 1
        ]
        battle._advance_terrain()
        battle._advance_zone_effects()
        battle._advance_room_effects()
        battle._resolve_delayed_hits()
        battle._clear_expired_follow_me()
        battle._clear_expired_foresight()
        for trainer in battle.trainers.values():
            trainer.expire_temporary_ap(battle.round)
            trainer.reset_actions()
        for mon in battle.pokemon.values():
            mon.remove_temporary_effect("intercept_ready")
            while mon.remove_temporary_effect("extra_action"):
                continue
            while mon.remove_temporary_effect("delayed"):
                continue
            while mon.remove_temporary_effect("riposte_ready"):
                continue
        battle.declared_actions = []
        if battle.round == 1:
            for actor_id, pokemon in battle.pokemon.items():
                if pokemon.active and not pokemon.fainted:
                    battle._apply_send_out_trainer_feature_effects(actor_id, initial_setup=True)
        battle.initiative_order = battle._build_initiative_order()
        battle._initiative_index = -1
        battle.phase = TurnPhase.START
        battle.current_actor_id = None
        battle._last_action_actor_id = None
        battle.damage_last_round = set(battle.damage_this_round)
        battle.damage_taken_from_last_round = {
            actor_id: set(sources) for actor_id, sources in battle.damage_taken_from.items()
        }
        battle.damage_this_round.clear()
        battle.damage_taken_from.clear()
        battle.damage_received_this_round.clear()
        battle._injuries_previous_round = dict(battle._injuries_last_round)
        battle._injuries_last_round = {
            actor_id: pokemon.injuries for actor_id, pokemon in battle.pokemon.items()
        }
        battle.echoed_voice_rounds = [r for r in battle.echoed_voice_rounds if r >= battle.round - 2]
        battle.fusion_bolt_rounds = [r for r in battle.fusion_bolt_rounds if r >= battle.round - 1]
        battle.fusion_flare_rounds = [r for r in battle.fusion_flare_rounds if r >= battle.round - 1]
        initial_states = []
        for actor_id, pokemon in battle.pokemon.items():
            if battle.round == 1 and pokemon.active:
                pokemon.add_temporary_effect("joined_round", round=battle.round)
            statuses = [
                name for entry in pokemon.statuses if (name := pokemon._normalized_status_name(entry))
            ]
            initial_states.append(
                {
                    "actor": actor_id,
                    "hp": pokemon.hp,
                    "max_hp": pokemon.max_hp(),
                    "statuses": statuses,
                    "abilities": pokemon.ability_names(),
                    "active": pokemon.active,
                }
            )
        battle.log_event(
            {
                "type": "round_start",
                "round": battle.round,
                "initiative": [entry.to_dict() for entry in battle.initiative_order],
                "weather": battle.weather,
                "initial_states": initial_states,
            }
        )
        if getattr(battle, "trainer_feature_dispatcher", None) is not None:
            battle.trainer_feature_dispatcher.trigger(
                "round_start",
                payload={"round": battle.round},
            )
        air_lock_holders = battle._active_ability_holders("Air Lock")
        if air_lock_holders and (battle.weather or "").strip().lower() not in {"clear", "normal"}:
            for pid in air_lock_holders:
                battle.log_event(
                    {
                        "type": "ability",
                        "actor": pid,
                        "ability": "Air Lock",
                        "effect": "weather_suppress",
                        "weather": battle.weather,
                        "description": "Air Lock suppresses the active weather.",
                    }
                )
        battle._apply_arena_trap()
        for actor_id, pokemon in battle.pokemon.items():
            if pokemon.active and not pokemon.fainted:
                battle._trigger_intimidate(actor_id)
                battle._trigger_impostor(actor_id)

    def end_turn(self) -> None:
        battle = self.battle
        if battle.current_actor_id is None:
            return
        actor = battle.pokemon.get(battle.current_actor_id)
        if actor:
            while actor.remove_temporary_effect("extra_action"):
                continue
            while actor.remove_temporary_effect("last_turn_round"):
                continue
            actor.add_temporary_effect("last_turn_round", round=battle.round)
            battle._clear_adaptive_geography(battle.current_actor_id)
            battle._clear_psionic_sponge_moves(battle.current_actor_id)
        battle._apply_psionic_overload_lift_ticks()
        battle.log_event(
            {
                "type": "turn_end",
                "round": battle.round,
                "actor": battle.current_actor_id,
                "phase": battle.phase.value,
            }
        )
        if getattr(battle, "trainer_feature_dispatcher", None) is not None:
            battle.trainer_feature_dispatcher.trigger(
                "turn_end",
                actor_id=battle.current_actor_id,
                payload={"round": battle.round},
            )
        battle.current_actor_id = None
        battle.phase = TurnPhase.START
