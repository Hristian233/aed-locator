"""HTTP Cloud Function: validate, resize, convert to WebP, upload to final bucket."""

from __future__ import annotations

import io
from typing import Any

from flask import Request, jsonify
from google.cloud import storage
from PIL import Image, UnidentifiedImageError

MAX_EDGE_PX = 1920
WEBP_QUALITY = 85


def _error(message: str, *, status: int = 400) -> tuple[Any, int]:
    return jsonify({"success": False, "error": message}), status


def _validate_request(data: dict[str, Any]) -> tuple[dict[str, Any] | None, tuple[Any, int] | None]:
    required = ("temp_bucket", "temp_object_key", "final_bucket", "final_object_key")
    for key in required:
        if not data.get(key):
            return None, _error(f"Missing required field: {key}")

    max_bytes = int(data.get("max_bytes") or 10 * 1024 * 1024)
    allowed = data.get("allowed_content_types") or [
        "image/jpeg",
        "image/png",
        "image/webp",
    ]
    if isinstance(allowed, str):
        allowed = [item.strip() for item in allowed.split(",") if item.strip()]

    return {
        "temp_bucket": str(data["temp_bucket"]),
        "temp_object_key": str(data["temp_object_key"]),
        "final_bucket": str(data["final_bucket"]),
        "final_object_key": str(data["final_object_key"]),
        "expected_content_type": data.get("content_type"),
        "expected_content_length": data.get("content_length"),
        "max_bytes": max_bytes,
        "allowed_content_types": set(allowed),
    }, None


def _process_image(raw: bytes, *, max_bytes: int, allowed_types: set[str]) -> bytes:
    if len(raw) < 1024:
        raise ValueError("Image file is too small")
    if len(raw) > max_bytes:
        raise ValueError(f"Image exceeds maximum size of {max_bytes} bytes")

    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw))
    except UnidentifiedImageError as exc:
        raise ValueError("Uploaded file is not a valid image") from exc

    format_to_mime = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }
    mime = format_to_mime.get(image.format or "")
    if mime not in allowed_types:
        allowed = ", ".join(sorted(allowed_types))
        raise ValueError(f"Unsupported image type. Allowed: {allowed}")

    image = image.convert("RGB")
    image.thumbnail((MAX_EDGE_PX, MAX_EDGE_PX))

    output = io.BytesIO()
    image.save(output, format="WEBP", quality=WEBP_QUALITY, method=6)
    processed = output.getvalue()
    if len(processed) > max_bytes:
        raise ValueError(f"Processed image exceeds maximum size of {max_bytes} bytes")
    return processed


def process_image_request(request: Request) -> tuple[Any, int]:
    if request.method != "POST":
        return _error("Method not allowed", status=405)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("Expected JSON request body")

    params, error = _validate_request(data)
    if error:
        return error

    assert params is not None
    client = storage.Client()

    try:
        temp_blob = client.bucket(params["temp_bucket"]).blob(params["temp_object_key"])
        if not temp_blob.exists():
            return _error("Temporary upload was not found. Please upload the image again.")
        raw = temp_blob.download_as_bytes()
    except Exception as exc:
        return _error(f"Could not read temporary upload: {exc}", status=500)

    expected_type = params["expected_content_type"]
    if expected_type and expected_type not in params["allowed_content_types"]:
        return _error(f"Unsupported content type: {expected_type}")

    expected_length = params["expected_content_length"]
    if expected_length is not None:
        try:
            if int(expected_length) != len(raw):
                return _error("Uploaded image size does not match declared size")
        except (TypeError, ValueError):
            return _error("Invalid content_length value")

    try:
        processed = _process_image(
            raw,
            max_bytes=params["max_bytes"],
            allowed_types=params["allowed_content_types"],
        )
    except ValueError as exc:
        return _error(str(exc))

    try:
        final_blob = client.bucket(params["final_bucket"]).blob(params["final_object_key"])
        final_blob.upload_from_string(processed, content_type="image/webp")
        temp_blob.delete()
    except Exception as exc:
        return _error(f"Could not store processed image: {exc}", status=500)

    return jsonify(
        {
            "success": True,
            "final_object_key": params["final_object_key"],
        }
    ), 200


def image_processor(request: Request) -> tuple[Any, int]:
    """Cloud Functions entry point (functions-framework)."""
    return process_image_request(request)


if __name__ == "__main__":
    from flask import Flask

    app = Flask(__name__)

    @app.route("/", methods=["POST"])
    def local_handler() -> tuple[Any, int]:
        return process_image_request(Request.from_values())

    app.run(host="0.0.0.0", port=8081)
