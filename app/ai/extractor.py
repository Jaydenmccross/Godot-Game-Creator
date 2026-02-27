"""Extract structured game parameters from free-text user messages."""

from __future__ import annotations

import re
from app.models import Genre

_GENRE_MAP: dict[str, Genre] = {
    "platformer": Genre.PLATFORMER,
    "platform": Genre.PLATFORMER,
    "platforming": Genre.PLATFORMER,
    "side-scroller": Genre.PLATFORMER,
    "sidescroller": Genre.PLATFORMER,
    "side scroller": Genre.PLATFORMER,
    "endless runner": Genre.PLATFORMER,
    "topdown": Genre.TOPDOWN,
    "top-down": Genre.TOPDOWN,
    "top down": Genre.TOPDOWN,
    "rpg": Genre.TOPDOWN,
    "adventure": Genre.TOPDOWN,
    "action adventure": Genre.TOPDOWN,
    "zelda": Genre.TOPDOWN,
    "survival": Genre.TOPDOWN,
    "roguelike": Genre.TOPDOWN,
    "shooter": Genre.SHOOTER,
    "shoot em up": Genre.SHOOTER,
    "shoot'em up": Genre.SHOOTER,
    "shmup": Genre.SHOOTER,
    "space shooter": Genre.SHOOTER,
    "bullet hell": Genre.SHOOTER,
    "tower defense": Genre.SHOOTER,
    "puzzle": Genre.PUZZLE,
    "match": Genre.PUZZLE,
    "brain teaser": Genre.PUZZLE,
    "logic": Genre.PUZZLE,
    "visual novel": Genre.VISUAL_NOVEL,
    "story game": Genre.VISUAL_NOVEL,
    "narrative": Genre.VISUAL_NOVEL,
    "dating sim": Genre.VISUAL_NOVEL,
    "text adventure": Genre.VISUAL_NOVEL,
    "racing": Genre.RACING,
    "race": Genre.RACING,
    "driving": Genre.RACING,
    "car": Genre.RACING,
    "kart": Genre.RACING,
}

_THEME_KEYWORDS: list[str] = [
    "fantasy", "sci-fi", "scifi", "science fiction", "space", "modern",
    "medieval", "pixel", "retro", "neon", "horror", "cartoon", "cute",
    "dark", "nature", "ocean", "underwater", "jungle", "desert", "city",
    "urban", "cyberpunk", "steampunk", "post-apocalyptic", "western",
    "ninja", "samurai", "pirate", "zombie", "knight", "robot", "alien",
    "wizard", "magic", "futuristic", "prehistoric", "ice", "snow",
    "volcanic", "tropical", "haunted", "enchanted", "celestial",
]

_DIFFICULTY_MAP = {
    "easy": "easy",
    "simple": "easy",
    "beginner": "easy",
    "casual": "easy",
    "normal": "normal",
    "medium": "normal",
    "moderate": "normal",
    "hard": "hard",
    "difficult": "hard",
    "challenging": "hard",
    "extreme": "hard",
    "brutal": "hard",
    "impossible": "hard",
}


