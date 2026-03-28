import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from statistics import median


STOP_WORDS = {
    "the",
    "and",
    "or",
    "to",
    "of",
    "a",
    "an",
    "is",
    "are",
    "for",
    "with",
    "on",
    "in",
    "by",
    "from",
    "at",
    "as",
    "this",
    "that",
    "it",
    "its",
    "their",
    "your",
    "user",
    "target",
    "effect",
    "trigger",
    "while",
    "when",
    "all",
    "may",
    "gain",
    "gains",
    "loses",
    "lose",
    "use",
    "used",
    "using",
    "within",
}

STATE_KEYWORDS = {
    "burn",
    "poison",
    "sleep",
    "frozen",
    "freeze",
    "paraly",
    "confus",
    "flinch",
    "trapped",
    "stuck",
    "vulnerable",
    "resist",
    "damage",
    "recoil",
    "critical",
    "crit",
    "evasion",
    "accuracy",
    "initiative",
    "priority",
    "combat",
    "stage",
    "speed",
    "attack",
    "defense",
    "special",
    "heals",
    "restore",
    "pp",
    "weather",
    "rain",
    "sun",
    "hail",
    "sand",
    "fog",
    "shield",
    "armor",
    "dr",
    "injury",
    "hit",
    "hp",
    "stat",
    "moves",
}

PLACEHOLDER_NAMES = {
    "body",
    "head",
    "feet",
    "hands",
    "off-hand",
    "accessory",
    "consumable",
    "item",
    "main + off hand",
    "body + head",
    "main hand",
}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9+ ]+", " ", (text or "").lower()).strip()


def tokens(text: str) -> set[str]:
    return {
        tok
        for tok in normalize(text).split()
        if len(tok) > 2 and tok not in STOP_WORDS
    }


def keyword_set(text: str) -> set[str]:
    n = normalize(text)
    return {k for k in STATE_KEYWORDS if k in n}


def family(name: str, text: str) -> str:
    s = (name + " " + text).lower()
    for key in [
        "berry",
        "ball",
        "orb",
        "seed",
        "gem",
        "plate",
        "incense",
        "booster",
        "brace",
        "armor",
        "shield",
        "vest",
        "scarf",
        "band",
        "claw",
        "fang",
        "rock",
        "powder",
        "herb",
        "potion",
        "medicine",
        "weather",
    ]:
        if key in s:
            return key
    return "other"


