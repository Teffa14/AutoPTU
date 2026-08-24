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
