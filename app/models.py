from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Genre(str, Enum):
    PLATFORMER = "platformer"
    TOPDOWN = "topdown"
    SHOOTER = "shooter"
    PUZZLE = "puzzle"
    VISUAL_NOVEL = "visual_novel"
    RACING = "racing"


class GameSpec(BaseModel):
    """Fully resolved specification for a game to be generated."""

    name: str = "My Game"
    genre: Genre = Genre.PLATFORMER
    theme: str = "fantasy"
    player_name: str = "Hero"
    has_enemies: bool = True
    has_collectibles: bool = True
    has_powerups: bool = False
    has_dialogue: bool = False
    difficulty: str = "normal"
    art_style: str = "simple"
    color_primary: str = "#4a90d9"
    color_secondary: str = "#d94a4a"
    color_bg: str = "#1a1a2e"
    description: str = ""


class ConversationState(str, Enum):
    GREETING = "greeting"
    GENRE_SELECTION = "genre_selection"
    THEME_SELECTION = "theme_selection"
    DETAIL_GATHERING = "detail_gathering"
    CONFIRMING = "confirming"
    GENERATING = "generating"
    COMPLETE = "complete"


class SessionData(BaseModel):
    session_id: str
    state: ConversationState = ConversationState.GREETING
    spec: GameSpec = Field(default_factory=GameSpec)
    history: list[dict] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    message: str
    state: ConversationState
    game_ready: bool = False
    download_url: Optional[str] = None
    preview_log: Optional[str] = None
    spec: Optional[GameSpec] = None
