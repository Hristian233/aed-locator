from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AEDBase(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str | None = Field(default=None, max_length=512)
    description: str | None = Field(default=None, max_length=2000)


class AEDCreate(AEDBase):
    pass


class AEDUpdate(BaseModel):
    address: str | None = Field(default=None, max_length=512)
    description: str | None = Field(default=None, max_length=2000)
    verification_status: Literal["pending", "verified", "rejected"] | None = None


class AEDResponse(AEDBase):
    id: int
    image_url: str | None
    verification_status: str
    distance_meters: float | None = None
    ai_confidence: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AEDListResponse(BaseModel):
    items: list[AEDResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class NearestAEDQuery(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    limit: int = Field(default=5, ge=1, le=20)
    max_distance_meters: float | None = Field(default=5000, ge=100, le=50000)


class SubmissionResult(BaseModel):
    aed: AEDResponse
    warnings: list[str] = []
    duplicate_of_id: int | None = None

    @field_validator("warnings", mode="before")
    @classmethod
    def default_warnings(cls, v: list[str] | None) -> list[str]:
        return v or []
