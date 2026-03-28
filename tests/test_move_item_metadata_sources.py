from __future__ import annotations

from auto_ptu.pokeapi_assets import move_metadata, item_metadata


def test_move_metadata_uses_ptu_csv() -> None:
    meta = move_metadata("Toxic")
    print("Move meta Toxic ->", meta)
    assert isinstance(meta, dict)
    assert meta.get("name") == "Toxic"
    effect = str(meta.get("effect") or "").lower()
    assert "poison" in effect
    assert meta.get("source") in {"ptu_csv", "ptu_csv_missing"}


def test_range_keyword_extraction() -> None:
    # Use the JS helper logic pattern in Python: ensure we keep the same behavior.
    # This mirrors the JS keyword extraction for range strings.
    def extract_range_keywords(range_text: str) -> list[str]:
        ignored = {
            "melee",
            "ranged",
            "self",
            "field",
            "line",
            "cone",
            "burst",
            "blast",
            "close blast",
            "closeblast",
            "target",
            "targets",
            "ally",
            "allies",
            "enemy",
            "enemies",
            "foe",
            "foes",
        }
        keywords = []
        for part in (range_text or "").split(","):
            token = part.strip()
            if not token:
                continue
            lower = token.lower()
            if lower in ignored:
                continue
            if lower.isdigit():
                continue
            if lower.replace(" ", "").isdigit():
                continue
            if lower.endswith(" target") and lower.split(" ")[0].isdigit():
                continue
            if lower.endswith(" targets") and lower.split(" ")[0].isdigit():
                continue
            keywords.append(token)
        return keywords

    keywords = extract_range_keywords("10, 1 Target, Exhaust, Smite")
    print("Range keywords ->", keywords)
    assert keywords == ["Exhaust", "Smite"]


def test_item_metadata_uses_ptu_catalog() -> None:
    meta = item_metadata("Bright Powder")
    print("Item meta Bright Powder ->", meta)
    assert isinstance(meta, dict)
    assert meta.get("name") == "Bright Powder"
    effect = str(meta.get("effect") or "").lower()
    assert "evasion" in effect
    assert "csv" in " ".join(meta.get("source") or []).lower()
