from __future__ import annotations

import pytest

from auto_ptu.rules import (
    BattleState,
    TrainerState,
    PokemonState,
    UseItemAction,
    FastPitchAction,
    GottaCatchEmAllAction,
    CapturedMomentumAction,
    DevitalizingThrowAction,
)
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


class FixedRng:
    def __init__(self, *values: int) -> None:
        self.values = list(values)

    def randint(self, low: int, high: int) -> int:
        if not self.values:
            raise AssertionError(f"No fixed RNG value left for randint({low}, {high})")
        value = self.values.pop(0)
        assert low <= value <= high
        return value


def _trainer_combatant(*features: str, item: str = "Basic Ball") -> tuple[TrainerState, PokemonState]:
    trainer = TrainerState(identifier="ash", name="Ash", team="heroes", ap=5)
    spec = _pokemon_spec("Ash")
    spec.tags.append("Trainer")
    spec.items = [{"name": item}]
    spec.trainer_features = [{"name": feature} for feature in features]
    spec.skills = {
        "acrobatics": 2,
        "athletics": 4,
        "stealth": 1,
        "survival": 3,
        "guile": 2,
        "perception": 1,
    }
    return trainer, PokemonState(spec=spec, controller_id=trainer.identifier)


def _wild_target(level: int = 20, hp: int | None = None) -> PokemonState:
    spec = _pokemon_spec("Pikachu")
    spec.level = level
    spec.tags.append("Wild")
    target = PokemonState(spec=spec, controller_id="wild")
    if hp is not None:
        target.hp = hp
    return target


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


def test_tools_of_the_trade_adds_poke_ball_accuracy_bonus() -> None:
    trainer, actor = _trainer_combatant("Tools of the Trade")
    target = _wild_target()
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(6, 90)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()

    accuracy = next(evt for evt in battle.log if evt.get("effect") == "capture_accuracy")
    assert accuracy["hit"] is True
    assert accuracy["accuracy_bonus"] == 2
    assert accuracy["tools_of_the_trade"] is True


def test_snare_subtracts_ten_from_capture_roll_against_stuck_target() -> None:
    trainer, actor = _trainer_combatant("Snare")
    target = _wild_target(level=50)
    target.statuses.append({"name": "Stuck"})
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(20, 50)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()

    capture = next(evt for evt in battle.log if evt.get("effect") == "capture_roll")
    assert "snare" in capture["reasons"]
    assert capture["roll_modifier"] <= -40


def test_gotta_catch_em_all_switches_capture_roll_digits() -> None:
    trainer, actor = _trainer_combatant("Gotta Catch 'Em All")
    target = _wild_target(level=50)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(20, 91)

    battle.queue_action(GottaCatchEmAllAction(actor_id="ash"))
    battle.resolve_next_action()
    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()

    capture = next(evt for evt in battle.log if evt.get("effect") == "capture_roll")
    assert capture["digit_swap"] == {"from": 91, "to": 19}
    assert capture["natural_roll"] == 19


def test_devitalizing_throw_triggers_after_escape_and_applies_slow() -> None:
    trainer, actor = _trainer_combatant("Devitalizing Throw")
    target = _wild_target(level=80)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(20, 99)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()
    assert actor.get_temporary_effects("devitalizing_throw_ready")

    battle.queue_action(DevitalizingThrowAction(actor_id="ash", mode="slow"))
    battle.resolve_next_action()
    assert target.has_status("Slowed")
    assert trainer.ap == 4


def test_captured_momentum_triggers_after_success_and_can_grant_temporary_ap() -> None:
    trainer, actor = _trainer_combatant("Captured Momentum", item="Master Ball")
    target = _wild_target(level=80)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(20, 99)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()
    assert actor.get_temporary_effects("captured_momentum_ready")
    assert target.active is False

    battle.queue_action(CapturedMomentumAction(actor_id="ash", mode="ap"))
    battle.resolve_next_action()
    assert trainer.ap == 6
    assert trainer.temporary_ap


def test_fast_pitch_spends_ap_and_throws_capture_ball() -> None:
    trainer, actor = _trainer_combatant("Fast Pitch")
    target = _wild_target(level=80)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(20, 99)

    battle.queue_action(FastPitchAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()

    assert trainer.ap == 4
    assert not actor.spec.items
    assert any(evt.get("feature") == "Fast Pitch" for evt in battle.log)
    assert any(evt.get("effect") == "capture_roll" for evt in battle.log)


def test_hand_net_is_reusable_and_applies_capture_roll_bonus() -> None:
    trainer, actor = _trainer_combatant("Tools of the Trade", item="Hand Net")
    actor.spec.items.append({"name": "Basic Ball"})
    target = _wild_target(level=80)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(6, 20, 90)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()
    assert [item["name"] for item in actor.spec.items] == ["Hand Net", "Basic Ball"]
    accuracy = next(evt for evt in battle.log if evt.get("effect") == "capture_tool_accuracy")
    assert accuracy["hit"] is True
    assert accuracy["accuracy_bonus"] == 2
    assert target.has_status("Trapped")
    assert target.get_temporary_effects("capture_tool_trap")[0]["capture_roll_modifier"] == -20

    battle.queue_action(UseItemAction(actor_id="ash", item_index=1, target_id="wild"))
    battle.resolve_next_action()
    capture = next(evt for evt in battle.log if evt.get("effect") == "capture_roll")
    assert "hand net" in capture["reasons"]
    assert capture["roll_modifier"] <= -40


def test_weighted_net_slows_grounds_and_applies_capture_roll_bonus() -> None:
    trainer, actor = _trainer_combatant(item="Weighted Nets")
    target = _wild_target(level=40)
    target.spec.movement["sky"] = 6
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(10)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()

    assert actor.spec.items[0]["name"] == "Weighted Nets"
    assert target.has_status("Slowed")
    assert target.get_temporary_effects("force_grounded")
    assert target.get_temporary_effects("capture_tool_trap")[0]["capture_roll_modifier"] == -20


def test_glue_cannon_critical_hit_sticks_and_traps_target() -> None:
    trainer, actor = _trainer_combatant(item="Glue Cannon")
    target = _wild_target(level=40)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(20)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()

    assert actor.spec.items[0]["name"] == "Glue Cannon"
    assert target.has_status("Stuck")
    assert target.has_status("Trapped")
    assert any(evt.get("tool") == "glue cannon" and evt.get("critical") is True for evt in battle.log)


def test_bait_failed_focus_marks_target_for_snare_capture_bonus() -> None:
    trainer, actor = _trainer_combatant("Snare", item="Bait")
    actor.spec.items.append({"name": "Basic Ball"})
    target = _wild_target(level=80)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash": actor, "wild": target})
    battle.rng = FixedRng(1, 20, 90)

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()
    assert target.get_temporary_effects("bait_distracted")

    battle.queue_action(UseItemAction(actor_id="ash", item_index=0, target_id="wild"))
    battle.resolve_next_action()
    capture = next(evt for evt in battle.log if evt.get("effect") == "capture_roll")
    assert "snare" in capture["reasons"]
