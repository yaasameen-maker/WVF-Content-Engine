from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.content import _as_utc


class PresignUploadRequest(BaseModel):
    """Ask the backend for a URL the browser can upload a file to
    directly — see app/services/object_storage.py. The backend never
    receives the file bytes."""
    filename: str = Field(..., description="Original filename, used to build the storage key")
    content_type: str = Field(..., description="MIME type, e.g. image/jpeg")


class PresignUploadResponse(BaseModel):
    upload_url: str = Field(..., description="Presigned URL — PUT the file bytes here directly")
    object_key: str = Field(..., description="Pass this back to POST /api/media/photos once the upload succeeds")


class PhotoAssetCreate(BaseModel):
    """Called after the browser's direct PUT to R2 succeeds, to persist
    the photo's metadata row."""
    object_key: str
    filename: str
    content_type: str
    size_bytes: int
    key_maker_id: Optional[int] = None
    event_id: Optional[int] = None
    caption: Optional[str] = None
    uploaded_by: Optional[str] = None


class PhotoAssetResponse(BaseModel):
    id: int
    object_key: str
    public_url: str
    filename: str
    content_type: str
    size_bytes: int
    key_maker_id: Optional[int] = None
    event_id: Optional[int] = None
    caption: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    _stamp_utc = field_validator("created_at")(_as_utc)


class ComposedImagePresignRequest(BaseModel):
    """Same shape/flow as PresignUploadRequest, kept as a separate model
    (rather than reusing that one) so the two upload kinds can diverge
    later — e.g. if composites ever need a different max size or
    content-type allowlist than raw photo uploads."""
    filename: str = Field(..., description="Filename for the flattened PNG, e.g. 'post-42-composite.png'")
    content_type: str = Field(..., description="MIME type — expected to be image/png")


class ComposedImageCreate(BaseModel):
    """Called after the browser's direct PUT to R2 succeeds, to persist
    the composed image's metadata row against the content item it's for."""
    content_item_id: int
    source_photo_id: Optional[int] = None
    object_key: str
    content_type: str
    size_bytes: int


class ComposedImageResponse(BaseModel):
    id: int
    content_item_id: int
    source_photo_id: Optional[int] = None
    object_key: str
    public_url: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}

    _stamp_utc = field_validator("created_at")(_as_utc)
