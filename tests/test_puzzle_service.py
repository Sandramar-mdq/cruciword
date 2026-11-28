from __future__ import annotations

from app.services.puzzle_service import check_answers, evaluate_progress


def _grid_data() -> dict[str, object]:
    return {
        "grid_size": {"rows": 5, "cols": 5},
        "blocked_cells": [[0, 1], [2, 3]],
        "clues": [
            {
                "number": 1,
                "direction": "across",
                "clue_text": "Fruit",
                "length": 5,
                "answer": "APPLE",
            },
            {
                "number": 2,
                "direction": "down",
                "clue_text": "Orbit",
                "length": 7,
                "answer": "GIVE UP",
            },
        ],
        "solutions": {"1_across": " apple ", "2_down": "give  up"},
    }


def test_evaluate_progress_normalizes_and_completes() -> None:
    result = evaluate_progress(
        _grid_data(),
        {"1_across": "  APPLE ", "2_down": "give   up"},
    )

    assert result.completed is True
    assert result.correct_words == ["1_across", "2_down"]
    assert result.incorrect_words == []
    assert result.power_badge_earned is False
    assert result.message.startswith("¡Muy bien!")


def test_evaluate_progress_separates_correct_and_incorrect() -> None:
    result = evaluate_progress(
        _grid_data(),
        {"1_across": "APPLE", "2_down": "WRONG"},
        hints_used=1,
    )

    assert result.completed is False
    assert result.correct_words == ["1_across"]
    assert result.incorrect_words == ["2_down"]
    assert "sin prisa" in result.message


def test_power_badge_requires_no_hints() -> None:
    answers = {"1_across": "APPLE", "2_down": "GIVE UP"}

    earned = evaluate_progress(_grid_data(), answers, 0, True)
    not_earned = evaluate_progress(_grid_data(), answers, 1, True)

    assert earned.power_badge_earned is True
    assert not_earned.power_badge_earned is False
    assert "insignia" in earned.message


def test_solutions_fallback_from_clues() -> None:
    grid_data: dict[str, object] = {
        "clues": [{"number": 3, "direction": "down", "answer": " apple "}]
    }

    result = evaluate_progress(grid_data, {"3_down": "Apple"})

    assert result.completed is True
    assert result.correct_words == ["3_down"]


def test_personal_best_only_grows() -> None:
    answers = {"1_across": "APPLE", "2_down": "GIVE UP"}

    first = evaluate_progress(_grid_data(), answers, previous_best=0)
    second = evaluate_progress(_grid_data(), answers, previous_best=2)

    assert first.score == 2
    assert first.best_score == 2
    assert first.improved is True
    assert "marca personal" in first.message
    assert second.best_score == 2
    assert second.improved is False


def test_check_answers_marks_letters_without_revealing_solutions() -> None:
    result = check_answers(
        _grid_data(),
        {"1_across": "APXLE", "2_down": "GIVE UP"},
    )

    assert result.letters["1_across"] == [True, True, False, True, True]
    assert result.correct_words == ["2_down"]
    assert result.incorrect_words == ["1_across"]
    assert result.score == 1
    assert "APPLE" not in result.model_dump_json()


def test_check_answers_marks_missing_words_as_pending() -> None:
    result = check_answers(_grid_data(), {"1_across": "APPLE"})

    assert result.letters["2_down"] == [False] * 6
    assert result.correct_words == ["1_across"]
    assert result.completed is False
