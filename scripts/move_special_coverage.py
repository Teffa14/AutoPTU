import json
from pathlib import Path


def _parse_decorator(text: str, specials: set[str]) -> None:
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


def _collect_specials(paths: list[Path]) -> set[str]:
    specials: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        buf = []
        in_decorator = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("@register_move_special"):
                in_decorator = True
                buf = [stripped]
                if ")" in stripped:
                    in_decorator = False
                    _parse_decorator(" ".join(buf), specials)
                continue
            if in_decorator:
                buf.append(stripped)
                if ")" in stripped:
                    in_decorator = False
                    _parse_decorator(" ".join(buf), specials)
        if in_decorator and buf:
            _parse_decorator(" ".join(buf), specials)
    return specials


root = Path("auto_ptu/data/compiled/moves.json")
if not root.exists():
    raise SystemExit("moves.json not found")

moves = json.loads(root.read_text(encoding="utf-8"))
move_names = sorted({m.get("name", "").strip() for m in moves if m.get("name")})

files = [
    Path("auto_ptu/rules/hooks/move_specials.py"),
    Path("auto_ptu/rules/hooks/move_specials_items.py"),
]

specials = _collect_specials(files)

norm = lambda s: s.strip().lower()
move_set = {norm(n) for n in move_names}

special_covered = sorted(n for n in move_set if n in specials)
missing_special = sorted(n for n in move_set if n not in specials)

print(f"TOTAL MOVES: {len(move_set)}")
print(f"SPECIAL HANDLED: {len(special_covered)}")
print(f"NO SPECIAL HANDLER: {len(missing_special)}")

out = Path("reports")
out.mkdir(exist_ok=True)
report = out / "move_special_coverage.txt"
report.write_text(
    "TOTAL MOVES: %d\nSPECIAL HANDLED: %d\nNO SPECIAL HANDLER: %d\n\n"
    % (len(move_set), len(special_covered), len(missing_special))
    + "SPECIAL HANDLED (name):\n"
    + "\n".join(special_covered)
    + "\n\nNO SPECIAL HANDLER (name):\n"
    + "\n".join(missing_special)
    + "\n",
    encoding="utf-8",
)
print(f"Wrote {report}")
