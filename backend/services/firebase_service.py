"""
Birthday Quest - Firebase Service

Centralized Firebase Admin SDK initialization and Firestore
access.

IMPORTANT:
- Firebase credentials are read only from environment variables.
- No credentials are stored in source code.
- Firebase initialization is lazy.
- Public Firebase Admin SDK APIs are used for app discovery.
- Initialization is protected against concurrent requests.
"""

from __future__ import annotations

import threading
from typing import Any

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from config import get_config


_firebase_lock = threading.RLock()

_firebase_app = None
_firestore_client = None


def _get_credentials() -> credentials.Certificate:
    """
    Build Firebase service-account credentials from environment
    variables.
    """
    config = get_config()

    required_values = {
        "project_id": config.FIREBASE_PROJECT_ID,
        "private_key_id": config.FIREBASE_PRIVATE_KEY_ID,
        "private_key": config.FIREBASE_PRIVATE_KEY,
        "client_email": config.FIREBASE_CLIENT_EMAIL,
        "client_id": config.FIREBASE_CLIENT_ID,
    }

    missing = [
        name
        for name, value in required_values.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Firebase configuration is incomplete. "
            f"Missing: {', '.join(missing)}"
        )

    service_account = {
        "type": "service_account",
        "project_id": config.FIREBASE_PROJECT_ID,
        "private_key_id": config.FIREBASE_PRIVATE_KEY_ID,
        "private_key": config.FIREBASE_PRIVATE_KEY,
        "client_email": config.FIREBASE_CLIENT_EMAIL,
        "client_id": config.FIREBASE_CLIENT_ID,
        "token_uri": (
            "https://oauth2.googleapis.com/token"
        ),
    }

    return credentials.Certificate(
        service_account
    )


def get_firebase_app():
    """
    Return the initialized Firebase application.

    Firebase is initialized lazily on the first call.

    A public Firebase Admin SDK lookup is attempted first.
    If no default app exists, a new one is initialized safely.
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    with _firebase_lock:
        if _firebase_app is not None:
            return _firebase_app

        try:
            _firebase_app = firebase_admin.get_app()
        except ValueError:
            firebase_credential = _get_credentials()

            _firebase_app = firebase_admin.initialize_app(
                firebase_credential
            )

        return _firebase_app


def get_firestore_client():
    """
    Return the shared Firestore client.

    The client is created only once and reused for subsequent
    requests.
    """
    global _firestore_client

    if _firestore_client is not None:
        return _firestore_client

    with _firebase_lock:
        if _firestore_client is not None:
            return _firestore_client

        firebase_app = get_firebase_app()

        _firestore_client = firestore.client(
            app=firebase_app
        )

        return _firestore_client


def get_collection(collection_name: str):
    """
    Return a Firestore collection reference.
    """
    if not isinstance(collection_name, str):
        raise TypeError(
            "collection_name must be a string."
        )

    collection_name = collection_name.strip()

    if not collection_name:
        raise ValueError(
            "collection_name cannot be empty."
        )

    if "/" in collection_name:
        raise ValueError(
            "collection_name must contain only one "
            "collection name."
        )

    return get_firestore_client().collection(
        collection_name
    )


def get_document(
    collection_name: str,
    document_id: str,
):
    """
    Return a Firestore document reference.
    """
    if not isinstance(document_id, str):
        raise TypeError(
            "document_id must be a string."
        )

    document_id = document_id.strip()

    if not document_id:
        raise ValueError(
            "document_id cannot be empty."
        )

    if "/" in document_id:
        raise ValueError(
            "document_id cannot contain '/'."
        )

    return get_collection(
        collection_name
    ).document(document_id)


def get_document_data(
    collection_name: str,
    document_id: str,
) -> dict[str, Any] | None:
    """
    Read a Firestore document.

    Returns None when the document does not exist.
    """
    document = get_document(
        collection_name,
        document_id,
    ).get()

    if not document.exists:
        return None

    data = document.to_dict()

    if data is None:
        return None

    return dict(data)


def set_document_data(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
) -> None:
    """
    Replace/create a Firestore document.
    """
    if not isinstance(data, dict):
        raise TypeError(
            "data must be a dictionary."
        )

    get_document(
        collection_name,
        document_id,
    ).set(data)


def update_document_data(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
) -> None:
    """
    Update selected fields in an existing Firestore document.
    """
    if not isinstance(data, dict):
        raise TypeError(
            "data must be a dictionary."
        )

    if not data:
        raise ValueError(
            "data cannot be empty."
        )

    get_document(
        collection_name,
        document_id,
    ).update(data)


def delete_document(
    collection_name: str,
    document_id: str,
) -> None:
    """
    Delete a Firestore document.
    """
    get_document(
        collection_name,
        document_id,
    ).delete()
