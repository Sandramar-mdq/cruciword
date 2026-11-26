from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.seed import SEED_PUZZLES, SEED_WORDS, seed
from models import Level, Puzzle, Word


def test_seed_loads_words_and_puzzles_for_all_levels(
    test_env: tuple[object, sessionmaker[Session]],
) -> None:
    _, session_factory = test_env

    with session_factory() as db:
        result = seed(db)

    assert result.words_added == 25
    assert result.puzzles_added == 5

    with session_factory() as db:
        words = db.scalars(select(Word)).all()
        puzzles = db.scalars(select(Puzzle)).all()

    assert len(words) == len(SEED_WORDS) == 25
    assert len(puzzles) == len(SEED_PUZZLES) == 5
    assert {getattr(word.level, "value", word.level) for word in words} == {
        level.value for level in Level
    }
    assert {getattr(puzzle.level, "value", puzzle.level) for puzzle in puzzles} == {
        level.value for level in Level
    }
    assert all(word.synonym_hint for word in words)
    assert all(word.definition_en for word in words)
    assert all("solutions" in puzzle.grid_data for puzzle in puzzles)
    assert all("static_hint" in clue for puzzle in puzzles for clue in puzzle.grid_data["clues"])


def test_seed_is_idempotent(
    test_env: tuple[object, sessionmaker[Session]],
) -> None:
    _, session_factory = test_env

    with session_factory() as db:
        first = seed(db)
    with session_factory() as db:
        second = seed(db)

    assert first.words_skipped == 0
    assert first.puzzles_skipped == 0
    assert second.words_added == 0
    assert second.words_skipped == 25
    assert second.puzzles_added == 0
    assert second.puzzles_skipped == 5

    with session_factory() as db:
        assert len(db.scalars(select(Word)).all()) == 25
        assert len(db.scalars(select(Puzzle)).all()) == 5
