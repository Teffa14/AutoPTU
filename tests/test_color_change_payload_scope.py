from __future__ import annotations

from pathlib import Path


BATTLE_STATE = Path(__file__).resolve().parents[1] / "auto_ptu" / "rules" / "battle_state.py"


def test_color_change_event_payload_stays_inside_type_change_guard() -> None:
    """Same-type hits must not read a payload that was never initialized."""
    source = BATTLE_STATE.read_text(encoding="utf-8")
    marker = '"ability": "Color Change"'
    marker_index = source.index(marker)
    window = source[marker_index - 700 : marker_index + 900]

    assert "if new_type and defender.spec.types != [new_type]:" in window
    assert (
        "                            events.append(payload)\n"
        "                            self.log_event(payload)\n"
        "                    if (\n"
    ) in window
