from geoalchemy2.elements import WKTElement

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.aed import AED, AccessibilityType, ReportType, VerificationStatus
from app.models.user import User
from app.repositories.aed_repository import AEDRepository
from app.schemas.aed import AEDCreate, AEDListResponse, AEDResponse, AEDUpdate, SubmissionResult
from app.services.ai_service import AIService
from app.services.opening_hours import (
    is_aed_available_now,
    is_aed_reachable,
    validate_opening_hours_json,
)
from app.services.storage_service import StorageService

logger = get_logger(__name__)


def _to_response(aed: AED, distance_meters: float | None = None) -> AEDResponse:
    return AEDResponse(
        id=aed.id,
        latitude=aed.latitude,
        longitude=aed.longitude,
        address=aed.address,
        description=aed.description,
        image_url=aed.image_url,
        verification_status=aed.verification_status.value,
        accessibility_type=aed.accessibility_type.value,
        opening_hours=aed.opening_hours,
        report_type=aed.report_type.value,
        contact_email=aed.contact_email,
        related_aed_id=aed.related_aed_id,
        distance_meters=distance_meters,
        ai_confidence=aed.ai_confidence,
        created_at=aed.created_at,
        updated_at=aed.updated_at,
    )


class AEDService:
    def __init__(
        self,
        aed_repo: AEDRepository,
        storage: StorageService | None = None,
        ai: AIService | None = None,
    ) -> None:
        self.aed_repo = aed_repo
        self.storage = storage or StorageService()
        self.ai = ai or AIService()

    async def list_aeds(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        verified_only: bool = True,
    ) -> AEDListResponse:
        status_enum = VerificationStatus(status) if status else None
        rows, total = await self.aed_repo.list_aeds(
            page=page,
            page_size=page_size,
            status=status_enum,
            verified_only=verified_only and status_enum is None,
        )
        if verified_only and status_enum is None:
            rows = [(aed, dist) for aed, dist in rows if is_aed_available_now(aed)]
            total = len(rows)
        items = [_to_response(aed, dist) for aed, dist in rows]
        return AEDListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=page * page_size < total,
        )

    async def get_aed(self, aed_id: int) -> AEDResponse | None:
        aed = await self.aed_repo.get_by_id(aed_id)
        return _to_response(aed) if aed else None

    async def find_nearest(
        self,
        latitude: float,
        longitude: float,
        *,
        limit: int,
        max_distance_meters: float | None,
        reachable_only: bool = True,
    ) -> list[AEDResponse]:
        fetch_limit = limit if not reachable_only else min(limit * 5, 100)
        rows = await self.aed_repo.find_nearest(
            latitude,
            longitude,
            limit=fetch_limit,
            max_distance_meters=max_distance_meters,
            verified_only=True,
        )
        if not reachable_only:
            return [_to_response(aed, dist) for aed, dist in rows[:limit]]

        available: list[AEDResponse] = []
        for aed, dist in rows:
            if is_aed_reachable(aed, distance_meters=dist):
                available.append(_to_response(aed, dist))
            if len(available) >= limit:
                break
        return available

    async def submit_aed(
        self,
        data: AEDCreate,
        *,
        submitter: User | None,
        image_content: bytes | None = None,
        image_content_type: str | None = None,
    ) -> SubmissionResult:
        settings = get_settings()
        warnings: list[str] = []
        duplicate_of_id: int | None = None

        opening_hours = validate_opening_hours_json(data.opening_hours)
        if data.accessibility_type == "business_hours" and not opening_hours:
            raise ValueError("Opening hours are required for business-hours accessibility.")

        report_type = ReportType(data.report_type)
        if report_type == ReportType.new_location and not image_content:
            raise ValueError("At least one photo is required for new AED submissions.")
        if report_type != ReportType.new_location and not data.description:
            raise ValueError("Please provide details describing the issue.")

        if report_type != ReportType.new_location and data.related_aed_id:
            related = await self.aed_repo.get_by_id(data.related_aed_id)
            if not related:
                raise ValueError("Referenced AED was not found.")

        duplicate = await self.aed_repo.find_duplicate_nearby(
            data.latitude, data.longitude, settings.duplicate_radius_meters
        )
        if duplicate and report_type == ReportType.new_location:
            duplicate_of_id = duplicate.id
            warnings.append(
                f"Another AED is already registered within {settings.duplicate_radius_meters}m."
            )

        spam = self.ai.check_spam(data.description, data.address)
        if spam.is_spam:
            raise ValueError("Submission flagged as potential spam.")

        ai_confidence: float | None = None
        image_url: str | None = None

        if image_content and image_content_type:
            analysis = self.ai.analyze_image(image_content)
            ai_confidence = analysis.confidence
            if not analysis.likely_aed:
                warnings.append(
                    "Uploaded image may not show an AED. An admin will review this submission."
                )
            image_url = await self.storage.save_image(image_content, image_content_type)

        point = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
        aed = AED(
            location=point,
            latitude=data.latitude,
            longitude=data.longitude,
            address=data.address,
            description=data.description,
            image_url=image_url,
            verification_status=VerificationStatus.pending,
            accessibility_type=AccessibilityType(data.accessibility_type),
            opening_hours=opening_hours,
            report_type=report_type,
            contact_email=str(data.contact_email) if data.contact_email else None,
            related_aed_id=data.related_aed_id,
            submitter_id=submitter.id if submitter else None,
            ai_confidence=ai_confidence,
            spam_score=spam.score,
        )
        created = await self.aed_repo.create(aed)
        logger.info("aed_submitted", aed_id=created.id, report_type=report_type.value, warnings=warnings)
        return SubmissionResult(
            aed=_to_response(created),
            warnings=warnings,
            duplicate_of_id=duplicate_of_id,
        )

    async def verify_aed(self, aed_id: int, status: VerificationStatus) -> AEDResponse | None:
        aed = await self.aed_repo.get_by_id(aed_id)
        if not aed:
            return None
        aed.verification_status = status
        updated = await self.aed_repo.update(aed)
        return _to_response(updated)

    async def update_aed(self, aed_id: int, data: AEDUpdate) -> AEDResponse | None:
        aed = await self.aed_repo.get_by_id(aed_id)
        if not aed:
            return None
        if data.address is not None:
            aed.address = data.address
        if data.description is not None:
            aed.description = data.description
        if data.verification_status is not None:
            aed.verification_status = VerificationStatus(data.verification_status)
        if data.accessibility_type is not None:
            aed.accessibility_type = AccessibilityType(data.accessibility_type)
        if data.opening_hours is not None:
            aed.opening_hours = validate_opening_hours_json(data.opening_hours)
        updated = await self.aed_repo.update(aed)
        return _to_response(updated)
