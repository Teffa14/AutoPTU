from __future__ import annotations

import json

from typer.testing import CliRunner

from auto_ptu.cli import app
from auto_ptu.tools.move_converter import ConversionRequest, convert_to_move


def test_convert_custom_move_text_to_usable_move() -> None:
    result = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Custom Ember",
            text="Range 4, 1 Target. DB 4. Burns the target on 18+.",
        )
    )
    move = result["move"]
    assert move["name"] == "Custom Ember"
    assert move["type"] == "Fire"
    assert move["category"] == "Special"
    assert move["freq"] == "At-Will"
    assert move["db"] == 4
    assert "Burns the target on 18+." in move["effects_text"]


def test_convert_passive_ability_to_usable_move() -> None:
    result = convert_to_move(
        ConversionRequest(
            kind="ability",
            name="Static",
        )
    )
    move = result["move"]
    assert move["name"] == "Static"
    assert move["category"] == "Status"
    assert move["freq"] == "Scene x2"
    assert "Trigger - You are hit." in move["effects_text"]
    assert "Paralyzed" in move["effects_text"]


def test_convert_item_to_usable_move() -> None:
    result = convert_to_move(
        ConversionRequest(
            kind="item",
            name="Bright Powder",
        )
    )
    move = result["move"]
    assert move["name"] == "Bright Powder"
    assert move["category"] == "Status"
    assert move["freq"] == "Scene x2"
    assert "evasion" in move["effects_text"].lower()


def test_convert_move_cli_outputs_json() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "convert-move",
            "--kind",
            "move",
            "--name",
            "Thunder Punch",
            "--text",
            "Melee, 1 Target. DB 6. The target is Paralyzed on 19+.",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["move"]["name"] == "Thunder Punch"
    assert payload["move"]["category"] == "Physical"
    assert payload["move"]["db"] == 6


def test_convert_raw_non_ptu_attack_description() -> None:
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Volt Jab",
            text="A fast electric punch that may paralyze the target.",
        )
    )
    move = payload["move"]
    assert move["type"] == "Electric"
    assert move["category"] == "Physical"
    assert move["db"] == 5
    assert move["range_kind"] == "Self" or move["range_kind"] == "Melee"


def test_convert_raw_non_ptu_area_attack_description() -> None:
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Night Volley",
            text="A dark projectile that hits all nearby enemies.",
        )
    )
    move = payload["move"]
    assert move["type"] == "Dark"
    assert move["category"] == "Special"
    assert move["area_kind"] == "Burst"
    assert move["area_value"] == 2


def test_convert_raw_non_ptu_support_description() -> None:
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Restorative Chorus",
            text="A healing song that restores allies over time.",
        )
    )
    move = payload["move"]
    assert move["category"] == "Status"
    assert move["area_kind"] == "Burst"
    assert move["freq"] == "Scene x2"


def test_convert_structured_move_sheet_text() -> None:
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Aqua Cutter",
            text=(
                "Move data\n"
                "Type\tWater\n"
                "Category\tPhysical  Physical\n"
                "Power\t70\n"
                "Accuracy\t100\n"
                "PP\t20  (max. 32)\n"
                "Makes contact?\tNo\n"
                "Introduced\tGeneration 9\n"
                "Effects\n"
                "Aqua Cutter deals damage and has an increased critical-hit ratio."
            ),
        )
    )
    move = payload["move"]
    assert move["type"] == "Water"
    assert move["category"] == "Physical"
    assert move["db"] == 7
    assert move["ac"] == 2
    assert move["range_kind"] == "Melee"
    assert move["crit_range"] == 18
    assert payload["metadata_source"] == "structured_move_text"


