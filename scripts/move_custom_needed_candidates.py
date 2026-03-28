import ast
import json
import re
from pathlib import Path


def _parse_string_container(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                values.append(elt.value)
        return values
    return []


def _collect_constant_sets(text: str) -> dict[str, list[str]]:
    consts: dict[str, list[str]] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return consts
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            name = node.targets[0].id
            values = _parse_string_container(node.value)
            if values:
                consts[name] = values
    return consts


def _parse_decorator(text: str, specials: set[str], consts: dict[str, list[str]]) -> None:
    start = text.find("(")
    end = text.rfind(")")
    if start == -1 or end == -1:
        return
    args = text[start + 1 : end]
    parts = []
    current = ""
    in_str = False
    quote = ""
    for ch in args:
        if ch in ("\"", "'"):
            if in_str and ch == quote:
                in_str = False
            elif not in_str:
                in_str = True
                quote = ch
        if ch == "," and not in_str:
            parts.append(current)
            current = ""
        else:
            current += ch
    if current:
        parts.append(current)
    for part in parts:
        part = part.strip()
        if part.startswith(("\"", "'")):
            name = part.strip().strip("\"").strip("'").strip().lower()
            if name:
                specials.add(name)
        else:
            if not part:
                continue
            const_name = part.split()[0].lstrip("*")
            if const_name in consts:
                for name in consts[const_name]:
                    cleaned = str(name).strip().lower()
                    if cleaned:
                        specials.add(cleaned)


def _collect_specials(paths: list[Path]) -> set[str]:
    specials: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        consts = _collect_constant_sets(text)
        buf = []
        in_decorator = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("@register_move_special"):
                in_decorator = True
                buf = [stripped]
                if ")" in stripped:
                    in_decorator = False
                    _parse_decorator(" ".join(buf), specials, consts)
                continue
            if in_decorator:
                buf.append(stripped)
                if ")" in stripped:
                    in_decorator = False
                    _parse_decorator(" ".join(buf), specials, consts)
        if in_decorator and buf:
            _parse_decorator(" ".join(buf), specials, consts)
    return specials


_MOVE_NAME_EQ_RE = re.compile(r"move_name\s*==\s*\"([^\"]+)\"")
_MOVE_NAME_IN_RE = re.compile(r"move_name\s*in\s*\{([^}]+)\}")
_STRING_RE = re.compile(r"\"([^\"]+)\"")


def _collect_core_handled(paths: list[Path]) -> set[str]:
    handled: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in _MOVE_NAME_EQ_RE.finditer(text):
            name = match.group(1).strip().lower()
            if name:
                handled.add(name)
        for match in _MOVE_NAME_IN_RE.finditer(text):
            raw = match.group(1)
            for s in _STRING_RE.findall(raw):
                name = s.strip().lower()
                if name:
                    handled.add(name)
    return handled


root = Path("auto_ptu/data/compiled/moves.json")
if not root.exists():
    raise SystemExit("moves.json not found")

moves = json.loads(root.read_text(encoding="utf-8"))

files = [
    Path("auto_ptu/rules/hooks/move_specials.py"),
    Path("auto_ptu/rules/hooks/move_specials_items.py"),
]

specials = _collect_specials(files)
core_handled = _collect_core_handled(
    [
        Path("auto_ptu/rules/battle_state.py"),
        Path("auto_ptu/rules/calculations.py"),
    ]
)

triggers = {
    "switch": ["switch", "swap", "pivot", "teleport", "voltswitch", "u-turn"],
    "copy": ["copy", "mimic", "sketch", "transform", "mirror", "metronome", "assist", "sleep talk"],
    "disable": ["disable", "encore", "taunt", "torment", "embargo", "imprison", "heal block"],
    "field": ["weather", "terrain", "room", "field", "tailwind", "safeguard", "mist"],
    "hazard": ["spikes", "stealth rock", "sticky web", "toxic spikes", "hazard"],
    "trap": ["trap", "bind", "cannot switch", "root", "ingrain"],
    "multi_turn": [
        "charging",
        "recharging",
        "two turns",
        "two-turn",
        "must recharge",
        "fly",
        "dig",
        "dive",
        "bounce",
        "phantom force",
        "shadow force",
        "sky drop",
    ],
    "delayed": ["future sight", "doom desire", "perish", "destiny bond", "wish"],
    "redirect": ["follow me", "rage powder", "spotlight"],
    "substitute": ["substitute"],
}

strict_triggers = {
    "action_timing": [
        "free action",
        "swift action",
        "full action",
        "interrupt",
        "reaction",
        "priority",
        "set-up",
        "setup",
        "resolution",
    ],
    "status": [
        "status",
        "inflict",
        "burn",
        "poison",
        "paralyze",
        "sleep",
        "freeze",
        "frostbite",
        "confuse",
        "flinch",
        "suppressed",
        "disabled",
        "trapped",
        "immobilized",
        "vulnerable",
        "slowed",
        "hindered",
        "blinded",
        "enraged",
        "infatuated",
        "cursed",
        "drowsy",
    ],
    "stages": ["combat stage", "stages", "accuracy", "evasion", "crit", "critical"],
    "healing": ["heal", "restore", "hit points", "hp", "injury", "injuries"],
    "recoil": ["recoil", "crash", "self-damage"],
    "multi_hit": ["multi-strike", "multi strike", "strike", "hits"],
    "movement": ["shift", "push", "pull", "trip", "grapple", "grab", "teleport"],
    "item_ability": ["item", "ability", "steal", "swap", "exchange"],
    "immunity": ["immune", "ignore", "cannot miss", "always hit", "resist"],
    "targeting": ["target's move", "last move", "swap", "switching"],
    "field": ["weather", "terrain", "room", "field", "hazard", "token"],
}

core_keywords = [
    "five strike",
    "double strike",
    "doublestrike",
    "triple strike",
    "multi-strike",
    "smite",
    "dash",
    "push",
    "recoil",
    "crash",
    "set-up",
    "setup",
    "resolution",
    "cannot miss",
    "always hit",
    "critical hit on",
    "burns",
    "poisons",
    "paralyzes",
    "freezes",
    "confuses",
    "flinches",
    "falls asleep",
    "raise the user's",
    "raise the target's",
    "lower the user's",
    "lower the target's",
    "priority",
    "swift action",
    "full action",
    "free action",
    "interrupt",
    "trigger",
    "reaction",
    "shield",
    "burst",
    "cone",
    "line",
    "close blast",
    "blessing",
    "coat",
    "aura",
    "sonic",
    "powder",
    "pass",
    "heal",
    "heals",
    "healing",
    "regains",
    "restores",
    "hit points",
    "hp",
    "injury",
]

likely = []
strict = []
for entry in moves:
    name = str(entry.get("name", "")).strip()
    if not name:
        continue
    lname = name.lower()
    if lname in specials or lname in core_handled:
        continue
    effects = str(entry.get("effects_text") or entry.get("effects") or entry.get("text") or "").lower()
    range_text = str(entry.get("range") or "").lower()
    combined = f"{lname} {range_text} {effects}"
    if not effects:
        continue
    hit = []
    for tag, words in triggers.items():
        for word in words:
            if word in combined:
                hit.append(tag)
                break
    if hit:
        likely.append((lname, sorted(set(hit)), effects))
    strict_hit = []
    for tag, words in strict_triggers.items():
        for word in words:
            if word in combined:
                strict_hit.append(tag)
                break
    if strict_hit:
        if any(token in combined for token in core_keywords):
            continue
        strict.append((lname, sorted(set(strict_hit)), combined))

out = Path("reports")
out.mkdir(exist_ok=True)
report = out / "move_custom_needed_candidates.txt"
lines = []
lines.append(f"TOTAL MOVES: {len({str(m.get('name','')).strip().lower() for m in moves if m.get('name')})}")
lines.append(f"SPECIAL HANDLED: {len(specials)}")
lines.append(f"CANDIDATES (no special + flagged text): {len(likely)}")
lines.append("")
for name, tags, text in sorted(likely):
    lines.append(f"{name} | {','.join(tags)} | {text}")
report.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {report} ({len(likely)} candidates)")

strict_report = out / "move_custom_needed_candidates_strict.txt"
strict_lines = []
strict_lines.append(f"TOTAL MOVES: {len({str(m.get('name','')).strip().lower() for m in moves if m.get('name')})}")
strict_lines.append(f"SPECIAL HANDLED: {len(specials)}")
strict_lines.append(f"CANDIDATES (strict heuristic): {len(strict)}")
strict_lines.append("")
for name, tags, text in sorted(strict):
    strict_lines.append(f"{name} | {','.join(tags)} | {text}")
strict_report.write_text("\n".join(strict_lines) + "\n", encoding="utf-8")
print(f"Wrote {strict_report} ({len(strict)} candidates)")
