"""Hybrid AI: reflex heuristics + shallow lookahead + opponent profiling."""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .battle_state import (
    BattleState,
    PokemonState,
    TrainerState,
    UseMoveAction,
    ShiftAction,
    GrappleAction,
    SwitchAction,
    TakeBreatherAction,
    DisengageAction,
    TurnPhase,
    _load_maneuver_moves,
    _load_move_specs,
)
from .calculations import expected_damage
from . import movement, targeting
from ..data_models import MoveSpec
from ..ai import aai_port
from ..ai import policy_adapter
from . import frequency
from .. import ptu_engine

_MEANINGFUL_DAMAGE_THRESHOLD = 1.0


@dataclass
class HybridAIConfig:
    top_k: int = 6
    top_m: int = 3
    depth: int = 2
    depth_extra: int = 3
    rollouts: int = 5
    lethal_threshold: float = 0.65
    danger_threshold: float = 0.5
    profile_influence_cap: float = 0.2
    debug: bool = False


@dataclass
class OpponentProfile:
    action_type: Dict[str, float] = field(default_factory=dict)
    target_pref: Dict[str, float] = field(default_factory=dict)
    risk_tolerance: Dict[str, float] = field(default_factory=dict)
    move_usage: Dict[str, float] = field(default_factory=dict)
    decay: float = 0.9

    def _decay_map(self, data: Dict[str, float]) -> None:
        for key in list(data.keys()):
            data[key] *= self.decay
            if data[key] < 1e-3:
                data.pop(key, None)

    def update_action(self, battle: BattleState, actor_id: str, action: object) -> None:
        self._decay_map(self.action_type)
        self._decay_map(self.target_pref)
        self._decay_map(self.risk_tolerance)
        self._decay_map(self.move_usage)
        kind = _action_kind(action)
        self.action_type[kind] = self.action_type.get(kind, 0.0) + 1.0
        target_pref = _target_preference(battle, actor_id, action)
        if target_pref:
            self.target_pref[target_pref] = self.target_pref.get(target_pref, 0.0) + 1.0
        risk = _risk_preference(battle, actor_id, action)
        if risk:
            self.risk_tolerance[risk] = self.risk_tolerance.get(risk, 0.0) + 1.0
        move_name = _action_move_name(action)
        if move_name:
            self.move_usage[move_name] = self.move_usage.get(move_name, 0.0) + 1.0


@dataclass
class ProfileStore:
    profiles: Dict[str, OpponentProfile] = field(default_factory=dict)
    path: Optional[Path] = None

    def profile_for(self, signature: str) -> OpponentProfile:
        if signature not in self.profiles:
            self.profiles[signature] = OpponentProfile()
        return self.profiles[signature]

    def update(self, battle: BattleState, actor_id: str, action: object) -> None:
        signature = _actor_signature(battle, actor_id)
        self.profile_for(signature).update_action(battle, actor_id, action)

    def load(self) -> None:
        if not self.path or not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for key, entry in raw.items():
            profile = OpponentProfile()
            profile.action_type = dict(entry.get("action_type", {}))
            profile.target_pref = dict(entry.get("target_pref", {}))
            profile.risk_tolerance = dict(entry.get("risk_tolerance", {}))
            profile.move_usage = dict(entry.get("move_usage", {}))
            self.profiles[key] = profile

    def save(self) -> None:
        if not self.path:
            return
        payload: Dict[str, dict] = {}
        for key, profile in self.profiles.items():
            payload[key] = {
                "action_type": profile.action_type,
                "target_pref": profile.target_pref,
                "risk_tolerance": profile.risk_tolerance,
                "move_usage": profile.move_usage,
            }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


_GLOBAL_STORE: Optional[ProfileStore] = None
_DEFAULT_CONFIG = HybridAIConfig()


def rank_candidates(
    battle: BattleState,
    actor_id: str,
    *,
    ai_level: str = "standard",
    profile_store: Optional[ProfileStore] = None,
    candidates: Optional[Sequence[object]] = None,
) -> List[Tuple[float, object]]:
    store = profile_store or get_profile_store()
    items = list(candidates) if candidates is not None else generate_candidates(battle, actor_id)
    scored = [(score_action(battle, actor_id, action), action) for action in items]
    scored = _apply_aai_port_adjustments(
        battle,
        actor_id,
        scored,
        store,
        ai_level=ai_level,
    )
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def get_profile_store(path: Optional[Path] = None) -> ProfileStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = ProfileStore(path=path)
        if path:
            _GLOBAL_STORE.load()
    return _GLOBAL_STORE


def set_profile_store_path(path: Path, *, save_current: bool = True, load: bool = True) -> ProfileStore:
    global _GLOBAL_STORE
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if _GLOBAL_STORE is not None and save_current:
        try:
            _GLOBAL_STORE.save()
        except Exception:
            pass
    _GLOBAL_STORE = ProfileStore(path=target)
    if load:
        try:
            _GLOBAL_STORE.load()
        except Exception:
            _GLOBAL_STORE.profiles = {}
    return _GLOBAL_STORE


def current_profile_store_path() -> Optional[Path]:
    if _GLOBAL_STORE is None:
        return None
    return _GLOBAL_STORE.path


def _action_eval_cache(battle: BattleState) -> Dict[Tuple[str, str, int, int], dict]:
    cache = getattr(battle, "_ai_action_eval_cache", None)
    if not isinstance(cache, dict):
        cache = {}
        setattr(battle, "_ai_action_eval_cache", cache)
    return cache


def _simulated_action_outcome(
    battle: BattleState,
    actor_id: str,
    action: object,
    *,
    rollouts: int = 2,
) -> dict:
    key = (
        actor_id,
        _action_label(action),
        int(getattr(battle, "round", 0) or 0),
        len(getattr(battle, "log", []) or []),
    )
    cache = _action_eval_cache(battle)
    cached = cache.get(key)
    if isinstance(cached, dict):
        return cached
    if not isinstance(action, UseMoveAction):
        result = {"damage": 0.0, "self_loss": 0.0, "item_removed": 0.0, "status_gain": 0.0}
        cache[key] = result
        return result
    totals = {"damage": 0.0, "self_loss": 0.0, "item_removed": 0.0, "status_gain": 0.0}
    samples = 0
    for rollout in range(max(1, int(rollouts or 1))):
        sim = _clone_battle(battle)
        _advance_rng(sim, rollout)
        actor_before = sim.pokemon.get(actor_id)
        target_before = sim.pokemon.get(action.target_id) if action.target_id else None
        actor_hp_before = float(actor_before.hp or 0) if actor_before is not None and actor_before.hp is not None else 0.0
        target_hp_before = float(target_before.hp or 0) if target_before is not None and target_before.hp is not None else 0.0
        target_items_before = len(getattr(target_before.spec, "items", []) or []) if target_before is not None else 0
        target_status_before = len(getattr(target_before, "statuses", []) or []) if target_before is not None else 0
        _simulate_action(sim, actor_id, copy.deepcopy(action))
        actor_after = sim.pokemon.get(actor_id)
        target_after = sim.pokemon.get(action.target_id) if action.target_id else None
        actor_hp_after = float(actor_after.hp or 0) if actor_after is not None and actor_after.hp is not None else 0.0
        target_hp_after = float(target_after.hp or 0) if target_after is not None and target_after.hp is not None else 0.0
        target_items_after = len(getattr(target_after.spec, "items", []) or []) if target_after is not None else 0
        target_status_after = len(getattr(target_after, "statuses", []) or []) if target_after is not None else 0
        totals["damage"] += max(0.0, target_hp_before - target_hp_after)
        totals["self_loss"] += max(0.0, actor_hp_before - actor_hp_after)
        totals["item_removed"] += max(0.0, float(target_items_before - target_items_after))
        totals["status_gain"] += max(0.0, float(target_status_after - target_status_before))
        samples += 1
    if samples <= 0:
        result = {"damage": 0.0, "self_loss": 0.0, "item_removed": 0.0, "status_gain": 0.0}
        cache[key] = result
        return result
    result = {name: value / samples for name, value in totals.items()}
    cache[key] = result
    return result


def generate_candidates(battle: BattleState, actor_id: str) -> List[object]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.fainted or not actor.active:
        return []
    candidates: List[object] = []
    opponents = _opponent_ids(battle, actor_id)
    ally_ids = _ally_ids(battle, actor_id)

    for move in actor.spec.moves:
        move_name = (move.name or "").strip()
        if not move_name:
            continue
        if _is_reaction_only_move(move):
            continue
        if _is_harmful_self_status_move(move):
            continue
        type_choices = _type_choice_options_for_move(battle, actor_id, actor, move)
        target_kind = targeting.normalized_target_kind(move)
        requires_target = targeting.move_requires_target(move)
        if target_kind == "self" and not requires_target:
            choice_values = type_choices or [None]
            for chosen_type in choice_values:
                if (move.category or "").lower() != "status":
                    if not _move_hits_opponent(battle, actor_id, move, actor_id):
                        continue
                action = UseMoveAction(
                    actor_id=actor_id,
                    move_name=move_name,
                    target_id=actor_id,
                    chosen_type=chosen_type,
                )
                if _action_is_legal(battle, action, actor_id):
                    candidates.append(action)
            continue
        if target_kind == "blessing":
            candidate_ids = [actor_id] + [ally_id for ally_id in ally_ids if ally_id != actor_id]
            for target_id in candidate_ids:
                target_state = battle.pokemon.get(target_id)
                if target_state is None or target_state.fainted:
                    continue
                if target_state.position is not None and actor.position is not None:
                    if not targeting.is_target_in_range(
                        actor.position,
                        target_state.position,
                        move,
                        attacker_size=getattr(actor.spec, "size", ""),
                        target_size=getattr(target_state.spec, "size", ""),
                        grid=battle.grid,
                    ):
                        continue
                    if battle.grid and not battle.has_line_of_sight(actor_id, target_state.position, target_id):
                        continue
                choice_values = type_choices or [None]
                for chosen_type in choice_values:
                    action = UseMoveAction(
                        actor_id=actor_id,
                        move_name=move_name,
                        target_id=target_id,
                        chosen_type=chosen_type,
                    )
                    if _action_is_legal(battle, action, actor_id):
                        candidates.append(action)
            continue
        candidate_ids = opponents if target_kind != "ally" else ally_ids
        if not candidate_ids and not requires_target:
            choice_values = type_choices or [None]
            for chosen_type in choice_values:
                if (move.category or "").lower() != "status":
                    if not _move_hits_opponent(battle, actor_id, move, None):
                        continue
                action = UseMoveAction(
                    actor_id=actor_id,
                    move_name=move_name,
                    target_id=None,
                    chosen_type=chosen_type,
                )
                if _action_is_legal(battle, action, actor_id):
                    candidates.append(action)
            continue
        for target_id in candidate_ids:
            target_state = battle.pokemon.get(target_id)
            if target_state is None or target_state.position is None or target_state.fainted:
                continue
            if actor.position is None:
                continue
            if _should_skip_target_for_move(battle, actor_id, move, target_id):
                continue
            if not targeting.is_target_in_range(
                actor.position,
                target_state.position,
                move,
                attacker_size=getattr(actor.spec, "size", ""),
                target_size=getattr(target_state.spec, "size", ""),
                grid=battle.grid,
            ):
                continue
            if battle.grid and not battle.has_line_of_sight(actor_id, target_state.position, target_id):
                continue
            choice_values = type_choices or [None]
            for chosen_type in choice_values:
                action = UseMoveAction(
                    actor_id=actor_id,
                    move_name=move_name,
                    target_id=target_id,
                    chosen_type=chosen_type,
                )
                if _action_is_legal(battle, action, actor_id):
                    candidates.append(action)

    for move in _load_maneuver_moves().values():
        move_name = (move.name or "").strip()
        if not move_name:
            continue
        for target_id in opponents:
            target_state = battle.pokemon.get(target_id)
            if target_state is None or target_state.position is None or target_state.fainted:
                continue
            if actor.position is None:
                continue
            if not targeting.is_target_in_range(
                actor.position,
                target_state.position,
                move,
                attacker_size=getattr(actor.spec, "size", ""),
                target_size=getattr(target_state.spec, "size", ""),
                grid=battle.grid,
            ):
                continue
            if battle.grid and not battle.has_line_of_sight(actor_id, target_state.position, target_id):
                continue
            action = UseMoveAction(actor_id=actor_id, move_name=move_name, target_id=target_id)
            if _action_is_legal(battle, action, actor_id):
                candidates.append(action)

    danger = _danger_score(battle, actor_id)
    if battle.grid is not None and actor.position is not None:
        reachable = movement.legal_shift_tiles(battle, actor_id)
        if reachable:
            for dest in _top_shift_targets(battle, actor_id, reachable):
                if dest == actor.position:
                    continue
                action = ShiftAction(actor_id=actor_id, destination=dest)
                if _action_is_legal(battle, action, actor_id):
                    candidates.append(action)
            if len(reachable) > 1 and danger >= 0.4:
                for dest in _top_defensive_shifts(battle, actor_id, reachable):
                    if dest == actor.position:
                        continue
                    action = ShiftAction(actor_id=actor_id, destination=dest)
                    if _action_is_legal(battle, action, actor_id):
                        candidates.append(action)
        if actor.position and opponents and (danger >= 0.4 or _prefers_ranged_disengage(battle, actor_id)):
            for dest in _top_disengage_targets(battle, actor_id, reachable):
                if dest == actor.position:
                    continue
                action = DisengageAction(actor_id=actor_id, destination=dest)
                if _action_is_legal(battle, action, actor_id):
                    candidates.append(action)

    status = battle.grapple_status(actor_id)
    if status:
        other_id = status.get("other_id")
        for action_kind in ["attack", "secure", "move", "end", "contest", "escape"]:
            action = GrappleAction(actor_id=actor_id, action_kind=action_kind, target_id=other_id)
            if action_kind == "move" and battle.grid is not None:
                dests = movement.legal_shift_tiles(battle, actor_id)
                for dest in dests[:2]:
                    action = GrappleAction(
                        actor_id=actor_id,
                        action_kind=action_kind,
                        target_id=other_id,
                        destination=dest,
                    )
                    if _action_is_legal(battle, action, actor_id):
                        candidates.append(action)
                continue
            if _action_is_legal(battle, action, actor_id):
                candidates.append(action)

    bench = _bench_candidates(battle, actor_id)
    for candidate in bench:
        target_position = None
        if hasattr(battle, "_best_ai_switch_position"):
            try:
                target_position = battle._best_ai_switch_position(
                    outgoing_id=actor_id,
                    replacement_id=candidate,
                )
            except Exception:
                target_position = None
        action = SwitchAction(
            actor_id=actor_id,
            replacement_id=candidate,
            target_position=target_position,
        )
        if _action_is_legal(battle, action, actor_id):
            candidates.append(action)

    if actor.hp is not None and actor.max_hp() > 0:
        if actor.hp / actor.max_hp() <= 0.35:
            has_debuffs = any(value != 0 for value in actor.combat_stages.values())
            if actor.statuses or actor.temp_hp > 0 or has_debuffs:
                action = TakeBreatherAction(actor_id=actor_id)
                if _action_is_legal(battle, action, actor_id):
                    candidates.append(action)

    return candidates


