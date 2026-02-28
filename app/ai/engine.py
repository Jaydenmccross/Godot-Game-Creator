"""AI Conversation Engine for game creation.

Uses smart keyword extraction and intent classification to guide users
through game creation via natural conversation. Works without an external
LLM — all intelligence is built-in. Includes undo/snapshot support.
"""

from __future__ import annotations

import copy
from typing import Optional

from app.ai.intent import Intent
from app.ai.llm_client import analyze_message_with_llm
from app.ai.responses import build_response
from app.ai.suggestions import get_suggestions
from app.models import (
    ChatRequest,
    ChatResponse,
    ConversationState,
    GameSpec,
    Genre,
    SessionData,
    StateSnapshot,
    UndoRequest,
)

_sessions: dict[str, SessionData] = {}


def get_or_create_session(session_id: str) -> SessionData:
    if session_id not in _sessions:
        _sessions[session_id] = SessionData(session_id=session_id)
    return _sessions[session_id]


def reset_session(session_id: str) -> SessionData:
    _sessions[session_id] = SessionData(session_id=session_id)
    return _sessions[session_id]


async def process_message(req: ChatRequest) -> ChatResponse:
    session = get_or_create_session(req.session_id)
    user_msg = req.message.strip()

    _save_snapshot(session)

    session.history.append({"role": "user", "content": user_msg})

    result = await analyze_message_with_llm(
        user_message=user_msg,
        current_state=session.state,
        current_spec=session.spec,
        history=session.history[:-1]
    )
    
    intent = result.intent
    session.spec = result.extracted_spec
    
    _apply_theme_colors(session.spec)

    if intent == Intent.START_OVER:
        session = reset_session(req.session_id)
        resp_text = build_response(session, intent)
        session.history.append({"role": "assistant", "content": resp_text})
        return ChatResponse(
            message=resp_text,
            state=session.state,
            suggestions=get_suggestions(session.state, session.spec),
            can_undo=False,
        )

    next_state = _transition(session.state, intent, session.spec)
    session.state = next_state

    response_text = build_response(session, intent)
    session.history.append({"role": "assistant", "content": response_text})

    game_ready = session.state == ConversationState.GENERATING
    download_url: Optional[str] = None
    preview_log: Optional[str] = None

    if game_ready:
        from app.generator.project_builder import generate_game
        from app.mcp.godot_mcp import validate_project

        result = await generate_game(session.spec)
        download_url = f"/api/download/{session.spec.name.replace(' ', '_')}"
        preview_log = await validate_project(result["project_dir"])
        session.state = ConversationState.COMPLETE

    suggestions = get_suggestions(session.state, session.spec)

    return ChatResponse(
        message=response_text,
        state=session.state,
        game_ready=game_ready or session.state == ConversationState.COMPLETE,
        download_url=download_url,
        preview_log=preview_log,
        spec=session.spec if session.state != ConversationState.GREETING else None,
        suggestions=suggestions,
        can_undo=len(session.snapshots) > 0,
    )


async def process_undo(req: UndoRequest) -> ChatResponse:
    """Revert to the previous state snapshot."""
    session = get_or_create_session(req.session_id)

    if not session.snapshots:
        return ChatResponse(
            message="Nothing to undo — you're at the beginning!",
            state=session.state,
            spec=session.spec if session.state != ConversationState.GREETING else None,
            suggestions=get_suggestions(session.state, session.spec),
            can_undo=False,
        )

    snapshot = session.snapshots.pop()
    session.state = snapshot.state
    session.spec = snapshot.spec
    session.history = session.history[: snapshot.message_count]

    undo_msg = "**Undo successful!** Reverted to previous state."
    session.history.append({"role": "assistant", "content": undo_msg})

    return ChatResponse(
        message=undo_msg,
        state=session.state,
        spec=session.spec if session.state != ConversationState.GREETING else None,
        suggestions=get_suggestions(session.state, session.spec),
        can_undo=len(session.snapshots) > 0,
    )


def _save_snapshot(session: SessionData) -> None:
    snapshot = StateSnapshot(
        state=session.state,
        spec=session.spec.model_copy(deep=True),
        message_count=len(session.history),
    )
    session.snapshots.append(snapshot)
    if len(session.snapshots) > 20:
        session.snapshots = session.snapshots[-20:]



