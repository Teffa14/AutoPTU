import random
import json
from pathlib import Path

from auto_ptu.api.engine_facade import EngineFacade
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, DirtyFightingFollowUpAction, FlightAction, PokemonState, PsychicResonanceFollowUpAction, QuickWitMoveAction, TrainerState, GridState, TurnPhase, UseMoveAction, WeaponFinesseFollowUpAction, create_trainer_feature_action
from auto_ptu.rules.calculations import resolve_move_action


def _move(
    name: str,
    *,
    type_name: str = "Normal",
    category: str = "Physical",
    db: int = 8,
    range_kind: str = "Melee",
    target_kind: str = "Melee",
    **aliases,
) -> MoveSpec:
    if "type" in aliases and aliases["type"] not in (None, ""):
        type_name = str(aliases.pop("type"))
    return MoveSpec(
        name=name,
        type=type_name,
        category=category,
        db=db,
        ac=aliases.pop("ac", None),
        range_kind=range_kind,
        range_value=1 if range_kind == "Melee" else 6,
        target_kind=target_kind,
        target_range=1 if target_kind == "Melee" else 6,
        freq=str(aliases.pop("freq", "At-Will")),
        range_text="Melee, 1 Target" if target_kind == "Melee" else "Ranged, 1 Target",
    )


def _spec(name: str, moves: list[MoveSpec], *, atk: int = 12, defense: int = 12, size: str = "Medium") -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=50,
        types=["Normal"],
        size=size,
        hp_stat=8,
        atk=atk,
        defense=defense,
        spatk=10,
        spdef=10,
        spd=10,
        moves=moves,
    )


def test_engine_facade_random_6v6_has_unique_active_positions_per_team():
    facade = EngineFacade()
    state = facade.start_encounter(
        random_battle=True,
        team_size=6,
        active_slots=6,
        min_level=20,
        max_level=60,
        seed=91,
        ai_mode="ai",
        step_ai=True,
    )
    by_team: dict[str, list[dict]] = {}
    for combatant in state["combatants"]:
        if not combatant["active"]:
            continue
        by_team.setdefault(str(combatant["team"]), []).append(combatant)
    assert len(by_team) == 2
    for members in by_team.values():
        assert len(members) == 6
        positions = [tuple(member["position"]) for member in members if member["position"] is not None]
        assert len(positions) == 6
        assert len(set(positions)) == 6


def test_engine_facade_snapshot_serializes_large_footprint_tiles():
    facade = EngineFacade()
    facade.battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player"),
            "foe": TrainerState(identifier="foe", name="Foe"),
        },
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Steelix", [_move("Tackle")], size="Large"),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "foe-1": PokemonState(
                spec=_spec("Target", [_move("Tackle")]),
                controller_id="foe",
                position=(5, 5),
                active=True,
            ),
        },
        grid=GridState(width=8, height=8),
    )
    payload = facade.snapshot()
    steelix = next(entry for entry in payload["combatants"] if entry["id"] == "player-1")
    assert steelix["footprint_side"] == 2
    assert sorted(tuple(tile) for tile in steelix["footprint_tiles"]) == [(1, 1), (1, 2), (2, 1), (2, 2)]
    for key in ("1,1", "1,2", "2,1", "2,2"):
        assert payload["occupants"][key] == "player-1"


def test_terrain_mapper_starter_records_exist():
    starter_root = Path("auto_ptu/data/terrain_maps/starter")
    manifest_path = starter_root / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    assert isinstance(manifest, list)
    assert len(manifest) >= 5
    first = manifest[0]
    record_path = starter_root / "records" / str(first["record"])
    assert record_path.exists()
    payload = json.loads(record_path.read_text(encoding="utf-8-sig"))
    assert payload["grid"]["width"] >= 15
    assert isinstance(payload["grid"]["tiles"], list)


def test_engine_facade_random_ai_battle_supports_configurable_side_count():
    facade = EngineFacade()
    state = facade.start_encounter(
        random_battle=True,
        ai_mode="ai",
        step_ai=True,
        side_count=4,
        team_size=1,
        active_slots=1,
        min_level=20,
        max_level=30,
        seed=123,
    )
    teams = {str(combatant["team"]) for combatant in state["combatants"]}
    assert len(teams) >= 4


def test_engine_facade_merges_hobbyist_granted_features_into_trainer_profile():
    facade = EngineFacade()
    facade.start_encounter(
        random_battle=True,
        team_size=1,
        active_slots=1,
        min_level=20,
        max_level=20,
        seed=812,
        trainer_profile={
            "profile": {"name": "Hobbyist"},
            "features": ["Hobbyist", "Look and Learn"],
            "hobbyist_granted_features": ["Focused Command", "Strike Again!"],
        },
    )

    trainer = next(iter(facade.battle.trainers.values()))
    assert [feature["name"] for feature in trainer.features] == [
        "Hobbyist",
        "Look and Learn",
        "Focused Command",
        "Strike Again!",
    ]


def test_engine_facade_merges_hobbyist_edges_into_trainer_profile():
    facade = EngineFacade()
    facade.start_encounter(
        random_battle=True,
        team_size=1,
        active_slots=1,
        min_level=20,
        max_level=20,
        seed=813,
        trainer_profile={
            "profile": {"name": "Hobbyist"},
            "edges": ["Basic Skills"],
            "hobbyist_skill_edges": ["Hobbyist Skill Edge: Perception -> Adept"],
            "hobbyist_granted_edges": ["Skill Stunt"],
        },
    )

    trainer = next(iter(facade.battle.trainers.values()))
    assert [edge["name"] for edge in trainer.edges] == [
        "Basic Skills",
        "Hobbyist Skill Edge: Perception -> Adept",
        "Skill Stunt",
    ]


def test_engine_facade_derives_hobbyist_granted_features_from_raw_payload():
    facade = EngineFacade()
    facade.start_encounter(
        random_battle=True,
        team_size=1,
        active_slots=1,
        min_level=20,
        max_level=20,
        seed=814,
        trainer_profile={
            "profile": {"name": "Hobbyist"},
            "features": ["Hobbyist", "Look and Learn", "Dilettante Rank 1"],
            "look_and_learn_features": {"scene": "Focused Command", "ap": "Type Sync"},
            "dilettante_picks": [{"rank": 1, "feature": "Quick Switch", "edge": "Skill Stunt"}],
        },
    )

    trainer = next(iter(facade.battle.trainers.values()))
    assert [feature["name"] for feature in trainer.features] == [
        "Hobbyist",
        "Look and Learn",
        "Dilettante Rank 1",
        "Focused Command",
        "Type Sync",
        "Quick Switch",
    ]


def test_engine_facade_derives_hobbyist_granted_edges_from_raw_payload():
    facade = EngineFacade()
    facade.start_encounter(
        random_battle=True,
        team_size=1,
        active_slots=1,
        min_level=20,
        max_level=20,
        seed=815,
        trainer_profile={
            "profile": {"name": "Hobbyist"},
            "edges": ["Basic Skills"],
            "hobbyist_skill_edges": ["Hobbyist Skill Edge: Perception -> Adept"],
            "dilettante_picks": [{"rank": 1, "feature": "Quick Switch", "edge": "Skill Stunt"}],
        },
    )

    trainer = next(iter(facade.battle.trainers.values()))
    assert [edge["name"] for edge in trainer.edges] == [
        "Basic Skills",
        "Hobbyist Skill Edge: Perception -> Adept",
        "Skill Stunt",
    ]


def test_engine_facade_preserves_mentor_skills_on_trainer_class_metadata():
    facade = EngineFacade()
    facade.start_encounter(
        random_battle=True,
        team_size=1,
        active_slots=1,
        min_level=20,
        max_level=20,
        seed=816,
        trainer_profile={
            "profile": {"name": "Mentor"},
            "class_id": "class:Mentor",
            "class_name": "Mentor",
            "features": ["Mentor", "Inspirational Support"],
            "mentor_skills": ["Charm", "Intuition"],
        },
    )

    trainer = next(iter(facade.battle.trainers.values()))
    assert trainer.trainer_class["id"] == "class:Mentor"
    assert trainer.trainer_class["name"] == "Mentor"
    assert trainer.trainer_class["mentor_skills"] == ["Charm", "Intuition"]


def test_engine_facade_preserves_feature_object_payloads_for_stat_ace():
    facade = EngineFacade()
    facade.start_encounter(
        random_battle=True,
        team_size=1,
        active_slots=1,
        min_level=20,
        max_level=20,
        seed=817,
        trainer_profile={
            "profile": {"name": "Stat Ace"},
            "features": [
                {"name": "Stat Ace", "chosen_stat": "spdef"},
                {"name": "Stat Link", "chosen_stat": "spdef"},
            ],
        },
    )

    trainer = next(iter(facade.battle.trainers.values()))
    assert trainer.features[0]["name"] == "Stat Ace"
    assert trainer.features[0]["chosen_stat"] == "spdef"
    assert trainer.features[1]["name"] == "Stat Link"
    assert trainer.features[1]["chosen_stat"] == "spdef"


def test_engine_facade_snapshot_exposes_stat_training_and_stratagem_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Ally", [_move("Tackle")]), controller_id="player", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(93),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Attack Training"}, {"name": "Attack Stratagem"}]
    battle.pokemon["player-2"].spec.tutor_points = 2
    facade.battle = battle

    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["stat_training_ready"] is True
    assert hints["stat_training_options"][0]["feature"] == "Attack Training"
    assert hints["stat_training_options"][0]["moves"][0]["move_name"] == "Swords Dance"
    assert hints["stat_stratagem_ready"] is True
    assert hints["stat_stratagem_options"][0]["feature"] == "Attack Stratagem"


def test_engine_facade_snapshot_exposes_generic_stat_training_and_stratagem_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Ally", [_move("Tackle")]), controller_id="player", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(94),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Stat Training", "chosen_stat": "spdef"},
        {"name": "Stat Stratagem", "chosen_stat": "spd"},
    ]
    battle.pokemon["player-2"].spec.tutor_points = 2
    facade.battle = battle

    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    training = next(option for option in hints["stat_training_options"] if option["feature"] == "Stat Training")
    assert training["stat"] == "spdef"
    assert training["stat_label"] == "SpDef"
    assert {move["move_name"] for move in training["moves"]} == {"Amnesia", "Light Screen"}
    stratagem = next(option for option in hints["stat_stratagem_options"] if option["feature"] == "Stat Stratagem")
    assert stratagem["stat"] == "spd"
    assert stratagem["stat_label"] == "Speed"


def test_engine_facade_snapshot_exposes_type_ace_generic_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Ally", [_move("Tackle"), _move("Surf", type="Water", freq="Scene x2")]), controller_id="player", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(95),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Type Ace", "chosen_type": "water"},
        {"name": "Type Refresh", "chosen_type": "water"},
        {"name": "Move Sync", "chosen_type": "electric"},
    ]
    battle.pokemon["player-2"].spec.tutor_points = 2
    battle.frequency_usage["player-2"] = {"Surf": 1}
    facade.battle = battle

    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["type_ace_ready"] is True
    assert hints["type_ace_options"][0]["type_label"] == "Water"
    assert {option["mode"] for option in hints["type_ace_options"][0]["ability_options"]} == {"strategist", "last_chance"}
    assert hints["type_refresh_ready"] is True
    assert hints["type_refresh_options"][0]["scene_moves"][0]["move_name"] == "Surf"
    assert hints["move_sync_ready"] is True
    assert hints["move_sync_options"][0]["type_label"] == "Electric"


