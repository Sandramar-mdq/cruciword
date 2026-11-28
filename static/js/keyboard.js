(function () {
  "use strict";

  var board = document.querySelector("[data-demo-board]");
  if (!board) {
    return;
  }

  var cells = Array.prototype.slice.call(board.querySelectorAll("[data-cell-index]"));
  var status = document.getElementById("cw-keyboard-status");
  var activeIndex = 0;

  if (!cells.length) {
    return;
  }

  function navigation() {
    if (
      window.CruciNavigation &&
      typeof window.CruciNavigation.getState === "function"
    ) {
      return window.CruciNavigation;
    }
    return null;
  }

  function say(message) {
    if (status) {
      status.textContent = message;
    }
  }

  function cellLetter(cell) {
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

  function getWord() {
    var nav = navigation();
    if (nav) {
      var navigationWord = nav.getWord();
      if (navigationWord) {
        return navigationWord;
      }
    }
    return cells.map(cellLetter).join("");
  }

  function getAnswers() {
    var nav = navigation();
    if (nav) {
      var navigationAnswers = nav.getAnswers();
      if (Object.keys(navigationAnswers).length) {
        return navigationAnswers;
      }
    }
    if (window.CruciBoard && typeof window.CruciBoard.getAnswers === "function") {
      return window.CruciBoard.getAnswers();
    }
    return { "1_across": getWord() };
  }

  function notify() {
    board.dispatchEvent(
      new CustomEvent("cruciword:boardchange", {
        detail: { word: getWord(), answers: getAnswers() }
      })
    );
  }

  function setActive(index, focus) {
    var next = Math.max(0, Math.min(cells.length - 1, index));
    activeIndex = next;
    cells.forEach(function (cell, position) {
      var selected = position === next;
      cell.classList.toggle("cw-cell--active", selected);
      if (selected) {
        cell.setAttribute("aria-current", "true");
      } else {
        cell.removeAttribute("aria-current");
      }
    });
    if (focus) {
      cells[next].focus();
    }
    return next;
  }

  function refresh() {
    var nav = navigation();
    if (nav) {
      nav.refresh();
      return;
    }
    cells = Array.prototype.slice.call(board.querySelectorAll("[data-cell-index]"));
    if (!cells.length) {
      return;
    }
    setActive(Math.min(activeIndex, cells.length - 1), false);
  }

  function write(letter) {
    var nav = navigation();
    if (nav) {
      nav.write(letter);
      return;
    }
    var value = String(letter || "").toUpperCase();
    if (!/^[A-Z]$/.test(value)) {
      return;
    }
    var cell = cells[activeIndex];
    cell.textContent = value;
    cell.setAttribute("aria-label", "Celda " + (activeIndex + 1) + ": " + value);
    say("Letra " + value + " escrita. Sigue cuando quieras.");
    notify();
    if (activeIndex < cells.length - 1) {
      setActive(activeIndex + 1, false);
    }
  }

  function erase() {
    var nav = navigation();
    if (nav) {
      nav.erase();
      return;
    }
    var cell = cells[activeIndex];
    if (cell.textContent.trim()) {
      cell.textContent = "";
      cell.setAttribute("aria-label", "Celda " + (activeIndex + 1));
      say("Letra borrada.");
      notify();
      return;
    }
    if (activeIndex > 0) {
      setActive(activeIndex - 1, false);
      erase();
    }
  }

  function toggleDirection() {
    var nav = navigation();
    if (nav && typeof nav.toggleDirection === "function") {
      nav.toggleDirection();
    }
  }

  function check() {
    if (window.CruciBoard && typeof window.CruciBoard.checkNow === "function") {
      window.CruciBoard.checkNow();
      say("Comprobando tus letras sin prisa.");
    }
  }

  function isBoardCell(target) {
    return !!(
      target &&
      target.closest &&
      target.closest("[data-board-grid] [data-cell-index]")
    );
  }

  function move(direction) {
    var nav = navigation();
    if (nav) {
      nav.move(typeof direction === "number" ? (direction < 0 ? "ArrowLeft" : "ArrowRight") : direction);
      return;
    }
    if (direction === "ArrowLeft") {
      setActive(activeIndex - 1, true);
      return;
    }
    if (direction === "ArrowRight") {
      setActive(activeIndex + 1, true);
      return;
    }
    setActive(activeIndex + direction, true);
  }

  function focusCell(index) {
    var nav = navigation();
    if (nav) {
      nav.selectCellIndex(index);
      return;
    }
    setActive(index, true);
  }

  function clear() {
    var nav = navigation();
    if (nav) {
      nav.clear();
      return;
    }
    cells.forEach(function (cell, position) {
      cell.textContent = "";
      cell.setAttribute("aria-label", "Celda " + (position + 1));
      cell.classList.remove("cw-cell--correct", "cw-cell--review", "cw-cell--attention");
    });
    setActive(0, false);
    notify();
  }

  board.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || typeof target.closest !== "function") {
      return;
    }

    var cell = target.closest("[data-cell-index]");
    if (cell) {
      if (!navigation()) {
        setActive(parseInt(cell.getAttribute("data-cell-index"), 10) || 0, true);
      }
      return;
    }

    var key = target.closest("[data-key]");
    if (key) {
      write(key.getAttribute("data-key"));
      return;
    }

    var action = target.closest("[data-key-action]");
    if (!action) {
      return;
    }
    var actionName = action.getAttribute("data-key-action");
    if (actionName === "backspace") {
      erase();
      return;
    }
    if (actionName === "toggle-direction") {
      toggleDirection();
      return;
    }
    if (actionName === "check") {
      check();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }

    var target = event.target;
    if (target && target.closest && target.closest("input, textarea, select, form, [contenteditable='true']")) {
      return;
    }
    if (target && target.isContentEditable) {
      return;
    }

    var key = event.key;
    if (/^[a-zA-Z]$/.test(key)) {
      event.preventDefault();
      write(key);
      return;
    }
    if (key === "Backspace" || key === "Delete") {
      event.preventDefault();
      erase();
      return;
    }
    if (key === "ArrowLeft" || key === "ArrowRight" || key === "ArrowUp" || key === "ArrowDown") {
      event.preventDefault();
      move(key);
      return;
    }
    if ((key === "Tab" || key === " " || key === "Spacebar") && isBoardCell(target)) {
      event.preventDefault();
      toggleDirection();
      return;
    }
    if (key === "Home") {
      event.preventDefault();
      focusCell(0);
      return;
    }
    if (key === "End") {
      event.preventDefault();
      focusCell(cells.length - 1);
    }
  });

  setActive(0, false);
  window.CruciKeyboard = {
    getWord: getWord,
    getAnswers: getAnswers,
    focusCell: focusCell,
    refresh: refresh,
    clear: clear,
    toggleDirection: toggleDirection,
    check: check
  };
}());
