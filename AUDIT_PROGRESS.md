# Audit Progress

This file tracks checklist items completed in strict order, with evidence links.

## Batch 1 (Moves 1-10)
- Absorb :: Verified handler `_drain_half_damage` (`auto_ptu/rules/hooks/move_specials.py`) and new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_absorb_drains`.
- Aerial Ace :: Verified generic cannot-miss handling; new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_aerial_ace_cannot_miss`.
- Aeroblast :: Verified crit even-roll handling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_aeroblast_even_roll_crit`.
- Arm Thrust :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py` (no special hook required).
- Attack Order :: Verified crit 18+ handling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_attack_order_crit_18`.
- Aura Sphere :: Verified generic cannot-miss handling; new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_aura_sphere_cannot_miss`.
- Barrage :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py` (no special hook required).
- Behemoth Bash :: Verified DB scaling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_behemoth_bash_scales`.
- Behemoth Blade :: Verified DB scaling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_behemoth_blade_scales`.
- Blast Burn :: Implemented generic Exhaust handling in `auto_ptu/rules/hooks/move_specials.py`; new test `tests/test_audit_batch1_moves.py::AuditBatch1MoveTests::test_blast_burn_exhausts`.

## Batch 2 (Moves 11-20)
- Blaze Kick :: Added burn-on-19+ handler; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_blaze_kick_burns_19`.
- Blue Flare :: Added burn-on-17+ handler; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_blue_flare_burns_17`.
- Body Slam :: Added paralyze-on-15+ handler; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_body_slam_paralyzes_15`.
- Bolt Strike :: Added paralyze-on-17+ handler; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_bolt_strike_paralyzes_17`.
- Bone Rush :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Bonemerang :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Boomburst :: Verified base damage flow; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_boomburst_base_damage`.
- Branch Poke :: Verified base damage flow; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_branch_poke_base_damage`.
- Brave Bird :: Verified forced movement via Push keyword; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_brave_bird_pushes`.
- Brine :: Verified DB boost at <=50% HP; new test `tests/test_audit_batch2_moves.py::AuditBatch2MoveTests::test_brine_db_boost`.

## Batch 3 (Moves 21-30)
- Brutal Swing :: Verified base damage flow; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_brutal_swing_base_damage`.
- Bubble :: Added speed drop on 16+; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_bubble_slows_16`.
- Bubblebeam :: Added speed drop on 18+; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_bubblebeam_slows_18`.
- Bulk Up :: Added +1 ATK/+1 DEF self buff; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_bulk_up_raises_stats`.
- Bullet Punch :: Verified base damage flow; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_bullet_punch_base_damage`.
- Bullet Seed :: Verified base damage flow; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_bullet_seed_base_damage`.
- Bullseye :: Verified crit 16+ handling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_bullseye_crit_16`.
- Captivate :: Added gender-gated -2 Sp. Atk; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_captivate_spatk_drop`.
- Charm :: Added -2 Attack; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_charm_atk_drop`.
- Chatter :: Added Confusion on 16+; new test `tests/test_audit_batch3_moves.py::AuditBatch3MoveTests::test_chatter_confuses_16`.

## Batch 4 (Moves 31-40)
- Cheap Shot :: Verified generic cannot-miss handling; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_cheap_shot_cannot_miss`.
- Chip Away :: Verified ignore DR/defensive stages; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_chip_away_ignores_defense_and_dr`.
- Close Combat :: Added post-damage DEF/SPDEF drops; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_close_combat_lowers_defenses`.
- Comet Punch :: Verified base damage flow; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_comet_punch_base_damage`.
- Confide :: Added -1 Sp. Atk; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_confide_lowers_spatk`.
- Confusion :: Verified confusion on 19+ via generic status; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_confusion_confuses_19`.
- Crabhammer :: Verified crit 18+ handling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_crabhammer_crit_18`.
- Cross Chop :: Verified crit 16+ handling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_cross_chop_crit_16`.
- Cross Poison :: Verified poison on 19+ via generic status; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_cross_poison_poison_19`.
- Crunch :: Verified DEF drop on 17+ via generic stat handling; new test `tests/test_audit_batch4_moves.py::AuditBatch4MoveTests::test_crunch_lowers_defense_17`.

## Batch 5 (Moves 41-50)
- Crush Claw :: Added even-roll DEF drop; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_crush_claw_even_roll_def_drop`.
- Crush Grip :: Verified DB scaling at low HP; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_crush_grip_db_reduces_when_low_hp`.
- Cut :: Verified ignore DR up to 5; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_cut_ignores_dr5`.
- Dark Pulse :: Added flinch on 17+; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_dark_pulse_flinch_17`.
- Darkest Lariat :: Verified ignore DR/positive defenses; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_darkest_lariat_ignores_def_and_dr`.
- Dazzling Gleam :: Verified base damage flow; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_dazzling_gleam_base_damage`.
- Defend Order :: Added +1 DEF/+1 SPDEF; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_defend_order_boosts_defenses`.
- Defog :: Verified hazard clear; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_defog_clears_hazards`.
- Destiny Bond :: Verified effect application; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_destiny_bond_sets_effect`.
- Diamond Storm :: Added even-roll DEF boost; new test `tests/test_audit_batch5_moves.py::AuditBatch5MoveTests::test_diamond_storm_even_roll_def_boost`.

## Batch 6 (Moves 51-60)
- Disarming Voice :: Verified generic cannot-miss handling; new test `tests/test_audit_batch6_moves.py::AuditBatch6MoveTests::test_disarming_voice_cannot_miss`.
- Discharge :: Verified paralyze on 15+; new test `tests/test_audit_batch6_moves.py::AuditBatch6MoveTests::test_discharge_paralyze_15`.
- Dizzy Punch :: Verified confusion on 17+ via generic status; new test `tests/test_audit_batch6_moves.py::AuditBatch6MoveTests::test_dizzy_punch_confuse_17`.
- Double Hit :: Verified Double Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Double Slap :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Double Swipe :: Verified Double Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Double Team :: Verified effect grants 3 charges; new test `tests/test_audit_batch6_moves.py::AuditBatch6MoveTests::test_double_team_grants_charges`.
- Draco Meteor :: Verified -2 Sp. Atk self drop; new test `tests/test_audit_batch6_moves.py::AuditBatch6MoveTests::test_draco_meteor_spatk_drop`.
- Dragon Darts :: Verified Double Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Dragon Hammer :: Verified base damage flow; new test `tests/test_audit_batch6_moves.py::AuditBatch6MoveTests::test_dragon_hammer_base_damage`.

## Batch 7 (Moves 61-70)
- Double Iron Bash :: Verified flinch on 15+ via generic status and Double Strike parsing; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_double_iron_bash_flinch_15`.
- Double Kick :: Verified Double Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Dragon Claw :: Verified base damage flow; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_dragon_claw_base_damage`.
- Dragon Energy :: Verified DB reduction at low HP in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_dragon_energy_db_reduces_when_low_hp`.
- Dragon Pulse :: Verified base damage flow; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_dragon_pulse_base_damage`.
- Dragon Rush :: Verified flinch on 17+ via generic status and Push 3 via forced movement parsing; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_dragon_rush_flinch_17_and_push`.
- Drain Punch :: Verified drain half damage handler; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_drain_punch_drains`.
- Draining Kiss :: Verified drain half damage handler; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_draining_kiss_drains`.
- Dream Eater :: Verified sleep-gated drain; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_dream_eater_requires_sleep_and_drains`.
- Drill Peck :: Verified base damage flow; new test `tests/test_audit_batch7_moves.py::AuditBatch7MoveTests::test_drill_peck_base_damage`.

## Batch 8 (Moves 71-80)
- Drill Run :: Verified crit 18+ handling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_drill_run_crit_18`.
- Drum Beating :: Verified Speed -1 CS via generic text parser; new test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_drum_beating_lowers_speed`.
- Dual Chop :: Verified Double Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Dual Wingbeat :: Verified Double Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Dynamax Cannon :: Verified DB scaling with positive target CS in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_dynamax_cannon_db_scales_positive_cs`.
- Echoed Voice :: Verified DB scaling based on prior rounds in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_echoed_voice_db_boosts_after_rounds`.
- Eerie Impulse :: Verified Special Attack -2 CS via generic stat parsing; test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_eerie_impulse_lowers_spatk`.
- Egg Bomb :: Verified base damage flow; new test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_egg_bomb_base_damage`.
- Electro Ball :: Verified speed-stat damage contribution in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_electro_ball_uses_speed_stats`.
- Eruption :: Verified DB reduction at low HP in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch8_moves.py::AuditBatch8MoveTests::test_eruption_db_reduces_when_low_hp`.

## Batch 9 (Moves 81-90)
- Eternabeam :: Verified Exhaust handling via global exhaust parser; new test `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_eternabeam_exhausts`.
- EW Adept :: No source references in audit; smoke test only (no crash) via `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_ew_adept_no_crash`.
- EW Expert :: No source references in audit; smoke test only (no crash) via `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_ew_expert_no_crash`.
- Explosion :: Verified self-destruct drops user to -50% max HP and logs self_destruct; test `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_explosion_sets_hp_below_zero`.
- Extrasensory :: Verified flinch on 19+ via generic status; new test `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_extrasensory_flinch_19`.
- Extreme Speed :: Verified base damage flow; new test `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_extreme_speed_base_damage`.
- False Surrender :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_false_surrender_cannot_miss`.
- Feint Attack :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_feint_attack_cannot_miss`.
- Fell Stinger :: Verified +2 Attack on KO via generic text handler; new test `tests/test_audit_batch9_moves.py::AuditBatch9MoveTests::test_fell_stinger_raises_attack_on_ko`.

## Batch 10 (Moves 91-100)
- Fiery Wrath :: Verified flinch on 17+ via generic status; verified Fire-type conversion once/scene in `auto_ptu/rules/battle_state.py` (type swap seen in roll options); new tests `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_fiery_wrath_flinch_17` and `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_fiery_wrath_can_convert_to_fire`.
- Fire Blast :: Verified burn on 19+ via generic status; new test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_fire_blast_burn_19`.
- Fire Lash :: Verified DEF -1 CS via generic text parser; new test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_fire_lash_lowers_defense`.
- Flail :: Verified DB scaling with injuries in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_flail_db_increases_with_injuries`.
- Flame Wheel :: Verified burn on 19+ via generic status; new test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_flame_wheel_burn_19`.
- Flare Blitz :: Verified burn on 19+ via generic status; new test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_flare_blitz_burn_19`.
- Flash Cannon :: Verified lowers Special Defense by -1 on 17+; test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_flash_cannon_spdef_drop_17`.
- Flatter :: Verified raises Special Attack +1 CS and Confuses; test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_flatter_raises_spatk_and_confuses`.
- Fleur Cannon :: Verified lowers user's Special Attack by -2 after damage; test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_fleur_cannon_lowers_self_spatk`.
- Focus Blast :: Verified lowers Special Defense by -1 on 18+; test `tests/test_audit_batch10_moves.py::AuditBatch10MoveTests::test_focus_blast_spdef_drop_18`.

## Batch 11 (Moves 101-110)
- Foul Play :: Verified uses target Attack in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_foul_play_uses_target_attack`.
- Freezing Glare :: Verified freeze on 19+ via generic status; verified Ice-type conversion once/scene in `auto_ptu/rules/battle_state.py` (type swap seen in roll options); new tests `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_freezing_glare_freeze_19` and `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_freezing_glare_can_convert_to_ice`.
- Frenzy Plant :: Verified Exhaust handling via global exhaust parser; new test `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_frenzy_plant_exhausts`.
- Frost Breath :: Verified always-crit handling in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_frost_breath_always_crits`.
- Frustration :: Verified DB scaling by loyalty in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_frustration_db_scales_with_loyalty`.
- Fury Attack :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Fury Cutter :: Verified chain-based DB scaling in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_fury_cutter_db_scales_with_chain`.
- Fury Swipes :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Fusion Bolt :: Verified +3 DB if Fusion Flare used in recent rounds in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_fusion_bolt_db_boost`.
- Fusion Flare :: Verified +3 DB if Fusion Bolt used in recent rounds in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch11_moves.py::AuditBatch11MoveTests::test_fusion_flare_db_boost`.

