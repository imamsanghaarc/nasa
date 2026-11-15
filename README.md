# MISSION LAIKA: THE RED HORIZON
## A Junior Astronaut Mission Trainer for NASA Space Apps Challenge 2026

[![NASA Space Apps](https://img.shields.io/badge/NASA%20Space%20Apps%20Challenge-2026-blue)](https://spaceapps.challenge.gov/)
[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![pygame-ce](https://img.shields.io/badge/pygame--ce-2.5.7-brightgreen)](https://pygbag.github.io/pygame-ce/)

---

## 🚀 Overview

**MISSION LAIKA: THE RED HORIZON** is a junior astronaut mission trainer built for the **NASA Space Apps Challenge 2026**. Players guide Laika, a robotic dog, through four survival challenges on the way to Mars. Every mechanic is grounded in real NASA data, teaching players about solar radiation, communication delays, sandstorm survival, and extreme cold operations.

**Game Title:** MISSION LAIKA: THE RED HORIZON  
**Platform:** Windows, macOS, Linux, Web (pygbag)  
**Python:** 3.12+ (3.11 also works)  
**Dependencies:** `pygame-ce` (never plain `pygame`)  
**Play Time:** 25-30 minutes full arc  
**Difficulties:** Easy (5 hearts, +25% time, frequent hints) · Normal (standard) · Hard (2 hearts, -15% time, hints on request only)  
**Endings:** Win · Incomplete · Lost

---

## 📦 Installation

**Prerequisites:** Python 3.12 (3.11 also works).

```bash
# Clone the repository
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa

# Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Never install plain `pygame`; use `pygame-ce`.**

**No assets needed** — the game is 100% procedural, so it runs fine with an empty `assets/` folder.

**Troubleshooting:** if pygame fails to import, run `pip install pygame-ce` (never plain `pygame`).

**Devs only:** `pip install -r requirements-dev.txt` for code formatting (`black`).

Start the game:

```bash
python main.py
```

---

## 🎮 How to Play

### Main Menu

- **New mission** — Resets all progress and starts Level 1 (Outpost)
- **Continue** — Loads last saved game (if exists)
- **Settings** — Change difficulty, volume, sound, text size
- **Quit** — Exit the game

### Difficulty Levels

| Level | Hearts | Timers | Hints |
|-------|--------|--------|-------|
| **Easy** | 5 | +25% time | Frequent hints |
| **Normal** | 3 | Standard | Standard hints |
| **Hard** | 2 | -15% time | Hints on request only |

### Four-Level Mission Arc

| Level | Theme | Key Mechanics |
|-------|-------|--------------|
| **1: Living on the Outpost** | Survival challenges | Food safety, exercise QTE, rest location, CO₂ management |
| **2: Preparing for the Mission** | Equipment + comms | Vending machine (3/6 items), 45s communication delay test |
| **3: Martian Surface** | Photography + survival | 6 camera buttons, sandstorm + hibernation mode (-125°C) |
| **4: Lava Tunnel** | Platforming + escape | Flashlight, rock sample + camera buttons, escape sequence |

### Three Endings

- **Win** — Laika survives and returns home with mission completed
- **Incomplete** — Laika returns but mission unfinished: *"I won't give up, try again before going back to Earth"*
- **Lost** — Laika doesn't return: whole mission was a failure

---

## 📚 Documentation

All documentation is kept in sync via `DOCS.md`. See the full documentation map:

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview (this file) |
| [DOCS.md](DOCS.md) | Documentation index and keeping docs in sync |
| [design.md](design.md) | Game design document — premise, story, pillars, level design, mechanics, art/audio, win-lose structure |
| [technical.md](technical.md) | Technical reference — architecture, scene design, data flow, module guide, engineering rules, save system |
| [playguide.md](playguide.md) | Player-facing guide — install, run, controls, level objectives, Laika/hints, difficulty, troubleshooting |
| [SCIENCE.md](SCIENCE.md) | NASA science appendix — planetary facts, sources, APOD, verification |
| [DATA.md](DATA.md) | Data & content format reference — planets, levels, dialogue, APOD JSON schemas |
| [TOOLS.md](TOOLS.md) | Developer/QA tools — smoke test, APOD cache, science refresh, screen shots |
| [HACKATHON.md](HACKATHON.md) | Hackathon-specific — project summary, judging criteria, controls, checklists |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributing guide — code conventions, adding levels/dialogue/difficulty, art, science, documentation |

Generate the journey document:

```bash
# The project journey document is at: LAIKA_MARS_MISSION_Project_Journey.docx
```

---

## 🔬 Science Systems (from Briefing)

Three NASA systems integrated per the briefing, all cached offline:

| System | Role | URL |
|--------|------|-----|
| **RADLAB + DONKI** | Radiation and real measurements | <https://ccmc.gsfc.nasa.gov/tools/DONKI/> |
| **OSDR** | Health and biology | <https://osdr.nasa.gov/> |
| **MARS TREK** | Real Mars terrain | <https://trek.nasa.gov/mars/> |

**Cached metrics in-game:** Mars surface dose ~0.64 mSv/day, bone density loss ~1-1.5%/month, night low -125°C, Gale Crater survey site, fastest winds >2,000 km/h (Neptune scale).

---

## 🏗️ Adding a Level

To add a new level to the campaign:

1. Create `data/levels/level<N>.json` with complete phase configuration
2. Create `scenes/level<N>.py` scene following the established patterns
3. Register the scene in `main.py` via `register_mission_scenes(manager)`
4. Add level data to `data/mission.json` under the `levels` array
5. Add planet part in `data/planets.json`
6. Update: `design.md`, `playguide.md`, `README.md`, `DOCS.md`

---

## 🎮 Controls

| Action | Key(s) |
|--------|--------|
| Advance dialogue / Interact | `E`, `Space` |
| Toggle flashlight (Level 4) | `F` |
| Laika hint | `H` |
| Pause menu | `Esc` |
| Move | Arrow keys, WASD |

---

## 🏆 Judging Criteria (NASA Space Apps)

1. **Innovation** — Procedural mission generator with science integration
2. **Technical** — Robust headless playtest, no crashes, graceful fallbacks
3. **Science accuracy** — Real NASA data integrated into gameplay mechanics
4. **User experience** — Intuitive controls, clear objectives, progressive difficulty
5. **Accessibility** — Difficulty levels, text size adjustment, hint system
6. **Completeness** — Full 4-level arc with win/incomplete/lose outcomes

---

## 📂 Repository Structure

```
E:\nasa\
├── assets/           (fonts, optional images — 100% procedural)
├── data/             (all JSON game data)
│   ├── cache/        (APOD + science cache)
│   ├── planets.json
│   ├── levels/       (level1-4.json)
│   ├── mission.json
│   ├── dialogue/     (mars.json, etc.)
│   └── science.json
├── core/             (game state, settings, levels module)
├── scenes/           (boot, menu, briefing, level1-4, ending)
├── ui/               (dialogue box, HUD, modal, vending)
├── art/              (environments, sprites — 100% procedural)
├── tools/            (smoke_test, fetch_apod, fetch_science)
├── main.py           (entry point, scene registration)
├── docs/             (README.md, DOCS.md, design.md, technical.md, playguide.md, SCIENCE.md, DATA.md, TOOLS.md, HACKATHON.md, CONTRIBUTING.md)
└── savegame.json     (player progress, auto-generated)
```

---

## 🐛 Smoke Test

Run the headless smoke test to verify all scenes:

```bash
python tools/smoke_test.py
```

**Output:** `all scenes ok` (14 scenes + ending)

---

Made with ❤️ for NASA Space Apps Challenge 2026 · [GitHub](https://github.com/imamsanghaarc/nasa)