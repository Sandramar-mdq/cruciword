from __future__ import annotations

from pydantic import BaseModel


class Token(BaseModel):
    """Bearer token devuelto tras autenticación."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Datos mínimos extraídos del token."""

    sub: str | None = None
    role: str | None = None