def _is_harmful_self_status_move(move: MoveSpec) -> bool:
    if (move.category or "").strip().lower() != "status":
        return False
    target_kind = targeting.normalized_target_kind(move)
    if target_kind != "self":
        return False
    text = _move_effect_blob(move)
    self_debuff_tokens = (
        "lower",
        "reduce",
        "decrease",
        "drops",
        "-1",
        "-2",
        "vulnerable",
        "tripped",
        "burn",
        "poison",
        "sleep",
        "paraly",
        "flinch",
        "confus",
    )
    return any(token in text for token in self_debuff_tokens)


def _should_skip_target_for_move(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    target_id: Optional[str],
) -> bool:
    if not target_id:
        return False
    target_kind = targeting.normalized_target_kind(move)
    if target_kind in {"self", "field"}:
        return False
    actor_team = _team_for(battle, actor_id)
    target_team = _team_for(battle, target_id)
    if not actor_team or actor_team != target_team:
        return False
    if (move.category or "").strip().lower() != "status":
        return True
    text = _move_effect_blob(move)
    harmful_tokens = (
        "lower",
        "reduce",
        "decrease",
        "drops",
        "-1",
        "-2",
        "vulnerable",
        "tripped",
        "burn",
        "poison",
        "sleep",
        "paraly",
        "flinch",
        "confus",
        "badly poisoned",
    )
    return any(token in text for token in harmful_tokens)


def score_action(battle: BattleState, actor_id: str, action: object) -> float:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return -999.0
    current_round = getattr(battle, "round", 0) or 0
    kind = _action_kind(action)
    score = 0.0
    if isinstance(action, UseMoveAction):
        move = _resolve_move(actor, action.move_name)
        target = battle.pokemon.get(action.target_id) if action.target_id else None
        if move is None:
            return -999.0
        if _should_skip_target_for_move(battle, actor_id, move, action.target_id):
            return -8.0
        if _is_maneuver_move(move):
            return _score_maneuver_action(battle, actor_id, move, target)
        if _is_struggle_name(move.name or action.move_name):
            score -= 2.5
            if _damaging_candidate_actions(
                battle,
                actor_id,
                generate_candidates(battle, actor_id),
                include_struggle=False,
            ):
                score -= 6.0
        if (move.category or "").lower() == "status":
            text = _move_effect_blob(move)
            self_debuff_tokens = (
                "lower",
                "reduce",
                "decrease",
                "drops",
                "-1",
                "-2",
                "vulnerable",
                "tripped",
                "burn",
                "poison",
                "sleep",
                "paraly",
                "flinch",
                "confus",
            )
            if (action.target_id is None or action.target_id == actor_id) and any(token in text for token in self_debuff_tokens):
                return -3.5
        if (move.category or "").lower() != "status":
            if not _move_hits_opponent(battle, actor_id, move, action.target_id):
                return -5.0
        if move.category.lower() != "status" and target is not None:
            outcome = _simulated_action_outcome(battle, actor_id, action)
            amount = float(outcome.get("damage", 0.0) or 0.0)
            score += amount
            if target.hp is not None and target.hp > 0:
                score += 0.2 * (amount / target.hp)
            score += 2.25 * float(outcome.get("item_removed", 0.0) or 0.0)
            score += 0.45 * float(outcome.get("status_gain", 0.0) or 0.0)
            score -= 0.2 * float(outcome.get("self_loss", 0.0) or 0.0)
            score += _item_denial_attack_bonus(battle, move, target, current_round)
            repeated_failures = _recent_same_move_target_no_damage_count(
                battle,
                actor_id,
                action.move_name,
                action.target_id,
                limit=6,
            )
            if amount <= _MEANINGFUL_DAMAGE_THRESHOLD:
                score -= 0.9
                if repeated_failures >= 2:
                    score -= min(8.0, 2.6 * repeated_failures)
            low_impact_repeats = _recent_same_move_target_low_damage_count(
                battle,
                actor_id,
                action.move_name,
                action.target_id,
                limit=6,
            )
            if target.max_hp() > 0 and amount > _MEANINGFUL_DAMAGE_THRESHOLD:
                damage_ratio = amount / max(1, target.max_hp())
                if damage_ratio <= 0.12 and low_impact_repeats >= 2:
                    score -= min(6.5, 1.85 * low_impact_repeats)
        if move.category.lower() == "status":
            score += 0.25
            score += _status_move_setup_score(battle, actor_id, move, action.target_id, current_round)
            score += _type_choice_bonus(battle, actor_id, move, action.chosen_type)
            if current_round >= 8:
                score -= 0.2
            if current_round >= 12:
                score -= 0.45
        score += _combo_description_bonus(battle, actor_id, move, target)
        score += _combo_intent_bonus(battle, actor_id, action, move, target)
        if move.priority > 0:
            score += 0.3
        last_move = _last_move_name(actor)
        if last_move and last_move.lower() == move.name.lower():
            score -= 0.4 if move.category.lower() == "status" else 0.2
    elif isinstance(action, ShiftAction):
        score += _shift_score(battle, actor_id, action.destination)
    elif isinstance(action, DisengageAction):
        score += _disengage_score(battle, actor_id, action.destination)
    elif isinstance(action, SwitchAction):
        score += _switch_score(battle, actor_id, action)
    elif isinstance(action, GrappleAction):
        score += 0.4
    elif isinstance(action, TakeBreatherAction):
        score += 0.8
    if kind == "defend" and not isinstance(action, SwitchAction):
        score += 0.6
    return score


def score_state(battle: BattleState, actor_id: str) -> float:
    actor_team = _team_for(battle, actor_id)
    score = 0.0
    for pid, mon in battle.pokemon.items():
        if mon.hp is None or mon.hp <= 0:
            continue
        ratio = (mon.hp or 0) / max(1, mon.max_hp())
        team = _team_for(battle, pid)
        if team == actor_team:
            score += ratio * 2.0
        else:
            score -= ratio * 2.2
        if mon.has_status("Vulnerable"):
            score -= 0.2 if team == actor_team else -0.2
        if mon.has_status("Tripped"):
            score -= 0.3 if team == actor_team else -0.3
    return score


