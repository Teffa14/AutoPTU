# PTU Dataset Overrides (Godfile Sync)

This file records authoritative PTUDatabase overrides applied to compiled move effects.
Source: `PTUDatabase-main/Data/ptu.1.05.yaml`

## Applied Updates
The following moves had empty/`--` effects text in `auto_ptu/data/compiled/moves.json` but non-empty effects in the PTU dataset, so the compiled data was updated to match PTU:

- Accelerock
- Blast Burn
- Branch Poke
- Brutal Swing
- Dual Wingbeat
- Eternabeam
- Frenzy Plant
- Hydro Cannon
- Leafage
- Origin Pulse
- Overdrive
- Prismatic Laser

## Notes
- The PTU dataset is treated as authoritative for effects text.
- If compiled data and PTU dataset diverge, prefer PTU dataset.
