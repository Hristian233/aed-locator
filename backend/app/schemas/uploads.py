from pydantic import BaseModel, Field


class SignedUploadRequest(BaseModel):
    content_type: str = Field(min_length=3, max_length=128)
    content_length: int = Field(ge=1024)


class SignedUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in_seconds: int
