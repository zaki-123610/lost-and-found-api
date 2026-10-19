from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, field_validator

from app.core.security import MAX_PASSWORD_BYTES

Email = Annotated[EmailStr, AfterValidator(str.lower)]


class UserCreate(BaseModel):
    email: Email = Field(examples=["amine@example.com"])
    password: str = Field(min_length=8, examples=["strongpassword123"])

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password is too long: at most {MAX_PASSWORD_BYTES} bytes "
                "(non-Latin characters count as 2 or more)"
            )
        return value


class UserLogin(BaseModel):
    email: Email = Field(examples=["amine@example.com"])
    password: str = Field(examples=["strongpassword123"])


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
