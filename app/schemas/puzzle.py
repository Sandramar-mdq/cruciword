from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClueSchema(BaseModel):
    """Pista estática de una palabra del crucigrama."""

    number: int
    direction: Literal["across", "down"]
    clue_text: str
    static_hint: str | None = None
    audio_url: str | None = None
    length: int


class PlacementSchema(BaseModel):
    """Posición de una palabra dentro de la grilla."""

    clue_key: str
    row: int
    col: int
    direction: Literal["across", "down"]


class PuzzleSummary(BaseModel):
    """Resumen ligero de un crucigrama para listados."""

    id: int
    title: str
    theme: str
    cefr_level: Literal["A1", "A2", "B1", "B2", "C1"]
    classroom_id: int | None


class PuzzleDetailResponse(BaseModel):
    """Detalle jugable del crucigrama sin IA externa."""

    id: int
    title: str
    cefr_level: Literal["A1", "A2", "B1", "B2", "C1"]
    grid_size: dict[str, int]
    blocked_cells: list[list[int]]
    clues: list[ClueSchema]
    placements: list[PlacementSchema]


class ProgressSubmit(BaseModel):
    """Respuestas del usuario, pistas usadas y Modo Power."""

    answers: dict[str, str]
    power_mode_used: bool
    hints_used: int = Field(default=0, ge=0)


class ProgressResultResponse(BaseModel):
    """Resultado alentador de la partida; nunca punitivo."""

    completed: bool
    correct_words: list[str]
    incorrect_words: list[str]
    power_badge_earned: bool
    score: int
    total_words: int
    best_score: int
    improved: bool
    message: str


class CheckSubmit(BaseModel):
    """Respuestas temporales para verificación instantánea sin guardarlas."""

    answers: dict[str, str]


class CheckResultResponse(BaseModel):
    """Estado por letra y palabra; no incluye las soluciones."""

    completed: bool
    correct_words: list[str]
    incorrect_words: list[str]
    letters: dict[str, list[bool]]
    score: int
    total_words: int
    message: str


class RetentionSubmit(BaseModel):
    """Respuestas del test de retención sin pistas ni Modo Power."""

    answers: dict[str, str]


class RetentionResultResponse(BaseModel):
    """Resultado del repaso semanal sin bloqueos ni mensajes punitivos."""

    completed: bool
    correct_words: list[str]
    incorrect_words: list[str]
    score: int
    message: str
