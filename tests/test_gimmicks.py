from __future__ import annotations

import random

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, PokemonState, TrainerState, TurnPhase, UseMoveAction


class FixedRNG(random.Random):
    def randint(self, a: int, b: int) -> int:
        return b


def _pokemon_spec(name: str, *, moves: list[MoveSpec], types: list[str] | None = None) -> PokemonSpec:
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


def _build_pair(attacker: PokemonState, defender: PokemonState) -> BattleState:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    battle.rng = FixedRNG()
    return battle


def test_mega_evolve_on_move_action() -> None:
    move = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2)
    atk_spec = _pokemon_spec("Altaria", moves=[move], types=["Dragon", "Flying"])
    atk_spec.items = [{"name": "Altarianite"}]
    attacker = PokemonState(spec=atk_spec, controller_id="ash")
    defender = PokemonState(spec=_pokemon_spec("Blastoise", moves=[move], types=["Water"]), controller_id="gary")
    battle = _build_pair(attacker, defender)

    UseMoveAction(
        actor_id="ash-1",
        move_name="Tackle",
        target_id="gary-1",
        mega_evolve=True,
    ).resolve(battle)

    assert attacker.get_temporary_effects("mega_form")
    assert any(evt.get("effect") == "mega_evolution" for evt in battle.log)


def test_dynamax_scales_hp_and_expires() -> None:
    move = MoveSpec(name="Slash", type="Normal", category="Physical", db=7, ac=2)
    attacker = PokemonState(spec=_pokemon_spec("Eevee", moves=[move]), controller_id="ash")
    defender = PokemonState(spec=_pokemon_spec("Pikachu", moves=[move]), controller_id="gary")
    battle = _build_pair(attacker, defender)

    base_max = attacker.max_hp_with_injuries()
    UseMoveAction(
        actor_id="ash-1",
        move_name="Slash",
        target_id="gary-1",
        dynamax=True,
    ).resolve(battle)

    assert attacker.max_hp_with_injuries() == base_max * 2
    assert attacker.hp is not None and attacker.hp > base_max

    battle.round = 4
    attacker.handle_phase_effects(battle, TurnPhase.START, "ash-1")
    assert attacker.max_hp_with_injuries() == base_max


def test_z_move_boosts_damage() -> None:
    move = MoveSpec(name="Ember", type="Fire", category="Special", db=5, ac=2)
    defender_move = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2)

    base_atk_spec = _pokemon_spec("Eevee", moves=[move], types=["Fire"])
    boosted_atk_spec = _pokemon_spec("Eevee", moves=[move], types=["Fire"])
    boosted_atk_spec.items = [{"name": "Firium-Z"}]

    base_battle = _build_pair(
        PokemonState(spec=base_atk_spec, controller_id="ash"),
        PokemonState(spec=_pokemon_spec("Bulbasaur", moves=[defender_move], types=["Grass"]), controller_id="gary"),
    )
    boosted_battle = _build_pair(
        PokemonState(spec=boosted_atk_spec, controller_id="ash"),
        PokemonState(spec=_pokemon_spec("Bulbasaur", moves=[defender_move], types=["Grass"]), controller_id="gary"),
    )

    UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1").resolve(base_battle)
    UseMoveAction(actor_id="ash-1", move_name="Ember", target_id="gary-1", z_move=True).resolve(boosted_battle)

    base_def = base_battle.pokemon["gary-1"]
    boosted_def = boosted_battle.pokemon["gary-1"]
    assert boosted_def.hp is not None and base_def.hp is not None
    assert boosted_def.hp < base_def.hp
    assert any(evt.get("effect") == "z_move_activate" for evt in boosted_battle.log)


def test_teracrystal_changes_type() -> None:
    move = MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2)
    atk_spec = _pokemon_spec("Eevee", moves=[move], types=["Normal"])
    atk_spec.items = [{"name": "Tera Orb"}]
    attacker = PokemonState(spec=atk_spec, controller_id="ash")
    defender = PokemonState(spec=_pokemon_spec("Gastly", moves=[move], types=["Ghost", "Poison"]), controller_id="gary")
    battle = _build_pair(attacker, defender)

    UseMoveAction(
        actor_id="ash-1",
        move_name="Tackle",
        target_id="gary-1",
        teracrystal=True,
        tera_type="Ghost",
    ).resolve(battle)

    assert attacker.spec.types == ["Ghost"]
    assert attacker.get_temporary_effects("terastallized")
    assert any(evt.get("effect") == "teracrystal" for evt in battle.log)
