import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from auto_ptu.ai_battles import run_ai_battles


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI vs AI random battles in parallel.")
    parser.add_argument("--total", type=int, default=10, help="Number of battles to run.")
    parser.add_argument("--seed", type=int, default=1, help="Starting seed.")
    parser.add_argument("--parallel", type=int, default=4, help="Worker processes.")
    parser.add_argument("--team-size", type=int, default=1, help="Pokemon per side.")
    parser.add_argument("--min-level", type=int, default=20, help="Minimum level.")
    parser.add_argument("--max-level", type=int, default=40, help="Maximum level.")
    parser.add_argument("--max-turns", type=int, default=1000, help="Turn limit per battle.")
    parser.add_argument("--depth", type=int, default=2, help="AI lookahead depth.")
    parser.add_argument("--top-k", type=int, default=4, help="AI candidate count.")
    parser.add_argument("--top-m", type=int, default=2, help="AI response count.")
    parser.add_argument("--rollouts", type=int, default=2, help="AI rollouts per action.")
    parser.add_argument(
        "--no-store",
        action="store_true",
        help="Disable writing simulation batch results to reports/simulations.",
    )
    parser.add_argument(
        "--store-dir",
        type=Path,
        default=None,
        help="Optional output directory for stored simulation batches.",
    )
    parser.add_argument(
        "--store-full-log",
        action="store_true",
        help="Store full per-turn battle logs for every match.",
    )
    parser.add_argument(
        "--randomize",
        action="store_true",
        help="Randomize seed/team size/levels per battle.",
    )
    args = parser.parse_args()

    return run_ai_battles(
        total=args.total,
        seed=args.seed,
        parallel=args.parallel,
        team_size=args.team_size,
        min_level=args.min_level,
        max_level=args.max_level,
        max_turns=args.max_turns,
        depth=args.depth,
        top_k=args.top_k,
        top_m=args.top_m,
        rollouts=args.rollouts,
        randomize=args.randomize,
        store_results=not args.no_store,
        store_dir=args.store_dir,
        store_full_log=args.store_full_log,
    )


if __name__ == "__main__":
    sys.exit(main())
