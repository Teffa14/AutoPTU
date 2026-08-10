from __future__ import annotations

from dataclasses import asdict

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.narrative import NarrativeRenderer, _mechanical_signature


def test_narrative_fallback_is_immediate_and_mechanically_identical(tmp_path) -> None:
    engine = CareerEngine(battle_runner=lambda spec: None)  # runner is not used while opening a season
    run = engine.new_run(
        player_id="narrative-user",
        name="Nora",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=42,
    )
    decision = run.season.decision
    assert decision is not None
    before = _mechanical_signature(decision)
    renderer = NarrativeRenderer(base_url="", model="", model_digest="", cache_root=tmp_path)
    rendered = renderer.render(decision, {"region": "kanto"}, "es")
    assert asdict(rendered) == asdict(decision)
    assert _mechanical_signature(rendered) == before
