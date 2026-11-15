"""Level 3: Martian Surface.

Rover exploration: take photographs, survive the sandstorm, activate hibernation.

The phase chain comes from ``data/levels/level3.json``::

    intro -> photo_intro -> take_photos -> sandstorm -> cold_alert -> hibernation -> complete

Every phase is dispatched through ``phase_handlers`` and every pacing number
(time limits, camera count, exposure budget) is read from the JSON config.
"""

from __future__ import annotations

import math

import pygame

from core import audio, levels, settings, text
from core.scene import Scene
from art import environments
from ui.dialogue_box import DialogueBox
from ui.hud import HUD
from ui.modal import Modal
from ui.vending import Vending


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item_rect(index: int, grid_rect: pygame.Rect) -> pygame.Rect:
    rows = max(1, math.ceil(grid_rect.width / 200))  # rough
    cols = 3
    gap = 12
    card_w = (grid_rect.width - gap * (cols - 1)) // cols
    card_h = min(126, (grid_rect.height - gap * (rows - 1)) // max(1, rows))
    col = index % cols
    row = index // cols
    return pygame.Rect(
        grid_rect.x + col * (card_w + gap),
        grid_rect.y + row * (card_h + gap),
        card_w,
        card_h,
    )


def _draw_astronaut_at(surface: pygame.Surface, pos: tuple[int, int], t: float) -> None:
    cx, cy = pos
    s = 1.0
    bob = math.sin(t * 6.0) * 1.5 * s
    pygame.draw.rect(
        surface,
        (232, 238, 248),
        pygame.Rect(cx - 9 * s, cy - 7 * s + bob, 18 * s, 17 * s),
        border_radius=max(2, int(5 * s)),
    )
    pygame.draw.circle(surface, (94, 210, 208), (cx, cy - 2 * s + bob), max(1, int(2 * s)))


# ---------------------------------------------------------------------------
# Level 3 Scene
# ---------------------------------------------------------------------------

class Level3Scene(Scene):
    name = settings.LEVEL3
    counts_time = True

    #: phase id -> handler method (also checked by ``tools/campaign_test.py``)
    phase_handlers = {
        "intro": "_handle_intro",
        "photo_intro": "_handle_photo_intro",
        "take_photos": "_handle_take_photos",
        "sandstorm": "_handle_sandstorm",
        "cold_alert": "_handle_cold_alert",
        "hibernation": "_handle_hibernation",
        "complete": "_handle_complete",
    }

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("level3")
        self.params = levels.params_for(self.cfg, self.state.difficulty)
        self.dialogue = levels.load_dialogue(self.cfg.get("dialogue", "dialogue/mars.json"))
        self.hud = HUD(self.state, level_name=self.cfg["name"], accent=settings.ACCENT)
        self.dlg = DialogueBox(self.game)
        self.modal: Modal | None = None
        self.vending: Vending | None = None

        self.t = 0.0
        self.phase = "intro"
        self.phase_start = self.state.elapsed
        self.level_time = 0.0
        self.objective = ""

        # interactables
        self.photo_buttons = [
            pygame.Rect(300, 260, 60, 60),
            pygame.Rect(480, 200, 60, 60),
            pygame.Rect(660, 260, 60, 60),
            pygame.Rect(840, 200, 60, 60),
            pygame.Rect(420, 340, 60, 60),
            pygame.Rect(600, 340, 60, 60),
        ]
        self.sample_rect = pygame.Rect(880, 300, 60, 60)

        # run state
        self.player_pos = pygame.Vector2(self.params.get("player_start", (640, 400)))
        self.move_speed = float(self.params.get("move_speed", 250))
        self.photos_taken: set[int] = set()
        self.photo_count = 0
        self.photo_total = int(
            (self._phase_cfg("take_photos") or {}).get("camera_buttons", len(self.photo_buttons))
        )
        self.sample_collected = False
        self.sandstorm_active = False
        self.hibernation_active = False
        self.low_power = False
        self.sheltered = False
        self.dust_exposure = 0.0
        self.cold_timer = 0.0
        self._e_latch = False
        self._l_latch = False
        self._h_latch = False
        self._intro_said = False
        self._finished = False

        # backdrop + boulders. Keep the interactables (and the player start) clear.
        avoid = [(*self.sample_rect.center, 46.0), (*self.player_pos, 46.0)]
        avoid += [(*rect.center, 46.0) for rect in self.photo_buttons]
        self.backdrop, self.rocks = environments.mars_surface(
            settings.WIDTH, settings.HEIGHT, seed=11, avoid=avoid
        )

        self._refresh_counters()
        self._goto_phase("intro")

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def _phase_cfg(self, phase: str) -> dict | None:
        return next((p for p in self.cfg.get("phases", []) if p["id"] == phase), None)

    def _time_limit(self, phase: str, default: float) -> float:
        value = (self._phase_cfg(phase) or {}).get("time_limit")
        try:
            return float(value) if value is not None else float(default)
        except (TypeError, ValueError):
            return float(default)

    def _goto_phase(self, phase: str, **data) -> None:
        self.phase = phase
        self.phase_start = self.state.elapsed
        self.objective = ""
        self.modal = None
        self.vending = None
        self.sandstorm_active = False
        self.hibernation_active = False
        self.dust_exposure = 0.0

        if phase == "sandstorm":
            self.sandstorm_active = True
        if phase == "hibernation":
            self.hibernation_active = True

        phase_cfg = self._phase_cfg(phase)
        if phase_cfg:
            self.objective = phase_cfg.get("objective", "")
            trigger = phase_cfg.get("dialogue_trigger")
            if trigger:
                self._say(trigger)

    def _lose_mission(self) -> None:
        """The rover was destroyed / the survival run failed."""
        audio.play("boom")
        self.state.finish_mission("lost")
        self._restart_mission()

    def _restart_mission(self) -> None:
        """Restart this level from its first phase (same scene object)."""
        self.dlg.clear()
        self.on_enter()

    # ------------------------------------------------------------------
    # Dialogue
    # ------------------------------------------------------------------

    def _say(self, trigger: str, speaker: str | None = None) -> None:
        lines = self.dialogue["lines"].get(trigger, [])
        if not lines:
            return
        self.dlg.queue(lines, speaker=speaker)

    def _dialogue_done(self) -> bool:
        return not self.dlg.is_active() and not self.dlg.lines

    # ------------------------------------------------------------------
    # Player / interaction helpers
    # ------------------------------------------------------------------

    def _move_player(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - (
            1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0
        )
        dy = (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0) - (
            1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0
        )
        if dx or dy:
            step = pygame.Vector2(dx, dy)
            if step.length_squared():
                step = step.normalize() * self.move_speed * dt
            self.player_pos += step
            self.player_pos.x = max(24.0, min(settings.WIDTH - 24.0, self.player_pos.x))
            self.player_pos.y = max(24.0, min(settings.HEIGHT - 24.0, self.player_pos.y))

    def _near(self, rect: pygame.Rect, radius: float = 48.0) -> bool:
        return self.player_pos.distance_to(pygame.Vector2(rect.center)) <= radius

    def _interact(self) -> bool:
        """True on the frame E goes from up to down."""
        held = bool(pygame.key.get_pressed()[pygame.K_e])
        pressed = held and not self._e_latch
        self._e_latch = held
        return pressed

    def _sheltered_by_rock(self) -> bool:
        return any(
            self.player_pos.distance_to(pygame.Vector2(rock["x"], rock["y"])) <= rock["r"] + 40
            for rock in self.rocks
        )

    def _refresh_counters(self) -> None:
        self.hud.set_counters([
            {"label": "PHOTOS", "value": f"{self.photo_count}/{self.photo_total}",
             "color": settings.ACCENT},
            {"label": "SAMPLES", "value": "1/1" if self.sample_collected else "0/1",
             "color": settings.GOLD},
        ])

    # ------------------------------------------------------------------
    # Phase logic
    # ------------------------------------------------------------------

    def _handle_intro(self, dt: float) -> None:
        self.t += dt
        target = pygame.Vector2(640, 380)
        if self.player_pos.distance_to(target) > 30:
            self.player_pos += (target - self.player_pos).normalize() * 120 * dt
        # the actual blocker fix: move on once the intro dialogue finishes
        if self._dialogue_done():
            self._goto_phase("photo_intro")

    def _handle_photo_intro(self, dt: float) -> None:
        self.t += dt
        if self._dialogue_done():
            self._goto_phase("take_photos")

    def _handle_take_photos(self, dt: float) -> None:
        self.t += dt
        self._move_player(dt)
        elapsed = self.state.elapsed - self.phase_start
        limit = self._time_limit("take_photos", 300.0)
        cold_after = float((self._phase_cfg("take_photos") or {}).get("cold_after", limit * 0.6))

        # loss check first - it used to be unreachable behind the temperature check
        if elapsed >= limit:
            self._lose_mission()
            return
        if elapsed >= cold_after:
            self.hud.banner(
                "TEMPERATURE DROPPING TO -125°C - ACTIVATE HIBERNATION MODE",
                4.0,
                settings.DANGER,
            )
            self._goto_phase("cold_alert")
            return

        if not self._interact():
            return

        # rock / soil sample collection
        if not self.sample_collected and self._near(self.sample_rect):
            self.sample_collected = True
            self.state.add_item("mars_sample")
            audio.play("confirm", 0.4)
            self.hud.toast("Mars rock sample collected!")
            self._refresh_counters()
            if self.photo_count >= self.photo_total:
                self._goto_phase("sandstorm")
            return

        # photographs of the marked cameras
        for index, rect in enumerate(self.photo_buttons):
            if index in self.photos_taken or not self._near(rect):
                continue
            self.photos_taken.add(index)
            self.photo_count = len(self.photos_taken)
            audio.play("camera", 0.4)
            self.hud.toast(f"Photo {self.photo_count}/{self.photo_total} taken!")
            self._refresh_counters()
            if self.photo_count >= self.photo_total and self.sample_collected:
                self._goto_phase("sandstorm")
            return

    def _handle_sandstorm(self, dt: float) -> None:
        self.t += dt
        self.sandstorm_active = True
        # Present choice: wait for storm or continue moving
        if not self.modal:
            self.modal = Modal(
                "SANDSTORM DECISION",
                "A sandstorm is rolling in. What do you do?",
                buttons=[
                    ("Wait for storm to pass", 
                     lambda: self._sandstorm_choice("wait"), "primary"),
                    ("Continue moving through storm",
                     lambda: self._sandstorm_choice("continue"), "ghost"),
                ],
                width=600,
            )
            self.modal.draw(self.screen)
        self._move_player(dt)

        # baseline freshness: the storm is judged from where the player is now
        self.sheltered = self._sheltered_by_rock()
        if not self.sheltered:
            self.dust_exposure += dt
        exposure_limit = float((self._phase_cfg("sandstorm") or {}).get("exposure_limit", 6.0))

        held = bool(pygame.key.get_pressed()[pygame.K_l])
        if held and not self._l_latch and not self.low_power:
            self.low_power = True
            audio.play("power_down", 0.5)
            self.hud.toast("LOW POWER MODE ACTIVATED - scientific activities halted")
        self._l_latch = held

        remaining = max(0.0, self._time_limit("sandstorm", 45.0) - (self.state.elapsed - self.phase_start))
        self.hud.toast(
            f"Sandstorm! {'Sheltered' if self.sheltered else 'EXPOSED'} - "
            f"Low Power: {'ON' if self.low_power else 'OFF'} - {int(remaining)}s"
        )

        if self.dust_exposure >= exposure_limit:
            self.hud.banner("DUST STORM - SOLAR PANELS UNREACHABLE - ROVER LOST", 4.0, settings.DANGER)
            self._lose_mission()
            return
        if self.low_power and self.sheltered:
            self._goto_phase("cold_alert")
            return
        if remaining <= 0:
            if self.low_power:
                self._goto_phase("cold_alert")
            else:
                self._lose_mission()

    def _handle_cold_alert(self, dt: float) -> None:
        self.t += dt
        remaining = max(0.0, self._time_limit("cold_alert", 10.0) - (self.state.elapsed - self.phase_start))
        self.hud.toast(f"Temperature dropping to -125 °C! Activate Hibernation Mode. {int(remaining)}s")

        held = bool(pygame.key.get_pressed()[pygame.K_h])
        if held and not self._h_latch:
            self._goto_phase("hibernation")
            return
        self._h_latch = held

        if remaining <= 0:
            self._lose_mission()

    def _handle_hibernation(self, dt: float) -> None:
        self.t += dt
        remaining = max(0.0, self._time_limit("hibernation", 45.0) - (self.state.elapsed - self.phase_start))
        self.hud.toast(f"Hibernation Mode active. Cold protecting rover. {int(remaining)}s")
        if remaining <= 0:
            self._goto_phase("complete")


    def _sandstorm_choice(self, choice: str) -> None:

        self.modal = None

        if choice == "wait":

            # Player waited for the storm to pass

            self.hud.toast("Sandstorm passed. Clearing exposure.")

            self.sandstorm_active = False

            self.dust_exposure = 0.0

            self._goto_phase("cold_alert")

        elif choice == "continue":

            # Player continued moving through the storm

            # Increased dust exposure risk

            self.hud.toast("Moving through storm - dust exposure increasing!")

            self.sandstorm_active = True

            # Add extra exposure for continuing

            extra_exposure = 3.0 * (self.state.elapsed - self.phase_start)

            self.dust_exposure = min(self.dust_exposure + extra_exposure, 10.0)

            # Stay in sandstorm phase but with higher risk
    def _handle_complete(self, dt: float) -> None:
        self.t += dt
        if self._finished:
            return
        if self.state.elapsed - self.phase_start >= float(
            (self._phase_cfg("complete") or {}).get("hold", 5.0)
        ):
            self._finished = True
            self.state.mark_level_done("surface", self.level_time)
            self.state.add_part(self.cfg.get("part"))
            self.manager.switch(settings.BRIEFING, level_id="surface")

    # ------------------------------------------------------------------
    # General loop
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.game.quit()
            if self.dlg.is_active():
                self.dlg.handle_events(events)
                return
            if self.modal and self.modal.is_active():
                self.modal.handle_events(events)
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.modal:
                    self.modal = None
                else:
                    self.manager.push(settings.PAUSE, parent=self)
                return

    def update(self, dt: float) -> None:
        self.t += dt
        self.level_time = self.state.elapsed - self.phase_start

        handler = self.phase_handlers.get(self.phase)
        if handler is not None:
            getattr(self, handler)(dt)

        self.hud.update(dt)
        if self.dlg.is_active():
            self.dlg.update(dt)
        if self.modal:
            self.modal.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.backdrop, (0, 0))

        # sample rock
        if not self.sample_collected:
            pygame.draw.circle(surface, (120, 96, 84), self.sample_rect.center, 22)
            pygame.draw.circle(surface, settings.GOLD, self.sample_rect.center, 24, 2)

        # camera markers
        for index, rect in enumerate(self.photo_buttons):
            done = index in self.photos_taken
            color = settings.GREEN if done else (94, 210, 208)
            pygame.draw.rect(surface, color, rect, 2, border_radius=5)
            text.draw(
                surface,
                f"CAM {index + 1}",
                (rect.centerx, rect.centery - 10),
                12,
                settings.DIM,
                display=True,
                center=True,
            )

        if self.sandstorm_active:
            veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            veil.fill((168, 96, 52, 110))
            surface.blit(veil, (0, 0))

        _draw_astronaut_at(surface, (int(self.player_pos.x), int(self.player_pos.y)), self.t)

        self.hud.draw(surface)

        if self.dlg.is_active():
            self.dlg.draw(surface)
        if self.modal:
            self.modal.draw(surface)

        if self.objective:
            text.draw(
                surface,
                f"OBJECTIVE: {self.objective}",
                (settings.WIDTH // 2, 60),
                20,
                settings.INK,
                display=True,
                center=True,
            )


# ----------------------------------------------------------------------
# Scene registration
# ----------------------------------------------------------------------

def register_mission_scenes(manager: object) -> None:
    from scenes.level1 import Level1Scene
    from scenes.level2 import Level2Scene
    from scenes.level3 import Level3Scene
    from scenes.briefing import BriefingScene
    manager.register(settings.LEVEL1, Level1Scene)
    manager.register(settings.LEVEL2, Level2Scene)
    manager.register(settings.LEVEL3, Level3Scene)
    manager.register(settings.BRIEFING, BriefingScene)