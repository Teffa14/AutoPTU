from __future__ import annotations

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.hooks import ability_hooks
from auto_ptu.rules.hooks.ability_hooks import AbilityHookContext


def _pokemon_spec(name: str, ability: str | None = None) -> PokemonSpec:
    abilities = [{"name": ability}] if ability else []
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=10,
        moves=[MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2)],
        abilities=abilities,
        movement={"overland": 4},
    )


def test_ice_scales_resists_special() -> None:
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker"),
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", ability="Ice Scales"),
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=6, height=6),
    )
    move = MoveSpec(
        name="Test Move",
        type="Fire",
        category="Special",
        db=6,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
    )
    result = {
        "hit": True,
        "damage": 40,
        "pre_type_damage": 20,
        "type_multiplier": 2.0,
        "roll": 20,
    }
    ctx = AbilityHookContext(
        battle=battle,
        attacker_id="a-1",
        attacker=attacker,
        defender_id="b-1",
        defender=defender,
        move=move,
        effective_move=move,
        events=[],
        phase="post_result",
        result=result,
    )
    ability_hooks.apply_ability_hooks("post_result", ctx)
    assert result.get("type_multiplier") == 1.5
    assert result.get("damage") == 30


def test_pastel_veil_blocks_poison() -> None:
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker"),
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    target = PokemonState(
        spec=_pokemon_spec("Target"),
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    ally = PokemonState(
        spec=_pokemon_spec("Ally", ability="Pastel Veil"),
        controller_id="b",
        position=(1, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": target, "b-2": ally},
        grid=GridState(width=6, height=6),
    )
    events: list[dict] = []
    battle._apply_status(
        events,
        attacker_id="a-1",
        target_id="b-1",
        move=MoveSpec(name="Toxic", type="Poison", category="Status", db=0, ac=2),
        target=target,
        status="Poisoned",
        effect="poison",
        description="Toxic poisons the target.",
    )
    assert not target.has_status("Poisoned")
    assert any(event.get("ability") == "Pastel Veil" for event in events)


def test_probability_control_sets_reroll() -> None:
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", ability="Probability Control"),
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender"),
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=6, height=6),
    )
    move = MoveSpec(
        name="Probability Control",
        type="Psychic",
        category="Status",
        db=0,
        ac=None,
        range_kind="Ranged",
        range_value=6,
        target_kind="Ranged",
        target_range=6,
    )
    battle.resolve_move_targets(
        attacker_id="a-1",
        move=move,
        target_id="b-1",
        target_position=defender.position,
    )
    assert defender.get_temporary_effects("probability_control")


def test_psychic_surge_sets_terrain() -> None:
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", ability="Psychic Surge"),
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender"),
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=6, height=6),
    )
    move = MoveSpec(
        name="Psychic Surge",
        type="Psychic",
        category="Status",
        db=0,
        ac=None,
        range_kind="Self",
        target_kind="Self",
    )
    battle.resolve_move_targets(
        attacker_id="a-1",
        move=move,
        target_id="a-1",
        target_position=attacker.position,
    )
    assert isinstance(battle.terrain, dict)
    assert (battle.terrain.get("name") or "").lower().startswith("psychic")


def test_dragons_maw_shifts_type_multiplier() -> None:
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
    ability_name = "Dragon’s Maw"
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", ability=ability_name),
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender"),
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=6, height=6),
    )
    move = MoveSpec(
        name="Dragon Test",
        type="Dragon",
        category="Special",
        db=6,
        ac=2,
        range_kind="Melee",
        range_value=1,
        target_kind="Melee",
        target_range=1,
    )
    result = {
        "hit": True,
        "damage": 10,
        "pre_type_damage": 20,
        "type_multiplier": 0.5,
        "roll": 20,
    }
    ctx = AbilityHookContext(
        battle=battle,
        attacker_id="a-1",
        attacker=attacker,
        defender_id="b-1",
        defender=defender,
        move=move,
        effective_move=move,
        events=[],
        phase="post_result",
        result=result,
    )
    ability_hooks.apply_ability_hooks("post_result", ctx)
    print(
        "Dragon's Maw result:",
        {"type_multiplier": result.get("type_multiplier"), "damage": result.get("damage")},
        "events:",
        ctx.events,
    )
    assert result.get("type_multiplier") == 1.0
    assert result.get("damage") == 20
    assert any(
        event.get("ability") in ("Dragon's Maw", ability_name) and event.get("effect") == "type_shift"
        for event in ctx.events
    )
