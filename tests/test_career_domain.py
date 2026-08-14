from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from auto_ptu.career.catalogs import FRANCHISE_TRAINERS, REGIONS, RARITY_ORDER, compiled_decision_count
from auto_ptu.career.class_adapters import compile_class_adapters
from auto_ptu.career.content_compiler import validate_compiled_content
from auto_ptu.career.decisions import apply_option, build_season_decision
from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript, CareerRun
from auto_ptu.career.evolutions import evolve_species_for_level, next_evolution
from auto_ptu.career.roster import capture_species, grant_partner_levels
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def fake_battle(spec: BattleSpec) -> BattleTranscript:
    winner = "career-home" if spec.seed % 3 else "career-away"
    return BattleTranscript(
        battle_id=spec.id,
        spec=spec,
        winner_team=winner,
        winner_label=spec.home_club if winner == "career-home" else spec.away_club,
        rounds=3,
        events=[{"type": "test", "seed": spec.seed}],
        initial_state={},
        final_state={"winner_team": winner},
        sha256=f"test-{spec.seed}",
    )


def test_catalog_covers_nine_regions_and_more_than_ten_thousand_decisions() -> None:
    assert len(REGIONS) == 9
    assert compiled_decision_count() >= 10_000
    assert all(region.underdogs for region in REGIONS.values())
    assert all(region.starters for region in REGIONS.values())
    assert len(REGIONS["kanto"].underdogs) >= 50
    assert {"Bulbasaur", "Charmander", "Squirtle"}.issubset(REGIONS["kanto"].starters)


def test_compiled_decisions_are_authored_and_mechanically_distinct() -> None:
    report = validate_compiled_content()
    assert report["family_count"] >= 200
    assert report["node_count"] >= 10_000
    assert report["mechanically_distinct"] == report["node_count"]


def test_every_ptu_class_and_feature_gets_a_career_adapter() -> None:
    payload = compile_class_adapters()
    assert payload["class_count"] == 69
    assert payload["feature_count"] == 709
    assert payload["unmapped"] == []
    assert all(entry["battle"] or entry["season"] for entry in payload["classes"])


def test_official_regional_starter_and_seeded_identity_are_supported() -> None:
    engine = CareerEngine(fake_battle)
    first = engine.new_run(player_id="first", name="Ari", region="kanto", starter="Bulbasaur", classes=["Commander"], seed=921)
    second = engine.new_run(player_id="second", name="Rei", region="kanto", starter="Bulbasaur", classes=["Commander"], seed=921)
    assert first.pokemon[0].nature == second.pokemon[0].nature
    assert first.pokemon[0].abilities == second.pokemon[0].abilities
    assert first.class_effects["battle"] == {"home_level_bonus": 1}
    assert engine._schedule(first)[0].home_level_bonus == 1
    assert "Commander" in first.season.decision.body


def test_every_regional_decision_uses_a_canonical_franchise_trainer() -> None:
    engine = CareerEngine(fake_battle)
    for index, region in enumerate(REGIONS):
        run = engine.new_run(
            player_id=f"canon-{region}", name="Ari", region=region,
            starter=REGIONS[region].starters[0], classes=["Ace Trainer"], seed=1200 + index,
        )
        decision = run.season.decision
        name, kind, _ = decision.npc_name.split(" · ")
        assert name in FRANCHISE_TRAINERS[region][kind]


def test_positive_career_milestones_unlock_as_achievements() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="milestones", name="Ari", region="kanto", starter="Bulbasaur",
        classes=["Ace Trainer"], seed=1210,
    )
    for species in ("Rattata", "Pidgey", "Zubat", "Oddish", "Psyduck"):
        capture_species(run, species, source="test")
    run.totals["wins"] = 6
    run.season.wins = 6
    run.season.losses = 0
    run.pokemon[0].evolution_history = [{}, {}, {}]
    engine._unlock_achievements(run, run.season, {"promoted": True})
    assert {"First victory", "Full squad", "Perfect season", "Evolution specialist", "Rising star"}.issubset(run.achievements)


