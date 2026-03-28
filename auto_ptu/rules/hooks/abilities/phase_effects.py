"""Ability phase hooks for start/end/command timing."""

from __future__ import annotations

import math
from typing import List

from ....data_models import MoveSpec
from ...battle_state import ActionType
from ... import targeting
from ...abilities.ability_variants import has_errata, has_ability_exact
from ..phase_hooks import PhaseHookContext, register_phase_hook
from ...helpers.parental_bond import (
    ensure_parental_bond_baby,
    reset_parental_bond_turn,
    apply_parental_bond_enrage,
)


def _guts_phase(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    actor_id = ctx.actor_id
    events = ctx.events
    guts_statuses = {
        "burned",
        "poisoned",
        "badly poisoned",
        "paralyzed",
        "frozen",
        "freeze",
        "sleep",
        "asleep",
    }
    has_guts_status = any(pokemon.has_status(name) for name in guts_statuses)
    entry = next(iter(pokemon.get_temporary_effects("guts_active")), None)
    move = MoveSpec(name="Guts", type="Normal", category="Status")
    if has_guts_status and entry is None:
        before = pokemon.combat_stages.get("atk", 0)
        battle._apply_combat_stage(
            events,
            attacker_id=actor_id,
            target_id=actor_id,
            move=move,
            target=pokemon,
            stat="atk",
            delta=2,
            description="Guts raises Attack by +2 CS while afflicted.",
            effect="guts",
        )
        applied = pokemon.combat_stages.get("atk", 0) - before
        pokemon.add_temporary_effect("guts_active", atk_delta=applied)
    elif not has_guts_status and entry is not None:
        atk_delta = int(entry.get("atk_delta", 0) or 0)
        if atk_delta:
            battle._apply_combat_stage(
                events,
                attacker_id=actor_id,
                target_id=actor_id,
                move=move,
                target=pokemon,
                stat="atk",
                delta=-atk_delta,
                description="Guts ends when the affliction is gone.",
                effect="guts_end",
            )
        pokemon.remove_temporary_effect("guts_active")


def _toxic_boost_phase(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if has_errata(pokemon, "Toxic Boost"):
        return
    battle = ctx.battle
    actor_id = ctx.actor_id
    events = ctx.events
    toxic_statuses = {"poisoned", "badly poisoned", "poison"}
    has_toxic = any(pokemon.has_status(name) for name in toxic_statuses)
    entry = next(iter(pokemon.get_temporary_effects("toxic_boost_active")), None)
    move_stub = MoveSpec(name="Toxic Boost", type="Poison", category="Status")
    if has_toxic and entry is None:
        before = pokemon.combat_stages.get("atk", 0)
        battle._apply_combat_stage(
            events,
            attacker_id=actor_id,
            target_id=actor_id,
            move=move_stub,
            target=pokemon,
            stat="atk",
            delta=2,
            description="Toxic Boost raises Attack while poisoned.",
            effect="toxic_boost",
        )
        applied = pokemon.combat_stages.get("atk", 0) - before
        pokemon.add_temporary_effect("toxic_boost_active", atk_delta=applied)
    elif not has_toxic and entry is not None:
        atk_delta = int(entry.get("atk_delta", 0) or 0)
        if atk_delta:
            battle._apply_combat_stage(
                events,
                attacker_id=actor_id,
                target_id=actor_id,
                move=move_stub,
                target=pokemon,
                stat="atk",
                delta=-atk_delta,
                description="Toxic Boost ends when poison fades.",
                effect="toxic_boost_end",
            )
        pokemon.remove_temporary_effect("toxic_boost_active")


def _thermosensitive_phase(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    actor_id = ctx.actor_id
    events = ctx.events
    weather = (battle.effective_weather() or "").strip().lower()
    sunny = "sun" in weather
    entry = next(iter(pokemon.get_temporary_effects("thermosensitive_active")), None)
    move_stub = MoveSpec(name="Thermosensitive", type="Fire", category="Status")
    if sunny and entry is None:
        applied = {}
        for stat in ("atk", "spatk"):
            before = pokemon.combat_stages.get(stat, 0)
            battle._apply_combat_stage(
                events,
                attacker_id=actor_id,
                target_id=actor_id,
                move=move_stub,
                target=pokemon,
                stat=stat,
                delta=2,
                description="Thermosensitive raises Attack and Special Attack in sun.",
                effect="thermosensitive",
            )
            applied[stat] = pokemon.combat_stages.get(stat, 0) - before
        pokemon.add_temporary_effect(
            "thermosensitive_active",
            atk_delta=applied.get("atk", 0),
            spatk_delta=applied.get("spatk", 0),
        )
    elif not sunny and entry is not None:
        for stat, key in (("atk", "atk_delta"), ("spatk", "spatk_delta")):
            delta = -int(entry.get(key, 0) or 0)
            if delta:
                battle._apply_combat_stage(
                    events,
                    attacker_id=actor_id,
                    target_id=actor_id,
                    move=move_stub,
                    target=pokemon,
                    stat=stat,
                    delta=delta,
                    description="Thermosensitive ends when sunlight fades.",
                    effect="thermosensitive_end",
                )
        pokemon.remove_temporary_effect("thermosensitive_active")


def _wave_rider_phase(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    actor_id = ctx.actor_id
    events = ctx.events
    entry = next(iter(pokemon.get_temporary_effects("wave_rider_active")), None)
    in_water = False
    if battle.grid is not None and pokemon.position is not None:
        tile_meta = battle.grid.tiles.get(pokemon.position, {})
        tile_type = str(tile_meta.get("type", "")).strip().lower()
        if any(tag in tile_type for tag in ("water", "ocean", "sea", "lake", "river", "stream")):
            in_water = True
    move_stub = MoveSpec(name="Wave Rider", type="Water", category="Status")
    if in_water and entry is None:
        before = pokemon.combat_stages.get("spd", 0)
        battle._apply_combat_stage(
            events,
            attacker_id=actor_id,
            target_id=actor_id,
            move=move_stub,
            target=pokemon,
            stat="spd",
            delta=4,
            description="Wave Rider boosts Speed in water.",
            effect="wave_rider",
        )
        applied = pokemon.combat_stages.get("spd", 0) - before
        pokemon.add_temporary_effect("wave_rider_active", spd_delta=applied)
    elif not in_water and entry is not None:
        spd_delta = int(entry.get("spd_delta", 0) or 0)
        if spd_delta:
            battle._apply_combat_stage(
                events,
                attacker_id=actor_id,
                target_id=actor_id,
                move=move_stub,
                target=pokemon,
                stat="spd",
                delta=-spd_delta,
                description="Wave Rider ends when leaving water.",
                effect="wave_rider_end",
            )
        pokemon.remove_temporary_effect("wave_rider_active")


@register_phase_hook("start", ability="Defeatist")
def _defeatist_start(ctx: PhaseHookContext) -> None:
    ctx.events.extend(ctx.battle._sync_defeatist_threshold(ctx.actor_id))


@register_phase_hook("end", ability="Defeatist")
def _defeatist_end(ctx: PhaseHookContext) -> None:
    ctx.events.extend(ctx.battle._sync_defeatist_threshold(ctx.actor_id))


@register_phase_hook("start", ability="Defeatist [Errata]")
def _defeatist_errata_start(ctx: PhaseHookContext) -> None:
    ctx.events.extend(ctx.battle._sync_defeatist_errata_threshold(ctx.actor_id))


@register_phase_hook("end", ability="Defeatist [Errata]")
def _defeatist_errata_end(ctx: PhaseHookContext) -> None:
    ctx.events.extend(ctx.battle._sync_defeatist_errata_threshold(ctx.actor_id))


@register_phase_hook("start", ability="Guts")
def _guts_start(ctx: PhaseHookContext) -> None:
    _guts_phase(ctx)


@register_phase_hook("end", ability="Guts")
def _guts_end(ctx: PhaseHookContext) -> None:
    _guts_phase(ctx)


@register_phase_hook("start", ability="Toxic Boost")
def _toxic_boost_start(ctx: PhaseHookContext) -> None:
    _toxic_boost_phase(ctx)


@register_phase_hook("end", ability="Toxic Boost")
def _toxic_boost_end(ctx: PhaseHookContext) -> None:
    _toxic_boost_phase(ctx)


@register_phase_hook("start", ability="Thermosensitive")
def _thermosensitive_start(ctx: PhaseHookContext) -> None:
    _thermosensitive_phase(ctx)


@register_phase_hook("end", ability="Thermosensitive")
def _thermosensitive_end(ctx: PhaseHookContext) -> None:
    _thermosensitive_phase(ctx)


@register_phase_hook("start", ability="Wave Rider")
def _wave_rider_start(ctx: PhaseHookContext) -> None:
    _wave_rider_phase(ctx)


@register_phase_hook("end", ability="Wave Rider")
def _wave_rider_end(ctx: PhaseHookContext) -> None:
    _wave_rider_phase(ctx)


@register_phase_hook("start", ability="Discipline")
def _discipline(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if pokemon.get_temporary_effects("discipline_used"):
        return
    cured: List[str] = []
    removed = pokemon.remove_status_by_names(ctx.confusion_status_names)
    if removed:
        cured.append(removed)
    removed = pokemon.remove_status_by_names({"enraged"})
    if removed:
        cured.append(removed)
    removed = pokemon.remove_status_by_names({"infatuated"})
    if removed:
        cured.append(removed)
    removed = pokemon.remove_status_by_names({"flinch", "flinched"})
    if removed:
        cured.append(removed)
    if cured:
        pokemon.add_temporary_effect("discipline_used")
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Discipline",
                "phase": ctx.phase,
                "effect": "cure",
                "statuses": cured,
                "description": "Discipline cures mental afflictions on initiative.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Truant")
def _truant_start(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    roll = battle.rng.randint(1, 20)
    pokemon.temporary_effects = [
        entry for entry in pokemon.temporary_effects if entry.get("kind") != "truant_state"
    ]
    skipped = roll <= 7 and pokemon.has_action_available(ActionType.STANDARD)
    healed = 0
    if skipped:
        pokemon.mark_action(ActionType.STANDARD, "Truant")
        healed = pokemon._apply_tick_heal(1)
        pokemon.add_temporary_effect(
            "save_bonus",
            amount=3,
            expires_round=battle.round,
            source="Truant",
        )
    pokemon.add_temporary_effect(
        "truant_state",
        round=battle.round,
        roll=roll,
        skipped=skipped,
        heal=healed,
    )
    if not skipped:
        return
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Truant",
            "phase": ctx.phase,
            "effect": "skip_standard",
            "roll": roll,
            "heal": healed,
            "description": "Truant prevents a Standard Action this turn.",
            "target_hp": pokemon.hp,
        }
    )


@register_phase_hook("start", ability="Covert")
def _covert(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    if not battle._covert_in_habitat(pokemon):
        return
    for entry in list(pokemon.get_temporary_effects("evasion_bonus")):
        if (entry.get("source") or "").strip().lower() == "covert":
            pokemon.temporary_effects.remove(entry)
    pokemon.add_temporary_effect(
        "evasion_bonus",
        amount=2,
        scope="all",
        expires_round=battle.round,
        source="Covert",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Covert",
            "phase": ctx.phase,
            "effect": "evasion_bonus",
            "amount": 2,
            "description": "Covert raises evasion while in a natural habitat.",
            "target_hp": pokemon.hp,
        }
    )


@register_phase_hook("command", ability="Bad Dreams")
def _bad_dreams(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    affected: List[str] = []
    if pokemon.position is not None:
        for pid, mon in battle.pokemon.items():
            if mon.hp is None or mon.hp <= 0:
                continue
            if mon.position is None:
                continue
            if targeting.chebyshev_distance(pokemon.position, mon.position) <= 5:
                affected.append(pid)
    else:
        affected = [
            pid for pid, mon in battle.pokemon.items() if mon.hp is not None and mon.hp > 0
        ]
    for pid in affected:
        target = battle.pokemon.get(pid)
        if target is None:
            continue
        if not (target.has_status("Sleep") or target.has_status("Asleep") or target.has_status("Bad Sleep")):
            continue
        damage = target._apply_tick_damage(1)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "target": pid,
                "ability": "Bad Dreams",
                "phase": ctx.phase,
                "effect": "tick",
                "amount": damage,
                "description": "Bad Dreams harms sleeping targets nearby.",
                "target_hp": target.hp,
            }
        )


@register_phase_hook("start", ability="Beautiful")
def _beautiful(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    if pokemon.get_temporary_effects("beautiful_used"):
        return
    affected: List[str] = []
    if pokemon.position is not None:
        for pid, mon in battle.pokemon.items():
            if mon.hp is None or mon.hp <= 0:
                continue
            if mon.position is None:
                continue
            if targeting.chebyshev_distance(pokemon.position, mon.position) <= 1:
                affected.append(pid)
    else:
        affected = [
            pid for pid, mon in battle.pokemon.items() if mon.hp is not None and mon.hp > 0
        ]
    for pid in affected:
        target = battle.pokemon.get(pid)
        if target is None:
            continue
        removed = target.remove_status_by_names({"enraged"})
        if removed:
            pokemon.add_temporary_effect("beautiful_used")
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "target": pid,
                    "ability": "Beautiful",
                    "phase": ctx.phase,
                    "effect": "cure_enraged",
                    "description": "Beautiful calms an adjacent enraged target.",
                    "target_hp": target.hp,
                }
            )


@register_phase_hook("end", ability="Deep Sleep")
def _deep_sleep(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if (
        pokemon.has_status("Sleep")
        or pokemon.has_status("Asleep")
        or pokemon.has_temporary_effect("asleep_this_phase")
    ):
        healed = pokemon._apply_tick_heal(1)
        if healed:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Deep Sleep",
                    "phase": ctx.phase,
                    "effect": "heal",
                    "amount": healed,
                    "description": "Deep Sleep restores a tick of HP while asleep.",
                    "target_hp": pokemon.hp,
                }
            )


