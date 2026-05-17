"""Validate opening hours JSON stored on AED records."""

import json
from typing import Any

VALID_DAYS = frozenset(
    {"mon", "tue", "wed", "thu", "fri", "sat", "sun", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
)


def validate_opening_hours_json(raw: str | None) -> str | None:
    if raw is None or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("opening_hours must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("opening_hours must be a JSON object")
    for day, hours in data.items():
        if day == "timezone":
            continue
        if day.lower() not in VALID_DAYS:
            raise ValueError(f"Invalid day key in opening_hours: {day}")
        if hours is None:
            continue
        if isinstance(hours, dict):
            if "open" not in hours or "close" not in hours:
                raise ValueError(f"Day {day} must include open and close times")
        elif not isinstance(hours, list):
            raise ValueError(f"Day {day} must be an object or list of periods")
    return raw


def normalize_opening_hours(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    return json.loads(raw)
