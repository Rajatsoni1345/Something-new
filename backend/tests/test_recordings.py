import io


def _create_session(client):
    response = client.post("/api/v1/sessions", json={})
    return response.get_json()["data"]["session"]["session_id"]


def test_start_recording_requires_json(client):
    response = client.post("/api/v1/recordings/start")
    assert response.status_code == 400


def test_start_recording_unknown_session(client):
    response = client.post(
        "/api/v1/recordings/start",
        json={
            "session_id": "00000000-0000-4000-8000-000000000000",
            "recording_type": "video_1",
        },
    )
    assert response.status_code == 400


def test_start_recording_invalid_type(client):
    session_id = _create_session(client)

    response = client.post(
        "/api/v1/recordings/start",
        json={
            "session_id": session_id,
            "recording_type": "invalid",
        },
    )
    assert response.status_code == 400


def test_stop_recording_requires_json(client):
    response = client.post("/api/v1/recordings/stop")
    assert response.status_code == 400


def test_upload_requires_multipart(client):
    response = client.post(
        "/api/v1/recordings/upload",
        json={
            "session_id": "s",
            "recording_id": "r",
        },
    )
    assert response.status_code == 400


def test_upload_requires_file(client):
    response = client.post(
        "/api/v1/recordings/upload",
        data={"session_id": "s", "recording_id": "r"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_upload_requires_session_id(client):
    response = client.post(
        "/api/v1/recordings/upload",
        data={
            "recording_id": "r",
            "file": (io.BytesIO(b"x"), "v.webm"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_verify_requires_json(client):
    response = client.post("/api/v1/recordings/verify")
    assert response.status_code == 400


def test_fail_requires_json(client):
    response = client.post("/api/v1/recordings/fail")
    assert response.status_code == 400


def test_get_recording_requires_session_id(client):
    response = client.get("/api/v1/recordings/abc")
    assert response.status_code == 400
