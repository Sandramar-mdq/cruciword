from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class AccountType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    INSTITUTIONAL = "institutional"


class Level(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [str(member.value) for member in enum_cls]


student_classrooms = Table(
    "student_classrooms",
    Base.metadata,
    Column(
        "student_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "classroom_id",
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "joined_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=_enum_values),
        default=UserRole.STUDENT,
        server_default="student",
        nullable=False,
    )
    account_type: Mapped[AccountType] = mapped_column(
        SAEnum(AccountType, name="account_type", values_callable=_enum_values),
        default=AccountType.FREE,
        server_default="free",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    classrooms_taught: Mapped[list[Classroom]] = relationship(
        back_populates="teacher",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    classrooms_enrolled: Mapped[list[Classroom]] = relationship(
        secondary=student_classrooms,
        back_populates="students",
        passive_deletes=True,
    )
    progress: Mapped[list[UserProgress]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    invite_code: Mapped[str] = mapped_column(
        String(24),
        unique=True,
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    teacher: Mapped[User] = relationship(back_populates="classrooms_taught")
    students: Mapped[list[User]] = relationship(
        secondary=student_classrooms,
        back_populates="classrooms_enrolled",
        passive_deletes=True,
    )
    puzzles: Mapped[list[Puzzle]] = relationship(
        back_populates="classroom",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    translation: Mapped[str] = mapped_column(String(160), nullable=False)
    level: Mapped[Level] = mapped_column(
        SAEnum(Level, name="level", values_callable=_enum_values),
        default=Level.A1,
        server_default="A1",
        index=True,
        nullable=False,
    )
    theme: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    definition_en: Mapped[str] = mapped_column(Text, nullable=False)
    synonym_hint: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_power: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )
    sponsored_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Puzzle(Base):
    __tablename__ = "puzzles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    level: Mapped[Level] = mapped_column(
        SAEnum(Level, name="level", values_callable=_enum_values),
        default=Level.A1,
        server_default="A1",
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    grid_data: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    classroom_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    classroom: Mapped[Classroom | None] = relationship(back_populates="puzzles")
    progress: Mapped[list[UserProgress]] = relationship(
        back_populates="puzzle",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "puzzle_id", name="uq_user_progress_user_puzzle"),
        CheckConstraint("score >= 0", name="ck_user_progress_score_non_negative"),
        CheckConstraint("hints_used >= 0", name="ck_user_progress_hints_used_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    puzzle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("puzzles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    hints_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="progress")
    puzzle: Mapped[Puzzle] = relationship(back_populates="progress")
