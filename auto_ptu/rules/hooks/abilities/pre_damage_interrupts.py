"""Pre-damage interrupt hooks (shields, bunkers, fox fire)."""

from __future__ import annotations

import math
from typing import Optional

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ...move_traits import move_has_contact_trait, has_range_keyword
from ... import targeting, movement
from ....data_models import MoveSpec
from ...battle_state import ActionType
from ...abilities.ability_variants import has_ability_exact


def _allow_out_of_turn(
    ctx: AbilityHookContext, actor_id: Optional[str], label: str, *, optional: bool = True
) -> bool:
    battle = getattr(ctx, "battle", None)
    if battle is None or not getattr(battle, "should_trigger_out_of_turn", None):
        return True
    payload = {
        "actor_id": actor_id,
        "label": label,
        "phase": "pre_damage_interrupt",
        "move": str(getattr(ctx.move, "name", "") or ""),
        "trigger_move": str(getattr(ctx.effective_move, "name", "") or ""),
        "attacker_id": ctx.attacker_id,
        "defender_id": ctx.defender_id,
        "optional": optional,
    }
    return battle.should_trigger_out_of_turn(actor_id, payload)


@register_ability_hook(phase="pre_damage_interrupt", ability=None)
def _crafty_shield_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if (ctx.effective_move.category or "").strip().lower() != "status":
        return
    defender = ctx.defender
    defender_team = ctx.battle._team_for(ctx.defender_id)
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        if ctx.battle._team_for(pid) != defender_team:
            continue
        if not mon.has_status("Crafty Shield"):
            continue
        if mon.position is not None and defender.position is not None:
            if abs(mon.position[0] - defender.position[0]) + abs(mon.position[1] - defender.position[1]) > 2:
                continue
        if not _allow_out_of_turn(ctx, pid, "Crafty Shield", optional=False):
            continue
        mon.remove_status_by_names({"crafty shield"})
        ctx.events.append(
            {
                "type": "move",
                "actor": pid,
                "target": ctx.attacker_id,
                "move": "Crafty Shield",
                "effect": "crafty_shield",
                "description": "Crafty Shield blocks a status move.",
                "target_hp": mon.hp,
            }
        )
        ctx.result["damage"] = 0
        ctx.result["type_multiplier"] = 0.0
        ctx.result["blocked_by_shield"] = True
        return


@register_ability_hook(phase="pre_damage_interrupt", ability=None)
def _mat_block_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.battle.round != 1:
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    defender = ctx.defender
    defender_team = ctx.battle._team_for(ctx.defender_id)
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        if ctx.battle._team_for(pid) != defender_team:
            continue
        if not mon.has_status("Mat Block"):
            continue
        if mon.position is not None and defender.position is not None:
            if abs(mon.position[0] - defender.position[0]) + abs(mon.position[1] - defender.position[1]) > 1:
                continue
        if not _allow_out_of_turn(ctx, pid, "Mat Block", optional=False):
            continue
        mon.remove_status_by_names({"mat block"})
        ctx.events.append(
            {
                "type": "move",
                "actor": pid,
                "target": ctx.attacker_id,
                "move": "Mat Block",
                "effect": "mat_block",
                "description": "Mat Block blocks an incoming attack.",
                "target_hp": mon.hp,
            }
        )
        ctx.result["damage"] = 0
        ctx.result["type_multiplier"] = 0.0
        ctx.result["blocked_by_shield"] = True
        return


@register_ability_hook(phase="pre_damage_interrupt", ability=None)
def _magic_coat_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if (ctx.effective_move.category or "").strip().lower() != "status":
        return
    if str(ctx.move.name or "").strip().lower() == "magic coat":
        return
    defender = ctx.defender
    if not defender.has_status("Magic Coat"):
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Magic Coat", optional=False):
        return
    defender.remove_status_by_names({"magic coat"})
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "move": "Magic Coat",
            "effect": "magic_coat_reflect",
            "description": "Magic Coat reflects the incoming status move.",
            "target_hp": defender.hp,
        }
    )
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.defender_id,
            move=ctx.move,
            target_id=ctx.attacker_id,
            target_position=ctx.attacker.position if ctx.attacker else None,
        )
    except Exception:
        pass
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["blocked_by_shield"] = True


