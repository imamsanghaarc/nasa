"""Title menu and settings."""

from __future__ import annotations

import pygame

from art import backgrounds, planets, sprites
from core import audio, save, settings, text
from core.scene import Scene
from ui.button import Button


class MenuScene(Scene):
    name = settings.MENU

    def on_enter(self, **data) -> None:
        audio.set_volume(self.state.volume)
        audio.set_muted(self.state.muted)
        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)
        self.t = 0.0
        self.show_settings = False
        self.focus = 0
        self.has_save = save.exists()
        self._build_main()

    # --- buttons ------------------------------------------------------------
    def _build_main(self) -> None:
        left = 120
        width = 384
        y = 330
        gap = 70

        self.buttons: list[Button] = [
            Button((left, y, width, 56), "New mission", self.new_mission, size=24),
            Button(
                (left, y + gap, width, 56),
                "Continue",
                self.continue_mission,
                style="ghost",
                size=24,
                enabled=self.has_save,
                subtitle=None if self.has_save else "no save yet",
            ),
            Button((left, y + gap * 2, width, 56), "Settings", self.open_settings, style="ghost", size=24),
            Button((left, y + gap * 3, width, 56), "Quit", self.game.quit, style="danger", size=24),
        ]
        self._sync_focus()

    def _build_settings(self) -> None:
        panel = pygame.Rect(settings.WIDTH // 2 - 290, 150, 580, 462)
        left = panel.x + 40
        width = panel.width - 80
        self.settings_panel = panel
        self.buttons = [
            Button(
                (left, panel.y + 92, width, 54),
                f"Difficulty: {settings.DIFFICULTY_LABELS[self.state.difficulty]}",
                self.cycle_difficulty,
                style="ghost",
                size=22,
            ),
            Button(
                (left, panel.y + 158, width, 54),
                f"Volume: {int(round(self.state.volume * 100))}%",
                self.cycle_volume,
                style="ghost",
                size=22,
            ),
            Button(
                (left, panel.y + 224, width, 54),
                f"Sound: {'Off' if self.state.muted else 'On'}",
                self.toggle_mute,
                style="ghost",
                size=22,
            ),
            Button(
                (left, panel.y + 290, width, 54),
                f"Text size: {'Large' if self.state.text_scale > 1.2 else 'Normal'}",
                self.cycle_text_scale,
                style="ghost",
                size=22,
            ),
            Button((left, panel.y + 356, width, 44), "Back", self.close_settings, size=20),
        ]
        self.focus = 0
        self._sync_focus()

    def _sync_focus(self) -> None:
        for index, button in enumerate(self.buttons):
            button.focused = index == self.focus and button.enabled

    # --- actions ------------------------------------------------------------
    def new_mission(self) -> None:
        self.state.reset_mission()
        self.state.save()
        self.manager.switch(settings.TUTORIAL)

    def continue_mission(self) -> None:
        if not self.state.load():
            self.has_save = False
            self._build_main()
            return
        audio.set_volume(self.state.volume)
        audio.set_muted(self.state.muted)
        text.set_scale(self.state.text_scale)
        target = settings.MAP if self.state.tutorial_done else settings.TUTORIAL
        self.manager.switch(target)

    def open_settings(self) -> None:
        self.show_settings = True
        self._build_settings()

    def close_settings(self) -> None:
        self.show_settings = False
        self.has_save = save.exists()
        self._build_main()

    def cycle_difficulty(self) -> None:
        self.state.next_difficulty()
        self._build_settings()

    def cycle_volume(self) -> None:
        self.state.volume = round((self.state.volume + 0.1) % 1.1, 1)
        audio.set_volume(self.state.volume)
        audio.play("click")
        self.state.save()
        self._build_settings()

    def toggle_mute(self) -> None:
        self.state.muted = not self.state.muted
        audio.set_muted(self.state.muted)
        self.state.save()
        self._build_settings()

    def cycle_text_scale(self) -> None:
        self.state.toggle_text_scale()
        text.set_scale(self.state.text_scale)
        audio.play("click")
        self._build_settings()

    # --- loop ---------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.show_settings:
                    self.close_settings()
                    return
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.focus = (self.focus + 1) % len(self.buttons)
                    self._sync_focus()
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.focus = (self.focus - 1) % len(self.buttons)
                    self._sync_focus()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    if self.buttons:
                        self.buttons[self.focus].activate()
                        return
        for index, button in enumerate(self.buttons):
            if button.handle_events(events):
                self.focus = index
                return

    def update(self, dt: float) -> None:
        self.t += dt

    # --- drawing ------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.stars, (0, 0))
        screen.blit(self.neb, (0, 0))
        planets.draw_planet(
            screen,
            (1150, 985),
            430,
            (58, 126, 184),
            band_color=(88, 168, 116),
            bands=2,
            seed=7,
        )

        # Fit the longer title inside the window at any text scale.
        title_size = 56
        while title_size > 18 and text.measure(settings.TITLE, title_size, True)[0] > settings.WIDTH - 160:
            title_size -= 2
        text.draw(screen, settings.TITLE, (118, 104), title_size, settings.INK, display=True)
        text.draw(screen, settings.SUBTITLE, (120, 178), 30, settings.ACCENT)

        sprites.draw_laika(screen, (988, 300), self.t, scale=1.5)
        text.draw(screen, "LAIKA", (988, 372), 16, settings.ACCENT, display=True, center=True)
        text.draw(screen, "navigation core", (988, 392), 18, settings.DIM, center=True, shadow=False)
        text.draw(
            screen,
            "Seven parts. Seven worlds.\nOne ride home.",
            (988, 432),
            22,
            settings.INK,
            center=True,
            max_width=300,
            shadow=False,
        )

        if not self.show_settings:
            for button in self.buttons:
                button.draw(screen)
            text.draw(
                screen,
                "NASA Space Apps Challenge 2026  |  every mechanic is a real planetary fact",
                (120, 652),
                18,
                settings.FAINT,
                shadow=False,
            )
            if self.has_save:
                text.draw(screen, self.state.status_line(), (120, 620), 18, settings.DIM, shadow=False)
            text.draw(
                screen,
                "up/down + enter, or mouse",
                (settings.WIDTH - 40, 652),
                17,
                settings.FAINT,
                right=True,
                shadow=False,
            )
        else:
            self._draw_settings(screen)

        screen.blit(self.vignette, (0, 0))

    def _draw_settings(self, screen: pygame.Surface) -> None:
        veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        veil.fill((2, 4, 10, 205))
        screen.blit(veil, (0, 0))

        panel = self.settings_panel
        pygame.draw.rect(screen, settings.PANEL, panel, border_radius=14)
        pygame.draw.rect(screen, settings.PANEL_EDGE, panel, 1, border_radius=14)

        text.draw(screen, "SETTINGS", (panel.centerx, panel.y + 34), 26, settings.ACCENT, display=True, center=True)
        text.draw(
            screen,
            settings.DIFFICULTY_BLURB[self.state.difficulty],
            (panel.centerx, panel.y + 66),
            19,
            settings.DIM,
            center=True,
            max_width=panel.width - 60,
            shadow=False,
        )
        text.draw(
            screen,
            "Changes apply to the next mission you launch.",
            (panel.centerx, panel.bottom - 26),
            17,
            settings.FAINT,
            center=True,
            shadow=False,
        )
        for button in self.buttons:
            button.draw(screen)