@register_phase_hook("start", ability="Hunger Switch")
def _hunger_switch(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    choice = None
    for entry in list(pokemon.get_temporary_effects("hunger_switch_choice")):
        raw = str(entry.get("mode") or entry.get("choice") or "").strip().lower()
        if raw in {"full", "full_belly", "full belly", "belly"}:
            choice = "full"
        elif raw in {"hangry", "hunger"}:
            choice = "hangry"
        pokemon.remove_temporary_effect("hunger_switch_choice")
        break
    if choice is None:
        pending_entry = next(iter(pokemon.get_temporary_effects("hunger_switch_pending")), None)
        if pending_entry and pending_entry.get("round") == battle.round:
            return
        if battle.is_player_controlled(ctx.actor_id):
            pokemon.add_temporary_effect("hunger_switch_pending", round=battle.round)
            return
        choice = "hangry"
    while pokemon.remove_temporary_effect("hunger_switch_mode"):
        continue
    pokemon.add_temporary_effect(
        "hunger_switch_mode",
        mode=choice,
        round=battle.round,
        expires_round=battle.round + 1,
    )
    if choice == "full":
        pokemon.add_temporary_effect(
            "accuracy_bonus",
            amount=2,
            round=battle.round,
            expires_round=battle.round + 1,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Hunger Switch",
                "phase": ctx.phase,
                "effect": "accuracy_bonus",
                "amount": 2,
                "description": "Hunger Switch (Full Belly) boosts accuracy.",
                "target_hp": pokemon.hp,
            }
        )
    else:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Hunger Switch",
                "phase": ctx.phase,
                "effect": "damage_bonus",
                "amount": 5,
                "description": "Hunger Switch (Hangry) boosts damage rolls.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("end", ability="Lancer")
