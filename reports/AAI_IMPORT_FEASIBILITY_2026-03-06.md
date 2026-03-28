# AAI Import Feasibility (2026-03-06)

Source scanned:
- `IMPLEMENTATION FILES/[000_AAI] Advanced AI System/[000_AAI] Advanced AI System`
- 49 files (48 `.rb`, 1 metadata text), RPG Maker Essentials plugin format.

## What Is Directly Portable

1. Tier behavior model
- Status: Ported.
- Location: `auto_ptu/ai/aai_port.py`.
- Notes: Adds feature tiers aligned with AutoPTU AI levels (`standard`, `tactical`, `strategic`).

2. Pattern probability heuristics
- Status: Ported.
- Location: `auto_ptu/ai/aai_port.py`.
- Notes: Defensive tendency and retreat tendency derived from learned opponent profile histograms.

3. Adaptive move-score nudges
- Status: Ported.
- Location: `auto_ptu/rules/ai_hybrid.py`.
- Notes: Strategic/tactical scoring now adds small bonuses for hazard/setup/status utility when opponent retreat tendency is high.

## What Is Not Directly Portable

1. Ruby battle hooks and plugin integration
- Files: `7_Integration/*.rb`, DBK compatibility hooks.
- Reason: Bound to Essentials runtime APIs and Ruby class model.

2. Gen 9 mechanic modules (Mega/Z/Dynamax/Tera)
- Files: `6_Meta_Mechanics/*.rb`.
- Reason: Mechanics differ from PTU rules and would require PTU-specific redesign.

3. Full move-by-move hardcoded immunity/failure tables
- Files: `2_Move_Intelligence/0_Move_Scorer.rb` and related.
- Reason: High maintenance and many mechanics are not 1:1 with PTU action resolution.

## Recommended Next Ports

1. Switch trigger model
- Port safe subset: low-HP + danger + bench quality + hazard entry cost.
- Integrate into existing `_ai_should_switch` path in `auto_ptu/gameplay.py`.

2. Threat decomposition telemetry
- Add structured threat components (`stats`, `coverage`, `speed`, `setup`) to diagnostics only.
- Keep decision layer deterministic and auditable.

3. Pattern-aware anti-stall
- Use profile signals (`defend` frequency, repeated non-damage turns) to increase engagement pressure before forced Struggle logic.

## Validation

- `python -m pytest tests/test_ai_hybrid.py -q`
- Result: `10 passed`.

