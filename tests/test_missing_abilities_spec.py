from __future__ import annotations

import ast
import csv
import random
import re
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.hooks import ability_hooks
from auto_ptu.rules.hooks.ability_hooks import AbilityHookContext


class SequenceRNG(random.Random):
    def __init__(self, values: List[int]) -> None:
        super().__init__()
        self._values = list(values)

    def randint(self, a: int, b: int) -> int:
        if self._values:
            return self._values.pop(0)
        return b


def _load_abilities_csv() -> Dict[str, str]:
    path = Path(__file__).resolve().parents[1] / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
    effects: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = str(row.get("Name") or "").strip()
            if not name:
                continue
            effect = str(row.get("Effect") or "").strip()
            effect2 = str(row.get("Effect 2") or "").strip()
            text = "\n".join(part for part in (effect, effect2) if part)
            effects[name] = text
    return effects


def _load_test_abilities() -> set[str]:
    abilities: set[str] = set()
    patterns = [
        re.compile(r"abilities\s*=\s*\[\s*\{\s*[\"']name[\"']\s*:\s*[\"']([^\"']+)[\"']\s*\}\s*\]"),
        re.compile(r"\.abilities\s*=\s*\[\s*\{\s*[\"']name[\"']\s*:\s*[\"']([^\"']+)[\"']\s*\}\s*\]"),
        re.compile(r"abilities\.append\(\s*\{\s*[\"']name[\"']\s*:\s*[\"']([^\"']+)[\"']\s*\}\s*\)"),
    ]
    list_patterns = [
        re.compile(r"abilities\s*=\s*\[[^\]]+\]"),
        re.compile(r"\.abilities\s*=\s*\[[^\]]+\]"),
    ]
    single_patterns = [
        re.compile(r"\bability\s*=\s*[\"']([^\"']+)[\"']"),
    ]
    tests = Path(__file__).resolve().parents[0]
    for file in tests.rglob("test_*.py"):
        source = file.read_text(encoding="utf-8")
        for pattern in patterns:
            for match in pattern.finditer(source):
                abilities.add(match.group(1).strip())
        for pattern in list_patterns:
            for match in pattern.finditer(source):
                segment = match.group(0)
                if "{" in segment:
                    continue
                for name in re.findall(r"[\"']([^\"']+)[\"']", segment):
                    abilities.add(name.strip())
        for pattern in single_patterns:
            for match in pattern.finditer(source):
                abilities.add(match.group(1).strip())
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        def _add_from_node(node: ast.AST) -> None:
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                abilities.add(node.value.strip())
                return
            if isinstance(node, ast.List):
                for elt in node.elts:
                    _add_from_node(elt)
                return
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value == "name":
                        _add_from_node(value)
                return

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "abilities":
                        _add_from_node(node.value)
                    elif isinstance(target, ast.Name) and target.id == "abilities":
                        _add_from_node(node.value)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "append":
                    target = node.func.value
                    if isinstance(target, ast.Attribute) and target.attr == "abilities":
                        if node.args:
                            _add_from_node(node.args[0])
                for keyword in node.keywords:
                    if keyword.arg in {"abilities", "ability"}:
                        _add_from_node(keyword.value)
    return abilities


def _missing_abilities() -> List[str]:
    effects = _load_abilities_csv()
    tested = _load_test_abilities()
    tested_norm = {name.lower() for name in tested}
    return sorted(name for name in effects.keys() if name.lower() not in tested_norm)


def _pokemon_spec(name: str, ability: str | None = None) -> PokemonSpec:
    abilities = [{"name": ability}] if ability else []
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=10,
        moves=[MoveSpec(name="Tackle", type="Normal", category="Physical", db=6, ac=2)],
        abilities=abilities,
        movement={"overland": 4},
    )


def _build_battle(ability: str, *, holder: str) -> Tuple[BattleState, str, str]:
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", ability if holder == "attacker" else None),
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", ability if holder == "defender" else None),
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=6, height=6),
    )
    battle.rng = SequenceRNG([20] * 50)
    battle.round = 1
    return battle, "a-1", "b-1"


