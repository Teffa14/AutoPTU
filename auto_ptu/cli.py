"""Command line surface for Auto PTU."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

os.environ.setdefault("UNICODE_VERSION", "16.0.0")

import typer
from .rich_compat import ensure_rich_unicode

ensure_rich_unicode()

from rich.console import Console
from rich.table import Table

from .battle_state import InteractiveBattleState
from .csv_repository import PTUCsvRepository
from .data_loader import default_campaign, list_campaigns, load_builtin_campaign, load_campaign
from .engine import MatchEngine
from .gameplay import TextBattleSession
from .matchmaker import AutoMatchPlanner
from .random_campaign import CsvRandomCampaignBuilder
from .tools.session_logger import log_session
from .tools.auto_update import ensure_ability_log
from .tools.attack_tester import (
    describe_move_test,
    find_move_matches,
    list_moves,
    prompt_for_move_name,
)
from .tools.move_converter import ConversionRequest, LocalModelConfig, convert_to_move, request_from_payload
from .tools.move_regression import report_regression_suite
from .tools.battle_audit import run_audit_battle

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

app = typer.Typer(help="Local encounter automation for Pokemon Tabletop United")
force_terminal = True
if getattr(sys, "frozen", False):
    # Frozen console apps can report a console but fail to render ANSI reliably.
    force_terminal = False
console = Console(legacy_windows=False, force_terminal=force_terminal)

ensure_ability_log()

VALID_MODES = {"expectimax", "monte-carlo"}


def _safe_text(value: str | None) -> str:
    if not value:
        return ""
    return value.encode("ascii", "ignore").decode("ascii")


def _load_spec(hint: Optional[str]):
    if hint is None:
        return default_campaign(), "builtin:demo"
    path = Path(hint)
    if path.exists():
        return load_campaign(path), str(path)
    return load_builtin_campaign(hint), f"builtin:{hint}"


def describe_command(campaign: Optional[str] = None) -> None:
    spec, source = _load_spec(campaign)
    console.print(f"[bold]{spec.name}[/bold] ({source})")
    if spec.description:
        console.print(spec.description)
    console.print(spec.summary())


def _resolve_campaign_spec(
    campaign: Optional[str],
    random_battle: bool,
    team_size: int,
    csv_root: Optional[Path],
    min_level: int,
    max_level: int,
    seed: Optional[int],
):
    if random_battle:
        repo = PTUCsvRepository(csv_root)
        builder = CsvRandomCampaignBuilder(repo=repo, seed=seed)
        spec = builder.build(team_size=team_size, min_level=min_level, max_level=max_level)
        return spec, "csv-random"
    return _load_spec(campaign)


def _prompt_int(label: str, default: int, minimum: int = 1) -> int:
    while True:
        raw = console.input(f"{label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            console.print("[yellow]Enter a whole number.[/yellow]")
            continue
        if value < minimum:
            console.print(f"[yellow]Enter a value >= {minimum}.[/yellow]")
            continue
        return value


def _prompt_context(default: str = "full_contact") -> str:
    prompt = f"Battle context (L = league, F = full contact; default {default})"
    raw = console.input(f"{prompt}: ").strip().lower()
    if not raw:
        return default
    if raw in {"l", "league"}:
        return "league"
    if raw in {"f", "full", "full_contact", "full-contact"}:
        return "full_contact"
    console.print("[yellow]Unknown choice, using full_contact.[/yellow]")
    return "full_contact"


def _print_play_setup_summary(
    team_size: int, active_slots: int, battle_context: str
) -> None:
    bench_count = max(0, team_size - active_slots)
    console.print("[bold]Battle setup[/bold]")
    console.print(f"Team size per side: {team_size} (active + bench).")
    console.print(
        f"Active slots per side: {active_slots} (bench: {bench_count})."
    )
    if battle_context == "league":
        console.print(
            "Context: League. Trainers declare actions from slow to fast; "
            "declarations resolve before Pokemon act."
        )
    else:
        console.print("Context: Full contact. Normal initiative order.")
    console.print("You will choose starting Pokemon before round 1.")
    console.print("Switching uses a Standard action during your turn.")
    console.print("")


def run_command(
    campaign: Optional[str] = None,
    team_size: int = 1,
    tags: Optional[List[str]] = None,
    weather: Optional[str] = None,
    mode: str = "expectimax",
    depth: int = 6,
    sims: int = 600,
    export: Optional[Path] = None,
    seed: Optional[int] = None,
    random_battle: bool = False,
    min_level: int = 20,
    max_level: int = 40,
    csv_root: Optional[Path] = None,
) -> None:
    if mode not in VALID_MODES:
        raise typer.BadParameter(f"mode must be one of: {', '.join(sorted(VALID_MODES))}")
    if min_level > max_level:
        raise typer.BadParameter("min-level cannot be greater than max-level")
    spec, source = _resolve_campaign_spec(
        campaign=campaign,
        random_battle=random_battle,
        team_size=team_size,
        csv_root=csv_root,
        min_level=min_level,
        max_level=max_level,
        seed=seed,
    )
    session_campaign = spec.name if not random_battle else f"CSV Random ({spec.name})"
    log_session(
        mode="run",
        campaign=session_campaign,
        team_size=team_size,
        random_csv=random_battle,
        tags=tags,
        weather=weather or spec.default_weather,
        seed=seed,
    )
    planner = AutoMatchPlanner(spec, seed=seed)
    plan = planner.create_plan(team_size=team_size, prefer_tags=tags or [], weather=weather or spec.default_weather)
    engine = MatchEngine(plan)
    results = engine.run(mode=mode, depth=depth, sims=sims)
    console.print(f"Campaign [bold]{spec.name}[/bold] from {source}")
    console.print(f"Plan: {plan.describe()}")
    table = Table("Matchup", "Best First Move", "Notes", box=None)
    posts: List[str] = []
    for result in results:
        matchup_name = _safe_text(result.matchup.label or "Duel")
        payload = result.payload
        if mode == "monte-carlo":
            summary = ", ".join(
                f"{name}:{score:.2f}" for name, score in sorted(payload.items(), key=lambda x: x[1], reverse=True)[:3]
            )
            table.add_row(matchup_name, "Monte Carlo", _safe_text(summary))
        else:
            move = _safe_text(payload.get("best_first_move", "?"))
            pv = payload.get("principal_variation", [])
            table.add_row(matchup_name, move, _safe_text(pv[0] if pv else ""))
            if result.discord_post:
                posts.append(result.discord_post)
    console.print(table)
    if export and posts:
        export.write_text("\n\n".join(posts), encoding="utf-8")
        console.print(f"Saved Discord-ready output to {export}")


def play_command(
    campaign: Optional[str] = None,
    team_size: Optional[int] = None,
    active_slots: Optional[int] = None,
    battle_context: Optional[str] = None,
    tags: Optional[List[str]] = None,
    weather: Optional[str] = None,
    seed: Optional[int] = None,
    random_battle: bool = False,
    min_level: int = 20,
    max_level: int = 40,
    csv_root: Optional[Path] = None,
) -> None:
    if min_level > max_level:
        raise typer.BadParameter("min-level cannot be greater than max-level")
    if team_size is None:
        team_size = _prompt_int(
            "How many Pokemon per side (total roster, incl. bench)",
            default=1,
            minimum=1,
        )
    if active_slots is None:
        active_slots = _prompt_int(
            "How many start on the field (active slots)",
            default=1,
            minimum=1,
        )
    if active_slots > team_size:
        console.print("[yellow]Active slots cannot exceed team size; using team size instead.[/yellow]")
        active_slots = team_size
    if battle_context is None:
        battle_context = _prompt_context(default="full_contact")
    else:
        battle_context = str(battle_context).strip().lower()
        if battle_context in {"full", "full-contact"}:
            battle_context = "full_contact"
        if battle_context not in {"league", "full_contact"}:
            console.print("[yellow]Unknown context, using full_contact.[/yellow]")
            battle_context = "full_contact"
    _print_play_setup_summary(team_size, active_slots, battle_context)
    spec, source = _resolve_campaign_spec(
        campaign=campaign,
        random_battle=random_battle,
        team_size=team_size,
        csv_root=csv_root,
        min_level=min_level,
        max_level=max_level,
        seed=seed,
    )
    session_campaign = spec.name if not random_battle else f"CSV Random ({spec.name})"
    log_session(
        mode="play",
        campaign=session_campaign,
        team_size=team_size,
        random_csv=random_battle,
        tags=tags,
        weather=weather or spec.default_weather,
        seed=seed,
    )
    planner = AutoMatchPlanner(spec, seed=seed)
    plan = planner.create_plan(team_size=team_size, prefer_tags=tags or [], weather=weather or spec.default_weather)
    plan.active_slots = active_slots
    plan.battle_context = battle_context
    console.print(f"Campaign [bold]{spec.name}[/bold] from {source}")
    console.print("Pick moves from the list to play out the battle. Press Ctrl+C to quit early.\n")
    session = TextBattleSession(
        plan,
        console=console,
        viewer_enabled=True,
        spectator_enabled=False,
    )
    session.play()


def species_command(
    name: str,
    level: int = 20,
    nickname: Optional[str] = None,
    move_names: Optional[List[str]] = None,
    csv_root: Optional[Path] = None,
    export: Optional[Path] = None,
) -> None:
    repo = PTUCsvRepository(csv_root)
    if not repo.available():
        raise typer.BadParameter(f"CSV bundle not found under {repo.root}. Drop the Fancy PTU files there first.")
    try:
        pokemon = repo.build_pokemon_spec(name, level=level, move_names=move_names or None, nickname=nickname)
    except ValueError as exc:  # pragma: no cover - user input flow
        raise typer.BadParameter(str(exc)) from exc

    console.print(f"[bold]{pokemon.name}[/bold] level {pokemon.level} ({', '.join(pokemon.types)})")
    stats_table = Table("Stat", "Value")
    stats_table.add_row("HP", str(pokemon.hp_stat))
    stats_table.add_row("Attack", str(pokemon.atk))
    stats_table.add_row("Defense", str(pokemon.defense))
    stats_table.add_row("Sp. Attack", str(pokemon.spatk))
    stats_table.add_row("Sp. Defense", str(pokemon.spdef))
    stats_table.add_row("Speed", str(pokemon.spd))
    console.print(stats_table)

    moves_table = Table("Move", "Type", "Category", "DB", "Freq")
    for mv in pokemon.moves:
        moves_table.add_row(mv.name, mv.type, mv.category, str(mv.db), mv.freq)
    console.print(moves_table)

    if export:
        export.write_text(json.dumps(pokemon.to_engine_dict(), indent=2), encoding="utf-8")
        console.print(f"Wrote Pokemon data to {export}")


@app.command()
def campaigns(directory: Optional[Path] = typer.Option(None, "--dir", help="Directory to scan")) -> None:
    """List packaged or user-provided campaign files."""
    entries = list_campaigns(directory)
    if not entries:
        console.print("[yellow]No campaign files found.[/yellow]")
        return
    table = Table("Name", "Path")
    for name, path in entries.items():
        table.add_row(name, str(path))
    console.print(table)


@app.command()
def describe(campaign: Optional[str] = typer.Argument(None, help="Path or built-in name")) -> None:
    """Show high-level information about a campaign."""
    describe_command(campaign)


@app.command()
def run(
    campaign: Optional[str] = typer.Argument(None, help="Path or built-in name."),
    team_size: int = typer.Option(1, "--team-size", min=1, help="Number of mons to pull per side"),
    tag: List[str] = typer.Option([], "--tag", help="Prioritise player mons with these tags"),
    weather: Optional[str] = typer.Option(None, "--weather", help="Override weather"),
    mode: str = typer.Option("expectimax", "--mode", help="expectimax or monte-carlo"),
    depth: int = typer.Option(6, "--depth", help="Expectimax lookahead depth"),
    sims: int = typer.Option(600, "--sims", help="Monte Carlo simulations per move"),
    export: Optional[Path] = typer.Option(None, "--export", help="Write Discord posts to this file"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Seed for deterministic team selection"),
    random_battle: bool = typer.Option(False, "--random-battle", help="Sample mons directly from the CSV dataset"),
    min_level: int = typer.Option(20, "--min-level", help="Minimum level for random CSV mons"),
    max_level: int = typer.Option(40, "--max-level", help="Maximum level for random CSV mons"),
    csv_root: Optional[Path] = typer.Option(None, "--csv-root", help="Override path to the CSV bundle"),
) -> None:
    """Create a match plan and execute it."""
    run_command(
        campaign=campaign,
        team_size=team_size,
        tags=tag,
        weather=weather,
        mode=mode,
        depth=depth,
        sims=sims,
        export=export,
        seed=seed,
        random_battle=random_battle,
        min_level=min_level,
        max_level=max_level,
        csv_root=csv_root,
    )


@app.command()
def play(
    campaign: Optional[str] = typer.Argument(None, help="Path or built-in name."),
    team_size: Optional[int] = typer.Option(None, "--team-size", min=1, help="Number of mons to pull per side"),
    active_slots: Optional[int] = typer.Option(None, "--active-slots", min=1, help="Number of active mons per side"),
    battle_context: Optional[str] = typer.Option(None, "--context", help="league or full_contact"),
    tag: List[str] = typer.Option([], "--tag", help="Prioritise player mons with these tags"),
    weather: Optional[str] = typer.Option(None, "--weather", help="Override weather"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Seed for roster selection"),
    random_battle: bool = typer.Option(False, "--random-battle", help="Sample mons directly from the CSV dataset"),
    min_level: int = typer.Option(20, "--min-level", help="Minimum level for random CSV mons"),
    max_level: int = typer.Option(40, "--max-level", help="Maximum level for random CSV mons"),
    csv_root: Optional[Path] = typer.Option(None, "--csv-root", help="Override path to the CSV bundle"),
) -> None:
    """Launch interactive play where you pick moves turn-by-turn."""
    play_command(
        campaign=campaign,
        team_size=team_size,
        active_slots=active_slots,
        battle_context=battle_context,
        tags=tag,
        weather=weather,
        seed=seed,
        random_battle=random_battle,
        min_level=min_level,
        max_level=max_level,
        csv_root=csv_root,
    )


@app.command()
def snapshot(
    campaign: Optional[str] = typer.Argument(None, help="Path or built-in name."),
    team_size: int = typer.Option(1, "--team-size", min=1, help="Number of mons to pull per side"),
    tag: List[str] = typer.Option([], "--tag", help="Prioritise player mons with these tags"),
    weather: Optional[str] = typer.Option(None, "--weather", help="Override weather"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Seed for roster selection"),
    random_battle: bool = typer.Option(False, "--random-battle", help="Sample mons directly from the CSV dataset"),
    min_level: int = typer.Option(20, "--min-level", help="Minimum level for random CSV mons"),
    max_level: int = typer.Option(40, "--max-level", help="Maximum level for random CSV mons"),
    csv_root: Optional[Path] = typer.Option(None, "--csv-root", help="Override path to the CSV bundle"),
) -> None:
    """Show the current trainer/turn snapshot for an interactive matchup."""
    if min_level > max_level:
        raise typer.BadParameter("min-level cannot be greater than max-level")
    spec, source = _resolve_campaign_spec(
        campaign=campaign,
        random_battle=random_battle,
        team_size=team_size,
        csv_root=csv_root,
        min_level=min_level,
        max_level=max_level,
        seed=seed,
    )
    planner = AutoMatchPlanner(spec, seed=seed)
    plan = planner.create_plan(team_size=team_size, prefer_tags=tag or [], weather=weather or spec.default_weather)
    engine = MatchEngine(plan)
    matchup = plan.matchups[0]
    state = InteractiveBattleState(plan=plan, matchup=matchup, engine=engine, seed=seed)
    snapshot = state.snapshot()
    console.print(f"Campaign [bold]{spec.name}[/bold] from {source}")
    console.print(f"Battle: {matchup.label or 'Duel 1'} | Weather: {snapshot['weather']} | Status: {snapshot['status']}")
    turn = snapshot.get("turn") or {}
    turn_text = f"{turn.get('trainer_id') or '-'} ({turn.get('controller') or 'n/a'})"
    console.print(f"Current turn: {turn_text} -> token {turn.get('token_id') or '-'}")

    trainer_table = Table("Trainer", "Controller", "Team", "Active Pokemon", "HP")
    for trainer_entry in snapshot.get("trainers", []):
        active = next((mon for mon in trainer_entry.get("pokemon", []) if mon.get("active")), None)
        active_name = active.get("name") if active else "-"
        if active and active.get("hp") is not None and active.get("max_hp") is not None:
            hp_text = f"{active['hp']}/{active['max_hp']}"
        else:
            hp_text = "-"
        trainer_table.add_row(
            trainer_entry.get("name", trainer_entry.get("id", "?")),
            trainer_entry.get("controller", "?"),
            trainer_entry.get("team", "?"),
            active_name or "-",
            hp_text,
        )
    console.print(trainer_table)

    board = snapshot.get("board", {})
    tokens_table = Table("Token", "Role", "Trainer", "Position", "HP")
    for token in board.get("tokens", []):
        position = f"({token.get('x', '?')},{token.get('y', '?')})"
        hp_text = f"{token.get('hp', '?')}/{token.get('max_hp', '?')}"
        tokens_table.add_row(
            token.get("id", "?"),
            token.get("role", "?"),
            token.get("trainer_id", "?"),
            position,
            hp_text,
        )
    if board.get("tokens"):
        console.print(tokens_table)
    console.print(
        f"Grid: {board.get('width', '?')}x{board.get('height', '?')} • Movement budget: "
        f"{board.get('movement', {}).get('steps', 0)} steps (used: {board.get('movement', {}).get('used', False)})"
    )


@app.command()
def species(
    name: str = typer.Argument(..., help="Pokemon species name to pull from the CSV library"),
    level: int = typer.Option(20, "--level", help="Level to assign to the generated Pokemon"),
    nickname: Optional[str] = typer.Option(None, "--nickname", help="Optional nickname"),
    move: List[str] = typer.Option([], "--move", help="Explicit moves to load (defaults to type-matching moves)"),
    csv_root: Optional[Path] = typer.Option(None, "--csv-root", help="Override path to the CSV bundle"),
    export: Optional[Path] = typer.Option(None, "--export", help="Write the resulting Pokemon dict to this file"),
) -> None:
    """Build a PokemonSpec straight from the provided CSV sheets."""
    species_command(name=name, level=level, nickname=nickname, move_names=move, csv_root=csv_root, export=export)


@app.command("attack-test")
def attack_test(
    move: Optional[str] = typer.Argument(None, help="Move name (partial ok)"),
    seed: int = typer.Option(1, "--seed", help="Seed for deterministic rolls"),
    resolve_pending: bool = typer.Option(True, "--resolve-pending", help="Resolve set-up moves"),
    show_log: bool = typer.Option(False, "--show-log", help="Print the full battle log"),
    attacker_hp: Optional[int] = typer.Option(None, "--attacker-hp", help="Override attacker HP"),
    defender_hp: Optional[int] = typer.Option(None, "--defender-hp", help="Override defender HP"),
    attacker_status: List[str] = typer.Option([], "--attacker-status", help="Add attacker status"),
    defender_status: List[str] = typer.Option([], "--defender-status", help="Add defender status"),
    attacker_stage: List[str] = typer.Option([], "--attacker-stage", help="Set attacker combat stages, e.g. atk=2"),
    defender_stage: List[str] = typer.Option([], "--defender-stage", help="Set defender combat stages, e.g. def=-1"),
    defender_item: List[str] = typer.Option([], "--defender-item", help="Give defender items"),
    defender_food_buff: bool = typer.Option(False, "--defender-food-buff", help="Give defender a food buff"),
    defender_defense: Optional[int] = typer.Option(None, "--defender-defense", help="Override defender Defense stat"),
    defender_spdef: Optional[int] = typer.Option(None, "--defender-spdef", help="Override defender Special Defense stat"),
) -> None:
    """Run a single move against a dummy target and print the resulting log events."""
    names = list_moves()
    if move:
        exact = next((name for name in names if name.lower() == move.lower()), None)
        if exact:
            move = exact
        else:
            matches = find_move_matches(move, names, limit=8)
            if not matches:
                raise typer.BadParameter(f"No moves match '{move}'.")
            console.print("Matches:")
            for idx, name in enumerate(matches, start=1):
                console.print(f"  {idx}. {name}")
            choice = console.input("Pick a number, or press Enter to cancel: ").strip()
            if not choice:
                return
            if not choice.isdigit():
                raise typer.BadParameter("Please pick a number from the matches.")
            idx = int(choice) - 1
            if idx < 0 or idx >= len(matches):
                raise typer.BadParameter("Choice out of range.")
            move = matches[idx]
    else:
        move = prompt_for_move_name(names)
        if not move:
            return
    describe_move_test(
        move,
        seed=seed,
        resolve_pending=resolve_pending,
        show_log=show_log,
        attacker_hp=attacker_hp,
        defender_hp=defender_hp,
        attacker_statuses=attacker_status,
        defender_statuses=defender_status,
        defender_items=defender_item,
        defender_food_buff=defender_food_buff,
        attacker_stages=attacker_stage,
        defender_stages=defender_stage,
        defender_defense=defender_defense,
        defender_spdef=defender_spdef,
    )


@app.command("move-regression")
def move_regression(
    suite: Optional[Path] = typer.Option(None, "--suite", help="Path to move regression suite JSON"),
    seed: int = typer.Option(1, "--seed", help="Seed for deterministic rolls"),
    show_log: bool = typer.Option(False, "--show-log", help="Print the full battle log for each test"),
) -> None:
    """Run the move regression suite and report failures."""
    failures = report_regression_suite(path=suite, seed=seed, show_log=show_log)
    raise typer.Exit(code=1 if failures else 0)


@app.command("convert-move")
def convert_move(
    kind: str = typer.Option(..., "--kind", help="move, ability, or item"),
    name: str = typer.Option("", "--name", help="Source name, such as a move, ability, or item name"),
    text: str = typer.Option("", "--text", help="Freeform source text for the move, ability, or item"),
    movement_mode: str = typer.Option("", "--movement-mode", help="Deprecated legacy field; ignored for move conversions"),
    range_override: str = typer.Option("", "--range", help="Override the resulting PTU range text, e.g. 'Melee, 1 Target'"),
    keywords: str = typer.Option("", "--keywords", help="Comma-separated PTU keywords to add"),
    type_override: str = typer.Option("", "--type", help="Override the resulting move type"),
    category: str = typer.Option("", "--category", help="Override the resulting move category"),
    frequency: str = typer.Option("", "--frequency", help="Override the resulting move frequency"),
    db: Optional[int] = typer.Option(None, "--db", help="Override the resulting move DB"),
    stdin_json: bool = typer.Option(False, "--stdin-json", help="Read the request payload from stdin as JSON"),
    use_ai: bool = typer.Option(False, "--use-ai", help="Refine the move with a local model"),
    ai_provider: str = typer.Option("ollama", "--ai-provider", help="ollama or openai-compatible"),
    ai_model: str = typer.Option("", "--ai-model", help="Local model name"),
    ai_base_url: str = typer.Option("", "--ai-base-url", help="Base URL for the local model endpoint"),
    ai_api_key: str = typer.Option("", "--ai-api-key", help="Optional API key for the local endpoint"),
    ai_temperature: float = typer.Option(0.2, "--ai-temperature", help="Sampling temperature for AI refinement"),
) -> None:
    """Convert move, ability, or item inputs into a normalized PTU move JSON payload."""
    if stdin_json:
        payload = request_from_payload(json.loads(sys.stdin.read() or "{}"))
    else:
        payload = ConversionRequest(
            kind=str(kind).strip().lower(),  # type: ignore[arg-type]
            name=name,
            text=text,
            movement_mode=movement_mode,
            range_override=range_override,
            keywords_override=keywords,
            type_override=type_override,
            category_override=category,
            frequency_override=frequency,
            db_override=db,
            use_ai=use_ai,
            local_model=LocalModelConfig(
                enabled=use_ai,
                provider=ai_provider,
                model=ai_model,
                base_url=ai_base_url,
                api_key=ai_api_key,
                temperature=ai_temperature,
            ),
        )
    result = convert_to_move(payload)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("audit-battle")
def audit_battle(
    seed: int = typer.Option(1, "--seed", help="Seed for deterministic selection"),
    team_size: int = typer.Option(1, "--team-size", min=1, help="Team size per side"),
    min_level: int = typer.Option(20, "--min-level", help="Minimum level"),
    max_level: int = typer.Option(40, "--max-level", help="Maximum level"),
    max_turns: int = typer.Option(200, "--max-turns", help="Turn cap for the audit run"),
    depth: int = typer.Option(2, "--depth", help="AI lookahead depth"),
    top_k: int = typer.Option(4, "--top-k", help="AI top-K candidates"),
    top_m: int = typer.Option(2, "--top-m", help="AI opponent top-M"),
    rollouts: int = typer.Option(2, "--rollouts", help="AI rollout count"),
    randomize: bool = typer.Option(True, "--randomize/--no-randomize", help="Randomize teams/levels"),
    output: Optional[Path] = typer.Option(None, "--output", help="Write audit JSON to this path"),
) -> None:
    """Run a single AI vs AI battle and write a detailed audit log."""
    out_path = run_audit_battle(
        seed=seed,
        team_size=team_size,
        min_level=min_level,
        max_level=max_level,
        max_turns=max_turns,
        depth=depth,
        top_k=top_k,
        top_m=top_m,
        rollouts=rollouts,
        randomize=randomize,
        output=output,
    )
    console.print(f"Wrote audit to {out_path}")


if __name__ == "__main__":
    app()
