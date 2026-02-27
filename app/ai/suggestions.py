"""Context-aware suggestion engine.

Generates targeted, genre-specific suggestion chips that guide users toward
richer game feature requests — especially visual elements like sprites,
backgrounds, particles, terrain, and effects.
"""

from __future__ import annotations

from app.models import ConversationState, GameSpec, Genre, Suggestion

# ── Genre-specific feature suggestions ──────────────────────────────────

_GENRE_FEATURES: dict[Genre, list[Suggestion]] = {
    Genre.PLATFORMER: [
        Suggestion(text="Add double jump", category="mechanic"),
        Suggestion(text="Add wall sliding", category="mechanic"),
        Suggestion(text="Add moving platforms", category="level"),
        Suggestion(text="Add a boss enemy", category="enemy"),
        Suggestion(text="Add spike traps", category="level"),
        Suggestion(text="Add treasure chests", category="collectible"),
        Suggestion(text="Add parallax scrolling background", category="visual"),
        Suggestion(text="Add dust particles when landing", category="particle"),
        Suggestion(text="Add floating coin sparkle effects", category="particle"),
        Suggestion(text="Add lava terrain with glow", category="terrain"),
        Suggestion(text="Add animated water in background", category="visual"),
        Suggestion(text="Add checkpoint flags", category="level"),
    ],
    Genre.TOPDOWN: [
        Suggestion(text="Add quest-giving NPCs", category="mechanic"),
        Suggestion(text="Add inventory system", category="mechanic"),
        Suggestion(text="Add grass and tree terrain", category="terrain"),
        Suggestion(text="Add fog of war effect", category="visual"),
        Suggestion(text="Add torch light particles", category="particle"),
        Suggestion(text="Add footstep dust trail", category="particle"),
        Suggestion(text="Add water tiles with ripples", category="terrain"),
        Suggestion(text="Add day/night cycle", category="visual"),
        Suggestion(text="Add treasure map collectible", category="collectible"),
        Suggestion(text="Add patrol guard enemies", category="enemy"),
        Suggestion(text="Add healing potion power-up", category="powerup"),
        Suggestion(text="Add dungeon environment", category="terrain"),
    ],
    Genre.SHOOTER: [
        Suggestion(text="Add weapon upgrades", category="powerup"),
        Suggestion(text="Add shield power-up", category="powerup"),
        Suggestion(text="Add boss battles", category="enemy"),
        Suggestion(text="Add explosion particles", category="particle"),
        Suggestion(text="Add laser beam effects", category="visual"),
        Suggestion(text="Add scrolling starfield background", category="visual"),
        Suggestion(text="Add asteroid obstacles", category="level"),
        Suggestion(text="Add engine trail particles", category="particle"),
        Suggestion(text="Add screen shake on hit", category="visual"),
        Suggestion(text="Add nebula backgrounds", category="terrain"),
        Suggestion(text="Add combo score multiplier", category="mechanic"),
        Suggestion(text="Add homing missiles", category="mechanic"),
    ],
    Genre.PUZZLE: [
        Suggestion(text="Add timer challenge mode", category="mechanic"),
        Suggestion(text="Add hint system", category="mechanic"),
        Suggestion(text="Add match-3 sparkle effects", category="particle"),
        Suggestion(text="Add tile glow animations", category="visual"),
        Suggestion(text="Add combo chain effects", category="particle"),
        Suggestion(text="Add ambient floating particles", category="particle"),
        Suggestion(text="Add gradient background", category="visual"),
        Suggestion(text="Add level progression", category="level"),
        Suggestion(text="Add star rating system", category="mechanic"),
        Suggestion(text="Add tile pop animations", category="visual"),
        Suggestion(text="Add streak counter", category="mechanic"),
        Suggestion(text="Add special power tiles", category="powerup"),
    ],
    Genre.VISUAL_NOVEL: [
        Suggestion(text="Add multiple story endings", category="mechanic"),
        Suggestion(text="Add character emotion sprites", category="visual"),
        Suggestion(text="Add background scene transitions", category="visual"),
        Suggestion(text="Add rain weather effect", category="particle"),
        Suggestion(text="Add falling cherry blossoms", category="particle"),
        Suggestion(text="Add text typing animation", category="visual"),
        Suggestion(text="Add character relationship meter", category="mechanic"),
        Suggestion(text="Add dream sequence visuals", category="visual"),
        Suggestion(text="Add ambient firefly particles", category="particle"),
        Suggestion(text="Add portrait frame effects", category="visual"),
        Suggestion(text="Add save/load system", category="mechanic"),
        Suggestion(text="Add flashback tint effect", category="visual"),
    ],
    Genre.RACING: [
        Suggestion(text="Add nitro boost", category="powerup"),
        Suggestion(text="Add speed line effects", category="visual"),
        Suggestion(text="Add tire smoke particles", category="particle"),
        Suggestion(text="Add oil slick obstacles", category="level"),
        Suggestion(text="Add ramp jumps", category="level"),
        Suggestion(text="Add rain weather effect", category="particle"),
        Suggestion(text="Add neon track edges", category="terrain"),
        Suggestion(text="Add checkpoint gates", category="level"),
        Suggestion(text="Add road terrain types", category="terrain"),
        Suggestion(text="Add spark collision effects", category="particle"),
        Suggestion(text="Add dynamic sky background", category="visual"),
        Suggestion(text="Add lap counter", category="mechanic"),
    ],
}

