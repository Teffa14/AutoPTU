from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text or f"terrain-{uuid4().hex[:8]}"


def _safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _to_float_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    result: list[float] = []
    for item in value:
        try:
            result.append(float(item))
        except Exception:
            result.append(0.0)
    return result


def _normalize_string(value: Any) -> str:
    return str(value or "").strip()


def _normalize_label_bundle(value: Any) -> dict:
    raw = _safe_dict(value)
    movement = _normalize_string(raw.get("movement")) or ("blocked" if raw.get("blocks_movement") else "difficult" if raw.get("difficult") else "open")
    visibility = _normalize_string(raw.get("visibility")) or ("blocks_los" if raw.get("blocks_los") else "clear")
    cover = _normalize_string(raw.get("cover")) or "none"
    structure = _normalize_string(raw.get("structure"))
    prop = _normalize_string(raw.get("prop"))
    object_label = _normalize_string(raw.get("object")) or structure or prop
    hazards = {}
    raw_hazards = raw.get("hazards")
    if isinstance(raw_hazards, dict):
        hazards = {str(key).strip(): max(0, int(value or 0)) for key, value in raw_hazards.items() if str(key).strip() and int(value or 0) > 0}
    primary_hazard = _normalize_string(raw.get("hazard")) or next(iter(hazards.keys()), "")
    if primary_hazard and primary_hazard not in hazards:
        hazards[primary_hazard] = 1
    traps = {}
    raw_traps = raw.get("traps")
    if isinstance(raw_traps, dict):
        traps = {str(key).strip(): max(0, int(value or 0)) for key, value in raw_traps.items() if str(key).strip() and int(value or 0) > 0}
    barriers = [entry for entry in _safe_list(raw.get("barriers")) if isinstance(entry, dict)]
    frozen_domain = [entry for entry in _safe_list(raw.get("frozen_domain")) if isinstance(entry, dict)]
    trap_sources = {str(key).strip(): value for key, value in _safe_dict(raw.get("trap_sources")).items() if str(key).strip() and isinstance(value, dict)}
    return {
        "surface": _normalize_string(raw.get("surface")),
        "structure": structure,
        "prop": prop,
        "object": object_label,
        "height": max(0, int(raw.get("height") or 0)),
        "hazard": primary_hazard,
        "hazards": hazards,
        "traps": traps,
        "barriers": barriers,
        "frozen_domain": frozen_domain,
        "trap_sources": trap_sources,
        "movement": movement,
        "visibility": visibility,
        "cover": cover,
        "standable": bool(raw.get("standable", True)),
        "blocks_movement": bool(raw.get("blocks_movement", False)) or movement == "blocked",
        "difficult": bool(raw.get("difficult", False)) or movement == "difficult",
        "blocks_los": bool(raw.get("blocks_los", False)) or visibility == "blocks_los",
    }


def _bundle_signature(labels: dict) -> str:
    normalized = _normalize_label_bundle(labels)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _decode_data_url(data_url: str) -> tuple[str, bytes]:
    match = re.match(
        r"^data:image/(?P<kind>png|jpeg|jpg);base64,(?P<data>.+)$",
        str(data_url or "").strip(),
        re.IGNORECASE,
    )
    if not match:
        raise ValueError("Invalid terrain image payload")
    kind = str(match.group("kind") or "png").lower()
    binary = base64.b64decode(match.group("data"))
    return kind, binary


def _normalize_distance(value: float) -> float:
    return max(0.0, min(1.0, value))


def _feature_distance(a: list[float], b: list[float]) -> float:
    length = max(len(a), len(b))
    if length <= 0:
        return 1.0
    total = 0.0
    for idx in range(length):
        av = a[idx] if idx < len(a) else 0.0
        bv = b[idx] if idx < len(b) else 0.0
        total += (av - bv) ** 2
    return math.sqrt(total / length)