## Batch 12 (Moves 111-120)
- Gear Grind :: Verified Double Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Giga Drain :: Verified drain half damage handler; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_giga_drain_drains`.
- Grass Whistle :: Verified sleep application via generic text handler; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_grass_whistle_sleeps`.
- Grav Apple :: Verified DEF -1 CS via generic text parser; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_grav_apple_lowers_def`.
- Growth :: Verified raises Attack + Special Attack, doubles in sun; tests `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_growth_raises_attack_and_spatk` and `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_growth_sunny_doubles`.
- Gunk Shot :: Verified poison on 15+ via generic status; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_gunk_shot_poison_15`.
- Gyro Ball :: Verified speed-difference DB bonus in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_gyro_ball_bonus_db`.
- Harden :: Verified DEF +1 via generic text parser; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_harden_raises_def`.
- Head Charge :: Verified Push 2 and recoil via forced movement + recoil parsing; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_head_charge_push_and_recoil`.
- Head Smash :: Verified Push 2 and recoil via forced movement + recoil parsing; new test `tests/test_audit_batch12_moves.py::AuditBatch12MoveTests::test_head_smash_push_and_recoil`.

## Batch 13 (Moves 121-130)
- Heal Bell :: Verified cures status on burst targets (not team-limited); test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_heal_bell_cures_status`.
- Heal Order :: Verified heals 1/2 max HP via `auto_ptu/rules/hooks/move_specials.py`; new test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_heal_order_heals_half`.
- Heat Crash :: Verified weight-class DB scaling in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_heat_crash_db_scales_with_weight`.
- Heat Wave :: Verified burn on 18+ via generic status; new test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_heat_wave_burns_18`.
- Helping Hand :: Verified accuracy bonus temp effect via `auto_ptu/rules/hooks/move_specials.py`; new test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_helping_hand_accuracy_bonus`.
- Hex :: Verified scene-limited DB 13 boost on statused target in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_hex_db_boost_when_statused`.
- High Horsepower :: Verified sprint follow-up logs Smite event; test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_high_horsepower_smite_on_sprint`.
- Horn Attack :: Verified base damage flow; test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_horn_attack_gore_crit_range` (crit entry present).
- Horn Leech :: Verified drain half damage handler; new test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_horn_leech_drains`.
- Hurricane :: Verified confusion on 15+ via handler; new test `tests/test_audit_batch13_moves.py::AuditBatch13MoveTests::test_hurricane_confusion_15`.

## Batch 14 (Moves 131-140)
- Hydro Pump :: Verified Push 3 via forced movement parsing; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_hydro_pump_pushes`.
- Hyper Voice :: MISSING/INCORRECT: Smite from range text not applied (no smite event) (fails `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_hyper_voice_smite`).
- Ice Beam :: Verified freeze on 19+ via handler; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_ice_beam_freeze_19`.
- Ice Punch :: Verified freeze on 19+ via generic status; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_ice_punch_freeze_19`.
- Ice Shard :: Verified base damage flow; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_ice_shard_base_damage`.
- Icicle Crash :: Verified flinch on 15+ via generic status; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_icicle_crash_flinch_15`.
- Imprison :: Verified cannot-miss and lock effect via handlers; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_imprison_cannot_miss_and_locks`.
- Inferno :: Verified guaranteed burn via handler; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_inferno_burns`.
- Iron Defense :: Verified DEF +2 via generic text parser; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_iron_defense_raises_def`.
- Iron Head :: Verified flinch on 15+ via generic status; new test `tests/test_audit_batch14_moves.py::AuditBatch14MoveTests::test_iron_head_flinch_15`.

## Batch 15 (Moves 141-150)
- Icy Wind :: Verified Speed -1 via handler; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_icy_wind_lowers_speed`.
- Incinerate :: Verified item drop via handler; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_incinerate_drops_item`.
- Infernal Parade :: MISSING/INCORRECT: burn on 17+ not applied (text uses "Burned" and generic handler only matches "burns") (fails `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_infernal_parade_burn_17`).
- Infestation :: Verified Vortex application via handler; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_infestation_vortex`.
- Ingrain :: Verified Ingrain status applied via handler; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_ingrain_applies_status`.
- Jaw Lock :: Verified Grapple via handler; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_jaw_lock_grapple`.
- Karate Chop :: Verified crit 17+ in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_karate_chop_crit_17`.
- Knock Off :: Verified item drop via handler; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_knock_off_drops_item`.
- Leaf Blade :: Verified crit 18+ in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_leaf_blade_crit_18`.
- Leech Life :: Verified drain half damage handler; new test `tests/test_audit_batch15_moves.py::AuditBatch15MoveTests::test_leech_life_drains`.

## Batch 16 (Moves 151-160)
- Leaf Tornado :: Verified Accuracy -1 on 15+ via handler; new test `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_leaf_tornado_accuracy_drop_15`.
- Light Screen :: MISSING/INCORRECT: Blessing move does not apply Light Screen status (no status/log) (fails `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_light_screen_applies_status`).
- Low Sweep :: Verified Speed -1 via generic text parser; new test `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_low_sweep_lowers_speed`.
- Luster Purge :: MISSING/INCORRECT: even-roll Sp. Def drop not parsed; no handler (fails `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_luster_purge_spdef_even`).
- Magical Leaf :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_magical_leaf_cannot_miss`.
- Magnet Bomb :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_magnet_bomb_cannot_miss`.
- Magnitude :: MISSING/INCORRECT: damage base roll not applied (effective_db remains 0 in log) (fails `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_magnitude_db_rolls`).
- Mega Drain :: Verified drain half damage handler; new test `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_mega_drain_drains`.
- Metal Claw :: Verified Attack +1 on 18+ via generic text parser; new test `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_metal_claw_attack_boost_18`.
- Meteor Mash :: Verified Attack +1 on 15+ via generic text parser; new test `tests/test_audit_batch16_moves.py::AuditBatch16MoveTests::test_meteor_mash_attack_boost_15`.

## Batch 17 (Moves 161-170)
- MH Adept :: No source references in audit; smoke test only (no crash) via `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_mh_adept_no_crash`.
- MH Expert :: No source references in audit; smoke test only (no crash) via `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_mh_expert_no_crash`.
- Moonblast :: MISSING/INCORRECT: Special Attack drop on 15+ not applied (parser maps to Attack) (fails `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_moonblast_lowers_spatk_15`).
- Multi-Attack :: Verified type change from item in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_multi_attack_type_from_item`.
- Multi-Attack [SS] :: Verified type change from item in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_multi_attack_ss_type_from_item`.
- Name :: Placeholder entry; smoke test only (no crash) via `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_name_no_crash`.
- Nasty Plot :: MISSING/INCORRECT: Special Attack +2 not applied (parser maps to Attack) (fails `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_nasty_plot_spatk_plus2`).
- Needle Arm :: Verified flinch on 15+ via generic status; new test `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_needle_arm_flinch_15`.
- Night Slash :: Verified crit 18+ in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_night_slash_crit_18`.
- OH Adept :: No source references in audit; smoke test only (no crash) via `tests/test_audit_batch17_moves.py::AuditBatch17MoveTests::test_oh_adept_no_crash`.

## Batch 18 (Moves 171-180)
- Origin Pulse :: MISSING/INCORRECT: Smite from range text not applied (no smite event) (fails `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_origin_pulse_smite`).
- Overdrive :: Verified base damage flow; new test `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_overdrive_base_damage`.
- Overheat :: MISSING/INCORRECT: self Sp. Atk -2 after damage not applied (fails `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_overheat_lowers_spatk`).
- Parabolic Charge :: Verified drain half total damage handler; new test `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_parabolic_charge_drains`.
- Parabolic Charge [SM] :: Verified drain half total damage handler; new test `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_parabolic_charge_sm_drains`.
- Peck :: Verified base damage flow; new test `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_peck_base_damage`.
- Petal Blizzard :: Verified base damage flow; new test `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_petal_blizzard_base_damage`.
- Photon Geyser :: Verified uses higher ATK/SPATK in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_photon_geyser_uses_highest_stat`.
- Pin Missile :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Pound :: Verified base damage flow; new test `tests/test_audit_batch18_moves.py::AuditBatch18MoveTests::test_pound_base_damage`.

## Batch 19 (Moves 181-190)
- Power Gem :: Verified base damage flow; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_power_gem_base_damage`.
- Power Trip :: Verified DB scaling with user positive CS in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_power_trip_db_scales`.
- Precipice Blades :: MISSING/INCORRECT: Smite from range text not applied (no smite event) (fails `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_precipice_blades_smite`).
- Prismatic Laser :: Verified Exhaust handling via global exhaust parser; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_prismatic_laser_exhausts`.
- Psych Up :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_psych_up_cannot_miss`.
- Psycho Boost :: MISSING/INCORRECT: self Sp. Atk -2 after damage not applied (fails `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_psycho_boost_lowers_spatk`).
- Psycho Cut :: Verified crit 18+ in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_psycho_cut_crit_18`.
- Punishment :: Verified DB scaling with target positive CS in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_punishment_db_scales`.
- Razor Leaf :: Verified crit 18+ in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_razor_leaf_crit_18`.
- Rock Throw :: Verified base damage flow; new test `tests/test_audit_batch19_moves.py::AuditBatch19MoveTests::test_rock_throw_base_damage`.

## Batch 20 (Moves 191-200)
- Rock Tomb :: Verified Speed -1 via generic text parser; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_rock_tomb_lowers_speed`.
- Rolling Kick :: Verified flinch on 15+ via generic status; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_rolling_kick_flinch_15`.
- Rollout :: Verified DB scaling with chain state in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_rollout_db_scales_chain`.
- Round :: Verified DB scaling with round uses in `auto_ptu/rules/battle_state.py`; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_round_db_scales_with_uses`.
- Sacred Sword :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_sacred_sword_cannot_miss`.
- Scratch :: Verified base damage flow; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_scratch_base_damage`.
- Seed Bomb :: Verified base damage flow; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_seed_bomb_base_damage`.
- Self-Destruct :: MISSING/INCORRECT: HP set to -50% max not implemented (engine only self-KOs) (fails `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_self_destruct_sets_hp_below_zero`).
- Shadow Bone :: Verified Defense -1 on 17+ via generic text parser; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_shadow_bone_def_drop_17`.
- Shadow Claw :: Verified crit 18+ in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch20_moves.py::AuditBatch20MoveTests::test_shadow_claw_crit_18`.

## Batch 21 (Moves 201-210)
- Shadow Punch :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_shadow_punch_cannot_miss`.
- Sharpen :: Verified Attack +1 via generic text parser; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_sharpen_raises_attack`.
- Shell Side Arm :: Verified uses highest ATK/SPATK in `auto_ptu/rules/calculations.py`; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_shell_side_arm_uses_highest_stat`.
- Shell Smash :: MISSING/INCORRECT: multi-stat raise/lower not applied (parser not handling combined list) (fails `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_shell_smash_stat_changes`).
- Shock Wave :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_shock_wave_cannot_miss`.
- Skull Bash :: Verified setup Defense +1 via generic text parser; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_skull_bash_setup_defense`.
- Smart Strike :: Verified cannot-miss via generic text handler; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_smart_strike_cannot_miss`.
- Smog :: Verified poison on even roll via generic status; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_smog_poisons_even_roll`.
- Snore :: Verified flinch on 15+ via generic status; new test `tests/test_audit_batch21_moves.py::AuditBatch21MoveTests::test_snore_flinch_15`.
- Spike Cannon :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.

## Batch 22 (Moves 211-220)
- Steam Eruption :: Verified burn on 15+ via generic status; new test `tests/test_audit_batch22_moves.py::AuditBatch22MoveTests::test_steam_eruption_burn_15`.
- Tackle :: Verified Push 2 via forced movement parsing; new test `tests/test_audit_batch22_moves.py::AuditBatch22MoveTests::test_tackle_pushes`.
- Tackle [SM] :: Verified Push 2 via forced movement parsing; new test `tests/test_audit_batch22_moves.py::AuditBatch22MoveTests::test_tackle_sm_pushes`.
- Tail Slap :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Twineedle :: Verified poison on 18+ via generic status; new test `tests/test_audit_batch22_moves.py::AuditBatch22MoveTests::test_twineedle_poison_18`.
- Venom Drench :: MISSING/INCORRECT: stat drops not applied (poisoned targets not lowered) (fails `tests/test_audit_batch22_moves.py::AuditBatch22MoveTests::test_venom_drench_lowers_poisoned_stats`).
- Volt Tackle :: Verified paralyze on 19+ via generic status; new test `tests/test_audit_batch22_moves.py::AuditBatch22MoveTests::test_volt_tackle_paralyze_19`.
- Water Shuriken :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Water Shuriken [SM] :: Verified Five Strike in range text; base strike handling via `auto_ptu/rules/move_traits.py`.
- Wave Crash :: Verified recoil from range text; new test `tests/test_audit_batch22_moves.py::AuditBatch22MoveTests::test_wave_crash_recoil`.

## Batch 23 (Moves 221-230)
- Wild Charge :: Verified recoil from range text; new test `tests/test_audit_batch23_moves.py::AuditBatch23MoveTests::test_wild_charge_recoil`.
- Wish :: Verified delayed heal (2 stages) via handler; new test `tests/test_audit_batch23_moves.py::AuditBatch23MoveTests::test_wish_applies_delayed_heal`.
- Wood Hammer :: Verified recoil from range text; new test `tests/test_audit_batch23_moves.py::AuditBatch23MoveTests::test_wood_hammer_recoil`.
- Yawn :: MISSING/INCORRECT: does not apply Drowsy status (target never becomes Drowsy) (fails `tests/test_audit_batch23_moves.py::AuditBatch23MoveTests::test_yawn_applies_drowsy`).

## Batch 24 (Abilities 1-10)
- Abominable :: Verified recoil immunity and massive damage injury suppression; new tests `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_abominable_blocks_recoil`, `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_abominable_blocks_massive_damage_injury`.
- Accelerate :: Verified ability action readies damage bonus and consumes on STAB attack; new test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_accelerate_adds_priority_damage_bonus`.
- Adaptability :: Verified +1 DB on STAB; new test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_adaptability_adds_db_to_stab`.
- Aftermath :: MISSING/INCORRECT: burst damage uses 1 tick (1/10) instead of 1/4 max HP (fails `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_aftermath_deals_quarter_max_hp`).
- Ambush :: Verified flinch on light melee strike; new test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_ambush_flinches_on_light_melee`.
- Anchored :: Verified anchor token granted on init; test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_anchored_places_anchor_token`.
- Aqua Bullet :: Verified pre-attack shift on Water move; new test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_aqua_bullet_shifts_before_water_move`.
- Arena Trap :: Verified Slowed on nearby foes at round start; new test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_arena_trap_slows_nearby_foes`.
- Aroma Veil :: Verified confusion block in 3m aura; new test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_aroma_veil_blocks_confusion`.
- Aura Break :: Verified suppression of Adaptability damage boost; new test `tests/test_audit_batch24_abilities.py::AuditBatch24AbilityTests::test_aura_break_suppresses_adaptability`.

