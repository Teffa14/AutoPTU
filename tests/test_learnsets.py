from __future__ import annotations

from auto_ptu.learnsets import load_learnsets


def _moves_for(species: str) -> set[str]:
    learnsets = load_learnsets()
    return {name for name, _level in learnsets.get(species.lower(), [])}


def test_evolution_line_moves_are_inherited_for_backend_learnsets() -> None:
    porygon2_moves = _moves_for("porygon2")
    assert {"Tackle", "Conversion", "Conversion2"} <= porygon2_moves

    charizard_moves = _moves_for("charizard")
    assert {"Scratch", "Growl"} <= charizard_moves

    raichu_moves = _moves_for("raichu")
    assert {"Growl", "Thunder Shock"} <= raichu_moves
