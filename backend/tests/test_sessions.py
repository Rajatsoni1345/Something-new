import pytest

from app import create_app
from routes import sessions as sessions_route


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def client(app):
    with app.test_client() as client:
        yield client


def test_create_session_requires_json(client):
    response = client.post("/api/v1/sessions")

    assert response.status_code == 400
    assert response.is_json


def test_create_session_rejects_invalid_json(client):
    response = client.post(
        "/api/v1/sessions",
        data="not-json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.is_json


def test_create_session_success(client, monkeypatch):
    expected = {
        "session_id": "test-session-123",
        "status": "active",
    }

    def fake_create_session():
        return expected

    monkeypatch.setattr(
        sessions_route.session_service,
        "create_session",
        fake_create_session,
    )

    response = client.post(
        "/api/v1/sessions",
        json={},
    )

    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()

    assert data["success"] is True
    assert data["data"] == expected


def test_create_session_handles_service_conflict(client, monkeypatch):
    def fake_create_session():
        raise RuntimeError("session conflict")

    monkeypatch.setattr(
        sessions_route.session_service,
        "create_session",
        fake_create_session,
    )

    response = client.post(
        "/api/v1/sessions",
        json={},
    )

    assert response.status_code == 409
    assert response.is_json


def test_recover_session_requires_json(client):
    response = client.post("/api/v1/sessions/recover")

    assert response.status_code == 400
    assert response.is_json


def test_recover_session_rejects_invalid_json(client):
    response = client.post(
        "/api/v1/sessions/recover",
        data="invalid",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.is_json


def test_get_session_requires_valid_session_id(client):
    response = client.get("/api/v1/sessions/")

    assert response.status_code in (404, 405)
