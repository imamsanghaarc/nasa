# MISSION LAIKA: THE RED HORIZON - Technical Document

## Architecture Essentials

- **One `GameState` owns progress** (parts, facts, deaths, difficulty, save/load). Scenes use its public API only; no module-level mutables.
- **Scene contract**: `handle_events`, `update(dt)`, `draw(screen)`, optional `on_enter`/`on_exit`. Manager: `switch`, `push`, `pop`, `reload`.
- **Gameplay numbers live in JSON under `data/`** — no hardcoded gameplay numbers in scenes.

## Scene Management

- **SceneManager** handles stack-based transitions: `switch`, `push`, `pop`, `reload`.
- Every screen is a `Scene` with the same four hooks. The manager never inspects what a scene does, which is why a new level only needs a register call in `main.py`.
- `Game` container handed to every scene: virtual screen, window, state, manager.

## Core Systems

### GameState (core/game_state.py)
- Dataclass with: `parts`, `facts`, `deaths`, `difficulty`, `player_name`, `current_level`, `elapsed`, `tutorial_done`, `volume`, `muted`, `text_scale`, `levels_done`, `best_times`
- Methods: `add_part()`, `has_part()`, `required_parts()`, `all_parts()`, `mark_level_done()`, `is_level_done()`, `best_time()`, `is_unlocked()`, `next_level_id()`, `complete_level()`, `finish_mission()`, `reset_mission()`, `save()`, `load()`, `to_dict()`, `from_dict()`
- Derived text: `status_line()`, `progress_line()`, `mission_line()`, `science_line()`
- Difficulty: Easy (+25% time, 5 hearts, frequent hints), Normal (standard), Hard (-15% time, 2 hearts, hints on request only)

### Scene Base Class (core/scene.py)
- `Scene` class with `name`, `counts_time` flag
- `SceneManager` with `registry` dict, `stack` list
- `handle_events`, `update(dt)`, `draw(screen)` hooks
- `Game` class: `screen`, `window`, `state`, `manager`, `running`

### Game Loop (main.py)
- Async-friendly `main()` function
- DPI awareness for Windows (ctypes)
- `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` for headless/smoke test
- Clock tick at `settings.FPS` (60), `dt = min(clock.tick() / 1000.0, 0.05)`
- Never `time.sleep()` in the main loop
- Virtual surface blitting to window with scale handling

## Data Format

### Planets (data/planets.json)
- Order: mercury, venus, mars, jupiter, saturn, uranus, neptune
- Each planet: `id`, `name`, `part`, `part_color`, `playable`, `map_position`, `orbit_px`, `radius`, `color`, `band_color`, `bands`, `craters`, `ring`, `tagline`, `fact`, `facts`, `unlock`, `source`
- Seven parts: Solar Panel Array, Hull Plating, Navigation Module, Shield Generator, Fuel Cells, Thermal Regulator, Signal Antenna

### Levels (data/levels/*.json)
- Keys: `id`, `name`, `style`, `params`, `dialogue`, `objective`, `briefing`, `phases`, `systems`, `part`, `part_color`, `facts`
- `phases`: list of phase dicts with `id`, `objective`, `dialogue_trigger`, `vending` (config), `time_limit`, `on_correct`, `on_wrong`
- `dialogue`: indexed by trigger, speaker `Laika`, lines dict

### Mission (data/mission.json)
- `title`, `subtitle`, `levels` array
- Each level: `id`, `name`, `blurb`, `briefing`, `systems`
- `level_ids()`: returns ordered list
- `level_meta(id)`: returns level dict
- `next_level(id)`: returns next level id
- `level_number(id)`: returns 1-based number

### Dialogue (data/dialogue/*.json)
- `{"speaker": "Laika", "lines": {"trigger": [{"speaker": "Laika", "text": "..."}]}`
- Lines indexed by trigger: start, intro, food_briefing, food_correct, food_wrong, exercise_intro, vending_code, bike_ready, bike_strap, bike_free, bike, rest_intro, rest_control, rest_exercise, rest_done, complete, etc.

## Adding a Level

1. Create `data/levels/level<N>.json` with all required keys
2. Create `scenes/level<N>.py` scene following the pattern:
   - Subclass `Scene`
   - `on_enter(**data)`: load cfg, params, dialogue, HUD, dialogue box, set phase
   - `handle_events(events)`: route to phase handlers
   - `update(dt)`: phase-specific logic, HUD update, modal/dialogue update
   - `draw(surface)`: backdrop, astronaut, HUD, dialogue, modal
   - Phase handlers: `_handle_<phase>()` methods
   - `_goto_phase(phase)`: transition method
   - `_schedule_next(phase, delay)`: delayed phase transition
   - Register in `register_mission_scenes(manager)`
3. Register scene in `main.py`: `register_mission_scenes(game.manager)`
4. Add level data to `data/mission.json` under `levels` array
5. Add planet part in `data/planets.json`
6. Update documentation

## Save System

- **One small JSON file** (`savegame.json`) next to the game
- Everything wrapped in try/except: corrupt/missing save never stops player from starting new mission
- `VERSION 2` format with `mission_started`, `levels_done`, `facts`, `inventory`, `photos`, `samples`, `deaths`, `difficulty`, `player_name`, `elapsed`, `outcome`, `volume`, `muted`, `text_scale`, `show_hints`, `best_times`
- Preferences (text_scale, volume, muted) survive reset; campaign progress does not
- Cross-version: if version changes, preferences survive; old campaign progress does not

## Audio System (core/audio.py)
- All sounds synthesized in code — no audio files required
- 30+ sound recipes: click, hover, dialogue, pickup, part, jump, hit, win, lose, back, laser, boom, camera, alarm, deny, beep, confirm, vacuum, power_down, wind, step, spark, radio, rumble
- `init()`: initialize mixer once, safe to call repeatedly
- `play(name, gain)`: play named sound at optional gain
- `set_volume(value)`, `set_muted(value)`, `is_muted()`

## Input Handling

- **Keyboard**: `pygame.KEYDOWN` for advance, `pygame.K_SPACE`, `pygame.K_RETURN`, `pygame.K_e`, `pygame.K_h` (hint)
- **Mouse**: `pygame.MOUSEBUTTONDOWN` for vending machine interaction, button clicks
- **Mouse scaling**: `game.scale_mouse(event.pos)` translates window coords to 1280x720 virtual canvas
- Events scaled in main.py before passing to manager

## Headless/Smoke Test

- `tools/smoke_test.py`: boots every scene and runs frames without a display
- Sets `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`
- Runs each scene for 30 frames, checks for errors
- Tests all 14 scenes + ending
- Must pass with no crashes

## Performance Guidelines
- Delta time everywhere; no `time.sleep` in main loop
- Never block the async-friendly `main()`
- All art/audio procedural — no file I/O during gameplay
- Graceful fallbacks for missing data/assets/audio/save
- Keep JSON data files lightweight and well-structured

## Testing
- Headless smoke test: `python tools/smoke_test.py`
- All 14 scenes + ending must pass
- Manual playtest recommended for each level
- Difficulty toggling should work across all levels
- Save/load roundtrip should preserve progress

## Dependencies
- `pygame-ce` (never plain `pygame`)
- Python 3.12 (3.11 also works)
- No external API keys or network required (all data cached offline)
- `numpy` not required — all math via `math` module