def _lancer_end(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    shifted_distance = 0
    for entry in list(pokemon.get_temporary_effects("lancer_shift")):
        if entry.get("round") != battle.round:
            pokemon.remove_temporary_effect("lancer_shift")
            continue
        shifted_distance = max(shifted_distance, int(entry.get("distance", 0) or 0))
    if shifted_distance >= 3:
        pokemon.add_temporary_effect(
            "crit_range_bonus",
            bonus=3,
            source="Lancer",
            expires_round=battle.round + 1,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Lancer",
                "phase": ctx.phase,
                "effect": "crit_range",
                "amount": 3,
                "description": "Lancer sharpens critical range after a charge.",
                "target_hp": pokemon.hp,
            }
        )
        return
    if not any(getattr(key, "value", "") == "shift" for key in pokemon.actions_taken):
        pokemon.add_temporary_effect(
            "damage_reduction",
            amount=5,
            round=battle.round,
            expires_round=battle.round + 1,
            source="Lancer",
            consume=False,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Lancer",
                "phase": ctx.phase,
                "effect": "damage_reduction",
                "amount": 5,
                "description": "Lancer grants damage reduction after holding position.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Ice Body")
def _ice_body(ctx: PhaseHookContext) -> None:
    if has_ability_exact(ctx.pokemon, "Ice Body [Errata]"):
        return
    pokemon = ctx.pokemon
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "hail" in weather or "snow" in weather:
        healed = pokemon._apply_tick_heal(1)
        if healed:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Ice Body",
                    "phase": ctx.phase,
                    "effect": "heal",
                    "amount": healed,
                    "description": "Ice Body restores HP during hail.",
                    "target_hp": pokemon.hp,
                }
            )


@register_phase_hook("start", ability="Ice Body [Errata]")
def _ice_body_errata(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    max_hp = pokemon.max_hp()
    current_hp = pokemon.hp or 0
    in_hail = "hail" in weather or "snow" in weather
    low_hp = max_hp > 0 and current_hp * 2 <= max_hp
    if not (in_hail or low_hp):
        return
    healed = pokemon._apply_tick_heal(1)
    if healed:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Ice Body [Errata]",
                "phase": ctx.phase,
                "effect": "heal",
                "amount": healed,
                "description": "Ice Body [Errata] restores HP.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("end", ability="Hay Fever")
def _hay_fever(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if pokemon.has_status("Sleep") or pokemon.has_status("Asleep"):
        ctx.events.extend(
            ctx.battle._apply_hay_fever(ctx.actor_id, source="Hay Fever", trigger="sleep")
        )


@register_phase_hook("start", ability="Forecast")
def _forecast(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" in weather:
        new_type = "Fire"
    elif "hail" in weather:
        new_type = "Ice"
    elif any(tag in weather for tag in ("rain", "storm", "downpour")):
        new_type = "Water"
    elif "sand" in weather:
        new_type = "Rock"
    else:
        new_type = "Normal"
    current_types = list(pokemon.spec.types)
    if current_types != [new_type]:
        pokemon.spec.types = [new_type]
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Forecast",
                "phase": ctx.phase,
                "effect": "type_change",
                "from": current_types,
                "to": [new_type],
                "description": "Forecast changes type based on the weather.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("end", ability="Dry Skin")
def _dry_skin(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    weather = (battle.effective_weather() or "").strip().lower()
    if any(tag in weather for tag in ("rain", "storm", "downpour")):
        healed = pokemon._apply_tick_heal(1)
        if healed:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Dry Skin",
                    "phase": ctx.phase,
                    "effect": "heal",
                    "amount": healed,
                    "description": "Dry Skin restores HP in rainy weather.",
                    "target_hp": pokemon.hp,
                }
            )
    elif "sun" in weather:
        block_ability = pokemon.indirect_damage_block_ability()
        if block_ability:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": block_ability,
                    "phase": ctx.phase,
                    "effect": "weather_block",
                    "weather": battle.weather,
                    "description": f"{block_ability} prevents weather damage.",
                    "target_hp": pokemon.hp,
                }
            )
        else:
            damage = pokemon._apply_tick_damage(1)
            if damage:
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.actor_id,
                        "ability": "Dry Skin",
                        "phase": ctx.phase,
                        "effect": "sun_damage",
                        "amount": damage,
                        "description": "Dry Skin loses HP in sunny weather.",
                        "target_hp": pokemon.hp,
                    }
                )


@register_phase_hook("end", ability="Desert Weather")
def _desert_weather(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if weather and any(tag in weather for tag in ("rain", "storm", "downpour")):
        max_hp = pokemon.max_hp()
        heal_amount = max(1, int(math.floor(max_hp / 16))) if max_hp > 0 else 0
        if heal_amount:
            pokemon.heal(heal_amount)
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Desert Weather",
                    "phase": ctx.phase,
                    "effect": "heal",
                    "amount": heal_amount,
                    "description": "Desert Weather restores HP in rainy weather.",
                    "target_hp": pokemon.hp,
                }
            )


@register_phase_hook("end", ability="Desert Weather [Errata]")
def _desert_weather_errata(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if weather and any(tag in weather for tag in ("rain", "storm", "downpour")):
        gained = pokemon.add_temp_hp(pokemon.tick_value())
        if gained:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Desert Weather [Errata]",
                    "phase": ctx.phase,
                    "effect": "temp_hp",
                    "amount": gained,
                    "description": "Desert Weather [Errata] grants temporary HP in rain.",
                    "target_hp": pokemon.hp,
                }
            )


