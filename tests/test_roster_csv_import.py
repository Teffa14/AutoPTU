from pathlib import Path
import random

from auto_ptu.api.engine_facade import EngineFacade
from auto_ptu.csv_repository import PTUCsvRepository
from auto_ptu.rules.calculations import defensive_stat
from auto_ptu.roster_csv import (
    campaign_from_roster_csv,
    campaign_from_roster_csv_file,
    match_plan_from_roster_csv,
)


def test_campaign_from_roster_csv_builds_expected_teams_and_order():
    csv_text = """side,slot,species,level,ability,item,move1,move2
foe,2,Squirtle,18,Torrent,Oran Berry,Tackle,Water Gun
player,2,Eevee,22,Run Away,Oran Berry,Tackle,Quick Attack
player,1,Pikachu,25,Static,Light Ball,Thunder Shock,Quick Attack
foe,1,Bulbasaur,19,Overgrow,Oran Berry,Vine Whip,Tackle
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    assert spec.metadata.get("source") == "roster_csv"
    assert [mon.species for mon in spec.players] == ["Pikachu", "Eevee"]
    assert [mon.species for mon in spec.foes] == ["Bulbasaur", "Squirtle"]

    pikachu = spec.players[0]
    assert pikachu.abilities and pikachu.abilities[0].get("name") == "Static"
    assert pikachu.items and pikachu.items[0].get("name") == "Light Ball"
    assert [move.name for move in pikachu.moves][:2] == ["Thunder Shock", "Quick Attack"]


def test_campaign_from_roster_csv_file_reads_from_disk(tmp_path: Path):
    csv_text = """side,species,level
player,Pikachu,30
foe,Squirtle,30
"""
    path = tmp_path / "roster.csv"
    path.write_text(csv_text, encoding="utf-8")

    spec = campaign_from_roster_csv_file(path=path)
    assert len(spec.players) == 1
    assert len(spec.foes) == 1
    assert spec.players[0].species == "Pikachu"
    assert spec.foes[0].species == "Squirtle"


def test_engine_facade_start_encounter_accepts_roster_csv_text():
    csv_text = """side,species,level
player,Pikachu,30
foe,Squirtle,30
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=77)

    assert snapshot["status"] == "ok"
    species = {entry["species"] for entry in snapshot["combatants"]}
    assert "Pikachu" in species
    assert "Squirtle" in species


def test_engine_facade_runtime_specs_include_struggle_for_all_combatants():
    csv_text = """side,species,level,move1
player,Wobbuffet,30,Counter
foe,Sigilyph,30,Gust
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=104)

    assert snapshot["status"] == "ok"
    assert facade.battle is not None
    for state in facade.battle.pokemon.values():
        move_names = {move.name for move in state.spec.moves}
        assert "Struggle" in move_names


def test_engine_facade_stop_battle_returns_result_and_clears_state():
    csv_text = """side,species,level,move1
player,Pikachu,30,Thunder Shock
foe,Squirtle,30,Tackle
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=105)

    assert snapshot["status"] == "ok"
    result = facade.stop_battle()
    assert result["status"] == "ok"
    assert result["stopped"] is True
    assert result["result"]["round"] >= 1
    assert facade.battle is None


def test_engine_facade_snapshot_exposes_full_log_history():
    csv_text = """side,species,level,move1
player,Pikachu,30,Thunder Shock
foe,Squirtle,30,Tackle
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=106)

    assert snapshot["status"] == "ok"
    assert facade.battle is not None
    facade.battle.log = [{"type": "move", "round": idx + 1, "actor": "ash-1", "move": f"Move {idx}"} for idx in range(250)]
    refreshed = facade.snapshot()
    assert len(refreshed["log"]) == 250


def test_engine_facade_snapshot_exposes_maneuvers_skills_and_creative_context():
    csv_text = """side,species,level,capability_1
player,Machop,30,Telekinetic
foe,Eevee,30,
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=107)
    if facade.battle is not None and facade.battle.current_actor_id in facade.battle.trainers:
        facade.battle.end_turn()
        facade.battle.advance_turn()
        snapshot = facade.snapshot()

    assert snapshot["status"] == "ok"
    assert any(entry["name"] == "Grapple" for entry in snapshot["maneuvers"])
    assert "creative_rulebook" in snapshot["maneuver_context"]
    player = next(entry for entry in snapshot["combatants"] if entry["team"] == "player")
    assert isinstance(player["skills"], dict)
    assert isinstance(snapshot["maneuver_context"]["capability_suggestions"], list)


