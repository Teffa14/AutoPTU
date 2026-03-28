from __future__ import annotations

import csv
import json
import random
import re
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.calculations import resolve_move_action
from auto_ptu.rules.hooks import move_specials
from auto_ptu.rules import move_traits


class SequenceRNG(random.Random):
    def __init__(self, values: List[int]) -> None:
        super().__init__()
        self._values = list(values)

    def randint(self, a: int, b: int) -> int:
        if self._values:
            return self._values.pop(0)
        return b


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
    text = text.encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def _load_moves() -> List[MoveSpec]:
    path = Path(__file__).resolve().parents[1] / "auto_ptu" / "data" / "compiled" / "moves.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    effects_map = _load_move_effects()
    moves: List[MoveSpec] = []
    for entry in data:
        if not isinstance(entry, dict) or not entry.get("name"):
            continue
        spec = MoveSpec.from_dict(entry)
        name = (spec.name or "").strip()
        effects_text = effects_map.get(name.lower())
        if effects_text:
            spec.effects_text = effects_text
        elif not spec.effects_text:
            spec.effects_text = str(entry.get("effects") or "")
        moves.append(spec)
    return moves


def _load_move_effects() -> Dict[str, str]:
    path = (
        Path(__file__).resolve().parents[1]
        / "files"
        / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Moves Data.csv"
    )
    if not path.exists():
        return {}
    effects: Dict[str, str] = {}
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_index = None
    for idx, line in enumerate(lines):
        if line.startswith("Name,"):
            header_index = idx
            break
    if header_index is None:
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        for _ in range(header_index):
            next(handle, None)
        reader = csv.DictReader(handle)
        for row in reader:
            name = str(row.get("Name") or "").strip()
            if not name:
                continue
            text = str(row.get("Effects") or "").strip()
            if text:
                effects[name.lower()] = text
    return effects


def _pokemon_spec(name: str, move: MoveSpec, *, atk: int = 10, spatk: int = 10, defense: int = 10, spdef: int = 10) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=10,
        moves=[move],
        movement={"overland": 4},
    )


def _build_battle(move: MoveSpec) -> Tuple[BattleState, str, str]:
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move),
        controller_id="b",
        position=(1, 0),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
    )
    battle.rng = SequenceRNG([20, 20, 20, 20])
    return battle, "a-1", "b-1"


def _build_battle_with_grid(move: MoveSpec, *, atk: int = 10, spatk: int = 10, defense: int = 10, spdef: int = 10) -> Tuple[BattleState, str, str]:
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, atk=atk, spatk=spatk),
        controller_id="a",
        position=(4, 4),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move, defense=defense, spdef=spdef),
        controller_id="b",
        position=(4, 5),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20, 20, 20, 20])
    battle.round = 1
    return battle, "a-1", "b-1"


def _resolve_and_apply(move: MoveSpec, roll: int) -> Tuple[BattleState, Dict[str, object]]:
    battle, attacker_id, defender_id = _build_battle(move)
    attacker = battle.pokemon[attacker_id]
    defender = battle.pokemon[defender_id]
    battle.rng = SequenceRNG([roll, 20, 20, 20])
    result = resolve_move_action(battle.rng, attacker, defender, move)
    result = dict(result)
    move_specials.handle_move_specials(
        battle=battle,
        attacker_id=attacker_id,
        attacker=attacker,
        defender_id=defender_id,
        defender=defender,
        move=move,
        result=result,
        damage_dealt=0,
        phase="pre_damage",
    )
    move_specials.handle_move_specials(
        battle=battle,
        attacker_id=attacker_id,
        attacker=attacker,
        defender_id=defender_id,
        defender=defender,
        move=move,
        result=result,
        damage_dealt=0,
        phase="post_damage",
    )
    return battle, result


def _resolve_full(move: MoveSpec, roll: int) -> Tuple[BattleState, str, str]:
    battle, attacker_id, defender_id = _build_battle_with_grid(move, atk=20, spatk=20, defense=6, spdef=6)
    battle.rng = SequenceRNG([roll, 20, 20, 20])
    defender = battle.pokemon[defender_id]
    target_pos = defender.position
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=target_pos,
    )
    return battle, attacker_id, defender_id


