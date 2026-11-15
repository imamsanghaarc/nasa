"""Solar system map: hub screen to inspect and launch missions."""

from __future__ import annotations

import math

import pygame

from art import backgrounds, planets, sprites
from core import audio, color as core_color, levels, settings, text
from core.scene import Scene
from ui.button import Button

hex_to_rgb = core_color.hex_to_rgb


def draw_ring(
    screen: pygame.Surface,
    cx: int,
    cy: int,
    radius: float,
    color: tuple[int, int, int],
    t: float,
) -> None:
    # Smooth pulsing: use a constant radius for stable planet positions
    pulse = 0.5
    pygame.draw.circle(screen, color, (cx, cy), int(radius * pulse), 2)


class MapScene(Scene):
    name = settings.MAP

    def on_enter(self, **data) -> None:
        self.stars = backgrounds.starfield(settings.WIDTH, settings.HEIGHT, seed=11)
        self.neb = backgrounds.nebula(settings.WIDTH, settings.HEIGHT, seed=5)
        self.vignette = backgrounds.vignette(settings.WIDTH, settings.HEIGHT)
        self.planets = levels.load_planets()["planets"]
        self.selected = None
        self.t = 0.0
        self.toast = ""
        self.toast_timer = 0.0
        self.mouse = (settings.WIDTH // 2, settings.HEIGHT // 2)
        self._resolve_positions()
        self.panel_buttons: list[Button] = []
        self.menu_button = Button(
            (settings.WIDTH - 300, 16, 284, 44), "Back to menu", self._back_to_menu
        )
        self.profile_button = Button(
            (settings.WIDTH - 466, 16, 152, 44), "Profile", self._toggle_profile, style="ghost"
        )
        self.profile_open = False
        self.name_buffer = self.state.player_name
        self.editing_name = False
        self._build_panel()

    # --- setup --------------------------------------------------------------
    def _resolve_positions(self) -> None:
        for planet in self.planets:
            p = planet["map_position"]
            planet["_pos"] = (int(p[0] * settings.WIDTH), int(p[1] * settings.HEIGHT))

    def _seed_for(self, planet) -> int:
        return sum(ord(ch) for ch in planet["id"]) * 7 + 1

    def _back_to_menu(self) -> None:
        self.manager.switch(settings.MENU)

    # --- profile ------------------------------------------------------------
    def _toggle_profile(self) -> None:
        self.profile_open = not self.profile_open
        self.editing_name = False
        self.name_buffer = self.state.player_name
        audio.play("click" if self.profile_open else "back")

    def _commit_name(self) -> None:
        cleaned = self.name_buffer.strip() or "Pilot"
        self.state.player_name = cleaned[:16]
        self.state.save()
        self.name_buffer = self.state.player_name

    def _profile_rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, 560, 586)
        rect.center = (settings.WIDTH // 2, settings.HEIGHT // 2 + 6)
        return rect

    # --- selection ----------------------------------------------------------
    def _find_at(self, pos: tuple[int, int]):
        for planet in self.planets:
            px, py = planet["_pos"]
            radius = int(planet["radius"] * 1.9)
            if (pos[0] - px) ** 2 + (pos[1] - py) ** 2 <= radius * radius:
                return planet
        return None

    def select(self, planet) -> None:
        self.selected = planet
        self._build_panel()
        audio.play("click")

    def deselect(self) -> None:
        if self.selected:
            self.selected = None
            self._build_panel()
            audio.play("back")

    # --- panel layout -------------------------------------------------------
    def _panel_rect(self) -> pygame.Rect:
        return pygame.Rect(884, 112, 372, 564)

    def _build_panel(self) -> None:
        """Buttons only. All text is drawn every frame in _draw_panel_content,
        so nothing is painted at build time and nothing overflows the box."""
        self.panel_buttons = []
        planet = self.selected
        self.close_rect = None
        if planet is None:
            return

        panel = self._panel_rect()
        x = panel.x + 34
        width = panel.width - 68
        y = panel.bottom - 70
        self.close_rect = pygame.Rect(panel.right - 30, panel.y + 50, 26, 26)

        playable = planet.get("playable")
        part = planet.get("part")

        if playable == "ending":
            if self.state.all_parts():
                self.panel_buttons.append(
                    Button((x, y, width, 46), "Assemble the ship", self._launch_ending)
                )
        elif playable:
            unlocked = self.state.is_unlocked(planet)
            owned = self.state.has_part(part) if part else False
            if unlocked and not owned:
                self.panel_buttons.append(
                    Button((x, y, width, 46), "Launch mission", self._launch_planet)
                )
        else:
            self.panel_buttons.append(
                Button((x, y, width, 46), "Log fact", self._log_archive)
            )

    def _launch_planet(self) -> None:
        self.manager.switch(self.selected["playable"])

    def _launch_ending(self) -> None:
        self.manager.switch(settings.ENDING)

    def _log_archive(self) -> None:
        for key in self.selected.get("facts", []):
            self.state.add_fact(key)
        self.toast = f"{self.selected['name']} fact logged"
        self.toast_timer = 3.0
        self.state.save()

    # --- helpers ------------------------------------------------------------
    def _short(self, value: str, max_px: int, size: int = 14) -> str:
        if text.measure(value, size)[0] <= max_px:
            return value
        trimmed = value
        while trimmed and text.measure(trimmed + "...", size)[0] > max_px:
            trimmed = trimmed[:-1]
        return trimmed + "..."

    def _fit_lines(self, value: str, width: int, max_height: int):
        """Pick the largest text size whose wrapped block fits the given height."""
        for size in (18, 17, 16, 15, 14):
            lines = text.wrap(value, size, width, False)
            line_h = text.font(size).get_linesize() + 3
            if len(lines) * line_h <= max_height:
                return size, lines, line_h
        size = 14
        lines = text.wrap(value, size, width, False)
        line_h = text.font(size).get_linesize() + 3
        max_lines = max(1, max_height // line_h)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            if len(lines[-1]) > 1:
                lines[-1] = lines[-1][:-1] + "..."
        return size, lines, line_h

    def _chip(
        self,
        screen: pygame.Surface,
        *,
        cy: int,
        label: str,
        color: tuple[int, int, int],
        right: int | None = None,
        left: int | None = None,
    ) -> int:
        width = text.measure(label, 14)[0] + 26
        rect = pygame.Rect(0, 0, width, 26)
        rect.centery = cy
        if right is not None:
            rect.right = right
        else:
            rect.x = left or 0
        pygame.draw.rect(screen, (9, 14, 26), rect, border_radius=13)
        pygame.draw.rect(screen, color, rect, 1, border_radius=13)
        text.draw(
            screen, label, (rect.centerx, rect.centery), 14, color,
            center=True, middle=True, shadow=False,
        )
        return width

    def _draw_part_icons(self, screen: pygame.Surface) -> None:
        by_part = {p.get("part"): p for p in self.planets if p.get("part")}
        x = 204
        for part in self.state.required_parts():
            planet = by_part.get(part)
            pcolor = hex_to_rgb(planet.get("part_color", planet.get("color", "#8fa3c8"))) if planet else settings.ACCENT
            owned = self.state.has_part(part)
            center = (x + 11, 45)
            if owned:
                sprites.draw_part(screen, center, 9, pcolor, self.t, glow=False)
            else:
                pygame.draw.circle(screen, settings.PANEL_EDGE, center, 9, 1)
                pygame.draw.circle(screen, (20, 30, 48), center, 7)
            x += 26

    # --- input --------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.mouse = event.pos

        if self.profile_open:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.editing_name:
                            self.editing_name = False
                            self.name_buffer = self.state.player_name
                        else:
                            self.profile_open = False
                        audio.play("back")
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        self.editing_name = False
                        self._commit_name()
                        audio.play("click")
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_buffer = self.name_buffer[:-1]
                    else:
                        glyph = getattr(event, "unicode", "") or ""
                        if glyph and len(self.name_buffer) < 16 and glyph.isprintable():
                            self.name_buffer += glyph
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._profile_rect().collidepoint(event.pos):
                        name_row = pygame.Rect(0, 0, 420, 44)
                        name_row.midtop = (settings.WIDTH // 2, self._profile_rect().top + 92)
                        self.editing_name = name_row.collidepoint(event.pos)
                        if self.editing_name:
                            audio.play("click")
                    else:
                        self.profile_open = False
                        self.editing_name = False
                        self._commit_name()
                        audio.play("back")
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.switch(settings.MENU)
                    return
                if event.key == pygame.K_p:
                    self._toggle_profile()
                    return
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._launch_selected()
                    return

        if self.menu_button.handle_events(events):
            return
        if self.profile_button.handle_events(events):
            return
        for button in self.panel_buttons:
            if button.handle_events(events):
                return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.close_rect is not None and self.close_rect.collidepoint(event.pos):
                    self.deselect()
                    return
                planet = self._find_at(event.pos)
                if planet is not None:
                    self.select(planet)
                    if planet.get("playable") and not self.state.is_unlocked(planet):
                        prev = levels.previous_mission(planet["id"])
                        prev_name = next(
                            (p["name"] for p in self.planets if p["id"] == prev), prev
                        ) if prev else "the tutorial"
                        self.toast = f"Locked - win {prev_name} first"
                        self.toast_timer = 3.0
                elif not self._panel_rect().collidepoint(event.pos):
                    self.deselect()

    def _launch_selected(self) -> None:
        planet = self.selected
        playable = planet.get("playable") if planet else None
        part = planet.get("part") if planet else None
        if not playable:
            return
        if playable == "ending":
            if self.state.all_parts():
                self.manager.switch(settings.ENDING)
            return
        if part and self.state.has_part(part):
            return
        if self.state.is_unlocked(planet):
            self.manager.switch(playable)

    # --- update -------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast = ""

    # --- drawing ------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        self.screen = screen
        screen.blit(self.stars, (0, 0))
        screen.blit(self.neb, (0, 0))

        sun_pos = (settings.WIDTH // 2, settings.HEIGHT // 2 + 16)
        self._draw_orbits(screen, sun_pos)
        planets.draw_sun(screen, sun_pos, 44, self.t)
        self._draw_mission_hints(screen, sun_pos)
        self._draw_planets(screen)
        self._draw_status_bar(screen)
        self.menu_button.draw(screen)
        self.profile_button.draw(screen)
        self._draw_panel(screen)

        for button in self.panel_buttons:
            button.draw(screen)

        self._draw_toast(screen)
        if self.profile_open:
            self._draw_profile(screen)
        screen.blit(self.vignette, (0, 0))

    def _draw_orbits(self, screen: pygame.Surface, sun_pos: tuple[int, int]) -> None:
        seen: set[int] = set()
        for planet in self.planets:
            orbit = planet["orbit_px"]
            if orbit in seen:
                continue
            seen.add(orbit)
            planets.draw_orbit(screen, sun_pos, orbit, color=(36, 54, 88), dashed=2)

    def _draw_mission_hints(self, screen: pygame.Surface, sun_pos: tuple[int, int]) -> None:
        for planet in self.planets:
            if not planet.get("playable"):
                continue
            px, py = planet["_pos"]
            dist = math.hypot(px - sun_pos[0], py - sun_pos[1])
            if dist <= 70:
                continue
            angle = math.atan2(py - sun_pos[1], px - sun_pos[0])
            anchor_r = min(dist - planet["radius"] - 10, 40)
            ax = sun_pos[0] + math.cos(angle) * anchor_r
            ay = sun_pos[1] + math.sin(angle) * anchor_r
            # Reduced pulse for stable hint lines
            pulse = 0.25
            pygame.draw.line(screen, settings.ACCENT, sun_pos, (ax, ay), 1)
            pygame.draw.circle(screen, settings.ACCENT, (int(ax), int(ay)), int(2 + 2 * pulse))

    def _draw_planets(self, screen: pygame.Surface) -> None:
        hover = self._find_at(self.mouse)
        for planet in self.planets:
            px, py = planet["_pos"]
            color = hex_to_rgb(planet.get("color", "#8fa3c8"))
            unlocked = self.state.is_unlocked(planet)
            playable = planet.get("playable")
            planets.draw_planet(
                screen,
                (px, py),
                planet["radius"],
                color,
                band_color=hex_to_rgb(planet.get("band_color", "#5a6b82")),
                bands=planet.get("bands", 0),
                craters=planet.get("craters", 0),
                seed=self._seed_for(planet),
                ring=planet.get("ring", False),
                ring_color=hex_to_rgb(planet.get("ring_color", "#d2c4b4")),
            )
            if playable and not unlocked:
                self._draw_padlock(screen, px, py, int(planet["radius"]))
                if planet == hover:
                    self._draw_hover_tooltip(screen, planet, subtitle="Locked")
                continue
            if self.selected == planet:
                pygame.draw.circle(screen, settings.ACCENT, (px, py), int(planet["radius"]) * 1.6, 2)
                pygame.draw.circle(screen, settings.ACCENT, (px, py), int(planet["radius"]) * 1.9, 1)
                self._draw_hover_tooltip(screen, planet)
            elif planet == hover:
                draw_ring(screen, px, py, int(planet["radius"]) * 1.9 + 10, settings.ACCENT, self.t)
                self._draw_hover_tooltip(screen, planet)

    def _draw_padlock(self, screen: pygame.Surface, cx: int, cy: int, radius: int) -> None:
        """Small padlock above a locked planet."""
        lock_y = cy - radius - 16
        body = pygame.Rect(cx - 6, lock_y, 12, 9)
        pygame.draw.rect(screen, (10, 16, 30), body, border_radius=2)
        pygame.draw.rect(screen, settings.DANGER, body, 1, border_radius=2)
        pygame.draw.arc(screen, settings.DANGER, (cx - 4, lock_y - 7, 8, 9), 0, 180, 1)

    def _draw_status_bar(self, screen: pygame.Surface) -> None:
        text.draw(screen, "SOLAR SYSTEM", (20, 16), 20, settings.ACCENT, display=True, shadow=False)
        required = self.state.required_parts()
        text.draw(
            screen,
            f"PARTS {self.state.part_count}/{len(required)}",
            (20, 44),
            19,
            settings.INK,
            shadow=False,
        )
        self._draw_part_icons(screen)

    def _draw_close_button(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, (20, 30, 50), rect, border_radius=6)
        pygame.draw.rect(screen, settings.DANGER, rect, 2, border_radius=6)
        cx, cy = rect.center
        pygame.draw.line(screen, settings.DANGER, (cx - 9, cy - 9), (cx + 9, cy + 9), 2)
        pygame.draw.line(screen, settings.DANGER, (cx + 9, cy - 9), (cx - 9, cy + 9), 2)

    def _draw_panel(self, screen: pygame.Surface) -> None:
        panel = self._panel_rect()
        pygame.draw.rect(screen, settings.PANEL, panel, border_radius=14)
        pygame.draw.rect(screen, settings.PANEL_EDGE, panel, 2, border_radius=14)

        header_h = 56
        text.draw(screen, "DETAILS", (panel.x + 20, panel.y + 18), 16, settings.ACCENT, display=True)
        text.draw(
            screen,
            "click empty space to close",
            (panel.right - 20, panel.y + 22),
            14,
            settings.FAINT,
            right=True,
            shadow=False,
        )
        pygame.draw.line(
            screen, settings.PANEL_EDGE,
            (panel.x + 2, panel.y + header_h), (panel.right - 2, panel.y + header_h), 1,
        )

        if self.selected is not None and self.close_rect is not None:
            self._draw_close_button(screen, self.close_rect)

        if self.selected is None:
            text.draw(
                screen,
                "Select a planet to inspect\nits mission or archive fact.",
                (panel.centerx, panel.centery),
                20,
                settings.DIM,
                center=True,
                shadow=False,
            )
            return

        self._draw_panel_content(screen, panel)

    def _draw_panel_content(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        planet = self.selected
        x = panel.x + 34
        width = panel.width - 68
        pcolor = hex_to_rgb(planet.get("color", "#8fa3c8"))
        playable = planet.get("playable")
        part = planet.get("part")

        # accent underline in the planet's colour
        pygame.draw.line(
            screen, pcolor, (panel.x + 18, panel.y + 56), (panel.right - 18, panel.y + 56), 3
        )

        # preview
        preview_r = 46
        preview_cy = panel.y + 66 + preview_r
        planets.draw_planet(
            screen,
            (panel.centerx, preview_cy),
            preview_r,
            pcolor,
            band_color=hex_to_rgb(planet.get("band_color", "#5a6b82")),
            bands=planet.get("bands", 0),
            craters=planet.get("craters", 0),
            seed=self._seed_for(planet),
            ring=planet.get("ring", False),
            ring_color=hex_to_rgb(planet.get("ring_color", "#d2c4b4")),
        )

        y = preview_cy + preview_r + 16

        if playable == "ending":
            title = f"{planet['name']} - Finale"
        elif playable:
            title = f"{planet['name']} Mission"
        else:
            title = f"{planet['name']} - Archive"
        text.draw(
            screen, title, (panel.centerx, y), 16, settings.INK,
            display=True, center=True, shadow=False,
        )
        y += 28
        text.draw(
            screen, planet.get("tagline", ""), (panel.centerx, y), 16, settings.DIM,
            center=True, max_width=width, shadow=False,
        )
        y += 30

        pygame.draw.line(screen, settings.PANEL_EDGE, (x, y), (panel.right - 34, y), 1)
        y += 12

        text.draw(screen, "FACT", (x, y), 14, settings.ACCENT, shadow=False)
        text.draw(
            screen, planet.get("source", "NASA"),
            (panel.right - 34, y), 13, settings.FAINT, right=True, shadow=False,
        )
        y += 20

        # part / status row (reserved space at the bottom of the panel)
        part_row_cy = panel.bottom - 96
        max_fact_h = max(40, part_row_cy - 14 - y)
        size, lines, line_h = self._fit_lines(planet["fact"], width, max_fact_h)
        for index, line in enumerate(lines):
            text.draw(screen, line, (x, y + index * line_h), size, settings.INK, shadow=False)

        # --- bottom row: status depends on mission type ------------------------
        if playable == "ending":
            if self.state.all_parts():
                self._chip(screen, cy=part_row_cy, label="READY TO LAUNCH", color=settings.GREEN, right=panel.right - 34)
            else:
                label = f"PARTS {self.state.part_count}/{len(self.state.required_parts())}"
                self._chip(screen, cy=part_row_cy, label=label, color=settings.GOLD, right=panel.right - 34)
            text.draw(
                screen, "Rebuild the ship to go home", (x, part_row_cy), 15,
                settings.DIM, middle=True, shadow=False,
            )
        elif playable:
            unlocked = self.state.is_unlocked(planet)
            owned = self.state.has_part(part) if part else False
            if unlocked:
                if part:
                    pygame.draw.circle(
                        screen, pcolor if owned else settings.FAINT, (x + 8, part_row_cy), 6,
                        0 if owned else 1,
                    )
                    text.draw(
                        screen, self._short(part, width - 170, 16), (x + 22, part_row_cy), 16,
                        settings.INK, middle=True, shadow=False,
                    )
            else:
                prev = levels.previous_mission(planet["id"])
                prev_name = next(
                    (p["name"] for p in self.planets if p["id"] == prev), prev
                ) if prev else "the tutorial"
                pygame.draw.circle(screen, settings.FAINT, (x + 8, part_row_cy), 6, 1)
                text.draw(
                    screen, f"Win {prev_name} to unlock", (x + 22, part_row_cy), 16,
                    settings.DIM, middle=True, shadow=False,
                )
            if unlocked and owned:
                self._chip(screen, cy=part_row_cy, label="RECOVERED", color=settings.GREEN, right=panel.right - 34)
            elif unlocked:
                self._chip(screen, cy=part_row_cy, label="MISSION READY", color=settings.ACCENT, right=panel.right - 34)
            else:
                self._chip(screen, cy=part_row_cy, label="LOCKED", color=settings.DANGER, right=panel.right - 34)
        else:
            self._chip(screen, cy=part_row_cy, label="DATA ONLY", color=settings.FAINT, right=panel.right - 34)
            text.draw(
                screen, "Not recoverable on a flyby", (x, part_row_cy), 15,
                settings.DIM, middle=True, shadow=False,
            )

    def _draw_profile(self, screen: pygame.Surface) -> None:
        """Pilot profile: set a name and see every part and where it came from."""
        panel = self._profile_rect()
        pygame.draw.rect(screen, settings.PANEL, panel, border_radius=16)
        pygame.draw.rect(screen, settings.ACCENT, panel, 2, border_radius=16)

        x = panel.x + 40
        text.draw(screen, "PILOT PROFILE", (x, panel.y + 24), 20, settings.ACCENT, display=True, shadow=False)
        text.draw(
            screen, "P / Esc to close", (panel.right - 40, panel.y + 28), 14,
            settings.FAINT, right=True, shadow=False,
        )
        pygame.draw.line(screen, settings.PANEL_EDGE, (x, panel.y + 58), (panel.right - 40, panel.y + 58), 1)

        # --- name row -----------------------------------------------------
        name_rect = pygame.Rect(0, 0, 420, 44)
        name_rect.midtop = (panel.centerx, panel.y + 92)
        editing = self.editing_name
        pygame.draw.rect(screen, (8, 14, 26), name_rect, border_radius=10)
        pygame.draw.rect(
            screen,
            settings.ACCENT if editing else settings.PANEL_EDGE,
            name_rect, 2, border_radius=10,
        )
        shown = self.name_buffer + ("|" if editing and (pygame.time.get_ticks() // 380) % 2 == 0 else "")
        text.draw(
            screen, shown or "Pilot", (name_rect.x + 16, name_rect.centery), 20,
            settings.INK, middle=True, shadow=False,
        )
        text.draw(screen, "NAME", (x, name_rect.centery), 14, settings.DIM, shadow=False)
        hint = "type to rename  ·  Enter to save" if editing else "click the name to edit"
        text.draw(
            screen, hint, (panel.centerx, panel.y + 148), 14, settings.FAINT,
            center=True, shadow=False,
        )

        # --- collected parts ----------------------------------------------
        y = panel.y + 182
        text.draw(screen, "PARTS RECOVERED", (x, y), 14, settings.ACCENT, shadow=False)
        text.draw(
            screen,
            f"{self.state.part_count}/{len(self.state.required_parts())}",
            (panel.right - 40, y), 14, settings.DIM, right=True, shadow=False,
        )
        y += 30
        by_part = {p.get("part"): p for p in self.planets if p.get("part")}
        for part in self.state.required_parts():
            planet = by_part.get(part)
            world = planet["name"] if planet else "?"
            pcolor = hex_to_rgb(planet.get("part_color", planet.get("color", "#8fa3c8"))) if planet else settings.ACCENT
            owned = self.state.has_part(part)
            best = self.state.best_time(planet["id"]) if planet else None
            center = (x + 12, y + 12)
            if owned:
                sprites.draw_part(screen, center, 10, pcolor, self.t, glow=False)
            else:
                pygame.draw.circle(screen, settings.PANEL_EDGE, center, 10, 1)
                pygame.draw.circle(screen, (20, 30, 48), center, 8)
            text.draw(screen, part, (x + 34, y + 2), 16, settings.INK if owned else settings.DIM, shadow=False)
            sub = f"found in {world}"
            if owned and best is not None:
                minutes = int(best // 60)
                seconds = int(best % 60)
                sub += f"  ·  best {minutes:01d}:{seconds:02d}"
            text.draw(
                screen, sub if owned else f"not recovered yet — {world}",
                (x + 34, y + 20), 13, settings.DIM if owned else settings.FAINT, shadow=False,
            )
            if owned:
                text.draw(
                    screen, "OK", (panel.right - 40, y + 12), 15, settings.GREEN,
                    right=True, middle=True, shadow=False,
                )
            y += 44

        # --- footer stats ---------------------------------------------------
        y = panel.bottom - 44
        pygame.draw.line(screen, settings.PANEL_EDGE, (x, y - 24), (panel.right - 40, y - 24), 1)
        text.draw(
            screen,
            self.state.status_line(),
            (panel.centerx, y), 15, settings.DIM, center=True, shadow=False,
        )

    def _draw_toast(self, screen: pygame.Surface) -> None:
        if not self.toast:
            return
        width = text.measure(self.toast, 18)[0] + 40
        rect = pygame.Rect((settings.WIDTH - width) // 2, settings.HEIGHT - 66, width, 30)
        pygame.draw.rect(screen, (6, 11, 24), rect, border_radius=15)
        pygame.draw.rect(screen, settings.GOLD, rect, 1, border_radius=15)
        text.draw(
            screen, self.toast, (rect.centerx, rect.centery), 18,
            settings.INK, center=True, middle=True, shadow=False,
        )

    def _draw_hover_tooltip(self, screen: pygame.Surface, planet, subtitle: str | None = None) -> None:
        name = planet["name"]
        label = f"{name} - {subtitle}" if subtitle else name
        width = text.measure(label, 16)[0] + 20
        rect = pygame.Rect(planet["_pos"][0] - width // 2, planet["_pos"][1] - 36, width, 22)
        pygame.draw.rect(screen, settings.PANEL, rect, border_radius=6)
        pygame.draw.rect(screen, settings.PANEL_EDGE, rect, 1, border_radius=6)
        text.draw(
            screen, label, (rect.centerx, rect.centery), 16,
            settings.DANGER if subtitle else settings.INK,
            center=True, middle=True, shadow=False,
        )