def test_mentor_class_directly_advances_partner_after_a_season() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(player_id="mentor", name="Ari", region="kanto", starter="Bulbasaur", classes=["Mentor"], seed=922)
    before = run.pokemon[0].level
    option = run.season.decision.options[0]
    run, _ = engine.advance_season(run, option_id=option.id)
    # Eight normal calendar levels plus Mentor's explicit extra level.
    assert run.pokemon[0].level == before + 9
    event = next(entry for entry in run.timeline if entry["type"] == "class.effect_applied")
    assert event["season_effects"]["partner_levels"] == 1


def test_career_starts_at_twelve_with_one_partner_and_ten_pokeballs() -> None:
    run = CareerEngine(fake_battle).new_run(
        player_id="trainer-1",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=42,
    )
    assert run.age == 12
    assert run.league == "junior"
    assert run.build.pokeballs == 10
    assert len(run.pokemon) == 1
    assert len(run.active_roster) == 1
    assert len([entry for entry in run.pokemon if entry.status == "pc"]) == 0
    assert run.roster[0] == "Rattata"
    assert len(set(entry.id for entry in run.pokemon)) == 1
    assert not any(entry["type"] == "pokemon.captured" for entry in run.timeline)
    assert any(reward["type"] == "pokemon" for option in run.season.decision.options for reward in option.rewards)
    assert len(run.season.decision.options) == 3


def test_first_calendar_uses_the_complete_owned_team_in_every_fixture() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-team",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=43,
    )
    schedule = engine._schedule(run)
    assert len(schedule) == 6
    assert all(entry.home_pokemon_ids == run.active_roster for entry in schedule)
    assert all(entry.home_team_species == ["Rattata"] for entry in schedule)
    assert all(entry.home_ai_level == entry.away_ai_level == "tactical" for entry in schedule)


def test_lineup_can_move_pokemon_between_active_team_and_pc() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-lineup",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=44,
    )
    for species in (entry for entry in REGIONS["kanto"].underdogs if entry != run.build.starter):
        capture_species(run, species, source="test")
        if len(run.pokemon) >= 8:
            break
    selected = [entry.id for entry in run.pokemon[2:8]]
    engine.update_lineup(run, selected)
    assert run.active_roster == selected
    assert [entry.id for entry in run.pokemon if entry.status == "active"] == selected
    assert engine._schedule(run)[0].home_pokemon_ids == selected
    with pytest.raises(ValueError, match="exactly 6"):
        engine.update_lineup(run, selected[:5])


def test_legacy_single_partner_run_is_not_filled_with_unchosen_pokemon() -> None:
    engine = CareerEngine(fake_battle)
    current = engine.new_run(
        player_id="trainer-legacy",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=46,
    )
    payload = current.to_dict()
    payload.pop("pokemon")
    payload.pop("active_roster")
    payload["roster"] = ["Rattata"]
    payload["build"]["pokeballs"] = 10
    restored = CareerRun.from_dict(payload)
    assert engine.ensure_roster(restored) is True
    assert restored.pokemon[0].nature
    assert restored.pokemon[0].abilities
    assert len(restored.pokemon) == 1
    assert len(restored.active_roster) == 1
    assert len([entry for entry in restored.pokemon if entry.status == "pc"]) == 0


def test_loading_a_legacy_ready_partner_applies_missing_evolutions() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="legacy-evolution", name="Ari", region="kanto", starter="Bulbasaur",
        classes=["Ace Trainer"], seed=47,
    )
    run.pokemon[0].level = 20
    assert engine.ensure_roster(run) is True
    assert run.pokemon[0].species == "Ivysaur"
    assert run.build.starter == "Ivysaur"
    assert any(entry["type"] == "pokemon.evolved" for entry in run.timeline)


