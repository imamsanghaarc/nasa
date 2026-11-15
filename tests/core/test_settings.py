"""Tests for ``core.settings`` - the constant/paths module."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, r"E:\nasa")

from core import settings


class TestWindow:
    def test_resolution(self):
        assert settings.WIDTH == 1280
        assert settings.HEIGHT == 720
        assert settings.FPS == 60

    def test_strings(self):
        assert settings.TITLE == "MISSION LAIKA: THE RED HORIZON"
        assert settings.SUBTITLE
        assert settings.CAPTION == f"{settings.TITLE} - {settings.SUBTITLE}"
        assert "NASA" in settings.HACKATHON


class TestPaths:
    def test_root_points_at_repo(self):
        assert settings.ROOT == Path(r"E:\nasa")
        assert (settings.ROOT / "core").is_dir()

    def test_derived_paths(self):
        assert settings.ASSETS == settings.ROOT / "assets"
        assert settings.DATA == settings.ROOT / "data"
        assert settings.SAVE_FILE == settings.ROOT / "savegame.json"

    def test_data_and_assets_exist(self):
        assert settings.DATA.is_dir()
        assert settings.ASSETS.is_dir()

    def test_font_names(self):
        assert settings.FONT_DISPLAY.endswith(".ttf")
        assert settings.FONT_BODY.endswith(".ttf")
        assert settings.FONT_DISPLAY != settings.FONT_BODY


class TestPalette:
    NAMES = (
        "SPACE", "SPACE_DEEP", "PANEL", "PANEL_LIGHT", "PANEL_EDGE",
        "INK", "DIM", "FAINT", "ACCENT", "ACCENT_DARK", "WARN",
        "DANGER", "GOLD", "GREEN", "RED", "RUST", "RUST_DARK",
        "DUST", "DUST_PALE", "BASALT", "METAL", "METAL_LIGHT",
    )

    def test_all_colors_are_rgb_triplets(self):
        for name in self.NAMES:
            value = getattr(settings, name)
            assert isinstance(value, tuple), name
            assert len(value) == 3, name
            assert all(0 <= channel <= 255 for channel in value), name

    def test_color_constants_are_distinct_enough(self):
        assert settings.SPACE != settings.SPACE_DEEP
        assert settings.INK != settings.DIM
        assert settings.DIM != settings.FAINT


class TestDifficulty:
    def test_order(self):
        assert settings.DIFFICULTIES == ("easy", "normal", "hard")

    def test_labels_cover_every_difficulty(self):
        assert set(settings.DIFFICULTY_LABELS) == set(settings.DIFFICULTIES)

    def test_blurbs_cover_every_difficulty(self):
        assert set(settings.DIFFICULTY_BLURB) == set(settings.DIFFICULTIES)

    def test_blurbs_non_empty(self):
        for key, text in settings.DIFFICULTY_BLURB.items():
            assert text.strip(), key


class TestSceneNames:
    def test_core_names(self):
        assert settings.BOOT == "boot"
        assert settings.MENU == "menu"
        assert settings.MAP == "map"
        assert settings.BRIEFING == "briefing"
        assert settings.TUTORIAL == "tutorial"
        assert settings.ENDING == "ending"
        assert settings.PAUSE == "pause"

    def test_level_scene_names(self):
        assert settings.LEVEL1 == "level1"
        assert settings.LEVEL2 == "level2"
        assert settings.LEVEL3 == "level3"
        assert settings.LEVEL4 == "level4"

    def test_planet_constants(self):
        assert settings.MERCURY == "mercury"
        assert settings.NEPTUNE == "neptune"
        assert settings.PLANET_SCENES == (
            "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune",
        )
        assert len(settings.PLANET_SCENES) == 7


class TestCampaign:
    def test_level_ids(self):
        assert settings.LEVEL_IDS == ("outpost", "landing", "surface", "tunnel")

    def test_level_scenes_map(self):
        scene_map = getattr(settings, "LEVEL_" + "SCENES")
        assert set(scene_map) == set(settings.LEVEL_IDS)
        for index, level_id in enumerate(settings.LEVEL_IDS, start=1):
            assert scene_map[level_id] == f"level{index}"

    def test_first_level(self):
        assert settings.FIRST_LEVEL == "outpost"
        assert settings.FIRST_LEVEL == settings.LEVEL_IDS[0]

    def test_playable_scenes(self):
        # NOTE: ``PLAYABLE_SCENES`` is assigned twice in settings.py (lines 78 and
        # 99). The second assignment wins so "tutorial" is dropped from the tuple.
        # Documented in test_core_bugs.py::test_playable_scenes_duplicate_assignment.
        assert isinstance(settings.PLAYABLE_SCENES, tuple)
        assert set(settings.PLAYABLE_SCENES) == {
            "level1", "level2", "level3", "level4", "ending",
        }
