from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from models import Level

Direction = Literal["across", "down"]


@dataclass(frozen=True)
class GridWord:
    answer: str
    clue_text: str
    static_hint: str
    row: int
    col: int
    direction: Direction


@dataclass(frozen=True)
class GridSpec:
    title: str
    theme: str
    level: Level
    rows: int
    cols: int
    words: tuple[GridWord, ...]


GRID_SPECS: tuple[GridSpec, ...] = (
    GridSpec(
        "Primeras palabras",
        "Daily life",
        Level.A1,
        5,
        5,
        (
            GridWord(
                "APPLE",
                "A round fruit that grows on a tree.",
                "red fruit",
                2,
                0,
                "across",
            ),
            GridWord(
                "CAT",
                "A small animal that often lives with people.",
                "pet that meows",
                1,
                0,
                "down",
            ),
        ),
    ),
    GridSpec(
        "Hogar y ciudad",
        "Home",
        Level.A2,
        6,
        6,
        (
            GridWord(
                "HOUSE",
                "A building where people live.",
                "home building",
                3,
                0,
                "across",
            ),
            GridWord(
                "FOOD",
                "Things people eat to live and grow.",
                "things we eat",
                2,
                1,
                "down",
            ),
            GridWord(
                "FRIEND",
                "A person you like and trust.",
                "close pal",
                0,
                4,
                "down",
            ),
        ),
    ),
    GridSpec(
        "Viaje y memoria",
        "Travel",
        Level.B1,
        7,
        7,
        (
            GridWord(
                "JOURNEY",
                "The act of traveling from one place to another.",
                "trip",
                3,
                0,
                "across",
            ),
            GridWord(
                "MEMORY",
                "The ability to remember things.",
                "recall",
                0,
                1,
                "down",
            ),
            GridWord(
                "MARKET",
                "A place where people buy and sell things.",
                "shopping place",
                1,
                3,
                "down",
            ),
            GridWord(
                "WEATHER",
                "The conditions of sun, rain, wind, or cold outside.",
                "outside conditions",
                6,
                0,
                "across",
            ),
        ),
    ),
    GridSpec(
        "Logros y retos",
        "Work",
        Level.B2,
        11,
        11,
        (
            GridWord(
                "ACHIEVEMENT",
                "Something difficult that you succeed in doing.",
                "success",
                7,
                0,
                "across",
            ),
            GridWord(
                "RELIABLE",
                "Able to be trusted to work well.",
                "trustworthy",
                0,
                4,
                "down",
            ),
            GridWord(
                "ESTIMATE",
                "To guess an amount or value close to the real one.",
                "rough guess",
                0,
                8,
                "down",
            ),
            GridWord(
                "PERSPECTIVE",
                "A particular way of seeing or thinking about something.",
                "point of view",
                0,
                10,
                "down",
            ),
        ),
    ),
    GridSpec(
        "Ideas precisas",
        "Language",
        Level.C1,
        13,
        13,
        (
            GridWord(
                "SOPHISTICATED",
                "Having refined taste or complex, advanced qualities.",
                "refined",
                4,
                0,
                "across",
            ),
            GridWord(
                "RESILIENT",
                "Able to recover quickly after difficulties.",
                "able to bounce back",
                2,
                0,
                "down",
            ),
            GridWord(
                "NUANCE",
                "A very small difference in meaning, feeling, or appearance.",
                "subtle difference",
                0,
                8,
                "down",
            ),
            GridWord(
                "AMBIGUITY",
                "A situation with more than one possible meaning.",
                "unclear meaning",
                4,
                9,
                "down",
            ),
        ),
    ),
)


def _cells_for(word: GridWord) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for index in range(len(word.answer)):
        row = word.row + (index if word.direction == "down" else 0)
        col = word.col + (index if word.direction == "across" else 0)
        cells.add((row, col))
    return cells


def _clue_key(number: int, direction: Direction) -> str:
    return f"{number}_{direction}".lower()


