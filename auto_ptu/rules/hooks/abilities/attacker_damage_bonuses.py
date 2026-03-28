"""Attacker damage bonus hooks."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ...abilities.ability_variants import has_errata
from ... import targeting, calculations


def _aura_break_errata_adjust(ctx: AbilityHookContext, ability_name: str, bonus: int) -> int:
    if bonus <= 0 or ctx.attacker is None:
        return bonus
    target = ability_name.strip().lower()
    entry = None
    for effect in list(ctx.attacker.get_temporary_effects("aura_break_errata")):
        expires_round = effect.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            ctx.attacker.remove_temporary_effect("aura_break_errata")
            continue
        if str(effect.get("ability", "")).strip().lower() == target:
            entry = effect
            break
    if entry is None:
        return bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": entry.get("source_id") or ctx.attacker_id,
            "target": ctx.attacker_id,
            "ability": "Aura Break [Errata]",
            "move": ctx.move.name,
            "effect": "damage_penalty",
            "amount": -bonus,
            "description": "Aura Break [Errata] inverts a damage bonus.",
            "target_hp": ctx.attacker.hp,
        }
    )
    return -bonus


@register_ability_hook(phase="post_result", ability="Adaptability [Errata]")
def _adaptability_errata_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if not move_type:
        return
    attacker_types = {t.strip().lower() for t in ctx.attacker.spec.types if t}
    if move_type not in attacker_types:
        return
    bonus = ctx.battle.rng.randint(1, 10)
    bonus = _aura_break_errata_adjust(ctx, "Adaptability [Errata]", bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["adaptability_errata_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Adaptability [Errata]",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Adaptability [Errata] boosts STAB damage rolls.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Damp [Errata]")
def _damp_errata_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "water":
        return
    bonus = ctx.battle.rng.randint(1, 10)
    bonus = _aura_break_errata_adjust(ctx, "Damp [Errata]", bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["damp_errata_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Damp [Errata]",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Damp [Errata] boosts Water damage rolls.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Defeatist [Errata]")
def _defeatist_errata_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    max_hp = ctx.attacker.max_hp()
    current_hp = ctx.attacker.hp or 0
    if max_hp <= 0 or current_hp <= 0:
        return
    if current_hp * 2 > max_hp:
        bonus = ctx.battle.rng.randint(1, 6) + ctx.battle.rng.randint(1, 6)
        description = "Defeatist [Errata] boosts damage above half HP."
    else:
        bonus = -5
        description = "Defeatist [Errata] penalizes damage at half HP or lower."
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["defeatist_errata_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Defeatist [Errata]",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": description,
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Aura Storm [Errata]")
def _aura_storm_errata_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    injuries = max(0, int(ctx.attacker.injuries or 0))
    if injuries <= 0:
        return
    bonus = injuries * 3
    bonus = _aura_break_errata_adjust(ctx, "Aura Storm [Errata]", bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["aura_storm_errata_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Aura Storm [Errata]",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Aura Storm [Errata] scales with injuries.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Analytic")
def _analytic_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender_id is None or ctx.defender is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    defender = ctx.defender
    acted = bool(defender.actions_taken)
    if not acted and ctx.battle._initiative_index >= 0:
        defender_index = None
        for idx, entry in enumerate(ctx.battle.initiative_order):
            if entry.actor_id == ctx.defender_id:
                defender_index = idx
                break
        if defender_index is not None and ctx.battle._initiative_index > defender_index:
            acted = True
    if not acted:
        return
    analytic_bonus = _aura_break_errata_adjust(ctx, "Analytic", 5)
    if analytic_bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + analytic_bonus
    ctx.result["analytic_bonus"] = analytic_bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Analytic",
            "move": ctx.move.name,
            "effect": "damage_bonus" if analytic_bonus > 0 else "damage_penalty",
            "amount": analytic_bonus,
            "description": "Analytic boosts damage against targets that have already acted.",
            "target_hp": defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Sunglow")
def _sunglow_radiant_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if has_errata(ctx.attacker, "Sunglow"):
        return
    if not ctx.attacker.get_temporary_effects("radiant"):
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    bonus = _aura_break_errata_adjust(ctx, "Sunglow", 5)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["sunglow_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Sunglow",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Sunglow boosts damage while Radiant.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Solar Power [Errata]")
def _solar_power_errata_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.attacker is None or ctx.defender is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    entry = next(iter(ctx.attacker.get_temporary_effects("solar_power_errata_ready")), None)
    if entry is None:
        return
    ctx.attacker.remove_temporary_effect("solar_power_errata_ready")
    bonus = 5 + ctx.attacker.tick_value()
    bonus = _aura_break_errata_adjust(ctx, "Solar Power [Errata]", bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["solar_power_errata_bonus"] = bonus
    ctx.attacker.apply_damage(ctx.attacker.tick_value())
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Solar Power [Errata]",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Solar Power boosts damage at a cost.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Twisted Power")
def _twisted_power_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    category = (ctx.move.category or "").strip().lower()
    if category == "special":
        bonus = max(0, calculations.offensive_stat(ctx.attacker, "physical") // 2)
    else:
        bonus = max(0, calculations.offensive_stat(ctx.attacker, "special") // 2)
    bonus = _aura_break_errata_adjust(ctx, "Twisted Power", bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["twisted_power_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Twisted Power",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Twisted Power blends physical and special power.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Weird Power")
def _weird_power_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if ctx.attacker.has_ability("Mixed Power"):
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    atk_stat = calculations.offensive_stat(ctx.attacker, "physical")
    spatk_stat = calculations.offensive_stat(ctx.attacker, "special")
    bonus = 0
    if (ctx.move.category or "").strip().lower() == "special" and atk_stat > spatk_stat:
        bonus = atk_stat
    elif (ctx.move.category or "").strip().lower() == "physical" and spatk_stat > atk_stat:
        bonus = spatk_stat
    bonus = _aura_break_errata_adjust(ctx, "Weird Power", bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["weird_power_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Weird Power",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Weird Power adds the higher stat to off-type damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Nimble Strikes")
def _nimble_strikes_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() != "physical":
        return
    if (ctx.effective_move.type or "").strip().lower() != "normal":
        return
    bonus = max(0, calculations.speed_stat(ctx.attacker) // 2)
    bonus = _aura_break_errata_adjust(ctx, "Nimble Strikes", bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["nimble_strikes_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Nimble Strikes",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Nimble Strikes adds half Speed to physical Normal damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Stakeout")
def _stakeout_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    joined_round = None
    for entry in ctx.defender.get_temporary_effects("joined_round"):
        joined_round = entry.get("round")
        break
    if joined_round is None:
        return
    last_turn_round = None
    for entry in ctx.attacker.get_temporary_effects("last_turn_round"):
        last_turn_round = entry.get("round")
        break
    try:
        if last_turn_round is not None and int(joined_round) <= int(last_turn_round):
            return
    except (TypeError, ValueError):
        return
    roll = ctx.battle.rng.randint(1, 6) + ctx.battle.rng.randint(1, 6) + 4
    roll = _aura_break_errata_adjust(ctx, "Stakeout", roll)
    if roll == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + roll
    ctx.result["stakeout_bonus"] = roll
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Stakeout",
            "move": ctx.move.name,
            "effect": "damage_bonus" if roll > 0 else "damage_penalty",
            "amount": roll,
            "description": "Stakeout punishes newly entered foes.",
            "target_hp": ctx.defender.hp,
        }
    )


def _sequence_bonus(ctx: AbilityHookContext, *, bonus_per_ally: int, ability_name: str) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    attacker = ctx.attacker
    if attacker.position is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if not move_type:
        return
    adjacent_allies = 0
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.attacker_id or mon.fainted or not mon.active:
            continue
        if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
            continue
        if mon.position is None:
            continue
        if targeting.chebyshev_distance(attacker.position, mon.position) != 1:
            continue
        ally_types = {str(t).strip().lower() for t in mon.spec.types if t}
        if move_type not in ally_types:
            continue
        adjacent_allies += 1
    if adjacent_allies <= 0:
        return
    bonus = adjacent_allies * bonus_per_ally
    bonus = _aura_break_errata_adjust(ctx, ability_name, bonus)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["sequence_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Sequence boosts damage alongside matching adjacent allies.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Sequence")
def _sequence_bonus_standard(ctx: AbilityHookContext) -> None:
    if has_errata(ctx.attacker, "Sequence"):
        return
    _sequence_bonus(ctx, bonus_per_ally=2, ability_name="Sequence")


@register_ability_hook(phase="post_result", ability="Sequence [Errata]")
def _sequence_bonus_errata(ctx: AbilityHookContext) -> None:
    _sequence_bonus(ctx, bonus_per_ally=3, ability_name="Sequence [Errata]")


@register_ability_hook(phase="post_result", ability="Rock Head [Errata]")
def _rock_head_errata_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() != "physical":
        return
    if ctx.attacker.position is None or ctx.defender.position is None:
        return
    entry_to_use = None
    for entry in list(ctx.attacker.get_temporary_effects("rock_head_errata_run")):
        if entry.get("round") != ctx.battle.round:
            ctx.attacker.remove_temporary_effect("rock_head_errata_run")
            continue
        distance = int(entry.get("distance", 0) or 0)
        if distance < 4:
            continue
        dx = ctx.defender.position[0] - ctx.attacker.position[0]
        dy = ctx.defender.position[1] - ctx.attacker.position[1]
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        if entry.get("dir") == (step_x, step_y):
            entry_to_use = entry
            break
    if entry_to_use is None:
        return
    bonus = ctx.battle.rng.randint(1, 6) + ctx.battle.rng.randint(1, 6)
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["rock_head_errata_bonus"] = bonus
    if entry_to_use in ctx.attacker.temporary_effects:
        ctx.attacker.temporary_effects.remove(entry_to_use)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Rock Head [Errata]",
            "move": ctx.move.name,
            "effect": "damage_bonus",
            "amount": bonus,
            "description": "Rock Head [Errata] adds damage after a straight-line charge.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Vanguard")
def _vanguard_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    if ctx.defender.actions_taken:
        return
    attacker_index = None
    defender_index = None
    for idx, entry in enumerate(ctx.battle.initiative_order):
        if entry.actor_id == ctx.attacker_id:
            attacker_index = idx
        if entry.actor_id == ctx.defender_id:
            defender_index = idx
    if attacker_index is None or defender_index is None:
        return
    if attacker_index >= defender_index:
        return
    bonus = _aura_break_errata_adjust(ctx, "Vanguard", 5)
    if bonus == 0:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
    ctx.result["vanguard_bonus"] = bonus
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Vanguard",
            "move": ctx.move.name,
            "effect": "damage_bonus" if bonus > 0 else "damage_penalty",
            "amount": bonus,
            "description": "Vanguard punishes foes who have not acted.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="White Flame")
def _white_flame_enraged_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.attacker is None:
        return
    if not ctx.attacker.has_status("Enraged"):
        return
    before = int(ctx.result.get("damage", 0) or 0)
    ctx.result["damage"] = before + 5
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "White Flame",
            "move": ctx.move.name,
            "effect": "damage_bonus",
            "amount": 5,
            "description": "White Flame adds +5 damage while Enraged.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_ability_hook(phase="post_result_bully", ability="Bully")
def _bully_trips_on_super_effective_melee(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    type_multiplier = float(ctx.result.get("type_multiplier", 1.0) or 1.0) if ctx.result else 1.0
    if type_multiplier <= 1.0:
        return
    if not ctx.defender.has_status("Tripped"):
        ctx.defender.statuses.append({"name": "Tripped", "remaining": 1})
    if ctx.result is not None:
        ctx.result["bully_triggered"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Bully",
            "move": ctx.move.name,
            "effect": "trip",
            "description": "Bully trips and injures super-effective melee targets.",
            "target_hp": ctx.defender.hp,
        }
    )