def test_engine_facade_snapshot_exposes_type_ace_branch_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Trainer", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "player-2": PokemonState(
                spec=_spec("DarkMon", [_move("Bite", type="Dark"), _move("Surf", type="Water")]),
                controller_id="player",
                position=(1, 2),
                active=True,
            ),
            "player-3": PokemonState(
                spec=_spec("FairyMon", [_move("Fairy Wind", type="Fairy")]),
                controller_id="player",
                position=(2, 2),
                active=True,
            ),
            "player-4": PokemonState(
                spec=_spec("Wing", [_move("Growl", type="Normal", category="Status")]),
                controller_id="player",
                position=(2, 1),
                active=True,
            ),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(96),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Close Quarters Mastery"},
        {"name": "Celerity"},
        {"name": "Foiling Foliage"},
    ]
    battle.pokemon["player-2"].spec.trainer_features = [{"name": "Clever Ruse"}, {"name": "Flood!"}]
    battle.pokemon["player-2"].spec.types = ["Dark", "Water"]
    battle.pokemon["player-3"].spec.trainer_features = [{"name": "Fairy Lights"}]
    battle.pokemon["player-3"].spec.types = ["Fairy"]
    battle.pokemon["player-4"].spec.trainer_features = [{"name": "Foiling Foliage"}]
    battle.pokemon["player-4"].spec.types = ["Flying"]
    facade.battle = battle

    payload = facade.snapshot()
    trainer_entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    trainer_hints = trainer_entry["trainer_action_hints"]
    assert trainer_hints["close_quarters_mastery_ready"] is True
    assert trainer_hints["celerity_ready"] is True
    assert isinstance(trainer_hints["foiling_foliage_options"], list)

    dark_entry = next(item for item in payload["combatants"] if item["id"] == "player-2")
    dark_hints = dark_entry["trainer_action_hints"]
    assert dark_hints["clever_ruse_ready"] is True
    assert dark_hints["flood_ready"] is True

    fairy_entry = next(item for item in payload["combatants"] if item["id"] == "player-3")
    fairy_hints = fairy_entry["trainer_action_hints"]
    assert fairy_hints["fairy_lights_ready"] is True


def test_engine_facade_exposes_fairy_lights_reposition_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("FairyMon", [_move("Fairy Wind", type="Fairy")]),
                controller_id="player",
                position=(2, 2),
                active=True,
            ),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(97),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Fairy Lights"}]
    battle.pokemon["player-1"].spec.types = ["Fairy"]
    battle.pokemon["player-1"].add_temporary_effect("fairy_lights", coord=(2, 2), source="Fairy Lights")
    battle.pokemon["player-1"].add_temporary_effect("fairy_lights", coord=(3, 2), source="Fairy Lights")
    facade.battle = battle

    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["fairy_lights_count"] == 2
    assert hints["fairy_lights_positions"] == [[2, 2], [3, 2]]
    assert any(option["coord"] == [2, 2] for option in hints["fairy_lights_destination_options"])


def test_engine_facade_simulates_attack_maneuver_prompt():
    facade = EngineFacade()
    tackle = MoveSpec(
        name="Tackle",
        type="Normal",
        category="Physical",
        db=6,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players"),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("Ace", [tackle]), controller_id="player", position=(2, 2), active=True),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(2, 3), active=True),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(66),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Attack Maneuver"}]
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "player-1", "move": "Tackle", "target_id": "foe-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") in {"Attack Maneuver", "Stat Maneuver"})
    assert prompt["optional"] is True
    assert {option["value"] for option in prompt["options"]} == {"pass", "three_targets"}


def test_engine_facade_ai_battle_royale_generates_large_biome_grid():
    facade = EngineFacade()
    state = facade.start_encounter(
        random_battle=True,
        ai_mode="ai",
        step_ai=True,
        battle_royale=True,
        side_count=4,
        team_size=1,
        active_slots=1,
        circle_interval=2,
        seed=2026,
    )
    grid = state.get("grid") or {}
    assert int(grid.get("width") or 0) >= 40
    assert int(grid.get("height") or 0) >= 40
    royale = state.get("battle_royale") or {}
    assert royale.get("enabled") is True
    assert int(royale.get("interval") or 0) == 2


def test_engine_facade_ai_battle_royale_circle_closes_and_shrinks():
    facade = EngineFacade()
    state = facade.start_encounter(
        random_battle=True,
        ai_mode="ai",
        step_ai=True,
        battle_royale=True,
        side_count=3,
        team_size=1,
        active_slots=1,
        circle_interval=1,
        seed=303,
    )
    before = int((state.get("battle_royale") or {}).get("current_radius") or 0)
    # One AI step should advance and trigger close when interval=1.
    next_state = facade.ai_step()
    after = int((next_state.get("battle_royale") or {}).get("current_radius") or 0)
    assert after <= before


def test_engine_facade_ai_battle_royale_supports_100_sides():
    facade = EngineFacade()
    state = facade.start_encounter(
        random_battle=True,
        ai_mode="ai",
        step_ai=True,
        battle_royale=True,
        side_count=100,
        team_size=1,
        active_slots=1,
        circle_interval=3,
        seed=9090,
    )
    teams = {str(combatant["team"]) for combatant in state["combatants"]}
    active = [combatant for combatant in state["combatants"] if combatant.get("active")]
    grid = state.get("grid") or {}
    assert len(teams) >= 100
    assert len(active) >= 100
    assert int(grid.get("width") or 0) >= 40
    assert int(grid.get("height") or 0) >= 40


def test_engine_facade_ai_step_exposes_rules_safe_diagnostics():
    facade = EngineFacade()
    facade.start_encounter(
        random_battle=True,
        ai_mode="ai",
        step_ai=True,
        side_count=2,
        team_size=1,
        active_slots=1,
        seed=8080,
    )
    next_state = facade.ai_step()
    diag = next_state.get("ai_diagnostics")
    assert isinstance(diag, dict)
    assert isinstance(diag.get("actor_id"), str) and diag.get("actor_id")
    assert "selected_action" in diag
    assert "selected_score" in diag
    assert isinstance(diag.get("legal_action_count"), int)
    assert isinstance(diag.get("legal_actions_top"), list)
    assert "fallback_reason" in diag
    assert isinstance(diag.get("fallback_used"), bool)
    learning = next_state.get("ai_learning")
    assert isinstance(learning, dict)
    assert isinstance(learning.get("current_model_id"), str) and learning.get("current_model_id")
    assert isinstance(learning.get("updates_since_snapshot"), int)
    assert isinstance(learning.get("total_updates"), int)
    assert isinstance(learning.get("battle"), dict)
    assert isinstance(learning["battle"].get("battle_updates"), int)


def test_engine_facade_backfills_abilities_for_default_campaign_species():
    facade = EngineFacade()
    state = facade.start_encounter(team_size=1, active_slots=1, seed=11)
    by_species = {str(c["species"]): c for c in state["combatants"]}
    assert by_species["Pikachu"]["abilities"]
    assert by_species["Squirtle"]["abilities"]
    assert by_species["Pikachu"]["base_abilities"]
    assert by_species["Squirtle"]["base_abilities"]


def test_struggle_does_not_gain_stab():
    normal_attacker = PokemonState(
        spec=_spec("NormalUser", [_move("Struggle", db=4)], atk=15, defense=10),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    off_type_spec = _spec("OffTypeUser", [_move("Struggle", db=4)], atk=15, defense=10)
    off_type_spec.types = ["Water"]
    off_type_attacker = PokemonState(
        spec=off_type_spec,
        controller_id="a2",
        position=(1, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_spec("Defender", [_move("Tackle")], atk=6, defense=12),
        controller_id="b",
        position=(0, 1),
        active=True,
    )
    move = _move("Struggle", db=4)
    normal_result = resolve_move_action(
        rng=random.Random(11),
        attacker=normal_attacker,
        defender=defender,
        move=move,
        weather="Clear",
        force_hit=True,
    )
    off_type_result = resolve_move_action(
        rng=random.Random(11),
        attacker=off_type_attacker,
        defender=defender,
        move=move,
        weather="Clear",
        force_hit=True,
    )
    assert normal_result["hit"] is True
    assert off_type_result["hit"] is True
    assert int(normal_result["stab_db"]) == int(off_type_result["stab_db"])
    assert int(normal_result["damage"]) == int(off_type_result["damage"])


def test_protect_is_not_automatic_without_status():
    attacker_move = _move("Tackle", db=10)
    defender_move = _move("Protect", category="Status", db=0, range_kind="Self", target_kind="Self")
    attacker = PokemonState(
        spec=_spec("Attacker", [attacker_move], atk=24, defense=8),
        controller_id="player",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_spec("Defender", [defender_move], atk=8, defense=4),
        controller_id="foe",
        position=(0, 1),
        active=True,
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="player"),
            "foe": TrainerState(identifier="foe", name="Foe", team="foe"),
        },
        pokemon={
            "player-1": attacker,
            "foe-1": defender,
        },
        rng=random.Random(5),
    )
    before_hp = defender.hp
    battle.resolve_move_targets("player-1", attacker_move, "foe-1", defender.position)
    block_logs = [
        event
        for event in battle.log
        if "blocks the incoming attack" in str(event.get("description") or "").lower()
    ]
    assert not block_logs
    assert defender.hp < before_hp


def test_hunger_switch_prompt_blocks_until_choice():
    facade = EngineFacade()
    facade.start_encounter(team_size=1, active_slots=1, seed=17)
    battle = facade.battle
    assert battle is not None
    actor_id = None
    for cid, mon in battle.pokemon.items():
        if battle.is_player_controlled(cid) and mon.active and not mon.fainted:
            actor_id = cid
            break
    if actor_id is None:
        actor_id = next(iter(battle.pokemon))
    battle.current_actor_id = actor_id
    actor = battle.pokemon[actor_id]
    actor.spec.abilities = ["Hunger Switch"]
    actor.add_temporary_effect("hunger_switch_pending", round=battle.round)
    facade._pending_action = None
    facade._pending_prompts = []
    facade._advance_until_player()
    assert facade._pending_prompts
    prompt = facade._pending_prompts[0]
    print(f"Hunger Switch prompt: {prompt}")
    assert prompt.get("kind") == "hunger_switch"
    prompt_id = prompt.get("id")
    facade.resolve_prompts({prompt_id: True})
    print(f"Hunger Switch mode effects: {actor.get_temporary_effects('hunger_switch_mode')}")
    assert actor.get_temporary_effects("hunger_switch_mode")


