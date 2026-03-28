from __future__ import annotations

import time
from typing import Dict, List, Tuple

from .rich_compat import ensure_rich_unicode

ensure_rich_unicode()

from rich import box
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from multiprocessing.connection import Client


def _render_status(snapshot: dict) -> object:
    active_table = Table(
        "Mk",
        "Pokemon",
        "Trainer",
        "Team",
        "HP",
        "TempHP",
        "Inj",
        "InjPen",
        "Status",
        "Pos",
        "CS",
        "Abilities",
        "Stats",
        "Caps",
        box=None,
        expand=True,
    )
    bench_table = Table(
        "Mk",
        "Pokemon",
        "Trainer",
        "Team",
        "HP",
        "TempHP",
        "Inj",
        "InjPen",
        "Status",
        "Pos",
        "CS",
        "Abilities",
        "Stats",
        "Caps",
        box=None,
        expand=True,
    )
    for entry in snapshot.get("combatants", []):
        name = entry.get("name", "?")
        if entry.get("active"):
            name = f"{name} *"
        hp_bar = _format_hp_bar(entry.get("hp", "?"))
        row = [
            entry.get("marker", "?"),
            name,
            entry.get("trainer", entry.get("team", "?")),
            entry.get("team", "?"),
            hp_bar,
            entry.get("temp_hp", "0"),
            entry.get("injuries", "0"),
            entry.get("injury_penalty", "0"),
            entry.get("status", "-"),
            entry.get("pos", "-"),
            entry.get("cs", ""),
            entry.get("abilities", "-"),
            entry.get("stats", ""),
            entry.get("caps", "-"),
        ]
        if entry.get("active"):
            active_table.add_row(*row)
        else:
            bench_table.add_row(*row)
    renderables: List[object] = [active_table]
    if bench_table.row_count:
        renderables.append(Text("Party (Bench)", style="dim"))
        renderables.append(bench_table)
    if len(renderables) == 1:
        return renderables[0]
    return Group(*renderables)


def _format_hp_bar(hp_text: str, width: int = 12) -> Text:
    try:
        current_str, max_str = str(hp_text).split("/", 1)
        current = int(current_str)
        maximum = int(max_str)
    except Exception:
        return Text(str(hp_text))
    if maximum <= 0:
        return Text("?")
    current = max(0, current)
    maximum = max(1, maximum)
    pct = max(0.0, min(1.0, current / maximum))
    filled = int(round(pct * width))
    empty = max(0, width - filled)
    color = "green"
    if pct < 0.25:
        color = "red"
    elif pct < 0.5:
        color = "yellow"
    text = Text(f"{current}/{maximum} ", style="bold")
    text.append(f"[{'#' * filled}{'-' * empty}]", style=color)
    return text


def _render_grid(snapshot: dict) -> object:
    grid = snapshot.get("grid")
    if not grid:
        return Text("No grid.", style="dim")
    width = grid.get("width", 0)
    height = grid.get("height", 0)
    blockers = {tuple(coord) for coord in grid.get("blockers", [])}
    tiles: Dict[Tuple[int, int], str] = {}
    for entry in grid.get("tiles", []):
        if isinstance(entry, (list, tuple)) and len(entry) >= 3:
            tiles[(int(entry[0]), int(entry[1]))] = str(entry[2])
    occupants = {}
    for key, marker in snapshot.get("occupants", {}).items():
        if isinstance(key, str) and "," in key:
            x, y = key.split(",", 1)
            occupants[(int(x), int(y))] = marker
    current = tuple(snapshot.get("current_pos")) if snapshot.get("current_pos") else None
    table = Table(show_header=True, header_style="bold", box=box.ASCII)
    table.add_column("Y/X", justify="right")
    for x in range(width):
        table.add_column(f"{x:02d}", justify="center")
    for y in range(height):
        row = [f"{y:02d}"]
        for x in range(width):
            coord = (x, y)
            if coord in occupants:
                marker = occupants[coord]
                if current == coord:
                    row.append(f"[bold yellow]{marker}[/bold yellow]")
                else:
                    row.append(f"[cyan]{marker}[/cyan]")
            elif coord in blockers:
                row.append("[red]#[/red]")
            else:
                tile = tiles.get(coord, "")
                if tile == "water":
                    row.append("[blue]~[/blue]")
                elif tile in {"difficult", "rough"}:
                    row.append("[yellow]*[/yellow]")
                else:
                    row.append(".")
        table.add_row(*row)
    legend = snapshot.get("legend", "")
    return Group(table, Text(legend), Text("#=Blocker, ~=Water, *=Difficult"))


def run_viewer(port: int, auth_hex: str) -> None:
    authkey = bytes.fromhex(auth_hex)
    console = Console(force_terminal=True)
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="status", ratio=2),
        Layout(name="grid", ratio=3),
        Layout(name="info", ratio=1),
    )

    with Client(("127.0.0.1", port), authkey=authkey) as conn:
        with Live(layout, console=console, refresh_per_second=4, screen=True, transient=False):
            while True:
                if conn.poll(0.1):
                    message = conn.recv()
                    if not isinstance(message, dict):
                        continue
                    if message.get("type") == "close":
                        break
                    if message.get("type") != "snapshot":
                        continue
                    snap = message.get("data", {})
                    layout["status"].update(Panel(_render_status(snap), title="Status"))
                    layout["grid"].update(Panel(_render_grid(snap), title="Grid"))
                    info = snap.get("info", "")
                    layout["info"].update(Panel(Text(info, style="dim"), title="Info"))
                else:
                    time.sleep(0.05)
