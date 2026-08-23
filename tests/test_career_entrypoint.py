from fastapi.testclient import TestClient

from auto_ptu.api.server import app


def test_root_redirects_to_playable_career_client() -> None:
    response = TestClient(app).get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/career-game/"


def test_career_client_entrypoint_serves_built_browser_app() -> None:
    response = TestClient(app).get("/career-game/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert 'id="root"' in response.text
    assert "/career-game/assets/" in response.text
