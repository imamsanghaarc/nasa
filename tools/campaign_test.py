"""Headless campaign test: plays the four campaign levels end to end.

This is the regression guard for the "campaign levels never leave the intro phase"
blocker.  It drives each level with simulated input and asserts that

* every phase declared in ``data/levels/<id>.json`` is reachable,
* no phase stalls (the level always moves forward),
* the levels can actually be completed,
* the inter-level briefing hands over to the next level,
* the failure paths (wrong food, lost rover) work.

Run from the project root::

    python tools/campaign_test.py
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

from core import audio, levels, settings  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.scene import Game  # noqa: E402
from scenes.briefing import BriefingScene  # noqa: E402
from scenes.ending import EndingScene  # noqa: E402
from scenes.level1 import Level1Scene  # noqa: E402
from scenes.level2 import Level2Scene  # noqa: E402
from scenes.level3 import Level3Scene  # noqa: E402
from scenes.level4 import Level4Scene  # noqa: E402

CAMPAIGN = {
    settings.LEVEL1: Level1Scene,
    settings.LEVEL2: Level2Scene,
    settings.LEVEL3: Level3Scene,
    settings.LEVEL4: Level4Scene,
}

DT = 1 / 60.0
DT_FAST = 0.1


# ---------------------------------------------------------------------------
# Fake input
# ---------------------------------------------------------------------------

class _FakeKeys:
    """Stand-in for the object returned by ``pygame.key.get_pressed()``."""

    def __init__(self) -> None:
        self.pressed: set[int] = set()

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


class _FakeMouse:
    def __init__(self) -> None:
        self.pos = (0, 0)

    def get_pos(self) -> tuple[int, int]:
        return self.pos


KEYS = _FakeKeys()
MOUSE = _FakeMouse()
pygame.key.get_pressed = lambda: KEYS  # type: ignore[assignment]
pygame.mouse.get_pos = lambda: MOUSE.get_pos()  # type: ignore[assignment]


class Harness:
    """Drives a scene with simulated keyboard and mouse input."""

    def __init__(self, state: GameState | None = None) -> None:
        self.state = state or GameState()
        self.game = Game(_surface(), _surface(), self.state)
        self.game.manager.register(settings.BRIEFING, BriefingScene)
        self.game.manager.register(settings.ENDING, EndingScene)
        for name, cls in CAMPAIGN.items():
            self.game.manager.register(name, cls)
        self.scene = None
        self.phases: list[str] = []

    # -- input ------------------------------------------------------------
    def press(self, *keys: int) -> None:
        for key in keys:
            KEYS.pressed.add(key)

    def release(self, *keys: int) -> None:
        for key in keys:
            KEYS.pressed.discard(key)

    def tap(self, key: int, frames: int = 2) -> None:
        self.press(key)
        self.step(frames)
        self.release(key)

    def click(self, pos: tuple[int, int], button: int = 1) -> None:
        MOUSE.pos = pos
        self.game.manager.handle_events([
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button),
        ])

    # -- loop -------------------------------------------------------------
    def step(self, frames: int = 1, dt: float = DT) -> None:
        for _ in range(frames):
            self.game.manager.handle_events([])
            self.game.manager.update(dt)
            self.game.manager.draw()
            name = self.game.manager.current_name
            if self.scene is not None and name == self.scene.name:
                if not self.phases or self.phases[-1] != self.scene.phase:
                    self.phases.append(self.scene.phase)

    def enter(self, name: str, **data) -> None:
        self.scene = self.game.manager.switch(name, **data)
        self.phases = [self.scene.phase]

    def advance_dialogue(self, limit: int = 400) -> str:
        """Mash SPACE until the dialogue box closes."""
        for _ in range(limit):
            self.tap(pygame.K_SPACE, frames=1)
            if not self.scene.dlg.is_active():
                break
        return self.scene.phase

    def wait_for_phase(self, wanted: str, limit: int = 600, dt: float = DT) -> bool:
        """Step until the scene reaches ``wanted`` (or another phase appears)."""
        for _ in range(limit):
            if self.scene.phase == wanted:
                return True
            self.step(1, dt)
        return self.scene.phase == wanted

    def wait_until(self, predicate, limit: int = 600, dt: float = DT) -> bool:
        for _ in range(limit):
            if predicate():
                return True
            self.step(1, dt)
        return predicate()


_SURFACES: list[pygame.Surface] = []


def _surface() -> pygame.Surface:
    if not _SURFACES:
        pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    surface = pygame.Surface((settings.WIDTH, settings.HEIGHT))
    _SURFACES.append(surface)
    return surface


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(condition), detail))
    mark = "ok  " if condition else "FAIL"
    line = f"{mark}  {name}"
    if detail:
        line += f" - {detail}"
    print(line)
    return bool(condition)


def test_level1() -> None:
    """Level 1: food challenge, crumbs, exercise, rest."""
    harness = Harness()
    harness.enter(settings.LEVEL1)

    check("level1 leaves intro", harness.advance_dialogue() == "food_briefing",
          f"phase={harness.scene.phase}")

    # the food vending must open
    harness.step(2)
    vending = harness.scene.vending
    check("level1 opens the food vending", vending is not None,
          f"vending={type(vending).__name__}")
    if vending is None:
        return

    # wrong food -> food_wrong modal
    vending.selected = ["soda_can", "cookie"]
    harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
    harness.step(2)
    check("level1 wrong food is rejected", harness.scene.phase == "food_wrong",
          f"phase={harness.scene.phase}")
    check("level1 wrong food shows the protocol modal", harness.scene.modal is not None)

    # restart the mission through the modal button
    harness.scene.modal.buttons[0].activate()
    harness.step(2)
    check("level1 wrong food restarts the mission", harness.scene.phase == "intro",
          f"phase={harness.scene.phase}")

    # now do it properly
    harness.advance_dialogue()
    harness.step(2)
    vending = harness.scene.vending
    vending.selected = ["sealed_drink", "irradiated_chicken"]
    harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
    harness.step(2)
    check("level1 correct food is accepted", harness.scene.phase == "food_correct",
          f"phase={harness.scene.phase}")

    harness.advance_dialogue()
    harness.step(2)
    check("level1 reaches the meal phase", harness.scene.phase == "food_eat",
          f"phase={harness.scene.phase}")

    # eat at the table
    harness.scene.player_pos = pygame.Vector2(harness.scene.table_rect.center)
    harness.tap(pygame.K_e)
    harness.step(2)
    check("level1 meal is eaten", harness.scene.phase == "clean_crumbs",
          f"phase={harness.scene.phase}")

    # vacuum every crumb
    harness.scene.player_pos = pygame.Vector2(harness.scene.vacuum_rect.center)
    for _ in range(harness.scene.crumbs_total + 4):
        harness.tap(pygame.K_e)
        if harness.scene.phase != "clean_crumbs":
            break
    check("level1 crumbs are cleaned", harness.scene.phase == "exercise_intro",
          f"phase={harness.scene.phase} crumbs={harness.scene.crumbs_cleaned}")

    harness.advance_dialogue()
    harness.step(2)
    check("level1 reaches the harness vending", harness.scene.phase == "vending_code",
          f"phase={harness.scene.phase}")

    harness.step(2)
    vending = harness.scene.vending
    check("level1 opens the harness vending", vending is not None)
    if vending is None:
        return
    vending.selected = ["harness"]
    harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
    harness.step(2)
    check("level1 harness is accepted", harness.scene.phase == "bike_ready",
          f"phase={harness.scene.phase}")

    # strap in
    harness.step(2)
    check("level1 shows the bike modal", harness.scene.modal is not None)
    if harness.scene.modal is not None:
        harness.scene.modal.buttons[0].activate()
        harness.step(2)
    check("level1 reaches the bike", harness.scene.phase == "bike",
          f"phase={harness.scene.phase}")

    # pedal: alternate left and right
    for _ in range(20):
        harness.tap(pygame.K_a)
        harness.tap(pygame.K_d)
        if harness.scene.phase != "bike":
            break
    check("level1 bike ride completes", harness.scene.phase == "rest_intro",
          f"phase={harness.scene.phase} progress={getattr(harness.scene, 'bike_progress', 0)}")

    # choose the resting stations
    harness.step(2)
    modal = harness.scene.modal
    check("level1 shows the rest modal", modal is not None)
    if modal is not None:
        modal.buttons[2].activate()
        harness.step(2)
    check("level1 reaches rest_done", harness.scene.phase == "rest_done",
          f"phase={harness.scene.phase}")

    harness.advance_dialogue()
    harness.step(2)
    check("level1 reaches complete", harness.scene.phase == "complete",
          f"phase={harness.scene.phase}")

    harness.wait_for_phase("complete", limit=400, dt=DT_FAST)
    check("level1 hands over to the briefing", harness.game.manager.current_name == settings.BRIEFING,
          f"scene={harness.game.manager.current_name}")
    check("level1 is recorded as done", "outpost" in harness.state.levels_done,
          f"levels_done={harness.state.levels_done}")


def test_level2() -> None:
    """Level 2: landing kit, landing, comms test."""
    harness = Harness()
    harness.enter(settings.LEVEL2)

    check("level2 leaves intro", harness.advance_dialogue() == "landing_briefing",
          f"phase={harness.scene.phase}")

    harness.step(2)
    vending = harness.scene.vending
    check("level2 opens the equipment vending", vending is not None)
    if vending is None:
        return

    # wrong kit first
    vending.selected = ["toy", "balloon", "disco"]
    harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
    harness.step(2)
    check("level2 wrong kit is rejected", harness.scene.phase == "landing_wrong",
          f"phase={harness.scene.phase}")

    harness.wait_for_phase("landing_briefing", limit=200, dt=DT_FAST)
    check("level2 returns to the equipment bay", harness.scene.phase == "landing_briefing",
          f"phase={harness.scene.phase}")

    harness.step(2)
    vending = harness.scene.vending
    vending.selected = ["parachute", "heat_shield", "sky_crane"]
    harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
    harness.step(2)
    check("level2 correct kit is accepted", harness.scene.phase == "landing_correct",
          f"phase={harness.scene.phase}")

    harness.wait_for_phase("comm_test", limit=600, dt=DT_FAST)
    check("level2 reaches the comms test", harness.scene.phase == "comm_test",
          f"phase={harness.scene.phase}")

    # waiting is the correct answer - the send button must not be pressed
    harness.wait_for_phase("comm_success", limit=900, dt=DT_FAST)
    check("level2 comms test succeeds", harness.scene.phase == "comm_success",
          f"phase={harness.scene.phase}")

    harness.wait_for_phase("complete", limit=400, dt=DT_FAST)
    check("level2 hands over to the briefing", harness.game.manager.current_name == settings.BRIEFING,
          f"scene={harness.game.manager.current_name}")
    check("level2 is recorded as done", "landing" in harness.state.levels_done,
          f"levels_done={harness.state.levels_done}")


def test_level3() -> None:
    """Level 3: the level Leslie reported - photography, storm, hibernation."""
    harness = Harness()
    harness.enter(settings.LEVEL3)

    check("level3 leaves intro", harness.advance_dialogue() == "photo_intro",
          f"phase={harness.scene.phase}")
    check("level3 reaches the photography briefing",
          harness.advance_dialogue() == "take_photos",
          f"phase={harness.scene.phase}")

    scene = harness.scene
    check("level3 has six camera buttons", len(scene.photo_buttons) == 6,
          f"buttons={len(scene.photo_buttons)}")

    # every camera button must be reachable on foot
    for index, rect in enumerate(scene.photo_buttons):
        scene.player_pos = pygame.Vector2(rect.center)
        harness.tap(pygame.K_e)
        harness.step(1)
    check("level3 takes every photo", scene.photo_count == 6, f"photos={scene.photo_count}")

    # the sample
    scene.player_pos = pygame.Vector2(scene.sample_rect.center)
    harness.tap(pygame.K_e)
    harness.step(1)
    check("level3 collects the rock sample", scene.sample_collected)
    check("level3 starts the sandstorm", scene.phase == "sandstorm",
          f"phase={scene.phase}")

    # shelter behind a boulder, then Low Power Mode
    rock = scene.rocks[0]
    scene.player_pos = pygame.Vector2(rock["x"], rock["y"])
    harness.step(2)
    check("level3 detects shelter", scene.sheltered, f"sheltered={scene.sheltered}")

    harness.tap(pygame.K_l)
    harness.step(2)
    check("level3 activates low power mode", scene.low_power, f"low_power={scene.low_power}")
    check("level3 reaches the cold alert", scene.phase == "cold_alert",
          f"phase={scene.phase}")

    harness.tap(pygame.K_h)
    harness.step(2)
    check("level3 enters hibernation", scene.phase == "hibernation",
          f"phase={scene.phase}")

    harness.wait_for_phase("complete", limit=900, dt=DT_FAST)
    check("level3 reaches complete", scene.phase == "complete", f"phase={scene.phase}")

    harness.wait_until(lambda: harness.game.manager.current_name == settings.BRIEFING,
                       limit=400, dt=DT_FAST)
    check("level3 hands over to the briefing", harness.game.manager.current_name == settings.BRIEFING,
          f"scene={harness.game.manager.current_name}")
    check("level3 is recorded as done", "surface" in harness.state.levels_done,
          f"levels_done={harness.state.levels_done}")
    check("level3 awards the Thermal Regulator", harness.state.has_part("Thermal Regulator"),
          f"inventory={harness.state.inventory}")


def test_level3_failure_paths() -> None:
    """Level 3: the rover can still be lost."""
    harness = Harness()
    harness.enter(settings.LEVEL3)
    harness.advance_dialogue()
    harness.advance_dialogue()
    scene = harness.scene

    # take the photos and the sample so the storm starts
    for rect in scene.photo_buttons:
        scene.player_pos = pygame.Vector2(rect.center)
        harness.tap(pygame.K_e)
        harness.step(1)
    scene.player_pos = pygame.Vector2(scene.sample_rect.center)
    harness.tap(pygame.K_e)
    harness.step(1)
    check("level3 storm starts for the failure test", scene.phase == "sandstorm",
          f"phase={scene.phase}")

    # find a spot with no boulder within shelter range
    open_spot = None
    for x in range(60, settings.WIDTH - 60, 40):
        for y in range(60, settings.HEIGHT - 60, 40):
            point = pygame.Vector2(x, y)
            if not any(
                point.distance_to(pygame.Vector2(rock["x"], rock["y"])) <= rock["r"] + 48
                for rock in scene.rocks
            ):
                open_spot = point
                break
        if open_spot:
            break
    check("level3 has an exposed spot to test in", open_spot is not None)

    if open_spot is not None:
        scene.player_pos = pygame.Vector2(open_spot)
        harness.press(pygame.K_d)
        for _ in range(120):
            harness.step(1, DT_FAST)
            if scene.phase != "sandstorm":
                break
        harness.release(pygame.K_d)
        check("level3 rover is lost in the open dust", scene.phase == "intro",
              f"phase={scene.phase} exposure={scene.dust_exposure:.2f}")
        check("level3 records the loss", harness.state.outcome == "lost",
              f"outcome={harness.state.outcome}")


def test_level4() -> None:
    """Level 4: flashlight, tunnel, buttons, escape."""
    harness = Harness()
    harness.enter(settings.LEVEL4)

    check("level4 leaves intro", harness.advance_dialogue() == "flashlight_on",
          f"phase={harness.scene.phase}")

    harness.tap(pygame.K_f)
    harness.step(2)
    check("level4 flashlight turns on", harness.scene.flashlight_on,
          f"flashlight={harness.scene.flashlight_on}")
    check("level4 reaches the tunnel", harness.scene.phase == "explore",
          f"phase={harness.scene.phase}")

    scene = harness.scene
    scene.player_pos = pygame.Vector2(scene.rock_button_rect.center)
    harness.tap(pygame.K_e)
    harness.step(1)
    check("level4 finds the rock sample", bool(scene.buttons_pressed & 1),
          f"buttons={scene.buttons_pressed}")

    scene.player_pos = pygame.Vector2(scene.camera_button_rect.center)
    harness.tap(pygame.K_e)
    harness.step(1)
    check("level4 activates the camera", bool(scene.buttons_pressed & 2),
          f"buttons={scene.buttons_pressed}")
    check("level4 reaches find_objects", scene.phase == "find_objects",
          f"phase={scene.phase}")

    harness.wait_for_phase("complete", limit=900, dt=DT_FAST)
    check("level4 reaches complete", scene.phase == "complete", f"phase={scene.phase}")

    harness.wait_until(lambda: harness.game.manager.current_name in (settings.BRIEFING, settings.ENDING),
                       limit=400, dt=DT_FAST)
    check("level4 finishes the campaign",
          harness.game.manager.current_name in (settings.BRIEFING, settings.ENDING),
          f"scene={harness.game.manager.current_name}")


def test_level4_jump_reachability() -> None:
    """The rock ledges must be reachable with the configured jump."""
    harness = Harness()
    harness.enter(settings.LEVEL4)
    harness.advance_dialogue()
    harness.tap(pygame.K_f)
    harness.step(2)

    scene = harness.scene
    # stand on the first ledge and check the player can actually land on it
    scene.player_pos = pygame.Vector2(scene.rock_ledges[0].centerx, scene.rock_ledges[0].y - 30)
    scene.vy = 0.0
    for _ in range(30):
        scene.vy = scene.vy + scene.gravity * DT
        scene.player_pos.y += scene.vy * DT
        if scene.player_pos.y > scene._ledge_top() + 20:
            scene.player_pos.y = scene._ledge_top() + 20
            scene.vy = 0.0
        for ledge in scene.rock_ledges:
            if (
                scene.player_pos.y + 30 >= ledge.y
                and scene.player_pos.y <= ledge.bottom
                and scene.player_pos.x + 25 > ledge.x
                and scene.player_pos.x < ledge.right
            ):
                scene.player_pos.y = ledge.y - 30
                scene.vy = 0.0
    check("level4 ledge is standable", abs(scene.player_pos.y - (scene.rock_ledges[0].y - 30)) < 2,
          f"y={scene.player_pos.y:.1f} expected={scene.rock_ledges[0].y - 30}")

    # the jump must reach the ledge from the ground
    height = scene.jump_velocity * scene.jump_velocity / (2.0 * scene.gravity)
    ground = scene._ledge_top() + 20
    check("level4 jump reaches the ledge", ground - height <= scene.rock_ledges[0].y - 30,
          f"apex={ground - height:.1f} ledge={scene.rock_ledges[0].y - 30}")


def test_full_campaign() -> None:
    """The whole campaign: level 1 -> 2 -> 3 -> 4 -> ending."""
    state = GameState()
    harness = Harness(state)
    harness.enter(settings.LEVEL1)

    def complete_level1() -> None:
        harness.advance_dialogue()
        harness.step(2)
        harness.scene.vending.selected = ["sealed_drink", "irradiated_chicken"]
        harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        harness.step(2)
        harness.advance_dialogue()
        harness.scene.player_pos = pygame.Vector2(harness.scene.table_rect.center)
        harness.tap(pygame.K_e)
        harness.step(2)
        harness.scene.player_pos = pygame.Vector2(harness.scene.vacuum_rect.center)
        for _ in range(harness.scene.crumbs_total + 4):
            harness.tap(pygame.K_e)
            if harness.scene.phase != "clean_crumbs":
                break
        harness.advance_dialogue()
        harness.step(2)
        harness.scene.vending.selected = ["harness"]
        harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        harness.step(2)
        harness.scene.modal.buttons[0].activate()
        harness.step(2)
        for _ in range(20):
            harness.tap(pygame.K_a)
            harness.tap(pygame.K_d)
            if harness.scene.phase != "bike":
                break
        harness.step(2)
        harness.scene.modal.buttons[2].activate()
        harness.step(2)
        harness.advance_dialogue()
        harness.wait_for_phase("complete", limit=400, dt=DT_FAST)

    def complete_level2() -> None:
        harness.advance_dialogue()
        harness.step(2)
        harness.scene.vending.selected = ["parachute", "heat_shield", "sky_crane"]
        harness.game.manager.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        harness.step(2)
        harness.wait_for_phase("comm_success", limit=900, dt=DT_FAST)
        harness.wait_for_phase("complete", limit=400, dt=DT_FAST)

    def complete_level3() -> None:
        harness.advance_dialogue()
        harness.advance_dialogue()
        scene = harness.scene
        for rect in scene.photo_buttons:
            scene.player_pos = pygame.Vector2(rect.center)
            harness.tap(pygame.K_e)
            harness.step(1)
        scene.player_pos = pygame.Vector2(scene.sample_rect.center)
        harness.tap(pygame.K_e)
        harness.step(1)
        rock = scene.rocks[0]
        scene.player_pos = pygame.Vector2(rock["x"], rock["y"])
        harness.step(2)
        harness.tap(pygame.K_l)
        harness.step(2)
        harness.tap(pygame.K_h)
        harness.step(2)
        harness.wait_for_phase("complete", limit=900, dt=DT_FAST)

    def complete_level4() -> None:
        harness.advance_dialogue()
        harness.tap(pygame.K_f)
        harness.step(2)
        scene = harness.scene
        scene.player_pos = pygame.Vector2(scene.rock_button_rect.center)
        harness.tap(pygame.K_e)
        harness.step(1)
        scene.player_pos = pygame.Vector2(scene.camera_button_rect.center)
        harness.tap(pygame.K_e)
        harness.step(1)
        harness.wait_for_phase("complete", limit=900, dt=DT_FAST)

    plan = [
        (settings.LEVEL1, complete_level1),
        (settings.LEVEL2, complete_level2),
        (settings.LEVEL3, complete_level3),
        (settings.LEVEL4, complete_level4),
    ]

    for index, (scene_name, driver) in enumerate(plan):
        if harness.game.manager.current_name == settings.BRIEFING:
            harness.tap(pygame.K_SPACE)
            harness.step(2)
        check(f"campaign reaches {scene_name}", harness.game.manager.current_name == scene_name,
              f"scene={harness.game.manager.current_name}")
        driver()
        # wait for the level to hand over
        harness.wait_until(
            lambda: harness.game.manager.current_name in (settings.BRIEFING, settings.ENDING),
            limit=900,
            dt=DT_FAST,
        )
        check(f"campaign leaves {scene_name}",
              harness.game.manager.current_name in (settings.BRIEFING, settings.ENDING),
              f"scene={harness.game.manager.current_name}")

    check("campaign finishes at the ending", harness.game.manager.current_name == settings.ENDING,
          f"scene={harness.game.manager.current_name}")
    check("campaign records every level",
          set(harness.state.levels_done) == {"outpost", "landing", "surface", "tunnel"},
          f"levels_done={harness.state.levels_done}")


def test_data_integrity() -> None:
    """Every campaign phase must have a handler and a dialogue trigger."""
    for level_id, cls in CAMPAIGN.items():
        config = levels.load_level(level_id)
        dialogue = levels.load_dialogue(config.get("dialogue", "dialogue/mars.json"))
        for entry in config["phases"]:
            phase_id = entry["id"]
            check(f"{level_id}:{phase_id} has a handler", phase_id in cls.phase_handlers)
            trigger = entry.get("dialogue_trigger")
            if trigger:
                check(f"{level_id}:{phase_id} has dialogue",
                      bool(dialogue["lines"].get(trigger)),
                      f"trigger={trigger}")


def main() -> int:
    pygame.init()
    audio.init()

    print("=" * 68)
    print("MISSION LAIKA: THE RED HORIZON - campaign test")
    print("=" * 68)

    test_data_integrity()
    print("-" * 68)
    test_level1()
    print("-" * 68)
    test_level2()
    print("-" * 68)
    test_level3()
    print("-" * 68)
    test_level3_failure_paths()
    print("-" * 68)
    test_level4()
    print("-" * 68)
    test_level4_jump_reachability()
    print("-" * 68)
    test_full_campaign()
    print("=" * 68)

    failures = [name for name, ok, _ in RESULTS if not ok]
    print(f"{len(RESULTS) - len(failures)}/{len(RESULTS)} checks passed")
    if failures:
        print("FAILED:")
        for name in failures:
            print(f"  - {name}")
        pygame.quit()
        return 1
    print("all campaign checks ok")
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
