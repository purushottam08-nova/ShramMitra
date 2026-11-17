
import base64
import binascii

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import ALGORITHM, SECRET_KEY


bearer_scheme = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_canonical_jwt(token: str) -> bool:
    """
    Reject malformed or non-canonical Base64URL JWT segments.
    This prevents alternate encodings of the same signature.
    """
    parts = token.split(".")

    if len(parts) != 3:
        return False

    try:
        for part in parts:
            padded_part = part + ("=" * (-len(part) % 4))

            decoded = base64.b64decode(
                padded_part,
                altchars=b"-_",
                validate=True,
            )

            canonical = (
                base64.urlsafe_b64encode(decoded)
                .rstrip(b"=")
                .decode("ascii")
            )

            if canonical != part:
                return False

    except (binascii.Error, ValueError, UnicodeError):
        return False

    return True


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not validate_canonical_jwt(token):
        raise credentials_exception

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user
