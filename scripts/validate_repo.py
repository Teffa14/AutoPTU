from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_check(command: list[str], *, optional: bool = False) -> bool:
    print(f"[validate] {' '.join(command)}")
    try:
        subprocess.run(command, cwd=REPO_ROOT, check=True)
    except FileNotFoundError:
        if optional:
            print(f"[validate] skipped; command not available: {command[0]}")
            return True
        print(f"[validate] missing required command: {command[0]}", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as exc:
        print(f"[validate] failed with exit code {exc.returncode}", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the standard AutoPTU validation checks."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full pytest suite instead of the default regression subset.",
    )
    parser.add_argument(
        "--skip-node",
        action="store_true",
        help="Skip the frontend syntax check.",
    )
    args = parser.parse_args()

    pytest_cmd = [sys.executable, "-m", "pytest", "-q"]
    if not args.full:
        pytest_cmd.extend(
            [
                "tests/test_trainer_passive_perks.py",
                "tests/test_web_regressions.py",
            ]
        )

    commands: list[tuple[list[str], bool]] = [(pytest_cmd, False)]
    if not args.skip_node:
        node_cmd = shutil.which("node")
        commands.append(
            ([node_cmd or "node", "--check", "auto_ptu/api/static/app.js"], True)
        )

    for command, optional in commands:
        if not run_check(command, optional=optional):
            return 1

    print("[validate] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
