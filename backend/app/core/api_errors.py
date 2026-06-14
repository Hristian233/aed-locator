"""Stable API error and warning codes for client-side translation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ApiValidationError(Exception):
    def __init__(
        self,
        code: str,
        *,
        message: str | None = None,
        **params: Any,
    ) -> None:
        self.code = code
        self.message = message or code
        self.params = params
        super().__init__(self.message)

    def to_detail(self) -> dict[str, Any]:
        detail: dict[str, Any] = {"code": self.code, "message": self.message}
        detail.update(self.params)
        return detail


class SubmissionWarning(BaseModel):
    code: str
    params: dict[str, int | float | str] = Field(default_factory=dict)


def pending_review_warning() -> SubmissionWarning:
    return SubmissionWarning(code="pending_review")


def duplicate_nearby_warning(meters: float) -> SubmissionWarning:
    return SubmissionWarning(code="duplicate_nearby", params={"meters": int(meters)})


def api_error_detail(code: str, message: str, **params: Any) -> dict[str, Any]:
    detail: dict[str, Any] = {"code": code, "message": message}
    detail.update(params)
    return detail


def exception_to_detail(exc: Exception) -> dict[str, Any] | str:
    if isinstance(exc, ApiValidationError):
        return exc.to_detail()
    return {"code": "unknown", "message": str(exc)}
