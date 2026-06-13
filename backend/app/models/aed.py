import enum
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class AccessibilityType(str, enum.Enum):
    always_open = "24_7"
    business_hours = "business_hours"
    restricted_access = "restricted_access"


class ReportType(str, enum.Enum):
    new_location = "new_location"
    incorrect_info = "incorrect_info"
    unavailable = "unavailable"
    duplicate = "duplicate"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class AED(Base):
    __tablename__ = "aeds"

    id: Mapped[int] = mapped_column(primary_key=True)
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    image_object_keys: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.pending, index=True
    )
    accessibility_type: Mapped[AccessibilityType] = mapped_column(
        Enum(AccessibilityType, values_callable=_enum_values),
        default=AccessibilityType.always_open,
    )
    opening_hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, values_callable=_enum_values),
        default=ReportType.new_location,
    )
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    related_aed_id: Mapped[int | None] = mapped_column(
        ForeignKey("aeds.id", ondelete="SET NULL"), nullable=True
    )
    submitter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(nullable=True)
    spam_score: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    submitter = relationship("User", back_populates="aed_submissions")
    related_aed = relationship("AED", remote_side=[id], foreign_keys=[related_aed_id])
