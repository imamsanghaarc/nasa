# MISSION LAIKA: THE RED HORIZON - Data Document

## Data Format Reference

All gameplay numbers live in JSON files under `data/`. Scenes read through this module so a bad edit produces a readable error instead of a traceback in the middle of a frame.

### Planets (data/planets.json)

```json
{
  "order": ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"],
  "sun": {"name": "Sun", "color": "#ffb54a"},
  "planets": [
    {
      "id": "mercury",
      "name": "Mercury",
      "part": "Solar Panel Array",
      "part_color": "#f7c948",
      "playable": "mercury",
      "map_position": [0.451, 0.552],
      "orbit_px": 67,
      "radius": 8,
      "color": "#9c9188",
      "band_color": "#6f675f",
      "bands": 1,
      "craters": 7,
      "ring": false,
      "tagline": "Chase the terminator. Stay out of the sun.",
      "fact": "Daytime surface temperatures reach about 430 °C; at night they fall to around -180 °C.",
      "facts": ["mercury_temps", "mercury_atmosphere"],
      "unlock": ["tutorial_done"],
      "source": "NASA Planetary Fact Sheet"
    },
    ...
  ]
}
```

**Required fields per planet**: `id`, `name`, `map_position`
**Part field**: Maps to one of the seven required parts. `null` for Earth (finale).
**Playable field**: `"mercury"`, `"venus"`, ..., `"ending"`. `"ending"` is the finale.

### Levels (data/levels/*.json)

Each level JSON has these keys:

| Key | Type | Description |
|-----|------|-----------|
| `id` | string | Unique identifier (e.g., "outpost", "landing", "surface", "tunnel") |
| `name` | string | Display name (e.g., "Level 1: Living on the Outpost") |
| `style` | string | Visual theme key (e.g., "outpost", "landing", "surface", "tunnel") |
| `params` | object | Movement parameters: `player_start`, `ground_y`, `gravity_px`, `move_speed`, `accel`, `friction`, `jump_speed`, `max_health`, `hold_boost` |
| `dialogue` | string | Dialogue file name (e.g., "dialogue/mars.json") |
| `objective` | string | Primary objective text |
| `briefing` | array | Pre-game briefing text lines |
| `phases` | array | Phase configs (see below) |
| `systems` | array | Science system IDs (e.g., `["RADLAB+DONKI", "OSDR", "MARS TREK"]`) |
| `part` | string | Part name for this level (maps to `data/planets.json` `part` field) |
| `part_color` | string | Hex color for HUD display |

### Phase Config (within `phases` array)

| Key | Type | Description |
|-----|------|-----------|
| `id` | string | Unique phase identifier (e.g., "intro", "food_briefing", "take_photos") |
| `objective` | string | Objective text for HUD |
| `dialogue_trigger` | string | Laika dialogue trigger to play at phase start |
| `time_limit` | float/int | Seconds before auto-advance, or null for player-paced |
| `vending` | object | Vending machine config (mode, items, max_select, footer, code_mode, labels) |
| `on_correct` | string | Dialogue trigger on correct selection |
| `on_wrong` | string | Dialogue trigger on wrong selection |
| `camera_buttons` | int | Number of camera photos needed (Level 3) |
| `flashlight_on` | bool | Whether flashlight starts on (Level 4) |
| `total_time` | int | Total time limit in seconds (Level 4) |

### World Params (data/levels/<planet>.json)

The seven mission planets run the shared world engine. Their `params` block holds:

| Key | Type | Description |
|-----|------|-----------|
| `seed` | int | World generator seed (terrain, hazards, enemies) |
| `world_length` | int | World width in pixels |
| `ground_y` | int | Height of the ground surface |
| `gravity_px`, `jump_speed`, `move_speed`, `friction` | float | Movement feel |
| `walker_speed`, `walker_charge`, `ufo_speed`, `ufo_fire_interval`, `plasma_speed` | float | Enemy behaviour |
| `gap_chance`, `gap_min`, `gap_max`, `platform_chance` | float | Terrain generation |
| `enemy_density`, `ufo_chance`, `hazard_density`, `hazard_types` | - | Spawn mix |
| `theme` | object | Colours, backdrop and fog style |
| `weather` | object | Weather type, density, colour |
| `storm_interval`, `storm_duration`, `visibility_radius` | float | Mars dust storm |
| `moment` | object | The world's signature moment (below) |
| `difficulty` | object | Per-difficulty overrides (`easy` / `normal` / `hard`) |

**Signature moment** - one scripted set piece per world. It fires when the player
reaches `at` (a fraction of the world width), raises an alert, shows the `title`,
and sends `wave` enemies every `burst_every` seconds until `duration` runs out.

```json
"moment": {
  "at": 0.55,
  "duration": 6.0,
  "wave": 2,
  "burst_every": 3.0,
  "title": "HEAT VENT SURGE"
}
```

### Dialogue (data/dialogue/*.json)

```json
{
  "speaker": "Laika",
  "lines": {
    "start": [
      {"speaker": "Laika", "text": "You are on Mars. Gravity here is 3.71 metres per second squared - about 38 percent of Earth. Hold jump longer to go higher."},
      {"speaker": "Laika", "text": "Dust devils and alien patrols ahead. The low gravity makes leaps float - use it."}
    ],
    "food_briefing": [
      {"speaker": "Laika", "text": "Before you eat, read the safety card. No open liquids: in microgravity, a spilled drink floats and can reach the panels, vents, and the outpost's most sensitive circuits. Choose sealed drinks you can drink through a straw or valve. No crumbly food: crumbs float into the ventilation grilles and circuit boards. Choose food that is sealed, moist, and eaten in one bite — like irradiated chicken in a pouch."}
    ],
    "food_correct": [
      {"speaker": "Laika", "text": "Excellent choice, Astronaut. Sealed drink and irradiated chicken are safe for our mission."}
    ],
    "food_wrong": [
      {"speaker": "Laika", "text": "Warning! This food is not proper for our mission. Open liquids and crumbly food damage the outpost's sensitive circuits and ventilation grilles. Let us try again."}
    ],
    ...
  }
}
```