def _choose_action_internal(
    battle: BattleState,
    actor_id: str,
    *,
    ai_level: str = "standard",
    config: Optional[HybridAIConfig] = None,
    profile_store: Optional[ProfileStore] = None,
    candidates: Optional[Sequence[object]] = None,
) -> Tuple[Optional[object], dict]:
    cfg = config or _DEFAULT_CONFIG
    store = profile_store or get_profile_store()

    candidates = list(candidates) if candidates is not None else generate_candidates(battle, actor_id)
    if not candidates:
        struggle = _struggle_action(battle, actor_id)
        if struggle is not None:
            return struggle, {"reason": "no_candidates_struggle"}
        return None, {"reason": "no_candidates"}

    status_streak, used_double = _status_streak_info(battle, actor_id)
    if status_streak >= 2:
        filtered = [action for action in candidates if not _is_status_action(battle, actor_id, action)]
        if filtered:
            candidates = filtered
    elif status_streak == 1 and used_double:
        filtered = [action for action in candidates if not _is_status_action(battle, actor_id, action)]
        if filtered:
            candidates = filtered

    non_struggle_damage = _damaging_candidate_actions(
        battle,
        actor_id,
        candidates,
        include_struggle=False,
    )

    stale = _recent_no_damage(battle, actor_id, limit=2) or _recent_no_offense(battle, actor_id, limit=1) or _global_stale(battle, rounds=1)
    if stale:
        ineffective_names = _recent_ineffective_move_names(battle, actor_id, limit=3)
        struggle = _struggle_action(battle, actor_id)
        if ineffective_names:
            actor = battle.pokemon.get(actor_id)
            filtered_damage = []
            for action in non_struggle_damage:
                move_name = str(getattr(action, "move_name", "") or "").strip().lower()
                repeated_failures = (
                    _recent_same_move_target_no_damage_count(
                        battle,
                        actor_id,
                        getattr(action, "move_name", ""),
                        getattr(action, "target_id", None),
                        limit=6,
                    )
                    if isinstance(action, UseMoveAction)
                    else 0
                )
                if move_name not in ineffective_names:
                    if repeated_failures < 2:
                        filtered_damage.append(action)
                    continue
                if not isinstance(action, UseMoveAction) or actor is None:
                    continue
                move = _resolve_move(actor, action.move_name)
                target = battle.pokemon.get(action.target_id) if action.target_id else None
                if move is None or target is None:
                    continue
                if _expected_damage_for_action(battle, actor_id, action) > _MEANINGFUL_DAMAGE_THRESHOLD:
                    filtered_damage.append(action)
            non_struggle_damage = filtered_damage
            if not non_struggle_damage and struggle is not None:
                best_switch = _best_switch_action(battle, actor_id, candidates)
                if best_switch is not None and score_action(battle, actor_id, best_switch) > 0.75:
                    return best_switch, {"reason": "stale_switch"}
                best_disengage = _best_disengage_action(battle, actor_id, candidates)
                if (
                    best_disengage is not None
                    and score_action(battle, actor_id, best_disengage) >= 0.0
                    and _disengage_has_tactical_value(battle, actor_id, best_disengage.destination)
                ):
                    return best_disengage, {"reason": "stale_disengage"}
                best_status = _best_status_action(battle, actor_id, candidates)
                best_status_name = (
                    str(getattr(best_status, "move_name", "") or "").strip().lower()
                    if isinstance(best_status, UseMoveAction)
                    else ""
                )
                if (
                    best_status is not None
                    and best_status_name not in ineffective_names
                    and score_action(battle, actor_id, best_status) >= -0.1
                ):
                    return best_status, {"reason": "stale_setup"}
                return struggle, {"reason": "stale_ineffective_struggle"}
        if non_struggle_damage:
            non_struggle_damage.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
            return non_struggle_damage[0], {"reason": "stale_force_damage"}
        best_switch = _best_switch_action(battle, actor_id, candidates)
        if best_switch is not None and score_action(battle, actor_id, best_switch) > 0.75:
            return best_switch, {"reason": "stale_switch"}
        best_disengage = _best_disengage_action(battle, actor_id, candidates)
        if (
            best_disengage is not None
            and score_action(battle, actor_id, best_disengage) >= 0.0
            and _disengage_has_tactical_value(battle, actor_id, best_disengage.destination)
        ):
            return best_disengage, {"reason": "stale_disengage"}
        best_status = _best_status_action(battle, actor_id, candidates)
        best_status_name = (
            str(getattr(best_status, "move_name", "") or "").strip().lower()
            if isinstance(best_status, UseMoveAction)
            else ""
        )
        if (
            best_status is not None
            and best_status_name not in ineffective_names
            and score_action(battle, actor_id, best_status) >= -0.1
        ):
            return best_status, {"reason": "stale_setup"}
        if struggle is not None:
            return struggle, {"reason": "stale_struggle"}
        forced = _force_engage_action(
            battle,
            actor_id,
            candidates,
            include_struggle=False,
            allow_status=False,
        )
        if forced is not None:
            return forced, {"reason": "stale_no_damage"}

    scored = rank_candidates(
        battle,
        actor_id,
        ai_level=ai_level,
        profile_store=store,
        candidates=candidates,
    )

    lethal = _lethal_action(battle, actor_id, scored, cfg.lethal_threshold)
    if lethal:
        return lethal, {"reason": "lethal"}

    forced_combo = _forced_combo_maneuver_action(battle, actor_id, candidates)
    if forced_combo is not None:
        return forced_combo, {"reason": "combo_maneuver"}

    forced_conversion = _force_one_time_conversion_action(battle, actor_id, candidates)
    if forced_conversion is not None:
        return forced_conversion, {"reason": "conversion_once"}

    best_damage = _best_damaging_action(
        battle,
        actor_id,
        candidates,
        include_struggle=False,
    )
    best_item_denial = _best_item_denial_action(battle, actor_id, candidates)
    best_disengage = _best_disengage_action(battle, actor_id, candidates)
    best_maneuver = _best_maneuver_action(battle, actor_id, candidates)
    best_status = _best_status_action(battle, actor_id, candidates)
    damage_score = score_action(battle, actor_id, best_damage) if best_damage is not None else float("-inf")
    damage_expected = _expected_damage_for_action(battle, actor_id, best_damage) if best_damage is not None else 0.0
    ineffective_names = _recent_ineffective_move_names(battle, actor_id, limit=3)
    best_damage_name = (
        str(getattr(best_damage, "move_name", "") or "").strip().lower()
        if isinstance(best_damage, UseMoveAction)
        else ""
    )
    repeated_damage_failures = (
        _recent_same_move_target_no_damage_count(
            battle,
            actor_id,
            best_damage.move_name,
            best_damage.target_id,
            limit=6,
        )
        if isinstance(best_damage, UseMoveAction)
        else 0
    )
    weak_damage_baseline = bool(
        best_damage is None
        or damage_expected <= _MEANINGFUL_DAMAGE_THRESHOLD
        or (best_damage_name and best_damage_name in ineffective_names)
        or repeated_damage_failures >= 2
    )
    if best_maneuver is not None and _should_force_combo_maneuver(battle, actor_id, best_maneuver):
        return best_maneuver, {"reason": "combo_maneuver"}
    if best_damage is not None and best_status is not None:
        status_score = score_action(battle, actor_id, best_status)
        if _should_prioritize_type_conversion(
            battle,
            actor_id,
            best_status,
            best_damage,
            status_score=status_score,
            damage_score=damage_score,
        ):
            return best_status, {"reason": "type_conversion"}
        current_round = getattr(battle, "round", 0) or 0
        opening_round = current_round <= 3
        low_pressure = damage_score < 7.0 or weak_damage_baseline
        if opening_round and weak_damage_baseline and status_score + 0.1 >= damage_score:
            return best_status, {"reason": "opening_setup"}
        if opening_round and not weak_damage_baseline and status_score >= damage_score + 1.0:
            return best_status, {"reason": "opening_setup"}
        if low_pressure and status_score >= damage_score - 0.15 and status_streak < 2:
            return best_status, {"reason": "status_value"}
        if not weak_damage_baseline and status_score < damage_score + 0.75:
            best_status = None
    if (
        best_status is not None
        and _should_use_setup_before_engage(battle, actor_id, best_status)
    ):
        return best_status, {"reason": "pre_engage_setup"}
    if weak_damage_baseline:
        best_switch = _best_switch_action(battle, actor_id, candidates)
        if best_switch is not None and score_action(battle, actor_id, best_switch) >= -0.05:
            return best_switch, {"reason": "weak_damage_switch"}
        if (
            best_disengage is not None
            and score_action(battle, actor_id, best_disengage) >= 0.0
            and _disengage_has_tactical_value(battle, actor_id, best_disengage.destination)
        ):
            return best_disengage, {"reason": "weak_damage_disengage"}
        if best_status is not None and status_streak < 2:
            return best_status, {"reason": "weak_damage_setup"}
    if best_disengage is not None and best_damage is not None and _prefers_ranged_disengage(battle, actor_id):
        if _disengage_has_tactical_value(battle, actor_id, best_disengage.destination):
            return best_disengage, {"reason": "ranged_disengage"}
    if best_item_denial is not None:
        item_denial_score = score_action(battle, actor_id, best_item_denial)
        threshold = 4.5
        current_round = int(getattr(battle, "round", 0) or 0)
        if current_round <= 6:
            threshold += 1.5
        if best_damage is None or item_denial_score >= damage_score - threshold:
            return best_item_denial, {"reason": "item_denial"}
    if best_damage is not None:
        return best_damage, {"reason": "attack_in_range"}
    if best_maneuver is not None:
        if best_status is not None:
            maneuver_score = score_action(battle, actor_id, best_maneuver)
            status_score = score_action(battle, actor_id, best_status)
            if maneuver_score >= status_score + 0.75:
                return best_maneuver, {"reason": "maneuver"}
        else:
            return best_maneuver, {"reason": "maneuver"}
    if _should_close_distance(battle, actor_id, candidates):
        struggle = _struggle_action(battle, actor_id)
        if struggle is not None:
            return struggle, {"reason": "close_struggle"}
        forced = _force_engage_action(
            battle,
            actor_id,
            candidates,
            include_struggle=False,
            allow_status=False,
        )
        if forced is not None:
            return forced, {"reason": "close_distance"}

    top_scored = scored[: cfg.top_k]
    best_action, best_value = None, float("-inf")
    second_value = float("-inf")
    for base_score, action in top_scored:
        value = _lookahead_value(
            battle,
            actor_id,
            action,
            cfg,
            store,
            ai_level=ai_level,
        )
        if value > best_value:
            second_value = best_value
            best_value = value
            best_action = action
        elif value > second_value:
            second_value = value

    if best_action is None:
        return top_scored[0][1], {"reason": "fallback"}

    if cfg.debug:
        battle.log_event(
            {
                "type": "ai_debug",
                "actor": actor_id,
                "detail": {
                    "reason": "lookahead",
                    "best_value": best_value,
                    "second_value": second_value,
                    "danger": danger,
                    "candidates": [
                        {"score": score, "action": _action_label(action)}
                        for score, action in top_scored
                    ],
                },
            }
        )

    return best_action, {"reason": "lookahead", "value": best_value}


def _hybrid_rules_policy_adapter(
    context: policy_adapter.PolicyAdapterContext,
) -> Optional[policy_adapter.PolicyDecision]:
    action, info = _choose_action_internal(
        context.battle,
        context.actor_id,
        ai_level=context.ai_level,
        config=context.config,
        profile_store=context.profile_store,
        candidates=context.candidates,
    )
    if action is None:
        return None
    payload = dict(info or {})
    reason = str(payload.pop("reason", "") or "hybrid_rules")
    source = str(payload.pop("source", "") or "hybrid_rules")
    return policy_adapter.PolicyDecision(
        action=action,
        reason=reason,
        source=source,
        info=payload,
    )


def choose_action(
    battle: BattleState,
    actor_id: str,
    *,
    ai_level: str = "standard",
    config: Optional[HybridAIConfig] = None,
    profile_store: Optional[ProfileStore] = None,
    policy_adapter_name: Optional[str] = None,
) -> Tuple[Optional[object], dict]:
    cfg = config or _DEFAULT_CONFIG
    store = profile_store or get_profile_store()
    candidates = generate_candidates(battle, actor_id)
    adapter_name = str(policy_adapter_name or policy_adapter.get_active_policy_adapter() or "hybrid_rules").strip().lower()
    adapter = policy_adapter.get_policy_adapter(adapter_name)
    if adapter is None:
        raise ValueError(f"Unknown policy adapter: {adapter_name}")
    context = policy_adapter.PolicyAdapterContext(
        battle=battle,
        actor_id=actor_id,
        ai_level=ai_level,
        config=cfg,
        profile_store=store,
        candidates=list(candidates),
        helper={
            "generate_candidates": generate_candidates,
            "score_action": score_action,
            "score_state": score_state,
            "rank_candidates": rank_candidates,
            "fallback_choose_action": _choose_action_internal,
        },
        metadata={"adapter_name": adapter_name},
    )
    decision = adapter(context)
    if decision is None or decision.action is None:
        return None, {"reason": "no_adapter_decision", "source": adapter_name, "policy_adapter": adapter_name}
    info = dict(decision.info or {})
    info.setdefault("source", decision.source)
    info.setdefault("policy_adapter", adapter_name)
    return decision.action, {
        "reason": decision.reason,
        **info,
    }


def choose_best_move(
    battle: BattleState,
    actor_id: str,
    *,
    ai_level: str = "standard",
    config: Optional[HybridAIConfig] = None,
    profile_store: Optional[ProfileStore] = None,
) -> Tuple[Optional[MoveSpec], Optional[str], float]:
    action, info = choose_action(
        battle,
        actor_id,
        ai_level=ai_level,
        config=config,
        profile_store=profile_store,
    )
    if isinstance(action, UseMoveAction):
        actor = battle.pokemon.get(actor_id)
        move = _resolve_move(actor, action.move_name) if actor else None
        return move, action.target_id, float(info.get("value", 0.0))
    return None, None, float(info.get("value", 0.0))


def observe_action(battle: BattleState, actor_id: str, action: object, store: Optional[ProfileStore] = None) -> None:
    store = store or get_profile_store()
    store.update(battle, actor_id, action)
    _update_status_streak(battle, actor_id, action)
    _update_combo_intent(battle, actor_id, action)


def _lookahead_value(
    battle: BattleState,
    actor_id: str,
    action: object,
    cfg: HybridAIConfig,
    store: ProfileStore,
    *,
    ai_level: str,
) -> float:
    values: List[float] = []
    for rollout in range(cfg.rollouts):
        sim = _clone_battle(battle)
        _advance_rng(sim, rollout)
        _simulate_action(sim, actor_id, action)
        value = score_state(sim, actor_id)
        opponents = _opponent_ids(sim, actor_id)
        if opponents:
            opponent_id = opponents[0]
            response = _opponent_response(sim, opponent_id, cfg, store)
            if response:
                _simulate_action(sim, opponent_id, response)
                value = score_state(sim, actor_id)
                if cfg.depth_extra > cfg.depth and _non_obvious(value, 0.15):
                    reply = _best_quick_action(sim, actor_id, cfg)
                    if reply:
                        _simulate_action(sim, actor_id, reply)
                        value = score_state(sim, actor_id)
        values.append(value)
    return sum(values) / max(1, len(values))


def _opponent_response(
    battle: BattleState,
    actor_id: str,
    cfg: HybridAIConfig,
    store: ProfileStore,
) -> Optional[object]:
    candidates = generate_candidates(battle, actor_id)
    if not candidates:
        return None
    scored = [(score_action(battle, actor_id, action), action) for action in candidates]
    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[: cfg.top_m]
    profile = store.profile_for(_actor_signature(battle, actor_id))
    weighted = [(_apply_profile_bias(score, action, profile, cfg.profile_influence_cap), action) for score, action in top]
    weighted.sort(key=lambda item: item[0], reverse=True)
    return weighted[0][1]


def _best_quick_action(battle: BattleState, actor_id: str, cfg: HybridAIConfig) -> Optional[object]:
    candidates = generate_candidates(battle, actor_id)
    if not candidates:
        return None
    scored = [(score_action(battle, actor_id, action), action) for action in candidates]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def _non_obvious(value: float, threshold: float) -> bool:
    return abs(value) < threshold


