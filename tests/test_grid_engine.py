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

function makeElement(tag) {
  const element = {
    tagName: tag.toUpperCase(),
    children: [],
    attributes: {},
    style: {},
    className: "",
    textContent: "",
    type: "",
    setAttribute: function (name, value) {
      this.attributes[name] = String(value);
    },
    appendChild: function (child) {
      this.children.push(child);
      return child;
    },
    replaceChildren: function () {
      this.children = [];
    }
  };
  element.classList = {
    add: function () {
      for (let index = 0; index < arguments.length; index += 1) {
        const name = arguments[index];
        if (element.className.split(" ").indexOf(name) < 0) {
          element.className = element.className
            ? element.className + " " + name
            : name;
        }
      }
    }
  };
  return element;
}

function snapshot(element) {
  return {
    tag: element.tagName,
    className: element.className,
    style: element.style,
    attributes: element.attributes,
    text: element.textContent,
    type: element.type,
    children: element.children.map(snapshot)
  };
}

const doc = {
  createElement: function (tag) {
    return makeElement(tag);
  }
};
const container = makeElement("div");
const model = engine.buildGridModel(payload.puzzle);
engine.renderGrid(container, model, doc);
console.log(JSON.stringify({
  normalized: engine.normalizePuzzle(payload.puzzle),
  model: model,
  rendered: snapshot(container)
}));
"""


def run_engine(payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "-e", NODE_HARNESS, str(ENGINE), json.dumps(payload)],
        capture_output=True,
        text=True,
        check=False,
    )


def engine_result(payload: dict[str, Any]) -> dict[str, Any]:
    process = run_engine(payload)
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def words_puzzle() -> dict[str, Any]:
    return {
        "id": 1,
        "title": "Nivel A1 - Basics",
        "level": "A1",
        "grid_size": {"rows": 5, "cols": 5},
        "words": [
            {
                "id": 1,
                "word": "APPLE",
                "clue": "Fruta roja o verde",
                "row": 0,
                "col": 0,
                "direction": "horizontal",
                "length": 5,
            },
            {
                "id": 2,
                "word": "CAT",
                "clue": "Animal que maulla",
                "row": 0,
                "col": 0,
                "direction": "vertical",
                "length": 3,
            },
        ],
    }


def backend_puzzle() -> dict[str, Any]:
    return {
        "id": 1,
        "title": "Primeras palabras",
        "cefr_level": "A1",
        "grid_size": {"rows": 5, "cols": 5},
        "grid_data": {"grid_size": {"rows": 99, "cols": 99}},
        "blocked_cells": [],
        "clues": [
            {
                "number": 1,
                "direction": "across",
                "clue_text": "A round fruit.",
                "length": 5,
            },
            {
                "number": 2,
                "direction": "down",
                "clue_text": "A small animal.",
                "length": 3,
            },
        ],
        "placements": [
            {"clue_key": "1_across", "row": 2, "col": 0, "direction": "across"},
            {"clue_key": "2_down", "row": 1, "col": 0, "direction": "down"},
        ],
    }


def test_grid_is_generated_from_words_collection() -> None:
    result = engine_result({"puzzle": words_puzzle()})
    model = result["model"]

    assert model["rows"] == 5
    assert model["cols"] == 5
    assert model["cells"][0][0]["playable"] is True
    assert model["cells"][0][0]["clueNumber"] == 1
    assert model["cells"][0][1]["playable"] is True
    assert model["cells"][1][0]["playable"] is True
    assert model["cells"][4][4]["playable"] is False
    assert model["cells"][1][2]["playable"] is False
    playable = sum(
        cell["playable"] for row in model["cells"] for cell in row
    )
    assert playable == 7


def test_dimensions_are_derived_without_grid_size() -> None:
    puzzle = words_puzzle()
    puzzle.pop("grid_size")

    model = engine_result({"puzzle": puzzle})["model"]

    assert model["rows"] == 3
    assert model["cols"] == 5


def test_backend_clues_and_placements_are_normalized() -> None:
    result = engine_result({"puzzle": backend_puzzle()})
    words = result["normalized"]
    model = result["model"]

    assert [word["key"] for word in words] == ["1_across", "2_down"]
    assert [word["direction"] for word in words] == ["horizontal", "vertical"]
    assert [word["length"] for word in words] == [5, 3]
    assert [word["row"] for word in words] == [2, 1]
    assert [word["clueNumber"] for word in words] == [1, 2]
    assert model["cells"][2][0]["wordKeys"] == ["1_across", "2_down"]
    assert model["cells"][3][4]["playable"] is False
    assert model["rows"] == 5


def test_render_uses_responsive_grid_and_accessible_cells() -> None:
    rendered = engine_result({"puzzle": words_puzzle()})["rendered"]

    assert "cw-grid--dynamic" in rendered["className"]
    assert rendered["style"]["display"] == "grid"
    assert rendered["style"]["gridTemplateColumns"] == (
        "repeat(5, minmax(0, 1fr))"
    )
    assert len(rendered["children"]) == 25

    blocked = [
        cell
        for cell in rendered["children"]
        if "cw-cell--blocked" in cell["className"]
    ]
    assert len(blocked) == 18
    assert all(cell["attributes"]["aria-hidden"] == "true" for cell in blocked)
    assert all(cell["attributes"]["tabindex"] == "-1" for cell in blocked)

    first = rendered["children"][0]
    assert first["tag"] == "BUTTON"
    assert first["style"]["aspectRatio"] == "1 / 1"
    assert first["attributes"]["data-row"] == "0"
    assert first["attributes"]["data-col"] == "0"
    assert "pista 1" in first["attributes"]["aria-label"]
    assert first["children"][0]["text"] == "1"
    assert first["children"][0]["attributes"]["aria-hidden"] == "true"


@pytest.mark.parametrize(
    "invalid_puzzle",
    [
        {"words": []},
        {"words": [{"row": 0, "col": 0, "direction": "diagonal", "length": 3}]},
        {"words": [{"row": -1, "col": 0, "direction": "across", "length": 3}]},
        {"words": [{"row": 0, "col": 0, "direction": "down", "length": 0}]},
    ],
)
def test_invalid_word_data_is_rejected(invalid_puzzle: dict[str, Any]) -> None:
    process = run_engine({"puzzle": invalid_puzzle})

    assert process.returncode != 0
    assert process.stderr.strip()


def test_grid_engine_asset_is_served_locally() -> None:
    with TestClient(app) as client:
        response = client.get("/static/js/grid-engine.js")

    assert response.status_code == 200
    assert "https://" not in response.text
    assert "repeat(" in response.text
