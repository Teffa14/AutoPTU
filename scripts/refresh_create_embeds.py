import json
import re
from pathlib import Path


def refresh_embed(create_html: Path, json_path: Path) -> None:
    html = create_html.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    compact = json.dumps(payload, ensure_ascii=False)
    pattern = r'(<script id="character-data" type="application/json">)(.*?)(</script>)'
    updated, count = re.subn(pattern, r"\1" + compact + r"\3", html, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"character-data script block not found in {create_html}")
    create_html.write_text(updated, encoding="utf-8")


def main() -> None:
    root = Path(r"C:\Users\tefa1\AutoPTU")
    targets = [
        (
            root / "auto_ptu" / "api" / "static" / "create.html",
            root / "auto_ptu" / "api" / "static" / "character_creation.json",
        ),
        (
            root / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "create.html",
            root / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "character_creation.json",
        ),
        (
            root / "dist" / "AutoPTUCharacter" / "create.html",
            root / "dist" / "AutoPTUCharacter" / "character_creation.json",
        ),
        (
            root / "dist" / "AutoPTUWeb" / "_internal" / "auto_ptu" / "api" / "static" / "create.html",
            root / "dist" / "AutoPTUWeb" / "_internal" / "auto_ptu" / "api" / "static" / "character_creation.json",
        ),
        (
            root
            / "dist"
            / "AutoPTUWeb"
            / "_internal"
            / "auto_ptu"
            / "api"
            / "static"
            / "AutoPTUCharacter"
            / "create.html",
            root
            / "dist"
            / "AutoPTUWeb"
            / "_internal"
            / "auto_ptu"
            / "api"
            / "static"
            / "AutoPTUCharacter"
            / "character_creation.json",
        ),
    ]
    for create_html, json_path in targets:
        refresh_embed(create_html, json_path)
        print(f"updated {create_html}")


if __name__ == "__main__":
    main()