def test_engine_facade_commit_action_supports_creative_action():
    csv_text = """side,species,level
player,Machop,30
foe,Eevee,30
    """
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=108)
    if facade.battle is not None and facade.battle.current_actor_id in facade.battle.trainers:
        facade.battle.end_turn()
        facade.battle.advance_turn()
        snapshot = facade.snapshot()

    assert snapshot["status"] == "ok"
    assert facade.battle is not None
    actor = next(state for state in facade.battle.pokemon.values() if state.spec.species == "Machop")
    actor.spec.skills["athletics"] = 4
    refreshed = facade.commit_action(
        {
            "type": "creative_action",
            "actor_id": facade.battle.current_actor_id,
            "title": "Leap Into Advantage",
            "description": "Use the terrain to gain a better angle.",
            "skill": "athletics",
            "dc": 8,
        }
    )

    assert refreshed["status"] == "ok"
    creative_events = [entry for entry in facade.battle.log if entry.get("type") == "creative_action"]
    assert creative_events
    assert creative_events[-1]["title"] == "Leap Into Advantage"


def test_engine_facade_creative_action_applies_consequence():
    csv_text = """side,species,level
player,Machop,30
foe,Eevee,30
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=109)
    if facade.battle is not None and facade.battle.current_actor_id in facade.battle.trainers:
        facade.battle.end_turn()
        facade.battle.advance_turn()
        snapshot = facade.snapshot()

    assert snapshot["status"] == "ok"
    assert facade.battle is not None
    actor = facade.battle.pokemon[facade.battle.current_actor_id]
    actor.spec.skills["combat"] = 4
    target_id = next(pid for pid in facade.battle.pokemon if pid != facade.battle.current_actor_id)
    facade.commit_action(
        {
            "type": "creative_action",
            "actor_id": facade.battle.current_actor_id,
            "title": "Sweep the Leg",
            "description": "A dirty low strike.",
            "skill": "combat",
            "dc": 8,
            "target_id": target_id,
            "consequence": "trip_target",
        }
    )

    assert facade.battle.pokemon[target_id].has_status("Tripped")


def test_engine_facade_creative_action_supports_explicit_opposed_check_mode_and_push():
    csv_text = """side,species,level
player,Machop,30
foe,Eevee,30
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=110)
    if facade.battle is not None and facade.battle.current_actor_id in facade.battle.trainers:
        facade.battle.end_turn()
        facade.battle.advance_turn()
        snapshot = facade.snapshot()

    assert snapshot["status"] == "ok"
    assert facade.battle is not None
    actor_id = facade.battle.current_actor_id
    actor = facade.battle.pokemon[actor_id]
    actor.spec.skills["athletics"] = 4
    target_id = next(pid for pid in facade.battle.pokemon if pid != actor_id)
    target = facade.battle.pokemon[target_id]
    target.spec.skills["athletics"] = 1
    class FixedRng(random.Random):
        def randint(self, a, b):
            return b
    facade.battle.rng = FixedRng()
    push_tile = None
    if target.position is not None:
        occupied = {
            mon.position
            for pid, mon in facade.battle.pokemon.items()
            if mon.active and not mon.fainted and mon.position is not None and pid != target_id
        }
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = (target.position[0] + dx, target.position[1] + dy)
            if not facade.battle.grid.in_bounds(candidate):
                continue
            if candidate in facade.battle.grid.blockers or candidate in occupied:
                continue
            push_tile = candidate
            break
    assert push_tile is not None
    refreshed = facade.commit_action(
        {
            "type": "creative_action",
            "actor_id": actor_id,
            "title": "Bull Rush",
            "description": "Win the contest and shove the foe backward.",
            "skill": "athletics",
            "target_id": target_id,
            "target_position": list(push_tile),
            "opposed_skill": "athletics",
            "check_mode": "opposed",
            "consequence": "push_target",
        }
    )

    assert refreshed["status"] == "ok"
    assert tuple(facade.battle.pokemon[target_id].position) == push_tile
    creative_events = [entry for entry in facade.battle.log if entry.get("type") == "creative_action"]
    assert creative_events
    assert creative_events[-1]["check_mode"] == "opposed"
    assert creative_events[-1]["consequence_applied"] == "push_target"


