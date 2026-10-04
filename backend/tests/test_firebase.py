import pytest

from app import create_app
from services import firebase_service


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(TESTING=True)
    return app


def test_firebase_service_has_expected_interface():
    assert callable(firebase_service.get_firebase_app)
    assert callable(firebase_service.get_firestore_client)
    assert callable(firebase_service.create_transaction)
    assert callable(firebase_service.run_transaction)


def test_collection_reference_requires_collection_name():
    with pytest.raises((ValueError, TypeError)):
        firebase_service.collection_ref("")


def test_document_reference_requires_collection_name():
    with pytest.raises((ValueError, TypeError)):
        firebase_service.document_ref("", "test-id")


def test_document_reference_requires_document_id():
    with pytest.raises((ValueError, TypeError)):
        firebase_service.document_ref("sessions", "")


def test_firestore_helpers_use_client(monkeypatch):
    class FakeClient:
        def collection(self, name):
            return ("collection", name)

    fake_client = FakeClient()

    monkeypatch.setattr(
        firebase_service,
        "get_firestore_client",
        lambda: fake_client,
    )

    result = firebase_service.collection_ref("sessions")

    assert result == ("collection", "sessions")


def test_firestore_document_helper_uses_client(monkeypatch):
    class FakeCollection:
        def document(self, document_id):
            return ("document", document_id)

    class FakeClient:
        def collection(self, name):
            assert name == "sessions"
            return FakeCollection()

    monkeypatch.setattr(
        firebase_service,
        "get_firestore_client",
        lambda: FakeClient(),
    )

    result = firebase_service.document_ref(
        "sessions",
        "session-123",
    )

    assert result == ("document", "session-123")


def test_run_transaction_requires_callable():
    with pytest.raises((ValueError, TypeError)):
        firebase_service.run_transaction(None)
