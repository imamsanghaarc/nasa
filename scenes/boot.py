"""Boot splash: title, cached NASA APOD, one line of story."""

from __future__ import annotations

import json

import pygame

from art import backgrounds
from core import audio, settings, text
from core.scene import Scene

APOD_JSON = settings.DATA / "cache" / "apod.json"
APOD_IMAGE = settings.DATA / "cache" / "apod.jpg"


class BootScene(Scene):
    name = settings.BOOT

    def on_enter(self, **data) -> None:
        self.t = 0.0
        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)
        self.apod = self._load_apod()
        self.apod_image = self._load_image()
        self.done = False

    # --- data ---------------------------------------------------------------
    def _load_apod(self) -> dict:
        try:
            return json.loads(APOD_JSON.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            return {
                "title": "NASA archive offline",
                "explanation": "Run tools/fetch_apod.py once with internet to cache today's APOD.",
                "offline_fallback": True,
            }

    def _load_image(self) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(APOD_IMAGE)).convert()
            return pygame.transform.smoothscale(image, (300, 168))
        except (pygame.error, OSError, ValueError):
            return None

    # --- loop ---------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if self.t > 0.4:
                    self.finish()
                    return

    def finish(self) -> None:
        if self.done:
            return
        self.done = True
        audio.play("click")
        self.manager.switch(settings.MENU)

    def update(self, dt: float) -> None:
        self.t += dt
        if self.t > 6.0:
            self.finish()

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.stars, (0, 0))
        screen.blit(self.neb, (0, 0))

        fade = min(1.0, self.t / 0.9)
        alpha = int(255 * fade)

        # Fit the longer title inside the window at any text scale.
        title_size = 62
        while title_size > 18 and text.measure(settings.TITLE, title_size, True)[0] > settings.WIDTH - 80:
            title_size -= 2
        text.draw_centered(
            screen,
            settings.TITLE,
            (settings.WIDTH // 2, 214),
            title_size,
            settings.INK,
            display=True,
            alpha=alpha,
        )
        text.draw_centered(
            screen,
            settings.SUBTITLE.upper(),
            (settings.WIDTH // 2, 274),
            28,
            settings.ACCENT,
            alpha=alpha,
        )
        text.draw_centered(
            screen,
            "You are stranded in orbit. Laika has seven parts to find and one way home.",
            (settings.WIDTH // 2, 330),
            24,
            settings.DIM,
            max_width=760,
            alpha=alpha,
        )

        if self.t > 0.9:
            panel = pygame.Rect(80, 470, 480, 180)
            pygame.draw.rect(screen, (7, 12, 24), panel, border_radius=10)
            pygame.draw.rect(screen, settings.PANEL_EDGE, panel, 1, border_radius=10)
            text.draw(screen, "NASA ASTRONOMY PICTURE OF THE DAY", (panel.x + 18, panel.y + 14), 14, settings.ACCENT, display=True)
            title = str(self.apod.get("title", "Archive"))
            text.draw(screen, title, (panel.x + 18, panel.y + 40), 24, settings.INK, max_width=panel.width - 36, shadow=False)
            explanation = str(self.apod.get("explanation", ""))
            text.draw(
                screen,
                explanation,
                (panel.x + 18, panel.y + 74),
                18,
                settings.DIM,
                max_width=panel.width - 36,
                shadow=False,
            )
            if self.apod_image:
                screen.blit(self.apod_image, (panel.right + 24, panel.y))
            text.draw(
                screen,
                f"{self.apod.get('date', '')}  |  apod.nasa.gov",
                (panel.x + 18, panel.bottom - 26),
                16,
                settings.FAINT,
                shadow=False,
            )

        if self.t > 1.4:
            blink = (pygame.time.get_ticks() // 500) % 2 == 0
            if blink:
                text.draw(
                    screen,
                    "PRESS ANY KEY",
                    (settings.WIDTH // 2, settings.HEIGHT - 70),
                    20,
                    settings.DIM,
                    display=True,
                    center=True,
                    alpha=180,
                )

        screen.blit(self.vignette, (0, 0))
