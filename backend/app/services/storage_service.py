import uuid
from pathlib import Path

import aiofiles

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

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
