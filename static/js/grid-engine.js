(function (root, factory) {
  "use strict";

  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.CruciGridEngine = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var DIRECTIONS = {
    horizontal: "horizontal",
    across: "horizontal",
    vertical: "vertical",
    down: "vertical"
  };

  function isNonNegativeInteger(value) {
    return typeof value === "number" && Number.isInteger(value) && value >= 0;
  }

  function isPositiveInteger(value) {
    return typeof value === "number" && Number.isInteger(value) && value > 0;
  }

  function findClue(clues, key) {
    for (var index = 0; index < clues.length; index += 1) {
      var clue = clues[index];
      if (clue && clue.number + "_" + clue.direction === key) {
        return clue;
      }
    }
    return null;
  }

  function wordsFromBackend(input) {
    var clues = Array.isArray(input.clues) ? input.clues : [];
    var placements = Array.isArray(input.placements) ? input.placements : [];
    var words = [];

    placements.forEach(function (placement, index) {
      if (!placement || typeof placement !== "object") {
        throw new TypeError("La colocación " + index + " no es válida.");
      }
      var key = typeof placement.clue_key === "string" ? placement.clue_key : "";
      var clue = findClue(clues, key);
      if (!clue) {
        throw new Error("La colocación " + key + " no tiene pista correspondiente.");
      }
      words.push({
        id: index + 1,
        key: key,
        word: typeof clue.answer === "string" ? clue.answer : "",
        clue: typeof clue.clue_text === "string" ? clue.clue_text : "",
        clueNumber: clue.number,
        row: placement.row,
        col: placement.col,
        direction: placement.direction,
        length: clue.length
      });
    });

    return words;
  }

  function normalizeWord(item, index) {
    if (!item || typeof item !== "object") {
      throw new TypeError("La palabra " + index + " no es válida.");
    }
    var direction = DIRECTIONS[item.direction];
    if (!direction) {
      throw new Error("Dirección no válida: " + String(item.direction));
    }
    if (!isNonNegativeInteger(item.row) || !isNonNegativeInteger(item.col)) {
      throw new Error("Coordenadas no válidas en la palabra " + (index + 1) + ".");
    }
    if (!isPositiveInteger(item.length)) {
      throw new Error("Longitud no válida en la palabra " + (index + 1) + ".");
    }
    var id = isPositiveInteger(item.id) ? item.id : index + 1;
    var clueNumber = isPositiveInteger(item.clueNumber)
      ? item.clueNumber
      : isPositiveInteger(item.number) ? item.number : index + 1;

    return {
      id: id,
      key: typeof item.key === "string" ? item.key : String(id),
      word: typeof item.word === "string" ? item.word : "",
      clue: typeof item.clue === "string" ? item.clue : "",
      clueNumber: clueNumber,
      row: item.row,
      col: item.col,
      direction: direction,
      length: item.length
    };
  }

  function normalizePuzzle(input) {
    if (!input || typeof input !== "object") {
      throw new TypeError("Se requiere un crucigrama válido.");
    }
    var rawWords = Array.isArray(input.words)
      ? input.words
      : wordsFromBackend(input);
    if (!rawWords.length) {
      throw new Error("El crucigrama necesita al menos una palabra.");
    }
    return rawWords.map(normalizeWord);
  }

  function buildGridModel(input) {
    var words = normalizePuzzle(input);
    var derivedRows = 0;
    var derivedCols = 0;

    words.forEach(function (word) {
      derivedRows = Math.max(
        derivedRows,
        word.row + (word.direction === "vertical" ? word.length : 1)
      );
      derivedCols = Math.max(
        derivedCols,
        word.col + (word.direction === "horizontal" ? word.length : 1)
      );
    });

    var size = input.grid_size && typeof input.grid_size === "object"
      ? input.grid_size
      : null;
    var rows = isPositiveInteger(size && size.rows)
      ? Math.max(size.rows, derivedRows)
      : derivedRows;
    var cols = isPositiveInteger(size && size.cols)
      ? Math.max(size.cols, derivedCols)
      : derivedCols;
    var cells = [];

    for (var row = 0; row < rows; row += 1) {
      cells[row] = [];
      for (var col = 0; col < cols; col += 1) {
        cells[row][col] = {
          row: row,
          col: col,
          playable: false,
          clueNumber: null,
          wordKeys: []
        };
      }
    }

    words.forEach(function (word) {
      for (var offset = 0; offset < word.length; offset += 1) {
        var row = word.row + (word.direction === "vertical" ? offset : 0);
        var col = word.col + (word.direction === "horizontal" ? offset : 0);
        if (row >= rows || col >= cols) {
          throw new Error("La palabra " + word.key + " excede la grilla.");
        }
        var cell = cells[row][col];
        cell.playable = true;
        cell.wordKeys.push(word.key);
        if (
          offset === 0 &&
          (cell.clueNumber === null || word.clueNumber < cell.clueNumber)
        ) {
          cell.clueNumber = word.clueNumber;
        }
      }
    });

    return { rows: rows, cols: cols, cells: cells, words: words };
  }

  function positionKey(row, col) {
    return row + ":" + col;
  }

  function opposite(direction) {
    return direction === "horizontal" ? "vertical" : "horizontal";
  }

  function wordByKey(model, key) {
    for (var index = 0; index < model.words.length; index += 1) {
      if (model.words[index].key === key) {
        return model.words[index];
      }
    }
    return null;
  }

  function wordsAt(model, row, col) {
    var cell = model.cells[row] && model.cells[row][col];
    if (!cell || !cell.playable) {
      return [];
    }
    var found = [];
    cell.wordKeys.forEach(function (key) {
      var word = wordByKey(model, key);
      if (word) {
        found.push(word);
      }
    });
    return found;
  }

  function cellsForWord(model, word) {
    var cells = [];
    for (var offset = 0; offset < word.length; offset += 1) {
      cells.push({
        row: word.row + (word.direction === "vertical" ? offset : 0),
        col: word.col + (word.direction === "horizontal" ? offset : 0)
      });
    }
    return cells;
  }

  function pickWord(words, preferred) {
    if (preferred) {
      for (var index = 0; index < words.length; index += 1) {
        if (words[index].direction === preferred) {
          return words[index];
        }
      }
    }
    for (var position = 0; position < words.length; position += 1) {
      if (words[position].direction === "horizontal") {
        return words[position];
      }
    }
    return words.length ? words[0] : null;
  }

  function offsetFor(word, row, col) {
    return word.direction === "vertical" ? row - word.row : col - word.col;
  }

  function movementFor(key) {
    var movements = {
      ArrowLeft: { direction: "horizontal", rowStep: 0, colStep: -1 },
      ArrowRight: { direction: "horizontal", rowStep: 0, colStep: 1 },
      ArrowUp: { direction: "vertical", rowStep: -1, colStep: 0 },
      ArrowDown: { direction: "vertical", rowStep: 1, colStep: 0 }
    };
    if (movements[key]) {
      return movements[key];
    }
    var aliases = {
      left: "ArrowLeft",
      right: "ArrowRight",
      up: "ArrowUp",
      down: "ArrowDown"
    };
    return movements[aliases[String(key).toLowerCase()]] || null;
  }

  function createNavigator(model, options) {
    if (!model || !Array.isArray(model.cells) || !Array.isArray(model.words)) {
      throw new TypeError("Se requiere un modelo de grilla válido.");
    }
    var config = options || {};
    var letters =
      config.letters && typeof config.letters === "object" ? config.letters : {};
    var activeKey = null;
    var position = 0;

    function activeWord() {
      return activeKey ? wordByKey(model, activeKey) : null;
    }

    function letterAt(row, col) {
      var value = letters[positionKey(row, col)];
      return typeof value === "string" ? value : "";
    }

    function snapshot() {
      var word = activeWord();
      if (!word) {
        return null;
      }
      var cells = cellsForWord(model, word);
      var index = Math.max(0, Math.min(position, cells.length - 1));
      return {
        key: word.key,
        word: word.word,
        clue: word.clue,
        clueNumber: word.clueNumber,
        direction: word.direction,
        index: index,
        length: word.length,
        row: cells[index].row,
        col: cells[index].col,
        letter: letterAt(cells[index].row, cells[index].col),
        cells: cells.map(function (cell) {
          return {
            row: cell.row,
            col: cell.col,
            letter: letterAt(cell.row, cell.col)
          };
        })
      };
    }

    function assign(word, index) {
      if (!word) {
        return null;
      }
      activeKey = word.key;
      position = Math.max(0, Math.min(index, word.length - 1));
      return snapshot();
    }

    function isCrossing(words) {
      var directions = {};
      words.forEach(function (word) {
        directions[word.direction] = true;
      });
      return Object.keys(directions).length > 1;
    }

    function selectCell(row, col, optionsForSelection) {
      if (
        !isNonNegativeInteger(row) ||
        !isNonNegativeInteger(col) ||
        !model.cells[row] ||
        !model.cells[row][col] ||
        !model.cells[row][col].playable
      ) {
        return null;
      }
      var candidates = wordsAt(model, row, col);
      if (!candidates.length) {
        return null;
      }
      var settings = optionsForSelection || {};
      var current = activeWord();
      var currentCells = current ? cellsForWord(model, current) : [];
      var sameCell =
        current &&
        currentCells[position] &&
        currentCells[position].row === row &&
        currentCells[position].col === col;
      var preferred = settings.direction || (sameCell ? current.direction : null);
      if (settings.toggle !== false && sameCell && isCrossing(candidates)) {
        preferred = opposite(current.direction);
      }
      var word = pickWord(candidates, preferred);
      return assign(word, offsetFor(word, row, col));
    }

    function selectCellIndex(index) {
      var numeric = parseInt(index, 10);
      if (!isFinite(numeric) || numeric < 0) {
        return null;
      }
      var cells = [];
      model.cells.forEach(function (row) {
        row.forEach(function (cell) {
          if (cell.playable) {
            cells.push(cell);
          }
        });
      });
      if (!cells[numeric]) {
        return null;
      }
      return selectCell(cells[numeric].row, cells[numeric].col);
    }

    function selectClue(key) {
      return assign(wordByKey(model, key), 0);
    }

    function toggleDirection() {
      var current = snapshot();
      if (!current) {
        return null;
      }
      var candidates = wordsAt(model, current.row, current.col);
      if (!isCrossing(candidates)) {
        return current;
      }
      var other = pickWord(candidates, opposite(current.direction));
      if (!other || other.key === current.key) {
        return current;
      }
      return assign(other, offsetFor(other, current.row, current.col));
    }

    function nextEmptyIndex(word, from) {
      for (var offset = 1; offset < word.length; offset += 1) {
        var forward = (from + offset) % word.length;
        var forwardCells = cellsForWord(model, word);
        if (!letterAt(forwardCells[forward].row, forwardCells[forward].col)) {
          return forward;
        }
      }
      return null;
    }

    function writeLetter(letter) {
      var value = String(letter || "").toUpperCase();
      if (!/^[A-Z]$/.test(value)) {
        return null;
      }
      var word = activeWord();
      if (!word) {
        return null;
      }
      var cells = cellsForWord(model, word);
      var target = cells[position];
      letters[positionKey(target.row, target.col)] = value;
      var next = nextEmptyIndex(word, position);
      if (next !== null) {
        position = next;
      }
      return {
        state: snapshot(),
        written: { row: target.row, col: target.col, letter: value }
      };
    }

    function eraseLetter() {
      var word = activeWord();
      if (!word) {
        return null;
      }
      var cells = cellsForWord(model, word);
      var target = cells[position];
      var key = positionKey(target.row, target.col);
      if (letterAt(target.row, target.col)) {
        delete letters[key];
        return {
          state: snapshot(),
          erased: { row: target.row, col: target.col },
          changed: true
        };
      }
      if (position > 0) {
        position -= 1;
        var previous = cells[position];
        delete letters[positionKey(previous.row, previous.col)];
        return {
          state: snapshot(),
          erased: { row: previous.row, col: previous.col },
          changed: true
        };
      }
      return { state: snapshot(), erased: null, changed: false };
    }

    function move(key) {
      var movement = movementFor(key);
      var current = snapshot();
      if (!movement || !current) {
        return current;
      }
      var row = current.row + movement.rowStep;
      var col = current.col + movement.colStep;
      while (
        row >= 0 &&
        row < model.cells.length &&
        col >= 0 &&
        col < model.cells[row].length
      ) {
        if (model.cells[row][col].playable) {
          return selectCell(row, col, {
            direction: movement.direction,
            toggle: false
          });
        }
        row += movement.rowStep;
        col += movement.colStep;
      }
      return current;
    }

    function getAnswers() {
      var answers = {};
      model.words.forEach(function (word) {
        answers[word.key] = cellsForWord(model, word)
          .map(function (cell) {
            return letterAt(cell.row, cell.col);
          })
          .join("");
      });
      return answers;
    }

    function getWord() {
      var state = snapshot();
      return state ? state.cells.map(function (cell) {
        return cell.letter;
      }).join("") : "";
    }

    function setLetters(next) {
      letters = next && typeof next === "object" ? next : {};
      return snapshot();
    }

    function clear() {
      letters = {};
      return snapshot();
    }

    return {
      selectCell: selectCell,
      selectCellIndex: selectCellIndex,
      selectClue: selectClue,
      toggleDirection: toggleDirection,
      writeLetter: writeLetter,
      eraseLetter: eraseLetter,
      move: move,
      getAnswers: getAnswers,
      getWord: getWord,
      getLetters: function () {
        return letters;
      },
      setLetters: setLetters,
      clear: clear,
      getState: snapshot
    };
  }

  function renderGrid(container, model, documentRef) {
    if (!container || typeof container.replaceChildren !== "function") {
      throw new TypeError("Se requiere un contenedor de grilla válido.");
    }
    if (!model || !Array.isArray(model.cells)) {
      throw new TypeError("Se requiere un modelo de grilla válido.");
    }
    var doc = documentRef || (typeof document !== "undefined" ? document : null);
    if (!doc || typeof doc.createElement !== "function") {
      throw new TypeError("Se requiere un documento para renderizar la grilla.");
    }

    container.replaceChildren();
    container.classList.add("cw-grid", "cw-grid--dynamic");
    container.style.display = "grid";
    container.style.gridTemplateColumns =
      "repeat(" + model.cols + ", minmax(0, 1fr))";

    var cellIndex = 0;
    for (var row = 0; row < model.rows; row += 1) {
      for (var col = 0; col < model.cols; col += 1) {
        var cellModel = model.cells[row][col];
        if (!cellModel.playable) {
          var blocked = doc.createElement("div");
          blocked.className = "cw-cell cw-cell--blocked";
          blocked.setAttribute("data-row", String(row));
          blocked.setAttribute("data-col", String(col));
          blocked.setAttribute("aria-hidden", "true");
          blocked.setAttribute("tabindex", "-1");
          container.appendChild(blocked);
          continue;
        }

        var cell = doc.createElement("button");
        cell.type = "button";
        cell.className = "cw-cell cw-cell--button aspect-square";
        cell.style.aspectRatio = "1 / 1";
        cell.style.position = "relative";
        cell.setAttribute("data-cell-index", String(cellIndex));
        cell.setAttribute("data-row", String(row));
        cell.setAttribute("data-col", String(col));
        cell.setAttribute("data-clue-keys", cellModel.wordKeys.join(" "));
        cell.setAttribute(
          "data-clue-number",
          cellModel.clueNumber === null ? "" : String(cellModel.clueNumber)
        );
        cell.setAttribute("data-letter", "");
        cell.setAttribute("tabindex", "0");
        var label = "Fila " + (row + 1) + ", columna " + (col + 1);
        if (cellModel.clueNumber !== null) {
          label += ", pista " + cellModel.clueNumber;
        }
        cell.setAttribute("aria-label", label);

        if (cellModel.clueNumber !== null) {
          var number = doc.createElement("span");
          number.className = "cw-cell__number";
          number.setAttribute("aria-hidden", "true");
          number.style.position = "absolute";
          number.style.top = "2px";
          number.style.left = "4px";
          number.style.fontSize = "0.7rem";
          number.style.lineHeight = "1";
          number.textContent = String(cellModel.clueNumber);
          cell.appendChild(number);
        }

        var letter = doc.createElement("span");
        letter.className = "cw-cell__letter";
        letter.setAttribute("aria-hidden", "true");
        letter.textContent = "";
        cell.appendChild(letter);

        container.appendChild(cell);
        cellIndex += 1;
      }
    }
    return container;
  }

  return {
    normalizePuzzle: normalizePuzzle,
    buildGridModel: buildGridModel,
    createNavigator: createNavigator,
    renderGrid: renderGrid
  };
});
