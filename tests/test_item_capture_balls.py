from __future__ import annotations

import pytest

from auto_ptu.rules import BattleState, TrainerState, PokemonState, UseItemAction
from auto_ptu.data_models import MoveSpec, PokemonSpec


def _pokemon_spec(name: str = "Eevee") -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=12,
        moves=[MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2)],
    )


def _capture_event(ball_name: str, *, target: PokemonState, weather: str | None = None) -> dict:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": ball_name}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user, "gary-1": target})
    if weather is not None:
        battle.weather = weather
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"{ball_name} capture event: {event}")
    return event


@pytest.mark.parametrize(
    ("ball_name", "base_modifier", "multiplier"),
    [
        ("Air Ball", 0, 1.0),
        ("Basic Ball", 0, 1.0),
        ("Cherish Ball", -5, 1.0),
        ("Dive Ball", 0, 1.0),
        ("Dusk Ball", 0, 1.0),
        ("Earth Ball", 0, 1.0),
        ("Fabulous Ball", -5, 1.0),
        ("Fast Ball", 0, 1.0),
        ("Friend Ball", -5, 1.0),
        ("Gossamer Ball", 0, 1.0),
        ("Great Ball", -10, 1.0),
        ("Hail Ball", 0, 1.0),
        ("Haunt Ball", 0, 1.0),
        ("Heal Ball", -5, 1.0),
        ("Heat Ball", 0, 1.0),
        ("Heavy Ball", 0, 1.0),
        ("Hefty Ball", 0, 1.5),
        ("Leaden Ball", 0, 2.0),
        ("Learning Ball", -5, 1.0),
        ("Level Ball", 0, 1.0),
        ("Love Ball", 0, 1.0),
        ("Lure Ball", 0, 1.0),
        ("Luxury Ball", -5, 1.0),
        ("Master Ball", -100, 1.0),
        ("Mold Ball", 0, 1.0),
        ("Moon Ball", 0, 1.0),
        ("Mystic Ball", 0, 1.0),
        ("Nest Ball", 0, 1.0),
        ("Net Ball", 0, 1.0),
        ("Park Ball", -15, 1.0),
        ("Power Ball", 0, 1.0),
        ("Premier Ball", 0, 1.0),
        ("Quick Ball", -20, 1.0),
        ("Rain Ball", 0, 1.0),
        ("Repeat Ball", 0, 1.0),
        ("Safari Ball", 0, 1.0),
        ("Sand Ball", 0, 1.0),
        ("Solid Ball", 0, 1.0),
        ("Sport Ball", 0, 1.0),
        ("Sun Ball", 0, 1.0),
        ("Timer Ball", 5, 1.0),
        ("Ultra Ball", -15, 1.0),
        ("Gigaton Ball", 0, 2.75),
    ],
)
def test_capture_ball_baseline_modifiers(ball_name: str, base_modifier: int, multiplier: float) -> None:
    target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="ash")
    event = _capture_event(ball_name, target=target)
    assert event.get("effect") == "capture_attempt"
    assert event.get("base_modifier") == base_modifier
    assert event.get("multiplier") == multiplier


def test_capture_ball_dream_ball_sleep_bonus() -> None:
    target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="ash")
    target.statuses.append({"name": "Sleep"})
    event = _capture_event("Dream Ball", target=target)
    assert event.get("multiplier") == 4.0


def test_capture_ball_beast_ball_ultra_beast_bonus() -> None:
    spec = _pokemon_spec("Nihilego")
    spec.tags.append("Ultra Beast")
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Beast Ball", target=target)
    assert event.get("multiplier") == 5.0


def test_capture_ball_dark_ball_closed_heart_bonus() -> None:
    spec = _pokemon_spec("Spiritomb")
    spec.tags.append("closed-heart")
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Dark Ball", target=target)
    assert event.get("multiplier") == 5.0


def test_capture_ball_strange_ball_paradox_bonus() -> None:
    spec = _pokemon_spec("Roaring Moon")
    spec.tags.append("paradox")
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Strange Ball", target=target)
    assert event.get("multiplier") == 5.0


def test_capture_ball_vane_ball_windy_bonus() -> None:
    target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="ash")
    event = _capture_event("Vane Ball", target=target, weather="Windy")
    assert event.get("multiplier") == 3.5


def test_capture_ball_beacon_ball_fog_bonus() -> None:
    target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="ash")
    event = _capture_event("Beacon Ball", target=target, weather="Foggy")
    assert event.get("multiplier") == 3.5


def test_capture_ball_smog_ball_weather_bonus() -> None:
    target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id="ash")
    event = _capture_event("Smog Ball", target=target, weather="Smoggy")
    assert event.get("multiplier") == 3.5


def test_capture_ball_coolant_ball_nuclear_bonus() -> None:
    spec = _pokemon_spec("Pikachu")
    spec.types.append("Nuclear")
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Coolant Ball", target=target)
    assert event.get("multiplier") == 3.5


def test_capture_ball_tiller_ball_burrow_bonus() -> None:
    spec = _pokemon_spec("Diglett")
    spec.movement["burrow"] = 4
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Tiller Ball", target=target)
    assert event.get("multiplier") == 4.0


def test_capture_ball_wing_ball_flight_bonus() -> None:
    spec = _pokemon_spec("Pidgey")
    spec.movement["sky"] = 6
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Wing Ball", target=target)
    assert event.get("multiplier") == 2.0


def test_capture_ball_jet_ball_flight_bonus() -> None:
    spec = _pokemon_spec("Pidgey")
    spec.movement["sky"] = 6
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Jet Ball", target=target)
    assert event.get("multiplier") == 3.0


def test_capture_ball_feather_ball_flight_bonus() -> None:
    spec = _pokemon_spec("Pidgey")
    spec.movement["sky"] = 6
    target = PokemonState(spec=spec, controller_id="ash")
    event = _capture_event("Feather Ball", target=target)
    assert event.get("multiplier") == 1.25