def test_partner_evolves_and_roster_keeps_growing_across_seasons() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-growth",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=45,
    )
    for _ in range(2):
        run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    partner = next(entry for entry in run.pokemon if entry.is_partner)
    assert partner.species == "Raticate"
    assert partner.level >= 20
    assert partner.matches == 12
    assert run.build.starter == "Raticate"
    assert len(run.pokemon) == 2
    assert sum(len(entry.evolution_history) for entry in run.pokemon) >= 1


@pytest.mark.parametrize(
    ("region", "starter"),
    [
        ("kanto", "Bulbasaur"), ("johto", "Chikorita"), ("hoenn", "Treecko"),
        ("sinnoh", "Turtwig"), ("unova", "Snivy"), ("kalos", "Chespin"),
        ("alola", "Rowlet"), ("galar", "Grookey"), ("paldea", "Sprigatito"),
    ],
)
def test_regional_starters_use_compiled_ptu_evolution_chains(region: str, starter: str) -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id=f"evolution-{region}", name="Ari", region=region, starter=starter,
        classes=["Ace Trainer"], seed=808,
    )
    partner = run.pokemon[0]
    target = next_evolution(starter, seed=run.seed, region=region)
    assert target is not None
    evolved, threshold = target
    grant_partner_levels(run, threshold - partner.level, source="test")
    assert partner.species == evolved
    assert partner.evolution_history[-1]["threshold"] == threshold


def test_evolution_is_automatic_and_never_occupies_an_advanced_decision() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="evolution-decision", name="Ari", region="kanto", starter="Bulbasaur",
        classes=["Ace Trainer"], seed=810,
    )
    assert run.pokemon[0].level == 5
    first = build_season_decision(run, 0)
    second = build_season_decision(run, 1)
    assert first.family != "evolution"
    assert second.family != "evolution"
    grant_partner_levels(run, 11, source="test")
    assert run.pokemon[0].species == "Ivysaur"


def test_high_level_rivals_evolve_and_featured_clubs_rotate() -> None:
    assert evolve_species_for_level("Poochyena", 63, seed=1, region="hoenn") == "Mightyena"
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="rival-rotation", name="Ari", region="kanto", starter="Bulbasaur",
        classes=["Ace Trainer"], seed=809,
    )
    featured = []
    for _ in range(4):
        featured.append(engine._schedule(run)[-1].away_club)
        run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    assert len(set(featured)) == len(featured)


def test_junior_is_age_gated_then_promotes_to_rookie() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-1",
        name="Ari",
        region="johto",
        starter="Sentret",
        classes=["Mentor"],
        seed=9,
    )
    for _ in range(4):
        run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    assert run.age == 16
    assert run.league == "rookie"


def test_legacy_runaway_levels_are_clamped_to_the_current_league() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-level-cap",
        name="Ari",
        region="hoenn",
        starter="Poochyena",
        classes=["Ace Trainer"],
        seed=63,
    )
    run.pokemon[0].level = 63
    assert engine.ensure_roster(run) is True
    assert run.pokemon[0].level == 20
    assert all(level <= 20 for spec in engine._schedule(run) for level in spec.away_team_levels)

    for _ in range(4):
        run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    assert run.league == "rookie"
    run.pokemon[0].level = 63
    engine.ensure_roster(run)
    schedule = engine._schedule(run)
    assert run.pokemon[0].level == 35
    assert all(level <= 35 for spec in schedule for level in spec.home_team_levels)
    assert all(level <= 35 for spec in schedule for level in spec.away_team_levels)


def test_advanced_mode_requires_three_season_decisions() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-advanced",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        mode="advanced",
        seed=77,
    )
    for expected in (1, 2):
        run, transcripts = engine.advance_season(run, option_id=run.season.decision.options[0].id)
        assert transcripts == []
        assert run.season.decisions_completed == expected
        assert run.season_number == 1
    run, transcripts = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    assert len(transcripts) == 6
    assert run.season_number == 2
    completed = next(entry for entry in run.timeline if entry["type"] == "season.completed")
    assert len(completed["decisions"]) == 3
    assert len(completed["battle_hashes"]) == 6
    assert "battle_ids" not in completed


