"""Portable subset of Advanced AI System heuristics for AutoPTU.

This module ports safe, engine-agnostic ideas from the Ruby AAI package:
- tiered behavior flags by AI level
- lightweight pattern probabilities from opponent profile histograms
- adaptive score deltas for setup/hazard/status decisions

It intentionally does not override legality or battle-rule resolution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class TierFeatures:
    switch_prediction: bool
    setup_detection: bool
    hazard_awareness: bool
    pivot_preference: bool
    recovery_timing: bool
    status_value: float
    prediction_depth: int
    learn_patterns: bool


_TIER_BY_LEVEL = {
    "standard": TierFeatures(
        switch_prediction=False,
        setup_detection=False,
        hazard_awareness=False,
        pivot_preference=False,
        recovery_timing=False,
        status_value=0.5,
        prediction_depth=0,
        learn_patterns=False,
    ),
    "tactical": TierFeatures(
        switch_prediction=True,
        setup_detection=True,
        hazard_awareness=True,
        pivot_preference=True,
        recovery_timing=True,
        status_value=1.0,
        prediction_depth=1,
        learn_patterns=False,
    ),
    "strategic": TierFeatures(
        switch_prediction=True,
        setup_detection=True,
        hazard_awareness=True,
        pivot_preference=True,
        recovery_timing=True,
        status_value=1.2,
        prediction_depth=2,
        learn_patterns=True,
    ),
}


def tier_for_level(ai_level: str) -> TierFeatures:
    return _TIER_BY_LEVEL.get(str(ai_level or "").strip().lower(), _TIER_BY_LEVEL["standard"])


def protect_tendency(action_type: Mapping[str, float]) -> float:
    """Estimate defensive tendency from observed action histogram."""
    attack = max(0.0, float(action_type.get("attack", 0.0)))
    defend = max(0.0, float(action_type.get("defend", 0.0)))
    other = max(0.0, float(action_type.get("other", 0.0)))
    total = attack + defend + other
    if total <= 1e-9:
        return 0.0
    return defend / total


def retreat_tendency(risk_tolerance: Mapping[str, float]) -> float:
    """Estimate switch/retreat tendency from learned risk buckets."""
    retreats = max(0.0, float(risk_tolerance.get("retreats", 0.0)))
    stays = max(0.0, float(risk_tolerance.get("stays_in_danger", 0.0)))
    total = retreats + stays
    if total <= 1e-9:
        return 0.0
    return retreats / total


def looks_like_setup(text: str, keywords: str) -> bool:
    source = f"{text} {keywords}".lower()
    return any(token in source for token in ("boost", "raise", "setup", "calm mind", "swords dance"))


def looks_like_hazard(text: str, keywords: str) -> bool:
    source = f"{text} {keywords}".lower()
    return any(token in source for token in ("hazard", "spikes", "rock", "sticky web", "toxic spikes"))


def looks_like_status_utility(text: str, keywords: str) -> bool:
    source = f"{text} {keywords}".lower()
    return any(
        token in source
        for token in ("status", "poison", "burn", "paraly", "sleep", "taunt", "disable", "encore", "debuff")
    )


def adaptive_delta(
    *,
    is_status: bool,
    move_text: str,
    move_keywords: str,
    defend_prob: float,
    retreat_prob: float,
    tier: TierFeatures,
) -> float:
    """Compute additive score delta for one candidate action."""
    delta = 0.0
    if is_status:
        delta += 0.12 * max(0.0, tier.status_value - 0.5)
        if tier.hazard_awareness and retreat_prob >= 0.45 and looks_like_hazard(move_text, move_keywords):
            delta += 0.35
        if tier.setup_detection and retreat_prob >= 0.45 and looks_like_setup(move_text, move_keywords):
            delta += 0.25
        if defend_prob >= 0.55 and looks_like_status_utility(move_text, move_keywords):
            delta += 0.12
    else:
        if tier.learn_patterns and defend_prob >= 0.60:
            # Slightly down-rank pure damage when target frequently plays defensive.
            delta -= 0.18
    return delta