def test_engine_facade_deployment_overrides_reorder_starters_and_tile():
    csv_text = """side,slot,species,level
player,1,Pikachu,30
player,2,Eevee,30
player,3,Bulbasaur,30
foe,1,Squirtle,30
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=3,
        active_slots=1,
        seed=77,
        deployment_overrides={
            "player": {
                "active": ["Bulbasaur"],
                "start_positions": [[4, 3]],
            }
        },
    )

    player_active = next(
        combatant
        for combatant in snapshot["combatants"]
        if combatant["active"] and combatant["team"] == "player"
    )
    assert player_active["species"] == "Bulbasaur"
    assert tuple(player_active["position"]) == (4, 3)


def test_engine_facade_auto_selects_ai_starter_when_no_override():
    csv_text = """side,slot,species,level,move1
player,1,Magikarp,30,Splash
player,2,Pikachu,30,Thunder Shock
foe,1,Squirtle,30,Tackle
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=2,
        active_slots=1,
        seed=83,
        ai_mode="ai",
    )

    assert snapshot["status"] == "ok"
    player_active = next(
        combatant
        for combatant in snapshot["combatants"]
        if combatant["active"] and combatant["team"] == "player"
    )
    assert player_active["species"] == "Pikachu"


def test_engine_facade_item_choice_overrides_apply_stat_boosters_choice():
    csv_text = """side,species,level,item
player,Pikachu,30,Stat Boosters
foe,Squirtle,30,Oran Berry
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=1,
        active_slots=1,
        seed=81,
        item_choice_overrides={
            "player": {
                "Pikachu": {
                    "Stat Boosters": {
                        "chosen_stat": "spatk",
                    }
                }
            }
        },
    )

    assert snapshot["status"] == "ok"
    assert facade.battle is not None
    facade.battle.advance_turn()
    pikachu_state = next(state for state in facade.battle.pokemon.values() if state.spec.species == "Pikachu")
    assert pikachu_state.combat_stages.get("spatk") == 1


def test_engine_facade_item_choice_overrides_apply_eviolite_stats():
    csv_text = """side,species,level,item
player,Pikachu,30,Eviolite
foe,Squirtle,30,Oran Berry
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=1,
        active_slots=1,
        seed=82,
        item_choice_overrides={
            "player": {
                "Pikachu": {
                    "Eviolite": {
                        "chosen_stats": ["def", "spdef"],
                    }
                }
            }
        },
    )

    assert snapshot["status"] == "ok"
    assert facade.battle is not None
    facade.battle.advance_turn()
    pikachu_state = next(state for state in facade.battle.pokemon.values() if state.spec.species == "Pikachu")
    chosen_bonus_effects = [
        effect
        for effect in pikachu_state.get_temporary_effects("post_stage_stat_bonus")
        if effect.get("source") == "Eviolite"
    ]
    assert {effect.get("stat") for effect in chosen_bonus_effects} == {"def", "spdef"}
    assert all(effect.get("amount") == 5 for effect in chosen_bonus_effects)
    assert defensive_stat(pikachu_state, "physical") >= pikachu_state.spec.defense + 5
    assert defensive_stat(pikachu_state, "special") >= pikachu_state.spec.spdef + 5


def test_engine_facade_ability_choice_overrides_apply_color_theory():
    csv_text = """side,species,level,ability1
player,Smeargle,30,Color Theory
foe,Squirtle,30,Torrent
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=1,
        active_slots=1,
        seed=84,
        ability_choice_overrides={
            "player": {
                "Smeargle": {
                    "Color Theory": {
                        "color_theory_roll": 10,
                        "color_theory_color": "Blue-Violet",
                    }
                }
            }
        },
    )

    assert snapshot["status"] == "ok"
    smeargle = next(entry for entry in snapshot["combatants"] if entry["species"] == "Smeargle")
    assert smeargle["color_theory"]["color"] == "Blue-Violet"
    assert smeargle["color_theory"]["roll"] == 10
    assert smeargle["max_hp"] > 30 + (3 * 6) + 10


def test_engine_facade_ability_choice_overrides_apply_serpents_mark_and_fabulous_trim():
    csv_text = """side,species,level,ability1