def test_decisions_grant_pokemon_items_moves_and_relationships() -> None:
    engine = CareerEngine(fake_battle)

    capture_run = engine.new_run(
        player_id="rewards-capture", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], mode="advanced", seed=1,
    )
    capture_option = next(option for option in capture_run.season.decision.options if any(reward["type"] == "pokemon" for reward in option.rewards))
    capture_run, _ = engine.advance_season(capture_run, option_id=capture_option.id)
    assert len(capture_run.pokemon) == 2
    assert capture_run.build.pokeballs == 9

    breeding_decision = capture_run.season.decision
    relationship_option = next(option for option in breeding_decision.options if any(reward["type"] == "relationship" for reward in option.rewards))
    capture_run, _ = engine.advance_season(capture_run, option_id=relationship_option.id)
    assert capture_run.relationships
    assert capture_run.relationship_effects["home_level_bonus"] >= 1

    contest_decision = capture_run.season.decision
    move_option = next(option for option in contest_decision.options if any(reward["type"] == "move" for reward in option.rewards))
    capture_run, _ = engine.advance_season(capture_run, option_id=move_option.id)
    assert next(entry for entry in capture_run.pokemon if entry.is_partner).taught_moves
    completed = next(entry for entry in capture_run.timeline if entry["type"] == "season.completed")
    assert completed["relationship_effects"]["recovery_applied"] >= 1

    item_run = engine.new_run(
        player_id="rewards-item", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=1,
    )
    item_option = next(
        option for option in item_run.season.decision.options
        if any(reward["type"] == "item" for reward in option.gamble.get("success_rewards", []))
    )
    item_run, _ = engine.advance_season(item_run, option_id=item_option.id)
    assert item_run.build.pokeballs > 10 or item_run.inventory


def test_capture_choices_never_train_an_unrelated_pokemon_stat() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="stat-training", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=1,
    )
    decision = run.season.decision
    assert decision.family == "capture"
    for option in decision.options:
        rewards = option.gamble.get("success_rewards", []) if option.risk == "gamble" else option.rewards
        assert not any(reward["type"] == "stat" for reward in rewards)
        pokemon_rewards = [reward for reward in rewards if reward["type"] == "pokemon"]
        assert pokemon_rewards
        assert pokemon_rewards[0]["rarity"] in {"common", "rare", "very_rare"}


def test_rival_species_and_rarities_change_with_league_progression() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="rarity-calendar", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=929,
    )
    junior = engine._schedule(run)
    assert all(rarity in {"common", "rare", "very_rare"} for spec in junior for rarity in spec.away_team_rarities)
    run.league = "elite"
    run.pokedex_level = 4
    elite = engine._schedule(run)
    assert all(rarity in RARITY_ORDER for spec in elite for rarity in spec.away_team_rarities)
    assert len({species for spec in elite for species in spec.away_team_species}) > 4
    assert any(rarity in {"epic", "legendary", "mythical"} for spec in elite for rarity in spec.away_team_rarities)


