import random

from auto_ptu.ai import policy_adapter
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, UseMoveAction
from auto_ptu.rules import ai_hybrid


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


def _make_battle():
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
    return battle


def test_policy_adapter_override_can_select_custom_action():
    battle = _make_battle()
    captured = {}

    def adapter(context):
        captured["helpers"] = sorted(context.helper.keys())
        return policy_adapter.PolicyDecision(
            action=context.candidates[0],
            reason="custom_adapter",
            source="test_adapter",
            info={"adapter_debug": True},
        )

    policy_adapter.register_policy_adapter("test_custom", adapter)
    try:
        action, info = ai_hybrid.choose_action(battle, "a-1", policy_adapter_name="test_custom")
    finally:
        policy_adapter.unregister_policy_adapter("test_custom")
    assert isinstance(action, UseMoveAction)
    assert info["reason"] == "custom_adapter"
    assert info["source"] == "test_adapter"
    assert info["policy_adapter"] == "test_custom"
    assert "rank_candidates" in captured["helpers"]
    assert "fallback_choose_action" in captured["helpers"]


def test_policy_adapter_active_registry_switches_runtime_path():
    battle = _make_battle()
    original = policy_adapter.get_active_policy_adapter()

    def adapter(context):
        ranked = context.helper["rank_candidates"](
            context.battle,
            context.actor_id,
            ai_level=context.ai_level,
            profile_store=context.profile_store,
            candidates=context.candidates,
        )
        return policy_adapter.PolicyDecision(
            action=ranked[0][1],
            reason="ranked_adapter",
            source="test_ranked",
        )

    policy_adapter.register_policy_adapter("test_ranked", adapter)
    try:
        policy_adapter.set_active_policy_adapter("test_ranked")
        action, info = ai_hybrid.choose_action(battle, "a-1")
    finally:
        policy_adapter.set_active_policy_adapter(original)
        policy_adapter.unregister_policy_adapter("test_ranked")
    assert isinstance(action, UseMoveAction)
    assert info["reason"] == "ranked_adapter"
    assert info["policy_adapter"] == "test_ranked"


def test_default_hybrid_rules_adapter_remains_registered():
    battle = _make_battle()
    action, info = ai_hybrid.choose_action(battle, "a-1", policy_adapter_name="hybrid_rules")
    assert action is not None
    assert info["policy_adapter"] == "hybrid_rules"
