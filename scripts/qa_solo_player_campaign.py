"""Browser-play the default human Trainer + AI GM campaign handoff into battle."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://127.0.0.1:8766"
REPORT_DIR = Path("reports/qa_solo_player_campaign")


def attach_diagnostics(page: Page, errors: dict[str, list[str]]) -> None:
    page.on("console", lambda message: errors["console"].append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors["page"].append(str(error)))
    page.on(
        "response",
        lambda response: errors["http"].append(f"{response.status} {response.url}")
        if response.status >= 400 and response.url.startswith(BASE_URL)
        else None,
    )


def session(page: Page) -> dict[str, str]:
    return json.loads(page.evaluate("localStorage.getItem('autoptu_campaign_session')"))


def campaign_state(page: Page) -> dict:
    current = session(page)
    response = page.request.get(
        f"{BASE_URL}/api/campaigns/{current['campaignId']}",
        headers={"Authorization": f"Bearer {current['participantToken']}"},
    )
    assert response.ok, response.text()
    return response.json()["campaign"]


def battle_state(page: Page) -> dict:
    current = session(page)
    response = page.request.get(
        f"{BASE_URL}/api/state",
        headers={"Authorization": f"Bearer {current['participantToken']}"},
    )
    assert response.ok, response.text()
    return response.json()


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    errors = {"console": [], "page": [], "http": []}
    checks: dict[str, object] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        attach_diagnostics(page, errors)

        page.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded")
        checks["solo_is_default"] = page.locator('#campaign-starter-form select[name="play_mode"]').input_value() == "solo"
        page.locator('#campaign-starter-form input[name="player_name"]').fill("Avery Browser")
        page.locator("#campaign-starter").click()
        page.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=60_000)

        initial = campaign_state(page)
        checks["human_is_player"] = initial["viewer"]["id"] == "player" and initial["viewer"]["role"] == "player"
        checks["ai_gm_is_authority"] = any(
            entry["id"] == "agent-gm" and entry["role"] == "gm" and entry["controller"] == "ai"
            for entry in initial["participants"]
        )
        checks["only_current_scene_visible"] = [entry["id"] for entry in initial["scenes"]] == ["scene-starter-day"]
        checks["director_tools_hidden"] = page.locator("#director-tools").evaluate("node => node.classList.contains('hidden')")
        checks["ai_controls_visible"] = page.locator("#agent-party").is_visible()
        checks["starter_goal_visible"] = "Choose a starter partner" in page.locator("#active-objective").inner_text()
        checks["continue_locked_before_starter"] = page.locator("#campaign-continue").is_disabled()

        current = session(page)
        forged = page.request.post(
            f"{BASE_URL}/api/campaigns/{current['campaignId']}/command",
            headers={"Authorization": f"Bearer {current['participantToken']}", "Content-Type": "application/json"},
            data={"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}},
        )
        checks["forged_scene_activation_denied"] = forged.status == 403

        page.locator('#starter-choice-list [data-starter="Bulbasaur"]').click()
        page.locator("#starter-choice-panel.starter-confirmed").wait_for(timeout=30_000)
        page.wait_for_function("() => !document.querySelector('#campaign-continue')?.disabled")
        selected = campaign_state(page)
        owned_starter = next(
            entry for entry in selected["actors"] if entry.get("species") == "Bulbasaur" and entry.get("sheet", {}).get("starter")
        )
        checks["starter_persisted_to_trainer"] = (
            owned_starter["owner_participant_id"] == "player"
            and owned_starter["id"] in next(entry for entry in selected["participants"] if entry["id"] == "player")["character_ids"]
        )
        checks["continue_delegates_to_ai_gm"] = "Ask the GM to continue" in page.locator("#campaign-continue").inner_text()
        page.screenshot(path=str(REPORT_DIR / "01_solo_starter_selected.png"), full_page=True)

        # A missing model makes this browser regression use the runtime's fast,
        # deterministic narration fallback while exercising the same endpoint.
        page.locator("#agent-gm-model").evaluate(
            "node => { node.innerHTML = '<option value=\"qa-missing-model\">qa-missing-model</option>'; node.value = 'qa-missing-model'; }"
        )
        page.locator("#campaign-continue").click()
        page.wait_for_function("() => document.querySelector('#scene-title')?.textContent?.includes(\"Cassian's First Challenge\")", timeout=60_000)
        advanced = campaign_state(page)
        checks["ai_gm_opened_exact_next_scene"] = (
            advanced["active_scene_id"] == "scene-first-rival"
            and [entry["id"] for entry in advanced["scenes"]] == ["scene-starter-day", "scene-first-rival"]
        )
        checks["battle_hidden_until_travel"] = not page.locator("#open-battle-link").is_visible()
        checks["travel_instruction_visible"] = "Travel to Sunpath Route" in page.locator("#campaign-continue").inner_text()

        page.locator('#campaign-world-map [data-travel-map="sunpath-route"]').click()
        page.wait_for_function("() => document.querySelector('#open-battle-link') && !document.querySelector('#open-battle-link').classList.contains('hidden')", timeout=30_000)
        travelled = campaign_state(page)
        checks["travel_unlocks_battle"] = travelled["world"]["current_location_id"] == "sunpath-route"
        page.screenshot(path=str(REPORT_DIR / "02_battle_ready_after_travel.png"), full_page=True)

        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            storage_state=context.storage_state(),
        )
        mobile = mobile_context.new_page()
        attach_diagnostics(mobile, errors)
        mobile.goto(f"{BASE_URL}/campaign", wait_until="domcontentloaded")
        mobile.locator("#campaign-workspace:not(.hidden)").wait_for(timeout=30_000)
        mobile.screenshot(path=str(REPORT_DIR / "03_mobile_solo_campaign.png"), full_page=True)
        checks["mobile_no_horizontal_overflow"] = mobile.evaluate(
            "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )
        mobile_context.close()

        page.locator("#open-battle-link").click()
        page.wait_for_url(f"{BASE_URL}/", timeout=120_000)
        page.locator("#turn-controller:not(.hidden)").wait_for(timeout=120_000)
        battle = battle_state(page)
        identity = battle.get("battle_identity") or {}
        checks["battle_identity_is_player"] = identity.get("bound") is True and identity.get("role") == "player"
        checks["battle_owns_persistent_roster"] = identity.get("owned_trainer_ids") == ["player"] and identity.get("owned_actor_ids") == ["player-1"]
        current_actor = str(battle.get("current_actor_id") or "")
        owns_turn = current_actor in set(identity.get("owned_actor_ids") or []) | set(identity.get("owned_trainer_ids") or [])
        checks["battle_controls_match_owner"] = (
            (owns_turn and not page.locator("#turn-actions").is_disabled() and page.locator("#turn-agent").is_disabled())
            or (not owns_turn and page.locator("#turn-actions").is_disabled() and not page.locator("#turn-agent").is_disabled())
        )
        checks["battle_role_locked"] = page.locator("#battle-role").is_disabled()
        page.screenshot(path=str(REPORT_DIR / "04_authenticated_player_battle.png"), full_page=True)

        required = [bool(value) for value in checks.values()]
        result = {
            "status": "passed" if all(required) and not any(errors.values()) else "failed",
            "campaign_id": current["campaignId"],
            "checks": checks,
            "errors": errors,
        }
        (REPORT_DIR / "report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        context.close()
        browser.close()

    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
