"""Executable entry point for Auto PTU with a simple launcher menu."""
from __future__ import annotations

import os
import multiprocessing
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

os.environ.setdefault("UNICODE_VERSION", "16.0.0")

from auto_ptu import cli as cli_mod
from auto_ptu.ui_viewer import run_viewer
from auto_ptu.ai_battles import run_ai_battles
from auto_ptu.tools.move_regression import report_regression_suite
from auto_ptu.tools.battle_audit import run_audit_battle
from auto_ptu.config import CAMPAIGNS_DIR
from auto_ptu.data_loader import list_campaigns
from auto_ptu.matchmaker import AutoMatchPlanner
from auto_ptu.random_campaign import CsvRandomCampaignBuilder
from auto_ptu.rules import ai_hybrid

_KEYWORD_DEMOS: Optional[list[dict]] = None


def _pause(message: str = "Press Enter to return to the menu...") -> None:
    try:
        input(message)
    except EOFError:
        pass


def _prompt_int(prompt: str, default: int, minimum: int = 1, maximum: Optional[int] = None) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            pass
        else:
            if value >= minimum and (maximum is None or value <= maximum):
                return value
        print(f"Enter a number between {minimum} and {maximum or '∞'}.")


def _prompt_campaign() -> Optional[str]:
    console = cli_mod.console
    entries = list(list_campaigns().items())
    if entries:
        console.print("\n[bold]Built-in campaigns[/bold]:")
        for idx, (name, path) in enumerate(entries, start=1):
            console.print(f"  {idx}. {name} ({path.name})")
    console.print("\nEnter a number above, a built-in name, or a path to a JSON/YAML file.")
    raw = input("Campaign (blank to cancel): ").strip()
    if not raw:
        return None
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(entries):
            return entries[idx][0]
    if Path(raw).exists():
        return raw
    return raw


def _run_play_with_options(**kwargs) -> None:
    console = cli_mod.console
    try:
        cli_mod.play_command(**kwargs)
    except Exception as exc:  # pragma: no cover - user-facing pause
        console.print(f"[red]Error: {exc}[/red]")
        _pause()
        return
    _pause()


def _handle_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Auto PTU Demo[/bold] - Rainy grid training with full initiative logs, Start->Command->Action->End phases, blockers, water tiles, and live coordinate status.\n"
    )
    try:
        cli_mod.describe_command("demo_campaign")
    except Exception:
        pass
    _run_play_with_options(campaign="demo_campaign", team_size=1)


def _handle_multi_trainer_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Multi-Trainer Tag Battle[/bold] - Ash and Misty alternate turns independently against Jessie & James on the Cerulean bridge. Launches the `multi_trainer_demo` campaign with a 2v2 tag setup so you can watch the initiative queue juggle multiple player controllers.\n"
    )
    _run_play_with_options(campaign="multi_trainer_demo", team_size=2)    


def _handle_action_budget_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Action Budget Demo[/bold] - Single-opponent lab that spends your Standard action on `Tackle`, attempts another attack, and narrates why each bucket was consumed. Shift or pick another move to watch the `action` log remind you the slot was blocked while the round log still reports `Available actions`. Launches the `action_budget_demo` campaign."
    )
    _run_play_with_options(campaign="action_budget_demo", team_size=1)

def _handle_maneuver_lab_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Maneuver Lab[/bold] - Single arena showcasing combat maneuvers, intercepts, sprint/disengage, and item pickup for Attack of Opportunity. Launches the `maneuver_lab` campaign.\n"
    )
    _run_play_with_options(campaign="maneuver_lab", team_size=2)


def _handle_status_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Status & Push Lab[/bold] - Machop starts Paralyzed while Graveler tosses push-heavy rocks over blockers. Shows paralysis skips plus forced-movement logs. Launches the `status_demo` campaign.\n"
    )
    _run_play_with_options(campaign="status_demo", team_size=1)


def _handle_sleep_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Sleep Lab[/bold] - Snorlax begins Asleep for two rounds while Hypno showcases Hypnosis and Dream Eater so you can watch the persistent Sleep skip/wake logs. Launches the `sleep_demo` campaign.\n"
    )
    _run_play_with_options(campaign="sleep_demo", team_size=1)