player,Arbok,30,Serpent's Mark
player,Furfrou,30,Fabulous Trim
foe,Squirtle,30,Torrent
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=2,
        active_slots=2,
        seed=85,
        ability_choice_overrides={
            "player": {
                "Arbok": {
                    "Serpent's Mark": {
                        "serpents_mark_roll": 6,
                        "serpents_mark_pattern": "Stealth Pattern",
                    }
                },
                "Furfrou": {
                    "Fabulous Trim": {
                        "fabulous_trim_style": "Diamond Trim",
                    }
                },
            }
        },
    )

    assert snapshot["status"] == "ok"
    arbok = next(entry for entry in snapshot["combatants"] if entry["species"] == "Arbok")
    furfrou = next(entry for entry in snapshot["combatants"] if entry["species"] == "Furfrou")
    assert arbok["serpents_mark"]["pattern"] == "Stealth Pattern"
    assert arbok["serpents_mark"]["roll"] == 6
    assert furfrou["fabulous_trim"]["style"] == "Diamond Trim"


def test_engine_facade_snapshot_exposes_passive_item_effects_and_effective_stats():
    csv_text = """side,species,level,item
player,Pikachu,30,Eviolite
foe,Squirtle,30,Leftovers
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=1,
        active_slots=1,
        seed=86,
        item_choice_overrides={
            "player": {
                "Pikachu": {
                    "Eviolite": {
                        "chosen_stats": ["def", "spdef"],
                    }
                }
            }
        },
    )

    assert snapshot["status"] == "ok"
    pikachu = next(entry for entry in snapshot["combatants"] if entry["species"] == "Pikachu")
    squirtle = next(entry for entry in snapshot["combatants"] if entry["species"] == "Squirtle")

    assert "effective_stats" in pikachu
    assert pikachu["effective_stats"]["def"] >= pikachu["stats"]["def"] + 5
    assert pikachu["effective_stats"]["spdef"] >= pikachu["stats"]["spdef"] + 5
    assert any("Chosen stats: Def, SpDef" == effect for effect in pikachu["passive_item_effects"])
    assert any(item["name"] == "Eviolite" and "Eviolite grants +5 post-stage to each chosen stat" in item["effect_summary"] for item in pikachu["items"])
    assert any(item["name"] == "Leftovers" and any("Heals 1/16 max HP at turn start" == effect for effect in item["effect_summary"]) for item in squirtle["items"])


def test_engine_facade_ability_choice_overrides_apply_giver_preference():
    csv_text = """side,species,level,ability1,move1
player,Delibird,30,Giver,Present
foe,Squirtle,30,Torrent,Tackle
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        team_size=1,
        active_slots=1,
        seed=86,
        ability_choice_overrides={
            "player": {
                "Delibird": {
                    "Giver": {
                        "giver_choice_roll": 5,
                    }
                }
            }
        },
    )

    assert snapshot["status"] == "ok"
    delibird = next(entry for entry in snapshot["combatants"] if entry["species"] == "Delibird")
    assert delibird["giver_state"]["preference_roll"] == 5
    assert delibird["giver_state"]["preference_mode"] == "Damage"


def test_engine_facade_start_encounter_accepts_roster_csv_path(tmp_path: Path):
    csv_text = """side,species,level
player,Pikachu,30
foe,Squirtle,30
"""
    csv_path = tmp_path / "teams.csv"
    csv_path.write_text(csv_text, encoding="utf-8")

    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv_path=str(csv_path), team_size=1, active_slots=1, seed=78)

    assert snapshot["status"] == "ok"
    species = {entry["species"] for entry in snapshot["combatants"]}
    assert "Pikachu" in species
    assert "Squirtle" in species


def test_campaign_from_roster_csv_accepts_single_team_file():
    csv_text = """side,species,level
player,Pikachu,30
player,Eevee,30
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    assert spec.metadata.get("source") == "roster_csv"
    assert spec.metadata.get("side_count") == 1
    assert [mon.species for mon in spec.players] == ["Pikachu", "Eevee"]
    assert spec.foes == []


def test_engine_facade_start_encounter_accepts_single_team_roster_csv():
    csv_text = """side,species,level
player,Pikachu,30
player,Eevee,30
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=2, active_slots=1, seed=79)

    assert snapshot["status"] == "ok"
    species = {entry["species"] for entry in snapshot["combatants"]}
    assert species == {"Pikachu", "Eevee"}


