"""Level 4: Lava Tunnel Exploration.

Platforming level: navigate cave with flashlight, find rock sample + camera buttons, escape.
"""

from __future__ import annotations

import math
import pygame

from core import audio, levels, settings, text
from core.scene import Scene
from core.game_state import GameState
from art import environments, sprites
from ui.dialogue_box import DialogueBox
from ui.hud import HUD
from ui.vending import Vending


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item_rect(index: int, grid_rect: pygame.Rect) -> pygame.Rect:
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
    f = 1
    bob = math.sin(t * 6.0) * 1.5 * s
    pygame.draw.rect(surface, (232, 238, 248), pygame.Rect(cx - 9 * s, cy - 7 * s + bob, 18 * s, 17 * s), border_radius=max(2, int(5 * s)))
    pygame.draw.circle(surface, (94, 210, 208), (cx, cy - 2 * s + bob), max(1, int(2 * s)))


def _draw_flashlight_beam(surface: pygame.Surface, center: tuple[int, int], t: float, radius: int = 200) -> None:
    """Draw a simple flashlight beam cone."""
    cx, cy = center
    # cone shape
    pygame.draw.polygon(surface, (255, 255, 200), [
        (cx, cy),
        (cx + radius * math.cos(t * 0.5), cy - radius * math.sin(t * 0.5)),
        (cx + radius * 0.8 * math.cos(t * 0.5 + 1.0), cy - radius * 0.8 * math.sin(t * 0.5 + 1.0)),
        (cx + radius * 0.8 * math.cos(t * 0.5 - 1.0), cy - radius * 0.8 * math.sin(t * 0.5 - 1.0)),
    ])
    # inner circle
    pygame.draw.circle(surface, (255, 255, 200), (cx, cy), radius // 3)
    # glow
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 200, 100, 40), (radius, radius), radius)
    surface.blit(glow, (cx - radius, cy - radius))


# ---------------------------------------------------------------------------
# Level 4 Scene
# ---------------------------------------------------------------------------

