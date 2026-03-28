from __future__ import annotations

import random
from typing import List

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.hooks import move_specials


class SequenceRNG(random.Random):
    def __init__(self, values: List[int]) -> None:
        super().__init__()
        self._values = list(values)

    def randint(self, a: int, b: int) -> int:
        if self._values:
            return self._values.pop(0)
        return b


def _pokemon_spec(name: str, move: MoveSpec) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=14,
        defense=10,
        spatk=14,
        spdef=10,
        spd=10,
        moves=[move],
        movement={"overland": 4},
    )


def _build_battle(move: MoveSpec) -> tuple[BattleState, str, str]:
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move),
        controller_id="a",
        position=(4, 4),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move),
        controller_id="b",
        position=(4, 5),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20, 20, 20, 20, 20])
    battle.round = 1
    return battle, "a-1", "b-1"


def _move_events_for(battle: BattleState, name: str) -> list[dict]:
    return [evt for evt in battle.log if evt.get("type") == "move" and evt.get("move") == name]


BATCH_MOVES = [
    "High Jump Kick",
    "Howl",
    "Hydro Pump",
    "Hyper Beam",
    "Hyper Fang",
    "Hyper Voice",
    "Ice Ball",
    "Ice Punch",
    "Ice Shard",
    "Icicle Crash",
    "Icicle Spear",
    "Infernal Parade",
    "Intercept Melee",
    "Intercept Ranged",
    "Iron Defense",
    "Iron Head",
    "Iron Tail",
    "Judgement",
    "Jump Kick",
    "Karate Chop",
    "Lash Out",
    "Lava Plume",
    "Leaf Blade",
    "Leaf Storm",
    "Light of Ruin",
    "Lock-On",
    "Low Sweep",
    "Luster Purge",
    "MH Adept",
    "MH Expert",
    "Mach Punch",
    "Magical Leaf",
    "Magnet Bomb",
    "Maneuver",
    "Mega Kick",
    "Mega Punch",
    "Megahorn",
    "Metal Burst",
    "Metal Claw",
    "Meteor Assault",
    "Meteor Mash",
    "Moonblast",
    "Multi-Attack",
    "Multi-Attack [SS]",
    "Night Slash",
    "OH Adept",
    "Overheat",
    "Peck",
    "Petal Blizzard",
    "Photon Geyser",
]


def test_generic_moves_batch03() -> None:
    missing = []
    for name in BATCH_MOVES:
        move = move_specials._lookup_move_spec(name)
        if move is None:
            missing.append(name)
            continue
        battle, attacker_id, defender_id = _build_battle(move)
        defender = battle.pokemon[defender_id]
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        events = _move_events_for(battle, move.name)
        print(
            f"{move.name} -> count={len(events)}",
            {
                "hit": events[-1].get("hit") if events else None,
                "damage": events[-1].get("damage") if events else None,
                "type_multiplier": events[-1].get("type_multiplier") if events else None,
                "target_hp": events[-1].get("target_hp") if events else None,
            },
        )
        assert events, f"No move events logged for {name}"
        category = (move.category or "").strip().lower()
        if category and category != "status":
            assert any(evt.get("hit") for evt in events), f"{name} never hit"
    assert not missing, f"Missing move specs: {missing}"
