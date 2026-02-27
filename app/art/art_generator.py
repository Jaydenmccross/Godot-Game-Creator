"""AI Art Generator — creates game assets via AI Horde (free, no API key).

AI Horde (stablehorde.net) is a free distributed Stable Diffusion network.
Uses the anonymous API key "0000000000" for free-tier access.

Flow: POST async request → poll for completion → download image URL.
"""

from __future__ import annotations

import asyncio
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

HORDE_API = "https://stablehorde.net/api/v2"
ANON_KEY = "0000000000"
POLL_INTERVAL = 8
MAX_POLLS = 30


def _post_json(url: str, data: dict, api_key: str = ANON_KEY) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "apikey": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[art] POST error: {e}")
        return {}


def _get_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[art] GET error: {e}")
        return {}


async def generate_image(prompt: str, dest: Path,
                         width: int = 512, height: int = 512,
                         model: str = "Deliberate") -> bool:
    """Submit an image generation job and wait for result. Returns True on success."""
    payload = {
        "prompt": prompt,
        "params": {
            "width": width,
            "height": height,
            "steps": 25,
            "sampler_name": "k_euler",
            "cfg_scale": 7,
        },
        "nsfw": False,
        "models": [model],
        "r2": True,
    }

    result = await asyncio.to_thread(_post_json, f"{HORDE_API}/generate/async", payload)
    job_id = result.get("id")
    if not job_id:
        print(f"[art] Failed to submit job for {dest.name}: {result}")
        return False

    for _ in range(MAX_POLLS):
        await asyncio.sleep(POLL_INTERVAL)
        check = await asyncio.to_thread(_get_json, f"{HORDE_API}/generate/check/{job_id}")
        if check.get("done"):
            break
    else:
        print(f"[art] Timeout waiting for {dest.name}")
        return False

    status = await asyncio.to_thread(_get_json, f"{HORDE_API}/generate/status/{job_id}")
    generations = status.get("generations", [])
    if not generations:
        print(f"[art] No generations for {dest.name}")
        return False

    img_url = generations[0].get("img", "")
    if not img_url.startswith("http"):
        print(f"[art] No image URL for {dest.name}")
        return False

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(img_url, str(dest))
        # Convert webp to png for Godot compatibility
        _convert_to_png(dest)
        return True
    except Exception as e:
        print(f"[art] Download error for {dest.name}: {e}")
        return False


def _convert_to_png(path: Path) -> None:
    """Convert webp to PNG using Pillow if available, otherwise keep as-is."""
    try:
        from PIL import Image
        img = Image.open(str(path))
        png_path = path.with_suffix(".png")
        img.save(str(png_path), "PNG")
        if png_path != path:
            path.unlink(missing_ok=True)
    except ImportError:
        pass
    except Exception:
        pass


class GameArtGenerator:
    """Generates a full set of game art assets for a project."""

    def __init__(self, assets_dir: Path, theme: str, art_style: str, genre: str) -> None:
        self.assets_dir = assets_dir
        self.theme = theme
        self.art_style = art_style
        self.genre = genre
        self._style = self._build_style()

    def _build_style(self) -> str:
        parts = [self.theme]
        if self.art_style and self.art_style not in ("simple", ""):
            parts.append(self.art_style + " style")
        parts.append("game art")
        parts.append("clean sharp")
        parts.append("high quality")
        return ", ".join(parts)

    async def generate_all(self, spec) -> dict[str, bool]:
        """Generate all game assets in parallel batches. Returns dict of name->success."""
        requests = self._build_request_list(spec)
        results = {}

        # Process in batches of 3 to be nice to the free API
        batch_size = 3
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            tasks = [
                generate_image(prompt, self.assets_dir / name, w, h)
                for name, prompt, w, h in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for j, (name, _, _, _) in enumerate(batch):
                res = batch_results[j]
                results[name] = res is True
                status = "✓" if res is True else "✗"
                print(f"[art] {status} {name}")

        return results

    def _build_request_list(self, spec) -> list[tuple[str, str, int, int]]:
        """Build list of (filename, prompt, width, height) for all needed assets."""
        genre_desc = {
            "platformer": "side-view 2D platformer",
            "topdown": "top-down RPG",
            "shooter": "space shooter",
            "racing": "racing game",
            "puzzle": "puzzle game",
            "visual_novel": "visual novel",
        }.get(self.genre, "2D game")

        player_name = spec.player_name if hasattr(spec, "player_name") else "hero"

        return [
            (
                "player_idle.png",
                f"{genre_desc} character sprite, {player_name} standing idle pose, "
                f"facing right, full body, {self._style}, centered on canvas, "
                f"solid color background, no text",
                256, 256,
            ),
            (
                "player_run.png",
                f"{genre_desc} character sprite, {player_name} running dynamic stride, "
                f"facing right, full body, {self._style}, centered, solid background, no text",
                256, 256,
            ),
            (
                "player_jump.png",
                f"{genre_desc} character sprite, {player_name} jumping pose arms up, "
                f"facing right, full body, {self._style}, centered, solid background, no text",
                256, 256,
            ),
            (
                "player_attack.png",
                f"{genre_desc} character sprite, {player_name} attacking with weapon, "
                f"facing right, full body, {self._style}, centered, solid background, no text",
                256, 256,
            ),
            (
                "enemy_1.png",
                f"{genre_desc} enemy creature sprite, menacing {self.theme} monster, "
                f"full body side view, {self._style}, centered, solid background",
                256, 256,
            ),
            (
                "enemy_2.png",
                f"{genre_desc} flying enemy sprite, {self.theme} winged creature, "
                f"full body, {self._style}, centered, solid background",
                256, 256,
            ),
            (
                "collectible.png",
                f"glowing magical collectible orb icon, {self.theme} theme, "
                f"game item, shiny, {self._style}, centered, solid dark background",
                128, 128,
            ),
            (
                "background_far.png",
                f"panoramic game background landscape, {self.theme}, "
                f"far distance, atmospheric, {self._style}, wide",
                1024, 512,
            ),
        ]