def test_convert_structured_special_adjacent_text_prefers_ranged_profile() -> None:
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Armor Cannon",
            text=(
                "Move data\n"
                "Type\tFire\n"
                "Category\tSpecial  Special\n"
                "Power\t120\n"
                "Accuracy\t100\n"
                "PP\t5  (max. 8)\n"
                "Makes contact?\tNo\n"
                "Introduced\tGeneration 9\n"
                "Effects\n"
                "Armor Cannon deals damage, but lowers the user's Defense and Special Defense stats by one stage each after attacking.\n\n"
                "Move target\n"
                "Targets a single adjacent Pokemon."
            ),
        )
    )
    move = payload["move"]
    assert move["category"] == "Special"
    assert move["db"] == 11
    assert move["range_kind"] == "Ranged"
    assert move["range_text"] == "Range 6, 1 Target"
    assert move["freq"] == "Scene x2"
    assert "lower the user's Defense and Special Defense by 1 Combat Stage each" in move["effects_text"]


def test_range_and_keyword_overrides_apply() -> None:
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Aqua Cutter",
            text="A water blade attack with a high critical-hit ratio.",
            range_override="Range 4, 1 Target",
            keywords_override="Priority, Dash",
        )
    )
    move = payload["move"]
    assert move["range_kind"] == "Ranged"
    assert move["range_value"] == 4
    assert move["range_text"] == "Range 4, 1 Target"
    assert "Priority" in move["keywords"]
    assert "Dash" in move["keywords"]


def test_request_payload_allows_local_ollama_without_api_key() -> None:
    from auto_ptu.tools.move_converter import request_from_payload

    request = request_from_payload(
        {
            "kind": "move",
            "name": "Volt Jab",
            "text": "A fast electric punch that may paralyze the target.",
            "use_ai": True,
            "local_model": {
                "enabled": True,
                "provider": "ollama",
                "model": "llama3.1:8b",
                "base_url": "http://127.0.0.1:11434",
                "api_key": "",
            },
        }
    )
    assert request.use_ai is True
    assert request.local_model is not None
    assert request.local_model.provider == "ollama"
    assert request.local_model.base_url == "http://127.0.0.1:11434"
    assert request.local_model.api_key == ""


def test_convert_includes_ai_diagnostics_when_not_used() -> None:
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Aqua Cutter",
            text="A water blade attack with a high critical-hit ratio.",
        )
    )
    assert payload["ai_refined"] is False
    assert payload["ai_status"] == "not_used"
    assert "not used" in payload["ai_detail"].lower()
    assert payload["request"]["use_ai"] is False


def test_convert_attempts_ai_when_use_ai_true_and_model_present(monkeypatch) -> None:
    from auto_ptu.tools import move_converter

    def fake_post_json(url, payload, headers=None, **kwargs):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "freq": "Scene x2",
                        "keywords": ["Dash"],
                        "notes": ["Refined by test model."],
                    }
                )
            }
        }

    monkeypatch.setattr(move_converter, "_post_json", fake_post_json)
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Aqua Cutter",
            text="A water blade attack with a high critical-hit ratio.",
            use_ai=True,
            local_model=move_converter.LocalModelConfig(
                enabled=False,
                provider="ollama",
                model="llama3.1:8b",
                base_url="http://127.0.0.1:11434",
            ),
        )
    )
    assert payload["ai_refined"] is True
    assert payload["ai_status"] == "applied"
    assert payload["move"]["freq"] == "Scene x2"
    assert "Dash" in payload["move"]["keywords"]


def test_user_overrides_win_after_ai_refinement(monkeypatch) -> None:
    from auto_ptu.tools import move_converter

    def fake_post_json(url, payload, headers=None, **kwargs):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "type": "Water",
                        "category": "Physical",
                        "db": 7,
                        "freq": "At-Will",
                        "range_text": "Melee, 1 Target",
                        "keywords": ["High Critical Hit Rate"],
                        "effects_text": "Critical Hits on 18+.",
                    }
                )
            }
        }

    monkeypatch.setattr(move_converter, "_post_json", fake_post_json)
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Aqua Cutter",
            text="Aqua Cutter deals damage and has an increased critical-hit ratio.",
            range_override="Range 4, 1 Target",
            keywords_override="Priority, Dash, Smite",
            type_override="Normal",
            category_override="Status",
            frequency_override="Scene x2",
            db_override=0,
            use_ai=True,
            local_model=move_converter.LocalModelConfig(
                provider="ollama",
                model="qwen2.5-coder:7b-64k",
                base_url="http://127.0.0.1:11434",
            ),
        )
    )
    move = payload["move"]
    assert payload["ai_refined"] is True
    assert move["type"] == "Normal"
    assert move["category"] == "Status"
    assert move["freq"] == "Scene x2"
    assert move["db"] == 0
    assert move["range_text"] == "Range 4, 1 Target"
    assert "Priority" in move["keywords"]


