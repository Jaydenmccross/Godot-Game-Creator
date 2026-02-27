"""Godot MCP bridge — validates generated projects via Godot headless mode.

This module uses Godot's --headless mode to perform static validation of
generated projects (script syntax, scene integrity) without requiring a
display server. It follows the MCP pattern of tool-based interaction with
the engine.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from app.config import GODOT_BIN


async def validate_project(project_dir: str) -> str:
    """Run Godot in headless mode to validate the project and return log output."""
    pdir = Path(project_dir)
    if not (pdir / "project.godot").exists():
        return "ERROR: project.godot not found"

    log_lines: list[str] = []
    log_lines.append(f"Validating project: {pdir.name}")
    log_lines.append("-" * 40)

    gd_files = list(pdir.rglob("*.gd"))
    log_lines.append(f"Found {len(gd_files)} GDScript file(s)")

    tscn_files = list(pdir.rglob("*.tscn"))
    log_lines.append(f"Found {len(tscn_files)} scene file(s)")

    try:
        proc = await asyncio.create_subprocess_exec(
            GODOT_BIN, "--headless", "--quit",
            cwd=str(pdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "HOME": os.environ.get("HOME", "/tmp")},
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode(errors="replace").strip()
        if output:
            log_lines.append("\nGodot output:")
            log_lines.append(output)

        if proc.returncode == 0:
            log_lines.append("\n✓ Project validated successfully")
        else:
            log_lines.append(f"\n✗ Godot exited with code {proc.returncode}")
    except asyncio.TimeoutError:
        log_lines.append("\n⚠ Validation timed out (30s)")
    except FileNotFoundError:
        log_lines.append(f"\n⚠ Godot binary not found at: {GODOT_BIN}")
        log_lines.append("  Project files were generated — open manually in Godot.")

    return "\n".join(log_lines)


async def run_script_check(project_dir: str, script_path: str) -> str:
    """Check a single GDScript file for errors."""
    try:
        proc = await asyncio.create_subprocess_exec(
            GODOT_BIN, "--headless", "--check-only",
            "--script", script_path,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        return stdout.decode(errors="replace").strip()
    except Exception as exc:
        return f"Error checking script: {exc}"
