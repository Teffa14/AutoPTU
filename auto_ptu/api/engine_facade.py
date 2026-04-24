from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Collection, Dict, Iterable, List, Optional, Tuple

from ..data_loader import default_campaign, load_builtin_campaign, load_campaign
from ..data_models import GridSpec, MatchPlan, MatchupSpec, MoveSpec, TrainerSideSpec
from ..matchmaker import AutoMatchPlanner
from ..csv_repository import PTUCsvRepository
from ..random_campaign import CsvRandomCampaignBuilder
from ..roster_csv import (
    campaign_from_roster_csv,
    campaign_from_roster_csv_file,
    match_plan_from_roster_csv,
    match_plan_from_roster_csv_file,
)
from ..rules import (
    BattleState,
    CreativeAction,
    DelayAction,
    DisengageAction,
    EquipWeaponAction,
    GrappleAction,
    GridState,
    InterceptAction,
    ManipulateAction,
    MotivatedAction,
    PickupItemAction,
    TrainerState,
    TrainerSwitchAction,
    PokemonState,
    ShiftAction,
    SprintAction,
    SwitchAction,
    TakeBreatherAction,
    TradeStandardForAction,
    UnequipWeaponAction,
    JumpAction,
    UseMoveAction,
    UseItemAction,
    TurnPhase,
    WakeAllyAction,
    create_trainer_feature_action,
)
from ..rules import movement, targeting
from ..rules import ai_hybrid
from ..rules.battle_state import (
    SUPPORTED_TARGET_ORDER_SPECS,
    _dashing_makeover_item_options_for_target,
    _item_entry_for,
    _item_name_text,
    _is_capture_ball_name,
    _load_maneuver_moves,
    _signature_technique_options_for_target,
    _wardrobe_slots,
    _weapon_tags,
)
from ..rules.calculations import defensive_stat, offensive_stat, speed_stat
from ..rules.item_effects import parse_item_effects
from ..gameplay import BattleRecord, TextBattleSession, ai_learning_status, ai_model_status, ai_record_battle_outcome
from rich.console import Console
from ..sprites import sprite_path_for
from ..natures import nature_profile


_MARKER_CHARS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_STAT_LABELS = {
    "hp": "HP",
    "atk": "Atk",
    "def": "Def",
    "spatk": "SpAtk",
    "spdef": "SpDef",
    "spd": "Speed",
    "accuracy": "Accuracy",
    "evasion": "Evasion",
}


def _normalize_move_key(value: object) -> str:
    text = str(value or "").strip().lower()
    return "".join(ch for ch in text if ch.isalnum())


def _normalize_ability_key(value: object) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("’", "'").replace("`", "'").replace("*", "")
    return "".join(ch for ch in text if ch.isalnum())


def _find_ability_payload(spec: object, ability_name: str) -> Optional[dict]:
    target = _normalize_ability_key(ability_name)
    if not target:
        return None
    for entry in list(getattr(spec, "abilities", []) or []):
        if not isinstance(entry, dict):
            continue
        if _normalize_ability_key(entry.get("name") or "") == target:
            return entry
    return None


def _runtime_struggle_move() -> MoveSpec:
    return MoveSpec(
        name="Struggle",
        type="Typeless",
        category="Physical",
        db=4,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
        range_text="Melee, 1 Target",
        effects_text="Default fallback attack available to all combatants.",
    )


def _trainer_feature_names(state: PokemonState) -> List[str]:
    names: List[str] = []
    seen: set[str] = set()
    for entry in getattr(state.spec, "trainer_features", []) or []:
        if isinstance(entry, str):
            label = entry.strip()
        elif isinstance(entry, dict):
            label = str(entry.get("name") or entry.get("feature_id") or entry.get("id") or "").strip()
        else:
            label = ""
        if not label:
            continue
        normalized = label.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        names.append(label)
    return names


def _trainer_feature_payloads(state: PokemonState, feature_names: Collection[str]) -> List[dict]:
    wanted = {str(name or "").strip().lower() for name in feature_names if str(name or "").strip()}
    payloads: List[dict] = []
    for entry in getattr(state.spec, "trainer_features", []) or []:
        if isinstance(entry, str):
            payload = {"name": entry.strip()}
        elif isinstance(entry, dict):
            payload = dict(entry)
            payload["name"] = str(entry.get("name") or entry.get("feature_id") or entry.get("id") or "").strip()
        else:
            continue
        normalized = str(payload.get("name") or "").strip().lower()
        if normalized and normalized in wanted:
            payloads.append(payload)
    return payloads


def _normalize_named_entries(entries: Any) -> List[dict]:
    normalized: List[dict] = []
    for entry in list(entries or []):
        if isinstance(entry, str):
            name = entry.strip()
            if name:
                normalized.append({"name": name})
            continue
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or entry.get("feature_id") or entry.get("id") or "").strip()
        if not name:
            continue
        payload = dict(entry)
        payload["name"] = name
        normalized.append(payload)
    return normalized


def _item_stat_label(stat: object) -> str:
    key = str(stat or "").strip().lower()
    return _STAT_LABELS.get(key, str(stat or "").strip() or "?")


def _type_label(type_name: object) -> str:
    value = str(type_name or "").strip().lower()
    return value.title() if value else "?"


def _append_unique_line(lines: List[str], text: str) -> None:
    value = str(text or "").strip()
    if value and value not in lines:
        lines.append(value)


def _describe_item_effects(state: PokemonState, item: object) -> Tuple[List[str], str]:
    entry = _item_entry_for(item)
    effects = parse_item_effects(entry) if entry is not None else {}
    raw = item if isinstance(item, dict) else {}
    lines: List[str] = []

    for stat, amount in effects.get("base_stat_changes", []) or []:
        try:
            amount_value = int(amount or 0)
        except (TypeError, ValueError):
            continue
        sign = "+" if amount_value >= 0 else ""
        _append_unique_line(lines, f"Base {_item_stat_label(stat)} {sign}{amount_value}")
    for stat, amount in effects.get("post_stage_stat_bonus", []) or []:
        try:
            amount_value = int(amount or 0)
        except (TypeError, ValueError):
            continue
        sign = "+" if amount_value >= 0 else ""
        _append_unique_line(lines, f"Post-stage {_item_stat_label(stat)} {sign}{amount_value}")
    for stat, value in effects.get("base_stat_scalars", []) or []:
        try:
            scalar_value = float(value or 1.0)
        except (TypeError, ValueError):
            continue
        _append_unique_line(lines, f"Base {_item_stat_label(stat)} x{scalar_value:g}")
    for stat, value in effects.get("stat_scalars", []) or []:
        try:
            scalar_value = float(value or 1.0)
        except (TypeError, ValueError):
            continue
        _append_unique_line(lines, f"{_item_stat_label(stat)} x{scalar_value:g}")
    for stat, amount in effects.get("stage_changes", []) or []:
        try:
            amount_value = int(amount or 0)
        except (TypeError, ValueError):
            continue
        sign = "+" if amount_value >= 0 else ""
        _append_unique_line(lines, f"{_item_stat_label(stat)} stages {sign}{amount_value}")

    if effects.get("start_heal_fraction"):
        num, den = effects["start_heal_fraction"]
        _append_unique_line(lines, f"Heals {num}/{den} max HP at turn start")
    if effects.get("end_heal_fraction"):
        num, den = effects["end_heal_fraction"]
        _append_unique_line(lines, f"Heals {num}/{den} max HP at turn end")
    if effects.get("use_heal_fraction"):
        num, den = effects["use_heal_fraction"]
        _append_unique_line(lines, f"Restores {num}/{den} max HP on use")
    if effects.get("use_heal_full"):
        _append_unique_line(lines, "Fully restores HP on use")
    if effects.get("use_heal_hp"):
        _append_unique_line(lines, f"Restores {int(effects['use_heal_hp'])} HP on use")
    if effects.get("revive_ticks"):
        _append_unique_line(lines, f"Revives for {int(effects['revive_ticks'])} ticks")
    if effects.get("start_ticks"):
        _append_unique_line(lines, f"Heals {int(effects['start_ticks'])} ticks at turn start")
    if effects.get("end_ticks"):
        _append_unique_line(lines, f"Heals {int(effects['end_ticks'])} ticks at turn end")
    if effects.get("save_bonus"):
        _append_unique_line(lines, f"+{int(effects['save_bonus'])} to save rolls")
    if effects.get("damage_bonus_scene"):
        _append_unique_line(lines, f"+{int(effects['damage_bonus_scene'])} damage for the scene")
    if effects.get("drain_multiplier"):
        _append_unique_line(lines, f"Drain healing x{float(effects['drain_multiplier']):g}")
    if effects.get("healing_multiplier"):
        _append_unique_line(lines, f"Healing x{float(effects['healing_multiplier']):g}")
    if effects.get("evasion_bonus_round"):
        _append_unique_line(lines, f"+{int(effects['evasion_bonus_round'])} evasion for 1 round")
    if effects.get("flinch_immunity"):
        _append_unique_line(lines, "Immune to flinch")
    if effects.get("secondary_immunity"):
        _append_unique_line(lines, "Immune to secondary effects")
    if effects.get("cure_volatile"):
        _append_unique_line(lines, "Cures volatile statuses")
    if effects.get("setup_skip"):
        _append_unique_line(lines, "Skips setup turn")
    if effects.get("clear_negative_stages"):
        _append_unique_line(lines, "Clears negative combat stages")
    if effects.get("self_status"):
        _append_unique_line(lines, f"Applies {effects['self_status']} to the user")
    if effects.get("choice_stat"):
        choice_stat, choice_amount = effects["choice_stat"]
        sign = "+" if int(choice_amount or 0) >= 0 else ""
        suffix = " while suppressed" if effects.get("choice_suppressed") else ""
        _append_unique_line(lines, f"Choice boost: {_item_stat_label(choice_stat)} {sign}{int(choice_amount or 0)} stages{suffix}")
    if effects.get("choice_lock_duration"):
        _append_unique_line(lines, f"Choice-lock for {int(effects['choice_lock_duration'])} rounds")

    name_key = str((raw.get("name") if isinstance(raw, dict) else item) or "").strip().lower()
    if name_key == "eviolite":
        chosen_stats = raw.get("chosen_stats") if isinstance(raw, dict) else None
        if isinstance(chosen_stats, list) and chosen_stats:
            chosen_labels = ", ".join(_item_stat_label(value) for value in chosen_stats if str(value or "").strip())
            if chosen_labels:
                _append_unique_line(lines, f"Chosen stats: {chosen_labels}")
                _append_unique_line(lines, "Eviolite grants +5 post-stage to each chosen stat")
    if name_key == "stat boosters":
        chosen_stat = raw.get("chosen_stat") if isinstance(raw, dict) else ""
        if str(chosen_stat or "").strip():
            _append_unique_line(lines, f"Chosen stat: {_item_stat_label(chosen_stat)}")
            _append_unique_line(lines, "Grants +1 CS to the chosen stat on turn start")

    description = ""
    if entry is not None:
        description = str(entry.description or "").strip()
    return lines, description


def _effective_stats_payload(state: PokemonState) -> Dict[str, int]:
    return {
        "hp": int(state.max_hp()),
        "atk": int(offensive_stat(state, "physical")),
        "def": int(defensive_stat(state, "physical")),
        "spatk": int(offensive_stat(state, "special")),
        "spdef": int(defensive_stat(state, "special")),
        "spd": int(speed_stat(state)),
    }


