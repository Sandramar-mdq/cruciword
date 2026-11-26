from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_teacher
from app.db.database import get_db
from app.schemas.word_list import WordListCreate, WordListResponse, WordSummary
from models import Classroom, User, UserRole, Word, WordList, student_classrooms

router = APIRouter()


def _is_teacher(user: User) -> bool:
    """Compara el rol sin depender del tipo ORM/str."""
    role = getattr(user.role, "value", user.role)
    return role == UserRole.TEACHER.value


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Aula o lista no encontrada.",
    )


def _resolve_words(db: Session, word_ids: list[int]) -> list[Word]:
    """Devuelve palabras existentes en el orden solicitado."""
    if not word_ids:
        return []

    found = {
        word.id: word
        for word in db.scalars(select(Word).where(Word.id.in_(word_ids))).all()
    }
    missing = [word_id for word_id in word_ids if word_id not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Palabras no encontradas: {missing}.",
        )
    return [found[word_id] for word_id in word_ids]


def _get_owned_classroom(
    db: Session,
    classroom_id: int,
    teacher_id: int,
) -> Classroom:
    """Devuelve un aula solo si pertenece al docente autenticado."""
    classroom = db.scalar(
        select(Classroom).where(
            Classroom.id == classroom_id,
            Classroom.teacher_id == teacher_id,
        )
    )
    if classroom is None:
        raise _not_found()
    return classroom


def _has_classroom_access(db: Session, classroom_id: int, user: User) -> bool:
    """Verifica propiedad docente o pertenencia estudiantil."""
    if _is_teacher(user):
        return (
            db.scalar(
                select(Classroom.id).where(
                    Classroom.id == classroom_id,
                    Classroom.teacher_id == user.id,
                )
            )
            is not None
        )
    return (
        db.scalar(
            select(student_classrooms.c.student_id).where(
                student_classrooms.c.classroom_id == classroom_id,
                student_classrooms.c.student_id == user.id,
            )
        )
        is not None
    )


def _to_response(word_list: WordList) -> WordListResponse:
    """Convierte la lista ORM y sus palabras al contrato público."""
    words = sorted(word_list.words, key=lambda word: word.id)
    return WordListResponse(
        id=word_list.id,
        name=word_list.name,
        description=word_list.description,
        classroom_id=word_list.classroom_id,
        teacher_id=word_list.teacher_id,
        words=[
            WordSummary(
                id=word.id,
                word=word.word,
                translation=word.translation,
                level=getattr(word.level, "value", word.level),
                theme=word.theme,
                definition_en=word.definition_en,
                synonym_hint=word.synonym_hint,
                is_power=word.is_power,
            )
            for word in words
        ],
    )


@router.post(
    "/classrooms/{classroom_id}/word-lists",
    response_model=WordListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_word_list(
    classroom_id: int,
    payload: WordListCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_teacher)],
) -> WordListResponse:
    """Crea una lista docente y la asocia a un aula propia."""
    classroom = _get_owned_classroom(db, classroom_id, current_user.id)
    word_list = WordList(
        name=payload.name,
        description=payload.description,
        teacher_id=current_user.id,
        classroom_id=classroom.id,
        words=_resolve_words(db, payload.word_ids),
    )
    db.add(word_list)
    db.commit()
    db.refresh(word_list)
    return _to_response(word_list)


@router.get(
    "/classrooms/{classroom_id}/word-lists",
    response_model=list[WordListResponse],
)
def list_word_lists(
    classroom_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[WordListResponse]:
    """Lista las listas visibles del aula para docente o alumno vinculado."""
    if not _has_classroom_access(db, classroom_id, current_user):
        raise _not_found()

    word_lists = db.scalars(
        select(WordList)
        .where(WordList.classroom_id == classroom_id)
        .order_by(WordList.id)
    ).all()
    return [_to_response(word_list) for word_list in word_lists]


@router.get("/word-lists/{word_list_id}", response_model=WordListResponse)
def get_word_list(
    word_list_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WordListResponse:
    """Devuelve una lista personalizada accesible al usuario."""
    word_list = db.get(WordList, word_list_id)
    if word_list is None:
        raise _not_found()

    if _is_teacher(current_user):
        if word_list.teacher_id != current_user.id:
            raise _not_found()
    elif word_list.classroom_id is None or not _has_classroom_access(
        db, word_list.classroom_id, current_user
    ):
        raise _not_found()

    return _to_response(word_list)
