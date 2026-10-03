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
            name
            for name, value in required_values.items()
            if not value
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
    folder: str = "birthday-quest/recordings",
) -> dict[str, Any]:
    """
    Upload a video to Cloudinary.

    The backend receives the file and sends it directly to
    Cloudinary without permanently storing it on Render.

    Args:
        file_object:
            File-like object containing the recording.

        public_id:
            Stable identifier for the Cloudinary asset.

        folder:
            Cloudinary folder used for organization.

    Returns:
        Cloudinary upload response dictionary.
    """

    _initialize_cloudinary()

    if file_object is None:
        raise ValueError(
            "file_object cannot be None."
        )

    if not isinstance(public_id, str):
        raise TypeError(
            "public_id must be a string."
        )

    public_id = public_id.strip()

    if not public_id:
        raise ValueError(
            "public_id cannot be empty."
        )

    if "/" in public_id:
        raise ValueError(
            "public_id must not contain '/'."
        )

    if not isinstance(folder, str):
        raise TypeError(
            "folder must be a string."
        )

    folder = folder.strip().strip("/")

    if not folder:
        raise ValueError(
            "folder cannot be empty."
        )

    result = cloudinary.uploader.upload(
        file_object,
        resource_type="video",
        public_id=public_id,
        folder=folder,
        overwrite=False,
        unique_filename=False,
        invalidate=False,
        use_filename=False,
        type="upload",
    )

    return result


# ------------------------------------------------------------
# VERIFY ASSET
# ------------------------------------------------------------

def verify_video(
    public_id: str,
) -> dict[str, Any]:
    """
    Verify that a Cloudinary video asset exists.

    Returns Cloudinary resource metadata.
    """

    _initialize_cloudinary()

    if not isinstance(public_id, str):
        raise TypeError(
            "public_id must be a string."
        )

    public_id = public_id.strip()

    if not public_id:
        raise ValueError(
            "public_id cannot be empty."
        )

    result = cloudinary.api.resource(
        public_id,
        resource_type="video",
        type="upload",
    )

    return result


# ------------------------------------------------------------
# DELETE ASSET
# ------------------------------------------------------------

def delete_video(
    public_id: str,
) -> dict[str, Any]:
    """
    Delete a Cloudinary video asset.

    This operation will only be called by authorized backend
    workflows.
    """

    _initialize_cloudinary()

    if not isinstance(public_id, str):
        raise TypeError(
            "public_id must be a string."
        )

    public_id = public_id.strip()

    if not public_id:
        raise ValueError(
            "public_id cannot be empty."
        )

    result = cloudinary.uploader.destroy(
        public_id,
        resource_type="video",
        type="upload",
        invalidate=True,
    )

    return result
