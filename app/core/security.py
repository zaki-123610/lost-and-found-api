from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY

JWT_ALGORITHM = "HS256"
# bcrypt refuses passwords longer than 72 bytes (not characters).
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Hash a password with bcrypt. The random salt is stored inside the hash."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if `password` matches the stored bcrypt hash."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False  # registration rejects such passwords, so it can't match
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    """Create a signed JWT that identifies the user and expires after the configured time."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),  # PyJWT requires the subject to be a string
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Return the user id from a valid token, or None if it is invalid or expired."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None
