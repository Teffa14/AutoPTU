from __future__ import annotations

import json

from auto_ptu.career.models import CareerDecision, CareerDecisionOption
from auto_ptu.career.narrative import NarrativeRenderer


def _decision() -> CareerDecision:
    return CareerDecision(
        id="decision-1",
        family="media",
        title="Original title",
        body="Original body",
        npc_name="Reporter",
        options=[
            CareerDecisionOption(
                id="safe",
                label="Original option",
                description="Original description",
                risk="low",
                transparency="clear",
                guaranteed={"reputation": 1},
                gamble={},
            )
        ],
    )


def _renderer(tmp_path) -> NarrativeRenderer:
    return NarrativeRenderer(
        base_url="http://127.0.0.1:9",
        model="test-model",
        model_digest="sha256:" + "a" * 64,
        cache_root=tmp_path,
        timeout_seconds=0.01,
    )


def test_corrupt_non_mapping_cache_falls_back_without_crashing(tmp_path) -> None:
    renderer = _renderer(tmp_path)
    decision = _decision()
    key = renderer._cache_key(decision, {}, "es")
    (tmp_path / f"{key}.json").write_text(json.dumps(["bad", "cache"]), encoding="utf-8")

    rendered = renderer.render(decision, {}, "es")

    assert rendered.title == decision.title
    assert rendered.body == decision.body
    assert rendered.options[0].label == decision.options[0].label
    assert rendered.options[0].guaranteed == {"reputation": 1}


def test_malformed_cached_prose_cannot_partially_replace_fallback(tmp_path) -> None:
    renderer = _renderer(tmp_path)
    decision = _decision()
    key = renderer._cache_key(decision, {}, "en")
    malformed = {
        "title": "Injected title",
        "body": "Injected body",
        "options": [{"label": "Missing description"}],
    }
    (tmp_path / f"{key}.json").write_text(json.dumps(malformed), encoding="utf-8")

    rendered = renderer.render(decision, {}, "en")

    assert rendered.title == "Original title"
    assert rendered.body == "Original body"
    assert rendered.options[0].label == "Original option"


def test_valid_cached_prose_changes_only_copy_and_preserves_mechanics(tmp_path) -> None:
    renderer = _renderer(tmp_path)
    decision = _decision()
    key = renderer._cache_key(decision, {}, "es")
    valid = {
        "title": "Conferencia de prensa",
        "body": "El club espera tu respuesta.",
        "options": [{"label": "Responder", "description": "Hablar con calma."}],
    }
    (tmp_path / f"{key}.json").write_text(json.dumps(valid), encoding="utf-8")

    rendered = renderer.render(decision, {}, "es")

    assert rendered.title == "Conferencia de prensa"
    assert rendered.options[0].label == "Responder"
    assert rendered.options[0].guaranteed == {"reputation": 1}
    assert rendered.options[0].risk == "low"
    assert decision.title == "Original title"
    assert decision.options[0].label == "Original option"