def _neighbor_summary(value: Any) -> dict:
    raw = _safe_dict(value)
    return {
        "surface_counts": _safe_dict(raw.get("surface_counts")),
        "hazard_counts": _safe_dict(raw.get("hazard_counts")),
        "blocking_neighbors": int(raw.get("blocking_neighbors") or 0),
    }


@dataclass
class TerrainMapperStore:
    root_dir: Path
    starter_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        self.root_dir = Path(self.root_dir)
        self.maps_dir = self.root_dir
        self.images_dir = self.maps_dir / "images"
        self.records_dir = self.maps_dir / "records"
        self.profiles_dir = self.maps_dir / "profiles"
        self.map_manifest_path = self.maps_dir / "manifest.json"
        self.profile_manifest_path = self.profiles_dir / "manifest.json"
        self.ensure_store()

    def ensure_store(self) -> None:
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        if not self.profile_manifest_path.exists():
            self.profile_manifest_path.write_text("[]", encoding="utf-8")
        if self.starter_dir:
            self._bootstrap_starter_maps()
        if not self.map_manifest_path.exists():
            self.map_manifest_path.write_text("[]", encoding="utf-8")

    def _bootstrap_starter_maps(self) -> None:
        starter_dir = Path(self.starter_dir)
        starter_manifest = starter_dir / "manifest.json"
        if not starter_manifest.exists():
            return
        try:
            starter_entries = json.loads(starter_manifest.read_text(encoding="utf-8-sig"))
        except Exception:
            starter_entries = []
        existing_entries = {
            _normalize_string(entry.get("id")): dict(entry)
            for entry in self._load_manifest(self.map_manifest_path)
            if isinstance(entry, dict) and _normalize_string(entry.get("id"))
        }
        for entry in starter_entries if isinstance(starter_entries, list) else []:
            if not isinstance(entry, dict):
                continue
            entry_id = _normalize_string(entry.get("id"))
            if not entry_id:
                continue
            record_name = _normalize_string(entry.get("record"))
            image_name = _normalize_string(entry.get("image"))
            if record_name:
                src_record = starter_dir / "records" / record_name
                dst_record = self.records_dir / record_name
                if src_record.exists() and not dst_record.exists():
                    dst_record.write_text(src_record.read_text(encoding="utf-8"), encoding="utf-8")
            if image_name:
                src_image = starter_dir / "images" / image_name
                dst_image = self.images_dir / image_name
                if src_image.exists() and not dst_image.exists():
                    dst_image.write_bytes(src_image.read_bytes())
            existing_entries.setdefault(entry_id, dict(entry))
        merged_entries = sorted(existing_entries.values(), key=lambda item: _normalize_string(item.get("name")).lower())
        self.map_manifest_path.write_text(json.dumps(merged_entries, indent=2), encoding="utf-8")

    def _load_manifest(self, path: Path) -> list[dict]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    def _write_manifest(self, path: Path, entries: list[dict]) -> None:
        path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def _record_path(self, map_id: str) -> Path:
        return self.records_dir / f"{map_id}.json"

    def _profile_path(self, profile_id: str) -> Path:
        return self.profiles_dir / f"{profile_id}.json"

    def list_maps(self) -> list[dict]:
        return [dict(entry) for entry in self._load_manifest(self.map_manifest_path) if isinstance(entry, dict)]

    def list_profiles(self) -> list[dict]:
        return [dict(entry) for entry in self._load_manifest(self.profile_manifest_path) if isinstance(entry, dict)]

    def profile_summary(self, profile: dict) -> dict:
        return self._profile_summary(profile)

    def get_map(self, map_id: str) -> dict:
        path = self._record_path(map_id)
        if not path.exists():
            raise FileNotFoundError("Terrain map not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def get_profile(self, profile_id: str) -> dict:
        path = self._profile_path(profile_id)
        if not path.exists():
            raise FileNotFoundError("Terrain profile not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def save_profile(self, payload: Dict[str, Any]) -> dict:
        self.ensure_store()
        name = _normalize_string(payload.get("name"))
        if not name:
            raise ValueError("Profile name is required")
        existing_id = _normalize_string(payload.get("id"))
        profile_id = _slugify(existing_id or name)
        path = self._profile_path(profile_id)
        current = {}
        if path.exists():
            current = self.get_profile(profile_id)
        created_at = _normalize_string(current.get("created_at")) or _utc_now()
        profile = {
            "id": profile_id,
            "name": name,
            "description": _normalize_string(payload.get("description")),
            "category": _normalize_string(payload.get("category")),
            "tags": [str(tag).strip() for tag in _safe_list(payload.get("tags")) if str(tag).strip()],
            "created_at": created_at,
            "updated_at": _utc_now(),
            "knowledge_examples": self._normalize_knowledge_examples(payload.get("knowledge_examples") or current.get("knowledge_examples")),
            "stats": self._safe_profile_stats(payload.get("stats") or current.get("stats")),
        }
        path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        manifest = [entry for entry in self.list_profiles() if _normalize_string(entry.get("id")) != profile_id]
        manifest.append(self._profile_summary(profile))
        manifest.sort(key=lambda entry: _normalize_string(entry.get("name")).lower())
        self._write_manifest(self.profile_manifest_path, manifest)
        return profile

    def save_map(self, payload: Dict[str, Any]) -> dict:
        self.ensure_store()
        name = _normalize_string(payload.get("name"))
        if not name:
            raise ValueError("Terrain map name is required")
        existing_id = _normalize_string(payload.get("id"))
        map_id = _slugify(existing_id or name)
        image_name = _normalize_string(payload.get("image_name")) or f"{map_id}.png"
        image_data_url = payload.get("image_data_url")
        if image_data_url:
            image_name = self._save_image(image_name, str(image_data_url))
        existing = {}
        path = self._record_path(map_id)
        if path.exists():
            existing = self.get_map(map_id)
        atlas = self._normalize_atlas(payload.get("atlas") or existing.get("atlas"))
        segments = self._normalize_segments(payload.get("segments") or existing.get("segments"))
        grid = payload.get("grid") if isinstance(payload.get("grid"), dict) else existing.get("grid")
        if not isinstance(grid, dict):
            grid = self._derive_grid_from_atlas(atlas)
        record = {
            "id": map_id,
            "name": name,
            "profile_id": _normalize_string(payload.get("profile_id") or existing.get("profile_id")),
            "image": image_name if (self.images_dir / image_name).exists() else existing.get("image"),
            "image_meta": self._normalize_image_meta(payload.get("image_meta") or existing.get("image_meta")),
            "tags": [str(tag).strip() for tag in _safe_list(payload.get("tags")) if str(tag).strip()],
            "notes": _normalize_string(payload.get("notes")),
            "atlas": atlas,
            "segments": segments,
            "grid": grid,
            "created_at": _normalize_string(existing.get("created_at")) or _utc_now(),
            "updated_at": _utc_now(),
        }
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        self._update_profile_knowledge(record)
        manifest = [entry for entry in self.list_maps() if _normalize_string(entry.get("id")) != map_id]
        manifest.append(self._map_summary(record))
        manifest.sort(key=lambda entry: _normalize_string(entry.get("name")).lower())
        self._write_manifest(self.map_manifest_path, manifest)
        return record

    def predict_tiles(self, payload: Dict[str, Any]) -> dict:
        profile_id = _normalize_string(payload.get("profile_id"))
        tiles = [self._normalize_tile_payload(entry) for entry in _safe_list(payload.get("tiles"))]
        extra_examples = self._normalize_knowledge_examples(payload.get("examples"))
        knowledge = self._collect_knowledge(profile_id, extra_examples)
        high_cutoff = float(payload.get("high_confidence") or 0.82)
        medium_cutoff = float(payload.get("medium_confidence") or 0.58)
        predictions: list[dict] = []
        counts = {"high": 0, "medium": 0, "low": 0, "known": 0}
        for tile in tiles:
            if tile["confirmed_by_user"] and self._has_labels(tile["labels"]):
                counts["known"] += 1
                predictions.append(
                    {
                        "row": tile["row"],
                        "col": tile["col"],
                        "labels": tile["labels"],
                        "confidence": 1.0,
                        "review_state": "confirmed",
                        "status": "confirmed",
                        "source": "user",
                        "matches": [],
                    }
                )
                continue
            prediction = self._predict_one(tile, knowledge, high_cutoff, medium_cutoff)
            counts[prediction["review_state"]] += 1
            predictions.append(prediction)
        return {
            "predictions": predictions,
            "stats": {
                "knowledge_examples": len(knowledge),
                "tiles_considered": len(tiles),
                "counts": counts,
                "high_confidence": high_cutoff,
                "medium_confidence": medium_cutoff,
            },
        }

    def _save_image(self, image_name: str, image_data_url: str) -> str:
        kind, binary = _decode_data_url(image_data_url)
        suffix = ".jpg" if kind in {"jpg", "jpeg"} else ".png"
        stem = Path(image_name).stem or _slugify(image_name)
        normalized_name = f"{stem}{suffix}"
        (self.images_dir / normalized_name).write_bytes(binary)
        return normalized_name

    def _profile_summary(self, profile: dict) -> dict:
        knowledge_examples = self._normalize_knowledge_examples(profile.get("knowledge_examples"))
        return {
            "id": profile["id"],
            "name": profile["name"],
            "category": profile.get("category") or "",
            "tags": list(profile.get("tags") or []),
            "example_count": len(knowledge_examples),
            "updated_at": profile.get("updated_at") or "",
        }

    def _map_summary(self, record: dict) -> dict:
        atlas = self._normalize_atlas(record.get("atlas"))
        return {
            "id": record["id"],
            "name": record["name"],
            "image": record.get("image"),
            "profile_id": record.get("profile_id") or "",
            "tags": list(record.get("tags") or []),
            "annotated_tiles": sum(1 for tile in atlas["tiles"] if self._has_labels(tile["labels"])),
            "review_tiles": sum(1 for tile in atlas["tiles"] if tile.get("review_state") in {"medium", "low"}),
            "segment_count": len(record.get("segments") or []),
            "updated_at": record.get("updated_at") or "",
        }

    def _safe_profile_stats(self, value: Any) -> dict:
        raw = _safe_dict(value)
        return {
            "maps_saved": int(raw.get("maps_saved") or 0),
            "confirmed_tiles": int(raw.get("confirmed_tiles") or 0),
            "corrections": int(raw.get("corrections") or 0),
        }

    def _normalize_image_meta(self, value: Any) -> dict:
        raw = _safe_dict(value)
        return {
            "width": int(raw.get("width") or 0),
            "height": int(raw.get("height") or 0),
            "source_name": _normalize_string(raw.get("source_name")),
        }

    def _normalize_segments(self, value: Any) -> list[dict]:
        items = []
        for entry in _safe_list(value):
            if not isinstance(entry, dict):
                continue
            items.append(
                {
                    "id": _normalize_string(entry.get("id")) or _slugify(entry.get("name") or "segment"),
                    "name": _normalize_string(entry.get("name")) or "Battlefield",
                    "row": max(0, int(entry.get("row") or 0)),
                    "col": max(0, int(entry.get("col") or 0)),
                    "width": max(1, int(entry.get("width") or 1)),
                    "height": max(1, int(entry.get("height") or 1)),
                }
            )
        return items

    def _normalize_atlas(self, value: Any) -> dict:
        raw = _safe_dict(value)
        grid = _safe_dict(raw.get("grid"))
        width = max(1, int(grid.get("width") or raw.get("width") or 15))
        height = max(1, int(grid.get("height") or raw.get("height") or 10))
        tiles = [self._normalize_tile_payload(entry) for entry in _safe_list(raw.get("tiles"))]
        return {
            "grid": {
                "width": width,
                "height": height,
                "offset_x": float(grid.get("offset_x") or 0.0),
                "offset_y": float(grid.get("offset_y") or 0.0),
                "tile_width": float(grid.get("tile_width") or 0.0),
                "tile_height": float(grid.get("tile_height") or 0.0),
            },
            "tiles": tiles,
            "review_rules": {
                "high_confidence": float(_safe_dict(raw.get("review_rules")).get("high_confidence") or 0.82),
                "medium_confidence": float(_safe_dict(raw.get("review_rules")).get("medium_confidence") or 0.58),
            },
        }

    def _normalize_tile_payload(self, value: Any) -> dict:
        raw = _safe_dict(value)
        labels = _normalize_label_bundle(raw.get("labels"))
        crop_data_url = _normalize_string(raw.get("tile_crop_data_url"))
        tile_hash = _normalize_string(raw.get("tile_image_hash"))
        if crop_data_url and not tile_hash:
            try:
                _, binary = _decode_data_url(crop_data_url)
                tile_hash = hashlib.sha256(binary).hexdigest()
            except Exception:
                tile_hash = ""
        confidence = float(raw.get("confidence") or 0.0)
        confidence_before = float(raw.get("confidence_before_correction") or confidence or 0.0)
        return {
            "row": max(0, int(raw.get("row") or 0)),
            "col": max(0, int(raw.get("col") or 0)),
            "labels": labels,
            "feature_vector": _to_float_list(raw.get("feature_vector")),
            "tile_image_hash": tile_hash,
            "tile_crop_data_url": crop_data_url,
            "confirmed_by_user": bool(raw.get("confirmed_by_user", False)),
            "source": _normalize_string(raw.get("source")) or ("user" if raw.get("confirmed_by_user") else "prediction"),
            "status": _normalize_string(raw.get("status")) or "unlabeled",
            "review_state": _normalize_string(raw.get("review_state")) or "low",
            "confidence": _normalize_distance(confidence),
            "confidence_before_correction": _normalize_distance(confidence_before),
            "neighbor_summary": _neighbor_summary(raw.get("neighbor_summary")),
            "final_label": _bundle_signature(labels),
        }

    def _normalize_knowledge_examples(self, value: Any) -> list[dict]:
        examples: list[dict] = []
        for entry in _safe_list(value):
            if not isinstance(entry, dict):
                continue
            labels = _normalize_label_bundle(entry.get("labels") or entry)
            examples.append(
                {
                    "example_id": _normalize_string(entry.get("example_id")) or uuid4().hex,
                    "map_id": _normalize_string(entry.get("map_id")),
                    "profile_id": _normalize_string(entry.get("profile_id")),
                    "row": max(0, int(entry.get("row") or 0)),
                    "col": max(0, int(entry.get("col") or 0)),
                    "tile_image_hash": _normalize_string(entry.get("tile_image_hash")),
                    "tile_crop_data_url": _normalize_string(entry.get("tile_crop_data_url")),
                    "feature_vector": _to_float_list(entry.get("feature_vector")),
                    "neighbor_summary": _neighbor_summary(entry.get("neighbor_summary")),
                    "labels": labels,
                    "label_surface": labels["surface"],
                    "label_structure": labels["structure"],
                    "label_prop": labels["prop"],
                    "label_object": labels["object"],
                    "label_height": labels["height"],
                    "label_hazard": labels["hazard"],
                    "label_hazards": labels["hazards"],
                    "label_traps": labels["traps"],
                    "confirmed_by_user": bool(entry.get("confirmed_by_user", True)),
                    "confidence_before_correction": _normalize_distance(float(entry.get("confidence_before_correction") or 0.0)),
                    "source": _normalize_string(entry.get("source")) or "user",
                    "created_at": _normalize_string(entry.get("created_at")) or _utc_now(),
                }
            )
        return examples

    def _derive_grid_from_atlas(self, atlas: dict) -> dict:
        blockers: list[list[int]] = []
        tiles: list[list[Any]] = []
        for tile in atlas["tiles"]:
            labels = tile["labels"]
            surface = labels["surface"]
            primary_feature = labels["structure"] or labels["prop"] or labels["object"]
            type_name = " ".join(part for part in [surface, primary_feature] if part).strip()
            hazards = labels["hazards"] or ({labels["hazard"]: 1} if labels["hazard"] else None)
            traps = labels["traps"] or None
            barriers = labels["barriers"] or None
            frozen_domain = labels["frozen_domain"] or None
            trap_sources = labels["trap_sources"] or None
            height = labels["height"] if labels["height"] > 0 else None
            difficult = labels["difficult"] or None
            obstacle = labels["blocks_movement"] or None
            if obstacle:
                blockers.append([tile["col"], tile["row"]])
            if type_name or hazards or height or difficult or obstacle:
                tiles.append([tile["col"], tile["row"], type_name, hazards, traps, barriers, frozen_domain, trap_sources, height, difficult, obstacle])
        return {
            "width": atlas["grid"]["width"],
            "height": atlas["grid"]["height"],
            "blockers": blockers,
            "tiles": tiles,
            "map": {
                "source": "terrain-mapper",
                "annotation_workflow": True,
                "grid_alignment": dict(atlas["grid"]),
            },
        }

    def _collect_knowledge(self, profile_id: str, extra_examples: list[dict]) -> list[dict]:
        knowledge = []
        if profile_id:
            try:
                profile = self.get_profile(profile_id)
                knowledge.extend(self._normalize_knowledge_examples(profile.get("knowledge_examples")))
            except FileNotFoundError:
                pass
        knowledge.extend(extra_examples)
        result = []
        for example in knowledge:
            if not self._has_labels(example["labels"]):
                continue
            if not example["feature_vector"]:
                continue
            result.append(example)
        return result

    def _has_labels(self, labels: dict) -> bool:
        return bool(
            labels.get("surface")
            or labels.get("structure")
            or labels.get("prop")
            or labels.get("object")
            or labels.get("hazard")
            or labels.get("hazards")
            or labels.get("traps")
            or labels.get("barriers")
            or labels.get("frozen_domain")
            or labels.get("height")
            or labels.get("blocks_movement")
            or labels.get("difficult")
            or labels.get("cover") not in (None, "", "none")
        )

    def _predict_one(self, tile: dict, knowledge: list[dict], high_cutoff: float, medium_cutoff: float) -> dict:
        if not tile["feature_vector"] or not knowledge:
            return {
                "row": tile["row"],
                "col": tile["col"],
                "labels": tile["labels"],
                "confidence": 0.0,
                "review_state": "low",
                "status": "needs_review",
                "source": "insufficient-knowledge",
                "matches": [],
            }
        ranked = []
        for example in knowledge:
            distance = _feature_distance(tile["feature_vector"], example["feature_vector"])
            score = 1.0 / (1.0 + distance * 6.0)
            ranked.append((score, distance, example))
        ranked.sort(key=lambda item: item[1])
        top = ranked[:5]
        total_weight = sum(item[0] for item in top) or 1.0
        by_signature: dict[str, dict] = {}
        for score, distance, example in top:
            signature = _bundle_signature(example["labels"])
            bucket = by_signature.setdefault(
                signature,
                {"weight": 0.0, "distance": 0.0, "labels": example["labels"], "examples": []},
            )
            bucket["weight"] += score
            bucket["distance"] += distance
            bucket["examples"].append(example)
        winner = max(by_signature.values(), key=lambda item: item["weight"])
        winner_weight = float(winner["weight"])
        winner_distance = float(winner["distance"]) / max(1, len(winner["examples"]))
        agreement = winner_weight / total_weight
        distance_confidence = max(0.0, 1.0 - min(1.0, winner_distance))
        confidence = _normalize_distance((agreement * 0.65) + (distance_confidence * 0.35))
        distinct_signatures = max(1, len(by_signature))
        supporting_examples = len(winner["examples"])
        knowledge_size = len(knowledge)
        # Stay conservative with sparse memory. A learning annotation tool should ask
        # back early rather than pretending one or two examples are enough to trust.
        if knowledge_size <= 1:
            confidence = min(confidence, max(0.0, medium_cutoff - 0.2))
        elif knowledge_size <= 3:
            confidence = min(confidence, max(0.0, medium_cutoff - 0.05))
        elif knowledge_size <= 6:
            confidence = min(confidence, max(0.0, high_cutoff - 0.05))
        if supporting_examples <= 1 and distinct_signatures > 1:
            confidence = min(confidence, max(0.0, medium_cutoff - 0.03))
        if confidence >= high_cutoff:
            review_state = "high"
            status = "predicted"
        elif confidence >= medium_cutoff:
            review_state = "medium"
            status = "needs_review"
        else:
            review_state = "low"
            status = "needs_review"
        matches = []
        for score, distance, example in top[:3]:
            matches.append(
                {
                    "map_id": example.get("map_id") or "",
                    "row": example.get("row") or 0,
                    "col": example.get("col") or 0,
                    "distance": round(distance, 4),
                    "score": round(score, 4),
                    "labels": example["labels"],
                }
            )
        return {
            "row": tile["row"],
            "col": tile["col"],
            "labels": winner["labels"],
            "confidence": round(confidence, 4),
            "review_state": review_state,
            "status": status,
            "source": "profile-memory",
            "matches": matches,
        }

    def _update_profile_knowledge(self, record: dict) -> None:
        profile_id = _normalize_string(record.get("profile_id"))
        if not profile_id:
            return
        try:
            profile = self.get_profile(profile_id)
        except FileNotFoundError:
            return
        knowledge = self._normalize_knowledge_examples(profile.get("knowledge_examples"))
        index = {
            (
                _normalize_string(entry.get("tile_image_hash")),
                _bundle_signature(entry.get("labels")),
            ): entry
            for entry in knowledge
            if _normalize_string(entry.get("tile_image_hash"))
        }
        confirmed_tiles = 0
        corrections = 0
        for tile in self._normalize_atlas(record.get("atlas"))["tiles"]:
            if not tile["confirmed_by_user"] or not self._has_labels(tile["labels"]):
                continue
            if not tile["feature_vector"]:
                continue
            confirmed_tiles += 1
            if tile["confidence_before_correction"] < 0.999:
                corrections += 1
            key = (tile["tile_image_hash"], _bundle_signature(tile["labels"]))
            index[key] = {
                "example_id": uuid4().hex,
                "map_id": record["id"],
                "profile_id": profile_id,
                "row": tile["row"],
                "col": tile["col"],
                "tile_image_hash": tile["tile_image_hash"],
                "tile_crop_data_url": tile.get("tile_crop_data_url") or "",
                "feature_vector": tile["feature_vector"],
                "neighbor_summary": tile["neighbor_summary"],
                "labels": tile["labels"],
                "label_surface": tile["labels"]["surface"],
                "label_structure": tile["labels"]["structure"],
                "label_prop": tile["labels"]["prop"],
                "label_object": tile["labels"]["object"],
                "label_height": tile["labels"]["height"],
                "label_hazard": tile["labels"]["hazard"],
                "label_hazards": tile["labels"]["hazards"],
                "label_traps": tile["labels"]["traps"],
                "confirmed_by_user": True,
                "confidence_before_correction": tile["confidence_before_correction"],
                "source": tile["source"],
                "created_at": _utc_now(),
            }
        profile["knowledge_examples"] = list(index.values())
        stats = self._safe_profile_stats(profile.get("stats"))
        stats["maps_saved"] += 1
        stats["confirmed_tiles"] += confirmed_tiles
        stats["corrections"] += corrections
        profile["stats"] = stats
        profile["updated_at"] = _utc_now()
        self._profile_path(profile_id).write_text(json.dumps(profile, indent=2), encoding="utf-8")
        manifest = [entry for entry in self.list_profiles() if _normalize_string(entry.get("id")) != profile_id]
        manifest.append(self._profile_summary(profile))
        manifest.sort(key=lambda entry: _normalize_string(entry.get("name")).lower())
        self._write_manifest(self.profile_manifest_path, manifest)
