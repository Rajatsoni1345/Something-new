"""
Birthday Quest - Firebase Service

Centralized Firebase Admin SDK initialization and Firestore
access.

Storage architecture:
- Firebase Firestore -> sessions, quest state, metadata, audit data
- Cloudinary -> permanent video/media storage
- Render filesystem -> no permanent media storage

IMPORTANT:
- Firebase credentials are read only from environment variables.
- No credentials are stored in source code.
- Firebase initialization is lazy.
- Firestore clients are reused.
- Firestore transactions are exposed through this service layer.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar

import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore


# ============================================================
# TYPES
# ============================================================

T = TypeVar(
    "T"
)


# ============================================================
# FIREBASE STATE
# ============================================================

_firebase_lock = threading.RLock()

_firebase_app = None

_firestore_client = None


# ============================================================
# FIREBASE CREDENTIALS
# ============================================================

def _get_credentials() -> credentials.Certificate:
    """
    Build Firebase service-account credentials from environment
    variables.

    Credentials are imported lazily to avoid requiring Firebase
    configuration merely to import this module.
    """

    from config import get_config

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


# ============================================================
# FIREBASE APP
# ============================================================

def get_firebase_app():
    """
    Return the initialized Firebase application.

    Initialization is lazy and protected by a lock so concurrent
    requests cannot initialize multiple default Firebase apps.
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


# ============================================================
# FIRESTORE CLIENT
# ============================================================

def get_firestore_client():
    """
    Return the shared Firestore client.

    The client is initialized only once and reused.
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


# ============================================================
# TRANSACTIONS
# ============================================================

def create_transaction():
    """
    Create a new Firestore transaction.

    The caller is responsible for:
    - reading documents through the transaction
    - applying transactional writes
    - committing the transaction
    """

    client = get_firestore_client()

    return client.transaction()


def run_transaction(
    callback: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Execute a callback inside a Firestore transaction.

    The callback receives the transaction object as its first
    argument.

    Example:

        def operation(transaction):
            snapshot = transaction.get(document)
            ...
            transaction.update(document, {...})
            return result

        result = run_transaction(operation)
    """

    if not callable(callback):
        raise TypeError(
            "callback must be callable."
        )

    transaction = create_transaction()

    return transaction.callable(
        callback
    )(
        transaction,
        *args,
        **kwargs,
    )


# ============================================================
# COLLECTION ACCESS
# ============================================================

def get_collection(
    collection_name: str,
):
    """
    Return a Firestore collection reference.
    """

    if not isinstance(
        collection_name,
        str,
    ):
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


# ============================================================
# DOCUMENT ACCESS
# ============================================================

def get_document(
    collection_name: str,
    document_id: str,
):
    """
    Return a Firestore document reference.
    """

    if not isinstance(
        document_id,
        str,
    ):
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


# ============================================================
# READ DOCUMENT
# ============================================================

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
    )

    snapshot = document.get()

    if not snapshot.exists:
        return None

    data = snapshot.to_dict()

    if data is None:
        return None

    return dict(
        data
    )


# ============================================================
# SET DOCUMENT
# ============================================================

def set_document_data(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
) -> None:
    """
    Replace or create a Firestore document.
    """

    if not isinstance(
        data,
        dict,
    ):
        raise TypeError(
            "data must be a dictionary."
        )

    get_document(
        collection_name,
        document_id,
    ).set(
        data
    )


# ============================================================
# CREATE DOCUMENT
# ============================================================

def create_document_data(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
) -> None:
    """
    Create a Firestore document.

    Raises an error if the document already exists.
    """

    if not isinstance(
        data,
        dict,
    ):
        raise TypeError(
            "data must be a dictionary."
        )

    get_document(
        collection_name,
        document_id,
    ).create(
        data
    )


# ============================================================
# UPDATE DOCUMENT
# ============================================================

def update_document_data(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
) -> None:
    """
    Update selected fields in an existing Firestore document.
    """

    if not isinstance(
        data,
        dict,
    ):
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
    ).update(
        data
    )


# ============================================================
# DELETE DOCUMENT
# ============================================================

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
