# Battle Phase Coverage Matrix

This file ties PTU Core 1.05 citations to unit tests that exercise each battle
phase. Update this list whenever phase behavior changes so UI layers can trust
the engine.

## Round Start / Initiative

- Rule citations: PTU Core 1.05 p. 202-203 (Initiative and turn order), p. 227
  (initiative calculation).
- Unit tests:
  - `tests/test_battle_state.py::test_initiative_prefers_faster_pokemon`
  - `tests/test_battle_state.py::test_initiative_uses_trainer_modifier`
  - `tests/test_battle_state.py::test_initiative_skips_inactive_bench`
  - `tests/test_battle_state.py::test_league_initiative_orders_trainers_before_pokemon`
  - `tests/test_battle_state.py::test_delay_moves_initiative_order`

## Start Phase

- Rule citations: PTU Core 1.05 p. 202-203 (phase order), p. 246-247 (status
  resolution timing).
- Unit tests:
  - `tests/test_battle_state.py::test_phase_progression_follows_start_command_action_end`
  - `tests/test_battle_state.py::test_flinch_status_skips_start_phase`
  - `tests/test_battle_state.py::test_paralyzed_pokemon_skips_turn`
  - `tests/test_battle_state.py::test_confusion_roll_hits_self_with_struggle`

## Command Phase

- Rule citations: PTU Core 1.05 p. 202-203 (command declarations).
- Unit tests:
  - `tests/test_battle_state.py::test_phase_progression_follows_start_command_action_end`
  - `tests/test_battle_state.py::test_trapped_status_logs_command_phase`

## Action Phase

- Rule citations: PTU Core 1.05 p. 202-203 (action resolution order).
- Unit tests:
  - `tests/test_battle_state.py::test_phase_progression_follows_start_command_action_end`
  - `tests/test_battle_state.py::test_rage_status_logs_action_phase`

## End Phase

- Rule citations: PTU Core 1.05 p. 202-203 (end phase) and p. 246-247 (status
  tick timing, saves, and cures).
- Unit tests:
  - `tests/test_battle_state.py::test_sleep_status_saves_at_end_of_turn`
  - `tests/test_battle_state.py::test_shed_skin_cures_status_at_end_phase`
  - `tests/test_battle_state.py::test_burn_status_ticks_hp`
  - `tests/test_battle_state.py::test_badly_poisoned_damage_doubles_each_round`

## Intercept & AoO

- Rule citations: PTU Core 1.05 p. 241 (AoO triggers) and p. 242 (Intercept checks
  and failure movement).
- Unit tests:
  - `tests/test_battle_state.py::test_intercept_loyalty_blocks_other_trainer`
  - `tests/test_battle_state.py::test_intercept_loyalty_allows_other_trainer`
  - **Coverage gap:** AoO provocation lacks direct unit tests; consider adding a
    dedicated scenario (e.g., adjacent opponent shifts or ranged attack checks)
    to document PTU p. 241 triggers.

## Targeting & AoE Shapes

- Rule citations: PTU Core 1.05 pp. 343-345 (Blast/Close Blast/Cone shapes, AoE LOS
  blocking).
- Unit tests:
- `tests/test_targeting.py::test_blast_is_square`
- `tests/test_targeting.py::test_close_blast_is_adjacent_square`
- `tests/test_targeting.py::test_cone_is_three_wide_rows`
 - `tests/test_battle_state.py::test_area_line_respects_wall_blocking`
