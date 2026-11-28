from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.auth import Token, TokenPayload
from app.schemas.classroom import ClassroomCreate, ClassroomJoin, ClassroomResponse
from app.schemas.puzzle import (
    CheckResultResponse,
    CheckSubmit,
    ClueSchema,
    PlacementSchema,
    ProgressResultResponse,
    ProgressSubmit,
    PuzzleDetailResponse,
    RetentionResultResponse,
    RetentionSubmit,
)
from app.schemas.user import UserCreate, UserResponse
from app.schemas.word_list import WordListCreate, WordListResponse, WordSummary


class UserRecord:
    id = 1
    username = "ana"
    role = "student"
    created_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    hashed_password = "hash-secreto"


class ClassroomRecord:
    id = 7
    name = "Inglés A1"
    description = "Grupo de lectoescritura"
    join_code = "M7K2"
    teacher_id = 3


def test_token_defaults() -> None:
    token = Token(access_token="abc")
    payload = TokenPayload()

    assert token.token_type == "bearer"
    assert payload.sub is None
    assert payload.role is None


def test_user_create_contract() -> None:
    student = UserCreate(username="ana@example.com", password="secreto")

    assert student.role == "student"

    with pytest.raises(ValidationError):
        UserCreate(username="ana", password="12345")

    with pytest.raises(ValidationError):
        UserCreate(username="ana", password="secreto", role="admin")


def test_user_response_excludes_password() -> None:
    response = UserResponse.model_validate(UserRecord())

    assert response.model_dump() == {
        "id": 1,
        "username": "ana",
        "role": "student",
        "created_at": datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    }
    assert "hashed_password" not in UserResponse.model_fields


def test_puzzle_detail_and_clue_validation() -> None:
    clue = ClueSchema(number=1, direction="across", clue_text="Fruit", length=5)
    placement = PlacementSchema(clue_key="1_across", row=0, col=0, direction="across")
    puzzle = PuzzleDetailResponse(
        id=1,
        title="Frutas",
        cefr_level="A1",
        grid_size={"rows": 5, "cols": 5},
        blocked_cells=[[0, 1], [2, 3]],
        clues=[clue],
        placements=[placement],
    )

    assert clue.static_hint is None
    assert clue.audio_url is None
    assert puzzle.grid_size["rows"] == 5
    assert puzzle.blocked_cells == [[0, 1], [2, 3]]
    assert puzzle.placements == [placement]

    with pytest.raises(ValidationError):
        ClueSchema(number=1, direction="diagonal", clue_text="Fruit", length=5)

    with pytest.raises(ValidationError):
        PuzzleDetailResponse(
            id=1,
            title="Frutas",
            cefr_level="C2",
            grid_size={"rows": 5, "cols": 5},
            blocked_cells=[],
            clues=[clue],
            placements=[placement],
        )


def test_progress_contracts() -> None:
    submit = ProgressSubmit(answers={"1_across": "APPLE"}, power_mode_used=True)
    result = ProgressResultResponse(
        completed=True,
        correct_words=["APPLE"],
        incorrect_words=[],
        power_badge_earned=True,
        score=1,
        total_words=1,
        best_score=1,
        improved=True,
        message="¡Buen trabajo, sigue así!",
    )
    check = CheckResultResponse(
        completed=False,
        correct_words=[],
        incorrect_words=["1_across"],
        letters={"1_across": [True, False]},
        score=0,
        total_words=1,
        message="Sigue a tu ritmo.",
    )

    assert submit.answers["1_across"] == "APPLE"
    assert result.power_badge_earned is True
    assert result.best_score == 1
    assert "answer" not in check.model_dump_json()
    assert CheckSubmit(answers={"1_across": "AP"}).answers == {"1_across": "AP"}

    with pytest.raises(ValidationError):
        ProgressSubmit(answers={"1_across": 5}, power_mode_used=False)


def test_classroom_join_normalizes_code() -> None:
    joined = ClassroomJoin(join_code="  m7k2 ")
    created = ClassroomCreate(name="Inglés A1")

    assert joined.join_code == "M7K2"
    assert created.description is None


def test_classroom_response_from_attributes() -> None:
    response = ClassroomResponse.model_validate(ClassroomRecord())

    assert response.model_dump() == {
        "id": 7,
        "name": "Inglés A1",
        "description": "Grupo de lectoescritura",
        "join_code": "M7K2",
        "teacher_id": 3,
    }


def test_word_list_contracts() -> None:
    created = WordListCreate(name="Frutas", word_ids=[3, 1, 3])
    word = WordSummary(
        id=1,
        word="APPLE",
        translation="manzana",
        level="A1",
        theme="Daily life",
        definition_en="A round fruit that grows on a tree.",
        synonym_hint="red fruit",
        is_power=False,
    )
    response = WordListResponse(
        id=9,
        name="Frutas",
        description=None,
        classroom_id=4,
        teacher_id=2,
        words=[word],
    )

    assert created.word_ids == [3, 1]
    assert response.words[0].word == "APPLE"

    with pytest.raises(ValidationError):
        WordListCreate(name="")


def test_retention_contracts() -> None:
    submit = RetentionSubmit(answers={"1_across": "APPLE"})
    result = RetentionResultResponse(
        completed=True,
        correct_words=["1_across"],
        incorrect_words=[],
        score=1,
        message="¡Muy bien! Completaste el crucigrama. Cada palabra suma.",
    )

    assert submit.answers["1_across"] == "APPLE"
    assert result.score == 1

    with pytest.raises(ValidationError):
        RetentionSubmit(answers={"1_across": 5})
