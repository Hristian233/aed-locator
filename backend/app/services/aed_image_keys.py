"""Serialize and resolve AED image object keys stored in the database."""

import json

from app.services.storage_service import StorageService


def parse_image_object_keys(
    image_object_keys: str | None,
    *,
    legacy_image_url: str | None = None,
) -> list[str]:
    if image_object_keys:
        try:
            parsed = json.loads(image_object_keys)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item) for item in parsed if isinstance(item, str) and item.strip()]
    if legacy_image_url and legacy_image_url.strip():
        return [legacy_image_url]
    return []


def serialize_image_object_keys(keys: list[str]) -> str | None:
    cleaned = [key for key in keys if key.strip()]
    if not cleaned:
        return None
    return json.dumps(cleaned)


def resolve_image_display_urls(
    keys: list[str],
    *,
    storage: StorageService,
) -> list[str]:
    urls: list[str] = []
    for key in keys:
        url = storage.resolve_display_url(key)
        if url:
            urls.append(url)
    return urls
