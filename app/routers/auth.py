from fastapi import APIRouter, HTTPException, status
from psycopg.errors import UniqueViolation

from app.core.security import create_access_token, hash_password, verify_password
from app.db import DbConn
from app.dependencies import CurrentUserId
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, conn: DbConn) -> UserOut:
    """Create an account. Returns the new user, without the password hash."""
    try:
        row = conn.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            RETURNING id, email, created_at
            """,
            (user.email, hash_password(user.password)),
        ).fetchone()
    except UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from None
    return UserOut.model_validate(row)


@router.post("/login")
def login(credentials: UserLogin, conn: DbConn) -> Token:
    """Exchange email and password for a JWT access token."""
    user = conn.execute(
        "SELECT id, password_hash FROM users WHERE email = %s",
        (credentials.email,),
    ).fetchone()
    # Same error for unknown email and wrong password, so emails can't be probed.
    if user is None or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user["id"]))


@router.get("/me")
def read_me(user_id: CurrentUserId, conn: DbConn) -> UserOut:
    """Return the account that owns the token."""
    row = conn.execute(
        "SELECT id, email, created_at FROM users WHERE id = %s",
        (user_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(row)