## Batch 25 (Abilities 11-20)
- Aura Storm :: Verified injury-scaled damage bonus on Aura keyword moves; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_aura_storm_adds_injury_scaled_bonus`.
- Bad Dreams :: Verified command-phase tick damage to sleeping targets; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_bad_dreams_ticks_sleeping_targets`.
- Ball Fetch :: Verified shift toward newly switched-in combatant; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_ball_fetch_shifts_on_switch_in`.
- Battery :: Verified ability action applies temporary boost to next special attack; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_battery_boosts_next_special_attack`.
- Beast Boost :: Verified highest stat +1 after KO; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_beast_boost_raises_highest_stat_on_ko`.
- Beautiful :: Verified adjacent enraged target is calmed at start phase; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_beautiful_clears_enraged_adjacent`.
- Berserk :: Verified Special Attack +1 when dropping below half HP; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_berserk_triggers_below_half_hp`.
- Blow Away :: Verified Whirlwind tick damage on hit; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_blow_away_whirlwind_tick`.
- Bodyguard :: Verified intercept + damage resist when adjacent; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_bodyguard_intercepts_and_halves_damage`.
- Bone Lord :: Verified Bone Club flinch on hit; new test `tests/test_audit_batch25_abilities.py::AuditBatch25AbilityTests::test_bone_lord_bone_club_flinch`.

## Batch 26 (Abilities 21-30)
- Bone Wielder :: Verified accuracy bonus on bone moves with Thick Club; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_bone_wielder_thick_club_accuracy_bonus`.
- Brimstone :: Verified Poisoned added when Fire burn applies; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_brimstone_adds_poison_on_fire_burn`.
- Celebrate :: Verified Speed +1 after KO; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_celebrate_triggers_after_ko`.
- Chemical Romance :: Verified Infatuated applied on qualifying poison status hit; test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_chemical_romance_infatuates_male_target`.
- Chilling Neigh :: Verified Attack +1 on KO and nearby foes get evasion penalty; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_chilling_neigh_raises_attack_and_chills_nearby`.
- Chlorophyll :: Verified +2 Overland in Sun; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_chlorophyll_adds_overland_in_sun`.
- Clay Cannons :: Verified ranged origin shift after ability action; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_clay_cannons_origin_shift_for_ranged`.
- Comatose :: Verified Sleep applied and tick heal; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_comatose_sleep_and_heal`.
- Combo Striker :: Verified Struggle follow-up on roll 10; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_combo_striker_triggers_struggle_followup`.
- Corrosion :: Verified Toxic applies to Steel-type target; new test `tests/test_audit_batch26_abilities.py::AuditBatch26AbilityTests::test_corrosion_allows_toxic_on_steel`.

## Batch 27 (Abilities 31-40)
- Cotton Down :: Verified adjacent targets get -1 Speed CS and Slowed after defender hit; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_cotton_down_slows_adjacent`.
- Curious Medicine :: Verified switch-in resets allied combat stages within 2; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_curious_medicine_resets_allies_on_switch`.
- Damp :: Verified Explosion blocked within radius; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_damp_blocks_explosion`.
- Dancer :: Verified copies dance move and applies additional stat drop; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_dancer_copies_dance_move`.
- Dauntless Shield :: Verified +1 Defense on init; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_dauntless_shield_grants_defense_stage`.
- Dazzling :: Verified priority suppression and initiative penalty from ability action; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_dazzling_blocks_priority`.
- Defeatist :: Verified CS shifts below 50% HP; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_defeatist_applies_below_half`.
- Defy Death :: Verified injuries reduced by 2 via ability action; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_defy_death_heals_injuries`.
- Desert Weather :: Verified Fire damage halved in sun; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_desert_weather_reduces_fire_damage_in_sun`.
- Designer :: Verified Fashion Designer crafts item from choice; new test `tests/test_audit_batch27_abilities.py::AuditBatch27AbilityTests::test_designer_fashion_designer_crafts_item`.

## Batch 28 (Abilities 41-50)
- Disguise :: Verified first hit nullified and +1 Defense CS; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_disguise_blocks_first_hit`.
- Download :: Verified ability action applies damage bonus vs weaker defense; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_download_adds_damage_bonus_against_weaker_defense`.
- Dream Smoke :: Verified melee attacker is put to Sleep; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_dream_smoke_puts_attacker_to_sleep`.
- Dreamspinner :: Verified heals per sleeping foe within 10m; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_dreamspinner_heals_per_sleeping_foe`.
- Drizzle :: Verified weather set to Rain; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_drizzle_sets_rain`.
- Drought :: Verified weather set to Sunny; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_drought_sets_sun`.
- Drown Out :: Verified Sonic moves are blocked; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_drown_out_blocks_sonic_move`.
- Dust Cloud :: Verified powder move expands to Burst 1; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_dust_cloud_expands_powder_move`.
- Early Bird :: Verified +3 save bonus on init; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_early_bird_grants_save_bonus`.
- Eggscellence :: Verified type effectiveness boosts on high roll; new test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_eggscellence_boosts_effectiveness_on_high_roll`.

## Batch 29 (Abilities 51-60)
- Electrodash :: Verified Sprint temporary effect granted; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_electrodash_grants_sprint`.
- Emergency Exit :: Verified forced switch when dropping below half HP; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_emergency_exit_switches_below_half`.
- Filter :: Verified super-effective damage reduction; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_filter_reduces_super_effective_damage`.
- Flare Boost :: Verified +2 Special Attack stages when burned; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_flare_boost_raises_special_attack_when_burned`.
- Flare Boost [Errata] :: Verified scene action grants +3 Attack and +3 Special Attack while burned; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_flare_boost_errata_grants_attack_boosts`.
- Flash Fire :: Verified Fire immunity and subsequent damage bonus event; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_flash_fire_absorbs_and_boosts`.
- Flash Fire [Errata] :: Verified Fire immunity with +1 CS boost; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_flash_fire_errata_absorbs_and_boosts`.
  - Flavorful Aroma :: Verified Aromatic Mist buffs ally accuracy and damage; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_flavorful_aroma_buffs_ally`.
- Flower Gift :: Verified ally ATK/SPD boosts in sun; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_flower_gift_boosts_allies_in_sun`.
- Flower Gift [Errata] :: Verified sun/low-HP stat boosts for user and nearby allies; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_flower_gift_errata_boosts_user_and_allies`.
- Flower Power :: Verified Grass move category swap; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_flower_power_swaps_grass_move_category`.
- Flower Power [Errata] :: Verified Grass move category swap for errata variant; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_flower_power_errata_swaps_grass_category`.
- Flower Veil :: Verified stat drops blocked for Grass ally; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_flower_veil_blocks_stat_drop`.
- Flower Veil [Errata] :: Verified 5-meter Grass stat-drop block; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_flower_veil_errata_blocks_within_five`.
  - Fox Fire :: Verified fox fire interrupt triggers; new test `tests/test_audit_batch29_abilities.py::AuditBatch29AbilityTests::test_fox_fire_triggers_interrupt`.
  - Fox Fire [Errata] :: Verified Ember follow-up and wisp consumption; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_fox_fire_errata_triggers_ember_followup`.

## Batch 30 (Abilities 61-70)
- Frisk :: Verified details revealed (types/abilities/items) via ability action; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_frisk_reveals_target_details`.
- Frisk [Feb Errata] :: Verified adjacent reveal action; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_frisk_feb_errata_reveals_target`.
- Frisk [SuMo Errata] :: Verified adjacent accuracy bonus; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_frisk_sumo_errata_adjacent_accuracy_bonus`.
- Full Guard :: Verified next-hit damage reduction when temp HP present; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_full_guard_reduces_next_hit`.
- Gale Wings :: Verified Flying move priority event; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_gale_wings_grants_flying_priority`.
- Gale Wings [Errata] :: Verified priority ready + half-Speed damage bonus; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_gale_wings_errata_priority_and_bonus`.
- Giver :: Verified Present roll forced to DB 10 (with STAB effective DB 12); new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_giver_forces_present_roll`.
- Gluttony :: Verified up to 3 food buffs allowed; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_gluttony_allows_multiple_food_buffs`.
- Gluttony [Errata] :: Verified three food buff uses per scene; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_gluttony_errata_food_buff_limit`.
- Gore :: Verified Horn Attack push and crit-range extension; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_gore_extends_crit_and_pushes`.
- Gore [Errata] :: Verified Horn Attack double strike and 2m push; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_gore_errata_double_strike_and_push`.
- Gorilla Tactics :: Verified lock activation and damage bonus; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_gorilla_tactics_locks_moves_and_boosts_damage`.
- Grass Pelt :: Verified damage reduction on grassy terrain; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_grass_pelt_reduces_damage_on_grass`.
- Grass Pelt [Errata] :: Verified swift temp HP and rough-grass damage reduction; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_grass_pelt_errata_grants_temp_hp`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_grass_pelt_errata_reduces_damage_on_rough_grass`.
- Grim Neigh :: Verified Special Attack +1 on KO and nearby accuracy penalty; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_grim_neigh_raises_spatk_and_penalizes_foes`.
- Gulp Missile :: Verified retaliation after Stockpile setup; new test `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_gulp_missile_retaliates_after_damage`.