def _handle_freeze_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Freeze Lab[/bold] - Froslass starts frozen while Articuno hurls Ice Shard so you can watch Freeze skip rolls and thaw logs after both random rolls and damage. Launches the `freeze_demo` campaign.\n"
    )
    _run_play_with_options(campaign="freeze_demo", team_size=1)


def _handle_poison_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Poison Lab[/bold] - Victreebel begins badly poisoned while Nidoqueen layers Toxic Spikes and Glare. Run `poison_demo` to watch the stacks grow each End phase and hear the increasing damage logs.\n"
    )
    _run_play_with_options(campaign="poison_demo", team_size=1)


def _handle_volatile_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Volatile Status Lab[/bold] - Hypno starts the fight confused while Primeape is flinched before its first punch. Launch `volatile_demo` to hear the new skip logs and see Hypno slam into itself while Primeape sits a turn out.\n"
    )
    _run_play_with_options(campaign="volatile_demo", team_size=1)


def _handle_shed_skin_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Shed Skin Lab[/bold] - Your Shed Skin user starts Burned while the foe keeps reapplying status moves so you can watch the end-phase rolls that cure statuses via the new ability hook.\n"
    )
    _run_play_with_options(campaign="shed_skin_demo", team_size=1)


def _handle_swift_swim_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Swift Swim Lab[/bold] - Rain floods the arena so your Swift Swim holder can race across every water tile while foes without it struggle to keep up. Launch `swift_swim_demo` to see the doubled swim range illustrated by the movement preview and logs.\n"
    )
    _run_play_with_options(campaign="swift_swim_demo", team_size=1)


def _handle_chlorophyll_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Chlorophyll Lab[/bold] - Sunlight brightens the field so your Chlorophyll user gets a free +2 overland movement before anything else happens. Run `chlorophyll_demo` to watch the movement preview show the boosted range.\n"
    )
    _run_play_with_options(campaign="chlorophyll_demo", team_size=1)


def _handle_levitate_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Levitate & Hazard Lab[/bold] - Ground hazards litter the center line while a Levitate user starts directly on the spikes, and foes must navigate Toxic Spikes, Stealth Rock, Sticky Web, and ground moves. Run `levitate_demo` to see the ability immunity logs next to every hazard tick.\n"
    )
    _run_play_with_options(campaign="levitate_demo", team_size=1)


def _handle_targeting_demo() -> None:
    console = cli_mod.console
    console.print(
        "[bold]Targeting Range Lab[/bold] - Purpose-built grid that highlights the color-coded in-range table, LOS blockers, and friendly-fire options added in v0.5. Run the `targeting_demo` campaign with two player Pokemon so the picker lists allies and foes with their new cues.\n"
    )
    _run_play_with_options(campaign="targeting_demo", team_size=2)


def _load_keyword_manifest() -> Optional[list[dict]]:
    global _KEYWORD_DEMOS
    if _KEYWORD_DEMOS is not None:
        return _KEYWORD_DEMOS
    manifest_path = CAMPAIGNS_DIR / "keyword_demos" / "_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    entries: list[dict] = []
    for entry in data.get("traits", []):
        if not isinstance(entry, dict):
            continue
        trait = entry.get("trait")
        campaign = entry.get("campaign")
        if not trait or not campaign:
            continue
        label = entry.get("label", trait)
        entries.append(
            {
                "trait": trait,
                "label": label,
                "campaign": campaign,
                "move": entry.get("move", ""),
                "_match": trait.lower(),
                "_label": label.lower(),
            }
        )
    _KEYWORD_DEMOS = entries
    return _KEYWORD_DEMOS