def test_pressure_applies_suppressed_and_ui_status():
    pressure_spec = _spec("PressureUser", [_move("Tackle")])
    pressure_spec.spd = 20
    pressure_user = PokemonState(
        spec=pressure_spec,
        controller_id="player",
        position=(0, 0),
        active=True,
    )
    pressure_user.spec.abilities = ["Pressure"]
    target = PokemonState(
        spec=_spec("Target", [_move("Tackle")]),
        controller_id="foe",
        position=(2, 0),
        active=True,
    )
    grid = GridState(width=4, height=4, blockers=set(), tiles={(0, 0): {}, (2, 0): {}})
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="player"),
            "foe": TrainerState(identifier="foe", name="Foe", team="foe"),
        },
        pokemon={
            "player-1": pressure_user,
            "foe-1": target,
        },
        grid=grid,
        rng=random.Random(3),
    )
    for _ in range(4):
        battle.advance_turn()
        if battle.current_actor_id == "player-1":
            break
    suppress_events = [evt for evt in battle.log if evt.get("ability") == "Pressure"]
    print(f"Pressure events: {suppress_events}")
    print(f"Pressure target statuses raw: {target.statuses}")
    facade = EngineFacade()
    facade.battle = battle
    state = facade.snapshot()
    target_entry = next(entry for entry in state["combatants"] if entry["id"] == "foe-1")
    print(f"Pressure UI statuses: {target_entry['statuses']}")
    assert any(status.startswith("Suppressed") for status in target_entry["statuses"])


def test_hazards_appear_in_grid_snapshot():
    facade = EngineFacade()
    state = facade.start_encounter(campaign="levitate_demo", team_size=1, active_slots=1, seed=23)
    grid = state.get("grid")
    assert grid is not None
    tiles = grid.get("tiles", [])
    hazard_tiles = [tile for tile in tiles if isinstance(tile, list) and len(tile) > 3 and tile[3]]
    print(f"Hazard tiles: {hazard_tiles[:4]}")
    assert hazard_tiles


def test_engine_facade_move_action_accepts_gimmick_flags():
    facade = EngineFacade()
    facade.start_encounter(team_size=1, active_slots=1, seed=23)
    battle = facade.battle
    assert battle is not None
    actor_id = next(
        cid for cid, mon in battle.pokemon.items() if mon.active and not mon.fainted and battle.is_player_controlled(cid)
    )
    target_id = next(cid for cid in battle.pokemon if cid != actor_id)
    action = facade._build_action(
        battle,
        {
            "type": "move",
            "actor_id": actor_id,
            "move_name": "Tackle",
            "target_id": target_id,
            "teracrystal": True,
            "tera_type": "Ghost",
            "mega_evolve": False,
            "dynamax": False,
            "z_move": False,
        },
    )
    assert action.teracrystal is True
    assert action.tera_type == "Ghost"
    assert action.mega_evolve is False
    assert action.dynamax is False
    assert action.z_move is False


def test_engine_facade_builds_trainer_feature_action_from_registry_key():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Confide", category="Status", range_kind="Ranged", target_kind="Ranged")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "actor_id": "player-1",
            "action_key": "quick_wit_move",
            "move_name": "Confide",
            "target_id": "foe-1",
        },
    )
    assert isinstance(action, QuickWitMoveAction)


def test_engine_facade_builds_direct_trainer_feature_action_type():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    action = facade._build_action(
        battle,
        {
            "type": "dirty_fighting_follow_up",
            "actor_id": "player-1",
            "trick": "Hinder",
            "target_id": "foe-1",
        },
    )
    assert isinstance(action, DirtyFightingFollowUpAction)


def test_engine_facade_builds_weapon_finesse_follow_up_action_type():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    action = facade._build_action(
        battle,
        {
            "type": "weapon_finesse_follow_up",
            "actor_id": "player-1",
            "maneuver": "Trip",
            "target_id": "foe-1",
        },
    )
    assert isinstance(action, WeaponFinesseFollowUpAction)


def test_engine_facade_snapshot_includes_trainer_action_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", ap=2), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Trainer", [_move("Confide", category="Status", range_kind="Ranged", target_kind="Ranged")]),
                controller_id="player",
                position=(1, 1),
            ),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.trainers["player"].skills = {"acrobatics": 3}
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Quick Wit"}, {"name": "Flight"}]
    battle.pokemon["player-1"].spec.movement["levitate"] = 2
    battle.pokemon["player-1"].add_temporary_effect("psychic_resonance_ready", target="foe-1", expires_round=0)
    battle.pokemon["player-1"].add_temporary_effect("play_them_like_a_fiddle_ready", target="foe-1", move="Confide", expires_round=0)
    battle.pokemon["foe-1"].statuses.append({"name": "Disabled", "move": "Tackle", "remaining": 2})
    battle._mark_manipulate_used(battle.pokemon["player-1"], "foe-1", "bon mot")
    battle._mark_manipulate_used(battle.pokemon["player-1"], "foe-1", "flirt")
    battle._mark_manipulate_used(battle.pokemon["player-1"], "foe-1", "terrorize")
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    assert "Quick Wit" in entry["trainer_features"]
    assert "social_moves" in entry["trainer_action_hints"]
    assert entry["trainer_action_hints"]["quick_wit_manipulate_targets"] == []
    assert "enchanting_gaze_anchors" in entry["trainer_action_hints"]
    assert entry["trainer_action_hints"]["quick_wit_manipulate_options"] == []
    assert entry["trainer_action_hints"]["psychic_resonance_targets"] == ["foe-1"]
    assert entry["trainer_action_hints"]["play_them_like_a_fiddle_ready"][0]["move"] == "Confide"
    assert entry["trainer_action_hints"]["play_them_like_a_fiddle_ready"][0]["target_moves"] == []
    assert entry["trainer_action_hints"]["trainer_ap"] == 2
    assert entry["trainer_action_hints"]["enchanting_gaze_ap_ready"] is True
    assert entry["trainer_action_hints"]["dirty_fighting_ap_ready"] is True
    assert entry["trainer_action_hints"]["weapon_finesse_ap_ready"] is True
    assert entry["trainer_action_hints"]["quick_wit_uses_left"] == 3
    assert entry["trainer_action_hints"]["psychic_resonance_uses_left"] == 2
    assert entry["trainer_action_hints"]["play_them_like_a_fiddle_uses_left"] == 3
    assert entry["trainer_action_hints"]["flight_speed"] == 5
    assert entry["trainer_action_hints"]["flight_active"] is False
    assert entry["trainer_action_hints"]["flight_ap_ready"] is True


def test_engine_facade_filters_out_of_range_follow_up_targets():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(8, 8)),
        },
        grid=GridState(width=9, height=9),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Dirty Fighting"}, {"name": "Weapon Finesse"}]
    battle.pokemon["player-1"].add_temporary_effect("dirty_fighting_ready", target="foe-1", expires_round=0)
    battle.pokemon["player-1"].add_temporary_effect("weapon_finesse_ready", target="foe-1", expires_round=0)
    battle.pokemon["player-1"].add_temporary_effect("psychic_resonance_ready", target="foe-1", expires_round=0)
    battle.pokemon["player-1"].add_temporary_effect("trickster_ready", target="foe-1", expires_round=0)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["dirty_fighting_targets"] == []
    assert hints["weapon_finesse_targets"] == []
    assert hints["psychic_resonance_targets"] == []
    assert hints["trickster_targets"] == []


def test_engine_facade_exposes_sleight_status_options():
    facade = EngineFacade()
    confide = _move("Confide", category="Status", range_kind="Ranged", target_kind="Ranged", keywords=["Social"])
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [confide]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Sleight"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["sleight_ready"] is True
    assert hints["sleight_options"][0]["move"] == "Confide"


def test_engine_facade_exposes_shell_game_hazard_options():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", skills={"guile": 4})},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Shell Game"}]
    battle._place_hazard((1, 1), "spikes", 1, source_id="player-1", allow_shell_game=False)
    battle._place_hazard((2, 1), "spikes", 1, source_id="player-1", allow_shell_game=False)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["shell_game_ready"] is True
    assert hints["shell_game_uses_left"] == 2
    assert hints["shell_game_options"][0]["hazard"] == "spikes"
    assert hints["shell_game_options"][0]["total_layers"] == 2


def test_engine_facade_filters_play_them_like_a_fiddle_for_fainted_target():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Confide", category="Status", range_kind="Ranged", target_kind="Ranged")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.pokemon["foe-1"].hp = 0
    battle.pokemon["player-1"].add_temporary_effect("play_them_like_a_fiddle_ready", target="foe-1", move="Confide", expires_round=0)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    assert entry["trainer_action_hints"]["play_them_like_a_fiddle_ready"] == []


def test_engine_facade_builds_flight_action_type():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    action = facade._build_action(
        battle,
        {
            "type": "flight",
            "actor_id": "player-1",
        },
    )
    assert isinstance(action, FlightAction)


def test_engine_facade_marks_flight_active_in_snapshot():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", skills={"acrobatics": 3}), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.round = 2
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Flight"}]
    battle.pokemon["player-1"].spec.movement["levitate"] = 2
    battle.pokemon["player-1"].add_temporary_effect("feature_round_marker", feature="Flight", round=2, expires_round=2)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    assert entry["trainer_action_hints"]["flight_active"] is True


def test_engine_facade_simulates_dive_interrupt_prompt():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Diver", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(
                spec=_spec("Shooter", [_move("Water Gun", category="Special", range_kind="Ranged", target_kind="Ranged")]),
                controller_id="foe",
                position=(1, 4),
            ),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Dive"}]
    battle.pokemon["player-1"].spec.movement["overland"] = 3
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Water Gun", "target_id": "player-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Dive")
    assert prompt["actor_name"] == "Diver"
    assert prompt["attacker_name"] == "Shooter"
    assert prompt["trainer_name"] == "Player"


def test_engine_facade_simulates_coaching_prompt_for_maneuver():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", ap=1), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("CoachMon", [_move("Trip")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("FoeMon", [_move("Tackle")]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Coaching"}]
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "player-1", "move": "Trip", "target_id": "foe-1"})
    assert any(prompt.get("feature") == "Coaching" for prompt in prompts)


