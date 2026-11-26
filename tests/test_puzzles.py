from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from models import Level, Puzzle, UserProgress


def _grid_data() -> dict[str, object]:
    return {
        "grid_size": {"rows": 5, "cols": 5},
        "blocked_cells": [[0, 1], [2, 3]],
        "clues": [
            {
                "number": 1,
                "direction": "across",
                "clue_text": "Fruit",
                "static_hint": "A red fruit",
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


def _seed_puzzle(
    session_factory: sessionmaker[Session],
    *,
    title: str = "Frutas",
    level: Level = Level.A1,
    classroom_id: int | None = None,
) -> int:
    with session_factory() as db:
        puzzle = Puzzle(
            title=title,
            theme="Día Soleado",
            level=level,
            grid_data=_grid_data(),
            classroom_id=classroom_id,
        )
        db.add(puzzle)
        db.commit()
        db.refresh(puzzle)
        return int(puzzle.id)


def _auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={"username": "ana@example.com", "password": "secreto"},
    )
    token = client.post(
        "/api/auth/login",
        json={"username": "ana@example.com", "password": "secreto"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_puzzles(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    puzzle_id = _seed_puzzle(session_factory)

    response = client.get("/api/puzzles")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": puzzle_id,
            "title": "Frutas",
            "theme": "Día Soleado",
            "cefr_level": "A1",
            "classroom_id": None,
        }
    ]


def test_list_puzzles_filters_by_level_and_classroom(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    _seed_puzzle(session_factory, title="General")
    _seed_puzzle(
        session_factory,
        title="Grupo B1",
        level=Level.B1,
        classroom_id=42,
    )

    response = client.get(
        "/api/puzzles",
        params={"cefr_level": "B1", "classroom_id": 42},
    )

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Grupo B1"]


def test_puzzle_detail_hides_answers(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    puzzle_id = _seed_puzzle(session_factory)

    response = client.get(f"/api/puzzles/{puzzle_id}")
    body = response.json()

    assert response.status_code == 200
    assert body["grid_size"] == {"rows": 5, "cols": 5}
    assert body["blocked_cells"] == [[0, 1], [2, 3]]
    assert len(body["clues"]) == 2
    assert body["clues"][0]["static_hint"] == "A red fruit"
    assert all("answer" not in clue for clue in body["clues"])
    assert "solutions" not in body


def test_puzzle_detail_missing_returns_404(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_env

    response = client.get("/api/puzzles/999")

    assert response.status_code == 404


def test_progress_requires_auth(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    puzzle_id = _seed_puzzle(session_factory)

    response = client.post(
        f"/api/puzzles/{puzzle_id}/progress",
        json={
            "answers": {"1_across": "APPLE", "2_down": "GIVE UP"},
            "power_mode_used": False,
            "hints_used": 1,
        },
    )

    assert response.status_code == 401


def test_progress_normal_mode_persists(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client)
    puzzle_id = _seed_puzzle(session_factory)

    response = client.post(
        f"/api/puzzles/{puzzle_id}/progress",
        headers=headers,
        json={
            "answers": {"1_across": "APPLE", "2_down": "GIVE UP"},
            "power_mode_used": False,
            "hints_used": 1,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["completed"] is True
    assert body["power_badge_earned"] is False

    with session_factory() as db:
        progress = db.scalar(
            select(UserProgress).where(UserProgress.puzzle_id == puzzle_id)
        )
        assert progress is not None
        assert progress.score == 2
        assert progress.hints_used == 1
        assert progress.power_badge_earned is False


def test_progress_power_mode_earns_badge(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client)
    puzzle_id = _seed_puzzle(session_factory)

    response = client.post(
        f"/api/puzzles/{puzzle_id}/progress",
        headers=headers,
        json={
            "answers": {"1_across": "APPLE", "2_down": "GIVE UP"},
            "power_mode_used": True,
            "hints_used": 0,
        },
    )

    assert response.status_code == 200
    assert response.json()["power_badge_earned"] is True

    with session_factory() as db:
        progress = db.scalar(
            select(UserProgress).where(UserProgress.puzzle_id == puzzle_id)
        )
        assert progress is not None
        assert progress.power_badge_earned is True


def test_progress_with_wrong_answers_is_encouraging(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = test_env
    headers = _auth_headers(client)
    puzzle_id = _seed_puzzle(session_factory)

    response = client.post(
        f"/api/puzzles/{puzzle_id}/progress",
        headers=headers,
        json={
            "answers": {"1_across": "APPLE", "2_down": "WRONG"},
            "power_mode_used": False,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["completed"] is False
    assert body["incorrect_words"] == ["2_down"]
    assert "sin prisa" in body["message"]
