import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = BASE_DIR / 'media' / 'products'
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_IMAGE_SIZE = 2 * 1024 * 1024

if any(value is None for value in [DATABASE_URL, SECRET_KEY, ALGORITHM]):
    raise ValueError(f'Secret value is None')

try: 
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS'))
except TypeError:
    raise TypeError('Access or refresh token is None')

except ValueError:
    raise ValueError('Access or refresh token is not type int')