def test_structured_move_rules_override_bad_ai_patch_without_manual_overrides(monkeypatch) -> None:
    from auto_ptu.tools import move_converter

    def fake_post_json(url, payload, headers=None, **kwargs):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "db": 120,
                        "freq": "At-Will",
                        "range_kind": "Melee",
                        "range_value": 1,
                        "target_kind": "Melee",
                        "target_range": 1,
                        "range_text": "Melee, 1 Target",
                        "effects_text": "Armor Cannon deals damage, but lowers the user's Defense and Special Defense stats by one stage each after attacking.",
                    }
                )
            }
        }

    monkeypatch.setattr(move_converter, "_post_json", fake_post_json)
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Armor Cannon",
            text=(
                "Move data\n"
                "Type\tFire\n"
                "Category\tSpecial  Special\n"
                "Power\t120\n"
                "Accuracy\t100\n"
                "PP\t5  (max. 8)\n"
                "Makes contact?\tNo\n"
                "Effects\n"
                "Armor Cannon deals damage, but lowers the user's Defense and Special Defense stats by one stage each after attacking.\n\n"
                "Move target\n"
                "Targets a single adjacent Pokemon."
            ),
            use_ai=True,
            local_model=move_converter.LocalModelConfig(
                provider="ollama",
                model="qwen2.5-coder:7b",
                base_url="http://127.0.0.1:11434",
            ),
        )
    )
    move = payload["move"]
    assert payload["ai_refined"] is True
    assert move["db"] == 11
    assert move["freq"] == "Scene x2"
    assert move["range_kind"] == "Ranged"
    assert move["range_text"] == "Range 6, 1 Target"
    assert "Combat Stage each" in move["effects_text"]
    assert any("Re-applied PTU range heuristics" in note for note in payload["ai_reasoning"])


def test_ai_sanitizer_rejects_videogame_power_and_bad_keywords(monkeypatch) -> None:
    from auto_ptu.tools import move_converter

    def fake_post_json(url, payload, headers=None, **kwargs):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "db": 120,
                        "keywords": ["Contact", "Lower Defense", "Priority"],
                        "effects_text": "After the attack resolves, lower the user's Defense and Special Defense by 1 Combat Stage each.",
                        "reasoning": [
                            "Converted videogame power 120 to a PTU-scale result.",
                            "Kept the rider effect in move text instead of inventing a keyword.",
                        ],
                    }
                )
            }
        }

    monkeypatch.setattr(move_converter, "_post_json", fake_post_json)
    payload = convert_to_move(
        ConversionRequest(
            kind="move",
            name="Armor Cannon",
            text=(
                "Type Fire. Category Special. Power 120. Accuracy 100. "
                "Armor Cannon deals damage, but lowers the user's Defense and Special Defense stats by one stage each after attacking."
            ),
            use_ai=True,
            local_model=move_converter.LocalModelConfig(
                provider="ollama",
                model="qwen2.5-coder:7b",
                base_url="http://127.0.0.1:11434",
            ),
        )
    )
    move = payload["move"]
    assert payload["ai_refined"] is True
    assert move["db"] != 120
    assert move["db"] == 11
    assert "Priority" in move["keywords"]
    assert "Contact" not in move["keywords"]
    assert "Lower Defense" not in move["keywords"]
    assert any("Dropped AI DB outside PTU bounds" in note for note in payload["notes"])
    assert payload["ai_raw_response"]
    assert any("PTU-scale" in entry for entry in payload["ai_reasoning"])
