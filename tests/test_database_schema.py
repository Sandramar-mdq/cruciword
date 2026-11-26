from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import JSON, UniqueConstraint, create_engine
from sqlalchemy import inspect as sa_inspect

import database
from alembic import command
from models import (
    AccountType,
    Classroom,
    Level,
    Puzzle,
    User,
    UserProgress,
    UserRole,
    Word,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {
    "users",
    "classrooms",
    "student_classrooms",
    "words",
    "puzzles",
    "user_progress",
}


def test_expected_tables() -> None:
    assert set(database.Base.metadata.tables) == EXPECTED_TABLES


def test_expected_columns() -> None:
    expected = {
        "users": {
            "id",
            "email",
            "hashed_password",
            "role",
            "account_type",
            "created_at",
        },
        "classrooms": {"id", "teacher_id", "name", "invite_code", "created_at"},
        "student_classrooms": {"student_id", "classroom_id", "joined_at"},
        "words": {
            "id",
            "word",
            "translation",
            "level",
            "theme",
            "definition_en",
            "synonym_hint",
            "is_power",
            "sponsored_by",
        },
        "puzzles": {"id", "theme", "level", "title", "grid_data", "classroom_id"},
        "user_progress": {
            "id",
            "user_id",
            "puzzle_id",
            "is_completed",
            "score",
            "hints_used",
            "updated_at",
        },
    }
    for table_name, columns in expected.items():
        assert set(database.Base.metadata.tables[table_name].columns.keys()) == columns


def _ondelete(table_name: str, column_name: str) -> str | None:
    column = database.Base.metadata.tables[table_name].c[column_name]
    return next(iter(column.foreign_keys)).ondelete


def test_foreign_keys_use_cascade() -> None:
    assert _ondelete("classrooms", "teacher_id") == "CASCADE"
    assert _ondelete("puzzles", "classroom_id") == "CASCADE"
    assert _ondelete("student_classrooms", "student_id") == "CASCADE"
    assert _ondelete("student_classrooms", "classroom_id") == "CASCADE"
    assert _ondelete("user_progress", "user_id") == "CASCADE"
    assert _ondelete("user_progress", "puzzle_id") == "CASCADE"


def test_relationships_are_configured() -> None:
    assert {"classrooms_taught", "classrooms_enrolled", "progress"} <= set(
        sa_inspect(User).relationships.keys()
    )
    assert {"teacher", "students", "puzzles"} <= set(
        sa_inspect(Classroom).relationships.keys()
    )
    assert {"classroom", "progress"} <= set(sa_inspect(Puzzle).relationships.keys())
    assert {"user", "puzzle"} <= set(sa_inspect(UserProgress).relationships.keys())
    assert set(sa_inspect(Word).relationships.keys()) == set()


def test_json_column_and_progress_uniqueness() -> None:
    assert isinstance(Puzzle.__table__.c.grid_data.type, JSON)
    assert any(
        isinstance(constraint, UniqueConstraint)
        and set(constraint.columns.keys()) == {"user_id", "puzzle_id"}
        for constraint in UserProgress.__table__.constraints
    )


def test_enum_values() -> None:
    assert [member.value for member in Level] == ["A1", "A2", "B1", "B2", "C1"]
    assert [member.value for member in UserRole] == ["student", "teacher", "admin"]
    assert [member.value for member in AccountType] == [
        "free",
        "premium",
        "institutional",
    ]


def test_initial_migration_applies_and_reverts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_url = "sqlite:///" + (tmp_path / "cruciword.db").as_posix()
    monkeypatch.setattr(database, "DATABASE_URL", db_url)
    config = Config(str(ROOT / "alembic.ini"))

    command.upgrade(config, "head")
    engine = create_engine(db_url)
    try:
        assert EXPECTED_TABLES <= set(sa_inspect(engine).get_table_names())
    finally:
        engine.dispose()

    command.downgrade(config, "base")
    engine = create_engine(db_url)
    try:
        assert EXPECTED_TABLES.isdisjoint(sa_inspect(engine).get_table_names())
    finally:
        engine.dispose()
