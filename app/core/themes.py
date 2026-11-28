from __future__ import annotations

from typing import TypedDict


class Theme(TypedDict):
    id: str
    label: str
    hint: str


THEMES: tuple[Theme, ...] = (
    {
        "id": "crema",
        "label": "Papel Crema",
        "hint": "Fondo cálido para leer sin deslumbramiento.",
    },
    {
        "id": "domingo",
        "label": "Edición Domingo",
        "hint": "Tono de periódico suave y descansado.",
    },
    {
        "id": "pizarra",
        "label": "Pizarra Nocturna",
        "hint": "Oscuro mate para jugar de noche.",
    },
)

DEFAULT_THEME: str = THEMES[0]["id"]