def _trainer_action_hints(battle: BattleState, actor_id: str, state: PokemonState) -> Dict[str, Any]:
    natural_fighter_map = {
        "grassland": ("Cotton Spore", "target"),
        "forest": ("Grass Whistle", "target"),
        "wetlands": ("Mud-Slap", "target"),
        "ocean": ("Aqua Ring", "self"),
        "tundra": ("Haze", "self"),
        "mountain": ("Smack Down", "target"),
        "cave": ("Astonish", "target"),
        "urban": ("Fling", "target"),
        "desert": ("Sand Attack", "target"),
    }
    def _combatant_name(target_id: str) -> str:
        target = battle.pokemon.get(target_id)
        if target is None:
            return target_id
        return str(target.spec.name or target.spec.species or target_id)

    def _target_distance(target_id: str) -> Optional[int]:
        target = battle.pokemon.get(target_id)
        if state.position is None or target is None or target.position is None or target.fainted:
            return None
        return battle._combatant_distance(state, target)

    def _within(target_id: str, max_distance: int) -> bool:
        distance = _target_distance(target_id)
        return distance is not None and distance <= max_distance

    def _can_use_follow_up_move(move_name: str, target_id: str) -> bool:
        try:
            UseMoveAction(actor_id=actor_id, move_name=move_name, target_id=target_id).validate(battle)
        except Exception:
            return False
        return True

    def _enemy_targets_within(max_distance: int) -> List[str]:
        if state.position is None:
            return []
        targets: List[str] = []
        state_team = battle._team_for(actor_id)
        for pid, other in battle.pokemon.items():
            if other.fainted or other.position is None:
                continue
            if other is state:
                continue
            if state_team and battle._team_for(pid) == state_team:
                continue
            if battle._combatant_distance(state, other) <= max_distance:
                targets.append(pid)
        return sorted(targets)

    social_moves = sorted(
        {
            str(move.name or "").strip()
            for move in state.spec.moves
            if str(move.name or "").strip() and "social" in {str(k).strip().lower() for k in (move.keywords or [])}
        }
    )
    trainer = battle.trainers.get(state.controller_id)
    trainer_ap = int(getattr(trainer, "ap", 0) or 0)
    flight_speed = None
    flight_active = False
    telepath_active = state.has_capability("Telepath") or state.has_capability("Telepathy")
    thought_detection_uses = battle._feature_scene_use_count(state, "Thought Detection")
    psionic_analysis_uses = battle._feature_scene_use_count(state, "Psionic Analysis")
    psionic_sponge_uses = battle._feature_scene_use_count(state, "Psionic Sponge")
    force_of_will_uses = battle._feature_scene_use_count(state, "Force of Will")
    trapper_uses = battle._feature_scene_use_count(state, "Trapper")
    adaptive_geography_uses = battle._feature_scene_use_count(state, "Adaptive Geography")
    suggestion_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, other in battle.pokemon.items()
        if pid != actor_id and other.active and not other.fainted
    ]
    psionic_analysis_targets = _visible_psychic_residue(battle, actor_id)
    adaptive_aliases = [
        str(entry.get("terrain") or "").strip().title()
        for entry in state.get_temporary_effects("terrain_alias")
        if str(entry.get("feature") or "").strip().lower() == "adaptive geography"
    ]
    suggestion_bound = next(
        (
            entry for entry in state.get_temporary_effects("feature_bound")
            if str(entry.get("feature") or "").strip().lower() == "suggestion"
        ),
        None,
    )
    suggestion_bound_target_id = str((suggestion_bound or {}).get("target_id") or "").strip() or None
    effective_weather_name = battle.effective_weather_for_actor(state) if hasattr(battle, "effective_weather_for_actor") else None
    effective_weather_source = None
    if state.get_temporary_effects("polar_vortex_hail"):
        effective_weather_source = "Polar Vortex"
    elif state.get_temporary_effects("arctic_zeal_hail"):
        source_entry = next(iter(state.get_temporary_effects("arctic_zeal_hail")), None)
        source_move = str((source_entry or {}).get("source_move") or "").strip()
        effective_weather_source = f"Arctic Zeal ({source_move})" if source_move else "Arctic Zeal"
    elif state.position is not None and getattr(battle, "_tile_has_frozen_domain", None) and battle._tile_has_frozen_domain(state.position):
        effective_weather_source = "Frozen Domain"
    if not effective_weather_source:
        effective_weather_name = None
    if state.has_trainer_feature("Flight"):
        trainer_skill = 0
        if trainer is not None:
            trainer_skill = max(trainer.skill_rank("acrobatics"), trainer.skill_rank("perception"))
        flight_speed = max(0, int(state.movement_speed("levitate") or 0) + int(trainer_skill))
        flight_active = any(
            str(entry.get("feature") or "").strip().lower() == "flight"
            and int(entry.get("round", -1) or -1) == battle.round
            for entry in state.get_temporary_effects("feature_round_marker")
        )
    play_fiddle_ready = []
    for entry in state.get_temporary_effects("play_them_like_a_fiddle_ready"):
        target_id = str(entry.get("target") or "").strip()
        move_name = str(entry.get("move") or "").strip()
        if not target_id or not move_name:
            continue
        target = battle.pokemon.get(target_id)
        if target is None or target.fainted:
            continue
        target_moves = []
        target_abilities = []
        disabled_moves = {
            str(status.get("move") or status.get("move_name") or "").strip().lower()
            for status in target.statuses
            if isinstance(status, dict) and str(status.get("name") or "").strip().lower() == "disabled"
        }
        target_moves = sorted(
            move_name
            for move_name in battle._moves_used_this_scene(target_id)
            if move_name.strip().lower() not in disabled_moves
        )
        disabled_abilities = {
            str(effect.get("ability") or "").strip().lower()
            for effect in target.get_temporary_effects("ability_disabled")
            if isinstance(effect, dict)
        }
        target_abilities = sorted(
            ability
            for ability in target.ability_names()
            if ability.strip().lower() not in disabled_abilities
        )
        play_fiddle_ready.append(
            {
                "target": target_id,
                "target_name": _combatant_name(target_id),
                "move": move_name,
                "target_moves": target_moves,
                "target_abilities": target_abilities,
            }
        )
    quick_wit_options = []
    for target_id in _enemy_targets_within(6):
        tricks = [
            trick
            for trick in ("Bon Mot", "Flirt", "Terrorize")
            if not battle._manipulate_used(state, target_id, trick.lower())
        ]
        if tricks:
            quick_wit_options.append({"target": target_id, "target_name": _combatant_name(target_id), "tricks": tricks})
    trickster_ready = []
    for entry in state.get_temporary_effects("trickster_ready"):
        target_id = str(entry.get("target") or "").strip()
        if not target_id:
            continue
        distance = _target_distance(target_id)
        manipulate = [
            trick
            for trick in ("Bon Mot", "Flirt", "Terrorize")
            if distance is not None and distance <= 6 and not battle._manipulate_used(state, target_id, trick.lower())
        ]
        dirty_trick = [
            trick
            for trick, key in (("Hinder", "hinder"), ("Blind", "blind"), ("Low Blow", "low_blow"))
            if distance is not None and distance <= 1 and not battle._dirty_trick_used(state, target_id, key)
        ]
        if manipulate or dirty_trick:
            trickster_ready.append(
                {
                    "target": target_id,
                    "target_name": _combatant_name(target_id),
                    "manipulate": manipulate,
                    "dirty_trick": dirty_trick,
                }
            )
    sleight_options = []
    if state.has_trainer_feature("Sleight"):
        for entry in battle._out_of_turn_move_options(actor_id):
            move_name = str(entry.get("move") or "").strip()
            if not move_name:
                continue
            move = next((mv for mv in state.spec.moves if str(mv.name or "").strip() == move_name), None)
            if move is None or str(move.category or "").strip().lower() != "status":
                continue
            sleight_options.append(entry)
    shell_game_options = battle._shell_game_hazard_options(actor_id) if state.has_trainer_feature("Shell Game") else []
    shell_game_uses_left = max(0, 2 - battle._feature_scene_use_count(state, "Shell Game"))
    dirty_fighting_options = []
    for target_id in sorted(
        {
            str(entry.get("target") or "").strip()
            for entry in state.get_temporary_effects("dirty_fighting_ready")
            if str(entry.get("target") or "").strip()
        }
    ):
        distance = _target_distance(target_id)
        tricks = [
            trick
            for trick, key in (("Hinder", "hinder"), ("Blind", "blind"), ("Low Blow", "low_blow"))
            if distance is not None and distance <= 1 and not battle._dirty_trick_used(state, target_id, key)
        ]
        if tricks:
            dirty_fighting_options.append({"target": target_id, "target_name": _combatant_name(target_id), "tricks": tricks})
    weapon_finesse_targets = sorted(
        {
            str(entry.get("target") or "").strip()
            for entry in state.get_temporary_effects("weapon_finesse_ready")
            if str(entry.get("target") or "").strip()
            and _within(str(entry.get("target") or "").strip(), 1)
        }
    )
    weapon_finesse_target_options = [
        {"target": target_id, "target_name": _combatant_name(target_id)}
        for target_id in weapon_finesse_targets
    ]
    psychic_resonance_targets = sorted(
        {
            str(entry.get("target") or "").strip()
            for entry in state.get_temporary_effects("psychic_resonance_ready")
            if str(entry.get("target") or "").strip()
            and _can_use_follow_up_move("Encore", str(entry.get("target") or "").strip())
        }
    )
    psychic_resonance_target_options = [
        {"target": target_id, "target_name": _combatant_name(target_id)}
        for target_id in psychic_resonance_targets
    ]
    enchanting_gaze_anchor_options = [
        {"target": target_id, "target_name": _combatant_name(target_id)}
        for target_id in _enemy_targets_within(2)
    ]
    quick_switch_replacements = [
        {"target": replacement_id, "target_name": _combatant_name(replacement_id)}
        for replacement_id in battle._quick_switch_replacements(actor_id)
    ]
    quick_switch_ap_cost = 1 if state.has_trainer_feature("Juggler") else 2
    emergency_release_targets = [
        {"target": replacement_id, "target_name": _combatant_name(replacement_id)}
        for replacement_id in battle._emergency_release_replacements(actor_id)
    ]
    bounce_shot_targets = list(emergency_release_targets)
    capture_ball_items = [
        {"index": idx, "item": _item_name_text(item)}
        for idx, item in enumerate(state.spec.items if isinstance(state.spec.items, list) else [])
        if _is_capture_ball_name(_item_name_text(item))
    ]
    capture_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and mon.active
        and not mon.fainted
        and battle._team_for(pid) != battle._team_for(actor_id)
    ]
    captured_momentum_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
    ]
    captured_momentum_ready = bool(state.get_temporary_effects("captured_momentum_ready"))
    devitalizing_throw_ready = bool(state.get_temporary_effects("devitalizing_throw_ready"))
    catch_combo_ready = bool(state.get_temporary_effects("catch_combo_ready"))
    relentless_pursuit_pokemon = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.is_trainer_combatant()
    ]
    relentless_pursuit_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) != battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
    ]
    ambient_aura_blessing = next(iter(state.get_temporary_effects("ambient_aura_blessing")), None)
    ambient_aura_barrier_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if mon.active
        and not mon.fainted
        and battle._team_for(pid) == battle._team_for(actor_id)
        and (
            state.position is None
            or mon.position is None
            or battle._combatant_distance(state, mon) <= 5
        )
    ]
    psionic_sponge_range = max(
        battle._combatant_skill_rank(state, "focus", trainer_override_id=state.controller_id),
        battle._combatant_skill_rank(state, "occult education", trainer_override_id=state.controller_id),
    )
    psionic_sponge_sources = []
    if state.position is not None:
        existing_move_names = {str(move.name or "").strip().lower() for move in state.spec.moves}
        for pid, mon in battle.pokemon.items():
            if pid == actor_id or not mon.active or mon.fainted or mon.position is None:
                continue
            if battle._team_for(pid) != battle._team_for(actor_id):
                continue
            if battle._combatant_distance(state, mon) > psionic_sponge_range:
                continue
            move_options = []
            seen_moves = set()
            for move in mon.spec.moves:
                move_name = str(move.name or "").strip()
                normalized = move_name.lower()
                if not move_name or normalized in seen_moves or normalized in existing_move_names:
                    continue
                if str(move.type or "").strip().lower() != "psychic":
                    continue
                seen_moves.add(normalized)
                move_options.append({"move": move_name, "move_name": move_name})
            if move_options:
                psionic_sponge_sources.append(
                    {
                        "target": pid,
                        "target_name": _combatant_name(pid),
                        "moves": sorted(move_options, key=lambda entry: entry["move_name"]),
                    }
                )
    psionic_sponge_borrowed_moves = sorted(
        {
            str(entry.get("name") or "").strip()
            for entry in state.get_temporary_effects("psionic_sponge_move")
            if str(entry.get("name") or "").strip()
        }
    )
    mindbreak_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and "psychic" in {str(t or "").strip().lower() for t in mon.spec.types}
    ]
    arctic_zeal_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) != battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and (
            state.position is None
            or mon.position is None
            or battle._combatant_distance(state, mon) <= 5
        )
    ]
    arctic_zeal_charges = battle._arctic_zeal_blessing_charges(state) if hasattr(battle, "_arctic_zeal_blessing_charges") else 0
    polar_vortex_active = bool(state.get_temporary_effects("polar_vortex_hail"))
    polar_vortex_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.get_temporary_effects("polar_vortex_hail")
    ]
    polar_vortex_bound_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if mon.get_temporary_effects("polar_vortex_hail")
        and battle._team_for(pid) == battle._team_for(actor_id)
    ]
    tough_as_schist_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and "rock" in {str(t or "").strip().lower() for t in mon.spec.types}
    ]
    tough_as_schist_bound_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if any(
            str(entry.get("kind") or "").strip().lower() == "tough_as_schist_bound"
            and str(entry.get("source_id") or "").strip() == actor_id
            for entry in mon.get_temporary_effects("tough_as_schist_bound")
        )
    ]
    mindbreak_bound_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if any(
            str(entry.get("kind") or "").strip().lower() == "mindbreak_bound"
            and str(entry.get("source_id") or "").strip() == actor_id
            for entry in mon.get_temporary_effects("mindbreak_bound")
        )
    ]
    psionic_overload_ready = next(iter(state.get_temporary_effects("psionic_overload_ready")), None)
    psionic_overload_move = str((psionic_overload_ready or {}).get("move") or "").strip() or None
    psionic_overload_target = str((psionic_overload_ready or {}).get("target_id") or "").strip() or None
    psionic_overload_barrier_tiles = [
        {"x": coord[0], "y": coord[1], "tile": [coord[0], coord[1]]}
        for coord in battle._psionic_overload_barrier_tiles(state)
    ] if psionic_overload_move and psionic_overload_move.lower() == "barrier" else []
    force_of_will_ready = next(iter(state.get_temporary_effects("force_of_will_ready")), None)
    force_of_will_moves = [
        {"move": name, "move_name": name}
        for name in battle._force_of_will_move_options(
            state,
            trigger_move_name=str((force_of_will_ready or {}).get("trigger_move") or ""),
        )
    ] if force_of_will_ready else []
    ghost_step_ready = bool(
        state.has_trainer_feature("Ghost Step")
        and state.position is not None
        and "ghost" in {str(token or "").strip().lower() for token in state.spec.types}
        and battle._feature_scene_use_count(state, "Ghost Step") < 1
        and not state.get_temporary_effects("ghost_step_pending")
    )
    boo_ready = bool(state.get_temporary_effects("boo_ready"))
    boo_uses = battle._feature_scene_use_count(state, "Boo!")
    staying_power_uses = battle._feature_scene_use_count(state, "Staying Power")
    staying_power_ready = bool(
        state.has_trainer_feature("Staying Power")
        and staying_power_uses < 1
    )
    brutal_training_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.is_trainer_combatant()
    ]
    training_targets = [dict(entry) for entry in brutal_training_targets]
    trained_stat_options = [
        {"value": "atk", "label": "Attack"},
        {"value": "def", "label": "Defense"},
        {"value": "spatk", "label": "Special Attack"},
        {"value": "spdef", "label": "Special Defense"},
        {"value": "spd", "label": "Speed"},
    ]
    stat_training_moves = {
        "atk": [{"move": "Swords Dance"}, {"move": "Rage"}],
        "def": [{"move": "Iron Defense"}, {"move": "Reflect"}],
        "spatk": [{"move": "Nasty Plot"}, {"move": "Hidden Power"}],
        "spdef": [{"move": "Amnesia"}, {"move": "Light Screen"}],
        "spd": [{"move": "Agility"}, {"move": "After You"}],
    }
    stat_training_feature_names = [
        "Stat Training",
        "Attack Training",
        "Defense Training",
        "Special Attack Training",
        "Special Defense Training",
        "Speed Training",
    ]
    stat_feature_to_key = {
        "stat training": "",
        "attack training": "atk",
        "defense training": "def",
        "special attack training": "spatk",
        "special defense training": "spdef",
        "speed training": "spd",
        "stat stratagem": "",
        "attack stratagem": "atk",
        "defense stratagem": "def",
        "special attack stratagem": "spatk",
        "special defense stratagem": "spdef",
        "speed stratagem": "spd",
    }
    stat_training_options = []
    for feature in _trainer_feature_payloads(state, stat_training_feature_names):
        feature_name = str(feature.get("name") or "").strip()
        stat_key = str(feature.get("chosen_stat") or stat_feature_to_key.get(feature_name.lower(), "")).strip().lower()
        if not stat_key:
            continue
        move_options = stat_training_moves.get(stat_key, [])
        for entry in training_targets:
            target = battle.pokemon.get(str(entry.get("target") or ""))
            if target is None:
                continue
            legal_moves = [
                option["move"]
                for option in move_options
                if all(str(move.name or "").strip().lower() != str(option["move"]).strip().lower() for move in target.spec.moves)
            ]
            if not legal_moves:
                continue
            stat_training_options.append(
                {
                    "feature": feature_name,
                    "stat": stat_key,
                    "stat_label": _item_stat_label(stat_key),
                    "target": entry["target"],
                    "target_name": entry["target_name"],
                    "moves": [{"move": move_name, "move_name": move_name} for move_name in legal_moves],
                }
            )
    stat_training_ready = bool(stat_training_options)
    stat_stratagem_feature_names = [
        "Stat Stratagem",
        "Attack Stratagem",
        "Defense Stratagem",
        "Special Attack Stratagem",
        "Special Defense Stratagem",
        "Speed Stratagem",
    ]
    stat_stratagem_options = []
    if trainer_ap >= 2:
        for feature in _trainer_feature_payloads(state, stat_stratagem_feature_names):
            feature_name = str(feature.get("name") or "").strip()
            stat_key = str(feature.get("chosen_stat") or stat_feature_to_key.get(feature_name.lower(), "")).strip().lower()
            if not stat_key:
                continue
            for entry in training_targets:
                stat_stratagem_options.append(
                    {
                        "feature": feature_name,
                        "stat": stat_key,
                        "stat_label": _item_stat_label(stat_key),
                        "target": entry["target"],
                        "target_name": entry["target_name"],
                    }
                )
    stat_stratagem_ready = bool(stat_stratagem_options)
    ace_trainer_ready = bool(state.has_trainer_feature("Ace Trainer") and trainer is not None and trainer.ap >= 1 and training_targets)
    champ_in_the_making = bool(state.has_trainer_feature("Champ in the Making"))
    agility_training_ready = bool(state.has_trainer_feature("Agility Training") and training_targets)
    brutal_training_ready = bool(state.has_trainer_feature("Brutal Training") and brutal_training_targets)
    focused_training_ready = bool(state.has_trainer_feature("Focused Training") and training_targets)
    inspired_training_ready = bool(state.has_trainer_feature("Inspired Training") and training_targets)
    duelist_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and mon.active
        and not mon.fainted
        and battle._team_for(pid) != battle._team_for(actor_id)
    ]
    duelist_ready = bool(state.has_trainer_feature("Duelist") and duelist_targets)
    effective_methods_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not bool((getattr(mon.spec, "poke_edge_choices", {}) or {}).get("effective_methods"))
    ]
    effective_methods_ready = bool(state.has_trainer_feature("Effective Methods") and effective_methods_targets)
    expend_momentum_targets = []
    for pid, mon in battle.pokemon.items():
        if pid == actor_id or battle._team_for(pid) != battle._team_for(actor_id):
            continue
        if mon.fainted or mon.is_trainer_combatant() or not mon.get_temporary_effects("focused_training"):
            continue
        momentum = battle._duelist_momentum(mon)
        if momentum <= 0:
            continue
        usage = battle.frequency_usage.get(pid, {})
        eot_moves = [
            {"move": move.name, "move_name": move.name}
            for move in mon.spec.moves
            if str(move.freq or "").strip().lower() == "eot" and usage.get(move.name, 0) > 0
        ]
        scene_moves = [
            {"move": move.name, "move_name": move.name}
            for move in mon.spec.moves
            if str(move.freq or "").strip().lower().startswith("scene") and usage.get(move.name, 0) > 0
        ]
        expend_momentum_targets.append(
            {
                "target": pid,
                "target_name": _combatant_name(pid),
                "momentum": momentum,
                "eot_moves": eot_moves,
                "scene_moves": scene_moves,
            }
        )
    expend_momentum_ready = bool(state.has_trainer_feature("Expend Momentum") and expend_momentum_targets)
    duelists_manual_targets = [
        dict(entry)
        for entry in expend_momentum_targets
        if int(entry.get("momentum", 0) or 0) >= 1
    ]
    duelists_manual_ready = bool(
        (state.has_trainer_feature("Duelist's Manual") or state.has_trainer_feature("Duelist’s Manual"))
        and trainer_ap >= 2
        and duelists_manual_targets
    )
    seize_the_moment_targets = []
    if state.has_trainer_feature("Seize The Moment") or state.has_trainer_feature("Seize the Moment"):
        ready = bool(state.get_temporary_effects("seize_the_moment_ready"))
        if ready:
            moves = [{"move": move.name, "move_name": move.name} for move in state.spec.moves if str(move.name or "").strip()]
            for pid, mon in battle.pokemon.items():
                if pid != actor_id and mon.active and not mon.fainted and battle._is_duelist_tagged_for(mon, state):
                    seize_the_moment_targets.append({"target": pid, "target_name": _combatant_name(pid), "moves": moves})
    seize_the_moment_ready = bool(seize_the_moment_targets)
    taskmaster_ready = bool(state.has_trainer_feature("Taskmaster") and state.has_trainer_feature("Brutal Training") and brutal_training_targets)
    press_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.is_trainer_combatant()
    ]
    press_ready = bool(state.has_trainer_feature("Press") and press_targets)
    focused_command_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.is_trainer_combatant()
    ]
    focused_command_pairs = []
    seen_focused_pairs: set[tuple[str, str]] = set()
    for pid, mon in battle.pokemon.items():
        if battle._team_for(pid) != battle._team_for(actor_id):
            continue
        if mon.is_trainer_combatant():
            continue
        for entry in mon.get_temporary_effects("focused_command_pair"):
            if int(entry.get("round", -1) or -1) != battle.round:
                continue
            partner_id = str(entry.get("partner_id") or "").strip()
            if not partner_id:
                continue
            key = (pid, partner_id)
            if key in seen_focused_pairs:
                continue
            seen_focused_pairs.add(key)
            focused_command_pairs.append(
                {
                    "target": pid,
                    "target_name": _combatant_name(pid),
                    "partner": partner_id,
                    "partner_name": _combatant_name(partner_id),
                    "lift_frequency": bool(entry.get("lift_frequency")),
                    "lift_damage": bool(entry.get("lift_damage")),
                }
            )
    focused_command_ready = bool(
        state.has_trainer_feature("Focused Command")
        and len(focused_command_targets) >= 2
        and trainer is not None
        and trainer.has_action_available(BattleState.ActionType.SWIFT)
    )
    commanders_voice_orders = []
    target_orders = []
    if trainer is not None:
        target_orders = [
            {"order": order_name, "order_name": order_name.title()}
            for order_name in battle._supported_target_orders_for(state)
            if battle._order_available_for_use(state, trainer, order_name)
        ]
        commanders_voice_orders = list(target_orders)
    commanders_voice_ready = bool(
        state.has_trainer_feature("Commander's Voice")
        and (
            bool(commanders_voice_orders)
            or (
                state.has_trainer_feature("Focused Command")
                and len(focused_command_targets) >= 2
            )
        )
    )
    order_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid in battle._order_target_candidates(
            actor_id,
            allow_team_allies=state.has_trainer_feature("Leadership"),
        )
    ]
    tip_the_scales_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid in battle._order_target_candidates(
            actor_id,
            allow_team_allies=True,
            range_limit=10,
        )
    ]
    at_will_orders = [
        {"order": order_name, "order_name": order_name.title()}
        for order_name in battle._supported_target_orders_for(state)
        if trainer is not None
        and battle._order_available_for_use(state, trainer, order_name)
        and SUPPORTED_TARGET_ORDER_SPECS.get(order_name, {}).get("scene_limit") is None
    ]
    scene_orders = [
        {"order": order_name, "order_name": order_name.title()}
        for order_name in battle._supported_target_orders_for(state)
        if trainer is not None
        and battle._order_available_for_use(state, trainer, order_name)
        and SUPPORTED_TARGET_ORDER_SPECS.get(order_name, {}).get("scene_limit") is not None
    ]
    battle_conductor_ready = bool(
        state.has_trainer_feature("Battle Conductor")
        and len(order_targets) >= 2
        and at_will_orders
    )
    mobilize_ready = bool(state.has_trainer_feature("Mobilize") and order_targets)
    scheme_twist_ready = bool(
        state.has_trainer_feature("Scheme Twist")
        and len(order_targets) >= 2
        and scene_orders
    )
    tip_the_scales_ready = bool(
        state.has_trainer_feature("Tip the Scales")
        and trainer is not None
        and trainer.ap >= 2
        and at_will_orders
        and tip_the_scales_targets
    )
    complex_orders_ready = bool(
        state.has_trainer_feature("Complex Orders")
        and len(order_targets) >= 2
        and len(commanders_voice_orders) >= 2
    )
    quick_healing_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "injuries": int(mon.injuries or 0),
            "hardened": bool(mon.is_hardened()),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and mon.is_hardened()
        and int(mon.injuries or 0) > 0
    ]
    quick_healing_ready = bool(state.has_trainer_feature("Quick Healing") and quick_healing_targets)
    savage_strike_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not mon.has_ability("Cruelty")
    ]
    savage_strike_ready = bool(state.has_trainer_feature("Savage Strike") and savage_strike_targets)
    signature_technique_targets = []
    if state.has_trainer_feature("Signature Technique"):
        for pid, mon in battle.pokemon.items():
            if pid == actor_id:
                continue
            if battle._team_for(pid) != battle._team_for(actor_id):
                continue
            if mon.fainted or mon.is_trainer_combatant():
                continue
            existing_signature = (getattr(mon.spec, "poke_edge_choices", {}) or {}).get("signature_technique")
            replacing = bool(existing_signature)
            available_tp = int(getattr(mon.spec, "tutor_points", 0) or 0) + (1 if replacing else 0)
            if available_tp < 2:
                continue
            move_options = _signature_technique_options_for_target(state, mon)
            if not move_options:
                continue
            signature_technique_targets.append(
                {
                    "target": pid,
                    "target_name": _combatant_name(pid),
                    "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
                    "replacement_refund": 1 if replacing else 0,
                    "current": existing_signature if isinstance(existing_signature, dict) else None,
                    "moves": move_options,
                }
            )
    signature_technique_ready = bool(state.has_trainer_feature("Signature Technique") and signature_technique_targets)
    cheerleader_playtest_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not mon.has_ability("Friend Guard")
    ]
    cheerleader_playtest_ready = bool(
        state.has_trainer_feature("Cheerleader [Playtest]") and cheerleader_playtest_targets
    )
    cheer_brigade_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not mon.has_ability("Friend Guard")
    ]
    cheer_brigade_ready = bool(state.has_trainer_feature("Cheer Brigade") and cheer_brigade_targets)
    mounted_partner_id = battle._mounted_partner_id(actor_id) if hasattr(battle, "_mounted_partner_id") else None
    mounted_mount_id = battle._mounted_mount_id(actor_id) if hasattr(battle, "_mounted_mount_id") else None
    mounted_rider_id = battle._mounted_rider_id(actor_id) if hasattr(battle, "_mounted_rider_id") else None
    mount_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and state.position is not None
        and mon.position is not None
        and battle._combatant_distance(state, mon) <= 1
        and not battle._is_mounted_actor(actor_id)
        and not battle._is_mounted_actor(pid)
    ] if hasattr(battle, "_is_mounted_actor") else []
    dismount_positions = [
        {"tile": [coord[0], coord[1]], "x": coord[0], "y": coord[1]}
        for coord in (battle._mounted_dismount_positions(actor_id) if hasattr(battle, "_mounted_dismount_positions") else [])
    ]
    ride_as_one_swap_ready = bool(
        state.has_trainer_feature("Ride as One")
        and hasattr(battle, "_ride_as_one_slot_swap_available")
        and battle._ride_as_one_slot_swap_available(actor_id)
    )
    conquerors_march_ready = bool(
        state.has_trainer_feature("Conqueror's March")
        and mounted_mount_id
        and (mount_state := battle.pokemon.get(mounted_mount_id)) is not None
        and mount_state.active
        and not mount_state.fainted
        and mount_state.has_ability("Run Up")
    )
    ramming_speed_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not mon.has_ability("Run Up")
        and not bool((getattr(mon.spec, "poke_edge_choices", {}) or {}).get("ramming_speed"))
    ]
    ramming_speed_ready = bool(state.has_trainer_feature("Ramming Speed") and ramming_speed_targets)
    vim_and_vigor_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not mon.has_ability("Vigor")
        and not bool((getattr(mon.spec, "poke_edge_choices", {}) or {}).get("vim_and_vigor"))
    ]
    vim_and_vigor_ready = bool(state.has_trainer_feature("Vim and Vigor") and vim_and_vigor_targets)
    type_ace_options = []
    for feature in _trainer_feature_payloads(state, ["Type Ace"]):
        chosen_type = str(feature.get("chosen_type") or "").strip().lower()
        if not chosen_type:
            continue
        for pid, mon in battle.pokemon.items():
            if pid == actor_id or battle._team_for(pid) != battle._team_for(actor_id):
                continue
            if mon.fainted or mon.is_trainer_combatant():
                continue
            if int(getattr(mon.spec, "tutor_points", 0) or 0) < 2:
                continue
            if bool((getattr(mon.spec, "poke_edge_choices", {}) or {}).get("type_ace")):
                continue
            ability_options = [
                {"mode": "strategist", "label": f"{_type_label(chosen_type)} Strategist"},
                {"mode": "last_chance", "label": _type_label(chosen_type) + " Surge"},
            ]
            type_ace_options.append(
                {
                    "feature": "Type Ace",
                    "chosen_type": chosen_type,
                    "type_label": _type_label(chosen_type),
                    "target": pid,
                    "target_name": _combatant_name(pid),
                    "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
                    "ability_options": ability_options,
                }
            )
    type_ace_ready = bool(type_ace_options)
    type_refresh_options = []
    if trainer_ap >= 2:
        for feature in _trainer_feature_payloads(state, ["Type Refresh"]):
            chosen_type = str(feature.get("chosen_type") or "").strip().lower()
            if not chosen_type:
                continue
            for pid, mon in battle.pokemon.items():
                if pid == actor_id or battle._team_for(pid) != battle._team_for(actor_id):
                    continue
                if mon.fainted or mon.is_trainer_combatant():
                    continue
                if battle._feature_scene_use_count(mon, "Type Refresh") >= 1:
                    continue
                usage = battle.frequency_usage.get(pid, {})
                scene_moves = []
                eot_moves = []
                for move in mon.spec.moves:
                    if str(move.type or "").strip().lower() != chosen_type:
                        continue
                    if int(usage.get(move.name, 0) or 0) <= 0:
                        continue
                    definition = battle._effective_move_frequency_definition(mon, move)
                    if definition is None:
                        definition = battle._frequency_definition(move)
                    if definition is None:
                        continue
                    freq = str(definition.raw or "").strip().lower()
                    if freq == "eot":
                        eot_moves.append({"move": move.name, "move_name": move.name})
                    elif freq.startswith("scene"):
                        scene_moves.append({"move": move.name, "move_name": move.name})
                if not scene_moves and not eot_moves:
                    continue
                type_refresh_options.append(
                    {
                        "feature": "Type Refresh",
                        "chosen_type": chosen_type,
                        "type_label": _type_label(chosen_type),
                        "target": pid,
                        "target_name": _combatant_name(pid),
                        "scene_moves": scene_moves,
                        "eot_moves": eot_moves,
                    }
                )
    type_refresh_ready = bool(type_refresh_options)
    move_sync_options = []
    for feature in _trainer_feature_payloads(state, ["Move Sync"]):
        chosen_type = str(feature.get("chosen_type") or "").strip().lower()
        if not chosen_type:
            continue
        for pid, mon in battle.pokemon.items():
            if pid == actor_id or battle._team_for(pid) != battle._team_for(actor_id):
                continue
            if mon.fainted or mon.is_trainer_combatant():
                continue
            if int(getattr(mon.spec, "tutor_points", 0) or 0) < 1:
                continue
            move_options = [
                {
                    "move": move.name,
                    "move_name": move.name,
                    "current_type": str(move.type or "").strip(),
                }
                for move in mon.spec.moves
                if str(move.name or "").strip()
            ]
            if not move_options:
                continue
            move_sync_options.append(
                {
                    "feature": "Move Sync",
                    "chosen_type": chosen_type,
                    "type_label": _type_label(chosen_type),
                    "target": pid,
                    "target_name": _combatant_name(pid),
                    "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
                    "moves": move_options,
                }
            )
    move_sync_ready = bool(move_sync_options)
    extra_ordinary_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and "normal" in {str(token or "").strip().lower() for token in mon.spec.types}
        and not bool((getattr(mon.spec, "poke_edge_choices", {}) or {}).get("extra_ordinary"))
        and (
            mon.has_ability("Last Chance")
            or str((mon.ability_metadata("Type Strategist") or {}).get("chosen_type") or "").strip().lower() == "normal"
        )
        and not (
            mon.has_ability("Last Chance")
            and str((mon.ability_metadata("Type Strategist") or {}).get("chosen_type") or "").strip().lower() == "normal"
        )
    ]
    extra_ordinary_ready = bool(state.has_trainer_feature("Extra Ordinary") and extra_ordinary_targets)
    culinary_appreciation_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not bool((getattr(mon.spec, "poke_edge_choices", {}) or {}).get("culinary_appreciation"))
        and not mon.has_ability("Gluttony")
    ]
    culinary_appreciation_ready = bool(state.has_trainer_feature("Culinary Appreciation") and culinary_appreciation_targets)
    hits_the_spot_targets = []
    for entry in reversed(list(state.get_temporary_effects("hits_the_spot_ready"))):
        target_id = str(entry.get("target_id") or "").strip()
        if not target_id:
            continue
        target = battle.pokemon.get(target_id)
        if target is None or target.fainted or target.controller_id != state.controller_id:
            continue
        if any(existing.get("target") == target_id for existing in hits_the_spot_targets):
            continue
        hits_the_spot_targets.append(
            {
                "target": target_id,
                "target_name": str(entry.get("target_name") or _combatant_name(target_id)).strip() or _combatant_name(target_id),
            }
        )
    hits_the_spot_ready = bool(state.has_trainer_feature("Hits the Spot") and trainer_ap >= 1 and hits_the_spot_targets)
    complex_aftertaste_targets = []
    for entry in reversed(list(state.get_temporary_effects("complex_aftertaste_ready"))):
        target_id = str(entry.get("target_id") or "").strip()
        if not target_id:
            continue
        target = battle.pokemon.get(target_id)
        if target is None or target.fainted or target.controller_id != state.controller_id:
            continue
        taste = str(entry.get("taste") or "").strip().lower()
        key = (target_id, taste, str(entry.get("instance_id") or "").strip())
        if any(
            existing.get("target") == target_id
            and str(existing.get("taste") or "").strip().lower() == taste
            and str(existing.get("instance_id") or "").strip() == key[2]
            for existing in complex_aftertaste_targets
        ):
            continue
        complex_aftertaste_targets.append(
            {
                "target": target_id,
                "target_name": str(entry.get("target_name") or _combatant_name(target_id)).strip() or _combatant_name(target_id),
                "taste": taste,
                "taste_label": taste.title() if taste else "",
                "source_item": str(entry.get("source_item") or "").strip(),
                "instance_id": str(entry.get("instance_id") or "").strip(),
            }
        )
    complex_aftertaste_ready = bool(state.has_trainer_feature("Complex Aftertaste") and trainer_ap >= 1 and complex_aftertaste_targets)
    close_quarters_mastery_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and mon.active
    ]
    close_quarters_mastery_ready = bool(state.has_trainer_feature("Close Quarters Mastery") and close_quarters_mastery_targets)
    celerity_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "initiative_bonus": int(battle._type_linked_rank(state, "flying") or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and mon.active
        and (
            "flying" in {str(token or "").strip().lower() for token in mon.spec.types}
            or bool(mon.movement_speed("sky") or mon.movement_speed("levitate"))
        )
    ]
    celerity_ready = bool(state.has_trainer_feature("Celerity") and celerity_targets)
    foiling_foliage_options = []
    for pid, mon in battle.pokemon.items():
        if pid == actor_id or battle._team_for(pid) != battle._team_for(actor_id):
            continue
        if mon.fainted or mon.is_trainer_combatant():
            continue
        move_options = [
            {"move": move.name, "move_name": move.name}
            for move in mon.spec.moves
            if str(move.type or "").strip().lower() == "grass" and str(move.category or "").strip().lower() == "status"
        ]
        if not move_options:
            continue
        foiling_foliage_options.append(
            {
                "target": pid,
                "target_name": _combatant_name(pid),
                "moves": move_options,
                "current_move": str(((getattr(mon.spec, "poke_edge_choices", {}) or {}).get("foiling_foliage") or {}).get("move") or ""),
            }
        )
    foiling_foliage_ready = bool(state.has_trainer_feature("Foiling Foliage") and foiling_foliage_options)
    clever_ruse_options = []
    if state.has_trainer_feature("Clever Ruse") and not state.is_trainer_combatant() and not state.fainted and state.active:
        choice_pool = [
            ("evasion", "Gain +4 Evasion for 1 full round"),
            ("ignore_evasion", "Ignore Evasion from Stats until end of next turn"),
        ]
        if battle._best_disengage_destination(actor_id=actor_id, threat_id=None) is not None:
            choice_pool.append(("disengage", "Immediately Disengage"))
        for idx, (first_value, first_label) in enumerate(choice_pool):
            for second_value, second_label in choice_pool[idx + 1:]:
                clever_ruse_options.append(
                    {
                        "value": f"{first_value},{second_value}",
                        "label": f"{first_label} + {second_label}",
                        "choices": [first_value, second_value],
                    }
                )
    clever_ruse_triggered = bool(state.get_temporary_effects("clever_ruse_ready"))
    clever_ruse_ready = bool(
        clever_ruse_options
        and (
            clever_ruse_triggered
            or not any(int(entry.get("round", -1) or -1) == battle.round for entry in state.get_temporary_effects("feature_round_marker") if str(entry.get("feature") or "").strip().lower() == "clever ruse")
        )
    )
    fairy_lights_count = len(state.get_temporary_effects("fairy_lights")) if not state.is_trainer_combatant() else 0
    fairy_lights_positions = [
        [int(coord[0]), int(coord[1])]
        for coord in (
            entry.get("coord")
            for entry in state.get_temporary_effects("fairy_lights")
            if isinstance(entry.get("coord"), (list, tuple)) and len(entry.get("coord")) >= 2
        )
    ] if not state.is_trainer_combatant() else []
    fairy_lights_destination_options = []
    if (
        not state.is_trainer_combatant()
        and not state.fainted
        and state.active
        and state.position is not None
        and battle.grid is not None
    ):
        for x in range(int(battle.grid.width or 0)):
            for y in range(int(battle.grid.height or 0)):
                coord = (x, y)
                if targeting.chebyshev_distance(state.position, coord) > 6:
                    continue
                tile_info = battle.grid.tiles.get(coord, {})
                tile_type = str(tile_info.get("type", "") if isinstance(tile_info, dict) else tile_info).strip().lower()
                if coord in battle.grid.blockers or any(token in tile_type for token in ("wall", "blocker", "blocking", "void")):
                    continue
                fairy_lights_destination_options.append({"coord": [x, y], "label": f"({x}, {y})"})
    fairy_lights_ready = bool(
        state.has_trainer_feature("Fairy Lights")
        and not state.is_trainer_combatant()
        and not state.fainted
        and state.active
        and "fairy" in {str(token or "").strip().lower() for token in state.spec.types}
    )
    flood_options = []
    if state.has_trainer_feature("Flood!") and not state.is_trainer_combatant() and not state.fainted and state.active:
        for move in state.spec.moves:
            if str(move.type or "").strip().lower() != "water" or str(move.category or "").strip().lower() == "status":
                continue
            flood_options.append({"move": move.name, "move_name": move.name, "mode": "line", "mode_label": "Line 4"})
            flood_options.append({"move": move.name, "move_name": move.name, "mode": "close_blast", "mode_label": "Close Blast 2"})
    flood_ready = bool(flood_options)
    versatile_wardrobe_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "tutor_points": int(getattr(mon.spec, "tutor_points", 0) or 0),
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and int(getattr(mon.spec, "tutor_points", 0) or 0) >= 2
        and not mon.is_chic()
    ]
    versatile_wardrobe_ready = bool(state.has_trainer_feature("Versatile Wardrobe") and versatile_wardrobe_targets)
    wardrobe_slots = _wardrobe_slots(state.spec)
    wardrobe_active_items = [
        {"index": idx, "item": _item_name_text(item)}
        for idx, item in enumerate(state.spec.items if isinstance(state.spec.items, list) else [])
        if _item_name_text(item)
    ]
    wardrobe_stored_items = [
        {"index": idx, "item": _item_name_text(item)}
        for idx, item in enumerate(wardrobe_slots)
        if _item_name_text(item)
    ]
    wardrobe_swap_ready = bool(state.is_chic() and wardrobe_active_items and wardrobe_stored_items)
    dress_to_impress_targets = [
        {
            "target": pid,
            "target_name": _combatant_name(pid),
            "items": [_item_name_text(item) for item in _wardrobe_slots(mon.spec) if _item_name_text(item)],
        }
        for pid, mon in battle.pokemon.items()
        if pid != actor_id
        and battle._team_for(pid) == battle._team_for(actor_id)
        and mon.active
        and not mon.fainted
        and not mon.is_trainer_combatant()
        and mon.is_chic()
        and any(_item_name_text(item) for item in _wardrobe_slots(mon.spec))
        and battle._feature_scene_use_count(mon, f"Dress to Impress:{pid}") < 1
    ]
    dress_to_impress_ready = bool(
        state.has_trainer_feature("Dress to Impress")
        and battle._feature_scene_use_count(state, "Dress to Impress") < 2
        and dress_to_impress_targets
    )
    dashing_makeover_bound = battle._current_dashing_makeover_binding(actor_id, state.controller_id)
    dashing_makeover_targets = []
    if state.has_trainer_feature("Dashing Makeover") and not dashing_makeover_bound:
        for pid, mon in battle.pokemon.items():
            if battle._team_for(pid) != battle._team_for(actor_id):
                continue
            if mon.fainted:
                continue
            item_options = _dashing_makeover_item_options_for_target(mon)
            if not item_options:
                continue
            dashing_makeover_targets.append(
                {
                    "target": pid,
                    "target_name": _combatant_name(pid),
                    "is_trainer": mon.is_trainer_combatant(),
                    "items": item_options,
                }
            )
    dashing_makeover_ready = bool(
        state.has_trainer_feature("Dashing Makeover")
        and trainer_ap >= 2
        and not dashing_makeover_bound
        and dashing_makeover_targets
    )
    moment_of_action_targets = [
        {
            "target": trainer_id,
            "target_name": str(getattr(target_trainer, "name", "") or trainer_id),
            "team": str(getattr(target_trainer, "team", "") or ""),
        }
        for trainer_id, target_trainer in battle.trainers.items()
        if target_trainer is not None
        and (
            not battle._team_for(actor_id)
            or str(getattr(target_trainer, "team", "") or "").strip().lower() == battle._team_for(actor_id)
        )
    ]
    moment_of_action_ready = bool(
        (
            state.has_trainer_feature("Moment of Action")
            or state.has_trainer_feature("Moment of Action [Playtest]")
        )
        and state.is_trainer_combatant()
        and bool(moment_of_action_targets)
    )
    go_fight_win_feature_name = (
        "Go, Fight, Win!" if state.has_trainer_feature("Go, Fight, Win!")
        else (
            "Go, Fight, Win! [Playtest]" if state.has_trainer_feature("Go, Fight, Win! [Playtest]")
            else ""
        )
    )
    go_fight_win_cheers = []
    if go_fight_win_feature_name:
        for value, label in (
            ("show_your_best", "Show Your Best!"),
            ("dont_stop_now", "Don't Stop Now!"),
            ("i_believe_in_you", "I Believe In You!"),
        ):
            scene_key = f"go, fight, win!:{label.lower()}"
            if battle._feature_scene_use_count(state, scene_key) >= 1:
                continue
            cheer_entry = {"value": value, "label": label}
            if value == "show_your_best":
                cheer_entry["stats"] = [
                    {"value": "def", "label": "Defense"},
                    {"value": "spdef", "label": "Special Defense"},
                ]
            go_fight_win_cheers.append(cheer_entry)
    go_fight_win_ready = bool(go_fight_win_feature_name and go_fight_win_cheers)
    shrug_off_ready = bool(
        state.has_trainer_feature("Shrug Off")
        and int(state.injuries or 0) > 0
        and battle._feature_daily_use_count(state, "Shrug Off") < 1
    )
    shocking_speed_move_options = [
        {"move": str(move.name or "").strip(), "move_name": str(move.name or "").strip()}
        for move in state.spec.moves
        if str(move.name or "").strip()
        and str(move.type or "").strip().lower() == "electric"
        and str(move.freq or "").strip().lower() in {"at-will", "at will"}
    ]
    shocking_speed_ready = bool(
        state.has_trainer_feature("Shocking Speed")
        and "electric" in {str(token or "").strip().lower() for token in state.spec.types}
        and battle._feature_scene_use_count(state, "Shocking Speed") < 2
        and shocking_speed_move_options
        and not state.get_temporary_effects("shocking_speed_ready")
    )
    quick_wit_uses = battle._feature_scene_use_count(state, "Quick Wit")
    play_them_like_a_fiddle_uses = battle._feature_scene_use_count(state, "Play Them Like a Fiddle")
    psychic_resonance_uses = battle._feature_scene_use_count(state, "Psychic Resonance")
    wilderness_guide_uses = battle._feature_scene_use_count(state, "Wilderness Guide")
    terrain_label = battle._current_terrain_label(state) if hasattr(battle, "_current_terrain_label") else ""
    natural_fighter_move, natural_fighter_target_mode = natural_fighter_map.get(str(terrain_label or "").strip().lower(), ("", ""))
    natural_fighter_targets = [
        {"target": pid, "target_name": _combatant_name(pid)}
        for pid in _enemy_targets_within(8)
    ] if natural_fighter_target_mode == "target" else []
    return {
        "trainer_ap": trainer_ap,
        "social_moves": social_moves,
        "flight_speed": flight_speed,
        "flight_active": flight_active,
        "flight_ap_ready": trainer_ap >= 1,
        "ghost_step_ready": ghost_step_ready,
        "ghost_step_uses_left": max(0, 1 - battle._feature_scene_use_count(state, "Ghost Step")),
        "ghost_step_destinations": [list(coord) for coord in movement.legal_shift_tiles(battle, actor_id)] if ghost_step_ready else [],
        "boo_ready": boo_ready,
        "boo_uses_left": max(0, 3 - boo_uses),
        "staying_power_ready": staying_power_ready,
        "staying_power_uses_left": max(0, 1 - staying_power_uses),
        "ace_trainer_ready": ace_trainer_ready,
        "ace_trainer_targets": training_targets,
        "ace_trainer_stat_options": trained_stat_options,
        "ace_trainer_stat_count": 2 if champ_in_the_making else 1,
        "agility_training_ready": agility_training_ready,
        "agility_training_targets": training_targets,
        "brutal_training_ready": brutal_training_ready,
        "brutal_training_targets": brutal_training_targets,
        "focused_training_ready": focused_training_ready,
        "focused_training_targets": training_targets,
        "inspired_training_ready": inspired_training_ready,
        "inspired_training_targets": training_targets,
        "stat_training_ready": stat_training_ready,
        "stat_training_options": stat_training_options,
        "stat_stratagem_ready": stat_stratagem_ready,
        "stat_stratagem_options": stat_stratagem_options,
        "duelist_ready": duelist_ready,
        "duelist_targets": duelist_targets,
        "effective_methods_ready": effective_methods_ready,
        "effective_methods_targets": effective_methods_targets,
        "expend_momentum_ready": expend_momentum_ready,
        "expend_momentum_targets": expend_momentum_targets,
        "duelists_manual_ready": duelists_manual_ready,
        "duelists_manual_ap_ready": trainer_ap >= 2,
        "duelists_manual_targets": duelists_manual_targets,
        "seize_the_moment_ready": seize_the_moment_ready,
        "seize_the_moment_targets": seize_the_moment_targets,
        "taskmaster_ready": taskmaster_ready,
        "press_ready": press_ready,
        "press_targets": press_targets,
        "focused_command_ready": focused_command_ready,
        "focused_command_targets": focused_command_targets,
        "focused_command_pairs": focused_command_pairs,
        "commanders_voice_ready": commanders_voice_ready,
        "commanders_voice_orders": commanders_voice_orders,
        "commanders_voice_focus_targets": focused_command_targets,
        "target_orders": target_orders,
        "order_targets": order_targets,
        "mobilize_ready": mobilize_ready,
        "battle_conductor_ready": battle_conductor_ready,
        "battle_conductor_orders": at_will_orders,
        "scheme_twist_ready": scheme_twist_ready,
        "scheme_twist_orders": scene_orders,
        "tip_the_scales_ready": tip_the_scales_ready,
        "tip_the_scales_orders": at_will_orders,
        "tip_the_scales_targets": tip_the_scales_targets,
        "complex_orders_ready": complex_orders_ready,
        "complex_orders_orders": commanders_voice_orders,
        "moment_of_action_ready": moment_of_action_ready,
        "moment_of_action_targets": moment_of_action_targets,
        "go_fight_win_ready": go_fight_win_ready,
        "go_fight_win_cheers": go_fight_win_cheers,
        "quick_healing_ready": quick_healing_ready,
        "quick_healing_targets": quick_healing_targets,
        "savage_strike_ready": savage_strike_ready,
        "savage_strike_targets": savage_strike_targets,
        "signature_technique_ready": signature_technique_ready,
        "signature_technique_targets": signature_technique_targets,
        "cheer_brigade_ready": cheer_brigade_ready,
        "cheer_brigade_targets": cheer_brigade_targets,
        "mounted_partner_id": mounted_partner_id,
        "mounted_mount_id": mounted_mount_id,
        "mounted_rider_id": mounted_rider_id,
        "mount_ready": bool(mount_targets),
        "mount_targets": mount_targets,
        "dismount_ready": bool(mounted_mount_id and dismount_positions),
        "dismount_positions": dismount_positions,
        "ride_as_one_swap_ready": ride_as_one_swap_ready,
        "conquerors_march_ready": conquerors_march_ready,
        "conquerors_march_target": mounted_mount_id,
        "ramming_speed_ready": ramming_speed_ready,
        "ramming_speed_targets": ramming_speed_targets,
        "type_ace_ready": type_ace_ready,
        "type_ace_options": type_ace_options,
        "type_refresh_ready": type_refresh_ready,
        "type_refresh_options": type_refresh_options,
        "move_sync_ready": move_sync_ready,
        "move_sync_options": move_sync_options,
        "extra_ordinary_ready": extra_ordinary_ready,
        "extra_ordinary_targets": extra_ordinary_targets,
        "culinary_appreciation_ready": culinary_appreciation_ready,
        "culinary_appreciation_targets": culinary_appreciation_targets,
        "hits_the_spot_ready": hits_the_spot_ready,
        "hits_the_spot_targets": hits_the_spot_targets,
        "complex_aftertaste_ready": complex_aftertaste_ready,
        "complex_aftertaste_targets": complex_aftertaste_targets,
        "close_quarters_mastery_ready": close_quarters_mastery_ready,
        "close_quarters_mastery_targets": close_quarters_mastery_targets,
        "celerity_ready": celerity_ready,
        "celerity_targets": celerity_targets,
        "foiling_foliage_ready": foiling_foliage_ready,
        "foiling_foliage_options": foiling_foliage_options,
        "clever_ruse_ready": clever_ruse_ready,
        "clever_ruse_triggered": clever_ruse_triggered,
        "clever_ruse_options": clever_ruse_options,
        "fairy_lights_ready": fairy_lights_ready,
        "fairy_lights_count": fairy_lights_count,
        "fairy_lights_positions": fairy_lights_positions,
        "fairy_lights_destination_options": fairy_lights_destination_options,
        "flood_ready": flood_ready,
        "flood_options": flood_options,
        "cheerleader_playtest_ready": cheerleader_playtest_ready,
        "cheerleader_playtest_targets": cheerleader_playtest_targets,
        "vim_and_vigor_ready": vim_and_vigor_ready,
        "vim_and_vigor_targets": vim_and_vigor_targets,
        "versatile_wardrobe_ready": versatile_wardrobe_ready,
        "versatile_wardrobe_targets": versatile_wardrobe_targets,
        "wardrobe_swap_ready": wardrobe_swap_ready,
        "wardrobe_swap_active_items": wardrobe_active_items,
        "wardrobe_swap_stored_items": wardrobe_stored_items,
        "dress_to_impress_ready": dress_to_impress_ready,
        "dress_to_impress_targets": dress_to_impress_targets,
        "dress_to_impress_uses_left": max(0, 2 - battle._feature_scene_use_count(state, "Dress to Impress")),
        "dashing_makeover_ready": dashing_makeover_ready,
        "dashing_makeover_ap_ready": trainer_ap >= 2,
        "dashing_makeover_targets": dashing_makeover_targets,
        "dashing_makeover_release_ready": bool(dashing_makeover_bound),
        "dashing_makeover_bound": dashing_makeover_bound,
        "emergency_release_ready": bool(state.has_trainer_feature("Emergency Release") and emergency_release_targets and trainer_ap >= 2),
        "emergency_release_ap_ready": trainer_ap >= 2,
        "emergency_release_targets": emergency_release_targets,
        "bounce_shot_ready": bool(state.has_trainer_feature("Bounce Shot") and bounce_shot_targets),
        "bounce_shot_targets": bounce_shot_targets,
        "capture_ball_items": capture_ball_items,
        "capture_targets": capture_targets,
        "fast_pitch_ready": bool(state.has_trainer_feature("Fast Pitch") and capture_ball_items and capture_targets and trainer_ap >= 1),
        "fast_pitch_ap_ready": trainer_ap >= 1,
        "gotta_catch_em_all_ready": bool(
            state.has_trainer_feature("Gotta Catch 'Em All")
            and battle._feature_scene_use_count(state, "Gotta Catch 'Em All") < 3
            and not state.get_temporary_effects("gotta_catch_em_all_ready")
        ),
        "gotta_catch_em_all_uses_left": max(0, 3 - battle._feature_scene_use_count(state, "Gotta Catch 'Em All")),
        "gotta_catch_em_all_primed": bool(state.get_temporary_effects("gotta_catch_em_all_ready")),
        "captured_momentum_ready": captured_momentum_ready,
        "captured_momentum_targets": captured_momentum_targets,
        "devitalizing_throw_ready": devitalizing_throw_ready,
        "devitalizing_throw_stat_options": [
            {"value": "atk", "label": "Attack"},
            {"value": "def", "label": "Defense"},
            {"value": "spatk", "label": "Special Attack"},
            {"value": "spdef", "label": "Special Defense"},
            {"value": "spd", "label": "Speed"},
        ],
        "catch_combo_ready": catch_combo_ready,
        "catch_combo_uses_left": max(0, 1 - battle._feature_scene_use_count(state, "Catch Combo")),
        "relentless_pursuit_ready": bool(
            state.has_trainer_feature("Relentless Pursuit")
            and trainer_ap >= 2
            and relentless_pursuit_pokemon
            and relentless_pursuit_targets
        ),
        "relentless_pursuit_ap_ready": trainer_ap >= 2,
        "relentless_pursuit_pokemon": relentless_pursuit_pokemon,
        "relentless_pursuit_targets": relentless_pursuit_targets,
        "shrug_off_ready": shrug_off_ready,
        "shrug_off_uses_left": max(0, 1 - battle._feature_daily_use_count(state, "Shrug Off")),
        "shocking_speed_ready": shocking_speed_ready,
        "shocking_speed_uses_left": max(0, 2 - battle._feature_scene_use_count(state, "Shocking Speed")),
        "shocking_speed_moves": shocking_speed_move_options,
        "telepath_active": telepath_active,
        "telepath_ap_ready": trainer_ap >= 2,
        "ambient_aura_ready": bool(ambient_aura_blessing),
        "ambient_aura_blessing_move": str((ambient_aura_blessing or {}).get("move") or "").strip() or None,
        "ambient_aura_barrier_targets": ambient_aura_barrier_targets,
        "ambient_aura_can_cure": any(
            state._normalized_status_name(status) in {
                "confused", "flinch", "flinched", "rage", "enraged", "trapped", "slowed",
                "vulnerable", "blinded", "hindered", "bad sleep", "infatuated", "suppressed",
                "disabled", "leech seed", "stuck", "tripped", "powdered", "heal blocked",
            }
            for status in state.statuses
        ),
        "thought_detection_ready": telepath_active and thought_detection_uses < 1,
        "thought_detection_uses_left": max(0, 1 - thought_detection_uses),
        "psionic_analysis_ready": bool(psionic_analysis_targets) and psionic_analysis_uses < 1,
        "psionic_analysis_uses_left": max(0, 1 - psionic_analysis_uses),
        "psionic_analysis_targets": psionic_analysis_targets,
        "psionic_sponge_ready": bool(psionic_sponge_sources) and psionic_sponge_uses < 1,
        "psionic_sponge_uses_left": max(0, 1 - psionic_sponge_uses),
        "psionic_sponge_range": psionic_sponge_range,
        "psionic_sponge_sources": psionic_sponge_sources,
        "psionic_sponge_borrowed_moves": psionic_sponge_borrowed_moves,
        "mindbreak_ap_ready": trainer_ap >= 2,
        "mindbreak_targets": mindbreak_targets,
        "mindbreak_bound_targets": mindbreak_bound_targets,
        "mindbreak_release_ready": bool(mindbreak_bound_targets),
        "arctic_zeal_ready": arctic_zeal_charges > 0,
        "arctic_zeal_charges": arctic_zeal_charges,
        "arctic_zeal_targets": arctic_zeal_targets,
        "arctic_zeal_hail_active": bool(state.get_temporary_effects("arctic_zeal_hail")),
        "arctic_zeal_source_move": str((next(iter(state.get_temporary_effects("arctic_zeal_hail")), None) or {}).get("source_move") or "").strip() or None,
        "polar_vortex_targets": polar_vortex_targets,
        "polar_vortex_bound_targets": polar_vortex_bound_targets,
        "polar_vortex_ready": trainer_ap >= 2 and bool(polar_vortex_targets),
        "polar_vortex_active": polar_vortex_active,
        "polar_vortex_release_ready": bool(polar_vortex_bound_targets),
        "tough_as_schist_ap_ready": trainer_ap >= 2,
        "tough_as_schist_targets": tough_as_schist_targets,
        "tough_as_schist_bound_targets": tough_as_schist_bound_targets,
        "tough_as_schist_release_ready": bool(tough_as_schist_bound_targets),
        "effective_weather": effective_weather_name,
        "effective_weather_source": effective_weather_source,
        "psionic_overload_ready": bool(psionic_overload_ready) and trainer_ap >= 1,
        "psionic_overload_move": psionic_overload_move,
        "psionic_overload_target": psionic_overload_target,
        "psionic_overload_target_name": _combatant_name(psionic_overload_target) if psionic_overload_target else None,
        "psionic_overload_barrier_tiles": psionic_overload_barrier_tiles,
        "force_of_will_ready": bool(force_of_will_ready) and force_of_will_uses < 3 and bool(force_of_will_moves),
        "force_of_will_uses_left": max(0, 3 - force_of_will_uses),
        "force_of_will_trigger_move": str((force_of_will_ready or {}).get("trigger_move") or "").strip() or None,
        "force_of_will_moves": force_of_will_moves,
        "suggestion_ap_ready": trainer_ap >= 1,
        "suggestion_targets": suggestion_targets,
        "suggestion_bound_target": suggestion_bound_target_id,
        "suggestion_bound_target_name": _combatant_name(suggestion_bound_target_id) if suggestion_bound_target_id else None,
        "suggestion_bound_text": str((suggestion_bound or {}).get("suggestion") or "").strip() or None,
        "suggestion_release_ready": suggestion_bound is not None,
        "adaptive_geography_uses_left": max(0, 2 - adaptive_geography_uses),
        "adaptive_geography_aliases": adaptive_aliases,
        "terrain_label": terrain_label.title() if terrain_label else None,
        "natural_fighter_move": natural_fighter_move or None,
        "natural_fighter_target_mode": natural_fighter_target_mode or None,
        "natural_fighter_targets": natural_fighter_targets,
        "natural_fighter_ap_ready": trainer_ap >= 1,
        "frozen_domain_ready": True,
        "frozen_domain_ap_ready": trainer_ap >= 2,
        "trapper_ready": bool(terrain_label) and trapper_uses < 2,
        "trapper_uses_left": max(0, 2 - trapper_uses),
        "wilderness_guide_ready": bool(terrain_label) and wilderness_guide_uses < 3,
        "wilderness_guide_uses_left": max(0, 3 - wilderness_guide_uses),
        "quick_switch_ap_cost": quick_switch_ap_cost,
        "quick_switch_ap_ready": trainer_ap >= quick_switch_ap_cost,
        "quick_switch_replacements": quick_switch_replacements,
        "quick_wit_uses": quick_wit_uses,
        "quick_wit_uses_left": max(0, 3 - quick_wit_uses),
        "quick_wit_manipulate_targets": sorted({entry["target"] for entry in quick_wit_options}),
        "quick_wit_manipulate_options": quick_wit_options,
        "enchanting_gaze_ap_ready": trainer_ap >= 2,
        "enchanting_gaze_anchors": _enemy_targets_within(2),
        "enchanting_gaze_anchor_options": enchanting_gaze_anchor_options,
        "trickster_targets": sorted({entry["target"] for entry in trickster_ready if entry["target"]}),
        "trickster_options": trickster_ready,
        "sleight_ready": bool(state.has_trainer_feature("Sleight") and sleight_options),
        "sleight_options": sleight_options,
        "shell_game_ready": bool(state.has_trainer_feature("Shell Game") and shell_game_uses_left > 0 and shell_game_options),
        "shell_game_options": shell_game_options,
        "shell_game_uses_left": shell_game_uses_left,
        "dirty_fighting_ap_ready": trainer_ap >= 1,
        "dirty_fighting_targets": sorted({entry["target"] for entry in dirty_fighting_options if entry["target"]}),
        "dirty_fighting_options": dirty_fighting_options,
        "weapon_finesse_ap_ready": trainer_ap >= 2,
        "weapon_finesse_targets": weapon_finesse_targets,
        "weapon_finesse_target_options": weapon_finesse_target_options,
        "psychic_resonance_uses": psychic_resonance_uses,
        "psychic_resonance_uses_left": max(0, 2 - psychic_resonance_uses),
        "psychic_resonance_targets": psychic_resonance_targets,
        "psychic_resonance_target_options": psychic_resonance_target_options,
        "play_them_like_a_fiddle_uses": play_them_like_a_fiddle_uses,
        "play_them_like_a_fiddle_uses_left": max(0, 3 - play_them_like_a_fiddle_uses),
        "play_them_like_a_fiddle_ready": play_fiddle_ready,
    }


