"""Validate opening hours JSON and evaluate whether an AED is reachable now."""

import json
from datetime import datetime
from typing import Any

from app.models.aed import AED, AccessibilityType

VALID_DAYS = frozenset(
    {"mon", "tue", "wed", "thu", "fri", "sat", "sun", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
)

DAY_KEYS = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")
LONG_DAY_NAMES = (
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
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


def _parse_time(value: str) -> int:
    hours, minutes = value.split(":", 1)
    return int(hours) * 60 + int(minutes or 0)


def _hours_for_today(opening_hours: str | None, now: datetime) -> dict[str, str] | None:
    if not opening_hours:
        return None
    try:
        data = json.loads(opening_hours)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    # Match JS Date.getDay(): 0=Sun … 6=Sat
    day_index = (now.weekday() + 1) % 7
    day_key = DAY_KEYS[day_index]
    long_name = LONG_DAY_NAMES[day_index]
    raw = data.get(day_key) or data.get(long_name) or data.get(day_key.upper())
    if raw is None:
        return None
    if isinstance(raw, dict) and "open" in raw and "close" in raw:
        return {"open": str(raw["open"]), "close": str(raw["close"])}
    return None


def _is_within_hours(period: dict[str, str], now: datetime) -> bool:
    minutes = now.hour * 60 + now.minute
    open_m = _parse_time(period["open"])
    close_m = _parse_time(period["close"])
    if close_m > open_m:
        return open_m <= minutes < close_m
    return minutes >= open_m or minutes < close_m


def is_aed_available_now(aed: AED, now: datetime | None = None) -> bool:
    """Whether the AED should appear on the public map right now."""
    now = now or datetime.now()
    acc = aed.accessibility_type
    if acc in (AccessibilityType.always_open, AccessibilityType.restricted_access):
        return True
    period = _hours_for_today(aed.opening_hours, now)
    if not period:
        return False
    return _is_within_hours(period, now)