def test_engine_facade_simulates_telepathic_warning_prompt():
    facade = EngineFacade()
    burst = MoveSpec(
        name="Shockwave Pulse",
        type="Electric",
        category="Special",
        db=6,
        ac=2,
        range_kind="Burst",
        range_value=1,
        target_kind="Self",
        target_range=0,
        area_kind="Burst",
        area_value=1,
        freq="At-Will",
    )
    telepath = _spec("Telepath", [burst])
    telepath.trainer_features = [{"name": "Telepathic Warning"}]
    telepath.capabilities = [{"name": "Telepath"}]
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
        pokemon={
            "player-1": PokemonState(spec=telepath, controller_id="player", position=(2, 2)),
            "player-2": PokemonState(spec=_spec("Ally", [burst]), controller_id="player", position=(2, 3)),
            "foe-1": PokemonState(spec=_spec("Foe", [_move("Tackle")]), controller_id="foe", position=(4, 4)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "player-1", "move": "Shockwave Pulse", "target_id": "player-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Telepathic Warning")
    assert prompt["actor_name"] == "Telepath"
    assert prompt["attacker_name"] == "Telepath"
    assert prompt["trainer_name"] == "Player"
    assert prompt["allied_targets"] == ["player-2"]
    assert prompt["allied_target_name_player-2"] == "Ally"


def test_engine_facade_snapshot_exposes_named_trainer_feature_targets():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Dirty Fighting"}, {"name": "Weapon Finesse"}]
    battle.pokemon["player-1"].add_temporary_effect("dirty_fighting_ready", target="foe-1", expires_round=1)
    battle.pokemon["player-1"].add_temporary_effect("weapon_finesse_ready", target="foe-1", expires_round=1)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["dirty_fighting_options"][0]["target_name"] == "Target"
    assert hints["weapon_finesse_target_options"][0]["target_name"] == "Target"


def test_engine_facade_snapshot_exposes_taskmaster_and_quick_healing_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", position=(1, 1))},
        pokemon={
            "player-1": PokemonState(spec=_spec("Coach", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "player-2": PokemonState(spec=_spec("Bruiser", [_move("Tackle")]), controller_id="player", position=(1, 2)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Brutal Training"},
        {"name": "Taskmaster"},
        {"name": "Quick Healing"},
    ]
    battle.pokemon["player-2"].injuries = 2
    battle.pokemon["player-2"].add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["brutal_training_ready"] is True
    assert hints["taskmaster_ready"] is True
    assert hints["quick_healing_ready"] is True
    assert any(option["target"] == "player-2" and option["target_name"] == "Bruiser" for option in hints["brutal_training_targets"])
    assert any(
        option["target"] == "player-2" and option["injuries"] == 2 and option["hardened"] is True
        for option in hints["quick_healing_targets"]
    )


def test_engine_facade_snapshot_excludes_trainer_combatants_from_taskmaster_and_quick_healing_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", position=(1, 1))},
        pokemon={
            "player-1": PokemonState(spec=_spec("Coach", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "player-2": PokemonState(spec=_spec("Bruiser", [_move("Tackle")]), controller_id="player", position=(1, 2)),
            "player-3": PokemonState(spec=_spec("Assistant", [_move("Tackle")]), controller_id="player", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(4),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-3"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Brutal Training"},
        {"name": "Taskmaster"},
        {"name": "Quick Healing"},
        {"name": "Press"},
    ]
    battle.pokemon["player-2"].injuries = 2
    battle.pokemon["player-2"].add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
    battle.pokemon["player-3"].injuries = 2
    battle.pokemon["player-3"].add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
    facade.battle = battle

    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert [option["target"] for option in hints["quick_healing_targets"]] == ["player-2"]
    assert [option["target"] for option in hints["press_targets"]] == ["player-2"]


def test_engine_facade_simulates_press_on_prompt():
    facade = EngineFacade()
    slash = MoveSpec(
        name="Scratch",
        type="Normal",
        category="Physical",
        db=1,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players", ap=2, skills={"intimidate": 4}),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("Bruiser", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Attacker", [slash]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Press On!"}]
    battle.pokemon["player-1"].injuries = 1
    battle.pokemon["player-1"].add_temporary_effect("hardened", source="Taskmaster", source_id="player-1")
    battle.pokemon["player-1"].hp = 1
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Scratch", "target_id": "player-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Press On!")
    assert prompt["actor_name"] == "Bruiser"
    assert prompt["trainer_name"] == "Player"
    assert prompt["ap_cost"] == 1
    assert prompt["trigger"] == "damage"


def test_engine_facade_simulates_not_yet_prompt():
    facade = EngineFacade()
    scratch = MoveSpec(
        name="Scratch",
        type="Normal",
        category="Physical",
        db=1,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players"),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("Soul", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Attacker", [scratch]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Not Yet!"}]
    battle.pokemon["player-1"].hp = 1
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Scratch", "target_id": "player-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Not Yet!")
    assert prompt["actor_name"] == "Soul"
    assert prompt["trainer_name"] == "Player"
    assert prompt["kind"] == "choice"
    assert any(option["value"] == "Tackle||foe-1" for option in prompt["options"])
    assert prompt["trigger"] == "damage"


def test_engine_facade_simulates_not_yet_prompt_with_area_move_option():
    facade = EngineFacade()
    scratch = MoveSpec(
        name="Scratch",
        type="Normal",
        category="Physical",
        db=1,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    discharge = MoveSpec(
        name="Discharge",
        type="Electric",
        category="Special",
        db=8,
        ac=2,
        range_kind="Self",
        range_value=0,
        target_kind="Self",
        target_range=0,
        area_kind="Burst",
        area_value=2,
        freq="Scene",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players"),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("Soul", [discharge]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Attacker", [scratch]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Not Yet!"}]
    battle.pokemon["player-1"].hp = 1
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Scratch", "target_id": "player-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Not Yet!")
    assert any(option["value"] == "Discharge||player-1" for option in prompt["options"])


def test_engine_facade_simulates_strike_of_the_whip_prompt():
    tackle = _move("Tackle", ac=2)
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players", ap=4),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(
                spec=PokemonSpec(
                    species="Taskmaster",
                    level=20,
                    types=["Normal"],
                    hp_stat=12,
                    atk=12,
                    defense=12,
                    spatk=12,
                    spdef=12,
                    spd=12,
                    trainer_features=[{"name": "Press"}, {"name": "Strike of the Whip"}, {"name": "Reckless Advance"}],
                    tags=["trainer"],
                    moves=[tackle],
                ),
                controller_id="player",
                position=(1, 1),
            ),
            "player-2": PokemonState(spec=_spec("Ally", [tackle]), controller_id="player", position=(1, 2)),
            "foe-1": PokemonState(spec=_spec("Foe", [tackle]), controller_id="foe", position=(4, 4)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(3),
    )
    facade = EngineFacade()
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "trainer_feature", "actor_id": "player-1", "action_key": "press", "target_id": "player-2"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Strike of the Whip")
    assert prompt["trigger"] == "press"
    assert any(option["value"] == "injury_temp_hp" for option in prompt["options"])
    assert any(option["value"] == "order:reckless advance" for option in prompt["options"])


def test_engine_facade_snapshot_exposes_press_and_savage_strike_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", position=(1, 1))},
        pokemon={
            "player-1": PokemonState(spec=_spec("Coach", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "player-2": PokemonState(spec=_spec("Bruiser", [_move("Bite", type="Dark")]), controller_id="player", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Press"}, {"name": "Savage Strike"}]
    battle.pokemon["player-2"].spec.tutor_points = 2
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["press_ready"] is True
    assert any(option["target"] == "player-2" and option["target_name"] == "Bruiser" for option in hints["press_targets"])
    assert hints["savage_strike_ready"] is True
    assert any(option["target"] == "player-2" and option["tutor_points"] == 2 for option in hints["savage_strike_targets"])


def test_engine_facade_snapshot_and_build_action_support_commanders_voice():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Commander", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "player-2": PokemonState(spec=_spec("Ally1", [_move("Tackle")]), controller_id="player", position=(2, 1)),
            "player-3": PokemonState(spec=_spec("Ally2", [_move("Tackle")]), controller_id="player", position=(3, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Commander's Voice"},
        {"name": "Focused Command"},
        {"name": "Long Shot"},
    ]
    battle.round = 1
    battle.current_actor_id = "player"
    battle.phase = TurnPhase.ACTION
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["commanders_voice_ready"] is True
    assert any(option["order"] == "long shot" for option in hints["target_orders"])
    assert any(option["order"] == "long shot" for option in hints["commanders_voice_orders"])
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "actor_id": "player-1",
            "action_key": "commanders_voice",
            "mode": "double_order",
            "order_name": "Focused Command",
            "primary_target_id": "player-2",
            "secondary_target_id": "player-3",
            "secondary_order_name": "Long Shot",
            "second_target_id": "player-2",
        }
    )
    assert action.__class__.__name__ == "CommandersVoiceAction"


def test_engine_facade_simulates_deadly_gambit_prompt():
    facade = EngineFacade()
    slash = MoveSpec(
        name="Slash",
        type="Normal",
        category="Physical",
        db=8,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players"), "foe": TrainerState(identifier="foe", name="Foe", team="foes")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Gambler", [slash]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Attacker", [slash]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Deadly Gambit"}]
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Slash", "target_id": "player-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Deadly Gambit")
    assert prompt["actor_name"] == "Gambler"
    assert prompt["attacker_name"] == "Attacker"
    assert prompt["kind"] == "choice"
    assert prompt["options"]


def test_engine_facade_snapshot_exposes_quick_switch_replacements():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Lead", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=None, active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Quick Switch"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["quick_switch_ap_ready"] is True
    assert hints["quick_switch_ap_cost"] == 2
    assert hints["quick_switch_replacements"][0]["target_name"] == "Bench"


def test_engine_facade_snapshot_reduces_quick_switch_ap_cost_for_juggler():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=1)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Lead", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=None, active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Quick Switch"}, {"name": "Juggler"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["quick_switch_ap_cost"] == 1
    assert hints["quick_switch_ap_ready"] is True
    assert hints["quick_switch_replacements"][0]["target_name"] == "Bench"


def test_engine_facade_simulates_bigger_and_boulder_choice_prompt():
    facade = EngineFacade()
    stone_edge = MoveSpec(
        name="Stone Edge",
        type="Rock",
        category="Physical",
        db=10,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players", skills={"combat": 4}),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("RockAce", [stone_edge]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 2)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(7),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Bigger and Boulder"}]
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "player-1", "move": "Stone Edge", "target_id": "foe-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Bigger and Boulder")
    assert prompt["kind"] == "choice"
    assert prompt["target_name"] == "Target"
    assert prompt["options"]


def test_engine_facade_simulates_gravel_before_me_prompt_on_rock_miss():
    facade = EngineFacade()
    rock_slide = MoveSpec(
        name="Rock Slide",
        type="Rock",
        category="Physical",
        db=8,
        ac=6,
        range_kind="Ranged",
        range_value=6,
        target_kind="Ranged",
        target_range=6,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players"),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("RockAce", [rock_slide]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(3, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(7),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Gravel Before Me"}]
    battle.pokemon["player-1"].spec.moves[0].ac = 99
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "player-1", "move": "Rock Slide", "target_id": "foe-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Gravel Before Me")
    assert prompt["kind"] == "choice"
    assert prompt["actor_name"] == "RockAce"
    assert prompt["options"]


def test_engine_facade_simulates_round_trip_prompt_after_move():
    facade = EngineFacade()
    slash = MoveSpec(
        name="Slash",
        type="Normal",
        category="Physical",
        db=6,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players", ap=1),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("Lead", [slash]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=None, active=False),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(11),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Round Trip"}]
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "player-1", "move": "Slash", "target_id": "foe-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Round Trip")
    assert prompt["kind"] == "choice"
    assert prompt["move"] == "Slash"
    assert prompt["options"][0]["label"] == "Bench"


def test_engine_facade_snapshot_exposes_emergency_release_targets():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=None, active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(5),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Emergency Release"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["emergency_release_ap_ready"] is True
    assert hints["emergency_release_targets"][0]["target_name"] == "Bench"


def test_engine_facade_simulates_emergency_release_interrupt_prompt():
    facade = EngineFacade()
    slash = MoveSpec(
        name="Slash",
        type="Normal",
        category="Physical",
        db=6,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=2),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=None, active=False),
            "foe-1": PokemonState(spec=_spec("Target", [slash]), controller_id="foe", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(6),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Emergency Release"}]
    facade.battle = battle
    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Slash", "target_id": "player-1"})
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Emergency Release")
    assert prompt["kind"] == "choice"
    assert prompt["options"][0]["label"] == "Bench"


def test_engine_facade_snapshot_exposes_bounce_shot_targets():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=None, active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(7),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Bounce Shot"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["bounce_shot_ready"] is True
    assert hints["bounce_shot_targets"][0]["target_name"] == "Bench"


def test_engine_facade_snapshot_exposes_moment_of_action_and_go_fight_win_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players"),
            "ally-trainer": TrainerState(identifier="ally-trainer", name="Ally", controller_kind="player", team="players"),
        },
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Trainer", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(7),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Moment of Action"}, {"name": "Go, Fight, Win!"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["moment_of_action_ready"] is True
    assert {option["target"] for option in hints["moment_of_action_targets"]} == {"player", "ally-trainer"}
    assert hints["go_fight_win_ready"] is True
    assert {option["value"] for option in hints["go_fight_win_cheers"]} == {
        "show_your_best",
        "dont_stop_now",
        "i_believe_in_you",
    }


def test_engine_facade_snapshot_exposes_cheerleader_playtest_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=(1, 2), active=True),
            "player-3": PokemonState(spec=_spec("Candidate", [_move("Tackle")]), controller_id="player", position=(2, 2), active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(7),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Cheerleader [Playtest]"}]
    battle.pokemon["player-2"].spec.tutor_points = 2
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["cheerleader_playtest_ready"] is True
    assert hints["cheerleader_playtest_targets"][0]["target"] == "player-2"


def test_engine_facade_snapshot_exposes_vim_and_vigor_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=(1, 2), active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(9),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Vim and Vigor"}]
    battle.pokemon["player-2"].spec.tutor_points = 2
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["vim_and_vigor_ready"] is True
    assert hints["vim_and_vigor_targets"][0]["target"] == "player-2"


def test_engine_facade_snapshot_exposes_ramming_speed_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Mount", [_move("Tackle")]), controller_id="player", position=(1, 2), active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(91),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Ramming Speed"}]
    battle.pokemon["player-2"].spec.tutor_points = 2
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["ramming_speed_ready"] is True
    assert hints["ramming_speed_targets"][0]["target"] == "player-2"


def test_engine_facade_snapshot_exposes_rider_mount_and_conquerors_march_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Mount", [_move("Tackle")]), controller_id="player", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(92),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Mounted Prowess"},
        {"name": "Ride as One"},
        {"name": "Conqueror's March"},
    ]
    battle.pokemon["player-2"].add_temporary_effect("ability_granted", ability="Run Up", source="Ramming Speed", source_id="player-1")

    facade.battle = battle
    payload = facade.snapshot()
    trainer_entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    trainer_hints = trainer_entry["trainer_action_hints"]
    assert trainer_hints["mount_ready"] is True
    assert trainer_hints["mount_targets"][0]["target"] == "player-2"
    assert trainer_hints["mounted_partner_id"] is None

    battle._mount_pair("player-1", "player-2")
    battle.current_actor_id = "player-1"
    payload = facade.snapshot()
    trainer_entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    trainer_hints = trainer_entry["trainer_action_hints"]
    assert trainer_hints["mounted_partner_id"] == "player-2"
    assert trainer_hints["mounted_mount_id"] == "player-2"
    assert trainer_hints["dismount_ready"] is True
    assert trainer_hints["ride_as_one_swap_ready"] is True
    assert trainer_hints["conquerors_march_ready"] is True
    assert trainer_hints["conquerors_march_target"] == "player-2"