def test_inventory_items_and_training_have_direct_pokemon_effects(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    created = service.create_run(
        "trainer-items",
        {"name": "Ari", "region": "kanto", "starter": "Rattata", "classes": ["Ace Trainer"], "seed": 303},
    )
    run = CareerRun.from_dict(created)
    run.inventory["Training Kit"] = 1
    run.inventory["Pokédex Upgrade"] = 1
    service.store.save_run(run)
    trained = service.use_item(
        "trainer-items", run.id,
        {"expected_revision": run.revision, "item": "Training Kit", "pokemon_id": run.pokemon[0].id, "stat": "atk"},
    )
    assert trained["pokemon"][0]["stat_training"]["atk"] == 2
    upgraded = service.use_item(
        "trainer-items", run.id,
        {"expected_revision": trained["revision"], "item": "Pokédex Upgrade"},
    )
    assert upgraded["pokedex_level"] == 1
    session = service.train(
        "trainer-items", run.id,
        {"expected_revision": upgraded["revision"], "method": "agility", "pokemon_id": run.pokemon[0].id},
    )
    assert session["pokemon"][0]["stat_training"]["spd"] == 2
    assert session["season"]["training_completed"] is True
    with pytest.raises(ValueError, match="already complete"):
        service.train(
            "trainer-items", run.id,
            {"expected_revision": session["revision"], "method": "guard", "pokemon_id": run.pokemon[0].id},
        )


def test_salary_is_paid_and_retirement_risk_is_explicit() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="salary", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=712,
    )
    salary = run.contract.salary
    run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    assert run.career_earnings == salary
    paid = next(entry for entry in run.timeline if entry["type"] == "contract.salary_paid")
    assert paid["salary"] == salary
    assert engine._forced_retirement_reason(run) in {"", "no_contract"}


def test_season_incidents_are_deterministic_and_visible_in_the_summary() -> None:
    engine = CareerEngine(fake_battle)
    first = engine.new_run(player_id="incident-a", name="Ari", region="kanto", starter="Rattata", classes=["Ace Trainer"], seed=313)
    second = engine.new_run(player_id="incident-b", name="Ari", region="kanto", starter="Rattata", classes=["Ace Trainer"], seed=313)
    first, _ = engine.advance_season(first, option_id=first.season.decision.options[0].id)
    second, _ = engine.advance_season(second, option_id=second.season.decision.options[0].id)
    first_incident = next(entry for entry in first.timeline if entry["type"] == "season.incident")
    second_incident = next(entry for entry in second.timeline if entry["type"] == "season.incident")
    assert first_incident["kind"] == second_incident["kind"]
    assert first_incident["title_es"] == second_incident["title_es"]
    completed = next(entry for entry in first.timeline if entry["type"] == "season.completed")
    assert completed["incident"] == first_incident


def test_decision_copy_never_exposes_internal_ruleset_language() -> None:
    run = CareerEngine(fake_battle).new_run(
        player_id="clean-copy", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=2,
    )
    decision = run.season.decision
    visible_copy = " ".join([decision.title, decision.body, *(value for option in decision.options for value in (option.label, option.description))])
    assert "PTU" not in visible_copy.upper()


def test_gamble_rewards_are_exclusive_and_only_granted_on_success() -> None:
    engine = CareerEngine(fake_battle)
    failed = engine.new_run(
        player_id="roulette-fail", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=4,
    )
    gamble = failed.season.decision.options[2]
    safe_species = failed.season.decision.options[0].rewards[0]["species"]
    calculated_species = failed.season.decision.options[1].rewards[0]["species"]
    gamble_species = gamble.gamble["success_rewards"][0]["species"]
    assert len({safe_species, calculated_species, gamble_species}) == 3
    assert gamble.rewards == []
    failed, _ = engine.advance_season(failed, option_id=gamble.id)
    completed = next(entry for entry in failed.timeline if entry["type"] == "season.completed")
    assert completed["decision_effects"]["gamble_success"] is False
    assert len(failed.pokemon) == 1
    assert "Premier Ball" not in failed.inventory


def test_career_attributes_change_schedule_preparation_transparently() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-prepared",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=91,
    )
    run.development = 6
    run.scouting = 3
    run.finances = 4
    schedule = engine._schedule(run)
    assert all(spec.home_level_bonus == 3 for spec in schedule)
    assert all(spec.away_level_bonus == -1 for spec in schedule)


