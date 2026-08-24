from __future__ import annotations

import importlib
import sys


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
