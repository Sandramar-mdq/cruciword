from __future__ import annotations

from app.schemas.puzzle import CheckResultResponse, ProgressResultResponse


def _normalize_text(value: str) -> str:
    """Normaliza mayúsculas y espacios para comparar respuestas."""
    return " ".join(value.upper().split())


def _normalize_key(value: str) -> str:
    """Normaliza la clave de una pista, por ejemplo 1_across."""
    return value.strip().lower()


def _normalize_answers(answers: dict[str, str]) -> dict[str, str]:
    return {_normalize_key(str(key)): str(value) for key, value in answers.items()}


def _letters(value: str) -> list[str]:
    return [character for character in value.upper() if character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]


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


def _personal_record(improved: bool, best_score: int) -> str:
    if improved:
        return f" Nueva marca personal: {best_score} palabras."
    return ""


def _feedback_message(
    completed: bool,
    has_errors: bool,
    badge: bool,
    improved: bool = False,
    best_score: int = 0,
) -> str:
    """Devuelve un mensaje amable, nunca punitivo."""
    record = _personal_record(improved, best_score)
    if completed and badge:
        return (
            "¡Excelente! Resolviste todo sin pistas y ganaste la insignia Modo Power."
            + record
        )
    if completed:
        return "¡Muy bien! Completaste el crucigrama. Cada palabra suma." + record
    if has_errors:
        return "Vas muy bien. Revisa las palabras marcadas y continúa cuando quieras; sin prisa."
    return "Buen comienzo. Puedes seguir cuando quieras; aquí estamos para ayudarte."


def evaluate_progress(
    grid_data: dict[str, object],
    answers: dict[str, str],
    hints_used: int = 0,
    power_mode_used: bool = False,
    previous_best: int = 0,
) -> ProgressResultResponse:
    """Evalúa respuestas normalizadas y calcula completado, errores e insignia."""
    solutions = _extract_solutions(grid_data)
    normalized_answers = _normalize_answers(answers)

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
    score = len(correct_words)
    best_score = max(score, previous_best)
    improved = score > previous_best

    return ProgressResultResponse(
        completed=completed,
        correct_words=correct_words,
        incorrect_words=incorrect_words,
        power_badge_earned=badge_earned,
        score=score,
        total_words=len(solutions),
        best_score=best_score,
        improved=improved,
        message=_feedback_message(completed, bool(incorrect_words), badge_earned, improved, best_score),
    )


def check_answers(
    grid_data: dict[str, object], answers: dict[str, str]
) -> CheckResultResponse:
    """Verifica letras y palabras sin guardar ni revelar las soluciones."""
    solutions = _extract_solutions(grid_data)
    normalized_answers = _normalize_answers(answers)

    correct_words: list[str] = []
    incorrect_words: list[str] = []
    letters: dict[str, list[bool]] = {}

    for key, expected in solutions.items():
        submitted = normalized_answers.get(key, "")
        expected_letters = _letters(expected)
        typed_letters = _letters(submitted)
        letters[key] = [
            index < len(typed_letters) and typed_letters[index] == letter
            for index, letter in enumerate(expected_letters)
        ]
        if _normalize_text(submitted) == _normalize_text(expected):
            correct_words.append(key)
        else:
            incorrect_words.append(key)

    completed = bool(solutions) and not incorrect_words
    score = len(correct_words)

    if completed:
        message = "¡Muy bien! Todas las palabras encajan. Sigue cuando quieras."
    elif incorrect_words and any(any(state) for state in letters.values()):
        message = "Vas muy bien. Las letras amarillas necesitan otra mirada; sin prisa."
    else:
        message = "Buen comienzo. Las letras verdes ya encajan; sigue a tu ritmo."

    return CheckResultResponse(
        completed=completed,
        correct_words=correct_words,
        incorrect_words=incorrect_words,
        letters=letters,
        score=score,
        total_words=len(solutions),
        message=message,
    )
