from __future__ import annotations

import importlib
import sys
from pathlib import Path


def test_career_vercel_entrypoint_exposes_playable_routes_without_full_server(monkeypatch):
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


def test_missing_browser_bundle_fails_over_without_redirect_loop(monkeypatch, tmp_path):
    sys.modules.pop("career_app", None)
    module = importlib.import_module("career_app")
    monkeypatch.setattr(module, "CAREER_STATIC_DIR", tmp_path / "missing-career-build")
    monkeypatch.setenv("CAREER_FALLBACK_URL", "https://fallback.example/career-game")

    response = module.career_game("run/abc 123")

    assert response.status_code == 307
    assert response.headers["location"] == "https://fallback.example/career-game/run/abc%20123"
    assert response.headers["cache-control"] == "no-store"
    assert "/career-game/index.html?resume=" not in response.headers["location"]


def test_vercel_artifact_workflows_keep_thin_career_entrypoint() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative_path in (
        ".github/workflows/build-vercel-bundle.yml",
        ".github/workflows/validate.yml",
    ):
        workflow = (root / relative_path).read_text(encoding="utf-8")
        assert 'root / "career_app.py"' in workflow
        assert "from career_app import app" in workflow
        assert "from auto_ptu.api.server import app" not in workflow


def test_vercel_bundle_rebuilds_when_thin_entrypoint_changes() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/build-vercel-bundle.yml").read_text(encoding="utf-8")

    # career_app.py is the production Career function source. If it changes without
    # rebuilding the slim artifact, Vercel can keep serving a stale entrypoint even
    # while main contains the fix.
    assert workflow.count("- career_app.py") == 2
