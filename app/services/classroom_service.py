from __future__ import annotations

import secrets

JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_join_code(length: int = 6) -> str:
    """Genera un código corto, alfanumérico y fácil de dictar."""
    if length < 1:
        raise ValueError("La longitud del código debe ser positiva.")
    return "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(length))
