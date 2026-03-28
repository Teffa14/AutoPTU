# Ability Hook Tracker

This document tracks the incremental implementation of PTU abilities once the hook infrastructure is in place. Each row represents a specific ability, the current state of its implementation, and notes about required phases, triggers, or interactions.

`ABILITY_LOG.md` now mirrors the full CSV-sourced ability list so you can see every entry and whether it is pending or done; rerun `python scripts/generate_ability_log.py` whenever the CSV changes to keep the master log in sync. The launcher/CLI runs `auto_ptu/tools/auto_update.py` at startup, so the generator executes automatically whenever the CSV or helper script is newer than the log.

We are working through the first ninety-one ability entries from `files/Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv` so reviewers can see how far the automated hooks have progressed; all 91 are now complete with code and tests.

## Code Audit (2026-02-11)

- A strict code scan confirms all 621 CSV abilities are referenced somewhere under `auto_ptu/rules/`.
- Test coverage is partial. See `reports/ability_code_audit.md` for the current list of abilities without test references (292 entries).
- A follow-up strict audit of those 292 abilities is available at `reports/ability_strict_audit.md`.
- That audit flags 109 abilities as `missing_action_move` (abilities with action-style frequencies but no ability move or move-special scaffolding found). The rest are marked as likely static hooks or likely action hooks pending manual verification.

| # | Ability | Status | Notes |
|---|---------|--------|-------|
| 1 | `Poison Heal` | done | Already converts persistent poison/Badly Poisoned ticks into healing via `_handle_status_phase_effects`, emits an `ability` log, and has regression coverage in `tests/test_battle_state.py::test_poison_heal_converts_damage_to_heal`. |
| 2 | `Shed Skin` | done | Runs in `_handle_ability_phase_effects` with the new `shed_skin_demo` scenario, test coverage (`tests/test_battle_state.py::test_shed_skin_cures_status_at_end_phase`), and launcher/README hooks so you can see the logged d20 cure roll replayed on demand. |
| 3 | `Swift Swim` | done | Movement_speed already doubles for Rain/Storm/Downpour and the new `swift_swim_demo` scenario plus `tests/test_battle_state.py::test_swift_swim_doubles_swim_movement_in_rain` prove the logged swim range matches the PTU rulebook. |
| 4 | `Chlorophyll` | done | Overland movement getter adds +2 during Sun/Harsh Sunlight, backed by `tests/test_battle_state.py::test_chlorophyll_boosts_overland_in_sun`, the new `chlorophyll_demo`, and the updated ability tracker/log so the stats are visible when the scenario launches. |
| 5 | `Levitate` | done | Hooks `BattleState._apply_hazard_effects` plus the new `resolve_move_action` guard so Levitate ignores Spikes/Toxic Spikes/Stealth Rock/Sticky Web and ground-type moves; the `levitate_demo` campaign plus `tests/test_battle_state.py::test_levitate_ignores_ground_hazards` and `tests/test_battle_state.py::test_levitate_blocks_ground_moves` prove the logs. |
| 6 | `Lightning Rod` | done | Redirects Electric single-target ranged moves in `BattleState._lightning_rod_redirect`, then absorbs the hit and logs the Sp. Atk boost (`tests/test_battle_state.py::test_lightning_rod_redirects_and_boosts_spatk`). |
| 7 | `Pressure` | done | Consumes extra move frequency usage when targeting a Pressure holder within 3m and logs the ability trigger (`tests/test_battle_state.py::test_pressure_adds_extra_frequency_usage`). |
| 8 | `Water Absorb` | done | Converts Water hits into a tick heal and blocks damage/effects during resolution with an ability log (`tests/test_battle_state.py::test_water_absorb_heals_and_blocks_damage`). |
| 9 | `Sturdy` | done | Blocks execute effects and prevents full-HP KOs by leaving the user at 1 HP, with ability logs and injury suppression (`tests/test_battle_state.py::test_sturdy_prevents_full_hp_ko`). |
|10 | `Intimidate` | done | Entry hook (`_trigger_intimidate`) applies -1 ATK to adjacent foes on join/start and emits ability logs (`tests/test_battle_state.py::test_intimidate_triggers_on_entry`). |

|11 | `Flame Body` | done | Contact move list (`auto_ptu/data/compiled/contact_moves.json`, generated via `python -m auto_ptu.tools.generate_contact_moves`) feeds the contact ability hook registry (`auto_ptu/rules/hooks/abilities/contact_effects.py`), with `_handle_contact_ability_effects` delegating for the Burn logs (`tests/test_battle_state.py::test_flame_body_burns_attacker_on_contact`). |
|12 | `Flame Tongue` | done | Shares the Flame Body entry in `_CONTACT_STATUS_EFFECTS`, so Flame Tongue users trigger the same Burn log for every contact attack. |
|13 | `White Flame` | done | Reuses the shared Burn hook so White Flame contact moves emit the same logged effect. |
|14 | `Static` | done | Contact ability hook registry records Paralysis rolls for Static holders when the compiled contact move list hits (`tests/test_battle_state.py::test_static_paralyzes_attacker_on_contact`). |
|15 | `Effect Spore` | done | The same handler cycles through `Burned`/`Paralyzed`/`Poisoned` outcomes when a contact move hits, and the RNG-controlled tests keep the logs reproducible. |
|16 | `Poison Touch` | done | Poisoned entries in `_CONTACT_STATUS_EFFECTS` fire whenever `move_has_contact_trait` matches a contact attack, matching the Foundry behavior without ad-hoc wiring. |
|17 | `Rough Skin` | done | `_CONTACT_DAMAGE_ABILITIES` applies 1/8 HP contact bumps, logs `type: "ability"`/`effect: "contact_damage"`, and `tests/test_battle_state.py::test_rough_skin_triggers_contact_damage` proves the result. |
|18 | `Iron Barbs` | done | Shares the Rough Skin damage hook so all contact moves punish attackers by 1/8 HP while emitting the same ability log entry. |

