from __future__ import annotations

import shutil
from pathlib import Path


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing source directory: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    src_static = root / "auto_ptu" / "api" / "static"
    src_char = src_static / "AutoPTUCharacter"

    targets = [
        ("web-static", src_static, root / "dist" / "AutoPTUWeb" / "_internal" / "auto_ptu" / "api" / "static"),
        ("char-static", src_char, root / "dist" / "AutoPTUWeb" / "_internal" / "auto_ptu" / "api" / "static" / "AutoPTUCharacter"),
        ("standalone-char", src_char, root / "dist" / "AutoPTUCharacter"),
    ]

    for label, src, dst in targets:
        copy_tree(src, dst)
        print(f"[ok] synced {label}: {src} -> {dst}")


if __name__ == "__main__":
    main()
