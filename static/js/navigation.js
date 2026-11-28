(function () {
  "use strict";

  var board = document.querySelector("[data-demo-board]");
  if (!board) {
    return;
  }

  var grid = board.querySelector("[data-board-grid]");
  var status = document.getElementById("cw-keyboard-status");
  var engine = window.CruciGridEngine;
  if (!grid || !engine) {
    return;
  }

  var model = null;
  var navigator = null;
  var cells = [];
  var cellsByPosition = {};
  var lastSyncedKey = null;

  function list(selector, root) {
    return Array.prototype.slice.call(
      (root || grid).querySelectorAll(selector)
    );
  }

  function describe(cell, value) {
    var row = parseInt(cell.getAttribute("data-row"), 10) + 1;
    var col = parseInt(cell.getAttribute("data-col"), 10) + 1;
    var label = "Fila " + row + ", columna " + col;
    var number = cell.getAttribute("data-clue-number");
    if (number) {
      label += ", pista " + number;
    }
    if (value) {
      label += ", letra " + value;
    }
    return label;
  }

  function readLetter(cell) {
    var element = cell.querySelector(".cw-cell__letter");
    if (element) {
      return element.textContent.trim();
    }
    var number = cell.querySelector(".cw-cell__number");
    if (number) {
      return cell.textContent.replace(number.textContent, "").trim();
    }
    return cell.textContent.trim();
  }

  function writeLetterToCell(cell, value) {
    var element = cell.querySelector(".cw-cell__letter");
    if (element) {
      element.textContent = value;
    } else {
      cell.textContent = value;
    }
    cell.setAttribute("data-letter", value);
    cell.setAttribute("aria-label", describe(cell, value));
  }

  function collectLetters() {
    var letters = {};
    cells.forEach(function (cell) {
      var value = readLetter(cell);
      if (value) {
        letters[
          cell.getAttribute("data-row") + ":" + cell.getAttribute("data-col")
        ] = value;
      }
    });
    return letters;
  }

  function dimensions() {
    var rows = 0;
    var cols = 0;
    list("[data-row][data-col]").forEach(function (cell) {
      rows = Math.max(rows, parseInt(cell.getAttribute("data-row"), 10) + 1);
      cols = Math.max(cols, parseInt(cell.getAttribute("data-col"), 10) + 1);
    });
    return { rows: rows, cols: cols };
  }

  function modelFromDom() {
    var byKey = {};
    list("[data-cell-index]").forEach(function (cell) {
      var row = parseInt(cell.getAttribute("data-row"), 10);
      var col = parseInt(cell.getAttribute("data-col"), 10);
      var keys = (cell.getAttribute("data-clue-keys") || "").split(/\s+/);
      keys.forEach(function (key) {
        if (!key) {
          return;
        }
        var match = /^(\d+)_(across|down)$/i.exec(key);
        if (!match) {
          return;
        }
        var direction =
          match[2].toLowerCase() === "across" ? "horizontal" : "vertical";
        var entry = byKey[key] || {
          key: key,
          word: "",
          clue: "",
          clueNumber: parseInt(match[1], 10),
          row: row,
          col: col,
          direction: direction,
          length: 1
        };
        entry.row = Math.min(entry.row, row);
        entry.col = Math.min(entry.col, col);
        entry.length = Math.max(
          entry.length,
          direction === "vertical" ? row - entry.row + 1 : col - entry.col + 1
        );
        byKey[key] = entry;
      });
    });

    var words = Object.keys(byKey)
      .sort()
      .map(function (key, index) {
        byKey[key].id = index + 1;
        return byKey[key];
      });
    if (!words.length) {
      return null;
    }
    return engine.buildGridModel({ grid_size: dimensions(), words: words });
  }

  function syncClue(state) {
    if (!state || state.key === lastSyncedKey) {
      return;
    }
    lastSyncedKey = state.key;
    if (window.CruciBoard && typeof window.CruciBoard.setClue === "function") {
      window.CruciBoard.setClue(state.key, false);
    }
  }

  function applyState(state, focus) {
    cells.forEach(function (cell) {
      cell.classList.remove("cw-cell--word", "cw-cell--active");
      cell.removeAttribute("aria-current");
    });
    if (!state) {
      return;
    }

    state.cells.forEach(function (item) {
      var cell = cellsByPosition[item.row + ":" + item.col];
      if (cell) {
        cell.classList.add("cw-cell--word");
      }
    });

    var active = cellsByPosition[state.row + ":" + state.col];
    if (active) {
      active.classList.add("cw-cell--active");
      active.setAttribute("aria-current", "true");
      if (focus) {
        active.focus();
      }
    }

    syncClue(state);
    if (status) {
      status.textContent =
        "Pista " +
        state.clueNumber +
        " · " +
        (state.direction === "horizontal" ? "horizontal" : "vertical") +
        ". Escribe cuando quieras.";
    }
  }

  function notify() {
    if (!navigator) {
      return;
    }
    board.dispatchEvent(
      new CustomEvent("cruciword:boardchange", {
        detail: { word: navigator.getWord(), answers: navigator.getAnswers() }
      })
    );
  }

  function refresh(nextModel) {
    model = nextModel || modelFromDom();
    if (!model) {
      return null;
    }
    cells = list("[data-cell-index]");
    cellsByPosition = {};
    cells.forEach(function (cell) {
      cellsByPosition[
        cell.getAttribute("data-row") + ":" + cell.getAttribute("data-col")
      ] = cell;
    });

    navigator = engine.createNavigator(model, { letters: collectLetters() });
    lastSyncedKey = null;

    var activeClue = board.querySelector(
      "[data-focus-clue].cw-clue--active"
    );
    var state = activeClue
      ? navigator.selectClue(activeClue.getAttribute("data-focus-clue"))
      : navigator.selectCellIndex(0);
    applyState(state, false);
    return state;
  }

  function selectCell(cell) {
    if (!navigator || !cell) {
      return null;
    }
    var state = navigator.selectCell(
      parseInt(cell.getAttribute("data-row"), 10),
      parseInt(cell.getAttribute("data-col"), 10),
      { toggle: true }
    );
    applyState(state, true);
    return state;
  }

  function selectCellIndex(index) {
    if (!navigator) {
      return null;
    }
    var state = navigator.selectCellIndex(index);
    applyState(state, true);
    return state;
  }

  function selectClue(key) {
    if (!navigator) {
      return null;
    }
    var state = navigator.selectClue(key);
    applyState(state, true);
    return state;
  }

  function toggleDirection() {
    if (!navigator) {
      return null;
    }
    var state = navigator.toggleDirection();
    applyState(state, true);
    if (state && status) {
      status.textContent =
        "Dirección " +
        (state.direction === "horizontal" ? "horizontal" : "vertical") +
        ". Escribe cuando quieras.";
    }
    return state;
  }

  function write(letter) {
    if (!navigator) {
      return null;
    }
    var result = navigator.writeLetter(letter);
    if (!result) {
      return null;
    }
    var cell = cellsByPosition[
      result.written.row + ":" + result.written.col
    ];
    if (cell) {
      writeLetterToCell(cell, result.written.letter);
    }
    applyState(result.state, false);
    notify();
    if (status) {
      status.textContent =
        "Letra " + result.written.letter + " escrita. Sigue cuando quieras.";
    }
    return result;
  }

  function erase() {
    if (!navigator) {
      return null;
    }
    var result = navigator.eraseLetter();
    if (!result) {
      return null;
    }
    if (result.erased) {
      var cell = cellsByPosition[result.erased.row + ":" + result.erased.col];
      if (cell) {
        writeLetterToCell(cell, "");
      }
    }
    applyState(result.state, false);
    if (result.changed) {
      notify();
      if (status) {
        status.textContent = "Letra borrada. Puedes seguir cuando quieras.";
      }
    }
    return result;
  }

  function move(key) {
    if (!navigator) {
      return null;
    }
    var state = navigator.move(key);
    applyState(state, true);
    return state;
  }

  function clear() {
    if (!navigator) {
      return null;
    }
    var state = navigator.clear();
    cells.forEach(function (cell) {
      writeLetterToCell(cell, "");
    });
    applyState(state, false);
    notify();
    return state;
  }

  grid.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || typeof target.closest !== "function") {
      return;
    }
    var cell = target.closest("[data-cell-index]");
    if (cell && grid.contains(cell)) {
      event.preventDefault();
      selectCell(cell);
    }
  });

  board.addEventListener("cruciword:gridchange", function (event) {
    refresh(event.detail && event.detail.model ? event.detail.model : null);
  });

  window.CruciNavigation = {
    refresh: refresh,
    selectCell: selectCell,
    selectCellIndex: selectCellIndex,
    selectClue: selectClue,
    toggleDirection: toggleDirection,
    write: write,
    erase: erase,
    move: move,
    clear: clear,
    getAnswers: function () {
      return navigator ? navigator.getAnswers() : {};
    },
    getWord: function () {
      return navigator ? navigator.getWord() : "";
    },
    getState: function () {
      return navigator ? navigator.getState() : null;
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      refresh();
    });
  } else {
    refresh();
  }
}());
