# MISSION LAIKA: THE RED HORIZON - Tools Document

## Available Tools

### tools/smoke_test.py

**Purpose**: Headless smoke test — boots every scene and runs frames without a display.

**Run**: `python tools/smoke_test.py`

**What it does**:
- Sets `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` for headless operation
- Initializes pygame and audio
- Registers all scenes (boot, menu, map, tutorial, all planets, ending, pause, and the new LAIKA mission scenes)
- Runs each scene for 30 frames, checking for errors
- Tests the ending scene with all parts unlocked
- Prints `ok <name>` or `FAIL <name>: <error>` for each scene
- Final output: `all scenes ok` or lists failed scenes

**Output example**:
```
pygame-ce 2.5.7 (SDL 2.32.10, Python 3.14.2)
ok    tutorial
ok    mercury
...
ok    ending
all scenes ok
```

**Failures indicate**: Import errors, missing data, scene initialization bugs. All 14 scenes + ending must pass.

### tools/fetch_apod.py

**Purpose**: Cache NASA Astronomy Picture of the Day.

**Run**: `python tools/fetch_apod.py`

**What it does**:
- Sets `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`
- Initializes pygame and audio
- Fetches today's APOD from NASA API
- Saves JSON to `data/cache/apod.json` and image to `data/cache/apod.jpg`
- Prints success/failure message
- Game reads from cache, so it only needs to run once (or when APOD data changes)

**Output example**:
```
APOD cached successfully: "Title: Earth rise over the Moon"
```

### tools/fetch_science.py

**Purpose**: Refresh science data from live NASA feeds.

**Run**: `python tools/fetch_science.py`

**What it does**:
- Sets `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`
- Initializes pygame and audio
- Fetches latest DONKI space weather events, OSDR health metrics, and MARS TREK data
- Updates `data/science.json` with new values
- Updates `data/science.json`'s `updated` field to ISO timestamp
- Prints number of events fetched and summary
- Game then uses cached values and never touches the network

**Output example**:
```
Fetched 3 DONKI events, 2 OSDR metrics, 1 MARS TREK fact
Science data refreshed.
```

### tools/shot_map.py / tools/shot_world.py

**Purpose**: Generate reference images for documentation.

**Run**: `python tools/shot_map.py` or `python tools/shot_world.py`

**What they do**:
- `shot_map.py`: Takes a screenshot of the solar system map scene
- `shot_world.py`: Takes a screenshot of a specific world level
- Both save PNG files in `tools/shots/` directory
- Used by TOOLS.md and the documentation system

## Development Workflow

1. **Make changes** to code, data, or art
2. **Run smoke test**: `python tools/smoke_test.py` — must pass all 14+1 scenes
3. **Test manually**: `python main.py` — play through the game
4. **Refresh data (if needed)**: 
   - `python tools/fetch_apod.py` — if APOD cache is stale
   - `python tools/fetch_science.py` — if science data should be updated
5. **Generate reference shots** (optional): `python tools/shot_map.py`, `python tools/shot_world.py`
6. **Update documentation** as needed (see DOCS.md keeping-in-sync section)

## Directory Structure (tools/)

```
tools/
├── smoke_test.py       (headless scene bootstrap)
├── fetch_apod.py       (APOD cache)
├── fetch_science.py    (science data refresh)
├── shot_map.py         (map screenshot)
├── shot_world.py       (world level screenshot)
└── shots/              (generated reference images, gitignored)
```

## Troubleshooting

**Smoke test fails with import errors**:
- Ensure all new files are saved before running
- Check that `register_mission_scenes()` is called in `main.py`
- Verify all JSON data files are valid and have required keys

**Audio init fails**:
- Ensure `pygame-ce` is installed, not plain `pygame`
- Check sound devices aren't exhausted (headless mode uses dummy driver)

**APOD fetch fails**:
- Check internet connectivity (game can run offline with cached data)
- Verify `data/cache/` directory is writable

**Science data not updating**:
- Ensure machine has internet access
- Check that `data/science.json` isn't read-only