## Batch 31 (Abilities 71-80)
- Handyman :: Verified Delivery Bird item index selection with handyman_choice; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_handyman_selects_item_index`.
- Heatproof :: Verified Fire damage halved; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_heatproof_halves_fire_damage`.
- Heatproof [Errata] :: Verified fire resistance shift and burn immunity; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_heatproof_errata_resists_fire`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_heatproof_errata_blocks_burn_damage`.
- Heavy Metal :: Verified +2 weight class; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_heavy_metal_increases_weight_class`.
- Heavy Metal [Errata] :: Verified defense/speed base adjustments and weight class; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_heavy_metal_errata_adjusts_defense_and_speed`.
- Heliovolt :: Verified evasion bonus and active flag; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_heliovolt_grants_evasion_bonus`.
- Honey Paws :: Verified Honey converts to food buff; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_honey_paws_turns_honey_into_food_buff`.
- Honey Paws [Errata] :: Verified Honey ignores food buff limit; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_honey_paws_errata_ignores_food_buff_limit`.
- Horde Break :: Verified statuses cured when Schooling breaks; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_horde_break_cures_all_statuses`.
- Huge Power :: Verified Attack doubled; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_huge_power_doubles_attack`.
- Hunger Switch :: Verified full belly accuracy bonus and hangry damage bonus; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_hunger_switch_full_belly_accuracy_bonus`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_hunger_switch_hangry_damage_bonus`.
- Huge Power / Pure Power [Errata] :: Verified base-attack bonus scaling with level; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_huge_power_errata_adds_base_attack`.
- Hustle :: Verified accuracy penalty on physical moves; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_hustle_lowers_accuracy`.
- Hustle [Errata] :: Verified accuracy penalty and damage bonus for all moves; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_hustle_errata_penalizes_all_accuracy`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_hustle_errata_boosts_all_damage`.
- Hydration :: Verified end-phase cure in rain; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_hydration_cures_in_rain`.
- Hydration [Errata] :: Verified swift status cure action; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_hydration_errata_cures_status`.
- Ice Body :: Verified start-phase heal in hail; new test `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_ice_body_heals_in_hail`.
- Ice Body [Errata] :: Verified heal on low HP or hail; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_ice_body_errata_heals_under_half`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_ice_body_errata_heals_in_hail`.

## Batch 32 (Abilities 81-90)
- Ice Face :: Verified hail ability action grants two ticks of temp HP; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_ice_face_grants_temp_hp_in_hail`.
- Imposter :: Verified on-switch copies combat stages and entrains target ability; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_imposter_copies_stages_and_ability_on_switch`.
- Innards Out :: Verified resist hook and 2x retaliation damage; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_innards_out_resists_and_retaliates`.
- Inner Focus :: Verified flinch immunity temp effect on init; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_inner_focus_grants_flinch_immunity`.
- Interference :: Verified accuracy penalty applied and enforced; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_interference_applies_accuracy_penalty`.
- Intimidate :: Verified adjacent Attack -1 on switch; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_intimidate_lowers_adjacent_on_switch`.
- Intrepid Sword :: Verified Attack +1 on init; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_intrepid_sword_raises_attack_on_init`.
- Juicy Energy :: Verified Berry Juice healing scales to level; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_juicy_energy_uses_level_for_berry_juice`.
- Justified :: Verified Attack +1 after taking Dark damage; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_justified_raises_attack_after_dark_hit`.
- Kampfgeist :: Verified Fighting move gains +2 DB STAB; new test `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_kampfgeist_grants_fighting_stab`.

## Batch 33 (Abilities 91-100)
- Leaf Guard :: Verified status blocked in sun; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_leaf_guard_blocks_status_in_sun`.
- Leaf Rush :: Verified priority Grass strike adds damage bonus; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_leaf_rush_grants_priority_and_damage_bonus`.
- Leafy Cloak :: Verified grants chosen abilities; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_leafy_cloak_grants_chosen_abilities`.
- Life Force :: Verified ability action heals a tick; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_life_force_heals_tick`.
- Light Metal :: Verified weight class reduced by 2; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_light_metal_reduces_weight_class`.
- Lightning Kicks :: Verified next kick gets priority event; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_lightning_kicks_grants_kick_priority`.
- Lightning Rod :: Verified redirect and absorb with Sp. Atk boost; test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_lightning_rod_redirects_and_absorbs`.
- Line Charge :: Verified diagonal shift blocked; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_line_charge_blocks_diagonal_shift`.
- Liquid Ooze :: Verified drain reversal damages attacker; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_liquid_ooze_reverses_drain`.
- Lunchbox :: Verified temp HP gained on food buff; new test `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_lunchbox_grants_temp_hp_on_food_buff`.

## Batch 34 (Abilities 101-110)
- Maelstrom Pulse :: Verified priority Water strike adds damage bonus; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_maelstrom_pulse_grants_priority_and_damage_bonus`.
- Magma Armor :: Verified freeze blocked; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_magma_armor_blocks_freeze`.
- Magnet Pull :: Verified Steel targets restricted; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_magnet_pull_restricts_steel_targets`.
- Mega Launcher :: Verified pulse move DB +2; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_mega_launcher_boosts_pulse_moves`.
- Memory Wipe :: Verified disables last move when recorded; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_memory_wipe_disables_last_move`.
- Migraine :: Verified Telekinetic capability granted below half HP; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_migraine_grants_telekinetic_below_half_hp`.
- Mimicry :: Verified type change based on weather; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_mimicry_changes_type_based_on_weather`.
- Missile Launch :: Verified Dreepy tokens deployed; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_missile_launch_deploys_tokens`.
- Moody :: Verified +2/-2 random CS adjustments; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_moody_adjusts_two_stats`.
- Mud Shield :: Verified temp HP and muddy terrain damage reduction; new test `tests/test_audit_batch34_abilities.py::AuditBatch34AbilityTests::test_mud_shield_grants_temp_hp_and_reduction`.

## Batch 35 (Abilities 111-120)
- Parental Bond :: Verified extra hit log plus baby companion rules (spawn, leash, enrage); tests `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_parental_bond_adds_extra_damage`, `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_parental_bond_spawns_baby_and_allows_action`, `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_parental_bond_baby_leash_blocks_far_shift`, `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_parental_bond_mother_enrages_on_baby_faint`.
- Perception :: Verified shift out of area attacks; new test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_perception_shifts_out_of_burst`.
- Perish Body :: Verified Perish Song applied on melee hit; new test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_perish_body_applies_perish_song`.
- Permafrost :: Verified super-effective damage reduced; new test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_permafrost_reduces_super_effective_damage`.
- Photosynthesis :: Verified start-phase healing in sun; test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_photosynthesis_heals_in_sun`.
- Plus :: Verified Gear Up boosts Plus ally stats and Plus action boosts Minus; tests `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_plus_boosts_gear_up`, `tests/test_battle_state.py::test_plus_boosts_minus_user_special_attack`.
- Plus [SwSh] :: Verified extra stat raise for allies within 10m; test `tests/test_battle_state.py::test_plus_swsh_intensifies_stat_raise`.
- Poltergeist :: Verified item-based tick damage at start; test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_poltergeist_damages_with_items`.
- Polycephaly :: Verified Struggle resolves as Swift action; new test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_polycephaly_makes_struggle_swift`.
- Power Construct :: Verified temp HP lock + form change event; new test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_power_construct_grants_temp_hp_and_form`.
- Power of Alchemy :: Verified copied ability granted; new test `tests/test_audit_batch35_abilities.py::AuditBatch35AbilityTests::test_power_of_alchemy_copies_ability`.

## Batch 36 (Abilities 121-130)
- Power Spot :: Verified +5 damage to nearby allies; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_power_spot_boosts_ally_damage`.
- Prankster :: Verified status move priority raised via deepcopy spy; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_prankster_grants_status_priority`.
- Pressure :: Verified extra frequency usage count and pressure event; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_pressure_increases_frequency_usage`.
- Pride :: Verified +2 Special Attack when afflicted; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_pride_raises_spatk_when_afflicted`.
- Prime Fury [Errata] :: Verified +1 Atk/SpAtk and Enraged; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_prime_fury_errata_raises_atk_and_spatk`.
- Propeller Tail :: Verified Sprint/no-intercept/target lock; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_propeller_tail_grants_sprint_and_lock`.
- Psionic Screech :: Verified Psychic conversion and flinch; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_psionic_screech_converts_and_flinches`.
- Pumpkingrab :: Verified grapple contest bonus; test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_pumpkingrab_bonus_grapple_contest`.
- Pumpkingrab [Errata] :: Verified grapple and vulnerable statuses applied; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_pumpkingrab_errata_grapples`.
- Pure Blooded :: Verified +5 damage at low HP for Dragon moves; new test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_pure_blooded_boosts_dragon_damage_low_hp`.
- Pure Power :: Verified doubled Attack damage; test `tests/test_battle_state.py::test_pure_power_doubles_attack_damage`.

## Batch 37 (Abilities 131-141)
- Ragelope :: Verified enrage and Speed/Attack boost on high roll; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_ragelope_enrages_and_boosts`.
- Rain Dish :: Verified start-phase heal in rain; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_rain_dish_heals_in_rain`.
- Rain Dish [Errata] :: Verified action heal below half HP; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_rain_dish_errata_requires_action`.
- Rally :: Verified ally shift away from foes; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_rally_shifts_ally`.
- Rally [Errata] :: Verified ally disengage; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_rally_errata_disengages`.
- Rattled [Errata] :: Verified Speed +1 after Dark hit; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_rattled_errata_raises_speed_on_dark_hit`.
- Razor Edge :: Verified crit range reduced via move clone; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_razor_edge_increases_crit_range`.
- Receiver :: Verified granted ability on ally faint; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_receiver_copies_ally_ability_on_faint`.
- Reckless :: Verified increased damage on recoil moves; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_reckless_increases_damage_for_recoil_move`.
- Regal Challenge :: Verified Speed -1 and Slowed on hit; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_regal_challenge_slows_on_hit`.
- Regal Challenge [Errata] :: Verified deference consumes Shift and stage drop; new test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_regal_challenge_errata_deference`.

## Batch 38 (Abilities 142-151)
- Run Away :: Verified blocks Slowed status; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_run_away_blocks_slowed`.
- Run Away [Errata] :: Verified blocks Slowed status; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_run_away_errata_blocks_slowed`.
- Run Up :: Verified straight-line shift adds melee damage; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_run_up_adds_damage_after_shift`.
- Sacred Bell :: Verified Dark damage resisted; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sacred_bell_reduces_dark_damage`.
- Sand Force :: Verified +5 damage in sand for Rock moves; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_force_adds_damage_in_sand`.
- Sand Force [Errata] :: Verified +5 damage in sand; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_force_errata_adds_damage_in_sand`.
- Sand Rush :: Verified Speed +4 in sand; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_rush_raises_speed_in_sand`.
- Sand Rush [Errata] :: Verified Speed +4 in sand; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_rush_errata_raises_speed_in_sand`.
- Sand Spit :: Verified Sand Attack counter on hit; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_spit_counters`.
- Sand Stream :: Verified sandstorm weather set; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_stream_summons_weather`.
- Sand Stream [Errata] :: Verified sandstorm + immunity; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_stream_errata_summons_weather_and_immunity`.
- Sand Veil :: Verified evasion bonus + sand immunity (adjacent ally) in sand; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sand_veil_grants_evasion_and_immunity`.
- Sap Sipper :: Verified Grass absorb + Attack boost; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_sap_sipper_absorbs_grass_and_boosts_attack`.
- Scrappy :: Verified Normal hits Ghost targets; new test `tests/test_audit_batch38_abilities.py::AuditBatch38AbilityTests::test_scrappy_allows_normal_to_hit_ghosts`.

## Batch 39 (Abilities 152-161)
- Sequence :: Verified damage bonus with adjacent matching-type allies; test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_sequence_boosts_damage_with_adjacent_allies`.
- Sequence [Errata] :: Verified +3 damage per adjacent matching-type ally; test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_sequence_errata_adds_flat_damage_per_adjacent_ally`.
- Serene Grace :: Verified +2 effect range applies to status roll; new test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_serene_grace_boosts_effect_roll`.
- Serpent's Mark :: Verified pattern roll grants abilities; new test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_serpents_mark_grants_pattern_abilities`.
- Serpent's Mark [Errata] :: Verified pattern roll grants abilities; new test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_serpents_mark_errata_grants_pattern_abilities`.
- Shackle [Errata] :: Verified foes in Burst 3 get movement halved; new test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_shackle_errata_halves_foe_movement_in_burst`.
- Shadow Shield :: Verified reduced damage at full HP; new test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_shadow_shield_reduces_damage_at_full_hp`.
- Sheer Force :: Verified damage boost on moves with effects text; new test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_sheer_force_boosts_moves_with_effects`.
- Sheer Force [Errata] :: Verified damage boost on moves with effects text; new test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_sheer_force_errata_boosts_moves_with_effects`.
- Shell Armor :: Verified critical hits negated; test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_shell_armor_blocks_critical_hits`.

## Batch 40 (Abilities 162-171)
- Shell Shield [Errata] :: Verified ready + damage reduction effects; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_shell_shield_errata_readies_withdraw_and_reduction`.
- Shield Dust :: Verified blocks post-damage effects on non-status moves; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_shield_dust_blocks_post_damage_effects`.
- Shields Down :: Verified core form shift at <= 1/2 HP; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_shields_down_switches_to_core_form`.
- Silk Threads :: Verified String Shot inflicts Slowed; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_silk_threads_slows_on_string_shot`.
- Silk Threads [Errata] :: Verified String Shot inflicts Slowed; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_silk_threads_errata_slows_on_string_shot`.
- Simple :: Verified combat stage changes doubled; test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_simple_doubles_combat_stage_changes`.
- Slow Start :: Verified stat scalars + damage reduction applied early; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_slow_start_applies_stat_scalars`.
- Slush Rush :: Verified doubled initiative speed in hail; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_slush_rush_doubles_speed_in_hail`.
- Sniper :: Verified critical damage boost; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_sniper_boosts_critical_damage`.
- Sniper [Errata] :: Verified critical damage boost; new test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_sniper_errata_boosts_critical_damage`.

## Batch 41 (Abilities 172-181)
- Snow Cloak :: Verified evasion bonus + hail immunity; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_snow_cloak_adds_evasion_bonus_in_hail`.
- Snow Cloak [Errata] :: Verified evasion bonus in hail; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_snow_cloak_errata_adds_evasion_bonus_in_hail`.
- Snow Warning :: Verified hail weather set; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_snow_warning_sets_hail`.
- Snuggle :: Verified temp HP granted to user and target; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_snuggle_grants_temp_hp_to_both`.
- Sol Veil :: Verified accuracy penalty logged in sun; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_sol_veil_adds_accuracy_penalty`.
- Solar Power :: Verified +2 SpAtk and sun drain; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_solar_power_boosts_spatk_and_drains_hp_in_sun`.
- Solar Power [Errata] :: Verified ready + damage bonus; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_solar_power_errata_ready_and_bonus_damage`.
- Solid Rock :: Verified reduced super-effective damage; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_solid_rock_reduces_super_effective_damage`.
- Solid Rock [Errata] :: Verified reduced super-effective damage; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_solid_rock_errata_reduces_super_effective_damage`.
- Sonic Courtship [Errata] :: Verified Attract burst infatuates multiple foes; new test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_sonic_courtship_errata_expands_attract`.
- Soothing Tone :: PASS - start-phase evasion bonus implemented; test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_soothing_tone_adds_evasion_bonus`.

