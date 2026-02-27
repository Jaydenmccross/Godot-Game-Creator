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

    template_cls = _TEMPLATE_MAP.get(spec.genre, PlatformerTemplate)
    template = template_cls(spec, project_dir)
    template.generate()

    generate_installers(project_dir, spec)

    return {
        "project_dir": str(project_dir),
        "name": spec.name,
        "genre": spec.genre.value,
    }
