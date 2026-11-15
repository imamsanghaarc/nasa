"""Headless smoke test: boots every scene and runs frames without a display.

Covers the current 4-level Mars campaign (Outpost -> Landing -> Surface ->
Tunnel), the tutorial, menu, map, briefing, pause and ending scene.

Run from the project root::

    python tools/smoke_test.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from core import audio, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game  # noqa: E402
from scenes.briefing import BriefingScene  # noqa: E402
from scenes.ending import EndingScene  # noqa: E402
from scenes.level1 import Level1Scene  # noqa: E402
from scenes.level2 import Level2Scene  # noqa: E402
from scenes.level3 import Level3Scene  # noqa: E402
from scenes.level4 import Level4Scene  # noqa: E402
from scenes.map import MapScene  # noqa: E402
from scenes.menu import MenuScene  # noqa: E402
from scenes.tutorial import TutorialScene  # noqa: E402
from ui.pause import PauseScene  # noqa: E402


def run_scene(game: Game, name: str, frames: int = 30, **enter) -> None:
    game.manager.switch(name, **enter)
    clock = pygame.time.Clock()
    for _ in range(frames):
        game.manager.handle_events([])
        dt = min(clock.tick(60) / 1000.0, 0.05)
        game.manager.update(dt)
        game.manager.draw()


def main() -> int:
    pygame.init()
    audio.init()
    pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    window = pygame.display.get_surface()
    virtual = pygame.Surface((settings.WIDTH, settings.HEIGHT))

    state = GameState()
    game = Game(virtual, window, state)

    registry = {
        settings.LEVEL1: Level1Scene,
        settings.LEVEL2: Level2Scene,
        settings.LEVEL3: Level3Scene,
        settings.LEVEL4: Level4Scene,
        settings.BRIEFING: BriefingScene,
        settings.TUTORIAL: TutorialScene,
        settings.ENDING: EndingScene,
        settings.MENU: MenuScene,
        settings.MAP: MapScene,
        settings.PAUSE: PauseScene,
    }
    for name, cls in registry.items():
        game.manager.register(name, cls)

    failures: list[str] = []
    # (scene name, extra switch kwargs)
    scene_cases = [
        (settings.TUTORIAL, {}),
        (settings.LEVEL1, {}),
        (settings.LEVEL2, {}),
        (settings.LEVEL3, {}),
        (settings.LEVEL4, {}),
        (settings.BRIEFING, {"level_id": "outpost"}),
        (settings.MENU, {}),
        (settings.MAP, {}),
        (settings.PAUSE, {}),
    ]

    for name, enter in scene_cases:
        try:
            run_scene(game, name, **enter)
            print(f"ok    {name}")
        except Exception as exc:  # noqa: BLE001
            import traceback

            traceback.print_exc()
            failures.append(name)
            print(f"FAIL  {name}: {exc}")

    # ending requires all parts; force them for the test
    for part in state.required_parts():
        state.add_part(part)
    try:
        run_scene(game, settings.ENDING)
        print("ok    ending")
    except Exception as exc:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        failures.append(settings.ENDING)
        print(f"FAIL  ending: {exc}")

    pygame.quit()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("all scenes ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
