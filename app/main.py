from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import auth, classrooms, puzzles, users, word_lists
from app.core.themes import DEFAULT_THEME, THEMES
from app.data.grids import GRID_SPECS, build_grid_data

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

mimetypes.add_type("font/woff2", ".woff2")

app = FastAPI(title="CruciWord")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(puzzles.router, prefix="/api/puzzles", tags=["puzzles"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["classrooms"])
app.include_router(word_lists.router, prefix="/api", tags=["word-lists"])


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "themes": THEMES,
            "default_theme": DEFAULT_THEME,
            "preview_grid": build_grid_data(GRID_SPECS[0]),
        },
    )
