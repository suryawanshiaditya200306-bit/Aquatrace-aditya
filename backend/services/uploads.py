"""Image upload helpers: validation and safe temporary storage."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
}

# Project root = AquaSlick/ (backend/services/uploads.py → parents[2])
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB prototype limit


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def validate_image_upload(file: UploadFile) -> str:
    """Return normalized extension (.jpg / .jpeg / .png) or raise 400."""
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext or 'unknown'}'. Allowed: JPG, JPEG, PNG.",
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{content_type}'. Allowed: image/jpeg, image/png.",
        )

    return ext


async def save_upload(file: UploadFile) -> tuple[str, Path]:
    """
    Validate and save an uploaded image under data/uploads/.

    Returns (image_id, saved_path).
    """
    ext = validate_image_upload(file)
    ensure_upload_dir()

    image_id = uuid.uuid4().hex
    dest = UPLOAD_DIR / f"{image_id}{ext}"

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    dest.write_bytes(data)
    return image_id, dest
