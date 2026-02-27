"""Build rich conversational responses based on session state and intent."""

from __future__ import annotations

from app.ai.intent import Intent
from app.models import ConversationState, Genre, SessionData

_GENRE_LABELS = {
    Genre.PLATFORMER: "2D Platformer",
    Genre.TOPDOWN: "Top-Down Adventure",
    Genre.SHOOTER: "Space Shooter",
    Genre.PUZZLE: "Puzzle Game",
    Genre.VISUAL_NOVEL: "Visual Novel",
    Genre.RACING: "Racing Game",
}


def build_response(session: SessionData, intent: Intent) -> str:
    state = session.state
    spec = session.spec

    if intent == Intent.START_OVER:
        return (
            "No problem — let's start fresh!\n\n"
            "What kind of game would you like to create? You can pick a genre "
            "or just describe your dream game in your own words.\n\n"
            "**Available genres:** Platformer · Top-Down Adventure · "
            "Space Shooter · Puzzle · Visual Novel · Racing"
        )

    if state == ConversationState.GREETING:
        return (
            "Welcome to **Godot Game Creator** — your AI-powered game studio!\n\n"
            "Tell me about the game you want to build. You can:\n"
            "- Pick a genre (e.g. *\"I want a platformer\"*)\n"
            "- Describe your idea (e.g. *\"A space shooter where you fight aliens\"*)\n"
            "- Or just chat and I'll guide you step by step\n\n"
            "**Available genres:** Platformer · Top-Down Adventure · "
            "Space Shooter · Puzzle · Visual Novel · Racing"
        )

    if state == ConversationState.GENRE_SELECTION:
        return (
            "What type of game excites you? Pick one or describe your vision:\n\n"
            "🎮 **Platformer** — run, jump, and explore side-scrolling levels\n"
            "🗺️ **Top-Down Adventure** — explore a world from above, RPG style\n"
            "🚀 **Space Shooter** — blast enemies in intense shoot-em-up action\n"
            "🧩 **Puzzle** — solve brain-teasing challenges\n"
            "📖 **Visual Novel** — tell a story with choices and characters\n"
            "🏎️ **Racing** — speed through tracks and dodge obstacles"
        )

    if state == ConversationState.THEME_SELECTION:
        genre_label = _GENRE_LABELS.get(spec.genre, spec.genre.value)
        return (
            f"Awesome — a **{genre_label}**! Now let's set the vibe.\n\n"
            f"What theme or setting do you imagine? Some ideas:\n"
            f"- **Fantasy** — knights, dragons, enchanted forests\n"
            f"- **Sci-Fi** — spaceships, lasers, futuristic cities\n"
            f"- **Retro/Pixel** — classic arcade feel\n"
            f"- **Horror** — dark, spooky, atmospheric\n"
            f"- **Cyberpunk** — neon-lit dystopian worlds\n\n"
            f"Or describe your own unique setting!"
        )

    if state == ConversationState.DETAIL_GATHERING:
        genre_label = _GENRE_LABELS.get(spec.genre, spec.genre.value)
        theme = spec.theme.title() if spec.theme else "Custom"
        parts = [
            f"Here's what I have so far:\n",
            f"- **Genre:** {genre_label}",
            f"- **Theme:** {theme}",
            f"- **Player:** {spec.player_name}",
        ]
        if spec.has_enemies:
            parts.append("- **Enemies:** Yes")
        if spec.has_collectibles:
            parts.append("- **Collectibles:** Yes")
        if spec.has_powerups:
            parts.append("- **Power-ups:** Yes")
        if spec.has_dialogue:
            parts.append("- **Dialogue/Story:** Yes")
        parts.append(f"- **Difficulty:** {spec.difficulty.title()}")
        parts.append(
            "\nWant to add anything else? You can mention:\n"
            "- A game name (e.g. *call it \"Dragon Quest\"*)\n"
            "- Character details, enemies, power-ups, dialogue\n"
            "- Difficulty level\n\n"
            "Or say **\"generate it\"** when you're ready!"
        )
        return "\n".join(parts)

    if state == ConversationState.CONFIRMING:
        genre_label = _GENRE_LABELS.get(spec.genre, spec.genre.value)
        theme = spec.theme.title() if spec.theme else "Custom"
        summary = (
            f"Here's your game blueprint:\n\n"
            f"🎮 **{spec.name}**\n"
            f"- Genre: {genre_label}\n"
            f"- Theme: {theme}\n"
            f"- Player: {spec.player_name}\n"
            f"- Enemies: {'Yes' if spec.has_enemies else 'No'}\n"
            f"- Collectibles: {'Yes' if spec.has_collectibles else 'No'}\n"
            f"- Power-ups: {'Yes' if spec.has_powerups else 'No'}\n"
            f"- Dialogue: {'Yes' if spec.has_dialogue else 'No'}\n"
            f"- Difficulty: {spec.difficulty.title()}\n\n"
            f"Shall I generate this game? Say **yes** to build it, "
            f"or tell me what to change."
        )
        return summary

    if state == ConversationState.GENERATING:
        return (
            f"🔨 **Building your game now...**\n\n"
            f"Generating scenes, scripts, and resources for *{spec.name}*. "
            f"This will just take a moment."
        )

    if state == ConversationState.COMPLETE:
        return (
            f"Your game **{spec.name}** is ready!\n\n"
            f"Click the download button below to get your complete Godot 4 project. "
            f"Open it in Godot Engine and hit Play — zero scripting required.\n\n"
            f"Want to create another game? Just say **\"start over\"**!"
        )

    return (
        "I'm here to help you create games! Tell me what kind of game "
        "you'd like to build, or pick a genre to get started."
    )
