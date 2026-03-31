from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Sync packaged AutoPTUWeb runtime assets.")
    parser.add_argument("target_root", help="Packaged _internal/auto_ptu target root")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    src_static = root / "auto_ptu" / "api" / "static"
    src_data = root / "auto_ptu" / "data"
    target_root = Path(args.target_root).resolve()

    copy_tree(src_static, target_root / "api" / "static")
    copy_tree(src_data, target_root / "data")
    print(f"[ok] synced packaged web runtime -> {target_root}")


if __name__ == "__main__":
    main()