def _visible_psychic_residue(battle: BattleState, actor_id: Optional[str]) -> List[Dict[str, Any]]:
    if not actor_id:
        return []
    actor = battle.pokemon.get(actor_id)
    if actor is None or not (actor.has_trainer_feature("Psionic Sight") or actor.has_trainer_feature("Psionic Analysis") or actor.has_trainer_feature("Witch Hunter")):
        return []
    visible: List[Dict[str, Any]] = []
    for pid, target in battle.pokemon.items():
        residues = target.get_temporary_effects("psychic_residue")
        if not residues:
            continue
        signatures: List[Dict[str, Any]] = []
        linked_targets: set[str] = set()
        seen_signatures: set[str] = set()
        for entry in residues:
            source_id = str(entry.get("source_id") or "").strip()
            signature = source_id or (str(entry.get("source") or "Unknown").strip().lower() or "unknown")
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            source = battle.pokemon.get(source_id) if source_id else None
            matching_targets: List[str] = []
            for other_id, other in battle.pokemon.items():
                if other_id == pid:
                    continue
                for other_entry in other.get_temporary_effects("psychic_residue"):
                    other_signature = str(other_entry.get("source_id") or "").strip() or (
                        str(other_entry.get("source") or "Unknown").strip().lower() or "unknown"
                    )
                    if other_signature == signature:
                        matching_targets.append(str(other.spec.name or other.spec.species or other_id))
                        linked_targets.add(other_id)
                        break
            signatures.append(
                {
                    "signature": signature,
                    "source_id": source_id or None,
                    "source_name": str(source.spec.name or source.spec.species or source_id) if source is not None else None,
                    "source_feature": str(entry.get("source") or "Unknown").strip() or "Unknown",
                    "matching_targets": sorted(matching_targets),
                }
            )
        visible.append(
            {
                "target": pid,
                "target_name": str(target.spec.name or target.spec.species or pid),
                "sources": sorted(
                    {
                        str(entry.get("source") or "Unknown").strip() or "Unknown"
                        for entry in residues
                    }
                ),
                "linked_targets": sorted(linked_targets),
                "signatures": signatures,
            }
        )
    return visible