def _keyword_demo_menu() -> None:
    console = cli_mod.console
    manifest = _load_keyword_manifest()
    if not manifest:
        console.print(
            "[yellow]No keyword demos found. Run "
            "`python -m auto_ptu.tools.generate_keyword_demos` after syncing the Foundry data."
            "[/yellow]"
        )
        _pause()
        return
    console.print(
        "\n[bold cyan]Keyword Demos[/bold cyan]\n"
        "Enter a trait slug (e.g., `double-strike`), its number, type `list` to show all keywords, "
        "or `back` to return to the previous menu.\n"
    )
    while True:
        choice = input("Keyword selector: ").strip().lower()
        if choice in {"back", "b"} or not choice:
            break
        if choice in {"list", "l"}:
            for idx, entry in enumerate(manifest, start=1):
                move = f" ({entry['move']})" if entry.get("move") else ""
                console.print(f"{idx:>3}) {entry['trait']}{move}")
            continue
        selected: Optional[dict] = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(manifest):
                selected = manifest[idx]
        else:
            for entry in manifest:
                if choice == entry["_match"] or choice == entry["_label"]:
                    selected = entry
                    break
        if not selected:
            console.print("[yellow]Unknown keyword. Type `list` to review options.[/yellow]")
            continue
        console.print(
            f"\n[bold]{selected['label']}[/bold] – showcasing `{selected.get('move', 'unknown move')}` "
            f"(campaign `{selected['campaign']}`).\n"
        )
        _run_play_with_options(campaign=selected["campaign"], team_size=1)


def _handle_campaign() -> None:
    campaign = _prompt_campaign()
    if not campaign:
        return
    team_size = _prompt_int(
        "How many Pokemon per side (total roster, incl. bench)",
        default=1,
        minimum=1,
        maximum=6,
    )
    _run_play_with_options(campaign=campaign, team_size=team_size)


def _handle_random() -> None:
    team_size = _prompt_int(
        "How many Pokemon per side (total roster, incl. bench)",
        default=1,
        minimum=1,
        maximum=6,
    )
    min_level = _prompt_int(
        "Minimum level for the random roster",
        default=20,
        minimum=1,
        maximum=100,
    )
    max_level = _prompt_int(
        "Maximum level for the random roster",
        default=40,
        minimum=min_level,
        maximum=100,
    )
    _run_play_with_options(
        random_battle=True,
        team_size=team_size,
        min_level=min_level,
        max_level=max_level,
    )


def _handle_ai_vs_ai_batch() -> None:
    total = _prompt_int(
        "How many AI vs AI battles",
        default=10,
        minimum=1,
        maximum=5000,
    )
    try:
        import multiprocessing

        default_parallel = max(1, min(4, multiprocessing.cpu_count()))
    except Exception:
        default_parallel = 2
    parallel = _prompt_int(
        "Parallel workers",
        default=default_parallel,
        minimum=1,
        maximum=16,
    )
    depth = _prompt_int(
        "AI depth (higher = smarter, slower)",
        default=2,
        minimum=1,
        maximum=8,
    )
    top_k = _prompt_int(
        "AI top-k candidate actions",
        default=4,
        minimum=1,
        maximum=32,
    )
    top_m = _prompt_int(
        "AI top-m opponent replies",
        default=2,
        minimum=1,
        maximum=16,
    )
    rollouts = _prompt_int(
        "AI rollout count",
        default=2,
        minimum=1,
        maximum=24,
    )
    randomize = input("Randomize teams/levels per battle? [Y/n]: ").strip().lower()
    randomize_flag = randomize in {"", "y", "yes"}
    watch = input("Watch one AI vs AI battle first? [Y/n]: ").strip().lower()
    watch_flag = watch in {"", "y", "yes"}

    if randomize_flag:
        if watch_flag:
            import random as _random

            rng = _random.Random()
            rng.seed(int.from_bytes(os.urandom(8), "big"))
            team_size = rng.randint(1, 3)
            min_level = rng.randint(5, 50)
            max_level = min(60, min_level + rng.randint(0, 20))
            _run_ai_vs_ai_watch(
                team_size,
                min_level,
                max_level,
                depth=depth,
                top_k=top_k,
                top_m=top_m,
                rollouts=rollouts,
            )
            return
        run_ai_battles(
            total=total,
            parallel=parallel,
            randomize=True,
            depth=depth,
            top_k=top_k,
            top_m=top_m,
            rollouts=rollouts,
        )
        return

    team_size = _prompt_int(
        "How many Pokemon per side (total roster, incl. bench)",
        default=1,
        minimum=1,
        maximum=6,
    )
    min_level = _prompt_int(
        "Minimum level for the random roster",
        default=20,
        minimum=1,
        maximum=100,
    )
    max_level = _prompt_int(
        "Maximum level for the random roster",
        default=40,
        minimum=min_level,
        maximum=100,
    )
    if watch_flag:
        _run_ai_vs_ai_watch(
            team_size,
            min_level,
            max_level,
            depth=depth,
            top_k=top_k,
            top_m=top_m,
            rollouts=rollouts,
        )
        return
    run_ai_battles(
        total=total,
        parallel=parallel,
        randomize=False,
        team_size=team_size,
        min_level=min_level,
        max_level=max_level,
        depth=depth,
        top_k=top_k,
        top_m=top_m,
        rollouts=rollouts,
    )


