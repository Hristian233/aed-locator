from dataclasses import dataclass

from geoalchemy2.elements import WKTElement

from app.core.config import Settings, get_settings
from app.core.upload_limits import ImageTooManyError
from app.core.logging import get_logger
from app.models.aed import AED, AccessibilityType, ReportType, VerificationStatus
from app.models.user import User
from app.repositories.aed_repository import AEDRepository
from app.schemas.aed import (
    AEDCreate,
    AEDListResponse,
    AEDResponse,
    AEDUpdate,
    SubmissionResult,
    TempImageUploadMeta,
)
from app.services.aed_image_keys import (
    parse_image_object_keys,
    resolve_image_display_urls,
    serialize_image_object_keys,
)
from app.services.ai_service import AIService
from app.services.image_processor import ImageProcessorError, ImageProcessorService
from app.services.opening_hours import (
    is_aed_available_now,
    is_aed_reachable,
    validate_opening_hours_json,
)
from app.services.storage_service import StorageService

logger = get_logger(__name__)


@dataclass
class LocalImageUpload:
    content: bytes
    content_type: str


def _validate_image_count(image_count: int, report_type: ReportType, settings: Settings) -> None:
    if image_count > settings.max_images_per_submission:
        raise ImageTooManyError(settings.max_images_per_submission)
    if report_type == ReportType.new_location and image_count < settings.min_images_new_location:
        raise ValueError("At least one photo is required for new AED submissions.")