## Batch 42 (Abilities 182-191)
- Soothing Tone [Errata] :: PASS - Heal Bell ally tick-heal logged; test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_soothing_tone_errata_heals_on_heal_bell`.
- Sorcery :: Verified SpAtk stat modifier added on init; new test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_sorcery_adds_special_attack_bonus`.
- Soul Heart :: Verified SpAtk +2 on ally faint; new test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_soul_heart_triggers_on_faint`.
- Soulstealer [Errata] :: PASS - heal on hit applied; test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_soulstealer_errata_heals_on_hit`.
- Sound Lance [Errata] :: Verified Supersonic damage on miss; new test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_sound_lance_errata_deals_damage_on_miss`.
- Speed Boost :: PASS - end-phase Speed +1 CS; test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_speed_boost_increases_speed_stage`.
- Spike Shot :: Verified melee move becomes range 8; new test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_spike_shot_extends_melee_range`.
- Spiteful Intervention :: Verified disables attacker last move; new test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_spiteful_intervention_disables_attacker_move`.
- Splendorous Rider :: Verified borrowed mount move added; new test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_splendorous_rider_borrows_mount_move`.

## Batch 43 (Abilities 192-201)
- Sprint :: Verified Sprint temp effect applied; new test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_sprint_grants_sprint_effect`.
- Sprint [Errata] :: PASS - Sprint temp effect applied; test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_sprint_errata_grants_sprint_effect`.
- Stakeout :: Verified damage bonus vs newcomer; new test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_stakeout_adds_damage_against_newcomer`.
- Stall :: Verified priority override helper; test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_stall_reduces_priority`.
- Stalwart :: Verified stat boosts after damage; new test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_stalwart_raises_stats_after_damage`.
- Stance Change :: PASS - stance switch triggers on attack; test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_stance_change_switches_on_attack`.
- Starlight :: Verified luminous confuses on hit; new test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_starlight_confuses_on_luminous_hit`.
- Starlight [Errata] :: Verified defensive buff after expending luminous; new test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_starlight_errata_grants_defensive_buff`.
- Starswirl :: Verified hazard clear; new test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_starswirl_cleans_hazards`.
- Starswirl [Errata] :: PASS - hazards cleared and status cured; test `tests/test_audit_batch43_abilities.py::AuditBatch43AbilityTests::test_starswirl_errata_cleans_hazards_and_cures`.

## Batch 44 (Abilities 202-231)
- Steadfast [Errata] :: Verified Speed +1 and initiative penalty on flinch; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_steadfast_errata_raises_speed_on_flinch`.
- Steam Engine :: Verified evasion bonus on Fire hit; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_steam_engine_grants_evasion_on_fire_hit`.
- Steelworker :: Verified Steel STAB while anchored; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_steelworker_adds_stab_when_anchored`.
- Stench :: Verified boosted flinch roll applies; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_stench_adds_flinch_chance`.
- Stench [Errata] :: Verified boosted flinch roll applies; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_stench_errata_adds_flinch_chance`.
- Sticky Hold :: Verified blocks item theft; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sticky_hold_blocks_theft`.
- Own Tempo :: Verified confusion immunity in `_apply_status`; test `tests/test_battle_state.py::test_own_tempo_blocks_confusion`.
- Storm Drain [Errata] :: Verified absorb + SpAtk +1; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_storm_drain_errata_absorbs_water`.
- Strong Jaw :: Verified +2 DB on bite-family moves; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_strong_jaw_boosts_bite_damage`.
- Sturdy [Errata] :: Verified survives full-HP KO at 1 HP; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sturdy_errata_prevents_full_hp_ko`.
- Suction Cups :: Verified blocks push; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_suction_cups_blocks_push`.
- Suction Cups [Errata] :: Verified blocks push; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_suction_cups_errata_blocks_push`.
- Sumo Stance :: Verified blocks push; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sumo_stance_blocks_push`.
- Sumo Stance [Errata] :: Verified ready + shove on melee hit; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sumo_stance_errata_shoves_on_melee_hit`.
- Sun Blanket [Errata] :: Verified tick heal at low HP; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sun_blanket_errata_heals_when_low`.
- Sunglow :: Verified Radiant in sun; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sunglow_grants_radiant_in_sun`.
- Sunglow [Errata] :: Verified Radiant in sun; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sunglow_errata_grants_radiant_in_sun`.
- Super Luck :: Verified crit range bonus effect; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_super_luck_adds_crit_range_bonus`.
- Surge Surfer :: Verified doubled initiative in Electric terrain; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_surge_surfer_doubles_speed_in_electric_terrain`.
- Sway :: Verified melee redirect; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sway_redirects_melee_attack`.
- Swift Swim [Errata] :: Verified doubled swim speed in rain; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_swift_swim_errata_doubles_swim_speed`.
- Symbiosis :: Verified item transferred; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_symbiosis_transfers_item`.
- Symbiosis [Errata] :: Verified shared item granted; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_symbiosis_errata_shares_item`.
- Synchronize :: Verified status reflected; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_synchronize_passes_status`.
- Tangled Feet :: Verified evasion boost while confused; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_tangled_feet_increases_evasion_when_confused`.
- Tangled Feet [Errata] :: Verified evasion boost while confused; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_tangled_feet_errata_increases_evasion_when_confused`.
- Tangling Hair :: Verified Speed drop + Slowed on melee hit; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_tangling_hair_slows_melee_attacker`.
- Targeting System :: Verified Lock-On Swift ready; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_targeting_system_readies_lock_on`.
- Teamwork :: Verified melee accuracy bonus; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_teamwork_boosts_melee_accuracy`.
- Telepathy :: Verified shift out of ally area attack; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_telepathy_shifts_out_of_ally_area`.
- Telepathy [Errata] :: Verified shift out of ally area attack; new test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_telepathy_errata_shifts_out_of_ally_area`.

## Batch 45 (Abilities 232-261)
- Teravolt :: Verified Neutralized temp effect on hit; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_teravolt_suppresses_defender`.
- Teravolt [Errata] :: Verified Neutralized temp effect on hit; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_teravolt_errata_suppresses_defender`.
- Quick Feet :: Verified Speed +2 CS while afflicted and paralysis penalty ignored; test `tests/test_battle_state.py::test_quick_feet_boosts_speed_and_ignores_paralysis`.
- Regenerator :: Verified switch-out heal; test `tests/test_battle_state.py::test_regenerator_heals_on_switch`.
- Rivalry :: Verified same-gender damage bonus; test `tests/test_battle_state.py::test_rivalry_boosts_damage_against_same_gender`.
- Rocket :: Verified initiative boost next round; test `tests/test_battle_state.py::test_rocket_grants_first_initiative_next_round`.
- Thermosensitive :: Verified +2 Atk/SpAtk in sun at phase start; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_thermosensitive_boosts_attack_in_sun`.
- Thrust :: Verified push on physical melee hit; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_thrust_adds_push_to_melee_hit`.
- Thunder Boost :: Verified Electric aura damage bonus; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_thunder_boost_increases_damage_for_adjacent_ally`.
- Tingle :: Verified damage penalty temp effect on melee hit; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_tingle_applies_damage_penalty`.
- Tingly Tongue :: Verified Lick paralyzes on effect roll; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_tingly_tongue_paralyzes_with_lick`.
- Tinted Lens :: Verified increased damage vs resisted targets; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_tinted_lens_increases_resisted_damage`.
- Tochukaso :: Verified Bug resistance; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_tochukaso_resists_bug_damage`.
- Tolerance :: PASS - resisted damage reduced further; test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_tolerance_further_resists_types`.
- Tonguelash :: Verified Lick paralyzes and flinches on effect roll; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_tonguelash_lick_paralyzes_and_flinches`.
- Toxic Boost :: Verified +2 Atk when poisoned at phase start; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_toxic_boost_raises_attack_when_poisoned`.
- Toxic Boost [Errata] :: Verified +3 Atk/SpAtk via ability action while poisoned; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_toxic_boost_errata_raises_atk_and_spatk`.
- Toxic Nourishment :: Verified cures poison and grants temp HP; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_toxic_nourishment_cures_poison_and_grants_temp_hp`.
- Trace :: Verified Entrainment temp ability set; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_trace_copies_target_ability`.
- Transporter :: Verified Teleport logs ability activation; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_transporter_empowers_teleport`.
- Transporter [Errata] :: Verified Teleport logs ability activation; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_transporter_errata_requires_ready_then_teleport`.
- Triage :: Verified Healing move priority bonus; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_triage_increases_healing_priority`.
- Trinity :: Verified Tri Attack inflicts Frozen at effect roll 17; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_trinity_tri_attack_freezes_on_17`.
- Truant :: PASS - standard action skip recorded; test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_truant_can_skip_standard_action`.
- Turboblaze :: Verified Neutralized temp effect on hit; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_turboblaze_suppresses_defender`.
- Turboblaze [Errata] :: Verified Neutralized temp effect on hit; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_turboblaze_errata_suppresses_defender`.
- Twisted Power :: Verified damage bonus on special moves; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_twisted_power_adds_damage`.
- Type Aura :: Verified adjacent aura damage bonus; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_type_aura_adds_damage`.
- Type Strategist :: Verified damage reduction after matching-type move; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_type_strategist_grants_damage_reduction`.
- Ugly :: Verified flinch on effect roll 19+; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_ugly_flinches_on_high_roll`.
- Unaware :: PASS - ignores positive defense stages; test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_unaware_ignores_positive_defense_stages`.
- Unbreakable :: Verified Steel move damage bonus at low HP; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_unbreakable_adds_damage_at_low_hp`.
- Vanguard :: Verified damage bonus before target acts; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_vanguard_adds_damage_before_target_acts`.
- Venom :: Verified Poison last-chance damage bonus; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_venom_last_chance_boosts_poison_damage`.
- Vicious :: Verified Hone Claws extra action; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_vicious_grants_extra_action_on_hone_claws`.
- Victory Star :: Verified ally accuracy bonus; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_victory_star_boosts_ally_accuracy`.
- Vigor :: Verified heal tick after Endure; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_vigor_heals_after_endure`.
- Vital Spirit :: Verified sleep blocked; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_vital_spirit_blocks_sleep`.
- Unburden [Errata] :: Verified Speed CS +2 at phase start; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_unburden_errata_raises_speed_on_start`.
- Unnerve [Errata] :: Verified digestion blocked + unnerved temp effects via ability action; new test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_unnerve_errata_applies_statuses`.