@register_ability_hook(phase="pre_damage_interrupt", ability="Perception", holder="defender")
def _perception_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ready = next(iter(ctx.defender.get_temporary_effects("perception_ready")), None)
    if ready is None:
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Perception", optional=True):
        return
    ctx.defender.remove_temporary_effect("perception_ready")
    if ctx.battle.grid is None or ctx.defender.position is None:
        return
    area_kind = targeting.normalized_area_kind(ctx.effective_move)
    if not area_kind:
        return
    for entry in list(ctx.defender.get_temporary_effects("perception_used")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            ctx.defender.remove_temporary_effect("perception_used")
            continue
        return
    tiles = targeting.affected_tiles(
        ctx.battle.grid,
        ctx.defender.position,
        ctx.defender.position,
        ctx.effective_move,
    )
    if ctx.defender.position not in tiles:
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Perception [Errata]", optional=True):
        return
    reachable = movement.legal_shift_tiles(ctx.battle, ctx.defender_id)
    safe_tiles = [coord for coord in reachable if coord not in tiles]
    if not safe_tiles:
        return
    origin = ctx.defender.position
    destination = max(safe_tiles, key=lambda coord: targeting.chebyshev_distance(origin, coord))
    ctx.defender.position = destination
    ctx.defender.add_temporary_effect("perception_used", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Perception",
            "move": ctx.move.name,
            "effect": "shift",
            "from": origin,
            "to": destination,
            "description": "Perception shifts out of the area-of-effect.",
            "target_hp": ctx.defender.hp,
        }
    )
    ctx.result["hit"] = False
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0


@register_ability_hook(phase="pre_damage_interrupt", ability="Perception [Errata]", holder="defender")
def _perception_errata_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if not has_ability_exact(ctx.defender, "Perception [Errata]"):
        return
    if ctx.attacker_id == ctx.defender_id:
        return
    if ctx.battle._team_for(ctx.attacker_id) != ctx.battle._team_for(ctx.defender_id):
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    if ctx.battle.grid is None or ctx.defender.position is None:
        return
    area_kind = targeting.normalized_area_kind(ctx.effective_move)
    if not area_kind:
        return
    origin = ctx.attacker.position if ctx.attacker and ctx.attacker.position else ctx.defender.position
    tiles = targeting.affected_tiles(
        ctx.battle.grid,
        origin,
        ctx.defender.position,
        ctx.effective_move,
    )
    if ctx.defender.position not in tiles:
        return
    reachable = movement.legal_shift_tiles(ctx.battle, ctx.defender_id)
    safe_tiles = [
        coord
        for coord in reachable
        if coord not in tiles
        and targeting.chebyshev_distance(ctx.defender.position, coord) <= 1
    ]
    if not safe_tiles:
        return
    origin_pos = ctx.defender.position
    destination = max(
        safe_tiles, key=lambda coord: targeting.chebyshev_distance(origin_pos, coord)
    )
    ctx.defender.position = destination
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Perception [Errata]",
            "move": ctx.move.name,
            "effect": "disengage",
            "from": origin_pos,
            "to": destination,
            "description": "Perception [Errata] disengages from an ally's area attack.",
            "target_hp": ctx.defender.hp,
        }
    )
    ctx.result["hit"] = False
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0


@register_ability_hook(phase="pre_damage_interrupt", ability="Parry", holder="defender")
def _parry_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ready = next(iter(ctx.defender.get_temporary_effects("parry_ready")), None)
    if ready is None:
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Parry", optional=True):
        return
    ctx.defender.remove_temporary_effect("parry_ready")
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    for entry in list(ctx.defender.get_temporary_effects("parry_used")):
        if entry.get("round") == ctx.battle.round:
            return
        ctx.defender.remove_temporary_effect("parry_used")
    ctx.defender.add_temporary_effect("parry_used", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Parry",
            "move": ctx.move.name,
            "effect": "avoid",
            "description": "Parry deflects the incoming attack.",
            "target_hp": ctx.defender.hp,
        }
    )
    ctx.result["hit"] = False
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0


@register_ability_hook(phase="pre_damage_interrupt", ability="Shell Shield", holder="defender")
def _shell_shield_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ready = next(iter(ctx.defender.get_temporary_effects("shell_shield_ready")), None)
    if ready is None:
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Shell Shield", optional=True):
        return
    ctx.defender.remove_temporary_effect("shell_shield_ready")
    ability_name = str(ready.get("ability") or "Shell Shield")
    if not ctx.defender.has_status("Withdrawn"):
        ctx.defender.statuses.append({"name": "Withdrawn"})
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="def",
        delta=1,
        effect="shell_shield",
        description="Shell Shield readies Withdraw as an interrupt.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "withdraw",
            "description": "Shell Shield activates Withdraw.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="pre_damage_interrupt", ability="Telepathy", holder="defender")
