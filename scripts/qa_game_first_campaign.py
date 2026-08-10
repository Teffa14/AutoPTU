"""End-to-end browser playthrough for the game-first campaign shell.

This is intentionally a visible-control test: campaign actions, local Ollama
turns, chapter transitions, and battle controls are driven through the UI.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://127.0.0.1:8765"
REPORT_DIR = Path("reports/qa_game_first")


def revision(page: Page) -> int:
    text = page.locator("#connection-state").inner_text()
    return int(text.rsplit(" ", 1)[-1])


def wait_revision(page: Page, previous: int, timeout: int = 20_000) -> int:
    page.wait_for_function(
        "([selector, old]) => Number(document.querySelector(selector)?.textContent?.match(/\\d+/)?.[0] || 0) > old",
        arg=["#connection-state", previous],
        timeout=timeout,
    )
    return revision(page)


def click_campaign_action(page: Page, selector: str) -> int:
    previous = revision(page)
    page.locator(selector).click()
    return wait_revision(page, previous)


def wait_agent(page: Page, previous_revision: int, timeout: int = 150_000) -> None:
    wait_revision(page, previous_revision, timeout=timeout)
    page.wait_for_function(
        "() => document.querySelector('#agent-thinking')?.classList.contains('hidden')",
        timeout=timeout,
    )


def campaign_agent_click(page: Page, selector: str, timeout: int = 150_000) -> None:
    previous = revision(page)
    page.locator(selector).click()
    wait_agent(page, previous, timeout=timeout)


def choose(page: Page, index: int) -> None:
    click_campaign_action(page, f'#scene-choices [data-choice="{index}"]')


def complete_objective(page: Page, quest_id: str, objective_number: int) -> None:
    objective_id = f"{quest_id}-objective-{objective_number}"
    checkbox = page.locator(f'#quest-list input[data-quest="{quest_id}"][data-objective="{objective_id}"]')
    if checkbox.is_checked():
        return
    previous = revision(page)
    checkbox.check()
    wait_revision(page, previous)


def party_round(page: Page) -> str:
    before = page.locator("#agent-turn-log").inner_text()
    campaign_agent_click(page, "#agent-round", timeout=240_000)
    after = page.locator("#agent-turn-log").inner_text()
    assert after and after != before
    return after


def snapshot(page: Page) -> dict:
    response = page.request.get(f"{BASE_URL}/api/state")
    assert response.ok
    return response.json()


def click_battle_agent(page: Page, timeout: int = 150_000) -> dict:
    button = page.locator("#turn-agent")
    if not button.is_visible() and page.locator("#turn-controller").get_attribute("class").find("turn-controller-collapsed") >= 0:
        page.locator("#turn-controller-collapse").click()
    button.wait_for(state="visible")
    button.click()
    page.wait_for_function(
        "() => !document.querySelector('#turn-agent')?.classList.contains('is-thinking')",
        timeout=timeout,
    )
    return snapshot(page)


def play_battle(page: Page, label: str, events: list[dict]) -> None:
    page.locator("#start-battle").click()
    page.wait_for_selector("#turn-controller:not(.hidden)", timeout=30_000)
    state = snapshot(page)
    events.append({"phase": label, "action": "battle_started", "round": state.get("round")})

    # Trainer declarations and Pokemon turns both go through the campaign agent.
    if state.get("current_actor_is_player"):
        state = click_battle_agent(page)
        events.append({"phase": label, "action": "agent_act", "actor": state.get("current_actor_id")})

    # Use an ordinary move through the visible quick-move and board target controls.
    if state.get("current_actor_is_player") and not state.get("trainer_turn"):
        quick = page.locator("#turn-quick-moves button:not([disabled])").first
        if quick.count():
            quick.click()
            target = page.locator("#grid .cell.in-range.occupied").first
            if target.count():
                target.click()
                page.wait_for_timeout(700)
                state = snapshot(page)
                events.append({"phase": label, "action": "manual_move", "actor": state.get("current_actor_id")})

    # If a player turn remains, stage an end-turn declaration, open and close a
    # reaction window, then resolve the declaration from the stack.
    state = snapshot(page)
    if state.get("current_actor_is_player"):
        page.locator("#turn-plan").click()
        page.locator("#turn-end").click()
        page.wait_for_function("() => !document.querySelector('#command-resolve-next')?.disabled", timeout=10_000)
        page.locator("#battle-role").select_option("gm")
        page.locator("#interrupt-trigger").fill("A rival reacts to the declared action")
        page.locator("#interrupt-open").click()
        page.wait_for_selector("#interrupt-window:not(.hidden)", timeout=10_000)
        page.locator("#interrupt-close").click()
        page.wait_for_selector("#interrupt-window.hidden", state="attached", timeout=10_000)
        page.locator("#command-resolve-next").click()
        page.wait_for_timeout(700)
        events.append({"phase": label, "action": "queue_and_interrupt"})

    if not page.locator("#turn-undo").is_disabled():
        page.locator("#turn-undo").click()
        page.wait_for_timeout(600)
        events.append({"phase": label, "action": "undo"})

    page.screenshot(path=str(REPORT_DIR / f"{label}.png"), full_page=True)
    # Stop the current encounter through the same control so the next combat
    # chapter starts with a clean engine state.
    page.locator("#start-battle").click()
    page.wait_for_selector("#turn-controller.hidden", state="attached", timeout=20_000)
    page.goto(f"{BASE_URL}/campaign")
    page.wait_for_selector("#campaign-workspace:not(.hidden)", timeout=20_000)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    events: list[dict] = []
    console_errors: list[str] = []
    started = time.time()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: console_errors.append(str(error)))
        page.goto(f"{BASE_URL}/campaign")
        page.locator('#campaign-starter-form input[name="player_name"]').fill("Browser Pathfinder")
        page.locator('#campaign-starter-form select[name="play_mode"]').select_option("director")
        page.locator("#campaign-starter").click()
        page.wait_for_selector("#campaign-workspace:not(.hidden)", timeout=20_000)
        page.wait_for_function("() => document.querySelector('#agent-ollama-state')?.textContent?.includes('models ready')", timeout=20_000)
        page.locator("#agent-gm-model").select_option("qwen2.5:3b")
        page.locator("#agent-player-model").select_option("qwen2.5:3b")
        events.append({"phase": "chapter_1", "action": "campaign_started", "revision": revision(page)})

        choose(page, 0)
        choose(page, 1)
        campaign_agent_click(page, "#agent-step-gm")
        campaign_agent_click(page, '[data-agent-step="agent-nova"]')
        events.append({"phase": "chapter_1", "action": "party_round", "summary": party_round(page)})

        # Exercise persistent campaign systems from the on-screen HUD.
        click_campaign_action(page, '#clock-list [data-clock="clock-rivals"][data-delta="1"]')
        complete_objective(page, "quest-missing-rangers", 1)
        page.locator(".journal-drawer").evaluate("element => element.open = true")
        page.locator('#journal-form input[name="title"]').fill("Lantern Compass")
        page.locator('#journal-form textarea[name="text"]').fill("The missing Ranger compass points toward Glasswood after the Pichu calms down.")
        previous = revision(page)
        page.locator('#journal-form button[type="submit"]').click()
        wait_revision(page, previous)
        click_campaign_action(page, "#safety-pause")
        click_campaign_action(page, "#safety-resume")
        page.locator("#director-tools").evaluate("element => element.open = true")
        page.locator('#time-form input[name="label"]').fill("Day 1, Lanternfall")
        previous = revision(page)
        page.locator('#time-form button[type="submit"]').click()
        wait_revision(page, previous)
        events.append({"phase": "chapter_1", "action": "campaign_systems_exercised"})

        click_campaign_action(page, "#campaign-continue")
        choose(page, 2)
        complete_objective(page, "quest-missing-rangers", 2)
        complete_objective(page, "quest-prism-cup", 1)
        events.append({"phase": "chapter_2", "action": "party_round", "summary": party_round(page)})
        click_campaign_action(page, "#campaign-continue")
        assert "Stormglass Ambush" in page.locator("#scene-title").inner_text()
        page.locator("#open-battle-link").click()
        page.wait_for_url(f"{BASE_URL}/", timeout=20_000)
        play_battle(page, "battle_stormglass", events)

        complete_objective(page, "quest-missing-rangers", 3)
        click_campaign_action(page, "#campaign-continue")
        choose(page, 0)
        complete_objective(page, "quest-prism-cup", 2)
        events.append({"phase": "chapter_4", "action": "party_round", "summary": party_round(page)})
        click_campaign_action(page, "#campaign-continue")
        assert "Prism Cup Qualifier" in page.locator("#scene-title").inner_text()
        page.locator("#open-battle-link").click()
        page.wait_for_url(f"{BASE_URL}/", timeout=20_000)
        play_battle(page, "battle_prism_cup", events)

        complete_objective(page, "quest-prism-cup", 3)
        click_campaign_action(page, "#campaign-continue")
        assert "Lanterns After the Storm" in page.locator("#scene-title").inner_text()
        choose(page, 0)
        events.append({"phase": "chapter_6", "action": "party_round", "summary": party_round(page)})
        page.screenshot(path=str(REPORT_DIR / "campaign_complete.png"), full_page=True)
        events.append(
            {
                "phase": "complete",
                "action": "adventure_complete",
                "chapter": page.locator("#chapter-label").inner_text(),
                "revision": revision(page),
                "journal_entries": page.locator("#journal-list .journal-card").count(),
                "objectives_remaining": page.locator('#quest-list input[type="checkbox"]:not(:checked)').count(),
            }
        )
        browser.close()

    report = {
        "base_url": BASE_URL,
        "elapsed_seconds": round(time.time() - started, 1),
        "console_errors": console_errors,
        "events": events,
    }
    (REPORT_DIR / "full_campaign_browser_transcript.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if console_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
