from __future__ import annotations

import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


def _resolve_database_url() -> str:
    use_local = os.getenv("USE_LOCAL_DATABASE", "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    url = os.getenv("LOCAL_DATABASE_URL") if use_local else os.getenv("DATABASE_URL")
    if not url:
        url = os.getenv("LOCAL_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "Define DATABASE_URL o LOCAL_DATABASE_URL en el entorno antes de importar la base de datos."
        )
    return url


DATABASE_URL: str = _resolve_database_url()

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
