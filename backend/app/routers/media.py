"""
Staff photo library, plus composed (photo + text overlay) images — both
direct-to-R2 presigned uploads with a metadata CRUD layer. See
app/services/object_storage.py for the storage mechanics and
app/models/media.py's module docstring for the proposed-scope framing.

Upload is a two-step confirm flow, not a single call, for both kinds:
the browser asks this backend for a presigned URL (POST /presign-upload
or /presign-composed-upload), uploads the file bytes straight to R2
itself, then tells this backend the upload succeeded (POST /photos or
/composed-images) so the metadata row gets created. This backend never
receives or trusts client-claimed file bytes — only the client-claimed
size/content-type, which are informational display fields here, not
security-relevant.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ComposedImage, ContentItem, PhotoAsset
from app.models.media import COMPOSED_IMAGE_OBJECT_PREFIX
from app.schemas.media import (
    ComposedImageCreate,
    ComposedImagePresignRequest,
    ComposedImageResponse,
    PhotoAssetCreate,
    PhotoAssetResponse,
    PresignUploadRequest,
    PresignUploadResponse,
    StockPhotoResult,
)
from app.services import object_storage, pexels

router = APIRouter(prefix="/api/media", tags=["media"])


def _serialize_photo(photo: PhotoAsset) -> PhotoAssetResponse:
    return PhotoAssetResponse(
        id=photo.id,
        object_key=photo.object_key,
        public_url=photo.public_url,
        filename=photo.filename,
        content_type=photo.content_type,
        size_bytes=photo.size_bytes,
        key_maker_id=photo.key_maker_id,
        event_id=photo.event_id,
        caption=photo.caption,
        uploaded_by=photo.uploaded_by,
        created_at=photo.created_at,
    )


@router.post("/presign-upload", response_model=PresignUploadResponse)
def presign_upload(request: PresignUploadRequest) -> PresignUploadResponse:
    object_key = object_storage.build_object_key("photos", request.filename)
    upload_url = object_storage.generate_presigned_upload_url(object_key, request.content_type)
    return PresignUploadResponse(upload_url=upload_url, object_key=object_key)


@router.post("/photos", response_model=PhotoAssetResponse)
def create_photo(request: PhotoAssetCreate, db: Session = Depends(get_db)) -> PhotoAssetResponse:
    """Persists the metadata row after the browser's direct PUT to R2
    succeeded. Does not verify the object actually exists in R2 — a
    client that lies here just gets a broken thumbnail, not a security
    issue, since object_key is R2-namespaced and uuid-prefixed (see
    object_storage.build_object_key), not guessable/collidable across
    uploads."""
    photo = PhotoAsset(
        object_key=request.object_key,
        public_url=object_storage.build_public_url(request.object_key),
        filename=request.filename,
        content_type=request.content_type,
        size_bytes=request.size_bytes,
        key_maker_id=request.key_maker_id,
        event_id=request.event_id,
        caption=request.caption,
        uploaded_by=request.uploaded_by,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return _serialize_photo(photo)


@router.get("/photos", response_model=list[PhotoAssetResponse])
def list_photos(
    key_maker_id: int | None = None,
    event_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[PhotoAssetResponse]:
    query = db.query(PhotoAsset)
    if key_maker_id is not None:
        query = query.filter(PhotoAsset.key_maker_id == key_maker_id)
    if event_id is not None:
        query = query.filter(PhotoAsset.event_id == event_id)
    photos = query.order_by(PhotoAsset.created_at.desc()).all()
    return [_serialize_photo(p) for p in photos]


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int, db: Session = Depends(get_db)) -> dict:
    photo = db.query(PhotoAsset).filter(PhotoAsset.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        object_storage.delete_object(photo.object_key)
    except Exception:
        # Best-effort — the DB row is the source of truth for what the
        # library considers to exist; an orphaned R2 object costs
        # fractions of a cent and isn't worth failing the request over.
        pass

    db.delete(photo)
    db.commit()
    return {"ok": True}


def _serialize_composed_image(image: ComposedImage) -> ComposedImageResponse:
    return ComposedImageResponse(
        id=image.id,
        content_item_id=image.content_item_id,
        source_photo_id=image.source_photo_id,
        object_key=image.object_key,
        public_url=image.public_url,
        content_type=image.content_type,
        size_bytes=image.size_bytes,
        created_at=image.created_at,
    )


@router.post("/presign-composed-upload", response_model=PresignUploadResponse)
def presign_composed_upload(request: ComposedImagePresignRequest) -> PresignUploadResponse:
    """Same presign-then-PUT flow as /presign-upload (see object_storage.py),
    under the 'composed/' prefix instead of 'photos/' — the browser flattens
    a PhotoAsset + overlay text to a PNG via Canvas, then uploads it here
    directly. This backend never renders or receives the composite itself."""
    object_key = object_storage.build_object_key(COMPOSED_IMAGE_OBJECT_PREFIX, request.filename)
    upload_url = object_storage.generate_presigned_upload_url(object_key, request.content_type)
    return PresignUploadResponse(upload_url=upload_url, object_key=object_key)


@router.post("/composed-images", response_model=ComposedImageResponse)
def create_composed_image(request: ComposedImageCreate, db: Session = Depends(get_db)) -> ComposedImageResponse:
    """Persists the metadata row after the browser's direct PUT to R2
    succeeded. content_item_id must already exist — a composite is always
    attached to a saved content item, not a still-in-progress draft."""
    content_item = db.query(ContentItem).filter(ContentItem.id == request.content_item_id).first()
    if not content_item:
        raise HTTPException(status_code=404, detail="Content item not found")

    image = ComposedImage(
        content_item_id=request.content_item_id,
        source_photo_id=request.source_photo_id,
        object_key=request.object_key,
        public_url=object_storage.build_public_url(request.object_key),
        content_type=request.content_type,
        size_bytes=request.size_bytes,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return _serialize_composed_image(image)


@router.get("/composed-images", response_model=list[ComposedImageResponse])
def list_composed_images(content_item_id: int, db: Session = Depends(get_db)) -> list[ComposedImageResponse]:
    images = (
        db.query(ComposedImage)
        .filter(ComposedImage.content_item_id == content_item_id)
        .order_by(ComposedImage.created_at.desc())
        .all()
    )
    return [_serialize_composed_image(i) for i in images]


@router.delete("/composed-images/{composed_image_id}")
def delete_composed_image(composed_image_id: int, db: Session = Depends(get_db)) -> dict:
    image = db.query(ComposedImage).filter(ComposedImage.id == composed_image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Composed image not found")

    try:
        object_storage.delete_object(image.object_key)
    except Exception:
        # Best-effort, same rationale as delete_photo above — the DB row
        # is the source of truth for what exists.
        pass

    db.delete(image)
    db.commit()
    return {"ok": True}


@router.get("/proxy/photos/{photo_id}")
def proxy_photo(photo_id: int, db: Session = Depends(get_db)) -> Response:
    """Re-serves a PhotoAsset's bytes through this backend — a workaround
    for the photo/text composer's Canvas needing to load images
    cross-origin (via crossOrigin="anonymous", so canvas.toBlob() isn't
    tainted) while R2's free .r2.dev public subdomain doesn't reliably
    send Access-Control-Allow-Origin on real GET responses (see
    object_storage.fetch_object_bytes) — this app's own CORSMiddleware
    (main.py) already handles the header correctly for every route,
    including this one, so nothing extra is set here. Fetches fresh from
    R2 on every call rather than caching — this is a small handful of
    photos per event, not high-traffic content."""
    photo = db.query(PhotoAsset).filter(PhotoAsset.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    content, content_type = object_storage.fetch_object_bytes(photo.object_key)
    return Response(
        content=content,
        media_type=content_type or photo.content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/proxy/composed-images/{composed_image_id}")
def proxy_composed_image(composed_image_id: int, db: Session = Depends(get_db)) -> Response:
    """Same workaround as proxy_photo above, for a ComposedImage."""
    image = db.query(ComposedImage).filter(ComposedImage.id == composed_image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Composed image not found")

    content, content_type = object_storage.fetch_object_bytes(image.object_key)
    return Response(
        content=content,
        media_type=content_type or image.content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/stock-photos", response_model=list[StockPhotoResult])
def search_stock_photos(query: str) -> list[StockPhotoResult]:
    """Proxies a Pexels search — see app/services/pexels.py. Keeps
    PEXELS_API_KEY server-side; the frontend only ever sees the search
    results, not the key itself."""
    try:
        results = pexels.search_photos(query)
    except pexels.PexelsNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    return [StockPhotoResult(**r) for r in results]
