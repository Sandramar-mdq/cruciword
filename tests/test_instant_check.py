from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).resolve().parents[1] / "static" / "js" / "board.js"

NODE_HARNESS = r"""
const fs = require("fs");
const vm = require("vm");

const source = fs.readFileSync(process.argv[1], "utf8");
const listeners = {};
const calls = [];

function classList() {
  const values = new Set();
  return {
    add: function (name) { values.add(name); },
    remove: function () {
      Array.prototype.slice.call(arguments).forEach(function (name) { values.delete(name); });
    },
    contains: function (name) { return values.has(name); }
  };
}

function makeCell(row, col, index, letter) {
  const letterNode = { textContent: letter };
  return {
    row: row,
    col: col,
    classList: classList(),
    querySelector: function (selector) {
      return selector === ".cw-cell__letter" ? letterNode : null;
    },
    getAttribute: function (name) {
      if (name === "data-row") { return String(row); }
      if (name === "data-col") { return String(col); }
      if (name === "data-cell-index") { return String(index); }
      return null;
    },
    setAttribute: function () {},
    removeAttribute: function () {},
    focus: function () {}
  };
}

const answers = {
  "1_across": "APLE",
  "2_down": "A  PLE",
  "3_down": ""
};

const cells = [
  makeCell(0, 0, 0, "A"),
  makeCell(0, 1, 1, "P"),
  makeCell(0, 2, 2, "L"),
  makeCell(0, 3, 3, "E"),
  makeCell(1, 0, 4, "P"),
  makeCell(2, 0, 5, ""),
  makeCell(3, 0, 6, "P"),
  makeCell(4, 0, 7, "L"),
  makeCell(5, 0, 8, "E"),
  makeCell(6, 0, 9, "")
];

const detail = {
  id: 7,
  grid_size: { rows: 7, cols: 5 },
  clues: [
    { number: 1, direction: "across", length: 4, clue_text: "FRUTA" },
    { number: 2, direction: "down", length: 7, clue_text: "VERTICAL" },
    { number: 3, direction: "down", length: 1, clue_text: "SIN ESCRIBIR" }
  ],
  placements: [
    { clue_key: "1_across", row: 0, col: 0, direction: "across" },
    { clue_key: "2_down", row: 0, col: 0, direction: "down" }
  ]
};

function findButtons(nodes, output) {
  nodes.forEach(function (node) {
    if (node.getAttribute && node.getAttribute("data-focus-clue")) {
      output.push(node);
    }
    if (node.children) {
      findButtons(node.children, output);
    }
  });
  return output;
}

function makeElement(tag) {
  const attributes = {};
  return {
    tagName: tag,
    children: [],
    className: "",
    textContent: "",
    classList: classList(),
    setAttribute: function (name, value) { attributes[name] = value; },
    getAttribute: function (name) {
      return Object.prototype.hasOwnProperty.call(attributes, name) ? attributes[name] : null;
    },
    appendChild: function (child) { this.children.push(child); return child; }
  };
}

const grid = {
  style: { setProperty: function () {} },
  querySelectorAll: function () { return cells; }
};

const clueList = {
  innerHTML: "",
  items: [],
  appendChild: function (node) { this.items.push(node); return node; },
  querySelectorAll: function () { return findButtons(this.items, []); },
  addEventListener: function () {}
};

const status = { textContent: "", className: "" };
const score = { textContent: "" };
const clue = { setAttribute: function () {} };
const clueNumber = { textContent: "" };
const clueCopy = { textContent: "" };
const select = {
  innerHTML: "",
  value: "",
  appendChild: function () {},
  addEventListener: function () {}
};

const board = {
  getAttribute: function (name) { return name === "data-puzzle-id" ? "7" : null; },
  setAttribute: function () {},
  dispatchEvent: function () {},
  querySelector: function (selector) {
    if (selector === "[data-board-grid]") { return grid; }
    if (selector === "[data-clue-list]") { return clueList; }
    if (selector === "[data-level-select]") { return select; }
    if (selector === "[data-puzzle-select]") { return select; }
    if (selector === "[data-clue-text]") { return clue; }
    if (selector === "[data-clue-number]") { return clueNumber; }
    if (selector === "[data-clue-copy]") { return clueCopy; }
    if (selector === "[data-check-status]") { return status; }
    if (selector === "[data-score-status]") { return score; }
    return null;
  },
  addEventListener: function (type, handler) { listeners["board:" + type] = handler; }
};

const document = {
  readyState: "complete",
  querySelector: function () { return board; },
  createElement: makeElement,
  createTextNode: function (text) { return { textContent: text }; },
  addEventListener: function () {}
};

const result = {
  letters: {
    "1_across": [true, true, false, true],
    "2_down": [true, false, true, true, true, true, true]
  },
  correct_words: [],
  incorrect_words: ["1_across", "2_down", "3_down"],
  score: 10,
  total_words: 3,
  completed: false,
  message: "Revisa estas letras con calma."
};

const api = {
  loadPuzzles: function () { return Promise.resolve([]); },
  request: function (url) {
    if (url === "/api/puzzles/7") { return Promise.resolve({ data: detail }); }
    return Promise.resolve(null);
  },
  checkAnswers: function (puzzleId, submitted) {
    calls.push({ puzzleId: puzzleId, answers: submitted });
    return Promise.resolve(result);
  }
};

const context = {
  window: {
    CruciApi: api,
    CruciStorage: {
      getPuzzleProgress: function () { return {}; },
      saveProgress: function () {}
    },
    CruciGridEngine: {
      buildGridModel: function () { return {}; },
      renderGrid: function () {}
    },
    CruciNavigation: {
      getAnswers: function () { return answers; },
      selectClue: function () {}
    },
    CruciKeyboard: { refresh: function () {} }
  },
  document: document,
  navigator: { onLine: true },
  CustomEvent: function () {},
  console: console
};

vm.runInNewContext(source, context);

function cellAt(row, col) {
  return cells.find(function (cell) { return cell.row === row && cell.col === col; });
}

function buttonFor(clueKey) {
  return clueList.querySelectorAll().find(function (button) {
    return button.getAttribute("data-focus-clue") === clueKey;
  });
}

function has(target, className) {
  return target.classList.contains(className);
}

function snapshot() {
  return {
    calls: calls.slice(),
    correctCell: has(cellAt(0, 0), "cw-cell--correct"),
    reviewCell: has(cellAt(0, 2), "cw-cell--review"),
    neutralEmptyCell: !has(cellAt(2, 0), "cw-cell--review") && !has(cellAt(2, 0), "cw-cell--correct"),
    reviewClue: has(buttonFor("1_across"), "cw-clue--review"),
    neutralUntouchedClue: !has(buttonFor("3_down"), "cw-clue--review"),
    statusText: status.textContent,
    statusKind: status.className
  };
}

setImmediate(function () {
  context.window.CruciBoard.checkNow().then(function () {
    const afterCheck = snapshot();
    listeners["board:cruciword:boardchange"]();
    console.log(JSON.stringify({
      afterCheck: afterCheck,
      afterEdit: snapshot()
    }));
  }).catch(function (error) {
    console.error(error);
    process.exitCode = 1;
  });
});
"""


