import pytest

from app import create_app
from routes import quest as quest_route


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def client(app):
    with app.test_client() as client:
        yield client


def test_get_state_requires_json(client):
    response = client.post("/api/v1/quest/state")

    assert response.status_code == 400
    assert response.is_json


def test_get_state_rejects_invalid_json(client):
    response = client.post(
        "/api/v1/quest/state",
        data="not-json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.is_json


def test_get_state_requires_session_id(client):
    response = client.post(
        "/api/v1/quest/state",
        json={},
    )

    assert response.status_code == 400
    assert response.is_json


def test_complete_level_requires_json(client):
    response = client.post("/api/v1/quest/levels/complete")

    assert response.status_code == 400
    assert response.is_json


def test_collect_item_requires_json(client):
    response = client.post("/api/v1/quest/items/collect")

    assert response.status_code == 400
    assert response.is_json


def test_discover_word_requires_json(client):
    response = client.post("/api/v1/quest/words/discover")

    assert response.status_code == 400
    assert response.is_json


def test_unlock_final_reveal_requires_json(client):
    response = client.post("/api/v1/quest/final-reveal/unlock")

    assert response.status_code == 400
    assert response.is_json


def test_complete_level_rejects_missing_session_id(client):
    response = client.post(
        "/api/v1/quest/levels/complete",
        json={"level": 1},
    )

    assert response.status_code == 400
    assert response.is_json


def test_collect_item_rejects_missing_session_id(client):
    response = client.post(
        "/api/v1/quest/items/collect",
        json={"item": "owl"},
    )

    assert response.status_code == 400
    assert response.is_json


def test_discover_word_rejects_missing_session_id(client):
    response = client.post(
        "/api/v1/quest/words/discover",
        json={"word": "magic"},
    )

    assert response.status_code == 400
    assert response.is_json


def test_unlock_final_reveal_rejects_missing_session_id(client):
    response = client.post(
        "/api/v1/quest/final-reveal/unlock",
        json={},
    )

    assert response.status_code == 400
    assert response.is_json


def test_complete_level_handles_missing_session(client, monkeypatch):
    def fake_get_session(session_id):
        raise LookupError("session not found")

    monkeypatch.setattr(
        quest_route.session_service,
        "get_session",
        fake_get_session,
    )

    response = client.post(
        "/api/v1/quest/levels/complete",
        json={
            "session_id": "test-session",
            "level": 1,
        },
    )

    assert response.status_code == 404
    assert response.is_json


def test_collect_item_handles_missing_session(client, monkeypatch):
    def fake_get_session(session_id):
        raise LookupError("session not found")

    monkeypatch.setattr(
        quest_route.session_service,
        "get_session",
        fake_get_session,
    )

    response = client.post(
        "/api/v1/quest/items/collect",
        json={
            "session_id": "test-session",
            "item": "owl",
        },
    )

    assert response.status_code == 404
    assert response.is_json