def test_match_plan_from_roster_csv_accepts_single_team_file():
    csv_text = """side,species,level
player,Pikachu,30
player,Eevee,30
"""
    plan = match_plan_from_roster_csv(csv_text=csv_text, active_slots=1)

    matchup = plan.matchups[0]
    sides = matchup.sides_or_default()
    assert len(sides) == 1
    assert [mon.species for mon in sides[0].pokemon] == ["Pikachu", "Eevee"]


def test_engine_facade_roster_csv_takes_precedence_over_random_generation():
    csv_text = """side,species,level
player,Pikachu,30
foe,Squirtle,30
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        random_battle=True,
        team_size=6,
        active_slots=1,
        min_level=80,
        max_level=100,
        seed=99,
    )
    species = {entry["species"] for entry in snapshot["combatants"]}
    assert "Pikachu" in species
    assert "Squirtle" in species


def test_roster_csv_stat_columns_override_species_stats():
    csv_text = """side,species,level,hp,atk,def,spatk,spdef,spd
player,Pikachu,30,14,9,8,13,11,15
foe,Squirtle,30,12,7,10,8,9,6
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    pikachu = spec.players[0]
    squirtle = spec.foes[0]

    assert pikachu.hp_stat == 14
    assert pikachu.atk == 9
    assert pikachu.defense == 8
    assert pikachu.spatk == 13
    assert pikachu.spdef == 11
    assert pikachu.spd == 15
    assert squirtle.hp_stat == 12
    assert squirtle.defense == 10
    assert squirtle.spd == 6


def test_engine_facade_roster_csv_stat_columns_reach_battle_snapshot():
    csv_text = """side,species,level,hp,atk,def,spatk,spdef,spd
player,Pikachu,30,14,9,8,13,11,15
foe,Squirtle,30,12,7,10,8,9,6
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=88)

    assert snapshot["status"] == "ok"
    pikachu = next(entry for entry in snapshot["combatants"] if entry["species"] == "Pikachu")
    assert pikachu["stats"]["hp"] == 14
    assert pikachu["stats"]["atk"] == 9
    assert pikachu["stats"]["def"] == 8
    assert pikachu["stats"]["spatk"] == 13
    assert pikachu["stats"]["spdef"] == 11
    assert pikachu["stats"]["spd"] == 15
    assert pikachu["max_hp"] == 82


def test_roster_csv_stat_columns_do_not_reduce_species_base_stats():
    csv_text = """side,species,level,hp,atk,def,spatk,spdef,spd
player,Pikachu,30,1,1,1,1,1,1
foe,Squirtle,30,1,1,1,1,1,1
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    pikachu = spec.players[0]
    squirtle = spec.foes[0]

    assert pikachu.hp_stat > 1
    assert pikachu.atk > 1
    assert pikachu.defense > 1
    assert pikachu.spatk > 1
    assert pikachu.spdef > 1
    assert pikachu.spd > 1
    assert squirtle.hp_stat > 1
    assert squirtle.defense > 1


def test_roster_csv_multiple_ability_and_item_columns_round_trip():
    csv_text = """side,species,level,ability1,ability2,item1,item2,move1,move2
player,Pikachu,30,Static,Lightning Rod,Light Ball,Oran Berry,Thunder Shock,Quick Attack
foe,Squirtle,30,Torrent,Rain Dish,Mystic Water,Oran Berry,Tackle,Water Gun
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    pikachu = spec.players[0]
    squirtle = spec.foes[0]

    assert [entry["name"] for entry in pikachu.abilities] == ["Static", "Lightning Rod"]
    assert [entry["name"] for entry in pikachu.items] == ["Light Ball", "Oran Berry"]
    assert [entry["name"] for entry in squirtle.abilities] == ["Torrent", "Rain Dish"]
    assert [entry["name"] for entry in squirtle.items] == ["Mystic Water", "Oran Berry"]


def test_poke_edge_grants_reach_engine_runtime_snapshot():
    csv_text = """side,species,level,poke_edge1,poke_edge2
