"""
Birthday Quest - Timestamp Utilities

Centralized UTC timestamp helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone


# ------------------------------------------------------------
# CURRENT UTC TIME
# ------------------------------------------------------------

def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC datetime.
    """

    return datetime.now(timezone.utc)


# ------------------------------------------------------------
# ISO TIMESTAMP
# ------------------------------------------------------------

def utc_now_iso() -> str:
    """
    Return the current UTC time as an ISO 8601 string.

    Example:
        2026-10-03T12:34:56.123456+00:00
    """

    return utc_now().isoformat()


# ------------------------------------------------------------
# DATETIME → ISO
# ------------------------------------------------------------

def datetime_to_iso(value: datetime) -> str:
    """
    Convert a datetime to a timezone-aware UTC ISO 8601 string.

    Naive datetimes are treated as UTC.
    """

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    value = value.astimezone(timezone.utc)

    return value.isoformat()


# ------------------------------------------------------------
# ISO → DATETIME
# ------------------------------------------------------------

def iso_to_datetime(value: str) -> datetime:
    """
    Convert an ISO 8601 timestamp string into a timezone-aware
    UTC datetime.
    """

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "Timestamp must be a non-empty ISO 8601 string."
        )

    normalized = value.strip()

    # Support timestamps ending in 'Z'.
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "Invalid ISO 8601 timestamp."
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(timezone.utc)
