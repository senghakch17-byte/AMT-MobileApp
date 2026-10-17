from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# Private directory: nothing here is mounted as static files. Downloads go through
# authenticated endpoints so one member can never fetch another member's document.
DOCUMENT_DIR = Path(settings.UPLOAD_DIR) / "documents"


@dataclass(frozen=True)
class StoredFile:
    stored_filename: str
    content_type: str
    size_bytes: int


def ensure_upload_dirs() -> None:
    DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)


def _sniff_type(data: bytes) -> tuple[str, str] | None:
    """Detect the real file type from magic bytes (content-type headers can be faked)."""
    if data.startswith(b"%PDF-"):
        return ".pdf", "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png", "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp", "image/webp"
    return None


async def save_document(file: UploadFile) -> StoredFile:
    max_bytes = settings.MAX_DOCUMENT_MB * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"{file.filename}: document must be <= {settings.MAX_DOCUMENT_MB} MB",
        )
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{file.filename}: file is empty")
    sniffed = _sniff_type(data)
    if sniffed is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"{file.filename}: only PDF, JPEG, PNG and WEBP files are allowed",
        )
    ext, content_type = sniffed
    name = f"{uuid4().hex}{ext}"
    (DOCUMENT_DIR / name).write_bytes(data)
    return StoredFile(stored_filename=name, content_type=content_type, size_bytes=len(data))


def document_path(stored_filename: str) -> Path:
    # Path(...).name strips any directory part, so a crafted value cannot escape DOCUMENT_DIR
    return DOCUMENT_DIR / Path(stored_filename).name


def delete_document_file(stored_filename: str) -> None:
    document_path(stored_filename).unlink(missing_ok=True)
