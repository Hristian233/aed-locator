from geoalchemy2.elements import WKTElement

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.upload_limits import ImageTooManyError
from app.models.aed import AED
from app.models.report import Report, ReportStatus
from app.models.user import User
from app.repositories.aed_repository import AEDRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.aed import TempImageUploadMeta
from app.schemas.report import (
    AEDSummary,
    ReportCreate,
    ReportListResponse,
    ReportResponse,
    ReportSubmissionResult,
)
from app.services.aed_image_keys import (
    parse_image_object_keys,
    resolve_image_display_urls,
    serialize_image_object_keys,
)
from app.services.aed_service import LocalImageUpload
from app.services.ai_service import AIService
from app.services.image_processor import ImageProcessorError, ImageProcessorService
from app.services.storage_service import StorageService

logger = get_logger(__name__)


def _validate_image_count(image_count: int, settings: Settings) -> None:
    if image_count > settings.max_images_per_submission:
        raise ImageTooManyError(settings.max_images_per_submission)


def _aed_summary(aed: AED, *, storage: StorageService) -> AEDSummary:
    keys = parse_image_object_keys(aed.image_object_keys, legacy_image_url=aed.image_url)
    image_urls = resolve_image_display_urls(keys, storage=storage)
    return AEDSummary(
        id=aed.id,
        location_name=aed.location_name,
        address=aed.address,
        latitude=aed.latitude,
        longitude=aed.longitude,
        accessibility_type=aed.accessibility_type.value,
        opening_hours=aed.opening_hours,
        is_restricted_access=aed.is_restricted_access,
        image_urls=image_urls,
    )


def _to_response(report: Report, *, storage: StorageService | None = None) -> ReportResponse:
    storage = storage or StorageService()
    keys = parse_image_object_keys(report.image_object_keys, legacy_image_url=report.image_url)
    image_urls = resolve_image_display_urls(keys, storage=storage)
    aed_summary = _aed_summary(report.aed, storage=storage) if report.aed else None
    return ReportResponse(
        id=report.id,
        aed_id=report.aed_id,
        description=report.description,
        reporter_latitude=report.reporter_latitude,
        reporter_longitude=report.reporter_longitude,
        image_url=image_urls[0] if image_urls else None,
        image_urls=image_urls,
        contact_email=report.contact_email,
        status=report.status.value,
        spam_score=report.spam_score,
        created_at=report.created_at,
        updated_at=report.updated_at,
        aed=aed_summary,
    )


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository,
        aed_repo: AEDRepository,
        storage: StorageService | None = None,
        ai: AIService | None = None,
        image_processor: ImageProcessorService | None = None,
    ) -> None:
        self.report_repo = report_repo
        self.aed_repo = aed_repo
        self.storage = storage or StorageService()
        self.ai = ai or AIService()
        self.image_processor = image_processor or ImageProcessorService()

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

    async def _analyze_images(self, object_keys: list[str], warnings: list[str]) -> None:
        any_likely_aed = False
        analysis_failed = False

        for object_key in object_keys:
            try:
                content = await self.storage.load_image_bytes(object_key)
            except Exception as exc:
                logger.warning(
                    "report_image_load_failed",
                    object_key=object_key,
                    error=str(exc),
                )
                analysis_failed = True
                continue

            analysis = self.ai.analyze_image(content)
            if analysis.likely_aed:
                any_likely_aed = True

        if analysis_failed:
            warnings.append("Some images were saved but automated checks could not be run.")
        if object_keys and not any_likely_aed:
            warnings.append(
                "Uploaded images may not show an AED. An admin will review this report."
            )

    async def submit_report(
        self,
        data: ReportCreate,
        *,
        submitter: User | None,
        local_images: list[LocalImageUpload] | None = None,
        temp_images: list[TempImageUploadMeta] | None = None,
    ) -> ReportSubmissionResult:
        settings = get_settings()
        warnings: list[str] = []
        local_images = local_images or []
        temp_images = temp_images or []

        if not data.description.strip():
            raise ValueError("Please provide a description of the problem.")

        if data.aed_id is not None:
            related = await self.aed_repo.get_by_id(data.aed_id)
            if not related:
                raise ValueError("Referenced AED was not found.")

        if (
            data.reporter_latitude is not None
            and data.reporter_longitude is None
        ) or (
            data.reporter_latitude is None
            and data.reporter_longitude is not None
        ):
            raise ValueError("Both reporter latitude and longitude are required together.")

        image_count = len(local_images) + len(temp_images)
        if image_count > 0:
            _validate_image_count(image_count, settings)

        spam = self.ai.check_spam(data.description, None)
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

        if image_object_keys:
            await self._analyze_images(image_object_keys, warnings)

        serialized_keys = serialize_image_object_keys(image_object_keys)
        reporter_location = None
        reporter_latitude = None
        reporter_longitude = None
        if data.reporter_latitude is not None and data.reporter_longitude is not None:
            reporter_latitude = data.reporter_latitude
            reporter_longitude = data.reporter_longitude
            reporter_location = WKTElement(
                f"POINT({data.reporter_longitude} {data.reporter_latitude})",
                srid=4326,
            )

        report = Report(
            aed_id=data.aed_id,
            description=data.description.strip(),
            reporter_latitude=reporter_latitude,
            reporter_longitude=reporter_longitude,
            reporter_location=reporter_location,
            image_url=image_object_keys[0] if image_object_keys else None,
            image_object_keys=serialized_keys,
            contact_email=str(data.contact_email) if data.contact_email else None,
            submitter_id=submitter.id if submitter else None,
            status=ReportStatus.pending,
            spam_score=spam.score,
        )
        created = await self.report_repo.create(report)
        logger.info(
            "report_submitted",
            report_id=created.id,
            aed_id=created.aed_id,
            image_count=len(image_object_keys),
            warnings=warnings,
        )
        return ReportSubmissionResult(
            report=_to_response(created, storage=self.storage),
            warnings=warnings,
        )

    async def list_pending_reports(self, *, page: int, page_size: int) -> ReportListResponse:
        rows, total = await self.report_repo.list_pending(page=page, page_size=page_size)
        items = [_to_response(report, storage=self.storage) for report in rows]
        return ReportListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=page * page_size < total,
        )

    async def update_status(
        self,
        report_id: int,
        status: ReportStatus,
    ) -> ReportResponse | None:
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            return None
        report.status = status
        updated = await self.report_repo.update(report)
        return _to_response(updated, storage=self.storage)
