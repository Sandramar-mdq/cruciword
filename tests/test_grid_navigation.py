from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app

ENGINE = Path(__file__).resolve().parents[1] / "static" / "js" / "grid-engine.js"

NODE_HARNESS = r"""
const engine = require(process.argv[1]);
const payload = JSON.parse(process.argv[2]);
const model = engine.buildGridModel(payload.puzzle);
const navigator = engine.createNavigator(model, { letters: payload.letters || {} });

const states = payload.operations.map(function (operation) {
  if (operation.type === "selectCell") {
    return navigator.selectCell(operation.row, operation.col, {
      toggle: operation.toggle === true
    });
  }
  if (operation.type === "selectClue") {
    return navigator.selectClue(operation.key);
  }
  if (operation.type === "toggle") {
    return navigator.toggleDirection();
  }
  if (operation.type === "write") {
    return navigator.writeLetter(operation.letter).state;
  }
  if (operation.type === "erase") {
    return navigator.eraseLetter().state;
  }
  if (operation.type === "move") {
    return navigator.move(operation.key);
  }
  if (operation.type === "answers") {
    return navigator.getAnswers();
  }
  throw new Error("Operación desconocida: " + operation.type);
});

console.log(JSON.stringify({
  states: states,
  final: navigator.getState(),
  answers: navigator.getAnswers(),
  letters: navigator.getLetters()
}));
"""


def run_navigation(
    puzzle: dict[str, Any],
    operations: list[dict[str, Any]],
    letters: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = {"puzzle": puzzle, "operations": operations, "letters": letters or {}}
    process = subprocess.run(
        ["node", "-e", NODE_HARNESS, str(ENGINE), json.dumps(payload)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def crossing_puzzle() -> dict[str, Any]:
    return {
        "grid_size": {"rows": 5, "cols": 5},
        "words": [
            {
                "id": 1,
                "key": "1_across",
                "word": "APPLE",
                "clue": "Fruta",
                "clueNumber": 1,
                "row": 0,
                "col": 0,
                "direction": "horizontal",
                "length": 5,
            },
            {
                "id": 2,
                "key": "2_down",
                "word": "CAT",
                "clue": "Animal",
                "clueNumber": 2,
                "row": 0,
                "col": 0,
                "direction": "vertical",
                "length": 3,
            },
        ],
    }


def gapped_puzzle() -> dict[str, Any]:
    return {
        "grid_size": {"rows": 3, "cols": 6},
        "words": [
            {
                "id": 1,
                "key": "1_across",
                "word": "HI",
                "clue": "Saludo",
                "clueNumber": 1,
                "row": 0,
                "col": 0,
                "direction": "horizontal",
                "length": 2,
            },
            {
                "id": 2,
                "key": "2_down",
                "word": "CAT",
                "clue": "Animal",
                "clueNumber": 2,
                "row": 0,
                "col": 0,
                "direction": "vertical",
                "length": 3,
            },
            {
                "id": 3,
                "key": "3_across",
                "word": "GO",
                "clue": "Salir",
                "clueNumber": 3,
                "row": 0,
                "col": 4,
                "direction": "horizontal",
                "length": 2,
            },
        ],
    }


def position(state: dict[str, Any]) -> tuple[int, int]:
    return state["row"], state["col"]


def test_clicking_cell_selects_word_and_toggles_crossing_direction() -> None:
    result = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 0, "toggle": True},
            {"type": "selectCell", "row": 0, "col": 0, "toggle": True},
            {"type": "selectCell", "row": 0, "col": 0, "toggle": True},
        ],
    )

    assert [state["direction"] for state in result["states"]] == [
        "horizontal",
        "vertical",
        "horizontal",
    ]
    assert [state["key"] for state in result["states"]] == [
        "1_across",
        "2_down",
        "1_across",
    ]
    assert all(position(state) == (0, 0) for state in result["states"])