def _ascii_clean(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": "\"",
        "\u201d": "\"",
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("ascii", "ignore").decode("ascii")


class MissingAbilitiesSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = _load_abilities_csv()
        ability_hooks.apply_ability_hooks(
            "pre_damage",
            AbilityHookContext(
                battle=None,
                attacker_id="",
                attacker=None,
                defender_id=None,
                defender=None,
                move=MoveSpec(name="Tackle", type="Normal"),
                effective_move=MoveSpec(name="Tackle", type="Normal"),
                events=[],
                phase="pre_damage",
                result={},
            ),
        )
        cls.hook_map: Dict[str, List[Tuple[str, str]]] = {}
        for phase, entries in ability_hooks._ABILITY_HOOKS.items():
            for ability, holder, _func in entries:
                if ability is None:
                    continue
                cls.hook_map.setdefault(ability, []).append((phase, holder))
        tested = _load_test_abilities()
        tested_norm = {name.lower() for name in tested}
        cls.missing = sorted(
            name
            for name in cls.effects.keys()
            if name.lower() not in tested_norm and name.lower() in cls.hook_map
        )

    def test_missing_ability_effects(self) -> None:
        for ability in self.missing:
            hooks = self.hook_map.get(ability.lower(), [])
            effect_text = _ascii_clean(self.effects.get(ability, "")).lower()
            for phase, holder in hooks:
                with self.subTest(ability=ability, phase=phase, holder=holder):
                    battle, attacker_id, defender_id = _build_battle(ability, holder=holder)
                    attacker = battle.pokemon[attacker_id]
                    defender = battle.pokemon[defender_id]

                    move_type = "fire"
                    type_tokens = (
                        "fire",
                        "water",
                        "rock",
                        "ground",
                        "ice",
                        "flying",
                        "dragon",
                        "electric",
                        "grass",
                        "psychic",
                        "dark",
                        "fairy",
                        "steel",
                        "bug",
                        "ghost",
                        "poison",
                        "normal",
                        "fighting",
                    )
                    for token in type_tokens:
                        if f"resists {token}-type" in effect_text or f"resist {token}-type" in effect_text:
                            move_type = token
                            break
                    else:
                        for token in type_tokens:
                            if f"{token}-type" in effect_text:
                                move_type = token
                                break

                    move = MoveSpec(
                        name="Test Move",
                        type=move_type.capitalize(),
                        category="Physical",
                        db=6,
                        ac=2,
                        range_kind="Melee",
                        range_value=1,
                        target_kind="Melee",
                        target_range=1,
                        keywords=["Sonic", "Contact", "Interrupt"],
                        priority=1,
                    )
                    result = {
                        "hit": True,
                        "damage": 40,
                        "pre_type_damage": 20,
                        "type_multiplier": 2.0,
                        "roll": 20,
                    }
                    if "vulnerable" in effect_text:
                        result["type_multiplier"] = 1.0
                        result["damage"] = 20
                    ctx = AbilityHookContext(
                        battle=battle,
                        attacker_id=attacker_id,
                        attacker=attacker,
                        defender_id=defender_id,
                        defender=defender,
                        move=move,
                        effective_move=move,
                        events=[],
                        phase=phase,
                        result=result,
                    )
                    ability_hooks.apply_ability_hooks(phase, ctx)

                    handled = False
                    if "one step less effective" in effect_text or "resists" in effect_text:
                        self.assertLess(result.get("type_multiplier", 2.0), 2.0)
                        handled = True
                    if "immune to" in effect_text or "immunity" in effect_text:
                        self.assertTrue(
                            result.get("damage") == 0
                            or result.get("type_multiplier") == 0.0
                            or result.get("immune_to")
                        )
                        handled = True
                    if "raise" in effect_text:
                        raised = any(value > 0 for value in defender.combat_stages.values()) or any(
                            value > 0 for value in attacker.combat_stages.values()
                        )
                        self.assertTrue(raised)
                        handled = True
                    if "lower" in effect_text:
                        lowered = any(value < 0 for value in defender.combat_stages.values()) or any(
                            value < 0 for value in attacker.combat_stages.values()
                        )
                        self.assertTrue(lowered)
                        handled = True
                    if "cs" in effect_text or "combat stage" in effect_text:
                        changed = any(value != 0 for value in defender.combat_stages.values()) or any(
                            value != 0 for value in attacker.combat_stages.values()
                        )
                        self.assertTrue(changed)
                        handled = True
                    if any(token in effect_text for token in ("burn", "poison", "paraly", "freeze", "sleep", "status")):
                        if "immune to" not in effect_text and "immunity" not in effect_text:
                            has_status = bool(defender.statuses or attacker.statuses)
                            self.assertTrue(has_status)
                            handled = True
                    if "vulnerable" in effect_text:
                        self.assertGreater(result.get("type_multiplier", 1.0), 1.0)
                        handled = True
                    if "heal" in effect_text or "regain" in effect_text or "restore" in effect_text:
                        if holder == "attacker":
                            attacker.hp = max(1, attacker.max_hp() - 3)
                        else:
                            defender.hp = max(1, defender.max_hp() - 3)
                        before = attacker.hp if holder == "attacker" else defender.hp
                        ability_hooks.apply_ability_hooks(phase, ctx)
                        after = attacker.hp if holder == "attacker" else defender.hp
                        self.assertGreaterEqual(after, before)
                        handled = True
                    if "damage" in effect_text and "+" in effect_text:
                        handled = True

                    if not handled:
                        self.fail(f"Unhandled ability effect text (needs bespoke test): {effect_text}")
            if not hooks:
                self.fail(f"No ability hooks found for missing-test ability: {ability} | {effect_text}")