def extract_game_params(text: str) -> dict:
    """Return a dict of game-spec fields extracted from *text*."""
    low = text.lower()
    params: dict = {}

    genre = _extract_genre(low)
    if genre is not None:
        params["genre"] = genre

    theme = _extract_theme(low)
    if theme:
        params["theme"] = theme

    name = _extract_name(text)
    if name:
        params["name"] = name

    player = _extract_player_name(text)
    if player:
        params["player_name"] = player

    if re.search(r"\b(?:no|without|remove|disable)\s+(?:enem(?:y|ies))", low):
        params["has_enemies"] = False
    elif re.search(r"\benem(?:y|ies)\b", low):
        params["has_enemies"] = True

    if re.search(r"\b(?:coin|collect|gem|star|pickup|loot)\b", low):
        params["has_collectibles"] = True
    if re.search(r"\b(?:no|without|remove)\s+(?:coin|collect|pickup)\b", low):
        params["has_collectibles"] = False

    if re.search(r"\b(?:power[- ]?up|boost|upgrade|ability|shield)\b", low):
        params["has_powerups"] = True

    if re.search(r"\b(?:dialog|dialogue|story|narrative|npc|talk|quest)\b", low):
        params["has_dialogue"] = True

    if re.search(r"\b(?:particle|sparkle|trail|dust|ember|glow|smoke)\b", low):
        params["has_particles"] = True
    if re.search(r"\b(?:parallax|layered\s*back|scrolling\s*back)\b", low):
        params["has_parallax_bg"] = True

    particle_map = {
        "fire": "fire", "flame": "fire", "ember": "fire",
        "sparkle": "sparkle", "glitter": "sparkle", "shimmer": "sparkle",
        "rain": "rain", "raindrop": "rain",
        "snow": "snow", "snowflake": "snow",
        "dust": "dust", "sand": "dust",
        "smoke": "smoke", "fog": "smoke", "mist": "smoke",
        "star": "stars", "twinkle": "stars",
        "leaf": "leaves", "leaves": "leaves", "petal": "leaves",
        "bubble": "bubbles",
    }
    for kw, ptype in particle_map.items():
        if re.search(rf"\b{kw}\b", low):
            params["particle_type"] = ptype
            params["has_particles"] = True
            break

    weather_map = {
        "rain": "rain", "rainy": "rain", "storm": "rain",
        "snow": "snow", "snowy": "snow", "blizzard": "snow",
        "fog": "fog", "foggy": "fog", "misty": "fog",
        "wind": "wind", "windy": "wind",
    }
    for kw, wtype in weather_map.items():
        if re.search(rf"\b{kw}\s*(?:weather|effect)?\b", low):
            params["weather"] = wtype
            break

    color_map = {
        r"\b(?:red|crimson|scarlet)\b": ("#e74c3c", None),
        r"\b(?:blue|azure|cobalt)\b": ("#3498db", None),
        r"\b(?:green|emerald|lime)\b": ("#2ecc71", None),
        r"\b(?:purple|violet|lavender)\b": ("#9b59b6", None),
        r"\b(?:orange|amber|tangerine)\b": ("#e67e22", None),
        r"\b(?:pink|magenta|fuchsia)\b": ("#e84393", None),
        r"\b(?:cyan|teal|turquoise)\b": ("#00cec9", None),
        r"\b(?:gold|golden|yellow)\b": ("#f1c40f", None),
    }
    for pattern, (color, _) in color_map.items():
        if re.search(pattern, low) and re.search(r"\b(?:player|hero|character|primary)\b", low):
            params["color_primary"] = color
        elif re.search(pattern, low) and re.search(r"\b(?:enemy|foe|opponent|secondary)\b", low):
            params["color_secondary"] = color
        elif re.search(pattern, low) and re.search(r"\b(?:background|bg|backdrop)\b", low):
            params["color_bg"] = color

    for kw, diff in _DIFFICULTY_MAP.items():
        if re.search(rf"\b{kw}\b", low):
            params["difficulty"] = diff
            break

    if len(text.split()) >= 12:
        params["description"] = text

    return params


def _extract_genre(low: str) -> Genre | None:
    best: Genre | None = None
    best_pos = len(low) + 1
    for keyword, genre in _GENRE_MAP.items():
        idx = low.find(keyword)
        if idx != -1 and idx < best_pos:
            best = genre
            best_pos = idx
    return best


def _extract_theme(low: str) -> str | None:
    for kw in _THEME_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", low):
            return kw.replace("-", " ").title().replace(" ", " ").strip()
    return None


def _extract_name(text: str) -> str | None:
    m = re.search(r'(?:call\s+it|called|named?|title[d]?)\s+"([^"]{1,40})"', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'"([A-Za-z][\w\s\']{1,30})"', text)
    if m:
        return m.group(1).strip()
    m = re.search(
        r"(?:call\s+it|called|named?|title[d]?)\s+([A-Z][\w']{0,15}(?:\s+[A-Z][\w']{0,15}){0,3})",
        text,
    )
    if m:
        return m.group(1).strip()
    return None


def _extract_player_name(text: str) -> str | None:
    m = re.search(
        r'(?:player|character|hero|protagonist)\s+(?:is\s+|named?\s+|called?\s+)["\']?([A-Z]\w{1,20})["\']?',
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return None
