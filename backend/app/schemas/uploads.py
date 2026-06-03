from pydantic import BaseModel, Field


class SignedUploadRequest(BaseModel):
    content_type: str = Field(min_length=3, max_length=128)
    content_length: int = Field(ge=1024)


class SignedUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in_seconds: int


class SignedUploadBatchRequest(BaseModel):
    uploads: list[SignedUploadRequest] = Field(min_length=1)


class SignedUploadBatchResponse(BaseModel):
    items: list[SignedUploadResponse]
    max_images_per_submission: int
