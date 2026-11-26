from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

import app.db.database as db_module
import database
from app.core.config import Settings, get_settings
from app.db.database import Base, SessionLocal, create_db_engine, engine, get_db


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("DATABASE_URL", "SECRET_KEY", "ALGORITHM"):
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.DATABASE_URL == "sqlite:///./cruciword.db"
    assert settings.SECRET_KEY == "dev-only-insecure-change-me-32chars!!"
    assert settings.ALGORITHM == "HS256"


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()

    assert first is second
    get_settings.cache_clear()


def test_create_db_engine_and_connection() -> None:
    sqlite_engine = create_db_engine("sqlite:///:memory:")

    assert isinstance(sqlite_engine, Engine)
    assert sqlite_engine.dialect.name == "sqlite"

    with sqlite_engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

    sqlite_engine.dispose()


def test_default_engine_is_configured() -> None:
    assert isinstance(engine, Engine)
    assert SessionLocal.kw["autocommit"] is False
    assert SessionLocal.kw["autoflush"] is False
    assert SessionLocal.kw["bind"] is engine


def test_get_db_yields_and_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(db_module, "SessionLocal", lambda: session)
    generator = get_db()

    yielded = next(generator)
    assert yielded is session
    assert session.closed is False

    with pytest.raises(StopIteration):
        next(generator)

    assert session.closed is True


def test_get_db_closes_on_generator_close(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(db_module, "SessionLocal", lambda: session)
    generator = get_db()
    next(generator)

    generator.close()

    assert session.closed is True


def test_legacy_shim_reexports() -> None:
    assert database.Base is Base
    assert database.engine is engine
    assert database.SessionLocal is SessionLocal
    assert database.get_db is get_db