def test_active_legacy_run_records_version_migration_before_new_mechanics() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-migration",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=102,
    )
    run.versions.career = "career-0.1.0"
    run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    migration = next(entry for entry in run.timeline if entry["type"] == "career.version_migrated")
    assert migration == {
        "type": "career.version_migrated",
        "season": 1,
        "age": 12,
        "from": "career-0.1.0",
        "to": "career-0.8.0",
    }


def test_invalid_underdog_or_class_is_rejected() -> None:
    engine = CareerEngine(fake_battle)
    with pytest.raises(ValueError, match="eligible"):
        engine.new_run(player_id="x", name="X", region="kanto", starter="Mewtwo", classes=["Ace Trainer"])
    with pytest.raises(ValueError, match="Unknown trainer class"):
        engine.new_run(player_id="x", name="X", region="kanto", starter="Rattata", classes=["Influencer"])


def test_decision_endpoint_is_revisioned_and_idempotent(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    created = service.create_run(
        "trainer-1",
        {"name": "Ari", "region": "kanto", "starter": "Rattata", "classes": ["Ace Trainer"], "seed": 5},
    )
    run_id = created["id"]
    option_id = created["season"]["decision"]["options"][0]["id"]
    first = service.decide("trainer-1", run_id, {"expected_revision": 0, "option_id": option_id}, "season-1")
    second = service.decide("trainer-1", run_id, {"expected_revision": 0, "option_id": option_id}, "season-1")
    assert first == second
    assert first["run"]["revision"] == 2
    assert first["run"]["season_number"] == 2
    assert first["season_resolved"] is True
    assert len(first["battle_ids"]) == 6
    assert first["featured_battle"]["battle_id"] == first["battle_ids"][-1]
    with pytest.raises(RuntimeError, match="Revision conflict"):
        service.decide("trainer-1", run_id, {"expected_revision": 0, "option_id": option_id}, "season-2")


def test_decision_precomputes_featured_battle_before_opening_the_arena(tmp_path: Path) -> None:
    calls: list[str] = []

    def counted_battle(spec: BattleSpec) -> BattleTranscript:
        calls.append(spec.id)
        return fake_battle(spec)

    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(counted_battle))
    created = service.create_run(
        "trainer-fast",
        {"name": "Ari", "region": "kanto", "starter": "Rattata", "classes": ["Ace Trainer"], "seed": 55},
    )
    option_id = created["season"]["decision"]["options"][0]["id"]
    prepared = service.decide(
        "trainer-fast",
        created["id"],
        {"expected_revision": created["revision"], "option_id": option_id},
        "fast-season-1",
    )
    assert len(calls) == 1
    assert prepared["run"]["season_number"] == 2
    assert prepared["season_resolved"] is True
    featured = prepared["battle_ids"][-1]
    assert prepared["featured_battle"]["battle_id"] == featured
    transcript = service.battle("trainer-fast", created["id"], featured)
    assert transcript["battle_id"] == featured
    assert calls == [featured]
    finished = service.get_run("trainer-fast", created["id"])
    assert finished["season_number"] == 2
    completed = next(entry for entry in finished["timeline"] if entry["type"] == "season.completed")
    assert len(completed["battle_hashes"]) == 6
    assert sum(1 for entry in completed["battle_hashes"] if entry["id"] == featured) == 1


def test_relationships_change_battle_recovery_and_contract_security() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-network", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=88,
    )
    contact = "Mara Vale · owner · Kanto"
    run.relationships[contact] = 6
    run.health = 50
    run.league = "regular"
    run.contract.seasons_remaining = 0
    engine.ensure_roster(run)
    assert run.relationship_effects["home_level_bonus"] == 2
    assert all(spec.home_level_bonus >= 2 for spec in engine._schedule(run))
    outcome = engine._apply_health_and_contract(run, wins=0, losses=10)
    assert run.contract is not None
    assert outcome["contract_guard_used"] is True
    assert run.relationships[contact] == 4
    assert run.health > 45


