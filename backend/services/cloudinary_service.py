"""
Birthday Quest - Cloudinary Service

Centralized Cloudinary configuration and media operations.

IMPORTANT:
- Cloudinary credentials come only from environment variables.
- API secrets are never returned to the frontend.
- Uploads are designed for permanent media storage.
"""

from __future__ import annotations

import threading
from typing import Any

import cloudinary
import cloudinary.api
import cloudinary.uploader

from config import get_config
from constants import CLOUDINARY_FOLDER


# Re-exported for test introspection and service composition.
__all__ = [
    "CLOUDINARY_FOLDER",
    "upload_video",
    "verify_video",
    "delete_video",
]


# ------------------------------------------------------------
# INITIALIZATION STATE
# ------------------------------------------------------------

_cloudinary_lock = threading.Lock()
_cloudinary_initialized = False


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

def _initialize_cloudinary() -> None:
    """
    Initialize Cloudinary exactly once.
    """

    global _cloudinary_initialized

    if _cloudinary_initialized:
        return

    with _cloudinary_lock:
        if _cloudinary_initialized:
            return

        config = get_config()

        required_values = {
            "cloud_name": config.CLOUDINARY_CLOUD_NAME,
            "api_key": config.CLOUDINARY_API_KEY,
            "api_secret": config.CLOUDINARY_API_SECRET,
        }

        missing = [
            name for name, value in required_values.items() if not value
        ]

        if missing:
            raise RuntimeError(
                "Cloudinary configuration is incomplete. "
                f"Missing: {', '.join(missing)}"
            )

        cloudinary.config(
            cloud_name=config.CLOUDINARY_CLOUD_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET,
            secure=True,
        )

        _cloudinary_initialized = True


# ------------------------------------------------------------
# UPLOAD
# ------------------------------------------------------------

def upload_video(
    file_object: Any,
    public_id: str,
    folder: str = CLOUDINARY_FOLDER,
) -> dict[str, Any]:
    """
    Upload a video to Cloudinary.

    The backend receives the file and sends it directly to
    Cloudinary without permanently storing it on Render.
    """

    _initialize_cloudinary()

    if file_object is None:
        raise ValueError("file_object cannot be None.")

    if not isinstance(public_id, str):
        raise TypeError("public_id must be a string.")

    public_id = public_id.strip()

    if not public_id:
        raise ValueError("public_id cannot be empty.")

    if "/" in public_id:
        raise ValueError("public_id must not contain '/'.")

    if not isinstance(folder, str):
        raise TypeError("folder must be a string.")

    folder = folder.strip().strip("/")

    if not folder:
        raise ValueError("folder cannot be empty.")

    result = cloudinary.uploader.upload(
        file_object,
        resource_type="video",
        public_id=public_id,
        folder=folder,
