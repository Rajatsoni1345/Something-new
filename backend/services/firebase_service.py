"""
Birthday Quest - Firebase Service

Centralized Firebase Admin SDK initialization and Firestore
access.

IMPORTANT:
- Firebase credentials are read only from environment variables.
- No credentials are stored in source code.
- Firebase is initialized lazily so local development can start
  before Firebase credentials are configured.
"""

from __future__ import annotations

import threading
from typing import Any

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from config import get_config


# ------------------------------------------------------------
# INITIALIZATION STATE
# ------------------------------------------------------------

_firebase_lock = threading.Lock()
_firebase_app = None
_firestore_client = None


# ------------------------------------------------------------
# REQUIRED CREDENTIALS
# ------------------------------------------------------------

def _get_credentials() -> credentials.Certificate:
    """
    Build Firebase Admin credentials from environment-backed
    configuration.
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

    return credentials.Certificate(service_account)


# ------------------------------------------------------------
# FIREBASE APP
# ------------------------------------------------------------

def get_firebase_app():
    """
    Return the initialized Firebase Admin application.

    Initialization is thread-safe and happens only once.
    """

    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    with _firebase_lock:
        if _firebase_app is not None:
            return _firebase_app

        existing_apps = firebase_admin._apps

        if existing_apps:
            _firebase_app = firebase_admin.get_app()
        else:
            firebase_credential = _get_credentials()

            _firebase_app = firebase_admin.initialize_app(
                firebase_credential,
            )

    return _firebase_app


# ------------------------------------------------------------
# FIRESTORE CLIENT
# ------------------------------------------------------------

def get_firestore_client():
    """
    Return the shared Firestore client.

    The Firebase Admin application is initialized before creating
    the Firestore client.
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


# ------------------------------------------------------------
# COLLECTION REFERENCE
# ------------------------------------------------------------

def get_collection(
    collection_name: str,
):
    """
    Return a Firestore collection reference.

    Collection names are validated to avoid accidental use of
    empty or malformed collection paths.
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
            "collection_name must contain only one collection name."
        )

    return get_firestore_client().collection(
        collection_name
    )


# ------------------------------------------------------------
# DOCUMENT REFERENCE
# ------------------------------------------------------------

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
    ).document(
        document_id
    )


# ------------------------------------------------------------
# DOCUMENT READ
# ------------------------------------------------------------

def get_document_data(
    collection_name: str,
    document_id: str,
) -> dict[str, Any] | None:
    """
    Read a Firestore document.

    Returns:
        Document data dictionary if the document exists,
        otherwise None.
    """

    document = get_document(
        collection_name,
        document_id,
    ).get()

    if not document.exists:
        return None

    return document.to_dict()


# ------------------------------------------------------------
# DOCUMENT CREATE / REPLACE
# ------------------------------------------------------------

def set_document_data(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
) -> None:
    """
    Create or completely replace a Firestore document.
    """

    if not isinstance(data, dict):
        raise TypeError(
            "data must be a dictionary."
        )

    get_document(
        collection_name,
        document_id,
    ).set(data)


# ------------------------------------------------------------
# DOCUMENT UPDATE
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# DOCUMENT DELETE
# ------------------------------------------------------------

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
