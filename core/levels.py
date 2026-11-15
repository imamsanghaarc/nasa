"""JSON mission data.

All gameplay numbers live in ``data/levels/*.json``; the campaign order and the
judge-facing blurb live in ``data/mission.json``. Scenes read through this module so a
bad edit produces a readable error instead of a traceback in the middle of a frame.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from core import settings

LEVEL_KEYS = ("id", "name", "dialogue", "params", "objective")

#: The playable mission planets, in campaign order (the finale comes after them).
PLANET_ORDER = (
    "mars",
)


class DataError(ValueError):
    """Raised when a data file is missing, malformed or incomplete."""


def _read_json(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise DataError(f"Missing data file: {path.relative_to(settings.ROOT)}") from None
    except OSError as exc:
        raise DataError(f"Cannot read {path.name}: {exc}") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DataError(f"Invalid JSON in {path.name} (line {exc.lineno}): {exc.msg}") from None
    if not isinstance(data, dict):
        raise DataError(f"{path.name} must contain a JSON object")
    return data


# --- campaign ---------------------------------------------------------------
def load_mission() -> dict:
    config = _read_json(settings.DATA / "mission.json")
    levels = config.get("levels")
    if not isinstance(levels, list) or not levels:
        raise DataError("mission.json: 'levels' must be a non-empty list")
    for entry in levels:
        for key in ("id", "name", "scene", "blurb", "briefing", "systems"):
            if key not in entry:
                raise DataError(f"mission.json: level {entry!r} is missing '{key}'")
    config.setdefault("title", settings.TITLE)
    config.setdefault("subtitle", settings.SUBTITLE)
    return config


def level_list() -> list[dict]:
    return list(load_mission()["levels"])


def level_ids() -> list[str]:
    return [entry["id"] for entry in level_list()]


def level_meta(level_id: str) -> dict:
    for entry in level_list():
        if entry["id"] == level_id:
            return entry
    raise DataError(f"mission.json: unknown level id '{level_id}'")


def next_level(level_id: str) -> str | None:
    ids = level_ids()
    if level_id in ids:
        index = ids.index(level_id)
        if index + 1 < len(ids):
            return ids[index + 1]
    return None


def level_number(level_id: str) -> int:
    ids = level_ids()
    return ids.index(level_id) + 1 if level_id in ids else 0


# --- level configs ----------------------------------------------------------
def load_level(level_id: str) -> dict:
    path = settings.DATA / "levels" / f"{level_id}.json"
    config = _read_json(path)
    missing = [key for key in LEVEL_KEYS if key not in config]
    if missing:
        raise DataError(f"{path.name} is missing: {', '.join(missing)}")

    config.setdefault("briefing", [])
    config.setdefault("facts", [])
    config.setdefault("source", "")
    config.setdefault("time_limit", None)
    config.setdefault("scene", "world")  # default scene name
    if not isinstance(config["params"], dict):
        raise DataError(f"{path.name}: 'params' must be an object")
    if not isinstance(config["briefing"], list):
        raise DataError(f"{path.name}: 'briefing' must be a list")
    return config


def params_for(config: dict, difficulty: str) -> dict:
    """Merge the level params with the per-difficulty override block."""
    params = dict(config.get("params") or {})
    overrides = params.pop("difficulty", {}) or {}
    if difficulty not in settings.DIFFICULTIES:
        difficulty = "normal"
    params.update(overrides.get(difficulty, {}) or {})
    return params


# --- dialogue ---------------------------------------------------------------
def load_dialogue(relative: str) -> dict:
    """Load a dialogue file and index its lines by trigger.

    File shape::

        {"speaker": "Laika", "lines": [{"trigger": "start", "text": "..."}]}

    A line may override the speaker. Returns::

        {"speaker": "Laika", "lines": {"start": [{"speaker": ..., "text": ...}]}}
    """
    name = str(relative).replace("\\", "/")
    if name.startswith("dialogue/"):
        name = name[len("dialogue/"):]
    path = settings.DATA / "dialogue" / name
    config = _read_json(path)

    default_speaker = str(config.get("speaker", "Laika"))
    by_trigger: dict[str, list[dict]] = {}
    for entry in config.get("lines", []):
        if not isinstance(entry, dict):
            continue
        body = str(entry.get("text", "")).strip()
        if not body:
            continue
        trigger = str(entry.get("trigger", "start"))
        by_trigger.setdefault(trigger, []).append(
            {"speaker": str(entry.get("speaker", default_speaker)), "text": body}
        )

    return {
        "speaker": default_speaker,
        "lines": by_trigger,
        "triggers": list(by_trigger.keys()),
    }


def load_planets() -> dict:
    """Load the planet definitions from ``data/planets.json``.

    Returns a dict good for iteration: ``{"planets": [...], "order": [...]}``.
    """
    config = _read_json(settings.DATA / "planets.json")
    planets = config.get("planets")
    if not isinstance(planets, list) or not planets:
        raise DataError("planets.json: 'planets' must be a non-empty list")
    for planet in planets:
        for key in ("id", "name", "map_position"):
            if key not in planet:
                raise DataError(f"planets.json: entry {planet!r} is missing '{key}'")
    config.setdefault("order", [planet["id"] for planet in planets])
    return config


def planet_index() -> dict[str, dict]:
    """Map planet id -> planet definition (``data/planets.json``)."""
    return {planet["id"]: planet for planet in load_planets()["planets"]}


@lru_cache(maxsize=1)
def _required_parts_cached() -> tuple[str, ...]:
    try:
        planets = load_planets()["planets"]
    except DataError:
        return ()
    return tuple(planet["part"] for planet in planets if planet.get("part"))


def required_parts() -> list[str]:
    """The parts the player has to recover - one per playable planet."""
    return list(_required_parts_cached())


def level_names() -> dict[str, str]:
    return {entry["id"]: entry["name"] for entry in level_list()}


def previous_mission(planet_id: str) -> str | None:
    """Get the previous mission planet id in the world order.
    Returns None for the first planet (tutorial).
    """
    if planet_id in PLANET_ORDER:
        idx = PLANET_ORDER.index(planet_id)
        if idx > 0:
            return PLANET_ORDER[idx - 1]
    return None
