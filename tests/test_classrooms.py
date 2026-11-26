from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.services.classroom_service import JOIN_CODE_ALPHABET, generate_join_code
from models import Classroom, User, student_classrooms

TEACHER_EMAIL = "profe@example.com"
STUDENT_EMAIL = "ana@example.com"
OTHER_TEACHER_EMAIL = "otra@example.com"
PASSWORD = "secreto"


def _auth_headers(
    client: TestClient,
    email: str,
    role: str = "student",
) -> dict[str, str]:
    registered = client.post(
        "/api/auth/register",
        json={"username": email, "password": PASSWORD, "role": role},
    )
    assert registered.status_code == 201

    token = client.post(
        "/api/auth/login",
        json={"username": email, "password": PASSWORD},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_classroom(
    client: TestClient,
    headers: dict[str, str],
    name: str,
    description: str | None = None,
) -> dict[str, object]:
    response = client.post(
        "/api/classrooms",
        headers=headers,
        json={"name": name, "description": description},
    )
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def test_generate_join_code_uses_safe_alphabet() -> None:
    code = generate_join_code()

    assert len(code) == 6
    assert set(code) <= set(JOIN_CODE_ALPHABET)
    assert not set(code) & set("IO01")

    with pytest.raises(ValueError):
        generate_join_code(0)


def test_teacher_creates_classroom(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client, TEACHER_EMAIL, "teacher")

    response = client.post(
        "/api/classrooms",
        headers=headers,
        json={"name": "Inglés A1", "description": "Grupo de lectoescritura"},
    )
    body = response.json()

    assert response.status_code == 201
    assert body["name"] == "Inglés A1"
    assert body["description"] == "Grupo de lectoescritura"
    assert len(body["join_code"]) == 6
    assert set(body["join_code"]) <= set(JOIN_CODE_ALPHABET)

    with session_factory() as db:
        teacher = db.scalar(select(User).where(User.email == TEACHER_EMAIL))
        classroom = db.get(Classroom, body["id"])
        assert teacher is not None
        assert classroom is not None
        assert classroom.invite_code == body["join_code"]
        assert classroom.description == "Grupo de lectoescritura"
        assert classroom.teacher_id == teacher.id


def test_student_cannot_create_classroom(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    headers = _auth_headers(client, STUDENT_EMAIL)

    response = client.post(
        "/api/classrooms",
        headers=headers,
        json={"name": "Aula prohibida"},
    )

    assert response.status_code == 403


def test_create_classroom_requires_auth(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env

    response = client.post("/api/classrooms", json={"name": "Sin token"})

    assert response.status_code == 401


def test_teacher_lists_only_own_classrooms(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    other_headers = _auth_headers(client, OTHER_TEACHER_EMAIL, "teacher")
    own = _create_classroom(client, teacher_headers, "Propias")
    _create_classroom(client, other_headers, "Ajena")

    response = client.get("/api/classrooms", headers=teacher_headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own["id"]]


def test_student_lists_only_joined_classrooms(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    student_headers = _auth_headers(client, STUDENT_EMAIL)
    joined = _create_classroom(client, teacher_headers, "Unida")
    _create_classroom(client, teacher_headers, "No unida")

    join_response = client.post(
        "/api/classrooms/join",
        headers=student_headers,
        json={"join_code": joined["join_code"]},
    )
    assert join_response.status_code == 200

    response = client.get("/api/classrooms", headers=student_headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [joined["id"]]


def test_join_classroom_normalizes_code_and_persists_membership(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    student_headers = _auth_headers(client, STUDENT_EMAIL)
    classroom = _create_classroom(client, teacher_headers, "Frutas")

    response = client.post(
        "/api/classrooms/join",
        headers=student_headers,
        json={"join_code": f"  {str(classroom['join_code']).lower()}  "},
    )

    assert response.status_code == 200
    assert response.json() == classroom

    with session_factory() as db:
        student = db.scalar(select(User).where(User.email == STUDENT_EMAIL))
        assert student is not None
        membership = db.scalar(
            select(student_classrooms.c.student_id).where(
                student_classrooms.c.student_id == student.id,
                student_classrooms.c.classroom_id == classroom["id"],
            )
        )
        assert membership == student.id


def test_join_classroom_is_idempotent(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    student_headers = _auth_headers(client, STUDENT_EMAIL)
    classroom = _create_classroom(client, teacher_headers, "Idempotente")

    first = client.post(
        "/api/classrooms/join",
        headers=student_headers,
        json={"join_code": classroom["join_code"]},
    )
    second = client.post(
        "/api/classrooms/join",
        headers=student_headers,
        json={"join_code": classroom["join_code"]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == classroom

    with session_factory() as db:
        student = db.scalar(select(User).where(User.email == STUDENT_EMAIL))
        assert student is not None
        rows = db.execute(
            select(student_classrooms.c.student_id).where(
                student_classrooms.c.student_id == student.id,
                student_classrooms.c.classroom_id == classroom["id"],
            )
        ).all()
        assert len(rows) == 1


@pytest.mark.parametrize("code", ["NOEXISTE", "I0O1!!"])
def test_join_unknown_or_invalid_code_returns_404(
    test_env: tuple[TestClient, sessionmaker[Session]],
    code: str,
) -> None:
    client, _ = test_env
    headers = _auth_headers(client, STUDENT_EMAIL)

    response = client.post(
        "/api/classrooms/join",
        headers=headers,
        json={"join_code": code},
    )

    assert response.status_code == 404


def test_join_classroom_requires_auth(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    classroom = _create_classroom(client, teacher_headers, "Privada")

    response = client.post(
        "/api/classrooms/join",
        json={"join_code": classroom["join_code"]},
    )

    assert response.status_code == 401