|19 | `Abominable` | done | Blocks massive damage injuries + recoil in `auto_ptu/rules/battle_state.py`; tests `tests/test_battle_state.py::test_abominable_ignores_recoil` and `tests/test_battle_state.py::test_abominable_blocks_massive_damage_injury`. |
|20 | `Absorb Force` | done | Physical hits drop one effectiveness stage in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_absorb_force_reduces_effectiveness`. |
|21 | `Adaptability` | done | +1 DB to STAB damage unless Aura Break suppresses (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_adaptability_adds_db_to_stab`. |
|22 | `Aerilate` | done | Normal attacks become Flying with log (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_aerilate_changes_normal_moves`. |
|23 | `Aftermath` | done | Burst damage on KO in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_aftermath_burst_damage`. |
|24 | `Air Lock` | done | Suppresses weather via `effective_weather` with phase logging; test `tests/test_battle_state.py::test_air_lock_suppresses_weather_damage`. |
|25 | `Ambush` | done | Priority on light melee + flinch on hit (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_ambush_flinches_on_hit`. |
|26 | `Analytic` | done | +5 damage when target acted earlier (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_analytic_bonus_damage`. |
|27 | `Anger Point` | done | Crit triggers Enraged +6 ATK CS with log (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_anger_point_triggers_on_crit`. |
|28 | `Anticipation` | done | Reveals super-effective move on turn start (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_anticipation_senses_super_effective`. |
|29 | `Aqua Boost` | done | Adjacent ally Water move +5 damage with Aura Break check (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_aqua_boost_adds_damage`. |
|30 | `Arena Trap` | done | Applies Slowed to nearby grounded foes (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_arena_trap_slows_foes`. |
|31 | `Aroma Veil` | done | Blocks confusion/rage/suppression status (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_aroma_veil_blocks_status`. |
|32 | `Aura Break` | done | Suppresses ability damage boosts (Adaptability/Aqua Boost/Analytic/Aura Storm/Anger Point) (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_aura_break_suppresses_adaptability`. |
|33 | `Aura Storm` | done | Aura keyword damage bonus from injuries/low HP (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_aura_storm_scales_with_injuries`. |
|34 | `Bad Dreams` | done | Start-phase tick damage to sleeping targets (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_bad_dreams_hits_sleeping_targets`. |
|35 | `Battle Armor` | done | Negates crits (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_battle_armor_blocks_crit`. |
|36 | `Beam Cannon` | done | Ranged single-target +3 range and crit range -3 (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_beam_cannon_extends_crit_range`. |
|37 | `Beautiful` | done | Calms adjacent Enraged target at Start (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_beautiful_cures_enraged_once`. |
|38 | `Berry Storage` | done | Triples berry food buffs in `PokemonState.add_food_buff` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_berry_storage_triples_berry_buffs`. |
|39 | `Big Pecks` | done | Blocks Defense drops from foes in `_apply_combat_stage` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_big_pecks_blocks_defense_drops`. |
|40 | `Big Swallow` | done | Boosts stockpile count for Swallow/Spit Up (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_big_swallow_boosts_swallow_count`. |
|41 | `Blaze` | done | Boosts Fire damage under Last Chance HP thresholds (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_blaze_boosts_fire_damage_under_last_chance`. |
|42 | `Blessed Touch` | done | Ability move heals 1/4 max HP (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_blessed_touch_heals_adjacent_ally`. |
|43 | `Blow Away` | done | Adds a tick of damage after Whirlwind hits (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_blow_away_adds_tick_after_whirlwind`. |
|44 | `Blur` | done | Forces accuracy checks on no-AC moves; halves evasion contribution (`auto_ptu/rules/calculations.py`); test `tests/test_battle_state.py::test_blur_requires_accuracy_roll`. |
|45 | `Bodyguard` | done | Redirects adjacent ally hits + resists one type stage (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_bodyguard_intercepts_and_resists`. |
|46 | `Bone Lord` | done | Bone Club flinch + bone move priority/multi-hit (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_bone_lord_forces_flinch_on_bone_club`. |
|47 | `Bone Wielder` | done | +1 accuracy for bone moves with Thick Club (`auto_ptu/rules/calculations.py`); test `tests/test_battle_state.py::test_bone_wielder_adds_accuracy_for_bone_moves`. |
|48 | `Brimstone` | done | Adds Poisoned when Fire attack burns (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_brimstone_adds_poison_on_fire_burn`. |

|49 | `Bulletproof` | done | Resists single-target ranged attacks one step further (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_bulletproof_resists_ranged_attacks`. |
|50 | `Bully` | done | Pushes, trips, and injures on super-effective melee hits (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_bully_trips_and_injures_on_super_effective_melee`. |
|51 | `Cave Crasher` | done | Resists Ground/Rock attacks one step further (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cave_crasher_resists_ground_attacks`. |
|52 | `Celebrate` | done | On KO, raises Speed +1 CS and grants a slowed shift (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_celebrate_boosts_speed_and_shifts_on_ko`. |
|53 | `Cherry Power` | done | Ability move grants temp HP and cures persistent status afflictions (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cherry_power_grants_temp_hp_and_cures`. |
|54 | `Clay Cannons` | done | Ability move lets ranged attacks originate from adjacent squares (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_clay_cannons_origin_shift`. |
|55 | `Clear Body` | done | Blocks combat stage drops from foes (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_clear_body_blocks_stage_drops`. |
|56 | `Cloud Nine` | done | Ability move clears weather (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cloud_nine_clears_weather`. |
|57 | `Cluster Mind` | done | Adds move pool bonus temporary effect (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cluster_mind_adds_move_pool_bonus`. |
|58 | `Color Change` | done | Changes type to the triggering move's type when hit (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_color_change_shifts_type_on_hit`. |
|59 | `Color Theory` | done | Assigns a tail color effect on init (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_color_theory_sets_color_effect`. |
|60 | `Competitive` | done | Raises Special Attack by +2 CS when foes lower combat stages (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_competitive_boosts_spatk_on_drop`. |
|61 | `Compound Eyes` | done | Adds +3 accuracy bonus in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_compound_eyes_adds_accuracy_bonus`. |
|62 | `Confidence` | done | Ability move boosts allies' chosen stat within 5m (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_confidence_boosts_allies`. |
|63 | `Contrary` | done | Reverses combat stage changes (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_contrary_inverts_stage_changes`. |
|64 | `Conqueror` | done | On KO, raises Attack, Special Attack, and Speed by +1 CS (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_conqueror_triggers_on_ko`. |
|65 | `Copy Master` | done | After Copycat/Mimic, boosts a chosen combat stat (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_copy_master_boosts_chosen_stat`. |
|66 | `Corrosive Toxins` | done | Toxic bypasses poison immunity and suppresses Poison Heal (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_corrosive_toxins_bypasses_poison_heal`. |
|67 | `Courage` | done | Adds +5 damage and +5 damage reduction at <=1/3 HP (`auto_ptu/rules/calculations.py`, `auto_ptu/rules/battle_state.py`); tests `tests/test_battle_state.py::test_courage_adds_damage_bonus` and `tests/test_battle_state.py::test_courage_reduces_damage_taken`. |
|68 | `Covert` | done | Start-phase habitat check adds an evasion bonus (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_covert_grants_evasion_bonus_in_habitat`. |
|69 | `Cruelty` | done | Damage resolution adds an Injury once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cruelty_adds_injury_on_hit`. |
|70 | `Crush Trap` | done | Wrap triggers Struggle damage once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_crush_trap_adds_struggle_damage_on_wrap`. |
|71 | `Cursed Body` | done | Disables the hitting move once per scene on damage (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cursed_body_disables_move`. |
|72 | `Cute Charm` | done | Infatuates melee attackers of the opposite gender once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cute_charm_infatuates_melee`. |
|73 | `Cute Tears` | done | Drops the attack stat used by the hit by -2 CS once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_cute_tears_lowers_attack_stat`. |
|74 | `Damp` | done | Blocks Explosion/Self-Destruct and Aftermath within 10m (`auto_ptu/rules/battle_state.py`); tests `tests/test_battle_state.py::test_damp_blocks_explosion` and `tests/test_battle_state.py::test_damp_blocks_aftermath`. |
|75 | `Danger Syrup` | done | Triggers Sweet Scent evasion drop on the attacker once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_danger_syrup_triggers_sweet_scent`. |
|76 | `Dark Art` | done | Adds Last Chance damage bonus to Dark moves (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_dark_art_boosts_dark_damage_under_last_chance`. |
|77 | `Dark Aura` | done | Adds +1 DB to Dark moves for nearby allies and logs the boost (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_dark_aura_adds_db_for_allies`. |
|78 | `Daze` | done | Ability move inflicts Sleep on a hit target (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_daze_puts_target_to_sleep`. |
|79 | `Deadly Poison` | done | Upgrades Poisoned to Badly Poisoned once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_deadly_poison_upgrades_poison`. |
|80 | `Decoy` | done | Ability move uses Follow Me and grants +2 evasion until next turn (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_decoy_uses_follow_me_and_evasion`. |
|81 | `Deep Sleep` | done | Restores a tick of HP at end of turn while asleep (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_deep_sleep_heals_tick`. |
|82 | `Defeatist` | done | Applies and reverts combat stage shifts when crossing 50% HP (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_defeatist_adjusts_stages_below_half`. |
|83 | `Defiant` | done | Raises Attack by +2 CS when foes lower combat stages (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_defiant_raises_attack_on_drop`. |
|84 | `Defy Death` | done | Ability move heals up to 2 injuries (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_defy_death_heals_injuries`. |
|85 | `Delayed Reaction` | done | Halves incoming damage and applies the remainder next turn once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_delayed_reaction_defers_damage`. |
|86 | `Delivery Bird` | done | Item selection respects equipped item when held items are affected (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_delivery_bird_prefers_equipped_item`. |
|87 | `Desert Weather` | done | Sandstorm immunity, rain healing, and sunny Fire resist (`auto_ptu/rules/battle_state.py`); tests `tests/test_battle_state.py::test_desert_weather_heals_in_rain` and `tests/test_battle_state.py::test_desert_weather_resists_fire_in_sun`. |
|88 | `Diamond Defense` | done | Stealth Rock frequency Scene x2 and fairy/rock hazard damage (`auto_ptu/rules/battle_state.py`); tests `tests/test_battle_state.py::test_diamond_defense_places_fairy_stealth_rock` and `tests/test_battle_state.py::test_diamond_defense_stealth_rock_uses_best_type`. |
|89 | `Dig Away` | done | Interrupt queues Dig to avoid a hit (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_dig_away_avoids_attack_and_sets_pending_dig`. |
|90 | `Discipline` | done | Start-phase cure for Confused/Enraged/Infatuated/Flinch once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_discipline_cures_afflictions_on_start`. |
|91 | `Dire Spore` | done | Spore adds Poisoned on hit (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_dire_spore_adds_poison_on_spore`. |
|92 | `Dodge` | done | Blocks a damaging move once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_dodge_avoids_damaging_move`. |
|93 | `Download` | done | Ability action applies +5 damage bonus against a target's weaker defense (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_download_boosts_damage_against_target`. |
|94 | `Dreamspinner` | done | Ability action heals for nearby sleeping targets (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_dreamspinner_heals_per_sleeping_target`. |
|95 | `Drizzle` | done | Ability action sets Rain for 5 rounds (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_drizzle_sets_rain`. |
|96 | `Drown Out` | done | Focus check blocks Sonic moves once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_drown_out_blocks_sonic_move`. |
|97 | `Drought` | done | Ability action sets Sunny for 5 rounds (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_drought_sets_sun`. |
|98 | `Dry Skin` | done | Water immunity/heal, fire tick damage, and weather ticks (`auto_ptu/rules/battle_state.py`); tests `tests/test_battle_state.py::test_dry_skin_blocks_water_and_heals` and `tests/test_battle_state.py::test_dry_skin_takes_fire_tick_damage`. |
|99 | `Dust Cloud` | done | Powder moves become Burst 1 once per scene (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_dust_cloud_turns_powder_into_burst`. |
|100 | `Early Bird` | done | Adds save bonus against status afflictions (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_early_bird_adds_save_bonus`. |
|101 | `Enfeebling Lips` | done | Lovely Kiss lowers a chosen stat by -2 CS (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_enfeebling_lips_lowers_stat_on_lovely_kiss`. |
|102 | `Electrodash` | done | Ability action grants Sprint movement (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_electrodash_grants_sprint`. |
|103 | `Enduring Rage` | done | Grants 5 damage reduction while enraged (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_enduring_rage_reduces_damage`. |
|104 | `Exploit` | done | Adds +5 damage on super-effective hits (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_exploit_adds_damage_on_super_effective_hit`. |
|105 | `Fabulous Trim` | done | Records trim metadata for Furfrou (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_fabulous_trim_sets_style_effect`. |
|106 | `Fade Away` | done | Ability action grants Fade Away and interrupt avoidance (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_fade_away_grants_invisibility`. |
|107 | `Fairy Aura` | done | Adds +1 DB to Fairy moves for nearby allies (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_fairy_aura_boosts_fairy_damage`. |


Add new entries below as we expand the hook coverage. Update the `Status` column to `in progress`/`done` once the corresponding code and tests land, citing relevant files/sections when helpful.

| # | Ability | Status | Notes |
|---|---------|--------|-------|
|92 | `Fashion Designer` | done | Ability action crafts a mapped held item and logs the choice (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_fashion_designer_crafts_item`. |
|93 | `Fiery Crash` | done | Dash moves gain +2 DB or become Fire, and Fire Dash burns on 19+ (`auto_ptu/rules/battle_state.py`); tests `tests/test_battle_state.py::test_fiery_crash_changes_dash_moves_and_burns` and `tests/test_battle_state.py::test_fiery_crash_db_mode_logs`. |
|94 | `Filter` | done | Super-effective damage reduced and logged, with Solid Rock DR synergy (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_filter_reduces_super_effective_damage`. |
|97 | `Flare Boost` | done | Burned users gain +2 Sp. Atk CS during special damage calculations (`auto_ptu/rules/calculations.py`); test `tests/test_battle_state.py::test_flare_boost_raises_special_attack_when_burned`. |
|98 | `Flash Fire` | done | Fire immunity grants +5 damage bonus to the next Fire attack (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_flash_fire_immunity_and_bonus`. |
|99 | `Fluffy Charge` | done | Charge applies +1 DEF CS when the ability is present (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_fluffy_charge_adds_defense_stage`. |
|100 | `Flower Gift` | done | Sunny-only burst boosts allies by +2 CS split across chosen stats (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_flower_gift_boosts_allies_in_sun`. |
|101 | `Flower Power` | done | Grass moves can swap physical/special category via choice hook (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_flower_power_swaps_grass_move_category`. |
|102 | `Flower Veil` | done | Blocks stat drops on nearby Grass allies (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_flower_veil_blocks_stat_drops`. |
|103 | `Flutter` | done | Grants +3 evasion and flank immunity until next turn (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_flutter_prevents_flanking`. |
|104 | `Flying Fly Trap` | done | Ground/Bug immunity with ability logs (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_flying_fly_trap_blocks_ground_and_bug`. |
|105 | `Focus` | done | Fighting Last Chance damage bonus uses the Blaze-style scaling (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_focus_boosts_fighting_damage_under_last_chance`. |
|106 | `Forecast` | done | Start-phase weather typing shift via phase hook registry (`auto_ptu/rules/hooks/abilities/phase_effects.py`); test `tests/test_battle_state.py::test_forecast_updates_type_on_start_phase`. |
|107 | `Forest Lord` | done | Ability action grants accuracy bonus and origin shifts from forest tiles (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_forest_lord_adds_accuracy_bonus`. |
|108 | `Forewarn` | done | Reveals top DB moves and applies accuracy penalty to them (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_forewarn_penalizes_target_accuracy`. |
|109 | `Fox Fire` | done | Grants Ember interrupt wisps with charge tracking (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_fox_fire_triggers_ember_interrupt`. |
|110 | `Freezing Point` | done | Ice Last Chance damage bonus mirrors Blaze-style scaling (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_freezing_point_boosts_ice_damage_under_last_chance`. |
|111 | `Friend Guard` | done | Adjacent allies resist damage one step further with ability logs (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_friend_guard_resists_adjacent_ally_hit`. |
|112 | `Frighten` | done | Ability action lowers target Speed by 2 CS (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_frighten_lowers_speed`. |
|113 | `Frisk` | done | Ability action logs target types, ability, nature, level, and held items (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_frisk_reveals_target_details`. |
|114 | `Frostbite` | done | Ice attacks add Slowed on 18+, extend Freeze range, and add Freeze on 20 (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_frostbite_slows_and_extends_freeze`. |
|115 | `Fur Coat` | done | Physical attacks are resisted one step further (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_fur_coat_resists_physical_attacks`. |
|116 | `Gale Wings` | done | Flying moves gain Priority 1 when the base ability is present (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gale_wings_grants_priority_to_flying_moves`. |
|117 | `Gale Wings [SuMo Errata]` | done | Quick Attack becomes Flying-type with a type-change log (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gale_wings_sumo_turns_quick_attack_flying`. |
|118 | `Gardener` | done | Ability action improves soil quality on plant tiles (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gardener_improves_soil_quality`. |
|119 | `Gentle Vibe` | done | Ability action resets combat stages and clears volatile statuses in Burst 2 (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gentle_vibe_resets_stages_and_cures_volatile`. |
|120 | `Gluttony` | done | Food buff storage caps at three while respecting Berry Storage (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gluttony_allows_three_food_buffs`. |
|121 | `Gooey` | done | Contact hits drop attacker Speed by -1 CS (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gooey_lowers_speed_on_contact`. |
|122 | `Gore` | done | Horn Attack gains crit range 18-20 and pushes 1m (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gore_pushes_and_extends_crit_range`. |
|123 | `Grass Pelt` | done | Grants +5 damage reduction on grassy rough/slow tiles (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_grass_pelt_reduces_damage_on_grassy_rough_tile`. |
|124 | `Gulp` | done | Ability action heals 25% max HP and removes one injury (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_gulp_heals_and_removes_injury`. |
|125 | `Guts` | done | Applies +2 Attack CS while afflicted and reverts when cured (`auto_ptu/rules/hooks/abilities/phase_effects.py`); test `tests/test_battle_state.py::test_guts_boosts_attack_while_afflicted`. |
|126 | `Harvest` | done | Berry food buffs may persist on a coin flip or in sun (`auto_ptu/rules/battle_state.py`); tests `tests/test_battle_state.py::test_harvest_preserves_berry_buff_on_heads` and `tests/test_battle_state.py::test_harvest_consumes_berry_buff_on_tails`. |
|127 | `Haunt` | done | Ghost Last Chance damage bonus mirrors Blaze-style scaling (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_haunt_boosts_ghost_damage_under_last_chance`. |
|128 | `Hay Fever` | done | Status moves and sleep triggers release pollen damage in Burst 2 (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_hay_fever_triggers_on_status_move`. |
|129 | `Healer` | done | Ability action cures adjacent allies of status conditions via `_remove_statuses_by_set` in `auto_ptu/rules/battle_state.py`, with the accompanying move defined in `auto_ptu/rules/abilities/ability_moves.py` and coverage in `tests/test_battle_state.py::test_healer_cures_adjacent_target_status_conditions`. |
|130 | `Heat Mirage` | done | Fire-type moves provide +3 evasion until the next turn by applying an `evasion_bonus` entry from `_resolve_move_targets` and logging the trigger in `auto_ptu/rules/battle_state.py`; regression coverage is `tests/test_battle_state.py::test_heat_mirage_grants_evasion_after_fire_move`. |
|131 | `Heatproof` | done | Resists Fire moves one step further in `auto_ptu/rules/battle_state.py` while burn ticks are already halved there; test `tests/test_battle_state.py::test_heatproof_resists_fire_attacks`. |
|132 | `Heavy Metal` | done | Weight class calculation adds +2 in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_heavy_metal_increases_weight_class`. |
|133 | `Helper` | done | Single-target ally moves grant +1 accuracy and skill bonus until next turn in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_helper_grants_accuracy_and_skill_bonus`. |
|134 | `Honey Paws` | done | Using Honey converts it into a Leftovers-style food buff without the usual limit in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_honey_paws_consumes_honey_for_leftovers_buff`. |
|135 | `Honey Thief` | done | Bug Bite grants a tick of temp HP when stealing a food buff in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_honey_thief_grants_temp_hp_on_bug_bite`. |
|136 | `Huge Power` | done | Attack stat scalar doubles base Attack in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_huge_power_doubles_attack_damage`. |
|137 | `Hustle` | done | Physical accuracy penalty and +10 physical damage in `auto_ptu/rules/calculations.py`; tests `tests/test_battle_state.py::test_hustle_penalizes_physical_accuracy` and `tests/test_battle_state.py::test_hustle_boosts_physical_damage`. |
|138 | `Hydration` | done | End-phase rain cures one status affliction in `auto_ptu/rules/hooks/abilities/phase_effects.py`; test `tests/test_battle_state.py::test_hydration_cures_status_in_rain`. |
|139 | `Hyper Cutter` | done | Attack combat stage drops are blocked in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_hyper_cutter_blocks_attack_drop`. |
|140 | `Hypnotic` | done | Hypnosis auto-hits via `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_hypnotic_makes_hypnosis_hit`. |
|141 | `Ice Body` | done | Start-phase hail/snow heals in `auto_ptu/rules/hooks/abilities/phase_effects.py` and hail damage skip in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_ice_body_heals_and_ignores_hail`. |
|142 | `Ice Shield` | done | Ability move and blocker placement in `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_ice_shield_places_blocking_segments`. |
|143 | `Ignition Boost` | done | Adjacent Fire move +5 damage with Aura Break suppression in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_ignition_boost_adds_damage_for_adjacent_fire_move`. |
|144 | `Illuminate` | done | Accuracy penalty for attacks targeting the user unless Blindsense in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_illuminate_accuracy_penalty_respects_blindsense`. |
|145 | `Illusion` | done | Ability moves to mark/shift + damage break in `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_illusion_marks_shift_and_breaks_on_damage`. |
|146 | `Immunity` | done | Poison/Badly Poisoned prevention in `_apply_status` and Toxic Spikes guard in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_immunity_blocks_poison_status`. |
|147 | `Impostor` | done | Entry hook copies combat stages and entrains a target ability in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_impostor_copies_stages_and_ability_on_entry`. |
|148 | `Infiltrator` | done | Stealth bonus, hazard ignore, substitute/buff bypass in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_infiltrator_bypasses_substitute_for_status_moves`. |
|149 | `Inner Focus` | done | Flinch immunity and Bashed prevention in `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_inner_focus_blocks_flinch`. |
|150 | `Insomnia` | done | Sleep immunity and Rest block in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_insomnia_blocks_rest`. |
|151 | `Instinct` | done | Default evasion +2 in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_instinct_increases_evasion`. |
|152 | `Interference` | done | Ability move applies accuracy penalties until next turn in `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_interference_applies_accuracy_penalty`. |
|157 | `Kampfgeist` | done | Fighting STAB applies to non-Fighting users in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_kampfgeist_grants_fighting_stab`. |
|158 | `Keen Eye` | done | Accuracy stage immunity/bonus and duration bump live in `auto_ptu/rules/calculations.py` + `auto_ptu/rules/battle_state.py`; tests `tests/test_battle_state.py::test_keen_eye_adds_accuracy_and_blocks_accuracy_drop` and `tests/test_battle_state.py::test_keen_eye_extends_accuracy_drop_duration`. |
|168 | `Light Metal` | done | Weight class reduction is applied in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_light_metal_reduces_weight_class`. |
|179 | `Magma Armor` | done | Contact ticks and freeze/frostbite immunity added in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_magma_armor_contact_tick_and_freeze_immunity`. |
|194 | `Motor Drive` | done | Electric hits are absorbed and grant Speed +1 CS in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_motor_drive_absorbs_electric_and_boosts_speed`. |
|196 | `Moxie` | done | KO triggers Attack +1 CS in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_moxie_raises_attack_on_ko`. |
|155 | `Iron Fist` | done | Punch-trait list sourced from Foundry (`auto_ptu/tools/generate_punch_moves.py`) drives the 30% damage scalar in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_iron_fist_boosts_punch_damage`. |
|156 | `Justified` | done | Dark hits raise Attack by +1 CS in the damage-resolution hooks of `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_justified_raises_attack_on_dark_hit`. |
|162 | `Last Chance` | done | Normal attacks gain the Blaze-style 20%/50% bonus in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_last_chance_boosts_normal_damage_under_low_hp`. |
|164 | `Leaf Guard` | done | Sunny weather blocks major status afflictions in `_apply_status` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_leaf_guard_blocks_major_status_in_sun`. |
|171 | `Limber` | done | Paralysis immunity added to `_apply_status` in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_limber_blocks_paralysis`. |
|172 | `Liquid Ooze` | done | Drain healing is reversed into damage in `_apply_drain_on_damage` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_liquid_ooze_reverses_drain_healing`. |
|173 | `Overgrow` | done | Last Chance damage bonus for Grass moves in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_overgrow_boosts_grass_damage_under_last_chance`. |
|174 | `Torrent` | done | Last Chance damage bonus for Water moves in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_torrent_boosts_water_damage_under_last_chance`. |
|175 | `Swarm` | done | Last Chance damage bonus for Bug moves in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_swarm_boosts_bug_damage_under_last_chance`. |
|176 | `Rock Head` | done | Recoil/crash damage ignored in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_rock_head_ignores_recoil`. |
|177 | `Reckless` | done | Recoil/crash moves gain 30% damage scalar via `auto_ptu/rules/calculations.py` and `auto_ptu/rules/move_traits.py`; test `tests/test_battle_state.py::test_reckless_boosts_recoil_damage`. |
|178 | `Technician` | done | Low-DB attacks (<= 6) gain 50% damage scalar in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_technician_boosts_low_power_damage`. |
|179 | `Skill Link` | done | Multi-strike moves hit the maximum number of strikes in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_skill_link_forces_max_strike_hits`. |
|217 | `Pickpocket` | done | Ability grants Thief as an ability move in `auto_ptu/rules/abilities/ability_moves.py`, reusing the existing Thief item-steal logic in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_pickpocket_grants_thief_move`. |
|223 | `Poison Point` | done | Added to the contact status hook mapping in `auto_ptu/rules/hooks/abilities/contact_effects.py` so contact hits can Poison on the shared 30% roll; test `tests/test_battle_state.py::test_poison_point_poisons_attacker_on_contact`. |

## Additional Abilities (2026-02-07 Batch)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
|159 | `Klutz` | done | Ignores held item effects by skipping held-item processing in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_klutz_ignores_air_balloon`. |
|160 | `Klutz [SwSh]` | done | Melee hits knock the target’s held item to the ground in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_klutz_swsh_knocks_item`. |
|161 | `Landslide` | done | Last Chance damage boost for Ground moves in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_landslide_boosts_ground_damage_under_last_chance`. |
|163 | `Leaf Gift` | done | Ability move crafts suits and grants abilities via `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_leaf_gift_grants_chosen_suit_abilities`. |
|165 | `Leek Mastery` | done | Acrobatics bonus in `auto_ptu/rules/calculations.py`, item theft blocked in `auto_ptu/rules/hooks/move_specials_items.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_leek_mastery_blocks_item_theft`. |
|167 | `Life Force` | done | Ability move restores a tick of HP in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_life_force_restores_tick`. |
|169 | `Lightning Kicks` | done | Ability move grants Kick priority via temp effects in `auto_ptu/rules/hooks/move_specials.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_lightning_kicks_grants_priority`. |
|173 | `Lullaby` | done | Ability move primes Sing to auto-hit in `auto_ptu/rules/hooks/move_specials.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_lullaby_makes_sing_auto_hit`. |
|174 | `Lunchbox` | done | Food-buff trade grants +5 temp HP in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_lunchbox_adds_temp_hp_on_food_buff_trade`. |
|175 | `Mach Speed` | done | Last Chance damage boost for Flying moves in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_mach_speed_boosts_flying_damage_under_last_chance`. |
|176 | `Magic Bounce` | done | Status reflection in `_apply_status` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_magic_bounce_reflects_status`. |
|177 | `Magic Guard` | done | Blocks hazard/weather/status/recoil/contact damage across `auto_ptu/rules/battle_state.py`, `auto_ptu/rules/hooks/abilities/contact_effects.py`, and `auto_ptu/rules/hooks/abilities/phase_effects.py`; test `tests/test_battle_state.py::test_magic_guard_blocks_hazard_damage`. |
|178 | `Magician` | done | Damaging single-target hits steal items in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_magician_steals_item_on_hit`. |
|180 | `Magnet Pull` | done | Ability move restricts Steel targets’ shift distance in `auto_ptu/rules/hooks/move_specials.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_magnet_pull_restricts_shift_distance`. |
|181 | `Marvel Scale` | done | Defense boost while afflicted handled in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_marvel_scale_boosts_defense_while_afflicted`. |

## Additional Abilities (2026-02-07 Batch 2)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
|182 | `Mega Launcher` | done | Pulse moves gain +2 DB via the ability hook registry in `auto_ptu/rules/hooks/ability_hooks.py` with pre-damage wiring in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_mega_launcher_boosts_pulse_move_db`. |
|183 | `Memory Wipe` | done | Ability move disables the target's last move in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_memory_wipe_disables_last_move`. |
|184 | `Migraine` | done | Low-HP Telekinetic capability and Psychic STAB are applied in `auto_ptu/rules/battle_state.py` + `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_migraine_grants_telekinetic_capability`. |
|185 | `Mimitree` | done | Mimic frequency usage is restored in `UseMoveAction.resolve` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_mimitree_ignores_mimic_frequency`. |
|186 | `Mind Mold` | done | Last Chance bonus for Psychic moves in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_mind_mold_boosts_psychic_damage_under_last_chance`. |
|187 | `Mini-Noses` | done | Ability move deploys proxy origins in `auto_ptu/rules/hooks/move_specials.py` and ranged origins in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_mini_noses_deploys_adjacent_origins`. |
|188 | `Minus` | done | Ability move boosts allied Plus users in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_minus_boosts_plus_user_special_attack`. |
|189 | `Minus [SwSh]` | done | Extra stat drops are applied in `_apply_combat_stage` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_minus_swsh_intensifies_stat_drop`. |
|190 | `Miracle Mile` | done | Last Chance bonus for Fairy moves in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_miracle_mile_boosts_fairy_damage_under_last_chance`. |
|191 | `Mojo` | done | Ghost moves bypass Normal immunity via type multiplier override in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_mojo_allows_ghost_damage_on_normal_targets`. |

## Additional Abilities (2026-02-10 Batch)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
| 1 | `Electric Surge` | done | Ability move sets Electric Terrain for one round via `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_electric_surge_sets_terrain`. |
| 2 | `Grassy Surge` | done | Ability move sets Grassy Terrain for one round via `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/hooks/move_specials.py`. |
| 3 | `Misty Surge` | done | Ability move sets Misty Terrain for one round via `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/hooks/move_specials.py`. |
| 4 | `Psychic Surge` | done | Ability move sets Psychic Terrain for one round via `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/hooks/move_specials.py`. |
| 5 | `Soundproof` | done | Blocks Sonic moves in `auto_ptu/rules/abilities/damage_effects.py`; test `tests/test_battle_state.py::test_soundproof_blocks_sonic_moves`. |
| 6 | `Thick Fat` | done | Resists Fire/Ice damage in `auto_ptu/rules/hooks/abilities/defender_resists.py`. |
| 7 | `Volt Absorb` | done | Electric hits heal and negate damage in `auto_ptu/rules/hooks/abilities/post_result_absorb.py`; test `tests/test_battle_state.py::test_volt_absorb_heals_and_blocks_damage`. |
| 8 | `Water Veil` | done | Blocks Burn in `_apply_status` (`auto_ptu/rules/battle_state.py`). |
| 9 | `Water Bubble` | done | Fire resistance in `defender_resists`, Burn immunity in `_apply_status`, and melee Water bonus in `battle_state.py` + `calculations.py`. |
|10 | `Full Metal Body` | done | Prevents combat stage drops from foes in `_apply_combat_stage` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_full_metal_body_blocks_combat_stage_drop`. |
|11 | `Mirror Armor` | done | Reflects combat stage drops in `_apply_combat_stage` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_mirror_armor_reflects_combat_stage_drop`. |
|12 | `Storm Drain` | done | Redirects ranged Water moves and absorbs them with Sp. Atk boost (`auto_ptu/rules/battle_state.py`, `auto_ptu/rules/hooks/abilities/post_result_absorb.py`). |
|13 | `Ice Scales` | done | Resists Special damage in `auto_ptu/rules/hooks/abilities/defender_resists.py`. |
|14 | `Pastel Veil` | done | Blocks Poison for nearby allies in `_apply_status` (`auto_ptu/rules/battle_state.py`). |
|15 | `Sweet Veil` | done | Blocks Sleep for nearby allies in `_apply_status` (`auto_ptu/rules/battle_state.py`). |
|16 | `Wonder Guard` | done | Blocks non-super-effective damage in `auto_ptu/rules/abilities/damage_effects.py`; test `tests/test_battle_state.py::test_wonder_guard_blocks_neutral_damage`. |
|17 | `Wonder Skin` | done | Applies status-move evasion bonus in `auto_ptu/rules/abilities/accuracy_effects.py`. |
|18 | `Unburden` | done | Speed +2 CS while no held item via phase hooks in `auto_ptu/rules/hooks/abilities/phase_effects.py`. |
|19 | `Tough Claws` | done | Melee moves gain +2 DB via `auto_ptu/rules/calculations.py`. |
|20 | `Punk Rock` | done | Sonic moves gain +2 DB and resist Sonic damage via `auto_ptu/rules/calculations.py` + `auto_ptu/rules/hooks/abilities/defender_resists.py`. |
|21 | `Prism Armor` | done | Super-effective hits lose 5 damage via `auto_ptu/rules/hooks/abilities/defender_resists.py`. |
|22 | `Dragon's Maw` | done | Type multiplier shifts +1 step for Dragon hits via `auto_ptu/rules/hooks/abilities/type_multiplier_shift.py`. |
|23 | `Transistor` | done | Type multiplier shifts +1 step for Electric hits via `auto_ptu/rules/hooks/abilities/type_multiplier_shift.py`. |
|24 | `White Smoke` | done | Prevents combat stage drops from foes in `_apply_combat_stage` (`auto_ptu/rules/battle_state.py`). |

## Additional Abilities (2026-02-11 Batch)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
| 1 | `Fluffy` | done | Resists melee damage and weakens Fire resistance via `auto_ptu/rules/hooks/abilities/defender_resists.py`; test `tests/test_battle_state.py::test_fluffy_adjusts_melee_and_fire`. |
| 2 | `Galvanize` | done | Normal attacks convert to Electric in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_galvanize_changes_normal_moves`. |
| 3 | `Glisten` | done | Fairy immunity + defensive CS in `auto_ptu/rules/abilities/damage_effects.py`; test `tests/test_battle_state.py::test_glisten_blocks_fairy_and_boosts_def`. |
| 4 | `Liquid Voice` | done | Sonic moves convert to Water/Friendly in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_liquid_voice_converts_sonic_to_water`. |
| 5 | `Long Reach` | done | Damaging moves gain range 8 in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_long_reach_allows_melee_at_range`. |
| 6 | `Merciless` | done | Criticals vs Poisoned targets in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_merciless_crits_poisoned_targets`. |
| 7 | `Stamina` | done | Ability move in `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_stamina_raises_defense`. |

## Additional Abilities (2026-02-11 Batch 2)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
| 1 | `Mold Breaker` | done | Ignores defender abilities during accuracy/immunity checks via `auto_ptu/rules/battle_state.py` + `auto_ptu/rules/abilities/damage_effects.py`; test `tests/test_battle_state.py::test_mold_breaker_ignores_levitate`. |
| 2 | `Moody` | done | End-phase stat swings in `auto_ptu/rules/hooks/abilities/phase_effects.py`; test `tests/test_battle_state.py::test_moody_changes_stats_on_end`. |
| 3 | `Mountain Peak` | done | Last Chance Rock damage bonus in `auto_ptu/rules/hooks/abilities/last_chance_bonuses.py`; test `tests/test_battle_state.py::test_mountain_peak_bonus_at_low_hp`. |
| 4 | `Mud Dweller` | done | Ground/Water resistance in `auto_ptu/rules/hooks/abilities/defender_resists.py`; test `tests/test_battle_state.py::test_mud_dweller_resists_ground_and_water`. |
| 5 | `Multiscale` | done | Full-HP damage resistance in `auto_ptu/rules/hooks/abilities/defender_resists.py`; test `tests/test_battle_state.py::test_multiscale_halves_damage_at_full_hp`. |
| 6 | `Multitype` | done | Item-driven type swaps in `auto_ptu/rules/hooks/abilities/phase_effects.py`; test `tests/test_battle_state.py::test_multitype_changes_type_from_item`. |
| 7 | `Mummy` | done | Contact ability replacement in `auto_ptu/rules/hooks/abilities/contact_effects.py`; test `tests/test_battle_state.py::test_mummy_replaces_attacker_ability_on_contact`. |
| 8 | `Natural Cure` | done | Status cleanse on recall/breather in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_natural_cure_cleanses_on_switch`. |
| 9 | `No Guard` | done | Auto-hit logic in `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_no_guard_forces_hit`. |
|10 | `Normalize` | done | Move type conversion in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_normalize_changes_move_type`. |
|11 | `Oblivious` | done | Blocks Enraged/Infatuated in `_apply_status` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_oblivious_blocks_infatuation`. |
|12 | `Odious Spray` | done | Poison Gas tweak + flinch in `auto_ptu/rules/battle_state.py` + `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_odious_spray_flinches_on_poison_gas`. |
|13 | `Omen` | done | Ability move in `auto_ptu/rules/abilities/ability_moves.py` + `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_omen_lowers_accuracy`. |
|14 | `Overcharge` | done | Last Chance Electric damage bonus in `auto_ptu/rules/hooks/abilities/last_chance_bonuses.py`; test `tests/test_battle_state.py::test_overcharge_bonus_at_low_hp`. |
|15 | `Overcoat` | done | Powder/status + weather immunity in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_overcoat_blocks_powder_and_weather`. |

## Additional Abilities (2026-02-11 Batch 3)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
| 1 | `Effect Spore` | done | Contact spore roll in `auto_ptu/rules/hooks/abilities/contact_effects.py`; test `tests/test_battle_state.py::test_effect_spore_rolls_status`. |
| 2 | `Flame Tongue` | done | Lick connection adds Burn + injury in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_flame_tongue_lick_burns_and_injures`. |
| 3 | `Iron Barbs` | done | Contact tick damage in `auto_ptu/rules/hooks/abilities/contact_effects.py`; test `tests/test_battle_state.py::test_iron_barbs_deals_tick`. |
| 4 | `Pack Hunt` | done | Ability move tick strike in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_pack_hunt_ability_move_deals_tick`. |
| 5 | `Parry` | done | Interrupt requires ready state in `auto_ptu/rules/hooks/abilities/pre_damage_interrupts.py`; test `tests/test_battle_state.py::test_parry_blocks_melee_attack_when_ready`. |
| 6 | `Perception` | done | Interrupt requires ready state in `auto_ptu/rules/hooks/abilities/pre_damage_interrupts.py`; test `tests/test_battle_state.py::test_perception_shifts_out_of_area`. |
| 7 | `Pickup` | done | Ability move roll logging in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_pickup_roll_logged`. |
| 8 | `Pixilate` | done | Ready-gated Normal-to-Fairy conversion in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_pixilate_ready_converts_normal_to_fairy`. |
| 9 | `Prime Fury` | done | Enrage + Attack CS in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_prime_fury_enrages_and_raises_attack`. |
|10 | `Probability Control` | done | Reroll activation + accuracy hook in `auto_ptu/rules/hooks/move_specials.py` + `auto_ptu/rules/calculations.py`; test `tests/test_battle_state.py::test_probability_control_reroll`. |
|11 | `Protean` | done | Ready-gated type shift in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_protean_ready_changes_type`. |
|12 | `Quick Cloak` | done | Burmy cloak action in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_quick_cloak_builds_burmy_cloak`. |
|13 | `Quick Curl` | done | Defense Curl swift marker in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_quick_curl_marks_defense_curl_swift`. |
|14 | `Rattled` | done | Ability move speed boost in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_rattled_ability_move_raises_speed`. |
|15 | `Refreshing Veil` | done | Scene-limited Aqua Ring cleanse in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_refreshing_veil_cures_on_aqua_ring`. |

## Additional Abilities (2026-02-11 Batch 4)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
| 1 | `Refridgerate` | done | Ready-gated Normal-to-Ice conversion via `auto_ptu/rules/abilities/ability_moves.py`, `auto_ptu/rules/hooks/move_specials.py`, and `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_refridgerate_ready_converts_normal_to_ice`. |
| 2 | `Root Down` | done | Ingrain-only temp HP gain in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_root_down_grants_temp_hp_with_ingrain`. |
| 3 | `Shackle` | done | Burst 3 movement halving with `movement_halved` and speed handling in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_shackle_halves_movement`. |
| 4 | `Shadow Tag` | done | Slowed/Trapped + anchor radius in `auto_ptu/rules/hooks/move_specials.py` with forced movement guard in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_shadow_tag_applies_anchor_and_statuses`. |
| 5 | `Shell Cannon` | done | Ready-gated accuracy/damage bonuses in `auto_ptu/rules/calculations.py`, `auto_ptu/rules/hooks/move_specials.py`, and `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_shell_cannon_ready_boosts_damage`. |
| 6 | `Shell Shield` | done | Interrupt Withdraw via `auto_ptu/rules/hooks/abilities/pre_damage_interrupts.py` + ability move in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_shell_shield_interrupt_applies_withdraw`. |
| 7 | `Sonic Courtship` | done | Attract cone + gender ignore via `auto_ptu/rules/hooks/move_specials.py` + `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_sonic_courtship_ignores_gender`. |
| 8 | `Soulstealer` | done | Post-KO heal/injury reset in `auto_ptu/rules/hooks/abilities/post_damage_effects.py`; test `tests/test_battle_state.py::test_soulstealer_heals_on_ko`. |
| 9 | `Sound Lance` | done | Ready-gated Supersonic damage in `auto_ptu/rules/hooks/move_specials.py`; test `tests/test_battle_state.py::test_sound_lance_deals_damage_when_ready`. |
|10 | `Spinning Dance` | done | Miss trigger evasion + shift in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_spinning_dance_triggers_on_miss`. |
|11 | `Spray Down` | done | Airborne knockdown via `auto_ptu/rules/hooks/abilities/post_damage_effects.py`; test `tests/test_battle_state.py::test_spray_down_knocks_airborne_targets`. |
|12 | `Steadfast` | done | Flinch speed boost in `_handle_status_phase_effects` (`auto_ptu/rules/battle_state.py`); test `tests/test_battle_state.py::test_steadfast_raises_speed_on_flinch`. |
|13 | `Sticky Smoke` | done | Smokescreen connection in `auto_ptu/rules/hooks/move_specials.py` with phase penalties in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_sticky_smoke_lowers_accuracy_on_start`. |
|14 | `Storm Drain` | done | Water redirection/absorb in `auto_ptu/rules/battle_state.py` + `auto_ptu/rules/hooks/abilities/post_result_absorb.py`; test `tests/test_battle_state.py::test_storm_drain_absorbs_water_and_boosts_spatk`. |
|15 | `Strange Tempo` | done | Confusion cure + stage boost move in `auto_ptu/rules/hooks/move_specials.py` with confusion skip in `auto_ptu/rules/battle_state.py`; test `tests/test_battle_state.py::test_strange_tempo_cures_confusion_and_raises_stat`. |

## Additional Abilities (2026-02-11 Batch 5)

| # | Ability | Status | Notes |
|---|---------|--------|-------|
| 1 | `Empower` | done | Action override in `auto_ptu/rules/hooks/move_specials_abilities.py` with cleanup in `auto_ptu/rules/hooks/abilities/phase_effects.py`; test `tests/test_battle_state.py::test_empower_allows_self_status_free_action`. |
| 2 | `Sun Blanket` | done | Tick heal gating in `auto_ptu/rules/hooks/move_specials_abilities.py`; test `tests/test_battle_state.py::test_sun_blanket_heals_on_low_hp`. |
| 3 | `Unnerve` | done | Swift suppression in `auto_ptu/rules/hooks/move_specials_abilities.py` with CS block in `auto_ptu/rules/hooks/abilities/combat_stage_reactions.py`; test `tests/test_battle_state.py::test_unnerve_blocks_positive_combat_stages`. |

## Errata + Corrections (2026-02-11 Batch)

- Implemented errata-specific actions and hooks for: Flare Boost [Errata], Flash Fire [Errata], Flower Gift [Errata], Flower Power [Errata], Flower Veil [Errata], Fox Fire [Errata], Frisk [Feb Errata], Frisk [SuMo Errata], Gale Wings [Errata], Gluttony [Errata], Gore [Errata], Grass Pelt [Errata], Heatproof [Errata], Heavy Metal [Errata], Honey Paws [Errata], Huge Power / Pure Power [Errata], Hustle [Errata], Hydration [Errata], Ice Body [Errata], Imposter [Errata], Prime Fury [Errata], Pumpkingrab [Errata], Quick Curl [Errata], Rain Dish [Errata], Rally [Errata], Rattled [Errata], Regal Challenge [Errata], Root Down [Errata], Sand Stream [Errata], Shackle [Errata], Shell Shield [Errata], Solar Power [Errata], Sonic Courtship [Errata], Soulstealer [Errata], Sound Lance [Errata], Spray Down [Errata], Starlight [Errata], Starswirl [Errata], Steadfast [Errata], Storm Drain [Errata], Suction Cups [Errata], Sumo Stance [Errata], Sunglow [Errata], Sun Blanket [Errata], Symbiosis [Errata], Toxic Boost [Errata], Transporter [Errata], Unnerve [Errata], and Zen Mode [Errata].
- Corrected base behaviors where errata diverged: Sun Blanket (static Fire resistance + sun tick heal), Unnerve (passive suppression aura), Soulstealer (KO healing scaling), Solar Power (errata handling vs base), Root Down (errata vs base), and updated logging/action-type mappings for errata variants.


## 2026-02-11 Batch 2
- Spinning Dance now resolves as an ability action (evasion + shift) and no longer triggers on misses.
- Soulstealer and Soulstealer [Errata] now trigger on any successful hit with KO-specific healing logic.
- Spray Down no longer requires ranged single-target hits to ground foes.
- Stalwart now triggers on any damaging hit (scene-limited) and preserves intercept/targeting locks.
- Heliovolt, Gorilla Tactics, and Psionic Screech are now explicit ability actions (with pending/active state handling).
- Gulp Missile readiness now only triggers from Stockpile, per connection text.
- Vicious now supports the critical-range option via a temporary choice flag.
