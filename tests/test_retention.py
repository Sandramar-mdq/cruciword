from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from models import Puzzle, UserProgress

STUDENT_EMAIL = "ana-retencion@example.com"
PASSWORD = "secreto"


def _grid_data() -> dict[str, object]:
    return {
        "grid_size": {"rows": 5, "cols": 5},
        "blocked_cells": [],
        "clues": [
            {
                "number": 1,
                "direction": "across",
                "clue_text": "Fruit",
                "static_hint": "red fruit",
                "audio_url": None,
                "length": 5,
                "answer": "APPLE",
            },
            {
                "number": 2,
                "direction": "down",
                "clue_text": "Orbit",
                "static_hint": None,
                "audio_url": None,
                "length": 7,
                "answer": "GIVE UP",
            },
        ],
        "solutions": {"1_across": "APPLE", "2_down": "GIVE UP"},
    }


def _seed_puzzle(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as db:
        puzzle = Puzzle(
            title="Repaso",
            theme="Daily life",
            level="A1",
            grid_data=_grid_data(),
        )
        db.add(puzzle)
        db.commit()
        db.refresh(puzzle)
        return int(puzzle.id)


def _auth_headers(client: TestClient) -> dict[str, str]:
    registered = client.post(
        "/api/auth/register",
        json={"username": STUDENT_EMAIL, "password": PASSWORD},
    )
    assert registered.status_code == 201

    token = client.post(
        "/api/auth/login",
        json={"username": STUDENT_EMAIL, "password": PASSWORD},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_retention_records_score_without_overwriting_normal_progress(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client)
    puzzle_id = _seed_puzzle(session_factory)

    client.post(
        f"/api/puzzles/{puzzle_id}/progress",
        headers=headers,
        json={
            "answers": {"1_across": "APPLE", "2_down": "WRONG"},
            "power_mode_used": True,
            "hints_used": 3,
        },
    )

    response = client.post(
        f"/api/puzzles/{puzzle_id}/retention",
        headers=headers,
        json={"answers": {"1_across": " apple ", "2_down": "give   up"}},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["completed"] is True
    assert body["score"] == 2
    assert body["incorrect_words"] == []
    assert "¡Muy bien!" in body["message"]

    with session_factory() as db:
        progress = db.scalar(select(UserProgress))
        assert progress is not None
        assert progress.retention_score == 2
        assert progress.retention_completed_at is not None
        assert progress.score == 1
        assert progress.hints_used == 3
        assert progress.power_badge_earned is False


def test_retention_is_repeatable_and_keeps_one_progress_row(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client)
    puzzle_id = _seed_puzzle(session_factory)

    first = client.post(
        f"/api/puzzles/{puzzle_id}/retention",
        headers=headers,
        json={"answers": {"1_across": "APPLE"}},
    )
    second = client.post(
        f"/api/puzzles/{puzzle_id}/retention",
        headers=headers,
        json={"answers": {"1_across": "APPLE", "2_down": "GIVE UP"}},
    )

    assert first.status_code == 200
    assert first.json()["score"] == 1
    assert second.status_code == 200
    assert second.json()["score"] == 2

    with session_factory() as db:
        rows = db.scalars(select(UserProgress)).all()
        assert len(rows) == 1
        assert rows[0].retention_score == 2


def test_retention_with_errors_returns_encouraging_feedback(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client)
    puzzle_id = _seed_puzzle(session_factory)

    response = client.post(
        f"/api/puzzles/{puzzle_id}/retention",
        headers=headers,
        json={"answers": {"1_across": "APPLE", "2_down": "WRONG"}},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["completed"] is False
    assert body["score"] == 1
    assert body["incorrect_words"] == ["2_down"]
    assert "sin prisa" in body["message"]


def test_retention_missing_puzzle_returns_404(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env
    headers = _auth_headers(client)

    response = client.post(
        "/api/puzzles/999/retention",
        headers=headers,
        json={"answers": {}},
    )

    assert response.status_code == 404


def test_retention_requires_auth(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    puzzle_id = _seed_puzzle(session_factory)

    response = client.post(
        f"/api/puzzles/{puzzle_id}/retention",
        json={"answers": {}},
    )

    assert response.status_code == 401
