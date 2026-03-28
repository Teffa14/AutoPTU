# Autonomous Battle Engine Alignment Plan

The Foundry PTR2e system you imported already encodes a production-ready math stack for PTU attacks, traits, statuses, and action sequencing. This document rewrites our original design so Auto PTU deliberately mirrors that logic path while remaining a self-contained, automation-first Python engine. Nothing here copies TypeScript; it translates the intent and the ordering of operations into our own architecture so contributors can reason about equivalence at every step.

## 1. Guiding Principles

1. **Logic parity, not code parity** - We read the Foundry sources (most notably `src/module/system/statistics/attack.ts`, the active effect pipelines, and trait modifiers) to understand the order in which accuracy, modifiers, crit gates, STAB, and keywords are resolved. We then apply the *same sequence* inside our Python modules without reusing their implementation.
2. **Autonomous-first UX** - Auto PTU is not a VTT module. Every subsystem must be invocable via CLI, scenario tests, and headless scripts. Whenever the Foundry flow expects UI interactivity (modifier popups, Tag prompts, etc.), we replace it with deterministic data-driven configuration.
3. **Declarative modifiers** - Inspired by Foundry's deferred resolver pattern, we expose structured "domains", "roll options", and "modifiers" for every action. This makes it trivial to bolt on abilities, features, and ad-hoc buffs without hardcoding.
4. **Scenario-driven safety net** - Each mechanic we port receives at least one deterministic scenario in `tests/test_battle_state.py`. We mirror the same cases Foundry covers (STAB boosts, priority resolution, trait-provided modifiers, etc.) so regressions are obvious.

## 2. Reference Flow from Foundry

The following table summarizes the key stages we mirror:

| Stage | Foundry Source | Auto PTU Translation |
| --- | --- | --- |
| Attack statistic initialization | `AttackStatistic` constructor - builds domains, attaches base "power" modifier, injects trait-based modifiers | `auto_ptu.rules.calculations.build_attack_context` - composes an `AttackContext` with `domains`, `roll_options`, and normalized modifiers drawn from MoveSpec keywords/capabilities |
| Roll option aggregation | `Statistic.getRollOptions`, actor/item roll options, ammo metadata | `AttackContext.roll_options()` - merges actor traits, held items, status flags, and field state into normalized strings (e.g., `stab-electric`, `weather-rain`) |
| Accuracy check | `AttackCheck` - handles omittable crit/accuracy rolls, trait-provided domains | `attack_hits` - enriched to accept contextual roll options (paralysis, smokescreen, etc.) plus de-dupable modifiers |
| Damage preparation | `power` modifier base + `Trait.effectsFromChanges` + ability hooks + STAB multipliers | `resolve_move_action` - now calls `compute_damage_packet`, which accumulates: base DB, power adjustments, STAB boosters, weather adjustments, keyword-based tweaks, defender-based resistances |
| Result shaping | `AttackRollResult` - carries separate entries for accuracy, crit, damage, additional triggers | Auto PTU log payloads continue to emit "move" events, but now also include `domains`, `modifier_breakdown`, and `keywords_applied` for auditing |

### Trait translations landed

