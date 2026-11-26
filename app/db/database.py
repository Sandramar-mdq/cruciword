from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

DATABASE_URL: str = get_settings().DATABASE_URL


def create_db_engine(url: str) -> Engine:
    """Crea un engine con ajustes según el dialecto de la URL."""
    is_sqlite = url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=not is_sqlite,
    )


engine: Engine = create_db_engine(DATABASE_URL)

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """Entrega una sesión por petición y siempre la cierra."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
