from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Devuelve el usuario autenticado a partir del JWT."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise credentials_error from exc

    if not payload.sub:
        raise credentials_error

    user = db.scalar(select(User).where(User.email == payload.sub))
    if user is None:
        raise credentials_error

    return user


def require_teacher(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Permite el acceso solo a usuarios con rol docente."""
    role = getattr(current_user.role, "value", current_user.role)
    if role != UserRole.TEACHER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere un rol de profesor.",
        )
    return current_user
