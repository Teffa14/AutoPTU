from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"C:\Users\tefa1\Downloads\PTU_Maps_Extracted\PTU Maps")
STARTER_DIR = ROOT / "auto_ptu" / "data" / "terrain_maps" / "starter"
IMAGES_DIR = STARTER_DIR / "images"
RECORDS_DIR = STARTER_DIR / "records"
MANIFEST_PATH = STARTER_DIR / "manifest.json"


def tile_entry(x: int, y: int, meta: dict) -> list:
    return [
        x,
        y,
        meta.get("type"),
        meta.get("hazards"),
        meta.get("traps"),
        meta.get("barriers"),
        meta.get("frozen_domain"),
        meta.get("trap_sources"),
        meta.get("height"),
        meta.get("difficult"),
        meta.get("obstacle"),
    ]


class GridBuilder:
    def __init__(self, width: int, height: int, default_type: str):
        self.width = width
        self.height = height
        self.tiles: dict[tuple[int, int], dict] = {}
        for y in range(height):
            for x in range(width):
                self.tiles[(x, y)] = {"type": default_type}

    def set(self, x: int, y: int, **meta):
        self.tiles[(x, y)] = {**self.tiles.get((x, y), {}), **meta}

    def rect(self, x1: int, y1: int, x2: int, y2: int, **meta):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.set(x, y, **meta)

    def points(self, coords: list[tuple[int, int]], **meta):
        for x, y in coords:
            self.set(x, y, **meta)

    def blockers(self) -> list[list[int]]:
        result = []
        for (x, y), meta in sorted(self.tiles.items(), key=lambda item: (item[0][1], item[0][0])):
            if meta.get("obstacle"):
                result.append([x, y])
        return result

    def serialise_tiles(self) -> list[list]:
        return [
            tile_entry(x, y, meta)
            for (x, y), meta in sorted(self.tiles.items(), key=lambda item: (item[0][1], item[0][0]))
        ]


def build_agricultural_society() -> dict:
    g = GridBuilder(20, 20, "grass")
    g.rect(0, 0, 19, 0, type="urban fence blocker", height=1, obstacle=True)
    g.rect(0, 9, 10, 9, type="rock ledge blocker", height=1, obstacle=True)
    g.rect(0, 10, 6, 12, type="grass")
    g.rect(8, 10, 19, 19, type="urban wood")
    g.rect(0, 13, 6, 19, type="flower garden difficult", difficult=True)
    g.rect(1, 1, 8, 7, type="sand path")
    for row in (1, 3, 5, 7):
        g.rect(1, row, 8, row, type="flower bed difficult", difficult=True)
    g.points([(4, 5)], type="garden bench blocker", height=1, obstacle=True)
    g.points([(10, 1), (10, 6)], type="stone lantern blocker", height=1, obstacle=True)
    g.rect(11, 1, 19, 8, type="flower garden difficult", difficult=True)
    g.points([(14, 1), (18, 1), (16, 3), (19, 5), (13, 6)], type="tree blocker", height=1, obstacle=True)
    g.points([(11, 5), (12, 5), (10, 4), (15, 5)], type="shrub difficult", difficult=True)
    g.rect(11, 11, 13, 13, type="grass planter difficult", difficult=True)
    g.points([(12, 12)], type="cherry tree blocker", height=1, obstacle=True)
    g.rect(16, 13, 18, 17, type="urban display blocker", height=1, obstacle=True)
    g.points([(15, 14), (15, 17), (18, 12), (19, 12)], type="potted plant blocker", obstacle=True)
    g.rect(0, 13, 4, 14, type="glass display blocker", height=1, obstacle=True)
    g.rect(1, 16, 4, 18, type="flower bed difficult", difficult=True)
    g.rect(5, 16, 6, 18, type="urban wood")
    g.rect(0, 19, 2, 19, type="urban roof blocker", height=1, obstacle=True)
    return {
        "id": "agricultural-society",
        "name": "Agricultural Society",
        "image": "Agricultural Society.png",
        "tags": ["garden", "mixed", "starter"],
        "grid": {
            "width": g.width,
            "height": g.height,
            "blockers": g.blockers(),
            "tiles": g.serialise_tiles(),
            "map": {
                "name": "Agricultural Society",
                "source": "terrain-mapper",
                "starter": True,
                "notes": "Garden society with flower beds, trees, lanterns, and an indoor display hall.",
            },
        },
    }


