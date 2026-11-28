"""refresh_coherent_grids

Revision ID: 9f2a6c1d4b70
Revises: c4c813450fd6
Create Date: 2026-11-27 10:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.data.grids import GRID_SPECS, build_grid_data

revision: str = "9f2a6c1d4b70"
down_revision: str | Sequence[str] | None = "c4c813450fd6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

puzzles_table = sa.table(
    "puzzles",
    sa.column("id", sa.Integer()),
    sa.column("title", sa.String()),
    sa.column("level", sa.String()),
    sa.column("grid_data", sa.JSON()),
)


def _legacy_grid_data(*clues: dict[str, object]) -> dict[str, object]:
    return {
        "grid_size": {"rows": 5, "cols": 5},
        "blocked_cells": [[0, 1], [2, 3]],
        "clues": [
            {
                "number": clue["number"],
                "direction": clue["direction"],
                "clue_text": clue["clue_text"],
                "static_hint": clue["static_hint"],
                "audio_url": None,
                "length": clue["length"],
                "answer": clue["answer"],
            }
            for clue in clues
        ],
        "solutions": {
            f"{clue['number']}_{clue['direction']}".lower(): clue["answer"]
            for clue in clues
        },
    }


LEGACY_GRIDS: dict[str, dict[str, object]] = {
    "Primeras palabras": _legacy_grid_data(
        {
            "number": 1,
            "direction": "across",
            "clue_text": "A round fruit",
            "static_hint": "red fruit",
            "length": 5,
            "answer": "APPLE",
        },
        {
            "number": 2,
            "direction": "down",
            "clue_text": "A bright day star",
            "static_hint": "daylight star",
            "length": 3,
            "answer": "SUN",
        },
    ),
    "Hogar y ciudad": _legacy_grid_data(
        {
            "number": 1,
            "direction": "across",
            "clue_text": "A building where people live",
            "static_hint": "home building",
            "length": 5,
            "answer": "HOUSE",
        },
        {
            "number": 2,
            "direction": "down",
            "clue_text": "A large town",
            "static_hint": "large town",
            "length": 4,
            "answer": "CITY",
        },
    ),
    "Viaje y memoria": _legacy_grid_data(
        {
            "number": 1,
            "direction": "across",
            "clue_text": "The act of traveling",
            "static_hint": "trip",
            "length": 7,
            "answer": "JOURNEY",
        },
        {
            "number": 2,
            "direction": "down",
            "clue_text": "A helpful suggestion",
            "static_hint": "suggestion",
            "length": 6,
            "answer": "ADVICE",
        },
    ),
    "Logros y retos": _legacy_grid_data(
        {
            "number": 1,
            "direction": "across",
            "clue_text": "Something difficult you succeed in",
            "static_hint": "success",
            "length": 10,
            "answer": "ACHIEVEMENT",
        },
        {
            "number": 2,
            "direction": "down",
            "clue_text": "Able to be trusted",
            "static_hint": "trustworthy",
            "length": 8,
            "answer": "RELIABLE",
        },
    ),
    "Ideas precisas": _legacy_grid_data(
        {
            "number": 1,
            "direction": "across",
            "clue_text": "A very small difference",
            "static_hint": "subtle difference",
            "length": 6,
            "answer": "NUANCE",
        },
        {
            "number": 2,
            "direction": "down",
            "clue_text": "Brief and clear",
            "static_hint": "brief and clear",
            "length": 7,
            "answer": "CONCISE",
        },
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    for spec in GRID_SPECS:
        bind.execute(
            puzzles_table.update()
            .where(
                puzzles_table.c.title == spec.title,
                puzzles_table.c.level == spec.level.value,
            )
            .values(grid_data=build_grid_data(spec))
        )


def downgrade() -> None:
    bind = op.get_bind()
    for title, grid_data in LEGACY_GRIDS.items():
        bind.execute(
            puzzles_table.update()
            .where(puzzles_table.c.title == title)
            .values(grid_data=grid_data)
        )
