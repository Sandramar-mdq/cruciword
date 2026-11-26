from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.user import UserResponse
from models import User

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Devuelve los datos públicos del usuario autenticado."""
    return UserResponse(
        id=current_user.id,
        username=current_user.email,
        role=getattr(current_user.role, "value", current_user.role),
        created_at=current_user.created_at,
    )
