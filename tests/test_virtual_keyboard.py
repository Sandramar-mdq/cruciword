from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

SOURCE = (
    Path(__file__).resolve().parents[1] / "static" / "js" / "keyboard.js"
)

NODE_HARNESS = r"""
const fs = require("fs");
const vm = require("vm");

const source = fs.readFileSync(process.argv[1], "utf8");
const listeners = {};
const calls = { toggle: 0, check: 0, write: 0, erase: 0, move: 0 };
const status = { textContent: "" };

function classList() {
  return { add: function () {}, remove: function () {}, toggle: function () {} };
}

const cells = [0, 1].map(function () {
  return {
    querySelector: function () { return null; },
    classList: classList(),
    setAttribute: function () {},
    removeAttribute: function () {},
    focus: function () {}
  };
});

const board = {
  querySelectorAll: function () { return cells; },
  addEventListener: function (type, handler) { listeners["board:" + type] = handler; }
};

const document = {
  querySelector: function () { return board; },
  getElementById: function () { return status; },
  addEventListener: function (type, handler) { listeners["document:" + type] = handler; }
};

const navigation = {
  getState: function () { return null; },
  toggleDirection: function () { calls.toggle += 1; },
  write: function () { calls.write += 1; },
  erase: function () { calls.erase += 1; },
  move: function () { calls.move += 1; },
  refresh: function () {},
  clear: function () {},
  getWord: function () { return ""; },
  getAnswers: function () { return {}; },
  selectCellIndex: function () {}
};

const boardApi = {
  checkNow: function () { calls.check += 1; },
  getAnswers: function () { return {}; }
};

vm.runInNewContext(source, {
  window: { CruciNavigation: navigation, CruciBoard: boardApi },
  document: document,
  CustomEvent: function () {},
  console: console
});

function keyEvent(key, insideBoard) {
  let prevented = false;
  const target = {
    closest: function (selector) {
      if (selector === "input, textarea, select, form, [contenteditable='true']") {
        return null;
      }
      if (insideBoard && selector === "[data-board-grid] [data-cell-index]") {
        return {};
      }
      return null;
    }
  };
  return {
    event: {
      key: key,
      target: target,
      ctrlKey: false,
      metaKey: false,
      altKey: false,
      preventDefault: function () { prevented = true; }
    },
    prevented: function () { return prevented; }
  };
}

function runKey(key, insideBoard) {
  const instance = keyEvent(key, insideBoard);
  listeners["document:keydown"](instance.event);
  return instance.prevented();
}

const tabInsidePrevented = runKey("Tab", true);
const tabOutsidePrevented = runKey("Tab", false);
const spaceInsidePrevented = runKey(" ", true);
const letterPrevented = runKey("a", false);
const backspacePrevented = runKey("Backspace", false);
const arrowPrevented = runKey("ArrowDown", false);

function actionTarget(name) {
  return {
    closest: function (selector) {
      if (selector === "[data-key-action]") {
        return { getAttribute: function () { return name; } };
      }
      return null;
    }
  };
}

listeners["board:click"]({ target: actionTarget("check") });
listeners["board:click"]({ target: actionTarget("toggle-direction") });

console.log(JSON.stringify({
  calls: calls,
  tabInsidePrevented: tabInsidePrevented,
  tabOutsidePrevented: tabOutsidePrevented,
  spaceInsidePrevented: spaceInsidePrevented,
  letterPrevented: letterPrevented,
  backspacePrevented: backspacePrevented,
  arrowPrevented: arrowPrevented
}));
"""


def run_keyboard() -> dict[str, Any]:
    process = subprocess.run(
        ["node", "-e", NODE_HARNESS, str(SOURCE)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def test_physical_keys_and_touch_actions_share_navigation() -> None:
    result = run_keyboard()

    assert result["calls"] == {
        "toggle": 3,
        "check": 1,
        "write": 1,
        "erase": 1,
        "move": 1,
    }
    assert result["tabInsidePrevented"] is True
    assert result["tabOutsidePrevented"] is False
    assert result["spaceInsidePrevented"] is True
    assert result["letterPrevented"] is True
    assert result["backspacePrevented"] is True
    assert result["arrowPrevented"] is True