def _handle_validation_tools() -> None:
    console = cli_mod.console
    while True:
        console.print(
            "\n[bold cyan]Validation Tools[/bold cyan]\n"
            "1) Run move regression suite\n"
            "2) Run single AI vs AI audit battle\n"
            "3) Back\n"
        )
        choice = input("Select an option: ").strip().lower()
        if choice in {"1", ""}:
            failures = report_regression_suite()
            console.print(f"Failures: {failures}")
            _pause()
        elif choice in {"2"}:
            seed = _prompt_int("Seed", default=1, minimum=1)
            max_turns = _prompt_int("Max turns", default=200, minimum=1, maximum=1000)
            out_path = run_audit_battle(seed=seed, max_turns=max_turns)
            console.print(f"Audit written to {out_path}")
            _pause()
        elif choice in {"3"}:
            break
        else:
            console.print("[yellow]Please choose an option number.[/yellow]")


def _run_ai_vs_ai_watch(
    team_size: int,
    min_level: int,
    max_level: int,
    *,
    depth: int = 2,
    top_k: int = 4,
    top_m: int = 2,
    rollouts: int = 2,
) -> None:
    ai_hybrid._DEFAULT_CONFIG.depth = depth
    ai_hybrid._DEFAULT_CONFIG.top_k = top_k
    ai_hybrid._DEFAULT_CONFIG.top_m = top_m
    ai_hybrid._DEFAULT_CONFIG.rollouts = rollouts
    builder = CsvRandomCampaignBuilder(seed=int.from_bytes(os.urandom(8), "big"))
    spec = builder.build(team_size=team_size, min_level=min_level, max_level=max_level)
    plan = AutoMatchPlanner(spec, seed=int.from_bytes(os.urandom(8), "big")).create_plan(
        team_size=team_size
    )
    for side in plan.matchups[0].sides:
        side.controller = "ai"
    session = cli_mod.TextBattleSession(
        plan,
        viewer_enabled=True,
        spectator_enabled=True,
    )
    session.play()


def _status_lab_menu() -> None:
    console = cli_mod.console
    while True:
        console.print(
            "\n[bold cyan]Status Labs[/bold cyan]\n"
            "1) Status & Push demo (Paralysis + forced movement)\n"
            "2) Sleep lab (persistent status showcase)\n"
            "3) Freeze lab (persistent freeze showcase)\n"
            "4) Poison lab (badly poisoned stacks)\n"
            "5) Volatile status lab (confusion + flinch)\n"
            "6) Back\n"
        )
        choice = input("Choose a status demo: ").strip().lower()
        if choice in {"1", "status", ""}:
            _handle_status_demo()
        elif choice == "2":
            _handle_sleep_demo()
        elif choice == "3":
            _handle_freeze_demo()
        elif choice == "4":
            _handle_poison_demo()
        elif choice == "5":
            _handle_volatile_demo()
        elif choice == "6":
            break
        else:
            console.print("[yellow]Please choose a status demo number.[/yellow]")


