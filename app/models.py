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


class VisualStyle(str, Enum):
    SIMPLE = "simple"
    PIXEL = "pixel"
    NEON = "neon"
    HAND_DRAWN = "hand_drawn"
    RETRO = "retro"
    MINIMALIST = "minimalist"


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
    has_particles: bool = False
    has_parallax_bg: bool = False
    difficulty: str = "normal"
    art_style: str = "simple"
    color_primary: str = "#4a90d9"
    color_secondary: str = "#d94a4a"
    color_accent: str = "#f9ca24"
    color_bg: str = "#1a1a2e"
    color_ground: str = "#2d5a27"
    particle_type: str = "none"
    weather: str = "none"
    description: str = ""


class ConversationState(str, Enum):
    GREETING = "greeting"
    GENRE_SELECTION = "genre_selection"
    THEME_SELECTION = "theme_selection"
    DETAIL_GATHERING = "detail_gathering"
    CONFIRMING = "confirming"
    GENERATING = "generating"
    COMPLETE = "complete"


class Suggestion(BaseModel):
    """A contextual suggestion chip shown to the user."""
    text: str
    category: str = "feature"


class StateSnapshot(BaseModel):
    """Snapshot for undo support."""
    state: ConversationState
    spec: GameSpec
    message_count: int


class SessionData(BaseModel):
    session_id: str
    state: ConversationState = ConversationState.GREETING
    spec: GameSpec = Field(default_factory=GameSpec)
    history: list[dict] = Field(default_factory=list)
    snapshots: list[StateSnapshot] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class UndoRequest(BaseModel):
    session_id: str


class ChatResponse(BaseModel):
    message: str
    state: ConversationState
    game_ready: bool = False
    download_url: Optional[str] = None
    preview_log: Optional[str] = None
    spec: Optional[GameSpec] = None
    suggestions: list[Suggestion] = Field(default_factory=list)
    can_undo: bool = False
