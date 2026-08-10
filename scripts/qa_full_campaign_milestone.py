"""Play Prism League end-to-end through visible browser controls.

This is intentionally a real browser journey, not a compressed state simulation.
Every state-changing operation is performed by clicking or submitting the same
controls a player uses. Read-only GETs are used to wait for authoritative state
and to choose among currently visible legal battle targets.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


BASE_URL = os.environ.get("AUTO_PTU_QA_URL", "http://127.0.0.1:8766").rstrip("/")
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "reports" / "qa_milestone_runtime" / "full_campaign"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
REPORT_PATH = OUTPUT_DIR / f"playthrough-{RUN_ID}.json"
USER_DATA_DIR = OUTPUT_DIR / f"browser-profile-{RUN_ID}"
ACTIVE_REPORT: dict[str, Any] | None = None


def announce(message: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def browser_get(page: Page, path: str) -> dict[str, Any]:
    return page.evaluate(
        """async (path) => {
          const session = JSON.parse(localStorage.getItem('autoptu_campaign_session') || 'null');
          const headers = session?.participantToken ? {Authorization: `Bearer ${session.participantToken}`} : {};
          const response = await fetch(path, {headers, cache: 'no-store'});
          const payload = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(payload.detail || `GET ${path} failed (${response.status})`);
          return payload;
        }""",
        path,
    )


def campaign_state(page: Page) -> dict[str, Any]:
    session = page.evaluate("JSON.parse(localStorage.getItem('autoptu_campaign_session') || 'null')")
    if not session:
        raise AssertionError("Campaign session is missing from browser storage.")
    return browser_get(page, f"/api/campaigns/{session['campaignId']}")["campaign"]


def battle_state(page: Page) -> dict[str, Any]:
    return browser_get(page, "/api/state")


def wait_until(predicate, *, timeout: float = 30.0, interval: float = 0.25, label: str = "condition"):
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except Exception as exc:  # transient state while a page is navigating
            last_error = exc
        time.sleep(interval)
    suffix = f" Last error: {last_error}" if last_error else ""
    raise AssertionError(f"Timed out waiting for {label}.{suffix}")


def click_campaign_and_wait(page: Page, locator: Locator, *, label: str, timeout: float = 45.0) -> dict[str, Any]:
    before = int(campaign_state(page).get("revision") or 0)
    locator.scroll_into_view_if_needed()
    locator.click()
    result = wait_until(
        lambda: state if int((state := campaign_state(page)).get("revision") or 0) > before else None,
        timeout=timeout,
        label=label,
    )
    announce(f"Campaign action: {label} (revision {result['revision']})")
    return result


def connected_route(campaign: dict[str, Any], destination_id: str) -> list[str]:
    start = str((campaign.get("world") or {}).get("current_location_id") or "")
    if start == destination_id:
        return []
    by_id = {str(entry["id"]): entry for entry in campaign.get("locations") or []}
    queue: deque[tuple[str, list[str]]] = deque([(start, [])])
    visited = {start}
    while queue:
        current, path = queue.popleft()
        for neighbor in by_id.get(current, {}).get("neighbors") or []:
            neighbor = str(neighbor)
            if neighbor in visited:
                continue
            if neighbor == destination_id:
                return [*path, neighbor]
            visited.add(neighbor)
            queue.append((neighbor, [*path, neighbor]))
    raise AssertionError(f"No connected route from {start} to {destination_id}.")


def travel_to_scene(page: Page) -> None:
    state = campaign_state(page)
    destination = str((state.get("active_scene") or {}).get("metadata", {}).get("location_id") or "")
    if not destination:
        return
    for location_id in connected_route(state, destination):
        click_campaign_and_wait(
            page,
            page.locator(f'#travel-options [data-travel="{location_id}"]'),
            label=f"travel to {location_id}",
        )


def choose_fast_ollama_model(page: Page, report: dict[str, Any]) -> None:
    wait_until(lambda: page.locator("#agent-gm-model option").count() > 0, timeout=30, label="agent model options")
    options = page.locator("#agent-gm-model option").all_text_contents()
    preferred = next((name for name in options if name.strip() == "qwen2.5:3b"), options[0] if options else "")
    if preferred:
        page.locator("#agent-gm-model").select_option(label=preferred)
        if preferred in page.locator("#agent-player-model option").all_text_contents():
            page.locator("#agent-player-model").select_option(label=preferred)
    report["ollama_status"] = page.locator("#agent-ollama-state").inner_text()
    report["ollama_model"] = preferred
    announce(f"Agent runtime: {report['ollama_status']} · model {preferred or 'default'}")


def speak_to_visible_npc(page: Page, spoken: set[str], report: dict[str, Any]) -> None:
    form = page.locator("#npc-talk-form:not(.hidden)")
    if form.count() == 0:
        return
    select = form.locator("select[name='npc_id']")
    npc_id = select.input_value()
    if not npc_id or npc_id in spoken:
        return
    state = campaign_state(page)
    npc = next((entry for entry in state.get("actors") or [] if entry.get("id") == npc_id), {})
    scene_title = str((state.get("active_scene") or {}).get("title") or "this moment")
    question = (
        f"{npc.get('name', 'Friend')}, speak honestly in your own voice: what do you believe I must understand "
        f"about {scene_title}, and what are you unwilling to pretend you know?"
    )
    before_dialogue = len(state.get("dialogue") or [])
    select.select_option(npc_id)
    form.locator("textarea[name='text']").fill(question)
    form.locator("button[type='submit']").click()
    answered = wait_until(
        lambda: (
            latest
            if len((latest := campaign_state(page)).get("dialogue") or []) > before_dialogue
            and bool((latest.get("dialogue") or [])[-1].get("response"))
            else None
        ),
        timeout=240,
        interval=0.5,
        label=f"in-character answer from {npc.get('name', npc_id)}",
    )
    exchange = (answered.get("dialogue") or [])[-1]
    report["dialogue"].append(
        {
            "scene": scene_title,
            "npc": exchange.get("npc_name"),
            "question": exchange.get("text"),
            "response": exchange.get("response"),
            "source": exchange.get("source"),
            "model": exchange.get("model"),
        }
    )
    spoken.add(npc_id)
    announce(f"NPC answered in character: {exchange.get('npc_name')} ({exchange.get('source') or 'runtime'})")


def verify_handoff_and_realtime(page: Page, mirror: Page, report: dict[str, Any]) -> None:
    take_over = page.locator('[data-seat-control="agent-nova"][data-controller="human"]')
    state = click_campaign_and_wait(page, take_over, label="take over Nova's seat")
    nova = next(entry for entry in state["participants"] if entry["id"] == "agent-nova")
    assert nova["controller"] == "human"
    assert page.locator("#acting-seat").input_value() == "agent-nova"

    line = f"Nova tests the live handoff at {RUN_ID}: I choose courage with consent."
    before = int(state["revision"])
    page.locator("#chat-form textarea[name='text']").fill(line)
    page.locator("#chat-form button[type='submit']").click()
    wait_until(lambda: int(campaign_state(page).get("revision") or 0) > before, label="Nova's human action")
    wait_until(lambda: line in mirror.locator("#story-feed").inner_text(), timeout=15, label="WebSocket update in second page")
    report["websocket_second_page"] = True
    report["human_ai_handoff"] = True
    announce("Human/AI handoff and second-page WebSocket delivery verified.")

    hand_back = page.locator('[data-seat-control="agent-nova"][data-controller="ai"]')
    state = click_campaign_and_wait(page, hand_back, label="hand Nova back to AI")
    nova = next(entry for entry in state["participants"] if entry["id"] == "agent-nova")
    assert nova["controller"] == "ai"


def sync_builder_through_ui(page: Page, mirror: Page, report: dict[str, Any]) -> None:
    before = int(campaign_state(mirror).get("revision") or 0)
    page.goto(f"{BASE_URL}/create?scenario=legal", wait_until="domcontentloaded", timeout=120_000)
    page.locator("#char-content").wait_for(state="visible", timeout=120_000)
    page.locator("#char-save-local").click()
    page.locator("#char-save-campaign").click()
    state = wait_until(
        lambda: current if int((current := campaign_state(mirror)).get("revision") or 0) > before else None,
        timeout=90,
        label="builder sync campaign event",
    )
    report["builder_sync"] = True
    report["persistent_actor_count_after_builder"] = len(state.get("actors") or [])
    announce("Trainer builder synced through its visible campaign control.")
    page.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded", timeout=120_000)
    page.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=60_000)


def resolve_prompt_or_interrupt(page: Page, snapshot: dict[str, Any]) -> bool:
    if snapshot.get("pending_prompts"):
        page.locator("#prompt-overlay:not(.hidden)").wait_for(timeout=15_000)
        choices = page.locator("#prompt-list .prompt-choice")
        for index in range(choices.count()):
            choice = choices.nth(index)
            no = choice.get_by_role("button", name=re.compile(r"^(No|Decline|Pass)$", re.I))
            if no.count():
                no.first.click()
            else:
                choice.locator("button").last.click()
        page.locator("#prompt-resolve").click()
        announce("Resolved a prompted rules choice through the battle modal.")
        return True
    window = (snapshot.get("command_center") or {}).get("interrupt_window")
    if window:
        page.locator("#interrupt-window:not(.hidden)").wait_for(timeout=15_000)
        while page.locator("#interrupt-window .interrupt-response-form").count():
            row = page.locator("#interrupt-window .interrupt-response-form").first
            row.get_by_role("button", name="Pass").click()
            time.sleep(0.15)
        if page.locator("#interrupt-resolve:not([disabled])").count():
            page.locator("#interrupt-resolve").click()
        else:
            page.locator("#interrupt-close").click()
        announce("Resolved the reaction stack through visible controls.")
        return True
    return False


def numeric_db(move: dict[str, Any]) -> int:
    match = re.search(r"\d+", str(move.get("db") or ""))
    return int(match.group(0)) if match else 0


def wait_battle_progress(
    page: Page,
    old_log_size: int,
    *,
    old_actor_id: str = "",
    timeout: float = 120.0,
) -> dict[str, Any]:
    return wait_until(
        lambda: (
            current
            if len((current := battle_state(page)).get("log") or []) > old_log_size
            or (old_actor_id and str(current.get("current_actor_id") or "") != old_actor_id)
            or current.get("battle_over")
            or current.get("winner_team")
            or (current.get("command_center") or {}).get("interrupt_window")
            or current.get("pending_prompts")
            else None
        ),
        timeout=timeout,
        interval=0.3,
        label="battle action resolution",
    )


def human_battle_action(page: Page, snapshot: dict[str, Any]) -> str:
    old_log_size = len(snapshot.get("log") or [])
    old_actor_id = str(snapshot.get("current_actor_id") or "")
    if snapshot.get("trainer_turn"):
        page.locator("#turn-end:not([disabled])").click()
        wait_battle_progress(page, old_log_size, old_actor_id=old_actor_id)
        return "human trainer ended turn"

    actor_id = str(snapshot.get("current_actor_id") or "")
    actor = next(entry for entry in snapshot.get("combatants") or [] if str(entry.get("id")) == actor_id)
    moves = sorted(actor.get("moves") or [], key=lambda move: (-numeric_db(move), str(move.get("name") or "")))
    for move in moves:
        name = str(move.get("name") or "")
        targets = list((snapshot.get("move_targets") or {}).get(name) or [])
        button = page.locator("#turn-quick-moves button", has_text=name)
        if not targets or not button.count() or not button.first.is_enabled():
            continue
        button.first.click()
        targetable = page.locator("#grid .cell.targetable")
        try:
            targetable.first.wait_for(timeout=3_000)
        except PlaywrightTimeoutError:
            page.keyboard.press("Escape")
            continue
        target_id = next((value for value in targets if value is not None), None)
        if target_id is not None:
            target_coords = [
                key.split(",", 1)
                for key, occupant_id in (snapshot.get("occupants") or {}).items()
                if occupant_id == target_id and "," in key
            ]
            target_cell = None
            for x, y in target_coords:
                candidate = page.locator(f'#grid .cell.targetable[data-x="{x}"][data-y="{y}"]')
                if candidate.count():
                    target_cell = candidate.first
                    break
            (target_cell if target_cell is not None else targetable.first).click(force=True)
        else:
            target_tile = page.locator("#grid .cell.targetable:not(.occupied)").first
            if not target_tile.count():
                target_tile = targetable.first
            target_tile.click(force=True)
        try:
            wait_battle_progress(page, old_log_size, old_actor_id=old_actor_id, timeout=12)
        except AssertionError:
            # A cinematic re-render can invalidate the exact DOM cell between
            # arming and clicking. Cancel the visible targeting mode and try
            # the next legal control rather than treating no submission as a
            # rules-engine stall.
            page.keyboard.press("Escape")
            continue
        return f"human used {name}"

    shift_button = page.locator("#turn-move:not([disabled])")
    shifts = [list(coord) for coord in snapshot.get("legal_shifts") or []]
    current = list(snapshot.get("current_pos") or [])
    shifts = [coord for coord in shifts if coord != current]
    if shift_button.count() and shifts:
        enemies = [
            entry
            for entry in snapshot.get("combatants") or []
            if entry.get("team") != actor.get("team") and int(entry.get("hp") or 0) > 0 and entry.get("position")
        ]
        shifts.sort(
            key=lambda coord: (
                min(
                    (abs(int(coord[0]) - int(enemy["position"][0])) + abs(int(coord[1]) - int(enemy["position"][1])) for enemy in enemies),
                    default=0,
                ),
                int(coord[1]),
                int(coord[0]),
            )
        )
        x, y = shifts[0]
        shift_button.click()
        shift_cell = page.locator(f'#grid .cell.in-range[data-x="{x}"][data-y="{y}"]')
        if not shift_cell.count():
            page.keyboard.press("Escape")
        else:
            shift_cell.click(force=True)
        try:
            wait_battle_progress(page, old_log_size, old_actor_id=old_actor_id, timeout=12)
            return f"human shifted to {x},{y}"
        except AssertionError:
            page.keyboard.press("Escape")

    page.locator("#turn-end:not([disabled])").click()
    wait_battle_progress(page, old_log_size, old_actor_id=old_actor_id)
    return "human ended turn"


def verify_command_stack(page: Page, report: dict[str, Any]) -> None:
    page.locator("#reaction-registry-panel summary").click()
    page.locator("#reaction-name").fill("QA Damage Reflex")
    page.locator("#reaction-event").fill("damage")
    page.locator("#reaction-actor").select_option(index=0)
    page.locator("#reaction-register").click()
    wait_until(lambda: int(page.locator("#reaction-registry-count").inner_text()) >= 1, label="reaction registry row")
    report["reaction_registry_ui"] = True

    page.locator("#interrupt-trigger").fill("QA consent reaction window")
    page.locator("#interrupt-open").click()
    wait_until(lambda: page.locator("#interrupt-window:not(.hidden)").count(), label="manual reaction window")
    snapshot = battle_state(page)
    resolve_prompt_or_interrupt(page, snapshot)
    report["manual_interrupt_ui"] = True

    old_actor = str(battle_state(page).get("current_actor_id") or "")
    page.locator("#turn-plan").click()
    wait_until(lambda: page.locator("#command-queue-mode").is_checked(), label="planning mode")
    page.locator("#turn-end:not([disabled])").click()
    wait_until(lambda: page.locator("#command-queue .command-row").count() == 1, label="queued declaration")
    page.locator("#command-resolve-next").click()
    wait_until(
        lambda: str(battle_state(page).get("current_actor_id") or "") != old_actor
        or page.locator("#command-queue .command-row").count() == 0,
        label="queued declaration resolution",
    )
    if page.locator("#command-queue-mode").is_checked():
        page.locator("#turn-plan").click()
    report["queued_action_ui"] = True
    announce("Queue, manual interrupt, and automatic reaction registry verified on the tactical board.")


def play_battle(page: Page, scene: dict[str, Any], report: dict[str, Any], *, first: bool) -> None:
    title = str(scene.get("title") or scene.get("id"))
    announce(f"Entering tactical encounter: {title}")
    page.locator("#open-battle-link").click()
    page.wait_for_url(re.compile(r"/$"), timeout=180_000)
    page.locator("#turn-controller:not(.hidden)").wait_for(timeout=180_000)
    if page.locator("#cinematic-speed").count():
        page.locator("#cinematic-speed").select_option("fast")
    snapshot = battle_state(page)
    assert (snapshot.get("battle_identity") or {}).get("bound") is True
    assert (snapshot.get("battle_identity") or {}).get("role") == "gm"
    assert page.locator("#battle-role").is_disabled()
    if first:
        page.screenshot(path=str(OUTPUT_DIR / f"battle-board-{RUN_ID}.png"), full_page=True)
        verify_command_stack(page, report)

    started = time.monotonic()
    agent_sources: dict[str, int] = {}
    actions: list[str] = []
    for step in range(1, 601):
        snapshot = battle_state(page)
        if snapshot.get("battle_over") or snapshot.get("winner_team"):
            break
        if resolve_prompt_or_interrupt(page, snapshot):
            continue
        actor_id = str(snapshot.get("current_actor_id") or "")
        if actor_id == "gm" or actor_id.startswith("gm-"):
            detail = human_battle_action(page, snapshot)
            actions.append(detail)
        else:
            agent_button = page.locator("#turn-agent:not([disabled])")
            http_error_count = len(report["http_errors"])
            agent_button.click()
            try:
                page.locator("#turn-agent.is-thinking").wait_for(timeout=3_000)
            except PlaywrightTimeoutError:
                # Very fast local responses can complete between Playwright's
                # click acknowledgement and the first DOM observation.
                pass
            page.wait_for_function(
                """() => {
                  const button = document.querySelector('#turn-agent');
                  return button && !button.classList.contains('is-thinking');
                }""",
                timeout=180_000,
            )
            # Read the authoritative result after the visible request lifecycle
            # completes. PTU may legitimately retain the same initiative actor
            # without appending a log row (for example, duplicated initiative).
            battle_state(page)
            if len(report["http_errors"]) > http_error_count:
                latest_error = report["http_errors"][-1]
                raise AssertionError(
                    f"Agent battle request failed with HTTP {latest_error['status']} at {latest_error['url']}."
                )
            notice = page.locator("#ui-notifications").inner_text() if page.locator("#ui-notifications").count() else ""
            source = "ollama" if "ollama" in notice.lower() else "agent-runtime"
            agent_sources[source] = agent_sources.get(source, 0) + 1
            actions.append(f"AI acted for {actor_id}")
        if step % 12 == 0:
            latest = battle_state(page)
            announce(
                f"{title}: {step} visible actions · round {latest.get('round')} · "
                f"active {latest.get('current_actor_id')}"
            )
    else:
        raise AssertionError(f"{title} did not complete within 600 visible battle actions.")

    final = battle_state(page)
    winner = str(final.get("winner_team") or "")
    if winner != "players":
        raise AssertionError(f"Party did not win {title}; authoritative winner was {winner or 'none'}.")
    victory_button = page.get_by_role("button", name="Record victory & return")
    try:
        victory_button.wait_for(timeout=10_000)
    except PlaywrightTimeoutError:
        # A long cinematic queue can finish after the authoritative victory
        # response. Reloading is a normal browser recovery and must reproduce
        # the same persistent result controls from server state.
        announce("Victory state is authoritative; reloading the board to recover delayed result controls.")
        page.reload(wait_until="domcontentloaded", timeout=120_000)
        page.locator("#turn-controller:not(.hidden)").wait_for(timeout=120_000)
        victory_button = page.get_by_role("button", name="Record victory & return")
        victory_button.wait_for(timeout=60_000)
    victory_button.click()
    page.wait_for_url(re.compile(r"/campaign$"), timeout=120_000)
    page.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=60_000)
    completed = wait_until(
        lambda: state if (state := campaign_state(page)).get("active_scene", {}).get("metadata", {}).get("battle_completed") else None,
        timeout=60,
        label=f"persistent completion of {title}",
    )
    report["battles"].append(
        {
            "scene_id": scene.get("id"),
            "title": title,
            "winner": winner,
            "rounds": final.get("round"),
            "visible_actions": len(actions),
            "duration_seconds": round(time.monotonic() - started, 2),
            "agent_sources": agent_sources,
            "campaign_revision": completed.get("revision"),
        }
    )
    announce(f"Victory recorded: {title} in {len(actions)} actions / {final.get('round')} rounds.")


def exercise_world_controls(page: Page, report: dict[str, Any]) -> None:
    def click_world_button(pattern: str, key: str) -> None:
        buttons = page.locator("#world-actions button:not([disabled])")
        labels = buttons.all_text_contents()
        index = next((i for i, text in enumerate(labels) if re.search(pattern, text, re.I)), None)
        if index is None:
            raise AssertionError(f"Expected visible world control for {key}.")
        before = int(campaign_state(page).get("revision") or 0)
        buttons.nth(index).click()
        wait_until(lambda: int(campaign_state(page).get("revision") or 0) > before, timeout=45, label=key)
        report["world_controls"][key] = True
        announce(f"World control used: {key}")

    # Field Poultice requires two Herbs. Buy both through the visible shop UI
    # before asking the visible crafting control to consume them.
    click_world_button(r"Buy Herb", "shopping")
    click_world_button(r"Buy Herb", "shopping_second_ingredient")
    click_world_button(r"Craft Field Poultice", "crafting")
    click_world_button(r"Recover party", "downtime_recover")
    click_world_button(r"Train partner", "downtime_train")


def run() -> dict[str, Any]:
    global ACTIVE_REPORT
    report: dict[str, Any] = {
        "run_id": RUN_ID,
        "base_url": BASE_URL,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "browser": "chromium",
        "battles": [],
        "dialogue": [],
        "world_controls": {},
        "console_errors": [],
        "page_errors": [],
        "http_errors": [],
    }
    ACTIVE_REPORT = report
    started = time.monotonic()
    spoken: set[str] = set()
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(USER_DATA_DIR),
            headless=True,
            viewport={"width": 1536, "height": 960},
            reduced_motion="no-preference",
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(30_000)
        page.on("console", lambda message: report["console_errors"].append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
        page.on(
            "response",
            lambda response: report["http_errors"].append({"status": response.status, "url": response.url})
            if response.status >= 400 and "/api/" in response.url
            else None,
        )

        announce("Opening the real campaign start screen.")
        page.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded", timeout=120_000)
        page.locator("#campaign-starter-form input[name='player_name']").fill("Avery Prism")
        page.locator("#campaign-starter-form select[name='play_mode']").select_option("director")
        page.locator("#campaign-starter").click()
        page.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=180_000)
        state = campaign_state(page)
        report["campaign_id"] = state["id"]
        report["initial_revision"] = state["revision"]
        report["initial_scene_count"] = len(state.get("scenes") or [])
        report["initial_actor_count"] = len(state.get("actors") or [])
        assert report["initial_scene_count"] == 14
        assert len(state.get("participants") or []) == 5
        page.screenshot(path=str(OUTPUT_DIR / f"campaign-starter-{RUN_ID}.png"), full_page=True)
        assert page.locator("#campaign-continue").is_disabled(), "Starter gate should prevent premature continuation."
        announce(f"Fresh populated campaign created with {report['initial_actor_count']} persistent actors.")

        mirror = context.new_page()
        mirror.set_default_timeout(30_000)
        mirror.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded", timeout=120_000)
        mirror.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=60_000)

        choose_fast_ollama_model(page, report)
        speak_to_visible_npc(page, spoken, report)
        click_campaign_and_wait(page, page.locator('[data-starter="Bulbasaur"]'), label="select Bulbasaur")
        verify_handoff_and_realtime(page, mirror, report)

        before_round = int(campaign_state(page).get("revision") or 0)
        page.locator("#agent-round").click()
        round_state = wait_until(
            lambda: current if int((current := campaign_state(page)).get("revision") or 0) >= before_round + 4 else None,
            timeout=300,
            interval=0.5,
            label="GM and three AI companion turns",
        )
        report["agent_party_round"] = int(round_state["revision"]) - before_round
        announce("Ollama GM and all three companion seats completed a campaign round.")

        sync_builder_through_ui(page, mirror, report)
        mirror.close()

        first_battle = True
        visited_scenes: set[str] = set()
        world_exercised = False
        while True:
            state = campaign_state(page)
            scene = state.get("active_scene") or {}
            scene_id = str(scene.get("id") or "")
            if scene_id not in visited_scenes:
                visited_scenes.add(scene_id)
                announce(f"Chapter {len(visited_scenes)}/14: {scene.get('title')} [{scene.get('kind')}]")
            travel_to_scene(page)
            state = campaign_state(page)
            scene = state.get("active_scene") or {}

            if scene.get("id") == "scene-embermarket" and not world_exercised:
                exercise_world_controls(page, report)
                world_exercised = True

            if scene.get("kind") == "combat" and not (scene.get("metadata") or {}).get("battle_completed"):
                speak_to_visible_npc(page, spoken, report)
                if first_battle:
                    for selector, key in (('[data-environment="fog"]', "fog"), ('[data-environment="lighting"]', "lighting")):
                        if page.locator(selector).count():
                            click_campaign_and_wait(page, page.locator(selector), label=f"toggle {key}")
                            report["world_controls"][key] = True
                play_battle(page, scene, report, first=first_battle)
                first_battle = False
                continue

            speak_to_visible_npc(page, spoken, report)
            if scene_id != "scene-starter-day" and scene.get("kind") != "combat":
                choice = page.locator("#scene-choices .scene-choice:not([disabled])").first
                if choice.count():
                    before = int(state.get("revision") or 0)
                    choice.click()
                    wait_until(lambda: int(campaign_state(page).get("revision") or 0) > before, label=f"scene choice in {scene_id}")

            scenes = state.get("scenes") or []
            index = next(index for index, entry in enumerate(scenes) if entry.get("id") == scene_id)
            if index == len(scenes) - 1:
                break
            click_campaign_and_wait(page, page.locator("#campaign-continue:not([disabled])"), label=f"continue from {scene_id}")

        final = campaign_state(page)
        report["final_revision"] = final.get("revision")
        report["visited_scenes"] = sorted(visited_scenes)
        report["final_progression"] = final.get("progression")
        report["final_time_label"] = final.get("time_label")
        report["final_quest_statuses"] = {entry["name"]: entry["status"] for entry in final.get("quests") or []}
        assert len(visited_scenes) == 14
        assert len(report["battles"]) == 7
        assert len((final.get("progression") or {}).get("gym_badges") or []) == 3
        assert str((final.get("progression") or {}).get("league_rank") or "").lower() == "champion"
        assert set(report["final_quest_statuses"].values()) == {"complete"}
        assert {"shopping", "crafting", "downtime_recover", "downtime_train"}.issubset(report["world_controls"])
        assert all(battle.get("agent_sources") for battle in report["battles"])
        assert report["http_errors"] == []
        assert report["console_errors"] == []
        assert report["page_errors"] == []
        page.screenshot(path=str(OUTPUT_DIR / f"campaign-complete-{RUN_ID}.png"), full_page=True)

        mobile = context.new_page()
        mobile.set_viewport_size({"width": 390, "height": 844})
        mobile.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded", timeout=120_000)
        mobile.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=60_000)
        overflow = mobile.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        report["mobile_horizontal_overflow_px"] = overflow
        assert overflow <= 2
        mobile.screenshot(path=str(OUTPUT_DIR / f"campaign-mobile-{RUN_ID}.png"), full_page=True)
        mobile.close()

        report["status"] = "passed"
        report["duration_seconds"] = round(time.monotonic() - started, 2)
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        context.close()
    return report


if __name__ == "__main__":
    result: dict[str, Any]
    try:
        result = run()
    except Exception as exc:
        result = dict(ACTIVE_REPORT or {})
        result.update({
            "run_id": RUN_ID,
            "base_url": BASE_URL,
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        REPORT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        announce(f"FAILED: {result['error']}")
        announce(f"Report: {REPORT_PATH}")
        raise
    REPORT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    announce(f"PASSED in {result['duration_seconds']} seconds")
    announce(f"Report: {REPORT_PATH}")
    sys.exit(0)
