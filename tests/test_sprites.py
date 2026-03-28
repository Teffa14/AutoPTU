from auto_ptu.sprites import SpriteCache, _fallback_slugs, _slugify, _strip_trainer_prefix_slug


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
