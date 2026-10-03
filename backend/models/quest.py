"""
Birthday Quest - Quest Model

Defines the domain representation of a quest's progress.

This model does not contain Firebase or HTTP logic. It only
represents quest data in a predictable, validated structure.

IMPORTANT:
- Normal quest levels are strictly 1 through 4.
- Level 5 is reserved for the separate final-reveal flow and
  is therefore NOT a valid completed level.
- The model validates internal consistency so malformed quest
  data cannot silently enter the service layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# ============================================================
# QUEST CONSTANTS
# ============================================================

MIN_QUEST_LEVEL = 0
MAX_QUEST_LEVEL = 4

NORMAL_QUEST_LEVELS = frozenset(
    {1, 2, 3, 4}
)


# ============================================================
# QUEST MODEL
# ============================================================

@dataclass(slots=True)
class Quest:
    """
    Domain model representing the progress of one quest session.
    """

    session_id: str
    state: str

    current_level: int = 0

    completed_levels: list[int] = field(
        default_factory=list
    )

    collected_items: list[str] = field(
        default_factory=list
    )

    discovered_words: list[str] = field(
        default_factory=list
    )

    collected_ticket: bool = False

    train_completed: bool = False

    final_reveal_unlocked: bool = False

    version: int = 1

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate the complete quest object immediately after
        construction.
        """

        self._validate_session_id()

        self._validate_state()

        self._validate_current_level()

        self._validate_completed_levels()

        self._validate_collected_items()

        self._validate_discovered_words()

        self._validate_boolean_fields()

        self._validate_version()

        self._validate_metadata()

        self._validate_progress_consistency()

    # ========================================================
    # SESSION ID
    # ========================================================

    def _validate_session_id(self) -> None:
        if not isinstance(
            self.session_id,
            str,
        ):
            raise TypeError(
                "session_id must be a string."
            )

        self.session_id = self.session_id.strip()

        if not self.session_id:
            raise ValueError(
                "session_id cannot be empty."
            )

        if "/" in self.session_id:
            raise ValueError(
                "session_id cannot contain '/'."
            )

    # ========================================================
    # STATE
    # ========================================================

    def _validate_state(self) -> None:
        if not isinstance(
            self.state,
            str,
        ):
            raise TypeError(
                "state must be a string."
            )

        self.state = self.state.strip()

        if not self.state:
            raise ValueError(
                "state cannot be empty."
            )

        if len(self.state) > 128:
            raise ValueError(
                "state cannot exceed 128 characters."
            )

    # ========================================================
    # CURRENT LEVEL
    # ========================================================

    def _validate_current_level(self) -> None:
        if (
            isinstance(
                self.current_level,
                bool,
            )
            or not isinstance(
                self.current_level,
                int,
            )
        ):
            raise TypeError(
                "current_level must be an integer."
            )

        if not (
            MIN_QUEST_LEVEL
            <= self.current_level
            <= MAX_QUEST_LEVEL
        ):
            raise ValueError(
                "current_level must be between "
                f"{MIN_QUEST_LEVEL} and "
                f"{MAX_QUEST_LEVEL}."
            )

    # ========================================================
    # COMPLETED LEVELS
    # ========================================================

    def _validate_completed_levels(self) -> None:
        if not isinstance(
            self.completed_levels,
            list,
        ):
            raise TypeError(
                "completed_levels must be a list."
            )

        validated_levels: list[int] = []

        for level in self.completed_levels:
            if (
                isinstance(level, bool)
                or not isinstance(level, int)
            ):
                raise TypeError(
                    "Every completed level must be an integer."
                )

            if level not in NORMAL_QUEST_LEVELS:
                raise ValueError(
                    "Completed levels must contain only "
                    "levels 1 through 4."
                )

            if level not in validated_levels:
                validated_levels.append(level)

        self.completed_levels = sorted(
            validated_levels
        )

    # ========================================================
    # COLLECTED ITEMS
    # ========================================================

    def _validate_collected_items(self) -> None:
        if not isinstance(
            self.collected_items,
            list,
        ):
            raise TypeError(
                "collected_items must be a list."
            )

        self.collected_items = self._validate_string_list(
            self.collected_items,
            "collected_items",
        )

    # ========================================================
    # DISCOVERED WORDS
    # ========================================================

    def _validate_discovered_words(self) -> None:
        if not isinstance(
            self.discovered_words,
            list,
        ):
            raise TypeError(
                "discovered_words must be a list."
            )

        self.discovered_words = self._validate_string_list(
            self.discovered_words,
            "discovered_words",
        )

        if len(self.discovered_words) > 4:
            raise ValueError(
                "A quest cannot contain more than "
                "four discovered words."
            )

    # ========================================================
    # BOOLEAN FIELDS
    # ========================================================

    def _validate_boolean_fields(self) -> None:
        boolean_fields = (
            "collected_ticket",
            "train_completed",
            "final_reveal_unlocked",
        )

        for field_name in boolean_fields:
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                bool,
            ):
                raise TypeError(
                    f"{field_name} must be a boolean."
                )

    # ========================================================
    # VERSION
    # ========================================================

    def _validate_version(self) -> None:
        if (
            isinstance(
                self.version,
                bool,
            )
            or not isinstance(
                self.version,
                int,
            )
        ):
            raise TypeError(
                "version must be an integer."
            )

        if self.version < 1:
            raise ValueError(
                "version must be greater than or equal to 1."
            )

    # ========================================================
    # METADATA
    # ========================================================

    def _validate_metadata(self) -> None:
        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )

        self.metadata = dict(
            self.metadata
        )

    # ========================================================
    # INTERNAL CONSISTENCY
    # ========================================================

    def _validate_progress_consistency(self) -> None:
        """
        Ensure that the stored quest progress is internally
        consistent.

        Examples:
        - Level 3 cannot be current while Level 1 and 2 are
          missing from completed_levels.
        - A final reveal cannot be unlocked before Level 4.
        """

        completed_level_set = set(
            self.completed_levels
        )

        # ----------------------------------------------------
        # Current level consistency
        # ----------------------------------------------------

        if self.current_level == 0:
            if completed_level_set:
                raise ValueError(
                    "completed_levels must be empty when "
                    "current_level is 0."
                )

        else:
            expected_completed_levels = set(
                range(
                    1,
                    self.current_level + 1,
                )
            )

            if not expected_completed_levels.issubset(
                completed_level_set
            ):
                raise ValueError(
                    "completed_levels is inconsistent "
                    "with current_level."
                )

        # ----------------------------------------------------
        # Final reveal consistency
        # ----------------------------------------------------

        if self.final_reveal_unlocked:
            if self.current_level < 4:
                raise ValueError(
                    "Final reveal cannot be unlocked "
                    "before Level 4 is complete."
                )

            if not NORMAL_QUEST_LEVELS.issubset(
                completed_level_set
            ):
                raise ValueError(
                    "Final reveal requires all four "
                    "quest levels to be completed."
                )

            if len(self.discovered_words) != 4:
                raise ValueError(
                    "Final reveal requires all four "
                    "hidden words to be discovered."
                )

    # ========================================================
    # STRING LIST VALIDATION
    # ========================================================

    @staticmethod
    def _validate_string_list(
        values: list[str],
        field_name: str,
    ) -> list[str]:
        """
        Validate and normalize a list of non-empty strings.

        Duplicate values are removed while preserving the first
        occurrence.
        """

        validated: list[str] = []

        for value in values:
            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"Every value in {field_name} "
                    "must be a string."
                )

            value = value.strip()

            if not value:
                raise ValueError(
                    f"{field_name} cannot contain "
                    "empty values."
                )

            if len(value) > 512:
                raise ValueError(
                    f"Values in {field_name} cannot "
                    "exceed 512 characters."
                )

            if value not in validated:
                validated.append(value)

        return validated

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the model into a Firestore/API-safe dictionary.
        """

        return asdict(self)

    # ========================================================
    # DESERIALIZATION
    # ========================================================

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Quest":
        """
        Build a Quest model from persisted dictionary data.
        """

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(
                "data must be a dictionary."
            )

        required_fields = (
            "session_id",
            "state",
        )

        missing_fields = [
            field_name
            for field_name in required_fields
            if field_name not in data
        ]

        if missing_fields:
            raise ValueError(
                "Missing required quest fields: "
                + ", ".join(missing_fields)
            )

        return cls(
            session_id=data["session_id"],
            state=data["state"],
            current_level=data.get(
                "current_level",
                0,
            ),
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
            version=data.get(
                "version",
                1,
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
    )
