"""Generates portable installer and launcher files for every game project.

Each generated game ZIP includes:
  - Setup.exe        — Native Windows GUI installer (downloads Godot, creates shortcut)
  - setup            — Native Linux installer binary
  - Play.bat         — Windows quick-launcher
  - Play.sh          — Linux/Mac quick-launcher
  - Play.command     — macOS double-clickable launcher
  - installer.pyw    — Cross-platform Python GUI installer (tkinter)
  - README.txt       — Instructions for the player
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.models import GameSpec

_ASSETS_DIR = Path(__file__).parent / "installer_assets"

_GODOT_WIN_URL = "https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_win64.exe.zip"
_GODOT_WIN_EXE = "Godot_v4.4.1-stable_win64.exe"
_GODOT_LINUX_URL = "https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_linux.x86_64.zip"
_GODOT_LINUX_BIN = "Godot_v4.4.1-stable_linux.x86_64"
_GODOT_MAC_URL = "https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_macos.universal.zip"


def generate_installers(project_dir: Path, spec: GameSpec) -> None:
    """Write all installer / launcher files into *project_dir*."""
    _copy_native_installers(project_dir)
    _write_play_bat(project_dir, spec)
    _write_play_sh(project_dir, spec)
    _write_play_command(project_dir, spec)
    _write_python_installer(project_dir, spec)
    _write_readme(project_dir, spec)


def _copy_native_installers(project_dir: Path) -> None:
    setup_exe = _ASSETS_DIR / "Setup.exe"
    if setup_exe.exists():
        shutil.copy2(setup_exe, project_dir / "Setup.exe")

    setup_linux = _ASSETS_DIR / "setup"
    if setup_linux.exists():
        dest = project_dir / "setup"
        shutil.copy2(setup_linux, dest)
        dest.chmod(0o755)


def _write_play_bat(project_dir: Path, spec: GameSpec) -> None:
    (project_dir / "Play.bat").write_text(
        f'@echo off\r\n'
        f'title {spec.name}\r\n'
        f'echo Starting {spec.name}...\r\n'
        f'\r\n'
        f'REM Check for engine in local folder first\r\n'
        f'if exist "engine\\{_GODOT_WIN_EXE}" (\r\n'
        f'    start "" "engine\\{_GODOT_WIN_EXE}" --path "%~dp0" --windowed\r\n'
        f'    exit /b\r\n'
        f')\r\n'
        f'\r\n'
        f'REM Check if Godot is on PATH\r\n'
        f'where godot >nul 2>&1\r\n'
        f'if %errorlevel%==0 (\r\n'
        f'    start "" godot --path "%~dp0" --windowed\r\n'
        f'    exit /b\r\n'
        f')\r\n'
        f'\r\n'
        f'echo Godot Engine not found.\r\n'
        f'echo Please run Setup.exe first to install the engine.\r\n'
        f'pause\r\n',
        newline="\r\n",
    )


def _write_play_sh(project_dir: Path, spec: GameSpec) -> None:
    p = project_dir / "Play.sh"
    p.write_text(
        f'#!/bin/bash\n'
        f'# {spec.name} — Quick Launcher\n'
        f'cd "$(dirname "$0")"\n'
        f'\n'
        f'# Try local engine first\n'
        f'if [ -f "engine/{_GODOT_LINUX_BIN}" ]; then\n'
        f'    ./engine/{_GODOT_LINUX_BIN} --path . --windowed "$@"\n'
        f'    exit 0\n'
        f'fi\n'
        f'\n'
        f'# Try system Godot\n'
        f'if command -v godot &>/dev/null; then\n'
        f'    godot --path . --windowed "$@"\n'
        f'    exit 0\n'
        f'fi\n'
        f'\n'
        f'echo "Godot Engine not found."\n'
        f'echo "Run ./setup first to install the engine."\n'
    )
    p.chmod(0o755)


def _write_play_command(project_dir: Path, spec: GameSpec) -> None:
    p = project_dir / "Play.command"
    p.write_text(
        f'#!/bin/bash\n'
        f'# {spec.name} — macOS Launcher\n'
        f'cd "$(dirname "$0")"\n'
        f'\n'
        f'if [ -d "engine/Godot.app" ]; then\n'
        f'    open engine/Godot.app --args --path "$(pwd)" --windowed\n'
        f'elif command -v godot &>/dev/null; then\n'
        f'    godot --path . --windowed\n'
        f'else\n'
        f'    echo "Godot Engine not found."\n'
        f'    echo "Download Godot from https://godotengine.org/download"\n'
        f'fi\n'
    )
    p.chmod(0o755)


def _write_python_installer(project_dir: Path, spec: GameSpec) -> None:
    """A cross-platform Python GUI installer using tkinter."""
    (project_dir / "installer.pyw").write_text(f'''#!/usr/bin/env python3
"""
{spec.name} — Cross-Platform Installer
Powered by Godot Game Creator