# ── Theme-specific visual suggestions ───────────────────────────────────

_THEME_VISUALS: dict[str, list[Suggestion]] = {
    "fantasy": [
        Suggestion(text="Add enchanted forest background", category="terrain"),
        Suggestion(text="Add magical sparkle particles", category="particle"),
        Suggestion(text="Add castle backdrop", category="visual"),
        Suggestion(text="Use emerald green + royal purple palette", category="color"),
    ],
    "sci-fi": [
        Suggestion(text="Add hologram UI effects", category="visual"),
        Suggestion(text="Add electric arc particles", category="particle"),
        Suggestion(text="Add space station backdrop", category="terrain"),
        Suggestion(text="Use cyan + electric blue palette", category="color"),
    ],
    "horror": [
        Suggestion(text="Add fog and mist particles", category="particle"),
        Suggestion(text="Add flickering light effect", category="visual"),
        Suggestion(text="Add dark forest terrain", category="terrain"),
        Suggestion(text="Use deep red + dark grey palette", category="color"),
    ],
    "cyberpunk": [
        Suggestion(text="Add neon glow effects", category="visual"),
        Suggestion(text="Add rain particles", category="particle"),
        Suggestion(text="Add city skyline backdrop", category="terrain"),
        Suggestion(text="Use hot pink + electric cyan palette", category="color"),
    ],
    "retro": [
        Suggestion(text="Add CRT scanline effect", category="visual"),
        Suggestion(text="Add pixel dust particles", category="particle"),
        Suggestion(text="Use 8-bit color palette", category="color"),
        Suggestion(text="Add chunky pixel terrain", category="terrain"),
    ],
    "nature": [
        Suggestion(text="Add falling leaf particles", category="particle"),
        Suggestion(text="Add rolling hills terrain", category="terrain"),
        Suggestion(text="Add sunbeam light rays", category="visual"),
        Suggestion(text="Use earthy green + sky blue palette", category="color"),
    ],
    "ocean": [
        Suggestion(text="Add bubble particles", category="particle"),
        Suggestion(text="Add underwater light rays", category="visual"),
        Suggestion(text="Add coral reef terrain", category="terrain"),
        Suggestion(text="Use deep blue + turquoise palette", category="color"),
    ],
    "space": [
        Suggestion(text="Add twinkling star particles", category="particle"),
        Suggestion(text="Add nebula background layers", category="visual"),
        Suggestion(text="Add asteroid field terrain", category="terrain"),
        Suggestion(text="Use dark navy + bright white palette", category="color"),
    ],
}

# ── State-based guidance suggestions ────────────────────────────────────

_STATE_GUIDANCE: dict[ConversationState, list[Suggestion]] = {
    ConversationState.GREETING: [
        Suggestion(text="Help me choose a genre", category="help"),
        Suggestion(text="I have a specific idea", category="help"),
    ],
    ConversationState.GENRE_SELECTION: [
        Suggestion(text="What genres are available?", category="help"),
        Suggestion(text="Recommend a genre for beginners", category="help"),
    ],
    ConversationState.THEME_SELECTION: [
        Suggestion(text="Show me theme examples", category="help"),
        Suggestion(text="Pick a random theme", category="help"),
    ],
}