def test_engine_facade_snapshot_exposes_versatile_wardrobe_and_swap_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Tackle")]), controller_id="player", position=(1, 2), active=True),
            "player-3": PokemonState(spec=_spec("Candidate", [_move("Tackle")]), controller_id="player", position=(2, 2), active=False),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(11),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Versatile Wardrobe"}, {"name": "Dress to Impress"}]
    battle.pokemon["player-2"].spec.tutor_points = 2
    battle.pokemon["player-3"].spec.tutor_points = 2
    battle.pokemon["player-2"].spec.tags = ["Chic"]
    battle.pokemon["player-2"].spec.items = [{"name": "Muscle Band"}]
    battle.pokemon["player-2"].spec.poke_edge_choices = {
        "versatile_wardrobe": {"chic": True, "slot_count": 2, "extra_slots": [{"name": "Charcoal"}, None]}
    }
    facade.battle = battle

    payload = facade.snapshot()

    trainer_entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    trainer_hints = trainer_entry["trainer_action_hints"]
    assert trainer_hints["versatile_wardrobe_ready"] is True
    assert trainer_hints["versatile_wardrobe_targets"][0]["target"] == "player-3"
    assert trainer_hints["dress_to_impress_ready"] is True
    assert trainer_hints["dress_to_impress_targets"][0]["target"] == "player-2"
    assert trainer_hints["dress_to_impress_targets"][0]["items"] == ["Charcoal"]
    chic_entry = next(item for item in payload["combatants"] if item["id"] == "player-2")
    chic_hints = chic_entry["trainer_action_hints"]
    assert chic_hints["wardrobe_swap_ready"] is True
    assert chic_hints["wardrobe_swap_active_items"][0]["item"] == "Muscle Band"
    assert chic_hints["wardrobe_swap_stored_items"][0]["item"] == "Charcoal"


def test_engine_facade_snapshot_exposes_dashing_makeover_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=4)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Model", [_move("Tackle")]), controller_id="player", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(12),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Dashing Makeover"}]
    facade.battle = battle

    payload = facade.snapshot()

    trainer_entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = trainer_entry["trainer_action_hints"]
    assert hints["dashing_makeover_ready"] is True
    assert hints["dashing_makeover_targets"][0]["target"] == "player-1"
    target = next(entry for entry in hints["dashing_makeover_targets"] if entry["target"] == "player-2")
    assert any(item["item"] == "Muscle Band" for item in target["items"])

    create_trainer_feature_action(
        "dashing_makeover",
        actor_id="player-1",
        target_id="player-2",
        item_name="Muscle Band",
    ).resolve(battle)

    payload = facade.snapshot()
    trainer_entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = trainer_entry["trainer_action_hints"]
    assert hints["dashing_makeover_ready"] is False
    assert hints["dashing_makeover_release_ready"] is True
    assert hints["dashing_makeover_bound"]["target_id"] == "player-2"
    assert hints["dashing_makeover_bound"]["item_name"] == "Muscle Band"


def test_engine_facade_snapshot_exposes_parfumier_incense_move():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Perfumed", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(13),
    )
    battle.pokemon["player-1"].spec.items = [{"name": "Rose Incense", "parfumier_move": "Sweet Scent"}]
    facade.battle = battle

    payload = facade.snapshot()

    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    move_names = {move["name"] for move in entry["moves"]}
    assert "Sweet Scent" in move_names
    sweet_scent = next(move for move in entry["moves"] if move["name"] == "Sweet Scent")
    assert sweet_scent["source"] == "Rose Incense"


def test_engine_facade_simulates_first_blood_prompt_after_emergency_release():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1), active=True),
            "player-2": PokemonState(spec=_spec("Bench", [_move("Water Gun", category="Special", range_kind="Ranged", target_kind="Ranged", db=4)]), controller_id="player", position=None, active=False),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 2), active=True),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(8),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Emergency Release"}]
    battle.pokemon["player-2"].spec.trainer_features = [{"name": "First Blood"}]
    facade.battle = battle
    prompts = facade._simulate_prompts(
        {
            "type": "trainer_feature",
            "action_key": "emergency_release",
            "actor_id": "player-1",
            "replacement_id": "player-2",
        }
    )
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "First Blood")
    assert prompt["kind"] == "choice"
    assert prompt["trigger"] == "send_out"
    assert any(option["value"] == "Water Gun||foe-1" for option in prompt["options"])


def test_engine_facade_simulates_surprise_prompt_on_attack():
    facade = EngineFacade()
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=2),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Trainer", [_move("Slash", ac=2, db=6)]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "foe-1": PokemonState(
                spec=_spec("Target", [_move("Tackle")]),
                controller_id="foe",
                position=(1, 2),
                active=True,
            ),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(12),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Surprise!"}]
    facade.battle = battle

    prompts = facade._simulate_prompts({"type": "move", "actor_id": "player-1", "move": "Slash", "target_id": "foe-1"})

    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Surprise!")
    assert prompt["trigger"] == "attack"
    assert prompt["ap_cost"] == 2


def test_engine_facade_simulates_resilience_prompt_on_critical_hit():
    facade = EngineFacade()
    crit_move = MoveSpec(
        name="Critical Slash",
        type="Normal",
        category="Physical",
        db=8,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
        crit_range=1,
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=2),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Tank", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "foe-1": PokemonState(
                spec=_spec("Attacker", [crit_move]),
                controller_id="foe",
                position=(1, 2),
                active=True,
            ),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(3),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Resilience"}]
    facade.battle = battle

    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Critical Slash", "target_id": "player-1"})

    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Resilience")
    assert prompt["trigger"] == "critical_hit"
    assert prompt["ap_cost"] == 2
    assert prompt["actor_name"] == "Tank"


def test_engine_facade_simulates_style_is_eternal_prompt_on_covet():
    facade = EngineFacade()
    covet = MoveSpec(
        name="Covet",
        type="Normal",
        category="Physical",
        db=6,
        ac=None,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
        freq="At-Will",
        range_text="Melee, 1 Target",
    )
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", controller_kind="player", team="players", ap=1),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Soul", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "foe-1": PokemonState(
                spec=_spec("Thief", [covet]),
                controller_id="foe",
                position=(1, 2),
                active=True,
            ),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(31),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Style is Eternal"}]
    battle.pokemon["player-1"].spec.items = [{"name": "Charcoal"}]
    facade.battle = battle

    prompts = facade._simulate_prompts({"type": "move", "actor_id": "foe-1", "move": "Covet", "target_id": "player-1"})

    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Style is Eternal")
    assert prompt["kind"] == "confirm"
    assert prompt["trigger"] == "item_theft"
    assert prompt["item"] == "Charcoal"
    assert prompt["move"] == "Covet"
    assert prompt["ap_cost"] == 1


