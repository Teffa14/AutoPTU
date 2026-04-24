"""Post-damage ability hooks."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ... import targeting, calculations, movement
from .... import ptu_engine
from ...battle_state import ActionType
from ...abilities.ability_variants import has_errata, has_ability_exact
from ...helpers.parental_bond import apply_parental_bond_enrage
from ....data_models import MoveSpec


@register_ability_hook(phase="post_damage", ability="Justified", holder="defender")
def _justified_raises_attack(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if has_ability_exact(ctx.defender, "Justified [Errata]"):
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if (ctx.effective_move.type or "").strip().lower() != "dark":
        return
    move_stub = MoveSpec(name="Justified", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=move_stub,
        target=ctx.defender,
        stat="atk",
        delta=1,
        effect="justified",
        description="Justified raises Attack after taking Dark-type damage.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Justified",
            "move": "Justified",
            "effect": "attack_raise",
            "description": "Justified raises Attack after taking Dark-type damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Justified [Errata]", holder="defender")
def _justified_errata_raises_attack(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if (ctx.effective_move.type or "").strip().lower() != "dark":
        return
    move_stub = MoveSpec(name="Justified [Errata]", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=move_stub,
        target=ctx.defender,
        stat="atk",
        delta=1,
        effect="justified",
        description="Justified [Errata] raises Attack after taking Dark-type damage.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Justified [Errata]",
            "move": "Justified [Errata]",
            "effect": "attack_raise",
            "description": "Justified [Errata] raises Attack after taking Dark-type damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Rattled", holder="defender")
def _rattled_raises_speed(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type not in {"dark", "ghost", "bug"}:
        return
    is_errata = has_errata(ctx.defender, "Rattled")
    ability_name = "Rattled [Errata]" if is_errata else "Rattled"
    move_stub = MoveSpec(name=ability_name, type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=move_stub,
        target=ctx.defender,
        stat="spd",
        delta=1,
        effect="rattled",
        description="Rattled raises Speed after taking frightening damage.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "speed_raise",
            "description": "Rattled raises Speed after taking Dark/Ghost/Bug damage.",
            "target_hp": ctx.defender.hp,
        }
    )
    if not is_errata:
        return
    if ctx.attacker is None or ctx.attacker.position is None or ctx.defender.position is None:
        return
    reachable = movement.legal_shift_tiles(ctx.battle, ctx.defender_id)
    if not reachable:
        return
    origin = ctx.defender.position
    destination = max(reachable, key=lambda coord: targeting.chebyshev_distance(coord, ctx.attacker.position))
    ctx.defender.position = destination
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "disengage",
            "from": origin,
            "to": destination,
            "description": "Rattled lets the target disengage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Sumo Stance [Errata]", holder="attacker")
def _sumo_stance_errata_push(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("hit"):
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    ready = next(iter(ctx.attacker.get_temporary_effects("sumo_stance_ready")), None)
    if ready is None:
        return
    ctx.attacker.remove_temporary_effect("sumo_stance_ready")
    ctx.battle._apply_push(ctx.attacker_id, ctx.defender_id, 1)
    ctx.attacker.add_temporary_effect(
        "push_immunity",
        expires_round=ctx.battle.round + 1,
        source="Sumo Stance [Errata]",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Sumo Stance [Errata]",
            "move": ctx.move.name,
            "effect": "push",
            "description": "Sumo Stance shoves the target back.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Pack Hunt", holder="defender")
def _pack_hunt_counter(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if ctx.defender.position is not None and ctx.attacker.position is not None:
        if ctx.battle.grid is not None and ctx.battle._team_for(ctx.defender_id) == ctx.battle._team_for(ctx.attacker_id):
            return
        if abs(ctx.defender.position[0] - ctx.attacker.position[0]) + abs(ctx.defender.position[1] - ctx.attacker.position[1]) > 1:
            return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    for entry in list(ctx.defender.get_temporary_effects("pack_hunt_used")):
        if entry.get("round") == ctx.battle.round:
            return
        ctx.defender.remove_temporary_effect("pack_hunt_used")
    roll = ctx.battle.rng.randint(1, 20)
    needed = 5
    if roll == 1 or roll < needed:
        return
    tick = ctx.attacker._apply_tick_damage(1)
    ctx.defender.add_temporary_effect("pack_hunt_used", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Pack Hunt",
            "move": ctx.move.name,
            "effect": "counter",
            "amount": tick,
            "roll": roll,
            "description": "Pack Hunt counters with a quick strike.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage_followup", ability="Cruelty")
def _cruelty_adds_injury(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if ctx.result is not None:
        ctx.result["cruelty_triggered"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Cruelty",
            "move": ctx.move.name,
            "effect": "injury",
            "description": "Cruelty adds an injury on a hit.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Psionic Screech")
def _psionic_screech_flinch(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("psionic_screech"):
        return
    if not ctx.result.get("hit"):
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="psionic_screech",
        description="Psionic Screech flinches targets hit by the converted move.",
        remaining=1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Psionic Screech",
            "move": ctx.move.name,
            "effect": "flinch",
            "description": "Psionic Screech flinches targets hit by the converted move.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability=None)
def _spiteful_intervention(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    defender_team = ctx.battle._team_for(ctx.defender_id)
    holders = [
        (pid, mon)
        for pid, mon in ctx.battle.pokemon.items()
        if not mon.fainted
        and mon.active
        and mon.has_ability("Spiteful Intervention")
        and ctx.battle._team_for(pid) == defender_team
        and pid != ctx.defender_id
    ]
    if not holders:
        return
    holders.sort(key=lambda item: item[0])
    holder_id, _holder = holders[0]
    last_entry = next(
        (
            entry
            for entry in ctx.attacker.get_temporary_effects("last_move")
            if entry.get("name")
        ),
        None,
    )
    if not last_entry:
        return
    if ctx.attacker.has_status("Disabled"):
        return
    ctx.attacker.statuses.append(
        {"name": "Disabled", "move": last_entry.get("name"), "remaining": 3}
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": holder_id,
            "target": ctx.attacker_id,
            "ability": "Spiteful Intervention",
            "move": "Spite",
            "effect": "spite",
            "description": "Spiteful Intervention disables the attacker's last move.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage_followup", ability="Wobble", holder="defender")
def _wobble_counter(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    used_entry = next(iter(ctx.defender.get_temporary_effects("wobble_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        return
    if used_entry is None:
        ctx.defender.add_temporary_effect("wobble_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    category = (ctx.move.category or "").strip().lower()
    counter_type = "Fighting" if category == "physical" else "Psychic"
    if ptu_engine.type_multiplier(counter_type, ctx.attacker.spec.types) <= 0:
        return
    before = ctx.attacker.hp or 0
    ctx.attacker.apply_damage(damage * 2)
    dealt = max(0, before - (ctx.attacker.hp or 0))
    if dealt > 0:
        ctx.battle.damage_received_this_round[ctx.attacker_id] = (
            ctx.battle.damage_received_this_round.get(ctx.attacker_id, 0) + dealt
        )
        ctx.battle._record_damage_exchange(ctx.defender_id, ctx.attacker_id)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Wobble",
            "move": "Counter" if category == "physical" else "Mirror Coat",
            "effect": "counter",
            "damage": dealt,
            "description": "Wobble reflects the triggering damage.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Winter's Kiss")
def _winters_kiss_heal_on_use(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "ice":
        return
    entry = next(iter(ctx.attacker.get_temporary_effects("winters_kiss_used")), None)
    if entry and entry.get("round") == ctx.battle.round and (entry.get("move") or "").strip().lower() == (
        ctx.move.name or ""
    ).strip().lower():
        return
    ctx.attacker.add_temporary_effect("winters_kiss_used", round=ctx.battle.round, move=ctx.move.name)
    healed = ctx.attacker._apply_tick_heal(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Winter's Kiss",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": "Winter's Kiss restores a tick when using Ice moves.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_ko", ability=None)
def _receiver_and_soul_heart(ctx: AbilityHookContext) -> None:
    if not ctx.defender_fainted or ctx.defender_id is None or ctx.defender is None:
        return
    battle = ctx.battle
    battle.fainted_history.append(
        {"round": battle.round, "attacker": ctx.attacker_id, "defender": ctx.defender_id}
    )
    defender_team = battle._team_for(ctx.defender_id)
    # Soul Heart triggers on any faint.
    for pid, mon in battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        if not mon.has_ability("Soul Heart"):
            continue
        used_entry = next(iter(mon.get_temporary_effects("soul_heart_used")), None)
        used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
        if used_count >= 2:
            continue
        if used_entry is None:
            mon.add_temporary_effect("soul_heart_used", count=used_count + 1)
        else:
            used_entry["count"] = used_count + 1
        before = int(mon.combat_stages.get("spatk", 0) or 0)
        mon.combat_stages["spatk"] = min(6, before + 2)
        temp_gain = mon.add_temp_hp(mon.tick_value())
        ctx.events.append(
            {
                "type": "ability",
                "actor": pid,
                "ability": "Soul Heart",
                "effect": "spatk_boost",
                "amount": 2,
                "temp_hp": temp_gain,
                "description": "Soul Heart empowers the user after a faint.",
                "target_hp": mon.hp,
            }
        )
    # Receiver: gain an ally's ability on ally faint.
    for pid, mon in battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        if not mon.has_ability("Receiver"):
            continue
        if battle._team_for(pid) != defender_team:
            continue
        if pid == ctx.defender_id:
            continue
        used_entry = next(iter(mon.get_temporary_effects("receiver_gain_used")), None)
        used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
        if used_count >= 1:
            continue
        donor_abilities = [name for name in ctx.defender.ability_names() if name.lower() != "receiver"]
        if not donor_abilities:
            continue
        gained = donor_abilities[0]
        mon.add_temporary_effect("granted_ability", ability=gained)
        if used_entry is None:
            mon.add_temporary_effect("receiver_gain_used", count=used_count + 1)
        else:
            used_entry["count"] = used_count + 1
        ctx.events.append(
            {
                "type": "ability",
                "actor": pid,
                "target": ctx.defender_id,
                "ability": "Receiver",
                "effect": "gain_ability",
                "gained": gained,
                "description": "Receiver copies an ally's ability.",
                "target_hp": mon.hp,
            }
        )
    # Receiver: on holder faint, grant their basic ability to an ally.
    if ctx.defender.has_ability("Receiver"):
        used_entry = next(iter(ctx.defender.get_temporary_effects("receiver_share_used")), None)
        used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
        if used_count < 1:
            allies = [
                (pid, mon)
                for pid, mon in battle.pokemon.items()
                if not mon.fainted
                and mon.active
                and battle._team_for(pid) == defender_team
                and pid != ctx.defender_id
            ]
            if allies:
                allies.sort(key=lambda item: item[0])
                ally_id, ally = allies[0]
                basic = None
                for entry in ctx.defender.spec.abilities:
                    if isinstance(entry, dict) and entry.get("name"):
                        basic = str(entry.get("name") or "").strip()
                        break
                    if isinstance(entry, str):
                        basic = entry.strip()
                        break
                if basic:
                    ally.add_temporary_effect("granted_ability", ability=basic)
                    ctx.events.append(
                        {
                            "type": "ability",
                            "actor": ctx.defender_id,
                            "target": ally_id,
                            "ability": "Receiver",
                            "effect": "share_ability",
                            "gained": basic,
                            "description": "Receiver shares a basic ability on fainting.",
                            "target_hp": ally.hp,
                        }
                    )
                    if used_entry is None:
                        ctx.defender.add_temporary_effect("receiver_share_used", count=used_count + 1)
                    else:
                        used_entry["count"] = used_count + 1


@register_ability_hook(phase="post_damage_followup", ability="Dry Skin", holder="defender")
def _dry_skin_fire_tick(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    extra = ctx.defender._apply_tick_damage(1)
    if extra <= 0:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    damage += extra
    if ctx.result is not None:
        ctx.result["damage"] = damage
    ctx.battle.damage_received_this_round[ctx.defender_id] = (
        ctx.battle.damage_received_this_round.get(ctx.defender_id, 0) + extra
    )
    ctx.battle._record_damage_exchange(ctx.attacker_id, ctx.defender_id)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Dry Skin",
            "move": ctx.move.name,
            "effect": "fire_tick",
            "amount": extra,
            "description": "Dry Skin takes extra damage from Fire-type moves.",
            "target_hp": ctx.defender.hp,
        }
    )


def _fox_fire_errata_ember() -> MoveSpec:
    return MoveSpec(
        name="Ember",
        type="Fire",
        category="Special",
        db=4,
        ac=2,
        range_kind="Ranged",
        range_value=6,
        target_kind="Ranged",
        target_range=6,
        freq="At-Will",
        range_text="Range 6, 1 Target",
    )


@register_ability_hook(phase="post_damage_followup", ability="Fox Fire [Errata]", holder="defender")
def _fox_fire_errata_followup(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.attacker is None or ctx.attacker_id is None:
        return
    if ctx.battle._team_for(ctx.attacker_id) == ctx.battle._team_for(ctx.defender_id):
        return
    defender_pos = ctx.defender.position
    attacker_pos = ctx.attacker.position
    if defender_pos is None or attacker_pos is None:
        return
    if targeting.chebyshev_distance(defender_pos, attacker_pos) > 6:
        return
    entry = next(iter(ctx.defender.get_temporary_effects("fox_fire_errata")), None)
    charges = int(entry.get("charges", 0) or 0) if entry else 0
    if charges <= 0:
        return
    if entry is not None:
        entry["charges"] = charges - 1
        if entry["charges"] <= 0:
            ctx.defender.remove_temporary_effect("fox_fire_errata")
    ember = _fox_fire_errata_ember()
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Fox Fire [Errata]",
            "move": ctx.move.name,
            "effect": "followup",
            "description": "Fox Fire unleashes an Ember wisp.",
            "target_hp": ctx.defender.hp,
        }
    )
    ctx.battle.resolve_move_targets(
        attacker_id=ctx.defender_id,
        move=ember,
        target_id=ctx.attacker_id,
        target_position=attacker_pos,
    )


@register_ability_hook(phase="post_ko", ability="Moxie")
def _moxie_raises_attack(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if not ctx.defender_fainted:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.effective_move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="moxie",
        description="Moxie raises Attack after knocking out a foe.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Moxie",
            "move": ctx.move.name,
            "effect": "attack_raise",
            "description": "Moxie raises Attack after knocking out a foe.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_ko", ability="Beast Boost")
def _beast_boost(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or not ctx.defender_fainted:
        return
    stats = {
        "atk": ctx.attacker.spec.atk,
        "def": ctx.attacker.spec.defense,
        "spatk": ctx.attacker.spec.spatk,
        "spdef": ctx.attacker.spec.spdef,
        "spd": ctx.attacker.spec.spd,
    }
    best_stat = max(stats.items(), key=lambda item: (item[1], item[0]))[0]
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.effective_move,
        target=ctx.attacker,
        stat=best_stat,
        delta=1,
        effect="beast_boost",
        description="Beast Boost raises the highest stat after a KO.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Beast Boost",
            "move": ctx.move.name,
            "effect": "stat_raise",
            "stat": best_stat,
            "description": "Beast Boost raises the highest stat after a KO.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_ko", ability="Chilling Neigh")
def _chilling_neigh(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or not ctx.defender_fainted:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.effective_move,
        target=ctx.attacker,
        stat="atk",
        delta=1,
        effect="chilling_neigh",
        description="Chilling Neigh raises Attack after a KO.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Chilling Neigh",
            "move": ctx.move.name,
            "effect": "attack_raise",
            "description": "Chilling Neigh raises Attack after a KO.",
            "target_hp": ctx.attacker.hp,
        }
    )
    if ctx.attacker.position is None:
        return
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.attacker_id or mon.fainted or not mon.active:
            continue
        if mon.position is None:
            continue
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 3:
            continue
        mon.add_temporary_effect("evasion_bonus", amount=-2, scope="all", expires_round=ctx.battle.round + 1)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Chilling Neigh",
                "move": ctx.move.name,
                "effect": "evasion_penalty",
                "amount": -2,
                "description": "Chilling Neigh chills nearby foes.",
                "target_hp": mon.hp,
            }
        )


@register_ability_hook(phase="post_ko", ability="Grim Neigh")
def _grim_neigh(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or not ctx.defender_fainted:
        return
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.attacker_id,
        move=ctx.effective_move,
        target=ctx.attacker,
        stat="spatk",
        delta=1,
        effect="grim_neigh",
        description="Grim Neigh raises Special Attack after a KO.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Grim Neigh",
            "move": ctx.move.name,
            "effect": "spatk_raise",
            "description": "Grim Neigh raises Special Attack after a KO.",
            "target_hp": ctx.attacker.hp,
        }
    )
    if ctx.attacker.position is None:
        return
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.attacker_id or mon.fainted or not mon.active:
            continue
        if mon.position is None:
            continue
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.attacker_id):
            continue
        if targeting.chebyshev_distance(ctx.attacker.position, mon.position) > 3:
            continue
        mon.add_temporary_effect("accuracy_penalty", amount=2, expires_round=ctx.battle.round + 1, source="Grim Neigh")
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Grim Neigh",
                "move": ctx.move.name,
                "effect": "accuracy_penalty",
                "amount": -2,
                "description": "Grim Neigh unnerves nearby foes.",
                "target_hp": mon.hp,
            }
        )


@register_ability_hook(phase="post_result", ability="Needles")
def _needles_tick(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if (ctx.effective_move.category or "").strip().lower() != "physical":
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    damage = int(ctx.result.get("damage", 0) or 0)
    if damage <= 0:
        return
    tick = ctx.defender._apply_tick_damage(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Needles",
            "move": ctx.move.name,
            "effect": "tick",
            "amount": tick,
            "description": "Needles pricks the target for a tick of damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Cotton Down", holder="defender")
def _cotton_down_burst(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.hit:
        return
    if ctx.defender.get_temporary_effects("cotton_down_used"):
        return
    ctx.defender.add_temporary_effect("cotton_down_used")
    origin = ctx.defender.position
    for pid, mon in ctx.battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        if mon.position is None or origin is None:
            continue
        if targeting.chebyshev_distance(mon.position, origin) > 1:
            continue
        if pid == ctx.defender_id:
            continue
        move_stub = MoveSpec(name="Cotton Down", type="Normal", category="Status")
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.defender_id,
            target_id=pid,
            move=move_stub,
            target=mon,
            stat="spd",
            delta=-1,
            effect="cotton_down",
            description="Cotton Down lowers Speed by -1 CS.",
        )
        if not mon.has_status("Slowed"):
            mon.statuses.append({"name": "Slowed", "remaining": 1})
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": pid,
                "ability": "Cotton Down",
                "move": ctx.move.name,
                "effect": "slow",
                "description": "Cotton Down slows nearby creatures.",
                "target_hp": mon.hp,
            }
        )


@register_ability_hook(phase="post_damage", ability="Dream Smoke", holder="defender")
def _dream_smoke_sleep(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    if not ctx.hit:
        return
    if ctx.defender.get_temporary_effects("dream_smoke_used"):
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    ctx.defender.add_temporary_effect("dream_smoke_used")
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.attacker_id,
        move=ctx.move,
        target=ctx.attacker,
        status="Sleep",
        effect="sleep",
        description="Dream Smoke puts the attacker to sleep.",
    )


@register_ability_hook(phase="post_result", ability="Chemical Romance", holder="attacker")
def _chemical_romance_infatuate(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.hit:
        return
    move_name = (ctx.move.name or "").strip().lower()
    if move_name not in {"poison gas", "smog", "sweet scent", "toxic", "venom drench"}:
        return
    gender = (ctx.defender.spec.gender or "").strip().lower()
    if gender not in {"m", "male"}:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Infatuated",
        effect="infatuate",
        description="Chemical Romance infatuates the target.",
    )


@register_ability_hook(phase="post_damage", ability="Gulp Missile", holder="defender")
def _gulp_missile_retaliate(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    entry = next(iter(ctx.defender.get_temporary_effects("gulp_missile_ready")), None)
    if entry is None:
        return
    ctx.defender.remove_temporary_effect("gulp_missile_ready")
    move = MoveSpec(name="Gulp Missile", type="Water", category="Physical", db=5, ac=4)
    accuracy = calculations.attack_hits(ctx.battle.rng, ctx.defender, ctx.attacker, move)
    hit = bool(accuracy.get("hit"))
    if not hit:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Gulp Missile",
                "move": ctx.move.name,
                "effect": "miss",
                "description": "Gulp Missile misses its retaliation.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    tick = ctx.attacker._apply_tick_damage(2)
    if tick > 0:
        if int(accuracy.get("roll", 0) or 0) % 2 == 0:
            ctx.battle._apply_status(
                ctx.events,
                attacker_id=ctx.defender_id,
                target_id=ctx.attacker_id,
                move=move,
                target=ctx.attacker,
                status="Paralyzed",
                effect="paralyze",
                description="Gulp Missile paralyzes on an even roll.",
            )
        else:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.defender_id,
                target_id=ctx.attacker_id,
                move=move,
                target=ctx.attacker,
                stat="def",
                delta=-1,
                effect="gulp_missile",
                description="Gulp Missile lowers Defense.",
            )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Gulp Missile",
            "move": ctx.move.name,
            "effect": "retaliate",
            "amount": tick,
            "description": "Gulp Missile retaliates after taking damage.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Innards Out", holder="defender")
def _innards_out_retaliate(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    pending = next(iter(ctx.defender.get_temporary_effects("innards_out_pending")), None)
    if pending is None:
        return
    ctx.defender.remove_temporary_effect("innards_out_pending")
    if ctx.defender.position is None or ctx.attacker.position is None:
        return
    if targeting.chebyshev_distance(ctx.defender.position, ctx.attacker.position) > 2:
        return
    counter = max(0, int(damage) * 2)
    if counter <= 0:
        return
    before = ctx.attacker.hp or 0
    ctx.attacker.apply_damage(counter)
    dealt = max(0, before - (ctx.attacker.hp or 0))
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Innards Out",
            "move": ctx.move.name,
            "effect": "retaliate",
            "amount": dealt,
            "description": "Innards Out reflects twice the damage taken.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Full Guard", holder="defender")
def _full_guard_temp_hp(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if ctx.defender.temp_hp > 0:
        return
    type_multiplier = float(ctx.result.get("type_multiplier", 1.0) or 1.0) if ctx.result else 1.0
    if type_multiplier <= 1.0:
        return
    gained = ctx.defender.add_temp_hp(ctx.defender.tick_value())
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Full Guard",
            "move": ctx.move.name,
            "effect": "temp_hp",
            "amount": gained,
            "description": "Full Guard grants temporary HP after super-effective damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Combo Striker")
def _combo_striker_followup(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    roll = ctx.result.get("roll")
    if roll not in {1, 10, 11}:
        return
    target_id = ctx.defender_id
    target_pos = ctx.defender.position if ctx.defender else None
    struggle = ctx.battle.build_struggle_move(ctx.attacker_id, ctx.attacker)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": target_id,
            "ability": "Combo Striker",
            "move": ctx.move.name,
            "effect": "followup",
            "description": "Combo Striker triggers a Struggle follow-up.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.attacker_id,
            move=struggle,
            target_id=target_id,
            target_position=target_pos,
        )
    except Exception:
        return


@register_ability_hook(phase="post_damage", ability="Perish Body", holder="defender")
def _perish_body_mark(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    for entry in list(ctx.defender.get_temporary_effects("perish_body_used")):
        return
    ctx.defender.add_temporary_effect("perish_body_used", expires_round=ctx.battle.round + 999)
    ctx.defender.add_temporary_effect("perish_song", count=3)
    ctx.attacker.add_temporary_effect("perish_song", count=3)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Perish Body",
            "move": ctx.move.name,
            "effect": "perish_body",
            "description": "Perish Body applies a Perish Count.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Sand Spit", holder="defender")
def _sand_spit_counter(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if ctx.defender.position is None or ctx.attacker.position is None:
        return
    if targeting.chebyshev_distance(ctx.defender.position, ctx.attacker.position) > 2:
        return
    for entry in list(ctx.defender.get_temporary_effects("sand_spit_used")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            ctx.defender.remove_temporary_effect("sand_spit_used")
            continue
        return
    ctx.defender.add_temporary_effect("sand_spit_used", expires_round=ctx.battle.round + 999)
    sand_attack = MoveSpec(
        name="Sand Attack",
        type="Ground",
        category="Status",
        db=0,
        ac=2,
        range_kind="Ranged",
        range_value=6,
        target_kind="Ranged",
        target_range=6,
        freq="At-Will",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Sand Spit",
            "move": ctx.move.name,
            "effect": "sand_spit",
            "description": "Sand Spit counters with Sand Attack.",
            "target_hp": ctx.attacker.hp,
        }
    )
    try:
        ctx.battle.resolve_move_targets(
            attacker_id=ctx.defender_id,
            move=sand_attack,
            target_id=ctx.attacker_id,
            target_position=ctx.attacker.position,
        )
    except Exception:
        return


@register_ability_hook(phase="post_damage", ability="Spray Down", holder="attacker")
def _spray_down_ground(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("hit"):
        return
    if not ctx.defender.can_fly():
        return
    is_errata = has_errata(ctx.attacker, "Spray Down")
    used_entry = next(iter(ctx.attacker.get_temporary_effects("spray_down_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    limit = 2 if is_errata else 1
    if used_count >= limit:
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("spray_down_used", count=1, expires_round=ctx.battle.round + 999)
    else:
        used_entry["count"] = used_count + 1
    ctx.defender.add_temporary_effect("spray_down", expires_round=ctx.battle.round + 3)
    ctx.defender.add_temporary_effect("force_grounded", expires_round=ctx.battle.round + 3)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Spray Down [Errata]" if is_errata else "Spray Down",
            "move": ctx.move.name,
            "effect": "grounded",
            "description": "Spray Down knocks the target out of the air.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Ragelope")
def _ragelope_enrage(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None:
        return
    if (ctx.move.category or "").strip().lower() != "physical":
        return
    roll = int(ctx.result.get("roll") or 0) if ctx.result else 0
    if roll < 18:
        return
    if ctx.attacker.has_status("Enraged"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat="atk",
            delta=1,
            effect="ragelope",
            description="Ragelope boosts Attack while enraged.",
        )
    else:
        ctx.attacker.statuses.append({"name": "Enraged"})
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.attacker_id,
            target_id=ctx.attacker_id,
            move=ctx.move,
            target=ctx.attacker,
            stat="spd",
            delta=1,
            effect="ragelope",
            description="Ragelope enrages and boosts Speed.",
        )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Ragelope",
            "move": ctx.move.name,
            "effect": "enrage",
            "description": "Ragelope triggers on a high roll.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Soulstealer")
def _soulstealer_heal(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("hit"):
        return
    for entry in list(ctx.attacker.get_temporary_effects("soulstealer_used")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            ctx.attacker.remove_temporary_effect("soulstealer_used")
            continue
        return
    ctx.attacker.add_temporary_effect("soulstealer_used", expires_round=ctx.battle.round + 999)
    max_hp = ctx.attacker.max_hp()
    if max_hp <= 0:
        return
    defender_fainted = bool(ctx.defender_fainted)
    if not defender_fainted and (ctx.defender.hp or 0) <= 0:
        defender_fainted = True
    before = ctx.attacker.hp or 0
    if defender_fainted:
        ctx.attacker.injuries = 0
        ctx.attacker.heal(max_hp)
        description = "Soulstealer drains vitality after a knockout."
    else:
        ctx.attacker.injuries = max(0, int(ctx.attacker.injuries or 0) - 1)
        ctx.attacker.heal(max_hp // 4)
        description = "Soulstealer drains vitality."
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Soulstealer",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": description,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Stench")
@register_ability_hook(phase="post_damage", ability="Stench [Errata]")
def _stench_flinch(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("hit"):
        return
    effect_text = (
        (ctx.effective_move.effects_text if ctx.effective_move else None)
        or (ctx.move.effects_text if ctx.move else None)
        or ""
    ).lower()
    if "flinch" in effect_text:
        return
    roll = int(ctx.result.get("roll") or 0)
    if roll < 19:
        return
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Flinch",
        effect="stench",
        description="Stench causes flinching on high rolls.",
        roll=roll,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Stench",
            "move": ctx.move.name,
            "effect": "flinch",
            "description": "Stench adds a flinch chance.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Stalwart", holder="defender")
def _stalwart_raise_stats(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    max_hp = ctx.defender.max_hp()
    if max_hp <= 0:
        return
    for entry in list(ctx.defender.get_temporary_effects("stalwart_used")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            ctx.defender.remove_temporary_effect("stalwart_used")
            continue
        return
    ctx.defender.add_temporary_effect("stalwart_used", expires_round=ctx.battle.round + 999)
    for stat in ("atk", "spatk", "def", "spdef"):
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.defender_id,
            target_id=ctx.defender_id,
            move=ctx.move,
            target=ctx.defender,
            stat=stat,
            delta=1,
            effect="stalwart",
            description="Stalwart hardens against massive damage.",
        )
    ctx.defender.add_temporary_effect("no_intercept", expires_round=ctx.battle.round + 1)
    ctx.defender.add_temporary_effect("target_lock", expires_round=ctx.battle.round + 1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Stalwart",
            "move": ctx.move.name,
            "effect": "stance",
            "description": "Stalwart raises all combat stages.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Starlight", holder="attacker")
def _starlight_confuse(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None or ctx.defender_id is None:
        return
    if has_errata(ctx.attacker, "Starlight"):
        return
    if not ctx.result or not ctx.result.get("hit"):
        return
    if (ctx.move.category or "").strip().lower() == "status":
        return
    if int(ctx.result.get("damage", 0) or 0) <= 0:
        return
    if not ctx.attacker.get_temporary_effects("luminous"):
        return
    while ctx.attacker.remove_temporary_effect("luminous"):
        continue
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Confused",
        effect="starlight",
        description="Starlight expends to confuse the target.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Starlight",
            "move": ctx.move.name,
            "effect": "confuse",
            "description": "Starlight confuses the target on hit.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Steam Engine", holder="defender")
def _steam_engine_smokescreen(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    damage = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage <= 0:
        return
    if move_type not in {"fire", "water"}:
        return
    entry = next(iter(ctx.defender.get_temporary_effects("steam_engine_used")), None)
    count = int(entry.get("count", 0) or 0) if entry else 0
    if count >= 2:
        return
    if entry is None:
        ctx.defender.add_temporary_effect("steam_engine_used", count=1)
    else:
        entry["count"] = count + 1
    ctx.defender.add_temporary_effect(
        "evasion_bonus",
        amount=3,
        scope="all",
        expires_round=ctx.battle.round + 3,
        source="Steam Engine",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Steam Engine",
            "move": ctx.move.name,
            "effect": "smokescreen",
            "description": "Steam Engine triggers Smokescreen.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Soulstealer [Errata]")
def _soulstealer_errata_post_result(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("hit"):
        return
    try:
        damage = int(ctx.result.get("damage", 0) or 0)
    except (TypeError, ValueError):
        damage = 0
    if damage > 0:
        return
    max_hp = ctx.attacker.max_hp()
    if max_hp <= 0:
        return
    before = ctx.attacker.hp or 0
    ctx.attacker.injuries = max(0, int(ctx.attacker.injuries or 0) - 1)
    ctx.attacker.heal(max_hp // 4)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Soulstealer [Errata]",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": "Soulstealer drains vitality.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Soulstealer [Errata]")
def _soulstealer_errata(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("hit"):
        return
    max_hp = ctx.attacker.max_hp()
    if max_hp <= 0:
        return
    defender_fainted = bool(ctx.defender_fainted)
    if not defender_fainted and (ctx.defender.hp or 0) <= 0:
        defender_fainted = True
    before = ctx.attacker.hp or 0
    if defender_fainted:
        ctx.attacker.injuries = 0
        ctx.attacker.heal(max_hp // 2)
        description = "Soulstealer drains vitality after a knockout."
    else:
        ctx.attacker.injuries = max(0, int(ctx.attacker.injuries or 0) - 1)
        ctx.attacker.heal(max_hp // 4)
        description = "Soulstealer drains vitality."
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Soulstealer [Errata]",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": description,
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Tangling Hair", holder="defender")
def _tangling_hair(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None:
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    move_stub = MoveSpec(name="Tangling Hair", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.attacker_id,
        move=move_stub,
        target=ctx.attacker,
        stat="spd",
        delta=-1,
        effect="tangling_hair",
        description="Tangling Hair lowers Speed on contact.",
    )
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.attacker_id,
        move=move_stub,
        target=ctx.attacker,
        status="Slowed",
        effect="tangling_hair",
        description="Tangling Hair slows the attacker.",
        remaining=1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Tangling Hair",
            "move": ctx.move.name,
            "effect": "slow",
            "description": "Tangling Hair punishes melee attackers.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Teravolt")
def _teravolt_suppress(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("neutralized", source_id=ctx.attacker_id)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Teravolt",
            "move": ctx.move.name,
            "effect": "neutralize",
            "description": "Teravolt suppresses the target's abilities.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Turboblaze")
def _turboblaze_suppress(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    ctx.defender.add_temporary_effect("neutralized", source_id=ctx.attacker_id)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Turboblaze",
            "move": ctx.move.name,
            "effect": "neutralize",
            "description": "Turboblaze suppresses the target's abilities.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Tingle")
def _tingle(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None:
        return
    if targeting.normalized_area_kind(ctx.effective_move):
        return
    if ctx.attacker.position is None or ctx.defender.position is None:
        return
    if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 1:
        return
    damage = ctx.defender._apply_tick_damage(1)
    ctx.defender.add_temporary_effect(
        "damage_penalty",
        amount=5,
        category="all",
        expires_round=ctx.battle.round + 1,
        source="Tingle",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Tingle",
            "move": ctx.move.name,
            "effect": "tingle",
            "amount": damage,
            "description": "Tingle drains a tick and weakens damage rolls.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Sunglow")
def _sunglow_blind(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None:
        return
    if has_errata(ctx.attacker, "Sunglow"):
        return
    if not ctx.attacker.get_temporary_effects("radiant"):
        return
    while ctx.attacker.remove_temporary_effect("radiant"):
        continue
    ctx.battle._apply_status(
        ctx.events,
        attacker_id=ctx.attacker_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        status="Blinded",
        effect="sunglow",
        description="Sunglow blinds the target.",
        remaining=1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Sunglow",
            "move": ctx.move.name,
            "effect": "blind",
            "description": "Sunglow expends Radiance to blind the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Water Compaction", holder="defender")
def _water_compaction(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "water":
        return
    move_stub = MoveSpec(name="Water Compaction", type="Water", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=move_stub,
        target=ctx.defender,
        stat="def",
        delta=2,
        effect="water_compaction",
        description="Water Compaction hardens Defense.",
    )


@register_ability_hook(phase="post_damage", ability="Weak Armor", holder="defender")
def _weak_armor(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if (ctx.effective_move.category or "").strip().lower() != "physical":
        return
    move_stub = MoveSpec(name="Weak Armor", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=move_stub,
        target=ctx.defender,
        stat="def",
        delta=-1,
        effect="weak_armor",
        description="Weak Armor lowers Defense.",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=move_stub,
        target=ctx.defender,
        stat="spd",
        delta=1,
        effect="weak_armor",
        description="Weak Armor raises Speed.",
    )


@register_ability_hook(phase="post_damage", ability="Wandering Spirit", holder="defender")
def _wandering_spirit_swap(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None:
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "melee":
        return
    used_entry = next(iter(ctx.defender.get_temporary_effects("wandering_spirit_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        return
    if ctx.battle._blocks_ability_replace(ctx.attacker):
        return
    abilities_attacker = ctx.attacker.ability_names()
    abilities_defender = ctx.defender.ability_names()
    if not abilities_attacker or not abilities_defender:
        return
    chosen_attacker = ctx.battle.rng.choice(abilities_attacker)
    chosen_defender = ctx.battle.rng.choice(abilities_defender)
    while ctx.attacker.remove_temporary_effect("entrained_ability"):
        continue
    while ctx.defender.remove_temporary_effect("entrained_ability"):
        continue
    ctx.attacker.add_temporary_effect("entrained_ability", ability=chosen_defender)
    ctx.defender.add_temporary_effect("entrained_ability", ability=chosen_attacker)
    if used_entry is None:
        ctx.defender.add_temporary_effect("wandering_spirit_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Wandering Spirit",
            "move": ctx.move.name,
            "effect": "ability_swap",
            "description": "Wandering Spirit swaps abilities.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Weeble", holder="defender")
def _weeble_counter(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None:
        return
    if ctx.attacker.position is None or ctx.defender.position is None:
        return
    if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 1:
        return
    if not ctx.defender.has_action_available(ActionType.STANDARD):
        return
    damage_taken = int(ctx.result.get("damage", 0) or 0) if ctx.result else 0
    if damage_taken <= 0:
        return
    roll = ctx.battle.rng.randint(1, 20)
    evasion = calculations.evasion_value(ctx.attacker, "physical")
    accuracy_stage = calculations.accuracy_stage_value(
        ctx.defender.combat_stages.get("accuracy", 0) + ctx.defender.spec.accuracy_cs
    )
    needed = max(2, 4 + evasion - accuracy_stage)
    hit = roll == 20 or (roll >= needed and roll != 1)
    ctx.defender.mark_action(ActionType.STANDARD, "Weeble")
    if not hit:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Weeble",
                "move": ctx.move.name,
                "effect": "miss",
                "roll": roll,
                "description": "Weeble misses the counterstrike.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    dealt = max(1, int(damage_taken / 3))
    ctx.battle._apply_damage_with_injury_rules(ctx.attacker_id, dealt)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Weeble",
            "move": ctx.move.name,
            "effect": "counter",
            "amount": dealt,
            "roll": roll,
            "description": "Weeble strikes back for a third of the damage taken.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_ability_hook(phase="post_ko", ability="Aftermath [Errata]", holder="defender")
def _aftermath_errata_burst(ctx: AbilityHookContext) -> None:
    if not ctx.defender_fainted or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.defender.get_temporary_effects("aftermath_errata_used"):
        return
    ctx.defender.add_temporary_effect("aftermath_errata_used")
    center = ctx.defender.position
    for pid, mon in ctx.battle.pokemon.items():
        if pid == ctx.defender_id or mon.fainted or mon.hp is None or mon.hp <= 0:
            continue
        if center is not None and mon.position is not None:
            if targeting.chebyshev_distance(center, mon.position) > 1:
                continue
        damage = mon.tick_value() * 3
        before = mon.hp or 0
        mon.apply_damage(damage)
        dealt = max(0, before - (mon.hp or 0))
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": pid,
                "ability": "Aftermath [Errata]",
                "move": ctx.move.name,
                "effect": "burst",
                "amount": dealt,
                "description": "Aftermath [Errata] bursts for three ticks of damage.",
                "target_hp": mon.hp,
            }
        )


@register_ability_hook(phase="post_damage", ability=None, holder="defender")
def _parental_bond_baby_faints(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.defender.fainted:
        return
    entry = next(iter(ctx.defender.get_temporary_effects("parental_bond_child")), None)
    if entry is None:
        return
    mother_id = entry.get("mother_id")
    if not mother_id:
        return
    if apply_parental_bond_enrage(ctx.battle, mother_id, ctx.defender_id):
        ctx.events.append(
            {
                "type": "ability",
                "actor": mother_id,
                "target": ctx.defender_id,
                "ability": "Parental Bond",
                "move": ctx.move.name,
                "effect": "enraged",
                "description": "Parental Bond enrages the mother after the baby faints.",
                "target_hp": ctx.defender.hp,
            }
        )
        return


@register_ability_hook(phase="post_damage", ability="Ugly")
def _ugly_flinch(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    roll = int(ctx.result.get("roll") or 0) if ctx.result else 0
    if roll < 19:
        return
    if not ctx.defender.has_status("Flinched"):
        ctx.defender.statuses.append({"name": "Flinched", "remaining": 1})
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Ugly",
            "move": ctx.move.name,
            "effect": "flinch",
            "description": "Ugly causes a flinch on a high roll.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_damage", ability="Celebrate [Errata]", holder="attacker")
def _celebrate_errata_disengage(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.result or not ctx.result.get("hit") or int(ctx.damage or 0) <= 0:
        return
    if not ctx.attacker.get_temporary_effects("celebrate_errata_ready"):
        return
    ctx.attacker.remove_temporary_effect("celebrate_errata_ready")
    if ctx.battle.grid is None or ctx.attacker.position is None:
        return
    origin = ctx.attacker.position
    max_distance = 2 if has_ability_exact(ctx.attacker, "Celebrate [Errata]") else 1
    reachable = movement.legal_shift_tiles(ctx.battle, ctx.attacker_id)
    reachable = [
        coord
        for coord in reachable
        if targeting.chebyshev_distance(origin, coord) <= max_distance and coord != origin
    ]
    if not reachable:
        return
    if ctx.defender.position is not None:
        reachable.sort(
            key=lambda coord: (targeting.chebyshev_distance(coord, ctx.defender.position), coord),
            reverse=True,
        )
    else:
        reachable.sort()
    destination = reachable[0]
    ctx.attacker.position = destination
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Celebrate [Errata]",
            "move": ctx.move.name,
            "effect": "disengage",
            "from": origin,
            "to": destination,
            "description": "Celebrate [Errata] lets the attacker disengage after a hit.",
            "target_hp": ctx.attacker.hp,
        }
    )
