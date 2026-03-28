import io
import random
import unittest

from rich.console import Console

from auto_ptu.battle_state import InteractiveBattleState
from auto_ptu.data_loader import default_campaign
from auto_ptu.data_models import GridSpec, MatchPlan, MatchupSpec, MoveSpec, PokemonSpec
from auto_ptu.engine import MatchEngine
from auto_ptu.gameplay import TextBattleSession
from auto_ptu.matchmaker import AutoMatchPlanner
from auto_ptu.rules import (
    BattleState as RulesBattleState,
    GridState as RulesGridState,
    PokemonState as RulesPokemonState,
    TrainerState as RulesTrainerState,
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
