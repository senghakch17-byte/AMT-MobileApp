import jwt
from fastapi import HTTPException, status
from jwt.exceptions import PyJWTError
from pydantic import BaseModel

from app.core.config import settings


class CurrentUser(BaseModel):
    id: str
    emailid: str
    role: str


def decode_access_token(token: str) -> CurrentUser:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return CurrentUser(**payload)
    except (PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc