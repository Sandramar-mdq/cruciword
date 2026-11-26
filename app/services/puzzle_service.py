from __future__ import annotations

from app.schemas.puzzle import ProgressResultResponse


def _normalize_text(value: str) -> str:
    """Normaliza mayúsculas y espacios para comparar respuestas."""
    return " ".join(value.upper().split())


def _normalize_key(value: str) -> str:
    """Normaliza la clave de una pista, por ejemplo 1_across."""
    return value.strip().lower()


def _extract_solutions(grid_data: dict[str, object]) -> dict[str, str]:
    """Obtiene soluciones desde solutions o, como respaldo, desde clues."""
    raw_solutions = grid_data.get("solutions")
    solutions: dict[str, str] = {}

    if isinstance(raw_solutions, dict):
        for key, value in raw_solutions.items():
            solutions[_normalize_key(str(key))] = str(value)
        return solutions

    raw_clues = grid_data.get("clues")
    if isinstance(raw_clues, list):
        for clue in raw_clues:
            if not isinstance(clue, dict):
                continue
            answer = clue.get("answer")
            number = clue.get("number")
            direction = clue.get("direction")
            if answer is None or number is None or direction is None:
                continue
            solutions[_normalize_key(f"{number}_{direction}")] = str(answer)

    return solutions


def _feedback_message(completed: bool, has_errors: bool, badge: bool) -> str:
    """Devuelve un mensaje amable, nunca punitivo."""
    if completed and badge:
        return "¡Excelente! Resolviste todo sin pistas y ganaste la insignia Modo Power."
    if completed:
        return "¡Muy bien! Completaste el crucigrama. Cada palabra suma."
    if has_errors:
        return "Vas muy bien. Revisa las palabras marcadas y continúa cuando quieras; sin prisa."
    return "Buen comienzo. Puedes seguir cuando quieras; aquí estamos para ayudarte."


def evaluate_progress(
    grid_data: dict[str, object],
    answers: dict[str, str],
    hints_used: int = 0,
    power_mode_used: bool = False,
) -> ProgressResultResponse:
    """Evalúa respuestas normalizadas y calcula completado, errores e insignia."""
    solutions = _extract_solutions(grid_data)
    normalized_answers = {
        _normalize_key(str(key)): str(value) for key, value in answers.items()
    }

    correct_words: list[str] = []
    incorrect_words: list[str] = []

    for key, expected in solutions.items():
        submitted = normalized_answers.get(key)
        if submitted is not None and _normalize_text(submitted) == _normalize_text(
            expected
        ):
            correct_words.append(key)
        else:
            incorrect_words.append(key)

    completed = bool(solutions) and not incorrect_words
    badge_earned = completed and power_mode_used and hints_used == 0

    return ProgressResultResponse(
        completed=completed,
        correct_words=correct_words,
        incorrect_words=incorrect_words,
        power_badge_earned=badge_earned,
        message=_feedback_message(completed, bool(incorrect_words), badge_earned),
    )
