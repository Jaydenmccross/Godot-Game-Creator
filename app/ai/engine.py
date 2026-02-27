"""AI Conversation Engine for game creation.

Uses smart keyword extraction and intent classification to guide users
through game creation via natural conversation. Works without an external
LLM — all intelligence is built-in.
"""

from __future__ import annotations

import re
import uuid
from typing import Optional

from app.ai.intent import classify_intent, Intent
from app.ai.extractor import extract_game_params
from app.ai.responses import build_response
from app.models import (
    ChatRequest,
    ChatResponse,
    ConversationState,
    GameSpec,
    Genre,
    SessionData,
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
    session.history.append({"role": "user", "content": user_msg})

    intent = classify_intent(user_msg, session.state)
    params = extract_game_params(user_msg)

    _apply_params(session, params)

    if intent == Intent.START_OVER:
        session = reset_session(req.session_id)
        return _reply(session, build_response(session, intent))

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

    return ChatResponse(
        message=response_text,
        state=session.state,
        game_ready=game_ready or session.state == ConversationState.COMPLETE,
        download_url=download_url,
        preview_log=preview_log,
        spec=session.spec if session.state != ConversationState.GREETING else None,
    )


def _apply_params(session: SessionData, params: dict) -> None:
    spec = session.spec
    if "genre" in params:
        spec.genre = params["genre"]
    if "theme" in params:
        spec.theme = params["theme"]
    if "name" in params:
        spec.name = params["name"]
    if "player_name" in params:
        spec.player_name = params["player_name"]
    if "has_enemies" in params:
        spec.has_enemies = params["has_enemies"]
    if "has_collectibles" in params:
        spec.has_collectibles = params["has_collectibles"]
    if "has_powerups" in params:
        spec.has_powerups = params["has_powerups"]
    if "has_dialogue" in params:
        spec.has_dialogue = params["has_dialogue"]
    if "difficulty" in params:
        spec.difficulty = params["difficulty"]
    if "color_primary" in params:
        spec.color_primary = params["color_primary"]
    if "color_secondary" in params:
        spec.color_secondary = params["color_secondary"]
    if "color_bg" in params:
        spec.color_bg = params["color_bg"]
    if "description" in params:
        spec.description = params["description"]


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


def _reply(session: SessionData, text: str) -> ChatResponse:
    session.history.append({"role": "assistant", "content": text})
    return ChatResponse(
        message=text,
        state=session.state,
    )
