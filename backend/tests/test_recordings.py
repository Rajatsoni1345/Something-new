import io

import pytest

from app import create_app
from routes import recordings as recordings_route


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def client(app):
    with app.test_client() as client:
        yield client


def test_start_recording_requires_json(client):
    response = client.post("/api/v1/recordings/start")

    assert response.status_code == 400
    assert response.is_json


def test_start_recording_rejects_invalid_json(client):
    response = client.post(
        "/api/v1/recordings/start",
        data="invalid",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.is_json


def test_start_recording_requires_session_id(client):
    response = client.post(
        "/api/v1/recordings/start",
        json={"recording_type": "video_1"},
    )

    assert response.status_code == 400
    assert response.is_json


def test_start_recording_requires_recording_type(client):
    response = client.post(
        "/api/v1/recordings/start",
        json={"session_id": "test-session"},
    )

    assert response.status_code == 400
    assert response.is_json


def test_start_recording_success(client, monkeypatch):
    expected = {
        "recording_id": "recording-123",
        "recording_type": "video_1",
        "status": "recording",
    }

    def fake_start_recording(session_id, recording_type):
        return expected

    monkeypatch.setattr(
        recordings_route.recording_service,
        "start_recording",
        fake_start_recording,
    )

    response = client.post(
        "/api/v1/recordings/start",
        json={
            "session_id": "test-session",
            "recording_type": "video_1",
        },
    )

    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()

    assert data["success"] is True
    assert data["data"] == expected


def test_stop_recording_requires_json(client):
    response = client.post("/api/v1/recordings/stop")

    assert response.status_code == 400
    assert response.is_json


def test_stop_recording_requires_recording_id(client):
    response = client.post(
        "/api/v1/recordings/stop",
        json={"session_id": "test-session"},
    )

    assert response.status_code == 400
    assert response.is_json


def test_upload_pending_requires_json(client):
    response = client.post("/api/v1/recordings/upload-pending")

    assert response.status_code == 400
    assert response.is_json


def test_upload_pending_requires_recording_id(client):
    response = client.post(
        "/api/v1/recordings/upload-pending",
        json={"session_id": "test-session"},
    )

    assert response.status_code == 400
    assert response.is_json


def test_upload_requires_multipart_data(client):
    response = client.post(
        "/api/v1/recordings/upload",
        json={
            "session_id": "test-session",
            "recording_id": "recording-123",
        },
    )

    assert response.status_code == 400
    assert response.is_json


def test_upload_requires_file(client):
    response = client.post(
        "/api/v1/recordings/upload",
        data={
            "session_id": "test-session",
            "recording_id": "recording-123",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.is_json


def test_upload_requires_session_id(client):
    response = client.post(
        "/api/v1/recordings/upload",
        data={
            "recording_id": "recording-123",
            "file": (
                io.BytesIO(b"fake-video"),
                "video.webm",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.is_json


def test_verify_recording_requires_json(client):
    response = client.post("/api/v1/recordings/verify")

    assert response.status_code == 400
    assert response.is_json


def test_fail_recording_requires_json(client):
    response = client.post("/api/v1/recordings/fail")

    assert response.status_code == 400
    assert response.is_json


def test_get_recording_requires_session_id(client):
    response = client.get("/api/v1/recordings/recording-123")

    assert response.status_code == 400
    assert response.is_json


def test_get_recording_success(client, monkeypatch):
    expected = {
        "recording_id": "recording-123",
        "recording_type": "video_1",
        "status": "verified",
    }

    def fake_get_recording(session_id, recording_id):
        return expected

    monkeypatch.setattr(
        recordings_route.recording_service,
        "get_recording",
        fake_get_recording,
    )

    response = client.get(
        "/api/v1/recordings/recording-123",
        query_string={"session_id": "test-session"},
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert data["success"] is True
    assert data["data"] == expected
