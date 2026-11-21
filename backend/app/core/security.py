import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from jose import jwt
from pwdlib import PasswordHash


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not configured")

if APP_ENV == "production" and len(SECRET_KEY) < 32:
    raise ValueError(
        "Production JWT_SECRET_KEY must contain at least 32 characters"
    )

ALGORITHM = "HS256"

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
except ValueError as exc:
    raise ValueError(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be an integer"
    ) from exc

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise ValueError("JWT token expiry must be greater than zero")

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
