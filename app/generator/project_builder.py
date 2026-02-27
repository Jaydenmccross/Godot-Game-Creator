"""Orchestrator: takes a GameSpec and produces a complete Godot 4 project."""

from __future__ import annotations

import shutil
from pathlib import Path

from app.config import GENERATED_GAMES_DIR
from app.models import GameSpec, Genre
from app.generator.godot_project import write_project_file
from app.generator.installer_builder import generate_installers
from app.generator.templates.platformer import PlatformerTemplate
from app.generator.templates.topdown import TopdownTemplate
from app.generator.templates.shooter import ShooterTemplate
from app.generator.templates.puzzle import PuzzleTemplate
from app.generator.templates.visual_novel import VisualNovelTemplate
from app.generator.templates.racing import RacingTemplate
from app.art.art_generator import GameArtGenerator

_TEMPLATE_MAP = {
    Genre.PLATFORMER: PlatformerTemplate,
    Genre.TOPDOWN: TopdownTemplate,
    Genre.SHOOTER: ShooterTemplate,
    Genre.PUZZLE: PuzzleTemplate,
    Genre.VISUAL_NOVEL: VisualNovelTemplate,
    Genre.RACING: RacingTemplate,
}


async def generate_game(spec: GameSpec) -> dict:
    safe_name = spec.name.replace(" ", "_")
    project_dir = GENERATED_GAMES_DIR / safe_name
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True)

    for sub in ("scenes", "scripts", "assets", "ui"):
        (project_dir / sub).mkdir()

    write_project_file(project_dir, spec)

    # Try AI art generation (Pollinations.ai — free, no key)
    art_gen = GameArtGenerator(
        project_dir / "assets",
        theme=spec.theme,
        art_style=spec.art_style,
        genre=spec.genre.value,
    )
    art_results = {}
    try:
        art_results = await art_gen.generate_all(spec)
        art_count = sum(1 for v in art_results.values() if v)
        print(f"[art] Generated {art_count}/{len(art_results)} AI art assets")
    except Exception as e:
        print(f"[art] AI art generation failed ({e}), using procedural fallback")

    template_cls = _TEMPLATE_MAP.get(spec.genre, PlatformerTemplate)
    template = template_cls(spec, project_dir)
    template.has_ai_art = any(art_results.values())
    template.art_results = art_results
    template.generate()

    generate_installers(project_dir, spec)

    return {
        "project_dir": str(project_dir),
        "name": spec.name,
        "genre": spec.genre.value,
        "ai_art_count": sum(1 for v in art_results.values() if v),
    }
