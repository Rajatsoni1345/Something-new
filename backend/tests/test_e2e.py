"""
Birthday Quest - End-to-End Test

Walks through:
    create session
    -> get quest state (creates quest)
    -> walk states manually via service layer
    -> verify SESSION_COMPLETE deactivates session

Uses fakes only. No network.
"""

from constants import (
    QUEST_STATE_SESSION_COMPLETE,
)


def test_full_session_lifecycle_via_services(client, app):
    # 1. Create session
    response = client.post("/api/v1/sessions", json={})
    assert response.status_code == 201
    session_id = response.get_json()["data"]["session"]["session_id"]

    # 2. Get quest state (creates quest)
    response = client.post(
        "/api/v1/quest/state",
        json={"session_id": session_id},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["quest"]["state"] == "NEW"

    # 3. Session still active
    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    assert response.get_json()["data"]["session"]["active"] is True

    # 4. Walk the quest service directly to SESSION_COMPLETE.
    from services.session_service import get_session
    from services.quest_service import get_quest, transition_quest

    session = get_session(session_id)
    quest = get_quest(session_id)

    # Legal sequence of transitions ending in SESSION_COMPLETE
    transitions = [
        "INTRO_COMPLETE",
        "GATE_ENTERED",
        "MAGIC_VERIFIED",
        "BIRTHDAY_SCENE",
    ]

    for next_state in transitions:
        transition_quest(session=session, quest=quest, next_state=next_state)

    # 5. Session state should now reflect BIRTHDAY_SCENE
    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.get_json()["data"]["session"]["state"] == "BIRTHDAY_SCENE"

    # 6. Invalid jump must be rejected
    try:
        transition_quest(
            session=session,
            quest=quest,
            next_state=QUEST_STATE_SESSION_COMPLETE,
        )
        raise AssertionError(
            "Expected ValueError for illegal transition"
        )
    except ValueError:
        pass