def _telepathy_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if ctx.battle._team_for(ctx.attacker_id) != ctx.battle._team_for(ctx.defender_id):
        return
    if ctx.battle.grid is None or ctx.defender.position is None:
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Telepathy", optional=True):
        return
    area_kind = targeting.normalized_area_kind(ctx.effective_move)
    if not area_kind:
        return
    tiles = targeting.affected_tiles(
        ctx.battle.grid,
        ctx.attacker.position if ctx.attacker and ctx.attacker.position else ctx.defender.position,
        ctx.defender.position,
        ctx.effective_move,
    )
    if ctx.defender.position not in tiles:
        return
    reachable = movement.legal_shift_tiles(ctx.battle, ctx.defender_id)
    safe_tiles = [coord for coord in reachable if coord not in tiles]
    if not safe_tiles:
        return
    origin = ctx.defender.position
    destination = max(
        safe_tiles, key=lambda coord: targeting.chebyshev_distance(origin, coord)
    )
    ctx.defender.position = destination
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Telepathy",
            "move": ctx.move.name,
            "effect": "shift",
            "from": origin,
            "to": destination,
            "description": "Telepathy shifts out of an ally's area attack.",
            "target_hp": ctx.defender.hp,
        }
    )
    ctx.result["hit"] = False
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0


@register_ability_hook(phase="pre_damage_interrupt", ability="Sway", holder="defender")
def _sway_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if ctx.attacker.get_temporary_effects("sway_redirect"):
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    used_entry = next(iter(ctx.defender.get_temporary_effects("sway_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        return
    if not ctx.defender.has_action_available(ActionType.STANDARD):
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Sway", optional=True):
        return
    ctx.defender.mark_action(ActionType.STANDARD, "Sway")
    if used_entry is None:
        ctx.defender.add_temporary_effect("sway_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    ctx.attacker.add_temporary_effect("sway_redirect", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Sway",
            "move": ctx.move.name,
            "effect": "redirect",
            "description": "Sway redirects the incoming melee attack.",
            "target_hp": ctx.defender.hp,
        }
    )
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.attacker_id,
            move=ctx.move,
            target_id=ctx.attacker_id,
            target_position=ctx.attacker.position,
        )
    except Exception:
        pass
    while ctx.attacker.remove_temporary_effect("sway_redirect"):
        continue
    if ctx.defender.position is not None and ctx.battle.grid is not None and ctx.attacker.position is not None:
        x, y = ctx.defender.position
        candidates = []
        for coord in (
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
            (x + 1, y + 1),
            (x + 1, y - 1),
            (x - 1, y + 1),
            (x - 1, y - 1),
        ):
            if not ctx.battle.grid.in_bounds(coord):
                continue
            if coord in ctx.battle.grid.blockers:
                continue
            occupied = any(
                mon.position == coord
                for pid, mon in ctx.battle.pokemon.items()
                if pid not in {ctx.attacker_id, ctx.defender_id}
                and mon.hp is not None
                and mon.hp > 0
                and mon.position is not None
            )
            if occupied:
                continue
            candidates.append(coord)
        if candidates:
            destination = sorted(candidates)[0]
            ctx.attacker.position = destination
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Sway",
                    "move": ctx.move.name,
                    "effect": "push",
                    "to": destination,
                    "description": "Sway pushes the attacker away.",
                    "target_hp": ctx.attacker.hp,
                }
            )
    ctx.result["hit"] = False
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0


