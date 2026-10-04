"""
Birthday Quest - Recording Model

Defines the domain representation of a user recording.

The model contains recording metadata only. Actual video files
are stored permanently in Cloudinary and are never stored in
Firestore or on the Render filesystem.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from constants import (
    ALLOWED_RECORDING_STATUSES,
    ALLOWED_RECORDING_TYPES,
)


# ============================================================
# MODULE-LEVEL CONSTANTS
# ============================================================
#
# These live OUTSIDE the dataclass to avoid any interaction
# with @dataclass(slots=True). The dataclass __slots__ only
# allocates storage for annotated fields, but keeping class
# variables out avoids confusion and version-specific edge
# cases.
# ============================================================

ALLOWED_TYPES = ALLOWED_RECORDING_TYPES
ALLOWED_STATUSES = ALLOWED_RECORDING_STATUSES


# ============================================================
# MODEL
# ============================================================

@dataclass(slots=True)
class Recording:
    """
    Represents one recording belonging to a quest session.
    """

    recording_id: str
    session_id: str
    recording_type: str
    status: str
    created_at: str
    updated_at: str

    cloudinary_public_id: str | None = None
    secure_url: str | None = None
    resource_type: str | None = None
    duration_ms: int | None = None
    file_size_bytes: int | None = None
    content_type: str | None = None
    completed_at: str | None = None
    attempt: int = 1
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate_identifier(self.recording_id, "recording_id")
        self._validate_identifier(self.session_id, "session_id")

        self.recording_id = self.recording_id.strip()
        self.session_id = self.session_id.strip()

        self.recording_type = self._validate_enum(
            self.recording_type,
            "recording_type",
            ALLOWED_TYPES,
        )

        self.status = self._validate_enum(
            self.status,
            "status",
            ALLOWED_STATUSES,
        )

        self.created_at = self._validate_required_string(
            self.created_at, "created_at"
        )

        self.updated_at = self._validate_required_string(
            self.updated_at, "updated_at"
        )

        if self.completed_at is not None:
            self.completed_at = self._validate_optional_string(
                self.completed_at, "completed_at"
            )

        if self.cloudinary_public_id is not None:
            self.cloudinary_public_id = self._validate_optional_string(
                self.cloudinary_public_id,
                "cloudinary_public_id",
            )

        if self.secure_url is not None:
            self.secure_url = self._validate_optional_string(
                self.secure_url, "secure_url"
            )
            if not self.secure_url.startswith("https://"):
                raise ValueError("secure_url must use HTTPS.")

        if self.resource_type is not None:
            self.resource_type = self._validate_optional_string(
                self.resource_type, "resource_type"
            )

        if self.duration_ms is not None:
            self.duration_ms = self._validate_positive_int(
                self.duration_ms, "duration_ms", allow_zero=True
            )

        if self.file_size_bytes is not None:
            self.file_size_bytes = self._validate_positive_int(
                self.file_size_bytes, "file_size_bytes", allow_zero=False
            )

        if self.content_type is not None:
            self.content_type = self._validate_optional_string(
                self.content_type, "content_type"
            )

        self.attempt = self._validate_positive_int(
            self.attempt, "attempt", allow_zero=False
        )

        self.version = self._validate_positive_int(
            self.version, "version", allow_zero=False
        )

        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary.")

        self.metadata = dict(self.metadata)

        self._validate_status_consistency()

    # --------------------------------------------------------
    # VALIDATORS
    # --------------------------------------------------------

    @staticmethod
    def _validate_identifier(value: str, field_name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        value = value.strip()

        if not value:
            raise ValueError(f"{field_name} cannot be empty.")

        if "/" in value:
            raise ValueError(f"{field_name} cannot contain '/'.")

    @staticmethod
    def _validate_required_string(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        value = value.strip()

        if not value:
            raise ValueError(f"{field_name} cannot be empty.")

        return value

    @staticmethod
    def _validate_optional_string(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string or None.")

        value = value.strip()

        if not value:
            raise ValueError(f"{field_name} cannot be empty when provided.")

        return value

    @staticmethod
    def _validate_enum(
        value: str,
        field_name: str,
        allowed_values: frozenset[str],
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        value = value.strip()

        if value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            raise ValueError(
                f"Invalid {field_name}: {value!r}. "
                f"Allowed values: {allowed}."
            )

        return value

    @staticmethod
    def _validate_positive_int(
        value: int,
        field_name: str,
        *,
        allow_zero: bool,
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{field_name} must be an integer.")

        minimum = 0 if allow_zero else 1

        if value < minimum:
            comparison = (
                "greater than or equal to 0"
                if allow_zero
                else "greater than 0"
            )
            raise ValueError(f"{field_name} must be {comparison}.")

        return value

    def _validate_status_consistency(self) -> None:
        if self.status in {"uploaded", "verified"} and not self.cloudinary_public_id:
            raise ValueError(
                "A Cloudinary public ID is required when "
                "recording status is uploaded or verified."
            )

        if self.status == "verified":
            if not self.secure_url:
                raise ValueError(
                    "A secure URL is required when a recording is verified."
                )

            if not self.resource_type:
                raise ValueError(
                    "A resource type is required when a recording is verified."
                )

            if self.resource_type != "video":
                raise ValueError(
                    "Verified recordings must have resource_type='video'."
                )

    # --------------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recording":
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary.")

        required_fields = (
            "recording_id",
            "session_id",
            "recording_type",
            "status",
            "created_at",
            "updated_at",
        )

        missing_fields = [
            field for field in required_fields if field not in data
        ]

        if missing_fields:
            raise ValueError(
                "Missing required recording fields: "
                + ", ".join(missing_fields)
            )

        return cls(
            recording_id=data["recording_id"],
            session_id=data["session_id"],
            recording_type=data["recording_type"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            cloudinary_public_id=data.get("cloudinary_public_id"),
            secure_url=data.get("secure_url"),
            resource_type=data.get("resource_type"),
            duration_ms=data.get("duration_ms"),
            file_size_bytes=data.get("file_size_bytes"),
            content_type=data.get("content_type"),
            completed_at=data.get("completed_at"),
            attempt=data.get("attempt", 1),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
