from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Solicitud de registro con credenciales simples."""

    username: str
    password: str = Field(min_length=6, max_length=128)
    role: Literal["student", "teacher"] = "student"


class UserResponse(BaseModel):
    """Datos públicos del usuario; nunca expone el hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    created_at: datetime
