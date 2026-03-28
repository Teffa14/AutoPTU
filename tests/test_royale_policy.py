import random

from auto_ptu.ai import royale_policy
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState


def _spec(name: str) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=30,
        types=["Normal"],
        hp_stat=8,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=10,
        moves=[MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2, range_kind="Melee", target_kind="Melee")],
    )


def test_royale_policy_prefers_safe_shift_when_in_storm():
    grid = GridState(
        width=6,
        height=6,
        blockers=set(),
        tiles={(2, 2): {"type": "storm", "zone": "danger"}, (2, 3): {"type": "grassland"}, (3, 2): {"type": "grassland"}},
    )
    actor = PokemonState(spec=_spec("Actor"), controller_id="a", position=(2, 2), active=True)
    actor.spec.movement["overland"] = 3
    foe = PokemonState(spec=_spec("Foe"), controller_id="b", position=(5, 5), active=True)
    battle = BattleState(
        trainers={
            "a": TrainerState(identifier="a", name="A", team="alpha", controller_kind="ai"),
            "b": TrainerState(identifier="b", name="B", team="beta", controller_kind="ai"),
        },
        pokemon={"a-1": actor, "b-1": foe},
        grid=grid,
        rng=random.Random(1),
    )
    setattr(battle, "_battle_royale_state", {"enabled": True, "center": [3, 3]})
    action = royale_policy.choose_emergency_shift(battle, "a-1")
    assert action is not None
    assert action.destination != (2, 2)
    assert not royale_policy.is_danger_tile(battle, action.destination)
