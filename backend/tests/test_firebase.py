from services import firebase_service


def test_document_ref_requires_collection_name():
    try:
        firebase_service.get_document("", "doc")
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected ValueError or TypeError")


def test_document_ref_requires_document_id():
    try:
        firebase_service.get_document("sessions", "")
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected ValueError or TypeError")


def test_run_transaction_requires_callable():
    try:
        firebase_service.run_transaction(None)
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected ValueError or TypeError")


def test_collection_and_document_helpers_work(monkeypatch):
    class FakeCollection:
        def document(self, doc_id):
            return ("document", doc_id)

    class FakeClient:
        def collection(self, name):
            assert name == "sessions"
            return FakeCollection()

    monkeypatch.setattr(
        firebase_service, "get_firestore_client", lambda: FakeClient()
    )

    result = firebase_service.get_document("sessions", "abc")
    assert result == ("document", "abc")
