# MISSION LAIKA: THE RED HORIZON - Hackathon Document

## NASA Space Apps Challenge 2026

### Project: MISSION LAIKA: THE RED HORIZON

**Team**: [Team to be filled]  
**Challenge Category**: Game/Interactive Application  
**Platform**: Windows, macOS, Linux, Web (pygbag)  
**Python Version**: 3.12+  
**Dependencies**: pygame-ce  

### Project Summary

MISSION LAIKA: THE RED HORIZON is a junior astronaut mission trainer where the player guides Laika, a robotic dog, through four survival challenges on the way to Mars. Every mechanic is grounded in real NASA data, and the game teaches players about solar radiation, communication delays, sandstorm survival, and extreme cold operations.

### Key Features (per NASA Space Apps Briefing)

1. **Four-level mission arc**:
   - Level 1: Outpost survival (food, exercise, rest)
   - Level 2: Landing preparation (equipment selection + comms delay)
   - Level 3: Martian surface (photos + sandstorm + cold)
   - Level 4: Lava tunnel exploration (platforming + flashlight + escape)

2. **Science integration**:
   - RADLAB + DONKI: Radiation measurements
   - OSDR: Human/biological effects of spaceflight
   - MARS TREK: Real Mars terrain data

3. **Procedural everything**: No image/audio files required. Game runs with empty `assets/`.

4. **Graceful fallbacks**: Missing data never crashes the game.

5. **Three difficulty levels**: Easy (longer timers, more retries), Normal (as designed), Hard (shorter timers, stricter comms).

6. **Three endings**: Win (Laika returns home), Incomplete (Laika returns but mission unfinished), Lost (Laika doesn't return).

### Development Roadmap

- **Week 1**: Core framework, settings, save system, game state, science layer
- **Week 2**: Art pipeline (procedural environments, sprites), movement controllers
- **Week 3**: Level 1 (Outpost) — food, exercise, rest challenges
- **Week 4**: Level 2 (Landing) — equipment vending + communication delay
- **Week 5**: Level 3 (Surface) — photography + sandstorm + cold
- **Week 6**: Level 4 (Lava Tunnel) — platforming + flashlight + escape
- **Week 7**: Ending screen, documentation, polish
- **Week 8**: Headless smoke test, final build, judge presentation

### judging Criteria (NASA Space Apps)

1. **Innovation**: Procedural mission generator with science integration
2. **Technical**: Robust headless playtest, no crashes, graceful fallbacks
3. **Science accuracy**: Real NASA data integrated into gameplay mechanics
4. **User experience**: Intuitive controls, clear objectives, progressive difficulty
5. **Accessibility**: Difficulty levels, text size adjustment, hint system
6. **Completeness**: Full 4-level arc with win/incomplete/lose outcomes

### Controls (Quick Reference)

| Action | Key(s) |
|--------|--------|
| Advance dialogue / Interact | `E`, `Space` |
| Toggle flashlight (Level 4) | `F` |
| Laika hint | `H` |
| Pause menu | `Esc` |
| Move | Arrow keys, WASD |

### Target Specifications

- **Play time**: 25-30 minutes full arc
- **Difficulties**: Easy, Normal, Hard
- **Scenes**: 14 (boot, menu, map, tutorial, 4 levels × 4: boot/menu/briefing/level, ending) + smoke test
- **Platforms**: Windows (primary), macOS, Linux, Web (pygbag)
- **Assets**: None required (procedural generation)
- **Save file**: `savegame.json` next to executable

### Submission Checklist

- [ ] Full 4-level mission playable from start to end
- [ ] All three endings (win/incomplete/lost) trigger correctly
- [ ] Headless smoke test passes (`python tools/smoke_test.py`)
- [ ] Difficulty toggling works across all levels
- [ ] Save/load roundtrip preserves progress
- [ ] Documentation complete (README, playguide, technical, science, data)
- [ ] No plain `pygame` dependency (must use `pygame-ce`)
- [ ] Game runs with empty `assets/` folder
- [ ] All dialogue triggers functional
- [ ] Vending machine modes (cart/code/load) working
- [ ] Communication delay mechanic functional (Level 2)
- [ ] Sandstorm and Hibernation Mode functional (Level 3)
- [ ] Flashlight and platforming functional (Level 4)
- [ ] All Laika dialogue lines playing correctly