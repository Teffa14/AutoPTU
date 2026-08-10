"""Two-session browser QA for campaign exploration controls and secrecy."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://127.0.0.1:8766"
REPORT_DIR = Path("reports/qa_exploration")


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


def show_desktop_exploration(page: Page) -> dict[str, object]:
    return page.evaluate(
        """() => {
          document.documentElement.style.scrollBehavior = 'auto';
          window.scrollTo({ left: 0, top: 0, behavior: 'instant' });
          const hud = document.querySelector('.adventure-hud');
          const card = document.querySelector('#exploration-card');
          const beforeHud = hud.getBoundingClientRect();
          const beforeCard = card.getBoundingClientRect();
          hud.scrollTop += beforeCard.top - beforeHud.top - 4;
          const workspace = document.querySelector('#campaign-workspace').getBoundingClientRect();
          const board = document.querySelector('#exploration-board').getBoundingClientRect();
          return {
            outerScrollX: window.scrollX,
            outerScrollY: window.scrollY,
            overflowX: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
            overflowY: Math.max(0, document.documentElement.scrollHeight - document.documentElement.clientHeight),
            workspaceInsideViewport: workspace.top >= 0 && workspace.bottom <= innerHeight,
            boardInsideHud: board.top >= hud.getBoundingClientRect().top && board.bottom <= hud.getBoundingClientRect().bottom,
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
        gm.locator('#campaign-starter-form input[name="player_name"]').fill("Exploration GM")
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
        checks["player_initial_hidden_cells"] = player.locator("#exploration-board .state-hidden").count()
        checks["player_owned_picker_tokens"] = player.locator("#exploration-token-picker [data-exploration-select]").count()
        checks["player_cannot_select_agent_tokens"] = player.locator('#exploration-token-picker [data-exploration-select="trainer-nova"]').count() == 0
        checks["secret_absent_initially"] = player.locator('#exploration-board .exploration-point[title="Sealed prism archive"]').count() == 0

        starter_id = "starter-squirtle"
        picker_ids = player.locator("#exploration-token-picker [data-exploration-select]").evaluate_all(
            "elements => elements.map(element => element.dataset.explorationSelect)"
        )
        trainer_id = next(actor_id for actor_id in picker_ids if actor_id != starter_id)
        player.locator(f'#exploration-token-picker [data-exploration-select="{trainer_id}"]').click()
        before_click = token_cell(player, trainer_id)
        click_target = player.locator("#exploration-board .legal-move").first
        click_target.click()
        player.wait_for_function(
            "([actorId, before]) => document.querySelector(`#exploration-board [data-exploration-select=\"${actorId}\"]`)?.parentElement?.dataset.cellKey !== before",
            arg=[trainer_id, before_click],
            timeout=20_000,
        )
        checks["click_move"] = {"from": before_click, "to": token_cell(player, trainer_id)}
        checks["fog_memory_after_move"] = player.locator("#exploration-board .state-explored").count()

        player.locator(f'#exploration-token-picker [data-exploration-select="{starter_id}"]').click()
        before_drag = token_cell(player, starter_id)
        drag_token = player.locator(f'#exploration-board [data-exploration-drag="{starter_id}"]')
        drag_target = player.locator("#exploration-board .legal-move").first
        drag_token.drag_to(drag_target)
        player.wait_for_function(
            "([actorId, before]) => document.querySelector(`#exploration-board [data-exploration-select=\"${actorId}\"]`)?.parentElement?.dataset.cellKey !== before",
            arg=[starter_id, before_drag],
            timeout=20_000,
        )
        checks["drag_move"] = {"from": before_drag, "to": token_cell(player, starter_id)}
        checks["desktop_player_fit"] = show_desktop_exploration(player)
        player.wait_for_timeout(250)
        player.screenshot(path=str(REPORT_DIR / "01_player_owned_movement_and_fog.png"))

        show_desktop_exploration(gm)
        gm.locator('[data-exploration-visibility="reveal_all"]').click()
        player.wait_for_function("() => document.querySelectorAll('#exploration-board .state-hidden').length === 0", timeout=20_000)
        checks["gm_reveal_all_realtime"] = player.locator("#exploration-board .state-hidden").count() == 0

        secret = gm.locator('[data-exploration-point="lab-sealed-drawer"]')
        secret.click()
        player.locator('#exploration-board .exploration-point[title="Sealed prism archive"]').wait_for(timeout=20_000)
        checks["gm_secret_publication_realtime"] = True
        checks["desktop_gm_fit"] = show_desktop_exploration(gm)
        gm.wait_for_timeout(250)
        gm.screenshot(path=str(REPORT_DIR / "02_gm_scene_floor_controls.png"))

        alder_visibility = gm.locator('[data-exploration-token-visibility="npc-alder"]')
        alder_visibility.click()
        player.wait_for_function(
            "() => !document.querySelector('#exploration-board [data-exploration-select=\"npc-alder\"]') && !document.querySelector('#npc-list [data-npc-pick=\"npc-alder\"]')",
            timeout=20_000,
        )
        checks["gm_hidden_npc_removed_from_map_and_dialogue"] = True
        gm.locator('[data-exploration-token-visibility="npc-alder"]').click()
        player.locator('#npc-list [data-npc-pick="npc-alder"]').wait_for(timeout=20_000)

        gm.locator('[data-exploration-visibility="restore_fog"]').click()
        player.wait_for_function("() => document.querySelectorAll('#exploration-board .state-hidden').length > 0", timeout=20_000)
        checks["gm_restore_fog_realtime"] = player.locator("#exploration-board .state-hidden").count() > 0

        player_storage = player_context.storage_state()
        mobile_context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, storage_state=player_storage)
        mobile = mobile_context.new_page()
        attach_diagnostics(mobile, errors)
        mobile.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded")
        mobile.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=20_000)
        mobile.locator("#exploration-card").scroll_into_view_if_needed()
        mobile.screenshot(path=str(REPORT_DIR / "03_mobile_scene_floor.png"))
        fit = mobile.evaluate(
            """() => {
              const board = document.querySelector('#exploration-board').getBoundingClientRect();
              const card = document.querySelector('#exploration-card').getBoundingClientRect();
              return {
                viewportWidth: innerWidth,
                overflowX: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
                boardInsideViewport: board.left >= 0 && board.right <= innerWidth,
                cardInsideViewport: card.left >= 0 && card.right <= innerWidth,
                boardHeight: Math.round(board.height),
              };
            }"""
        )
        checks["mobile_fit"] = fit

        result = {
            "status": "passed" if not any(errors.values()) and all(
                [
                    checks["player_initial_hidden_cells"] > 0,
                    checks["player_owned_picker_tokens"] == 2,
                    checks["player_cannot_select_agent_tokens"],
                    checks["secret_absent_initially"],
                    checks["fog_memory_after_move"] > 0,
                    checks["gm_reveal_all_realtime"],
                    checks["gm_secret_publication_realtime"],
                    checks["gm_hidden_npc_removed_from_map_and_dialogue"],
                    checks["gm_restore_fog_realtime"],
                    checks["desktop_player_fit"]["outerScrollY"] == 0,
                    checks["desktop_player_fit"]["outerScrollX"] == 0,
                    checks["desktop_player_fit"]["overflowX"] == 0,
                    checks["desktop_player_fit"]["workspaceInsideViewport"],
                    checks["desktop_player_fit"]["boardInsideHud"],
                    checks["desktop_gm_fit"]["outerScrollY"] == 0,
                    checks["desktop_gm_fit"]["outerScrollX"] == 0,
                    checks["desktop_gm_fit"]["workspaceInsideViewport"],
                    checks["desktop_gm_fit"]["boardInsideHud"],
                    fit["overflowX"] == 0,
                    fit["boardInsideViewport"],
                    fit["cardInsideViewport"],
                ]
            ) else "failed",
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
