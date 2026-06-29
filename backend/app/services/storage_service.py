import uuid
from pathlib import Path

import aiofiles

from app.core.config import Settings, get_settings
from app.services.gcs_storage import GCSStorageError, GCSStorageService
from app.services.image_validation import validate_image_metadata


class StorageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        if not self.settings.uses_gcs_storage:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._gcs: GCSStorageService | None = None

    @property
    def gcs(self) -> GCSStorageService:
        if self._gcs is None:
            self._gcs = GCSStorageService(self.settings)
        return self._gcs

    def validate_upload_metadata(self, content_type: str, content_length: int) -> None:
        validate_image_metadata(
            content_type,
            content_length,
            settings=self.settings,
        )

    def create_signed_upload(
        self,
        *,
        content_type: str,
        content_length: int,
    ) -> tuple[str, str, int]:
        if not self.settings.uses_gcs_storage:
            raise GCSStorageError("Signed uploads are only available with GCS storage")
        return self.gcs.create_signed_upload_url(
            content_type=content_type,
            content_length=content_length,
        )

    def resolve_display_url(self, stored_value: str | None) -> str | None:
        if not stored_value:
            return None
        if not self.settings.uses_gcs_storage or stored_value.startswith("/"):
            return stored_value

        public_base = (self.settings.gcs_images_public_url_base or "").strip()
        if public_base:
            return f"{public_base.rstrip('/')}/{stored_value.lstrip('/')}"

        return self.gcs.create_signed_read_url(stored_value)

    def build_final_object_key(self) -> str:
        return self.gcs.build_final_object_key()

    async def save_image(self, content: bytes, content_type: str) -> str:
        ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }.get(content_type, ".bin")
        filename = f"{uuid.uuid4().hex}{ext}"
        path = self.upload_dir / filename
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)
        return f"/uploads/{filename}"

    async def load_image_bytes(self, object_key: str) -> bytes:
        if self.settings.uses_gcs_storage:
            return await self.gcs.download_object_bytes(
                self.settings.gcs_images_bucket,
                object_key,
            )
        path = Path(object_key)
        if not path.is_absolute():
            path = self.upload_dir / path.name
        async with aiofiles.open(path, "rb") as f:
            return await f.read()
