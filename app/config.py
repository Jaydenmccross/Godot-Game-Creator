from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_GAMES_DIR = BASE_DIR / "generated_games"
STATIC_DIR = Path(__file__).resolve().parent / "static"
GODOT_BIN = "godot"

GENERATED_GAMES_DIR.mkdir(exist_ok=True)