def build_alleyway() -> dict:
    g = GridBuilder(10, 20, "urban concrete")
    g.rect(0, 0, 1, 19, type="urban building blocker", height=1, obstacle=True)
    g.rect(8, 0, 9, 19, type="urban building blocker", height=1, obstacle=True)
    g.rect(3, 0, 6, 19, type="urban road")
    g.rect(2, 0, 2, 19, type="urban sidewalk")
    g.rect(7, 0, 7, 19, type="urban sidewalk")
    g.rect(3, 0, 6, 1, type="urban truck blocker", height=1, obstacle=True)
    g.points([(3, 4)], type="hydrant blocker", obstacle=True)
    g.points([(2, 2), (2, 3), (2, 7), (2, 8), (2, 9)], type="crate pile blocker", obstacle=True)
    g.points([(7, 2), (7, 3), (7, 4), (7, 10), (7, 15)], type="crate pile blocker", obstacle=True)
    g.points([(6, 7), (6, 8), (7, 7), (7, 8)], type="construction barrier blocker", obstacle=True)
    g.points([(6, 6), (6, 9)], type="barrel blocker", obstacle=True)
    g.points([(2, 14), (7, 14)], type="awning post blocker", obstacle=True)
    g.points([(2, 18), (7, 18)], type="streetlamp blocker", obstacle=True)
    return {
        "id": "alleyway",
        "name": "Alleyway",
        "image": "Alleyway.png",
        "tags": ["urban", "street", "starter"],
        "grid": {
            "width": g.width,
            "height": g.height,
            "blockers": g.blockers(),
            "tiles": g.serialise_tiles(),
            "map": {
                "name": "Alleyway",
                "source": "terrain-mapper",
                "starter": True,
                "notes": "Tight city alley with a central lane, sidewalks, stacked crates, and construction clutter.",
            },
        },
    }


def build_bakery() -> dict:
    g = GridBuilder(20, 10, "urban indoor")
    g.rect(0, 0, 19, 0, type="urban wall blocker", height=1, obstacle=True)
    g.rect(0, 0, 0, 9, type="urban wall blocker", height=1, obstacle=True)
    g.rect(19, 0, 19, 9, type="urban wall blocker", height=1, obstacle=True)
    g.rect(4, 0, 7, 0, type="doorway")
    g.rect(10, 1, 13, 2, type="display case blocker", height=1, obstacle=True)
    g.rect(15, 2, 18, 3, type="service counter blocker", height=1, obstacle=True)
    g.points([(16, 1)], type="flower vase blocker", obstacle=True)
    g.points([(18, 2)], type="register blocker", obstacle=True)
    g.rect(1, 3, 2, 4, type="table blocker", obstacle=True)
    g.points([(1, 2), (2, 2), (1, 5), (2, 5), (0, 3), (0, 4), (3, 3), (3, 4)], type="chair blocker", obstacle=True)
    g.rect(8, 5, 9, 6, type="table blocker", obstacle=True)
    g.points([(8, 4), (9, 4), (8, 7), (9, 7), (7, 5), (7, 6), (10, 5), (10, 6)], type="chair blocker", obstacle=True)
    g.rect(16, 5, 17, 6, type="table blocker", obstacle=True)
    g.points([(16, 4), (17, 4), (16, 7), (17, 7), (15, 5), (15, 6), (18, 5), (18, 6)], type="chair blocker", obstacle=True)
    g.rect(14, 1, 18, 2, type="rug")
    return {
        "id": "bakery",
        "name": "Bakery",
        "image": "Bakery.png",
        "tags": ["indoor", "urban", "starter"],
        "grid": {
            "width": g.width,
            "height": g.height,
            "blockers": g.blockers(),
            "tiles": g.serialise_tiles(),
            "map": {
                "name": "Bakery",
                "source": "terrain-mapper",
                "starter": True,
                "notes": "Compact bakery interior with display cases, service counter, and tightly packed seating.",
            },
        },
    }


