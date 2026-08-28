from pathlib import Path
import uuid
from fastapi import UploadFile, File, Form, HTTPException

from app.config import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, MEDIA_ROOT, BASE_DIR


async def save_product_image(file: UploadFile):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG or WebP images are allowed",
        )
    
    content = await file.read()

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail='Image is too large',
        )
    
    extension = Path(file.filename or '').suffix.lower() or '.jpg'
    file_name = f'{uuid.uuid4()}{extension}'
    file_path = MEDIA_ROOT / file_name
    file_path.write_bytes(content)

    return f"/media/products/{file_name}" 


def remove_product_image(url: str | None) -> None:
    if not url:
        return
    relative_path = url.lstrip("/")
    file_path = BASE_DIR / relative_path
    if file_path.exists():
        file_path.unlink()