"""Adjacent aura damage bonuses."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ... import targeting
from ...move_traits import move_has_keyword


@register_ability_hook(phase="post_result_auras", ability=None)
def _adjacent_aura_sources(ctx: AbilityHookContext) -> None:
    attacker = ctx.attacker
    if attacker is None or attacker.position is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type == "water" and not ctx.result.get("aqua_boosted_by"):
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id or mon.fainted or not mon.active:
                continue
            if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
                continue
            if not mon.has_ability("Aqua Boost") or mon.position is None:
                continue
            if targeting.chebyshev_distance(attacker.position, mon.position) <= 1:
                ctx.result["aqua_boosted_by"] = pid
                break
    if move_type == "fire" and not ctx.result.get("ignition_boosted_by"):
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id or mon.fainted or not mon.active:
                continue
            if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
                continue
            if not mon.has_ability("Ignition Boost") or mon.position is None:
                continue
            if targeting.chebyshev_distance(attacker.position, mon.position) <= 1:
                ctx.result["ignition_boosted_by"] = pid
                break
    if move_type == "electric" and not ctx.result.get("thunder_boosted_by"):
        for pid, mon in ctx.battle.pokemon.items():
            if pid == ctx.attacker_id or mon.fainted or not mon.active:
                continue
            if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
                continue
            if not mon.has_ability("Thunder Boost") or mon.position is None:
                continue
            if targeting.chebyshev_distance(attacker.position, mon.position) <= 1:
                ctx.result["thunder_boosted_by"] = pid
                break
    if not ctx.result.get("power_spot_source"):
        allies = ctx.battle._ability_in_radius(
            attacker.position,
            "Power Spot",
            2,
            team=ctx.battle._team_for(ctx.attacker_id),
        )
        if allies:
            ctx.result["power_spot_source"] = allies[0]
    if not ctx.result.get("type_aura_source"):
        for pid, mon in ctx.battle.pokemon.items():
            if mon.fainted or not mon.active or mon.position is None:
                continue
            if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
                continue
            if not mon.has_ability("Type Aura"):
                continue
            if targeting.chebyshev_distance(attacker.position, mon.position) > 3:
                continue
            primary = (mon.spec.types[0] if mon.spec.types else "").strip().lower()
            if primary and primary == move_type:
                ctx.result["type_aura_source"] = pid
                ctx.result["type_aura_type"] = primary
                break


@register_ability_hook(phase="post_result_auras", ability=None)
def _apply_adjacent_aura_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    aqua_boosted_by = ctx.result.get("aqua_boosted_by")
    if aqua_boosted_by:
        ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + 5
        ctx.result["aqua_boost_bonus"] = 5
        ctx.events.append(
            {
                "type": "ability",
                "actor": aqua_boosted_by,
                "target": ctx.attacker_id,
                "ability": "Aqua Boost",
                "move": ctx.move.name,
                "effect": "damage_bonus",
                "amount": 5,
                "description": "Aqua Boost empowers nearby Water attacks.",
                "target_hp": ctx.defender.hp,
            }
        )
    ignition_boosted_by = ctx.result.get("ignition_boosted_by")
    if ignition_boosted_by:
        ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + 5
        ctx.result["ignition_boost_bonus"] = 5
        ctx.events.append(
            {
                "type": "ability",
                "actor": ignition_boosted_by,
                "target": ctx.attacker_id,
                "ability": "Ignition Boost",
                "move": ctx.move.name,
                "effect": "damage_bonus",
                "amount": 5,
                "description": "Ignition Boost empowers nearby Fire attacks.",
                "target_hp": ctx.defender.hp,
            }
        )
    thunder_boosted_by = ctx.result.get("thunder_boosted_by")
    if thunder_boosted_by:
        ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + 5
        ctx.result["thunder_boost_bonus"] = 5
        ctx.events.append(
            {
                "type": "ability",
                "actor": thunder_boosted_by,
                "target": ctx.attacker_id,
                "ability": "Thunder Boost",
                "move": ctx.move.name,
                "effect": "damage_bonus",
                "amount": 5,
                "description": "Thunder Boost empowers nearby Electric attacks.",
                "target_hp": ctx.defender.hp,
            }
        )
    power_spot_source = ctx.result.get("power_spot_source")
    if power_spot_source:
        ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + 5
        ctx.result["power_spot_bonus"] = 5
        ctx.events.append(
            {
                "type": "ability",
                "actor": power_spot_source,
                "target": ctx.attacker_id,
                "ability": "Power Spot",
                "move": ctx.move.name,
                "effect": "damage_bonus",
                "amount": 5,
                "description": "Power Spot empowers nearby allies.",
                "target_hp": ctx.defender.hp,
            }
        )
    type_aura_source = ctx.result.get("type_aura_source")
    if type_aura_source:
        ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + 5
        ctx.result["type_aura_bonus"] = 5
        ctx.events.append(
            {
                "type": "ability",
                "actor": type_aura_source,
                "target": ctx.attacker_id,
                "ability": "Type Aura",
                "move": ctx.move.name,
                "effect": "damage_bonus",
                "amount": 5,
                "description": "Type Aura empowers allied moves of the aura type.",
                "target_hp": ctx.defender.hp,
            }
        )
    if ctx.attacker and ctx.attacker.has_ability("Aura Storm") and move_has_keyword(
        ctx.effective_move, "aura"
    ):
        if not ctx.battle._aura_break_blockers(ctx.attacker_id):
            aura_bonus = max(0, 5 + 2 * int(ctx.attacker.injuries or 0))
            if aura_bonus:
                ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + aura_bonus
                ctx.result["aura_storm_bonus"] = aura_bonus
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.attacker_id,
                        "target": ctx.defender_id,
                        "ability": "Aura Storm",
                        "move": ctx.move.name,
                        "effect": "damage_bonus",
                        "amount": aura_bonus,
                        "description": "Aura Storm scales damage with injuries on Aura moves.",
                        "target_hp": ctx.defender.hp,
                    }
                )
