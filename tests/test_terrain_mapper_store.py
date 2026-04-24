from __future__ import annotations

import json
from pathlib import Path

from auto_ptu.api.terrain_mapper_store import TerrainMapperStore


def _starter_fixture(root: Path) -> Path:
    starter = root / "starter"
    (starter / "records").mkdir(parents=True)
    (starter / "images").mkdir(parents=True)
    (starter / "records" / "starter-map.json").write_text(
        json.dumps({"id": "starter-map", "name": "Starter Map", "grid": {"width": 4, "height": 3, "tiles": []}}),
        encoding="utf-8",
    )
    (starter / "images" / "starter.png").write_bytes(b"png-bytes")
    (starter / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "starter-map",
                    "name": "Starter Map",
                    "record": "starter-map.json",
                    "image": "starter.png",
                    "tags": ["starter"],
                }
            ]
        ),
        encoding="utf-8",
    )
    return starter


def test_terrain_mapper_store_bootstraps_starter_maps(tmp_path: Path):
    starter = _starter_fixture(tmp_path)
    store = TerrainMapperStore(tmp_path / "terrain_maps", starter_dir=starter)

    maps = store.list_maps()
    assert len(maps) == 1
    assert maps[0]["id"] == "starter-map"
    assert (store.records_dir / "starter-map.json").exists()
    assert (store.images_dir / "starter.png").exists()


def test_terrain_mapper_store_save_map_updates_profile_knowledge(tmp_path: Path):
    store = TerrainMapperStore(tmp_path / "terrain_maps")
    profile = store.save_profile({"name": "Forest Tiles", "category": "forest"})

    record = store.save_map(
        {
            "name": "Blackleaf Atlas",
            "profile_id": profile["id"],
            "atlas": {
                "grid": {"width": 2, "height": 1, "offset_x": 0, "offset_y": 0, "tile_width": 32, "tile_height": 32},
                "tiles": [
                    {
                        "row": 0,
                        "col": 0,
                        "labels": {"surface": "grass", "object": "tree", "height": 1, "hazard": "", "blocks_movement": True, "difficult": True},
                        "feature_vector": [0.1, 0.7, 0.1, 0.5],
                        "tile_image_hash": "hash-a",
                        "tile_crop_data_url": "data:image/png;base64,AAAA",
                        "confirmed_by_user": True,
                        "confidence_before_correction": 0.44,
                    }
                ],
            },
            "segments": [{"name": "North", "row": 0, "col": 0, "width": 1, "height": 1}],
        }
    )

    assert record["grid"]["width"] == 2
    assert record["grid"]["tiles"][0][2] == "grass tree"
    assert record["segments"][0]["name"] == "North"

    updated_profile = store.get_profile(profile["id"])
    assert len(updated_profile["knowledge_examples"]) == 1
    assert updated_profile["knowledge_examples"][0]["label_surface"] == "grass"
    assert updated_profile["stats"]["maps_saved"] == 1
    assert updated_profile["stats"]["confirmed_tiles"] == 1
    assert updated_profile["stats"]["corrections"] == 1


def test_terrain_mapper_store_predicts_with_profile_memory(tmp_path: Path):
    store = TerrainMapperStore(tmp_path / "terrain_maps")
    profile = store.save_profile(
        {
            "name": "Industrial",
            "knowledge_examples": [
                {
                    "map_id": "plant",
                    "row": 0,
                    "col": 0,
                    "feature_vector": [0.8, 0.8, 0.8, 0.6],
                    "tile_image_hash": "hash-1",
                    "labels": {"surface": "industrial", "object": "machine", "height": 0, "hazard": "", "blocks_movement": True, "difficult": False},
                    "confirmed_by_user": True,
                }
            ],
        }
    )

    result = store.predict_tiles(
        {
            "profile_id": profile["id"],
            "tiles": [
                {"row": 0, "col": 0, "feature_vector": [0.8, 0.8, 0.79, 0.61], "labels": {}},
                {"row": 0, "col": 1, "feature_vector": [0.1, 0.1, 0.1, 0.1], "labels": {}},
            ],
            "high_confidence": 0.8,
            "medium_confidence": 0.55,
        }
    )

    first, second = result["predictions"]
    assert first["labels"]["surface"] == "industrial"
    assert first["review_state"] == "low"
    assert second["review_state"] in {"medium", "low"}
    assert result["stats"]["knowledge_examples"] == 1
