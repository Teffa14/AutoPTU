from __future__ import annotations

import importlib
import sys
from pathlib import Path


def test_career_api_entrypoint_exposes_playable_routes_without_full_server(monkeypatch):
    monkeypatch.setenv("AUTOPTU_SOURCE_COMMIT", "test-sha")
    sys.modules.pop("career_app", None)
    sys.modules.pop("auto_ptu.api.server", None)

    module = importlib.import_module("career_app")
    paths = {route.path for route in module.app.routes}

    assert "/api/v1/catalog" in paths
    assert "/api/v1/build" in paths
    assert "/career-game/" in paths
    assert "/career-game/{path:path}" in paths
    assert "/" in paths
    assert "auto_ptu.api.server" not in sys.modules
    assert module.deployed_build() == {"source_commit": "test-sha"}
    assert "https://teffa14.github.io" in module._cors_origins()


def test_missing_local_browser_bundle_redirects_to_github_pages(monkeypatch, tmp_path):
    sys.modules.pop("career_app", None)
    module = importlib.import_module("career_app")
    monkeypatch.setattr(module, "CAREER_STATIC_DIR", tmp_path / "missing-career-build")
    monkeypatch.delenv("CAREER_WEB_URL", raising=False)

    response = module.career_game("run/abc 123")

    assert response.status_code == 307
    assert response.headers["location"] == "https://teffa14.github.io/AutoPTU/career-game/run/abc%20123"
    assert response.headers["cache-control"] == "no-store"


def test_github_pages_workflow_builds_expected_project_site_path() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/deploy-github-pages.yml").read_text(encoding="utf-8")

    assert "actions/deploy-pages@v4" in workflow
    assert "actions/upload-pages-artifact@v3" in workflow
    assert "VITE_BASE_PATH: /AutoPTU/career-game/" in workflow
    assert "VITE_API_URL:" in workflow
    assert "vercel" not in workflow.lower()


def test_vite_build_accepts_pages_base_path() -> None:
    root = Path(__file__).resolve().parents[1]
    config = (root / "career_web" / "vite.config.ts").read_text(encoding="utf-8")

    assert 'process.env.VITE_BASE_PATH ?? "/career-game/"' in config
    assert 'outDir: "../public/career-game"' in config