player,Lucario,30,Aura Pulse,Mixed Power [9-15 Playtest]
foe,Abra,30,Psychic Navigator,
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=92)

    assert snapshot["status"] == "ok"
    lucario = next(entry for entry in snapshot["combatants"] if entry["species"] == "Lucario")
    abra = next(entry for entry in snapshot["combatants"] if entry["species"] == "Abra")
    battle = facade.battle
    assert battle is not None
    lucario_state = next(state for state in battle.pokemon.values() if state.spec.species == "Lucario")
    abra_state = next(state for state in battle.pokemon.values() if state.spec.species == "Abra")

    assert lucario_state.has_capability("Aura Pulse")
    assert "Twisted Power" in lucario["abilities"]
    assert abra_state.has_capability("Psychic Navigator")


def test_roster_csv_poke_edge_choice_columns_reach_specs_and_snapshot():
    csv_text = """side,species,level,move1,move2,ability1,poke_edge1,poke_edge2,poke_edge3,poke_edge_accuracy_training,poke_edge_advanced_connection,poke_edge_underdog_evolution,poke_edge_underdog_moves
player,Lucario,30,Aura Sphere,Quick Attack,Inner Focus,Accuracy Training,Advanced Connection,Underdog's Lessons,Aura Sphere,Inner Focus,Lucario,Extreme Speed;Bone Rush
foe,Abra,30,Confusion,,,Psychic Navigator,,,,
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)
    lucario_spec = spec.players[0]

    assert lucario_spec.poke_edge_choices["accuracy_training"] == ["Aura Sphere"]
    assert lucario_spec.poke_edge_choices["advanced_connection"] == ["Inner Focus"]
    assert lucario_spec.poke_edge_choices["underdog_lessons"]["evolution"] == "Lucario"
    assert lucario_spec.poke_edge_choices["underdog_lessons"]["moves"] == ["Extreme Speed", "Bone Rush"]

    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=93)
    lucario = next(entry for entry in snapshot["combatants"] if entry["species"] == "Lucario")

    assert lucario["poke_edge_choices"]["accuracy_training"] == ["Aura Sphere"]
    assert lucario["poke_edge_choices"]["advanced_connection"] == ["Inner Focus"]
    assert lucario["poke_edge_choices"]["underdog_lessons"]["evolution"] == "Lucario"
    assert lucario["poke_edge_choices"]["underdog_lessons"]["moves"] == ["Extreme Speed", "Bone Rush"]


def test_roster_csv_post_nature_stat_mode_matches_final_battle_stats():
    csv_text = """side,species,level,nature,stat_mode,hp,atk,def,spatk,spdef,spd
player,Pikachu,30,Adamant,post_nature,11,13,6,10,7,12
foe,Squirtle,30,Hardy,pre_nature,12,7,10,8,9,6
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=91)

    assert snapshot["status"] == "ok"
    pikachu = next(entry for entry in snapshot["combatants"] if entry["species"] == "Pikachu")
    assert pikachu["nature"] == "Adamant"
    assert pikachu["stats"]["hp"] == 11
    assert pikachu["stats"]["atk"] == 13
    assert pikachu["stats"]["spatk"] == 10


def test_roster_csv_tutor_points_column_reaches_pokemon_specs():
    csv_text = """side,species,level,tutor_points
player,Pikachu,30,5
foe,Squirtle,30,2
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    assert spec.players[0].tutor_points == 5
    assert spec.foes[0].tutor_points == 2


def test_engine_facade_roster_csv_tutor_points_reach_battle_snapshot():
    csv_text = """side,species,level,tutor_points
player,Pikachu,30,5
foe,Squirtle,30,2
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=92)

    assert snapshot["status"] == "ok"
    pikachu = next(entry for entry in snapshot["combatants"] if entry["species"] == "Pikachu")
    squirtle = next(entry for entry in snapshot["combatants"] if entry["species"] == "Squirtle")
    assert pikachu["tutor_points"] == 5
    assert squirtle["tutor_points"] == 2


def test_roster_csv_preserves_builder_metadata_fields():
    csv_text = """side,species,level,stat_mode,poke_edge1,poke_edge2,move1,move2,move_source1,move_source2
player,Pikachu,30,post_nature,Threaded,Pack Hunt,Thunder Shock,Quick Attack,level_up,tutor
foe,Squirtle,30,pre_nature,Stealthy,,Tackle,Water Gun,egg,level_up
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    pikachu = spec.players[0]
    squirtle = spec.foes[0]

    assert pikachu.stat_mode == "post_nature"
    assert squirtle.stat_mode == "pre_nature"
    assert [entry["name"] for entry in pikachu.poke_edges] == ["Threaded", "Pack Hunt"]
    assert [entry["name"] for entry in squirtle.poke_edges] == ["Stealthy"]
    assert pikachu.move_sources == {"thundershock": "level_up", "quickattack": "tutor"}
    assert squirtle.move_sources == {"tackle": "egg", "watergun": "level_up"}


def test_engine_facade_roster_csv_builder_metadata_reaches_snapshot():
    csv_text = """side,species,level,stat_mode,poke_edge1,poke_edge2,move1,move2,move_source1,move_source2
