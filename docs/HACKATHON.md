# MISSION LAIKA: THE RED HORIZON - Hackathon Document

## NASA Space Apps Challenge 2026

### Project: MISSION LAIKA: THE RED HORIZON

**Team**: [Team to be filled]  
**Challenge Category**: Game/Interactive Application  
**Platform**: Windows, macOS, Linux, Web (pygbag)  
**Python Version**: 3.12+  
**Dependencies**: pygame-ce  

### Project Summary & Emotional Hook

MISSION LAIKA: THE RED HORIZON is a junior astronaut mission trainer where the player guides Laika, a robotic dog, through four survival challenges on the way to Mars. Laika — history's first animal astronaut — embodies the courage of early space explorers. Players step into the role of a junior astronaut trainer, making critical decisions that determine Laika's survival. Every mechanic is grounded in real NASA data, and the game teaches players about solar radiation, communication delays, sandstorm survival, and extreme cold operations. The emotional hook: honoring Laika's legacy while inspiring the next generation to pursue STEM and planetary exploration.

### Key Features (per NASA Space Apps Briefing)

1. **Four-level mission arc**:
   - Level 1: Outpost survival (food, exercise, rest)
   - Level 2: Landing preparation (equipment selection + comms delay)
   - Level 3: Martian surface (photos + sandstorm + cold)
   - Level 4: Lava tunnel exploration (platforming + flashlight + escape)

2. **Science integration**:
   - RADLAB + DONKI: Radiation measurements and real-space weather
   - OSDR: Human/biological effects of spaceflight
   - MARS TREK: Real Mars terrain data

3. **Procedural everything**: No image/audio files required. Game runs with empty `assets/`.

4. **Graceful fallbacks**: Missing data never crashes the game.

5. **Three difficulty levels**: Easy (longer timers, more retries), Normal (as designed), Hard (shorter timers, stricter comms).

6. **Three endings**: Win (Laika returns home), Incomplete (Laika returns but mission unfinished), Lost (Laika does not return).

### Learning Outcomes

Players will achieve the following 3-5 outcomes:

1. **Radiation safety**: Understanding planetary radiation environments (0.64 mSv/day on Mars surface), the role of DONKI real-time space weather monitoring, and how mission designers must account for cumulative exposure.

2. **Bone and muscle loss mitigation**: The importance of exercise in microgravity, referencing the in-game bike challenge and real NASA data on ~1-1.5%/month bone density loss without loading.

3. **CO2 and rest management**: Recognizing the critical role of ventilation grilles for CO2 extraction and the consequences of poor rest area selection, tying into the in-game rest challenge with ventilation grille proximity.

4. **EDL sequence (Entry, Descent, Landing)**: Understanding the communication delay (~45 seconds one-way at Mars), equipment selection (parachute, heat shield, sky crane), and why waiting without pressing send is essential for safe landing.

5. **Sandstorms and extreme cold**: Identifying Martian sandstorm hazards, the temperature drop to -125°C, and the hibernation mode procedure that protects rover batteries — all based on real MARS TREK data.

### How This Maps to NASA Data

The game integrates three core NASA data systems into every gameplay mechanic:

- **RADLAB + DONKI**: Mars surface dose ~0.64 mSv/day; solar particle events are watched via the DONKI feed at `https://ccmc.gsfc.nasa.gov/tools/DONKI/`. In-game, radiation meters and warning alerts reflect real-time space weather data.
- **OSDR**: Bone density loss (~1-1.5%/month without loading), muscle loss without exercise, and other biomedical effects are tracked via `https://osdr.nasa.gov/`. The game's exercise bike and rest challenges embody these concepts.
- **MARS TREK**: Real Mars terrain at `https://trek.nasa.gov/mars/`, including night lows of -125°C at Gale Crater, survey sites, and fastest winds >2,000 km/h (used as a scale reference, not as Mars winds). Sandstorm visuals and hibernation temperature warnings are derived from MARS TREK data.

### Impact Statement

MISSION LAIKA: THE RED HORIZON brings NASA-calibrated space science to a broad junior-audience through an accessible, 20-30 minute game. By integrating real radiation data (DONKI), biomedical findings (OSDR), and planetary imagery (MARS TREK), the game transforms abstract science into tactile decisions: managing radiation exposure, choosing exercise to counteract muscle loss, selecting safe rest zones to avoid CO2 buildup, and respecting EDL communication delays. The project addresses the NASA Space Apps Challenge goal of making NASA data explorable and engaging, particularly for younger audiences who may not encounter these systems otherwise. All science values are verified: 0.64 mSv/day (NASA PDS), 1-1.5%/month (NASA HRP), -125°C extreme polar (MARS TREK/Gale Crater), 3.71 m/s² Mars gravity.

### Future Work

- Expand the mission to include additional planets and moons from the solar system
- Add multiplayer collaborative mode where players coordinate decisions across levels
- Implement text size accessibility slider with live preview
- Develop web (pygbag) build for instant play without installation
- Create educational companion materials (lesson plans, data exploration activities)
- Add more Laika dialogue lines with branching paths based on player choices
- Integrate additional NASA data systems (e.g., Mars Climate Database, MAVEN particle data)

### Screenshot Captions (for judging materials)

| Screenshot | Description |
|------------|-------------|
| Boot screen with APOD image | Daily NASA Astronomy Picture of the Day displayed on game launch, cached offline in `data/cache/apod.json` |
| Outpost vending machine food challenge | Player selecting sealed drink + irradiated chicken; wrong choices trigger "FOOD SAFETY PROTOCOL VIOLATED" modal |
| Level 2 communication delay countdown | 45-second countdown "Communications delay: 00:45. Do NOT press the button." |
| Level 3 sandstorm approaching | Storm clouds overlay, visibility reduced, warning "Temperature dropping to -125°C! Activate Hibernation Mode." |
| Level 4 lava tunnel with flashlight | F key toggles Laika's flashlight; beam lights dark tunnel; rock sample and camera buttons visible |
| Win ending: Laika returns home | Laika inside spacecraft, reuniting with player; stats screen shows mission time, parts recovered, facts learned |
| HUD with part inventory | Top bar shows level name, challenge/timer, objective, time left, and part inventory counters |

### Controls (Quick Reference)

| Action | Key(s) |
|--------|--------|
| Advance dialogue / Interact | `E`, `Space` |
| Toggle flashlight (Level 4) | `F` |
| Laika hint | `H` |
| Pause menu | `Esc` |
| Move | Arrow keys, WASD |

### Target Specifications

- **Play time**: 20-30 minutes total experience (15-25 min core gameplay, rest from briefings/dialogue)
- **Difficulties**: Easy, Normal, Hard
- **Scenes**: 14 (boot, menu, map, tutorial, level1-4, briefing, ending) + smoke test
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