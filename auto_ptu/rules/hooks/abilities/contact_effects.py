"""Contact ability effects moved into the ability hook registry."""

from __future__ import annotations

from typing import Dict, List

from ...move_traits import move_has_contact_trait
from ..ability_hooks import AbilityHookContext, register_ability_hook

CONTACT_STATUS_EFFECTS: Dict[str, dict] = {
    "flame body": {"statuses": ["Burned"], "chance": 30, "effect": "burn"},
    "static": {"statuses": ["Paralyzed"], "chance": 30, "effect": "paralyze"},
    "poison point": {"statuses": ["Poisoned"], "chance": 30, "effect": "poison"},
}
CONTACT_DAMAGE_ABILITIES: Dict[str, float] = {"rough skin": 0.125}


@register_ability_hook(phase="post_contact")
def _contact_ability_effects(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.attacker is None:
        return
    move = ctx.effective_move
    if not move_has_contact_trait(move):
        return
    battle = ctx.battle
    attacker = ctx.attacker
    defender = ctx.defender
    events = ctx.events
    block_entry = next(iter(attacker.get_temporary_effects("contact_ability_block")), None)
    if block_entry:
        events.append(
            {
                "type": "item",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "item": str(block_entry.get("source") or "Protective Pads"),
                "effect": "contact_ability_block",
                "description": "Protective Pads blocks contact-triggered effects.",
                "target_hp": attacker.hp,
            }
        )
        return
    for ability in defender.ability_names():
        key = ability.lower()
        status_info = CONTACT_STATUS_EFFECTS.get(key)
        if status_info:
            roll = battle.rng.randint(1, 100)
            if roll <= status_info["chance"]:
                statuses = status_info["statuses"]
                status_choice = (
                    battle.rng.choice(statuses) if isinstance(statuses, list) else statuses
                )
                if battle._terrain_blocks_status(attacker, status_choice):
                    events.append(
                        {
                            "type": "terrain",
                            "actor": ctx.defender_id,
                            "target": ctx.attacker_id,
                            "ability": ability,
                            "move": move.name,
                            "effect": "misty_terrain_block",
                            "status": status_choice,
                            "description": "Misty Terrain prevents status conditions for grounded targets.",
                            "target_hp": attacker.hp,
                        }
                    )
                    continue
                if not attacker.has_status(status_choice):
                    attacker.statuses.append({"name": status_choice})
                    events.append(
                        {
                            "type": "ability",
                            "actor": ctx.defender_id,
                            "target": ctx.attacker_id,
                            "ability": ability,
                            "move": move.name,
                            "effect": "status",
                            "status": status_choice,
                            "roll": roll,
                            "target_hp": attacker.hp,
                        }
                    )
        damage_fraction = CONTACT_DAMAGE_ABILITIES.get(key)
        if damage_fraction:
            block_ability = attacker.indirect_damage_block_ability()
            if block_ability:
                events.append(
                    {
                        "type": "ability",
                        "actor": ctx.attacker_id,
                        "target": ctx.defender_id,
                        "ability": block_ability,
                        "move": move.name,
                        "effect": "contact_block",
                        "description": f"{block_ability} prevents contact recoil damage.",
                        "target_hp": attacker.hp,
                    }
                )
            else:
                damage_amount = battle._apply_contact_damage(attacker, damage_fraction)
                if damage_amount > 0:
                    events.append(
                        {
                            "type": "ability",
                            "actor": ctx.defender_id,
                            "target": ctx.attacker_id,
                            "ability": ability,
                            "move": move.name,
                            "effect": "contact_damage",
                            "amount": damage_amount,
                            "target_hp": attacker.hp,
                        }
                    )
        if key == "iron barbs":
            block_ability = attacker.indirect_damage_block_ability()
            if block_ability:
                events.append(
                    {
                        "type": "ability",
                        "actor": ctx.attacker_id,
                        "target": ctx.defender_id,
                        "ability": block_ability,
                        "move": move.name,
                        "effect": "contact_block",
                        "description": f"{block_ability} prevents contact recoil damage.",
                        "target_hp": attacker.hp,
                    }
                )
            else:
                damage_amount = attacker._apply_tick_damage(1)
                if damage_amount > 0:
                    events.append(
                        {
                            "type": "ability",
                            "actor": ctx.defender_id,
                            "target": ctx.attacker_id,
                            "ability": ability,
                            "move": move.name,
                            "effect": "contact_damage",
                            "amount": damage_amount,
                            "description": "Iron Barbs punishes contact with a tick of damage.",
                            "target_hp": attacker.hp,
                        }
                    )
        if key == "effect spore":
            if defender.get_temporary_effects("effect_spore_used"):
                continue
            roll = battle.rng.randint(1, 6)
            if roll <= 2:
                status_choice = "Poisoned"
            elif roll <= 4:
                status_choice = "Paralyzed"
            else:
                status_choice = "Sleep"
            battle._apply_status(
                events,
                attacker_id=ctx.defender_id,
                target_id=ctx.attacker_id,
                move=move,
                target=attacker,
                status=status_choice,
                effect="effect_spore",
                description="Effect Spore releases a status spore cloud.",
            )
            defender.add_temporary_effect("effect_spore_used", expires_round=battle.round + 999)
            events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": ability,
                    "move": move.name,
                    "effect": "spore",
                    "roll": roll,
                    "status": status_choice,
                    "description": "Effect Spore afflicts the attacker.",
                    "target_hp": attacker.hp,
                }
            )
        if key == "cute charm":
            if not defender.get_temporary_effects("cute_charm_used"):
                attacker_gender = attacker.gender()
                defender_gender = defender.gender()
                if (
                    attacker_gender in {"male", "female"}
                    and defender_gender in {"male", "female"}
                    and attacker_gender != defender_gender
                ):
                    battle._apply_status(
                        events,
                        attacker_id=ctx.defender_id,
                        target_id=ctx.attacker_id,
                        move=move,
                        target=attacker,
                        status="Infatuated",
                        effect="cute_charm",
                        description="Cute Charm infatuates opposite-gender attackers.",
                    )
                    defender.add_temporary_effect("cute_charm_used")
                    events.append(
                        {
                            "type": "ability",
                            "actor": ctx.defender_id,
                            "target": ctx.attacker_id,
                            "ability": ability,
                            "move": move.name,
                            "effect": "infatuate",
                            "description": "Cute Charm infatuates the attacker.",
                            "target_hp": attacker.hp,
                        }
                    )
        if key == "mummy":
            if battle._blocks_ability_replace(attacker):
                events.append(
                    {
                        "type": "ability",
                        "actor": ctx.attacker_id,
                        "target": ctx.defender_id,
                        "ability": "Ability Shield",
                        "move": move.name,
                        "effect": "block_ability_replace",
                        "description": "Ability Shield prevents ability replacement.",
                        "target_hp": attacker.hp,
                    }
                )
            else:
                while attacker.remove_temporary_effect("entrained_ability"):
                    continue
                attacker.add_temporary_effect("entrained_ability", ability="Mummy", source="mummy")
                events.append(
                    {
                        "type": "ability",
                        "actor": ctx.defender_id,
                        "target": ctx.attacker_id,
                        "ability": "Mummy",
                        "move": move.name,
                        "effect": "ability_replace",
                        "description": "Mummy replaces the attacker's abilities.",
                        "target_hp": attacker.hp,
                    }
                )
        if key == "cute tears":
            if not defender.get_temporary_effects("cute_tears_used"):
                category = (move.category or "").strip().lower()
                stat = None
                if category == "physical":
                    stat = "atk"
                elif category == "special":
                    stat = "spatk"
                if stat:
                    battle._apply_combat_stage(
                        events,
                        attacker_id=ctx.defender_id,
                        target_id=ctx.attacker_id,
                        move=move,
                        target=attacker,
                        stat=stat,
                        delta=-2,
                        effect="cute_tears",
                        description="Cute Tears lowers the attacker's combat stage by -2.",
                    )
                    defender.add_temporary_effect("cute_tears_used")
                    events.append(
                        {
                            "type": "ability",
                            "actor": ctx.defender_id,
                            "target": ctx.attacker_id,
                            "ability": ability,
                            "move": move.name,
                            "effect": "stage_drop",
                            "stat": stat,
                            "amount": -2,
                            "description": "Cute Tears lowers the attacker's combat stage.",
                            "target_hp": attacker.hp,
                        }
                    )
        if key == "danger syrup":
            if not defender.get_temporary_effects("danger_syrup_used"):
                attacker.add_temporary_effect(
                    "evasion_bonus",
                    amount=-2,
                    scope="all",
                    expires_round=battle.round,
                    source="Danger Syrup",
                )
                defender.add_temporary_effect("danger_syrup_used")
                events.append(
                    {
                        "type": "ability",
                        "actor": ctx.defender_id,
                        "target": ctx.attacker_id,
                        "ability": ability,
                        "move": move.name,
                        "effect": "sweet_scent",
                        "amount": -2,
                        "description": "Danger Syrup lowers the attacker's evasion.",
                        "target_hp": attacker.hp,
                    }
                )
        if key == "magma armor":
            attacker_types = {t.lower().strip() for t in attacker.spec.types}
            if "fire" not in attacker_types:
                tick = attacker._apply_tick_damage(1)
                if tick > 0:
                    events.append(
                        {
                            "type": "ability",
                            "actor": ctx.defender_id,
                            "target": ctx.attacker_id,
                            "ability": ability,
                            "move": move.name,
                            "effect": "contact_tick",
                            "amount": tick,
                            "description": "Magma Armor deals a tick of damage on contact.",
                            "target_hp": attacker.hp,
                        }
                    )
        if key == "gooey":
            battle._apply_combat_stage(
                events,
                attacker_id=ctx.defender_id,
                target_id=ctx.attacker_id,
                move=move,
                target=attacker,
                stat="spd",
                delta=-1,
                effect="gooey",
                description="Gooey lowers the attacker's Speed by -1 CS.",
            )
        if key == "cursed body":
            if not attacker.has_status("Disabled"):
                attacker.statuses.append({"name": "Disabled", "move": move.name, "remaining": 3})
                events.append(
                    {
                        "type": "ability",
                        "actor": ctx.defender_id,
                        "target": ctx.attacker_id,
                        "ability": ability,
                        "move": move.name,
                        "effect": "disable",
                        "status": "Disabled",
                        "description": "Cursed Body disables the last move used.",
                        "target_hp": attacker.hp,
                    }
                )


@register_ability_hook(phase="post_contact", ability="Poison Touch", holder="defender")
def _poison_touch(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.attacker is None:
        return
    move = ctx.effective_move
    if not move_has_contact_trait(move):
        return
    battle = ctx.battle
    attacker = ctx.attacker
    roll = battle.rng.randint(1, 100)
    if roll > 30:
        return
    status_choice = "Poisoned"
    if battle._terrain_blocks_status(attacker, status_choice):
        ctx.events.append(
            {
                "type": "terrain",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Poison Touch",
                "move": move.name,
                "effect": "misty_terrain_block",
                "status": status_choice,
                "description": "Misty Terrain prevents status conditions for grounded targets.",
                "target_hp": attacker.hp,
            }
        )
        return
    if attacker.has_status(status_choice):
        return
    attacker.statuses.append({"name": status_choice})
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Poison Touch",
            "move": move.name,
            "effect": "status",
            "status": status_choice,
            "roll": roll,
            "target_hp": attacker.hp,
        }
    )
