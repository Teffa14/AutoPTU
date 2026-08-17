# AutoPTU Java Core

This directory is the bootstrap for a clean Java port of the AutoPTU battle rules engine.

It is intentionally **not** a Minecraft mod yet. The first goal is behavioral parity with the existing Python engine. Minecraft, Craftics, and Cobblemon should consume this core later rather than own PTU rules themselves.

## Source oracle

The current Python implementation remains authoritative while the port is incomplete.

Primary oracle pieces in the parent repository:

- `auto_ptu/career/models.py` — deterministic battle input/output contracts.
- `auto_ptu/career/battle.py` — isolated seeded battle simulation and transcript hashing.
- `tests/test_career_battle_determinism.py` — proves repeated simulations produce identical transcripts.
- `auto_ptu/api/battle_commands.py` — command boundary that does not own PTU math.
- `auto_ptu/rules/targeting.py` — first rules module being ported here.

## Port rule

Do not translate the Python monolith line by line.

For each subsystem:

1. Define a language-neutral input/output contract.
2. Freeze Python fixtures for representative scenarios.
3. Implement the same behavior in Java.
4. Compare ordered events and final state.
5. Only move to the next subsystem when parity tests pass.

## Current status

- [x] Java 21 library skeleton.
- [x] Cross-language oracle contract types.
- [x] Targeting/range/area/footprint/line-of-sight port started.
- [x] Java tests for the first targeting slice.
- [ ] Export golden targeting fixtures from Python.
- [ ] Port deterministic RNG contract.
- [ ] Port core calculations.
- [ ] Port movement legality.
- [ ] Port action economy and phases.
- [ ] Port statuses and effects.
- [ ] Port move/ability/item/feature hook registries.
- [ ] Port AI policy after rules parity.

## Run

```bash
./gradlew test
```

If a Gradle wrapper has not been generated yet, use a local Gradle installation once to generate it or run `gradle test`.