**Line structure**: `{"speaker": "Laika", "text": "..."}`. Speaker can be overridden per line.

**Triggers**: `start`, `hint`, `part`, `win`, `death_3`, `storm` and `moment`
(`moment` is the line Laika says when a world's signature moment fires).

### Mission (data/mission.json)

```json
{
  "title": "MISSION LAIKA: THE RED HORIZON",
  "subtitle": "A Junior Astronaut Mission Trainer",
  "levels": [
    {
      "id": "outpost",
      "name": "Level 1: Living on the Outpost",
      "blurb": "Survival challenges test your decisions. Laika guides you.",
      "briefing": [
        "No open liquids: in microgravity, a spilled drink floats and can reach the panels, vents, and the outpost's most sensitive circuits.",
        "No crumbly food: crumbs float into the ventilation grilles and circuit boards."
      ],
      "systems": ["RADLAB+DONKI", "OSDR", "MARS TREK"]
    },
    ...
  ]
}
```

**Required top-level keys**: `title`, `subtitle`, `levels`
**Each level must have**: `id`, `name`, `blurb`, `briefing`, `systems`
**`level_ids()`**: Returns ordered list from mission.json levels array
**`level_meta(id)`**: Returns level dict for given id
**`next_level(id)`**: Returns next level id or None (used for campaign progression)
**`level_number(id)`**: Returns 1-based number

## Science (data/science.json)

```json
{
  "updated": "bundled",
  "systems": [
    {
      "id": "radlab",
      "name": "RADLAB + DONKI",
      "role": "Radiation and real measurements",
      "url": "https://ccmc.gsfc.nasa.gov/tools/DONKI/",
      "status": "cache",
      "metrics": [
        {"label": "Mars surface dose", "value": "~0.64 mSv/day"},
        {"label": "Solar particle event", "value": "watch the feed"}
      ]
    },
    {
      "id": "osdr",
      "name": "OSDR",
      "role": "Health and biology",
      "url": "https://osdr.nasa.gov/",
      "status": "cache",
      "metrics": [
        {"label": "Bone density", "value": "~1-1.5% / month"},
        {"label": "Muscle loss", "value": "without loading"}
      ]
    },
    {
      "id": "marstrek",
      "name": "MARS TREK",
      "role": "Real Mars terrain",
      "url": "https://trek.nasa.gov/mars/",
      "status": "cache",
      "metrics": [
        {"label": "Survey site", "value": "Gale Crater"},
        {"label": "Night low", "value": "-125 C"}
      ]
    }
  ],
  "facts": []
}
```

**`updated`**: "bundled" or ISO timestamp if refreshed online
**`systems`**: Three system objects as above
**`facts`**: Free-form science facts

## Tools (tools/)

### fetch_apod.py
- Caches today's NASA Astronomy Picture of the Day
- Runs once, stores JSON + image in `data/cache/`
- Game reads from cache, never needs internet

### fetch_science.py
- Refreshes `data/science.json` from live DONKI/OSDR/MARS TREK feeds
- Runs when machine has internet access
- Updates `updated` field and system metrics

### smoke_test.py
- Bootstraps every scene and runs 30 frames headless
- Sets `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`
- Tests all scenes + ending for errors
- Run: `python tools/smoke_test.py`

### shot_map.py, shot_world.py
- Generate reference images for documentation
- Used by TOOLS.md

## Adding Content

### New Planet
1. Add entry to `data/planets.json` with all required fields
2. Add part to `data/mission.json` levels array if playable
3. Register planet scene in `main.py` via `register_mission_scenes()`
4. Update `design.md`, `playguide.md`, `README.md`

### New Level
1. Create `data/levels/level<N>.json` with complete phase config
2. Create `scenes/level<N>.py` scene following established patterns
3. Register scene in `main.py`
4. Add level to `data/mission.json` `levels` array
5. Add planet part in `data/planets.json`
6. Update documentation

### New Dialogue Trigger
1. Add lines to `data/dialogue/<planet>.json` under appropriate trigger key
2. Reference in level phase configs' `dialogue_trigger` fields
3. Add dialogue handling in scene's `_handle_<phase>()` methods

## File Hierarchy

```
E:\nasa\
├── assets/           (fonts, optional images)
├── data/             (all JSON game data)
│   ├── cache/        (APOD + science cache)
│   ├── apod.json
│   ├── planets.json
│   ├── levels/       (level<N>.json)
│   ├── mission.json
│   ├── dialogue/     (mars.json, etc.)
│   ├── science.json
│   └── ...
├── core/             (game state, settings, levels module)
├── scenes/           (boot, menu, briefing, level1-4)
├── ui/               (dialogue box, HUD, modal, vending)
├── art/              (environments, sprites)
├── tools/            (smoke_test, fetch_apod, fetch_science)
├── main.py           (entry point, scene registration)
├── docs/             (README.md, DOCS.md, design.md, technical.md, playguide.md, SCIENCE.md, DATA.md, TOOLS.md, HACKATHON.md, CONTRIBUTING.md)
└── savegame.json     (player progress, auto-generated)
```