def build_grid_data(spec: GridSpec) -> dict[str, object]:
    ordered = sorted(spec.words, key=lambda item: (item.row, item.col))
    occupied: dict[tuple[int, int], str] = {}
    placements: list[dict[str, object]] = []
    clues: list[dict[str, object]] = []
    solutions: dict[str, str] = {}

    for number, word in enumerate(ordered, start=1):
        for index, letter in enumerate(word.answer):
            row = word.row + (index if word.direction == "down" else 0)
            col = word.col + (index if word.direction == "across" else 0)
            existing = occupied.get((row, col))
            if existing is not None and existing != letter:
                raise ValueError(
                    f"Cruce incompatible en {spec.title}: ({row}, {col})"
                )
            occupied[(row, col)] = letter

        key = _clue_key(number, word.direction)
        placements.append(
            {
                "clue_key": key,
                "row": word.row,
                "col": word.col,
                "direction": word.direction,
            }
        )
        clues.append(
            {
                "number": number,
                "direction": word.direction,
                "clue_text": word.clue_text,
                "static_hint": word.static_hint,
                "audio_url": None,
                "length": len(word.answer),
            }
        )
        solutions[key] = word.answer

    blocked = [
        [row, col]
        for row in range(spec.rows)
        for col in range(spec.cols)
        if (row, col) not in occupied
    ]
    grid_data: dict[str, object] = {
        "grid_size": {"rows": spec.rows, "cols": spec.cols},
        "blocked_cells": blocked,
        "clues": clues,
        "placements": placements,
        "solutions": solutions,
    }
    validate_grid_data(grid_data)
    return grid_data


def validate_grid_data(grid_data: dict[str, object]) -> None:
    raw_size = grid_data.get("grid_size")
    if not isinstance(raw_size, dict):
        raise TypeError("Falta grid_size.")
    rows = raw_size.get("rows")
    cols = raw_size.get("cols")
    if not isinstance(rows, int) or not isinstance(cols, int) or rows <= 0 or cols <= 0:
        raise ValueError("grid_size inválido.")

    raw_clues = grid_data.get("clues")
    raw_placements = grid_data.get("placements")
    raw_solutions = grid_data.get("solutions")
    if not isinstance(raw_clues, list) or not raw_clues:
        raise ValueError("Faltan pistas.")
    if not isinstance(raw_placements, list) or not raw_placements:
        raise ValueError("Faltan colocaciones.")
    if not isinstance(raw_solutions, dict):
        raise TypeError("Faltan soluciones.")

    answers: dict[str, str] = {}
    occupied: dict[tuple[int, int], str] = {}

    for placement in raw_placements:
        if not isinstance(placement, dict):
            raise TypeError("Colocación inválida.")
        key = placement.get("clue_key")
        row = placement.get("row")
        col = placement.get("col")
        direction = placement.get("direction")
        answer = raw_solutions.get(str(key))
        if (
            not isinstance(key, str)
            or not isinstance(row, int)
            or not isinstance(col, int)
            or direction not in {"across", "down"}
            or not isinstance(answer, str)
            or not answer
        ):
            raise ValueError(f"Colocación inválida: {key}.")
        if any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for character in answer):
            raise ValueError(f"Respuesta no alfabética: {key}.")
        answers[key] = answer

        for index, letter in enumerate(answer):
            target_row = row + (index if direction == "down" else 0)
            target_col = col + (index if direction == "across" else 0)
            if not (0 <= target_row < rows and 0 <= target_col < cols):
                raise ValueError(f"Palabra fuera de la grilla: {key}.")
            existing = occupied.get((target_row, target_col))
            if existing is not None and existing != letter:
                raise ValueError(f"Cruce incompatible: {key} en ({target_row}, {target_col}).")
            occupied[(target_row, target_col)] = letter

    for clue in raw_clues:
        if not isinstance(clue, dict):
            raise TypeError("Pista inválida.")
        number = clue.get("number")
        direction = clue.get("direction")
        length = clue.get("length")
        if not isinstance(number, int) or direction not in {"across", "down"}:
            raise ValueError("Pista inválida.")
        key = _clue_key(number, direction)
        if key not in answers or not isinstance(length, int) or length != len(answers[key]):
            raise ValueError(f"Longitud inconsistente: {key}.")

    expected_blocked = [
        [row, col]
        for row in range(rows)
        for col in range(cols)
        if (row, col) not in occupied
    ]
    if grid_data.get("blocked_cells") != expected_blocked:
        raise ValueError("blocked_cells no coincide con las palabras colocadas.")
