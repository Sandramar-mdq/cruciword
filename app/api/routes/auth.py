from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from models import User, UserRole

router = APIRouter()


def _to_user_response(user: User) -> UserResponse:
    """Convierte el ORM a respuesta pública sin exponer el hash."""
    return UserResponse(
        id=user.id,
        username=user.email,
        role=getattr(user.role, "value", user.role),
        created_at=user.created_at,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Registra un estudiante o profesor con contraseña hasheada."""
    existing = db.scalar(select(User).where(User.email == payload.username))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese usuario o email.",
        )

    user = User(
        email=payload.username,
        hashed_password=hash_password(payload.password),
        role=UserRole(payload.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.post("/login", response_model=Token)
def login(
    credentials: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Valida credenciales y devuelve un JWT Bearer."""
    user = db.scalar(select(User).where(User.email == credentials.username))
    if user is None or not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = getattr(user.role, "value", user.role)
    return Token(access_token=create_access_token({"sub": user.email, "role": role}))
