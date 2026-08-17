# Java Port Plan

## Goal

Rebuild the AutoPTU battle core in Java while using the existing Python engine as an executable oracle.

The Java runtime should eventually be usable directly by a Craftics/Cobblemon integration without shipping Python to end users.

## Scope to port

- Battle state models and deterministic state transitions.
- Targeting, range, areas, footprints, and line of sight.
- PTU calculations and rounding semantics.
- Movement legality.
- Action economy, initiative, phases, and reactions.
- Statuses, hazards, terrain, forced movement, and temporary effects.
- Moves, abilities, items, perks, and Trainer Feature hook registries.
- Event emission.
- AI policy only after legal-action and resolution parity is stable.

## Explicitly out of scope for the core port

- FastAPI.
- Browser UI and React/Pixi UI.
- Career mode.
- Campaign/VTT layers.
- Supabase/Postgres deployment.
- PyInstaller and desktop launchers.
- Minecraft rendering and Cobblemon entity integration.

## Parity contract

For a fixed input, content version, and RNG stream:

```text
Python AutoPTU -> ordered events -> final state
Java AutoPTU   -> ordered events -> final state
```

The Java implementation passes only when the normalized outputs match.

## Migration order

1. Targeting and geometry.
2. RNG contract.
3. Basic stat and damage calculations.
4. Movement legality.
5. Core combatant and grid state.
6. Action economy and phase scheduler.
7. Basic move resolution.
8. Statuses, terrain, hazards, push/knockback.
9. Ability/item/perk/feature hooks.
10. Full move-special registry.
11. AI policy boundary.
12. Craftics/Cobblemon adapter.

## Non-negotiable compatibility rules

- Never rely on Java collection iteration order accidentally. Use explicit ordering where Python behavior depends on ordering.
- Never assume `java.util.Random` matches Python `random.Random`.
- Make rounding points explicit and test them.
- Preserve event order, not only final HP totals.
- Data that can remain data should not be rewritten as Java code.
