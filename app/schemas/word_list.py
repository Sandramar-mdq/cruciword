from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WordSummary(BaseModel):
    """Palabra pública del banco léxico propio."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    word: str
    translation: str
    level: Literal["A1", "A2", "B1", "B2", "C1"]
    theme: str
    definition_en: str
    synonym_hint: str | None
    is_power: bool


class WordListCreate(BaseModel):
    """Lista docente compuesta por palabras ya existentes."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    word_ids: list[int] = Field(default_factory=list)

    @field_validator("word_ids")
    @classmethod
    def dedupe_word_ids(cls, value: list[int]) -> list[int]:
        """Conserva el orden original pero elimina IDs repetidos."""
        return list(dict.fromkeys(value))


class WordListResponse(BaseModel):
    """Lista personalizada visible por docente y alumnos vinculados."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    classroom_id: int | None
    teacher_id: int
    words: list[WordSummary]
