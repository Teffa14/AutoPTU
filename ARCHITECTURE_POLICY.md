# Architecture Policy (No Monoliths)

This project enforces small, composable rule units. The goal is to prevent giant files and entangled logic as moves, abilities, items, perks, and homebrew scale.

## Non-Negotiables
- Core engine flow lives in `auto_ptu/rules/battle_state.py` but must not accumulate new rule logic.
- All new ability/item/move/perk behavior must go through registries and hooks.
- No direct calls to behavior by name outside registries.
- Calculations, targeting, and movement APIs are treated as frozen once validated by tests.
- Frequency logic must be centralized; no custom reset rules outside `auto_ptu/rules/frequency.py`.

## File Size Discipline
- Prefer one module per ability family or keyword group.
- Split files once they exceed ~300-400 lines.
- If a rule cannot be described in a small hook, add a helper in a dedicated module under `auto_ptu/rules/helpers/`.

## BattleState Decomposition Plan (No Immediate Breakage)
BattleState remains the orchestrator, but new responsibilities must be routed to controllers:
- PhaseController: phase sequencing and transitions
- StatusController: status ticking, duration changes, and end-of-turn status hooks
- ActionResolver: validation + resolution for actions and action types
- HookDispatcher: centralized registry execution (abilities, items, perks, move specials)
- BattleLog: logging helpers and event normalization

## Spatial Rules Boundaries
- `targeting.py` and `movement.py` only own geometry and spatial rules.
- Narrative or special-case behavior must be decided before calling spatial helpers.

## Hook Contracts
- Hooks are pure functions over a context object.
- All state changes go through context helpers and emit events.
- No RNG access except via the context/battle RNG.

## Registries Are the Entry Points
- Abilities: `auto_ptu/rules/hooks/abilities/`
- Phase effects: `auto_ptu/rules/hooks/phase_hooks.py`
- Combat stage reactions: `auto_ptu/rules/hooks/combat_stage_hooks.py`
- Move specials: `auto_ptu/rules/hooks/move_specials_*.py`
- Items: `auto_ptu/rules/hooks/item_effects/`
- Perks: `auto_ptu/rules/hooks/perk_effects/`

## Homebrew Extension Rules
- Extensions live under `extensions/<pack>/`.
- Each pack ships a `manifest.json` with priority and compatibility.
- Packs can override or augment content using explicit override policy.

## Effect Ownership
- `item_effects.py` and `move_traits.py` stay declarative and callback-driven.
- The core engine executes effects but does not interpret or duplicate their logic.

## Testing Requirements
- Every new hook must ship with at least one test.
- Interaction changes require a scenario test or golden log.