def _prompt_id(payload: dict) -> str:
    keys = (
        "label",
        "actor_id",
        "phase",
        "move",
        "trigger_move",
        "attacker_id",
        "defender_id",
    )
    parts = [str(payload.get(key, "") or "") for key in keys]
    return "|".join(parts)


def _ordered_combatants(battle: BattleState) -> List[str]:
    team_order: Dict[str, int] = {}
    next_order = 0
    for trainer in battle.trainers.values():
        key = trainer.team or trainer.identifier
        if key not in team_order:
            team_order[key] = next_order
            next_order += 1

    def sort_key(item: Tuple[str, PokemonState]) -> Tuple[int, str, str, str]:
        cid, state = item
        trainer = battle.trainers.get(state.controller_id)
        team_key = trainer.team if trainer and trainer.team else (trainer.identifier if trainer else state.controller_id)
        order = team_order.get(team_key, 99)
        trainer_name = trainer.name if trainer else state.controller_id
        mon_name = _display_combatant_name(state)
        return (order, trainer_name, mon_name, cid)

    return [cid for cid, _state in sorted(battle.pokemon.items(), key=sort_key)]


def _combatant_markers(battle: BattleState) -> Dict[str, str]:
    markers: Dict[str, str] = {}
    ordered = _ordered_combatants(battle)
    for idx, cid in enumerate(ordered):
        markers[cid] = _MARKER_CHARS[idx % len(_MARKER_CHARS)]
    return markers


def _display_combatant_name(state: PokemonState) -> str:
    raw = str(state.spec.name or state.spec.species or "").strip()
    species = str(state.spec.species or raw).strip()
    if ":" in raw and species:
        return species
    return raw or species


def _status_labels(state: PokemonState) -> List[str]:
    labels: List[str] = []
    for entry in state.statuses:
        if isinstance(entry, str):
            labels.append(entry.title())
        elif isinstance(entry, dict):
            name = str(entry.get("name", "")).title()
            stacks = entry.get("stacks")
            if stacks:
                name = f"{name}({stacks})"
            labels.append(name)
    return labels


def _base_ability_names(state: PokemonState) -> List[str]:
    names: List[str] = []
    for entry in state.spec.abilities:
        name = ""
        if isinstance(entry, str):
            name = entry.strip()
        elif isinstance(entry, dict):
            name = str(entry.get("name") or "").strip()
        if not name:
            continue
        if any(existing.lower() == name.lower() for existing in names):
            continue
        names.append(name)
    return names


def _team_for(battle: BattleState, actor_id: str) -> Optional[str]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None
    trainer = battle.trainers.get(actor.controller_id)
    return (trainer.team or trainer.identifier) if trainer else actor.controller_id


def _opponent_ids(battle: BattleState, actor_id: str) -> List[str]:
    team = _team_for(battle, actor_id)
    ids: List[str] = []
    for cid, state in battle.pokemon.items():
        if state.fainted or not state.active or state.position is None:
            continue
        if _team_for(battle, cid) != team:
            ids.append(cid)
    return ids


def _ally_ids(battle: BattleState, actor_id: str) -> List[str]:
    team = _team_for(battle, actor_id)
    ids: List[str] = []
    for cid, state in battle.pokemon.items():
        if cid == actor_id:
            continue
        if state.fainted or not state.active or state.position is None:
            continue
        if _team_for(battle, cid) == team:
            ids.append(cid)
    return ids


def _move_target_ids(battle: BattleState, actor_id: str) -> Dict[str, List[Optional[str]]]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return {}
    actor._sync_parfumier_moves()
    opponent_ids = _opponent_ids(battle, actor_id)
    ally_ids = _ally_ids(battle, actor_id)
    targets: Dict[str, List[Optional[str]]] = {}
    for move in actor.spec.moves:
        move_name = str(move.name or "").strip()
        if not move_name:
            continue
        target_kind = targeting.normalized_target_kind(move)
        requires_target = targeting.move_requires_target(move)
        candidate_ids: List[Optional[str]] = []
        if target_kind == "self" and not requires_target:
            candidate_ids = [actor_id]
        elif target_kind == "ally":
            candidate_ids = ally_ids or ([] if requires_target else [None])
        elif target_kind == "self":
            candidate_ids = [actor_id]
        else:
            candidate_ids = opponent_ids or ([] if requires_target else [None])
        accepted: List[Optional[str]] = []
        for target_id in candidate_ids:
            if target_id is None:
                accepted.append(None)
                continue
            target = battle.pokemon.get(target_id)
            if target is None or target.position is None or target.fainted or not target.active:
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
            accepted.append(target_id)
        if not accepted and not requires_target:
            accepted.append(None)
        targets[move_name] = accepted
    return targets


def _maneuver_target_ids(battle: BattleState, actor_id: str) -> Dict[str, List[Optional[str]]]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return {}
    targets: Dict[str, List[Optional[str]]] = {}
    for move in _load_maneuver_moves().values():
        move_name = str(move.name or "").strip()
        if not move_name:
            continue
        accepted: List[Optional[str]] = []
        for target_id in _opponent_ids(battle, actor_id):
            try:
                UseMoveAction(actor_id=actor_id, move_name=move_name, target_id=target_id).validate(battle)
            except Exception:
                continue
            accepted.append(target_id)
        targets[move_name] = accepted
    return targets


def _capability_battle_suggestions(state: PokemonState) -> List[dict]:
    suggestions_map = {
        "telekinetic": [
            "Use Focus for ranged Push, Trip, or Disarm style stunts.",
            "Manipulate distant objects or terrain without crossing the map.",
        ],
        "telepath": [
            "Use Focus for silent coordination, mind-to-mind warnings, or sensing intent.",
        ],
        "threaded": [
            "Use Acrobatics or Combat for Wrap, snag, trip, or grapple-style stunts.",
        ],
        "wallclimber": [
            "Use Athletics or Acrobatics to take vertical routes or claim cover.",
        ],
        "phasing": [
            "Use Focus for slipping through barriers or escaping a bind.",
        ],
        "teleporter": [
            "Use Focus for blink repositioning, escapes, or sudden angle changes.",
        ],
        "levitate": [
            "Use Acrobatics for hovering, repositioning, or avoiding grounded hazards.",
        ],
        "burrow": [
            "Use Athletics or Survival for tunneling angles, cover, or ambush entries.",
        ],
        "swim": [
            "Use Athletics for water repositioning, dragging, or aquatic hazards.",
        ],
        "reach": [
            "Use Combat for long-limbed grabs, trips, or zone control.",
        ],
        "power": [
            "Use Athletics for lifts, shoves, breaking obstacles, or heavy-object throws.",
        ],
        "guster": [
            "Use Acrobatics or Focus for gust-assisted repositioning or improvised pushes.",
        ],
        "fountain": [
            "Use Athletics or Focus for water redirection, slippery terrain, or cover.",
        ],
    }
    results: List[dict] = []
    seen: set[str] = set()
    for raw in state.capability_names():
        label = str(raw or "").strip()
        key = label.lower()
        if not label or key in seen:
            continue
        seen.add(key)
        notes = suggestions_map.get(key.split()[0], []) or suggestions_map.get(key, [])
        if notes:
            results.append({"capability": label, "ideas": list(notes)})
    return results


def _maneuver_context(battle: BattleState, actor_id: str) -> Dict[str, Any]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return {}
    context: Dict[str, Any] = {
        "maneuver_targets": _maneuver_target_ids(battle, actor_id),
        "wake_targets": [],
        "intercept_melee_targets": [],
        "intercept_ranged_targets": [],
        "manipulate_targets": [],
        "pickup_available": False,
        "capability_suggestions": _capability_battle_suggestions(actor),
        "creative_rulebook": [
            "PTU Core p.228: use abilities, capabilities, or skill checks as combat actions.",
            "PTU Core p.222-223: capabilities define your movement, throwing, and physical limits.",
            "PTU Core p.50: complex stunts may call for Focus with another skill.",
        ],
    }
    if battle.grid is not None and actor.position is not None:
        others = battle._occupied_tiles(exclude_id=actor_id)
        context["disengage_tiles"] = [
            list(coord)
            for coord in movement.legal_shift_tiles(battle, actor_id)
            if battle._combatant_distance_to_coord(actor, coord) <= 1
            and (coord == actor.position or battle._position_can_fit(actor_id, coord, exclude_id=actor_id))
        ]
    else:
        context["disengage_tiles"] = []
    for pid, mon in battle.pokemon.items():
        if pid == actor_id or mon.fainted or mon.position is None:
            continue
        distance = (
            battle._combatant_distance(actor, mon)
            if actor.position is not None
            else None
        )
        if _team_for(battle, pid) == _team_for(battle, actor_id):
            if mon.has_status("Sleep") or mon.has_status("Asleep"):
                if distance == 1:
                    context["wake_targets"].append({"id": pid, "name": mon.spec.name or mon.spec.species})
            if pid != actor_id:
                try:
                    InterceptAction(actor_id=actor_id, kind="melee", ally_id=pid).validate(battle)
                    context["intercept_melee_targets"].append({"id": pid, "name": mon.spec.name or mon.spec.species})
                except Exception:
                    pass
                try:
                    InterceptAction(actor_id=actor_id, kind="ranged", ally_id=pid).validate(battle)
                    context["intercept_ranged_targets"].append({"id": pid, "name": mon.spec.name or mon.spec.species})
                except Exception:
                    pass
        else:
            try:
                ManipulateAction(actor_id=actor_id, trick="Bon Mot", target_id=pid).validate(battle)
                context["manipulate_targets"].append({"id": pid, "name": mon.spec.name or mon.spec.species})
            except Exception:
                pass
    try:
        PickupItemAction(actor_id=actor_id).validate(battle)
        context["pickup_available"] = True
    except Exception:
        context["pickup_available"] = False
    grapple_status = battle.grapple_status(actor_id)
    if grapple_status:
        context["grapple_status"] = dict(grapple_status)
        try:
            other_id = grapple_status.get("other_id")
            actor_state = battle.pokemon.get(actor_id)
            other = battle.pokemon.get(other_id) if other_id else None
            if actor_state is not None and actor_state.position is not None and battle.grid is not None:
                penalty = other.weight_class() if other is not None else 0
                context["grapple_move_tiles"] = [
                    list(coord)
                    for coord in movement.legal_shift_tiles(battle, actor_id, limit_penalty=penalty)
                ]
        except Exception:
            context["grapple_move_tiles"] = []
    return context


def _core_action_hints(battle: BattleState, actor_id: str, state: PokemonState) -> Dict[str, Any]:
    hints: Dict[str, Any] = {
        "can_take_breather": False,
        "can_trade_standard_shift": False,
        "can_trade_standard_swift": False,
        "motivated_ready": False,
        "motivated_stat_options": [],
        "delay_options": [],
        "switch_replacements": [],
        "weapon_options": [],
        "can_unequip_weapon": False,
        "equipped_weapon_name": "",
    }
    try:
        TakeBreatherAction(actor_id=actor_id).validate(battle)
        hints["can_take_breather"] = True
    except Exception:
        hints["can_take_breather"] = False
    for target_action, key in (("shift", "can_trade_standard_shift"), ("swift", "can_trade_standard_swift")):
        try:
            TradeStandardForAction(actor_id=actor_id, target_action=target_action).validate(battle)
            hints[key] = True
        except Exception:
            hints[key] = False
    motivated_stats = []
    for stat, label in (
        ("atk", "Attack"),
        ("def", "Defense"),
        ("spatk", "Special Attack"),
        ("spdef", "Special Defense"),
        ("spd", "Speed"),
        ("accuracy", "Accuracy"),
        ("evasion", "Evasion"),
    ):
        try:
            MotivatedAction(actor_id=actor_id, stat=stat).validate(battle)
        except Exception:
            continue
        motivated_stats.append({"value": stat, "label": label})
    hints["motivated_stat_options"] = motivated_stats
    hints["motivated_ready"] = bool(motivated_stats)
    if battle.current_actor_id == actor_id:
        entry = battle.current_initiative_entry()
        current_total = int(getattr(entry, "total", 0) or 0) if entry is not None else None
        if current_total is not None:
            delay_totals = sorted(
                {
                    int(getattr(slot, "total", 0) or 0)
                    for slot in (battle.initiative_order or [])
                    if str(getattr(slot, "actor_id", "") or "").strip() != actor_id
                    and int(getattr(slot, "total", 0) or 0) < current_total
                },
                reverse=True,
            )
            for total in delay_totals:
                try:
                    DelayAction(actor_id=actor_id, target_total=total).validate(battle)
                except Exception:
                    continue
                hints["delay_options"].append(
                    {
                        "value": total,
                        "label": f"Delay to {total}",
                    }
                )
    for replacement_id, mon in battle.pokemon.items():
        if mon.controller_id != state.controller_id or replacement_id == actor_id:
            continue
        try:
            SwitchAction(actor_id=actor_id, replacement_id=replacement_id).validate(battle)
        except Exception:
            continue
        hints["switch_replacements"].append(
            {
                "target": replacement_id,
                "target_name": mon.spec.name or mon.spec.species or replacement_id,
            }
        )
    equipped_weapon = state.equipped_weapon()
    if equipped_weapon is not None:
        hints["equipped_weapon_name"] = str(equipped_weapon.get("name") or equipped_weapon or "").strip()
    try:
        UnequipWeaponAction(actor_id=actor_id).validate(battle)
        hints["can_unequip_weapon"] = True
    except Exception:
        hints["can_unequip_weapon"] = False
    for idx, item in enumerate(getattr(state.spec, "items", []) or []):
        if "weapon" not in _weapon_tags(item):
            continue
        try:
            EquipWeaponAction(actor_id=actor_id, item_index=idx).validate(battle)
        except Exception:
            continue
        name = str(item.get("name") if isinstance(item, dict) else item or "").strip()
        hints["weapon_options"].append(
            {
                "item_index": idx,
                "name": name or f"Weapon {idx + 1}",
            }
        )
    return hints


def _trainer_turn_context(battle: BattleState, trainer_id: str) -> Dict[str, Any]:
    trainer = battle.trainers.get(trainer_id)
    if trainer is None:
        return {}
    switch_options: List[Dict[str, Any]] = []
    active_ids = [
        pid
        for pid, mon in battle.pokemon.items()
        if mon.controller_id == trainer_id and mon.active and not mon.fainted
    ]
    bench_ids = [
        pid
        for pid, mon in battle.pokemon.items()
        if mon.controller_id == trainer_id and not mon.active and not mon.fainted
    ]
    for outgoing_id in active_ids:
        for replacement_id in bench_ids:
            try:
                action = TrainerSwitchAction(
                    actor_id=trainer_id,
                    outgoing_id=outgoing_id,
                    replacement_id=replacement_id,
                )
                action.validate(battle)
            except Exception:
                continue
            outgoing = battle.pokemon.get(outgoing_id)
            replacement = battle.pokemon.get(replacement_id)
            switch_options.append(
                {
                    "outgoing_id": outgoing_id,
                    "outgoing_name": outgoing.spec.name or outgoing.spec.species or outgoing_id if outgoing else outgoing_id,
                    "replacement_id": replacement_id,
                    "replacement_name": replacement.spec.name or replacement.spec.species or replacement_id if replacement else replacement_id,
                    "action_type": action.action_type.value,
                }
            )
    return {
        "id": trainer.identifier,
        "name": trainer.name or trainer.identifier,
        "team": trainer.team or trainer.identifier,
        "throw_origin": list(trainer.position) if getattr(trainer, "position", None) is not None else None,
        "throw_range": max(1, 4 + int((trainer.skills or {}).get("athletics", 0) or 0)),
        "actions_taken": {k.value: v for k, v in trainer.actions_taken.items()},
        "switch_options": switch_options,
    }


