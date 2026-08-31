import uuid
from io import BytesIO

from fastapi import UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError

from app.config import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, MEDIA_ROOT, BASE_DIR


async def save_product_image(file: UploadFile):
    
    content = await file.read(MAX_IMAGE_SIZE + 1)

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail='Image is too large',
        )

    try:
        image = Image.open(BytesIO(content))
        image_format = image.format
        image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="File is not a valid image",
        )
    extension = ALLOWED_IMAGE_TYPES.get(image_format)

    if extension is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format",
        )
    
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