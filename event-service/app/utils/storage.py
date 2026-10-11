from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

EVENT_DIR = Path(settings.UPLOAD_DIR) / "events"


def ensure_upload_dirs() -> None:
    EVENT_DIR.mkdir(parents=True, exist_ok=True)


def _sniff_extension(data: bytes) -> str | None:
    """Detect the real image type from magic bytes (content-type headers can be faked)."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


async def save_image(file: UploadFile) -> str:
    max_bytes = settings.MAX_IMAGE_MB * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"{file.filename}: image must be <= {settings.MAX_IMAGE_MB} MB",
        )
    ext = _sniff_extension(data)
    if ext is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"{file.filename}: only JPEG, PNG and WEBP images are allowed",
        )
    name = f"{uuid4().hex}{ext}"
    (EVENT_DIR / name).write_bytes(data)
    return f"{settings.PUBLIC_BASE_URL}/uploads/events/{name}"


def delete_image(url: str) -> None:
    # Path(...).name strips any directory part, so a crafted URL cannot escape EVENT_DIR
    (EVENT_DIR / Path(url).name).unlink(missing_ok=True)