@dataclass
class EngineFacade:
    plan: Optional[MatchPlan] = None
    matchup: Optional[MatchupSpec] = None
    battle: Optional[BattleState] = None
    _pending_action: Optional[Dict[str, Any]] = None
    _pending_prompts: List[dict] = None
    _prompt_answers: Dict[str, Any] = None
    mode: str = "player"
    ai_step_mode: bool = False
    session: Optional[TextBattleSession] = None
    record: Optional[BattleRecord] = None
    _history: List[dict] = None
    _history_limit: int = 20
    _ability_repo: Optional[PTUCsvRepository] = None
    _ability_repo_checked: bool = False
    _last_random_terrain: Optional[str] = None
    _battle_royale_state: Optional[Dict[str, Any]] = None
    _battle_log_path: Optional[str] = None
    _battle_log_cursor: int = 0
    _battle_log_closed: bool = False

    def __post_init__(self) -> None:
        self._pending_prompts = []
        self._prompt_answers = {}
        self._history = []
        self._battle_royale_state = None
        self._battle_log_path = None
        self._battle_log_cursor = 0
        self._battle_log_closed = False

    def _out_of_turn_prompt(self, payload: dict) -> bool:
        # Default: allow the trigger; UI preflights prompts separately.
        return True

    def _preflight_turn_prompts(self, battle: BattleState, actor_id: Optional[str]) -> List[dict]:
        if not actor_id:
            return []
        actor = battle.pokemon.get(actor_id)
        if actor is None or not actor.active or actor.fainted:
            return []
        if not battle.is_player_controlled(actor_id):
            return []
        pending = next(iter(actor.get_temporary_effects("hunger_switch_pending")), None)
        if not pending or pending.get("round") != battle.round:
            return []
        prompt = {
            "label": "Hunger Switch: Full Belly?",
            "detail": "Yes: Full Belly (+2 Accuracy). No: Hangry (+5 damage).",
            "yes_label": "Full Belly",
            "no_label": "Hangry",
            "actor_id": actor_id,
            "phase": "turn_start",
            "optional": True,
            "kind": "hunger_switch",
        }
        prompt["id"] = _prompt_id(prompt)
        return [prompt]

    def _apply_hunger_switch_choice(self, battle: BattleState, actor_id: Optional[str], full_belly: bool) -> None:
        if not actor_id:
            return
        actor = battle.pokemon.get(actor_id)
        if actor is None or not actor.has_ability("Hunger Switch"):
            return
        for entry in list(actor.get_temporary_effects("hunger_switch_pending")):
            actor.remove_temporary_effect("hunger_switch_pending")
        choice = "full" if full_belly else "hangry"
        while actor.remove_temporary_effect("hunger_switch_mode"):
            continue
        actor.add_temporary_effect(
            "hunger_switch_mode",
            mode=choice,
            round=battle.round,
            expires_round=battle.round + 1,
        )
        if choice == "full":
            actor.add_temporary_effect(
                "accuracy_bonus",
                amount=2,
                round=battle.round,
                expires_round=battle.round + 1,
            )
            battle.log_event(
                {
                    "type": "ability",
                    "actor": actor_id,
                    "ability": "Hunger Switch",
                    "phase": battle.phase.value if isinstance(battle.phase, TurnPhase) else None,
                    "effect": "accuracy_bonus",
                    "amount": 2,
                    "description": "Hunger Switch (Full Belly) boosts accuracy.",
                    "target_hp": actor.hp,
                }
            )
        else:
            battle.log_event(
                {
                    "type": "ability",
                    "actor": actor_id,
                    "ability": "Hunger Switch",
                    "phase": battle.phase.value if isinstance(battle.phase, TurnPhase) else None,
                    "effect": "damage_bonus",
                    "amount": 5,
                    "description": "Hunger Switch (Hangry) boosts damage rolls.",
                    "target_hp": actor.hp,
                }
            )

    def _battle_log_dir(self) -> Path:
        override = str(os.environ.get("AUTOPTU_BATTLE_LOG_DIR") or "").strip()
        if override:
            path = Path(override).expanduser()
        else:
            path = Path.cwd() / "reports" / "battle_logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _start_battle_log(self, *, mode: str, source: str, seed: Optional[int]) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        suffix = random.randint(1000, 9999)
        path = self._battle_log_dir() / f"battle_{ts}_{suffix}.jsonl"
        self._battle_log_path = str(path)
        self._battle_log_cursor = 0
        self._battle_log_closed = False
        header = {
            "type": "battle_start",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "source": source,
            "seed": seed,
        }
        self._append_battle_log_line(header)

    def _append_battle_log_line(self, payload: Dict[str, Any]) -> None:
        if not self._battle_log_path:
            return
        try:
            path = Path(self._battle_log_path)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _flush_battle_log_events(self, battle: Optional[BattleState]) -> None:
        if battle is None or not self._battle_log_path:
            return
        log_entries = list(getattr(battle, "log", []) or [])
        if self._battle_log_cursor > len(log_entries):
            self._battle_log_cursor = len(log_entries)
        for idx in range(self._battle_log_cursor, len(log_entries)):
            entry = log_entries[idx]
            payload = {
                "type": "battle_event",
                "idx": idx,
                "round": int(getattr(battle, "round", 0) or 0),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "event": entry,
            }
            self._append_battle_log_line(payload)
        self._battle_log_cursor = len(log_entries)

    def _finalize_battle_log_if_finished(self, battle: Optional[BattleState]) -> None:
        if self._battle_log_closed or battle is None or not self._battle_log_path:
            return
        session = self.session
        finished = bool(session and session._battle_finished(battle))
        if not finished:
            return
        alive_teams: List[str] = []
        if session:
            try:
                alive_teams = sorted(session._alive_teams(battle))
            except Exception:
                alive_teams = []
        footer = {
            "type": "battle_end",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "round": int(getattr(battle, "round", 0) or 0),
            "alive_teams": alive_teams,
        }
        self._append_battle_log_line(footer)
        self._battle_log_closed = True

    def start_encounter(
        self,
        *,
        campaign: Optional[str] = None,
        team_size: int = 1,
        matchup_index: int = 0,
        seed: Optional[int] = None,
        random_battle: bool = False,
        min_level: int = 20,
        max_level: int = 40,
        csv_root: Optional[str] = None,
        roster_csv: Optional[str] = None,
        roster_csv_path: Optional[str] = None,
        ai_mode: str = "player",
        step_ai: bool = False,
        active_slots: Optional[int] = None,
        trainer_profile: Optional[dict] = None,
        side_names: Optional[dict] = None,
        deployment_overrides: Optional[dict] = None,
        item_choice_overrides: Optional[dict] = None,
        ability_choice_overrides: Optional[dict] = None,
        grid: Optional[dict] = None,
        side_count: int = 2,
        battle_royale: bool = False,
        circle_interval: int = 3,
    ) -> dict:
        self.mode = ai_mode
        source = "builtin:demo"
        if roster_csv:
            plan = match_plan_from_roster_csv(
                csv_text=roster_csv,
                csv_root=csv_root,
                default_level=max(1, min_level),
                active_slots=max(1, int(active_slots)) if active_slots is not None else 1,
                ai_mode=ai_mode,
                seed=seed,
            )
            source = "roster-csv"
        elif roster_csv_path:
            plan = match_plan_from_roster_csv_file(
                path=roster_csv_path,
                csv_root=csv_root,
                default_level=max(1, min_level),
                active_slots=max(1, int(active_slots)) if active_slots is not None else 1,
                ai_mode=ai_mode,
                seed=seed,
            )
            source = f"roster-csv:{roster_csv_path}"
        elif battle_royale and ai_mode == "ai":
            royale_sides = max(3, int(side_count or 3))
            plan = self._build_battle_royale_plan(
                side_count=royale_sides,
                team_size=max(1, int(team_size)),
                min_level=max(1, int(min_level)),
                max_level=max(1, int(max_level)),
                seed=seed,
                csv_root=csv_root,
            )
            source = f"battle-royale:{royale_sides}sides"
        elif random_battle and ai_mode == "ai" and int(side_count or 2) > 2:
            plan = self._build_random_multi_side_plan(
                side_count=max(2, int(side_count)),
                team_size=max(1, int(team_size)),
                min_level=max(1, int(min_level)),
                max_level=max(1, int(max_level)),
                seed=seed,
                csv_root=csv_root,
            )
            source = f"csv-random:{side_count}sides"
        else:
            campaign_spec, source = self._resolve_campaign_spec(
                campaign=campaign,
                random_battle=random_battle,
                team_size=team_size,
                min_level=min_level,
                max_level=max_level,
                seed=seed,
                csv_root=csv_root,
                roster_csv=None,
                roster_csv_path=None,
            )
            planner = AutoMatchPlanner(campaign_spec, seed=seed)
            plan = planner.create_plan(team_size=team_size)
        if random_battle and not battle_royale and not isinstance(grid, dict):
            plan.grid = self._random_grid_spec(plan.grid)
        if isinstance(grid, dict) and grid:
            plan.grid = GridSpec.from_dict(dict(grid))
        if active_slots is not None:
            plan.active_slots = max(1, int(active_slots))
        if isinstance(side_names, dict) and side_names:
            self._apply_side_names_to_plan(plan, side_names)
        matchup = plan.matchups[matchup_index % len(plan.matchups)]
        if not (isinstance(deployment_overrides, dict) and deployment_overrides):
            self._auto_select_ai_starters(matchup, plan)
        if isinstance(deployment_overrides, dict) and deployment_overrides:
            self._apply_deployment_overrides(matchup, plan, deployment_overrides)
        if isinstance(item_choice_overrides, dict) and item_choice_overrides:
            self._apply_item_choice_overrides(matchup, item_choice_overrides)
        if isinstance(ability_choice_overrides, dict) and ability_choice_overrides:
            self._apply_ability_choice_overrides(matchup, ability_choice_overrides)
        battle = self._build_battle_state(plan, matchup, matchup_index)
        if isinstance(side_names, dict) and side_names:
            self._apply_side_names_to_battle(battle, side_names)
        if random_battle:
            battle.terrain = self._random_field_terrain()
        if trainer_profile and battle.trainers:
            try:
                trainer = next(iter(battle.trainers.values()))
                profile = trainer_profile.get("profile", {}) if isinstance(trainer_profile, dict) else {}
                name = profile.get("name") if isinstance(profile, dict) else None
                if not name and isinstance(trainer_profile, dict):
                    name = trainer_profile.get("name")
                if name:
                    trainer.name = str(name)
                team = None
                if isinstance(profile, dict):
                    team = profile.get("region") or profile.get("team")
                if not team and isinstance(trainer_profile, dict):
                    team = trainer_profile.get("team")
                if team:
                    trainer.team = str(team)
                if isinstance(trainer_profile, dict):
                    def _derive_hobbyist_feature_names(payload: dict[str, Any]) -> list[str]:
                        derived: list[str] = []
                        granted = payload.get("hobbyist_granted_features")
                        if isinstance(granted, list):
                            derived.extend(str(name).strip() for name in granted if str(name).strip())
                        if derived:
                            return derived
                        look_and_learn = payload.get("look_and_learn_features")
                        if isinstance(look_and_learn, dict):
                            for key in ("scene", "ap"):
                                name = str(look_and_learn.get(key) or "").strip()
                                if name:
                                    derived.append(name)
                        dilettante_picks = payload.get("dilettante_picks")
                        if isinstance(dilettante_picks, list):
                            for pick in dilettante_picks:
                                if not isinstance(pick, dict):
                                    continue
                                name = str(pick.get("feature") or "").strip()
                                if name:
                                    derived.append(name)
                        return derived

                    def _derive_hobbyist_edge_names(payload: dict[str, Any]) -> list[str]:
                        derived: list[str] = []
                        granted = payload.get("hobbyist_granted_edges")
                        if isinstance(granted, list):
                            derived.extend(str(name).strip() for name in granted if str(name).strip())
                        if derived:
                            return derived
                        dilettante_picks = payload.get("dilettante_picks")
                        if isinstance(dilettante_picks, list):
                            for pick in dilettante_picks:
                                if not isinstance(pick, dict):
                                    continue
                                name = str(pick.get("edge") or "").strip()
                                if name:
                                    derived.append(name)
                        return derived

                    class_id = str(trainer_profile.get("class_id") or "")
                    class_name = str(trainer_profile.get("class_name") or class_id)
                    mentor_skills = trainer_profile.get("mentor_skills")
                    if class_id or class_name:
                        trainer.trainer_class = {"id": class_id, "name": class_name}
                    if isinstance(mentor_skills, list):
                        trainer.trainer_class["mentor_skills"] = [
                            str(name).strip()
                            for name in mentor_skills
                            if str(name).strip()
                        ]
                    feature_entries: list[dict] = []
                    features = trainer_profile.get("features")
                    if isinstance(features, list):
                        feature_entries.extend(_normalize_named_entries(features))
                    capture_techniques = trainer_profile.get("capture_techniques")
                    if isinstance(capture_techniques, list):
                        for entry in capture_techniques:
                            label = str(entry).strip()
                            if not label or label.lower().startswith("capture skills"):
                                continue
                            feature_entries.append({"name": label})
                    commander_orders = trainer_profile.get("commander_orders")
                    if isinstance(commander_orders, list):
                        feature_entries.extend(_normalize_named_entries(commander_orders))
                    elif isinstance(commander_orders, str) and commander_orders.strip():
                        feature_entries.append({"name": commander_orders.strip()})
                    feature_entries.extend(_normalize_named_entries(_derive_hobbyist_feature_names(trainer_profile)))
                    if feature_entries:
                        seen_features: set[str] = set()
                        merged_features = []
                        for feature_entry in feature_entries:
                            feature_name = str(feature_entry.get("feature_id") or feature_entry.get("id") or feature_entry.get("name") or "").strip()
                            key = feature_name.lower()
                            if key in seen_features:
                                continue
                            seen_features.add(key)
                            merged_features.append(dict(feature_entry))
                        trainer.features = merged_features
                    edge_names: list[str] = []
                    edges = trainer_profile.get("edges")
                    if isinstance(edges, list):
                        edge_names.extend(str(name).strip() for name in edges if str(name).strip())
                    hobbyist_skill_edges = trainer_profile.get("hobbyist_skill_edges")
                    if isinstance(hobbyist_skill_edges, list):
                        edge_names.extend(str(name).strip() for name in hobbyist_skill_edges if str(name).strip())
                    edge_names.extend(_derive_hobbyist_edge_names(trainer_profile))
                    if edge_names:
                        seen_edges: set[str] = set()
                        merged_edges = []
                        for edge_name in edge_names:
                            key = edge_name.lower()
                            if key in seen_edges:
                                continue
                            seen_edges.add(key)
                            merged_edges.append({"name": edge_name})
                        trainer.edges = merged_edges
            except Exception:
                pass
        battle.out_of_turn_prompt = self._out_of_turn_prompt
        setattr(battle, "_ai_diagnostics", None)
        self.plan = plan
        self.matchup = matchup
        self.battle = battle
        self.ai_step_mode = step_ai
        self.session = TextBattleSession(
            plan,
            console=Console(file=io.StringIO(), force_terminal=False),
            viewer_enabled=False,
            spectator_enabled=False,
        )
        self.record = BattleRecord(matchup=matchup)
        self._pending_action = None
        self._pending_prompts = []
        self._prompt_answers = {}
        self._ai_model_rating_recorded = False
        self._start_battle_log(mode=ai_mode, source=source, seed=seed)
        self._battle_royale_state = None
        if battle_royale and ai_mode == "ai":
            self._battle_royale_state = self._init_battle_royale_state(
                battle,
                interval=max(1, int(circle_interval)),
            )
            setattr(battle, "_battle_royale_state", self._battle_royale_state)
        battle.start_round()
        battle.advance_turn()
        if self.mode == "player":
            self._advance_until_player()
        return self.snapshot()

    def _apply_deployment_overrides(
        self,
        matchup: MatchupSpec,
        plan: MatchPlan,
        deployment_overrides: dict,
    ) -> None:
        sides = matchup.sides
        if not sides:
            sides = matchup.sides_or_default()
            matchup.sides = sides
        for side in sides:
            override = None
            for key in (
                side.identifier,
                side.name,
                side.team,
                side.controller,
            ):
                if key is None:
                    continue
                override = deployment_overrides.get(str(key))
                if override is not None:
                    break
                override = deployment_overrides.get(str(key).strip().lower())
                if override is not None:
                    break
            if not isinstance(override, dict):
                continue
            selected = override.get("active") or override.get("active_pokemon") or override.get("starters")
            if isinstance(selected, list) and selected:
                remaining = list(side.pokemon)
                picked: List[object] = []
                used_indexes: set[int] = set()
                for raw_choice in selected:
                    choice_text = str(raw_choice or "").strip().lower()
                    matched_index: Optional[int] = None
                    try:
                        numeric = int(raw_choice)
                    except (TypeError, ValueError):
                        numeric = 0
                    if numeric > 0 and numeric <= len(remaining):
                        matched_index = numeric - 1
                    else:
                        for idx, spec in enumerate(remaining):
                            if idx in used_indexes:
                                continue
                            name_options = {
                                str(getattr(spec, "name", "") or "").strip().lower(),
                                str(getattr(spec, "species", "") or "").strip().lower(),
                            }
                            if choice_text and choice_text in name_options:
                                matched_index = idx
                                break
                    if matched_index is None or matched_index in used_indexes:
                        continue
                    used_indexes.add(matched_index)
                    picked.append(remaining[matched_index])
                if picked:
                    side.pokemon = picked + [spec for idx, spec in enumerate(remaining) if idx not in used_indexes]
            raw_positions = override.get("start_positions") or override.get("positions") or override.get("tiles")
            if isinstance(raw_positions, list) and raw_positions:
                parsed_positions: List[Tuple[int, int]] = []
                grid_tiles: Dict[Tuple[int, int], Dict[str, object]] = {}
                for coord, metadata in (plan.grid.tiles or {}).items():
                    if isinstance(metadata, dict):
                        grid_tiles[coord] = dict(metadata)
                    else:
                        grid_tiles[coord] = {"type": str(metadata or "")}
                grid = GridState(
                    width=plan.grid.width,
                    height=plan.grid.height,
                    blockers=set(plan.grid.blockers),
                    tiles=grid_tiles,
                    map=dict(getattr(plan.grid, "map", {}) or {}),
                )
                origin = side.start_positions[0] if side.start_positions else self._default_origin_for_side(side, grid)
                throw_range = max(1, 4 + int((side.skills or {}).get("athletics", 0) or 0))
                active_limit = max(1, int(plan.active_slots or 1))
                for raw in raw_positions[:active_limit]:
                    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
                        continue
                    coord = (int(raw[0]), int(raw[1]))
                    if coord[0] < 0 or coord[1] < 0 or coord[0] >= grid.width or coord[1] >= grid.height:
                        raise ValueError(f"Deployment tile {coord} is outside the battlefield.")
                    if coord in grid.blockers:
                        raise ValueError(f"Deployment tile {coord} is blocked.")
                    if targeting.footprint_distance(origin, "Medium", coord, "Medium", grid) > throw_range:
                        raise ValueError(
                            f"Deployment tile {coord} is beyond {side.name}'s throwing range of {throw_range}."
                        )
                    parsed_positions.append(coord)
                if parsed_positions:
                    existing = [coord for coord in side.start_positions if coord not in parsed_positions]
                    side.start_positions = parsed_positions + existing

    def _apply_item_choice_overrides(self, matchup: MatchupSpec, item_choice_overrides: dict) -> None:
        sides = matchup.sides
        if not sides:
            sides = matchup.sides_or_default()
            matchup.sides = sides
        for side in sides:
            side_override = None
            for key in (side.identifier, side.name, side.team, side.controller):
                if key is None:
                    continue
                side_override = item_choice_overrides.get(str(key))
                if side_override is not None:
                    break
                side_override = item_choice_overrides.get(str(key).strip().lower())
                if side_override is not None:
                    break
            if not isinstance(side_override, dict):
                continue
            for spec in side.pokemon:
                spec_key_candidates = [
                    str(getattr(spec, "name", "") or "").strip(),
                    str(getattr(spec, "species", "") or "").strip(),
                ]
                mon_override = None
                for key in spec_key_candidates:
                    if not key:
                        continue
                    mon_override = side_override.get(key)
                    if mon_override is not None:
                        break
                    mon_override = side_override.get(key.lower())
                    if mon_override is not None:
                        break
                if not isinstance(mon_override, dict):
                    continue
                next_items: List[object] = []
                for item in list(getattr(spec, "items", []) or []):
                    item_name = ""
                    if isinstance(item, dict):
                        item_name = str(item.get("name") or "").strip()
                    else:
                        item_name = str(item or "").strip()
                    if not item_name:
                        next_items.append(item)
                        continue
                    item_override = mon_override.get(item_name) or mon_override.get(item_name.lower())
                    if not isinstance(item_override, dict):
                        next_items.append(item)
                        continue
                    payload = dict(item) if isinstance(item, dict) else {"name": item_name}
                    chosen_stat = item_override.get("chosen_stat")
                    if chosen_stat:
                        payload["chosen_stat"] = str(chosen_stat)
                    chosen_stats = item_override.get("chosen_stats")
                    if isinstance(chosen_stats, list):
                        payload["chosen_stats"] = [str(value) for value in chosen_stats if str(value or "").strip()]
                    next_items.append(payload)
                spec.items = next_items

    def _apply_ability_choice_overrides(self, matchup: MatchupSpec, ability_choice_overrides: dict) -> None:
        sides = matchup.sides
        if not sides:
            sides = matchup.sides_or_default()
            matchup.sides = sides
        for side in sides:
            side_override = None
            for key in (side.identifier, side.name, side.team, side.controller):
                if key is None:
                    continue
                side_override = ability_choice_overrides.get(str(key))
                if side_override is not None:
                    break
                side_override = ability_choice_overrides.get(str(key).strip().lower())
                if side_override is not None:
                    break
            if not isinstance(side_override, dict):
                continue
            for spec in side.pokemon:
                spec_key_candidates = [
                    str(getattr(spec, "name", "") or "").strip(),
                    str(getattr(spec, "species", "") or "").strip(),
                ]
                mon_override = None
                for key in spec_key_candidates:
                    if not key:
                        continue
                    mon_override = side_override.get(key)
                    if mon_override is not None:
                        break
                    mon_override = side_override.get(key.lower())
                    if mon_override is not None:
                        break
                if not isinstance(mon_override, dict):
                    continue
                next_abilities: List[object] = []
                for ability in list(getattr(spec, "abilities", []) or []):
                    ability_name = ""
                    if isinstance(ability, dict):
                        ability_name = str(ability.get("name") or "").strip()
                    else:
                        ability_name = str(ability or "").strip()
                    if not ability_name:
                        next_abilities.append(ability)
                        continue
                    ability_override = mon_override.get(ability_name) or mon_override.get(ability_name.lower())
                    if ability_override is None:
                        ability_key = _normalize_ability_key(ability_name)
                        for override_key, override_value in mon_override.items():
                            if _normalize_ability_key(override_key) == ability_key:
                                ability_override = override_value
                                break
                    if not isinstance(ability_override, dict):
                        next_abilities.append(ability)
                        continue
                    payload = dict(ability) if isinstance(ability, dict) else {"name": ability_name}
                    normalized_ability = _normalize_ability_key(ability_name)
                    if normalized_ability == _normalize_ability_key("color theory"):
                        roll = ability_override.get("color_theory_roll")
                        color = ability_override.get("color_theory_color")
                        if roll not in (None, ""):
                            payload["color_theory_roll"] = int(roll)
                        if color:
                            payload["color_theory_color"] = str(color).strip()
                    elif normalized_ability in {
                        _normalize_ability_key("serpent's mark"),
                        _normalize_ability_key("serpent's mark [errata]"),
                    }:
                        roll = ability_override.get("serpents_mark_roll")
                        pattern = ability_override.get("serpents_mark_pattern")
                        if roll not in (None, ""):
                            payload["serpents_mark_roll"] = int(roll)
                        if pattern:
                            payload["serpents_mark_pattern"] = str(pattern).strip()
                    elif normalized_ability == _normalize_ability_key("fabulous trim"):
                        style = ability_override.get("fabulous_trim_style")
                        if style:
                            payload["fabulous_trim_style"] = str(style).strip()
                    elif normalized_ability == _normalize_ability_key("giver"):
                        roll = ability_override.get("giver_choice_roll")
                        if roll not in (None, ""):
                            try:
                                parsed_roll = int(roll)
                            except (TypeError, ValueError):
                                parsed_roll = 0
                            if parsed_roll in {1, 5}:
                                payload["giver_choice_roll"] = parsed_roll
                    next_abilities.append(payload)
                spec.abilities = next_abilities

    def _auto_select_ai_starters(self, matchup: MatchupSpec, plan: MatchPlan) -> None:
        sides = matchup.sides
        if not sides:
            sides = matchup.sides_or_default()
            matchup.sides = sides
        if not sides:
            return
        active_limit = max(1, int(plan.active_slots or 1))
        for side in sides:
            controller = str(getattr(side, "controller", "") or "").strip().lower()
            if self.mode != "ai" and controller != "ai":
                continue
            opponents = [other for other in sides if other is not side]
            if not opponents or len(side.pokemon) <= active_limit:
                continue
            ranked = sorted(
                list(side.pokemon),
                key=lambda spec: self._starter_selection_score(spec, opponents),
                reverse=True,
            )
            side.pokemon = ranked

    def _starter_selection_score(self, spec: object, opponents: List[TrainerSideSpec]) -> float:
        level = float(getattr(spec, "level", 1) or 1)
        hp_stat = float(getattr(spec, "hp_stat", 1) or 1)
        atk = float(getattr(spec, "atk", 1) or 1)
        defense = float(getattr(spec, "defense", 1) or 1)
        spatk = float(getattr(spec, "spatk", 1) or 1)
        spdef = float(getattr(spec, "spdef", 1) or 1)
        spd = float(getattr(spec, "spd", 1) or 1)
        own_types = {str(kind).strip().lower() for kind in (getattr(spec, "types", []) or []) if str(kind).strip()}
        own_move_score = 0.0
        for move in list(getattr(spec, "moves", []) or []):
            category = str(getattr(move, "category", "") or "").strip().lower()
            if category == "status":
                continue
            db = float(getattr(move, "db", 0) or 0)
            stab = 1.5 if str(getattr(move, "type", "") or "").strip().lower() in own_types else 1.0
            attack_stat = spatk if category == "special" else atk
            own_move_score = max(own_move_score, (db * stab) + (attack_stat * 0.8))
        matchup_pressure = 0.0
        for other in opponents:
            for foe in list(getattr(other, "pokemon", []) or []):
                foe_level = float(getattr(foe, "level", 1) or 1)
                foe_hp = float(getattr(foe, "hp_stat", 1) or 1)
                foe_def = float(getattr(foe, "defense", 1) or 1)
                foe_spdef = float(getattr(foe, "spdef", 1) or 1)
                own_bulk = hp_stat + defense + spdef
                foe_bulk = foe_hp + foe_def + foe_spdef
                matchup_pressure += ((own_move_score + level) - (foe_bulk * 0.35)) + ((own_bulk * 0.12) - (foe_level * 0.2))
        speed_bonus = spd * 1.1
        bulk_bonus = (hp_stat * 0.6) + (defense * 0.35) + (spdef * 0.35)
        return matchup_pressure + speed_bonus + bulk_bonus

    def _normalize_side_name_key(self, value: object) -> str:
        raw = str(value or "").strip().lower()
        if not raw:
            return ""
        if "player" in raw:
            return "player"
        if "foe" in raw or "enemy" in raw or "rival" in raw:
            return "foe"
        return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in raw).strip("_")

    def _apply_side_names_to_plan(self, plan: MatchPlan, side_names: dict) -> None:
        normalized = {
            self._normalize_side_name_key(key): str(value).strip()
            for key, value in side_names.items()
            if str(value or "").strip()
        }
        if not normalized:
            return
        for matchup in plan.matchups:
            for side in matchup.sides or []:
                key = self._normalize_side_name_key(side.team or side.identifier or side.name)
                if key and key in normalized:
                    side.name = normalized[key]

    def _apply_side_names_to_battle(self, battle: BattleState, side_names: dict) -> None:
        normalized = {
            self._normalize_side_name_key(key): str(value).strip()
            for key, value in side_names.items()
            if str(value or "").strip()
        }
        if not normalized:
            return
        for trainer in battle.trainers.values():
            key = self._normalize_side_name_key(getattr(trainer, "team", None) or getattr(trainer, "identifier", None) or getattr(trainer, "name", None))
            if key and key in normalized:
                trainer.name = normalized[key]

    def _build_random_multi_side_plan(
        self,
        *,
        side_count: int,
        team_size: int,
        min_level: int,
        max_level: int,
        seed: Optional[int],
        csv_root: Optional[str],
    ) -> MatchPlan:
        repo = PTUCsvRepository(root=csv_root, rng=random.Random(seed))
        builder = CsvRandomCampaignBuilder(repo=repo, seed=seed)
        if not repo.available():
            raise FileNotFoundError(
                f"CSV bundle not found under {repo.root}. Drop the Fancy PTU files there first."
            )
        records = [record for record in repo.iter_species() if builder._is_playable_species(record)]
        if not records:
            raise ValueError("Failed to load species records from the CSV bundle.")
        clamped_min = max(1, min(int(min_level), int(max_level)))
        clamped_max = max(clamped_min, int(max_level))
        sides: List[TrainerSideSpec] = []
        for idx in range(side_count):
            mons = [
                builder._random_mon(records, clamped_min, clamped_max, prefix=f"Side {idx + 1}")
                for _ in range(team_size)
            ]
            side_id = f"side{idx + 1}"
            sides.append(
                TrainerSideSpec(
                    identifier=side_id,
                    name=f"Side {idx + 1}",
                    controller="ai",
                    team=side_id,
                    ai_level="standard",
                    pokemon=mons,
                )
            )
        base = default_campaign()
        matchup = MatchupSpec(
            you=sides[0].pokemon[0],
            foe=sides[1].pokemon[0],
            label=f"{side_count}-way Random Battle",
            sides=sides,
        )
        return MatchPlan(
            matchups=[matchup],
            weather=base.default_weather,
            grid=base.grid,
            battle_context="full_contact",
            active_slots=1,
            description=f"Random {side_count}-side encounter generated from CSV data.",
            seed=seed,
        )

    def _build_battle_royale_plan(
        self,
        *,
        side_count: int,
        team_size: int,
        min_level: int,
        max_level: int,
        seed: Optional[int],
        csv_root: Optional[str],
    ) -> MatchPlan:
        repo = PTUCsvRepository(root=csv_root, rng=random.Random(seed))
        builder = CsvRandomCampaignBuilder(repo=repo, seed=seed)
        if not repo.available():
            raise FileNotFoundError(
                f"CSV bundle not found under {repo.root}. Drop the Fancy PTU files there first."
            )
        records = [record for record in repo.iter_species() if builder._is_playable_species(record)]
        if not records:
            raise ValueError("Failed to load species records from the CSV bundle.")
        clamped_min = max(1, min(int(min_level), int(max_level)))
        clamped_max = max(clamped_min, int(max_level))
        sides: List[TrainerSideSpec] = []
        for idx in range(side_count):
            mons = [
                builder._random_mon(records, clamped_min, clamped_max, prefix=f"Royale {idx + 1}")
                for _ in range(team_size)
            ]
            side_id = f"side{idx + 1}"
            sides.append(
                TrainerSideSpec(
                    identifier=side_id,
                    name=f"Side {idx + 1}",
                    controller="ai",
                    team=side_id,
                    ai_level="standard",
                    pokemon=mons,
                )
            )
        grid = self._build_royale_grid(seed=seed)
        base = default_campaign()
        matchup = MatchupSpec(
            you=sides[0].pokemon[0],
            foe=sides[1].pokemon[0],
            label=f"{side_count}-way Battle Royale",
            sides=sides,
        )
        return MatchPlan(
            matchups=[matchup],
            weather=base.default_weather,
            grid=grid,
            battle_context="full_contact",
            active_slots=max(1, min(3, team_size)),
            description=f"Battle royale with {side_count} sides.",
            seed=seed,
        )

    def _build_royale_grid(self, *, seed: Optional[int]) -> GridSpec:
        rng = random.Random(seed if seed is not None else random.randint(1, 10_000_000))
        width = 42
        height = 42
        blockers: set[Tuple[int, int]] = set()
        tiles: Dict[Tuple[int, int], Dict[str, object]] = {}

        for x in range(width):
            for y in range(height):
                roll = rng.random()
                if roll < 0.52:
                    tile_type = "grassland"
                elif roll < 0.67:
                    tile_type = "forest"
                elif roll < 0.76:
                    tile_type = "wetlands"
                elif roll < 0.84:
                    tile_type = "lake"
                elif roll < 0.9:
                    tile_type = "sea"
                elif roll < 0.95:
                    tile_type = "mountain"
                else:
                    tile_type = "cave"
                tiles[(x, y)] = {"type": tile_type}

                if tile_type in {"forest", "mountain"} and rng.random() < 0.08:
                    blockers.add((x, y))
                    tiles[(x, y)] = {"type": "tree" if tile_type == "forest" else "rock"}

                if tile_type == "sea" and rng.random() < 0.2:
                    blockers.add((x, y))
                    tiles[(x, y)] = {"type": "deep_sea"}

        return GridSpec(width=width, height=height, blockers=sorted(blockers), tiles=tiles)

    def _init_battle_royale_state(self, battle: BattleState, *, interval: int) -> Dict[str, Any]:
        grid = battle.grid
        if grid is None:
            return {"enabled": False}
        center = (grid.width // 2, grid.height // 2)
        start_radius = max(6, min(grid.width, grid.height) // 2 - 2)
        return {
            "enabled": True,
            "interval": max(1, int(interval)),
            "center": [center[0], center[1]],
            "current_radius": int(start_radius),
            "min_radius": 5,
            "shrink_step": 2,
            "damage_divisor": 8,
            "last_close_round": 0,
            "last_damage_round": 0,
        }

    def _apply_battle_royale_circle_if_needed(self, battle: BattleState) -> None:
        state = self._battle_royale_state
        if not state or not state.get("enabled"):
            return
        setattr(battle, "_battle_royale_state", state)
        grid = battle.grid
        if grid is None:
            return
        interval = max(1, int(state.get("interval", 3)))
        current_round = int(getattr(battle, "round", 1) or 1)
        if current_round <= 0:
            return
        if current_round % interval != 0:
            return
        if int(state.get("last_close_round", 0)) == current_round:
            return

        cx, cy = int(state["center"][0]), int(state["center"][1])
        current_radius = int(state.get("current_radius", 10))
        min_radius = int(state.get("min_radius", 5))
        shrink_step = max(1, int(state.get("shrink_step", 2)))
        next_radius = max(min_radius, current_radius - shrink_step)
        state["current_radius"] = next_radius
        state["last_close_round"] = current_round

        for x in range(grid.width):
            for y in range(grid.height):
                if max(abs(x - cx), abs(y - cy)) > next_radius:
                    meta = dict(grid.tiles.get((x, y), {}))
                    meta["type"] = "storm"
                    meta["zone"] = "danger"
                    grid.tiles[(x, y)] = meta

        damage_divisor = max(4, int(state.get("damage_divisor", 8)))
        damaged = 0
        for cid, mon in battle.pokemon.items():
            if mon.fainted or not mon.active or mon.position is None:
                continue
            footprint = mon.footprint_tiles(grid) or {mon.position}
            if all(max(abs(x - cx), abs(y - cy)) <= next_radius for x, y in footprint):
                continue
            damage = max(1, int(mon.max_hp() // damage_divisor))
            mon.apply_damage(damage)
            damaged += 1
            battle.log_event(
                {
                    "type": "terrain",
                    "actor": cid,
                    "effect": "battle_royale_circle",
                    "amount": damage,
                    "description": "The storm circle closes and deals damage outside the safe zone.",
                    "target_hp": mon.hp,
                    "round": current_round,
                }
            )
        state["last_damage_round"] = current_round
        if damaged:
            battle.log_event(
                {
                    "type": "phase",
                    "description": f"Battle Royale circle closed to radius {next_radius}. {damaged} combatant(s) took storm damage.",
                    "round": current_round,
                }
            )

    def snapshot(self) -> dict:
        battle = self.battle
        if battle is None:
            return {"status": "no_battle"}
        self._apply_battle_royale_circle_if_needed(battle)
        self._flush_battle_log_events(battle)
        self._finalize_battle_log_if_finished(battle)
        battle_over = bool(self.session and self.session._battle_finished(battle))
        alive_teams: List[str] = []
        if self.session:
            try:
                alive_teams = sorted(self.session._alive_teams(battle))
            except Exception:
                alive_teams = []
        winner_team: Optional[str] = alive_teams[0] if battle_over and len(alive_teams) == 1 else None
        winner_label: Optional[str] = None
        winner_is_player: Optional[bool] = None
        if battle_over:
            if winner_team:
                winner_names: List[str] = []
                winner_is_player = False
                for trainer in battle.trainers.values():
                    team_key = trainer.team or trainer.identifier
                    if team_key != winner_team:
                        continue
                    trainer_name = str(trainer.name or trainer.identifier or winner_team).strip()
                    if trainer_name and trainer_name not in winner_names:
                        winner_names.append(trainer_name)
                    if getattr(trainer, "controller_kind", "") == "player":
                        winner_is_player = True
                winner_label = " / ".join(winner_names) if winner_names else str(winner_team)
            else:
                winner_label = "Draw"
            if not getattr(self, "_ai_model_rating_recorded", False):
                try:
                    ai_record_battle_outcome(
                        winner_is_ai=None if winner_is_player is None else not winner_is_player,
                        ai_mode=str(self.mode or "player"),
                    )
                except Exception:
                    pass
                self._ai_model_rating_recorded = True
        markers = _combatant_markers(battle)
        ordered = _ordered_combatants(battle)
        combatants: List[dict] = []
        trainers_payload: List[dict] = []
        for trainer in battle.trainers.values():
            trainers_payload.append(
                {
                    "id": trainer.identifier,
                    "name": trainer.name or trainer.identifier,
                    "team": trainer.team or trainer.identifier,
                    "controller_kind": getattr(trainer, "controller_kind", ""),
                }
            )
        occupants: Dict[str, str] = {}
        for cid in ordered:
            state = battle.pokemon[cid]
            state._sync_parfumier_moves()
            trainer = battle.trainers.get(state.controller_id)
            trainer_label = trainer.name if trainer and trainer.name else state.controller_id
            team = (trainer.team or trainer.identifier) if trainer else state.controller_id
            pos = state.position
            footprint_tiles = sorted(
                tile
                for tile in state.footprint_tiles(battle.grid)
                if battle.grid is None or battle.grid.in_bounds(tile)
            )
            if state.active and footprint_tiles:
                for tile in footprint_tiles:
                    occupants[f"{tile[0]},{tile[1]}"] = cid
            moves = []
            for move in state.spec.moves:
                name = str(move.name or "").strip()
                if not name:
                    continue
                move_source_map = getattr(state.spec, "move_sources", {}) or {}
                payload = {
                    "name": name,
                    "type": move.type,
                    "category": move.category,
                    "db": move.db,
                    "ac": move.ac,
                    "range": move.range_text or move.range_kind,
                    "target": move.target_kind,
                    "freq": move.freq,
                    "priority": move.priority,
                    "keywords": list(move.keywords),
                    "effects": move.effects_text,
                    "source": str(move_source_map.get(_normalize_move_key(name), "") or ""),
                }
                move_name = name.lower()
                if move_name == "conversion":
                    options = battle._conversion_type_options(state)
                    payload["type_options"] = options
                    payload["requires_type_choice"] = len(options) > 1
                elif move_name == "conversion2":
                    options = battle._conversion2_type_options(cid)
                    payload["type_options"] = options
                    payload["requires_type_choice"] = len(options) > 1
                    payload["last_damage_taken"] = battle._last_damage_taken_info(cid) or None
                moves.append(payload)
            held_items: List[dict] = []
            passive_item_effects: List[str] = []
            for item in getattr(state.spec, "items", []) or []:
                raw = item if isinstance(item, dict) else {}
                name = str((raw.get("name") if isinstance(raw, dict) else None) or item or "").strip()
                if not name:
                    continue
                is_weapon = False
                if isinstance(raw, dict):
                    kind = str(raw.get("kind") or "").strip().lower()
                    weapon_type = str(raw.get("weapon_type") or "").strip().lower()
                    is_weapon = bool(raw.get("weapon")) or kind == "weapon" or weapon_type in {"melee", "ranged"}
                equipped = bool(raw.get("equipped")) if isinstance(raw, dict) else True
                visible_on_token = equipped if is_weapon else True
                effect_summary, effect_description = _describe_item_effects(state, item)
                passive_item_effects.extend(effect_summary)
                held_items.append(
                    {
                        "name": name,
                        "taste": str(raw.get("taste") or "") if isinstance(raw, dict) else "",
                        "equipped": equipped,
                        "visible_on_token": visible_on_token,
                        "kind": str(raw.get("kind") or "") if isinstance(raw, dict) else "",
                        "slot": str(raw.get("slot") or "") if isinstance(raw, dict) else "",
                        "effect_summary": effect_summary,
                        "effect_description": effect_description,
                    }
                )
            nature_name = str(getattr(state.spec, "nature", "") or "").strip()
            nature_data = nature_profile(nature_name) if nature_name else None
            serialized_nature = None
            if isinstance(nature_data, dict):
                serialized_nature = {
                    "name": str(nature_data.get("name") or nature_name),
                    "raise": str(nature_data.get("raise") or ""),
                    "lower": str(nature_data.get("lower") or ""),
                    "modifiers": dict(nature_data.get("modifiers") or {}),
                }
            trainer_features = _trainer_feature_names(state)
            poke_edges = []
            for entry in getattr(state.spec, "poke_edges", []) or []:
                if isinstance(entry, str):
                    label = entry.strip()
                elif isinstance(entry, dict):
                    label = str(entry.get("name") or entry.get("id") or "").strip()
                else:
                    label = ""
                if label:
                    poke_edges.append(label)
            effective_stats = _effective_stats_payload(state)
            combatants.append(
                {
                    "id": cid,
                    "marker": markers.get(cid, "?"),
                    "name": _display_combatant_name(state),
                    "species": state.spec.species,
                    "level": int(getattr(state.spec, "level", 1) or 1),
                    "nature": nature_name,
                    "nature_profile": serialized_nature,
                    "stat_mode": str(getattr(state.spec, "stat_mode", "pre_nature") or "pre_nature"),
                    "trainer": trainer_label,
                    "team": team,
                    "hp": state.hp,
                    "max_hp": state.max_hp(),
                    "temp_hp": state.temp_hp,
                    "injuries": state.injuries,
                    "statuses": _status_labels(state),
                    "position": list(pos) if pos else None,
                    "mounted_partner_id": battle._mounted_partner_id(cid) if hasattr(battle, "_mounted_partner_id") else None,
                    "mounted_rider_id": battle._mounted_rider_id(cid) if hasattr(battle, "_mounted_rider_id") else None,
                    "mounted_mount_id": battle._mounted_mount_id(cid) if hasattr(battle, "_mounted_mount_id") else None,
                    "size": str(getattr(state.spec, "size", "") or ""),
                    "footprint_side": state.footprint_side(),
                    "footprint_tiles": [list(tile) for tile in footprint_tiles],
                    "active": bool(state.active),
                    "fainted": bool(state.fainted),
                    "combat_stages": dict(state.combat_stages),
                    "abilities": list(state.ability_names()),
                    "base_abilities": _base_ability_names(state),
                    "color_theory": next(
                        (
                            {
                                "roll": int(entry.get("roll", 0) or 0),
                                "color": str(entry.get("color") or "").strip(),
                            }
                            for entry in state.get_temporary_effects("color_theory")
                            if str(entry.get("color") or "").strip()
                        ),
                        None,
                    ),
                    "serpents_mark": next(
                        (
                            {
                                "roll": int(entry.get("roll", 0) or 0),
                                "pattern": str(entry.get("pattern") or "").strip(),
                            }
                            for entry in state.get_temporary_effects("serpents_mark")
                            if str(entry.get("pattern") or "").strip()
                        ),
                        None,
                    ),
                    "fabulous_trim": next(
                        (
                            {
                                "style": str(entry.get("style") or "").strip(),
                            }
                            for entry in state.get_temporary_effects("fabulous_trim")
                            if str(entry.get("style") or "").strip()
                        ),
                        None,
                    ),
                    "moody_state": next(
                        (
                            {
                                "round": int(entry.get("round", 0) or 0),
                                "up_roll": int(entry.get("up_roll", 0) or 0),
                                "up_stat": str(entry.get("up_stat") or "").strip(),
                                "up_delta": int(entry.get("up_delta", 0) or 0),
                                "down_roll": int(entry.get("down_roll", 0) or 0),
                                "down_stat": str(entry.get("down_stat") or "").strip(),
                                "down_delta": int(entry.get("down_delta", 0) or 0),
                                "errata": bool(entry.get("errata")),
                            }
                            for entry in reversed(list(state.get_temporary_effects("moody_state")))
                        ),
                        None,
                    ),
                    "truant_state": next(
                        (
                            {
                                "round": int(entry.get("round", 0) or 0),
                                "roll": int(entry.get("roll", 0) or 0),
                                "skipped": bool(entry.get("skipped")),
                                "heal": int(entry.get("heal", 0) or 0),
                            }
                            for entry in reversed(list(state.get_temporary_effects("truant_state")))
                        ),
                        None,
                    ),
                    "giver_state": (
                        lambda ability_payload, runtime_entry: None
                        if ability_payload is None and runtime_entry is None
                        else {
                            "preference_roll": int(ability_payload.get("giver_choice_roll", 0) or 0)
                            if ability_payload and ability_payload.get("giver_choice_roll") not in (None, "")
                            else None,
                            "preference_mode": (
                                "Heal"
                                if ability_payload and int(ability_payload.get("giver_choice_roll", 0) or 0) == 1
                                else "Damage"
                                if ability_payload and int(ability_payload.get("giver_choice_roll", 0) or 0) == 5
                                else ""
                            ),
                            "last_roll": int(runtime_entry.get("roll", 0) or 0) if runtime_entry else None,
                            "last_effective_db": int(runtime_entry.get("effective_db", 0) or 0)
                            if runtime_entry and runtime_entry.get("effective_db") not in (None, "")
                            else None,
                            "last_mode": str(runtime_entry.get("mode") or "").strip() if runtime_entry else "",
                            "round": int(runtime_entry.get("round", 0) or 0) if runtime_entry else None,
                        }
                    )(
                        _find_ability_payload(state.spec, "Giver"),
                        next(iter(reversed(list(state.get_temporary_effects("giver_state")))), None),
                    ),
                    "gimmicks": {
                        "mega_form": str((next(iter(state.get_temporary_effects("mega_form")), None) or {}).get("species") or "").strip() or None,
                        "terastallized": next(
                            (
                                {
                                    "tera_type": str(entry.get("tera_type") or "").strip() or None,
                                    "original_types": list(entry.get("original_types") or []),
                                }
                                for entry in reversed(list(state.get_temporary_effects("terastallized")))
                            ),
                            None,
                        ),
                        "dynamax_active": bool(state.get_temporary_effects("dynamax_active")),
                        "primal_reversion_ready": str((next(iter(state.get_temporary_effects("primal_reversion_ready")), None) or {}).get("source") or "").strip() or None,
                    },
                    "trainer_features": trainer_features,
                    "poke_edges": poke_edges,
                    "poke_edge_choices": dict(getattr(state.spec, "poke_edge_choices", {}) or {}),
                    "capabilities": list(state.capability_names()),
                    "skills": dict(getattr(state.spec, "skills", {}) or {}),
                    "trainer_action_hints": _trainer_action_hints(battle, cid, state),
                    "action_hints": _core_action_hints(battle, cid, state),
                    "items": held_items,
                    "passive_item_effects": list(dict.fromkeys(passive_item_effects)),
                    "sprite_url": sprite_path_for(state.spec.species or state.spec.name),
                    "tutor_points": int(getattr(state.spec, "tutor_points", 0) or 0),
                    "move_sources": dict(getattr(state.spec, "move_sources", {}) or {}),
                    "stats": {
                        "hp": state.spec.hp_stat,
                        "atk": state.spec.atk,
                        "def": state.spec.defense,
                        "spatk": state.spec.spatk,
                        "spdef": state.spec.spdef,
                        "spd": state.spec.spd,
                    },
                    "effective_stats": effective_stats,
                    "moves": moves,
                    "actions_taken": {k.value: v for k, v in state.actions_taken.items()},
                }
            )
        grid_payload = None
        if battle.grid is not None:
            tiles = []
            for coord, meta in battle.grid.tiles.items():
                tile_type = ""
                hazards = None
                traps = None
                barriers = None
                frozen_domain = None
                trap_sources = None
                if isinstance(meta, dict):
                    tile_type = str(meta.get("type", "")).lower()
                    hazards = meta.get("hazards")
                    traps = meta.get("traps")
                    barriers = meta.get("barriers")
                    frozen_domain = meta.get("frozen_domain")
                    trap_sources = meta.get("trap_sources")
                    height_value = meta.get("height")
                    difficult_value = bool(meta.get("difficult")) if "difficult" in meta else None
                    obstacle_value = bool(meta.get("obstacle")) if "obstacle" in meta else None
                else:
                    tile_type = str(meta or "").lower()
                    height_value = None
                    difficult_value = None
                    obstacle_value = None
                tiles.append([coord[0], coord[1], tile_type, hazards, traps, barriers, frozen_domain, trap_sources, height_value, difficult_value, obstacle_value])
            grid_payload = {
                "width": battle.grid.width,
                "height": battle.grid.height,
                "blockers": [list(coord) for coord in battle.grid.blockers],
                "tiles": tiles,
                "map": copy.deepcopy(getattr(battle.grid, "map", {}) or {}),
            }
        current = battle.current_actor_id
        current_pos = battle.pokemon[current].position if current and current in battle.pokemon else None
        legal_shifts: List[List[int]] = []
        legal_jumps: List[List[int]] = []
        legal_long_jumps: List[List[int]] = []
        legal_high_jumps: List[List[int]] = []
        legal_frozen_domain_tiles: List[List[int]] = []
        legal_trapper_tiles: List[List[int]] = []
        legal_trapper_anchors: List[List[int]] = []
        if current and current in battle.pokemon:
            for coord in movement.legal_shift_tiles(battle, current):
                legal_shifts.append([coord[0], coord[1]])
            for coord in movement.legal_long_jump_tiles(battle, current):
                payload = [coord[0], coord[1]]
                legal_jumps.append(payload)
                legal_long_jumps.append(payload)
            for coord in movement.legal_high_jump_tiles(battle, current):
                legal_high_jumps.append([coord[0], coord[1]])
            actor = battle.pokemon.get(current)
            if actor is not None and actor.position is not None and actor.has_trainer_feature("Trapper") and battle.grid is not None:
                for x in range(battle.grid.width):
                    for y in range(battle.grid.height):
                        coord = (x, y)
                        if battle._combatant_distance_to_coord(actor, coord) > 6:
                            continue
                        tile_meta = battle.grid.tiles.get(coord, {})
                        tile_type = str(tile_meta.get("type", "") if isinstance(tile_meta, dict) else tile_meta).strip().lower()
                        if coord in battle.grid.blockers or any(token in tile_type for token in ("wall", "blocker", "blocking")):
                            continue
                        legal_trapper_tiles.append([x, y])
                        if len(battle._trapper_cluster(actor.position, coord)) >= 8:
                            legal_trapper_anchors.append([x, y])
            if actor is not None and actor.position is not None and actor.has_trainer_feature("Frozen Domain") and battle.grid is not None:
                for x in range(battle.grid.width):
                    for y in range(battle.grid.height):
                        coord = (x, y)
                        if battle._combatant_distance_to_coord(actor, coord) > 6:
                            continue
                        tile_meta = battle.grid.tiles.get(coord, {})
                        tile_type = str(tile_meta.get("type", "") if isinstance(tile_meta, dict) else tile_meta).strip().lower()
                        if coord in battle.grid.blockers or any(token in tile_type for token in ("wall", "blocker", "blocking", "void")):
                            continue
                        legal_frozen_domain_tiles.append([x, y])
        visible_psychic_residue = _visible_psychic_residue(battle, current)
        move_targets = _move_target_ids(battle, current) if current and current in battle.pokemon else {}
        maneuver_context = _maneuver_context(battle, current) if current and current in battle.pokemon else {}
        maneuver_targets = dict(maneuver_context.get("maneuver_targets") or {})
        maneuvers_payload: List[dict] = []
        if current and current in battle.pokemon:
            for move in _load_maneuver_moves().values():
                maneuvers_payload.append(
                    {
                        "name": str(move.name or ""),
                        "type": move.type,
                        "category": move.category,
                        "db": move.db,
                        "ac": move.ac,
                        "range": move.range_text or move.range_kind,
                        "target": move.target_kind,
                        "freq": move.freq,
                        "priority": move.priority,
                        "keywords": list(move.keywords),
                        "effects": move.effects_text,
                    }
                )
        turn_order: List[dict] = []
        initiative_entries = list(battle.initiative_order or [])
        if initiative_entries:
            index = battle._initiative_index if isinstance(battle._initiative_index, int) else 0
            index = max(0, min(index, len(initiative_entries) - 1))
            rotated = initiative_entries[index:] + initiative_entries[:index]
            seen_counts: Dict[str, int] = {}
            for slot_index, slot in enumerate(rotated):
                actor_id = getattr(slot, "actor_id", "")
                if not actor_id:
                    continue
                actor_state = battle.pokemon.get(actor_id)
                if actor_state is None or not actor_state.active or actor_state.fainted:
                    continue
                seen_counts[actor_id] = seen_counts.get(actor_id, 0) + 1
                trainer = battle.trainers.get(actor_state.controller_id)
                team = (trainer.team or trainer.identifier) if trainer else actor_state.controller_id
                max_priority = 0
                for move in actor_state.spec.moves:
                    try:
                        prio = int(move.priority or 0)
                    except (TypeError, ValueError):
                        prio = 0
                    if prio > max_priority:
                        max_priority = prio
                turn_order.append(
                    {
                        "id": actor_id,
                        "name": actor_state.spec.name or actor_state.spec.species or actor_id,
                        "team": team,
                        "sprite_url": sprite_path_for(actor_state.spec.species or actor_state.spec.name),
                        "initiative_total": getattr(slot, "total", actor_state.spec.spd),
                        "priority": max_priority,
                        "slot_index": slot_index,
                        "occurrence": seen_counts[actor_id],
                    }
                )
        trainer_turn = _trainer_turn_context(battle, current) if current and battle.is_trainer_actor_id(current) else None
        log_payload = list(getattr(battle, "log", []) or [])
        if str(os.environ.get("AUTOPTU_BATTLE_LOG_DIR") or "").strip():
            log_payload = log_payload[-200:]
        return {
            "status": "ok",
            "mode": self.mode,
            "ai_step_mode": self.ai_step_mode,
            "round": battle.round,
            "phase": battle.phase.value if isinstance(battle.phase, TurnPhase) else None,
            "weather": battle.effective_weather(),
            "terrain": battle.terrain,
            "current_actor_id": current,
            "current_actor_is_player": bool(current and battle.is_player_controlled(current)),
            "current_pos": list(current_pos) if current_pos else None,
            "grid": grid_payload,
            "map": copy.deepcopy(getattr(battle.grid, "map", {}) or {}) if battle.grid is not None else {},
            "seed": self.plan.seed if self.plan is not None else None,
            "battle_over": battle_over,
            "winner_team": winner_team,
            "winner_label": winner_label,
            "winner_is_player": winner_is_player,
            "alive_teams": alive_teams,
            "trainers": trainers_payload,
            "combatants": combatants,
            "occupants": occupants,
            "legal_shifts": legal_shifts,
                "legal_jumps": legal_jumps,
                "legal_long_jumps": legal_long_jumps,
                "legal_high_jumps": legal_high_jumps,
                "legal_frozen_domain_tiles": legal_frozen_domain_tiles,
                "legal_trapper_tiles": legal_trapper_tiles,
            "legal_trapper_anchors": legal_trapper_anchors,
            "visible_psychic_residue": visible_psychic_residue,
            "move_targets": move_targets,
            "maneuvers": maneuvers_payload,
            "maneuver_targets": maneuver_targets,
            "maneuver_context": maneuver_context,
            "turn_order": turn_order,
            "trainer_turn": trainer_turn,
            "log": log_payload,
            "pending_prompts": list(self._pending_prompts),
            "battle_royale": copy.deepcopy(self._battle_royale_state),
            "ai_diagnostics": copy.deepcopy(getattr(battle, "_ai_diagnostics", None)),
            "ai_model": ai_model_status(),
            "ai_learning": ai_learning_status(battle),
            "battle_log_path": self._battle_log_path,
        }

    def _serialize_grid_payload(self, grid: Optional[GridState]) -> Optional[dict]:
        if grid is None:
            return None
        tiles = []
        for coord, meta in grid.tiles.items():
            tile_type = ""
            hazards = None
            traps = None
            barriers = None
            frozen_domain = None
            trap_sources = None
            height_value = None
            difficult_value = None
            obstacle_value = None
            if isinstance(meta, dict):
                tile_type = str(meta.get("type", "")).lower()
                hazards = meta.get("hazards")
                traps = meta.get("traps")
                barriers = meta.get("barriers")
                frozen_domain = meta.get("frozen_domain")
                trap_sources = meta.get("trap_sources")
                height_value = meta.get("height")
                difficult_value = bool(meta.get("difficult")) if "difficult" in meta else None
                obstacle_value = bool(meta.get("obstacle")) if "obstacle" in meta else None
            else:
                tile_type = str(meta or "").lower()
            tiles.append([coord[0], coord[1], tile_type, hazards, traps, barriers, frozen_domain, trap_sources, height_value, difficult_value, obstacle_value])
        return {
            "width": grid.width,
            "height": grid.height,
            "blockers": [list(coord) for coord in grid.blockers],
            "tiles": tiles,
            "map": copy.deepcopy(getattr(grid, "map", {}) or {}),
        }

    def _grid_state_from_payload(self, payload: Dict[str, Any]) -> GridState:
        width = int(payload.get("width", 15) or 15)
        height = int(payload.get("height", 10) or 10)
        blockers = {tuple(int(v) for v in coord[:2]) for coord in (payload.get("blockers") or []) if isinstance(coord, (list, tuple)) and len(coord) >= 2}
        tiles: Dict[Tuple[int, int], Dict[str, object]] = {}
        raw_tiles = payload.get("tiles") or []
        if isinstance(raw_tiles, list):
            for entry in raw_tiles:
                if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                    x = int(entry[0])
                    y = int(entry[1])
                    meta: Dict[str, object] = {"type": str(entry[2] or "").strip().lower()}
                    if len(entry) > 3 and entry[3]:
                        meta["hazards"] = dict(entry[3] or {})
                    if len(entry) > 4 and entry[4]:
                        meta["traps"] = dict(entry[4] or {})
                    if len(entry) > 5 and entry[5]:
                        meta["barriers"] = list(entry[5] or [])
                    if len(entry) > 6 and entry[6]:
                        meta["frozen_domain"] = list(entry[6] or [])
                    if len(entry) > 7 and entry[7]:
                        meta["trap_sources"] = dict(entry[7] or {})
                    if len(entry) > 8 and entry[8] not in (None, ""):
                        meta["height"] = int(entry[8])
                    if len(entry) > 9 and entry[9] is not None:
                        meta["difficult"] = bool(entry[9])
                    if len(entry) > 10 and entry[10] is not None:
                        meta["obstacle"] = bool(entry[10])
                    if meta.get("obstacle"):
                        blockers.add((x, y))
                    if any(value not in (None, "", [], {}, False) for value in meta.values()):
                        tiles[(x, y)] = meta
                elif isinstance(entry, dict):
                    x = int(entry.get("x", 0))
                    y = int(entry.get("y", 0))
                    meta = dict(entry.get("meta", {}) or {})
                    if "type" in entry and "type" not in meta:
                        meta["type"] = str(entry.get("type") or "").strip().lower()
                    if meta.get("obstacle"):
                        blockers.add((x, y))
                    if any(value not in (None, "", [], {}, False) for value in meta.values()):
                        tiles[(x, y)] = meta
        return GridState(
            width=width,
            height=height,
            blockers=blockers,
            tiles=tiles,
            map=dict(payload.get("map", {}) or {}),
        )

    def _validate_active_positions_against_grid(self, grid: GridState) -> None:
        battle = self.battle
        if battle is None:
            return
        for actor in battle.pokemon.values():
            if not actor.active or actor.fainted or actor.position is None:
                continue
            for tile in actor.footprint_tiles(grid):
                if not grid.in_bounds(tile):
                    raise ValueError(f"{actor.spec.name or actor.spec.species} would be outside the battlefield on the new map.")
                if tile in grid.blockers:
                    raise ValueError(f"{actor.spec.name or actor.spec.species} would overlap blocking terrain on the new map.")

    def load_battle_grid_for_mapper(self) -> dict:
        battle = self.battle
        if battle is None or battle.grid is None:
            raise ValueError("No active battle grid to load.")
        return {
            "status": "ok",
            "grid": self._serialize_grid_payload(battle.grid),
        }

    def apply_terrain_layout(self, payload: Dict[str, Any]) -> dict:
        battle = self.battle
        if battle is None:
            raise ValueError("No active battle to apply terrain to.")
        grid_payload = payload.get("grid") if isinstance(payload.get("grid"), dict) else payload
        grid_state = self._grid_state_from_payload(dict(grid_payload or {}))
        self._validate_active_positions_against_grid(grid_state)
        battle.grid = grid_state
        return self.snapshot()

    def export_battle_log(self) -> dict:
        battle = self.battle
        if battle is None:
            return {"status": "no_battle", "log": [], "battle_log_path": self._battle_log_path}
        self._apply_battle_royale_circle_if_needed(battle)
        self._flush_battle_log_events(battle)
        self._finalize_battle_log_if_finished(battle)
        alive_teams: List[str] = []
        if self.session:
            try:
                alive_teams = sorted(self.session._alive_teams(battle))
            except Exception:
                alive_teams = []
        winner_team: Optional[str] = alive_teams[0] if len(alive_teams) == 1 else None
        winner_label: Optional[str] = None
        if winner_team:
            winner_names: List[str] = []
            for trainer in battle.trainers.values():
                team_key = trainer.team or trainer.identifier
                if team_key != winner_team:
                    continue
                trainer_name = str(trainer.name or trainer.identifier or winner_team).strip()
                if trainer_name and trainer_name not in winner_names:
                    winner_names.append(trainer_name)
            winner_label = " / ".join(winner_names) if winner_names else winner_team
        return {
            "status": "ok",
            "round": int(getattr(battle, "round", 0) or 0),
            "winner_team": winner_team,
            "winner_label": winner_label,
            "battle_log_path": self._battle_log_path,
            "log": list(getattr(battle, "log", []) or []),
        }

    def _stop_summary(self, battle: BattleState) -> dict:
        alive_teams: List[str] = []
        if self.session:
            try:
                alive_teams = sorted(self.session._alive_teams(battle))
            except Exception:
                alive_teams = []
        battle_over = bool(self.session and self.session._battle_finished(battle))
        winner_team: Optional[str] = alive_teams[0] if battle_over and len(alive_teams) == 1 else None
        winner_label: Optional[str] = None
        if winner_team:
            winner_names: List[str] = []
            for trainer in battle.trainers.values():
                team_key = trainer.team or trainer.identifier
                if team_key != winner_team:
                    continue
                trainer_name = str(trainer.name or trainer.identifier or winner_team).strip()
                if trainer_name and trainer_name not in winner_names:
                    winner_names.append(trainer_name)
            winner_label = " / ".join(winner_names) if winner_names else winner_team
        elif battle_over:
            winner_label = "Draw"
        team_hp: Dict[str, Dict[str, int]] = {}
        for state in battle.pokemon.values():
            trainer = battle.trainers.get(state.controller_id)
            team_key = str((trainer.team or trainer.identifier) if trainer else state.controller_id)
            bucket = team_hp.setdefault(team_key, {"remaining_hp": 0, "active": 0, "fainted": 0})
            if state.fainted:
                bucket["fainted"] += 1
                continue
            bucket["active"] += 1
            bucket["remaining_hp"] += max(0, int(state.hp or 0))
        return {
            "round": int(getattr(battle, "round", 0) or 0),
            "battle_over": battle_over,
            "winner_team": winner_team,
            "winner_label": winner_label,
            "alive_teams": alive_teams,
            "team_summary": team_hp,
        }

    def stop_battle(self) -> dict:
        battle = self.battle
        if battle is None:
            return {"status": "no_battle"}
        self._flush_battle_log_events(battle)
        summary = self._stop_summary(battle)
        self._append_battle_log_line(
            {
                "type": "battle_stopped",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "round": summary["round"],
                "battle_over": summary["battle_over"],
                "winner_team": summary["winner_team"],
                "alive_teams": summary["alive_teams"],
            }
        )
        self._battle_log_closed = True
        final_snapshot = self.snapshot()
        battle_log_path = self._battle_log_path
        self.clear_battle()
        return {
            "status": "ok",
            "stopped": True,
            "result": summary,
            "final_snapshot": final_snapshot,
            "battle_log_path": battle_log_path,
        }

    def clear_battle(self) -> dict:
        self.plan = None
        self.matchup = None
        self.battle = None
        self.session = None
        self.record = None
        self._pending_action = None
        self._pending_prompts = []
        self._prompt_answers = {}
        self.ai_step_mode = False
        self.mode = "player"
        self._battle_royale_state = None
        self._battle_log_path = None
        self._battle_log_cursor = 0
        self._battle_log_closed = False
        return self.snapshot()

    def commit_action(self, payload: Dict[str, Any]) -> dict:
        battle = self.battle
        if battle is None:
            raise ValueError("No active battle.")
        action_payload = dict(payload)
        action_type = str(action_payload.get("type") or "").strip().lower()
        if self.mode == "ai":
            raise ValueError("AI vs AI mode does not accept player actions.")
        preflight = self._preflight_turn_prompts(battle, action_payload.get("actor_id") or battle.current_actor_id)
        if preflight:
            self._pending_action = action_payload
            self._pending_prompts = preflight
            return self.snapshot()
        if action_type == "end_turn":
            self._push_history()
            return self._end_turn_and_advance()
        promptless_actions = {
            "creative_action",
            "delay",
            "disengage",
            "equip_weapon",
            "sprint",
            "intercept",
            "take_breather",
            "trade_standard",
            "unequip_weapon",
            "wake_ally",
            "pickup_item",
            "grapple",
            "manipulate",
        }
        prompts = [] if action_type in promptless_actions else self._simulate_prompts(action_payload)
        if prompts:
            self._pending_action = action_payload
            self._pending_prompts = prompts
            return self.snapshot()
        self._push_history()
        self._apply_action(battle, action_payload, prompt_answers={})
        self._pending_action = None
        self._pending_prompts = []
        self._advance_until_player()
        return self.snapshot()

    def resolve_prompts(self, answers: Dict[str, Any]) -> dict:
        if not self._pending_action:
            return self.snapshot()
        battle = self.battle
        if battle is None:
            raise ValueError("No active battle.")
        self._push_history()
        self._prompt_answers = dict(answers or {})
        action_payload = dict(self._pending_action)
        prompts = list(self._pending_prompts)
        self._pending_action = None
        self._pending_prompts = []
        if action_payload.get("type") == "prompt_only":
            if prompts and prompts[0].get("kind") == "hunger_switch":
                prompt_id = prompts[0].get("id")
                full_choice = bool(self._prompt_answers.get(prompt_id, False))
                actor_id = prompts[0].get("actor_id")
                self._apply_hunger_switch_choice(battle, actor_id, full_choice)
            self._prompt_answers = {}
            if self.mode == "player":
                self._advance_until_player()
            return self.snapshot()
        if prompts and prompts[0].get("kind") == "hunger_switch":
            prompt_id = prompts[0].get("id")
            full_choice = bool(self._prompt_answers.get(prompt_id, False))
            actor_id = prompts[0].get("actor_id")
            self._apply_hunger_switch_choice(battle, actor_id, full_choice)
        self._apply_action(battle, action_payload, prompt_answers=self._prompt_answers)
        self._prompt_answers = {}
        if self.mode == "player":
            self._advance_until_player()
        return self.snapshot()

    def _end_turn_and_advance(self) -> dict:
        battle = self.battle
        if battle is None:
            raise ValueError("No active battle.")
        battle.end_turn()
        battle.advance_turn()
        if self.mode == "player":
            self._advance_until_player()
        return self.snapshot()

    def ai_step(self) -> dict:
        if self.mode != "ai":
            raise ValueError("Not in AI vs AI mode.")
        battle = self.battle
        session = self.session
        record = self.record
        if battle is None or session is None or record is None:
            raise ValueError("No active AI battle.")
        if session._battle_finished(battle):
            return self.snapshot()
        self._push_history()
        entry = battle.advance_turn()
        if entry is None:
            return self.snapshot()
        controller_kind = session._controller_kind_for_actor(battle, entry.actor_id)
        if battle.is_trainer_actor_id(entry.actor_id):
            if controller_kind != "player":
                session._ai_trainer_turn(battle, record, entry.actor_id)
        else:
            if controller_kind != "player":
                try:
                    session._ai_turn(battle, record, entry.actor_id)
                except ValueError:
                    session._ai_skip_turn(battle, entry.actor_id, record)
        battle.end_turn()
        return self.snapshot()

    def undo(self) -> dict:
        if not self._history:
            return self.snapshot()
        last = self._history.pop()
        self.battle = last["battle"]
        self.record = last["record"]
        self._pending_action = last["pending_action"]
        self._pending_prompts = last["pending_prompts"]
        self._prompt_answers = last["prompt_answers"]
        self.mode = last["mode"]
        self.ai_step_mode = last["ai_step_mode"]
        self._battle_royale_state = copy.deepcopy(last.get("battle_royale_state"))
        self._battle_log_path = last.get("battle_log_path")
        self._battle_log_cursor = int(last.get("battle_log_cursor", self._battle_log_cursor))
        self._battle_log_closed = bool(last.get("battle_log_closed", self._battle_log_closed))
        if self.battle is not None:
            self.battle.out_of_turn_prompt = self._out_of_turn_prompt
        return self.snapshot()

    def _push_history(self) -> None:
        if self.battle is None or self.record is None:
            return
        battle_clone = self._clone_battle_for_history(self.battle)
        snapshot = {
            "battle": battle_clone,
            "record": copy.deepcopy(self.record),
            "pending_action": copy.deepcopy(self._pending_action),
            "pending_prompts": copy.deepcopy(self._pending_prompts),
            "prompt_answers": copy.deepcopy(self._prompt_answers),
            "mode": self.mode,
            "ai_step_mode": self.ai_step_mode,
            "battle_royale_state": copy.deepcopy(self._battle_royale_state),
            "battle_log_path": self._battle_log_path,
            "battle_log_cursor": self._battle_log_cursor,
            "battle_log_closed": self._battle_log_closed,
        }
        self._history.append(snapshot)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit :]

    def _apply_action(
        self,
        battle: BattleState,
        payload: Dict[str, Any],
        *,
        prompt_answers: Dict[str, Any],
    ) -> None:
        def prompt_callback(prompt_payload: dict) -> bool:
            if not prompt_payload.get("optional"):
                return True
            prompt_key = _prompt_id(prompt_payload)
            return prompt_answers.get(prompt_key, False)

        battle.out_of_turn_prompt = prompt_callback
        action = self._build_action(battle, payload)
        battle.queue_action(action)
        while battle.resolve_next_action() is not None:
            continue

    def _simulate_prompts(self, payload: Dict[str, Any]) -> List[dict]:
        battle = self.battle
        if battle is None:
            return []
        clone = copy.deepcopy(battle)
        prompts: List[dict] = []

        def prompt_callback(prompt_payload: dict) -> bool:
            if prompt_payload.get("optional"):
                prompt = dict(prompt_payload)
                prompt["id"] = _prompt_id(prompt_payload)
                prompts.append(prompt)
            return True

        clone.out_of_turn_prompt = prompt_callback
        action = self._build_action(clone, payload)
        clone.queue_action(action)
        while clone.resolve_next_action() is not None:
            continue
        return prompts

    def _clone_battle_for_history(self, battle: BattleState) -> BattleState:
        def clone_trainer(trainer: TrainerState) -> TrainerState:
            clone = copy.copy(trainer)
            clone.actions_taken = dict(trainer.actions_taken)
            return clone

        def clone_pokemon(mon: PokemonState) -> PokemonState:
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

        trainers = {key: clone_trainer(trainer) for key, trainer in battle.trainers.items()}
        pokemon = {key: clone_pokemon(mon) for key, mon in battle.pokemon.items()}
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
        clone.damage_received_this_round = dict(battle.damage_received_this_round)
        clone.fainted_history = copy.deepcopy(battle.fainted_history)
        clone.dance_moves_used_this_round = dict(battle.dance_moves_used_this_round)
        clone.echoed_voice_rounds = list(battle.echoed_voice_rounds)
        clone.fusion_bolt_rounds = list(battle.fusion_bolt_rounds)
        clone.fusion_flare_rounds = list(battle.fusion_flare_rounds)
        clone.declared_actions = copy.deepcopy(battle.declared_actions)
        clone._injuries_last_round = dict(battle._injuries_last_round)
        clone._injuries_previous_round = dict(battle._injuries_previous_round)
        clone.zone_effects = copy.deepcopy(battle.zone_effects)
        clone.room_effects = copy.deepcopy(battle.room_effects)
        clone.tailwind_teams = set(battle.tailwind_teams)
        clone.wishes = copy.deepcopy(battle.wishes)
        clone.delayed_hits = copy.deepcopy(battle.delayed_hits)
        clone._last_action_actor_id = battle._last_action_actor_id
        clone.extension_packs = battle.extension_packs
        clone.log = copy.deepcopy(battle.log)
        clone._action_queue = copy.deepcopy(battle._action_queue)
        clone.out_of_turn_prompt = None
        setattr(clone, "_ai_diagnostics", copy.deepcopy(getattr(battle, "_ai_diagnostics", None)))
        clone.injury_stage_loss_enabled = getattr(battle, "injury_stage_loss_enabled", False)
        for mon_id, mon in clone.pokemon.items():
            setattr(mon, "_battle_id", mon_id)
            setattr(mon, "_injury_stage_loss_rng", clone.rng)
            setattr(mon, "_injury_stage_loss_enabled", clone.injury_stage_loss_enabled)
            setattr(mon, "_injury_stage_loss_logger", clone.log_event)
        return clone

    def _spec_with_runtime_fallback_moves(self, spec):
        clone = copy.deepcopy(spec)
        normalized = {_normalize_move_key(getattr(move, "name", "")) for move in (clone.moves or [])}
        if "struggle" not in normalized:
            clone.moves.append(_runtime_struggle_move())
        return clone

    def _build_action(self, battle: BattleState, payload: Dict[str, Any]):
        action_type = str(payload.get("type") or "").strip().lower()
        actor_id = payload.get("actor_id") or battle.current_actor_id
        if not actor_id:
            raise ValueError("No actor selected.")
        if action_type == "move":
            move_name = payload.get("move") or payload.get("move_name")
            if not move_name:
                raise ValueError("Move name is required.")
            target_id = payload.get("target_id")
            return UseMoveAction(
                actor_id=actor_id,
                move_name=move_name,
                target_id=target_id,
                mega_evolve=bool(payload.get("mega_evolve")),
                dynamax=bool(payload.get("dynamax")),
                z_move=bool(payload.get("z_move")),
                teracrystal=bool(payload.get("teracrystal") or payload.get("terastallize")),
                tera_type=payload.get("tera_type"),
                chosen_type=payload.get("chosen_type") or payload.get("type_choice"),
            )
        if action_type == "shift":
            dest = payload.get("destination") or payload.get("dest")
            if dest and isinstance(dest, (list, tuple)) and len(dest) >= 2:
                destination = (int(dest[0]), int(dest[1]))
            else:
                destination = (int(payload.get("x")), int(payload.get("y")))
            return ShiftAction(actor_id=actor_id, destination=destination)
        if action_type == "jump":
            dest = payload.get("destination") or payload.get("dest")
            if dest and isinstance(dest, (list, tuple)) and len(dest) >= 2:
                destination = (int(dest[0]), int(dest[1]))
            else:
                destination = (int(payload.get("x")), int(payload.get("y")))
            return JumpAction(
                actor_id=actor_id,
                destination=destination,
                jump_kind=str(payload.get("jump_kind") or "long").strip().lower(),
            )
        if action_type == "delay":
            target_total = payload.get("target_total")
            if target_total in (None, ""):
                raise ValueError("Delay requires a lower initiative target.")
            return DelayAction(actor_id=actor_id, target_total=int(target_total))
        if action_type == "disengage":
            dest = payload.get("destination") or payload.get("dest")
            if dest and isinstance(dest, (list, tuple)) and len(dest) >= 2:
                destination = (int(dest[0]), int(dest[1]))
            else:
                destination = (int(payload.get("x")), int(payload.get("y")))
            return DisengageAction(actor_id=actor_id, destination=destination)
        if action_type == "switch":
            replacement_id = payload.get("replacement_id") or payload.get("target_id")
            if not replacement_id:
                raise ValueError("Switch requires a replacement.")
            dest = payload.get("target_position") or payload.get("destination") or payload.get("dest")
            target_position = None
            if isinstance(dest, (list, tuple)) and len(dest) >= 2:
                target_position = (int(dest[0]), int(dest[1]))
            elif payload.get("x") is not None and payload.get("y") is not None:
                target_position = (int(payload.get("x")), int(payload.get("y")))
            return SwitchAction(
                actor_id=actor_id,
                replacement_id=str(replacement_id),
                target_position=target_position,
            )
        if action_type == "trainer_switch":
            outgoing_id = payload.get("outgoing_id")
            replacement_id = payload.get("replacement_id") or payload.get("target_id")
            if not outgoing_id or not replacement_id:
                raise ValueError("Trainer Switch requires outgoing and replacement combatants.")
            dest = payload.get("target_position") or payload.get("destination") or payload.get("dest")
            target_position = None
            if isinstance(dest, (list, tuple)) and len(dest) >= 2:
                target_position = (int(dest[0]), int(dest[1]))
            elif payload.get("x") is not None and payload.get("y") is not None:
                target_position = (int(payload.get("x")), int(payload.get("y")))
            return TrainerSwitchAction(
                actor_id=str(actor_id),
                outgoing_id=str(outgoing_id),
                replacement_id=str(replacement_id),
                target_position=target_position,
                forced=bool(payload.get("forced")),
            )
        if action_type == "sprint":
            return SprintAction(actor_id=actor_id)
        if action_type == "take_breather":
            return TakeBreatherAction(actor_id=actor_id)
        if action_type == "trade_standard":
            target_action = payload.get("target_action") or payload.get("action") or payload.get("to_action")
            if not target_action:
                raise ValueError("Trade Standard requires a target action.")
            return TradeStandardForAction(actor_id=actor_id, target_action=str(target_action))
        if action_type == "intercept":
            ally_id = payload.get("ally_id") or payload.get("target_id")
            kind = str(payload.get("kind") or payload.get("intercept_kind") or "melee").strip().lower()
            if not ally_id:
                raise ValueError("Intercept requires an ally target.")
            return InterceptAction(actor_id=actor_id, kind=kind, ally_id=str(ally_id))
        if action_type == "wake_ally":
            target_id = payload.get("target_id")
            if not target_id:
                raise ValueError("Wake Ally requires a target.")
            return WakeAllyAction(actor_id=actor_id, target_id=str(target_id))
        if action_type == "pickup_item":
            return PickupItemAction(actor_id=actor_id)
        if action_type == "grapple":
            action_kind = str(payload.get("action_kind") or payload.get("kind") or "").strip().lower()
            if not action_kind:
                raise ValueError("Grapple actions require an action kind.")
            target_id = payload.get("target_id")
            dest = payload.get("destination") or payload.get("dest")
            destination = None
            if dest and isinstance(dest, (list, tuple)) and len(dest) >= 2:
                destination = (int(dest[0]), int(dest[1]))
            elif payload.get("x") is not None and payload.get("y") is not None:
                destination = (int(payload.get("x")), int(payload.get("y")))
            return GrappleAction(
                actor_id=actor_id,
                action_kind=action_kind,
                target_id=str(target_id) if target_id else None,
                destination=destination,
            )
        if action_type == "manipulate":
            target_id = payload.get("target_id")
            trick = str(payload.get("trick") or payload.get("maneuver") or "Bon Mot").strip()
            if not target_id:
                raise ValueError("Manipulate requires a target.")
            return ManipulateAction(actor_id=actor_id, trick=trick, target_id=str(target_id))
        if action_type == "creative_action":
            dest = payload.get("target_position") or payload.get("destination") or payload.get("dest")
            target_position = None
            if isinstance(dest, (list, tuple)) and len(dest) >= 2:
                target_position = (int(dest[0]), int(dest[1]))
            elif payload.get("x") is not None and payload.get("y") is not None:
                target_position = (int(payload.get("x")), int(payload.get("y")))
            dc = payload.get("dc")
            if dc is not None and str(dc).strip() != "":
                dc = int(dc)
            else:
                dc = None
            return CreativeAction(
                actor_id=actor_id,
                title=str(payload.get("title") or payload.get("label") or "Creative Action").strip(),
                description=str(payload.get("description") or payload.get("detail") or "").strip(),
                skill=str(payload.get("skill") or "").strip(),
                dc=dc,
                capability=str(payload.get("capability") or "").strip() or None,
                target_id=str(payload.get("target_id") or "").strip() or None,
                target_position=target_position,
                opposed_skill=str(payload.get("opposed_skill") or "").strip() or None,
                secondary_skill=str(payload.get("secondary_skill") or "").strip() or None,
                check_mode=str(payload.get("check_mode") or "auto").strip().lower(),
                action_cost=str(payload.get("action_cost") or "standard").strip().lower(),
                note=str(payload.get("note") or "").strip(),
                consequence=str(payload.get("consequence") or "").strip() or None,
                consequence_value=int(payload.get("consequence_value")) if payload.get("consequence_value") not in (None, "") else None,
            )
        if action_type == "item":
            item_index = payload.get("item_index")
            if item_index is None:
                item_name = str(payload.get("item_name") or payload.get("item") or "").strip().lower()
                if not item_name:
                    raise ValueError("Item selection is required.")
                actor = battle.pokemon.get(actor_id)
                if actor is None:
                    raise ValueError("Unknown combatant for item use.")
                for idx, item in enumerate(actor.spec.items or []):
                    name = ""
                    if isinstance(item, dict):
                        name = str(item.get("name") or "").strip().lower()
                    else:
                        name = str(item or "").strip().lower()
                    if name == item_name:
                        item_index = idx
                        break
            if item_index is None:
                raise ValueError("Item selection is required.")
            target_id = payload.get("target_id")
            return UseItemAction(actor_id=actor_id, item_index=int(item_index), target_id=target_id)
        if action_type == "equip_weapon":
            item_index = payload.get("item_index")
            if item_index in (None, ""):
                raise ValueError("Equip Weapon requires an item selection.")
            return EquipWeaponAction(actor_id=actor_id, item_index=int(item_index))
        if action_type == "unequip_weapon":
            return UnequipWeaponAction(actor_id=actor_id)
        if action_type == "trainer_feature":
            action_key = str(payload.get("action_key") or payload.get("feature_action") or "").strip().lower()
            if not action_key:
                raise ValueError("Trainer feature action key is required.")
            kwargs = dict(payload.get("params") or {})
            kwargs.setdefault("actor_id", actor_id)
            for key, value in payload.items():
                if key in {"type", "actor_id", "action_key", "feature_action", "params"} or key in kwargs:
                    continue
                kwargs[key] = value
            return create_trainer_feature_action(action_key, **kwargs)
        if action_type in {"quick_wit_manipulate", "quick_wit_move", "enchanting_gaze", "trickster_follow_up", "dirty_fighting_follow_up", "weapon_finesse_follow_up", "play_them_like_a_fiddle_follow_up", "psychic_resonance_follow_up", "flight", "telepath", "thought_detection", "suggestion", "quick_switch", "mindbreak", "arctic_zeal", "polar_vortex", "psionic_overload_follow_up", "force_of_will_follow_up", "trapper", "psionic_sponge", "frozen_domain"}:
            kwargs = dict(payload.get("params") or {})
            kwargs.setdefault("actor_id", actor_id)
            for key, value in payload.items():
                if key in {"type", "actor_id", "params"} or key in kwargs:
                    continue
                kwargs[key] = value
            return create_trainer_feature_action(action_type, **kwargs)
        raise ValueError(f"Unsupported action type: {action_type}")

    def _advance_until_player(self) -> None:
        battle = self.battle
        if battle is None:
            return
        session = self.session
        record = self.record
        if session is None or record is None:
            return
        while True:
            actor_id = battle.current_actor_id
            if actor_id is None:
                entry = battle.advance_turn()
                if entry is None:
                    return
                actor_id = entry.actor_id
            if battle.is_player_controlled(actor_id):
                preflight = self._preflight_turn_prompts(battle, actor_id)
                if preflight:
                    self._pending_action = {"type": "prompt_only", "actor_id": actor_id}
                    self._pending_prompts = preflight
                return
            controller_kind = session._controller_kind_for_actor(battle, actor_id)
            if battle.is_trainer_actor_id(actor_id):
                if controller_kind != "player":
                    session._ai_trainer_turn(battle, record, actor_id)
            else:
                if controller_kind != "player":
                    try:
                        session._ai_turn(battle, record, actor_id)
                    except ValueError:
                        session._ai_skip_turn(battle, actor_id, record)
            battle.end_turn()
            battle.advance_turn()

    def _action_payload_from_action(self, action: object) -> Dict[str, Any]:
        if isinstance(action, UseMoveAction):
            payload = {
                "type": "move",
                "actor_id": action.actor_id,
                "move": action.move_name,
                "target_id": action.target_id,
            }
            if getattr(action, "chosen_type", ""):
                payload["chosen_type"] = action.chosen_type
            return payload
        if isinstance(action, ShiftAction):
            dest = action.destination
            return {
                "type": "shift",
                "actor_id": action.actor_id,
                "destination": [dest[0], dest[1]],
            }
        if isinstance(action, UseItemAction):
            return {
                "type": "item",
                "actor_id": action.actor_id,
                "item_index": action.item_index,
                "target_id": action.target_id,
            }
        raise ValueError("Unsupported AI action type.")

    def _build_battle_state(
        self,
        plan: MatchPlan,
        matchup: MatchupSpec,
        index: int,
    ) -> BattleState:
        grid_spec = plan.grid
        tiles: Dict[Tuple[int, int], Dict[str, object]] = {}
        for coord, metadata in grid_spec.tiles.items():
            if isinstance(metadata, dict):
                tile_meta = dict(metadata)
            else:
                tile_meta = {"type": str(metadata) if metadata is not None else ""}
            tile_type = tile_meta.get("type")
            if tile_type is not None and not isinstance(tile_type, str):
                tile_meta["type"] = str(tile_type)
            tiles[coord] = tile_meta
        grid_state = GridState(
            width=grid_spec.width,
            height=grid_spec.height,
            blockers=set(grid_spec.blockers),
            tiles=tiles,
            map=dict(getattr(grid_spec, "map", {}) or {}),
        )
        sides = matchup.sides_or_default()
        trainers: Dict[str, TrainerState] = {}
        pokemon_states: Dict[str, PokemonState] = {}
        active_positions: Dict[str, List[Tuple[int, int]]] = {}
        occupied: set[Tuple[int, int]] = set()
        rng = random.Random((plan.seed or 0) + index * 101)
        for side in sides:
            trainer_id = side.identifier or f"trainer-{len(trainers) + 1}"
            controller_kind = "ai" if self.mode == "ai" else side.controller
            base = self._default_origin_for_side(side, grid_state)
            trainer = TrainerState(
                identifier=trainer_id,
                name=side.name,
                position=base,
                initiative_modifier=side.initiative_modifier,
                speed=side.speed,
                skills=dict(side.skills),
                save_bonus_base=side.save_bonus,
                evasion_phys=side.evasion_phys,
                evasion_spec=side.evasion_spec,
                evasion_spd=side.evasion_spd,
                controller_kind=controller_kind,
                team=side.team or side.controller,
                ai_level=side.ai_level,
                trainer_class=side.trainer_class.to_dict() if side.trainer_class else {},
                features=[feature.to_dict() for feature in side.trainer_features],
                edges=[edge.to_dict() for edge in side.trainer_edges],
                feature_resources=dict(side.feature_resources),
            )
            trainers[trainer_id] = trainer
            positions = list(side.start_positions)
            active_limit = max(1, int(plan.active_slots))
            active_count = min(len(side.pokemon), active_limit)
            needed = active_count
            if grid_state is None:
                auto_positions: List[Tuple[int, int]] = [(0, idx) for idx in range(needed)]
            else:
                auto_positions = self._allocate_positions(grid_state, base, side.pokemon[:needed], positions, occupied)
            actual_active_count = min(active_count, len(auto_positions))
            active_positions[trainer_id] = list(auto_positions)
            for idx, spec in enumerate(side.pokemon):
                is_active = idx < actual_active_count
                pos = auto_positions[idx] if is_active else None
                mon_id = f"{trainer_id}-{idx + 1}"
                pokemon_states[mon_id] = PokemonState(
                    spec=self._spec_with_runtime_fallback_moves(self._spec_with_backfilled_abilities(spec)),
                    controller_id=trainer_id,
                    position=pos,
                    active=is_active,
                )
                if pos is not None and grid_state is not None:
                    occupied.update(targeting.footprint_tiles(pos, getattr(pokemon_states[mon_id].spec, "size", ""), grid_state))
        battle = BattleState(
            trainers=trainers,
            pokemon=pokemon_states,
            weather=plan.weather,
            grid=grid_state,
            battle_context=plan.battle_context,
            active_slots=plan.active_slots,
            rng=rng,
        )
        return battle

    def _resolve_campaign_spec(
        self,
        *,
        campaign: Optional[str],
        random_battle: bool,
        team_size: int,
        min_level: int,
        max_level: int,
        seed: Optional[int],
        csv_root: Optional[str],
        roster_csv: Optional[str],
        roster_csv_path: Optional[str],
    ):
        if roster_csv:
            spec = campaign_from_roster_csv(
                csv_text=roster_csv,
                csv_root=csv_root,
                default_level=max(1, min_level),
            )
            return spec, "roster-csv"
        if roster_csv_path:
            spec = campaign_from_roster_csv_file(
                path=roster_csv_path,
                csv_root=csv_root,
                default_level=max(1, min_level),
            )
            return spec, f"roster-csv:{roster_csv_path}"
        if random_battle:
            repo = PTUCsvRepository(root=csv_root)
            builder = CsvRandomCampaignBuilder(repo=repo, seed=seed)
            spec = builder.build(team_size=team_size, min_level=min_level, max_level=max_level)
            return spec, "csv-random"
        if campaign:
            try:
                return load_builtin_campaign(campaign), f"builtin:{campaign}"
            except Exception:
                return load_campaign(campaign), str(campaign)
        return default_campaign(), "builtin:demo"

    def _default_origin_for_side(self, side: Any, grid: GridState) -> Tuple[int, int]:
        label = str(side.team or side.controller or "").strip().lower()
        if not label:
            label = str(side.identifier or "").strip().lower()
        if label in {"players", "player", "ally", "allies", "left"}:
            return (0, 0)
        if label in {"foes", "foe", "enemy", "enemies", "right"}:
            return (grid.width - 1, grid.height - 1)
        points = [
            (0, 0),
            (grid.width - 1, 0),
            (grid.width - 1, grid.height - 1),
            (0, grid.height - 1),
            (grid.width // 2, 0),
            (grid.width - 1, grid.height // 2),
            (grid.width // 2, grid.height - 1),
            (0, grid.height // 2),
        ]
        idx = sum(ord(ch) for ch in label) % len(points) if label else 0
        return points[idx]

    def _allocate_positions(
        self,
        grid: GridState,
        origin: Tuple[int, int],
        specs: Iterable[PokemonSpec],
        preferred: Iterable[Tuple[int, int]],
        occupied: set[Tuple[int, int]],
    ) -> List[Tuple[int, int]]:
        positions: List[Tuple[int, int]] = []
        spec_list = list(specs)
        needed = len(spec_list)

        def can_fit(pos: Tuple[int, int], spec: PokemonSpec) -> bool:
            footprint = targeting.footprint_tiles(pos, getattr(spec, "size", ""), grid)
            if not footprint:
                return False
            if any(tile in occupied or tile in grid.blockers for tile in footprint):
                return False
            return all(grid.in_bounds(tile) for tile in footprint)

        def reserve(pos: Tuple[int, int], spec: PokemonSpec) -> None:
            positions.append(pos)
            occupied.update(targeting.footprint_tiles(pos, getattr(spec, "size", ""), grid))

        for pos in preferred:
            if pos in positions:
                continue
            if len(positions) >= needed:
                return positions
            spec = spec_list[len(positions)]
            if not can_fit(pos, spec):
                continue
            reserve(pos, spec)
        ox, oy = origin
        for radius in range(max(grid.width, grid.height)):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if len(positions) >= needed:
                        return positions
                    x = ox + dx
                    y = oy + dy
                    if x < 0 or y < 0 or x >= grid.width or y >= grid.height:
                        continue
                    coord = (x, y)
                    if coord in positions:
                        continue
                    spec = spec_list[len(positions)]
                    if not can_fit(coord, spec):
                        continue
                    reserve(coord, spec)
        return positions

    def _ability_repo_or_none(self) -> Optional[PTUCsvRepository]:
        if self._ability_repo_checked:
            return self._ability_repo
        self._ability_repo_checked = True
        try:
            repo = PTUCsvRepository()
            if repo.available():
                self._ability_repo = repo
        except Exception:
            self._ability_repo = None
        return self._ability_repo

    def _spec_with_backfilled_abilities(self, spec):
        if getattr(spec, "abilities", None):
            return spec
        species_name = str(getattr(spec, "species", "") or getattr(spec, "name", "")).strip()
        if not species_name:
            return spec
        repo = self._ability_repo_or_none()
        if repo is None:
            return spec
        try:
            probe = repo.build_pokemon_spec(
                species_name,
                level=max(1, int(getattr(spec, "level", 1) or 1)),
                assign_abilities=True,
            )
        except Exception:
            return spec
        if not getattr(probe, "abilities", None):
            return spec
        patched = copy.deepcopy(spec)
        patched.abilities = list(probe.abilities)
        return patched

    def _random_field_terrain(self) -> Optional[dict]:
        rng = random.Random()
        choices = [
            "Grassy Terrain",
            "Electric Terrain",
            "Misty Terrain",
            "Psychic Terrain",
            "Gravity Field",
            "Warped Space",
        ]
        name = rng.choice(choices)
        if self._last_random_terrain:
            for _ in range(4):
                if name != self._last_random_terrain:
                    break
                name = rng.choice(choices)
        self._last_random_terrain = name
        return {"name": name, "remaining": rng.randint(3, 6)}

    @staticmethod
    def _stable_seed_value(value: object) -> int:
        text = str(value or "").strip()
        if not text:
            return 0
        try:
            return int(text)
        except (TypeError, ValueError):
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            return int(digest[:16], 16)

    @staticmethod
    def _tile_type_tokens(value: object) -> List[str]:
        text = str(value or "").strip().lower()
        if not text:
            return []
        return [token for token in text.replace(",", " ").split() if token]

    @classmethod
    def _compose_tile_type(
        cls,
        existing: object,
        *,
        terrain_type: Optional[str] = None,
        obstacle: Optional[bool] = None,
        difficult: Optional[bool] = None,
    ) -> str:
        existing_tokens = cls._tile_type_tokens(existing)
        tokens = [token for token in existing_tokens if token not in {"blocker", "blocking", "wall", "difficult", "rough"}]
        if terrain_type is not None:
            terrain = str(terrain_type or "").strip().lower()
            tokens = [terrain] if terrain else []
        if difficult is None:
            difficult = any(token in {"difficult", "rough"} for token in existing_tokens)
        if obstacle is None:
            obstacle = any(token in {"blocker", "blocking", "wall"} for token in existing_tokens)
        if difficult:
            tokens.append("difficult")
        if obstacle:
            tokens.append("blocker")
        return " ".join(dict.fromkeys(tokens))

    @staticmethod
    def _clear_reserved_area(
        blockers: List[Tuple[int, int]],
        tiles: Dict[Tuple[int, int], Dict[str, object]],
        reserved: set[Tuple[int, int]],
    ) -> None:
        reserved_blockers = set(reserved)
        blockers[:] = [coord for coord in blockers if coord not in reserved_blockers]
        for coord in reserved:
            meta = dict(tiles.get(coord, {}) or {})
            meta.pop("hazards", None)
            meta.pop("traps", None)
            meta.pop("barriers", None)
            meta.pop("frozen_domain", None)
            if "type" in meta:
                clean_type = " ".join(
                    token
                    for token in str(meta.get("type") or "").split()
                    if token not in {"blocker", "blocking", "wall", "difficult", "rough"}
                ).strip()
                if clean_type:
                    meta["type"] = clean_type
                else:
                    meta.pop("type", None)
            if meta:
                tiles[coord] = meta
            else:
                tiles.pop(coord, None)

    def _generate_seeded_grid_spec(
        self,
        base_grid: GridSpec,
        *,
        seed: object,
        theme: str = "",
        tileset: str = "",
        occupied: Optional[set[Tuple[int, int]]] = None,
    ) -> GridSpec:
        seed_value = self._stable_seed_value(seed)
        rng = random.Random(seed_value)
        width = int(getattr(base_grid, "width", 15) or 15)
        height = int(getattr(base_grid, "height", 10) or 10)
        blockers: List[Tuple[int, int]] = []
        tiles: Dict[Tuple[int, int], Dict[str, object]] = {}
        occupied = set(occupied or set())
        reserved = set(occupied)
        for ox, oy in list(occupied):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx = ox + dx
                    ny = oy + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        reserved.add((nx, ny))
        active_theme = str(theme or tileset or "").strip().lower()
        base_type_map = {
            "forest": "forest",
            "grassy": "grass",
            "grass": "grass",
            "coast": "water",
            "water": "water",
            "cave": "cave",
            "urban": "urban",
            "desert": "sand",
            "sand": "sand",
            "psychic": "psychic",
            "ice": "ice",
            "snow": "ice",
            "volcanic": "rock",
            "rock": "rock",
            "ruins": "rock",
        }
        accent_type_map = {
            "forest": "water",
            "grassy": "water",
            "grass": "water",
            "coast": "sand",
            "water": "sand",
            "cave": "rock difficult",
            "urban": "urban difficult",
            "desert": "rock",
            "sand": "rock",
            "psychic": "psychic difficult",
            "ice": "water",
            "snow": "water",
            "volcanic": "rock difficult",
            "rock": "sand",
            "ruins": "sand",
        }
        base_type = base_type_map.get(active_theme, "")
        accent_type = accent_type_map.get(active_theme, "difficult")

        def in_bounds(coord: Tuple[int, int]) -> bool:
            return 0 <= coord[0] < width and 0 <= coord[1] < height

        def is_reserved(coord: Tuple[int, int]) -> bool:
            x, y = coord
            if coord in reserved:
                return True
            if x <= 1 and y <= 1:
                return True
            if x >= width - 2 and y >= height - 2:
                return True
            return False

        def flood_patch(tile_type: str, size: int, *, avoid_reserved: bool = True) -> None:
            if size <= 0:
                return
            attempts = 0
            start = None
            while attempts < 60 and start is None:
                attempts += 1
                candidate = (rng.randrange(0, width), rng.randrange(0, height))
                if avoid_reserved and is_reserved(candidate):
                    continue
                if candidate in blockers:
                    continue
                start = candidate
            if start is None:
                return
            frontier = [start]
            seen = {start}
            while frontier and size > 0:
                coord = frontier.pop(0)
                if coord in blockers or (avoid_reserved and is_reserved(coord)):
                    continue
                meta = dict(tiles.get(coord, {}) or {})
                meta["type"] = self._compose_tile_type(meta.get("type"), terrain_type=tile_type)
                if rng.random() < 0.35:
                    meta["height"] = max(0, int(meta.get("height", 0) or 0) + 1)
                tiles[coord] = meta
                size -= 1
                x, y = coord
                neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                rng.shuffle(neighbors)
                for nxt in neighbors:
                    if nxt in seen or not in_bounds(nxt):
                        continue
                    seen.add(nxt)
                    frontier.append(nxt)

        def paint_obstacle_clusters(target: int) -> None:
            attempts = 0
            while len(blockers) < target and attempts < target * 30:
                attempts += 1
                coord = (rng.randrange(0, width), rng.randrange(0, height))
                if coord in blockers or is_reserved(coord):
                    continue
                cluster = [coord]
                if rng.random() < 0.45:
                    x, y = coord
                    neighbor = (x + rng.choice([-1, 1]), y + rng.choice([-1, 0, 1]))
                    if in_bounds(neighbor) and not is_reserved(neighbor):
                        cluster.append(neighbor)
                valid = [tile for tile in cluster if tile not in blockers and not is_reserved(tile)]
                for tile in valid:
                    blockers.append(tile)
                    meta = dict(tiles.get(tile, {}) or {})
                    meta["type"] = self._compose_tile_type(meta.get("type"), obstacle=True)
                    meta["obstacle"] = True
                    meta["height"] = max(1, int(meta.get("height", 0) or 0) + 1)
                    tiles[tile] = meta

        def place_hazards(target: int) -> None:
            hazard_names = ["spikes", "toxic_spikes", "sticky_web", "stealth_rock", "fire_hazards"]
            attempts = 0
            while target > 0 and attempts < 160:
                attempts += 1
                coord = (rng.randrange(0, width), rng.randrange(0, height))
                if is_reserved(coord) or coord in blockers:
                    continue
                meta = dict(tiles.get(coord, {}) or {})
                hazard_name = rng.choice(hazard_names)
                hazards = dict(meta.get("hazards") or {})
                hazards[hazard_name] = max(1, int(hazards.get(hazard_name, 0) or 0) + (1 if rng.random() < 0.25 else 0))
                meta["hazards"] = hazards
                tiles[coord] = meta
                target -= 1

        def paint_linear_feature(tile_type: str, thickness: int, *, orientation: str) -> set[Tuple[int, int]]:
            painted: set[Tuple[int, int]] = set()
            if orientation == "vertical":
                center = rng.randrange(max(2, width // 4), min(width - 2, width - max(2, width // 4)))
                for x in range(center - thickness // 2, center + thickness // 2 + 1):
                    for y in range(0, height):
                        coord = (x, y)
                        if not in_bounds(coord) or is_reserved(coord):
                            continue
                        meta = dict(tiles.get(coord, {}) or {})
                        meta["type"] = self._compose_tile_type(meta.get("type"), terrain_type=tile_type)
                        tiles[coord] = meta
                        painted.add(coord)
            else:
                center = rng.randrange(max(2, height // 4), min(height - 2, height - max(2, height // 4)))
                for y in range(center - thickness // 2, center + thickness // 2 + 1):
                    for x in range(0, width):
                        coord = (x, y)
                        if not in_bounds(coord) or is_reserved(coord):
                            continue
                        meta = dict(tiles.get(coord, {}) or {})
                        meta["type"] = self._compose_tile_type(meta.get("type"), terrain_type=tile_type)
                        tiles[coord] = meta
                        painted.add(coord)
            return painted

        def paint_ring(coords: set[Tuple[int, int]], tile_type: str) -> None:
            if not coords:
                return
            for x, y in list(coords):
                for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not in_bounds(nxt) or is_reserved(nxt) or nxt in blockers or nxt in coords:
                        continue
                    meta = dict(tiles.get(nxt, {}) or {})
                    existing_type = str(meta.get("type") or "")
                    if "water" in existing_type.split():
                        continue
                    meta["type"] = self._compose_tile_type(meta.get("type"), terrain_type=tile_type)
                    tiles[nxt] = meta

        def generate_water_coast_map() -> None:
            orientation = "vertical" if width >= height else "horizontal"
            main_water = paint_linear_feature("water", max(2, min(4, width // 5 if orientation == "vertical" else height // 5)), orientation=orientation)
            if rng.random() < 0.65:
                branch_orientation = "horizontal" if orientation == "vertical" else "vertical"
                branch = paint_linear_feature("water", 2, orientation=branch_orientation)
                main_water.update(branch)
            paint_ring(main_water, "sand")
            for _ in range(max(1, width // 6)):
                flood_patch("sand", rng.randint(3, 6))
            paint_obstacle_clusters(max(2, int(width * height * 0.025)))
            place_hazards(max(1, int(width * height * 0.01)))

        def generate_grassy_map() -> None:
            for _ in range(max(3, int((width * height) * 0.02))):
                flood_patch("grass", rng.randint(4, 8))
            for _ in range(max(2, int((width * height) * 0.012))):
                flood_patch("forest", rng.randint(3, 6))
            for _ in range(max(1, int((width * height) * 0.008))):
                flood_patch("water", rng.randint(2, 4))
            paint_obstacle_clusters(max(3, int(width * height * 0.04)))
            place_hazards(max(2, int(width * height * 0.012)))

        if active_theme in {"water", "coast"}:
            generate_water_coast_map()
        elif active_theme in {"grass", "grassy", "forest"} and str(tileset or "").strip().lower() == "gen4-outside":
            generate_grassy_map()
        else:
            if base_type:
                for _ in range(max(2, int((width * height) * 0.018))):
                    flood_patch(base_type, rng.randint(3, 7))
            for _ in range(max(2, int((width * height) * 0.012))):
                flood_patch(accent_type, rng.randint(3, 6))
            for _ in range(max(1, int((width * height) * 0.008))):
                flood_patch(f"{base_type} difficult" if base_type else "difficult", rng.randint(2, 5))
            paint_obstacle_clusters(max(4, int(width * height * 0.05)))
            place_hazards(max(2, int(width * height * 0.018)))
        self._clear_reserved_area(blockers, tiles, reserved)
        map_meta = {
            "name": f"{(tileset or theme or 'Field').strip().title()} Seed {seed}",
            "seed": str(seed),
            "theme": active_theme or "default",
            "tileset": str(tileset or theme or "default").strip().lower(),
            "generated": True,
        }
        return GridSpec(
            width=width,
            height=height,
            scale=float(getattr(base_grid, "scale", 1.0)),
            blockers=sorted(set(blockers)),
            tiles=tiles,
            map=map_meta,
        )

    def _random_grid_spec(self, base_grid: GridSpec) -> GridSpec:
        rng = random.Random()
        randomized_base = GridSpec(
            width=rng.randint(10, 14),
            height=rng.randint(8, 12),
            scale=float(getattr(base_grid, "scale", 1.0)),
        )
        theme = rng.choice(["grassy", "water", "cave", "urban", "desert", "psychic", "ice", "forest"])
        seed = rng.randint(1, 999999)
        return self._generate_seeded_grid_spec(randomized_base, seed=seed, theme=theme, tileset=theme)
