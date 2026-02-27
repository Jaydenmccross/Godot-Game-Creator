"""Intent classification for game-creation conversations."""

from __future__ import annotations

import re
from enum import Enum

from app.models import ConversationState


class Intent(str, Enum):
    SELECT_GENRE = "select_genre"
    SET_THEME = "set_theme"
    DESCRIBE_GAME = "describe_game"
    ADD_DETAIL = "add_detail"
    READY = "ready"
    CONFIRM_YES = "confirm_yes"
    CONFIRM_NO = "confirm_no"
    GENERATE_NOW = "generate_now"
    START_OVER = "start_over"
    GENERAL_CHAT = "general_chat"


_GENRE_PATTERNS = [
    r"\bplatform(?:er|ing)?\b",
    r"\btop[- ]?down\b",
    r"\brpg\b",
    r"\bshoot(?:er|ing|em|\'em)\b",
    r"\bspace\b.*\bshoot",
    r"\bpuzzle\b",
    r"\bvisual novel\b",
    r"\bstory\b.*\bgame\b",
    r"\brac(?:e|ing)\b",
    r"\bdriv(?:e|ing)\b",
    r"\badventure\b",
    r"\baction\b",
    r"\bsurvival\b",
    r"\broguelike\b",
    r"\btower\s*defen[sc]e\b",
    r"\bside[- ]?scroll(?:er|ing)?\b",
    r"\bendless\s*runner\b",
]

_THEME_PATTERNS = [
    r"\bfantasy\b", r"\bsci[- ]?fi\b", r"\bspace\b", r"\bmodern\b",
    r"\bmedieval\b", r"\bpixel\b", r"\bretro\b", r"\bneon\b",
    r"\bhorror\b", r"\bcartoon\b", r"\bcute\b", r"\bdark\b",
    r"\bnature\b", r"\bocean\b", r"\bunder\s*water\b", r"\bjungle\b",
    r"\bdesert\b", r"\bcity\b", r"\burban\b", r"\bcyber\s*punk\b",
    r"\bsteam\s*punk\b", r"\bpost[- ]?apocalyp\b", r"\bwest(?:ern)?\b",
    r"\bninja\b", r"\bsamurai\b", r"\bpirate\b", r"\bzombie\b",
    r"\bknight\b", r"\brobot\b", r"\balien\b", r"\bwizard\b",
]

_YES_PATTERNS = [
    r"\byes\b", r"\byeah\b", r"\byep\b", r"\bsure\b", r"\bok(?:ay)?\b",
    r"\bgo\s*ahead\b", r"\bdo\s*it\b", r"\blet'?s\s*go\b",
    r"\bperfect\b", r"\bgreat\b", r"\bawesome\b", r"\blooks?\s*good\b",
    r"\bthat'?s?\s*(?:right|correct|good|fine)\b", r"\bconfirm\b",
    r"\bgenerate\b", r"\bbuild\b", r"\bcreate\b", r"\bmake\s*it\b",
]

_NO_PATTERNS = [
    r"\bno\b", r"\bnah\b", r"\bnope\b", r"\bwait\b", r"\bchange\b",
    r"\bmodify\b", r"\bactually\b", r"\bhmm\b", r"\bnot\s*(?:quite|right)\b",
    r"\bgo\s*back\b", r"\bedit\b",
]

_READY_PATTERNS = [
    r"\bready\b", r"\bthat'?s?\s*(?:all|it|everything)\b",
    r"\bdone\b.*\bdescrib", r"\bnothing\s*else\b",
    r"\bgenerate\b", r"\bbuild\s*(?:it|my|the)\b",
    r"\bcreate\s*(?:it|my|the)\b", r"\bmake\s*(?:it|my|the)\b",
    r"\bstart\s*generat",
]

_START_OVER = [
    r"\bstart\s*over\b", r"\breset\b", r"\bnew\s*game\b",
    r"\bfrom\s*scratch\b", r"\bclear\b",
]

_LONG_DESCRIPTION_MIN_WORDS = 12


def classify_intent(text: str, state: ConversationState) -> Intent:
    low = text.lower().strip()

    if _any_match(_START_OVER, low):
        return Intent.START_OVER

    if state == ConversationState.CONFIRMING:
        if _any_match(_YES_PATTERNS, low):
            return Intent.CONFIRM_YES
        if _any_match(_NO_PATTERNS, low):
            return Intent.CONFIRM_NO

    if _any_match(_READY_PATTERNS, low) and state in (
        ConversationState.DETAIL_GATHERING,
        ConversationState.THEME_SELECTION,
    ):
        if _any_match(_GENRE_PATTERNS, low) or len(low.split()) >= _LONG_DESCRIPTION_MIN_WORDS:
            pass  # fall through — this is a description that happens to contain "build"
        else:
            return Intent.GENERATE_NOW

    word_count = len(low.split())
    has_genre = _any_match(_GENRE_PATTERNS, low)
    has_theme = _any_match(_THEME_PATTERNS, low)

    if word_count >= _LONG_DESCRIPTION_MIN_WORDS:
        return Intent.DESCRIBE_GAME

    if has_genre and has_theme:
        return Intent.DESCRIBE_GAME

    if has_genre:
        return Intent.SELECT_GENRE

    if has_theme:
        return Intent.SET_THEME

    if state in (
        ConversationState.DETAIL_GATHERING,
        ConversationState.THEME_SELECTION,
    ) and word_count >= 3:
        return Intent.ADD_DETAIL

    return Intent.GENERAL_CHAT


def _any_match(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)
