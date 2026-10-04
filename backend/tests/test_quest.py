import pytest


def _create_session(client):
    response = client.post("/api/v1/sessions", json={})
    return response.get_json()["data"]["session"]["session_id"]


def test_get_state_requires_json(client):
    response = client.post("/api/v1/quest/state")

    assert response.status_code == 400
    assert response.is_json


def test_get_state_requires_session_id(client):
    response = client.post("/api/v1/quest/state", json={})

    assert response.status_code == 400


def test_get_state_unknown_session(client):
    response = client.post(
        "/api/v1/quest/state",
        json={"session_id": "00000000-0000-4000-8000-000000000000"},
    )

    assert response.status_code == 404


def test_get_state_creates_quest(client):
    session_id = _create_session(client)

    response = client.post(
        "/api/v1/quest/state",
        json={"session_id": session_id},
    )

    assert response.status_code == 200
    quest = response.get_json()["data"]["quest"]
    assert quest["state"] == "NEW"
    assert quest["session_id"] == session_id


def test_complete_level_requires_json(client):
    response = client.post("/api/v1/quest/levels/complete")
    assert response.status_code == 400


def test_complete_level_unknown_session(client):
    response = client.post(
        "/api/v1/quest/levels/complete",
        json={
            "session_id": "00000000-0000-4000-8000-000000000000",
            "level": 1,
            "answer": "whatever",
        },
    )
    assert response.status_code == 404


def test_collect_item_requires_json(client):
    response = client.post("/api/v1/quest/items/collect")
    assert response.status_code == 400


def test_discover_word_requires_json(client):
    response = client.post("/api/v1/quest/words/discover")
    assert response.status_code == 400


def test_unlock_final_reveal_requires_json(client):
    response = client.post("/api/v1/quest/final-reveal/unlock")
    assert response.status_code == 400


def test_complete_level_wrong_state_returns_400(client):
    session_id = _create_session(client)

    response = client.post(
        "/api/v1/quest/levels/complete",
        json={
            "session_id": session_id,
            "level": 1,
            "answer": "LEVEL_ONE_ANSWER",
        },
    )

    # Quest is still in NEW; level 1 is not available.
    assert response.status_code == 400
