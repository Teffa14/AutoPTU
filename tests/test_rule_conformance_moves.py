from __future__ import annotations

import random

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, PokemonState, TrainerState, UseMoveAction, ActionType


def _spec(name: str, moves: list[MoveSpec], *, types: list[str] | None = None) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=30,
        types=types or ["Normal"],
        hp_stat=12,
        atk=12,
        defense=10,
        spatk=12,
        spdef=10,
        spd=10,
        moves=moves,
    )


def _battle(attacker: PokemonState, defender: PokemonState) -> BattleState:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
        rng=random.Random(5),
    )
    return battle


def test_bestow_is_swift_and_transfers_item() -> None:
    bestow = MoveSpec(name="Bestow", type="Normal", category="Status", db=0, ac=2, freq="EOT")
    tackle = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2, freq="EOT")
    atk_spec = _spec("Eevee", [bestow])
    atk_spec.items = [{"name": "Oran Berry"}]
    def_spec = _spec("Pikachu", [tackle])
    attacker = PokemonState(spec=atk_spec, controller_id="ash")
    defender = PokemonState(spec=def_spec, controller_id="gary")
    battle = _battle(attacker, defender)

    action = UseMoveAction(actor_id="ash-1", move_name="Bestow", target_id="gary-1")
    assert action._resolve_action_type(attacker, bestow) == ActionType.SWIFT
    action.resolve(battle)

    assert not attacker.spec.items
    assert defender.spec.items and defender.spec.items[0].get("name") == "Oran Berry"
    assert any(evt.get("effect") == "bestow" for evt in battle.log)


def test_covet_steals_when_user_has_no_item() -> None:
    covet = MoveSpec(name="Covet", type="Normal", category="Physical", db=6, ac=2, freq="EOT")
    tackle = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2, freq="EOT")
    atk_spec = _spec("Eevee", [covet])
    def_spec = _spec("Pikachu", [tackle])
    def_spec.items = [{"name": "Sitrus Berry"}]
    attacker = PokemonState(spec=atk_spec, controller_id="ash")
    defender = PokemonState(spec=def_spec, controller_id="gary")
    battle = _battle(attacker, defender)

    UseMoveAction(actor_id="ash-1", move_name="Covet", target_id="gary-1").resolve(battle)

    assert attacker.spec.items and attacker.spec.items[0].get("name") == "Sitrus Berry"
    assert not defender.spec.items
    assert any(evt.get("effect") == "covet" for evt in battle.log)


def test_leech_life_sm_drains_half_damage() -> None:
    leech = MoveSpec(name="Leech Life [SM]", type="Bug", category="Physical", db=7, ac=2, freq="EOT")
    tackle = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2, freq="EOT")
    atk_spec = _spec("Scyther", [leech], types=["Bug", "Flying"])
    def_spec = _spec("Abra", [tackle], types=["Psychic"])
    attacker = PokemonState(spec=atk_spec, controller_id="ash")
    defender = PokemonState(spec=def_spec, controller_id="gary")
    battle = _battle(attacker, defender)
    attacker.hp = max(1, attacker.max_hp() - 15)
    before_hp = attacker.hp

    UseMoveAction(actor_id="ash-1", move_name="Leech Life [SM]", target_id="gary-1").resolve(battle)

    assert attacker.hp is not None and before_hp is not None
    assert attacker.hp > before_hp
