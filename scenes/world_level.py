"""Shared world-level scene: every mission planet is a full side-scrolling world.

One engine, seven planets: seeded terrain, parallax skies, per-planet weather, alien
enemies (ground walkers and saucers that shoot back), themed hazards, checkpoints, a
labeled part on a pedestal, a return pad, a circular minimap, a stopwatch, and a mission
briefing when the world opens. All numbers come from ``data/levels/*.json``.
"""

from __future__ import annotations

import math
import random

import pygame

from art import sprites, world_bg
from core import audio, color as core_color, levels, settings, text, weather as weather_mod, world_gen
from core.scene import Scene
from entities.enemies import LaserBolt, Projectile, UFO, Walker
from entities.player import CombatPlayer
from entities.pickups import Pickup
from ui.dialogue_box import DialogueBox
from ui.hud import HUD

hex_to_rgb = core_color.hex_to_rgb


def make_world_scene(level_id: str):
    """Factory: one scene class per planet, registered under the planet id."""
    return type(
        f"WorldLevel_{level_id}",
        (WorldLevelBase,),
        {"name": level_id, "level_id": level_id},
    )


def _format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:01d}:{seconds % 60:02d}"


class WorldLevelBase(Scene):
    counts_time = True

    # --- setup --------------------------------------------------------------
    def on_enter(self, **data) -> None:
        self.test_mode = bool(data.get("_test"))
        self.cfg = levels.load_level(self.level_id)
        self.params = self.cfg["params"]
        self.dialogue = levels.load_dialogue(self.cfg["dialogue"])

        self.theme = world_gen.default_theme()
        for key, value in self.params.get("theme", {}).items():
            self.theme[key] = hex_to_rgb(value) if isinstance(value, str) and value.startswith("#") else value
        self.part_color = hex_to_rgb(self.cfg["part"].get("color", "#8fd3ff"))
        self.alien_color = hex_to_rgb(self.params.get("alien_color", "#60c87a"))
        self.meteor_color = hex_to_rgb(self.params.get("meteor_color", "#ff9650"))

        self.gen = world_gen.generate(self.level_id, self.params, self.state.difficulty)
        self.world_w = self.gen["world_w"]
        self.world_h = self.gen["world_h"]
        self.ground_y = int(self.gen.get("ground_y", self.world_h))
        self.world_rect = pygame.Rect(0, 0, self.world_w, self.world_h + 300)
        # closer camera: the world is rendered at this zoom, then scaled to the window
        self.zoom = max(1.0, float(self.params.get("zoom", 1.28)))
        view_w = math.ceil(settings.WIDTH / self.zoom)
        view_h = math.ceil(settings.HEIGHT / self.zoom)
        self._view = pygame.Surface((view_w, view_h))
        self.backdrop = world_bg.make_backdrop(self.theme, self._seed())
        self.weather = weather_mod.Weather(self.params.get("weather"))

        self.hud = HUD(self.state, self.cfg)
        self.hud.set_objective(self.cfg.get("objective", ""))
        self.hud.set_hearts(self.state.hearts(), self.state.hearts())
        self.hud.set_target(self.cfg["part"]["name"], self.part_color)

        self.player = CombatPlayer(
            *self.gen["start_pos"], self.params, self.state, self.hud
        )
        self.player.max_health = self.state.hearts()
        self.player.health = self.player.max_health

        self.platforms = self.gen["platforms"]
        self.hazards = self.gen["hazards"]
        self.checkpoints = self.gen["checkpoints"]
        self.last_checkpoint = self.checkpoints[0]
        self.cp_active = {cp: index == 0 for index, cp in enumerate(self.checkpoints)}

        self.walkers = [
            Walker(spec, self.cfg, self.state, color=self.alien_color)
            for spec in self.gen["enemies"]
            if spec["type"] == "walker"
        ]
        self.ufos = [
            UFO(spec, self.cfg, self.state, color=self.theme.get("ufo_color", (150, 170, 200)))
            for spec in self.gen["enemies"]
            if spec["type"] == "ufo"
        ]
        self.plasma: list[Projectile] = []
        self.lasers: list[LaserBolt] = []

        self.part = Pickup(
            self.gen["part_pos"], "part", color=self.part_color, radius=15
        )
        self.exit_pos = self.gen["exit_pos"]
        self.exit_active = False

        # collectibles and decorations from the generator
        self.props = self.gen.get("props", [])
        self.pickups = [
            Pickup(
                (spec["x"], spec["y"]),
                spec["type"],
                color=self.theme["accent"] if spec["type"] == "bonus" else (255, 120, 140),
                radius=8,
            )
            for spec in self.gen.get("pickups", [])
        ]
        self.total_health = sum(1 for item in self.pickups if item.kind == "health")
        self.total_bonus = sum(1 for item in self.pickups if item.kind == "bonus")
        self.health_taken = 0
        self.bonus_taken = 0
        self.sparks: list[list] = []
        self.toast = ""
        self.toast_timer = 0.0
        self._refresh_checklist()

        # mars-style dust storm (optional)
        self.storm_interval = float(self.params.get("storm_interval", 0))
        self.storm_duration = float(self.params.get("storm_duration", 0))
        self.visibility_radius = int(self.params.get("visibility_radius", 130))
        self.storm_timer = 0.0
        self.storm_active = False
        self.storm_left = 0.0
        self.storm_hinted = False

        # one scripted "signature moment" per world (Victoria's set piece)
        self.moment_cfg = self.params.get("moment") or None
        self.moment_x = int(self.world_w * float(self.moment_cfg.get("at", 0.55))) if self.moment_cfg else 0
        self.moment_fired = False
        self.moment_left = 0.0
        self._moment_burst_timer = 0.0
        self.moment_flash = 0.0

        self.dlg = DialogueBox(self.game)
        self.deaths_at_start = self.state.deaths
        self.death_hinted = False
        self.t = 0.0
        self.stopwatch = 0.0
        self.won = False
        self.last_camera_x = 0.0

        self.phase = "brief"
        if self.test_mode:
            self.phase = "play"
        else:
            self._show_brief()

    def _seed(self) -> int:
        return sum(ord(ch) for ch in self.level_id) * 31 + int(self.params.get("seed", 1))

    # --- dialogue / briefing ------------------------------------------------
    def _show_brief(self) -> None:
        self.phase = "brief"

    def _start_mission(self) -> None:
        self.phase = "play"
        lines = self.dialogue["lines"].get("start", [])
        if lines:
            self.dlg.queue(lines)

    def _hint(self) -> None:
        lines = self.dialogue["lines"].get("hint", [])
        if lines:
            self.dlg.hint(lines[(self.state.deaths) % len(lines)])

    def _death_hint(self) -> None:
        lines = self.dialogue["lines"].get("death_3", [])
        if lines:
            self.dlg.queue(lines)

    def _storm_line(self) -> None:
        lines = self.dialogue["lines"].get("storm", [])
        if lines:
            self.dlg.hint(lines[0])

    # --- win / lose ---------------------------------------------------------
    def _win(self) -> None:
        if self.won:
            return
        self.won = True
        audio.play("win")
        self.state.mark_level_done(self.level_id, self.stopwatch)
        for fact in self.cfg.get("facts", []):
            self.state.add_fact(fact)
        self.state.save()
        self.manager.switch(settings.MAP)

    def _collect_part(self) -> None:
        self.part.taken = True
        self.exit_active = True
        audio.play("part")
        self.state.add_part(self.cfg["part"]["name"])
        self.state.save()
        self._toast(f"{self.cfg['part']['name'].upper()} RECOVERED")
        self._refresh_checklist()
        lines = self.dialogue["lines"].get("part", [])
        if lines:
            self.dlg.queue(lines)

    # --- camera -------------------------------------------------------------
    def _camera_x(self) -> float:
        view_w = self._view.get_width()
        target = self.player.pos.x - view_w * 0.40
        return max(0.0, min(target, self.world_w - view_w))

    def _camera_y(self) -> float:
        view_h = self._view.get_height()
        target = self.player.pos.y - view_h * 0.62
        return max(0.0, min(target, self.world_h - view_h))

    # --- storm --------------------------------------------------------------
    def _update_storm(self, dt: float) -> None:
        if self.storm_interval <= 0:
            return
        if self.storm_active:
            self.storm_left -= dt
            if self.storm_left <= 0:
                self.storm_active = False
            elif not self.storm_hinted and self.storm_left <= 6.0:
                self._storm_line()
                self.storm_hinted = True
        else:
            self.storm_timer += dt
            if self.storm_timer >= self.storm_interval:
                self.storm_active = True
                self.storm_left = self.storm_duration
                self.storm_timer = 0.0
                self.storm_hinted = False
                self._storm_line()

    # --- signature moment ---------------------------------------------------
    def _update_moment(self, dt: float) -> None:
        """One scripted set piece per world, configured in ``params.moment``.

        Fires once the player reaches ``at`` (a fraction of the world width),
        then keeps sending short waves until ``duration`` runs out.
        """
        if not self.moment_cfg:
            return

        if not self.moment_fired:
            if self.player.pos.x < self.moment_x:
                return
            self.moment_fired = True
            self.moment_left = float(self.moment_cfg.get("duration", 8.0))
            self._moment_burst_timer = float(self.moment_cfg.get("burst_every", 2.0))
            self.moment_flash = 1.0
            self._toast(str(self.moment_cfg.get("title", "CONTACT!")).upper())
            lines = self.dialogue["lines"].get("moment", [])
            if lines:
                self.dlg.hint(lines[0])
            self._spawn_moment_wave()
            return

        if self.moment_left <= 0:
            return
        self.moment_left -= dt
        self._moment_burst_timer -= dt
        if self._moment_burst_timer <= 0:
            self._moment_burst_timer = float(self.moment_cfg.get("burst_every", 2.0))
            self._spawn_moment_wave()

    def _spawn_moment_wave(self) -> None:
        """Reinforcements for the set piece: walkers on the ground, saucers above."""
        if not self.moment_cfg:
            return
        count = max(1, int(self.moment_cfg.get("wave", 2)))
        ufo_color = self.theme.get("ufo_color", (150, 170, 200))
        for index in range(count):
            side = 1 if index % 2 == 0 else -1
            x = int(self.player.pos.x + side * (420 + index * 170))
            x = max(60, min(x, self.world_w - 60))
            ground = min(self._ground_top_at(x), self.ground_y)
            if index % 2 == 0:
                spec = {"type": "walker", "x": x, "y": ground - 16, "range": 100}
                self.walkers.append(Walker(spec, self.cfg, self.state, color=self.alien_color))
            else:
                spec = {"type": "ufo", "x": x, "y": ground - 170, "range": 130}
                self.ufos.append(UFO(spec, self.cfg, self.state, color=ufo_color))

    # --- input --------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self.phase == "failed":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.manager.switch(settings.MAP)
                        return
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                        self._retry()
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._retry()
                    return
            return

        if self.phase == "brief":
            for event in events:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.manager.switch(settings.MENU)
                        return
                    self._start_mission()
                    return
            return

        if self.dlg.is_active():
            self.dlg.handle_events(events)
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.push(settings.PAUSE, parent=self)
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.player.jump()
                elif event.key == pygame.K_e:
                    if self.player.try_fire():
                        direction = pygame.Vector2(self.player.facing, 0)
                        muzzle = self.player.pos + direction * 20 + pygame.Vector2(0, -1)
                        self.lasers.append(LaserBolt(muzzle, direction))
                elif event.key == pygame.K_h:
                    self._hint()

    # --- update -------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt
        self.moment_flash = max(0.0, self.moment_flash - dt * 1.5)
        if self.phase == "failed":
            self.toast_timer = max(0.0, self.toast_timer - dt)
            self.hud.update(dt)
            return
        if self.phase == "brief":
            return

        if self.dlg.is_active():
            self.dlg.update(dt)
            self.hud.update(dt)
            return

        if self.won:
            return

        playing = not self.player.dead
        if playing:
            self.stopwatch += dt

        keys = pygame.key.get_pressed()
        self._apply_ice_friction()
        self.player.update(dt, keys, None, self.platforms)
        self._apply_wind(dt)

        if playing:
            self._update_enemies(dt)
            self._update_hazards(dt)
            self._update_storm(dt)
            self._check_pickups()
            self._advance_checkpoints()
            for item in self.pickups:
                item.update(dt)
            self._update_moment(dt)

        self._update_projectiles(dt)
        self._update_death(dt)

        self.dlg.update(dt)
        self.hud.update(dt)
        camera_x = self._camera_x()
        self.weather.update(dt, camera_dx=camera_x - self.last_camera_x)
        self.last_camera_x = camera_x

    def _apply_ice_friction(self) -> None:
        slippery = False
        for hazard in self.hazards:
            if hazard["type"] != "ice":
                continue
            zone = pygame.Rect(hazard["x"], hazard["y"] - 4, hazard["w"], 20)
            if zone.colliderect(self.player.rect):
                slippery = True
                break
        self.player.friction = self.player.base_friction * (0.12 if slippery else 1.0)

    def _apply_wind(self, dt: float) -> None:
        for hazard in self.hazards:
            if hazard["type"] != "wind":
                continue
            phase = (self.t + hazard.get("offset", 0.0)) % hazard["cycle"]
            if phase > hazard["cycle"] * 0.45:
                continue
            zone = pygame.Rect(hazard["x"], 0, hazard["w"], settings.HEIGHT)
            if zone.collidepoint(self.player.rect.center):
                self.player.vel.x += hazard["strength"] * dt

    def _update_enemies(self, dt: float) -> None:
        for walker in self.walkers:
            walker.update(dt, self.player)
            self._resolve_contact(walker)
        for ufo in self.ufos:
            shot = ufo.update(dt, self.player)
            if shot:
                self.plasma.append(shot)
            self._resolve_contact(ufo)

    def _resolve_contact(self, enemy) -> None:
        if not enemy.collides_player(self.player):
            return
        stomping = self.player.vel.y > 140 and self.player.rect.bottom <= enemy.rect.top + 16
        if stomping:
            enemy.hit()
            self.player.bounce()
        else:
            self.player.take_damage()

    def _update_projectiles(self, dt: float) -> None:
        for bolt in self.lasers:
            bolt.update(dt, self.world_rect, self.platforms)
            if bolt.dead and bolt.impact:
                self._spark(bolt.pos)
            if bolt.dead:
                continue
            for walker in self.walkers:
                if not walker.dead and bolt.rect.colliderect(walker.rect):
                    walker.hit()
                    bolt.dead = True
                    self._spark(bolt.pos)
                    break
            if bolt.dead:
                continue
            for ufo in self.ufos:
                if not ufo.dead and bolt.rect.colliderect(ufo.rect):
                    ufo.hit()
                    bolt.dead = True
                    self._spark(bolt.pos)
                    break
        self.lasers = [bolt for bolt in self.lasers if not bolt.dead]

        for shot in self.plasma:
            shot.update(dt, self.world_rect, self.platforms)
            if shot.dead:
                if shot.impact:
                    self._spark(shot.pos)
                continue
            if shot.rect.colliderect(self.player.hit_rect):
                self.player.take_damage()
                shot.dead = True
                self._spark(shot.pos, sound=False)
        self.plasma = [shot for shot in self.plasma if not shot.dead]

        for spark in self.sparks:
            spark[1] += dt
        self.sparks = [spark for spark in self.sparks if spark[1] < 0.22]

    def _spark(self, pos, sound: bool = True) -> None:
        """Small impact flash wherever a bolt really hits."""
        self.sparks.append([pygame.Vector2(pos), 0.0])
        if sound:
            audio.play("hit", 0.3)

    def _active_hazard_rect(self, hazard: dict) -> pygame.Rect | None:
        kind = hazard["type"]
        if kind == "spikes":
            return pygame.Rect(hazard["x"], hazard["y"] - 14, hazard["w"], 14)
        if kind == "acid_pool":
            return pygame.Rect(hazard["x"], hazard["y"] - 8, hazard["w"], 10)
        if kind == "geyser":
            phase = (self.t + hazard.get("offset", 0.0)) % hazard["cycle"]
            if phase < 1.1:
                return pygame.Rect(hazard["x"] - 14, hazard["y"] - 190, 30, 190)
            return None
        if kind == "lightning":
            phase = (self.t + hazard.get("offset", 0.0)) % hazard["cycle"]
            if phase < 0.35:
                top = self._ground_top_at(hazard["x"])
                return pygame.Rect(hazard["x"] - hazard["w"] // 2, 0, hazard["w"], top)
            return None
        return None

    def _ground_top_at(self, x: float) -> int:
        top = self.world_h
        for plat in self.platforms:
            if plat.left <= x <= plat.right and plat.height > 40:
                top = min(top, plat.top)
        return top

    def _update_hazards(self, dt: float) -> None:
        for hazard in self.hazards:
            if hazard["type"] == "meteor_zone":
                near = abs(hazard["x"] - self.player.pos.x) < 900
                timer = hazard.setdefault("timer", hazard.get("offset", 0.0))
                if near:
                    timer += dt
                    hazard["timer"] = timer
                    if timer >= hazard["cycle"]:
                        hazard["timer"] = 0.0
                        mx = hazard["x"] + random.uniform(-hazard["w"] / 2, hazard["w"] / 2)
                        direction = pygame.Vector2(random.uniform(-0.25, 0.25), 1)
                        self.plasma.append(
                            Projectile((mx, -20), direction, 300, radius=4, color=self.meteor_color)
                        )
                continue

            rect = self._active_hazard_rect(hazard)
            if rect and rect.colliderect(self.player.rect):
                self.player.take_damage()

    def _check_pickups(self) -> None:
        if not self.part.taken and self.part.collides(self.player.rect):
            self._collect_part()

        for item in self.pickups:
            if item.taken or not item.collides(self.player.rect):
                continue
            item.taken = True
            if item.kind == "health":
                self.health_taken += 1
                self.player.heal(1)
                audio.play("pickup")
                self._toast("SUPPLIES FOUND  +1 HEART")
            else:
                self.bonus_taken += 1
                audio.play("pickup", 0.8)
                self._toast(f"BONUS CELL  {self.bonus_taken}/{self.total_bonus}")
            self._refresh_checklist()

        if self.exit_active:
            exit_rect = pygame.Rect(0, 0, 74, 84)
            exit_rect.center = (int(self.exit_pos[0]), int(self.exit_pos[1]))
            if exit_rect.colliderect(self.player.rect):
                lines = self.dialogue["lines"].get("win", [])
                if lines:
                    self.dlg.queue(lines, on_done=self._win)
                else:
                    self._win()

    def _advance_checkpoints(self) -> None:
        for cp in self.checkpoints:
            if self.player.pos.x >= cp and not self.cp_active.get(cp):
                self.cp_active[cp] = True
                self.last_checkpoint = cp
                audio.play("pickup", 0.5)
                self._toast("CHECKPOINT REACHED")

    def _toast(self, message: str) -> None:
        self.toast = message
        self.toast_timer = 2.4

    def _refresh_checklist(self) -> None:
        items = [
            {
                "label": self.cfg["part"]["name"],
                "done": self.part.taken,
                "color": self.part_color,
            }
        ]
        if self.total_health:
            items.append(
                {
                    "label": f"Supplies  {self.health_taken}/{self.total_health}",
                    "done": self.health_taken >= self.total_health,
                    "color": (255, 120, 140),
                }
            )
        if self.total_bonus:
            items.append(
                {
                    "label": f"Bonus cells  {self.bonus_taken}/{self.total_bonus}",
                    "done": self.bonus_taken >= self.total_bonus,
                    "color": self.theme["accent"],
                }
            )
        self.hud.set_checklist(items)

    def _update_death(self, dt: float) -> None:
        if self.player.pos.y > self.world_h + 220 and not self.player.dead:
            self.player.take_damage(99)

        if self.player.dead:
            self.restart_timer = getattr(self, "restart_timer", 0.0) + dt
            if self.restart_timer > 1.0 and self.phase != "failed":
                # mission failed: show the fail screen instead of silently respawning
                self.phase = "failed"
                self.restart_timer = 0.0
                self.state.deaths += 1
                self.state.save()

    def _retry(self) -> None:
        """Restart the mission from the last checkpoint."""
        self.phase = "play"
        self.restart_timer = 0.0
        respawn_y = self._ground_top_at(self.last_checkpoint) - 40
        self.player.respawn(self.last_checkpoint, respawn_y)
        if self.state.deaths - self.deaths_at_start >= 3 and not self.death_hinted:
            self.death_hinted = True
            self._death_hint()

    # --- test hooks ---------------------------------------------------------
    def _test_complete(self) -> None:
        """Instantly finish the level (used by tools/playtest.py)."""
        if not self.part.taken:
            self._collect_part()
        self._win()

    # --- drawing ------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        camera_x = int(self._camera_x())
        camera_y = int(self._camera_y())
        camera = (camera_x, camera_y)
        view = self._view
        view.fill((4, 8, 18))

        world_bg.draw_backdrop(self.backdrop, view, camera_x)
        self._draw_platforms(view, camera)
        self._draw_props(view, camera)
        self._draw_checkpoints(view, camera)
        self._draw_hazards(view, camera)
        self._draw_start_pod(view, camera)
        self._draw_exit(view, camera)
        self._draw_part(view, camera)
        self._draw_pickups(view, camera)

        for walker in self.walkers:
            walker.draw(view, camera)
        for ufo in self.ufos:
            ufo.draw(view, camera)
        for bolt in self.lasers:
            bolt.draw(view, camera)
        for shot in self.plasma:
            shot.draw(view, camera)

        self.player.draw(view, camera)
        self._draw_sparks(view, camera)

        # scale the world pass up to the window: a closer camera on the action
        pygame.transform.scale(view, (settings.WIDTH, settings.HEIGHT), screen)

        self.weather.draw(screen)
        self.weather.draw_haze(screen)

        if self.storm_active:
            self._draw_storm(screen, camera)

        self.hud.draw(screen)
        self._draw_toast(screen)
        self._draw_moment_flash(screen)
        self._draw_minimap(screen)
        self._draw_stopwatch(screen)
        self.dlg.draw(screen)
        if self.phase == "brief":
            self._draw_brief(screen)

    def _draw_platforms(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        for plat in self.platforms:
            r = plat.move(-camera[0], -camera[1])
            if r.right < -40 or r.left > settings.WIDTH + 40:
                continue
            pygame.draw.rect(screen, self.theme["ground"], r)
            top = r.copy()
            top.height = 7
            pygame.draw.rect(screen, self.theme["ground_top"], top)
            pygame.draw.rect(screen, self.theme["ground_edge"], r, 1)

    def _draw_checkpoints(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        for cp in self.checkpoints:
            top = self._ground_top_at(cp) - camera[1]
            x = cp - camera[0]
            if x < -40 or x > settings.WIDTH + 40 or top < -60 or top > settings.HEIGHT + 60:
                continue
            active = self.cp_active.get(cp)
            color = self.theme["accent"] if active else settings.FAINT
            # pulse halo on the checkpoint the player last touched
            if active and cp == self.last_checkpoint:
                pulse = 9 + int(3 * math.sin(self.t * 4.0))
                pygame.draw.circle(screen, color, (int(x), int(top - 24)), pulse, 1)
            pygame.draw.line(screen, (120, 136, 162), (x, top), (x, top - 46), 3)
            pygame.draw.circle(screen, (10, 16, 28), (int(x), int(top - 47)), 3, 1)
            wave = math.sin(self.t * 3.0 + cp * 0.7) * 2 if active else 0
            pygame.draw.polygon(
                screen,
                color,
                [(x, top - 46), (x + 19, top - 40 + wave), (x, top - 32)],
            )
            if not active:
                pygame.draw.polygon(
                    screen,
                    (10, 16, 28),
                    [(x, top - 46), (x + 19, top - 40), (x, top - 32)],
                    1,
                )

    def _draw_props(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        """Decorations: rocks, crystals, ruins — themed per world."""
        for prop in self.props:
            x = prop["x"] - camera[0]
            if x < -60 or x > settings.WIDTH + 60:
                continue
            y = prop["y"] - camera[1]
            s = prop["s"]
            kind = prop["kind"]
            if kind == "rock":
                for dx, dy, r in ((-8, -3, 9), (4, -2, 7), (11, -3, 5)):
                    pygame.draw.circle(
                        screen, self.theme["ground_edge"],
                        (int(x + dx * s), int(y + dy * s)), int(r * s),
                    )
                pygame.draw.circle(
                    screen, self.theme["ridge_near"],
                    (int(x - 2 * s), int(y - 8 * s)), int(5 * s),
                )
            elif kind == "crystal":
                h = (26 + prop["variant"] * 9) * s
                tilt = (-6 + prop["variant"] * 5) * s
                pygame.draw.polygon(
                    screen, self.theme["accent"],
                    [(x - 6 * s, y), (x + 6 * s, y), (x + tilt, y - h)],
                )
                pygame.draw.polygon(
                    screen, (255, 255, 255),
                    [(x - 6 * s, y), (x + tilt, y - h), (x + tilt + 3 * s, y - h + 7 * s)],
                    1,
                )
            elif kind == "ruin":
                h = (30 + prop["variant"] * 12) * s
                w = 12 * s
                rect = pygame.Rect(int(x - w / 2), int(y - h), int(w), int(h))
                pygame.draw.rect(screen, self.theme["ridge_far"], rect, border_radius=2)
                pygame.draw.rect(screen, self.theme["ground_edge"], rect, 1, border_radius=2)
                pygame.draw.line(
                    screen, self.theme["ground_edge"],
                    (x - w / 2, y - h * 0.6), (x + w / 2, y - h * 0.5), 1,
                )
            else:  # shard: a floating crystal fragment
                bob = math.sin(self.t * 1.6 + prop["x"] * 0.1) * 4 * s
                size = 7 * s
                pygame.draw.polygon(
                    screen, self.theme["accent"],
                    [
                        (x, y - size + bob),
                        (x + size * 0.7, y + bob),
                        (x, y + size + bob),
                        (x - size * 0.7, y + bob),
                    ],
                    1,
                )

    def _draw_pickups(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        for item in self.pickups:
            if item.taken:
                continue
            ix = item.center[0] - camera[0]
            iy = item.center[1] - camera[1]
            if ix < -40 or ix > settings.WIDTH + 40:
                continue
            bob = math.sin(item.t * 3.0) * 3
            if item.kind == "health":
                halo = 11 + int(2 * math.sin(item.t * 4.0))
                pygame.draw.circle(screen, (255, 120, 140), (int(ix), int(iy + bob)), halo, 1)
                sprites.draw_heart(screen, (int(ix), int(iy + bob)), item.radius * 2, filled=True)
            else:
                halo = 12 + int(2 * math.sin(item.t * 4.0))
                pygame.draw.circle(screen, item.color, (int(ix), int(iy + bob)), halo, 1)
                sprites.draw_part(screen, (int(ix), int(iy + bob)), item.radius, item.color, item.t, glow=False)

    def _draw_sparks(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        for pos, age in self.sparks:
            k = age / 0.22
            radius = int(3 + 10 * k)
            alpha = int(230 * (1 - k))
            size = radius * 2 + 4
            ring = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 232, 170, alpha), (size // 2, size // 2), radius, 2)
            screen.blit(
                ring,
                (int(pos.x - camera[0] - size // 2), int(pos.y - camera[1] - size // 2)),
            )

    def _draw_toast(self, screen: pygame.Surface) -> None:
        if self.toast_timer <= 0.0 or not self.toast:
            return
        alpha = min(1.0, self.toast_timer / 0.4)
        width = text.measure(self.toast, 17)[0] + 34
        rect = pygame.Rect(0, 0, width, 30)
        rect.midtop = (settings.WIDTH // 2, 170)
        pill = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(pill, (6, 11, 24, int(215 * alpha)), pill.get_rect(), border_radius=15)
        screen.blit(pill, rect.topleft)
        pygame.draw.rect(screen, (*self.theme["accent"],), rect, 1, border_radius=15)
        text.draw(
            screen, self.toast, (rect.centerx, rect.centery), 17,
            settings.INK, center=True, middle=True, shadow=False,
        )

    def _draw_hazards(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        for hazard in self.hazards:
            kind = hazard["type"]
            x = hazard["x"] - camera[0]
            if x < -200 or x > settings.WIDTH + 200:
                continue
            if kind == "spikes":
                base_y = hazard["y"] - camera[1]
                for i in range(int(hazard["w"] // 14)):
                    sx = hazard["x"] + i * 14 - camera[0]
                    pygame.draw.polygon(
                        screen,
                        self.theme["hazard"],
                        [(sx, base_y), (sx + 14, base_y), (sx + 7, base_y - 13)],
                    )
            elif kind == "acid_pool":
                rect = pygame.Rect(hazard["x"], hazard["y"] - 8, hazard["w"], 8).move(-camera[0], -camera[1])
                pygame.draw.rect(screen, (110, 220, 120), rect, border_radius=4)
                for i in range(3):
                    bubble_x = hazard["x"] + (i + 0.5) * hazard["w"] / 3 - camera[0]
                    bubble_y = hazard["y"] - 10 - camera[1] - 4 * abs(math.sin(self.t * 3 + i))
                    pygame.draw.circle(screen, (190, 255, 170), (int(bubble_x), int(bubble_y)), 2)
            elif kind == "ice":
                rect = pygame.Rect(hazard["x"], hazard["y"] - 3, hazard["w"], 5).move(-camera[0], -camera[1])
                pygame.draw.rect(screen, (220, 245, 255), rect, border_radius=2)
            elif kind == "geyser":
                vent = pygame.Rect(hazard["x"] - 18, hazard["y"] - 8, 36, 8).move(-camera[0], -camera[1])
                pygame.draw.rect(screen, (90, 74, 58), vent, border_radius=3)
                phase = (self.t + hazard.get("offset", 0.0)) % hazard["cycle"]
                if phase < 1.1:
                    strength = 1.0 - abs(phase - 0.55) / 0.55
                    color = self.theme["hazard"]
                    for i in range(9):
                        h = ((self.t * 260 + i * 30) % 190)
                        wobble = math.sin(self.t * 12 + i) * 6
                        alpha = max(0, int(170 * strength * (1 - h / 190)))
                        particle = pygame.Surface((12, 12), pygame.SRCALPHA)
                        pygame.draw.circle(particle, (*color, alpha), (6, 6), 5)
                        screen.blit(
                            particle,
                            (int(x + wobble - 6), int(hazard["y"] - 8 - h - camera[1])),
                        )
            elif kind == "lightning":
                phase = (self.t + hazard.get("offset", 0.0)) % hazard["cycle"]
                if phase < 0.5:
                    charge = 1.0 - abs(phase - 0.25) / 0.25 if phase < 0.35 else 0.0
                    if charge > 0:
                        pygame.draw.circle(
                            screen,
                            self.theme["hazard"],
                            (int(x), int(20 - camera[1])),
                            int(6 + 10 * charge),
                            1,
                        )
                if phase < 0.35:
                    top = self._ground_top_at(hazard["x"])
                    points = [(int(x), int(-camera[1]))]
                    y = 0
                    while y < top:
                        y += 28
                        points.append((int(x + random.uniform(-12, 12)), int(min(y, top) - camera[1])))
                    pygame.draw.lines(screen, (255, 240, 170), False, points, 2)
            elif kind == "wind":
                phase = (self.t + hazard.get("offset", 0.0)) % hazard["cycle"]
                if phase < hazard["cycle"] * 0.45:
                    for i in range(10):
                        wy = 60 + i * 56
                        wx = hazard["x"] + ((self.t * 420 + i * 80) % hazard["w"]) - camera[0]
                        pygame.draw.line(
                            screen,
                            (170, 200, 255),
                            (int(wx), wy),
                            (int(wx + 26), wy + 3),
                            1,
                        )

    def _draw_start_pod(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        sx = 130 - camera[0]
        ground_top = self._ground_top_at(130) - camera[1]
        if sx < -100 or sx > settings.WIDTH + 100:
            return
        sprites.draw_ship(screen, (int(sx), int(ground_top - 34)), 0.8, self.t, damaged=True, thrust=False)

    def _draw_exit(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        ex = int(self.exit_pos[0] - camera[0])
        ey = int(self.exit_pos[1] - camera[1])
        if ex < -100 or ex > settings.WIDTH + 100:
            return
        sprites.draw_ship(screen, (ex, ey), 1.0, self.t, damaged=not self.exit_active, thrust=self.exit_active)
        if self.exit_active:
            bob = int(math.sin(self.t * 4.0) * 4)
            label = "RETURN TO SHIP"
            width = text.measure(label, 16)[0] + 24
            rect = pygame.Rect(ex - width // 2, ey - 92 + bob, width, 26)
            pygame.draw.rect(screen, (6, 11, 24), rect, border_radius=13)
            pygame.draw.rect(screen, settings.GREEN, rect, 1, border_radius=13)
            text.draw(screen, label, (rect.centerx, rect.centery), 16, settings.GREEN, center=True, middle=True, shadow=False)

    def _draw_part(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        if self.part.taken:
            return
        px, py = self.part.center
        self.part.update(0.0)
        px -= camera[0]
        py -= camera[1]
        sprites.draw_part(screen, (int(px), int(py)), self.part.radius, self.part_color, self.t)
        label = self.cfg["part"]["name"]
        width = text.measure(label, 15)[0] + 22
        rect = pygame.Rect(int(px - camera[0]) - width // 2, int(py) - 44, width, 24)
        pygame.draw.rect(screen, (6, 11, 24), rect, border_radius=12)
        pygame.draw.rect(screen, self.part_color, rect, 1, border_radius=12)
        text.draw(screen, label, (rect.centerx, rect.centery), 15, settings.INK, center=True, middle=True, shadow=False)

    def _draw_storm(self, screen: pygame.Surface, camera: tuple[int, int]) -> None:
        """Dust storm: the world is fully hidden outside the visibility circle."""
        radius = int(self.visibility_radius * self.zoom)
        px = int((self.player.pos.x - camera[0]) * self.zoom)
        py = int((self.player.pos.y - camera[1]) * self.zoom)
        overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        overlay.fill((172, 112, 62, 255))
        cut = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(cut, (0, 0, 0, 255), (radius, radius), radius)
        # feathered edge: full-clear core, then a semi-haze band at the rim
        for shrink, alpha in ((radius, 90), (int(radius * 0.86), 255)):
            pygame.draw.circle(cut, (0, 0, 0, alpha), (radius, radius), shrink)
        overlay.blit(cut, (px - radius, py - radius), special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(overlay, (0, 0))
        # faint drifting dust streaks inside the visible circle
        for index in range(7):
            streak_y = (index * 37 + int(self.t * 140)) % (radius * 2) - radius
            streak_x = px - radius + (index * 53 + int(self.t * 260)) % (radius * 2)
            pygame.draw.line(
                screen,
                (214, 150, 90),
                (streak_x, py + streak_y),
                (streak_x + 22, py + streak_y - 4),
                1,
            )

    # --- minimap / stopwatch ------------------------------------------------
    def _draw_moment_flash(self, screen: pygame.Surface) -> None:
        """Red alert wash when the world's signature moment kicks in."""
        if self.moment_flash <= 0.0:
            return
        alpha = int(120 * min(1.0, self.moment_flash))
        veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        veil.fill((255, 70, 60, alpha))
        screen.blit(veil, (0, 0))
        if self.moment_flash > 0.55:
            label = "ALERT"
            width = text.measure(label, 22)[0] + 26
            rect = pygame.Rect(0, 0, width, 32)
            rect.midtop = (settings.WIDTH // 2, 108)
            pygame.draw.rect(screen, (6, 11, 24), rect, border_radius=16)
            pygame.draw.rect(screen, settings.DANGER, rect, 1, border_radius=16)
            text.draw(screen, label, (rect.centerx, rect.centery), 22, settings.DANGER, center=True, middle=True, shadow=False)

    def _draw_minimap(self, screen: pygame.Surface) -> None:
        radius = 62
        diameter = radius * 2
        center = (settings.WIDTH - radius - 26, radius + 66)
        mini = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(mini, (6, 11, 24, 205), (radius, radius), radius)

        def project(x: float, y: float) -> tuple[int, int]:
            mx = int(10 + x / self.world_w * (diameter - 20))
            my = int(10 + y / self.world_h * (diameter - 20))
            return (mx, my)

        for plat in self.platforms:
            a = project(plat.x, plat.y)
            b = project(plat.right, plat.y)
            pygame.draw.line(mini, self.theme["ground_top"], a, b, 2)

        for hazard in self.hazards:
            if hazard["type"] in ("spikes", "geyser", "lightning", "acid_pool", "meteor_zone"):
                pygame.draw.circle(mini, self.theme["hazard"], project(hazard["x"], hazard["y"]), 2)

        # during a dust storm the minimap keeps secrets too: no enemy positions
        if not self.storm_active:
            for walker in self.walkers:
                if not walker.dead:
                    pygame.draw.circle(mini, settings.DANGER, project(*walker.pos), 2)
            for ufo in self.ufos:
                if not ufo.dead:
                    pygame.draw.circle(mini, settings.DANGER, project(*ufo.pos), 2)

        if not self.part.taken:
            part_pos = project(*self.part.pos)
            pygame.draw.polygon(
                mini,
                self.part_color,
                [
                    (part_pos[0], part_pos[1] - 4),
                    (part_pos[0] + 4, part_pos[1]),
                    (part_pos[0], part_pos[1] + 4),
                    (part_pos[0] - 4, part_pos[1]),
                ],
            )
        exit_mark = project(*self.exit_pos)
        pygame.draw.circle(mini, settings.GREEN, exit_mark, 3)

        player_pos = project(self.player.pos.x, self.player.pos.y)
        pulse = 3 + int(2 * abs(math.sin(self.t * 5.0)))
        pygame.draw.circle(mini, settings.ACCENT, player_pos, pulse)

        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius - 1)
        mini.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(mini, (center[0] - radius, center[1] - radius))
        pygame.draw.circle(screen, self.theme["ground_top"], center, radius, 2)

        label = self.cfg["name"].upper()
        text.draw(
            screen, label, (center[0], center[1] - radius - 14), 15,
            settings.DIM, center=True, shadow=False,
        )

    def _draw_stopwatch(self, screen: pygame.Surface) -> None:
        center_x = settings.WIDTH - 88
        top = 66 + 62 * 2 + 12
        text.draw(screen, "TIME", (center_x, top), 14, settings.FAINT, center=True, shadow=False)
        text.draw(
            screen,
            _format_time(self.stopwatch),
            (center_x, top + 16),
            22,
            settings.INK,
            display=True,
            center=True,
            shadow=False,
        )
        best = self.state.best_time(self.level_id)
        if best is not None:
            text.draw(
                screen,
                f"BEST {_format_time(best)}",
                (center_x, top + 44),
                14,
                settings.DIM,
                center=True,
                shadow=False,
            )

    def _draw_brief(self, screen: pygame.Surface) -> None:
        veil = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        veil.fill((4, 8, 18, 215))
        screen.blit(veil, (0, 0))

        card = pygame.Rect(0, 0, 720, 430)
        card.center = (settings.WIDTH // 2, settings.HEIGHT // 2 - 10)
        pygame.draw.rect(screen, settings.PANEL, card, border_radius=16)
        pygame.draw.rect(screen, self.theme["accent"], card, 2, border_radius=16)

        x = card.x + 40
        y = card.y + 30
        text.draw(screen, "MISSION BRIEF", (x, y), 15, settings.DIM, shadow=False)
        y += 34
        text.draw(screen, self.cfg["name"].upper(), (x, y), 26, self.theme["accent"], display=True, shadow=False)
        y += 44

        # part goal with icon
        sprites.draw_part(screen, (x + 14, y + 14), 13, self.part_color, self.t, glow=False)
        goal = f"Recover the {self.cfg['part']['name']}"
        text.draw(screen, goal, (x + 38, y + 4), 22, settings.INK, middle=True, shadow=False)
        y += 44

        objective = self.cfg.get("objective", "")
        if objective:
            text.draw(screen, objective, (x, y), 19, settings.DIM, max_width=card.width - 80, shadow=False)
            y += 46

        briefing = self.cfg.get("briefing", [])
        for line in briefing:
            pygame.draw.circle(screen, self.theme["accent"], (x + 4, y + 9), 3)
            text.draw(screen, line, (x + 16, y), 18, settings.DIM, max_width=card.width - 96, shadow=False)
            y += 26

        y = card.bottom - 96
        pygame.draw.line(screen, settings.PANEL_EDGE, (x, y - 12), (card.right - 40, y - 12), 1)
        text.draw(
            screen,
            "WASD / Arrows move   SPACE / UP / W jump   E fire   H hint",
            (x, y),
            16,
            settings.FAINT,
            shadow=False,
        )
        blink = (pygame.time.get_ticks() // 450) % 2 == 0
        if blink:
            text.draw(
                screen,
                "PRESS SPACE TO LAUNCH",
                (card.centerx, card.bottom - 34),
                18,
                self.theme["accent"],
                display=True,
                center=True,
                shadow=False,
            )