def test_engine_facade_snapshot_exposes_tough_as_schist_targets():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "player-2": PokemonState(spec=_spec("RockMon", [_move("Tackle")]), controller_id="player", position=(2, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(7),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Tough as Schist"}]
    battle.pokemon["player-2"].spec.types = ["Rock"]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["tough_as_schist_ap_ready"] is True
    assert hints["tough_as_schist_targets"][0]["target_name"] == "RockMon"


def test_engine_facade_builds_psychic_resonance_follow_up_action_type():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player"), "foe": TrainerState(identifier="foe", name="Foe")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    action = facade._build_action(
        battle,
        {
            "type": "psychic_resonance_follow_up",
            "actor_id": "player-1",
            "target_id": "foe-1",
        },
    )
    assert isinstance(action, PsychicResonanceFollowUpAction)


def test_engine_facade_snapshot_and_build_action_support_order_spread_features():
    facade = EngineFacade()
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players", ap=4),
            "ally": TrainerState(identifier="ally", name="Ally", team="players"),
        },
        pokemon={
            "player-1": PokemonState(spec=_spec("Commander", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Tank1", [_move("Tackle")]), controller_id="player", position=(2, 1)),
            "ally-2": PokemonState(spec=_spec("Tank2", [_move("Tackle")]), controller_id="ally", position=(5, 1)),
            "ally-3": PokemonState(spec=_spec("Tank3", [_move("Tackle")]), controller_id="player", position=(12, 1)),
        },
        grid=GridState(width=20, height=6),
        rng=random.Random(9),
    )
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Leadership"},
        {"name": "Battle Conductor"},
        {"name": "Scheme Twist"},
        {"name": "Tip the Scales"},
        {"name": "Brace for Impact"},
        {"name": "Long Shot"},
    ]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["battle_conductor_ready"] is True
    assert hints["scheme_twist_ready"] is True
    assert hints["tip_the_scales_ready"] is True
    assert any(target["target"] == "ally-2" for target in hints["order_targets"])
    assert any(target["target"] == "ally-2" for target in hints["tip_the_scales_targets"])
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "feature_action": "battle_conductor",
            "actor_id": "player-1",
            "order_name": "Brace for Impact",
            "target_ids": ["ally-1", "ally-2"],
        },
    )
    assert type(action).__name__ == "SpreadOrderAction"
    assert getattr(action, "mode") == "battle_conductor"


def test_engine_facade_snapshot_and_build_action_support_mobilize_and_complex_orders():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Commander", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Tank", [_move("Tackle")]), controller_id="player", position=(2, 1)),
            "ally-2": PokemonState(spec=_spec("Runner", [_move("Tackle")]), controller_id="player", position=(3, 1)),
        },
        grid=GridState(width=8, height=8),
        rng=random.Random(12),
    )
    battle.current_actor_id = "player"
    battle.phase = TurnPhase.ACTION
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Mobilize"},
        {"name": "Complex Orders"},
        {"name": "Brace for Impact"},
    ]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["mobilize_ready"] is True
    assert hints["complex_orders_ready"] is True
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "feature_action": "complex_orders",
            "actor_id": "player-1",
            "target_orders": [
                {"order_name": "Brace for Impact", "target_id": "ally-1"},
                {"order_name": "Mobilize", "target_id": "ally-2"},
            ],
        },
    )
    assert type(action).__name__ == "ComplexOrdersAction"


def test_engine_facade_simulates_cheerleader_prompt_on_orders():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Commander", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Tank1", [_move("Tackle")]), controller_id="player", position=(2, 1)),
            "ally-2": PokemonState(spec=_spec("Tank2", [_move("Tackle")]), controller_id="player", position=(3, 1)),
        },
        grid=GridState(width=8, height=8),
        rng=random.Random(14),
    )
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Cheerleader"},
        {"name": "Battle Conductor"},
        {"name": "Brace for Impact"},
    ]
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    facade.battle = battle
    prompts = facade._simulate_prompts(
        {
            "type": "trainer_feature",
            "feature_action": "battle_conductor",
            "actor_id": "player-1",
            "order_name": "Brace for Impact",
            "target_ids": ["ally-1", "ally-2"],
        }
    )
    prompt = next(prompt for prompt in prompts if prompt.get("feature") == "Cheerleader")
    assert prompt["ap_cost"] == 1
    assert len(prompt["allied_targets"]) == 2
    assert {option["value"] for option in prompt["options"]} == {"cheered", "excited", "motivated"}


def test_engine_facade_snapshot_exposes_strike_again_order():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", position=(1, 1))},
        pokemon={
            "player-1": PokemonState(spec=_spec("Commander", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally", [_move("Tackle")]), controller_id="player", position=(2, 1)),
        },
        grid=GridState(width=8, height=8),
        rng=random.Random(17),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Strike Again!"}, {"name": "Commander's Voice"}]
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert any(order["order"] == "strike again!" for order in hints["commanders_voice_orders"])
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "feature_action": "target_order",
            "actor_id": "player-1",
            "order_name": "Strike Again!",
            "target_id": "ally-1",
        },
    )
    assert type(action).__name__ == "TargetOrderAction"


def test_engine_facade_snapshot_exposes_legal_jumps_and_builds_jump_action():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", position=(1, 1))},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Jumper", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
            ),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(8),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.movement["l_jump"] = 2
    battle.pokemon["player-1"].spec.movement["h_jump"] = 1
    facade.battle = battle
    payload = facade.snapshot()
    assert [3, 1] in payload["legal_jumps"]
    assert [3, 1] in payload["legal_long_jumps"]
    assert [1, 2] in payload["legal_high_jumps"]
    action = facade._build_action(
        battle,
        {
            "type": "jump",
            "actor_id": "player-1",
            "x": 3,
            "y": 1,
            "jump_kind": "long",
        },
    )
    assert action.__class__.__name__ == "JumpAction"
    assert getattr(action, "jump_kind", None) == "long"


def test_engine_facade_snapshot_exposes_core_action_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", position=(1, 1))},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Lead", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "bench-1": PokemonState(
                spec=_spec("Bench", [_move("Tackle")]),
                controller_id="player",
                position=(4, 4),
                active=False,
            ),
            "foe-1": PokemonState(
                spec=_spec("Foe", [_move("Scratch")]),
                controller_id="foe",
                position=(3, 1),
                active=True,
            ),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(12),
    )
    battle.pokemon["player-1"].spec.items = [
        {"name": "Iron Sword", "kind": "weapon", "slot": "weapon"},
        {"name": "Potion", "kind": "item", "slot": "belt"},
    ]
    battle.advance_turn()
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["action_hints"]
    assert hints["can_take_breather"] is True
    assert hints["can_trade_standard_shift"] is True
    assert hints["can_trade_standard_swift"] is True
    assert any(option["target"] == "bench-1" for option in hints["switch_replacements"])
    assert any(option["item_index"] == 0 for option in hints["weapon_options"])


def test_engine_facade_builds_core_action_types():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Lead", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "bench-1": PokemonState(
                spec=_spec("Bench", [_move("Tackle")]),
                controller_id="player",
                position=(4, 4),
                active=False,
            ),
            "foe-1": PokemonState(
                spec=_spec("Foe", [_move("Scratch")]),
                controller_id="foe",
                position=(3, 1),
                active=True,
            ),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(13),
    )
    battle.pokemon["player-1"].spec.items = [
        {"name": "Iron Sword", "kind": "weapon", "slot": "weapon"},
    ]
    battle.advance_turn()
    delay_action = facade._build_action(battle, {"type": "delay", "actor_id": "player-1", "target_total": 10})
    assert delay_action.__class__.__name__ == "DelayAction"
    switch_action = facade._build_action(
        battle,
        {
            "type": "switch",
            "actor_id": "player-1",
            "replacement_id": "bench-1",
            "target_position": [2, 1],
        },
    )
    assert switch_action.__class__.__name__ == "SwitchAction"
    assert tuple(switch_action.target_position) == (2, 1)
    breather_action = facade._build_action(battle, {"type": "take_breather", "actor_id": "player-1"})
    assert breather_action.__class__.__name__ == "TakeBreatherAction"
    trade_action = facade._build_action(battle, {"type": "trade_standard", "actor_id": "player-1", "target_action": "swift"})
    assert trade_action.__class__.__name__ == "TradeStandardForAction"
    equip_action = facade._build_action(battle, {"type": "equip_weapon", "actor_id": "player-1", "item_index": 0})
    assert equip_action.__class__.__name__ == "EquipWeaponAction"
    battle.pokemon["player-1"].equip_weapon(0)
    unequip_action = facade._build_action(battle, {"type": "unequip_weapon", "actor_id": "player-1"})
    assert unequip_action.__class__.__name__ == "UnequipWeaponAction"


def test_engine_facade_snapshot_exposes_trainer_turn_switches():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", position=(1, 1))},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Lead", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "bench-1": PokemonState(
                spec=_spec("Bench", [_move("Tackle")]),
                controller_id="player",
                position=(4, 4),
                active=False,
            ),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(21),
    )
    battle.current_actor_id = "player"
    facade.battle = battle
    payload = facade.snapshot()
    trainer_turn = payload["trainer_turn"]
    assert trainer_turn["id"] == "player"
    assert trainer_turn["throw_origin"] == [1, 1]
    assert trainer_turn["throw_range"] >= 4
    assert any(
        option["outgoing_id"] == "player-1" and option["replacement_id"] == "bench-1"
        for option in trainer_turn["switch_options"]
    )


def test_engine_facade_builds_trainer_switch_action_type():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Lead", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "bench-1": PokemonState(
                spec=_spec("Bench", [_move("Tackle")]),
                controller_id="player",
                position=(4, 4),
                active=False,
            ),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(22),
    )
    action = facade._build_action(
        battle,
        {
            "type": "trainer_switch",
            "actor_id": "player",
            "outgoing_id": "player-1",
            "replacement_id": "bench-1",
            "target_position": [2, 1],
        },
    )
    assert action.__class__.__name__ == "TrainerSwitchAction"
    assert tuple(action.target_position) == (2, 1)


