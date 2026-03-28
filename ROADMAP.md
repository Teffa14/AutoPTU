# AutoPTU Overhaul Roadmap

## Milestone 1: Move-Special Coverage
- Implement missing move-special handlers until test suite no longer fails on move specials.
- Ensure all event payloads match expected test fields.
- Keep timing phases (pre_damage/post_damage/end_action) consistent.

## Milestone 2: Deterministic Hook Registration
- Replace side-effect imports with an explicit `register_all_hooks()` in `auto_ptu/rules/hooks/__init__.py`.
- Call registration exactly once at startup (or BattleState init).

## Milestone 2.5: API Freezes (Safety)
- Freeze the public APIs for `calculations.py`, `targeting.py`, and `movement.py`.
- Add docs for what must *not* live in `battle_state.py`.
- Establish `frequency.py` as the sole authority for usage resets and caps.

## Milestone 3: Ability/Item Registries
- Extract common ability triggers (on_hit, on_contact, on_turn_start/end, on_damage_calc).
- Extract item triggers (held activation, damage calc, end-of-turn ticks).
- Keep logic deterministic and keep logs unchanged.

## Milestone 4: Service Extraction
- Split `battle_state.py` by system: PhaseController, StatusController, ActionResolver, HookDispatcher, BattleLog.
- BattleState orchestrates sequence; services contain logic.

## Milestone 4.5: State Separation
- Separate `CampaignState` from `EncounterState`.
- Keep out-of-combat rules isolated from in-combat resolution.

## Milestone 5: Data-Driven Content
- Convert eligible move/ability/item effects into declarative tables.
- Preserve existing mechanics and logs; no new mechanics.

## Testing Strategy
- Maintain deterministic logs as goldens.
- Add targeted tests per new registry.
- Run full suite after each batch of handlers.

