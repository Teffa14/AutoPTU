import json

from auto_ptu.tools.generate_trainer_coverage_report import generate_report


def test_generate_trainer_coverage_report_classifies_entries(tmp_path):
    character_creation = tmp_path / "character_creation.json"
    character_creation.write_text(
        json.dumps(
            {
                "features": [
                    {
                        "name": "Mapped Feature",
                        "trigger": "round_start",
                        "effect_payload": {"type": "grant_ap", "amount": 1},
                    },
                    {
                        "name": "Hooked Feature",
                    },
                    {
                        "name": "Action Feature",
                    },
                    {
                        "name": "Pokemon Action Feature",
                    },
                    {
                        "name": "Move Grant Feature",
                    },
                ],
                "edges_catalog": [
                    {
                        "name": "Missing Edge",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    perk_dir = tmp_path / "perk_effects"
    perk_dir.mkdir()
    (perk_dir / "__init__.py").write_text("", encoding="utf-8")
    (perk_dir / "hooks.py").write_text(
        "\n".join(
            [
                "from auto_ptu.rules.hooks.perk_hooks import register_perk_hook",
                "",
                "@register_perk_hook('turn_start', 'Hooked Feature')",
                "def _hook(ctx):",
                "    return None",
                "",
            ]
        ),
        encoding="utf-8",
    )
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / "battle_state.py").write_text(
        "\n".join(
            [
                "class ActionFeatureAction:",
                "    pass",
                "",
                "class TrainerMappedAction(TrainerFeatureAction):",
                "    feature_name = 'Action Feature'",
                "",
                "class PokemonMappedAction(PokemonFeatureAction):",
                "    feature_name = 'Pokemon Action Feature'",
                "",
                "TRAINER_FEATURE_MOVE_GRANTS = {",
                "    'move grant feature': ('Demo Move',),",
                "}",
                "",
                "WEAPONIZED_TRAINER_FEATURE_MOVE_GRANTS = {",
                "    'move grant feature',",
                "}",
                "",
                "def apply_feature():",
                "    feature = 'Mapped Feature'",
                "    return feature",
                "",
            ]
        ),
        encoding="utf-8",
    )

    json_out = tmp_path / "coverage.json"
    md_out = tmp_path / "coverage.md"
    payload = generate_report(
        character_creation_path=character_creation,
        perk_effects_dir=perk_dir,
        runtime_dir=runtime_dir,
        json_out=json_out,
        markdown_out=md_out,
    )

    assert payload["summary"]["total"] == 6
    assert payload["summary"]["features"] == 5
    assert payload["summary"]["edges"] == 1
    assert payload["summary"]["perk_hook_ready"] == 1
    assert payload["summary"]["trainer_action_registry_ready"] == 1
    assert payload["summary"]["pokemon_action_registry_ready"] == 1
    assert payload["summary"]["move_grant_rider_ready"] == 0
    assert payload["summary"]["weaponized_move_grant_ready"] == 1
    assert payload["summary"]["move_grant_ready"] == 0
    assert payload["summary"]["core_runtime_ready"] == 1
    assert payload["summary"]["core_runtime_passive"] == 0
    assert payload["summary"]["core_runtime_action"] == 1
    assert payload["summary"]["generic_runtime_ready"] == 0
    assert payload["summary"]["missing_runtime_mapping"] == 1
    assert payload["sources"]["trainer_feature_actions"] == ["action feature"]
    assert payload["sources"]["pokemon_feature_actions"] == ["pokemon action feature"]
    assert payload["sources"]["weaponized_trainer_feature_move_grants"] == ["move grant feature"]
    assert payload["queues"]["trainer_action_registry_ready"] == ["Action Feature"]
    assert payload["queues"]["pokemon_action_registry_ready"] == ["Pokemon Action Feature"]
    assert payload["queues"]["move_grant_rider_ready"] == []
    assert payload["queues"]["core_runtime_action"] == ["Mapped Feature"]
    assert payload["queues"]["weaponized_move_grant_ready"] == ["Move Grant Feature"]
    action_entry = next(entry for entry in payload["entries"] if entry["name"] == "Action Feature")
    pokemon_action_entry = next(entry for entry in payload["entries"] if entry["name"] == "Pokemon Action Feature")
    assert action_entry["notes"] == []
    assert pokemon_action_entry["notes"] == []
    assert json_out.exists()
    assert md_out.exists()
    persisted = json.loads(json_out.read_text(encoding="utf-8"))
    assert persisted["summary"] == payload["summary"]


def test_generate_trainer_coverage_report_honors_explicit_runtime_map(tmp_path):
    character_creation = tmp_path / "character_creation.json"
    character_creation.write_text(
        json.dumps({"features": [{"name": "Stamina"}], "edges_catalog": []}),
        encoding="utf-8",
    )
    perk_dir = tmp_path / "perk_effects"
    perk_dir.mkdir()
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / "battle_state.py").write_text("", encoding="utf-8")
    payload = generate_report(
        character_creation_path=character_creation,
        perk_effects_dir=perk_dir,
        runtime_dir=runtime_dir,
        json_out=tmp_path / "coverage.json",
        markdown_out=tmp_path / "coverage.md",
    )
    assert payload["summary"]["core_runtime_ready"] == 1
    assert payload["entries"][0]["runtime_status"] == "core_runtime_ready"


def test_generate_trainer_coverage_report_discovers_indirect_feature_action_subclasses(tmp_path):
    character_creation = tmp_path / "character_creation.json"
    character_creation.write_text(
        json.dumps({"features": [{"name": "Indirect Action Feature"}], "edges_catalog": []}),
        encoding="utf-8",
    )
    perk_dir = tmp_path / "perk_effects"
    perk_dir.mkdir()
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / "battle_state.py").write_text(
        "\n".join(
            [
                "class TrainerFeatureAction:",
                "    pass",
                "",
                "class _SharedAction(TrainerFeatureAction):",
                "    pass",
                "",
                "class IndirectMappedAction(_SharedAction):",
                "    feature_name = 'Indirect Action Feature'",
            ]
        ),
        encoding="utf-8",
    )
    payload = generate_report(
        character_creation_path=character_creation,
        perk_effects_dir=perk_dir,
        runtime_dir=runtime_dir,
        json_out=tmp_path / "coverage.json",
        markdown_out=tmp_path / "coverage.md",
    )
    assert payload["summary"]["trainer_action_registry_ready"] == 1
    assert payload["sources"]["trainer_feature_actions"] == ["indirect action feature"]
    assert payload["entries"][0]["runtime_status"] == "trainer_action_registry_ready"
