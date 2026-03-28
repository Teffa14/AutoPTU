import random

from auto_ptu.ai import behavior_tree_policy, mcts_policy
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, ShiftAction, UseMoveAction


def _make_mon(name: str, *, hp: int = 20, atk: int = 10, defense: int = 10, spd: int = 10, moves=None):
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=hp,
        atk=atk,
        defense=defense,
        spatk=atk,
        spdef=defense,
        spd=spd,
        moves=moves or [],
    )


def test_behavior_tree_prefers_first_available_branch():
    shift = ShiftAction(actor_id="a-1", destination=(2, 3))
    context = behavior_tree_policy.BTContext(
        actor_id="a-1",
        ai_level="standard",
        item_action=shift,
        hybrid_action=UseMoveAction(actor_id="a-1", move_name="Tackle", target_id="b-1"),
        hybrid_info={"reason": "hybrid"},
    )
    action, info = behavior_tree_policy.choose_action(context)
    assert isinstance(action, ShiftAction)
    assert info["reason"] == "use_item_priority"
    assert info["policy"] == "py_trees"


def test_mcts_returns_action_for_strategic_ai():
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
    )
    actor = PokemonState(spec=_make_mon("Actor", moves=[tackle]), controller_id="a", position=(2, 2))
    foe = PokemonState(spec=_make_mon("Foe", moves=[tackle]), controller_id="b", position=(2, 3))
    battle = BattleState(
        trainers={},
        pokemon={"a-1": actor, "b-1": foe},
        grid=GridState(width=6, height=6),
        rng=random.Random(12),
    )
    battle.start_round()
    action, info = mcts_policy.choose_action(battle, "a-1", ai_level="strategic")
    assert isinstance(action, UseMoveAction)
    assert info["reason"] == "mcts_search"

