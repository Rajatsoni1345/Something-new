"""
Birthday Quest - ID Utilities

Secure identifier generation helpers.
"""

from __future__ import annotations

import secrets
import uuid


# ------------------------------------------------------------
# UUID
# ------------------------------------------------------------

def generate_uuid() -> str:
    """
    Generate a cryptographically random UUID4 string.
    """

    return str(uuid.uuid4())


# ------------------------------------------------------------
# SECURE TOKEN
# ------------------------------------------------------------

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure URL-safe token.

    The length represents the number of random bytes before
    URL-safe encoding, so the resulting string may be longer.
    """

    if not isinstance(length, int):
        raise TypeError("length must be an integer.")

    if length < 16:
        raise ValueError(
            "Secure token length must be at least 16 bytes."
        )

    return secrets.token_urlsafe(length)


# ------------------------------------------------------------
# REQUEST ID
# ------------------------------------------------------------

def generate_request_id() -> str:
    """
    Generate a unique request identifier.
    """

    return generate_uuid()


# ------------------------------------------------------------
# SESSION ID
# ------------------------------------------------------------

def generate_session_id() -> str:
    """
    Generate a unique Birthday Quest session identifier.
    """

    return generate_uuid()


# ------------------------------------------------------------
# RECORDING ID
# ------------------------------------------------------------

def generate_recording_id() -> str:
    """
    Generate a unique recording identifier.
    """

    return generate_uuid()
