"""Generate a trainer feature/edge runtime coverage report.

This turns the raw character creation dataset into an implementation queue by
classifying trainer features and edges against the current runtime surfaces:
- generic TrainerFeatureDispatcher payload execution
- perk hook modules under auto_ptu.rules.hooks.perk_effects
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHARACTER_CREATION = ROOT / "reports" / "character_creation.json"
DEFAULT_PERK_EFFECTS_DIR = ROOT / "auto_ptu" / "rules" / "hooks" / "perk_effects"
DEFAULT_RUNTIME_DIR = ROOT / "auto_ptu" / "rules"
DEFAULT_JSON_OUT = ROOT / "reports" / "trainer_runtime_coverage.json"
DEFAULT_MD_OUT = ROOT / "reports" / "trainer_runtime_coverage.md"
EXPLICIT_CORE_RUNTIME_FEATURES: Set[str] = {
    "awareness",
    "coaching",
    "counter stance",
    "deadly gambit",
    "dive",
    "fearsome display",
    "harrier",
    "immutable mind",
    "iron mind",
    "menace",
    "mettle",
    "mental resistance",
    "glacial defense",
    "glacial ice",
    "gravel before me",
    "gneiss aim",
    "bigger and boulder",
    "tough as schist",
    "pain resistance",
    "polished shine",
    "ambient aura",
    "psychic navigator",
    "psionic sight",
    "quick gymnastics",
    "stamina",
    "survivalist",
    "telepathic warning",
    "deep cold",
    "true steel",
    "traveler",
    "wallrunner",
    "the cold never bothered me anyway",
    "winter is coming",
    "witch hunter",
}


def _normalize_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _normalize_feature_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name or "").strip().lower()).strip("-")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    os.replace(temp_path, path)


def _nonempty_mapping(value: Any) -> bool:
    if isinstance(value, dict):
        return any(v not in (None, "", [], {}) for v in value.values())
    if isinstance(value, list):
        return any(isinstance(entry, dict) and entry for entry in value)
    return False


class _PerkHookVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.perks: Set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id == "register_perk_hook":
            if len(node.args) >= 2:
                perk_name = self._literal_str(node.args[1])
                if perk_name:
                    self.perks.add(_normalize_token(perk_name))
            for kw in node.keywords:
                if kw.arg == "perk":
                    perk_name = self._literal_str(kw.value)
                    if perk_name:
                        self.perks.add(_normalize_token(perk_name))
        self.generic_visit(node)

    @staticmethod
    def _literal_str(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""


class _CoreRuntimeTokenVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.tokens: Set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        if any(isinstance(target, ast.Name) and target.id == "TRAINER_FEATURE_MOVE_GRANTS" for target in node.targets):
            return
        if any(isinstance(target, ast.Name) and target.id == "WEAPONIZED_TRAINER_FEATURE_MOVE_GRANTS" for target in node.targets):
            return
        if any(isinstance(target, ast.Name) and target.id == "feature_name" for target in node.targets):
            return
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and node.target.id in {"TRAINER_FEATURE_MOVE_GRANTS", "WEAPONIZED_TRAINER_FEATURE_MOVE_GRANTS", "feature_name"}:
            return
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            normalized = _normalize_token(node.value)
            if normalized:
                self.tokens.add(normalized)
        self.generic_visit(node)


class _TrainerFeatureMoveGrantVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.feature_names: Set[str] = set()
        self.weaponized_feature_names: Set[str] = set()

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and node.target.id in {"TRAINER_FEATURE_MOVE_GRANTS", "CHOICE_TRAINER_FEATURE_MOVE_GRANTS"}:
            self._collect_from_value(node.value)
        if isinstance(node.target, ast.Name) and node.target.id == "WEAPONIZED_TRAINER_FEATURE_MOVE_GRANTS":
            self._collect_weaponized(node.value)

    def _collect_from_value(self, value: ast.AST | None) -> None:
        if not isinstance(value, ast.Dict):
            return
        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                self.feature_names.add(_normalize_token(key.value))

    def visit_Assign(self, node: ast.Assign) -> None:
        if any(isinstance(target, ast.Name) and target.id in {"TRAINER_FEATURE_MOVE_GRANTS", "CHOICE_TRAINER_FEATURE_MOVE_GRANTS"} for target in node.targets):
            self._collect_from_value(node.value)
        if any(isinstance(target, ast.Name) and target.id == "WEAPONIZED_TRAINER_FEATURE_MOVE_GRANTS" for target in node.targets):
            self._collect_weaponized(node.value)

    def _collect_weaponized(self, value: ast.AST | None) -> None:
        if isinstance(value, (ast.Set, ast.Tuple, ast.List)):
            for elt in value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    self.weaponized_feature_names.add(_normalize_token(elt.value))


def _discover_perk_hooks(perk_effects_dir: Path) -> Set[str]:
    discovered: Set[str] = set()
    if not perk_effects_dir.exists():
        return discovered
    for path in perk_effects_dir.glob("*.py"):
        if path.name.startswith("__"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        visitor = _PerkHookVisitor()
        visitor.visit(tree)
        discovered.update(visitor.perks)
    return discovered


def _discover_runtime_tokens(runtime_dir: Path) -> Set[str]:
    discovered: Set[str] = set()
    if not runtime_dir.exists():
        return discovered
    for path in runtime_dir.rglob("*.py"):
        if any(part.startswith("__") for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        visitor = _CoreRuntimeTokenVisitor()
        visitor.visit(tree)
        discovered.update(visitor.tokens)
    return discovered


class _TrainerFeatureActionRegistryVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.trainer_feature_names: Set[str] = set()
        self.pokemon_feature_names: Set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bucket: Set[str] | None = None
        base_names = {self._base_name(base) for base in node.bases}
        if "TrainerFeatureAction" in base_names:
            bucket = self.trainer_feature_names
        elif "PokemonFeatureAction" in base_names:
            bucket = self.pokemon_feature_names
        if bucket is not None:
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "feature_name":
                        value = self._literal_str(stmt.value)
                        if value:
                            bucket.add(_normalize_token(value))
        self.generic_visit(node)

    @staticmethod
    def _base_name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    @staticmethod
    def _literal_str(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""


def _discover_trainer_feature_action_registry(runtime_dir: Path) -> Dict[str, Set[str]]:
    path = runtime_dir / "battle_state.py"
    if not path.exists():
        return {"trainer": set(), "pokemon": set()}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return {"trainer": set(), "pokemon": set()}
    visitor = _TrainerFeatureActionRegistryVisitor()
    visitor.visit(tree)
    return {
        "trainer": visitor.trainer_feature_names,
        "pokemon": visitor.pokemon_feature_names,
    }


def _discover_trainer_feature_move_grants(runtime_dir: Path) -> Dict[str, Set[str]]:
    path = runtime_dir / "battle_state.py"
    if not path.exists():
        return {"all": set(), "weaponized": set()}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return {"all": set(), "weaponized": set()}
    visitor = _TrainerFeatureMoveGrantVisitor()
    visitor.visit(tree)
    return {"all": visitor.feature_names, "weaponized": visitor.weaponized_feature_names}


@dataclass
class CoverageEntry:
    name: str
    kind: str
    runtime_status: str
    runtime_surface: str
    generic_runtime_ready: bool
    perk_hook_ready: bool
    trainer_action_registry_ready: bool
    pokemon_action_registry_ready: bool
    move_grant_ready: bool
    weaponized_move_grant_ready: bool
    move_grant_rider_ready: bool
    feature_id: str
    frequency: str
    prerequisites: str
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "runtime_status": self.runtime_status,
            "runtime_surface": self.runtime_surface,
            "generic_runtime_ready": self.generic_runtime_ready,
            "perk_hook_ready": self.perk_hook_ready,
            "trainer_action_registry_ready": self.trainer_action_registry_ready,
            "pokemon_action_registry_ready": self.pokemon_action_registry_ready,
            "move_grant_ready": self.move_grant_ready,
            "weaponized_move_grant_ready": self.weaponized_move_grant_ready,
            "move_grant_rider_ready": self.move_grant_rider_ready,
            "feature_id": self.feature_id,
            "frequency": self.frequency,
            "prerequisites": self.prerequisites,
            "notes": list(self.notes),
        }


def _classify_entry(
    entry: Dict[str, Any],
    *,
    kind: str,
    perk_hooks: Set[str],
    runtime_tokens: Set[str],
    trainer_action_registry_features: Set[str],
    pokemon_action_registry_features: Set[str],
    move_grant_features: Set[str],
    weaponized_move_grant_features: Set[str],
) -> CoverageEntry:
    name = str(entry.get("name", "")).strip()
    feature_id = str(entry.get("feature_id", "")).strip() or _normalize_feature_id(name)
    trigger = str(entry.get("trigger", "")).strip()
    effect_payload = entry.get("effect_payload", entry.get("effect"))
    generic_runtime_ready = bool(trigger) and _nonempty_mapping(effect_payload)
    normalized_name = _normalize_token(name)
    normalized_feature_id = _normalize_token(feature_id)
    perk_hook_ready = normalized_name in perk_hooks or normalized_feature_id in perk_hooks
    core_runtime_ready = (
        normalized_name in runtime_tokens
        or normalized_feature_id in runtime_tokens
        or normalized_name in EXPLICIT_CORE_RUNTIME_FEATURES
        or normalized_feature_id in EXPLICIT_CORE_RUNTIME_FEATURES
    )
    trainer_action_registry_ready = normalized_name in trainer_action_registry_features or normalized_feature_id in trainer_action_registry_features
    pokemon_action_registry_ready = normalized_name in pokemon_action_registry_features or normalized_feature_id in pokemon_action_registry_features
    action_registry_ready = trainer_action_registry_ready or pokemon_action_registry_ready
    move_grant_ready = normalized_name in move_grant_features or normalized_feature_id in move_grant_features
    weaponized_move_grant_ready = normalized_name in weaponized_move_grant_features or normalized_feature_id in weaponized_move_grant_features
    move_grant_rider_ready = move_grant_ready and (core_runtime_ready or action_registry_ready or perk_hook_ready)
    runtime_surface = "missing"
    if perk_hook_ready:
        runtime_surface = "perk_hook"
    elif trainer_action_registry_ready:
        runtime_surface = "trainer_action"
    elif pokemon_action_registry_ready:
        runtime_surface = "pokemon_action"
    elif move_grant_rider_ready:
        runtime_surface = "move_grant_rider"
    elif weaponized_move_grant_ready:
        runtime_surface = "weaponized_move_grant"
    elif move_grant_ready:
        runtime_surface = "move_grant"
    elif core_runtime_ready:
        runtime_surface = _core_runtime_surface(entry)
    elif generic_runtime_ready:
        runtime_surface = "generic_runtime"
    notes: List[str] = []
    if not (
        perk_hook_ready
        or core_runtime_ready
        or action_registry_ready
        or move_grant_ready
        or weaponized_move_grant_ready
    ) and not generic_runtime_ready:
        if not trigger:
            notes.append("missing trigger")
        if not _nonempty_mapping(effect_payload):
            notes.append("missing effect payload")
    if not perk_hook_ready and not core_runtime_ready and not action_registry_ready and not move_grant_ready:
        notes.append("no perk hook")
    if perk_hook_ready:
        runtime_status = "perk_hook_ready"
    elif trainer_action_registry_ready:
        runtime_status = "trainer_action_registry_ready"
    elif pokemon_action_registry_ready:
        runtime_status = "pokemon_action_registry_ready"
    elif move_grant_rider_ready:
        runtime_status = "move_grant_rider_ready"
    elif weaponized_move_grant_ready:
        runtime_status = "weaponized_move_grant_ready"
    elif move_grant_ready:
        runtime_status = "move_grant_ready"
    elif core_runtime_ready:
        runtime_status = "core_runtime_ready"
    elif generic_runtime_ready:
        runtime_status = "generic_runtime_ready"
    else:
        runtime_status = "missing_runtime_mapping"
    return CoverageEntry(
        name=name,
        kind=kind,
        runtime_status=runtime_status,
        runtime_surface=runtime_surface,
        generic_runtime_ready=generic_runtime_ready,
        perk_hook_ready=perk_hook_ready,
        trainer_action_registry_ready=trainer_action_registry_ready,
        pokemon_action_registry_ready=pokemon_action_registry_ready,
        move_grant_ready=move_grant_ready,
        weaponized_move_grant_ready=weaponized_move_grant_ready,
        move_grant_rider_ready=move_grant_rider_ready,
        feature_id=feature_id,
        frequency=str(entry.get("frequency", "")).strip(),
        prerequisites=str(entry.get("prerequisites", "")).strip(),
        notes=notes,
    )


def _collect_entries(
    dataset: Dict[str, Any],
    perk_hooks: Set[str],
    runtime_tokens: Set[str],
    trainer_action_registry_features: Set[str],
    pokemon_action_registry_features: Set[str],
    move_grant_features: Set[str],
    weaponized_move_grant_features: Set[str],
) -> List[CoverageEntry]:
    entries: List[CoverageEntry] = []
    trainer = dataset if "features" in dataset else dataset.get("trainer", {})
    for feature in trainer.get("features", []) or []:
        if isinstance(feature, dict) and feature.get("name"):
            entries.append(
                _classify_entry(
                    feature,
                    kind="feature",
                    perk_hooks=perk_hooks,
                    runtime_tokens=runtime_tokens,
                    trainer_action_registry_features=trainer_action_registry_features,
                    pokemon_action_registry_features=pokemon_action_registry_features,
                    move_grant_features=move_grant_features,
                    weaponized_move_grant_features=weaponized_move_grant_features,
                )
            )
    for edge in trainer.get("edges_catalog", trainer.get("edges", [])) or []:
        if isinstance(edge, dict) and edge.get("name"):
            entries.append(
                _classify_entry(
                    edge,
                    kind="edge",
                    perk_hooks=perk_hooks,
                    runtime_tokens=runtime_tokens,
                    trainer_action_registry_features=trainer_action_registry_features,
                    pokemon_action_registry_features=pokemon_action_registry_features,
                    move_grant_features=move_grant_features,
                    weaponized_move_grant_features=weaponized_move_grant_features,
                )
            )
    return sorted(entries, key=lambda item: (item.kind, item.runtime_status, item.name.lower()))


def _core_runtime_surface(entry: Dict[str, Any]) -> str:
    trigger = str(entry.get("trigger", "")).strip().lower()
    frequency = str(entry.get("frequency", "")).strip().lower()
    effects = str(entry.get("effects", "")).strip().lower()
    action_markers = (" ap", "swift", "free action", "standard action", "scene", "trigger:", "at-will", "daily", "eot")
    if trigger:
        return "core_runtime_action"
    if any(marker in frequency for marker in action_markers):
        return "core_runtime_action"
    if "trigger:" in effects:
        return "core_runtime_action"
    return "core_runtime_passive"


def _build_summary(entries: Iterable[CoverageEntry]) -> Dict[str, Any]:
    entries = list(entries)
    summary: Dict[str, Any] = {
        "total": len(entries),
        "features": 0,
        "edges": 0,
        "perk_hook_ready": 0,
        "trainer_action_registry_ready": 0,
        "pokemon_action_registry_ready": 0,
        "move_grant_rider_ready": 0,
        "weaponized_move_grant_ready": 0,
        "move_grant_ready": 0,
        "core_runtime_ready": 0,
        "core_runtime_passive": 0,
        "core_runtime_action": 0,
        "generic_runtime_ready": 0,
        "missing_runtime_mapping": 0,
    }
    for entry in entries:
        summary[f"{entry.kind}s"] = int(summary.get(f"{entry.kind}s", 0)) + 1
        summary[entry.runtime_status] = int(summary.get(entry.runtime_status, 0)) + 1
        summary[entry.runtime_surface] = int(summary.get(entry.runtime_surface, 0)) + 1
    return summary


def _render_markdown(summary: Dict[str, Any], entries: Iterable[CoverageEntry]) -> str:
    entries = list(entries)
    lines = [
        "# Trainer Runtime Coverage",
        "",
        f"- Total entries: {summary['total']}",
        f"- Features: {summary['features']}",
        f"- Edges: {summary['edges']}",
        f"- Perk hook ready: {summary['perk_hook_ready']}",
        f"- Trainer action registry ready: {summary['trainer_action_registry_ready']}",
        f"- Pokemon action registry ready: {summary['pokemon_action_registry_ready']}",
        f"- Move grant+rider ready: {summary['move_grant_rider_ready']}",
        f"- Weaponized move grant ready: {summary['weaponized_move_grant_ready']}",
        f"- Move grant ready: {summary['move_grant_ready']}",
        f"- Core runtime ready: {summary['core_runtime_ready']}",
        f"- Core runtime passive: {summary['core_runtime_passive']}",
        f"- Core runtime action: {summary['core_runtime_action']}",
        f"- Generic runtime ready: {summary['generic_runtime_ready']}",
        f"- Missing runtime mapping: {summary['missing_runtime_mapping']}",
        "",
        "| Kind | Name | Status | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for entry in entries:
        notes = ", ".join(entry.notes) if entry.notes else ""
        lines.append(f"| {entry.kind} | {entry.name} | {entry.runtime_status} | {notes} |")
    lines.append("")
    return "\n".join(lines)


def generate_report(
    *,
    character_creation_path: Path = DEFAULT_CHARACTER_CREATION,
    perk_effects_dir: Path = DEFAULT_PERK_EFFECTS_DIR,
    runtime_dir: Path = DEFAULT_RUNTIME_DIR,
    json_out: Path = DEFAULT_JSON_OUT,
    markdown_out: Path = DEFAULT_MD_OUT,
) -> Dict[str, Any]:
    dataset = _load_json(character_creation_path)
    perk_hooks = _discover_perk_hooks(perk_effects_dir)
    runtime_tokens = _discover_runtime_tokens(runtime_dir)
    action_registry_features = _discover_trainer_feature_action_registry(runtime_dir)
    move_grant_features = _discover_trainer_feature_move_grants(runtime_dir)
    entries = _collect_entries(
        dataset,
        perk_hooks,
        runtime_tokens,
        action_registry_features["trainer"],
        action_registry_features["pokemon"],
        move_grant_features["all"],
        move_grant_features["weaponized"],
    )
    summary = _build_summary(entries)
    queues = {
        "trainer_action_registry_ready": [entry.name for entry in entries if entry.runtime_status == "trainer_action_registry_ready"],
        "pokemon_action_registry_ready": [entry.name for entry in entries if entry.runtime_status == "pokemon_action_registry_ready"],
        "core_runtime_passive": [entry.name for entry in entries if entry.runtime_surface == "core_runtime_passive"],
        "core_runtime_action": [entry.name for entry in entries if entry.runtime_surface == "core_runtime_action"],
        "move_grant_rider_ready": [entry.name for entry in entries if entry.runtime_status == "move_grant_rider_ready"],
        "move_grant_ready": [entry.name for entry in entries if entry.runtime_status == "move_grant_ready"],
        "weaponized_move_grant_ready": [entry.name for entry in entries if entry.runtime_status == "weaponized_move_grant_ready"],
    }
    payload = {
        "sources": {
            "character_creation": str(character_creation_path),
            "perk_effects_dir": str(perk_effects_dir),
            "runtime_dir": str(runtime_dir),
            "trainer_feature_actions": sorted(action_registry_features["trainer"]),
            "pokemon_feature_actions": sorted(action_registry_features["pokemon"]),
            "trainer_feature_move_grants": sorted(move_grant_features["all"]),
            "weaponized_trainer_feature_move_grants": sorted(move_grant_features["weaponized"]),
        },
        "summary": summary,
        "queues": queues,
        "entries": [entry.to_dict() for entry in entries],
    }
    _write_text_atomic(json_out, json.dumps(payload, indent=2))
    _write_text_atomic(markdown_out, _render_markdown(summary, entries))
    written_payload = _load_json(json_out)
    if written_payload.get("summary") != summary:
        raise RuntimeError("Coverage summary mismatch after writing JSON report.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate trainer runtime coverage report.")
    parser.add_argument("--character-creation", type=Path, default=DEFAULT_CHARACTER_CREATION)
    parser.add_argument("--perk-effects-dir", type=Path, default=DEFAULT_PERK_EFFECTS_DIR)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MD_OUT)
    args = parser.parse_args()
    payload = generate_report(
        character_creation_path=args.character_creation,
        perk_effects_dir=args.perk_effects_dir,
        runtime_dir=args.runtime_dir,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
    )
    summary = payload["summary"]
    print(
        "Trainer runtime coverage: "
            f"{summary['total']} entries, "
            f"{summary['perk_hook_ready']} perk-hook ready, "
            f"{summary['trainer_action_registry_ready']} trainer-action ready, "
            f"{summary['pokemon_action_registry_ready']} pokemon-action ready, "
            f"{summary['move_grant_rider_ready']} move-grant+rider ready, "
            f"{summary['weaponized_move_grant_ready']} weaponized-move-grant ready, "
            f"{summary['move_grant_ready']} move-grant ready, "
            f"{summary['core_runtime_ready']} core-runtime ready, "
            f"{summary['core_runtime_passive']} core-passive, "
            f"{summary['core_runtime_action']} core-action, "
            f"{summary['generic_runtime_ready']} generic-runtime ready, "
            f"{summary['missing_runtime_mapping']} missing."
    )


if __name__ == "__main__":
    main()