def _to_response(
    aed: AED,
    distance_meters: float | None = None,
    *,
    storage: StorageService | None = None,
) -> AEDResponse:
    storage = storage or StorageService()
    keys = parse_image_object_keys(aed.image_object_keys, legacy_image_url=aed.image_url)
    image_urls = resolve_image_display_urls(keys, storage=storage)
    return AEDResponse(
        id=aed.id,
        latitude=aed.latitude,
        longitude=aed.longitude,
        address=aed.address,
        location_name=aed.location_name,
        is_restricted_access=aed.is_restricted_access,
        description=aed.description,
        image_url=image_urls[0] if image_urls else None,
        image_urls=image_urls,
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
        image_processor: ImageProcessorService | None = None,
    ) -> None:
        self.aed_repo = aed_repo
        self.storage = storage or StorageService()
        self.ai = ai or AIService()
        self.image_processor = image_processor or ImageProcessorService()

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
        items = [_to_response(aed, dist, storage=self.storage) for aed, dist in rows]
        return AEDListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=page * page_size < total,
        )

    async def get_aed(self, aed_id: int) -> AEDResponse | None:
        aed = await self.aed_repo.get_by_id(aed_id)
        return _to_response(aed, storage=self.storage) if aed else None

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
            return [_to_response(aed, dist, storage=self.storage) for aed, dist in rows[:limit]]

        available: list[AEDResponse] = []
        for aed, dist in rows:
            if is_aed_reachable(aed, distance_meters=dist):
                available.append(_to_response(aed, dist, storage=self.storage))
            if len(available) >= limit:
                break
        return available

    async def _process_local_images(self, uploads: list[LocalImageUpload]) -> list[str]:
        keys: list[str] = []
        for upload in uploads:
            self.storage.validate_upload_metadata(upload.content_type, len(upload.content))
            keys.append(await self.storage.save_image(upload.content, upload.content_type))
        return keys

    async def _process_temp_images(self, uploads: list[TempImageUploadMeta]) -> list[str]:
        keys: list[str] = []
        for upload in uploads:
            if upload.content_type and upload.content_length:
                self.storage.validate_upload_metadata(
                    upload.content_type,
                    upload.content_length,
                )
            final_object_key = self.storage.build_final_object_key()
            try:
                processed = await self.image_processor.process_temp_image(
                    temp_object_key=upload.temp_object_key,
                    content_type=upload.content_type,
                    content_length=upload.content_length,
                    final_object_key=final_object_key,
                )
            except ImageProcessorError as exc:
                raise ValueError(exc.message) from exc
            keys.append(processed.final_object_key)
        return keys

    async def _analyze_images(self, object_keys: list[str], warnings: list[str]) -> float | None:
        best_confidence: float | None = None
        any_likely_aed = False
        analysis_failed = False

        for object_key in object_keys:
            try:
                content = await self.storage.load_image_bytes(object_key)
            except Exception as exc:
                logger.warning(
                    "processed_image_load_failed",
                    object_key=object_key,
                    error=str(exc),
                )
                analysis_failed = True
                continue

            analysis = self.ai.analyze_image(content)
            if best_confidence is None or analysis.confidence > best_confidence:
                best_confidence = analysis.confidence
            if analysis.likely_aed:
                any_likely_aed = True

        if analysis_failed:
            warnings.append("Some images were saved but automated checks could not be run.")
        if object_keys and not any_likely_aed:
            warnings.append(
                "Uploaded images may not show an AED. An admin will review this submission."
            )
        return best_confidence

    async def submit_aed(
        self,
        data: AEDCreate,
        *,
        submitter: User | None,
        local_images: list[LocalImageUpload] | None = None,
        temp_images: list[TempImageUploadMeta] | None = None,
    ) -> SubmissionResult:
        settings = get_settings()
        warnings: list[str] = []
        duplicate_of_id: int | None = None
        local_images = local_images or []
        temp_images = temp_images or []

        opening_hours = validate_opening_hours_json(data.opening_hours)
        if data.accessibility_type == "business_hours" and not opening_hours:
            raise ValueError("Opening hours are required for business-hours accessibility.")

        report_type = ReportType(data.report_type)
        image_count = len(local_images) + len(temp_images)

        if report_type == ReportType.new_location:
            _validate_image_count(image_count, report_type, settings)
        elif image_count > 0:
            _validate_image_count(image_count, report_type, settings)

        if report_type != ReportType.new_location and not data.description:
            raise ValueError("Please provide details describing the issue.")

        if data.is_restricted_access and not data.description:
            raise ValueError("Please provide access details when restricted access is selected.")

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

        if settings.uses_gcs_storage and local_images:
            raise ValueError(
                "Upload photos using signed URLs, then submit image_temp_object_key for each image."
            )
        if not settings.uses_gcs_storage and temp_images:
            raise ValueError("Temporary image keys are only used with GCS storage.")

        image_object_keys: list[str] = []
        if temp_images:
            image_object_keys = await self._process_temp_images(temp_images)
        elif local_images:
            image_object_keys = await self._process_local_images(local_images)

        ai_confidence: float | None = None
        if image_object_keys:
            ai_confidence = await self._analyze_images(image_object_keys, warnings)

        serialized_keys = serialize_image_object_keys(image_object_keys)
        point = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
        aed = AED(
            location=point,
            latitude=data.latitude,
            longitude=data.longitude,
            address=data.address,
            location_name=data.location_name,
            is_restricted_access=data.is_restricted_access,
            description=data.description,
            image_url=image_object_keys[0] if image_object_keys else None,
            image_object_keys=serialized_keys,
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
        logger.info(
            "aed_submitted",
            aed_id=created.id,
            report_type=report_type.value,
            image_count=len(image_object_keys),
            warnings=warnings,
        )
        return SubmissionResult(
            aed=_to_response(created, storage=self.storage),
            warnings=warnings,
            duplicate_of_id=duplicate_of_id,
        )

    async def verify_aed(self, aed_id: int, status: VerificationStatus) -> AEDResponse | None:
        aed = await self.aed_repo.get_by_id(aed_id)
        if not aed:
            return None
        aed.verification_status = status
        updated = await self.aed_repo.update(aed)
        return _to_response(updated, storage=self.storage)

    async def update_aed(self, aed_id: int, data: AEDUpdate) -> AEDResponse | None:
        aed = await self.aed_repo.get_by_id(aed_id)
        if not aed:
            return None
        if data.address is not None:
            aed.address = data.address
        if data.location_name is not None:
            aed.location_name = data.location_name
        if data.is_restricted_access is not None:
            aed.is_restricted_access = data.is_restricted_access
        if data.description is not None:
            aed.description = data.description
        if data.verification_status is not None:
            aed.verification_status = VerificationStatus(data.verification_status)
        if data.accessibility_type is not None:
            aed.accessibility_type = AccessibilityType(data.accessibility_type)
        if data.opening_hours is not None:
            aed.opening_hours = validate_opening_hours_json(data.opening_hours)
        updated = await self.aed_repo.update(aed)
        return _to_response(updated, storage=self.storage)