@register_phase_hook("end", ability="Hydration")
def _hydration(ctx: PhaseHookContext) -> None:
    if has_ability_exact(ctx.pokemon, "Hydration [Errata]"):
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if any(tag in weather for tag in ("rain", "storm", "downpour")):
        cured = ctx.battle._remove_statuses_by_set(ctx.pokemon, ctx.status_afflictions, limit=1)
        if cured:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Hydration",
                    "phase": ctx.phase,
                    "effect": "cure",
                    "statuses": cured,
                    "description": "Hydration cures a status affliction in the rain.",
                    "target_hp": ctx.pokemon.hp,
                }
            )


@register_phase_hook("end", ability="Shed Skin")
def _shed_skin(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if any(pokemon.has_status(name) for name in ctx.status_afflictions):
        roll = ctx.battle.rng.randint(1, 20)
        if roll >= 16:
            cured = ctx.battle._remove_statuses_by_set(
                pokemon, ctx.status_afflictions, limit=1
            )
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Shed Skin",
                    "phase": ctx.phase,
                    "effect": "cure",
                    "statuses": cured,
                    "roll": roll,
                    "result": "cure" if cured else "none",
                    "description": "Shed Skin cures a status at the end of the turn.",
                    "target_hp": pokemon.hp,
                }
            )


@register_phase_hook("end", ability="Delayed Reaction")
def _delayed_reaction(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    for entry in list(pokemon.get_temporary_effects("delayed_reaction")):
        trigger_round = entry.get("trigger_round")
        if trigger_round is not None and ctx.battle.round < int(trigger_round):
            continue
        try:
            amount = int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount > 0:
            block_ability = pokemon.indirect_damage_block_ability()
            if block_ability:
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.actor_id,
                        "ability": block_ability,
                        "phase": ctx.phase,
                        "effect": "status_block",
                        "description": f"{block_ability} prevents Delayed Reaction damage.",
                        "target_hp": pokemon.hp,
                    }
                )
            else:
                pokemon.apply_damage(amount)
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.actor_id,
                        "ability": "Delayed Reaction",
                        "phase": ctx.phase,
                        "effect": "delayed_damage",
                        "amount": amount,
                        "description": "Delayed Reaction applies stored damage.",
                        "target_hp": pokemon.hp,
                    }
                )
        pokemon.remove_temporary_effect("delayed_reaction")


@register_phase_hook("end", ability="Speed Boost")
def _speed_boost(ctx: PhaseHookContext) -> None:
    move_stub = MoveSpec(name="Speed Boost", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.actor_id,
        target_id=ctx.actor_id,
        move=move_stub,
        target=ctx.pokemon,
        stat="spd",
        delta=1,
        description="Speed Boost raises Speed at the end of the turn.",
        effect="speed_boost",
    )


@register_phase_hook("end", ability="Moody")
def _moody_end(ctx: PhaseHookContext) -> None:
    if has_errata(ctx.pokemon, "Moody"):
        return
    pokemon = ctx.pokemon
    battle = ctx.battle
    roll_up = battle.rng.randint(1, 10)
    roll_down = battle.rng.randint(1, 10)
    stat_map = {
        1: "atk",
        2: "atk",
        3: "def",
        4: "def",
        5: "spatk",
        6: "spatk",
        7: "spdef",
        8: "spdef",
        9: "spd",
        10: "spd",
    }
    up_stat = stat_map.get(roll_up, "atk")
    down_stat = stat_map.get(roll_down, "def")
    pokemon.temporary_effects = [
        entry for entry in pokemon.temporary_effects if entry.get("kind") != "moody_state"
    ]
    pokemon.add_temporary_effect(
        "moody_state",
        round=battle.round,
        up_roll=roll_up,
        up_stat=up_stat,
        up_delta=2,
        down_roll=roll_down,
        down_stat=down_stat,
        down_delta=-2,
        errata=False,
    )
    move_stub = MoveSpec(name="Moody", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.actor_id,
        target_id=ctx.actor_id,
        move=move_stub,
        target=pokemon,
        stat=up_stat,
        delta=2,
        description="Moody raises a random stat by +2 CS.",
        effect="moody_up",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.actor_id,
        target_id=ctx.actor_id,
        move=move_stub,
        target=pokemon,
        stat=down_stat,
        delta=-2,
        description="Moody lowers a random stat by -2 CS.",
        effect="moody_down",
    )


@register_phase_hook("end", ability="Moody [Errata]")
def _moody_errata_end(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    roll_up = battle.rng.randint(1, 6)
    roll_down = battle.rng.randint(1, 6)
    stat_map = {
        1: "atk",
        2: "def",
        3: "spatk",
        4: "spdef",
        5: "spd",
        6: "accuracy",
    }
    up_stat = stat_map.get(roll_up, "atk")
    down_stat = stat_map.get(roll_down, "def")
    pokemon.temporary_effects = [
        entry for entry in pokemon.temporary_effects if entry.get("kind") != "moody_state"
    ]
    pokemon.add_temporary_effect(
        "moody_state",
        round=battle.round,
        up_roll=roll_up,
        up_stat=up_stat,
        up_delta=2,
        down_roll=roll_down,
        down_stat=down_stat,
        down_delta=-1,
        errata=True,
    )
    move_stub = MoveSpec(name="Moody [Errata]", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.actor_id,
        target_id=ctx.actor_id,
        move=move_stub,
        target=pokemon,
        stat=up_stat,
        delta=2,
        description="Moody [Errata] raises a random stat by +2 CS.",
        effect="moody_errata_up",
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.actor_id,
        target_id=ctx.actor_id,
        move=move_stub,
        target=pokemon,
        stat=down_stat,
        delta=-1,
        description="Moody [Errata] lowers a random stat by -1 CS.",
        effect="moody_errata_down",
    )


@register_phase_hook("start", ability="Rain Dish")
def _rain_dish(ctx: PhaseHookContext) -> None:
    if has_errata(ctx.pokemon, "Rain Dish"):
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if any(tag in weather for tag in ("rain", "storm", "downpour")):
        healed = ctx.pokemon._apply_tick_heal(1)
        if healed:
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.actor_id,
                    "ability": "Rain Dish",
                    "phase": ctx.phase,
                    "effect": "heal",
                    "amount": healed,
                    "description": "Rain Dish restores HP in rainy weather.",
                    "target_hp": ctx.pokemon.hp,
                }
            )


@register_phase_hook("start", ability="Sun Blanket")
def _sun_blanket(ctx: PhaseHookContext) -> None:
    if has_errata(ctx.pokemon, "Sun Blanket"):
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" not in weather:
        return
    healed = ctx.pokemon._apply_tick_heal(1)
    if healed:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Sun Blanket",
                "phase": ctx.phase,
                "effect": "heal",
                "amount": healed,
                "description": "Sun Blanket restores HP in sunny weather.",
                "target_hp": ctx.pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Photosynthesis")