def _ability_lab_menu() -> None:
    console = cli_mod.console
    while True:
        console.print(
            "\n[bold cyan]Ability Labs[/bold cyan]\n"
            "1) Poison Heal lab (Poison-healing Crobat)\n"
            "2) Shed Skin lab (status-recovering Ninetales)\n"
            "3) Swift Swim lab (rainy swim corridor)\n"
            "4) Chlorophyll lab (sun-powered sprinter)\n"
            "5) Levitate & Hazard lab (ground hazards + immunity)\n"
            "6) Back\n"
        )
        choice = input("Choose an ability demo: ").strip().lower()
        if choice in {"1", "poison heal", ""}:
            _run_play_with_options(campaign="ability_demo", team_size=1)
        elif choice in {"2", "shed skin"}:
            _handle_shed_skin_demo()
        elif choice in {"3", "swift swim"}:
            _handle_swift_swim_demo()
        elif choice in {"4", "chlorophyll"}:
            _handle_chlorophyll_demo()
        elif choice in {"5", "levitate"}:
            _handle_levitate_demo()
        elif choice == "6":
            break
        else:
            console.print("[yellow]Please choose an ability demo number.[/yellow]")


def _moves_lab_menu() -> None:
    console = cli_mod.console
    while True:
        console.print(
            "\n[bold cyan]Moves & Targeting Labs[/bold cyan]\n"
            "1) Quick demo battle\n"
            "2) Targeting range lab (colored targeting table)\n"
            "3) Back\n"
        )
        choice = input("Choose a moves demo: ").strip().lower()
        if choice in {"1", ""}:
            _handle_demo()
        elif choice == "2":
            _handle_targeting_demo()
        elif choice == "3":
            break
        else:
            console.print("[yellow]Please choose a move demo number.[/yellow]")


def _other_demos_menu() -> None:
    console = cli_mod.console
    while True:
        console.print(
            "\n[bold cyan]Other Scenarios[/bold cyan]\n"
            "1) Multi-trainer demo (Ash & Misty tag battle)\n"
            "2) Action Budget demo (Standard/Shift action-budget lab)\n"
            "3) Maneuver lab\n"
            "4) Back\n"
        )
        choice = input("Choose an option: ").strip().lower()
        if choice in {"1", ""}:
            _handle_multi_trainer_demo()
        elif choice in {"2", "action budget", "action", "budget"}:
            _handle_action_budget_demo()
        elif choice in {"3", "maneuver", "maneuvers"}:
            _handle_maneuver_lab_demo()
        elif choice == "4":
            break
        else:
            console.print("[yellow]Please choose an option number.[/yellow]")


def _run_scenarios_menu() -> None:
    console = cli_mod.console
    while True:
        console.print(
            "\n[bold cyan]Scenario Launcher[/bold cyan]\n"
            "1) Status labs\n"
            "2) Ability labs\n"
            "3) Moves & targeting labs\n"
            "4) Keyword demos (per keyword campaign files)\n"
            "5) Other scenarios\n"
            "6) Back to main menu\n"
        )
        choice = input("Select a scenario group: ").strip().lower()
        if choice in {"1", ""}:
            _status_lab_menu()
        elif choice == "2":
            _ability_lab_menu()
        elif choice == "3":
            _moves_lab_menu()
        elif choice == "4":
            _keyword_demo_menu()
        elif choice == "5":
            _other_demos_menu()
        elif choice == "6":
            break
        else:
            console.print("[yellow]Please choose a scenario group number.[/yellow]")


def run_menu() -> None:
    console = cli_mod.console
    while True:
        console.print(
            "\n[bold cyan]Auto PTU Launcher[/bold cyan]\n"
            "1) Scenario demos\n"
            "2) Random battle from CSV data\n"
            "3) Play a campaign file\n"
            "4) AI vs AI random battles (batch)\n"
            "5) Validation tools\n"
            "6) Exit\n"
        )
        choice = input("Select an option: ").strip().lower()
        if choice in {"1", ""}:
            _run_scenarios_menu()
        elif choice == "2":
            _handle_random()
        elif choice == "3":
            _handle_campaign()
        elif choice == "4":
            _handle_ai_vs_ai_batch()
        elif choice in {"5"}:
            _handle_validation_tools()
        elif choice in {"6", "q", "quit", "exit"}:
            console.print("Goodbye!")
            break
        else:
            console.print("[yellow]Please choose a menu number.[/yellow]")


def main() -> None:
    multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--viewer":
        if len(sys.argv) < 4:
            return
        port = int(sys.argv[2])
        auth_hex = sys.argv[3]
        run_viewer(port, auth_hex)
        return
    if len(sys.argv) > 1:
        cli_mod.app()
    else:
        run_menu()


if __name__ == "__main__":
    main()