player,Pikachu,30,post_nature,Threaded,Pack Hunt,Thunder Shock,Quick Attack,level_up,tutor
foe,Squirtle,30,pre_nature,Stealthy,,Tackle,Water Gun,egg,level_up
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=93)

    assert snapshot["status"] == "ok"
    pikachu = next(entry for entry in snapshot["combatants"] if entry["species"] == "Pikachu")
    squirtle = next(entry for entry in snapshot["combatants"] if entry["species"] == "Squirtle")

    assert pikachu["level"] == 30
    assert squirtle["level"] == 30
    assert pikachu["stat_mode"] == "post_nature"
    assert squirtle["stat_mode"] == "pre_nature"
    assert pikachu["poke_edges"] == ["Threaded", "Pack Hunt"]
    assert squirtle["poke_edges"] == ["Stealthy"]
    assert pikachu["move_sources"] == {"thundershock": "level_up", "quickattack": "tutor"}
    assert squirtle["move_sources"] == {"tackle": "egg", "watergun": "level_up"}
    assert [move["source"] for move in pikachu["moves"][:2]] == ["level_up", "tutor"]
    assert [move["source"] for move in squirtle["moves"][:2]] == ["egg", "level_up"]


def test_roster_csv_supports_more_than_four_moves_and_sources():
    csv_text = """side,species,level,move1,move2,move3,move4,move5,move6,move_source1,move_source2,move_source3,move_source4,move_source5,move_source6
player,Porygon2,30,Conversion,Conversion2,Tackle,Sharpen,Psybeam,Agility,level_up,level_up,level_up,level_up,tutor,tutor
foe,Sawk,30,Bind,Leer,Bide,Focus Energy,Seismic Toss,,level_up,level_up,level_up,level_up,tutor,
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    porygon2 = spec.players[0]
    sawk = spec.foes[0]

    assert [move.name for move in porygon2.moves][:6] == [
        "Conversion",
        "Conversion2",
        "Tackle",
        "Sharpen",
        "Psybeam",
        "Agility",
    ]
    assert [move.name for move in sawk.moves][:5] == [
        "Bind",
        "Leer",
        "Bide",
        "Focus Energy",
        "Seismic Toss",
    ]
    assert porygon2.move_sources == {
        "conversion": "level_up",
        "conversion2": "level_up",
        "tackle": "level_up",
        "sharpen": "level_up",
        "psybeam": "tutor",
        "agility": "tutor",
    }
    assert sawk.move_sources["seismictoss"] == "tutor"


def test_engine_facade_roster_csv_more_than_four_moves_reaches_snapshot():
    csv_text = """side,species,level,move1,move2,move3,move4,move5,move6
player,Porygon2,30,Conversion,Conversion2,Tackle,Sharpen,Psybeam,Agility
foe,Sawk,30,Bind,Leer,Bide,Focus Energy,Seismic Toss,
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, team_size=1, active_slots=1, seed=94)

    assert snapshot["status"] == "ok"
    porygon2 = next(entry for entry in snapshot["combatants"] if entry["species"] == "Porygon2")
    sawk = next(entry for entry in snapshot["combatants"] if entry["species"] == "Sawk")

    assert [move["name"] for move in porygon2["moves"]][:6] == [
        "Conversion",
        "Conversion2",
        "Tackle",
        "Sharpen",
        "Psybeam",
        "Agility",
    ]
    assert [move["name"] for move in sawk["moves"]][:5] == [
        "Bind",
        "Leer",
        "Bide",
        "Focus Energy",
        "Seismic Toss",
    ]


