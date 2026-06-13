from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


AccessibilityTypeLiteral = Literal["24_7", "business_hours", "restricted_access"]
ReportTypeLiteral = Literal["new_location", "aed_issue"]


class AEDBase(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str | None = Field(default=None, max_length=512)
    location_name: str | None = Field(default=None, max_length=255)
    is_restricted_access: bool = False
    description: str | None = Field(default=None, max_length=2000)
    accessibility_type: AccessibilityTypeLiteral = "24_7"
    opening_hours: str | None = Field(default=None, max_length=4000)


class AEDCreate(AEDBase):
    report_type: ReportTypeLiteral = "new_location"
    contact_email: EmailStr | None = None
    related_aed_id: int | None = Field(default=None, ge=1)


class AEDUpdate(BaseModel):
    address: str | None = Field(default=None, max_length=512)
    location_name: str | None = Field(default=None, max_length=255)
    is_restricted_access: bool | None = None
    description: str | None = Field(default=None, max_length=2000)
    verification_status: Literal["pending", "verified", "rejected"] | None = None
    accessibility_type: AccessibilityTypeLiteral | None = None
    opening_hours: str | None = Field(default=None, max_length=4000)


class AEDResponse(AEDBase):
    id: int
    image_url: str | None
    image_urls: list[str] = []
    verification_status: str
    report_type: str
    contact_email: str | None = None
    related_aed_id: int | None = None
    distance_meters: float | None = None
    ai_confidence: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("image_urls", mode="before")
    @classmethod
    def default_image_urls(cls, v: list[str] | None) -> list[str]:
        return v or []


class AEDListResponse(BaseModel):
    items: list[AEDResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class NearestAEDQuery(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    limit: int = Field(default=20, ge=1, le=50)
    max_distance_meters: float | None = Field(default=None, ge=100, le=50000)
    reachable_only: bool = True


class SubmissionResult(BaseModel):
    aed: AEDResponse
    warnings: list[str] = []
    duplicate_of_id: int | None = None

    @field_validator("warnings", mode="before")
    @classmethod
    def default_warnings(cls, v: list[str] | None) -> list[str]:
        return v or []


class TempImageUploadMeta(BaseModel):
    temp_object_key: str = Field(min_length=1, max_length=512)
    content_type: str | None = Field(default=None, max_length=128)
    content_length: int | None = Field(default=None, ge=1024)
