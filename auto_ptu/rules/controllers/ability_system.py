"""Ability system extraction for targeted hooks and modifiers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..battle_state import BattleState, PokemonState, MoveSpec
from ..abilities import (
    apply_defender_pre_damage_abilities,
    apply_defender_immunity_abilities,
    apply_accuracy_ability_modifiers,
)


@dataclass
class AbilitySystem:
    battle: BattleState

    def apply_accuracy_modifiers(
        self,
        attacker_id: str,
        attacker: PokemonState,
        defender_id: str,
        defender: PokemonState,
        move: MoveSpec,
        accuracy_adjust: int,
    ) -> int:
        return apply_accuracy_ability_modifiers(
            self.battle,
            attacker_id=attacker_id,
            attacker=attacker,
            defender_id=defender_id,
            defender=defender,
            move=move,
            accuracy_adjust=accuracy_adjust,
        )

    def apply_defender_immunity(
        self,
        attacker_id: str,
        defender_id: str,
        defender: PokemonState,
        move: MoveSpec,
        effective_move: MoveSpec,
        result: Dict[str, object],
    ) -> None:
        apply_defender_immunity_abilities(
            self.battle,
            attacker_id=attacker_id,
            defender_id=defender_id,
            defender=defender,
            move=move,
            effective_move=effective_move,
            result=result,
        )

    def apply_defender_pre_damage(
        self,
        attacker_id: str,
        attacker: PokemonState,
        defender_id: str,
        defender: PokemonState,
        move: MoveSpec,
        effective_move: MoveSpec,
        result: Dict[str, object],
        events: List[dict],
    ) -> bool:
        return apply_defender_pre_damage_abilities(
            self.battle,
            attacker_id=attacker_id,
            attacker=attacker,
            defender_id=defender_id,
            defender=defender,
            move=move,
            effective_move=effective_move,
            result=result,
            events=events,
        )
