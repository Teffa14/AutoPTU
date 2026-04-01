from __future__ import annotations

from auto_ptu.pokeapi_assets import ability_metadata


def test_ability_metadata_foundry_fallback():
    meta = ability_metadata("Haunting")
    assert meta is not None
    print(f"Haunting metadata: {meta}")
    effect = str(meta.get("effect") or "")
    assert meta.get("source") == "foundry_core_abilities"
    assert "trigger" in effect.lower() or "cursed" in effect.lower()


def test_ability_metadata_ptu_csv_preferred():
    meta = ability_metadata("Adaptability")
    assert meta is not None
    print(f"Adaptability metadata: {meta}")
    assert meta.get("source") == "ptu_csv"
    assert str(meta.get("effect") or "").strip()


def test_dimensional_rift_metadata_uses_plural_foundry_alias():
    meta = ability_metadata("Dimensional Rift")
    assert meta is not None
    assert meta.get("source") == "foundry_core_abilities"
    effect = str(meta.get("effect") or "").lower()
    assert "originate" in effect or "rift" in effect
