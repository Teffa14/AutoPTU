from auto_ptu.career.relationships import calculate_relationship_effects


def test_relationship_effects_ignore_corrupt_persisted_bonds() -> None:
    effects = calculate_relationship_effects(
        {
            "Mara · mentor · Kanto": "6",
            "Glitch · rival · Johto": "not-a-number",
            "Void · owner · Hoenn": None,
            "Overflow · rival · Sinnoh": float("inf"),
            "Missing · contact · Unova": float("nan"),
        }  # type: ignore[arg-type]
    )

    assert effects["best_contact"] == "Mara · mentor · Kanto"
    assert effects["best_value"] == 6
    assert effects["mentor_training_bonus"] == 2
    assert effects["rival_scouting_bonus"] == 0
    assert effects["owner_recovery_bonus"] == 0
    assert [entry["name"] for entry in effects["contact_effects"]] == ["Mara · mentor · Kanto"]


def test_relationship_roles_survive_persisted_formatting_drift() -> None:
    effects = calculate_relationship_effects(
        {
            "  Mara · Mentor · Kanto  ": 6,
            "Ivo · RIVAL · Johto": 4,
            "Tess · Owner · Hoenn": 5,
            "   ": 9,
        }
    )

    assert effects["best_contact"] == "Mara · Mentor · Kanto"
    assert effects["mentor_training_bonus"] == 2
    assert effects["rival_scouting_bonus"] == 0
    assert effects["owner_recovery_bonus"] == 2
    assert effects["contract_guard"] is True
    assert [entry["role"] for entry in effects["contact_effects"]] == ["mentor", "owner", "rival"]
    assert all(entry["name"].strip() for entry in effects["contact_effects"])


def test_rivalry_history_stays_narrative_only() -> None:
    effects = calculate_relationship_effects({"Ivo · rival · Johto": 8})

    assert effects["best_contact"] == "Ivo · rival · Johto"
    assert effects["best_value"] == 8
    assert effects["active_contacts"] == 1
    assert effects["home_level_bonus"] == 0
    assert effects["rival_scouting_bonus"] == 0
    assert effects["season_recovery"] == 0
    assert effects["contract_guard"] is False
    assert effects["contact_effects"][0]["role"] == "rival"
    assert effects["contact_effects"][0]["amount"] == 0
