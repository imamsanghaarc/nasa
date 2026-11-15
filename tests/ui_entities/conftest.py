"""Headless harness for the UI / ENTITIES layer of MISSION LAIKA: THE RED HORIZON.

Rules honoured here:
  * SDL dummy video + audio drivers are set BEFORE pygame is imported.
  * ``E:\\nasa`` is put on ``sys.path`` so the project imports as a package.
  * pygame is initialised and a display surface exists before any Surface is made.
  * ``core.save.write`` is stubbed so the tests never touch ``savegame.json``.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# keep the audio subsystem silent and allocation-free in CI
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = r"E:\nasa"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402  (must come after the SDL env vars)

from core import save as _save  # noqa: E402
from core import settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game, SceneManager  # noqa: E402

pygame.init()
DISPLAY = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
pygame.display.set_caption("LAIKA TEST HARNESS")


# --- keep the real save file untouched --------------------------------------
_saved_write = _save.write
_saved_clear = _save.clear
WRITES: list[dict] = []


def _fake_write(payload: dict) -> bool:
    WRITES.append(payload)
    return True


def _fake_clear() -> None:
    WRITES.append({"__cleared__": True})


_save.write = _fake_write
_save.clear = _fake_clear


# --- fixtures ---------------------------------------------------------------
import pytest  # noqa: E402


@pytest.fixture(scope="session")
def display():
    return DISPLAY


@pytest.fixture()
def screen():
    """A clean 1280x720 surface."""
    surf = pygame.Surface((settings.WIDTH, settings.HEIGHT))
    surf.fill((0, 0, 0))
    return surf


@pytest.fixture()
def small_screen():
    """A deliberately tiny surface for 'draw at various widths' checks."""
    return pygame.Surface((320, 200))


@pytest.fixture()
def state():
    return GameState()


@pytest.fixture()
def game(state):
    """A minimal stand-in for the real Game container."""
    g = Game(DISPLAY, DISPLAY, state)
    g.manager = SceneManager(g)
    return g


@pytest.fixture()
def fake_game(state):
    """Game-like object for widgets that only need ``screen``."""

    class _Fake:
        def __init__(self):
            self.screen = DISPLAY
            self.state = state
            self.manager = None

    return _Fake()


# --- event helpers ----------------------------------------------------------
def mouse_motion(pos):
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos, "rel": (0, 0), "buttons": (0, 0, 0)})


def mouse_down(pos, button=1):
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": button, "rel": (0, 0)}
    )


def mouse_up(pos, button=1):
    return pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"pos": pos, "button": button, "rel": (0, 0)}
    )


def key_down(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": mod, "unicode": "", "scancode": 0})


def key_up(key, mod=0):
    return pygame.event.Event(pygame.KEYUP, {"key": key, "mod": mod, "scancode": 0})
