from services.session_service import create_session


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


def test_create_session_success(client):
    response = client.post("/api/v1/sessions", json={})

    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()

    assert data["success"] is True
    assert "session" in data["data"]
    assert data["data"]["session"]["state"] == "NEW"


def test_get_session_success(client):
    created = client.post("/api/v1/sessions", json={})
    session_id = created.get_json()["data"]["session"]["session_id"]

    response = client.get(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    assert response.get_json()["data"]["session"]["session_id"] == session_id


def test_get_session_not_found(client):
    response = client.get(
        "/api/v1/sessions/00000000-0000-4000-8000-000000000000"
    )

    assert response.status_code == 404


def test_recover_session_requires_json(client):
    response = client.post("/api/v1/sessions/recover")

    assert response.status_code == 400


def test_recover_session_success(client):
    created = client.post("/api/v1/sessions", json={})
    session_id = created.get_json()["data"]["session"]["session_id"]

    response = client.post(
        "/api/v1/sessions/recover",
        json={"session_id": session_id},
    )

    assert response.status_code == 200
    assert (
        response.get_json()["data"]["session"]["session_id"]
        == session_id
    )


def test_recover_unknown_session(client):
    response = client.post(
        "/api/v1/sessions/recover",
        json={"session_id": "00000000-0000-4000-8000-000000000000"},
    )

    assert response.status_code == 404