def _apply_theme_colors(spec: GameSpec) -> None:
    """Set colors based on theme when user hasn't explicitly set them."""
    theme_colors = {
        "fantasy":    ("#4a90d9", "#d94a4a", "#f9ca24", "#1a1a2e", "#2d5a27"),
        "sci-fi":     ("#00d2ff", "#ff6b6b", "#00ff88", "#0a0a2a", "#1a3a4a"),
        "sci fi":     ("#00d2ff", "#ff6b6b", "#00ff88", "#0a0a2a", "#1a3a4a"),
        "horror":     ("#8b0000", "#4a0080", "#ff4444", "#0a0a0a", "#1a1a1a"),
        "cyberpunk":  ("#ff006e", "#00f5d4", "#fee440", "#0a0a1a", "#1a1a2e"),
        "retro":      ("#ff5722", "#4caf50", "#ffeb3b", "#1a0a2e", "#2e1a4e"),
        "neon":       ("#ff00ff", "#00ffff", "#ffff00", "#0a0a1a", "#1a0a2a"),
        "ocean":      ("#0077b6", "#00b4d8", "#48cae4", "#0a1628", "#1a3a4a"),
        "space":      ("#c0c0ff", "#ff4444", "#ffffff", "#050510", "#0a0a20"),
        "nature":     ("#4caf50", "#8bc34a", "#ffeb3b", "#1a2e1a", "#2d5a27"),
        "desert":     ("#e6a23c", "#d94a4a", "#f5deb3", "#2e1a0a", "#8b7355"),
        "snow":       ("#a8d8ea", "#5e8cc9", "#ffffff", "#1a2a3a", "#c0c0c0"),
        "ice":        ("#a8d8ea", "#5e8cc9", "#ffffff", "#1a2a3a", "#c0c0c0"),
        "jungle":     ("#2e8b57", "#ff6347", "#ffd700", "#0a1a0a", "#1a3a1a"),
        "pirate":     ("#c19a6b", "#d94a4a", "#ffd700", "#1a1a2e", "#4a3728"),
        "zombie":     ("#4a7a4a", "#8b0000", "#808080", "#0a0a0a", "#2a2a1a"),
        "ninja":      ("#2a2a2a", "#d94a4a", "#c0c0c0", "#0a0a15", "#1a1a2e"),
        "robot":      ("#808080", "#00bfff", "#ffd700", "#0a0a1a", "#2a2a3a"),
        "medieval":   ("#8b7355", "#d94a4a", "#ffd700", "#1a1a0a", "#3a3a1a"),
        "steampunk":  ("#b87333", "#8b4513", "#ffd700", "#1a1a0a", "#2a2a1a"),
        "volcanic":   ("#ff4500", "#ff6347", "#ffd700", "#1a0a0a", "#4a2a0a"),
        "tropical":   ("#00b894", "#fdcb6e", "#ff6348", "#0a1a2e", "#2d5a27"),
        "haunted":    ("#6c5ce7", "#d63031", "#dfe6e9", "#0a0a15", "#1a1a2e"),
        "celestial":  ("#a29bfe", "#fd79a8", "#ffeaa7", "#0a0a1a", "#1a1a3a"),
        "western":    ("#c19a6b", "#d94a4a", "#f5deb3", "#2e1a0a", "#8b7355"),
    }
    low_theme = spec.theme.lower()
    for key, colors in theme_colors.items():
        if key in low_theme:
            spec.color_primary, spec.color_secondary, spec.color_accent, spec.color_bg, spec.color_ground = colors
            break


def _transition(
    current: ConversationState, intent: Intent, spec: GameSpec
) -> ConversationState:
    if intent == Intent.GENERATE_NOW:
        return ConversationState.GENERATING

    if intent == Intent.CONFIRM_YES and current == ConversationState.CONFIRMING:
        return ConversationState.GENERATING

    if intent == Intent.CONFIRM_NO and current == ConversationState.CONFIRMING:
        return ConversationState.DETAIL_GATHERING

    transitions = {
        ConversationState.GREETING: {
            Intent.SELECT_GENRE: ConversationState.THEME_SELECTION,
            Intent.DESCRIBE_GAME: ConversationState.DETAIL_GATHERING,
            Intent.GENERAL_CHAT: ConversationState.GENRE_SELECTION,
        },
        ConversationState.GENRE_SELECTION: {
            Intent.SELECT_GENRE: ConversationState.THEME_SELECTION,
            Intent.DESCRIBE_GAME: ConversationState.DETAIL_GATHERING,
        },
        ConversationState.THEME_SELECTION: {
            Intent.SET_THEME: ConversationState.DETAIL_GATHERING,
            Intent.DESCRIBE_GAME: ConversationState.DETAIL_GATHERING,
            Intent.READY: ConversationState.CONFIRMING,
        },
        ConversationState.DETAIL_GATHERING: {
            Intent.ADD_DETAIL: ConversationState.DETAIL_GATHERING,
            Intent.DESCRIBE_GAME: ConversationState.DETAIL_GATHERING,
            Intent.READY: ConversationState.CONFIRMING,
            Intent.SET_THEME: ConversationState.DETAIL_GATHERING,
            Intent.SELECT_GENRE: ConversationState.DETAIL_GATHERING,
        },
        ConversationState.COMPLETE: {
            Intent.START_OVER: ConversationState.GREETING,
            Intent.DESCRIBE_GAME: ConversationState.DETAIL_GATHERING,
        },
    }

    state_map = transitions.get(current, {})
    return state_map.get(intent, current)