def test_engine_facade_trainer_feature_payload_preserves_action_specific_kwargs():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Trainer", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
                active=True,
            ),
            "bench-1": PokemonState(
                spec=_spec("Bench", [_move("Tackle")]),
                controller_id="player",
                position=(4, 4),
                active=False,
            ),
            "ally-1": PokemonState(
                spec=_spec("Ally", [_move("Tackle")]),
                controller_id="player",
                position=(2, 1),
                active=True,
            ),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(23),
    )

    quick_switch = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "quick_switch",
            "actor_id": "player-1",
            "replacement_id": "bench-1",
        },
    )
    assert quick_switch.__class__.__name__ == "QuickSwitchAction"
    assert quick_switch.replacement_id == "bench-1"

    press = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "press",
            "actor_id": "player-1",
            "target_id": "ally-1",
            "stats": ["atk", "spd"],
        },
    )
    assert press.__class__.__name__ == "PressAction"
    assert press.stats == ["atk", "spd"]

    brutal_training = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "brutal_training",
            "actor_id": "player-1",
            "target_id": "ally-1",
            "injuries_to_add": 2,
        },
    )
    assert brutal_training.__class__.__name__ == "BrutalTrainingAction"
    assert brutal_training.injuries_to_add == 2

    ace_trainer = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "ace_trainer",
            "actor_id": "player-1",
            "target_id": "ally-1",
            "stats": ["atk", "spd"],
        },
    )
    assert ace_trainer.__class__.__name__ == "AceTrainerAction"
    assert ace_trainer.stats == ["atk", "spd"]

    agility_training = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "agility_training",
            "actor_id": "player-1",
            "target_id": "ally-1",
        },
    )
    assert agility_training.__class__.__name__ == "AgilityTrainingAction"

    focused_training = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "focused_training",
            "actor_id": "player-1",
            "target_id": "ally-1",
        },
    )
    assert focused_training.__class__.__name__ == "FocusedTrainingAction"

    inspired_training = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "inspired_training",
            "actor_id": "player-1",
            "target_id": "ally-1",
        },
    )
    assert inspired_training.__class__.__name__ == "InspiredTrainingAction"

    quick_healing = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "quick_healing",
            "actor_id": "player-1",
            "target_id": "ally-1",
            "injuries_to_remove": 3,
        },
    )
    assert quick_healing.__class__.__name__ == "QuickHealingAction"
    assert quick_healing.injuries_to_remove == 3

    go_fight_win = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "go_fight_win",
            "actor_id": "player-1",
            "cheer": "show_your_best",
            "stat": "spdef",
        },
    )
    assert go_fight_win.__class__.__name__ == "GoFightWinAction"
    assert go_fight_win.cheer == "show_your_best"
    assert go_fight_win.stat == "spdef"


def test_engine_facade_snapshot_exposes_telepath_hint_state():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Telepath", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(9),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Telepath"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["telepath_ap_ready"] is True
    assert hints["telepath_active"] is False


def test_engine_facade_snapshot_exposes_ace_trainer_training_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(
                spec=_spec("Coach", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
            ),
            "ally-1": PokemonState(
                spec=_spec("Ally", [_move("Tackle")]),
                controller_id="player",
                position=(1, 2),
            ),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(13),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Ace Trainer"},
        {"name": "Champ in the Making"},
        {"name": "Elite Trainer", "choice": "Agility Training"},
        {"name": "Focused Training"},
        {"name": "Inspired Training"},
    ]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["ace_trainer_ready"] is True
    assert hints["ace_trainer_stat_count"] == 2
    assert any(option["value"] == "atk" for option in hints["ace_trainer_stat_options"])
    assert hints["agility_training_ready"] is True
    assert hints["focused_training_ready"] is True
    assert hints["inspired_training_ready"] is True


def test_engine_facade_snapshot_exposes_duelist_hint_state():
    facade = EngineFacade()
    burst = MoveSpec(
        name="Burst Test",
        type="Normal",
        category="Special",
        db=6,
        ac=2,
        range_kind="Burst",
        range_value=1,
        target_kind="Self",
        target_range=0,
        area_kind="Burst",
        area_value=1,
        freq="EOT",
    )
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Coach", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally", [burst]), controller_id="player", position=(1, 2)),
            "foe-1": PokemonState(spec=_spec("Foe", [_move("Tackle")]), controller_id="foe", position=(2, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(27),
    )
    battle.pokemon["player-1"].spec.tags = ["trainer"]
    battle.pokemon["player-1"].spec.trainer_features = [
        {"name": "Duelist"},
        {"name": "Effective Methods"},
        {"name": "Expend Momentum"},
        {"name": "Duelist's Manual"},
    ]
    ally = battle.pokemon["ally-1"]
    ally.add_temporary_effect("focused_training", source="Focused Training")
    ally.spec.tutor_points = 2
    battle._set_duelist_momentum(ally, 2)
    battle.frequency_usage.setdefault("ally-1", {})["Burst Test"] = 1
    facade.battle = battle

    payload = facade.snapshot()

    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["duelist_ready"] is True
    assert hints["effective_methods_ready"] is True
    assert hints["expend_momentum_ready"] is True
    assert hints["duelists_manual_ready"] is True
    assert hints["duelist_targets"][0]["target"] == "foe-1"
    assert hints["effective_methods_targets"][0]["target"] == "ally-1"
    assert any(option["move"] == "Burst Test" for option in hints["expend_momentum_targets"][0]["eot_moves"])
    assert hints["duelists_manual_targets"][0]["target"] == "ally-1"


def test_engine_facade_snapshot_exposes_ambient_aura_hints():
    facade = EngineFacade()
    aura_move = MoveSpec(
        name="Aura Burst",
        type="Fighting",
        category="Special",
        db=6,
        ac=2,
        range_kind="Ranged",
        range_value=6,
        target_kind="Ranged",
        target_range=6,
        freq="At-Will",
        keywords=["Aura"],
    )
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("AuraTrainer", [aura_move]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally", [_move("Tackle")]), controller_id="player", position=(1, 2)),
        },
        grid=GridState(width=5, height=5),
        rng=random.Random(9),
    )
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Ambient Aura"}]
    battle.pokemon["player-1"].spec.capabilities = ["Aura Pulse"]
    battle.pokemon["player-1"].add_temporary_effect("ambient_aura_blessing", move="Aura Burst")
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["ambient_aura_ready"] is True
    assert hints["ambient_aura_blessing_move"] == "Aura Burst"
    assert any(opt["target"] == "ally-1" for opt in hints["ambient_aura_barrier_targets"])


def test_engine_facade_snapshot_exposes_suggestion_and_jump_hint_state():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Telepath", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(2, 1)),
        },
        grid=GridState(width=6, height=6, blockers={(2, 1)}),
        rng=random.Random(10),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Telepath"}, {"name": "Suggestion"}, {"name": "Thought Detection"}, {"name": "Acrobat"}]
    battle.pokemon["player-1"].spec.movement["l_jump"] = 1
    battle.pokemon["player-1"].spec.movement["h_jump"] = 1
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["suggestion_ap_ready"] is True
    assert any(opt["target"] == "foe-1" for opt in hints["suggestion_targets"])
    assert [1, 3] in payload["legal_high_jumps"]


def test_engine_facade_snapshot_exposes_visible_psychic_residue_for_psionic_sight():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Seer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(2, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(11),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Psionic Sight"}]
    battle.pokemon["foe-1"].add_temporary_effect("psychic_residue", source="Suggestion")
    facade.battle = battle
    payload = facade.snapshot()
    residue = payload["visible_psychic_residue"]
    assert residue[0]["target"] == "foe-1"
    assert residue[0]["sources"] == ["Suggestion"]


def test_engine_facade_snapshot_exposes_visible_psychic_residue_for_witch_hunter():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Hunter", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(2, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(12),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Witch Hunter"}]
    battle.pokemon["foe-1"].add_temporary_effect("psychic_residue", source="Suggestion")
    facade.battle = battle
    payload = facade.snapshot()
    assert payload["visible_psychic_residue"][0]["target"] == "foe-1"


def test_engine_facade_snapshot_links_matching_psionic_signatures():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Seer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally", [_move("Tackle")]), controller_id="player", position=(1, 2)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(2, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(13),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Psionic Sight"}]
    battle.pokemon["foe-1"].add_temporary_effect("psychic_residue", source="Suggestion", source_id="seer-source")
    battle.pokemon["ally-1"].add_temporary_effect("psychic_residue", source="Suggestion", source_id="seer-source")
    facade.battle = battle
    payload = facade.snapshot()
    target_entry = next(entry for entry in payload["visible_psychic_residue"] if entry["target"] == "foe-1")
    assert target_entry["linked_targets"] == ["ally-1"]
    assert target_entry["signatures"][0]["source_id"] == "seer-source"


def test_engine_facade_snapshot_exposes_natural_fighter_and_wilderness_guide_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Guide", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(1, 3)),
        },
        grid=GridState(width=6, height=6),
        terrain={"name": "Forest"},
        rng=random.Random(14),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Natural Fighter"}, {"name": "Wilderness Guide"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["terrain_label"] == "Forest"
    assert hints["natural_fighter_move"] == "Grass Whistle"
    assert hints["wilderness_guide_ready"] is True


def test_engine_facade_snapshot_exposes_psionic_analysis_and_adaptive_geography_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Seer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Target", [_move("Tackle")]), controller_id="foe", position=(2, 1)),
        },
        grid=GridState(width=6, height=6),
        terrain={"name": "Wetlands"},
        rng=random.Random(12),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Psionic Analysis"}, {"name": "Adaptive Geography"}]
    battle.pokemon["player-1"].add_temporary_effect("terrain_alias", feature="Adaptive Geography", terrain="forest")
    battle.pokemon["foe-1"].add_temporary_effect("psychic_residue", source="Suggestion")
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["psionic_analysis_ready"] is True
    assert hints["psionic_analysis_uses_left"] == 1
    assert hints["adaptive_geography_aliases"] == ["Forest"]


def test_engine_facade_snapshot_exposes_psionic_sponge_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", skills={"focus": 4})},
        pokemon={
            "player-1": PokemonState(spec=_spec("PsychicMon", [_move("Confusion", type="Psychic", category="Special")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally", [_move("Psybeam", type="Psychic", category="Special"), _move("Tackle")]), controller_id="player", position=(1, 3)),
        },
        grid=GridState(width=7, height=7),
        rng=random.Random(3),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.types = ["Psychic"]
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Psionic Sponge"}]
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["psionic_sponge_ready"] is True
    assert hints["psionic_sponge_uses_left"] == 1
    assert hints["psionic_sponge_range"] == 4
    assert hints["psionic_sponge_sources"][0]["target"] == "ally-1"
    assert hints["psionic_sponge_sources"][0]["moves"][0]["move_name"] == "Psybeam"


def test_engine_facade_snapshot_exposes_trapper_mindbreak_and_force_of_will_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Barrier", type="Psychic", category="Status"), _move("Calm Mind", type="Psychic", category="Status")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally", [_move("Psybeam", type="Psychic", category="Special")]), controller_id="player", position=(1, 2)),
        },
        grid=GridState(width=9, height=9),
        terrain={"name": "Forest"},
        rng=random.Random(3),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Trapper"}, {"name": "Mindbreak"}, {"name": "Force of Will"}]
    battle.pokemon["ally-1"].spec.types = ["Psychic"]
    battle.pokemon["player-1"].add_temporary_effect("force_of_will_ready", trigger_move="Barrier", expires_round=0)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["trapper_ready"] is True
    assert hints["mindbreak_ap_ready"] is True
    assert hints["mindbreak_bound_targets"] == []
    assert hints["mindbreak_targets"][0]["target"] == "ally-1"
    assert hints["force_of_will_ready"] is True
    assert hints["force_of_will_trigger_move"] == "Barrier"
    assert hints["force_of_will_moves"][0]["move_name"] == "Calm Mind"
    assert payload["legal_trapper_tiles"]
    assert payload["legal_trapper_anchors"]