def run_check() -> dict[str, Any]:
    process = subprocess.run(
        ["node", "-e", NODE_HARNESS, str(SOURCE)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def test_check_request_and_kind_feedback() -> None:
    result = run_check()
    after_check = result["afterCheck"]

    assert after_check["calls"] == [
        {
            "puzzleId": 7,
            "answers": {
                "1_across": "APLE",
                "2_down": "A  PLE",
                "3_down": "",
            },
        }
    ]
    assert after_check["correctCell"] is True
    assert after_check["reviewCell"] is True
    assert after_check["neutralEmptyCell"] is True
    assert after_check["reviewClue"] is True
    assert after_check["neutralUntouchedClue"] is True
    assert after_check["statusText"] == "Revisa estas letras con calma."
    assert after_check["statusKind"] == "cw-feedback cw-feedback--review"


def test_editing_clears_feedback_without_new_requests() -> None:
    result = run_check()
    after_edit = result["afterEdit"]

    assert after_edit["correctCell"] is False
    assert after_edit["reviewCell"] is False
    assert after_edit["reviewClue"] is False
    assert after_edit["statusText"] == "Escribe y pulsa ✓ cuando quieras ver tu avance."
    assert after_edit["statusKind"] == "cw-feedback"
    assert len(after_edit["calls"]) == 1
