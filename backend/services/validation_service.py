from __future__ import annotations

from typing import Any, Mapping, Optional


class ValidationError(ValueError):
    """Raised when incoming data fails application validation."""


MIN_LEVEL = 1
MAX_LEVEL = 4

ALLOWED_RECORDING_TYPES = {
    "video_1",
    "video_2",
    "reaction",
    "final",
}

ALLOWED_COLLECTIBLE_ITEMS = {
    "owl",
    "wand",
    "broom",
}

MAX_TEXT_LENGTH = 500
MAX_WORD_LENGTH = 100
MAX_CODE_LENGTH = 100


def _require_mapping(data: Any, field_name: str = "data") -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ValidationError(f"{field_name} must be an object.")

    return data


def _require_non_empty_string(
    value: Any,
    field_name: str,
    *,
    max_length: int = MAX_TEXT_LENGTH,
) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    normalized = value.strip()

    if not normalized:
        raise ValidationError(f"{field_name} is required.")

    if len(normalized) > max_length:
        raise ValidationError(
            f"{field_name} must not exceed {max_length} characters."
        )

    return normalized


def validate_session_id(session_id: Any) -> str:
    return _require_non_empty_string(
        session_id,
        "session_id",
        max_length=128,
    )


def validate_level(level: Any) -> int:
    if isinstance(level, bool) or not isinstance(level, int):
        raise ValidationError("level must be an integer.")

    if level < MIN_LEVEL or level > MAX_LEVEL:
        raise ValidationError(
            f"level must be between {MIN_LEVEL} and {MAX_LEVEL}."
        )

    return level


def validate_recording_type(recording_type: Any) -> str:
    normalized = _require_non_empty_string(
        recording_type,
        "recording_type",
        max_length=32,
    ).casefold()

    if normalized not in ALLOWED_RECORDING_TYPES:
        raise ValidationError("Unsupported recording type.")

    return normalized


def validate_collectible_item(item: Any) -> str:
    normalized = _require_non_empty_string(
        item,
        "item",
        max_length=32,
    ).casefold()

    if normalized not in ALLOWED_COLLECTIBLE_ITEMS:
        raise ValidationError("Unsupported collectible item.")

    return normalized


def validate_hidden_word(word: Any) -> str:
    return _require_non_empty_string(
        word,
        "word",
        max_length=MAX_WORD_LENGTH,
    )


def validate_code(code: Any) -> str:
    return _require_non_empty_string(
        code,
        "code",
        max_length=MAX_CODE_LENGTH,
    )


def validate_answer(answer: Any) -> str:
    return _require_non_empty_string(
        answer,
        "answer",
        max_length=MAX_CODE_LENGTH,
    )


def validate_expected_version(version: Any) -> int:
    if isinstance(version, bool) or not isinstance(version, int):
        raise ValidationError("expected_version must be an integer.")

    if version < 0:
        raise ValidationError("expected_version cannot be negative.")

    return version


def validate_expected_state(state: Any) -> str:
    return _require_non_empty_string(
        state,
        "expected_state",
        max_length=64,
    )


def validate_quest_transition(
    current_state: Any,
    next_state: Any,
) -> tuple[str, str]:
    current = _require_non_empty_string(
        current_state,
        "current_state",
        max_length=64,
    )

    next_value = _require_non_empty_string(
        next_state,
        "next_state",
        max_length=64,
    )

    if current == next_value:
        raise ValidationError("Current state and next state must be different.")

    return current, next_value


def validate_level_payload(data: Any) -> dict[str, Any]:
    payload = _require_mapping(data)

    level = validate_level(payload.get("level"))
    answer = validate_answer(payload.get("answer"))

    return {
        "level": level,
        "answer": answer,
    }


def validate_collectible_payload(data: Any) -> dict[str, Any]:
    payload = _require_mapping(data)

    item = validate_collectible_item(payload.get("item"))

    return {
        "item": item,
    }


def validate_word_payload(data: Any) -> dict[str, Any]:
    payload = _require_mapping(data)

    word = validate_hidden_word(payload.get("word"))

    return {
        "word": word,
    }


def validate_ticket_payload(data: Any) -> dict[str, Any]:
    payload = _require_mapping(data)

    ticket_code = validate_code(payload.get("ticket_code"))

    return {
        "ticket_code": ticket_code,
    }


def validate_sorting_payload(data: Any) -> dict[str, Any]:
    payload = _require_mapping(data)

    house = _require_non_empty_string(
        payload.get("house"),
        "house",
        max_length=64,
    )

    return {
        "house": house,
    }


def validate_recording_payload(data: Any) -> dict[str, Any]:
    payload = _require_mapping(data)

    recording_type = validate_recording_type(
        payload.get("recording_type")
    )

    return {
        "recording_type": recording_type,
    }


def validate_optional_string(
    value: Any,
    field_name: str,
    *,
    max_length: int = MAX_TEXT_LENGTH,
) -> Optional[str]:
    if value is None:
        return None

    return _require_non_empty_string(
        value,
        field_name,
        max_length=max_length,
    )


def validate_boolean(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field_name} must be a boolean.")

    return value
