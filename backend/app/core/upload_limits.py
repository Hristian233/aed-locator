class ImageTooManyError(ValueError):
    def __init__(self, max_images: int) -> None:
        self.max_images = max_images
        super().__init__(
            f"At most {max_images} photos are allowed per submission.",
        )


def image_too_many_detail(max_images: int) -> dict[str, int | str]:
    return {
        "code": "image_too_many",
        "message": f"At most {max_images} photos are allowed per submission.",
        "max_images": max_images,
    }