def parse_numeric_cost(value) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def load_foundry_core_gear(foundry_root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    core_dir = foundry_root / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-gear"
    for fp in core_dir.glob("*.json"):
        try:
            obj = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        name = (obj.get("name") or "").strip().lower()
        if not name:
            continue
        system = obj.get("system") or {}
        out[name] = {
            "grade": system.get("grade"),
            "cost": system.get("cost") if isinstance(system.get("cost"), (int, float)) else None,
        }
    return out


def build_pricing_model(data: dict, foundry_index: dict[str, dict]):
    priced = []
    for item in data["items"]["inventory"]:
        cost = parse_numeric_cost(item.get("cost"))
        if not cost or cost <= 0:
            continue
        text = (item.get("description", "") + " " + item.get("mod", "")).strip()
        name = item.get("name", "")
        lname = name.lower()
        fam = family(name, text)
        fmeta = foundry_index.get(lname, {})
        priced.append(
            {
                "name": name,
                "lname": lname,
                "cost": cost,
                "text": text,
                "fam": fam,
                "tok": tokens(name + " " + text),
                "kw": keyword_set(name + " " + text),
                "grade": fmeta.get("grade"),
                "foundry_cost": fmeta.get("cost"),
            }
        )

    exact_name = {p["lname"]: p["cost"] for p in priced}

    family_values: dict[str, list[int]] = {}
    for p in priced:
        family_values.setdefault(p["fam"], []).append(p["cost"])
    family_median = {k: int(median(v)) for k, v in family_values.items() if v}
    global_median = int(median([p["cost"] for p in priced]))

    grade_values: dict[str, list[int]] = {}
    for p in priced:
        if p["grade"]:
            grade_values.setdefault(p["grade"], []).append(p["cost"])
    grade_median = {k: int(median(v)) for k, v in grade_values.items() if v}

    # Calibrate Foundry numeric cost tiers to PTU prices by family when possible.
    foundry_family_cost_map: dict[str, dict[int, int]] = {}
    buckets: dict[tuple[str, int], list[int]] = {}
    for p in priced:
        if isinstance(p["foundry_cost"], (int, float)):
            key = (p["fam"], int(p["foundry_cost"]))
            buckets.setdefault(key, []).append(p["cost"])
    for (fam, tier), vals in buckets.items():
        if len(vals) >= 3:
            foundry_family_cost_map.setdefault(fam, {})[tier] = int(median(vals))

    return {
        "priced": priced,
        "exact_name": exact_name,
        "family_median": family_median,
        "global_median": global_median,
        "grade_median": grade_median,
        "foundry_family_cost_map": foundry_family_cost_map,
    }


def best_similarity_cost(name: str, text: str, model: dict):
    lname = name.lower().strip()
    if lname in model["exact_name"]:
        return model["exact_name"][lname], 1.0, "exact-name", name

    ntok = tokens(name + " " + text)
    nkw = keyword_set(name + " " + text)
    nfam = family(name, text)
    nname = normalize(name)

    candidates = [p for p in model["priced"] if p["fam"] == nfam]
    if len(candidates) < 20:
        candidates = model["priced"]

    best = None
    best_score = -1.0
    for cand in candidates:
        name_sim = SequenceMatcher(None, nname, normalize(cand["name"])).ratio()
        tok_j = len(ntok & cand["tok"]) / max(1, len(ntok | cand["tok"]))
        kw_j = len(nkw & cand["kw"]) / max(1, len(nkw | cand["kw"])) if (nkw or cand["kw"]) else 0
        score = 0.5 * name_sim + 0.35 * tok_j + 0.15 * kw_j
        if score > best_score:
            best = cand
            best_score = score

    if best_score >= 0.42:
        return best["cost"], best_score, "strong-sim", best["name"]
    if best_score >= 0.30:
        return best["cost"], best_score, "sim", best["name"]
    return None, best_score, "fallback", nfam


def assign_cost(item: dict, list_name: str, model: dict, foundry_index: dict[str, dict]) -> tuple[int, str]:
    name = item.get("name", "")
    text = (
        (item.get("description", "") or "")
        + " "
        + (item.get("buff", "") or "")
        + " "
        + (item.get("effect", "") or "")
        + " "
        + (item.get("mod", "") or "")
    ).strip()

    if (
        list_name == "inventory"
        and item.get("category") == "Foundry Gear"
        and not text
        and name.lower() in PLACEHOLDER_NAMES
    ):
        return 0, "placeholder"

    cost, _, method, _ = best_similarity_cost(name, text, model)
    if cost is not None:
        return int(cost), method

    lname = name.lower().strip()
    nfam = family(name, text)
    fmeta = foundry_index.get(lname, {})
    fcost = fmeta.get("cost")
    fgrade = fmeta.get("grade")

    family_tiers = model["foundry_family_cost_map"].get(nfam, {})
    if isinstance(fcost, (int, float)) and int(fcost) in family_tiers:
        return int(family_tiers[int(fcost)]), "foundry-tier"

    if fgrade and fgrade in model["grade_median"]:
        return int(model["grade_median"][fgrade]), "grade-med"

    if nfam in model["family_median"]:
        return int(model["family_median"][nfam]), "family-med"
    return int(model["global_median"]), "global-med"


def update_file(path: Path, foundry_index: dict[str, dict]) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    model = build_pricing_model(data, foundry_index)
    stats: dict[str, int] = {}

    for list_name in ["held_items", "food_items", "weather"]:
        for item in data["items"][list_name]:
            cost, method = assign_cost(item, list_name, model, foundry_index)
            item["cost"] = int(cost)
            stats[method] = stats.get(method, 0) + 1

    for item in data["items"]["inventory"]:
        raw_cost = item.get("cost")
        numeric_cost = parse_numeric_cost(raw_cost)
        needs_price = numeric_cost == 0 or (
            numeric_cost is None
            and isinstance(raw_cost, str)
            and raw_cost.strip() in {"", "--", "Varies", "varies"}
        )
        if needs_price:
            cost, method = assign_cost(item, "inventory", model, foundry_index)
            item["cost"] = int(cost)
            stats[method] = stats.get(method, 0) + 1

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Assign prices to zero-cost battle items.")
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Paths to character_creation.json files to update.",
    )
    parser.add_argument(
        "--foundry-root",
        default=r"C:\Users\tefa1\AutoPTU\Foundry",
        help="Foundry root that contains ptr2e core-gear pack JSON files.",
    )
    args = parser.parse_args()

    foundry_index = load_foundry_core_gear(Path(args.foundry_root))
    for raw in args.files:
        path = Path(raw)
        stats = update_file(path, foundry_index)
        print(path)
        print("  methods:", dict(sorted(stats.items(), key=lambda kv: kv[0])))


if __name__ == "__main__":
    main()
