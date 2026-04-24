import io
import random
import unittest

from rich.console import Console

from auto_ptu.battle_state import InteractiveBattleState
from auto_ptu.data_loader import default_campaign
from auto_ptu.data_models import GridSpec, MatchPlan, MatchupSpec, MoveSpec, PokemonSpec, TrainerSideSpec
from auto_ptu.engine import MatchEngine
from auto_ptu.gameplay import TextBattleSession
from auto_ptu.matchmaker import AutoMatchPlanner
from auto_ptu.rules import (
    BattleState as RulesBattleState,
    GridState as RulesGridState,
    PokemonState as RulesPokemonState,
    SwitchAction,
    TrainerState as RulesTrainerState,
    TurnPhase as RulesTurnPhase,
    UseMoveAction,
    targeting,
)


def _first_move_selector(moves, *_args):
    return moves[0]


def _test_move_spec(name: str = "Tackle") -> MoveSpec:
    return MoveSpec(name=name, type="Normal", category="Physical", range_kind="Melee", range_value=1)


def _test_pokemon_spec(name: str) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=5,
        types=["Normal"],
        hp_stat=5,
        atk=5,
        defense=5,
        spatk=5,
        spdef=5,
        spd=5,
        moves=[_test_move_spec()],
        movement={"overland": 3},
    )


def _dummy_plan() -> MatchPlan:
    grid = GridSpec(width=4, height=4)
    you = _test_pokemon_spec("PlayerMon")
    foe = _test_pokemon_spec("FoeMon")
    matchup = MatchupSpec(you=you, foe=foe)
    return MatchPlan(matchups=[matchup], weather="Clear", grid=grid)


