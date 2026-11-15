# MISSION LAIKA: THE RED HORIZON - Contributing Guide

## Contributing to MISSION LAIKA: THE RED HORIZON

### Getting Started

1. **Fork the repository** and clone your fork
2. **Create a branch** for your feature/fix: `git checkout -b feature/foo`
3. **Make your changes** following the existing patterns in the codebase
4. **Run the smoke test**: `python tools/smoke_test.py` — all 14 scenes + ending must pass
5. **Test manually**: `python main.py` — play through the game
6. **Commit your changes** with a clear message
7. **Push to your fork** and open a Pull Request

### Code Conventions

- **Python format**: Follow PEP 8. Use 4-space indentation, no tabs.
- **Type hints**: Use `from __future__ import annotations` and type hints where practical.
- **Docstrings**: All public functions/classes should have docstrings.
- **Naming**: `snake_case` for functions/variables, `CapWords` for classes, `UPPER_CASE` for constants.
- **Imports**: Standard library first, then local (`from core import ...`, `from art import ...`, `from ui import ...`).

### Adding a New Level

1. Create `data/levels/level<N>.json` with complete phase configuration
2. Create `scenes/level<N>.py` scene following the pattern:
   - Subclass `Scene`
   - Implement `on_enter(**data)`, `handle_events()`, `update(dt)`, `draw(surface)`
   - Implement phase handlers: `_handle_<phase>()`, `_goto_phase()`, `_schedule_next()`
   - Register in `register_mission_scenes(manager)`
3. Add level to `data/mission.json` `levels` array
4. Add planet part in `data/planets.json`
5. Update: `design.md`, `playguide.md`, `README.md`, `DOCS.md`

### Adding Dialogue

1. Edit `data/dialogue/mars.json` adding lines under appropriate trigger keys
2. Reference triggers in level phase configs' `dialogue_trigger` fields
3. Add dialogue handling in scene's phase handler methods
4. Test: run the level and verify Laika's lines play correctly

### Modifying Difficulty Levels

1. Edit `core/settings.py` `DIFFICULTY_BLURB` dict for blurb text
2. Edit `core/game_state.py` `MULTIPLIERS` dict (or the new `scale_speed()` method) for numerical values
3. Test all levels with each difficulty setting
4. Verify: easy has longer timers, hard has shorter timers and stricter comms

### Art Contributions

- All art is procedural (drawn in code, no image files required)
- If adding new visual elements, draw them using pygame primitives in `art/environments.py` or `art/sprites.py`
- Test with empty `assets/` folder to ensure fallback works
- Reference existing patterns: `outpost_room()`, `mars_surface()`, `tunnel_backdrop()`, `draw_laika_portrait()`, `draw_rover_top()`, etc.

### Science Data

- `data/science.json` holds cached NASA system metrics
- To refresh: run `python tools/fetch_science.py` (requires internet)
- If adding new system metrics: add entry to `systems` array in `data/science.json`
- Update `SCIENCE.md` documentation

### Documentation

- Update `design.md` for gameplay changes
- Update `playguide.md` for player-facing changes
- Update `README.md` for high-level changes
- Update `DOCS.md` for structure changes
- Update `technical.md` for architecture changes
- Update `DATA.md` for data format changes
- Update `TOOLS.md` for tools changes
- Run `python tools/smoke_test.py` after any structural changes

### Python Version Support

- Python 3.12 (primary), 3.11 also supported
- Use `from __future__ import annotations` for all modules
- Type hints encouraged but not strictly required
- No deprecated Python features used

### License

This project is licensed under the MIT License. See the `LICENSE` file or project root for details.

### Questions or Issues

- Open an issue in the GitHub repository
- Contact the project maintainer
- Check `CONTRIBUTING.md` for patterns before contributing