def test_toggle_direction_switches_words_at_crossing() -> None:
    result = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 0},
            {"type": "toggle"},
        ],
    )

    assert result["states"][0]["direction"] == "horizontal"
    assert result["states"][1]["direction"] == "vertical"
    assert result["states"][1]["key"] == "2_down"
    assert position(result["states"][1]) == (0, 0)


def test_toggle_direction_is_safe_outside_crossings() -> None:
    result = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 2},
            {"type": "toggle"},
        ],
    )

    assert result["states"][1]["key"] == "1_across"
    assert result["states"][1]["direction"] == "horizontal"
    assert position(result["states"][1]) == (0, 2)


def test_typing_advances_to_next_empty_cell_of_active_word() -> None:
    result = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 0},
            {"type": "write", "letter": "a"},
        ],
        letters={"0:1": "X"},
    )

    assert result["letters"]["0:0"] == "A"
    assert position(result["states"][1]) == (0, 2)
    assert result["states"][1]["index"] == 2


def test_backspace_clears_current_cell_and_then_previous_cell() -> None:
    current = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 1},
            {"type": "erase"},
        ],
        letters={"0:1": "P"},
    )

    assert position(current["states"][1]) == (0, 1)
    assert "0:1" not in current["letters"]

    previous = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 2},
            {"type": "erase"},
        ],
        letters={"0:1": "P"},
    )

    assert position(previous["states"][1]) == (0, 1)
    assert "0:1" not in previous["letters"]


def test_arrows_skip_blocked_cells_and_adjust_active_direction() -> None:
    result = run_navigation(
        gapped_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 1},
            {"type": "move", "key": "ArrowRight"},
            {"type": "selectClue", "key": "2_down"},
            {"type": "move", "key": "ArrowDown"},
        ],
    )

    assert position(result["states"][1]) == (0, 4)
    assert result["states"][1]["direction"] == "horizontal"
    assert result["states"][1]["key"] == "3_across"
    assert position(result["states"][3]) == (1, 0)
    assert result["states"][3]["direction"] == "vertical"
    assert result["states"][3]["key"] == "2_down"


def test_clue_click_positions_cursor_at_first_cell() -> None:
    result = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectCell", "row": 0, "col": 3},
            {"type": "selectClue", "key": "2_down"},
        ],
    )

    assert position(result["states"][1]) == (0, 0)
    assert result["states"][1]["index"] == 0
    assert result["states"][1]["direction"] == "vertical"
    assert result["states"][1]["key"] == "2_down"


def test_answers_are_grouped_by_clue_key() -> None:
    result = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectClue", "key": "1_across"},
            {"type": "write", "letter": "A"},
            {"type": "write", "letter": "P"},
            {"type": "write", "letter": "P"},
            {"type": "write", "letter": "L"},
            {"type": "write", "letter": "E"},
        ],
    )

    assert result["answers"]["1_across"] == "APPLE"
    assert result["answers"]["2_down"] == "A"


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("ArrowLeft", (0, 0)),
        ("ArrowUp", (0, 0)),
    ],
)
def test_arrows_do_not_leave_the_grid(key: str, expected: tuple[int, int]) -> None:
    result = run_navigation(
        crossing_puzzle(),
        [
            {"type": "selectClue", "key": "1_across"},
            {"type": "move", "key": key},
        ],
    )

    assert position(result["states"][1]) == expected


def test_navigation_assets_are_served_and_registered() -> None:
    with TestClient(app) as client:
        html = client.get("/").text
        css = client.get("/static/css/themes.css").text
        script = client.get("/static/sw.js").text
        engine = client.get("/static/js/grid-engine.js").text
        navigation = client.get("/static/js/navigation.js").text

    assert "/static/js/grid-engine.js" in html
    assert "/static/js/navigation.js" in html
    assert html.index("grid-engine.js") < html.index("board.js")
    assert html.index("board.js") < html.index("navigation.js")
    assert ".cw-cell--word" in css
    assert "/static/js/grid-engine.js" in script
    assert "/static/js/navigation.js" in script
    assert "createNavigator" in engine
    assert "cruciword:gridchange" in navigation
    assert "https://" not in engine
    assert "https://" not in navigation