def test_csv_repository_resolves_species_move_and_ability_typos_and_forms():
    repo = PTUCsvRepository()

    assert repo.resolve_species_name("Galarian Slowbro") == "Slowbro Galarian"
    assert repo.resolve_move_name("Quick Atack") == "Quick Attack"
    assert repo.resolve_move_name("Water Pusle") == "Water Pulse"
    assert repo.resolve_ability_name("Pikachu", "Staticc", 30) == "Static"
    assert repo.resolve_ability_name("Pikachu", "Lightning Rodd", 30) == "Lightning Rod"
    assert repo.resolve_item_name("Ligth Ball") == "Light Ball"
    assert repo.resolve_item_name("Oran Bery") == "Oran Berry"
    assert repo.resolve_item_name("Mystic Watre") == "Mystic Water"
    assert repo.resolve_item_name("Dragon Fang") == "Dragon Fang"
    assert repo.resolve_item_name("Never Melt Ice") == "Never-Melt Ice"


def test_roster_csv_canonicalizes_species_move_ability_and_item_names():
    csv_text = """side,species,level,ability1,item1,move1,move2
player,Galarian Slowbro,30,Quick Draww,Ligth Ball,Water Pusle,Quick Atack
foe,Pikachu,30,Staticc,Oran Bery,Thundershok,Quick Atack
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    slowbro = spec.players[0]
    pikachu = spec.foes[0]

    assert slowbro.species == "Slowbro Galarian"
    assert [entry["name"] for entry in slowbro.abilities] == ["Quick Draw"]
    assert [entry["name"] for entry in slowbro.items] == ["Light Ball"]
    assert [move.name for move in slowbro.moves][:2] == ["Water Pulse", "Quick Attack"]
    assert pikachu.species == "Pikachu"
    assert [entry["name"] for entry in pikachu.abilities] == ["Static"]
    assert [entry["name"] for entry in pikachu.items] == ["Oran Berry"]
    assert [move.name for move in pikachu.moves][:2] == ["Thunder Shock", "Quick Attack"]


def test_roster_csv_canonicalizes_items_missing_from_primary_catalogs():
    csv_text = """side,species,level,item1,item2
player,Pikachu,30,Mystic Watre,Never Melt Ice
foe,Charmander,30,Dragon Fang,Black Glassses
"""
    spec = campaign_from_roster_csv(csv_text=csv_text, default_level=30)

    pikachu = spec.players[0]
    charmander = spec.foes[0]

    assert [entry["name"] for entry in pikachu.items] == ["Mystic Water", "Never-Melt Ice"]
    assert [entry["name"] for entry in charmander.items] == ["Dragon Fang", "Black Glasses"]


def test_match_plan_from_roster_csv_supports_three_sides():
    csv_text = """side,species,level
alpha,Pikachu,30
beta,Squirtle,30
gamma,Bulbasaur,30
"""
    plan = match_plan_from_roster_csv(csv_text=csv_text, active_slots=1)
    matchup = plan.matchups[0]
    sides = matchup.sides_or_default()
    assert len(sides) == 3
    teams = {side.team for side in sides}
    assert {"alpha", "beta", "gamma"} == teams


def test_engine_facade_start_encounter_supports_three_sides_roster_csv():
    csv_text = """side,species,level
alpha,Pikachu,30
beta,Squirtle,30
gamma,Bulbasaur,30
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv=csv_text, active_slots=1, seed=101)
    assert snapshot["status"] == "ok"
    teams = {str(entry["team"]) for entry in snapshot["combatants"]}
    assert {"alpha", "beta", "gamma"} <= teams


def test_engine_facade_side_names_override_winner_label_and_trainers():
    csv_text = """side,species,level
player,Pikachu,30
foe,Magikarp,1
"""
    facade = EngineFacade()
    snapshot = facade.start_encounter(
        roster_csv=csv_text,
        active_slots=1,
        seed=102,
        side_names={"player": "Ash", "foe": "Gary"},
    )
    trainer_names = {str(entry["team"]): str(entry["name"]) for entry in snapshot["trainers"]}
    assert trainer_names["player"] == "Ash"
    assert trainer_names["foe"] == "Gary"


def test_engine_facade_clear_battle_resets_snapshot_state():
    facade = EngineFacade()
    snapshot = facade.start_encounter(roster_csv="side,species,level\nplayer,Pikachu,30\nfoe,Eevee,30\n", active_slots=1, seed=103)
    assert snapshot["status"] == "ok"
    cleared = facade.clear_battle()
    assert cleared["status"] == "no_battle"
