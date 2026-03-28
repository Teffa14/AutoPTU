"""Passive trainer-feature perk hooks for combat modifiers and turn-end links."""

from __future__ import annotations

from ..perk_hooks import PerkHookContext, register_perk_hook

_LINK_FEATURES = {
    "Attack Link": "atk",
    "Defense Link": "def",
    "Special Attack Link": "spatk",
    "Special Defense Link": "spdef",
    "Speed Link": "spd",
}


def _apply_link(ctx: PerkHookContext, feature_name: str, stat: str) -> None:
    actor = ctx.actor
    if getattr(actor, "fainted", False):
        return
    trainer = getattr(ctx.battle, "trainers", {}).get(getattr(actor, "controller_id", ""))
    if trainer is None or int(getattr(trainer, "ap", 0) or 0) < 1:
        return
    current = int(getattr(actor, "combat_stages", {}).get(stat, 0) or 0)
    if current > 0:
        return
    actor.combat_stages[stat] = min(6, current + 1)
    trainer.ap = int(getattr(trainer, "ap", 0) or 0) - 1
    ctx.events.append(
        {
            "type": "trainer_feature",
            "actor": ctx.actor_id,
            "trainer": actor.controller_id,
            "feature": feature_name,
            "effect": "raise_cs",
            "stat": stat,
            "amount": 1,
            "ap_spent": 1,
            "phase": ctx.phase,
            "description": f"{feature_name} spends 1 AP to raise the Pokemon's combat stage.",
        }
    )


@register_perk_hook("end", "Attack Link")
def _attack_link(ctx: PerkHookContext) -> None:
    _apply_link(ctx, "Attack Link", "atk")


@register_perk_hook("end", "Defense Link")
def _defense_link(ctx: PerkHookContext) -> None:
    _apply_link(ctx, "Defense Link", "def")


@register_perk_hook("end", "Special Attack Link")
def _special_attack_link(ctx: PerkHookContext) -> None:
    _apply_link(ctx, "Special Attack Link", "spatk")


@register_perk_hook("end", "Special Defense Link")
def _special_defense_link(ctx: PerkHookContext) -> None:
    _apply_link(ctx, "Special Defense Link", "spdef")


@register_perk_hook("end", "Speed Link")
def _speed_link(ctx: PerkHookContext) -> None:
    _apply_link(ctx, "Speed Link", "spd")
