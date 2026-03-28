from __future__ import annotations

from auto_ptu.swsh_rulebook_parser import compile_swsh_rulebooks


def main() -> None:
    galardex, references = compile_swsh_rulebooks()
    print(
        f"Compiled SwSh datasets: "
        f"{galardex['species_count']} species, "
        f"{references['ability_count']} abilities, "
        f"{references['move_count']} moves, "
        f"{references['capability_count']} capabilities."
    )


if __name__ == "__main__":
    main()