def _photosynthesis(ctx: PhaseHookContext) -> None:
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" not in weather:
        return
    healed = ctx.pokemon._apply_tick_heal(1)
    if healed:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Photosynthesis",
                "phase": ctx.phase,
                "effect": "heal",
                "amount": healed,
                "description": "Photosynthesis restores HP in sunny weather.",
                "target_hp": ctx.pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Poltergeist")
def _poltergeist_item_tick(ctx: PhaseHookContext) -> None:
    items = ctx.pokemon.spec.items if isinstance(ctx.pokemon.spec.items, list) else []
    if not items:
        return
    damage = ctx.pokemon._apply_tick_damage(1)
    if damage <= 0:
        return
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.actor_id,
            "status": "Poltergeist",
            "phase": ctx.phase,
            "effect": "tick",
            "amount": damage,
            "description": "Poltergeist damages targets still holding items.",
            "target_hp": ctx.pokemon.hp,
        }
    )
    ctx.battle.log_event(ctx.events[-1])


@register_phase_hook("start", ability="Soothing Tone")
def _soothing_tone_evasion(ctx: PhaseHookContext) -> None:
    if has_errata(ctx.pokemon, "Soothing Tone"):
        return
    ctx.pokemon.add_temporary_effect(
        "evasion_bonus",
        amount=2,
        scope="all",
        expires_round=ctx.battle.round + 1,
        source="Soothing Tone",
    )


def _weather_speed_stage(
    ctx: PhaseHookContext, *, ability: str, stat: str, delta: int, weather_tags: List[str]
) -> None:
    pokemon = ctx.pokemon
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    active = any(tag in weather for tag in weather_tags)
    entry = next(iter(pokemon.get_temporary_effects(f"{ability.lower()}_active")), None)
    move_stub = MoveSpec(name=ability, type="Normal", category="Status")
    if active and entry is None:
        before = pokemon.combat_stages.get(stat, 0)
        ctx.battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.actor_id,
            target_id=ctx.actor_id,
            move=move_stub,
            target=pokemon,
            stat=stat,
            delta=delta,
            description=f"{ability} raises {stat.upper()} during the weather.",
            effect=ability.lower(),
        )
        applied = pokemon.combat_stages.get(stat, 0) - before
        pokemon.add_temporary_effect(f"{ability.lower()}_active", delta=applied)
    elif not active and entry is not None:
        applied = int(entry.get("delta", 0) or 0)
        if applied:
            ctx.battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.actor_id,
                target_id=ctx.actor_id,
                move=move_stub,
                target=pokemon,
                stat=stat,
                delta=-applied,
                description=f"{ability} ends when the weather clears.",
                effect=f"{ability.lower()}_end",
            )
        pokemon.remove_temporary_effect(f"{ability.lower()}_active")


@register_phase_hook("start", ability="Sand Rush")
def _sand_rush(ctx: PhaseHookContext) -> None:
    _weather_speed_stage(ctx, ability="Sand Rush", stat="spd", delta=4, weather_tags=["sand"])


@register_phase_hook("start", ability="Sand Veil")
def _sand_veil(ctx: PhaseHookContext) -> None:
    if has_errata(ctx.pokemon, "Sand Veil"):
        return
    battle = ctx.battle
    weather = (battle.effective_weather() or "").strip().lower()
    if "sand" not in weather:
        return
    pokemon = ctx.pokemon
    pokemon.add_temporary_effect(
        "evasion_bonus",
        amount=2,
        scope="all",
        expires_round=battle.round,
        source="Sand Veil",
    )
    pokemon.add_temporary_effect(
        "weather_immunity",
        weather="sandstorm",
        expires_round=battle.round,
        source="Sand Veil",
    )
    if pokemon.position is None:
        return
    for pid, mon in battle.pokemon.items():
        if pid == ctx.actor_id or mon.position is None:
            continue
        if battle._team_for(pid) != battle._team_for(ctx.actor_id):
            continue
        if targeting.chebyshev_distance(pokemon.position, mon.position) <= 1:
            mon.add_temporary_effect(
                "weather_immunity",
                weather="sandstorm",
                expires_round=battle.round,
                source="Sand Veil",
            )


@register_phase_hook("start", ability="Sand Veil [Errata]")
def _sand_veil_errata(ctx: PhaseHookContext) -> None:
    battle = ctx.battle
    weather = (battle.effective_weather() or "").strip().lower()
    terrain_name = ""
    if isinstance(battle.terrain, dict):
        terrain_name = (battle.terrain.get("name") or "").strip().lower()
    sandy_terrain = "sandy" in terrain_name
    pokemon = ctx.pokemon

    pokemon.temporary_effects = [
        entry
        for entry in pokemon.temporary_effects
        if not (
            isinstance(entry, dict)
            and entry.get("kind") == "evasion_bonus"
            and entry.get("source") == "Sand Veil [Errata]"
        )
    ]
    if "sand" in weather or sandy_terrain:
        pokemon.add_temporary_effect(
            "evasion_bonus",
            amount=1,
            scope="all",
            expires_round=battle.round,
            source="Sand Veil [Errata]",
        )
    if "sand" not in weather:
        return
    pokemon.add_temporary_effect(
        "weather_immunity",
        weather="sandstorm",
        expires_round=battle.round,
        source="Sand Veil [Errata]",
    )
    if pokemon.position is None:
        return
    for pid, mon in battle.pokemon.items():
        if pid == ctx.actor_id or mon.position is None:
            continue
        if battle._team_for(pid) != battle._team_for(ctx.actor_id):
            continue
        if targeting.chebyshev_distance(pokemon.position, mon.position) <= 1:
            mon.add_temporary_effect(
                "weather_immunity",
                weather="sandstorm",
                expires_round=battle.round,
                source="Sand Veil [Errata]",
            )


@register_phase_hook("start", ability="Snow Cloak")
def _snow_cloak(ctx: PhaseHookContext) -> None:
    battle = ctx.battle
    weather = (battle.effective_weather() or "").strip().lower()
    if "hail" not in weather and "snow" not in weather:
        return
    pokemon = ctx.pokemon
    pokemon.add_temporary_effect(
        "evasion_bonus",
        amount=2,
        scope="all",
        expires_round=battle.round,
        source="Snow Cloak",
    )
    pokemon.add_temporary_effect(
        "weather_immunity",
        weather="hail",
        expires_round=battle.round,
        source="Snow Cloak",
    )
    if pokemon.position is None:
        return
    for pid, mon in battle.pokemon.items():
        if pid == ctx.actor_id or mon.position is None:
            continue
        if battle._team_for(pid) != battle._team_for(ctx.actor_id):
            continue
        if targeting.chebyshev_distance(pokemon.position, mon.position) <= 1:
            mon.add_temporary_effect(
                "weather_immunity",
                weather="hail",
                expires_round=battle.round,
                source="Snow Cloak",
            )