def _simulate_action(battle: BattleState, actor_id: str, action: object) -> None:
    battle.current_actor_id = actor_id
    if isinstance(battle.phase, TurnPhase) and battle.phase == TurnPhase.START:
        try:
            battle.advance_phase()
        except ValueError:
            pass
    try:
        action.validate(battle)
        action.resolve(battle)
        _update_combo_intent(battle, actor_id, action)
        if isinstance(battle.phase, TurnPhase) and battle.phase == TurnPhase.ACTION:
            battle.advance_phase()
    except Exception:
        pass


def _clone_battle(battle: BattleState) -> BattleState:
    trainers = {key: _clone_trainer(trainer) for key, trainer in battle.trainers.items()}
    pokemon = {key: _clone_pokemon(mon) for key, mon in battle.pokemon.items()}
    clone = BattleState(
        trainers=trainers,
        pokemon=pokemon,
        weather=battle.weather,
        terrain=copy.deepcopy(battle.terrain),
        grid=copy.deepcopy(battle.grid),
        battle_context=battle.battle_context,
        active_slots=battle.active_slots,
        rng=copy.deepcopy(battle.rng),
    )
    clone.round = battle.round
    clone.round_uses = battle.round_uses
    clone.phase = battle.phase
    clone.current_actor_id = battle.current_actor_id
    clone.initiative_order = copy.deepcopy(battle.initiative_order)
    clone._initiative_index = battle._initiative_index
    clone._pending_status_skip = copy.deepcopy(battle._pending_status_skip)
    clone.frequency_usage = copy.deepcopy(battle.frequency_usage)
    clone.damage_this_round = set(battle.damage_this_round)
    clone.damage_last_round = set(battle.damage_last_round)
    clone.damage_taken_from = {key: set(value) for key, value in battle.damage_taken_from.items()}
    clone.damage_taken_from_last_round = {
        key: set(value) for key, value in battle.damage_taken_from_last_round.items()
    }
    clone.last_damage_taken = copy.deepcopy(battle.last_damage_taken)
    clone.damage_received_this_round = dict(battle.damage_received_this_round)
    clone.fainted_history = copy.deepcopy(battle.fainted_history)
    clone.dance_moves_used_this_round = dict(battle.dance_moves_used_this_round)
    clone.echoed_voice_rounds = list(battle.echoed_voice_rounds)
    clone.fusion_bolt_rounds = list(battle.fusion_bolt_rounds)
    clone.fusion_flare_rounds = list(battle.fusion_flare_rounds)
    clone.declared_actions = []
    clone._injuries_last_round = dict(battle._injuries_last_round)
    clone._injuries_previous_round = dict(battle._injuries_previous_round)
    clone.zone_effects = copy.deepcopy(battle.zone_effects)
    clone.room_effects = copy.deepcopy(battle.room_effects)
    clone.tailwind_teams = set(battle.tailwind_teams)
    clone.wishes = copy.deepcopy(battle.wishes)
    clone._last_action_actor_id = battle._last_action_actor_id
    clone.extension_packs = battle.extension_packs
    clone.log = []
    for mon_id, mon in clone.pokemon.items():
        setattr(mon, "_battle_id", mon_id)
        setattr(mon, "_injury_stage_loss_rng", clone.rng)
        setattr(mon, "_injury_stage_loss_enabled", getattr(clone, "injury_stage_loss_enabled", False))
        setattr(mon, "_injury_stage_loss_logger", clone.log_event)
    return clone


def _clone_trainer(trainer: TrainerState) -> TrainerState:
    clone = copy.copy(trainer)
    clone.actions_taken = dict(trainer.actions_taken)
    return clone


def _clone_pokemon(mon: PokemonState) -> PokemonState:
    clone = copy.copy(mon)
    clone.spec = copy.deepcopy(mon.spec)
    clone._source_spec = clone.spec
    clone.combat_stages = dict(mon.combat_stages)
    clone.statuses = copy.deepcopy(mon.statuses)
    clone.temporary_effects = copy.deepcopy(mon.temporary_effects)
    clone.actions_taken = dict(mon.actions_taken)
    clone.food_buffs = copy.deepcopy(mon.food_buffs)
    clone.consumed_items = copy.deepcopy(mon.consumed_items)
    clone.pending_resolution = copy.deepcopy(mon.pending_resolution)
    return clone


def _advance_rng(battle: BattleState, steps: int) -> None:
    if battle.rng is None:
        return
    for _ in range(steps):
        battle.rng.random()


def _lethal_action(
    battle: BattleState,
    actor_id: str,
    scored: Sequence[Tuple[float, object]],
    lethal_threshold: float,
) -> Optional[object]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None
    for _score, action in scored[:6]:
        if not isinstance(action, UseMoveAction):
            continue
        move = _resolve_move(actor, action.move_name)
        target = battle.pokemon.get(action.target_id) if action.target_id else None
        if move is None or target is None:
            continue
        expected = expected_damage(actor, target, move, weather=battle.weather)
        if target.hp:
            p_ko = min(1.0, expected / max(1, target.hp))
            if p_ko >= lethal_threshold:
                return action
    return None


def _is_status_action(battle: BattleState, actor_id: str, action: object) -> bool:
    if not isinstance(action, UseMoveAction):
        return False
    actor = battle.pokemon.get(actor_id)
    move = _resolve_move(actor, action.move_name) if actor else None
    if move is None:
        return False
    return (move.category or "").strip().lower() == "status"


def _status_streak_info(battle: BattleState, actor_id: str) -> Tuple[int, bool]:
    if not battle.log:
        return 0, False
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 0, False
    stored = actor.get_temporary_effects("ai_status_streak")
    if stored:
        entry = stored[-1]
        try:
            streak = int(entry.get("count", 0) or 0)
        except (TypeError, ValueError):
            streak = 0
        used_double = bool(entry.get("used_double"))
        return streak, used_double
    used_double = False
    current_streak = 0
    for event in battle.log:
        if event.get("actor") != actor_id:
            continue
        if event.get("type") != "move":
            continue
        move_name = event.get("move")
        if not move_name:
            continue
        move = _resolve_move(actor, str(move_name))
        if move is None:
            continue
        if (move.category or "").strip().lower() == "status":
            current_streak += 1
            if current_streak >= 2:
                used_double = True
        else:
            current_streak = 0
    return current_streak, used_double


def _update_status_streak(battle: BattleState, actor_id: str, action: object) -> None:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return
    is_status = _is_status_action(battle, actor_id, action)
    streak = 0
    used_double = False
    stored = actor.get_temporary_effects("ai_status_streak")
    if stored:
        entry = stored[-1]
        try:
            streak = int(entry.get("count", 0) or 0)
        except (TypeError, ValueError):
            streak = 0
        used_double = bool(entry.get("used_double"))
    if is_status:
        streak += 1
        if streak >= 2:
            used_double = True
    else:
        streak = 0
    actor.temporary_effects = [
        entry
        for entry in actor.temporary_effects
        if not (isinstance(entry, dict) and entry.get("kind") == "ai_status_streak")
    ]
    actor.add_temporary_effect(
        "ai_status_streak",
        count=streak,
        used_double=used_double,
    )


def _combo_intent_entries(actor: PokemonState, current_round: int) -> List[dict]:
    entries: List[dict] = []
    for entry in actor.get_temporary_effects("ai_combo_intent"):
        try:
            expires_round = int(entry.get("expires_round", current_round) or current_round)
        except (TypeError, ValueError):
            expires_round = current_round
        if expires_round < current_round:
            continue
        entries.append(entry)
    return entries


def _clear_combo_intents(actor: PokemonState) -> None:
    actor.temporary_effects = [
        entry
        for entry in actor.temporary_effects
        if not (isinstance(entry, dict) and entry.get("kind") == "ai_combo_intent")
    ]


def _status_move_creates_combo_intent(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    target: Optional[PokemonState],
    target_id: Optional[str],
) -> Optional[dict]:
    text = _move_effect_blob(move)
    current_round = int(getattr(battle, "round", 0) or 0)
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None
    if target is not None and _is_accuracy_pressure_move(text):
        if _has_meaningful_followup_damage(battle, actor, target, exclude_move_name=move.name):
            return {
                "intent": "accuracy_pressure_payoff",
                "target_id": str(target_id or ""),
                "setup_move": str(move.name or ""),
                "created_round": current_round,
                "expires_round": current_round + 2,
            }
    if (target_id is None or target_id == actor_id) and any(token in text for token in ("raise", "boost", "increases", "+1", "+2", "combat stage")):
        if any((candidate.category or "").strip().lower() != "status" for candidate in actor.spec.moves):
            return {
                "intent": "self_setup_payoff",
                "target_id": "",
                "setup_move": str(move.name or ""),
                "created_round": current_round,
                "expires_round": current_round + 2,
            }
    return None


def _update_combo_intent(battle: BattleState, actor_id: str, action: object) -> None:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return
    current_round = int(getattr(battle, "round", 0) or 0)
    active_entries = _combo_intent_entries(actor, current_round)
    retained: List[dict] = []
    consumed = False
    if isinstance(action, UseMoveAction):
        move = _resolve_move(actor, action.move_name)
        if move is not None:
            for entry in active_entries:
                intent = str(entry.get("intent") or "").strip().lower()
                target_id = str(entry.get("target_id") or "").strip()
                same_target = not target_id or target_id == str(action.target_id or "").strip()
                if intent == "accuracy_pressure_payoff" and same_target and (move.category or "").strip().lower() != "status":
                    consumed = True
                    continue
                if intent == "self_setup_payoff" and (move.category or "").strip().lower() != "status":
                    consumed = True
                    continue
                retained.append(entry)
            new_entry = _status_move_creates_combo_intent(
                battle,
                actor_id,
                move,
                battle.pokemon.get(action.target_id) if action.target_id else None,
                action.target_id,
            )
            if new_entry:
                retained.append(new_entry)
    else:
        retained = active_entries
    _clear_combo_intents(actor)
    for entry in retained:
        actor.add_temporary_effect("ai_combo_intent", **{k: v for k, v in entry.items() if k != "kind"})
    if consumed and not retained:
        actor.add_temporary_effect("ai_combo_intent_cooldown", round=current_round)


def _combo_intent_bonus(
    battle: BattleState,
    actor_id: str,
    action: UseMoveAction,
    move: MoveSpec,
    target: Optional[PokemonState],
) -> float:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 0.0
    entries = _combo_intent_entries(actor, int(getattr(battle, "round", 0) or 0))
    if not entries:
        return 0.0
    bonus = 0.0
    action_target_id = str(action.target_id or "").strip()
    move_name = str(move.name or "").strip().lower()
    is_status = (move.category or "").strip().lower() == "status"
    for entry in entries:
        intent = str(entry.get("intent") or "").strip().lower()
        target_id = str(entry.get("target_id") or "").strip()
        setup_move = str(entry.get("setup_move") or "").strip().lower()
        same_target = not target_id or target_id == action_target_id
        if intent == "accuracy_pressure_payoff":
            if move_name == setup_move and same_target:
                bonus -= 0.8
            elif same_target and not is_status:
                bonus += 1.45
                if target is not None:
                    accuracy_drop = abs(min(0, int(target.combat_stages.get("accuracy", 0) or 0)))
                    if accuracy_drop > 0:
                        bonus += min(0.5, 0.15 * accuracy_drop)
        elif intent == "self_setup_payoff":
            if move_name == setup_move:
                bonus -= 0.5
            elif not is_status:
                bonus += 1.1
    return bonus


def _danger_score(battle: BattleState, actor_id: str) -> float:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.hp is None:
        return 0.0
    opponents = _opponent_ids(battle, actor_id)
    worst = 0.0
    for opponent_id in opponents:
        foe = battle.pokemon.get(opponent_id)
        if foe is None:
            continue
        for move in foe.spec.moves:
            if (move.category or "").lower() == "status":
                continue
            if foe.position is None or actor.position is None:
                continue
            if not targeting.is_target_in_range(
                foe.position,
                actor.position,
                move,
                attacker_size=getattr(foe.spec, "size", ""),
                target_size=getattr(actor.spec, "size", ""),
                grid=battle.grid,
            ):
                continue
            expected = expected_damage(foe, actor, move, weather=battle.weather)
            worst = max(worst, expected)
    return min(1.0, worst / max(1, actor.hp))


def _best_defensive(scored: Sequence[Tuple[float, object]]) -> Optional[object]:
    return None


def _best_damaging_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
    *,
    include_struggle: bool = False,
) -> Optional[object]:
    moves = _damaging_candidate_actions(
        battle,
        actor_id,
        candidates,
        include_struggle=include_struggle,
    )
    if not moves:
        return None
    moves.sort(
        key=lambda action: (
            _damaging_action_priority_value(battle, actor_id, action),
            score_action(battle, actor_id, action),
        ),
        reverse=True,
    )
    return moves[0]


