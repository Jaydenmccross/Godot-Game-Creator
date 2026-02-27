"""Godot Game Creator — FastAPI application.

Serves the chat UI and handles game-creation conversations + project generation.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import GENERATED_GAMES_DIR, STATIC_DIR
from app.models import ChatRequest, ChatResponse, UndoRequest
from app.ai.engine import process_message, process_undo, get_or_create_session
from app.ai.suggestions import get_help_text

app = FastAPI(title="Godot Game Creator", version="2.0.0")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return await process_message(req)


@app.post("/api/undo", response_model=ChatResponse)
async def undo(req: UndoRequest):
    return await process_undo(req)


@app.get("/api/help/{session_id}")
async def help_text(session_id: str):
    session = get_or_create_session(session_id)
    return {"help": get_help_text(session.state, session.spec)}


@app.get("/api/download/{game_name}")
async def download_game(game_name: str):
    game_dir = GENERATED_GAMES_DIR / game_name
    if not game_dir.exists():
        raise HTTPException(status_code=404, detail="Game not found")

    zip_path = Path(tempfile.gettempdir()) / f"{game_name}.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(game_dir))
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"{game_name}.zip",
    )


@app.get("/api/games")
async def list_games():
    if not GENERATED_GAMES_DIR.exists():
        return {"games": []}
    games = [
        d.name
        for d in GENERATED_GAMES_DIR.iterdir()
        if d.is_dir() and (d / "project.godot").exists()
    ]
    return {"games": games}
