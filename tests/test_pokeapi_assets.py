from __future__ import annotations

from pathlib import Path

from auto_ptu import pokeapi_assets


def test_ability_metadata_uses_ptu_csv_when_pokeapi_missing(monkeypatch) -> None:
    monkeypatch.setattr(pokeapi_assets, "_ability_effect_from_ptu_csv", lambda _name: "PTU fallback text")
    monkeypatch.setattr(pokeapi_assets, "_cached_meta", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pokeapi_assets, "_request_json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pokeapi_assets, "_store_meta", lambda *_args, **_kwargs: None)

    meta = pokeapi_assets.ability_metadata("Haunting")

    assert meta is not None
    assert meta["effect"] == "PTU fallback text"
    assert meta["source"] == "ptu_csv"


def test_ability_metadata_repairs_cached_placeholder_effect(monkeypatch) -> None:
    cached = {
        "id": None,
        "name": "Haunting",
        "generation": None,
        "effect": "Haunting",
    }
    stored: list[dict] = []

    def _capture_store(_kind: str, _slug: str, payload: dict) -> None:
        stored.append(payload)

    monkeypatch.setattr(pokeapi_assets, "_ability_effect_from_ptu_csv", lambda _name: "PTU fallback text")
    monkeypatch.setattr(pokeapi_assets, "_cached_meta", lambda *_args, **_kwargs: dict(cached))
    monkeypatch.setattr(pokeapi_assets, "_store_meta", _capture_store)

    meta = pokeapi_assets.ability_metadata("Haunting")

    assert meta is not None
    assert meta["effect"] == "PTU fallback text"
    assert meta["source"] == "ptu_csv"
    assert stored


def test_ability_metadata_prefers_ptu_effect_over_pokeapi_effect(monkeypatch) -> None:
    payload = {
        "id": 91,
        "name": "adaptability",
        "generation": {"name": "generation-iv"},
        "effect_entries": [
            {
                "language": {"name": "en"},
                "short_effect": "Boosts same-type moves.",
            }
        ],
    }
    monkeypatch.setattr(pokeapi_assets, "_ability_effect_from_ptu_csv", lambda _name: "PTU adaptability text")
    monkeypatch.setattr(pokeapi_assets, "_cached_meta", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pokeapi_assets, "_request_json", lambda *_args, **_kwargs: payload)
    monkeypatch.setattr(pokeapi_assets, "_store_meta", lambda *_args, **_kwargs: None)

    meta = pokeapi_assets.ability_metadata("Adaptability")

    assert meta is not None
    assert meta["id"] == 91
    assert meta["effect"] == "PTU adaptability text"
    assert meta["source"] == "ptu_csv"


def test_cry_path_prefers_local_pack_dir(monkeypatch, tmp_path: Path) -> None:
    cries = tmp_path / "cries"
    cries.mkdir(parents=True, exist_ok=True)
    local = cries / "AEGISLASH.ogg"
    local.write_bytes(b"OggS")

    monkeypatch.setenv("AUTO_PTU_LOCAL_CRY_DIRS", str(cries))
    monkeypatch.setattr(pokeapi_assets, "_local_cry_index", None)
    monkeypatch.setattr(pokeapi_assets, "_request_json", lambda *_args, **_kwargs: None)

    resolved = pokeapi_assets.cry_path("Aegislash")

    assert resolved is not None
    assert resolved.resolve() == local.resolve()


def test_item_icon_path_prefers_local_pack_dir(monkeypatch, tmp_path: Path) -> None:
    icons = tmp_path / "items"
    icons.mkdir(parents=True, exist_ok=True)
    local = icons / "BLACKAUGURITE.png"
    local.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setenv("AUTO_PTU_LOCAL_ITEM_ICON_DIRS", str(icons))
    monkeypatch.setattr(pokeapi_assets, "_local_item_index", None)
    monkeypatch.setattr(pokeapi_assets, "_request_json", lambda *_args, **_kwargs: None)

    resolved = pokeapi_assets.item_icon_path("Black Augurite")

    assert resolved is not None
    assert resolved.resolve() == local.resolve()
