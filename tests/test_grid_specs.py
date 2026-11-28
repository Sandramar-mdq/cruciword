from __future__ import annotations

import pytest

from app.data.grids import GRID_SPECS, GridSpec, build_grid_data, validate_grid_data
from models import Level


@pytest.mark.parametrize("spec", GRID_SPECS)
def test_grid_spec_is_mathematically_coherent(spec: GridSpec) -> None:
    data = build_grid_data(spec)
    size = data["grid_size"]
    placements = data["placements"]
    solutions = data["solutions"]
    clues = data["clues"]

    assert isinstance(size, dict)
    assert isinstance(placements, list)
    assert isinstance(solutions, dict)
    assert isinstance(clues, list)
    assert len(placements) == len(solutions) == len(clues)

    occupied: dict[tuple[int, int], str] = {}
    for placement in placements:
        key = placement["clue_key"]
        answer = solutions[key]
        for index, letter in enumerate(answer):
            row = placement["row"] + (index if placement["direction"] == "down" else 0)
            col = placement["col"] + (index if placement["direction"] == "across" else 0)
            assert 0 <= row < size["rows"]
            assert 0 <= col < size["cols"]
            assert occupied.setdefault((row, col), letter) == letter

    expected_blocked = [
        [row, col]
        for row in range(size["rows"])
        for col in range(size["cols"])
        if (row, col) not in occupied
    ]
    assert data["blocked_cells"] == expected_blocked

    for clue in clues:
        key = f"{clue['number']}_{clue['direction']}".lower()
        assert clue["length"] == len(solutions[key])
        assert clue["static_hint"]

    validate_grid_data(data)


def test_grid_specs_cover_all_cefr_levels() -> None:
    assert {spec.level for spec in GRID_SPECS} == set(Level)


def test_validator_rejects_incompatible_crossings() -> None:
    data = build_grid_data(GRID_SPECS[0])
    data["solutions"] = {"1_down": "CAT", "2_across": "BANANA"}

    with pytest.raises(ValueError, match="Cruce incompatible"):
        validate_grid_data(data)


def test_validator_rejects_words_outside_the_grid() -> None:
    data = build_grid_data(GRID_SPECS[0])
    data["placements"][0]["col"] = 99

    with pytest.raises(ValueError, match="fuera de la grilla"):
        validate_grid_data(data)