@register_ability_hook(phase="pre_damage_interrupt", ability=None)
def _shield_interrupts(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    defender = ctx.defender
    target_kind = (ctx.effective_move.target_kind or "").strip().lower()
    blocked_by_shield = False
    shield_move = ""
    prompt_label = ""
    if defender.has_status("Protect"):
        prompt_label = "Protect"
    elif defender.has_status("Detect"):
        prompt_label = "Detect"
    elif defender.has_status("Obstruct"):
        prompt_label = "Obstruct"
    elif defender.has_status("King's Shield"):
        prompt_label = "King's Shield"
    elif defender.has_status("Spiky Shield"):
        prompt_label = "Spiky Shield"
    elif defender.has_status("Quick Guard"):
        prompt_label = "Quick Guard"
    if prompt_label and not _allow_out_of_turn(ctx, ctx.defender_id, prompt_label, optional=False):
        return
    if defender.has_status("Protect"):
        defender.remove_status_by_names({"protect"})
        blocked_by_shield = True
        shield_move = "Protect"
    elif defender.has_status("Detect"):
        defender.remove_status_by_names({"detect"})
        blocked_by_shield = True
        shield_move = "Detect"
    elif defender.has_status("Obstruct"):
        defender.remove_status_by_names({"obstruct"})
        blocked_by_shield = True
        shield_move = "Obstruct"
        if target_kind == "melee" and ctx.attacker is not None:
            before = ctx.attacker.combat_stages.get("def", 0)
            after = max(-6, min(6, before - 2))
            if after != before:
                ctx.attacker.combat_stages["def"] = after
                ctx.events.append(
                    {
                        "type": "move",
                        "actor": ctx.defender_id,
                        "target": ctx.attacker_id,
                        "move": "Obstruct",
                        "effect": "obstruct_def_drop",
                        "stat": "def",
                        "amount": after - before,
                        "target_hp": ctx.attacker.hp if ctx.attacker else None,
                    }
                )
    elif defender.has_status("King's Shield"):
        defender.remove_status_by_names({"king's shield"})
        blocked_by_shield = True
        shield_move = "King's Shield"
        if target_kind == "melee" and ctx.attacker is not None:
            before = ctx.attacker.combat_stages.get("atk", 0)
            after = max(-6, min(6, before - 2))
            if after != before:
                ctx.attacker.combat_stages["atk"] = after
                ctx.events.append(
                    {
                        "type": "move",
                        "actor": ctx.defender_id,
                        "target": ctx.attacker_id,
                        "move": "King's Shield",
                        "effect": "kings_shield_atk_drop",
                        "stat": "atk",
                        "amount": after - before,
                        "target_hp": ctx.attacker.hp if ctx.attacker else None,
                    }
                )
    elif defender.has_status("Spiky Shield"):
        defender.remove_status_by_names({"spiky shield"})
        blocked_by_shield = True
        shield_move = "Spiky Shield"
        if target_kind == "melee" and ctx.attacker is not None:
            max_hp = ctx.attacker.max_hp()
            damage = max(1, int(math.ceil(max_hp / 10))) if max_hp else 0
            if damage:
                before = ctx.attacker.hp or 0
                ctx.attacker.apply_damage(damage, skip_injury=True)
                dealt = max(0, before - (ctx.attacker.hp or 0))
                ctx.events.append(
                    {
                        "type": "move",
                        "actor": ctx.defender_id,
                        "target": ctx.attacker_id,
                        "move": "Spiky Shield",
                        "effect": "spiky_shield",
                        "amount": dealt,
                        "target_hp": ctx.attacker.hp if ctx.attacker else None,
                    }
                )
    elif defender.has_status("Quick Guard"):
        if int(ctx.effective_move.priority or 0) > 0:
            defender.remove_status_by_names({"quick guard"})
            blocked_by_shield = True
            shield_move = "Quick Guard"
    if blocked_by_shield and shield_move:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "move": shield_move,
                "effect": shield_move.lower().replace(" ", "_"),
                "description": f"{shield_move} blocks the incoming attack.",
                "target_hp": defender.hp,
            }
        )
        ctx.result["damage"] = 0
        ctx.result["type_multiplier"] = 0.0
        ctx.result["blocked_by_shield"] = True


@register_ability_hook(phase="pre_damage_interrupt", ability="Fox Fire", holder="defender")
def _fox_fire_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.get_temporary_effects("fox_fire"):
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Fox Fire", optional=True):
        return
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Fox Fire",
            "move": ctx.move.name,
            "effect": "interrupt",
            "description": "Fox Fire triggers an ember interrupt.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="pre_damage_interrupt", ability=None)
