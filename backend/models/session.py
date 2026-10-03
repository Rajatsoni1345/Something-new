"""
Birthday Quest - Session Model

Defines the domain representation of a Birthday Quest session.

A session represents one complete journey through the quest.
The model contains only application data and does not directly
access Firebase or any external service.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class Session:
    """
    Represents one Birthday Quest session.

    Attributes:
        session_id:
            Unique identifier for the quest session.

        state:
            Current high-level state of the quest.

        created_at:
            UTC ISO 8601 timestamp when the session was created.

        updated_at:
            UTC ISO 8601 timestamp when the session was last updated.

        last_activity_at:
            UTC ISO 8601 timestamp of the latest meaningful activity.

        completed_at:
            UTC ISO 8601 timestamp when the entire quest was completed.
            None while the session is still active.

        version:
            Integer used for optimistic concurrency/version control.

        active:
            Whether the session is currently active.

        metadata:
            Non-sensitive session metadata required by the application.
    """

    session_id: str
    state: str
    created_at: str
    updated_at: str
    last_activity_at: str
    completed_at: str | None = None
    version: int = 1
    active: bool = True
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str):
            raise TypeError("session_id must be a string.")

        self.session_id = self.session_id.strip()

        if not self.session_id:
            raise ValueError("session_id cannot be empty.")

        if "/" in self.session_id:
            raise ValueError("session_id cannot contain '/'.")

        if not isinstance(self.state, str):
            raise TypeError("state must be a string.")

        self.state = self.state.strip()

        if not self.state:
            raise ValueError("state cannot be empty.")

        for field_name in (
            "created_at",
            "updated_at",
            "last_activity_at",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty."
                )

            setattr(self, field_name, value.strip())

        if self.completed_at is not None:
            if not isinstance(self.completed_at, str):
                raise TypeError(
                    "completed_at must be a string or None."
                )

            self.completed_at = self.completed_at.strip()

            if not self.completed_at:
                self.completed_at = None

        if not isinstance(self.version, int):
            raise TypeError("version must be an integer.")

        if self.version < 1:
            raise ValueError(
                "version must be greater than or equal to 1."
            )

        if not isinstance(self.active, bool):
            raise TypeError("active must be a boolean.")

        if self.metadata is not None:
            if not isinstance(self.metadata, dict):
                raise TypeError(
                    "metadata must be a dictionary or None."
                )

            self.metadata = dict(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the model into a Firestore-safe dictionary.
        """
        data = asdict(self)

        if data["metadata"] is None:
            data["metadata"] = {}

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Session":
        """
        Create a Session model from persisted dictionary data.
        """
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary.")

        required_fields = (
            "session_id",
            "state",
            "created_at",
            "updated_at",
            "last_activity_at",
        )

        missing_fields = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing_fields:
            raise ValueError(
                "Missing required session fields: "
                + ", ".join(missing_fields)
            )

        return cls(
            session_id=data["session_id"],
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            last_activity_at=data["last_activity_at"],
            completed_at=data.get("completed_at"),
            version=data.get("version", 1),
            active=data.get("active", True),
            metadata=data.get("metadata", {}),
        )
