from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from models import Level, User, Word, WordList, word_list_words

TEACHER_EMAIL = "profe-listas@example.com"
STUDENT_EMAIL = "ana-listas@example.com"
OTHER_EMAIL = "otra-listas@example.com"
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


def _create_classroom(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/classrooms",
        headers=headers,
        json={"name": "Inglés A1", "description": "Grupo base"},
    )
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def _seed_word(
    session_factory: sessionmaker[Session],
    word: str,
    translation: str,
) -> int:
    with session_factory() as db:
        item = Word(
            word=word,
            translation=translation,
            level=Level.A1,
            theme="Daily life",
            definition_en=f"Definition of {word}.",
            synonym_hint=f"hint for {word}",
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return int(item.id)


def test_teacher_creates_word_list_with_existing_words(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    classroom = _create_classroom(client, headers)
    apple_id = _seed_word(session_factory, "APPLE", "manzana")
    book_id = _seed_word(session_factory, "BOOK", "libro")

    response = client.post(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=headers,
        json={
            "name": "Frutas y lectura",
            "description": "Lista personalizada",
            "word_ids": [apple_id, book_id],
        },
    )
    body = response.json()

    assert response.status_code == 201
    assert body["classroom_id"] == classroom["id"]
    assert body["teacher_id"] > 0
    assert [item["word"] for item in body["words"]] == ["APPLE", "BOOK"]

    with session_factory() as db:
        teacher = db.scalar(select(User).where(User.email == TEACHER_EMAIL))
        stored = db.scalar(select(WordList).where(WordList.id == body["id"]))
        associations = db.execute(
            select(word_list_words).where(word_list_words.c.word_list_id == body["id"])
        ).all()
        assert teacher is not None
        assert stored is not None
        assert stored.teacher_id == teacher.id
        assert len(associations) == 2


def test_word_ids_are_deduplicated_and_missing_ids_return_404(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    classroom = _create_classroom(client, headers)
    word_id = _seed_word(session_factory, "APPLE", "manzana")

    duplicated = client.post(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=headers,
        json={"name": "Sin duplicados", "word_ids": [word_id, word_id]},
    )
    missing = client.post(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=headers,
        json={"name": "Con falta", "word_ids": [999999]},
    )

    assert duplicated.status_code == 201
    assert len(duplicated.json()["words"]) == 1
    assert missing.status_code == 404


def test_student_cannot_create_word_list(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    student_headers = _auth_headers(client, STUDENT_EMAIL)
    classroom = _create_classroom(client, teacher_headers)

    response = client.post(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=student_headers,
        json={"name": "Prohibida"},
    )

    assert response.status_code == 403


def test_other_teacher_cannot_create_in_foreign_classroom(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    owner_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    other_headers = _auth_headers(client, OTHER_EMAIL, "teacher")
    classroom = _create_classroom(client, owner_headers)

    response = client.post(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=other_headers,
        json={"name": "Ajena"},
    )

    assert response.status_code == 404


def test_enrolled_student_can_list_and_read_word_lists(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    student_headers = _auth_headers(client, STUDENT_EMAIL)
    classroom = _create_classroom(client, teacher_headers)
    word_id = _seed_word(session_factory, "APPLE", "manzana")

    created = client.post(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=teacher_headers,
        json={"name": "Visible", "word_ids": [word_id]},
    ).json()
    joined = client.post(
        "/api/classrooms/join",
        headers=student_headers,
        json={"join_code": classroom["join_code"]},
    )
    assert joined.status_code == 200

    listed = client.get(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=student_headers,
    )
    detail = client.get(
        f"/api/word-lists/{created['id']}",
        headers=student_headers,
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created["id"]]
    assert detail.status_code == 200
    assert detail.json()["words"][0]["word"] == "APPLE"


def test_student_outside_classroom_cannot_see_word_lists(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    teacher_headers = _auth_headers(client, TEACHER_EMAIL, "teacher")
    student_headers = _auth_headers(client, STUDENT_EMAIL)
    classroom = _create_classroom(client, teacher_headers)
    word_id = _seed_word(session_factory, "APPLE", "manzana")

    created = client.post(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=teacher_headers,
        json={"name": "Privada", "word_ids": [word_id]},
    ).json()

    listed = client.get(
        f"/api/classrooms/{classroom['id']}/word-lists",
        headers=student_headers,
    )
    detail = client.get(
        f"/api/word-lists/{created['id']}",
        headers=student_headers,
    )

    assert listed.status_code == 404
    assert detail.status_code == 404


def test_word_list_endpoints_require_auth(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env

    response = client.get("/api/classrooms/1/word-lists")

    assert response.status_code == 401
