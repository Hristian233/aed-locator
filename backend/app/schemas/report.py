from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.api_errors import SubmissionWarning


class ReportCreate(BaseModel):
    description: str = Field(min_length=1, max_length=2000)
    aed_id: int | None = Field(default=None, ge=1)
    reporter_latitude: float | None = Field(default=None, ge=-90, le=90)
    reporter_longitude: float | None = Field(default=None, ge=-180, le=180)
    contact_email: EmailStr | None = None


class AEDSummary(BaseModel):
    id: int
    location_name: str | None = None
    address: str | None = None
    latitude: float
    longitude: float
    accessibility_type: str
    opening_hours: str | None = None
    is_restricted_access: bool = False
    image_urls: list[str] = []

    model_config = {"from_attributes": True}

    @field_validator("image_urls", mode="before")
    @classmethod
    def default_image_urls(cls, v: list[str] | None) -> list[str]:
        return v or []


class ReportResponse(BaseModel):
    id: int
    aed_id: int | None = None
    description: str
    reporter_latitude: float | None = None
    reporter_longitude: float | None = None
    image_url: str | None = None
    image_urls: list[str] = []
    contact_email: str | None = None
    status: str
    spam_score: float | None = None
    created_at: datetime
    updated_at: datetime
    aed: AEDSummary | None = None

    model_config = {"from_attributes": True}

    @field_validator("image_urls", mode="before")
    @classmethod
    def default_image_urls(cls, v: list[str] | None) -> list[str]:
        return v or []


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReportSubmissionResult(BaseModel):
    report: ReportResponse
    warnings: list[SubmissionWarning] = []

    @field_validator("warnings", mode="before")
    @classmethod
    def default_warnings(cls, v: list | None) -> list:
        return v or []
