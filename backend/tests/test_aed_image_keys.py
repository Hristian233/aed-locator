from app.services.aed_image_keys import (
    parse_image_object_keys,
    serialize_image_object_keys,
)


def test_parse_legacy_single_image_url() -> None:
    keys = parse_image_object_keys(None, legacy_image_url="aed-images/one.webp")
    assert keys == ["aed-images/one.webp"]


def test_parse_json_image_object_keys() -> None:
    keys = parse_image_object_keys('["aed-images/a.webp","aed-images/b.webp"]')
    assert keys == ["aed-images/a.webp", "aed-images/b.webp"]


def test_serialize_image_object_keys() -> None:
    assert serialize_image_object_keys(["a", "b"]) == '["a", "b"]'
