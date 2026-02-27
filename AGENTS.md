# Godot Game Creator

A genre agnostic game creation suite built with the Godot 4 engine.

## Cursor Cloud specific instructions

### Engine & Tools

- **Godot 4.4.1** is installed at `/usr/local/bin/godot`.
- **gdtoolkit 4.5.0** (pip) provides `gdlint` and `gdformat` for GDScript linting and formatting.
- Python pip user packages are in `~/.local/bin` — ensure this is on PATH (`export PATH="$HOME/.local/bin:$PATH"`).

### Common commands

| Task | Command |
|---|---|
| Run project headless | `godot --headless --quit` |
| Validate GDScript | `godot --headless --check-only --script res://scripts/<file>.gd` |
| Lint all GDScript | `gdlint scripts/` |
| Format-check GDScript | `gdformat --check scripts/` |
| Auto-format GDScript | `gdformat scripts/` |
| Open editor (GUI) | `godot --editor` |

### Gotchas

- Godot needs the `project.godot` file in the working directory to recognize the project. Always run commands from `/workspace`.
- Headless mode (`--headless --quit`) runs `_ready()` on the main scene and exits — useful for CI and smoke tests.
- `gdformat` uses two blank lines between top-level declarations (GDScript style convention). Let the formatter handle this rather than manually adding/removing blank lines.
- The Godot editor requires a display (X11/Wayland). In headless cloud VMs, use `--headless` for validation or launch the editor via the Desktop pane.
