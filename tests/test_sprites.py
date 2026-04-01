import os

from auto_ptu.sprites import SpriteCache, _fallback_slugs, _needs_sprite_refresh, _slugify, _strip_trainer_prefix_slug


def test_slugify_known_variant_forms() -> None:
    assert _slugify("Nidoran♀") == "nidoran-f"
    assert _slugify("Nidoran♂") == "nidoran-m"
    assert _slugify("Basculegion (Male)") == "basculegion-male"
    assert _slugify("Oricorio (Pa'u)") == "oricorio-pau"
    assert _slugify("Minior (Core)") == "minior-red-core"
    assert _slugify("Enamorus (Therian)") == "enamorus-therian"
    assert _slugify("Necrozma (Dawn Wings)") == "necrozma-dawn-wings"
    assert _slugify("Zacian (Crowned)") == "zacian-crowned"
    assert _slugify("Rotom-N") == "rotom"
    assert _slugify("Minior-Core") == "minior-red-core"
    assert _slugify("Obsideon") == "obsideon"
    assert _slugify("Inteleon") == "inteleon"
    assert _slugify("Indeedee Female") == "indeedee-female"
    assert _slugify("Rotom Wash") == "rotom-wash"
    assert _slugify("Eiscue Noice Face") == "eiscue-noice-face"


def test_slugify_strips_trainer_prefix_labels() -> None:
    assert _slugify("Player 1: Grimer (Alola)") == "grimer-alola"
    assert _slugify("Foe-2: Sizzlipede") == "sizzlipede"


def test_fallback_slugs_drop_trainer_prefix_slug() -> None:
    assert _strip_trainer_prefix_slug("player-1-grimer-alola") == "grimer-alola"
    fallbacks = _fallback_slugs("player-1-grimer-alola")
    assert "grimer" in fallbacks


def test_fallback_slugs_do_not_route_generic_eon_names_to_eevee() -> None:
    assert "eevee" not in _fallback_slugs("draconeon")
    assert "eevee" not in _fallback_slugs("inteleon")
    assert "eevee" not in _fallback_slugs("obsideon")


def test_fallback_slugs_reduce_common_forms_to_base_species() -> None:
    assert "indeedee" in _fallback_slugs("indeedee-female")
    assert "eiscue" in _fallback_slugs("eiscue-noice-face")
    assert "wormadam" in _fallback_slugs("wormadam-trash")
    assert "rotom" in _fallback_slugs("rotom-wash")


def test_sprite_path_prefers_existing_form_fallback(tmp_path) -> None:
    cache = SpriteCache(cache_dir=tmp_path)
    (tmp_path / "minior-red-core.png").write_bytes(b"png")
    assert cache.sprite_path_for("Minior-Core") == "/sprites/minior-red-core.png"


def test_sprite_url_uses_local_pack_fallback(monkeypatch, tmp_path) -> None:
    local_dir = tmp_path / "local-front"
    local_dir.mkdir(parents=True, exist_ok=True)
    (local_dir / "AEGISLASH.png").write_bytes(b"png")
    cache_dir = tmp_path / "cache"
    cache = SpriteCache(cache_dir=cache_dir)
    monkeypatch.setenv("AUTO_PTU_LOCAL_SPRITE_DIRS", str(local_dir))
    from auto_ptu import sprites as sprites_mod
    monkeypatch.setattr(sprites_mod, "_LOCAL_SPRITE_INDEX", {})
    monkeypatch.setattr(sprites_mod, "_LOCAL_SPRITE_INDEX_KEY", ())

    url = cache.sprite_url_for("Aegislash", allow_download=False)

    assert url == "/sprites/aegislash.png"
    assert (cache_dir / "aegislash.png").exists()


def test_sprite_url_prefers_first_local_sprite_dir(monkeypatch, tmp_path) -> None:
    animated_dir = tmp_path / "animated-front"
    static_dir = tmp_path / "static-front"
    animated_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)
    (animated_dir / "ABRA.png").write_bytes(b"animated-sheet")
    (static_dir / "ABRA.png").write_bytes(b"static")
    cache_dir = tmp_path / "cache"
    cache = SpriteCache(cache_dir=cache_dir)
    monkeypatch.setenv("AUTO_PTU_LOCAL_SPRITE_DIRS", os.pathsep.join([str(animated_dir), str(static_dir)]))
    from auto_ptu import sprites as sprites_mod
    monkeypatch.setattr(sprites_mod, "_LOCAL_SPRITE_INDEX", {})
    monkeypatch.setattr(sprites_mod, "_LOCAL_SPRITE_INDEX_KEY", ())

    url = cache.sprite_url_for("Abra", allow_download=False)

    assert url == "/sprites/abra.png"
    assert (cache_dir / "abra.png").read_bytes() == b"animated-sheet"


def test_low_fidelity_form_sprite_cache_gets_refreshed(monkeypatch, tmp_path) -> None:
    from auto_ptu import sprites as sprites_mod

    cache = SpriteCache(cache_dir=tmp_path)
    target = tmp_path / "articuno-galar.png"
    target.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + b"\x00\x00\x00D\x00\x00\x008"  # 68x56
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )
    assert _needs_sprite_refresh("articuno-galar", target)

    payload = {
        "sprites": {
            "front_default": "https://example.com/articuno-galar-front.png",
            "other": {"official-artwork": {"front_default": "https://example.com/articuno-galar-official.png"}},
            "versions": {"generation-viii": {"icons": {"front_default": "https://example.com/articuno-galar-icon.png"}}},
        }
    }

    monkeypatch.setattr(sprites_mod, "_fetch_pokemon_payload", lambda slug: payload if slug == "articuno-galar" else None)

    class _FakeResponse:
        def __init__(self, data: bytes):
            self._data = data

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    called_urls = []

    def _fake_urlopen(request, timeout=10):
        called_urls.append(request.full_url)
        return _FakeResponse(b"real-form-sprite")

    monkeypatch.setattr(sprites_mod.urllib.request, "urlopen", _fake_urlopen)

    assert cache.ensure_sprite_filename("articuno-galar.png")
    assert target.read_bytes() == b"real-form-sprite"
    assert called_urls == ["https://example.com/articuno-galar-front.png"]
