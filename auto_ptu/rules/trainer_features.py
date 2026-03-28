"""Runtime trainer feature dispatcher.

Phase 2 scaffolding:
- normalized trigger dispatch
- frequency/cooldown/resource gates
- optional context conditions
- target scopes + multi-effect payload handlers
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


_FREQUENCY_LIMIT_RE = re.compile(r"^\s*(\d+)\s*/\s*(round|turn|scene|encounter|daily)\s*$")
_STAT_ALIASES = {
    "atk": "atk",
    "attack": "atk",
    "def": "def",
    "defense": "def",
    "spa": "spatk",
    "spatk": "spatk",
    "special-attack": "spatk",
    "special_attack": "spatk",
    "spd": "spd",
    "speed": "spd",
    "spdef": "spdef",
    "special-defense": "spdef",
    "special_defense": "spdef",
    "acc": "accuracy",
    "accuracy": "accuracy",
}


def _normalize_token(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_tokens(value: Any) -> List[str]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    out: List[str] = []
    for entry in values:
        token = _normalize_token(entry)
        if token:
            out.append(token)
    return out


def _int_like(value: Any, default: int = 0) -> int:
    try:
        if value in ("", None):
            return default
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def _float_like(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool_like(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    token = _normalize_token(value)
    if token in {"1", "true", "yes", "y", "on"}:
        return True
    if token in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _feature_identifier(feature: Dict[str, Any]) -> str:
    raw = feature.get("feature_id") or feature.get("id") or feature.get("name")
    token = _normalize_token(raw).replace(" ", "-")
    return token or "feature"


def _is_feature_enabled(feature: Dict[str, Any]) -> bool:
    if "enabled" not in feature:
        return True
    return bool(feature.get("enabled"))


def _feature_trigger(feature: Dict[str, Any]) -> str:
    return _normalize_token(feature.get("trigger"))


def _frequency_token(feature: Dict[str, Any]) -> str:
    return _normalize_token(feature.get("frequency") or "at-will")


@dataclass
class TrainerFeatureDispatcher:
    battle: Any
    _trigger_counts: Dict[str, int] = field(default_factory=dict)

    def trigger(self, trigger: str, *, actor_id: Optional[str] = None, payload: Optional[dict] = None) -> None:
        token = _normalize_token(trigger)
        if not token:
            return
        self._trigger_counts[token] = int(self._trigger_counts.get(token, 0)) + 1
        context_payload = dict(payload or {})
        for trainer_id, trainer in getattr(self.battle, "trainers", {}).items():
            features = self._trainer_features(trainer)
            if not features:
                continue
            for feature in features:
                if not _is_feature_enabled(feature):
                    continue
                if _feature_trigger(feature) != token:
                    continue
                if not self._feature_prerequisites_met(
                    trainer_id=trainer_id,
                    trainer=trainer,
                    feature=feature,
                ):
                    continue
                if not self._feature_matches_context(
                    trainer_id=trainer_id,
                    trainer=trainer,
                    feature=feature,
                    actor_id=actor_id,
                    payload=context_payload,
                ):
                    continue
                if not self._feature_is_available(trainer, feature):
                    continue
                if not self._feature_has_resources(trainer, feature):
                    continue
                applied = self._apply_feature(
                    trainer_id=trainer_id,
                    trainer=trainer,
                    feature=feature,
                    actor_id=actor_id,
                    payload=context_payload,
                )
                if applied:
                    self._consume_resources(trainer, feature)
                    self._mark_feature_use(trainer, feature, actor_id=actor_id)

    def _trainer_features(self, trainer: Any) -> List[Dict[str, Any]]:
        collected: List[Dict[str, Any]] = []
        seen = set()
        for source_name in ("features", "edges"):
            source_entries = getattr(trainer, source_name, []) or []
            for entry in source_entries:
                normalized = self._normalize_feature_entry(entry, source_name=source_name)
                if normalized is None:
                    continue
                fid = _feature_identifier(normalized)
                if fid in seen:
                    continue
                seen.add(fid)
                collected.append(normalized)
        trainer_class = getattr(trainer, "trainer_class", None) or {}
        known = trainer_class.get("known_features") if isinstance(trainer_class, dict) else []
        if isinstance(known, list):
            for entry in known:
                normalized = self._normalize_feature_entry(entry, source_name="feature")
                if normalized is None:
                    continue
                fid = _feature_identifier(normalized)
                if fid in seen:
                    continue
                seen.add(fid)
                collected.append(normalized)
        return collected

    def _normalize_feature_entry(
        self,
        entry: Any,
        *,
        source_name: str,
    ) -> Optional[Dict[str, Any]]:
        if isinstance(entry, dict):
            normalized = dict(entry)
        elif isinstance(entry, str):
            token = str(entry).strip()
            if not token:
                return None
            normalized = {"name": token}
        else:
            return None
        normalized.setdefault(
            "runtime_kind",
            "edge" if _normalize_token(source_name) == "edges" else "feature",
        )
        return normalized

    def _feature_usage(self, trainer: Any, feature: Dict[str, Any]) -> Dict[str, int]:
        usage: Dict[str, Dict[str, int]] = getattr(trainer, "feature_usage", {})
        fid = _feature_identifier(feature)
        return dict(usage.get(fid, {}))

    def _trainer_known_feature_ids(self, trainer: Any) -> List[str]:
        known: List[str] = []
        for entry in self._trainer_features(trainer):
            if not isinstance(entry, dict):
                continue
            token = _feature_identifier(entry)
            if token and token not in known:
                known.append(token)
        return known

    def _feature_prerequisites_met(
        self,
        *,
        trainer_id: str,
        trainer: Any,
        feature: Dict[str, Any],
    ) -> bool:
        trainer_class = getattr(trainer, "trainer_class", {}) or {}
        if not isinstance(trainer_class, dict):
            trainer_class = {}
        class_id = _normalize_token(trainer_class.get("class_id") or trainer_class.get("id") or "")
        subclass_id = _normalize_token(
            trainer_class.get("subclass_id") or trainer_class.get("subclass") or ""
        )
        class_level = _int_like(trainer_class.get("level"), 0)
        min_level = _int_like(feature.get("min_trainer_level", feature.get("level_required", 0)), 0)
        if min_level > 0 and class_level < min_level:
            return False

        required_classes = _normalize_tokens(feature.get("required_classes"))
        if required_classes and class_id not in required_classes:
            return False

        required_subclasses = _normalize_tokens(feature.get("required_subclasses"))
        if required_subclasses and subclass_id not in required_subclasses:
            return False

        required_features = _normalize_tokens(feature.get("required_features"))
        if required_features:
            known_features = set(self._trainer_known_feature_ids(trainer))
            if any(req not in known_features for req in required_features):
                return False

        prereq = feature.get("prerequisites")
        if isinstance(prereq, dict):
            prereq_min_level = _int_like(
                prereq.get("min_trainer_level", prereq.get("level", 0)), 0
            )
            if prereq_min_level > 0 and class_level < prereq_min_level:
                return False
            prereq_classes = _normalize_tokens(prereq.get("classes") or prereq.get("class"))
            if prereq_classes and class_id not in prereq_classes:
                return False
            prereq_subclasses = _normalize_tokens(
                prereq.get("subclasses") or prereq.get("subclass")
            )
            if prereq_subclasses and subclass_id not in prereq_subclasses:
                return False
            prereq_features = _normalize_tokens(prereq.get("features") or prereq.get("feature"))
            if prereq_features:
                known_features = set(self._trainer_known_feature_ids(trainer))
                if any(req not in known_features for req in prereq_features):
                    return False
        return True

    def _frequency_limits(self, feature: Dict[str, Any]) -> Tuple[int, int]:
        total_limit = _int_like(feature.get("max_uses"), 0)
        round_limit = _int_like(feature.get("uses_per_round"), 0)
        token = _frequency_token(feature)
        if token in {"daily", "scene", "encounter"} and total_limit <= 0:
            total_limit = 1
        if token in {"eot", "round", "turn", "x/round", "per-round", "per round"} and round_limit <= 0:
            round_limit = 1
        match = _FREQUENCY_LIMIT_RE.match(token)
        if match:
            count = _int_like(match.group(1), 0)
            scope = _normalize_token(match.group(2))
            if scope in {"round", "turn"} and round_limit <= 0:
                round_limit = count
            if scope in {"daily", "scene", "encounter"} and total_limit <= 0:
                total_limit = count
        return max(0, total_limit), max(0, round_limit)

    def _feature_is_available(self, trainer: Any, feature: Dict[str, Any]) -> bool:
        info = self._feature_usage(trainer, feature)
        current_round = int(getattr(self.battle, "round", 0) or 0)
        cooldown_until = int(info.get("cooldown_until", 0) or 0)
        if cooldown_until and current_round <= cooldown_until:
            return False
        total_limit, round_limit = self._frequency_limits(feature)
        if total_limit > 0 and int(info.get("uses_total", 0) or 0) >= total_limit:
            return False
        round_key = f"uses_round_{current_round}"
        if round_limit > 0 and int(info.get(round_key, 0) or 0) >= round_limit:
            return False
        return True

    def _feature_matches_context(
        self,
        *,
        trainer_id: str,
        trainer: Any,
        feature: Dict[str, Any],
        actor_id: Optional[str],
        payload: Dict[str, Any],
    ) -> bool:
        conditions = feature.get("conditions") or feature.get("condition") or {}
        if not isinstance(conditions, dict):
            return True
        if _bool_like(conditions.get("actor_required")) and not actor_id:
            return False
        actor_trainer_id = self._trainer_for_actor(actor_id)
        actor_mon = self.battle.pokemon.get(actor_id) if actor_id else None

        actor_scope = _normalize_token(conditions.get("actor_scope"))
        if actor_scope in {"self", "self_team", "ally", "allies", "own"} and actor_trainer_id != trainer_id:
            return False
        if actor_scope in {"enemy", "foe", "opponent"} and (
            actor_trainer_id is None or actor_trainer_id == trainer_id
        ):
            return False
        if actor_scope == "trainer" and actor_id != trainer_id:
            return False
        if actor_scope == "pokemon" and actor_mon is None:
            return False

        phase_filters = _normalize_tokens(conditions.get("phase_in") or conditions.get("phase"))
        if phase_filters:
            phase_value = _normalize_token(payload.get("phase"))
            if not phase_value:
                phase_obj = getattr(self.battle, "phase", "")
                phase_value = _normalize_token(getattr(phase_obj, "value", phase_obj))
            if phase_value not in phase_filters:
                return False

        action_filters = _normalize_tokens(conditions.get("action_types") or conditions.get("action_type"))
        if action_filters and _normalize_token(payload.get("action_type")) not in action_filters:
            return False

        move_name_filters = _normalize_tokens(conditions.get("move_names") or conditions.get("move_name"))
        if move_name_filters and _normalize_token(payload.get("move_name")) not in move_name_filters:
            return False

        move_category_filters = _normalize_tokens(
            conditions.get("move_categories") or conditions.get("move_category")
        )
        if move_category_filters and _normalize_token(payload.get("move_category")) not in move_category_filters:
            return False

        if "actor_active" in conditions:
            target_state = _bool_like(conditions.get("actor_active"))
            if actor_mon is None or bool(actor_mon.active) != target_state:
                return False

        min_round = _int_like(conditions.get("min_round"), 0)
        max_round = _int_like(conditions.get("max_round"), 0)
        current_round = int(getattr(self.battle, "round", 0) or 0)
        if min_round > 0 and current_round < min_round:
            return False
        if max_round > 0 and current_round > max_round:
            return False

        damage = _int_like(
            payload.get("damage"),
            _int_like(payload.get("damage_dealt"), _int_like(payload.get("total_damage"), 0)),
        )
        min_damage = _int_like(conditions.get("min_damage"), 0)
        max_damage = _int_like(conditions.get("max_damage"), 0)
        if min_damage > 0 and damage < min_damage:
            return False
        if max_damage > 0 and damage > max_damage:
            return False

        if _bool_like(conditions.get("once_per_actor_per_round")) and actor_id:
            info = self._feature_usage(trainer, feature)
            actor_round_key = f"actor_round_{actor_id}_{current_round}"
            if int(info.get(actor_round_key, 0) or 0) >= 1:
                return False

        if conditions.get("chance") not in (None, ""):
            chance = _float_like(conditions.get("chance"), 0.0)
            if chance > 1.0:
                chance = chance / 100.0
            chance = max(0.0, min(1.0, chance))
            if chance <= 0.0:
                return False
            rng = getattr(self.battle, "rng", None)
            roll = rng.random() if callable(getattr(rng, "random", None)) else 0.0
            if roll >= chance:
                return False
        return True

    def _trainer_for_actor(self, actor_id: Optional[str]) -> Optional[str]:
        if not actor_id:
            return None
        if actor_id in self.battle.trainers:
            return actor_id
        mon = self.battle.pokemon.get(actor_id)
        if mon is None:
            return None
        return mon.controller_id

    def _feature_has_resources(self, trainer: Any, feature: Dict[str, Any]) -> bool:
        resources = getattr(trainer, "feature_resources", {}) or {}
        costs = feature.get("resource_cost") or {}
        if not isinstance(costs, dict):
            return True
        for key, value in costs.items():
            token = str(key)
            need = _int_like(value, 0)
            if need <= 0:
                continue
            if int(resources.get(token, 0) or 0) < need:
                return False
        return True

    def _consume_resources(self, trainer: Any, feature: Dict[str, Any]) -> None:
        resources = getattr(trainer, "feature_resources", {}) or {}
        costs = feature.get("resource_cost") or {}
        if not isinstance(costs, dict):
            return
        for key, value in costs.items():
            token = str(key)
            need = _int_like(value, 0)
            if need <= 0:
                continue
            resources[token] = max(0, int(resources.get(token, 0) or 0) - need)
        setattr(trainer, "feature_resources", resources)

    def _mark_feature_use(self, trainer: Any, feature: Dict[str, Any], *, actor_id: Optional[str] = None) -> None:
        usage: Dict[str, Dict[str, int]] = dict(getattr(trainer, "feature_usage", {}) or {})
        fid = _feature_identifier(feature)
        info = dict(usage.get(fid, {}))
        current_round = int(getattr(self.battle, "round", 0) or 0)
        info["uses_total"] = int(info.get("uses_total", 0) or 0) + 1
        info["last_round"] = current_round
        round_key = f"uses_round_{current_round}"
        info[round_key] = int(info.get(round_key, 0) or 0) + 1
        if actor_id:
            actor_round_key = f"actor_round_{actor_id}_{current_round}"
            info[actor_round_key] = int(info.get(actor_round_key, 0) or 0) + 1
        cooldown = _int_like(feature.get("cooldown_rounds", feature.get("cooldown", 0)), 0)
        if cooldown > 0:
            info["cooldown_until"] = current_round + cooldown
        usage[fid] = info
        setattr(trainer, "feature_usage", usage)

    def _apply_feature(
        self,
        *,
        trainer_id: str,
        trainer: Any,
        feature: Dict[str, Any],
        actor_id: Optional[str],
        payload: Dict[str, Any],
    ) -> bool:
        applied = False
        applied_effects: List[str] = []
        applied_targets: List[str] = []
        details: List[Dict[str, Any]] = []
        for effect in self._feature_effects(feature):
            effect_applied, effect_type, effect_targets, effect_detail = self._apply_effect(
                trainer_id=trainer_id,
                trainer=trainer,
                feature=feature,
                effect=effect,
                actor_id=actor_id,
                payload=payload,
            )
            if not effect_applied:
                continue
            applied = True
            applied_effects.append(effect_type or "log_only")
            applied_targets.extend(effect_targets)
            if effect_detail:
                details.append(effect_detail)

        if applied:
            unique_targets: List[str] = []
            for target in applied_targets:
                if target not in unique_targets:
                    unique_targets.append(target)
            self.battle.log_event(
                {
                    "type": "trainer_feature",
                    "trainer": trainer_id,
                    "actor": actor_id or trainer_id,
                    "feature_id": _feature_identifier(feature),
                    "feature": str(feature.get("name") or _feature_identifier(feature)),
                    "feature_kind": str(feature.get("runtime_kind") or "feature"),
                    "trigger": _feature_trigger(feature),
                    "effect_type": (
                        applied_effects[0] if len(applied_effects) == 1 else "multi"
                    ),
                    "effect_types": applied_effects,
                    "targets": unique_targets,
                    "details": details,
                    "payload": payload,
                }
            )
        return applied

    def _feature_effects(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw_effects = feature.get("effects")
        if isinstance(raw_effects, list):
            entries = [dict(entry) for entry in raw_effects if isinstance(entry, dict)]
            return entries if entries else [{}]
        raw_primary = feature.get("effect_payload")
        if raw_primary is None:
            raw_primary = feature.get("effect")
        if isinstance(raw_primary, list):
            entries = [dict(entry) for entry in raw_primary if isinstance(entry, dict)]
            return entries if entries else [{}]
        if isinstance(raw_primary, dict):
            return [dict(raw_primary)]
        return [{}]

    def _resolve_effect_targets(
        self,
        *,
        trainer_id: str,
        actor_id: Optional[str],
        payload: Dict[str, Any],
        feature: Dict[str, Any],
        effect: Dict[str, Any],
    ) -> List[str]:
        rules: Dict[str, Any] = {}
        feature_rules = feature.get("target_rules")
        if isinstance(feature_rules, dict):
            rules.update(feature_rules)
        effect_rules = effect.get("target_rules")
        if isinstance(effect_rules, dict):
            rules.update(effect_rules)
        return self._targets_for_feature(
            trainer_id=trainer_id,
            actor_id=actor_id,
            payload=payload,
            rules=rules,
        )

    def _resolve_trainer_targets(self, trainer_id: str, effect: Dict[str, Any]) -> List[str]:
        selector = _normalize_token(effect.get("trainer_scope") or effect.get("trainer") or "self")
        if selector in {"self", "ally", "allies", "self_team", "own"}:
            return [trainer_id]
        if selector in {"enemy", "foe", "opponent"}:
            return [tid for tid in self.battle.trainers if tid != trainer_id]
        if selector in {"all", "any"}:
            return list(self.battle.trainers.keys())
        if selector in self.battle.trainers:
            return [selector]
        return [trainer_id]

    def _normalize_stat(self, raw: Any) -> str:
        return _STAT_ALIASES.get(_normalize_token(raw), "")

    def _apply_effect(
        self,
        *,
        trainer_id: str,
        trainer: Any,
        feature: Dict[str, Any],
        effect: Dict[str, Any],
        actor_id: Optional[str],
        payload: Dict[str, Any],
    ) -> Tuple[bool, str, List[str], Dict[str, Any]]:
        effect_type = _normalize_token(effect.get("type"))
        if not effect_type:
            return True, "log_only", [], {}
        if effect_type == "grant_ap":
            amount = _int_like(effect.get("amount", 1), 0)
            if amount <= 0:
                return False, effect_type, [], {}
            targets = self._resolve_trainer_targets(trainer_id, effect)
            changed: List[str] = []
            for tid in targets:
                target_trainer = self.battle.trainers.get(tid)
                if target_trainer is None:
                    continue
                target_trainer.ap = int(getattr(target_trainer, "ap", 0) or 0) + amount
                changed.append(tid)
            return bool(changed), effect_type, [], {"amount": amount, "trainers": changed}

        target_ids = self._resolve_effect_targets(
            trainer_id=trainer_id,
            actor_id=actor_id,
            payload=payload,
            feature=feature,
            effect=effect,
        )

        if effect_type in {"heal_active", "heal"}:
            amount = _int_like(effect.get("amount"), 0)
            if amount <= 0 or not target_ids:
                return False, effect_type, [], {}
            changed: List[str] = []
            for pid in target_ids:
                mon = self.battle.pokemon.get(pid)
                if mon is None:
                    continue
                before = int(mon.hp or 0)
                mon.heal(amount)
                if int(mon.hp or 0) != before:
                    changed.append(pid)
            return bool(changed), "heal", changed, {"amount": amount}

        if effect_type == "grant_temp_hp":
            amount = _int_like(effect.get("amount"), 0)
            if amount <= 0 or not target_ids:
                return False, effect_type, [], {}
            changed: List[str] = []
            for pid in target_ids:
                mon = self.battle.pokemon.get(pid)
                if mon is None:
                    continue
                gained = mon.add_temp_hp(amount)
                if gained > 0:
                    changed.append(pid)
            return bool(changed), effect_type, changed, {"amount": amount}

        if effect_type == "raise_cs":
            stats_payload = effect.get("stats")
            stat_changes: Dict[str, int] = {}
            if isinstance(stats_payload, dict):
                for key, value in stats_payload.items():
                    stat = self._normalize_stat(key)
                    amount = _int_like(value, 0)
                    if stat and amount:
                        stat_changes[stat] = amount
            else:
                stat = self._normalize_stat(effect.get("stat"))
                amount = _int_like(effect.get("amount"), 0)
                if stat and amount:
                    stat_changes[stat] = amount
            if not stat_changes or not target_ids:
                return False, effect_type, [], {}
            changed: List[str] = []
            for pid in target_ids:
                mon = self.battle.pokemon.get(pid)
                if mon is None:
                    continue
                mon_changed = False
                for stat, amount in stat_changes.items():
                    current = _int_like(mon.combat_stages.get(stat, 0), 0)
                    updated = max(-6, min(6, current + amount))
                    if updated != current:
                        mon.combat_stages[stat] = updated
                        mon_changed = True
                if mon_changed:
                    changed.append(pid)
            return bool(changed), effect_type, changed, {"stats": stat_changes}

        if effect_type == "apply_status":
            status_name = str(effect.get("status", effect.get("name", ""))).strip()
            duration = _int_like(effect.get("duration", effect.get("remaining", 0)), 0)
            stack = _bool_like(effect.get("stack"), False)
            if not status_name or not target_ids:
                return False, effect_type, [], {}
            changed: List[str] = []
            for pid in target_ids:
                mon = self.battle.pokemon.get(pid)
                if mon is None:
                    continue
                if mon.has_status(status_name) and not stack:
                    if duration > 0:
                        for status in list(mon.statuses):
                            if mon._normalized_status_name(status) != status_name.lower():
                                continue
                            entry = mon._upgrade_status_entry(status, canonical_name=status_name)
                            current = _int_like(entry.get("remaining", entry.get("duration", 0)), 0)
                            if current < duration:
                                entry["remaining"] = duration
                                entry["duration"] = duration
                                changed.append(pid)
                                break
                    continue
                status_entry: Dict[str, Any] = {
                    "name": status_name,
                    "source": f"trainer_feature:{_feature_identifier(feature)}",
                }
                if duration > 0:
                    status_entry["remaining"] = duration
                    status_entry["duration"] = duration
                mon.statuses.append(status_entry)
                changed.append(pid)
            return bool(changed), effect_type, changed, {"status": status_name, "duration": duration}

        if effect_type == "remove_status":
            statuses = _normalize_tokens(effect.get("statuses") or effect.get("status"))
            remove_all = _bool_like(effect.get("all"), False)
            if (not statuses and not remove_all) or not target_ids:
                return False, effect_type, [], {}
            changed: List[str] = []
            removed_names: List[str] = []
            for pid in target_ids:
                mon = self.battle.pokemon.get(pid)
                if mon is None:
                    continue
                local_removed = False
                if remove_all:
                    count = len(mon.statuses)
                    if count > 0:
                        mon.statuses = []
                        local_removed = True
                        removed_names.append("all")
                else:
                    for status_name in statuses:
                        removed = mon.remove_status_by_names({status_name})
                        while removed:
                            local_removed = True
                            removed_names.append(removed)
                            removed = mon.remove_status_by_names({status_name})
                if local_removed:
                    changed.append(pid)
            return bool(changed), effect_type, changed, {"removed": removed_names}

        if effect_type == "set_weather":
            weather = str(effect.get("weather", "")).strip()
            if not weather:
                return False, effect_type, [], {}
            if _normalize_token(getattr(self.battle, "weather", "")) == _normalize_token(weather):
                return False, effect_type, [], {}
            self.battle.weather = weather
            return True, effect_type, [], {"weather": weather}

        return True, effect_type, [], {"unhandled": True}

    def _targets_for_feature(
        self,
        *,
        trainer_id: str,
        actor_id: Optional[str],
        payload: Dict[str, Any],
        rules: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        cfg = dict(rules or {})
        scope = _normalize_token(cfg.get("scope") or cfg.get("target") or "active_allies")
        default_include_inactive = scope in {"all_allies", "all_enemies", "all", "all_pokemon"}
        include_inactive = _bool_like(cfg.get("include_inactive"), default_include_inactive)
        include_fainted = _bool_like(cfg.get("include_fainted"), False)
        candidate_ids = self._target_ids_for_scope(
            trainer_id=trainer_id,
            actor_id=actor_id,
            payload=payload,
            scope=scope,
        )

        required_status = _normalize_tokens(cfg.get("require_status"))
        blocked_status = _normalize_tokens(cfg.get("exclude_status"))

        filtered: List[str] = []
        for pid in candidate_ids:
            mon = self.battle.pokemon.get(pid)
            if mon is None:
                continue
            if not include_fainted and mon.fainted:
                continue
            if not include_inactive and not mon.active:
                continue
            if required_status and not any(mon.has_status(name) for name in required_status):
                continue
            if blocked_status and any(mon.has_status(name) for name in blocked_status):
                continue
            filtered.append(pid)

        limit = _int_like(cfg.get("limit"), 0)
        if limit > 0:
            filtered = filtered[:limit]
        return filtered

    def _target_ids_for_scope(
        self,
        *,
        trainer_id: str,
        actor_id: Optional[str],
        payload: Dict[str, Any],
        scope: str,
    ) -> List[str]:
        pokemon = getattr(self.battle, "pokemon", {})
        if scope in {"actor", "self", "acting"}:
            return [actor_id] if actor_id in pokemon else []
        if scope in {"target", "action_target"}:
            target_id = payload.get("target_id")
            return [target_id] if target_id in pokemon else []
        if scope in {"targets", "action_targets"}:
            values = payload.get("target_ids")
            if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
                return []
            return [pid for pid in values if pid in pokemon]
        if scope in {"all_active", "active"}:
            return [pid for pid, mon in pokemon.items() if mon.active]
        if scope in {"all_allies", "allies"}:
            return [pid for pid, mon in pokemon.items() if mon.controller_id == trainer_id]
        if scope in {"active_allies", "ally_active", "self_team"}:
            return [
                pid
                for pid, mon in pokemon.items()
                if mon.controller_id == trainer_id and mon.active
            ]
        if scope in {"all_enemies", "enemies", "foes"}:
            return [pid for pid, mon in pokemon.items() if mon.controller_id != trainer_id]
        if scope in {"active_enemies", "enemy_active", "foe_active"}:
            return [
                pid
                for pid, mon in pokemon.items()
                if mon.controller_id != trainer_id and mon.active
            ]
        if scope in {"all", "all_pokemon"}:
            return list(pokemon.keys())
        # Safe default is active allies.
        return [
            pid
            for pid, mon in pokemon.items()
            if mon.controller_id == trainer_id and mon.active
        ]
