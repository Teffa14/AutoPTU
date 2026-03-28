"""Last chance damage bonuses."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook


def _apply_bonus(
    ctx: AbilityHookContext,
    *,
    ability: str,
    bonus_key: str,
    description: str,
) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + 5
    ctx.result[bonus_key] = 5
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": ability,
            "move": ctx.move.name,
            "effect": "damage_bonus",
            "amount": 5,
            "description": description,
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result_last_chance", ability=None)
def _last_chance_bonuses(ctx: AbilityHookContext) -> None:
    attacker = ctx.attacker
    if attacker is None or ctx.result is None:
        return
    if attacker.hp is None or attacker.max_hp() <= 0:
        return
    if attacker.hp > max(1, attacker.max_hp() // 3):
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type == "fire" and attacker.has_ability("Blaze"):
        _apply_bonus(
            ctx,
            ability="Blaze",
            bonus_key="blaze_bonus",
            description="Blaze powers up Fire-type moves at low HP.",
        )
    if move_type == "dark" and attacker.has_ability("Dark Art"):
        _apply_bonus(
            ctx,
            ability="Dark Art",
            bonus_key="dark_art_bonus",
            description="Dark Art powers up Dark-type moves at low HP.",
        )
    if move_type == "normal" and attacker.has_ability("Last Chance"):
        _apply_bonus(
            ctx,
            ability="Last Chance",
            bonus_key="last_chance_bonus",
            description="Last Chance powers up Normal-type moves at low HP.",
        )
    if move_type == "grass" and attacker.has_ability("Overgrow"):
        _apply_bonus(
            ctx,
            ability="Overgrow",
            bonus_key="overgrow_bonus",
            description="Overgrow powers up Grass-type moves at low HP.",
        )
    if move_type == "water" and attacker.has_ability("Torrent"):
        _apply_bonus(
            ctx,
            ability="Torrent",
            bonus_key="torrent_bonus",
            description="Torrent powers up Water-type moves at low HP.",
        )
    if move_type == "bug" and attacker.has_ability("Swarm"):
        _apply_bonus(
            ctx,
            ability="Swarm",
            bonus_key="swarm_bonus",
            description="Swarm powers up Bug-type moves at low HP.",
        )
    if move_type == "fighting" and attacker.has_ability("Focus"):
        _apply_bonus(
            ctx,
            ability="Focus",
            bonus_key="focus_bonus",
            description="Focus powers up Fighting-type moves at low HP.",
        )
    if move_type == "ice" and attacker.has_ability("Freezing Point"):
        _apply_bonus(
            ctx,
            ability="Freezing Point",
            bonus_key="freezing_point_bonus",
            description="Freezing Point powers up Ice-type moves at low HP.",
        )
    if move_type == "ghost" and attacker.has_ability("Haunt"):
        _apply_bonus(
            ctx,
            ability="Haunt",
            bonus_key="haunt_bonus",
            description="Haunt powers up Ghost-type moves at low HP.",
        )
    if move_type == "psychic" and attacker.has_ability("Mind Mold"):
        _apply_bonus(
            ctx,
            ability="Mind Mold",
            bonus_key="mind_mold_bonus",
            description="Mind Mold powers up Psychic-type moves at low HP.",
        )
    if move_type == "ground" and attacker.has_ability("Landslide"):
        _apply_bonus(
            ctx,
            ability="Landslide",
            bonus_key="landslide_bonus",
            description="Landslide powers up Ground-type moves at low HP.",
        )
    if move_type == "rock" and attacker.has_ability("Mountain Peak"):
        _apply_bonus(
            ctx,
            ability="Mountain Peak",
            bonus_key="mountain_peak_bonus",
            description="Mountain Peak powers up Rock-type moves at low HP.",
        )
    if move_type == "electric" and attacker.has_ability("Overcharge"):
        _apply_bonus(
            ctx,
            ability="Overcharge",
            bonus_key="overcharge_bonus",
            description="Overcharge powers up Electric-type moves at low HP.",
        )
    if move_type == "poison" and attacker.has_ability("Venom"):
        _apply_bonus(
            ctx,
            ability="Venom",
            bonus_key="venom_bonus",
            description="Venom powers up Poison-type moves at low HP.",
        )
    if move_type == "dragon" and attacker.has_ability("Pure Blooded"):
        _apply_bonus(
            ctx,
            ability="Pure Blooded",
            bonus_key="pure_blooded_bonus",
            description="Pure Blooded powers up Dragon-type moves at low HP.",
        )
    if move_type == "flying" and attacker.has_ability("Mach Speed"):
        _apply_bonus(
            ctx,
            ability="Mach Speed",
            bonus_key="mach_speed_bonus",
            description="Mach Speed powers up Flying-type moves at low HP.",
        )
    if move_type == "fairy" and attacker.has_ability("Miracle Mile"):
        _apply_bonus(
            ctx,
            ability="Miracle Mile",
            bonus_key="miracle_mile_bonus",
            description="Miracle Mile powers up Fairy-type moves at low HP.",
        )
    if move_type == "steel" and attacker.has_ability("Unbreakable"):
        _apply_bonus(
            ctx,
            ability="Unbreakable",
            bonus_key="unbreakable_bonus",
            description="Unbreakable powers up Steel-type moves at low HP.",
        )