class GameplayTests(unittest.TestCase):
    def test_text_battle_session_runs(self) -> None:
        campaign = default_campaign()
        planner = AutoMatchPlanner(campaign, seed=7)
        plan = planner.create_plan(team_size=1)
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        records = session.play(selector=_first_move_selector)
        self.assertTrue(records)
        self.assertTrue(records[0].turns)
        self.assertIn(records[0].winner, {"Player", "AI"})

    def test_text_session_detects_multi_trainer_players(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_player = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player")
        trainer_ai = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai")
        pokemon_player = RulesPokemonState(spec=_test_pokemon_spec("Pikachu"), controller_id="ash")
        pokemon_ai = RulesPokemonState(spec=_test_pokemon_spec("Eevee"), controller_id="gary")
        battle = RulesBattleState(
            trainers={"ash": trainer_player, "gary": trainer_ai},
            pokemon={"ash-1": pokemon_player, "gary-1": pokemon_ai},
            rng=random.Random(3),
        )
        self.assertEqual(session._controller_kind_for_actor(battle, "ash-1"), "player")
        self.assertEqual(session._controller_kind_for_actor(battle, "gary-1"), "ai")

    def test_board_snapshot_and_movement(self) -> None:
        campaign = default_campaign()
        planner = AutoMatchPlanner(campaign, seed=1)
        plan = planner.create_plan(team_size=1)
        engine = MatchEngine(plan)
        state = InteractiveBattleState(plan=plan, matchup=plan.matchups[0], engine=engine, seed=1)
        snapshot = state.snapshot()
        trainers = snapshot["trainers"]
        self.assertGreaterEqual(len(trainers), 2)
        self.assertTrue(any(entry["controller"] == "player" for entry in trainers))
        self.assertTrue(any(entry["controller"] != "player" for entry in trainers))
        turn_info = snapshot["turn"]
        self.assertEqual(turn_info["controller"], "player")
        self.assertIsNotNone(turn_info["token_id"])
        initial_board = snapshot["board"]
        self.assertIn("tokens", initial_board)
        player_token = next(token for token in initial_board["tokens"] if token["role"] == "player")
        state.move_token(player_token["id"], (player_token["x"], player_token["y"]))
        with self.assertRaises(ValueError):
            state.move_token(player_token["id"], (-1, 0))

    def test_target_overview_marks_alignment_and_range(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        grid = RulesGridState(width=10, height=8, blockers={(2, 2), (3, 2)})
        trainer_player = RulesTrainerState(identifier="lens", name="Lens", controller_kind="player", team="players")
        trainer_ally = RulesTrainerState(identifier="fern", name="Fern", controller_kind="player", team="players")
        trainer_enemy = RulesTrainerState(identifier="rogue", name="Rogue", controller_kind="ai", team="rogues")
        actor_state = RulesPokemonState(spec=_test_pokemon_spec("Luxio"), controller_id="lens", position=(1, 1))
        ally_state = RulesPokemonState(spec=_test_pokemon_spec("Ivysaur"), controller_id="fern", position=(1, 2))
        enemy_clear = RulesPokemonState(spec=_test_pokemon_spec("Pidgeotto"), controller_id="rogue", position=(4, 1))
        enemy_blocked = RulesPokemonState(spec=_test_pokemon_spec("Graveler"), controller_id="rogue", position=(4, 3))
        battle = RulesBattleState(
            trainers={"lens": trainer_player, "fern": trainer_ally, "rogue": trainer_enemy},
            pokemon={
                "lens-1": actor_state,
                "fern-1": ally_state,
                "rogue-1": enemy_clear,
                "rogue-2": enemy_blocked,
            },
            grid=grid,
            rng=random.Random(4),
        )
        move = MoveSpec(name="Thunderbolt", type="Electric", category="Special", range_kind="Ranged", range_value=6)
        overview = session._build_target_overview(
            battle=battle,
            actor_id="lens-1",
            move=move,
            candidate_ids=["fern-1", "rogue-1", "rogue-2"],
            ally_ids={"fern-1"},
        )
        self.assertEqual(overview["rogue-1"]["status_key"], "in_range")
        self.assertTrue(overview["rogue-1"]["reachable"])
        self.assertEqual(overview["rogue-2"]["status_key"], "blocked")
        self.assertFalse(overview["rogue-2"]["reachable"])
        self.assertEqual(overview["fern-1"]["status_key"], "in_range")
        self.assertEqual(overview["fern-1"]["note"], "[yellow]Friendly fire[/yellow]")

    def test_ai_shift_followed_by_same_turn_attack(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_ai = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai", team="foe")
        trainer_foe = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player", team="player")
        ai_spec = _test_pokemon_spec("Machop")
        ai_spec.moves = [
            MoveSpec(
                name="Tackle",
                type="Normal",
                category="Physical",
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
            )
        ]
        foe_spec = _test_pokemon_spec("Eevee")
        battle = RulesBattleState(
            trainers={"gary": trainer_ai, "ash": trainer_foe},
            pokemon={
                "gary-1": RulesPokemonState(spec=ai_spec, controller_id="gary", position=(0, 0)),
                "ash-1": RulesPokemonState(spec=foe_spec, controller_id="ash", position=(1, 2)),
            },
            grid=RulesGridState(width=5, height=5),
            rng=random.Random(5),
        )
        battle.start_round()
        entry = None
        while battle.current_actor_id != "gary-1":
            entry = battle.advance_turn()
            self.assertIsNotNone(entry)
        self.assertEqual(battle.current_actor_id, "gary-1")

        from auto_ptu.gameplay import BattleRecord

        record = BattleRecord(matchup=plan.matchups[0])
        session._ai_turn(battle, record, "gary-1")

        actor_events = [evt for evt in battle.log if evt.get("actor") == "gary-1"]
        self.assertTrue(any(evt.get("type") == "shift" for evt in actor_events))
        self.assertTrue(any(evt.get("type") == "move" and evt.get("move") == "Tackle" for evt in actor_events))

    def test_ai_ranged_attacker_prefers_disengage_then_attack(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_ai = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai", team="foe")
        trainer_foe = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player", team="player")
        ai_spec = _test_pokemon_spec("Pikachu")
        ai_spec.moves = [
            MoveSpec(
                name="Thunder Shock",
                type="Electric",
                category="Special",
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
            )
        ]
        foe_spec = _test_pokemon_spec("Machop")
        battle = RulesBattleState(
            trainers={"gary": trainer_ai, "ash": trainer_foe},
            pokemon={
                "gary-1": RulesPokemonState(spec=ai_spec, controller_id="gary", position=(1, 1), active=True),
                "ash-1": RulesPokemonState(spec=foe_spec, controller_id="ash", position=(1, 2), active=True),
            },
            grid=RulesGridState(width=5, height=5),
            rng=random.Random(15),
        )
        battle.start_round()
        while battle.current_actor_id != "gary-1":
            entry = battle.advance_turn()
            self.assertIsNotNone(entry)

        from auto_ptu.gameplay import BattleRecord

        record = BattleRecord(matchup=plan.matchups[0])
        session._ai_turn(battle, record, "gary-1")

        actor_events = [evt for evt in battle.log if evt.get("actor") == "gary-1"]
        disengage_index = next(
            idx for idx, evt in enumerate(actor_events)
            if evt.get("type") == "maneuver" and evt.get("effect") == "disengage"
        )
        move_index = next(
            idx for idx, evt in enumerate(actor_events)
            if evt.get("type") == "move" and evt.get("move") == "Thunder Shock"
        )
        self.assertLess(disengage_index, move_index)

    def test_text_session_auto_selects_ai_starter(self) -> None:
        grid = GridSpec(width=4, height=4)
        weak = _test_pokemon_spec("Magikarp")
        weak.moves = [MoveSpec(name="Splash", type="Normal", category="Status", range_kind="Self", range_value=0)]
        strong = _test_pokemon_spec("Pikachu")
        strong.moves = [
            MoveSpec(
                name="Thunder Shock",
                type="Electric",
                category="Special",
                db=4,
                range_kind="Ranged",
                range_value=6,
                target_kind="Ranged",
                target_range=6,
            )
        ]
        foe = _test_pokemon_spec("Squirtle")
        matchup = MatchupSpec(
            you=weak,
            foe=foe,
            sides=[
                TrainerSideSpec(
                    identifier="player",
                    name="Player",
                    controller="ai",
                    team="player",
                    pokemon=[weak, strong],
                ),
                TrainerSideSpec(
                    identifier="foe",
                    name="Foe",
                    controller="ai",
                    team="foe",
                    pokemon=[foe],
                ),
            ]
        )
        plan = MatchPlan(matchups=[matchup], weather="Clear", grid=grid, active_slots=1)
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)

        battle = session._build_battle_state(0, matchup)

        active_species = {
            mon.spec.species
            for mon in battle.pokemon.values()
            if mon.controller_id == "player" and mon.active
        }
        self.assertEqual(active_species, {"Pikachu"})

    def test_ai_uses_light_screen_on_self_not_enemy(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_ai = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai", team="foe")
        trainer_foe = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player", team="player")
        ai_spec = _test_pokemon_spec("MrMime")
        ai_spec.moves = [
            MoveSpec(
                name="Light Screen",
                type="Psychic",
                category="Status",
                range_kind="Blessing",
                range_value=0,
            )
        ]
        foe_spec = _test_pokemon_spec("Machop")
        battle = RulesBattleState(
            trainers={"gary": trainer_ai, "ash": trainer_foe},
            pokemon={
                "gary-1": RulesPokemonState(spec=ai_spec, controller_id="gary", position=(1, 1), active=True),
                "ash-1": RulesPokemonState(spec=foe_spec, controller_id="ash", position=(1, 2), active=True),
            },
            grid=RulesGridState(width=5, height=5),
            rng=random.Random(19),
        )
        battle.start_round()
        while battle.current_actor_id != "gary-1":
            entry = battle.advance_turn()
            self.assertIsNotNone(entry)

        from auto_ptu.gameplay import BattleRecord

        record = BattleRecord(matchup=plan.matchups[0])
        session._ai_turn(battle, record, "gary-1")

        actor_events = [
            evt for evt in battle.log
            if evt.get("actor") == "gary-1" and evt.get("type") == "move" and evt.get("move") == "Light Screen"
        ]
        self.assertTrue(actor_events)
        self.assertEqual(actor_events[-1].get("target"), "gary-1")
        self.assertTrue(battle.pokemon["gary-1"].has_status("Light Screen"))

    def test_ai_trainer_switch_chooses_throw_tile_within_range(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_ai = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai", team="foe", position=(0, 0), speed=1)
        trainer_foe = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player", team="player", speed=2)
        active = RulesPokemonState(spec=_test_pokemon_spec("Machop"), controller_id="gary", position=(5, 5), active=True)
        active.hp = 0
        bench = RulesPokemonState(spec=_test_pokemon_spec("Pikachu"), controller_id="gary", position=None, active=False)
        foe = RulesPokemonState(spec=_test_pokemon_spec("Eevee"), controller_id="ash", position=(2, 2), active=True)
        battle = RulesBattleState(
            trainers={"gary": trainer_ai, "ash": trainer_foe},
            pokemon={"gary-1": active, "gary-2": bench, "ash-1": foe},
            grid=RulesGridState(width=8, height=8),
            rng=random.Random(23),
        )
        battle.start_round()
        entry = battle.advance_turn()
        while entry is not None and entry.actor_id != "gary":
            battle.end_turn()
            entry = battle.advance_turn()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.actor_id, "gary")

        from auto_ptu.gameplay import BattleRecord

        record = BattleRecord(matchup=plan.matchups[0])
        session._ai_trainer_turn(battle, record, "gary")

        self.assertTrue(battle.pokemon["gary-2"].active)
        self.assertNotEqual(battle.pokemon["gary-2"].position, (5, 5))
        self.assertLessEqual(
            targeting.footprint_distance((0, 0), "Medium", battle.pokemon["gary-2"].position, "Medium", battle.grid),
            4,
        )

    def test_ai_uses_healing_item_when_low_hp(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_ai = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai", team="foe")
        trainer_foe = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player", team="player")
        ai_spec = _test_pokemon_spec("Pikachu")
        ai_spec.items = [{"name": "Potion"}]
        ai_spec.moves = [MoveSpec(name="Growl", type="Normal", category="Status", range_kind="Ranged", range_value=6)]
        foe_spec = _test_pokemon_spec("Eevee")
        ai_state = RulesPokemonState(spec=ai_spec, controller_id="gary", position=(0, 0))
        ai_state.hp = max(1, ai_state.max_hp() // 3)
        battle = RulesBattleState(
            trainers={"gary": trainer_ai, "ash": trainer_foe},
            pokemon={
                "gary-1": ai_state,
                "ash-1": RulesPokemonState(spec=foe_spec, controller_id="ash", position=(3, 0)),
            },
            grid=RulesGridState(width=5, height=5),
            rng=random.Random(6),
        )
        battle.start_round()
        entry = None
        while battle.current_actor_id != "gary-1":
            entry = battle.advance_turn()
            self.assertIsNotNone(entry)
        self.assertEqual(battle.current_actor_id, "gary-1")

        from auto_ptu.gameplay import BattleRecord

        before_hp = ai_state.hp
        record = BattleRecord(matchup=plan.matchups[0])
        session._ai_turn(battle, record, "gary-1")

        self.assertGreater(ai_state.hp or 0, before_hp or 0)
        self.assertTrue(
            any(
                evt.get("type") == "item"
                and evt.get("actor") == "gary-1"
                and evt.get("item") == "Potion"
                for evt in battle.log
            )
        )

    def test_standard_switch_declares_in_command_and_resolves_in_action(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_player = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player", team="players")
        trainer_foe = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai", team="foes")
        active_state = RulesPokemonState(spec=_test_pokemon_spec("Pikachu"), controller_id="ash", position=(0, 0), active=True)
        bench_state = RulesPokemonState(spec=_test_pokemon_spec("Bulbasaur"), controller_id="ash", active=False)
        foe_state = RulesPokemonState(spec=_test_pokemon_spec("Eevee"), controller_id="gary", position=(1, 0), active=True)
        battle = RulesBattleState(
            trainers={"ash": trainer_player, "gary": trainer_foe},
            pokemon={"ash-1": active_state, "ash-2": bench_state, "gary-1": foe_state},
            grid=RulesGridState(width=4, height=4),
            rng=random.Random(12),
        )
        battle.start_round()
        while battle.current_actor_id != "ash-1":
            entry = battle.advance_turn()
            self.assertIsNotNone(entry)
        self.assertEqual(battle.phase, RulesTurnPhase.START)
        battle.advance_phase()
        self.assertEqual(battle.phase, RulesTurnPhase.COMMAND)

        session._resolve_selected_action(
            battle,
            SwitchAction(actor_id="ash-1", replacement_id="ash-2"),
        )

        event_types = [evt.get("type") for evt in battle.log]
        self.assertIn("action_declared", event_types)
        declared_index = event_types.index("action_declared")
        action_phase_index = next(
            idx for idx, evt in enumerate(battle.log)
            if evt.get("type") == "phase" and evt.get("phase") == "action"
        )
        switch_index = event_types.index("switch")
        self.assertLess(declared_index, action_phase_index)
        self.assertLess(action_phase_index, switch_index)
        self.assertEqual(battle.phase, RulesTurnPhase.ACTION)
        self.assertTrue(battle.pokemon["ash-2"].active)
        self.assertFalse(battle.pokemon["ash-1"].active)

    def test_standard_move_declares_in_command_and_resolves_in_action(self) -> None:
        plan = _dummy_plan()
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)
        session = TextBattleSession(plan, console=console)
        trainer_player = RulesTrainerState(identifier="ash", name="Ash", controller_kind="player", team="players")
        trainer_foe = RulesTrainerState(identifier="gary", name="Gary", controller_kind="ai", team="foes")
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
        )
        attacker_spec = _test_pokemon_spec("Pikachu")
        attacker_spec.moves = [move]
        attacker_state = RulesPokemonState(spec=attacker_spec, controller_id="ash", position=(0, 0), active=True)
        defender_state = RulesPokemonState(spec=_test_pokemon_spec("Eevee"), controller_id="gary", position=(0, 1), active=True)
        battle = RulesBattleState(
            trainers={"ash": trainer_player, "gary": trainer_foe},
            pokemon={"ash-1": attacker_state, "gary-1": defender_state},
            grid=RulesGridState(width=4, height=4),
            rng=random.Random(13),
        )
        battle.start_round()
        while battle.current_actor_id != "ash-1":
            entry = battle.advance_turn()
            self.assertIsNotNone(entry)
        battle.advance_phase()
        self.assertEqual(battle.phase, RulesTurnPhase.COMMAND)

        session._resolve_selected_action(
            battle,
            UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"),
        )

        declared_index = next(
            idx for idx, evt in enumerate(battle.log) if evt.get("type") == "action_declared"
        )
        action_phase_index = next(
            idx for idx, evt in enumerate(battle.log)
            if evt.get("type") == "phase" and evt.get("phase") == "action"
        )
        move_index = next(
            idx for idx, evt in enumerate(battle.log)
            if evt.get("type") == "move" and evt.get("actor") == "ash-1"
        )
        self.assertLess(declared_index, action_phase_index)
        self.assertLess(action_phase_index, move_index)
        self.assertEqual(battle.phase, RulesTurnPhase.ACTION)
