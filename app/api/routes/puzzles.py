from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.schemas.puzzle import (
    CheckResultResponse,
    CheckSubmit,
    ClueSchema,
    PlacementSchema,
    ProgressResultResponse,
    ProgressSubmit,
    PuzzleDetailResponse,
    PuzzleSummary,
    RetentionResultResponse,
    RetentionSubmit,
)
from app.services.puzzle_service import check_answers, evaluate_progress
from models import Level, Puzzle, User, UserProgress

router = APIRouter()


def _grid_size(grid_data: dict[str, object]) -> dict[str, int]:
    """Extrae rows y cols del JSON del crucigrama."""
    raw = grid_data.get("grid_size")
    if isinstance(raw, dict):
        rows = raw.get("rows")
        cols = raw.get("cols")
        if isinstance(rows, int) and isinstance(cols, int):
            return {"rows": rows, "cols": cols}
    return {"rows": 0, "cols": 0}


def _blocked_cells(grid_data: dict[str, object]) -> list[list[int]]:
    """Extrae las celdas bloqueadas como pares fila/columna."""
    raw = grid_data.get("blocked_cells")
    cells: list[list[int]] = []
    if isinstance(raw, list):
        for pair in raw:
            if isinstance(pair, list) and len(pair) == 2:
                row, col = pair
                if isinstance(row, int) and isinstance(col, int):
                    cells.append([row, col])
    return cells


def _clues(grid_data: dict[str, object]) -> list[ClueSchema]:
    """Convierte las pistas estáticas sin exponer sus respuestas."""
    raw = grid_data.get("clues")
    clues: list[ClueSchema] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            number = item.get("number")
            direction = item.get("direction")
            clue_text = item.get("clue_text")
            length = item.get("length")
            if (
                not isinstance(number, int)
                or direction not in {"across", "down"}
                or not isinstance(clue_text, str)
                or not isinstance(length, int)
            ):
                continue
            static_hint = item.get("static_hint")
            audio_url = item.get("audio_url")
            clues.append(
                ClueSchema(
                    number=number,
                    direction=direction,
                    clue_text=clue_text,
                    static_hint=static_hint if isinstance(static_hint, str) else None,
                    audio_url=audio_url if isinstance(audio_url, str) else None,
                    length=length,
                )
            )
    return clues


def _placements(grid_data: dict[str, object]) -> list[PlacementSchema]:
    """Extrae las posiciones de palabras sin incluir sus respuestas."""
    raw = grid_data.get("placements")
    placements: list[PlacementSchema] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            clue_key = item.get("clue_key")
            row = item.get("row")
            col = item.get("col")
            direction = item.get("direction")
            if (
                isinstance(clue_key, str)
                and isinstance(row, int)
                and isinstance(col, int)
                and direction in {"across", "down"}
            ):
                placements.append(
                    PlacementSchema(
                        clue_key=clue_key,
                        row=row,
                        col=col,
                        direction=direction,
                    )
                )
    return placements


def _get_puzzle_or_404(db: Session, puzzle_id: int) -> Puzzle:
    """Devuelve un crucigrama o lanza 404."""
    puzzle = db.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crucigrama no encontrado.",
        )
    return puzzle


def _to_detail(puzzle: Puzzle) -> PuzzleDetailResponse:
    """Convierte el modelo ORM a la respuesta detallada."""
    grid_data = puzzle.grid_data or {}
    return PuzzleDetailResponse(
        id=puzzle.id,
        title=puzzle.title,
        cefr_level=getattr(puzzle.level, "value", puzzle.level),
        grid_size=_grid_size(grid_data),
        blocked_cells=_blocked_cells(grid_data),
        clues=_clues(grid_data),
        placements=_placements(grid_data),
    )


def _get_or_create_progress(db: Session, user_id: int, puzzle_id: int) -> UserProgress:
    """Obtiene o crea el progreso único de un usuario para un crucigrama."""
    progress = db.scalar(
        select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.puzzle_id == puzzle_id,
        )
    )
    if progress is None:
        progress = UserProgress(user_id=user_id, puzzle_id=puzzle_id)
        db.add(progress)
    return progress


@router.get("", response_model=list[PuzzleSummary])
def list_puzzles(
    db: Annotated[Session, Depends(get_db)],
    cefr_level: Level | None = None,
    classroom_id: int | None = None,
) -> list[PuzzleSummary]:
    """Lista crucigramas con filtros opcionales de nivel y aula."""
    query = select(Puzzle)
    if cefr_level is not None:
        query = query.where(Puzzle.level == cefr_level)
    if classroom_id is not None:
        query = query.where(Puzzle.classroom_id == classroom_id)

    puzzles = db.scalars(query.order_by(Puzzle.id)).all()
    return [
        PuzzleSummary(
            id=puzzle.id,
            title=puzzle.title,
            theme=puzzle.theme,
            cefr_level=getattr(puzzle.level, "value", puzzle.level),
            classroom_id=puzzle.classroom_id,
        )
        for puzzle in puzzles
    ]


@router.get("/{puzzle_id}", response_model=PuzzleDetailResponse)
def get_puzzle(
    puzzle_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> PuzzleDetailResponse:
    """Devuelve grilla, tamaño, celdas bloqueadas y pistas estáticas."""
    return _to_detail(_get_puzzle_or_404(db, puzzle_id))


@router.post("/{puzzle_id}/check", response_model=CheckResultResponse)
def check_puzzle(
    puzzle_id: int,
    payload: CheckSubmit,
    db: Annotated[Session, Depends(get_db)],
) -> CheckResultResponse:
    """Verifica letras y palabras sin iniciar sesión ni guardar respuestas."""
    puzzle = _get_puzzle_or_404(db, puzzle_id)
    return check_answers(puzzle.grid_data, payload.answers)


@router.post("/{puzzle_id}/progress", response_model=ProgressResultResponse)
def submit_progress(
    puzzle_id: int,
    payload: ProgressSubmit,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProgressResultResponse:
    """Valida respuestas, guarda el progreso y devuelve feedback amable."""
    puzzle = _get_puzzle_or_404(db, puzzle_id)
    progress = _get_or_create_progress(db, current_user.id, puzzle_id)
    previous_best = progress.score or 0

    result = evaluate_progress(
        puzzle.grid_data,
        payload.answers,
        payload.hints_used,
        payload.power_mode_used,
        previous_best,
    )

    progress.is_completed = bool(progress.is_completed) or result.completed
    progress.score = result.best_score
    progress.hints_used = payload.hints_used
    progress.power_badge_earned = bool(progress.power_badge_earned) or result.power_badge_earned
    db.commit()

    return result


@router.post("/{puzzle_id}/retention", response_model=RetentionResultResponse)
def submit_retention(
    puzzle_id: int,
    payload: RetentionSubmit,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RetentionResultResponse:
    """Registra un repaso sin pistas sin alterar el progreso normal."""
    puzzle = _get_puzzle_or_404(db, puzzle_id)
    result = evaluate_progress(puzzle.grid_data, payload.answers)
    score = len(result.correct_words)

    progress = _get_or_create_progress(db, current_user.id, puzzle_id)
    progress.retention_score = score
    progress.retention_completed_at = datetime.now(timezone.utc)
    db.commit()

    return RetentionResultResponse(
        completed=result.completed,
        correct_words=result.correct_words,
        incorrect_words=result.incorrect_words,
        score=score,
        message=result.message,
    )