- **Set-Up / Resolution queueing** - `BattleState.move_requires_setup` looks for "Set-Up" strings in the Foundry range/effect fields and queues the move payload on the attacker, forcing a later Standard action to fire the stored resolution just like PTR2e.
- **X-Strike multi-hit math** - Double/Five Strike moves read the Foundry trait tokens (`1 + d(X-1)` hits) via `rules.move_traits.strike_count`. `BattleState.resolve_move_targets` rolls the extra die, multiplies the per-hit damage, and logs `strike_hits/strike_damage_per_hit` so clustered attacks narrate their burst the same way Foundry chat cards do.
- **Recoil fractions** - Moves whose range text includes `Recoil 1/8` through `Recoil 1` now deduct the matching fraction (ceil'd, per target) from the attacker, log a `recoil` payload, and respect stacking from multi-target attacks exactly as the trait describes.
- **Smite chip damage** - Range strings that include `Smite` (Core 1.05, p.341) now trigger a forced-hit damage roll on a miss, drop the type chart one resistance stage, apply chip damage without secondary effects, and log a `smite` payload for parity with the Foundry trait.
- **Dragon Energy scaling** - `build_attack_context` now applies a `-1` Damage Base penalty for every 10% of the user's missing HP whenever the move is Dragon Energy, keeping the damage roll in sync with the PTU description (`tests/test_battle_state.py::test_dragon_energy_scales_db_with_missing_hp`).
- **Dragon move effects** - `_handle_move_special_effects` now mirrors Dragon Breath's 15+ Paralysis roll, Dragon Dance's Attack/Speed boosts, and Dragon Ascent's Defense/Special Defense drop, logging each combat-stage/status change so the CLI reflects the Foundry descriptions (`tests/test_battle_state.py::test_dragon_breath_paralyzes_on_high_roll`, `tests/test_battle_state.py::test_dragon_dance_increases_attack_and_speed`, `tests/test_battle_state.py::test_dragon_ascent_lowers_defenses`).
- **False Swipe & Fire Fang** - The new helper also enforces False Swipe's "leave the foe at 1 HP" rule and reproduces Fire Fang's 18-19 coin flip plus 20 both Burn/Flinch outcome, ensuring each effect logs through the same pipeline once the move hits (`tests/test_battle_state.py::test_false_swipe_leaves_target_at_one_hp`, `tests/test_battle_state.py::test_fire_fang_burns_and_flinches_on_20`).
- **Contact ability hooks** - `auto_ptu.rules.move_traits.move_has_contact_trait` now consults `auto_ptu/data/compiled/contact_moves.json` (generated by `auto_ptu/tools/generate_contact_moves.py`), and the contact ability hook registry (`auto_ptu/rules/hooks/abilities/contact_effects.py`) emits Flame Body/Flame Tongue/White Flame burns, Static paralysis, Effect Spore/Poison Touch status rolls, and Rough Skin/Iron Barbs contact damage whenever a compiled contact move lands (see `tests/test_battle_state.py` for the logged `ability` events).

## 3. Modular Subsystems

### 3.1 Attack Context

New dataclass describing the ongoing action:

```python
@dataclass
class AttackContext:
    attacker: PokemonState
    defender: PokemonState
    move: MoveSpec
    weather: Optional[str]
    terrain: Optional[dict]
    domains: Set[str]
    roll_options: Set[str]
    modifiers: List[AttackModifier]
```

`build_attack_context()` populates this structure using the same order we observed in Foundry:

1. Seed domains with generic labels (`all`, `check`, `<category>`, `<type>`, `<melee|ranged>-<type>`).
2. Append trait-driven labels (Goldimbers `-trait-attack` style) by parsing `move.keywords`, `attacker.spec.tags`, and statuses.
3. Add STAB-specific roll options (`stab-electric`, `stab`) if move types intersect with attacker types.
4. Include weather-derived options (`weather-rain`, `weather-sun`) for later DB adjustments.
5. Inject ability-driven modifiers (Swift Swim, Chlorophyll, etc.) as structured `AttackModifier` objects that can either adjust accuracy or damage before/after STAB.

### 3.2 Modifier Pipeline

`AttackModifier` is a lightweight struct with:

- `slug`
- `value`
- `kind` (one of `power`, `accuracy`, `damage`, `type_step`, `crit`, `other`)
- `applies_at` (enum: `pre_accuracy`, `post_accuracy`, `pre_damage`, `post_damage`)
- `sources` (free-form metadata for logging)

All modifiers are applied deterministically by stage:

1. **Pre-accuracy** - accuracy stage adjustments, smoke, focus energy, trait-sourced bonuses.
2. **Post-accuracy** - seldom used; placeholder for reaction traits.
3. **Pre-damage** - base power replacement, DB adjustments, Burn halves, weather DB adjustments.
4. **Post-damage** - type multipliers, STAB special cases (Galvanize), ability-based conversions.

### 3.3 Domains & Roll Options

We store normalized strings (lowercase, hyphen separated) and expose:

- `context.has_option("stab-electric")`
- `context.with_domain("damaging-physical")`

These lists are serializable for debugging and will later power CLI "explain" commands.

## 4. Porting Roadmap

1. **Attack context & modular modifiers (this patch)** - Create the scaffolding, update `resolve_move_action` to accept contexts, feed log payloads with the breakdown.
2. **Trait, feature, and item registries** - Introduce JSON/YAML definitions describing how each trait or item inserts modifiers (mirrors Foundry trait change definitions).
3. **Effect hooks by phase** - Convert existing hazard/status handling to emit domain-aware modifiers so everything flows through the same pipeline.
4. **AI awareness** - Extend `rules.ai` so it reasons about modifiers and expected crit chances (Foundry's attack popup uses Tag prompts; we'll use context roll options).

## 5. Testing Expectations

For each ported feature we add a scenario:

- **STAB parity** - ensures two Electric STAB contexts produce identical damage as previously but now surface modifier metadata.
- **Weather boosts** - Rain + Swift Swim verifies both movement and damage DB adjustments fire via modifier pipeline.
- **Burn halving** - Already covered, but now validated via `AttackModifier` stage application.
- **Trait-sourced power boosts** - Synthetic trait entry that adds `+2 power` proves the declarative notes run.

These tests intentionally mimic the deterministic sequences we observed in Foundry logs, providing confidence we track the same math even though we execute it entirely within Auto PTU.

## 6. Future Enhancements

- **Roll transcription** - Because contexts know about every domain/option, CLI logs can explain *exactly* how a roll was constructed ("Domains: `['electric-physical', 'damaging-physical']`; Modifiers: `power:+2 (Rainy Terrain)`, `status:-2 (Paralysis)`).
- **Declarative data ingestion** - Feature JSON files (similar to Foundry's compendiums) will map to `AttackModifier` definitions, enabling community-driven data entry.
- **Backwards compatibility** - The previous `ptu_engine` helpers remain for comparison until the new flow achieves full PTU coverage.

This rewrite sets the tone for the rest of the engine: we replicate Foundry's logic path step by step, but the code stays entirely Pythonic, testable, and suitable for automated newbie-friendly play.

## 7. BattleState Boundaries (Non-Negotiable)
- BattleState orchestrates only: phase order, action scheduling, and controller delegation.
- New rule logic must live in registries or controllers (see ARCHITECTURE_POLICY.md).
- calculations.py, 	argeting.py, and movement.py are treated as frozen APIs once validated.