def test_relationship_roles_have_distinct_mechanical_effects() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-roles", name="Ari", region="kanto", starter="Rattata",
        classes=["Ace Trainer"], seed=89,
    )
    run.relationships["Brock · mentor · Kanto"] = 6
    run.relationships["Blue · rival · Kanto"] = 6
    partner = run.pokemon[0]
    before = sum(partner.stat_training.values())
    schedule = engine._schedule(run)
    assert all(spec.away_level_bonus <= -2 for spec in schedule)
    outcome = engine._apply_health_and_contract(run, wins=3, losses=3)
    assert outcome["mentor_training_bonus"] == 2
    assert sum(partner.stat_training.values()) == before + 2
    assert any(entry["type"] == "relationship.mentor_training" for entry in run.timeline)


def test_lineup_endpoint_is_revisioned_and_persisted(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    run = service.create_run(
        "trainer-1",
        {"name": "Ari", "region": "kanto", "starter": "Rattata", "classes": ["Ace Trainer"], "seed": 6},
    )
    stored = CareerRun.from_dict(run)
    for species in (entry for entry in REGIONS["kanto"].underdogs if entry != stored.build.starter):
        capture_species(stored, species, source="test")
        if len(stored.pokemon) >= 8:
            break
    service.store.save_run(stored)
    run = stored.to_dict()
    selected = [entry["id"] for entry in run["pokemon"][2:8]]
    updated = service.lineup(
        "trainer-1",
        run["id"],
        {"expected_revision": run["revision"], "pokemon_ids": selected},
    )
    assert updated["active_roster"] == selected
    assert service.get_run("trainer-1", run["id"])["active_roster"] == selected


def test_ranked_daily_attempts_are_limited_to_three(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    from datetime import date

    day = date(2026, 8, 10)
    challenge = service.daily(day)
    starter = REGIONS[challenge["region"]].underdogs[0]
    payload = {"name": "Ari", "mode": "simple", "starter": starter, "classes": ["Ace Trainer"]}
    results = []
    for expected in range(1, 4):
        varied = {**payload, "starter": REGIONS[challenge["region"]].underdogs[expected - 1], "classes": ["Mentor" if expected == 2 else "Ace Trainer"]}
        result = service.create_daily_attempt("trainer-1", varied, day)
        assert result["attempt_no"] == expected
        results.append(result)
    assert {entry["run"]["seed"] for entry in results} == {challenge["seed"]}
    assert len({entry["run"]["build"]["starter"] for entry in results}) == 3
    skeletons = [
        [(option["risk"], option["transparency"], option["guaranteed"]) for option in entry["run"]["season"]["decision"]["options"]]
        for entry in results
    ]
    assert skeletons[0] == skeletons[1] == skeletons[2]
    with pytest.raises(PermissionError, match="three"):
        service.create_daily_attempt("trainer-1", payload, day)


def test_sharing_requires_retirement_and_is_explicit(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    run = service.create_run(
        "trainer-1",
        {"name": "Ari", "region": "kanto", "starter": "Rattata", "classes": ["Ace Trainer"], "seed": 5},
    )
    with pytest.raises(ValueError, match="retired"):
        service.share("trainer-1", run["id"], {"include_replay": False})
    service.retire("trainer-1", run["id"], {"reason": "voluntary"})
    card_only = service.share("trainer-1", run["id"], {"include_replay": False})
    shared = service.share("trainer-1", run["id"], {"include_replay": True})
    assert shared["published"] is True
    assert shared["include_replay"] is False
    assert card_only["share_id"] != shared["share_id"]
    assert service.public_share(card_only["share_id"])["has_replay"] is False
    assert (tmp_path / "meta" / f"{shared['share_id']}.json").exists()
    public = service.public_share(shared["share_id"])
    assert public["has_replay"] is False
    assert public["summary"]["trainer"] == "Ari"
    assert "timeline" not in public