def build_campsite() -> dict:
    g = GridBuilder(10, 10, "grass")
    g.points(
        [(2, 1), (2, 2), (0, 3), (1, 3), (2, 3), (0, 4), (1, 4), (0, 5), (0, 6), (8, 1), (8, 2), (8, 3)],
        type="rock ledge blocker",
        height=1,
        obstacle=True,
    )
    g.points([(3, 0), (4, 0), (3, 1), (4, 1), (7, 0), (8, 5), (8, 6), (8, 7), (8, 8), (0, 9), (1, 9)], type="tree blocker", height=1, obstacle=True)
    g.points([(1, 8)], type="tent blocker", height=1, obstacle=True)
    g.points([(4, 3), (5, 3), (7, 4), (8, 4)], type="log blocker", height=1, obstacle=True)
    g.points([(5, 4)], type="campfire", hazards={"fire_hazards": 1})
    g.points([(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (9, 3), (1, 5), (2, 5), (1, 6), (2, 6), (0, 8), (9, 5), (7, 9), (8, 9), (9, 9)], type="brush difficult", difficult=True)
    g.rect(4, 5, 6, 6, type="sand path")
    g.rect(3, 7, 6, 8, type="sand path")
    g.rect(3, 9, 5, 9, type="sand path")
    return {
        "id": "campsite",
        "name": "Campsite",
        "image": "Campsite.png",
        "tags": ["forest", "camp", "starter"],
        "grid": {
            "width": g.width,
            "height": g.height,
            "blockers": g.blockers(),
            "tiles": g.serialise_tiles(),
            "map": {
                "name": "Campsite",
                "source": "terrain-mapper",
                "starter": True,
                "notes": "Small forest campsite with northern cliffs, two fallen logs, a central campfire, southern tent, and a sandy clearing path.",
            },
        },
    }


def build_bleakwood_ruins() -> dict:
    g = GridBuilder(14, 14, "dirt")
    g.rect(0, 0, 3, 1, type="rock ledge blocker", height=1, obstacle=True)
    g.rect(7, 0, 13, 1, type="rock ledge blocker", height=1, obstacle=True)
    g.rect(0, 10, 3, 13, type="rock ledge blocker", height=1, obstacle=True)
    g.rect(12, 0, 13, 6, type="rock ledge blocker", height=1, obstacle=True)
    g.rect(4, 4, 9, 9, type="water difficult", difficult=True)
    g.rect(6, 6, 7, 7, type="dead stump blocker", height=1, obstacle=True)
    g.points([(2, 3), (10, 3), (1, 11), (11, 11)], type="dead stump blocker", height=1, obstacle=True)
    g.points([(8, 5), (3, 10), (9, 12), (5, 12)], type="ruin slab blocker", height=1, obstacle=True)
    g.points([(3, 3), (4, 3), (3, 5), (2, 12), (12, 12), (11, 3)], type="brush difficult", difficult=True)
    g.points([(0, 6), (4, 10), (10, 4), (13, 7)], type="ruin wall blocker", height=1, obstacle=True)
    return {
        "id": "bleakwood-ruins",
        "name": "Bleakwood Ruins",
        "image": "Bleakwood Ruins.png",
        "tags": ["ruins", "swamp", "starter"],
        "grid": {
            "width": g.width,
            "height": g.height,
            "blockers": g.blockers(),
            "tiles": g.serialise_tiles(),
            "map": {
                "name": "Bleakwood Ruins",
                "source": "terrain-mapper",
                "starter": True,
                "notes": "Ruined marsh basin with dead stumps, shallow water, ledges, and scattered broken walls.",
            },
        },
    }


MAP_BUILDERS = [
    ("Agricultural Society.png", "agricultural-society.json", build_agricultural_society),
    ("Alleyway.png", "alleyway.json", build_alleyway),
    ("Bakery.png", "bakery.json", build_bakery),
    ("Campsite.png", "campsite.json", build_campsite),
    ("Bleakwood Ruins.png", "bleakwood-ruins.json", build_bleakwood_ruins),
]


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    manifest_by_id = {entry["id"]: entry for entry in manifest}

    for image_name, record_name, builder in MAP_BUILDERS:
        record = builder()
        shutil.copy2(SOURCE_DIR / image_name, IMAGES_DIR / image_name)
        (RECORDS_DIR / record_name).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        manifest_by_id[record["id"]] = {
            "id": record["id"],
            "name": record["name"],
            "image": image_name,
            "record": record_name,
            "tags": record["tags"],
        }

    ordered = sorted(manifest_by_id.values(), key=lambda entry: entry["name"].lower())
    MANIFEST_PATH.write_text(json.dumps(ordered, indent=4) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
