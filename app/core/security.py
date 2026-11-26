from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from app.core.config import get_settings
from app.schemas.auth import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de una contraseña."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba una contraseña contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, object],
    expires_delta: timedelta | None = None,
) -> str:
    """Crea un JWT de acceso con expiración estándar de sesión."""
    settings = get_settings()
    to_encode = dict(data)
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta if expires_delta is not None else timedelta(minutes=60)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """Valida un JWT y devuelve su payload mínimo."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise ValueError("Token JWT inválido o expirado.") from exc
    return TokenPayload(sub=payload.get("sub"), role=payload.get("role"))
