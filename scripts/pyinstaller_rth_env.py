import os
import sys
from pathlib import Path

os.environ.setdefault("UNICODE_VERSION", "16.0.0")


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def _env_join(paths: list[Path]) -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for path in paths:
        try:
            resolved = str(path.resolve())
        except Exception:
            resolved = str(path)
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        parts.append(str(path))
    return os.pathsep.join(parts)


bundle_root = _bundle_root()
runtime_root = _runtime_root()
portable_root = runtime_root / "portable_data"

for folder in (
    portable_root,
    portable_root / "sprites",
    portable_root / "pokeapi",
    portable_root / "pokeapi" / "type-icons",
    portable_root / "pokeapi" / "item-icons",
    portable_root / "pokeapi" / "cries",
    portable_root / "pokeapi" / "meta",
):
    folder.mkdir(parents=True, exist_ok=True)

if getattr(sys, "frozen", False):
    try:
        os.chdir(runtime_root)
    except Exception:
        pass

os.environ.setdefault("AUTO_PTU_RUNTIME_ROOT", str(runtime_root))
os.environ.setdefault("AUTO_PTU_BUNDLE_ROOT", str(bundle_root))
os.environ.setdefault("AUTO_PTU_SPRITE_DIR", str(portable_root / "sprites"))
os.environ.setdefault("AUTO_PTU_POKEAPI_CACHE", str(portable_root / "pokeapi"))

sprite_dirs = [
    runtime_root / "IMPLEMENTATION FILES" / "Generation 9 Pack v3.3.4" / "Graphics" / "Pokemon" / "Front",
    bundle_root / "IMPLEMENTATION FILES" / "Generation 9 Pack v3.3.4" / "Graphics" / "Pokemon" / "Front",
]
cry_dirs = [
    runtime_root / "IMPLEMENTATION FILES" / "Generation 9 Pack v3.3.4" / "Audio" / "SE" / "Cries",
    bundle_root / "IMPLEMENTATION FILES" / "Generation 9 Pack v3.3.4" / "Audio" / "SE" / "Cries",
]
item_icon_dirs = [
    runtime_root / "IMPLEMENTATION FILES" / "Generation 9 Pack v3.3.4" / "Graphics" / "Items",
    bundle_root / "IMPLEMENTATION FILES" / "Generation 9 Pack v3.3.4" / "Graphics" / "Items",
    runtime_root / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "static" / "img" / "item-icons",
    bundle_root / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "static" / "img" / "item-icons",
]
type_icon_dirs = [
    runtime_root / "PTUDatabase-main" / "PTUDataEditor" / "Resources" / "Types",
    bundle_root / "PTUDatabase-main" / "PTUDataEditor" / "Resources" / "Types",
]

sprite_env = _env_join(sprite_dirs)
cry_env = _env_join(cry_dirs)
item_env = _env_join(item_icon_dirs)
type_env = _env_join(type_icon_dirs)

if sprite_env:
    os.environ.setdefault("AUTO_PTU_LOCAL_SPRITE_DIRS", sprite_env)
if cry_env:
    os.environ.setdefault("AUTO_PTU_LOCAL_CRY_DIRS", cry_env)
if item_env:
    os.environ.setdefault("AUTO_PTU_LOCAL_ITEM_ICON_DIRS", item_env)
if type_env:
    os.environ.setdefault("AUTO_PTU_LOCAL_TYPE_ICON_DIRS", type_env)
