import random

from auto_ptu.api.engine_facade import EngineFacade
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, DirtyFightingFollowUpAction, FlightAction, PokemonState, PsychicResonanceFollowUpAction, QuickWitMoveAction, TrainerState, GridState, TurnPhase, UseMoveAction, WeaponFinesseFollowUpAction
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


def _spec(name: str, moves: list[MoveSpec], *, atk: int = 12, defense: int = 12) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=50,
        types=["Normal"],
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
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
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
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
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
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
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
        trainers={"player": TrainerState(identifier="player", name="Player", team="players")},
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
