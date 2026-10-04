"""
Birthday Quest - Test Fixtures

Provides:
    - app fixture (testing environment)
    - client fixture
    - In-memory fake Firestore
    - Fake Cloudinary uploader

Tests never touch real Firebase or Cloudinary.
"""

from __future__ import annotations

import copy
import threading
from typing import Any

import pytest


# ============================================================
# FAKE FIRESTORE
# ============================================================

class _FakeSnapshot:
    def __init__(self, data: dict | None):
        self._data = copy.deepcopy(data)

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict | None:
        return copy.deepcopy(self._data)


class _FakeDocument:
    def __init__(self, store: dict, key: tuple[str, str]):
        self._store = store
        self._key = key

    def get(self) -> _FakeSnapshot:
        return _FakeSnapshot(self._store.get(self._key))

    def set(self, data: dict) -> None:
        self._store[self._key] = copy.deepcopy(data)

    def create(self, data: dict) -> None:
        if self._key in self._store:
            raise RuntimeError("Document already exists.")
        self._store[self._key] = copy.deepcopy(data)

    def update(self, data: dict) -> None:
        existing = self._store.get(self._key)

        if existing is None:
            raise RuntimeError("Document does not exist.")

        existing.update(copy.deepcopy(data))

    def delete(self) -> None:
        self._store.pop(self._key, None)


class _FakeCollection:
    def __init__(self, store: dict, name: str):
        self._store = store
        self._name = name

    def document(self, document_id: str) -> _FakeDocument:
        return _FakeDocument(self._store, (self._name, document_id))


class _FakeTransaction:
    def __init__(self, store: dict):
        self._store = store
        self._pending_writes: list[tuple[str, tuple, dict, str]] = []

    def get(self, document: _FakeDocument) -> _FakeSnapshot:
        return _FakeSnapshot(self._store.get(document._key))

    def set(self, document: _FakeDocument, data: dict) -> None:
        self._pending_writes.append(("set", document._key, data, ""))

    def create(self, document: _FakeDocument, data: dict) -> None:
        self._pending_writes.append(("create", document._key, data, ""))

    def update(self, document: _FakeDocument, data: dict) -> None:
        self._pending_writes.append(("update", document._key, data, ""))

    def delete(self, document: _FakeDocument) -> None:
        self._pending_writes.append(("delete", document._key, {}, ""))

    def commit(self) -> None:
        for op, key, data, _ in self._pending_writes:
            if op == "set":
                self._store[key] = copy.deepcopy(data)
            elif op == "create":
                if key in self._store:
                    raise RuntimeError("Document already exists.")
                self._store[key] = copy.deepcopy(data)
            elif op == "update":
                existing = self._store.get(key)
                if existing is None:
                    raise RuntimeError("Document does not exist.")
                existing.update(copy.deepcopy(data))
            elif op == "delete":
                self._store.pop(key, None)

        self._pending_writes.clear()


class _FakeFirestoreClient:
    """
    In-memory stand-in for firebase_admin.firestore.client().

    Supports:
        - collection()
        - document()
        - transaction()
        - transactional decorator behaviour used by services
    """

    def __init__(self):
        self._store: dict[tuple[str, str], dict] = {}
        self._lock = threading.RLock()

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self._store, name)

    def transaction(self) -> _FakeTransaction:
        return _FakeTransaction(self._store)


# ============================================================
# FAKE CLOUDINARY
# ============================================================

class _FakeCloudinaryUploader:
    """
    Fake Cloudinary uploader for tests.
    """

    def __init__(self):
        self._uploaded: dict[str, dict] = {}
        self._fail_next = False

    def fail_next_upload(self) -> None:
        self._fail_next = True

    def upload(self, file_object, **kwargs) -> dict:
        if self._fail_next:
            self._fail_next = False
            raise RuntimeError("Simulated Cloudinary failure.")

        public_id = kwargs.get("public_id") or "fake-public-id"
        folder = kwargs.get("folder", "")

        full_public_id = (
            f"{folder}/{public_id}" if folder else public_id
        )

        resource = {
            "public_id": full_public_id,
            "resource_type": "video",
            "secure_url": (
                f"https://res.cloudinary.com/fake/video/upload/"
                f"{full_public_id}.webm"
            ),
            "bytes": 1024,
            "format": "webm",
        }

        self._uploaded[full_public_id] = resource

        return resource

    def destroy(self, public_id, **kwargs) -> dict:
        self._uploaded.pop(public_id, None)
        return {"result": "ok"}

    def reset(self) -> None:
        self._uploaded.clear()
        self._fail_next = False


class _FakeCloudinaryApi:
    def __init__(self, uploader: _FakeCloudinaryUploader):
        self._uploader = uploader

    def resource(self, public_id, **kwargs) -> dict:
        resource = self._uploader._uploaded.get(public_id)

        if resource is None:
            raise RuntimeError("Resource does not exist in Cloudinary.")

        return copy.deepcopy(resource)


class _FakeCloudinary:
    def __init__(self):
        self.uploader = _FakeCloudinaryUploader()
        self.api = _FakeCloudinaryApi(self.uploader)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture()
def fake_firestore() -> _FakeFirestoreClient:
    return _FakeFirestoreClient()


@pytest.fixture()
def fake_cloudinary() -> _FakeCloudinary:
    return _FakeCloudinary()


@pytest.fixture()
def app(monkeypatch, fake_firestore, fake_cloudinary):
    """
    Create a testing Flask app with fully faked external
    dependencies.
    """

    # --------------------------------------------------------
    # Patch Firebase BEFORE app creation so any lazy init
    # during import sees the fakes.
    # --------------------------------------------------------

    from services import firebase_service

    monkeypatch.setattr(
        firebase_service,
        "get_firestore_client",
        lambda: fake_firestore,
    )

    # --------------------------------------------------------
    # Patch Cloudinary to a fake that exposes uploader/api.
    # --------------------------------------------------------

    from services import cloudinary_service

    monkeypatch.setattr(
        cloudinary_service,
        "cloudinary",
        fake_cloudinary,
    )

    # Prevent real Cloudinary initialization.
    monkeypatch.setattr(
        cloudinary_service,
        "_initialize_cloudinary",
        lambda: None,
    )

    from app import create_app

    flask_app = create_app("testing")

    flask_app.config.update(TESTING=True)

    # Keep a handle to fakes for test inspection.
    flask_app._fake_firestore = fake_firestore
    flask_app._fake_cloudinary = fake_cloudinary

    return flask_app


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client
