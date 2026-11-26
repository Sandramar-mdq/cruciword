from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import auth, classrooms, puzzles, users, word_lists

app = FastAPI(title="CruciWord")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(puzzles.router, prefix="/api/puzzles", tags=["puzzles"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["classrooms"])
app.include_router(word_lists.router, prefix="/api", tags=["word-lists"])