## Batch 46 (Abilities 262-291)
- Whirlwind Kicks [Errata] :: Verified Rapid Spin becomes Burst 1 with priority; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_whirlwind_kicks_errata_burst_rapid_spin`.
- Windveiled [Errata] :: Verified Flying immunity and charged DB+1; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_windveiled_errata_blocks_flying_and_charges_bonus`.
- Zen Mode [Errata] :: PASS - Zen Mode activates and grants moves; test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_zen_mode_errata_activates_and_grants_moves`.
- Aqua Bullet :: Verified shift toward target; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_aqua_bullet_shifts_toward_target`.
- Designer :: PASS - ability action exposed; test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_designer_grants_ability_action`.
- Combo Striker :: Verified Struggle follow-up trigger; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_combo_striker_triggers_followup`.
- Dream Smoke :: Verified melee hit sleeps attacker; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_dream_smoke_puts_attacker_to_sleep`.
- Empower :: Verified Free Action override set; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_empower_readies_free_action`.
- Flower Power :: Verified Grass category swap; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_flower_power_swaps_grass_category`.
- Full Guard :: Verified ready effect applied; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_full_guard_sets_ready`.
- Giver :: PASS - Present roll override deterministic; test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_giver_forces_present_roll`.
- Heliovolt :: Verified evasion + heliovolt_active effects; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_heliovolt_adds_evasion_and_sunny_resonance`.
- Juicy Energy :: Verified Berry Juice heal uses level; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_juicy_energy_uses_level_heal`.
- Lancer :: Verified crit range bonus after charge distance; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_lancer_grants_crit_after_charge`.
- Leaf Rush :: Verified priority + damage bonus after ability action; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_leaf_rush_adds_priority_and_damage_bonus`.
- Leafy Cloak :: Verified granted abilities; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_leafy_cloak_grants_abilities`.
- Line Charge :: Verified diagonal shift blocked; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_line_charge_blocks_diagonal_shift`.
- Maestrom Pulse :: PASS - misspelling supported and damage bonus logged; test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_maestrom_pulse_adds_priority_and_damage_bonus`.
- Nimble Strikes :: Verified damage bonus; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_nimble_strikes_adds_damage`.
- Ragelope :: Verified Enraged + Speed CS on high roll; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_ragelope_enrages_on_high_roll`.
- Sacred Bell :: Verified Dark/Ghost resistance; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_sacred_bell_resists_dark`.
- Seasonal :: Verified seasonal ability grant; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_seasonal_grants_ability`.
- Snuggle :: Verified temp HP to both; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_snuggle_grants_temp_hp_to_both`.
- Sol Veil :: Verified evasion + DR in sun; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_sol_veil_grants_evasion_and_dr_in_sun`.
- Sorcery :: Verified Sp. Atk bonus; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_sorcery_adds_special_attack_bonus`.
- Spike Shot :: Verified melee range extended; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_spike_shot_extends_melee_range`.
- Tingle :: Verified tick damage + damage penalty; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_tingle_drains_tick_and_applies_penalty`.
- Tonguelash :: Verified paralysis + flinch on Lick; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_tonguelash_paralyzes_and_flinches`.
- Trinity :: Verified Frozen applied on first high roll; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_trinity_tri_attack_applies_frozen_first`.
- Type Aura :: Verified adjacent aura damage bonus; new test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_type_aura_adds_damage_bonus`.

## Batch 47 (Abilities 292-321)
- Weird Power :: Verified higher-stat bonus on off-type damage; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_weird_power_adds_higher_stat`.
- Accelerate :: Verified priority + damage bonus after ability action; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_accelerate_adds_priority_and_damage`.
- Anchored :: Verified anchor token granted; test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_anchored_grants_anchor_token`.
- Battery :: Verified charged ally special gains damage bonus (consumes on attempt); test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_battery_charges_ally_special`.
- Berserk :: Verified Sp. Atk +1 when below half HP after damage; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_berserk_triggers_below_half`.
- Beast Boost :: Verified highest stat +1 after KO; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_beast_boost_raises_highest_stat_on_ko`.
- Dancer :: Verified copies dance status move; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_dancer_copies_dance_move`.
- DIsguise :: Verified first hit blocked + Def +1 (handler uses Disguise); new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_disguise_blocks_first_hit`.
- Dazzling :: Verified priority suppression and initiative penalty; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_dazzling_suppresses_priority`.
- Chemical Romance :: Verified Infatuated applied on qualifying move; test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_chemical_romance_infatuates_male`.
- Comatose :: Verified Sleep + tick heal on ability action; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_comatose_sets_sleep_and_heals`.
- Corrosion :: Verified Toxic poisons Steel; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_corrosion_allows_toxic_on_steel`.
- Electric Surge :: Verified Electric Terrain set; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_electric_surge_sets_terrain`.
- Emergency Exit :: Verified switch at low HP; test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_emergency_exit_switches_out`.
- Fluffy :: Verified melee damage reduction; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_fluffy_reduces_melee_damage`.
- Full Metal Body :: Verified blocks foe stage drops; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_full_metal_body_blocks_stage_drop`.
- Galvanize :: Verified Normal -> Electric conversion (reduced vs Ground); new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_galvanize_converts_normal_to_electric`.
- Glisten :: Verified Fairy immunity + defensive CS; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_glisten_blocks_fairy_and_boosts_defense`.
- Grassy Surge :: Verified Grassy Terrain set; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_grassy_surge_sets_terrain`.
- Handyman :: Verified delivery item index selection; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_handyman_selects_item_index`.
- Horde Break :: Verified status cure on Schooling return; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_horde_break_cures_status_on_schooling_return`.
- Innards Out :: Verified retaliate after damage; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_innards_out_retaliates`.
- Liquid Voice :: Verified sonic status moves convert to damage; test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_liquid_voice_converts_sonic_status_to_damage`.
- Long Reach :: Verified melee range extended; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_long_reach_extends_range`.
- Merciless :: Verified attack_hits forces crit on poisoned targets; test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_merciless_forces_crit_on_poisoned`.
- Misty Surge :: Verified Misty Terrain set; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_misty_surge_sets_terrain`.
- Mud Shield :: Verified temp HP granted; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_mud_shield_grants_temp_hp`.
- Neuroforce :: Verified super-effective damage bonus; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_neuroforce_adds_damage_on_super_effective`.
- Power Construct :: Verified temp HP + form activation below half HP; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_power_construct_grants_temp_hp_below_half`.
- Power of Alchemy :: Verified ability copy; new test `tests/test_audit_batch47_abilities.py::AuditBatch47AbilityTests::test_power_of_alchemy_copies_ability`.

## Batch 48 (Abilities 350-372)
- Voodoo Doll :: Verified Curse spreads to an extra target; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_voodoo_doll_curses_additional_target`.
- Wallmaster :: Verified Barrier adds diagonal segments; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_wallmaster_adds_barrier_diagonals`.
- Wash Away :: Verified Water hits reset combat stages and clear coats; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_wash_away_resets_stages_and_clears_coats`.
- Wave Rider :: Verified Speed boost while in water tiles; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_wave_rider_boosts_speed_in_water`.
- Weak Armor :: Verified Defense drop and Speed rise on physical hit; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_weak_armor_shifts_defense_and_speed`.
- Weaponize :: Verified Living Weapon intercepts attacks; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_weaponize_intercepts_for_living_weapon`.
- Weeble :: Verified melee counterstrike for one-third damage; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_weeble_counters_melee_hit`.
- Whirlwind Kicks :: Verified Rapid Spin becomes Burst 1 with priority; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_whirlwind_kicks_turns_rapid_spin_into_burst`.
- Windveiled :: Verified Flying immunity and charged DB bonus; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_windveiled_blocks_flying_and_charges_bonus`.
- Winter's Kiss :: Verified Ice immunity/tick heal and Ice-move heal; new tests `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_winters_kiss_blocks_ice_and_heals` and `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_winters_kiss_heals_when_using_ice_moves`.
- Wishmaster :: Verified Wish resolves immediately with cure; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_wishmaster_cures_status_immediately`.
- Wistful Melody :: Verified Sing lowers Attack and Special Attack; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_wistful_melody_lowers_attack_and_spatk`.
- Wobble :: Verified damage reflection as Counter/Mirror Coat; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_wobble_reflects_damage`.
- Zen Mode :: Verified toggle below half HP; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_zen_mode_toggles_below_half_hp`.
- Needles :: Verified melee physical tick damage; new test `tests/test_audit_batch48_abilities.py::AuditBatch48AbilityTests::test_needles_adds_tick_damage`.
- Eggscellence :: Verified egg move power boost; existing test `tests/test_audit_batch28_abilities.py::AuditBatch28AbilityTests::test_eggscellence_boosts_effectiveness_on_high_roll`.

