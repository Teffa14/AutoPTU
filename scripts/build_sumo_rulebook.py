from __future__ import annotations

from auto_ptu.sumo_rulebook_parser import compile_sumo_rulebook


def main() -> None:
    references = compile_sumo_rulebook()
    print(
        f"Wrote SuMo references: {references['move_count']} moves, "
        f"{references['ability_count']} abilities, {references['capability_count']} capabilities."
    )


if __name__ == "__main__":
    main()