class Level4Scene(Scene):
    name = settings.LEVEL4
    counts_time = True

    #: phase id -> handler method (checked by tools/campaign_test.py)
    phase_handlers = {
        "intro": "_handle_intro",
        "flashlight_on": "_handle_flashlight_on",
        "explore": "_handle_explore",
        "escape": "_handle_escape",
        "complete": "_handle_complete",
    }

    def on_enter(self, **data) -> None:
        self.cfg = levels.load_level("level4")
        self.params = levels.params_for(self.cfg, self.state.difficulty)
        self.dialogue = levels.load_dialogue(self.cfg.get("dialogue", "dialogue/mars.json"))
        self.hud = HUD(self.state, level_name=self.cfg["name"], accent=settings.ACCENT)
        self.dlg = DialogueBox(self.game)
        self.modal: Modal | None = None
        self.vending: Vending | None = None
        self.t = 0.0
        self.phase = "intro"
        self.phase_start = 0.0
        self.level_time = 0.0
        self.flashlight_on = False
        self.fall_timer = 0.0
        self.buttons_pressed = 0  # 0=nothing, 1=rock, 2=camera, 3=both
        self.total_time = 240  # 4 minutes

        # tunnel backdrop
        self.backdrop = environments.tunnel_backdrop(settings.WIDTH, settings.HEIGHT, seed=3)

        # player
        self.player_pos = pygame.Vector2(self.params["player_start"])
        self.vending_rect = pygame.Rect(96, 196, 112, 168)

        # button positions in the tunnel
        self.rock_button_rect = pygame.Rect(400, 300, 60, 60)
        self.camera_button_rect = pygame.Rect(800, 300, 60, 60)
        self.entrance_rect = pygame.Rect(100, 500, 200, 80)

        self.vy = 0.0
        self.gravity = 900.0
        self.jump_velocity = 650.0
        self.rock_ledges = [
            pygame.Rect(300, 300, 60, 60),
            pygame.Rect(520, 240, 60, 60),
            pygame.Rect(760, 300, 60, 60),
        ]
        self.entrance_pos = pygame.Vector2(self.params["player_start"])

        # objective
        self.objective = ""

        self.phase_start = self.state.elapsed
        self._goto_phase("intro")

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def _goto_phase(self, phase: str, **data) -> None:
        self.phase = phase
        self.phase_start = self.state.elapsed
        self.objective = ""
        self.modal = None
        self.vending = None
        self.flashlight_on = False
        self.buttons_pressed = 0

        if phase == "flashlight_on":
            self.flashlight_on = True
            self._say("flashlight_on")
            self._schedule_next("explore", 3.0)
            return
        if phase == "find_objects":
            self._say("find_objects")
            self._schedule_next("escape", 3.0)
            return
        if phase == "escape":
            self._say("escape")
            self._schedule_next("complete", 3.0)
            return
        if phase == "complete":
            self._schedule_next("briefing", 3.0)
            return

        phase_cfg = next((p for p in self.cfg["phases"] if p["id"] == phase), None)
        if phase_cfg:
            self.objective = phase_cfg.get("objective", "")
            trig = phase_cfg.get("dialogue_trigger")
            if trig:
                self._say(trig)

    def _schedule_next(self, phase: str, delay: float) -> None:
        self._next_phase = phase
        self._next_phase_time = self.state.elapsed + delay

    def _ledge_top(self) -> float:
        return float(self.params.get("ground_y") or 560)

    def _restart_tunnel(self) -> None:
        """PPTX: if Laika falls, restart from the initial cave entrance checkpoint."""
        self.player_pos = pygame.Vector2(self.entrance_pos)
        self.phase = "explore"
        self.phase_start = self.state.elapsed
        self.objective = "Navigate the tunnel using the flashlight. Find the rock sample and camera buttons. Watch for falling rocks!"
        self.hud.toast("Laika fell - restarting from the cave entrance checkpoint.")
        audio.play("boom")

    # ------------------------------------------------------------------
    # Dialogue
    # ------------------------------------------------------------------

    def _say(self, trigger: str, speaker: str | None = None) -> None:
        lines = self.dialogue["lines"].get(trigger, [])
        if not lines:
            if self.dlg.is_active():
                self.dlg.advance()
            return
        self.dlg.queue(lines, speaker=speaker, on_done=self._on_dialogue_done)

    def _on_dialogue_done(self) -> None:
        if self.dlg.index + 1 < len(self.dlg.lines):
            self.dlg.index += 1
            self.dlg.revealed = 0.0
        else:
            self.dlg.clear()

    # ------------------------------------------------------------------
    # Phase logic
    # ------------------------------------------------------------------

    def _handle_intro(self, dt: float) -> None:
        self.t += dt
        if self.player_pos.distance_to(pygame.Vector2(640, 380)) > 30:
            direction = (pygame.Vector2(640, 380) - self.player_pos).normalize() * 120 * dt
            self.player_pos += direction
        if self.player_pos.distance_to(pygame.Vector2(640, 380)) < 50 and not self.dlg.is_active():
            self._say("intro")

    # -- flashlight_on --
    def _handle_flashlight_on(self, dt: float) -> None:
        self.t += dt
        keys = pygame.key.get_pressed()
        if keys[pygame.K_f] and not self.dlg.is_active():
            self.flashlight_on = not self.flashlight_on
            audio.play("beep", 0.5)
            self._say("flashlight_on" if not self.flashlight_on else "flashlight_on")
        # auto-advance once the flashlight is on - the player moves into the tunnel
        if self.flashlight_on and self.phase == "flashlight_on":
            self.phase = "explore"
            self.phase_start = self.state.elapsed
            self.objective = "Navigate the tunnel using the flashlight. Find the rock sample and camera buttons. Watch for falling rocks!"

    # -- explore --
    def _handle_explore(self, dt: float) -> None:
        self.t += dt
        self.level_time = self.state.elapsed - self.phase_start
        # timeout: 4 minutes
        if self.level_time >= self.total_time:
            self._goto_phase("complete")
            return

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())

        # flashlight toggle
        if keys[pygame.K_f] and not self.dlg.is_active():
            self.flashlight_on = not self.flashlight_on
            audio.play("beep", 0.5)

        # check fall - if player goes off the left/right edges, restart at the cave entrance
        # simple check: if player x goes beyond bounds
        if self.player_pos.x < -50 or self.player_pos.x > settings.WIDTH + 50:
            self._restart_tunnel()

        # jump between rocks (PPTX: Roblox-style obstacle course jumps in the cave)
        jump_keys = (keys[pygame.K_2], keys[pygame.K_UP], keys[pygame.K_w], keys[pygame.K_SPACE])
        jump_height = self.jump_velocity * self.jump_velocity / (2.0 * self.gravity)
        if any(jump_keys) and not self.dlg.is_active() and self.player_pos.y >= self._ledge_top() - jump_height - 20:
            self.vy = -self.jump_velocity
            audio.play("jump", 0.4)

        # simple gravity + movement inside the tunnel
        self.vy = self.vy + self.gravity * dt
        self.player_pos.y = self.player_pos.y + self.vy * dt
        ledge_top = self._ledge_top()
        if self.player_pos.y > ledge_top + 20:
            self.player_pos.y = ledge_top + 20
            self.vy = 0.0
        for ledge in self.rock_ledges:
            if self.player_pos.y + 30 >= ledge.y and self.player_pos.y <= ledge.bottom and self.player_pos.x + 25 > ledge.x and self.player_pos.x < ledge.right:
                self.player_pos.y = ledge.y - 30
                self.vy = 0.0

        # fall -> restart from the initial cave entrance checkpoint
        if self.player_pos.y > settings.HEIGHT + 100 or self.player_pos.x < -100 or self.player_pos.x > settings.WIDTH + 100:
            self._restart_tunnel()

        # check button presses
        # rock button
        if self.rock_button_rect.collidepoint(int(mouse_pos[0]), int(mouse_pos[1])) and keys[pygame.K_e] and not self.dlg.is_active():
            self.buttons_pressed |= 1  # rock pressed
            self.hud.toast("Rock sample obtained!")
            audio.play("confirm", 0.4)
        # camera button
        if self.camera_button_rect.collidepoint(int(mouse_pos[0]), int(mouse_pos[1])) and keys[pygame.K_e] and not self.dlg.is_active():
            self.buttons_pressed |= 2  # camera pressed
            self.hud.toast("Camera activated!")
            audio.play("camera", 0.4)

        # both pressed → escape
        if self.buttons_pressed == 3:
            self._goto_phase("escape")

        # draw flashlight beam when on
        if self.flashlight_on:
            _draw_flashlight_beam(surface, (int(self.player_pos.x), int(self.player_pos.y)), self.t, radius=250)

    # -- escape --
    def _handle_escape(self, dt: float) -> None:
        self.t += dt
        if self.state.elapsed - self.phase_start > 3.0:
            self._goto_phase("complete")

    # -- complete --
    def _handle_complete(self, dt: float) -> None:
        self.t += dt
        if self.state.elapsed - self.phase_start >= 5.0:
            self.state.mark_level_done("tunnel", self.level_time)
            # PPTX: final two minutes are a short victory sequence - Laika returns
            # to Earth inside the spacecraft and the mission is won.
            if self.state.elapsed - self.phase_start >= self.total_time - 120.0:
                self.state.finish_mission("win")
                self.manager.switch(settings.ENDING)
            elif self.state.level_count >= len(settings.LEVEL_IDS):
                self.state.finish_mission("win")
                self.manager.switch(settings.ENDING)
            else:
                self.manager.switch(settings.BRIEFING, level_id="tunnel")

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
                elif self.dlg.is_active():
                    self.dlg.clear()
                else:
                    self.manager.push(settings.PAUSE, parent=self)
                return

    def update(self, dt: float) -> None:
        self.t += dt
        self.level_time = self.state.elapsed - self.phase_start

        if self.phase == "intro":
            self._handle_intro(dt)
        elif self.phase == "flashlight_on":
            self._handle_flashlight_on(dt)
        elif self.phase == "explore":
            self._handle_explore(dt)
        elif self.phase == "escape":
            self._handle_escape(dt)
        elif self.phase == "complete":
            self._handle_complete(dt)

        self.hud.update(dt)
        if self.dlg.is_active():
            self.dlg.update(dt)
        if self.modal:
            self.modal.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.backdrop, (0, 0))

        _draw_astronaut_at(surface, (640, 380), self.t)

        self.hud.draw(surface)

        if self.dlg.is_active():
            self.dlg.draw(surface)

        if self.modal:
            self.modal.draw(surface)

        # draw buttons
        rock_color = (150, 130, 120) if self.buttons_pressed & 1 else (96, 74, 66)
        camera_color = (150, 130, 120) if self.buttons_pressed & 2 else (96, 74, 66)
        pygame.draw.rect(surface, rock_color, self.rock_button_rect, border_radius=8)
        pygame.draw.rect(surface, camera_color, self.camera_button_rect, border_radius=8)
        # labels
        text.draw(surface, "ROCK", (self.rock_button_rect.centerx, self.rock_button_rect.top - 10), 12, settings.DIM, display=True, center=True)
        text.draw(surface, "CAMERA", (self.camera_button_rect.centerx, self.camera_button_rect.top - 10), 12, settings.DIM, display=True, center=True)

        # draw objective banner
        if self.objective:
            text.draw(surface, f"OBJECTIVE: {self.objective}",
                     (settings.WIDTH // 2, 60), 20, settings.INK, display=True, center=True)


# ----------------------------------------------------------------------
# Scene registration
# ----------------------------------------------------------------------

def register_mission_scenes(manager: object) -> None:
    from scenes.level1 import Level1Scene
    from scenes.level2 import Level2Scene
    from scenes.level3 import Level3Scene
    from scenes.level4 import Level4Scene
    from scenes.briefing import BriefingScene
    manager.register(settings.LEVEL1, Level1Scene)
    manager.register(settings.LEVEL2, Level2Scene)
    manager.register(settings.LEVEL3, Level3Scene)
    manager.register(settings.LEVEL4, Level4Scene)
    manager.register(settings.BRIEFING, BriefingScene)