## Batch 49 (Abilities 373-382)
- Abominable [Errata] :: Verified +5 base HP and recoil immunity; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_abominable_errata_increases_max_hp_and_blocks_recoil`.
- Adaptability [Errata] :: Verified +1d10 STAB damage bonus; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_adaptability_errata_adds_d10_to_stab_damage`.
- Aftermath [Errata] :: Verified Burst 1 tick damage on faint; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_aftermath_errata_bursts_for_three_ticks`.
- Ambush [Errata] :: Verified priority-ready + flinch and accuracy penalty; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_ambush_errata_flutches_and_penalizes_accuracy`.
- Arena Trap [Errata] :: Verified activation toggles Slowed/Trapped aura; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_arena_trap_errata_slows_and_traps`.
- Aroma Veil [Errata] :: Verified adjacent-only confusion/rage/suppression block; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_aroma_veil_errata_blocks_adjacent_only`.
- Aura Break [Errata] :: Verified damage bonus inversion applied to chosen ability; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_aura_break_errata_inverts_adaptability`.
- Aura Storm [Errata] :: Verified +3 damage per injury; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_aura_storm_errata_scales_with_injuries`.
- Bad Dreams [Errata] :: Verified sleeping-target tick drain + temp HP; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_bad_dreams_errata_drains_sleeping_targets`.
- Beautiful [Errata] :: Verified +1 Sp. Atk CS and Enraged cure; new test `tests/test_audit_batch49_abilities.py::AuditBatch49AbilityTests::test_beautiful_errata_boosts_spatk_and_cures_enraged`.

## Batch 50 (Abilities 383-392)
- Blow Away [Errata] :: Verified Whirlwind tick damage plus extra push; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_blow_away_errata_pushes_and_ticks`.
- Bodyguard [Errata] :: Verified intercept + resisted damage; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_bodyguard_errata_intercepts_and_reduces_damage`.
- Bone Lord [Errata] :: Verified Bone Club stage drop, Bonemerang line conversion, and Bone Rush strike override; tests `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_bone_lord_errata_bone_club_drops_def_and_spatk`, `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_bone_lord_errata_bonemerang_no_double_strike`, and `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_bone_lord_errata_bone_rush_hits_four_times`.
- Bone Wielder [Errata] :: Verified Ground immunity bypass; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_bone_wielder_errata_ignores_ground_immunity`.
- Brimstone [Errata] :: Verified Burn/Poison double-status application; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_brimstone_errata_applies_both_statuses`.
- Celebrate [Errata] :: Verified ready + disengage after hit; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_celebrate_errata_disengages_after_hit`.
- Chlorophyll [Errata] :: Verified initiative doubles in sun; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_chlorophyll_errata_doubles_initiative`.
- Clay Cannons [Errata] :: Verified 2m origin shift for ranged moves; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_clay_cannons_errata_extends_origin`.
- Damp [Errata] :: Verified +1d10 Water damage bonus; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_damp_errata_adds_water_damage_bonus`.
- Danger Syrup [Errata] :: Verified Sweet Scent blinds targets; new test `tests/test_audit_batch50_abilities.py::AuditBatch50AbilityTests::test_danger_syrup_errata_blinds_on_sweet_scent`.

## Batch 51 (Abilities 393-402)
- Download [Errata] :: Verified stat raise based on target defenses; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_download_errata_raises_attack_when_def_lower`.
- Defeatist [Errata] :: Verified damage bonus/penalty and initiative bonus; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_defeatist_errata_bonus_above_half`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_defeatist_errata_penalty_and_initiative_bonus`.
- Defy Death [Errata] :: Verified injury removal with tick healing and daily cap; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_defy_death_errata_heals_injuries_and_hp`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_defy_death_errata_caps_three_injuries_per_day`.
- Desert Weather [Errata] :: Verified sand immunity, fire resist in sun, and temp HP in rain; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_desert_weather_errata_grants_temp_hp_in_rain`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_desert_weather_errata_resists_fire_in_sun`.
- Dreamspinner [Errata] :: Verified sleeping foes drain and temp HP gain; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_dreamspinner_errata_drains_sleeping_foes`.
- Drizzle [Errata] :: Verified rain set via swift action; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_drizzle_errata_sets_rain`.
- Drought [Errata] :: Verified sun set via swift action; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_drought_errata_sets_sun`.
- Drown Out [Errata] :: Verified Sonic moves blocked twice per scene; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_drown_out_errata_blocks_sonic_twice`.
- Dust Cloud [Errata] :: Verified Powder keyword moves become Burst 1; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_dust_cloud_errata_expands_powder_moves`.
- Early Bird [Errata] :: Verified half-Speed initiative bonus and +3 Sleep save bonus; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_early_bird_errata_grants_initiative_bonus`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_early_bird_errata_adds_sleep_save_bonus`.
- Electrodash [Errata] :: Verified free Sprint action, Stuck clearance on Shift, and no AoO while sprinting; new tests `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_electrodash_errata_sprint_is_free`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_electrodash_errata_clears_stuck_on_shift`, `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_electrodash_errata_blocks_aoo_while_sprinting`.
- Filter [Errata] :: Verified +5 damage reduction vs. super-effective hits; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_filter_errata_reduces_super_effective_damage`.

## Batch 52 (Abilities 403-432)
- Imposter [Errata] :: Verified pre-damage Transform interrupt; new test `tests/test_audit_batch51_abilities.py::AuditBatch51AbilityTests::test_imposter_errata_interrupts_with_transform`.

## Batch 56 (Errata Abilities)
- Mummy [Errata] :: Verified melee hit disables one of the user's abilities; new test `tests/test_audit_batch56_abilities.py::AuditBatch56AbilityTests::test_mummy_errata_disables_ability_on_melee_hit`.

## Batch 57 (Errata Abilities)
- Odious Spray [Errata] :: Verified Poison Gas range/AC override and flinch on hit; new tests `tests/test_audit_batch57_abilities.py::AuditBatch57AbilityTests::test_odious_spray_errata_modifies_poison_gas`, `tests/test_audit_batch57_abilities.py::AuditBatch57AbilityTests::test_odious_spray_errata_flinches_poison_gas`.

## Batch 58 (Errata Abilities)
- Perception [Errata] :: Verified +1 evasion and free Disengage from ally damaging AoE; new tests `tests/test_audit_batch58_abilities.py::AuditBatch58AbilityTests::test_perception_errata_adds_evasion`, `tests/test_audit_batch58_abilities.py::AuditBatch58AbilityTests::test_perception_errata_disengages_on_ally_aoe`.

## Batch 59 (Errata Abilities)
- Permafrost [Errata] :: Verified indirect damage immunity (status ticks); new test `tests/test_audit_batch59_abilities.py::AuditBatch59AbilityTests::test_permafrost_errata_blocks_status_damage`.
- Poltergeist [Errata] :: Verified Rotom form grants Phantom Body and form move at level 40+; new test `tests/test_audit_batch59_abilities.py::AuditBatch59AbilityTests::test_poltergeist_errata_grants_form_ability_and_move`.
- Pressure [Errata] :: Verified swift action suppresses nearby foes within 3m; new test `tests/test_audit_batch59_abilities.py::AuditBatch59AbilityTests::test_pressure_errata_suppresses_nearby_foes`.

## Batch 60 (Errata Abilities)
- Quick Curl [Errata] :: Verified Defense Curl interrupt readiness; new test `tests/test_audit_batch60_abilities.py::AuditBatch60AbilityTests::test_quick_curl_errata_readies_defense_curl_interrupt`.
- Quick Feet [Errata] :: Verified speed boost under status and paralysis penalty suppression; new test `tests/test_audit_batch60_abilities.py::AuditBatch60AbilityTests::test_quick_feet_errata_boosts_speed_and_ignores_paralysis`.
- Reckless [Errata] :: Verified DB bonus for Exhaust/Recoil/Reckless keyword moves; new test `tests/test_audit_batch60_abilities.py::AuditBatch60AbilityTests::test_reckless_errata_adds_db_for_keyword_moves`.

## Batch 61 (Errata Abilities)
- Rock Head [Errata] :: Verified charge bonus after straight-line movement; new test `tests/test_audit_batch61_abilities.py::AuditBatch61AbilityTests::test_rock_head_errata_adds_charge_bonus`.
- Rocket [Errata] :: Verified initiative jump and response block; new test `tests/test_audit_batch61_abilities.py::AuditBatch61AbilityTests::test_rocket_errata_moves_first_next_round`.
- Root Down [Errata] :: Verified Ingrain-gated damage reduction; new test `tests/test_audit_batch61_abilities.py::AuditBatch61AbilityTests::test_root_down_errata_grants_damage_reduction`.

## Batch 62 (Errata Abilities)
- Sap Sipper [Errata] :: Verified Grass immunity and chosen stat boost; new test `tests/test_audit_batch62_abilities.py::AuditBatch62AbilityTests::test_sap_sipper_errata_absorbs_and_boosts_choice`.
- Sand Veil [Errata] :: Verified base +1 evasion, +2 in sand, and sandstorm immunity for adjacent allies; new test `tests/test_audit_batch62_abilities.py::AuditBatch62AbilityTests::test_sand_veil_errata_evasion_and_immunity`.
- Spray Down [Errata] :: Verified grounding of airborne targets with scene x2 limit; new test `tests/test_audit_batch62_abilities.py::AuditBatch62AbilityTests::test_spray_down_errata_grounds_airborne_target`.

## Batch 63 (Abilities)
- Quick Draw :: Verified interrupt counterstrike and accuracy penalty; new test `tests/test_audit_batch63_abilities.py::AuditBatch63AbilityTests::test_quick_draw_interrupts_and_penalizes_accuracy`.
- Unseen Fist :: Verified melee attacks block interrupt responses; new test `tests/test_audit_batch63_abilities.py::AuditBatch63AbilityTests::test_unseen_fist_blocks_quick_draw_interrupt`.
- Wandering Spirit :: Verified melee-hit ability swap; new test `tests/test_audit_batch63_abilities.py::AuditBatch63AbilityTests::test_wandering_spirit_swaps_abilities_on_melee_hit`.

## Batch 64 (Abilities)
- Queenly Majesty :: Verified priority/interrupt move block; new test `tests/test_audit_batch64_abilities.py::AuditBatch64AbilityTests::test_queenly_majesty_blocks_priority_moves`.
- Radiant Beam :: Verified Grass moves convert to Line 4; new test `tests/test_audit_batch64_abilities.py::AuditBatch64AbilityTests::test_radiant_beam_converts_grass_move_to_line`.
- RKS System :: Verified Memory type override and Normal-type resistance shift; new test `tests/test_audit_batch64_abilities.py::AuditBatch64AbilityTests::test_rks_system_memory_sets_type_and_resists`.

## Batch 65 (Abilities)
- Water Compaction :: Verified Defense CS boost on Water hits; new test `tests/test_audit_batch65_abilities.py::AuditBatch65AbilityTests::test_water_compaction_raises_defense_on_water_hit`.
- Wily :: Verified status moves add an extra target; new test `tests/test_audit_batch65_abilities.py::AuditBatch65AbilityTests::test_wily_adds_extra_status_target`.
- Neutralizing Gas :: Verified burst suppression of nearby abilities; new test `tests/test_audit_batch65_abilities.py::AuditBatch65AbilityTests::test_neutralizing_gas_suppresses_abilities_in_burst`.

## Batch 66 (Abilities)
- Ripen :: Verified berry numeric buffs are doubled; new test `tests/test_audit_batch66_abilities.py::AuditBatch66AbilityTests::test_ripen_doubles_berry_heal`.
- Screen Cleaner :: Verified clearing of blessings; new test `tests/test_audit_batch66_abilities.py::AuditBatch66AbilityTests::test_screen_cleaner_clears_blessings`.
- Zen Snowed :: Verified Zen form activation and punch move unlocks; new test `tests/test_audit_batch66_abilities.py::AuditBatch66AbilityTests::test_zen_snowed_unlocks_punch_moves`.

## Batch 67 (Errata Abilities)
- Inner Focus [Errata] :: Verified initiative penalty block; test `tests/test_audit_batch52_abilities.py::AuditBatch52AbilityTests::test_inner_focus_errata_blocks_initiative_penalty`.
- Interference [Errata] :: Verified accuracy penalty burst; test `tests/test_audit_batch52_abilities.py::AuditBatch52AbilityTests::test_interference_errata_penalizes_accuracy`.
- Intimidate [Errata] :: Verified scene-limited attack drop; test `tests/test_audit_batch52_abilities.py::AuditBatch52AbilityTests::test_intimidate_errata_once_per_target`.
- Justified [Errata] :: Verified Dark-hit and AoO bonuses; tests `tests/test_audit_batch54_abilities.py::AuditBatch54AbilityTests::test_justified_errata_raises_attack_on_dark_hit`, `tests/test_audit_batch54_abilities.py::AuditBatch54AbilityTests::test_justified_errata_adds_intercept_bonus`.
- Kampfgeist [Errata] :: Verified resistance to triggering damage; test `tests/test_audit_batch54_abilities.py::AuditBatch54AbilityTests::test_kampfgeist_errata_resists_triggering_damage`.
- Leaf Guard [Errata] :: Verified cure and sun frequency override; tests `tests/test_audit_batch53_abilities.py::AuditBatch53AbilityTests::test_leaf_guard_errata_cures_status`, `tests/test_audit_batch53_abilities.py::AuditBatch53AbilityTests::test_leaf_guard_errata_ignores_frequency_in_sun`.

## Batch 68 (Errata Abilities)
- Light Metal [Errata] :: Verified stat adjustments; test `tests/test_audit_batch52_abilities.py::AuditBatch52AbilityTests::test_light_metal_errata_adjusts_stats`.
- Lightning Kicks [Errata] :: Verified kick priority and accuracy bonus; test `tests/test_audit_batch52_abilities.py::AuditBatch52AbilityTests::test_lightning_kicks_errata_grants_accuracy_bonus`.
- Lightning Rod [Errata] :: Verified redirect and SpAtk boost; test `tests/test_audit_batch54_abilities.py::AuditBatch54AbilityTests::test_lightning_rod_errata_redirects_and_boosts`.
- Liquid Ooze [Errata] :: Verified drain recoil and Leech Seed reversal; tests `tests/test_audit_batch54_abilities.py::AuditBatch54AbilityTests::test_liquid_ooze_errata_drains_on_absorb`, `tests/test_audit_batch54_abilities.py::AuditBatch54AbilityTests::test_liquid_ooze_errata_reverses_leech_seed`.
- Lunchbox [Errata] :: Verified temp HP on food buff trade; test `tests/test_audit_batch54_abilities.py::AuditBatch54AbilityTests::test_lunchbox_errata_grants_temp_hp`.
- Magma Armor [Errata] :: Verified freeze immunity and burn on fire hit; tests `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_magma_armor_errata_prevents_freeze`, `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_magma_armor_errata_burns_on_fire_hit`.

## Batch 69 (Errata Abilities)
- Magnet Pull [Errata] :: Verified aura distance control; test `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_magnet_pull_errata_limits_distance`.
- Mega Launcher [Errata] :: Verified pulse move damage bonus; test `tests/test_audit_batch53_abilities.py::AuditBatch53AbilityTests::test_mega_launcher_errata_boosts_pulse_moves`.
- Memory Wipe [Errata] :: Verified move disable and reset on hit; tests `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_memory_wipe_errata_disables_move`, `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_memory_wipe_errata_clears_disabled_on_hit`.
- Migraine [Errata] :: Verified confusion-triggered bonus; test `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_migraine_errata_triggers_on_confusion`.
- Moody [Errata] :: Verified end-phase stat swings; test `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_moody_errata_swings_two_stats`.
- Multiscale [Errata] :: Verified half damage at full HP; test `tests/test_audit_batch53_abilities.py::AuditBatch53AbilityTests::test_multiscale_errata_halves_damage_at_full_hp`.

## Batch 70 (Errata Abilities)
- No Guard [Errata] :: Verified forced hit and ignore override; tests `tests/test_audit_batch53_abilities.py::AuditBatch53AbilityTests::test_no_guard_errata_forces_hit`, `tests/test_audit_batch53_abilities.py::AuditBatch53AbilityTests::test_no_guard_errata_can_be_ignored`.
- Normalize [Errata] :: Verified type conversion and damage bonus; tests `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_normalize_errata_changes_move_type`, `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_normalize_errata_boosts_damage`, `tests/test_audit_batch55_abilities.py::AuditBatch55AbilityTests::test_normalize_errata_ignores_resistance_on_status`.
- Prime Fury [Errata] :: Verified enrage + Attack boost; test `tests/test_audit_batch36_abilities.py::AuditBatch36AbilityTests::test_prime_fury_errata_enrages_and_boosts`.
- Rattled [Errata] :: Verified speed boost and disengage; test `tests/test_audit_batch37_abilities.py::AuditBatch37AbilityTests::test_rattled_errata_raises_speed_and_disengages`.
- Shackle [Errata] :: Verified movement halving in Burst 3; test `tests/test_audit_batch39_abilities.py::AuditBatch39AbilityTests::test_shackle_errata_halves_movement_in_burst`.
- Shell Shield [Errata] :: Verified Withdraw interrupt readiness; test `tests/test_audit_batch40_abilities.py::AuditBatch40AbilityTests::test_shell_shield_errata_sets_withdraw_ready`.

## Batch 71 (Errata Abilities)
- Sonic Courtship [Errata] :: Verified Attract cone ignores gender; test `tests/test_audit_batch41_abilities.py::AuditBatch41AbilityTests::test_sonic_courtship_errata_ignores_gender`.
- Sound Lance [Errata] :: Verified Supersonic damage when ready; test `tests/test_audit_batch42_abilities.py::AuditBatch42AbilityTests::test_sound_lance_errata_deals_damage`.
- Steadfast [Errata] :: Verified speed boost on flinch; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_steadfast_errata_raises_speed_on_flinch`.
- Storm Drain [Errata] :: Verified Water redirect and SpAtk boost; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_storm_drain_errata_redirects_and_boosts`.
- Sturdy [Errata] :: Verified 1 HP survival at full HP; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sturdy_errata_prevents_full_hp_ko`.
- Sun Blanket [Errata] :: Verified low-HP sun heal; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_sun_blanket_errata_heals_on_low_hp`.

## Batch 72 (Errata + Ability)
- Swift Swim [Errata] :: Verified swim speed doubling in rain; test `tests/test_audit_batch44_abilities.py::AuditBatch44AbilityTests::test_swift_swim_errata_doubles_swim_speed`.
- Unburden [Errata] :: Verified movement boost without held item; test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_unburden_errata_grants_movement`.
- Unnerve [Errata] :: Verified suppression of positive CS; test `tests/test_audit_batch45_abilities.py::AuditBatch45AbilityTests::test_unnerve_errata_blocks_positive_combat_stages`.
- Whirlwind Kicks [Errata] :: Verified Rapid Spin swift action; test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_whirlwind_kicks_errata_rapid_spin_swift`.
- Windveiled [Errata] :: Verified Flying damage bonus; test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_windveiled_errata_adds_flying_damage`.
- Full Guard :: Verified super-effective resist and temp HP; tests `tests/test_audit_batch30_abilities.py::AuditBatch30AbilityTests::test_full_guard_resists_super_effective_damage`, `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_full_guard_grants_temp_hp_after_super_effective`.