def test_engine_facade_snapshot_exposes_psionic_overload_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=2)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Barrier", type="Psychic", category="Status")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=9, height=9),
        terrain={"name": "Forest"},
        rng=random.Random(4),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Psionic Overload"}]
    battle.pokemon["player-1"].add_temporary_effect("psionic_overload_ready", move="Barrier", expires_round=0)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["psionic_overload_ready"] is True
    assert hints["psionic_overload_move"] == "Barrier"
    assert hints["psionic_overload_barrier_tiles"]


def test_engine_facade_snapshot_serializes_barrier_tile_metadata():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Barrier", type="Psychic", category="Status")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=8, height=8),
        rng=random.Random(5),
    )
    battle._place_barrier_segment((2, 1), source_id="player-1", source_name="Trainer")
    facade.battle = battle
    payload = facade.snapshot()
    barrier_tile = next(entry for entry in payload["grid"]["tiles"] if entry[0] == 2 and entry[1] == 1)
    assert barrier_tile[5]


def test_engine_facade_builds_frozen_domain_action():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=8, height=8),
        rng=random.Random(6),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Frozen Domain"}]
    facade.battle = battle
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "frozen_domain",
            "actor_id": "player-1",
            "target_positions": [[2, 2], [3, 2], [4, 2], [2, 3], [3, 3], [4, 3]],
        },
    )
    assert action.describe_action() == "Frozen Domain"


def test_engine_facade_snapshot_exposes_frozen_domain_hints_and_tiles():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3, skills={"survival": 3})},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=8, height=8),
        terrain={"name": "Tundra"},
        rng=random.Random(7),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Frozen Domain"}]
    battle._place_frozen_domain((2, 2), source_id="player-1", trainer_id="player", source_name="Trainer", dc=10)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["frozen_domain_ready"] is True
    assert hints["frozen_domain_ap_ready"] is True
    assert [2, 2] in payload["legal_frozen_domain_tiles"]
    frozen_tile = next(tile for tile in payload["grid"]["tiles"] if tile[0] == 2 and tile[1] == 2)
    assert frozen_tile[6][0]["dc"] == 10


def test_engine_facade_snapshot_includes_winter_is_coming_ability_grant():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("WinterAce", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(17),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Winter is Coming"}]
    battle._sync_static_trainer_feature_abilities_to_pokemon()
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    assert "Frostbite" in entry["abilities"]


def test_engine_facade_snapshot_includes_glacial_defense_chosen_ability():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
        pokemon={
            "player-1": PokemonState(spec=_spec("WinterAce", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(21),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Glacial Defense", "choice": "Winter's Kiss"}]
    battle._sync_static_trainer_feature_abilities_to_pokemon()
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    assert "Winter's Kiss" in entry["abilities"]


def test_engine_facade_builds_arctic_zeal_action():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Foe", [_move("Tackle")]), controller_id="foe", position=(2, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(31),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Arctic Zeal"}]
    battle.pokemon["player-1"].add_temporary_effect("arctic_zeal_blessing", charges=2, expires_round=1)
    facade.battle = battle
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "arctic_zeal",
            "actor_id": "player-1",
            "mode": "slow",
            "target_id": "foe-1",
        },
    )
    assert action.describe_action() == "Arctic Zeal slow"


def test_engine_facade_snapshot_exposes_arctic_zeal_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "foe-1": PokemonState(spec=_spec("Foe", [_move("Tackle")]), controller_id="foe", position=(2, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(32),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Arctic Zeal"}]
    battle.pokemon["player-1"].add_temporary_effect("arctic_zeal_blessing", charges=3, expires_round=1)
    battle.pokemon["player-1"].add_temporary_effect("arctic_zeal_hail", expires_round=1)
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["arctic_zeal_ready"] is True
    assert hints["arctic_zeal_charges"] == 3
    assert hints["arctic_zeal_targets"][0]["target"] == "foe-1"
    assert hints["arctic_zeal_hail_active"] is True


def test_engine_facade_builds_polar_vortex_action():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(31),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Polar Vortex"}]
    facade.battle = battle
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "polar_vortex",
            "actor_id": "player-1",
            "target_id": "player-1",
        },
    )
    assert action.describe_action() == "Polar Vortex player-1"


def test_engine_facade_snapshot_exposes_polar_vortex_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(32),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Polar Vortex"}]
    battle.pokemon["player-1"].add_temporary_effect("polar_vortex_hail", source="Polar Vortex")
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["polar_vortex_active"] is True
    assert hints["polar_vortex_ready"] is False
    assert hints["polar_vortex_release_ready"] is True
    assert hints["polar_vortex_bound_targets"][0]["target"] == "player-1"
    assert hints["polar_vortex_targets"] == []


def test_engine_facade_snapshot_exposes_bind_release_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=5)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally", [_move("Tackle")]), controller_id="player", position=(2, 1)),
            "foe-1": PokemonState(spec=_spec("Foe", [_move("Tackle")]), controller_id="foe", position=(3, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(33),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Telepath"}, {"name": "Suggestion"}, {"name": "Mindbreak"}, {"name": "Polar Vortex"}]
    battle.pokemon["player-1"].add_temporary_effect("feature_bound", feature="Suggestion", target_id="foe-1", suggestion="Withdraw.")
    battle.pokemon["foe-1"].add_temporary_effect("suggestion_bound", source_id="player-1", trainer_id="player", suggestion="Withdraw.")
    battle.pokemon["ally-1"].add_temporary_effect("mindbreak_bound", source_id="player-1", trainer_id="player")
    battle.pokemon["ally-1"].add_temporary_effect("polar_vortex_hail", source_id="player-1", trainer_id="player")
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["suggestion_release_ready"] is True
    assert hints["suggestion_bound_target"] == "foe-1"
    assert hints["suggestion_bound_target_name"] == "Foe"
    assert hints["mindbreak_release_ready"] is True
    assert hints["mindbreak_bound_targets"][0]["target"] == "ally-1"
    assert hints["polar_vortex_release_ready"] is True


def test_engine_facade_builds_focused_command_action():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally1", [_move("Tackle")]), controller_id="player", position=(2, 1)),
            "ally-2": PokemonState(spec=_spec("Ally2", [_move("Tackle")]), controller_id="player", position=(3, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(35),
    )
    battle.current_actor_id = "player"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Focused Command"}]
    facade.battle = battle
    action = facade._build_action(
        battle,
        {
            "type": "trainer_feature",
            "action_key": "focused_command",
            "actor_id": "player-1",
            "primary_target_id": "ally-1",
            "secondary_target_id": "ally-2",
            "lift_option": "both",
        },
    )
    assert action.describe_action() == "Focused Command ally-1 + ally-2"


def test_engine_facade_snapshot_exposes_focused_command_hints():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=3)},
        pokemon={
            "player-1": PokemonState(spec=_spec("Trainer", [_move("Tackle")]), controller_id="player", position=(1, 1)),
            "ally-1": PokemonState(spec=_spec("Ally1", [_move("Tackle")]), controller_id="player", position=(2, 1)),
            "ally-2": PokemonState(spec=_spec("Ally2", [_move("Tackle")]), controller_id="player", position=(3, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(36),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Focused Command"}]
    battle.pokemon["ally-1"].add_temporary_effect(
        "focused_command_pair",
        source="Focused Command",
        partner_id="ally-2",
        round=1,
        lift_frequency=False,
        lift_damage=True,
    )
    battle.round = 1
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["focused_command_ready"] is True
    assert len(hints["focused_command_targets"]) == 2
    assert hints["focused_command_pairs"][0]["partner"] == "ally-2"
    assert hints["focused_command_pairs"][0]["lift_damage"] is True


def test_engine_facade_snapshot_exposes_effective_weather_source():
    facade = EngineFacade()
    battle = BattleState(
        trainers={"player": TrainerState(identifier="player", name="Player", team="players", ap=5)},
        pokemon={
            "player-1": PokemonState(spec=_spec("WinterMon", [_move("Tackle")]), controller_id="player", position=(1, 1)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(34),
    )
    battle.current_actor_id = "player-1"
    battle.pokemon["player-1"].spec.trainer_features = [{"name": "Arctic Zeal"}, {"name": "Polar Vortex"}]
    battle.pokemon["player-1"].add_temporary_effect("arctic_zeal_hail", source="Arctic Zeal", source_move="Ice Beam")
    facade.battle = battle
    payload = facade.snapshot()
    entry = next(item for item in payload["combatants"] if item["id"] == "player-1")
    hints = entry["trainer_action_hints"]
    assert hints["effective_weather"] == "Hail"
    assert hints["effective_weather_source"] == "Arctic Zeal (Ice Beam)"
    assert hints["arctic_zeal_source_move"] == "Ice Beam"


def test_engine_facade_snapshot_exposes_chef_hints_and_item_taste():
    facade = EngineFacade()
    battle = BattleState(
        trainers={
            "player": TrainerState(identifier="player", name="Player", team="players", ap=3),
            "foe": TrainerState(identifier="foe", name="Foe", team="foes"),
        },
        pokemon={
            "chef-1": PokemonState(
                spec=_spec("Chef", [_move("Tackle")]),
                controller_id="player",
                position=(1, 1),
            ),
            "ally-1": PokemonState(
                spec=_spec("Ally", [_move("Tackle")]),
                controller_id="player",
                position=(2, 1),
            ),
            "foe-1": PokemonState(spec=_spec("Foe", [_move("Tackle")]), controller_id="foe", position=(5, 5)),
        },
        grid=GridState(width=6, height=6),
        rng=random.Random(37),
    )
    battle.current_actor_id = "chef-1"
    battle.pokemon["chef-1"].spec.trainer_features = [
        {"name": "Hits the Spot"},
        {"name": "Complex Aftertaste"},
        {"name": "Culinary Appreciation"},
    ]
    battle.pokemon["chef-1"].add_temporary_effect("hits_the_spot_ready", target_id="ally-1", target_name="Ally", round=0)
    battle.pokemon["chef-1"].add_temporary_effect(
        "complex_aftertaste_ready",
        target_id="ally-1",
        target_name="Ally",
        taste="sweet",
        source_item="Chef Special",
        instance_id="meal#1",
        round=0,
    )
    battle.pokemon["ally-1"].spec.items = [{"name": "Sweet Confection", "taste": "sweet"}]
    battle.pokemon["ally-1"].spec.tutor_points = 2
    facade.battle = battle

    payload = facade.snapshot()
    chef = next(item for item in payload["combatants"] if item["id"] == "chef-1")
    ally = next(item for item in payload["combatants"] if item["id"] == "ally-1")
    hints = chef["trainer_action_hints"]

    assert hints["culinary_appreciation_ready"] is True
    assert hints["culinary_appreciation_targets"][0]["target"] == "ally-1"
    assert hints["hits_the_spot_ready"] is True
    assert hints["hits_the_spot_targets"][0]["target"] == "ally-1"
    assert hints["complex_aftertaste_ready"] is True
    assert hints["complex_aftertaste_targets"][0]["taste"] == "sweet"
    assert ally["items"][0]["taste"] == "sweet"