@register_phase_hook("start", ability="Sol Veil")
def _sol_veil(ctx: PhaseHookContext) -> None:
    battle = ctx.battle
    pokemon = ctx.pokemon
    weather = (battle.effective_weather() or "").strip().lower()
    terrain_name = str((battle.terrain or {}).get("name") or "").strip().lower()
    evasion = 2 if ("sun" in weather or terrain_name.startswith("grassy")) else 1
    pokemon.add_temporary_effect(
        "evasion_bonus",
        amount=evasion,
        scope="all",
        expires_round=battle.round,
        source="Sol Veil",
    )
    if "sun" in weather:
        pokemon.add_temporary_effect(
            "damage_reduction",
            amount=5,
            expires_round=battle.round,
            consume=False,
            source="Sol Veil",
        )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Sol Veil",
            "phase": ctx.phase,
            "effect": "evasion_bonus",
            "amount": evasion,
            "description": "Sol Veil boosts evasion; sunny weather grants DR.",
            "target_hp": pokemon.hp,
        }
    )


@register_phase_hook("start", ability="Solar Power")
def _solar_power(ctx: PhaseHookContext) -> None:
    battle = ctx.battle
    pokemon = ctx.pokemon
    if has_errata(pokemon, "Solar Power"):
        return
    weather = (battle.effective_weather() or "").strip().lower()
    sunny = "sun" in weather
    entry = next(iter(pokemon.get_temporary_effects("solar_power_active")), None)
    move_stub = MoveSpec(name="Solar Power", type="Fire", category="Status")
    if sunny and entry is None:
        before = pokemon.combat_stages.get("spatk", 0)
        battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.actor_id,
            target_id=ctx.actor_id,
            move=move_stub,
            target=pokemon,
            stat="spatk",
            delta=2,
            description="Solar Power raises Special Attack in sunshine.",
            effect="solar_power",
        )
        applied = pokemon.combat_stages.get("spatk", 0) - before
        pokemon.add_temporary_effect("solar_power_active", delta=applied)
    elif not sunny and entry is not None:
        applied = int(entry.get("delta", 0) or 0)
        if applied:
            battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.actor_id,
                target_id=ctx.actor_id,
                move=move_stub,
                target=pokemon,
                stat="spatk",
                delta=-applied,
                description="Solar Power ends when the sunlight fades.",
                effect="solar_power_end",
            )
        pokemon.remove_temporary_effect("solar_power_active")
    if sunny:
        max_hp = pokemon.max_hp()
        loss = max(1, int(math.floor(max_hp / 16))) if max_hp > 0 else 0
        if loss:
            block_ability = pokemon.indirect_damage_block_ability()
            if block_ability:
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.actor_id,
                        "ability": block_ability,
                        "phase": ctx.phase,
                        "effect": "status_block",
                        "description": f"{block_ability} prevents Solar Power damage.",
                        "target_hp": pokemon.hp,
                    }
                )
            else:
                pokemon.apply_damage(loss)
                ctx.events.append(
                    {
                        "type": "ability",
                        "actor": ctx.actor_id,
                        "ability": "Solar Power",
                        "phase": ctx.phase,
                        "effect": "sun_damage",
                        "amount": loss,
                        "description": "Solar Power drains HP in sunlight.",
                        "target_hp": pokemon.hp,
                    }
                )


@register_phase_hook("start", ability="Pride")
def _pride_phase(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    pride_statuses = {
        "burned",
        "poisoned",
        "badly poisoned",
        "paralyzed",
        "frozen",
        "freeze",
        "sleep",
        "asleep",
    }
    has_pride_status = any(pokemon.has_status(name) for name in pride_statuses)
    entry = next(iter(pokemon.get_temporary_effects("pride_active")), None)
    move_stub = MoveSpec(name="Pride", type="Normal", category="Status")
    if has_pride_status and entry is None:
        before = pokemon.combat_stages.get("spatk", 0)
        battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.actor_id,
            target_id=ctx.actor_id,
            move=move_stub,
            target=pokemon,
            stat="spatk",
            delta=2,
            description="Pride raises Special Attack while afflicted.",
            effect="pride",
        )
        applied = pokemon.combat_stages.get("spatk", 0) - before
        pokemon.add_temporary_effect("pride_active", delta=applied)
    elif not has_pride_status and entry is not None:
        applied = int(entry.get("delta", 0) or 0)
        if applied:
            battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.actor_id,
                target_id=ctx.actor_id,
                move=move_stub,
                target=pokemon,
                stat="spatk",
                delta=-applied,
                description="Pride ends when the affliction is gone.",
                effect="pride_end",
            )
        pokemon.remove_temporary_effect("pride_active")