def _baneful_bunker(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    defender = ctx.defender
    if not defender.has_status("Baneful Bunker"):
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Baneful Bunker", optional=False):
        return
    defender.remove_status_by_names({"baneful bunker"})
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "move": "Baneful Bunker",
            "effect": "baneful_bunker_block",
            "description": "Baneful Bunker blocks the incoming attack.",
            "target_hp": defender.hp,
        }
    )
    if move_has_contact_trait(ctx.effective_move) and ctx.attacker is not None:
        ctx.battle._apply_status(
            ctx.events,
            attacker_id=ctx.defender_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            status="Poisoned",
            effect="baneful_bunker",
            description="Baneful Bunker poisons contact attackers.",
        )
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["blocked_by_bunker"] = True


@register_ability_hook(phase="pre_damage_interrupt", ability="Quick Draw", holder="defender")
def _quick_draw_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if ctx.defender.actions_taken:
        return
    entry = next(iter(ctx.defender.get_temporary_effects("quick_draw_used")), None)
    if entry is not None:
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Quick Draw", optional=True):
        return
    ctx.defender.add_temporary_effect("quick_draw_used", expires_round=ctx.battle.round + 999)
    chosen = None
    for move in ctx.defender.spec.moves:
        if (move.category or "").strip().lower() == "status":
            continue
        chosen = move
        break
    if chosen is None:
        chosen = MoveSpec(
            name="Struggle",
            type="Normal",
            category="Physical",
            db=4,
            ac=4,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            freq="At-Will",
        )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Quick Draw",
            "move": chosen.name,
            "effect": "interrupt",
            "description": "Quick Draw strikes before the opponent acts.",
            "target_hp": ctx.defender.hp,
        }
    )
    try:
        ctx.defender.mark_action(ActionType.STANDARD, "Quick Draw")
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.defender_id,
            move=chosen,
            target_id=ctx.attacker_id,
            target_position=ctx.attacker.position if ctx.attacker else None,
        )
    except Exception:
        pass
    if not ctx.attacker.get_temporary_effects("flinch_immunity") and not ctx.attacker.has_ability("Inner Focus"):
        ctx.attacker.add_temporary_effect(
            "accuracy_penalty",
            amount=2,
            expires_round=ctx.battle.round,
            source="Quick Draw",
            source_id=ctx.defender_id,
        )


@register_ability_hook(phase="pre_damage_interrupt", ability="Queenly Majesty", holder="defender")
def _queenly_majesty_stomp(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if ctx.defender.position is None or ctx.attacker.position is None:
        return
    if targeting.chebyshev_distance(ctx.defender.position, ctx.attacker.position) > 1:
        return
    if ctx.effective_move.priority <= 0 and not has_range_keyword(ctx.effective_move, "interrupt"):
        return
    entry = next(iter(ctx.defender.get_temporary_effects("queenly_majesty_used")), None)
    count = int(entry.get("count", 0) or 0) if entry else 0
    if count >= 2:
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Queenly Majesty", optional=True):
        return
    if entry is None:
        ctx.defender.add_temporary_effect("queenly_majesty_used", count=1)
    else:
        entry["count"] = count + 1
    stomp = MoveSpec(
        name="Stomp",
        type="Normal",
        category="Physical",
        db=7,
        ac=3,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Queenly Majesty",
            "move": ctx.move.name,
            "effect": "stomp",
            "description": "Queenly Majesty interrupts with Stomp.",
            "target_hp": ctx.defender.hp,
        }
    )
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.defender_id,
            move=stomp,
            target_id=ctx.attacker_id,
            target_position=ctx.attacker.position,
        )
    except Exception:
        pass


@register_ability_hook(phase="pre_damage_interrupt", ability="Imposter [Errata]", holder="defender")
def _imposter_errata_interrupt(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if not has_ability_exact(ctx.defender, "Imposter [Errata]"):
        return
    if ctx.defender.get_temporary_effects("transformed"):
        return
    if not _allow_out_of_turn(ctx, ctx.defender_id, "Imposter [Errata]", optional=False):
        return
    transform = MoveSpec(
        name="Transform",
        type="Normal",
        category="Status",
        db=0,
        ac=None,
        range_kind="Ranged",
        range_value=10,
        target_kind="Ranged",
        target_range=10,
        range_text="10, 1 Target",
        freq="At-Will",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Imposter [Errata]",
            "move": ctx.move.name,
            "effect": "transform_interrupt",
            "description": "Imposter interrupts with Transform.",
            "target_hp": ctx.defender.hp,
        }
    )
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.defender_id,
            move=transform,
            target_id=ctx.attacker_id,
            target_position=ctx.attacker.position if ctx.attacker else None,
        )
    except Exception:
        pass
