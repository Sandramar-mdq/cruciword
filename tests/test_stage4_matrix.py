from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from test_frontend import _contrast, _token
from test_grid_navigation import crossing_puzzle, gapped_puzzle, run_navigation
from test_instant_check import run_check
from test_virtual_keyboard import run_keyboard

from app.main import app


def edge_puzzle() -> dict[str, Any]:
    return {
        "grid_size": {"rows": 3, "cols": 3},
        "words": [
            {
                "id": 1,
                "key": "1_across",
                "word": "CAT",
                "clue": "Gato",
                "clueNumber": 1,
                "row": 0,
                "col": 0,
                "direction": "horizontal",
                "length": 3,
            },
            {
                "id": 2,
                "key": "2_down",
                "word": "CAR",
                "clue": "Coche",
                "clueNumber": 2,
                "row": 0,
                "col": 2,
                "direction": "vertical",
                "length": 3,
            },
        ],
    }


def covers(word: dict[str, Any], row: int, col: int) -> bool:
    last_row = word["row"] + (word["length"] - 1 if word["direction"] == "vertical" else 0)
    last_col = word["col"] + (word["length"] - 1 if word["direction"] == "horizontal" else 0)
    return word["row"] <= row <= last_row and word["col"] <= col <= last_col


def positions(states: list[dict[str, Any]]) -> list[tuple[int, int]]:
    return [(state["row"], state["col"]) for state in states]


def test_matrix_intersection_and_direction_toggle() -> None:
    puzzle = crossing_puzzle()
    shared = {word["key"] for word in puzzle["words"] if covers(word, 0, 0)}

    assert shared == {"1_across", "2_down"}

    result = run_navigation(
        puzzle,
        [
            {"type": "selectCell", "row": 0, "col": 0},
            {"type": "toggle"},
            {"type": "toggle"},
        ],
    )

    assert [(state["key"], state["direction"]) for state in result["states"]] == [
        ("1_across", "horizontal"),
        ("2_down", "vertical"),
        ("1_across", "horizontal"),
    ]
    assert positions(result["states"]) == [(0, 0), (0, 0), (0, 0)]


def test_matrix_grid_edges_and_blocked_cells() -> None:
    blocked = run_navigation(
        gapped_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 1},
            {"type": "move", "key": "ArrowRight"},
        ],
    )

    assert positions(blocked["states"])[1] == (0, 4)
    assert blocked["states"][1]["key"] == "3_across"

    edges = run_navigation(
        edge_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 2},
            {"type": "move", "key": "ArrowRight"},
            {"type": "move", "key": "ArrowUp"},
            {"type": "toggle"},
            {"type": "move", "key": "ArrowDown"},
            {"type": "move", "key": "ArrowDown"},
            {"type": "move", "key": "ArrowDown"},
        ],
    )

    assert positions(edges["states"]) == [
        (0, 2),
        (0, 2),
        (0, 2),
        (0, 2),
        (1, 2),
        (2, 2),
        (2, 2),
    ]
    assert edges["states"][-1]["direction"] == "vertical"
    assert edges["states"][-1]["key"] == "2_down"


def test_matrix_physical_and_virtual_keyboard_share_one_dispatch() -> None:
    result = run_keyboard()

    assert result["calls"] == {
        "toggle": 3,
        "check": 1,
        "write": 1,
        "erase": 1,
        "move": 1,
    }
    assert result["letterPrevented"] is True
    assert result["backspacePrevented"] is True
    assert result["tabInsidePrevented"] is True
    assert result["tabOutsidePrevented"] is False

    with TestClient(app) as client:
        script = client.get("/static/js/keyboard.js").text

    assert script.count('addEventListener("keydown"') == 1
    assert "keypress" not in script
    assert "keyup" not in script
    assert "data-key-action" in script


def test_matrix_feedback_states_are_aaa_and_not_red() -> None:
    checked = run_check()["afterCheck"]

    assert checked["correctCell"] is True
    assert checked["reviewCell"] is True
    assert checked["neutralEmptyCell"] is True
    assert checked["statusKind"] == "cw-feedback cw-feedback--review"

    with TestClient(app) as client:
        css = client.get("/static/css/themes.css").text

    feedback = css.split(".cw-feedback--success", 1)[1].split(".cw-clue-list", 1)[0]
    success = _token(css, "cw-success")
    success_ink = _token(css, "cw-success-contrast")
    review = _token(css, "cw-review")
    review_ink = _token(css, "cw-review-contrast")

    assert _contrast(success, success_ink) >= 7
    assert _contrast(review, review_ink) >= 7
    for red in ("#ff0000", "#dc2626", "#ef4444", "#f87171", "red"):
        assert red not in feedback.lower()


def test_stage4_smoke_assets_and_exposed_apis() -> None:
    modules = ("grid-engine.js", "board.js", "navigation.js", "keyboard.js")

    with TestClient(app) as client:
        html = client.get("/").text
        css = client.get("/static/css/themes.css").text
        service_worker = client.get("/static/sw.js").text
        scripts = {name: client.get("/static/js/" + name).text for name in modules}

        assert client.get("/").status_code == 200
        assert client.get("/static/css/themes.css").status_code == 200
        assert client.get("/static/sw.js").status_code == 200
        for name in modules:
            assert client.get("/static/js/" + name).status_code == 200

    for name in modules:
        assert 'src="/static/js/' + name + '"' in html
    assert html.index('src="/static/js/grid-engine.js"') < html.index('src="/static/js/board.js"')
    assert html.index('src="/static/js/board.js"') < html.index('src="/static/js/navigation.js"')
    assert html.index('src="/static/js/navigation.js"') < html.index('src="/static/js/keyboard.js"')

    assert "cruciword-static-v6" in service_worker
    for name in modules:
        assert "/static/js/" + name in service_worker

    assert "--cw-success: #d1fae5;" in css
    assert "--cw-review: #fef3c7;" in css
    assert "createNavigator" in scripts["grid-engine.js"]
    assert "window.CruciNavigation" in scripts["navigation.js"]
    assert "window.CruciBoard" in scripts["board.js"]
    assert "window.CruciKeyboard" in scripts["keyboard.js"]
    for name in ("grid-engine.js", "navigation.js", "keyboard.js"):
        assert "https://" not in scripts[name]