def _build_battle_with_ally(move: MoveSpec) -> Tuple[BattleState, str, str, str]:
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Helper", move),
        controller_id="a",
        position=(4, 4),
        active=True,
    )
    ally = PokemonState(
        spec=_pokemon_spec("Ally", move),
        controller_id="a",
        position=(4, 5),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move),
        controller_id="b",
        position=(4, 6),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "a-2": ally, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20, 20, 20, 20])
    battle.round = 1
    return battle, "a-1", "a-2", "b-1"


def _last_move_event(battle: BattleState) -> Dict[str, object]:
    for entry in reversed(battle.log):
        if isinstance(entry, dict) and entry.get("type") == "move":
            return entry
    return {}


def _damage_from_move(
    move: MoveSpec,
    *,
    roll: int = 20,
    attacker_hp: int | None = None,
    defender_hp: int | None = None,
    attacker_injuries: int | None = None,
    attacker_weight: int | None = None,
    defender_weight: int | None = None,
    attacker_speed: int | None = None,
    defender_speed: int | None = None,
    attacker_loyalty: int | None = None,
    attacker_cs: Dict[str, int] | None = None,
    defender_cs: Dict[str, int] | None = None,
    attacker_effects: List[dict] | None = None,
    defender_effects: List[dict] | None = None,
    attacker_statuses: List[str] | None = None,
    defender_statuses: List[str] | None = None,
    attacker_items: List[dict] | None = None,
    defender_items: List[dict] | None = None,
    attacker_types: List[str] | None = None,
    defender_types: List[str] | None = None,
    echoed_voice_rounds: List[int] | None = None,
    battle_round: int | None = None,
    round_uses: int | None = None,
    fusion_bolt_rounds: List[int] | None = None,
    fusion_flare_rounds: List[int] | None = None,
) -> Tuple[int, BattleState, str, str]:
    battle, attacker_id, defender_id = _build_battle_with_grid(move, atk=20, spatk=20, defense=6, spdef=6)
    battle.rng = SequenceRNG([roll, 20, 20, 20])
    if battle_round is not None:
        battle.round = battle_round
    if round_uses is not None:
        battle.round_uses = round_uses
    if fusion_bolt_rounds is not None:
        battle.fusion_bolt_rounds = list(fusion_bolt_rounds)
    if fusion_flare_rounds is not None:
        battle.fusion_flare_rounds = list(fusion_flare_rounds)
    attacker = battle.pokemon[attacker_id]
    defender = battle.pokemon[defender_id]
    if attacker_hp is not None:
        attacker.hp = attacker_hp
    if defender_hp is not None:
        defender.hp = defender_hp
    if attacker_injuries is not None:
        attacker.injuries = attacker_injuries
    if attacker_weight is not None:
        attacker.spec.weight = attacker_weight
    if defender_weight is not None:
        defender.spec.weight = defender_weight
    if attacker_speed is not None:
        attacker.spec.spd = attacker_speed
    if defender_speed is not None:
        defender.spec.spd = defender_speed
    if attacker_loyalty is not None:
        attacker.spec.loyalty = attacker_loyalty
    if attacker_items is not None:
        attacker.spec.items = list(attacker_items)
    if defender_items is not None:
        defender.spec.items = list(defender_items)
    if attacker_types is not None:
        attacker.spec.types = list(attacker_types)
    if defender_types is not None:
        defender.spec.types = list(defender_types)
    if echoed_voice_rounds is not None:
        battle.echoed_voice_rounds = list(echoed_voice_rounds)
    if attacker_cs:
        attacker.combat_stages.update(attacker_cs)
    if defender_cs:
        defender.combat_stages.update(defender_cs)
    if attacker_effects:
        for entry in attacker_effects:
            attacker.add_temporary_effect(entry.get("kind", ""), **{k: v for k, v in entry.items() if k != "kind"})
    if defender_effects:
        for entry in defender_effects:
            defender.add_temporary_effect(entry.get("kind", ""), **{k: v for k, v in entry.items() if k != "kind"})
    if attacker_statuses:
        attacker.statuses.extend(attacker_statuses)
    if defender_statuses:
        defender.statuses.extend(defender_statuses)
    before = defender.hp
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=defender.position,
    )
    after = defender.hp
    return max(0, int(before or 0) - int(after or 0)), battle, attacker_id, defender_id


class MissingMovesSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        move_specials.initialize_move_specials()
        cls.moves = [
            move
            for move in _load_moves()
            if not move_specials._has_specific_handler((move.name or "").strip().lower())
        ]

        cls.status_map = {
            "burn": "Burned",
            "poison": "Poisoned",
            "paralyzes": "Paralyzed",
            "freeze": "Frozen",
            "confuse": "Confused",
            "flinch": "Flinched",
        }

    def test_missing_moves_effects(self) -> None:
        for move in self.moves:
            move_name = (move.name or "").strip()
            text = _ascii_clean(move.effects_text or "").strip().lower()
            if not text:
                continue
            with self.subTest(move=move_name):
                handled = False
                move_key = _ascii_clean(move_name).lower()
                battle, result = _resolve_and_apply(move, 20)
                attacker = battle.pokemon["a-1"]
                defender = battle.pokemon["b-1"]

                match = move_specials._STATUS_PATTERN.search(text)
                if match:
                    verb = match.group("verb").lower()
                    for key, status in self.status_map.items():
                        if verb.startswith(key):
                            self.assertTrue(defender.has_status(status))
                            handled = True
                            break

                always = move_specials._STATUS_ALWAYS_PATTERN.search(text)
                if always and "on " not in text:
                    verb = always.group("verb").lower()
                    for key, status in self.status_map.items():
                        if verb.startswith(key):
                            self.assertTrue(defender.has_status(status))
                            handled = True
                            break

                if "falls asleep" in text:
                    self.assertTrue(defender.has_status("Sleep"))
                    handled = True

                if not handled:
                    status_threshold = re.search(r"is\s+(slowed|tripped|flinched|confused|paralyzed|poisoned|burned|frozen)\s+on\s+(\d+)\+", text)
                    if status_threshold:
                        status_word = status_threshold.group(1)
                        status_name = status_word.capitalize()
                        self.assertTrue(defender.has_status(status_name))
                        handled = True
                even_status = re.search(
                    r"(burns?|poisons?|paralyzes|freezes|confuses|flinches)\b.*even-numbered",
                    text,
                )
                if even_status:
                    _, even_result = _resolve_and_apply(move, 20)
                    verb = even_status.group(1).lower()
                    for key, status in self.status_map.items():
                        if verb.startswith(key):
                            self.assertTrue(battle.pokemon["b-1"].has_status(status))
                            handled = True
                            break

                if "cannot miss" in text or "always hit" in text:
                    _, result_miss = _resolve_and_apply(move, 1)
                    self.assertTrue(result_miss.get("hit"))
                    handled = True

                crit_match = move_specials._CRIT_PATTERN.search(text)
                if crit_match:
                    threshold = int(crit_match.group("threshold"))
                    _, result_crit = _resolve_and_apply(move, threshold)
                    self.assertTrue(result_crit.get("crit"))
                    handled = True
                if move_specials._CRIT_EVEN_PATTERN.search(text):
                    _, result_crit = _resolve_and_apply(move, 20)
                    self.assertTrue(result_crit.get("crit"))
                    handled = True

                if "if" in text and "hits" in text and "critical hit" in text and "on" not in text:
                    _, result_crit = _resolve_and_apply(move, 20)
                    self.assertTrue(result_crit.get("crit"))
                    handled = True

                raise_match = move_specials._RAISE_PATTERN.search(text)
                if raise_match:
                    amount = int(raise_match.group("amount"))
                    target = raise_match.group("target").lower()
                    stats = move_specials._normalize_stats(raise_match.group("stats"))
                    target_state = attacker if target == "user" else defender
                    for stat in stats:
                        self.assertEqual(target_state.combat_stages.get(stat), amount)
                    handled = True
                if not handled:
                    alt_raise = re.search(
                        r"raise(?:s)?\s+the\s+(user|target)'?s?\s+([\w\s/]+?)\s+by\s+\+?(\d+)\s+cs(?:\s+on\s+\d+\+)?",
                        text,
                    )
                    if alt_raise:
                        target = alt_raise.group(1).lower()
                        amount = int(alt_raise.group(3))
                        stats = move_specials._normalize_stats(alt_raise.group(2))
                        target_state = attacker if target == "user" else defender
                        for stat in stats:
                            self.assertEqual(target_state.combat_stages.get(stat), amount)
                        handled = True

                lower_match = move_specials._LOWER_PATTERN.search(text)
                if lower_match:
                    amount = -int(lower_match.group("amount"))
                    target = lower_match.group("target").lower()
                    stats = move_specials._normalize_stats(lower_match.group("stats"))
                    target_state = attacker if target == "user" else defender
                    for stat in stats:
                        self.assertEqual(target_state.combat_stages.get(stat), amount)
                    handled = True
                if not handled:
                    alt_lower = re.search(
                        r"lower(?:s)?\s+the\s+(user|target)'?s?\s+([\w\s/]+?)\s+by\s+\-?(\d+)\s+cs(?:\s+on\s+\d+\+)?",
                        text,
                    )
                    if alt_lower:
                        target = alt_lower.group(1).lower()
                        amount = -int(alt_lower.group(3))
                        stats = move_specials._normalize_stats(alt_lower.group(2))
                        target_state = attacker if target == "user" else defender
                        for stat in stats:
                            self.assertEqual(target_state.combat_stages.get(stat), amount)
                        handled = True
                if not handled:
                    threshold_lower = re.search(
                        r"lowers?\s+the\s+target's\s+([\w\s/]+?)\s+by\s+\-?(\d+)\s+cs\s+on\s+(\d+)\+",
                        text,
                    )
                    if threshold_lower:
                        amount = -int(threshold_lower.group(2))
                        threshold = int(threshold_lower.group(3))
                        stats = move_specials._normalize_stats(threshold_lower.group(1))
                        _, _ = _resolve_and_apply(move, threshold)
                        defender = battle.pokemon["b-1"]
                        for stat in stats:
                            self.assertEqual(defender.combat_stages.get(stat), amount)
                        handled = True

                if not handled:
                    self_lower = re.search(
                        r"user'?s?\s+([\w\s/]+?)\s+is\s+lowered\s+by\s+\-?(\d+)\s+cs",
                        text,
                    )
                    if self_lower:
                        amount = -int(self_lower.group(2))
                        stats = move_specials._normalize_stats(self_lower.group(1))
                        for stat in stats:
                            self.assertEqual(attacker.combat_stages.get(stat), amount)
                        handled = True
                if "after damage" in text and "user" in text and "lower" in text and "cs" in text:
                    lowered = any(value < 0 for value in attacker.combat_stages.values())
                    self.assertTrue(lowered)
                    handled = True

                if not handled and (
                    "gains hp equal to half of the damage" in text
                    or "regains hp equal to half" in text
                    or "heals" in text and "half of the damage" in text
                    or "total damage" in text and "half" in text
                ):
                    battle_full, attacker_id, defender_id = _build_battle_with_grid(
                        move, atk=20, spatk=20, defense=6, spdef=6
                    )
                    full_attacker = battle_full.pokemon[attacker_id]
                    full_attacker.hp = max(1, full_attacker.max_hp() - 5)
                    before = full_attacker.hp
                    battle_full.resolve_move_targets(
                        attacker_id=attacker_id,
                        move=move,
                        target_id=defender_id,
                        target_position=battle_full.pokemon[defender_id].position,
                    )
                    self.assertGreater(full_attacker.hp, before)
                    handled = True

                if not handled and "if the user successfully knocks out" in text and "raise" in text:
                    battle_full, attacker_id, defender_id = _build_battle_with_grid(
                        move, atk=20, spatk=20, defense=6, spdef=6
                    )
                    defender_state = battle_full.pokemon[defender_id]
                    defender_state.hp = 1
                    battle_full.resolve_move_targets(
                        attacker_id=attacker_id,
                        move=move,
                        target_id=defender_id,
                        target_position=defender_state.position,
                    )
                    attacker_state = battle_full.pokemon[attacker_id]
                    self.assertTrue(attacker_state.combat_stages.get("atk", 0) >= 2)
                    handled = True

                if not handled and ("target is pushed" in text or "pushed" in text):
                    instruction = move_traits.forced_movement_instruction(move)
                    if instruction:
                        battle_full, attacker_id, defender_id = _resolve_full(move, 20)
                        defender_state = battle_full.pokemon[defender_id]
                        self.assertNotEqual(defender_state.position, (4, 5))
                        handled = True
                if "tripped on" in text:
                    threshold_match = re.search(r"tripped\s+on\s+(\d+)\+", text)
                    if threshold_match:
                        threshold = int(threshold_match.group(1))
                        battle_full, _, defender_id = _resolve_full(move, threshold)
                        defender_state = battle_full.pokemon[defender_id]
                        self.assertTrue(defender_state.has_status("Tripped"))
                        handled = True

                if not handled and "vortex" in text:
                    battle_full, _, defender_id = _resolve_full(move, 20)
                    defender_state = battle_full.pokemon[defender_id]
                    self.assertTrue(defender_state.has_status("Vortex"))
                    handled = True

                if not handled and "tripped" in text:
                    battle_full, _, defender_id = _resolve_full(move, 20)
                    defender_state = battle_full.pokemon[defender_id]
                    self.assertTrue(defender_state.has_status("Tripped"))
                    handled = True

                if not handled and "loses hp" in text and "user" in text:
                    battle_full, attacker_id, defender_id = _build_battle_with_grid(
                        move, atk=20, spatk=20, defense=6, spdef=6
                    )
                    attacker_state = battle_full.pokemon[attacker_id]
                    before = attacker_state.hp
                    battle_full.resolve_move_targets(
                        attacker_id=attacker_id,
                        move=move,
                        target_id=defender_id,
                        target_position=battle_full.pokemon[defender_id].position,
                    )
                    self.assertLess(attacker_state.hp, before)
                    handled = True
                if "misses" in text and "1/4" in text and "hit points" in text:
                    battle_full, attacker_id, defender_id = _build_battle_with_grid(
                        move, atk=20, spatk=20, defense=6, spdef=6
                    )
                    battle_full.rng = SequenceRNG([1, 20, 20, 20])
                    attacker_state = battle_full.pokemon[attacker_id]
                    before = attacker_state.hp
                    battle_full.resolve_move_targets(
                        attacker_id=attacker_id,
                        move=move,
                        target_id=defender_id,
                        target_position=battle_full.pokemon[defender_id].position,
                    )
                    self.assertLess(attacker_state.hp, before)
                    handled = True

                if not handled and text in {"--", "effects"}:
                    if (move.category or "").strip().lower() != "status":
                        damage, _, _, _ = _damage_from_move(move)
                        self.assertGreater(damage, 0)
                    handled = True

                if not handled and "becomes enraged" in text and "confused" in text:
                    battle_full, attacker_id, _ = _resolve_full(move, 20)
                    attacker_state = battle_full.pokemon[attacker_id]
                    self.assertTrue(attacker_state.has_status("Enraged"))
                    self.assertTrue(attacker_state.has_status("Confused"))
                    handled = True

                if not handled and "is a critical hit" in text and "on" not in text:
                    _, result_crit = _resolve_and_apply(move, 20)
                    self.assertTrue(result_crit.get("crit"))
                    handled = True

                if not handled and move_key == "foul play":
                    battle_fp, attacker_id, defender_id = _build_battle(move)
                    attacker_state = battle_fp.pokemon[attacker_id]
                    defender_state = battle_fp.pokemon[defender_id]
                    attacker_state.spec.atk = 5
                    defender_state.spec.atk = 20
                    battle_fp.rng = SequenceRNG([20, 20, 20, 20])
                    result_fp = resolve_move_action(battle_fp.rng, attacker_state, defender_state, move)
                    self.assertEqual(result_fp.get("attack_value"), defender_state.spec.atk)
                    handled = True
                if not handled and move_key == "shell side arm":
                    battle_fp, attacker_id, defender_id = _build_battle(move)
                    attacker_state = battle_fp.pokemon[attacker_id]
                    defender_state = battle_fp.pokemon[defender_id]
                    attacker_state.spec.atk = 6
                    attacker_state.spec.spatk = 20
                    battle_fp.rng = SequenceRNG([20, 20, 20, 20])
                    result_fp = resolve_move_action(battle_fp.rng, attacker_state, defender_state, move)
                    self.assertEqual(result_fp.get("attack_value"), attacker_state.spec.spatk)
                    handled = True
                if not handled and move_key == "photon geyser":
                    battle_fp, attacker_id, defender_id = _build_battle(move)
                    attacker_state = battle_fp.pokemon[attacker_id]
                    defender_state = battle_fp.pokemon[defender_id]
                    attacker_state.spec.atk = 18
                    attacker_state.spec.spatk = 8
                    battle_fp.rng = SequenceRNG([20, 20, 20, 20])
                    result_fp = resolve_move_action(battle_fp.rng, attacker_state, defender_state, move)
                    self.assertEqual(result_fp.get("attack_value"), attacker_state.spec.atk)
                    handled = True

                if not handled and move_key == "electro ball":
                    battle_eb, attacker_id, defender_id = _build_battle(move)
                    attacker_state = battle_eb.pokemon[attacker_id]
                    defender_state = battle_eb.pokemon[defender_id]
                    attacker_state.spec.spd = 20
                    defender_state.spec.spd = 5
                    battle_eb.rng = SequenceRNG([20, 20, 20, 20])
                    result_eb = resolve_move_action(battle_eb.rng, attacker_state, defender_state, move)
                    self.assertGreater(result_eb.get("attack_value", 0), attacker_state.spec.atk)
                    self.assertGreater(result_eb.get("defense_value", 0), defender_state.spec.defense)
                    handled = True

                if not handled and move_key in {"brine"}:
                    damage_full, battle_full, _, defender_id = _damage_from_move(move)
                    max_hp = battle_full.pokemon[defender_id].max_hp()
                    damage_low, battle_low, _, _ = _damage_from_move(move, defender_hp=max_hp // 2)
                    db_full = _last_move_event(battle_full).get("effective_db", 0)
                    db_low = _last_move_event(battle_low).get("effective_db", 0)
                    self.assertGreater(db_low, db_full)
                    handled = True

                if not handled and move_key in {"eruption", "dragon energy"}:
                    damage_full, battle_full, attacker_id, _ = _damage_from_move(move)
                    max_hp = battle_full.pokemon[attacker_id].max_hp()
                    damage_low, battle_low, _, _ = _damage_from_move(move, attacker_hp=max_hp // 2)
                    db_full = _last_move_event(battle_full).get("effective_db", 0)
                    db_low = _last_move_event(battle_low).get("effective_db", 0)
                    self.assertLess(db_low, db_full)
                    handled = True

                if not handled and move_key == "crush grip":
                    damage_full, battle_full, _, defender_id = _damage_from_move(move)
                    max_hp = battle_full.pokemon[defender_id].max_hp()
                    damage_low, battle_low, _, _ = _damage_from_move(move, defender_hp=max_hp // 2)
                    db_full = _last_move_event(battle_full).get("effective_db", 0)
                    db_low = _last_move_event(battle_low).get("effective_db", 0)
                    self.assertLess(db_low, db_full)
                    handled = True

                if not handled and move_key == "flail":
                    damage_full, battle_full, _, _ = _damage_from_move(move)
                    damage_injured, battle_injured, _, _ = _damage_from_move(move, attacker_injuries=3)
                    db_full = _last_move_event(battle_full).get("effective_db", 0)
                    db_injured = _last_move_event(battle_injured).get("effective_db", 0)
                    self.assertGreater(db_injured, db_full)
                    handled = True

                if not handled and move_key in {"behemoth bash", "behemoth blade", "dynamax cannon"}:
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, defender_cs={"atk": 2, "def": 2})
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key == "power trip":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, attacker_cs={"atk": 2, "def": 1})
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key == "punishment":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, defender_cs={"atk": 2, "def": 1})
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key in {"heat crash", "heavy slam"}:
                    damage_base, battle_base, _, _ = _damage_from_move(move, attacker_weight=3, defender_weight=3)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, attacker_weight=8, defender_weight=3)
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key == "gyro ball":
                    damage_base, battle_base, _, _ = _damage_from_move(move, attacker_speed=8, defender_speed=8)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, attacker_speed=5, defender_speed=15)
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key == "fury cutter":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_chain, battle_chain, _, _ = _damage_from_move(
                        move,
                        attacker_effects=[{"kind": "fury_cutter_chain", "stage": 2, "target_id": "b-1"}],
                    )
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_chain = _last_move_event(battle_chain).get("effective_db", 0)
                    self.assertGreater(db_chain, db_base)
                    handled = True

                if not handled and move_key == "ice ball":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_chain, battle_chain, _, _ = _damage_from_move(
                        move,
                        attacker_effects=[{"kind": "ice_ball_chain", "stage": 2}],
                    )
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_chain = _last_move_event(battle_chain).get("effective_db", 0)
                    self.assertGreater(db_chain, db_base)
                    handled = True

                if not handled and move_key == "rollout":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_chain, battle_chain, _, _ = _damage_from_move(
                        move,
                        attacker_effects=[{"kind": "rollout_chain", "count": 2}],
                    )
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_chain = _last_move_event(battle_chain).get("effective_db", 0)
                    self.assertGreater(db_chain, db_base)
                    handled = True

                if not handled and move_key == "round":
                    damage_base, battle_base, _, _ = _damage_from_move(move, battle_round=1, round_uses=0)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, battle_round=1, round_uses=2)
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key == "hex":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, defender_statuses=["Burned"])
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key == "infernal parade":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, defender_statuses=["Burned"])
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key in {"fusion bolt", "fusion flare"}:
                    damage_base, battle_base, _, _ = _damage_from_move(move, battle_round=2)
                    if move_key == "fusion bolt":
                        damage_boost, battle_boost, _, _ = _damage_from_move(
                            move, battle_round=2, fusion_flare_rounds=[2]
                        )
                    else:
                        damage_boost, battle_boost, _, _ = _damage_from_move(
                            move, battle_round=2, fusion_bolt_rounds=[2]
                        )
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key == "lash out":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_boost, battle_boost, _, _ = _damage_from_move(
                        move,
                        attacker_cs={"atk": 0},
                        attacker_effects=[{"kind": "cs_snapshot", "stages": {"atk": 2}}],
                    )
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True

                if not handled and move_key in {"multi-attack", "multi-attack [ss]"}:
                    damage_base, battle_base, _, _ = _damage_from_move(
                        move,
                        defender_types=["Grass"],
                    )
                    damage_boost, battle_boost, _, _ = _damage_from_move(
                        move,
                        attacker_items=[{"name": "Flame Disk", "type": "Fire"}],
                        defender_types=["Grass"],
                    )
                    mult_base = _last_move_event(battle_base).get("type_multiplier", 1.0)
                    mult_boost = _last_move_event(battle_boost).get("type_multiplier", 1.0)
                    self.assertGreater(mult_boost, mult_base)
                    handled = True

                if not handled and move_key == "judgement":
                    damage_base, battle_base, _, _ = _damage_from_move(
                        move,
                        attacker_types=["Normal"],
                        defender_types=["Ghost"],
                    )
                    mult_base = _last_move_event(battle_base).get("type_multiplier", 0.0)
                    self.assertGreater(mult_base, 0.0)
                    handled = True
                if not handled and move_key == "chip away":
                    damage_base, _, _, _ = _damage_from_move(
                        move,
                        defender_cs={"def": 0, "spdef": 0},
                        defender_effects=[],
                    )
                    damage_boost, _, _, _ = _damage_from_move(
                        move,
                        defender_cs={"def": 2, "spdef": 2},
                        defender_effects=[{"kind": "damage_reduction", "category": "physical", "amount": 5}],
                    )
                    self.assertEqual(damage_boost, damage_base)
                    handled = True
                if not handled and move_key == "darkest lariat":
                    damage_base, _, _, _ = _damage_from_move(
                        move,
                        defender_cs={"def": 0, "spdef": 0},
                        defender_effects=[],
                    )
                    damage_boost, _, _, _ = _damage_from_move(
                        move,
                        defender_cs={"def": 2, "spdef": 2},
                        defender_effects=[{"kind": "damage_reduction", "category": "physical", "amount": 5}],
                    )
                    self.assertEqual(damage_boost, damage_base)
                    handled = True
                if not handled and move_key == "cut":
                    damage_base, _, _, _ = _damage_from_move(
                        move,
                        defender_effects=[],
                    )
                    damage_dr, _, _, _ = _damage_from_move(
                        move,
                        defender_effects=[{"kind": "damage_reduction", "category": "physical", "amount": 5}],
                    )
                    self.assertEqual(damage_dr, damage_base)
                    handled = True
                if not handled and move_key == "facade":
                    damage_base, battle_base, _, _ = _damage_from_move(move)
                    damage_boost, battle_boost, _, _ = _damage_from_move(move, attacker_statuses=["Burned"])
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True
                if not handled and move_key == "dream eater":
                    battle_full, attacker_id, defender_id = _build_battle_with_grid(move)
                    battle_full.rng = SequenceRNG([20, 20, 20, 20])
                    battle_full.resolve_move_targets(
                        attacker_id=attacker_id,
                        move=move,
                        target_id=defender_id,
                        target_position=battle_full.pokemon[defender_id].position,
                    )
                    defender_state = battle_full.pokemon[defender_id]
                    self.assertEqual(defender_state.hp, defender_state.max_hp())
                    handled = True
                if not handled and move_key in {"explosion", "self-destruct"}:
                    battle_full, attacker_id, defender_id = _build_battle_with_grid(move)
                    attacker_state = battle_full.pokemon[attacker_id]
                    battle_full.resolve_move_targets(
                        attacker_id=attacker_id,
                        move=move,
                        target_id=defender_id,
                        target_position=battle_full.pokemon[defender_id].position,
                    )
                    self.assertEqual(attacker_state.hp, 0)
                    handled = True
                if not handled and move_key == "frustration":
                    damage_low, battle_low, _, _ = _damage_from_move(move, attacker_loyalty=1)
                    damage_high, battle_high, _, _ = _damage_from_move(move, attacker_loyalty=5)
                    db_low = _last_move_event(battle_low).get("effective_db", 0)
                    db_high = _last_move_event(battle_high).get("effective_db", 0)
                    self.assertGreater(db_low, db_high)
                    handled = True
                if not handled and move_key == "echoed voice":
                    damage_base, battle_base, _, _ = _damage_from_move(
                        move, battle_round=3, echoed_voice_rounds=[]
                    )
                    damage_boost, battle_boost, _, _ = _damage_from_move(
                        move, battle_round=3, echoed_voice_rounds=[2]
                    )
                    db_base = _last_move_event(battle_base).get("effective_db", 0)
                    db_boost = _last_move_event(battle_boost).get("effective_db", 0)
                    self.assertGreater(db_boost, db_base)
                    handled = True
                if not handled and move_key == "psywave":
                    damage, battle_full, _, _ = _damage_from_move(move)
                    last_event = _last_move_event(battle_full)
                    dealt = int(last_event.get("damage", 0) or 0)
                    self.assertTrue(dealt % 10 == 0 and 10 <= dealt <= 100)
                    handled = True
                if not handled and move_key == "helping hand":
                    battle_full, helper_id, ally_id, _ = _build_battle_with_ally(move)
                    battle_full.resolve_move_targets(
                        attacker_id=helper_id,
                        move=move,
                        target_id=ally_id,
                        target_position=battle_full.pokemon[ally_id].position,
                    )
                    ally_state = battle_full.pokemon[ally_id]
                    accuracy_bonus = any(
                        entry.get("kind") == "accuracy_bonus" and int(entry.get("amount", 0) or 0) >= 2
                        for entry in ally_state.temporary_effects
                        if isinstance(entry, dict)
                    )
                    damage_bonus = any(
                        entry.get("kind") == "damage_bonus" and int(entry.get("amount", 0) or 0) >= 10
                        for entry in ally_state.temporary_effects
                        if isinstance(entry, dict)
                    )
                    self.assertTrue(accuracy_bonus and damage_bonus)
                    handled = True

                if not handled:
                    gain_match = re.search(
                        r"gain(?:s)?\s+\+?(\d+)\s+(attack|special attack|special defense|defense|speed|accuracy|evasion)",
                        text,
                    )
                    if gain_match:
                        amount = int(gain_match.group(1))
                        stat = move_specials._normalize_stats(gain_match.group(2))[0]
                        attacker_state = attacker
                        self.assertEqual(attacker_state.combat_stages.get(stat), amount)
                        handled = True

                if not handled:
                    target_lower = re.search(
                        r"target'?s?\s+([\w\s/]+?)\s+is\s+lowered\s+by\s+\-?(\d+)\s+cs",
                        text,
                    )
                    if target_lower:
                        amount = -int(target_lower.group(2))
                        stats = move_specials._normalize_stats(target_lower.group(1))
                        for stat in stats:
                            self.assertEqual(defender.combat_stages.get(stat), amount)
                        handled = True

                if not handled:
                    self.fail(f"Unhandled move effect text (needs bespoke test): {text}")
