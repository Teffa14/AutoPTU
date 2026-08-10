"""Browser-play path movement, authored interactions, GM locks, and responsive UI."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://127.0.0.1:8766"
REPORT_DIR = Path("reports/qa_path_interactions")


def attach_diagnostics(page: Page, errors: dict[str, list[str]]) -> None:
    page.on("console", lambda message: errors["console"].append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors["page"].append(str(error)))
    page.on(
        "response",
        lambda response: errors["http"].append(f"{response.status} {response.url}")
        if response.status >= 400 and response.url.startswith(BASE_URL)
        else None,
    )


def token_cell(page: Page, actor_id: str) -> str:
    return str(
        page.locator(f'#exploration-board [data-exploration-select="{actor_id}"]')
        .first.locator("xpath=parent::*")
        .get_attribute("data-cell-key")
    )


def focus_floor(page: Page) -> dict[str, object]:
    return page.evaluate(
        """() => {
          window.scrollTo({ left: 0, top: 0, behavior: 'instant' });
          const hud = document.querySelector('.adventure-hud');
          const card = document.querySelector('#exploration-card');
          hud.scrollTop += card.getBoundingClientRect().top - hud.getBoundingClientRect().top - 4;
          const panelBefore = document.querySelector('#exploration-interaction-panel').getBoundingClientRect();
          const hudBefore = hud.getBoundingClientRect();
          if (panelBefore.bottom > hudBefore.bottom) hud.scrollTop += panelBefore.bottom - hudBefore.bottom + 4;
          const workspace = document.querySelector('#campaign-workspace').getBoundingClientRect();
          const topbar = document.querySelector('.campaign-topbar').getBoundingClientRect();
          const gameHeader = document.querySelector('.game-header').getBoundingClientRect();
          const board = document.querySelector('#exploration-board').getBoundingClientRect();
          const panel = document.querySelector('#exploration-interaction-panel').getBoundingClientRect();
          const hudRect = hud.getBoundingClientRect();
          return {
            overflowX: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
            outerScrollX: window.scrollX,
            outerScrollY: window.scrollY,
            workspaceInsideViewport: workspace.top >= 0 && workspace.bottom <= innerHeight,
            topbarInsideViewport: topbar.top >= 0 && topbar.bottom <= innerHeight,
            gameHeaderInsideViewport: gameHeader.top >= topbar.bottom && gameHeader.bottom <= innerHeight,
            boardInsideHud: board.top >= hudRect.top && board.bottom <= hudRect.bottom,
            panelInsideHud: panel.top >= hudRect.top && panel.bottom <= hudRect.bottom,
          };
        }"""
    )


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    errors = {"console": [], "page": [], "http": []}
    checks: dict[str, object] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        gm_context = browser.new_context(viewport={"width": 1440, "height": 900})
        player_context = browser.new_context(viewport={"width": 1440, "height": 900})
        gm = gm_context.new_page()
        player = player_context.new_page()
        attach_diagnostics(gm, errors)
        attach_diagnostics(player, errors)

        gm.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded")
        gm.locator('#campaign-starter-form input[name="player_name"]').fill("Pathfinder GM")
        gm.locator('#campaign-starter-form select[name="play_mode"]').select_option("director")
        gm.locator("#campaign-starter").click()
        gm.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=30_000)
        invite = gm.locator("#campaign-invite").inner_text().replace("Invite", "").strip()
        session = json.loads(gm.evaluate("localStorage.getItem('autoptu_campaign_session')"))
        campaign_id = session["campaignId"]

        player.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded")
        player.locator(".gate-existing").click()
        player.locator(f'#join-campaign-id option[value="{campaign_id}"]').wait_for(state="attached", timeout=20_000)
        player.locator("#join-campaign-id").select_option(campaign_id)
        player.locator('#campaign-join-form input[name="invite_code"]').fill(invite)
        player.locator('#campaign-join-form input[name="name"]').fill("Ari Pathfinder")
        player.locator('#campaign-join-form select[name="role"]').select_option("player")
        player.locator('#campaign-join-form button[type="submit"]').click()
        player.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=30_000)
        player.locator('#starter-choice-list [data-starter="Squirtle"]').click()
        player.locator("#starter-choice-panel.starter-confirmed").wait_for(timeout=20_000)

        player.locator("#exploration-card").scroll_into_view_if_needed()
        player.locator("#exploration-board .exploration-cell").first.wait_for()
        picker_ids = player.locator("#exploration-token-picker [data-exploration-select]").evaluate_all(
            "elements => elements.map(element => element.dataset.explorationSelect)"
        )
        trainer_id = next(actor_id for actor_id in picker_ids if actor_id != "starter-squirtle")
        player.locator(f'#exploration-token-picker [data-exploration-select="{trainer_id}"]').click()

        checks["speed_is_visible"] = "Speed 4" in player.locator("#exploration-help").inner_text()
        checks["multi_step_destination_count"] = player.locator('#exploration-board .legal-move[data-move-steps="4"]').count()
        checks["secret_absent_initially"] = player.locator('[data-exploration-point-select="lab-sealed-drawer"]').count() == 0

        player.locator('[data-exploration-point-select="lab-starter-pods"]').click()
        checks["starter_point_description"] = "Five habitat pods" in player.locator("#exploration-interaction-panel").inner_text()
        player.locator('[data-exploration-point-interact="lab-starter-pods"]').click()
        player.locator("#story-feed .discovery-story").wait_for(timeout=20_000)
        checks["starter_interaction_in_story"] = "starter candidates answer" in player.locator("#story-feed").inner_text()

        before = token_cell(player, trainer_id)
        target = player.locator('#exploration-board [data-cell-key="7,1"][data-move-steps="4"]')
        target.click()
        player.wait_for_function(
            "actorId => document.querySelector(`#exploration-board [data-exploration-select=\"${actorId}\"]`)?.parentElement?.dataset.cellKey === '7,1'",
            arg=trainer_id,
            timeout=20_000,
        )
        checks["multi_step_move"] = {"from": before, "to": token_cell(player, trainer_id), "steps": 4}

        focus_floor(gm)
        gm.locator('[data-exploration-visibility="reveal_all"]').click()
        player.wait_for_function("() => document.querySelectorAll('#exploration-board .state-hidden').length === 0", timeout=20_000)
        gm.locator('[data-exploration-point-select="lab-sealed-drawer"]').click()
        gm.locator('[data-exploration-point-visibility="lab-sealed-drawer"]').click()
        player.locator('[data-exploration-point-select="lab-sealed-drawer"]').wait_for(timeout=20_000)
        player.locator('[data-exploration-point-select="lab-sealed-drawer"]').click()
        player_panel = player.locator("#exploration-interaction-panel")
        checks["locked_marker_visible"] = "Locked by GM" in player_panel.inner_text()
        checks["locked_button_disabled"] = player_panel.locator('[data-exploration-point-interact="lab-sealed-drawer"]').is_disabled()
        checks["outcome_hidden_before_interaction"] = "copied covenant clause" not in player_panel.inner_text()

        gm.locator('[data-exploration-point-available="lab-sealed-drawer"]').click()
        player.wait_for_function(
            "() => document.querySelector('#exploration-interaction-panel [data-exploration-point-interact=\"lab-sealed-drawer\"]')?.disabled === false",
            timeout=20_000,
        )
        checks["gm_unlock_realtime"] = "In range" in player_panel.inner_text()
        player_panel.locator('[data-exploration-point-interact="lab-sealed-drawer"]').click()
        player.wait_for_function(
            "() => [...document.querySelectorAll('#story-feed .discovery-story')].some(node => node.textContent.includes('Open the archive'))",
            timeout=20_000,
        )
        checks["checked_interaction_story"] = "Technology Education" in player.locator("#story-feed").inner_text()
        checks["point_completed_or_retryable"] = any(
            text in player_panel.inner_text() for text in ("Completed", "In range")
        )
        checks["desktop_player_fit"] = focus_floor(player)
        player.wait_for_timeout(300)
        player.screenshot(path=str(REPORT_DIR / "01_player_path_and_discovery.png"))

        checks["desktop_gm_fit"] = focus_floor(gm)
        gm.wait_for_timeout(300)
        gm.screenshot(path=str(REPORT_DIR / "02_gm_reveal_and_lock_controls.png"))

        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            storage_state=player_context.storage_state(),
        )
        mobile = mobile_context.new_page()
        attach_diagnostics(mobile, errors)
        mobile.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded")
        mobile.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=20_000)
        mobile.locator("#exploration-card").scroll_into_view_if_needed()
        mobile.locator('[data-exploration-point-select="lab-sealed-drawer"]').click()
        mobile.screenshot(path=str(REPORT_DIR / "03_mobile_interaction_panel.png"))
        mobile_fit = mobile.evaluate(
            """() => {
              const card = document.querySelector('#exploration-card').getBoundingClientRect();
              const panel = document.querySelector('#exploration-interaction-panel').getBoundingClientRect();
              return {
                overflowX: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
                cardInsideViewport: card.left >= 0 && card.right <= innerWidth,
                panelInsideViewport: panel.left >= 0 && panel.right <= innerWidth,
                panelHeight: Math.round(panel.height),
              };
            }"""
        )
        checks["mobile_fit"] = mobile_fit

        required = [
            checks["speed_is_visible"],
            checks["multi_step_destination_count"] > 0,
            checks["secret_absent_initially"],
            checks["starter_point_description"],
            checks["starter_interaction_in_story"],
            checks["multi_step_move"]["to"] == "7,1",
            checks["locked_marker_visible"],
            checks["locked_button_disabled"],
            checks["outcome_hidden_before_interaction"],
            checks["gm_unlock_realtime"],
            checks["checked_interaction_story"],
            checks["point_completed_or_retryable"],
            checks["desktop_player_fit"]["overflowX"] == 0,
            checks["desktop_player_fit"]["workspaceInsideViewport"],
            checks["desktop_player_fit"]["topbarInsideViewport"],
            checks["desktop_player_fit"]["gameHeaderInsideViewport"],
            checks["desktop_player_fit"]["boardInsideHud"],
            checks["desktop_player_fit"]["panelInsideHud"],
            checks["desktop_gm_fit"]["overflowX"] == 0,
            checks["desktop_gm_fit"]["workspaceInsideViewport"],
            checks["desktop_gm_fit"]["topbarInsideViewport"],
            checks["desktop_gm_fit"]["gameHeaderInsideViewport"],
            checks["desktop_gm_fit"]["boardInsideHud"],
            checks["desktop_gm_fit"]["panelInsideHud"],
            mobile_fit["overflowX"] == 0,
            mobile_fit["cardInsideViewport"],
            mobile_fit["panelInsideViewport"],
        ]
        result = {
            "status": "passed" if not any(errors.values()) and all(required) else "failed",
            "campaign_id": campaign_id,
            "checks": checks,
            "errors": errors,
        }
        (REPORT_DIR / "report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        mobile_context.close()
        player_context.close()
        gm_context.close()
        browser.close()

    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
