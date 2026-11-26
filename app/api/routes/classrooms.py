from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_teacher
from app.db.database import get_db
from app.schemas.classroom import ClassroomCreate, ClassroomJoin, ClassroomResponse
from app.services.classroom_service import generate_join_code
from models import Classroom, User, UserRole, student_classrooms

router = APIRouter()
MAX_CODE_ATTEMPTS = 10


def _is_teacher(user: User) -> bool:
    """Compara el rol del usuario sin depender del tipo ORM/str."""
    role = getattr(user.role, "value", user.role)
    return role == UserRole.TEACHER.value


def _to_response(classroom: Classroom) -> ClassroomResponse:
    """Mapea el modelo al contrato público usando join_code."""
    return ClassroomResponse(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        join_code=classroom.invite_code,
        teacher_id=classroom.teacher_id,
    )


def _generate_unique_code(db: Session) -> str:
    """Busca un código disponible antes de asignarlo al aula."""
    for _ in range(MAX_CODE_ATTEMPTS):
        code = generate_join_code()
        existing = db.scalar(select(Classroom.id).where(Classroom.invite_code == code))
        if existing is None:
            return code
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="No se pudo generar un código de aula único.",
    )


@router.post(
    "",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_classroom(
    payload: ClassroomCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_teacher)],
) -> ClassroomResponse:
    """Crea un aula docente con un código de unión único."""
    classroom = Classroom(
        name=payload.name,
        description=payload.description,
        invite_code=_generate_unique_code(db),
        teacher_id=current_user.id,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return _to_response(classroom)


@router.get("", response_model=list[ClassroomResponse])
def list_classrooms(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ClassroomResponse]:
    """Lista las aulas creadas por docentes o las uniones del estudiante."""
    if _is_teacher(current_user):
        classrooms = db.scalars(
            select(Classroom)
            .where(Classroom.teacher_id == current_user.id)
            .order_by(Classroom.id)
        ).all()
    else:
        classrooms = db.scalars(
            select(Classroom)
            .join(
                student_classrooms,
                student_classrooms.c.classroom_id == Classroom.id,
            )
            .where(student_classrooms.c.student_id == current_user.id)
            .order_by(Classroom.id)
        ).all()
    return [_to_response(classroom) for classroom in classrooms]


@router.post("/join", response_model=ClassroomResponse)
def join_classroom(
    payload: ClassroomJoin,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ClassroomResponse:
    """Une al usuario a un aula; repetir la llamada no crea duplicados."""
    classroom = db.scalar(
        select(Classroom).where(Classroom.invite_code == payload.join_code)
    )
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de aula no encontrado.",
        )

    membership = db.scalar(
        select(student_classrooms.c.student_id).where(
            student_classrooms.c.student_id == current_user.id,
            student_classrooms.c.classroom_id == classroom.id,
        )
    )
    if membership is None:
        db.execute(
            student_classrooms.insert().values(
                student_id=current_user.id,
                classroom_id=classroom.id,
            )
        )
        db.commit()

    return _to_response(classroom)
