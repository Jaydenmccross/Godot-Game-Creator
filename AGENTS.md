# Godot Game Creator

A genre agnostic AI-powered game creation suite built with Godot 4 and FastAPI.

## Cursor Cloud specific instructions

### Architecture

- **Web App** (`app/`): FastAPI backend + vanilla HTML/CSS/JS frontend serving a chat UI at `http://localhost:8000`
- **AI Engine** (`app/ai/`): Intent classification, parameter extraction, and response generation for game-creation conversations
- **Generator** (`app/generator/`): Produces complete Godot 4 projects from a `GameSpec` — 6 genre templates (platformer, topdown, shooter, puzzle, visual_novel, racing)
- **MCP Bridge** (`app/mcp/`): Validates generated projects via `godot --headless --quit`
- **Godot Project** (root `project.godot`): Minimal hello-world project for environment verification

### Engine & Tools

- **Godot 4.4.1** installed at `/usr/local/bin/godot`
- **gdtoolkit 4.5.0** (pip) provides `gdlint` and `gdformat` for GDScript linting/formatting
- **FastAPI + uvicorn** for the web application
- Python pip user packages in `~/.local/bin` — ensure on PATH (`export PATH="$HOME/.local/bin:$PATH"`)

### Common commands

| Task | Command |
|---|---|
| Start web app | `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Run Godot project headless | `godot --headless --quit` |
| Validate GDScript | `godot --headless --check-only --script res://scripts/<file>.gd` |
| Lint all GDScript | `gdlint scripts/` |
| Format-check GDScript | `gdformat --check scripts/` |
| Auto-format GDScript | `gdformat scripts/` |
| Open Godot editor (GUI) | `godot --editor` |
| Run a generated game | `cd generated_games/<name> && godot --windowed` |

### Gotchas

- Godot needs the `project.godot` file in the working directory. Always `cd` into the correct project directory before running Godot.
- Headless mode (`--headless --quit`) runs `_ready()` on the main scene and exits. Generated projects with timers/spawners may cause `--quit` to hang briefly before the process terminates — the 30s timeout in `godot_mcp.py` handles this.
- `gdformat` uses two blank lines between top-level declarations (GDScript style convention). Let the formatter handle this.
- The Godot editor requires a display (X11/Wayland). In headless cloud VMs use `--headless` for validation or launch via the Desktop pane.
- Generated game descriptions with quotes must be sanitized — `godot_project.py` strips double-quotes from descriptions to avoid breaking `project.godot` parsing.
- The web app serves generated game downloads as ZIP files from `/generated_games/` directory.
