(function () {
  "use strict";

  var board = document.querySelector("[data-demo-board]");
  if (!board) {
    return;
  }

  var grid = board.querySelector("[data-board-grid]");
  var clueList = board.querySelector("[data-clue-list]");
  var levelSelect = board.querySelector("[data-level-select]");
  var puzzleSelect = board.querySelector("[data-puzzle-select]");
  var clue = board.querySelector("[data-clue-text]");
  var clueNumber = board.querySelector("[data-clue-number]");
  var clueCopy = board.querySelector("[data-clue-copy]");
  var checkStatus = board.querySelector("[data-check-status]");
  var scoreStatus = board.querySelector("[data-score-status]");

  var state = {
    puzzleId: parseInt(board.getAttribute("data-puzzle-id"), 10) || 1,
    detail: null,
    puzzles: []
  };

  var neutralStatus = "Escribe y pulsa ✓ cuando quieras ver tu avance.";

  function storage() {
    return window.CruciStorage;
  }

  function api() {
    return window.CruciApi;
  }

  function key(id) {
    return String(id);
  }

  function getBest(id) {
    var store = storage();
    var record = store ? store.getPuzzleProgress(key(id)) : {};
    return Number(record.bestScore) || 0;
  }

  function rememberBest(id, score, total) {
    var previous = getBest(id);
    if (score <= previous) {
      return { best: previous, improved: false };
    }
    var store = storage();
    if (store) {
      store.saveProgress(key(id), {
        bestScore: score,
        totalWords: total,
        completed: score >= total
      });
    }
    return { best: score, improved: true };
  }

  function showScore(best, total) {
    if (!scoreStatus) {
      return;
    }
    scoreStatus.textContent =
      "Tu mejor marca: " + best + " de " + total + " palabras.";
  }

  function setCheckStatus(message, kind) {
    if (!checkStatus) {
      return;
    }
    checkStatus.className =
      "cw-feedback" + (kind ? " cw-feedback--" + kind : "");
    checkStatus.textContent = message;
  }

  function cellAt(row, col) {
    if (!grid) {
      return null;
    }
    return grid.querySelector(
      '[data-row="' + row + '"][data-col="' + col + '"]'
    );
  }

  function readLetter(cell) {
    var letter = cell.querySelector(".cw-cell__letter");
    if (letter) {
      return letter.textContent.trim();
    }
    var number = cell.querySelector(".cw-cell__number");
    if (number) {
      return cell.textContent.replace(number.textContent, "").trim();
    }
    return cell.textContent.trim();
  }

  function answerFor(placement) {
    var clue = findClue(placement.clue_key);
    var length = clue ? clue.length : 0;
    var letters = [];
    for (var index = 0; index < length; index += 1) {
      var row = placement.row + (placement.direction === "down" ? index : 0);
      var col = placement.col + (placement.direction === "across" ? index : 0);
      var cell = cellAt(row, col);
      letters.push(cell ? readLetter(cell) : "");
    }
    return letters.join("");
  }

  function getAnswers() {
    if (window.CruciNavigation && typeof window.CruciNavigation.getAnswers === "function") {
      var navigationAnswers = window.CruciNavigation.getAnswers();
      if (Object.keys(navigationAnswers).length) {
        return navigationAnswers;
      }
    }
    if (!state.detail || !state.detail.placements.length) {
      var fallback = window.CruciKeyboard ? window.CruciKeyboard.getWord() : "";
      return { "1_across": fallback };
    }
    var answers = {};
    state.detail.placements.forEach(function (placement) {
      answers[placement.clue_key] = answerFor(placement);
    });
    return answers;
  }

  function getWord() {
    if (window.CruciNavigation && typeof window.CruciNavigation.getWord === "function") {
      var navigationWord = window.CruciNavigation.getWord();
      if (navigationWord) {
        return navigationWord;
      }
    }
    var answers = getAnswers();
    var keys = Object.keys(answers);
    return keys.length ? answers[keys[0]] : "";
  }

  function findPlacement(clueKey) {
    if (!state.detail) {
      return null;
    }
    for (var index = 0; index < state.detail.placements.length; index += 1) {
      if (state.detail.placements[index].clue_key === clueKey) {
        return state.detail.placements[index];
      }
    }
    return null;
  }

  function findClue(clueKey) {
    if (!state.detail) {
      return null;
    }
    for (var index = 0; index < state.detail.clues.length; index += 1) {
      var item = state.detail.clues[index];
      if (item.number + "_" + item.direction === clueKey) {
        return item;
      }
    }
    return null;
  }

  function setClue(clueKey, focus) {
    var item = findClue(clueKey);
    if (!item) {
      return;
    }
    if (clue) {
      clue.setAttribute("data-clue-text", item.clue_text);
      clue.setAttribute("data-clue-audio-text", item.clue_text);
    }
    if (clueNumber) {
      clueNumber.textContent =
        "Pista " +
        item.number +
        " · " +
        (item.direction === "across" ? "horizontal" : "vertical");
    }
    if (clueCopy) {
      clueCopy.textContent = item.clue_text;
    }
    if (clueList) {
      Array.prototype.forEach.call(
        clueList.querySelectorAll("[data-focus-clue]"),
        function (button) {
          button.classList.toggle(
            "cw-clue--active",
            button.getAttribute("data-focus-clue") === clueKey
          );
        }
      );
    }
    if (focus) {
      if (window.CruciNavigation && typeof window.CruciNavigation.selectClue === "function") {
        window.CruciNavigation.selectClue(clueKey);
        return;
      }
      var placement = findPlacement(clueKey);
      var cell = placement ? cellAt(placement.row, placement.col) : null;
      var index = cell ? parseInt(cell.getAttribute("data-cell-index"), 10) : 0;
      if (window.CruciKeyboard) {
        window.CruciKeyboard.focusCell(index || 0);
      }
    }
  }

  function markLetters(result) {
    var states = {};
    Object.keys(result.letters || {}).forEach(function (clueKey) {
      var placement = findPlacement(clueKey);
      if (!placement) {
        return;
      }
      result.letters[clueKey].forEach(function (correct, index) {
        var row = placement.row + (placement.direction === "down" ? index : 0);
        var col = placement.col + (placement.direction === "across" ? index : 0);
        var keyPosition = row + ":" + col;
        states[keyPosition] = states[keyPosition] || correct;
      });
    });

    if (!grid) {
      return;
    }
    Array.prototype.forEach.call(
      grid.querySelectorAll("[data-cell-index]"),
      function (cell) {
        cell.classList.remove("cw-cell--correct", "cw-cell--review", "cw-cell--attention");
        if (!readLetter(cell)) {
          return;
        }
        var position = cell.getAttribute("data-row") + ":" + cell.getAttribute("data-col");
        if (states[position] === true) {
          cell.classList.add("cw-cell--correct");
        } else if (states[position] === false) {
          cell.classList.add("cw-cell--review");
        }
      }
    );
  }

  function markClues(result) {
    if (!clueList) {
      return;
    }
    var correct = result.correct_words || [];
    var review = result.incorrect_words || [];
    var answers = getAnswers();
    Array.prototype.forEach.call(
      clueList.querySelectorAll("[data-focus-clue]"),
      function (button) {
        var clueKey = button.getAttribute("data-focus-clue");
        button.classList.remove("cw-clue--correct", "cw-clue--review", "cw-clue--attention");
        if (correct.indexOf(clueKey) >= 0) {
          button.classList.add("cw-clue--correct");
        } else if (review.indexOf(clueKey) >= 0 && answers[clueKey] && answers[clueKey].length) {
          button.classList.add("cw-clue--review");
        }
      }
    );
  }

  function clearFeedback() {
    if (grid) {
      Array.prototype.forEach.call(
        grid.querySelectorAll("[data-cell-index]"),
        function (cell) {
          cell.classList.remove("cw-cell--correct", "cw-cell--review", "cw-cell--attention");
        }
      );
    }
    if (clueList) {
      Array.prototype.forEach.call(
        clueList.querySelectorAll("[data-focus-clue]"),
        function (button) {
          button.classList.remove("cw-clue--correct", "cw-clue--review", "cw-clue--attention");
        }
      );
    }
    setCheckStatus(neutralStatus);
  }

  function applyCheck(result) {
    if (!result) {
      return;
    }
    markLetters(result);
    markClues(result);
    var total = result.total_words || (state.detail ? state.detail.clues.length : 0);
    var record = rememberBest(state.puzzleId, result.score || 0, total);
    showScore(record.best, total);
    var kind = result.completed ? "success" : result.score ? "review" : "";
    setCheckStatus(result.message, kind);
  }

  function checkNow() {
    if (!navigator.onLine) {
      setCheckStatus("Sin conexión; tus letras se guardan para más tarde.", "review");
      return Promise.resolve(null);
    }
    if (!api() || typeof api().checkAnswers !== "function") {
      return Promise.resolve(null);
    }
    var answers = getAnswers();
    if (!Object.keys(answers).some(function (clueKey) {
      return answers[clueKey].length > 0;
    })) {
      setCheckStatus(neutralStatus);
      return Promise.resolve(null);
    }
    return api()
      .checkAnswers(state.puzzleId, answers)
      .then(function (result) {
        applyCheck(result);
        return result;
      })
      .catch(function () {
        setCheckStatus("No se pudo verificar ahora; sigue escribiendo cuando quieras.", "review");
        return null;
      });
  }

  function renderClues(detail) {
    if (!clueList) {
      return;
    }
    clueList.innerHTML = "";
    detail.clues.forEach(function (item) {
      var listItem = document.createElement("li");
      var button = document.createElement("button");
      var label = document.createElement("strong");
      button.type = "button";
      button.className = "cw-clue";
      button.setAttribute("data-focus-clue", item.number + "_" + item.direction);
      label.textContent = item.number + " · " + (item.direction === "across" ? "HORIZONTAL" : "VERTICAL");
      button.appendChild(label);
      button.appendChild(document.createTextNode(" " + item.clue_text));
      listItem.appendChild(button);
      clueList.appendChild(listItem);
    });
  }

  function render(detail) {
    if (!grid || !detail || !detail.grid_size) {
      return;
    }
    var engine = window.CruciGridEngine;
    if (!engine) {
      return;
    }
    var model = engine.buildGridModel(detail);
    state.detail = detail;
    state.puzzleId = detail.id;
    board.setAttribute("data-puzzle-id", String(detail.id));
    grid.style.setProperty("--cw-grid-cols", String(detail.grid_size.cols));
    engine.renderGrid(grid, model);

    renderClues(detail);
    showScore(getBest(detail.id), detail.clues.length);
    setCheckStatus(neutralStatus);
    if (detail.clues.length) {
      setClue(detail.clues[0].number + "_" + detail.clues[0].direction, false);
    }
    board.dispatchEvent(
      new CustomEvent("cruciword:gridchange", { detail: { model: model } })
    );
    if (window.CruciKeyboard && typeof window.CruciKeyboard.refresh === "function") {
      window.CruciKeyboard.refresh();
    }
  }

  function loadPuzzle(id) {
    if (!api()) {
      return Promise.resolve(null);
    }
    return api()
      .request("/api/puzzles/" + id, { auth: false })
      .then(function (result) {
        render(result.data);
        return result.data;
      })
      .catch(function () {
        return null;
      });
  }

  function fillPuzzleSelect(level) {
    if (!puzzleSelect) {
      return null;
    }
    var previous = puzzleSelect.value;
    var list = state.puzzles.filter(function (puzzle) {
      return !level || puzzle.cefr_level === level;
    });
    puzzleSelect.innerHTML = "";
    list.forEach(function (puzzle) {
      var option = document.createElement("option");
      option.value = String(puzzle.id);
      option.textContent = puzzle.title + " · " + puzzle.cefr_level;
      puzzleSelect.appendChild(option);
    });
    if (!list.length) {
      return null;
    }
    var selected = list.some(function (puzzle) {
      return String(puzzle.id) === previous;
    }) ? previous : String(list[0].id);
    puzzleSelect.value = selected;
    return selected;
  }

  function applyProgress(result) {
    if (!result) {
      return;
    }
    var total = result.total_words || (state.detail ? state.detail.clues.length : 0);
    var local = getBest(state.puzzleId);
    var best = Math.max(local, Number(result.best_score) || 0);
    showScore(best, total);
    setCheckStatus(result.message, result.completed ? "success" : "review");
  }

  function wire() {
    board.addEventListener("cruciword:boardchange", clearFeedback);

    if (puzzleSelect) {
      puzzleSelect.addEventListener("change", function () {
        loadPuzzle(puzzleSelect.value);
      });
    }
    if (levelSelect) {
      levelSelect.addEventListener("change", function () {
        var selected = fillPuzzleSelect(levelSelect.value);
        if (selected) {
          loadPuzzle(selected);
        }
      });
    }
    if (clueList) {
      clueList.addEventListener("click", function (event) {
        var target = event.target;
        if (!target || typeof target.closest !== "function") {
          return;
        }
        var button = target.closest("[data-focus-clue]");
        if (!button) {
          return;
        }
        var clueKey = button.getAttribute("data-focus-clue");
        setClue(clueKey, true);
      });
    }
  }

  function init() {
    wire();
    var loader = api() && typeof api().loadPuzzles === "function"
      ? api().loadPuzzles()
      : Promise.resolve([]);
    loader
      .then(function (list) {
        state.puzzles = Array.isArray(list) ? list : [];
        var level = levelSelect ? levelSelect.value : "";
        var selected = fillPuzzleSelect(level);
        return loadPuzzle(selected || String(state.puzzleId));
      })
      .catch(function () {
        return null;
      });
  }

  window.CruciBoard = {
    getAnswers: getAnswers,
    getWord: getWord,
    setClue: setClue,
    applyProgress: applyProgress,
    checkNow: checkNow
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}());
