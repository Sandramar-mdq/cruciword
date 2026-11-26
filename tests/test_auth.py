from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import require_teacher
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from models import User, UserRole

STUDENT_EMAIL = "ana@example.com"
TEACHER_EMAIL = "profesor@example.com"
PASSWORD = "secreto"


def _register(
    client: TestClient,
    email: str = STUDENT_EMAIL,
    password: str = PASSWORD,
    role: str = "student",
):
    return client.post(
        "/api/auth/register",
        json={"username": email, "password": password, "role": role},
    )


def _login(
    client: TestClient,
    email: str = STUDENT_EMAIL,
    password: str = PASSWORD,
):
    return client.post(
        "/api/auth/login",
        json={"username": email, "password": password},
    )


def test_password_hash_roundtrip() -> None:
    hashed = hash_password(PASSWORD)

    assert hashed != PASSWORD
    assert verify_password(PASSWORD, hashed) is True
    assert verify_password("incorrecta", hashed) is False


def test_access_token_roundtrip() -> None:
    token = create_access_token(
        {"sub": TEACHER_EMAIL, "role": "teacher"},
        expires_delta=timedelta(minutes=5),
    )

    payload = decode_access_token(token)

    assert payload.sub == TEACHER_EMAIL
    assert payload.role == "teacher"


def test_expired_access_token_is_rejected() -> None:
    token = create_access_token(
        {"sub": STUDENT_EMAIL},
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_register_student(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env

    response = _register(client)
    body = response.json()

    assert response.status_code == 201
    assert body["username"] == STUDENT_EMAIL
    assert body["role"] == "student"
    assert "hashed_password" not in body

    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == STUDENT_EMAIL))
        assert user is not None
        assert user.hashed_password != PASSWORD
        assert verify_password(PASSWORD, user.hashed_password) is True


def test_register_teacher(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env

    response = _register(client, email=TEACHER_EMAIL, role="teacher")

    assert response.status_code == 201
    assert response.json()["role"] == "teacher"


def test_register_duplicate_is_rejected(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    _register(client)

    response = _register(client)

    assert response.status_code == 409


def test_login_success(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    _register(client)

    response = _login(client)
    body = response.json()

    assert response.status_code == 200
    assert body["token_type"] == "bearer"

    payload = decode_access_token(body["access_token"])
    assert payload.sub == STUDENT_EMAIL
    assert payload.role == "student"


def test_login_wrong_password_is_rejected(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    _register(client)

    response = _login(client, password="incorrecta")

    assert response.status_code == 401


def test_login_unknown_user_is_rejected(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env

    response = _login(client, email="desconocido@example.com")

    assert response.status_code == 401


def test_me_with_valid_token(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    _register(client)
    token = _login(client).json()["access_token"]

    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == STUDENT_EMAIL
    assert response.json()["role"] == "student"


def test_me_without_token_is_rejected(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env

    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_me_with_invalid_token_is_rejected(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env

    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert response.status_code == 401


def test_require_teacher_allows_teacher() -> None:
    teacher = User(
        email=TEACHER_EMAIL,
        hashed_password="hash",
        role=UserRole.TEACHER,
    )

    assert require_teacher(teacher) is teacher


def test_require_teacher_rejects_student() -> None:
    student = User(
        email=STUDENT_EMAIL,
        hashed_password="hash",
        role=UserRole.STUDENT,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_teacher(student)

    assert exc_info.value.status_code == 403
