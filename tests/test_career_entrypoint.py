from fastapi.testclient import TestClient

from auto_ptu.api.server import app


def test_root_redirects_to_playable_career_client() -> None:
    response = TestClient(app).get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/career-game/"