@register_phase_hook("start", ability="Prime Fury")
def _prime_fury_start(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if has_errata(pokemon, "Prime Fury"):
        return
    if not pokemon.get_temporary_effects("prime_fury_ready"):
        return
    if pokemon.get_temporary_effects("prime_fury_used"):
        return
    if not pokemon.has_status("Enraged"):
        pokemon.statuses.append({"name": "Enraged", "remaining": 1})
    move_stub = MoveSpec(name="Prime Fury", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.actor_id,
        target_id=ctx.actor_id,
        move=move_stub,
        target=pokemon,
        stat="atk",
        delta=1,
        description="Prime Fury raises Attack.",
        effect="prime_fury",
    )
    pokemon.add_temporary_effect("prime_fury_used")


@register_phase_hook("start", ability="Empower")
def _empower_cleanup(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    current_round = ctx.battle.round
    for entry in list(pokemon.get_temporary_effects("action_override")):
        if entry.get("source") != "Empower":
            continue
        used_round = entry.get("round")
        if used_round is None:
            continue
        try:
            if int(used_round) < int(current_round):
                if entry in pokemon.temporary_effects:
                    pokemon.temporary_effects.remove(entry)
        except (TypeError, ValueError):
            if entry in pokemon.temporary_effects:
                pokemon.temporary_effects.remove(entry)


@register_phase_hook("start", ability="Root Down")
def _root_down(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if has_errata(pokemon, "Root Down"):
        return
    if not pokemon.has_status("Ingrain"):
        return
    for entry in list(pokemon.get_temporary_effects("root_down_used")):
        if entry.get("round") == ctx.battle.round:
            return
        pokemon.remove_temporary_effect("root_down_used")
    max_hp = pokemon.max_hp()
    temp_gain = max(1, int(math.floor(max_hp / 16))) if max_hp > 0 else 0
    if temp_gain <= 0:
        return
    pokemon.temp_hp = (pokemon.temp_hp or 0) + temp_gain
    pokemon.add_temporary_effect("root_down_used", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Root Down",
            "phase": ctx.phase,
            "effect": "temp_hp",
            "amount": temp_gain,
            "description": "Root Down grants temporary HP while rooted.",
            "target_hp": pokemon.hp,
        }
    )


@register_phase_hook("start", ability="Unnerve")
def _unnerve_aura(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    if has_errata(pokemon, "Unnerve"):
        return
    if pokemon.position is None:
        return
    for pid, mon in battle.pokemon.items():
        if not mon.active or mon.fainted or mon.position is None:
            continue
        if battle._team_for(pid) == battle._team_for(ctx.actor_id):
            continue
        if targeting.chebyshev_distance(pokemon.position, mon.position) > 3:
            continue
        mon.add_temporary_effect(
            "unnerved",
            source="Unnerve",
            ability="Unnerve",
            source_id=ctx.actor_id,
            expires_round=battle.round + 1,
        )
        mon.add_temporary_effect(
            "digestion_blocked",
            source="Unnerve",
            ability="Unnerve",
            source_id=ctx.actor_id,
            expires_round=battle.round + 1,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "target": pid,
                "ability": "Unnerve",
                "phase": ctx.phase,
                "effect": "suppression",
                "description": "Unnerve suppresses positive combat stages and digestion.",
                "target_hp": mon.hp,
            }
        )


@register_phase_hook("start", ability="Pressure")
def _pressure_aura(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    if pokemon.position is None:
        return
    for pid, mon in battle.pokemon.items():
        if not mon.active or mon.fainted or mon.position is None:
            continue
        if battle._team_for(pid) == battle._team_for(ctx.actor_id):
            continue
        if targeting.chebyshev_distance(pokemon.position, mon.position) > 3:
            continue
        pressure_move = MoveSpec(
            name="Pressure",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_value=0,
            target_kind="Self",
            target_range=0,
            freq="Static",
        )
        battle._apply_status(
            ctx.events,
            attacker_id=ctx.actor_id,
            target_id=pid,
            move=pressure_move,
            target=mon,
            status="Suppressed",
            effect="pressure",
            description="Pressure suppresses nearby foes.",
            remaining=1,
        )
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "target": pid,
                "ability": "Pressure",
                "phase": ctx.phase,
                "effect": "suppression",
                "description": "Pressure suppresses nearby foes.",
                "target_hp": mon.hp,
            }
        )


@register_phase_hook("start", ability="Symbiosis [Errata]")
def _symbiosis_errata_cleanup(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    for entry in list(pokemon.get_temporary_effects("symbiosis_shared")):
        expires_round = entry.get("expires_round")
        if expires_round is None or battle.round <= int(expires_round):
            continue
        target_id = entry.get("target")
        item_name = str(entry.get("item") or "").strip().lower()
        if target_id:
            target = battle.pokemon.get(target_id)
            if target is not None and isinstance(target.spec.items, list):
                filtered = []
                for item in target.spec.items:
                    if isinstance(item, dict):
                        name = str(item.get("name") or "").strip().lower()
                        if item.get("shared") and item.get("source") == "Symbiosis [Errata]":
                            if item_name and name == item_name:
                                continue
                    filtered.append(item)
                target.spec.items = filtered
                target._sync_source_items()
        pokemon.remove_temporary_effect("symbiosis_shared")

@register_phase_hook("start", ability="Slow Start")
def _slow_start(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    joined = None
    for entry in pokemon.get_temporary_effects("joined_round"):
        joined = entry.get("round")
        break
    if joined is None:
        return
    rounds_active = battle.round - int(joined)
    active = rounds_active <= 2
    if active and not pokemon.get_temporary_effects("slow_start_active"):
        pokemon.add_temporary_effect("stat_scalar", stat="atk", multiplier=0.5, source="Slow Start")
        pokemon.add_temporary_effect("stat_scalar", stat="spd", multiplier=0.5, source="Slow Start")
        pokemon.add_temporary_effect("damage_reduction", amount=10, source="Slow Start")
        pokemon.add_temporary_effect("slow_start_active", until_round=battle.round + 2)
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Slow Start",
                "phase": ctx.phase,
                "effect": "slow_start",
                "description": "Slow Start halves Attack/Speed and adds damage reduction.",
                "target_hp": pokemon.hp,
            }
        )
    if not active and pokemon.get_temporary_effects("slow_start_active"):
        pokemon.temporary_effects = [
            entry
            for entry in pokemon.temporary_effects
            if not (
                entry.get("kind") in {"stat_scalar", "damage_reduction"}
                and entry.get("source") == "Slow Start"
            )
            and entry.get("kind") != "slow_start_active"
        ]
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Slow Start",
                "phase": ctx.phase,
                "effect": "slow_start_end",
                "description": "Slow Start ends after a few rounds.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Shadow Tag")
def _shadow_tag(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    if pokemon.position is None:
        return
    for pid, mon in battle.pokemon.items():
        if pid == ctx.actor_id or mon.fainted or not mon.active:
            continue
        if battle._team_for(pid) == battle._team_for(ctx.actor_id):
            continue
        if mon.position is None:
            continue
        if targeting.chebyshev_distance(pokemon.position, mon.position) > 5:
            continue
        battle._apply_status(
            ctx.events,
            attacker_id=ctx.actor_id,
            target_id=pid,
            move=MoveSpec(name="Shadow Tag", type="Ghost", category="Status"),
            target=mon,
            status="Slowed",
            effect="shadow_tag",
            description="Shadow Tag slows the target.",
            remaining=5,
        )
        battle._apply_status(
            ctx.events,
            attacker_id=ctx.actor_id,
            target_id=pid,
            move=MoveSpec(name="Shadow Tag", type="Ghost", category="Status"),
            target=mon,
            status="Trapped",
            effect="shadow_tag",
            description="Shadow Tag traps the target.",
            remaining=5,
        )
        mon.add_temporary_effect(
            "shadow_tag_anchor",
            anchor=pokemon.position,
            expires_round=battle.round + 5,
        )


@register_phase_hook("start", ability="Multitype")
def _multitype(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    item_type = None
    if pokemon.equipped_weapon():
        item_type = battle._item_type_from_item(pokemon.equipped_weapon())
    if item_type is None:
        for entry in pokemon.spec.items:
            item_type = battle._item_type_from_item(entry)
            if item_type:
                break
    if not item_type:
        return
    if pokemon.spec.types != [item_type]:
        old_types = list(pokemon.spec.types)
        pokemon.spec.types = [item_type]
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Multitype",
                "phase": ctx.phase,
                "effect": "type_change",
                "from": old_types,
                "to": [item_type],
                "description": "Multitype changes the user's type based on its held item.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Quick Cloak")
def _quick_cloak(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    species = (pokemon.spec.species or "").strip().lower()
    if species != "burmy":
        return
    if pokemon.get_temporary_effects("quick_cloak"):
        return
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if "sand" in weather:
        cloak_type = "Ground"
    elif "hail" in weather or "snow" in weather:
        cloak_type = "Steel"
    else:
        cloak_type = "Grass"
    if cloak_type not in pokemon.spec.types:
        pokemon.spec.types.append(cloak_type)
    pokemon.add_temporary_effect("quick_cloak", type=cloak_type)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Quick Cloak",
            "phase": ctx.phase,
            "effect": "cloak",
            "cloak_type": cloak_type,
            "description": "Quick Cloak adapts Burmy's cloak.",
            "target_hp": pokemon.hp,
        }
    )


