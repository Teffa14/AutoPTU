from __future__ import annotations

import importlib
import sys
from pathlib import Path


def test_career_api_entrypoint_exposes_playable_routes_without_full_server(monkeypatch):
    monkeypatch.setenv("AUTOPTU_SOURCE_COMMIT", "test-sha")
    sys.modules.pop("career_app", None)
    sys.modules.pop("auto_ptu.api.server", None)

    module = importlib.import_module("career_app")
    app_paths = {route.path for route in module.app.routes if hasattr(route, "path")}
    api_paths = {route.path for route in module.career_router.routes if hasattr(route, "path")}

    assert "/api/v1/catalog" in api_paths
    assert "/api/v1/build" in app_paths
    assert "/career-game/" in app_paths
    assert "/career-game/{path:path}" in app_paths
    assert "/" in app_paths
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


def test_github_pages_workflow_deploys_browser_build_with_spa_fallback() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/deploy-github-pages.yml").read_text(encoding="utf-8")

    assert "actions/configure-pages@v5" in workflow
    assert "enablement: true" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "actions/upload-pages-artifact@v3" in workflow
    assert "VITE_API_URL: https://obfecwinjdczsfsperks.supabase.co/functions/v1/career-api" in workflow
    assert "autoptu-career-api.onrender.com" not in workflow
    assert "cp public/career-game/index.html public/404.html" in workflow
    assert "vercel" not in workflow.lower()


def test_vite_build_uses_github_project_site_path() -> None:
    root = Path(__file__).resolve().parents[1]
    config = (root / "career_web" / "vite.config.ts").read_text(encoding="utf-8")

    assert 'command === "serve" ? "/career-game/" : "/AutoPTU/career-game/"' in config
    assert 'outDir: "../public/career-game"' in config


def test_render_container_starts_the_cors_enabled_career_api() -> None:
    root = Path(__file__).resolve().parents[1]
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY career_app.py ./career_app.py" in dockerfile
    assert "uvicorn career_app:app" in dockerfile
    assert "uvicorn auto_ptu.api.server:app" not in dockerfile