# ── Visual element suggestions (always available during detail_gathering) ─

_VISUAL_SUGGESTIONS: list[Suggestion] = [
    Suggestion(text="Customize player sprite colors", category="visual"),
    Suggestion(text="Add background particle effects", category="particle"),
    Suggestion(text="Change terrain style", category="terrain"),
    Suggestion(text="Customize enemy appearance", category="enemy"),
    Suggestion(text="Add weather effects", category="particle"),
    Suggestion(text="Set custom color palette", category="color"),
]


def get_suggestions(
    state: ConversationState,
    spec: GameSpec,
    max_count: int = 6,
) -> list[Suggestion]:
    """Return a prioritised list of contextual suggestions."""
    pool: list[Suggestion] = []

    if state in _STATE_GUIDANCE:
        pool.extend(_STATE_GUIDANCE[state])

    if state in (
        ConversationState.THEME_SELECTION,
        ConversationState.DETAIL_GATHERING,
        ConversationState.CONFIRMING,
    ):
        genre_sugs = _GENRE_FEATURES.get(spec.genre, [])
        pool.extend(_filter_relevant(genre_sugs, spec))

        theme_key = spec.theme.lower().replace(" ", "")
        for key, sugs in _THEME_VISUALS.items():
            if key in theme_key or theme_key in key:
                pool.extend(sugs)
                break

    if state == ConversationState.DETAIL_GATHERING:
        pool.extend(_VISUAL_SUGGESTIONS)

    seen: set[str] = set()
    unique: list[Suggestion] = []
    for s in pool:
        if s.text not in seen:
            seen.add(s.text)
            unique.append(s)

    return unique[:max_count]


def _filter_relevant(suggestions: list[Suggestion], spec: GameSpec) -> list[Suggestion]:
    """Remove suggestions for features the user already has."""
    result = []
    for s in suggestions:
        low = s.text.lower()
        if "enemy" in low and spec.has_enemies:
            continue
        if "collectible" in low and spec.has_collectibles:
            continue
        if "power-up" in low and spec.has_powerups:
            continue
        if "dialogue" in low and spec.has_dialogue:
            continue
        if "parallax" in low and spec.has_parallax_bg:
            continue
        if "particle" in low and spec.has_particles:
            continue
        result.append(s)
    return result


def get_help_text(state: ConversationState, spec: GameSpec) -> str:
    """Return rich help text for the current conversation state."""
    genre_label = {
        Genre.PLATFORMER: "2D Platformer",
        Genre.TOPDOWN: "Top-Down Adventure",
        Genre.SHOOTER: "Space Shooter",
        Genre.PUZZLE: "Puzzle Game",
        Genre.VISUAL_NOVEL: "Visual Novel",
        Genre.RACING: "Racing Game",
    }.get(spec.genre, "Game")

    if state == ConversationState.GREETING:
        return (
            "**Getting Started**\n\n"
            "Describe your dream game in as much detail as you like! "
            "Mention the genre, theme, visual style, characters, enemies, "
            "and any special effects you'd love to see.\n\n"
            "**Tip:** The more visual details you provide, the richer your game will be. "
            "Try mentioning particle effects, background styles, color palettes, and terrain types."
        )

    if state == ConversationState.DETAIL_GATHERING:
        return (
            f"**Customizing Your {genre_label}**\n\n"
            "You can refine any aspect of your game:\n\n"
            "**Visual Elements:**\n"
            "- Player/enemy sprite colors and styles\n"
            "- Background art and terrain types\n"
            "- Particle effects (fire, sparkles, rain, snow)\n"
            "- Weather effects and ambient visuals\n\n"
            "**Game Features:**\n"
            "- Power-ups and collectibles\n"
            "- Enemy types and behaviors\n"
            "- Difficulty and pacing\n"
            "- Story and dialogue elements\n\n"
            "**Tip:** Say things like *\"add fire particles\"*, "
            "*\"make the background a snowy mountain\"*, or "
            "*\"use neon pink and cyan colors\"*."
        )

    if state == ConversationState.CONFIRMING:
        return (
            "**Review & Generate**\n\n"
            "Check your game blueprint on the right.\n"
            "Say **yes** to generate, or describe changes.\n\n"
            "**Tip:** You can still add visual effects, change colors, "
            "or tweak any feature before generating."
        )

    return ""