def _damaging_action_priority_value(
    battle: BattleState,
    actor_id: str,
    action: object,
) -> float:
    if not isinstance(action, UseMoveAction):
        return float("-inf")
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return float("-inf")
    move = _resolve_move(actor, action.move_name)
    target = battle.pokemon.get(action.target_id) if action.target_id else None
    if move is None or target is None:
        return float("-inf")
    if (move.category or "").strip().lower() == "status":
        return float("-inf")
    outcome = _simulated_action_outcome(battle, actor_id, action)
    damage = float(outcome.get("damage", 0.0) or 0.0)
    item_removed = float(outcome.get("item_removed", 0.0) or 0.0)
    status_gain = float(outcome.get("status_gain", 0.0) or 0.0)
    self_loss = float(outcome.get("self_loss", 0.0) or 0.0)
    priority = damage
    priority += 3.0 * item_removed
    priority += 0.45 * status_gain
    priority -= 0.2 * self_loss
    priority += _item_denial_attack_bonus(
        battle,
        move,
        target,
        int(getattr(battle, "round", 0) or 0),
    )
    return priority


def _expected_damage_for_action(
    battle: BattleState,
    actor_id: str,
    action: object,
) -> float:
    if not isinstance(action, UseMoveAction):
        return 0.0
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 0.0
    move = _resolve_move(actor, action.move_name)
    target = battle.pokemon.get(action.target_id) if action.target_id else None
    if move is None or target is None:
        return 0.0
    if (move.category or "").strip().lower() == "status":
        return 0.0
    outcome = _simulated_action_outcome(battle, actor_id, action)
    return float(outcome.get("damage", 0.0) or 0.0)


def _best_switch_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> Optional[SwitchAction]:
    switches = [action for action in candidates if isinstance(action, SwitchAction)]
    if not switches:
        return None
    switches.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    return switches[0]


def _best_item_denial_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> Optional[UseMoveAction]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None
    actions: List[UseMoveAction] = []
    for action in candidates:
        if not isinstance(action, UseMoveAction):
            continue
        move = _resolve_move(actor, action.move_name)
        target = battle.pokemon.get(action.target_id) if action.target_id else None
        if move is None or target is None:
            continue
        if (move.category or "").strip().lower() == "status":
            continue
        if _target_item_denial_value(target) <= 0:
            continue
        if not _is_item_denial_move(_move_effect_blob(move)):
            continue
        actions.append(action)
    if not actions:
        return None
    actions.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    return actions[0]


def _best_disengage_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> Optional[DisengageAction]:
    actions = [action for action in candidates if isinstance(action, DisengageAction)]
    if not actions:
        return None
    actions.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    return actions[0]


def _switch_score(battle: BattleState, actor_id: str, action: SwitchAction) -> float:
    actor = battle.pokemon.get(actor_id)
    replacement = battle.pokemon.get(action.replacement_id)
    if actor is None or replacement is None:
        return -1.0
    score = -0.35
    actor_ratio = (actor.hp or 0) / max(1, actor.max_hp()) if actor.hp is not None else 0.0
    replacement_ratio = (replacement.hp or 0) / max(1, replacement.max_hp()) if replacement.hp is not None else 0.0
    danger = _danger_score(battle, actor_id)
    score += max(0.0, replacement_ratio - actor_ratio) * 0.5
    score += danger * 0.9
    if _recent_switch_count(battle, actor_id, limit=2) > 0:
        score -= 1.25
    if _has_attack_in_range(battle, actor_id):
        score -= 0.9
    return score


def _disengage_score(battle: BattleState, actor_id: str, destination: Tuple[int, int]) -> float:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return 0.0
    score = _shift_score(battle, actor_id, destination) + 0.2
    if _prefers_ranged_disengage(battle, actor_id):
        score += 0.9
    current_offense = _has_attack_in_range(battle, actor_id)
    next_offense = _has_attack_in_range_from_position(battle, actor_id, destination)
    current_threat = _opponents_have_attack_on_position(battle, actor_id, actor.position)
    next_threat = _opponents_have_attack_on_position(battle, actor_id, destination)
    if current_threat and not next_threat:
        score += 1.25
    elif current_threat and next_threat:
        score -= 0.95
    elif not current_threat and next_threat:
        score -= 1.4
    if current_offense and not next_offense:
        score -= 2.25
    elif not current_offense and next_offense:
        score += 1.4
    if current_offense and next_offense and current_threat and next_threat:
        score -= 0.8
    return score


def _disengage_has_tactical_value(
    battle: BattleState,
    actor_id: str,
    destination: Tuple[int, int],
) -> bool:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return False
    current_threat = _opponents_have_attack_on_position(battle, actor_id, actor.position)
    next_threat = _opponents_have_attack_on_position(battle, actor_id, destination)
    if current_threat and not next_threat:
        return True
    current_offense = _has_attack_in_range(battle, actor_id)
    next_offense = _has_attack_in_range_from_position(battle, actor_id, destination)
    return (not current_offense) and next_offense


def _force_engage_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
    *,
    include_struggle: bool = False,
    allow_status: bool = True,
) -> Optional[object]:
    moves = _damaging_candidate_actions(
        battle,
        actor_id,
        candidates,
        include_struggle=include_struggle,
    )
    if moves:
        moves.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
        return moves[0]
    shifts = [action for action in candidates if isinstance(action, ShiftAction)]
    if shifts:
        if battle.grid is not None:
            actor = battle.pokemon.get(actor_id)
            if actor is not None and actor.position is not None:
                reachable = [action.destination for action in shifts]
                closest = _top_shift_targets(battle, actor_id, reachable)
                if closest:
                    for action in shifts:
                        if action.destination == closest[0]:
                            if score_action(battle, actor_id, action) > 0.05:
                                return action
        shifts.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
        if score_action(battle, actor_id, shifts[0]) > 0.05:
            return shifts[0]
    if allow_status:
        best_status = _best_status_action(battle, actor_id, candidates)
        if best_status is not None:
            return best_status
    best_switch = _best_switch_action(battle, actor_id, candidates)
    if best_switch is not None and score_action(battle, actor_id, best_switch) > -0.15:
        return best_switch
    return None


def _recent_no_damage(battle: BattleState, actor_id: str, limit: int = 3) -> bool:
    if not battle.log:
        return False
    recent = []
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        recent.append(event)
        if len(recent) >= limit:
            break
    if len(recent) < limit:
        return False
    return all(int(ev.get("damage") or 0) <= 0 for ev in recent)


def _recent_no_offense(battle: BattleState, actor_id: str, limit: int = 2) -> bool:
    if not battle.log:
        return False
    passive = {"shift", "disengage", "switch", "take_breather", "wait", "pass"}
    offensive = {"move", "attack_of_opportunity", "grapple", "maneuver"}
    recent = []
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        event_type = event.get("type")
        if event_type in {"turn_start", "turn_end", "phase"}:
            continue
        action_type = (event.get("action_type") or "").strip().lower()
        if event_type in offensive:
            recent.append({"type": event_type})
            if len(recent) >= limit:
                break
            continue
        if event_type in passive:
            recent.append({"type": event_type})
            if len(recent) >= limit:
                break
            continue
        if event_type == "action" and action_type in passive:
            recent.append({"type": action_type})
            if len(recent) >= limit:
                break
            continue
    if len(recent) < limit:
        return False
    return all(ev.get("type") in passive for ev in recent)


def _recent_destinations(
    battle: BattleState,
    actor_id: str,
    *,
    limit: int = 4,
) -> List[Tuple[int, int]]:
    if not battle.log:
        return []
    recent: List[Tuple[int, int]] = []
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        coord = event.get("to") or event.get("destination") or event.get("end")
        if not (isinstance(coord, (list, tuple)) and len(coord) >= 2):
            continue
        try:
            recent.append((int(coord[0]), int(coord[1])))
        except Exception:
            continue
        if len(recent) >= limit:
            break
    return recent


def _is_recent_position_loop(
    battle: BattleState,
    actor_id: str,
    destination: Tuple[int, int],
) -> bool:
    history = _recent_destinations(battle, actor_id, limit=4)
    if not history:
        return False
    if destination == history[0]:
        return True
    if len(history) >= 2 and destination == history[1]:
        return True
    if len(history) >= 3 and history[0] == history[2] and destination == history[1]:
        return True
    return False


def _recent_switch_count(battle: BattleState, actor_id: str, limit: int = 2) -> int:
    if not battle.log:
        return 0
    count = 0
    seen = 0
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        event_type = str(event.get("type") or "").strip().lower()
        action_type = str(event.get("action_type") or "").strip().lower()
        if event_type in {"turn_start", "turn_end", "phase"}:
            continue
        seen += 1
        if event_type == "switch" or (event_type == "action" and action_type == "switch"):
            count += 1
        if seen >= limit:
            break
    return count


def _recent_ineffective_move_names(battle: BattleState, actor_id: str, limit: int = 3) -> set[str]:
    if not battle.log:
        return set()
    names: set[str] = set()
    count = 0
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        if int(event.get("damage") or 0) > 0:
            continue
        move_name = str(event.get("move") or "").strip().lower()
        if move_name:
            names.add(move_name)
        count += 1
        if count >= limit:
            break
    return names


def _recent_same_move_target_no_damage_count(
    battle: BattleState,
    actor_id: str,
    move_name: str,
    target_id: Optional[str],
    *,
    limit: int = 6,
) -> int:
    if not battle.log:
        return 0
    target_text = str(target_id or "").strip()
    move_text = str(move_name or "").strip().lower()
    if not move_text:
        return 0
    count = 0
    seen = 0
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        event_move = str(event.get("move") or "").strip().lower()
        if event_move != move_text:
            continue
        event_target = str(event.get("target") or "").strip()
        if target_text and event_target and event_target != target_text:
            continue
        seen += 1
        if int(event.get("damage") or 0) <= 0:
            count += 1
        else:
            break
        if seen >= limit:
            break
    return count


def _recent_same_move_target_low_damage_count(
    battle: BattleState,
    actor_id: str,
    move_name: str,
    target_id: Optional[str],
    *,
    limit: int = 6,
) -> int:
    if not battle.log:
        return 0
    target_text = str(target_id or "").strip()
    move_text = str(move_name or "").strip().lower()
    if not move_text:
        return 0
    count = 0
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        event_move = str(event.get("move") or "").strip().lower()
        if event_move != move_text:
            continue
        event_target = str(event.get("target") or "").strip()
        if target_text and event_target and event_target != target_text:
            continue
        damage = int(event.get("damage") or 0)
        if damage <= 0:
            count += 1
        elif damage <= 8:
            count += 1
        else:
            break
        if count >= limit:
            break
    return count


def _global_stale(battle: BattleState, rounds: int = 2) -> bool:
    if battle.round <= rounds:
        return False
    for entry in battle.log:
        if entry.get("type") == "move" and int(entry.get("damage") or 0) > 0:
            if int(entry.get("round") or 0) >= battle.round - rounds:
                return False
    return True


def _has_attack_in_range(battle: BattleState, actor_id: str) -> bool:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return False
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return False
    for move in actor.spec.moves:
        if (move.category or "").lower() == "status":
            continue
        for target_id in opponents:
            target = battle.pokemon.get(target_id)
            if target is None or target.position is None:
                continue
            if not targeting.is_target_in_range(
                actor.position,
                target.position,
                move,
                attacker_size=getattr(actor.spec, "size", ""),
                target_size=getattr(target.spec, "size", ""),
                grid=battle.grid,
            ):
                continue
            if battle.grid and not battle.has_line_of_sight(actor_id, target.position, target_id):
                continue
            if _move_hits_opponent(battle, actor_id, move, target_id):
                return True
    return False


def _has_attack_in_range_from_position(
    battle: BattleState,
    actor_id: str,
    position: Tuple[int, int],
) -> bool:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return False
    original = actor.position
    actor.position = position
    try:
        return _has_attack_in_range(battle, actor_id)
    finally:
        actor.position = original


def _opponents_have_attack_on_position(
    battle: BattleState,
    actor_id: str,
    position: Tuple[int, int],
) -> bool:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return False
    original = actor.position
    actor.position = position
    try:
        for foe_id in _opponent_ids(battle, actor_id):
            foe = battle.pokemon.get(foe_id)
            if foe is None or foe.position is None:
                continue
            for move in foe.spec.moves:
                if (move.category or "").lower() == "status":
                    continue
                if not targeting.is_target_in_range(
                    foe.position,
                    position,
                    move,
                    attacker_size=getattr(foe.spec, "size", ""),
                    target_size=getattr(actor.spec, "size", ""),
                    grid=battle.grid,
                ):
                    continue
                if battle.grid and not battle.has_line_of_sight(foe_id, position, actor_id):
                    continue
                if _move_hits_opponent(battle, foe_id, move, actor_id):
                    return True
        return False
    finally:
        actor.position = original


