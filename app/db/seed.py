from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.grids import GRID_SPECS, build_grid_data
from app.db.database import SessionLocal
from models import Level, Puzzle, Word


@dataclass(frozen=True)
class SeedWord:
    word: str
    translation: str
    level: Level
    theme: str
    definition_en: str
    synonym_hint: str
    is_power: bool = False


@dataclass(frozen=True)
class SeedPuzzle:
    title: str
    theme: str
    level: Level
    grid_data: dict[str, object]


@dataclass(frozen=True)
class SeedResult:
    words_added: int
    words_skipped: int
    puzzles_added: int
    puzzles_skipped: int


SEED_WORDS: tuple[SeedWord, ...] = (
    SeedWord("APPLE", "manzana", Level.A1, "Daily life", "A round fruit that grows on a tree.", "red fruit"),
    SeedWord("BOOK", "libro", Level.A1, "Daily life", "A set of pages you read.", "read pages"),
    SeedWord("SUN", "sol", Level.A1, "Nature", "The bright star that gives light during the day.", "daylight star"),
    SeedWord("WATER", "agua", Level.A1, "Daily life", "A clear liquid people drink.", "clear drink"),
    SeedWord("CAT", "gato", Level.A1, "Animals", "A small animal that often lives with people.", "pet that meows"),
    SeedWord("HOUSE", "casa", Level.A2, "Home", "A building where people live.", "home building"),
    SeedWord("FRIEND", "amigo", Level.A2, "People", "A person you like and trust.", "close pal"),
    SeedWord("CITY", "ciudad", Level.A2, "Places", "A large town with many people and streets.", "large town"),
    SeedWord("FOOD", "comida", Level.A2, "Daily life", "Things people eat to live and grow.", "things we eat"),
    SeedWord("TRAIN", "tren", Level.A2, "Transport", "A vehicle that travels on rails.", "rail vehicle"),
    SeedWord("JOURNEY", "viaje", Level.B1, "Travel", "The act of traveling from one place to another.", "trip"),
    SeedWord("MEMORY", "memoria", Level.B1, "Mind", "The ability to remember things.", "recall"),
    SeedWord("ADVICE", "consejo", Level.B1, "People", "A suggestion about what someone should do.", "suggestion"),
    SeedWord("MARKET", "mercado", Level.B1, "Places", "A place where people buy and sell things.", "shopping place"),
    SeedWord("WEATHER", "tiempo", Level.B1, "Nature", "The conditions of sun, rain, wind, or cold outside.", "outside conditions"),
    SeedWord("ACHIEVEMENT", "logro", Level.B2, "Work", "Something difficult that you succeed in doing.", "success"),
    SeedWord("PERSPECTIVE", "perspectiva", Level.B2, "Ideas", "A particular way of seeing or thinking about something.", "point of view"),
    SeedWord("RELIABLE", "fiable", Level.B2, "People", "Able to be trusted to work well.", "trustworthy"),
    SeedWord("CHALLENGE", "desafío", Level.B2, "Work", "A difficult task that tests your ability.", "test of skill", True),
    SeedWord("ESTIMATE", "estimar", Level.B2, "Work", "To guess an amount or value close to the real one.", "rough guess"),
    SeedWord("SOPHISTICATED", "sofisticado", Level.C1, "Ideas", "Having refined taste or complex, advanced qualities.", "refined"),
    SeedWord("NUANCE", "matiz", Level.C1, "Language", "A very small difference in meaning, feeling, or appearance.", "subtle difference", True),
    SeedWord("RESILIENT", "resiliente", Level.C1, "People", "Able to recover quickly after difficulties.", "able to bounce back", True),
    SeedWord("AMBIGUITY", "ambigüedad", Level.C1, "Language", "A situation with more than one possible meaning.", "unclear meaning"),
    SeedWord("CONCISE", "conciso", Level.C1, "Language", "Expressing a lot in few words.", "brief and clear"),
)


SEED_PUZZLES: tuple[SeedPuzzle, ...] = tuple(
    SeedPuzzle(
        title=spec.title,
        theme=spec.theme,
        level=spec.level,
        grid_data=build_grid_data(spec),
    )
    for spec in GRID_SPECS
)


def seed(db: Session) -> SeedResult:
    """Carga palabras y crucigramas base sin duplicar registros existentes."""
    words_added = 0
    words_skipped = 0
    puzzles_added = 0
    puzzles_skipped = 0

    try:
        for item in SEED_WORDS:
            existing = db.scalar(
                select(Word.id).where(
                    Word.word == item.word,
                    Word.level == item.level,
                )
            )
            if existing is not None:
                words_skipped += 1
                continue
            db.add(
                Word(
                    word=item.word,
                    translation=item.translation,
                    level=item.level,
                    theme=item.theme,
                    definition_en=item.definition_en,
                    synonym_hint=item.synonym_hint,
                    is_power=item.is_power,
                )
            )
            words_added += 1

        for item in SEED_PUZZLES:
            existing = db.scalar(
                select(Puzzle.id).where(
                    Puzzle.title == item.title,
                    Puzzle.level == item.level,
                )
            )
            if existing is not None:
                puzzles_skipped += 1
                continue
            db.add(
                Puzzle(
                    title=item.title,
                    theme=item.theme,
                    level=item.level,
                    grid_data=item.grid_data,
                )
            )
            puzzles_added += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    return SeedResult(
        words_added=words_added,
        words_skipped=words_skipped,
        puzzles_added=puzzles_added,
        puzzles_skipped=puzzles_skipped,
    )


def main() -> None:
    """Punto de entrada para `python -m app.db.seed`."""
    db = SessionLocal()
    try:
        result = seed(db)
    finally:
        db.close()

    print(
        "Seed completado: "
        f"{result.words_added} palabras nuevas, {result.words_skipped} omitidas; "
        f"{result.puzzles_added} crucigramas nuevos, {result.puzzles_skipped} omitidos."
    )


if __name__ == "__main__":
    main()