Works on Windows, macOS, and Linux.
Requires Python 3.7+ (tkinter is bundled with standard Python).
"""

import os
import platform
import subprocess
import sys
import threading
import urllib.request
import zipfile
from pathlib import Path

GAME_NAME = "{spec.name}"
INSTALL_DIR = Path(__file__).resolve().parent
ENGINE_DIR = INSTALL_DIR / "engine"

GODOT_URLS = {{
    "Windows": ("{_GODOT_WIN_URL}", "{_GODOT_WIN_EXE}"),
    "Linux":   ("{_GODOT_LINUX_URL}", "{_GODOT_LINUX_BIN}"),
    "Darwin":  ("{_GODOT_MAC_URL}", "Godot.app"),
}}


def get_platform_key():
    s = platform.system()
    return s if s in GODOT_URLS else "Linux"


def is_installed():
    key = get_platform_key()
    _, binary = GODOT_URLS[key]
    return (ENGINE_DIR / binary).exists()


def download_and_extract(on_progress=None, on_done=None):
    key = get_platform_key()
    url, binary = GODOT_URLS[key]
    ENGINE_DIR.mkdir(exist_ok=True)
    zip_path = ENGINE_DIR / "godot.zip"

    def progress_hook(block, block_size, total):
        if on_progress and total > 0:
            pct = min(100, int(block * block_size * 100 / total))
            on_progress(pct)

    try:
        urllib.request.urlretrieve(url, str(zip_path), progress_hook)
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            zf.extractall(str(ENGINE_DIR))
        zip_path.unlink()

        exe_path = ENGINE_DIR / binary
        if exe_path.exists() and platform.system() != "Windows":
            exe_path.chmod(0o755)

        if on_done:
            on_done(True, "")
    except Exception as e:
        if on_done:
            on_done(False, str(e))


def launch_game():
    key = get_platform_key()
    _, binary = GODOT_URLS[key]
    exe = ENGINE_DIR / binary

    if key == "Darwin" and (ENGINE_DIR / "Godot.app").is_dir():
        subprocess.Popen(["open", str(ENGINE_DIR / "Godot.app"),
                          "--args", "--path", str(INSTALL_DIR), "--windowed"])
    else:
        subprocess.Popen([str(exe), "--path", str(INSTALL_DIR), "--windowed"])


def run_gui():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("tkinter not available. Use ./Play.sh or Play.bat instead.")
        return

    root = tk.Tk()
    root.title(f"Install {{GAME_NAME}}")
    root.geometry("460x340")
    root.resizable(False, False)
    root.configure(bg="#1a1a2e")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#1a1a2e", foreground="#e8e8f0")
    style.configure("TButton", padding=6)
    style.configure("TProgressbar", troughcolor="#22223a", background="#6c5ce7")

    tk.Label(root, text=GAME_NAME, font=("Helvetica", 22, "bold"),
             bg="#1a1a2e", fg="#6c5ce7").pack(pady=(25, 5))
    tk.Label(root, text="Powered by Godot Game Creator",
             font=("Helvetica", 10), bg="#1a1a2e", fg="#9898b0").pack()

    status_var = tk.StringVar(value="Ready to install")
    tk.Label(root, textvariable=status_var, font=("Helvetica", 11),
             bg="#1a1a2e", fg="#e8e8f0").pack(pady=(30, 8))

    progress = ttk.Progressbar(root, length=380, mode="determinate",
                                style="TProgressbar")
    progress.pack(pady=5)

    btn_frame = tk.Frame(root, bg="#1a1a2e")
    btn_frame.pack(pady=25)

    def on_install():
        if is_installed():
            status_var.set("Already installed! Launching...")
            root.update()
            launch_game()
            root.after(1500, root.destroy)
            return

        install_btn.config(state="disabled")
        status_var.set("Downloading Godot Engine...")

        def on_prog(pct):
            progress["value"] = pct
            root.update_idletasks()

        def on_done(ok, err):
            if ok:
                progress["value"] = 100
                status_var.set("Installation complete! Launching game...")
                root.update()
                launch_game()
                root.after(2000, root.destroy)
            else:
                status_var.set(f"Error: {{err}}")
                install_btn.config(state="normal")

        threading.Thread(target=download_and_extract,
                         args=(on_prog, on_done), daemon=True).start()

    install_btn = tk.Button(btn_frame, text="  Install & Play  ",
                            font=("Helvetica", 13, "bold"),
                            bg="#6c5ce7", fg="white", relief="flat",
                            activebackground="#5a4bd6", command=on_install)
    install_btn.pack(side="left", padx=8)

    cancel_btn = tk.Button(btn_frame, text="  Cancel  ",
                           font=("Helvetica", 13), bg="#2a2a48", fg="#e8e8f0",
                           relief="flat", command=root.destroy)
    cancel_btn.pack(side="left", padx=8)

    root.mainloop()


if __name__ == "__main__":
    if "--headless" in sys.argv:
        if is_installed():
            print(f"{{GAME_NAME}} is already installed.")
        else:
            print(f"Installing {{GAME_NAME}}...")
            download_and_extract(
                on_progress=lambda p: print(f"  {{p}}%", end="\\r"),
                on_done=lambda ok, e: print("\\nDone!" if ok else f"\\nError: {{e}}"),
            )
        launch_game()
    else:
        run_gui()
''')


def _write_readme(project_dir: Path, spec: GameSpec) -> None:
    (project_dir / "README.txt").write_text(f"""
{'=' * 50}
  {spec.name}
  A {spec.theme.title()} {spec.genre.value.replace('_', ' ').title()}
{'=' * 50}

  Created with Godot Game Creator
  https://github.com/Jaydenmccross/Godot-Game-Creator

HOW TO PLAY
-----------

  WINDOWS:
    Double-click Setup.exe to install, then Play.bat to play.
    (Setup.exe downloads the free Godot Engine automatically.)

  LINUX:
    Run: ./setup
    Then: ./Play.sh

  macOS:
    Run: ./Play.command
    (Install Godot from https://godotengine.org if not found.)

  CROSS-PLATFORM (requires Python 3):
    Run: python installer.pyw

CONTROLS
--------

  Arrow Keys / WASD — Move
  Space — Jump / Action
  Enter / Left Click — Interact / Shoot
  Escape — Pause

REQUIREMENTS
------------

  - Windows 10+, Linux (x86_64), or macOS 10.15+
  - Internet connection (first run only, to download Godot Engine)
  - ~130 MB disk space for the engine

ALREADY HAVE GODOT?
-------------------

  If you already have Godot 4.4+ installed, just open
  project.godot in the Godot editor and press Play!

{'=' * 50}
""")
