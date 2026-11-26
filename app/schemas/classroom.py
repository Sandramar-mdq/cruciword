from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class ClassroomCreate(BaseModel):
    """Datos para crear un aula docente."""

    name: str
    description: str | None = None


class ClassroomResponse(BaseModel):
    """Aula visible por docentes y estudiantes vinculados."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    join_code: str
    teacher_id: int


class ClassroomJoin(BaseModel):
    """Código de clase normalizado antes de validarse."""

    join_code: str

    @field_validator("join_code", mode="before")
    @classmethod
    def normalize_join_code(cls, value: object) -> object:
        """Elimina espacios y convierte el código a mayúsculas."""
        if isinstance(value, str):
            return value.strip().upper()
        return value
