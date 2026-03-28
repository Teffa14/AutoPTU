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
            if not targeting.is_target_in_range(actor.position, target_state.position, move):
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
            if not targeting.is_target_in_range(actor.position, target_state.position, move):
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
        if actor.position and opponents and danger >= 0.4:
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
        action = SwitchAction(actor_id=actor_id, replacement_id=candidate)
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
        if _is_maneuver_move(move):
            return _score_maneuver_action(battle, actor_id, move, target)
        if (move.category or "").lower() != "status":
            if not _move_hits_opponent(battle, actor_id, move, action.target_id):
                return -5.0
        if move.category.lower() != "status" and target is not None:
            amount = expected_damage(actor, target, move, weather=battle.weather)
            score += amount
            if target.hp is not None and target.hp > 0:
                score += 0.2 * (amount / target.hp)
        if move.category.lower() == "status":
            score += 0.25
            score += _status_move_setup_score(battle, actor_id, move, action.target_id, current_round)
            score += _type_choice_bonus(battle, actor_id, move, action.chosen_type)
            if current_round >= 8:
                score -= 0.2
            if current_round >= 12:
                score -= 0.45
        score += _combo_description_bonus(battle, actor_id, move, target)
        if move.priority > 0:
            score += 0.3
        last_move = _last_move_name(actor)
        if last_move and last_move.lower() == move.name.lower():
            score -= 0.4 if move.category.lower() == "status" else 0.2
    elif isinstance(action, ShiftAction):
        score += _shift_score(battle, actor_id, action.destination)
    elif isinstance(action, DisengageAction):
        score += _shift_score(battle, actor_id, action.destination) + 0.2
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


def choose_action(
    battle: BattleState,
    actor_id: str,
    *,
    ai_level: str = "standard",
    config: Optional[HybridAIConfig] = None,
    profile_store: Optional[ProfileStore] = None,
) -> Tuple[Optional[object], dict]:
    cfg = config or _DEFAULT_CONFIG
    store = profile_store or get_profile_store()

    candidates = generate_candidates(battle, actor_id)
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
                if move_name not in ineffective_names:
                    filtered_damage.append(action)
                    continue
                if not isinstance(action, UseMoveAction) or actor is None:
                    continue
                move = _resolve_move(actor, action.move_name)
                target = battle.pokemon.get(action.target_id) if action.target_id else None
                if move is None or target is None:
                    continue
                if expected_damage(actor, target, move, weather=battle.weather) > _MEANINGFUL_DAMAGE_THRESHOLD:
                    filtered_damage.append(action)
            if filtered_damage:
                non_struggle_damage = filtered_damage
            elif struggle is not None:
                return struggle, {"reason": "stale_ineffective_struggle"}
        if non_struggle_damage:
            non_struggle_damage.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
            return non_struggle_damage[0], {"reason": "stale_force_damage"}
        if struggle is not None:
            return struggle, {"reason": "stale_struggle"}
        best_switch = _best_switch_action(battle, actor_id, candidates)
        if best_switch is not None and score_action(battle, actor_id, best_switch) > 0.75:
            return best_switch, {"reason": "stale_switch"}
        forced = _force_engage_action(
            battle,
            actor_id,
            candidates,
            include_struggle=False,
            allow_status=False,
        )
        if forced is not None:
            return forced, {"reason": "stale_no_damage"}

    scored = [(score_action(battle, actor_id, action), action) for action in candidates]
    scored = _apply_aai_port_adjustments(
        battle,
        actor_id,
        scored,
        store,
        ai_level=ai_level,
    )
    scored.sort(key=lambda item: item[0], reverse=True)

    lethal = _lethal_action(battle, actor_id, scored, cfg.lethal_threshold)
    if lethal:
        return lethal, {"reason": "lethal"}

    best_damage = _best_damaging_action(
        battle,
        actor_id,
        candidates,
        include_struggle=False,
    )
    best_maneuver = _best_maneuver_action(battle, actor_id, candidates)
    best_status = _best_status_action(battle, actor_id, candidates)
    if best_maneuver is not None and _should_force_combo_maneuver(battle, actor_id, best_maneuver):
        return best_maneuver, {"reason": "combo_maneuver"}
    if best_damage is not None and best_status is not None:
        damage_score = score_action(battle, actor_id, best_damage)
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
        low_pressure = damage_score < 7.0
        if opening_round and status_score + 0.35 >= damage_score:
            return best_status, {"reason": "opening_setup"}
        if low_pressure and status_score >= damage_score - 0.15 and status_streak < 2:
            return best_status, {"reason": "status_value"}
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
            if not targeting.is_target_in_range(foe.position, actor.position, move):
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
    moves.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
    return moves[0]


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
                            return action
        shifts.sort(key=lambda action: score_action(battle, actor_id, action), reverse=True)
        return shifts[0]
    if allow_status:
        best_status = _best_status_action(battle, actor_id, candidates)
        if best_status is not None:
            return best_status
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
            if not targeting.is_target_in_range(actor.position, target.position, move):
                continue
            if battle.grid and not battle.has_line_of_sight(actor_id, target.position, target_id):
                continue
            if _move_hits_opponent(battle, actor_id, move, target_id):
                return True
    return False


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
        dist = targeting.chebyshev_distance(actor_pos, foe.position)
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
    if any(token in text for token in debuff_tokens) and targets_enemy:
        bonus += 0.7

    field_tokens = ("weather", "rain", "sun", "sand", "hail", "terrain", "screen")
    if any(token in text for token in field_tokens):
        bonus += 0.45 if current_round <= 4 else 0.15

    guard_tokens = ("protect", "detect", "king's shield", "spiky shield", "baneful bunker")
    if any(token in text for token in guard_tokens):
        bonus += 0.45 if actor_ratio <= 0.45 else 0.18

    if current_round <= 3 and (targets_self or targets_enemy):
        bonus += 0.2

    return bonus


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
    distances = []
    for pid in opponents:
        foe = battle.pokemon.get(pid)
        if foe is None or foe.position is None:
            continue
        distances.append(targeting.chebyshev_distance(destination, foe.position))
    if not distances:
        return 0.2
    if danger >= 0.4:
        return 0.12 * max(distances)
    return 0.08 * (1.0 / max(1, min(distances))) + 0.02


def _top_shift_targets(
    battle: BattleState,
    actor_id: str,
    reachable: Sequence[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return list(reachable)[:3]
    foe = battle.pokemon.get(opponents[0])
    if foe is None or foe.position is None:
        return list(reachable)[:3]
    ordered = sorted(reachable, key=lambda coord: targeting.chebyshev_distance(coord, foe.position))
    return ordered[:3]


def _top_defensive_shifts(
    battle: BattleState,
    actor_id: str,
    reachable: Sequence[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    opponents = _opponent_ids(battle, actor_id)
    if not opponents:
        return []
    foe = battle.pokemon.get(opponents[0])
    if foe is None or foe.position is None:
        return []
    ordered = sorted(reachable, key=lambda coord: targeting.chebyshev_distance(coord, foe.position), reverse=True)
    return ordered[:2]


def _top_disengage_targets(
    battle: BattleState,
    actor_id: str,
    reachable: Sequence[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return []
    options = [coord for coord in reachable if targeting.chebyshev_distance(actor.position, coord) == 1]
    return options[:1]


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
    "generate_candidates",
    "observe_action",
]
