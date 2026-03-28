# AutoPTU Overhaul Task Tracker

## Goal
Incremental refactor of the deterministic PTU battle engine with registry-driven move specials, abilities, and items, preserving logs and timing.

## Current Status (2026-02-26)
- Move-special registry is wired into runtime (pre_damage/post_damage/end_action).
- Explicit timing support added to move specials.
- Move pipeline restored and logging reinserted (per-target move event).
- Smite miss partial damage event added.
- Ability effects added in damage pipeline: Absorb Force, Filter, Water Absorb, Motor Drive, Heatproof, Dry Skin, Flash Fire, Abominable/Rock Head recoil block.
- Phase effects restored: _run_phase_effects + status_skip logging.
- Spec copy-on-init to avoid shared mutation between Pokemon instances.
- Ability batch implemented: Klutz, Klutz [SwSh], Landslide, Leaf Gift, Leek Mastery, Life Force, Lightning Kicks, Lullaby, Lunchbox, Mach Speed, Magic Bounce, Magic Guard, Magician, Magnet Pull, Marvel Scale.
- Ability batch implemented: Mega Launcher, Memory Wipe, Migraine, Mimitree, Mind Mold, Mini-Noses, Minus, Minus [SwSh], Miracle Mile, Mojo.
- Ability hooks now auto-load from `auto_ptu/rules/hooks/abilities/`, with architecture guardrails documented in `ARCHITECTURE_POLICY.md`.
- Defender ability hooks now run through the registry (Absorb Force, Filter), reducing battle_state monolith growth.
- Heatproof migrated into the defender hook registry.
- Damage-resolution abilities migrated to hook phases (Analytic, Bully, Bulletproof, Cave Crasher, Courage, Enduring Rage, Friend Guard, Fur Coat, Grass Pelt, Desert Weather, Sturdy, Delayed Reaction, Justified, Cruelty, Dry Skin, Moxie).
- Damage pipeline refactor extended: last-chance bonuses, aura adjacency bonuses, super-effective bonuses, and absorb/immunity hooks now live in registry modules.
- Pre-damage interrupts migrated to hook registry (Protect/Obstruct/Quick Guard, Fox Fire, Baneful Bunker).
- Phase effects migrated to the phase hook registry (`auto_ptu/rules/hooks/abilities/phase_effects.py`).
- Combat stage reaction abilities (Minus [SwSh], Defiant, Competitive) migrated to `combat_stage_hooks`.
- Contact ability effects now route through the hook registry (`auto_ptu/rules/hooks/abilities/contact_effects.py`).
- Item hook registry added with defender mitigation hooks (Focus Sash/Band, super-effective resist, damage scalars).
- Perk hook registry scaffolding added for future modules.
- Homebrew extension loader added with an example pack under `extensions/`.
- Item hook registry expanded to cover attacker modifiers, miss triggers, post-damage effects, and defender triggers.
- Perk hooks wired into phase processing with trainer feature accessors on PokemonState.
- BattleState now discovers extension packs automatically.
- Move specials implemented across extensive move families (see `archive/notes/TASK.md` for the historical list).
- Hunger Switch now prompts at turn start in the web UI and blocks action until a choice is made.
- ITEM_LOG and ATTACK_LOG updated to reflect full completion counts.

## Recent Updates (2026-02-26)
- Item effect batches implemented and covered in `tests/test_battle_state.py` with explicit event payload checks (see `ITEM_LOG.md` for tracked coverage).
- Documentation cleanup started: canonical docs listed in `DOCS_INDEX.md`, duplicates archived, and source-of-truth rules clarified.

## Open Issues (high priority)
- Many move specials remain in tests (status moves, secondary effects, priority logs, hazards, etc.).
- Ability/system registries are still largely hardcoded in `auto_ptu/rules/battle_state.py`.
- Move-special tests expect specific event fields; keep event shapes consistent.
- Phase effects and status skip logic should remain deterministic and log-stable.

## Testing
- Full suite passing (2026-02-26): 1455 passed.

## Next Actions
1) Reconcile `AUDIT_CHECKLIST.md` against current coverage and prune entries that are already fully handled.
2) Audit ability metadata coverage from PTU CSV to eliminate missing text cases in the UI.
3) Expand item/ability logic extraction into registries or service modules.

