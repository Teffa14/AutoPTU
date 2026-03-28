from __future__ import annotations

from auto_ptu.hisui_rulebook_parser import compile_hisui_rulebooks


def main() -> None:
    hisuidex, references = compile_hisui_rulebooks()
    print(
        f"Wrote Hisui datasets: {hisuidex['species_count']} species/forms, "
        f"{references['move_count']} moves, {references['ability_count']} abilities, "
        f"{references['capability_count']} capabilities."
    )


if __name__ == "__main__":
    main()
