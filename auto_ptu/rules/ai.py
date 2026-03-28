"""Heuristics for non-player combatants."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from ..data_models import MoveSpec
from .battle_state import BattleState, PokemonState, _load_maneuver_moves, _load_move_specs
from .calculations import expected_damage
from . import move_traits, movement, targeting
from . import ai_hybrid
from . import frequency

_USE_HYBRID_AI = True


def choose_grapple_action(
    battle: BattleState, actor_id: str
) -> Optional[Tuple[str, Optional[Tuple[int, int]]]]:
    status = battle.grapple_status(actor_id)
    if not status:
        return None
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None
    other_id = status.get("other_id")
    if other_id:
        if _has_damaging_move_in_range(battle, actor_id, other_id):
            return None
        # Let the main AI pick an option (including Struggle) if no real damage is available.
        return None
    if status.get("dominant"):
        return ("attack", None)
    if actor.has_capability("Phasing") or actor.has_capability("Teleporter"):
        return ("escape", None)
    return ("contest", None)


def choose_best_move(
    battle: BattleState, actor_id: str, *, ai_level: str = "standard"
) -> Tuple[Optional[MoveSpec], Optional[str], float]:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return None, None, 0.0
    trainer = battle.trainers.get(actor.controller_id)
    actor_team = (trainer.team or trainer.identifier) if trainer else actor.controller_id
    opponents: List[str] = []
    for pid, target in battle.pokemon.items():
        if target.fainted or not target.active or target.position is None:
            continue
        opponent_trainer = battle.trainers.get(target.controller_id)
        target_team = (opponent_trainer.team or opponent_trainer.identifier) if opponent_trainer else target.controller_id
        if target_team != actor_team:
            opponents.append(pid)
    if _should_force_struggle(battle, actor_id, opponents):
        struggle = _load_struggle_move()
        target_id = opponents[0] if opponents else None
        return struggle, target_id, 0.0
    if _USE_HYBRID_AI:
        return ai_hybrid.choose_best_move(battle, actor_id, ai_level=ai_level)
    ai_level = (ai_level or "standard").strip().lower()

    weather = battle.weather
    best_move: Optional[MoveSpec] = None
    best_target: Optional[str] = None
    best_score = float("-inf")
    best_damage_score = float("-inf")
    candidates: List[Tuple[float, float, bool, MoveSpec, Optional[str]]] = []
    has_damage_option = False
    def _team_for(pid: str) -> Optional[str]:
        state = battle.pokemon.get(pid)
        if state is None:
            return None
        trainer = battle.trainers.get(state.controller_id)
        return (trainer.team or trainer.identifier) if trainer else state.controller_id
    for move in actor.spec.moves:
        if _is_interrupt_only_move(move):
            continue
        if not _frequency_available(battle, actor_id, move):
            continue
        requirements = battle.weapon_requirements_for_move(move)
        if requirements:
            weapon_tags = actor.equipped_weapon_tags()
            if not weapon_tags or not any(req.issubset(weapon_tags) for req in requirements):
                continue
        requires_target = targeting.move_requires_target(move)
        candidate_ids: Sequence[Optional[str]] = opponents if requires_target else [None]
        if not candidate_ids:
            candidate_ids = [None]
        for target_id in candidate_ids:
            target_state = battle.pokemon.get(target_id) if target_id else None
            target_team = None
            if requires_target and target_state is None:
                continue
            if target_state is not None:
                if target_state.position is None:
                    continue
                if not targeting.is_target_in_range(actor.position, target_state.position, move):
                    continue
                if battle.grid and not battle.has_line_of_sight(actor_id, target_state.position, target_id):
                    continue
                opponent_trainer = battle.trainers.get(target_state.controller_id)
                target_team = (opponent_trainer.team or opponent_trainer.identifier) if opponent_trainer else target_state.controller_id
            tiles = targeting.affected_tiles(
                battle.grid, actor.position, target_state.position if target_state else None, move
            )
            impacted = _collect_impacted_ids(
                battle=battle,
                tiles=tiles,
                actor_id=actor_id,
                fallback_target=target_id,
                move=move,
            )
            move_category = (move.category or "").lower()
            if not impacted and move_category != "status":
                continue
            if move_category != "status":
                if not any(_team_for(pid) and _team_for(pid) != actor_team for pid in impacted):
                    continue
            damage_score = 0.0
            is_status = move_category == "status"
            if is_status:
                score = _score_status_move(move, actor, target_state, actor_team, target_team)
            else:
                damage_score = _score_impacts(
                    battle=battle,
                    actor_id=actor_id,
                    actor_team=actor_team,
                    impacted_ids=impacted,
                    move=move,
                    weather=weather,
                )
                score = damage_score
                if score <= 0:
                    score -= 0.6
                if damage_score > 0:
                    has_damage_option = True
                    if damage_score > best_damage_score:
                        best_damage_score = damage_score
            score += _combo_description_bonus(battle, actor_id, move, target_state)
            score += _field_bonus_for_move(battle, impacted, ai_level)
            score += _move_type_bonus(
                battle=battle,
                actor=actor,
                actor_id=actor_id,
                move=move,
                target_state=target_state,
                ai_level=ai_level,
                move_category=move_category,
                target_id=target_id,
            )
            score += _recent_move_penalty(battle, actor_id, move, move_category)
            score += _status_redundancy_penalty(actor, target_state, move)
            candidates.append((score, damage_score, is_status, move, target_id))
            if score > best_score:
                best_score = score
                best_move = move
                best_target = target_id
    if _should_force_struggle(battle, actor_id, opponents):
        struggle = _load_struggle_move()
        target_id = opponents[0] if opponents else None
        return struggle, target_id, 0.0
    if not candidates and opponents:
        struggle = _load_struggle_move()
        return struggle, opponents[0], 0.0
    maneuver_move, maneuver_target, maneuver_score = _choose_best_maneuver(battle, actor_id, opponents)
    if maneuver_move and (
        best_damage_score <= 0.0
        or (
            (maneuver_move.name or "").strip().lower() == "grapple"
            and _recent_combo_setup_used(battle, actor_id, ("wrap", "bind", "trap", "clamp", "infestation"))
        )
    ):
        return maneuver_move, maneuver_target, maneuver_score
    if candidates:
        if has_damage_option:
            candidates = [
                entry for entry in candidates
                if entry[1] > 0 or (entry[2] and entry[0] > 1.2)
            ] or candidates
        if ai_level == "strategic":
            threshold = best_score - 2.0
        elif ai_level == "tactical":
            threshold = best_score - 1.2
        else:
            threshold = best_score - 1.0
        near_best = [entry for entry in candidates if entry[0] >= threshold]
        if not near_best:
            return best_move, best_target, best_score
        randomness = 0.2 if ai_level == "strategic" else 0.4 if ai_level == "tactical" else 0.6
        weights = [
            1 + max(0.0, entry[0] - threshold) + randomness * max(0.0, threshold - entry[0])
            for entry in near_best
        ]
        selected = random.choices(near_best, weights=weights, k=1)[0]      
        return selected[3], selected[4], selected[0]
    if opponents and best_damage_score <= 0:
        struggle = _load_struggle_move()
        target_id = opponents[0] if opponents else None
        return struggle, target_id, 0.0
    if best_move:
        return best_move, best_target, best_score
    fallback = _find_any_usable_move(battle, actor_id, actor, actor_team, opponents)
    return fallback[0], fallback[1], 0.0


def _choose_best_maneuver(
    battle: BattleState,
    actor_id: str,
    opponents: Sequence[str],
) -> Tuple[Optional[MoveSpec], Optional[str], float]:
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return None, None, float("-inf")
    best_move: Optional[MoveSpec] = None
    best_target: Optional[str] = None
    best_score = float("-inf")
    maneuvers = _load_maneuver_moves()
    if not maneuvers:
        return None, None, float("-inf")
    for move in maneuvers.values():
        for target_id in opponents:
            target = battle.pokemon.get(target_id)
            if target is None or target.position is None or target.hp is None or target.hp <= 0:
                continue
            if not targeting.is_target_in_range(actor.position, target.position, move):
                continue
            if battle.grid and not battle.has_line_of_sight(actor_id, target.position, target_id):
                continue
            score = _score_maneuver(battle, actor, target, move)
            if score > best_score:
                best_score = score
                best_move = move
                best_target = target_id
    if best_move and best_score > 0:
        return best_move, best_target, best_score
    return None, None, best_score


def _score_maneuver(
    battle: BattleState,
    attacker: PokemonState,
    defender: PokemonState,
    move: MoveSpec,
) -> float:
    name = (move.name or "").strip().lower()
    attacker_rank = max(attacker.skill_rank("combat"), attacker.skill_rank("athletics"))
    defender_rank = max(defender.skill_rank("combat"), defender.skill_rank("athletics"))
    if name == "disarm":
        if not defender.spec.items:
            return -1.0
        defender_rank = max(defender.skill_rank("combat"), defender.skill_rank("stealth"))
        attacker_rank = max(attacker.skill_rank("combat"), attacker.skill_rank("stealth"))
        base = 6.0
    elif name == "trip":
        defender_rank = max(defender.skill_rank("combat"), defender.skill_rank("acrobatics"))
        attacker_rank = max(attacker.skill_rank("combat"), attacker.skill_rank("acrobatics"))
        base = 5.0
        if defender.has_status("Tripped"):
            base = 0.5
    elif name == "push":
        base = 3.0
    elif name == "hinder":
        attacker_rank = attacker.skill_rank("athletics")
        defender_rank = defender.skill_rank("athletics")
        base = 4.0
        if defender.has_status("Hindered"):
            base = 0.5
    elif name == "blind":
        attacker_rank = attacker.skill_rank("stealth")
        defender_rank = defender.skill_rank("stealth")
        base = 4.0
        if defender.has_status("Blinded"):
            base = 0.5
    elif name == "low blow":
        attacker_rank = attacker.skill_rank("acrobatics")
        defender_rank = defender.skill_rank("acrobatics")
        base = 5.0
        if defender.has_status("Vulnerable"):
            base = 0.5
    elif name == "dirty trick":
        base = 4.0
        if defender.has_status("Hindered") and defender.has_status("Blinded") and defender.has_status("Vulnerable"):
            base = 0.5
    elif name == "grapple":
        base = 7.0
        if defender.has_status("Grappled"):
            base = 0.5
    else:
        base = 2.0
    diff = attacker_rank - defender_rank
    win_prob = max(0.1, min(0.9, 0.5 + diff / 20.0))
    return win_prob * base


def _collect_impacted_ids(
    battle: BattleState,
    tiles: Set[Tuple[int, int]],
    actor_id: str,
    fallback_target: Optional[str],
    move: MoveSpec,
) -> List[str]:
    area_kind = targeting.normalized_area_kind(move)
    ids: List[str] = []
    if area_kind == "field" and (battle.grid is None or not tiles):
        ids = [pid for pid, mon in battle.pokemon.items() if mon.hp is not None and mon.hp > 0]
    elif tiles:
        for pid, mon in battle.pokemon.items():
            if mon.hp is None or mon.hp <= 0:
                continue
            if mon.position in tiles:
                ids.append(pid)
    elif fallback_target:
        ids = [fallback_target]
    elif targeting.normalized_target_kind(move) == "self":
        ids = [actor_id]
    return ids


def _score_impacts(
    battle: BattleState,
    actor_id: str,
    actor_team: str,
    impacted_ids: Sequence[str],
    move: MoveSpec,
    weather: Optional[str],
) -> float:
    actor = battle.pokemon[actor_id]
    score = 0.0
    for target_id in impacted_ids:
        target = battle.pokemon.get(target_id)
        if target is None or target.hp is None or target.hp <= 0:
            continue
        trainer = battle.trainers.get(target.controller_id)
        team = (trainer.team or trainer.identifier) if trainer else target.controller_id
        amount = expected_damage(actor, target, move, weather=weather)
        if team == actor_team:
            score -= amount
        else:
            score += amount
    return score


def _score_status_move(
    move: MoveSpec,
    actor: PokemonState,
    target: Optional[PokemonState],
    actor_team: str,
    target_team: Optional[str],
) -> float:
    """Score status/setup moves so the AI prefers buffs or debuffs when useful."""
    base = 0.4
    description = (move.effects_text or "").lower()
    keywords = [
        "boost",
        "raise",
        "increase",
        "heal",
        "charge",
        "focus",
        "protect",
        "guard",
        "defend",
        "shield",
        "restore",
    ]
    for keyword in keywords:
        if keyword in description:
            base += 0.2
    if move_traits.is_setup_move(move):
        base += 0.6
    target_kind = (move.target_kind or "").lower()
    if "self" in target_kind or (move.target_range or 0) == 0:
        base += 0.3
    if target_team:
        if target_team == actor_team:
            base += 0.4
        else:
            base += 0.2
    if "debuff" in description or "lower" in description:
        base += 0.1
    if "status" in description and "inflict" in description:
        base += 0.1
    base += _status_cap_penalty(actor, target, move, description, actor_team, target_team)
    base += _status_immunity_penalty(actor, target, move, description)
    base += _status_no_effect_penalty(actor, target, move, description)
    return base


def _frequency_available(battle: BattleState, actor_id: str, move: MoveSpec) -> bool:
    definition = battle._frequency_definition(move)
    if definition is None or definition.limit is None:
        return True
    usage = battle.frequency_usage.get(actor_id, {}).get(move.name, 0)
    return usage < definition.limit


def _recent_move_penalty(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    move_category: str,
) -> float:
    if not battle.log:
        return 0.0
    move_name = (move.name or "").strip().lower()
    if not move_name:
        return 0.0
    recent: List[dict] = []
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        recent.append(event)
        if len(recent) >= 2:
            break
    if not recent:
        return 0.0
    penalty = 0.0
    last_name = (recent[0].get("move") or "").strip().lower()
    if last_name == move_name:
        penalty -= 1.2
        if int(recent[0].get("damage") or 0) <= 0 and move_category != "status":
            penalty -= 0.6
    if len(recent) > 1:
        prev_name = (recent[1].get("move") or "").strip().lower()
        if prev_name == move_name:
            penalty -= 0.8
    return penalty


def _status_redundancy_penalty(
    actor: PokemonState,
    target: Optional[PokemonState],
    move: MoveSpec,
) -> float:
    text = " ".join(
        [
            (move.name or ""),
            (move.effects_text or ""),
            " ".join(str(entry) for entry in (move.keywords or [])),
        ]
    ).lower()
    penalty = 0.0
    protect_like = ("protect" in text or "guard" in text or "obstruct" in text or "bunker" in text)
    if protect_like:
        for status in actor.statuses:
            name = str(status.get("name", "")).lower()
            if "protect" in name or "guard" in name or "obstruct" in name or "bunker" in name:
                penalty -= 2.0
                break
    if target and ("grapple" in text or "trap" in text or "bind" in text or "wrap" in text):
        if target.has_status("Grappled") or target.has_status("Trapped"):
            penalty -= 1.0
    if "double team" in text:
        entry = next(iter(actor.get_temporary_effects("double_team")), None)
        if entry and int(entry.get("charges", 0) or 0) > 0:
            penalty -= 2.0
    return penalty


def _combo_description_bonus(
    battle: BattleState,
    actor_id: str,
    move: MoveSpec,
    target: Optional[PokemonState],
) -> float:
    text = " ".join(
        [
            str(move.name or ""),
            str(move.effects_text or ""),
            str(move.range_text or ""),
            " ".join(str(entry) for entry in (move.keywords or [])),
        ]
    ).lower()
    if not text:
        return 0.0
    name = (move.name or "").strip().lower()
    target_is_bound = bool(target and (target.has_status("Grappled") or target.has_status("Trapped")))
    wrap_like = any(token in text for token in ("wrap", "bind", "trap", "clamp", "infestation"))
    grapple_like = "grapple" in text or "dominance" in text
    bonus = 0.0
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
    bonus += _conditional_target_combo_bonus(text, target)
    return bonus


def _conditional_target_combo_bonus(
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


def _status_cap_penalty(
    actor: PokemonState,
    target: Optional[PokemonState],
    move: MoveSpec,
    description: str,
    actor_team: str,
    target_team: Optional[str],
) -> float:
    penalty = 0.0
    text = description
    stat_map = {
        "attack": "atk",
        "defense": "def",
        "special attack": "spatk",
        "special defense": "spdef",
        "speed": "spd",
        "accuracy": "accuracy",
        "evasion": "evasion",
    }
    boost_tokens = ("raise", "boost", "increase", "gain", "+1", "+2", "+3")
    drop_tokens = ("lower", "reduce", "-1", "-2", "-3")
    for label, stat_key in stat_map.items():
        if label not in text:
            continue
        if any(token in text for token in boost_tokens):
            if target_team and target_team == actor_team:
                current = actor.combat_stages.get(stat_key, 0)
                if current >= 6:
                    penalty -= 1.5
        if any(token in text for token in drop_tokens):
            if target and target_team and target_team != actor_team:
                current = target.combat_stages.get(stat_key, 0)
                if current <= -6:
                    penalty -= 1.5
    if target and target_team and target_team != actor_team:
        status_tokens = (
            "sleep",
            "paralyz",
            "poison",
            "burn",
            "freeze",
            "confus",
            "trapped",
            "grapple",
            "inflict",
        )
        if any(token in text for token in status_tokens):
            if target.statuses:
                penalty -= 1.0
    return penalty


def _status_immunity_penalty(
    actor: PokemonState,
    target: Optional[PokemonState],
    move: MoveSpec,
    description: str,
) -> float:
    if target is None:
        return 0.0
    text = f"{move.name or ''} {description}".lower()
    target_types = {t.lower().strip() for t in target.spec.types if t}
    penalty = 0.0
    if "poison" in text or "toxic" in text:
        if {"poison", "steel"} & target_types and not actor.has_ability("Corrosion"):
            penalty -= 2.5
    if "burn" in text and "fire" in target_types:
        penalty -= 2.0
    if "paraly" in text and "electric" in target_types:
        penalty -= 2.0
    if "sleep" in text and "grass" in target_types:
        penalty -= 2.0
    if "freeze" in text and "ice" in target_types:
        penalty -= 2.0
    return penalty


def _status_no_effect_penalty(
    actor: PokemonState,
    target: Optional[PokemonState],
    move: MoveSpec,
    description: str,
) -> float:
    text = description.lower()
    penalty = 0.0
    if target is not None and "combat stage" in text:
        if any(token in text for token in ("match", "copy", "swap", "exchange")):
            if actor.combat_stages == target.combat_stages:
                penalty -= 2.0
        if any(token in text for token in ("reset", "clear", "remove")):
            if all(value == 0 for value in target.combat_stages.values()) and all(
                value == 0 for value in actor.combat_stages.values()
            ):
                penalty -= 1.5
    if target is not None and any(token in text for token in ("cure", "remove status", "heal status")):
        if not target.statuses:
            penalty -= 1.0
    return penalty


def _is_interrupt_only_move(move: MoveSpec) -> bool:
    canonical_text = ""
    move_key = (move.name or "").strip().lower()
    for known in _load_move_specs():
        if (known.name or "").strip().lower() != move_key:
            continue
        canonical_text = " ".join(
            [
                str(known.range_text or ""),
                str(known.effects_text or ""),
            ]
        )
        break
    activation = str(frequency.activation_for_move(move.name) or "").strip().lower()
    if activation in {"interrupt", "reaction"}:
        return True
    text = " ".join(
        [
            str(move.range_text or ""),
            str(move.effects_text or ""),
            canonical_text,
        ]
    ).lower()
    if "interrupt" in text or "reaction" in text or "trigger" in text:
        return True
    return False


def _recent_move_events(
    battle: BattleState, actor_id: str, limit: int = 4
) -> List[dict]:
    if not battle.log:
        return []
    events: List[dict] = []
    for event in reversed(battle.log):
        if event.get("actor") != actor_id:
            continue
        if event.get("type") not in {"move", "attack_of_opportunity"}:
            continue
        events.append(event)
        if len(events) >= limit:
            break
    return events


def _should_force_struggle(
    battle: BattleState, actor_id: str, opponents: Sequence[str]
) -> bool:
    if not opponents:
        return False
    recent = _recent_move_events(battle, actor_id, limit=4)
    if len(recent) < 3:
        return False
    if any(int(event.get("damage") or 0) > 0 for event in recent):
        return False
    # If we've missed or dealt zero damage repeatedly, force a struggle to break stalemates.
    return True


def _load_struggle_move() -> MoveSpec:
    for move in _load_move_specs():
        if (move.name or "").strip().lower() == "struggle":
            return move
    return MoveSpec(
        name="Struggle",
        type="Typeless",
        category="Physical",
        db=4,
        ac=None,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
        range_text="Melee, 1 Target",
    )


def _field_bonus_for_move(
    battle: BattleState,
    impacted_ids: Sequence[str],
    ai_level: str,
) -> float:
    """Give additional score for hitting expensive tiles when using smarter AI tiers."""
    if ai_level not in {"tactical", "strategic"}:
        return 0.0
    grid = battle.grid
    if grid is None:
        return 0.0
    bonus = 0.0
    tiles: Dict[Tuple[int, int], Dict[str, Any]] = getattr(grid, "tiles", {}) or {}
    center_accumulator = 0.0
    for target_id in impacted_ids:
        target = battle.pokemon.get(target_id)
        if target is None or target.position is None:
            continue
        tile_meta = tiles.get(target.position)
        if not isinstance(tile_meta, dict):
            continue
        tile_type = str(tile_meta.get("type", "") or "").lower()
        bonus += _tile_type_bonus(tile_type, ai_level)
        bonus += 0.05 * _sum_hazard_layers(tile_meta.get("hazards"))
        if ai_level == "strategic":
            center_accumulator += _center_influence(grid, target.position)
    if ai_level == "strategic":
        bonus += center_accumulator
    return bonus


def _move_type_bonus(
    battle: BattleState,
    actor: PokemonState,
    actor_id: str,
    move: MoveSpec,
    target_state: Optional[PokemonState],
    ai_level: str,
    move_category: str,
    target_id: Optional[str],
) -> float:
    if ai_level not in {"tactical", "strategic"} or move_category == "status":
        return 0.0
    actor_pos = actor.position
    distance = None
    if actor_pos and target_state and target_state.position:
        distance = targeting.chebyshev_distance(actor_pos, target_state.position)
    move_kind = ((move.target_kind or "") or (move.range_kind or "")).lower()
    preferred_range = move.target_range or move.range_value or 1
    bonus = 0.0
    opponent_shift = _estimated_shift_distance(
        battle, target_state.controller_id if target_state else None
    )
    actor_shift = _max_actor_shift_distance(battle, actor_id)
    if "melee" in move_kind:
        range_gap = max(0, (distance or 0) - preferred_range)
        bonus += max(0.1, 0.5 - range_gap * 0.1)
        bonus += 0.05 * min(actor_shift, actor_shift + opponent_shift)
    if "ranged" in move_kind:
        gap = abs((distance or preferred_range) - preferred_range + opponent_shift)
        bonus += max(0.1, 0.35 - gap * 0.04)
        if ai_level == "strategic":
            bonus += 0.05 * actor_shift
    if move.area_kind in {"field", "burst", "cone", "line", "closeblast"}:
        bonus += 0.2
        if ai_level == "strategic":
            bonus += 0.1
    effects = (move.effects_text or "").lower()
    keywords = [str(entry).lower() for entry in move.keywords]
    keyword_bonus = _keyword_bonus(keywords, effects, ai_level)
    bonus += keyword_bonus
    if distance is not None and ai_level == "strategic":
        bonus += max(0.0, 0.2 - distance * 0.02)
    return bonus


def _tile_type_bonus(tile_type: str, ai_level: str) -> float:
    value = 0.0
    if "hazard" in tile_type:
        value += 0.15
    if "difficult" in tile_type:
        value += 0.08
    if "water" in tile_type:
        value += 0.05
    if ai_level == "strategic" and "cover" in tile_type:
        value += 0.05
    return value


def _sum_hazard_layers(raw: Any | None) -> int:
    if not raw:
        return 0
    total = 0
    if isinstance(raw, dict):
        iterator = raw.values()
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        iterator = raw
    else:
        iterator = [raw]
    for entry in iterator:
        try:
            layers = int(entry)
        except (TypeError, ValueError):
            continue
        if layers > 0:
            total += layers
    return total


def _center_influence(grid: Any, coord: Tuple[int, int]) -> float:
    width = getattr(grid, "width", None)
    height = getattr(grid, "height", None)
    if not width or not height:
        return 0.0
    center = (int(width) // 2, int(height) // 2)
    distance = targeting.chebyshev_distance(coord, center)
    max_span = max(width, height) / 2
    if max_span <= 0:
        return 0.0
    influence = max(0.0, (max_span - distance) / max_span)
    return 0.1 * influence


def _estimated_shift_distance(battle: BattleState, actor_id: Optional[str]) -> int:
    if not actor_id:
        return 0
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.position is None:
        return 0
    tiles = movement.legal_shift_tiles(battle, actor_id)
    if not tiles:
        return 0
    distances = [
        targeting.chebyshev_distance(actor.position, coord)
        for coord in tiles
        if coord is not None
    ]
    return max(distances) if distances else 0


def _max_actor_shift_distance(battle: BattleState, actor_id: str) -> int:
    return _estimated_shift_distance(battle, actor_id)


def _keyword_bonus(
    keywords: Sequence[str], effects: str, ai_level: str
) -> float:
    bonus = 0.0
    if ai_level == "strategic":
        bonus += 0.05
    if "protect" in keywords or "protect" in effects:
        bonus += 0.15
    if "drain" in keywords or "drain" in effects:
        bonus += 0.12
    if "heal" in keywords or "heal" in effects:
        bonus += 0.1
    if "hazard" in keywords or "hazard" in effects:
        bonus += 0.08
    if "push" in keywords or "pull" in keywords:
        bonus += 0.07
    if "boost" in effects:
        bonus += 0.1
    return bonus


def _find_any_usable_move(
    battle: BattleState,
    actor_id: str,
    actor: PokemonState,
    actor_team: str,
    opponents: Sequence[str],
) -> Tuple[Optional[MoveSpec], Optional[str]]:
    for move in actor.spec.moves:
        if _is_interrupt_only_move(move):
            continue
        if not _frequency_available(battle, actor_id, move):
            continue
        requirements = battle.weapon_requirements_for_move(move)
        if requirements:
            weapon_tags = actor.equipped_weapon_tags()
            if not weapon_tags or not any(req.issubset(weapon_tags) for req in requirements):
                continue
        requires_target = targeting.move_requires_target(move)
        candidate_ids: Sequence[Optional[str]] = opponents if requires_target else [None]
        if not candidate_ids:
            candidate_ids = [None]
        for target_id in candidate_ids:
            target_state = battle.pokemon.get(target_id) if target_id else None
            if requires_target and target_state is None:
                continue
            if target_state is not None:
                if target_state.position is None:
                    continue
                if not targeting.is_target_in_range(actor.position, target_state.position, move):
                    continue
                if battle.grid and not battle.has_line_of_sight(actor_id, target_state.position, target_id):
                    continue
            return move, target_id
    if opponents:
        struggle = _load_struggle_move()
        return struggle, opponents[0]
    return None, None


def _has_damaging_move_in_range(
    battle: BattleState, actor_id: str, target_id: str
) -> bool:
    actor = battle.pokemon.get(actor_id)
    target = battle.pokemon.get(target_id)
    if actor is None or target is None or actor.position is None or target.position is None:
        return False
    for move in actor.spec.moves:
        if (move.category or "").strip().lower() == "status":
            continue
        requirements = battle.weapon_requirements_for_move(move)
        if requirements:
            weapon_tags = actor.equipped_weapon_tags()
            if not weapon_tags or not any(req.issubset(weapon_tags) for req in requirements):
                continue
        if not targeting.is_target_in_range(actor.position, target.position, move):
            continue
        if battle.grid and not battle.has_line_of_sight(actor_id, target.position, target_id):
            continue
        if expected_damage(actor, target, move, weather=battle.effective_weather()) > 0:
            return True
    return False


__all__ = ["choose_best_move", "choose_grapple_action"]
