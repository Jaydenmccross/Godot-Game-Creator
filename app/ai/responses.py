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

_GENRE_VISUAL_TIPS = {
    Genre.PLATFORMER: "Try adding *parallax backgrounds*, *dust particles* on landing, or *animated coin sparkles*!",
    Genre.TOPDOWN: "Consider *torch glow particles*, *grass terrain*, or *fog of war* effects!",
    Genre.SHOOTER: "How about *explosion particles*, *engine trails*, or a *nebula starfield* background?",
    Genre.PUZZLE: "Add *match sparkle effects*, *tile glow animations*, or a *gradient background*!",
    Genre.VISUAL_NOVEL: "Try *falling cherry blossoms*, *rain weather*, or *character emotion sprites*!",
    Genre.RACING: "Consider *tire smoke particles*, *speed line effects*, or *neon track edges*!",
}


def build_response(session: SessionData, intent: Intent) -> str:
    state = session.state
    spec = session.spec

    if intent == Intent.START_OVER:
        return (
            "No problem — let's start fresh!\n\n"
            "What kind of game would you like to create? You can pick a genre "
            "or just describe your dream game in your own words — the more "
            "detail the better!\n\n"
            "**Tip:** Mention visual elements like *particle effects*, "
            "*background styles*, *terrain types*, and *color palettes* "
            "for a richer game.\n\n"
            "**Available genres:** Platformer · Top-Down Adventure · "
            "Space Shooter · Puzzle · Visual Novel · Racing"
        )

    if state == ConversationState.GREETING:
        return (
            "Welcome to **Godot Game Creator** — your AI-powered game studio!\n\n"
            "Tell me about the game you want to build. You can:\n"
            "- Pick a genre (e.g. *\"I want a platformer\"*)\n"
            "- Describe your idea in detail (e.g. *\"A cyberpunk shooter with "
            "neon effects and rain particles\"*)\n"
            "- Or just chat and I'll guide you step by step\n\n"
            "**Pro tip:** The more visual details you describe — colors, "
            "particle effects, backgrounds, terrain — the more polished "
            "your game will look!\n\n"
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
            "🏎️ **Racing** — speed through tracks and dodge obstacles\n\n"
            "**Tip:** You can also describe the *mood* and *visual style* you want — "
            "like *\"a dark horror puzzle with fog effects\"*."
        )

    if state == ConversationState.THEME_SELECTION:
        genre_label = _GENRE_LABELS.get(spec.genre, spec.genre.value)
        visual_tip = _GENRE_VISUAL_TIPS.get(spec.genre, "")
        return (
            f"Awesome — a **{genre_label}**! Now let's set the vibe.\n\n"
            f"What theme or setting do you imagine? Some ideas:\n"
            f"- **Fantasy** — knights, dragons, enchanted forests\n"
            f"- **Sci-Fi** — spaceships, lasers, futuristic cities\n"
            f"- **Cyberpunk** — neon-lit dystopian worlds\n"
            f"- **Horror** — dark, spooky, atmospheric\n"
            f"- **Nature** — forests, oceans, mountains\n"
            f"- **Retro/Pixel** — classic arcade feel\n\n"
            f"🎨 **Visual tip:** {visual_tip}\n\n"
            f"The preview panel on the right updates in real-time as you describe!"
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
        if spec.has_particles:
            parts.append(f"- **Particles:** {spec.particle_type.title() if spec.particle_type != 'none' else 'Yes'}")
        if spec.has_parallax_bg:
            parts.append("- **Parallax Background:** Yes")
        if spec.weather != "none":
            parts.append(f"- **Weather:** {spec.weather.title()}")
        parts.append(f"- **Difficulty:** {spec.difficulty.title()}")
        parts.append(
            "\n**Want to enhance your game?** Try adding:\n"
            "- 🎨 *Visual elements:* sprite colors, backgrounds, terrain styles\n"
            "- ✨ *Effects:* particles, weather, glow, parallax scrolling\n"
            "- ⚔️ *Features:* power-ups, enemies, dialogue, collectibles\n"
            "- 🎯 *Details:* difficulty, player name, game title\n\n"
            "Check the **preview** on the right to see your game take shape!\n"
            "Say **\"generate it\"** when you're ready."
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
        )
        if spec.has_particles:
            summary += f"- Particles: {spec.particle_type.title() if spec.particle_type != 'none' else 'Yes'}\n"
        if spec.weather != "none":
            summary += f"- Weather: {spec.weather.title()}\n"
        summary += (
            f"- Difficulty: {spec.difficulty.title()}\n\n"
            f"Check the **preview** for a visual snapshot of your game.\n"
            f"Shall I generate it? Say **yes** to build, or describe changes.\n"
            f"Use the **undo** button if you want to revert your last change."
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
            f"Click **Download** to get your complete Godot 4 project with "
            f"built-in installers for Windows, Linux, and macOS.\n\n"
            f"The ZIP includes `Setup.exe`, launcher scripts, and a README.\n"
            f"Just unzip and run the installer — zero scripting required.\n\n"
            f"Want to create another game? Just say **\"start over\"**!"
        )

    return (
        "I'm here to help you create games! Tell me what kind of game "
        "you'd like to build, or pick a genre to get started."
    )