def _should_close_distance(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> bool:
    if not _opponent_ids(battle, actor_id):
        return False
    if _damaging_candidate_actions(battle, actor_id, candidates, include_struggle=False):
        return False
    return any(isinstance(action, ShiftAction) for action in candidates)


def _should_use_setup_before_engage(
    battle: BattleState,
    actor_id: str,
    action: object,
) -> bool:
    if not _is_self_or_setup_status_action(battle, actor_id, action):
        return False
    if _has_used_setup_move_before_engage(battle, actor_id):
        return False
    status_streak, _used_double = _status_streak_info(battle, actor_id)
    if status_streak >= 1:
        return False
    return not _has_attack_in_range(battle, actor_id)


def _has_used_setup_move_before_engage(battle: BattleState, actor_id: str) -> bool:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return False
    for event in battle.log:
        if event.get("actor") != actor_id or event.get("type") != "move":
            continue
        move_name = str(event.get("move") or "").strip()
        if not move_name:
            continue
        move = _resolve_move(actor, move_name)
        if move is None:
            continue
        simulated = UseMoveAction(
            actor_id=actor_id,
            move_name=move.name,
            target_id=event.get("target"),
        )
        if _is_self_or_setup_status_action(battle, actor_id, simulated):
            return True
    return False


def _struggle_action(battle: BattleState, actor_id: str) -> Optional[UseMoveAction]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return None
    actor_pos = actor.position
    if actor_pos is None:
        return None
    target_id = None
    best_distance = 999
    for pid in opponents:
        foe = battle.pokemon.get(pid)
        if foe is None or foe.position is None:
            continue
        dist = targeting.footprint_distance(
            actor_pos,
            getattr(actor.spec, "size", ""),
            foe.position,
            getattr(foe.spec, "size", ""),
            battle.grid,
        )
        if dist < best_distance:
            best_distance = dist
            target_id = pid
    if target_id is None:
        return None
    action = UseMoveAction(actor_id=actor_id, move_name="Struggle", target_id=target_id)
    if _action_is_legal(battle, action, actor_id):
        return action
    return None


def _last_move_name(actor: PokemonState) -> Optional[str]:
    last_moves = actor.get_temporary_effects("last_move")
    if not last_moves:
        return None
    last = last_moves[-1]
    name = last.get("name") if isinstance(last, dict) else None
    return str(name) if name else None


def _damaging_candidate_actions(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
    *,
    include_struggle: bool = False,
) -> List[UseMoveAction]:
    moves: List[UseMoveAction] = []
    actor = battle.pokemon.get(actor_id)
    for action in candidates:
        if not isinstance(action, UseMoveAction):
            continue
        move = _resolve_move(actor, action.move_name) if actor else None
        if move is None:
            continue
        if (move.category or "").lower() == "status":
            continue
        if not include_struggle and _is_struggle_name(move.name or action.move_name):
            continue
        if not _move_hits_opponent(battle, actor_id, move, action.target_id):
            continue
        target = battle.pokemon.get(action.target_id) if action.target_id else None
        if target is None:
            continue
        expected = expected_damage(actor, target, move, weather=battle.weather) if actor else 0
        if expected <= 0:
            continue
        moves.append(action)
    return moves


def _is_struggle_name(move_name: str) -> bool:
    return (move_name or "").strip().lower() == "struggle"


def _best_status_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> Optional[object]:
    moves: List[UseMoveAction] = []
    actor = battle.pokemon.get(actor_id)
    for action in candidates:
        if not isinstance(action, UseMoveAction):
            continue
        move = _resolve_move(actor, action.move_name) if actor else None
        if move is None:
            continue
        if _is_maneuver_move(move):
            continue
        if (move.category or "").lower() != "status":
            continue
        moves.append(action)
    if not moves:
        return None
    moves.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    return moves[0]


def _is_self_or_setup_status_action(
    battle: BattleState,
    actor_id: str,
    action: object,
) -> bool:
    if not isinstance(action, UseMoveAction):
        return False
    actor = battle.pokemon.get(actor_id)
    move = _resolve_move(actor, action.move_name) if actor else None
    if move is None:
        return False
    if (move.category or "").strip().lower() != "status":
        return False
    text = _move_effect_blob(move)
    self_debuff_tokens = (
        "lower",
        "reduce",
        "decrease",
        "drops",
        "-1",
        "-2",
        "vulnerable",
        "tripped",
        "burn",
        "poison",
        "sleep",
        "paraly",
        "flinch",
        "confus",
    )
    target_kind = targeting.normalized_target_kind(move)
    if (target_kind == "self" or action.target_id is None or action.target_id == actor_id) and any(
        token in text for token in self_debuff_tokens
    ):
        return False
    if target_kind == "self":
        return True
    if action.target_id is None or action.target_id == actor_id:
        return True
    setup_tokens = (
        "raise",
        "boost",
        "increases",
        "+1",
        "+2",
        "combat stage",
        "screen",
        "reflect",
        "light screen",
        "safeguard",
        "terrain",
        "weather",
    )
    return any(token in text for token in setup_tokens)


def _best_maneuver_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> Optional[UseMoveAction]:
    moves: List[UseMoveAction] = []
    actor = battle.pokemon.get(actor_id)
    for action in candidates:
        if not isinstance(action, UseMoveAction):
            continue
        move = _resolve_move(actor, action.move_name) if actor else None
        if move is None or not _is_maneuver_move(move):
            continue
        moves.append(action)
    if not moves:
        return None
    moves.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    return moves[0]


def _is_maneuver_move(move: MoveSpec) -> bool:
    return (move.name or "").strip().lower() in _load_maneuver_moves()


def _score_maneuver_action(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    target: Optional[PokemonState],
) -> float:
    actor = battle.pokemon.get(actor_id)
    if actor is None or target is None:
        return -999.0
    name = (move.name or "").strip().lower()
    attacker_rank = max(actor.skill_rank("combat"), actor.skill_rank("athletics"))
    defender_rank = max(target.skill_rank("combat"), target.skill_rank("athletics"))
    if name == "disarm":
        if not target.spec.items:
            return -1.0
        defender_rank = max(target.skill_rank("combat"), target.skill_rank("stealth"))
        attacker_rank = max(actor.skill_rank("combat"), actor.skill_rank("stealth"))
        base = 6.0
    elif name == "trip":
        defender_rank = max(target.skill_rank("combat"), target.skill_rank("acrobatics"))
        attacker_rank = max(actor.skill_rank("combat"), actor.skill_rank("acrobatics"))
        base = 5.0 if not target.has_status("Tripped") else 0.5
    elif name == "push":
        base = 3.0
    elif name == "hinder":
        attacker_rank = actor.skill_rank("athletics")
        defender_rank = target.skill_rank("athletics")
        base = 4.0 if not target.has_status("Hindered") else 0.5
    elif name == "blind":
        attacker_rank = actor.skill_rank("stealth")
        defender_rank = target.skill_rank("stealth")
        base = 4.0 if not target.has_status("Blinded") else 0.5
    elif name == "low blow":
        attacker_rank = actor.skill_rank("acrobatics")
        defender_rank = target.skill_rank("acrobatics")
        base = 5.0 if not target.has_status("Vulnerable") else 0.5
    elif name == "dirty trick":
        base = 4.0
        if target.has_status("Hindered") and target.has_status("Blinded") and target.has_status("Vulnerable"):
            base = 0.5
    elif name == "grapple":
        base = 4.5
        if _recent_combo_setup_used(battle, actor_id, ("wrap", "bind", "trap", "clamp", "infestation")):
            base += 1.8
        if target.has_status("Grappled") or target.has_status("Trapped"):
            base += 0.6
    else:
        base = 2.0
    diff = attacker_rank - defender_rank
    win_prob = max(0.1, min(0.9, 0.5 + diff / 20.0))
    return win_prob * base


def _move_effect_blob(move: MoveSpec) -> str:
    parts = [
        str(move.name or ""),
        str(move.effects_text or ""),
        str(move.range_text or ""),
    ]
    return " ".join(parts).strip().lower()


def _combo_description_bonus(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    target: Optional[PokemonState],
) -> float:
    text = _move_effect_blob(move)
    name = (move.name or "").strip().lower()
    if not text:
        return 0.0
    bonus = 0.0
    target_is_bound = bool(target and (target.has_status("Grappled") or target.has_status("Trapped")))
    wrap_like = any(token in text for token in ("wrap", "bind", "trap", "clamp", "infestation"))
    grapple_like = "grapple" in text or "dominance" in text
    if wrap_like:
        if target is not None and not target_is_bound:
            bonus += 0.85
        if target_is_bound:
            bonus -= 0.75
        if grapple_like:
            bonus += 0.35
    if name == "grapple" or "grapple" in name:
        if _recent_combo_setup_used(battle, actor_id, ("wrap", "bind", "trap", "clamp", "infestation")):
            bonus += 1.4
        if target_is_bound:
            bonus += 0.35
    if target is not None and _is_item_denial_move(text):
        denial_value = _target_item_denial_value(target)
        if denial_value > 0:
            bonus += denial_value
        else:
            bonus -= 0.5
    if target is not None and (move.category or "").strip().lower() != "status":
        accuracy_drop = abs(min(0, int(target.combat_stages.get("accuracy", 0) or 0)))
        if accuracy_drop > 0:
            bonus += min(0.85, 0.2 * accuracy_drop)
    bonus += _conditional_target_combo_bonus(battle, actor_id, text, target)
    return bonus


def _conditional_target_combo_bonus(
    battle: BattleState,
    actor_id: str,
    text: str,
    target: Optional[PokemonState],
) -> float:
    if target is None or not text:
        return 0.0
    bonus = 0.0
    status_phrases = {
        "poisoned": ("poisoned", "badly poisoned", "poison"),
        "burned": ("burned", "burn"),
        "paralyzed": ("paralyzed", "paralyze"),
        "frozen": ("frozen", "freeze"),
        "sleeping": ("sleep", "asleep", "drowsy", "bad sleep"),
        "asleep": ("sleep", "asleep", "drowsy", "bad sleep"),
        "confused": ("confused", "confusion"),
        "tripped": ("tripped",),
        "vulnerable": ("vulnerable",),
        "hindered": ("hindered",),
        "blinded": ("blinded",),
        "grappled": ("grappled", "trapped"),
        "trapped": ("trapped", "grappled"),
    }
    phrase_weights = {
        "poisoned": 1.4,
        "burned": 1.1,
        "paralyzed": 1.1,
        "frozen": 1.6,
        "sleeping": 1.8,
        "asleep": 1.8,
        "confused": 1.0,
        "tripped": 1.0,
        "vulnerable": 1.0,
        "hindered": 0.9,
        "blinded": 0.9,
        "grappled": 1.2,
        "trapped": 1.2,
    }
    for phrase, statuses in status_phrases.items():
        if not any(
            token in text
            for token in (
                f"{phrase} target",
                f"{phrase} targets",
                f"target is {phrase}",
                f"targets that are {phrase}",
                f"against {phrase}",
            )
        ):
            continue
        if any(target.has_status(status) for status in statuses):
            bonus += phrase_weights.get(phrase, 1.0)
        else:
            bonus -= 0.35
    if "screen" in text or "reflect" in text or "light screen" in text:
        if any(
            str(entry.get("name") or "").strip().lower() in {"reflect", "light screen"}
            for entry in getattr(target, "statuses", [])
        ):
            bonus += 1.0
    return bonus


def _type_choice_options_for_move(
    battle: BattleState,
    actor_id: str,
    actor: PokemonState,
    move: MoveSpec,
) -> List[str]:
    name = (move.name or "").strip().lower()
    if name == "conversion" and hasattr(battle, "_conversion_type_options"):
        return list(battle._conversion_type_options(actor))
    if name == "conversion2" and hasattr(battle, "_conversion2_type_options"):
        return list(battle._conversion2_type_options(actor_id))
    return []


def _type_choice_bonus(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    chosen_type: str,
) -> float:
    name = (move.name or "").strip().lower()
    selected = str(chosen_type or "").strip().title()
    if not selected:
        return 0.0
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 0.0
    current_types = [str(value or "").strip().title() for value in (actor.spec.types or []) if str(value or "").strip()]
    bonus = 0.0
    if selected not in current_types:
        bonus += 0.25
    if name == "conversion2":
        legal = set(_type_choice_options_for_move(battle, actor_id, actor, move))
        if selected in legal:
            bonus += 1.6
        if hasattr(battle, "_last_damage_taken_info"):
            entry = battle._last_damage_taken_info(actor_id)
            attack_type = str(entry.get("move_type") or "").strip().title()
            if attack_type:
                selected_mult = ptu_engine.type_multiplier(attack_type, [selected])
                current_mult = 1.0
                if current_types:
                    current_mult = min(
                        ptu_engine.type_multiplier(attack_type, [current_type])
                        for current_type in current_types
                    )
                if selected_mult < current_mult:
                    damage = float(entry.get("damage") or 0.0)
                    hp_ratio = damage / max(1, actor.max_hp())
                    bonus += 2.4 + min(2.0, hp_ratio * 3.0)
        return bonus
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return bonus
    best_offense = 0.0
    for move_spec in actor.spec.moves:
        move_type = str(move_spec.type or "").strip().title()
        if not move_type or move_type != selected:
            continue
        for target_id in opponents:
            target = battle.pokemon.get(target_id)
            if target is None:
                continue
            best_offense = max(best_offense, expected_damage(actor, target, move_spec, weather=battle.weather))
    if best_offense > 0:
        bonus += min(1.4, best_offense / 12.0)
    defensive_score = 0.0
    for target_id in opponents:
        target = battle.pokemon.get(target_id)
        if target is None:
            continue
        for move_spec in target.spec.moves:
            move_type = str(move_spec.type or "").strip().title()
            if not move_type:
                continue
            defensive_score += max(0.0, 1.0 - ptu_engine.type_multiplier(move_type, [selected]))
    if defensive_score > 0:
        bonus += min(0.9, defensive_score / max(1, len(opponents) * 4))
    return bonus


def _should_force_combo_maneuver(
    battle: BattleState,
    actor_id: str,
    action: UseMoveAction,
) -> bool:
    actor = battle.pokemon.get(actor_id)
    move = _resolve_move(actor, action.move_name) if actor else None
    if move is None:
        return False
    if (move.name or "").strip().lower() != "grapple":
        return False
    if not _recent_combo_setup_used(battle, actor_id, ("wrap", "bind", "trap", "clamp", "infestation")):
        return False
    target = battle.pokemon.get(action.target_id) if action.target_id else None
    if target is None or target.has_status("Grappled"):
        return False
    return score_action(battle, actor_id, action) >= 2.0


def _forced_combo_maneuver_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> Optional[UseMoveAction]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None
    grapple_actions: List[UseMoveAction] = []
    for action in candidates:
        if not isinstance(action, UseMoveAction):
            continue
        move = _resolve_move(actor, action.move_name)
        if move is None or (move.name or "").strip().lower() != "grapple":
            continue
        grapple_actions.append(action)
    if not grapple_actions:
        return None
    grapple_actions.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    for action in grapple_actions:
        if _should_force_combo_maneuver(battle, actor_id, action):
            return action
    return None


def _should_prioritize_type_conversion(
    battle: BattleState,
    actor_id: str,
    status_action: object,
    damage_action: object,
    *,
    status_score: float,
    damage_score: float,
) -> bool:
    if not isinstance(status_action, UseMoveAction):
        return False
    move_name = str(status_action.move_name or "").strip().lower()
    if move_name not in {"conversion", "conversion2"}:
        return False
    if move_name == "conversion2":
        if not hasattr(battle, "_last_damage_taken_info"):
            return False
        entry = battle._last_damage_taken_info(actor_id)
        damage = float(entry.get("damage") or 0.0)
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return False
        damage_ratio = damage / max(1, actor.max_hp())
        return (damage >= 8 or damage_ratio >= 0.1) and status_score + 1.5 >= damage_score
    current_round = getattr(battle, "round", 0) or 0
    return current_round <= 3 and status_score + 1.0 >= damage_score


def _conversion_move_already_used(
    battle: BattleState,
    actor_id: str,
    move_name: str,
) -> bool:
    needle = str(move_name or "").strip().lower()
    if not needle or not battle.log:
        return False
    for event in reversed(battle.log):
        if not isinstance(event, dict):
            continue
        actor = str(event.get("actor") or event.get("actor_id") or event.get("source") or "").strip()
        move = str(event.get("move") or event.get("move_name") or "").strip().lower()
        if actor == actor_id and move == needle:
            return True
    return False


def _force_one_time_conversion_action(
    battle: BattleState,
    actor_id: str,
    candidates: Sequence[object],
) -> Optional[UseMoveAction]:
    conversion_actions: List[UseMoveAction] = []
    for action in candidates:
        if not isinstance(action, UseMoveAction):
            continue
        move_name = str(action.move_name or "").strip().lower()
        if move_name not in {"conversion", "conversion2"}:
            continue
        if _conversion_move_already_used(battle, actor_id, move_name):
            continue
        conversion_actions.append(action)
    if not conversion_actions:
        return None
    conversion_actions.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    return conversion_actions[0]


def _recent_combo_setup_used(
    battle: BattleState,
    actor_id: str,
    keywords: Sequence[str],
    *,
    limit: int = 2,
) -> bool:
    if not battle.log:
        return False
    needle = tuple(str(keyword).strip().lower() for keyword in keywords if str(keyword).strip())
    if not needle:
        return False
    seen = 0
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        move_name = str(event.get("move") or "").strip().lower()
        if any(token in move_name for token in needle):
            return True
        seen += 1
        if seen >= limit:
            break
    return False


def _status_move_setup_score(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    target_id: Optional[str],
    current_round: int,
) -> float:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 0.0
    text = _move_effect_blob(move)
    actor_ratio = (actor.hp or 0) / max(1, actor.max_hp()) if actor.hp is not None else 1.0
    target = battle.pokemon.get(target_id) if target_id else None
    actor_team = _team_for(battle, actor_id)
    targets_enemy = target is not None and _team_for(battle, target_id or "") != actor_team
    targets_self = target is None or target_id == actor_id
    stage_total = sum(int(v or 0) for v in actor.combat_stages.values())
    bonus = 0.0

    healing_tokens = (
        "heal",
        "recover",
        "rest",
        "roost",
        "wish",
        "moonlight",
        "morning sun",
        "synthesis",
        "milk drink",
        "slack off",
        "life dew",
    )
    if any(token in text for token in healing_tokens):
        if actor_ratio <= 0.65:
            bonus += 1.1
        elif actor_ratio <= 0.85:
            bonus += 0.45
        else:
            bonus -= 0.4

    setup_tokens = ("raise", "boost", "increases", "+1", "+2", "combat stage")
    if any(token in text for token in setup_tokens) and targets_self:
        if stage_total <= 1:
            bonus += 0.8
        elif stage_total <= 3:
            bonus += 0.35
        else:
            bonus -= 0.2
        recent_same_setup = _recent_same_move_use_count(battle, actor_id, move.name, limit=4)
        if recent_same_setup >= 1:
            bonus -= 1.1 * recent_same_setup
        if "withdraw" in text or "withdrawn" in text:
            if actor.has_status("Withdrawn"):
                bonus -= 4.5
            defense_stage = int(actor.combat_stages.get("def", 0) or 0)
            if defense_stage >= 2:
                bonus -= 1.25 + 0.45 * max(0, defense_stage - 2)
        if any(token in text for token in ("reflect", "light screen", "safeguard")):
            recent_same_setup = max(recent_same_setup, 1 if _recent_same_move_use_count(battle, actor_id, move.name, limit=3) > 0 else 0)

    debuff_tokens = (
        "lower",
        "reduce",
        "decrease",
        "drops",
        "vulnerable",
        "tripped",
        "burn",
        "poison",
        "sleep",
        "paraly",
        "flinch",
        "confus",
    )
    if any(token in text for token in debuff_tokens) and targets_self:
        bonus -= 1.5
    if any(token in text for token in debuff_tokens) and targets_enemy:
        bonus += 0.7
        bonus += _enemy_advantage_setup_bonus(battle, actor_id, actor, move, target)

    field_tokens = ("weather", "rain", "sun", "sand", "hail", "terrain", "screen")
    if any(token in text for token in field_tokens):
        bonus += 0.45 if current_round <= 4 else 0.15

    guard_tokens = ("protect", "detect", "king's shield", "spiky shield", "baneful bunker")
    if any(token in text for token in guard_tokens):
        bonus += 0.45 if actor_ratio <= 0.45 else 0.18

    if current_round <= 3 and (targets_self or targets_enemy):
        bonus += 0.2

    return bonus


def _recent_same_move_use_count(
    battle: BattleState,
    actor_id: str,
    move_name: str,
    *,
    limit: int = 4,
) -> int:
    if not battle.log:
        return 0
    needle = str(move_name or "").strip().lower()
    if not needle:
        return 0
    count = 0
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        event_move = str(event.get("move") or "").strip().lower()
        if event_move != needle:
            break
        count += 1
        if count >= limit:
            break
    return count


def _enemy_advantage_setup_bonus(
    battle: BattleState,
    actor_id: str,
    actor: PokemonState,
    move: MoveSpec,
    target: Optional[PokemonState],
) -> float:
    if target is None:
        return 0.0
    text = _move_effect_blob(move)
    bonus = 0.0
    if _is_accuracy_pressure_move(text):
        target_accuracy = int(target.combat_stages.get("accuracy", 0) or 0)
        if target_accuracy >= 0:
            bonus += 4.25
            if _danger_score(battle, actor_id) >= 0.35:
                bonus += 2.2
            if _has_meaningful_followup_damage(battle, actor, target, exclude_move_name=move.name):
                bonus += 1.5
        else:
            bonus -= 0.25
    if _is_item_denial_move(text):
        denial_value = _target_item_denial_value(target)
        if denial_value > 0:
            bonus += denial_value
        else:
            bonus -= 0.35
    return bonus


def _is_accuracy_pressure_move(text: str) -> bool:
    if not text:
        return False
    if "accuracy" in text and any(token in text for token in ("lower", "reduce", "decrease", "drops", "-1", "-2")):
        return True
    return any(token in text for token in ("sand attack", "mud-slap", "mud slap", "kinesis", "flash", "smokescreen", "night daze", "mud bomb", "muddy water", "omen"))


def _is_item_denial_move(text: str) -> bool:
    if not text:
        return False
    if "knock off" in text:
        return True
    return "item" in text and any(token in text for token in ("remove", "drop", "lose", "steal", "knock off"))


def _item_name(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or item.get("id") or "").strip()
    return str(item or "").strip()


def _target_item_denial_value(target: Optional[PokemonState]) -> float:
    if target is None:
        return 0.0
    items = list(getattr(target.spec, "items", []) or [])
    if not items:
        return 0.0
    bonus = 3.85
    for item in items:
        name = _item_name(item).lower()
        if not name:
            continue
        if any(token in name for token in ("berry", "leftovers", "orb", "band", "specs", "scarf", "sash", "eviolite", "helmet", "leek", "stick")):
            bonus += 0.45
            break
    return min(4.6, bonus)


def _item_denial_attack_bonus(
    battle: BattleState,
    move: MoveSpec,
    target: Optional[PokemonState],
    current_round: int,
) -> float:
    if target is None:
        return 0.0
    text = _move_effect_blob(move)
    if not _is_item_denial_move(text):
        return 0.0
    denial_value = _target_item_denial_value(target)
    if denial_value <= 0:
        return -0.45
    bonus = 1.65 + denial_value * 1.15
    move_name = str(move.name or "").strip().lower()
    if move_name == "knock off":
        bonus += 0.85
    if current_round <= 6:
        bonus += 0.8
    if len(list(getattr(target.spec, "items", []) or [])) >= 2:
        bonus += 0.45
    return bonus


def _has_meaningful_followup_damage(
    battle: BattleState,
    actor: PokemonState,
    target: PokemonState,
    *,
    exclude_move_name: Optional[str] = None,
) -> bool:
    skip_name = str(exclude_move_name or "").strip().lower()
    for candidate in actor.spec.moves:
        move_name = str(candidate.name or "").strip().lower()
        if not move_name or move_name == skip_name:
            continue
        if (candidate.category or "").strip().lower() == "status":
            continue
        if expected_damage(actor, target, candidate, weather=battle.weather) > _MEANINGFUL_DAMAGE_THRESHOLD:
            return True
    return False


def _action_is_legal(battle: BattleState, action: object, actor_id: str) -> bool:
    battle.current_actor_id = actor_id
    try:
        action.validate(battle)
        return True
    except Exception:
        return False


def _is_reaction_only_move(move: MoveSpec) -> bool:
    canonical_text = ""
    move_key = (move.name or "").strip().lower()
    for known in _load_move_specs():
        if (known.name or "").strip().lower() != move_key:
            continue
        canonical_text = " ".join([str(known.range_text or ""), str(known.effects_text or "")])
        break
    text = " ".join([str(move.range_text or ""), str(move.effects_text or ""), canonical_text]).strip().lower()
    activation = str(frequency.activation_for_move(move.name) or "").strip().lower()
    return bool(activation in {"interrupt", "reaction"} or "trigger:" in text or "reaction" in text)


def _action_kind(action: object) -> str:
    if isinstance(action, UseMoveAction):
        return "attack"
    if isinstance(action, ShiftAction):
        return "defend"
    if isinstance(action, DisengageAction):
        return "defend"
    if isinstance(action, SwitchAction):
        return "defend"
    if isinstance(action, TakeBreatherAction):
        return "defend"
    if isinstance(action, GrappleAction):
        return "attack"
    return "other"


def _action_move_name(action: object) -> str:
    if isinstance(action, UseMoveAction):
        return action.move_name
    if isinstance(action, GrappleAction):
        return f"grapple:{action.action_kind}"
    return ""


def _action_label(action: object) -> str:
    if isinstance(action, UseMoveAction):
        return f"Move {action.move_name}"
    if isinstance(action, ShiftAction):
        return f"Shift {action.destination}"
    if isinstance(action, DisengageAction):
        return f"Disengage {action.destination}"
    if isinstance(action, SwitchAction):
        return f"Switch {action.replacement_id}"
    if isinstance(action, GrappleAction):
        return f"Grapple {action.action_kind}"
    if isinstance(action, TakeBreatherAction):
        return "Take Breather"
    return "Action"


def _target_preference(battle: BattleState, actor_id: str, action: object) -> str:
    if not isinstance(action, UseMoveAction):
        return ""
    target_id = action.target_id
    if not target_id:
        return ""
    target = battle.pokemon.get(target_id)
    if target is None or target.hp is None:
        return ""
    lowest = None
    for pid, mon in battle.pokemon.items():
        if mon.hp is None or mon.hp <= 0:
            continue
        if _team_for(battle, pid) == _team_for(battle, actor_id):
            continue
        ratio = mon.hp / max(1, mon.max_hp())
        if lowest is None or ratio < lowest:
            lowest = ratio
    if lowest is not None:
        target_ratio = target.hp / max(1, target.max_hp())
        if abs(target_ratio - lowest) <= 1e-6:
            return "lowest_hp"
    return "nearest"


def _risk_preference(battle: BattleState, actor_id: str, action: object) -> str:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.hp is None:
        return ""
    danger = _danger_score(battle, actor_id)
    if danger >= 0.5 and _action_kind(action) == "attack":
        return "stays_in_danger"
    if danger >= 0.5 and _action_kind(action) == "defend":
        return "retreats"
    return ""


def _apply_profile_bias(score: float, action: object, profile: OpponentProfile, cap: float) -> float:
    kind = _action_kind(action)
    bias = 0.0
    if profile.action_type:
        total = sum(profile.action_type.values()) or 1.0
        bias += (profile.action_type.get(kind, 0.0) / total) - 0.25
    move = _action_move_name(action)
    if move and profile.move_usage:
        total = sum(profile.move_usage.values()) or 1.0
        bias += (profile.move_usage.get(move, 0.0) / total) - 0.1
    bias = max(-cap, min(cap, bias))
    return score * (1.0 + bias)


def _apply_aai_port_adjustments(
    battle: BattleState,
    actor_id: str,
    scored: Sequence[Tuple[float, object]],
    store: ProfileStore,
    *,
    ai_level: str,
) -> List[Tuple[float, object]]:
    if not scored:
        return []
    tier = aai_port.tier_for_level(ai_level)
    if not (tier.hazard_awareness or tier.setup_detection or tier.learn_patterns):
        return list(scored)
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return list(scored)
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return list(scored)

    adjusted: List[Tuple[float, object]] = []
    for base_score, action in scored:
        move_text = ""
        move_keywords = ""
        is_status = False
        defend_prob = 0.0
        retreat_prob = 0.0
        if isinstance(action, UseMoveAction):
            move = _resolve_move(actor, action.move_name)
            if move is not None:
                is_status = (move.category or "").strip().lower() == "status"
                move_text = move.effects_text or ""
                move_keywords = " ".join(str(keyword) for keyword in (move.keywords or []))
            profile = _target_profile_for_action(battle, actor_id, action, store)
            if profile is not None:
                defend_prob = aai_port.protect_tendency(profile.action_type)
                retreat_prob = aai_port.retreat_tendency(profile.risk_tolerance)
            delta = aai_port.adaptive_delta(
                is_status=is_status,
                move_text=move_text,
                move_keywords=move_keywords,
                defend_prob=defend_prob,
                retreat_prob=retreat_prob,
                tier=tier,
            )
            adjusted.append((base_score + delta, action))
            continue
        adjusted.append((base_score, action))
    return adjusted


def _target_profile_for_action(
    battle: BattleState,
    actor_id: str,
    action: UseMoveAction,
    store: ProfileStore,
) -> Optional[OpponentProfile]:
    target_id = action.target_id
    if target_id and target_id in battle.pokemon:
        signature = _actor_signature(battle, target_id)
        return store.profile_for(signature)
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return None
    signature = _actor_signature(battle, opponents[0])
    return store.profile_for(signature)


def _shift_score(battle: BattleState, actor_id: str, destination: Tuple[int, int]) -> float:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return 0.0
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return 0.2
    danger = _danger_score(battle, actor_id)
    current_distances = []
    distances = []
    for pid in opponents:
        foe = battle.pokemon.get(pid)
        if foe is None or foe.position is None:
            continue
        current_distances.append(
            targeting.footprint_distance(
                actor.position,
                getattr(actor.spec, "size", ""),
                foe.position,
                getattr(foe.spec, "size", ""),
                battle.grid,
            )
        )
        distances.append(
            targeting.footprint_distance(
                destination,
                getattr(actor.spec, "size", ""),
                foe.position,
                getattr(foe.spec, "size", ""),
                battle.grid,
            )
        )
    if not distances:
        return 0.2
    min_current = min(current_distances) if current_distances else min(distances)
    min_next = min(distances)
    progress = float(min_current - min_next)
    if danger >= 0.4:
        return 0.14 * max(distances)
    score = 0.05 * (1.0 / max(1, min_next)) + 0.02
    if progress > 0:
        score += 0.34 * progress
    elif progress < 0:
        score -= 0.42 * abs(progress)
    if _recent_no_offense(battle, actor_id, limit=2) and progress <= 0:
        score -= 1.4
    if _is_recent_position_loop(battle, actor_id, destination):
        score -= 2.6
    return score


def _top_shift_targets(
    battle: BattleState,
    actor_id: str,
    reachable: Sequence[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return list(reachable)[:3]
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return list(reachable)[:3]
    foe = battle.pokemon.get(opponents[0])
    if foe is None or foe.position is None:
        return list(reachable)[:3]
    ordered = sorted(
        reachable,
        key=lambda coord: (
            _is_recent_position_loop(battle, actor_id, coord),
            targeting.footprint_distance(
                coord,
                getattr(actor.spec, "size", ""),
                foe.position,
                getattr(foe.spec, "size", ""),
                battle.grid,
            ),
        ),
    )
    return ordered[:3]


def _top_defensive_shifts(
    battle: BattleState,
    actor_id: str,
    reachable: Sequence[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return []
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return []
    foe = battle.pokemon.get(opponents[0])
    if foe is None or foe.position is None:
        return []
    ordered = sorted(
        reachable,
        key=lambda coord: targeting.footprint_distance(
            coord,
            getattr(actor.spec, "size", ""),
            foe.position,
            getattr(foe.spec, "size", ""),
            battle.grid,
        ),
        reverse=True,
    )
    return ordered[:2]


def _top_disengage_targets(
    battle: BattleState,
    actor_id: str,
    reachable: Sequence[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return []
    options = [coord for coord in reachable if battle._combatant_distance_to_coord(actor, coord) == 1]
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return options[:1]
    foe_positions = [
        battle.pokemon[pid].position
        for pid in opponents
        if battle.pokemon.get(pid) is not None and battle.pokemon[pid].position is not None
    ]
    if not foe_positions:
        return options[:1]
    ordered = sorted(
        options,
        key=lambda coord: (
            min(
                targeting.footprint_distance(
                    coord,
                    getattr(actor.spec, "size", ""),
                    pos,
                    getattr(battle.pokemon[pid].spec, "size", ""),
                    battle.grid,
                )
                for pid, pos in (
                    (pid, battle.pokemon[pid].position)
                    for pid in opponents
                    if battle.pokemon.get(pid) is not None and battle.pokemon[pid].position is not None
                )
            ),
            sum(
                targeting.footprint_distance(
                    coord,
                    getattr(actor.spec, "size", ""),
                    pos,
                    getattr(battle.pokemon[pid].spec, "size", ""),
                    battle.grid,
                )
                for pid, pos in (
                    (pid, battle.pokemon[pid].position)
                    for pid in opponents
                    if battle.pokemon.get(pid) is not None and battle.pokemon[pid].position is not None
                )
            ),
        ),
        reverse=True,
    )
    return ordered[:2]


def _prefers_ranged_disengage(battle: BattleState, actor_id: str) -> bool:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return False
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return False
    adjacent_threat = False
    for pid in opponents:
        foe = battle.pokemon.get(pid)
        if foe is None or foe.position is None:
            continue
        if targeting.footprint_distance(
            actor.position,
            getattr(actor.spec, "size", ""),
            foe.position,
            getattr(foe.spec, "size", ""),
            battle.grid,
        ) <= 1:
            adjacent_threat = True
            break
    if not adjacent_threat:
        return False
    for move in actor.spec.moves:
        if (move.category or "").strip().lower() == "status":
            continue
        if targeting.normalized_target_kind(move) == "melee":
            continue
        if targeting.move_range_distance(move) <= 1:
            continue
        return True
    return False


def _resolve_move(actor: Optional[PokemonState], move_name: str) -> Optional[MoveSpec]:
    if actor is None:
        return None
    for move in actor.spec.moves:
        if move.name == move_name:
            return move
    maneuver = _load_maneuver_moves().get((move_name or "").strip().lower())
    if maneuver is not None:
        return maneuver
    return None


def _move_hits_opponent(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    target_id: Optional[str],
) -> bool:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return False
    actor_team = _team_for(battle, actor_id)
    target = battle.pokemon.get(target_id) if target_id else None
    target_pos = target.position if target and target.position is not None else actor.position
    tiles = targeting.affected_tiles(battle.grid, actor.position, target_pos, move)
    if not tiles:
        return False
    for pid, mon in battle.pokemon.items():
        if not mon.active or mon.fainted or mon.hp is None or mon.hp <= 0 or mon.position is None:
            continue
        if mon.position not in tiles:
            continue
        if _team_for(battle, pid) != actor_team:
            return True
    return False


def _team_for(battle: BattleState, actor_id: str) -> str:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return ""
    trainer = battle.trainers.get(actor.controller_id)
    return (trainer.team or trainer.identifier) if trainer else actor.controller_id


def _opponent_ids(battle: BattleState, actor_id: str) -> List[str]:
    actor_team = _team_for(battle, actor_id)
    return [
        pid
        for pid, mon in battle.pokemon.items()
        if mon.active
        and not mon.fainted
        and _team_for(battle, pid) != actor_team
        and mon.position is not None
    ]


def _ally_ids(battle: BattleState, actor_id: str) -> List[str]:
    actor_team = _team_for(battle, actor_id)
    return [
        pid
        for pid, mon in battle.pokemon.items()
        if mon.active
        and not mon.fainted
        and _team_for(battle, pid) == actor_team
        and pid != actor_id
    ]


def _bench_candidates(battle: BattleState, actor_id: str) -> List[str]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return []
    return [
        pid
        for pid, mon in battle.pokemon.items()
        if mon.controller_id == actor.controller_id
        and not mon.active
        and mon.hp is not None
        and mon.hp > 0
    ]


def _actor_signature(battle: BattleState, actor_id: str) -> str:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return actor_id
    trainer: Optional[TrainerState] = battle.trainers.get(actor.controller_id)
    trainer_id = trainer.identifier if trainer else actor.controller_id
    return f"{trainer_id}:{actor.spec.species}"


policy_adapter.register_policy_adapter("hybrid_rules", _hybrid_rules_policy_adapter)


__all__ = [
    "HybridAIConfig",
    "ProfileStore",
    "OpponentProfile",
    "get_profile_store",
    "set_profile_store_path",
    "current_profile_store_path",
    "choose_action",
    "choose_best_move",
    "score_state",
    "score_action",
    "rank_candidates",
    "generate_candidates",
    "observe_action",
]