## Batch 73 (Errata + Abilities)
- Life Force [Errata] :: Verified tick heal action; test `tests/test_audit_batch52_abilities.py::AuditBatch52AbilityTests::test_life_force_errata_heals_tick`.
- Heliovolt :: Verified evasion bonus and sunny resonance readiness; tests `tests/test_audit_batch31_abilities.py::AuditBatch31AbilityTests::test_heliovolt_grants_evasion_bonus`, `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_heliovolt_adds_evasion_and_sunny_resonance`.
- Juicy Energy :: Verified Berry Juice heal scales to level; tests `tests/test_audit_batch32_abilities.py::AuditBatch32AbilityTests::test_juicy_energy_uses_level_for_berry_juice`, `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_juicy_energy_uses_level_heal`.
- Lancer :: Verified crit-range bonus after charge; test `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_lancer_grants_crit_after_charge`.
- Leaf Rush :: Verified priority and damage bonus after readying; tests `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_leaf_rush_grants_priority_and_damage_bonus`, `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_leaf_rush_adds_priority_and_damage_bonus`.
- Leafy Cloak :: Verified ability grants via Leafy Cloak action; tests `tests/test_audit_batch33_abilities.py::AuditBatch33AbilityTests::test_leafy_cloak_grants_chosen_abilities`, `tests/test_audit_batch46_abilities.py::AuditBatch46AbilityTests::test_leafy_cloak_grants_abilities`.

## Batch 74 (Abilities)
- Line Charge :: Verified via tests `tests/test_audit_batch33_abilities.py::test_line_charge_blocks_diagonal_shift`, `tests/test_audit_batch46_abilities.py::test_line_charge_blocks_diagonal_shift`.
- Nimble Strikes :: Verified via tests `tests/test_audit_batch46_abilities.py::test_nimble_strikes_adds_damage`.
- Ragelope :: Verified via tests `tests/test_audit_batch37_abilities.py::test_ragelope_enrages_and_boosts`, `tests/test_audit_batch46_abilities.py::test_ragelope_enrages_on_high_roll`.
- Sacred Bell :: Verified via tests `tests/test_audit_batch38_abilities.py::test_sacred_bell_reduces_dark_damage`, `tests/test_audit_batch46_abilities.py::test_sacred_bell_resists_dark`.
- Seasonal :: Verified via tests `tests/test_audit_batch46_abilities.py::test_seasonal_grants_ability`.
- Snuggle :: Verified via tests `tests/test_audit_batch41_abilities.py::test_snuggle_grants_temp_hp_to_both`, `tests/test_audit_batch46_abilities.py::test_snuggle_grants_temp_hp_to_both`.

## Batch 75 (Abilities)
- Sol Veil :: Verified via tests `tests/test_audit_batch41_abilities.py::test_sol_veil_adds_accuracy_penalty`, `tests/test_audit_batch46_abilities.py::test_sol_veil_grants_evasion_and_dr_in_sun`.
- Sorcery :: Verified via tests `tests/test_audit_batch42_abilities.py::test_sorcery_adds_special_attack_bonus`, `tests/test_audit_batch46_abilities.py::test_sorcery_adds_special_attack_bonus`.
- Spike Shot :: Verified via tests `tests/test_audit_batch42_abilities.py::test_spike_shot_extends_melee_range`, `tests/test_audit_batch46_abilities.py::test_spike_shot_extends_melee_range`.
- Tingle :: Verified via tests `tests/test_audit_batch45_abilities.py::test_tingle_drains_tick_and_penalizes_damage`, `tests/test_audit_batch46_abilities.py::test_tingle_drains_tick_and_applies_penalty`.
- Tonguelash :: Verified via tests `tests/test_audit_batch45_abilities.py::test_tonguelash_paralyzes_and_flinches`, `tests/test_audit_batch46_abilities.py::test_tonguelash_paralyzes_and_flinches`.
- Trinity :: Verified via tests `tests/test_audit_batch45_abilities.py::test_trinity_tri_attack_applies_frozen_first`, `tests/test_audit_batch46_abilities.py::test_trinity_tri_attack_applies_frozen_first`.

## Batch 76 (Abilities)
- Type Aura :: Verified via tests `tests/test_audit_batch45_abilities.py::test_type_aura_boosts_matching_type_damage`, `tests/test_audit_batch46_abilities.py::test_type_aura_adds_damage_bonus`.
- Weird Power :: Verified via tests `tests/test_audit_batch47_abilities.py::test_weird_power_adds_higher_stat`.
- Handyman :: Verified via tests `tests/test_audit_batch31_abilities.py::test_handyman_selects_item_index`, `tests/test_audit_batch47_abilities.py::test_handyman_selects_item_index`.
- Horde Break :: Verified via tests `tests/test_audit_batch31_abilities.py::test_horde_break_cures_all_statuses`, `tests/test_audit_batch47_abilities.py::test_horde_break_cures_status_on_schooling_return`.
- Innards Out :: Verified via tests `tests/test_audit_batch32_abilities.py::test_innards_out_resists_and_retaliates`, `tests/test_audit_batch47_abilities.py::test_innards_out_retaliates`.
- Mud Shield :: Verified via tests `tests/test_audit_batch34_abilities.py::test_mud_shield_grants_temp_hp_and_reduction`, `tests/test_audit_batch47_abilities.py::test_mud_shield_grants_temp_hp`.

## Batch 77 (Abilities)
- Neuroforce :: Verified via tests `tests/test_audit_batch47_abilities.py::test_neuroforce_adds_damage_on_super_effective`.
- Power Construct :: Verified via tests `tests/test_audit_batch35_abilities.py::test_power_construct_grants_temp_hp_and_form`, `tests/test_audit_batch47_abilities.py::test_power_construct_grants_temp_hp_below_half`.
- Power of Alchemy :: Verified via tests `tests/test_audit_batch35_abilities.py::test_power_of_alchemy_copies_ability`, `tests/test_audit_batch47_abilities.py::test_power_of_alchemy_copies_ability`.
- Revelation :: Verified via tests `tests/test_battle_state.py::test_revelation_dance_bonus_damage`.
- Receiver :: Verified via tests `tests/test_audit_batch37_abilities.py::test_receiver_copies_ally_ability_on_faint`.
- Schooling :: Verified via tests `tests/test_audit_batch31_abilities.py::test_horde_break_cures_all_statuses`, `tests/test_audit_batch47_abilities.py::test_horde_break_cures_status_on_schooling_return`.

## Batch 78 (Abilities)
- Shadow Shield :: Verified via tests `tests/test_audit_batch39_abilities.py::test_shadow_shield_reduces_damage_at_full_hp`.
- Shields Down :: Verified via tests `tests/test_audit_batch40_abilities.py::test_shields_down_switches_to_core_form`.
- Slush Rush :: Verified via tests `tests/test_audit_batch40_abilities.py::test_slush_rush_doubles_speed_in_hail`.
- Stakeout :: Verified via tests `tests/test_audit_batch43_abilities.py::test_stakeout_adds_damage_against_newcomer`.
- Steelworker :: Verified via tests `tests/test_audit_batch44_abilities.py::test_steelworker_adds_stab_when_anchored`.
- Tangling Hair :: Verified via tests `tests/test_audit_batch44_abilities.py::test_tangling_hair_slows_melee_attacker`.

## Batch 79 (Abilities)
- Surge Surfer :: Verified via tests `tests/test_audit_batch44_abilities.py::test_surge_surfer_doubles_speed_in_electric_terrain`.
- Triage :: Verified via tests `tests/test_audit_batch45_abilities.py::test_triage_grants_priority_to_healing`.
- Flavorful Aroma :: Verified via tests `tests/test_audit_batch29_abilities.py::test_flavorful_aroma_buffs_ally`.
- Gorilla Tactics :: Verified via tests `tests/test_audit_batch30_abilities.py::test_gorilla_tactics_locks_moves_and_boosts_damage`.
- Gulp Missile :: Verified via tests `tests/test_audit_batch30_abilities.py::test_gulp_missile_retaliates_after_damage`.
- Ice Face :: Verified via tests `tests/test_audit_batch32_abilities.py::test_ice_face_grants_temp_hp_in_hail`.

## Batch 80 (Abilities)
- Intrepid Sword :: Verified via tests `tests/test_audit_batch32_abilities.py::test_intrepid_sword_raises_attack_on_init`.
- Mimicry :: Verified via tests `tests/test_audit_batch34_abilities.py::test_mimicry_changes_type_based_on_weather`.
- Missile Launch :: Verified via tests `tests/test_audit_batch34_abilities.py::test_missile_launch_deploys_tokens`.
- Perish Body :: Verified via tests `tests/test_audit_batch35_abilities.py::test_perish_body_applies_perish_song`.
- Power Spot :: Verified via tests `tests/test_audit_batch36_abilities.py::test_power_spot_boosts_ally_damage`.
- Propeller Tail :: Verified via tests `tests/test_audit_batch36_abilities.py::test_propeller_tail_grants_sprint_and_lock`.

## Batch 81 (Abilities)
- Sand Spit :: Verified via tests `tests/test_audit_batch38_abilities.py::test_sand_spit_counters`.
- Stalwart :: Verified via tests `tests/test_audit_batch43_abilities.py::test_stalwart_raises_stats_after_damage`.
- Steam Engine :: Verified via tests `tests/test_audit_batch44_abilities.py::test_steam_engine_grants_evasion_on_fire_hit`.
- Grim Neigh :: Verified via tests `tests/test_audit_batch30_abilities.py::test_grim_neigh_raises_spatk_and_penalizes_foes`.
- Splendorous Rider :: Verified via tests `tests/test_audit_batch42_abilities.py::test_splendorous_rider_borrows_mount_move`.
- Psionic Screech :: Verified via tests `tests/test_audit_batch36_abilities.py::test_psionic_screech_converts_and_flinches`.

## Batch 82 (Abilities)
- Toxic Nourishment :: Verified via tests `tests/test_audit_batch45_abilities.py::test_toxic_nourishment_cures_poison_and_grants_temp_hp`.