def _unburden_phase(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    has_item = pokemon.is_holding_item()
    entry = next(iter(pokemon.get_temporary_effects("unburden_active")), None)
    move_stub = MoveSpec(name="Unburden", type="Normal", category="Status")
    if not has_item and entry is None:
        before = pokemon.combat_stages.get("spd", 0)
        battle._apply_combat_stage(
            ctx.events,
            attacker_id=ctx.actor_id,
            target_id=ctx.actor_id,
            move=move_stub,
            target=pokemon,
            stat="spd",
            delta=2,
            description="Unburden raises Speed while unencumbered.",
            effect="unburden",
        )
        applied = pokemon.combat_stages.get("spd", 0) - before
        pokemon.add_temporary_effect("unburden_active", delta=applied)
    elif has_item and entry is not None:
        applied = int(entry.get("delta", 0) or 0)
        if applied:
            battle._apply_combat_stage(
                ctx.events,
                attacker_id=ctx.actor_id,
                target_id=ctx.actor_id,
                move=move_stub,
                target=pokemon,
                stat="spd",
                delta=-applied,
                description="Unburden ends once the user holds an item.",
                effect="unburden_end",
            )
        pokemon.remove_temporary_effect("unburden_active")


@register_phase_hook("start", ability="Unburden")
def _unburden_start(ctx: PhaseHookContext) -> None:
    _unburden_phase(ctx)


@register_phase_hook("end", ability="Unburden")
def _unburden_end(ctx: PhaseHookContext) -> None:
    _unburden_phase(ctx)


@register_phase_hook("start", ability="Steam Engine")
def _steam_engine_rain(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    battle = ctx.battle
    weather = (battle.effective_weather() or "").strip().lower()
    if "rain" not in weather and "storm" not in weather and "downpour" not in weather:
        return
    entry = next(iter(pokemon.get_temporary_effects("steam_engine_used")), None)
    count = int(entry.get("count", 0) or 0) if entry else 0
    if count >= 2:
        return
    if entry is None:
        pokemon.add_temporary_effect("steam_engine_used", count=1)
    else:
        entry["count"] = count + 1
    pokemon.add_temporary_effect(
        "evasion_bonus",
        amount=3,
        scope="all",
        expires_round=battle.round + 3,
        source="Steam Engine",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Steam Engine",
            "phase": ctx.phase,
            "effect": "smokescreen",
            "description": "Steam Engine triggers Smokescreen in rain.",
            "target_hp": pokemon.hp,
        }
    )


@register_phase_hook("start", ability="Shields Down")
def _shields_down(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    if pokemon.hp is None:
        return
    max_hp = pokemon.max_hp()
    entry = next(iter(pokemon.get_temporary_effects("shields_down_form")), None)
    form = str(entry.get("form") or "meteor").lower() if entry else "meteor"
    if max_hp > 0 and pokemon.hp * 2 <= max_hp and form != "core":
        ctx.battle._set_shields_down_form(ctx.actor_id, pokemon, form="core", source="Shields Down")
        if entry is None:
            pokemon.add_temporary_effect("shields_down_form", form="core")
        else:
            entry["form"] = "core"
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Shields Down",
                "phase": ctx.phase,
                "effect": "form",
                "form": "core",
                "description": "Shields Down shifts to Core Forme.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Schooling")
def _schooling_form(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    entry = next(iter(pokemon.get_temporary_effects("schooling_active")), None)
    if entry is None:
        return
    max_hp = pokemon.max_hp()
    if max_hp <= 0 or pokemon.hp is None:
        return
    if pokemon.hp * 2 > max_hp:
        return
    if pokemon.temp_hp > 0:
        return
    pokemon.remove_temporary_effect("schooling_active")
    ctx.battle._set_schooling_form(ctx.actor_id, pokemon, form="solo", source="Schooling")
    for effect in list(pokemon.get_temporary_effects("temp_hp_locked")):
        if effect.get("source") == "Schooling" and effect in pokemon.temporary_effects:
            pokemon.temporary_effects.remove(effect)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Schooling",
            "phase": ctx.phase,
            "effect": "form",
            "form": "solo",
            "description": "Schooling returns to Solo Forme.",
            "target_hp": pokemon.hp,
        }
    )
    if pokemon.has_ability("Horde Break"):
        if pokemon.statuses:
            pokemon.statuses = []
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.actor_id,
                "ability": "Horde Break",
                "phase": ctx.phase,
                "effect": "cure",
                "description": "Horde Break cures all status conditions.",
                "target_hp": pokemon.hp,
            }
        )


@register_phase_hook("start", ability="Steam Engine")
def _steam_engine_rain(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    if not weather or "rain" not in weather:
        return
    entry = next(iter(pokemon.get_temporary_effects("steam_engine_used")), None)
    count = int(entry.get("count", 0) or 0) if entry else 0
    if count >= 2:
        return
    if entry is None:
        pokemon.add_temporary_effect("steam_engine_used", count=1)
    else:
        entry["count"] = count + 1
    pokemon.add_temporary_effect(
        "evasion_bonus",
        amount=3,
        scope="all",
        expires_round=ctx.battle.round + 3,
        source="Steam Engine",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Steam Engine",
            "phase": ctx.phase,
            "effect": "smokescreen",
            "description": "Steam Engine triggers in the rain.",
            "target_hp": pokemon.hp,
        }
    )

@register_phase_hook("start", ability="Queenly Majesty")
def _queenly_majesty_interrupt_block(ctx: PhaseHookContext) -> None:
    pokemon = ctx.pokemon
    pokemon.add_temporary_effect("no_interrupts", expires_round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.actor_id,
            "ability": "Queenly Majesty",
            "phase": ctx.phase,
            "effect": "interrupt_block",
            "description": "Queenly Majesty prevents interrupt responses.",
            "target_hp": pokemon.hp,
        }
    )


@register_phase_hook("start", ability="Parental Bond")
def _parental_bond_start(ctx: PhaseHookContext) -> None:
    battle = ctx.battle
    mother_id = ctx.actor_id
    baby_id, created = ensure_parental_bond_baby(battle, mother_id)
    if not baby_id:
        return
    baby = battle.pokemon.get(baby_id)
    if baby is None:
        return
    if not any(
        entry.get("source") == "Parental Bond"
        for entry in baby.get_temporary_effects("damage_reduction")
    ):
        baby.add_temporary_effect("damage_reduction", amount=10, consume=False, source="Parental Bond")
    reset_parental_bond_turn(battle, mother_id)
    if created:
        ctx.events.append(
            {
                "type": "ability",
                "actor": mother_id,
                "ability": "Parental Bond",
                "phase": ctx.phase,
                "effect": "baby_join",
                "baby_id": baby_id,
                "description": "Parental Bond sends the baby into battle.",
                "target_hp": ctx.pokemon.hp,
            }
        )
    if apply_parental_bond_enrage(battle, mother_id, baby_id):
        ctx.events.append(
            {
                "type": "ability",
                "actor": mother_id,
                "ability": "Parental Bond",
                "phase": ctx.phase,
                "effect": "enraged",
                "description": "Parental Bond enrages the mother after the baby faints.",
                "target_hp": ctx.pokemon.hp,
            }
        )
