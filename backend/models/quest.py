"""
Birthday Quest - Quest Model

Defines the domain representation of a quest's progress.

This model does not contain Firebase or HTTP logic. It only
represents quest data in a predictable, validated structure.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Quest:
    """
    Represents the progress of a Birthday Quest.

    Attributes:
        session_id:
            Session to which this quest belongs.

        state:
            Current quest state.

        current_level:
            Highest level currently available to the player.

        completed_levels:
            Levels that have been successfully completed.

        collected_items:
            Magical quest items collected during the journey.

        discovered_words:
            Hidden words discovered during completed levels.

        collected_ticket:
            Whether the railway ticket has been collected.

        train_completed:
            Whether the magical train sequence is complete.

        final_reveal_unlocked:
            Whether the final reveal has been unlocked.

        version:
            Quest data version used for optimistic concurrency.

        metadata:
            Additional non-sensitive quest metadata.
    """

    session_id: str
    state: str
    current_level: int = 0
    completed_levels: list[int] = field(default_factory=list)
    collected_items: list[str] = field(default_factory=list)
    discovered_words: list[str] = field(default_factory=list)
    collected_ticket: bool = False
    train_completed: bool = False
    final_reveal_unlocked: bool = False
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

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

        if not isinstance(self.current_level, int):
            raise TypeError("current_level must be an integer.")

        if not 0 <= self.current_level <= 5:
            raise ValueError(
                "current_level must be between 0 and 5."
            )

        if not isinstance(self.completed_levels, list):
            raise TypeError(
                "completed_levels must be a list."
            )

        self.completed_levels = self._validate_levels(
            self.completed_levels
        )

        if not isinstance(self.collected_items, list):
            raise TypeError(
                "collected_items must be a list."
            )

        self.collected_items = self._validate_strings(
            self.collected_items,
            "collected_items",
        )

        if not isinstance(self.discovered_words, list):
            raise TypeError(
                "discovered_words must be a list."
            )

        self.discovered_words = self._validate_strings(
            self.discovered_words,
            "discovered_words",
        )

        if not isinstance(self.collected_ticket, bool):
            raise TypeError(
                "collected_ticket must be a boolean."
            )

        if not isinstance(self.train_completed, bool):
            raise TypeError(
                "train_completed must be a boolean."
            )

        if not isinstance(self.final_reveal_unlocked, bool):
            raise TypeError(
                "final_reveal_unlocked must be a boolean."
            )

        if not isinstance(self.version, int):
            raise TypeError("version must be an integer.")

        if self.version < 1:
            raise ValueError(
                "version must be greater than or equal to 1."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

        self.metadata = dict(self.metadata)

        if self.current_level > 0:
            expected_completed = set(
                range(1, self.current_level)
            )

            if not expected_completed.issubset(
                set(self.completed_levels)
            ):
                raise ValueError(
                    "completed_levels is inconsistent with "
                    "current_level."
                )

        if self.final_reveal_unlocked and (
            self.current_level < 5
        ):
            raise ValueError(
                "Final reveal cannot be unlocked before "
                "the final level."
            )

    @staticmethod
    def _validate_levels(
        levels: list[int],
    ) -> list[int]:
        validated: list[int] = []

        for level in levels:
            if not isinstance(level, int):
                raise TypeError(
                    "Every completed level must be an integer."
                )

            if not 1 <= level <= 5:
                raise ValueError(
                    "Completed levels must be between 1 and 5."
                )

            if level not in validated:
                validated.append(level)

        return sorted(validated)

    @staticmethod
    def _validate_strings(
        values: list[str],
        field_name: str,
    ) -> list[str]:
        validated: list[str] = []

        for value in values:
            if not isinstance(value, str):
                raise TypeError(
                    f"Every value in {field_name} must be a string."
                )

            value = value.strip()

            if not value:
                raise ValueError(
                    f"{field_name} cannot contain empty values."
                )

            if value not in validated:
                validated.append(value)

        return validated

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the model into a Firestore-safe dictionary.
        """
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Quest":
        """
        Create a Quest model from persisted dictionary data.
        """
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary.")

        if "session_id" not in data:
            raise ValueError(
                "Missing required quest field: session_id."
            )

        if "state" not in data:
            raise ValueError(
                "Missing required quest field: state."
            )

        return cls(
            session_id=data["session_id"],
            state=data["state"],
            current_level=data.get("current_level", 0),
            completed_levels=data.get(
                "completed_levels",
                [],
            ),
            collected_items=data.get(
                "collected_items",
                [],
            ),
            discovered_words=data.get(
                "discovered_words",
                [],
            ),
            collected_ticket=data.get(
                "collected_ticket",
                False,
            ),
            train_completed=data.get(
                "train_completed",
                False,
            ),
            final_reveal_unlocked=data.get(
                "final_reveal_unlocked",
                False,
            ),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
                         )
