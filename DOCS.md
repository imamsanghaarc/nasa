# MISSION LAIKA: THE RED HORIZON - Documentation Index

This directory contains the complete documentation suite for MISSION LAIKA: THE RED HORIZON, a junior astronaut mission built for the NASA Space Apps Challenge 2026.

## Documents

| Document | Type | Purpose |
|---|---|---|
| [README.md](README.md) | Main | Project overview for judges and players - pitch, features, tech stack, structure, levels, controls, run steps. |
| [design.md](design.md) | Design | Game design document - premise, story, design pillars, level design, mechanics, art/audio, win-lose structure. |
| [technical.md](technical.md) | Technical | Technical reference - architecture, scene/game-state design, data flow, module guide, engineering rules, save system, adding a level. |
| [playguide.md](playguide.md) | Player | Player-facing guide - install, run, controls, level objectives, Laika/hints, difficulty, troubleshooting. |
| [TOOLS.md](TOOLS.md) | Tools | Developer/QA tools - NASA APOD cache, headless smoke test, scripted playtest, map panel shots. |
| [SCIENCE.md](SCIENCE.md) | Science | NASA science appendix - planetary facts, sources, APOD imagery, verification. |
| [DATA.md](DATA.md) | Data | Data & content format reference - planets, levels, dialogue, APOD JSON schemas, adding content. |
| [issue.md](issue.md) | Issue tracker | Open defects with root cause, itemised fix list and estimates - starts with the 4-level campaign "stuck in intro" blocker. |

## Suggested reading order

1. [README.md](README.md) - start here for the full picture.
2. [design.md](design.md) - understand the design intent.
3. [technical.md](technical.md) - understand the engineering.
4. [playguide.md](playguide.md) - play the game.
5. [SCIENCE.md](SCIENCE.md) and [DATA.md](DATA.md) - deep dives on the content and facts.
6. [TOOLS.md](TOOLS.md) - developer/QA tools.
7. [HACKATHON.md](HACKATHON.md) - hackathon-specific information.
8. [CONTRIBUTING.md](CONTRIBUTING.md) - contributing guidelines.

## Keeping docs in sync

When gameplay or architecture changes, update the relevant document:

- Gameplay / levels / story → `design.md`, `playguide.md`, `README.md`
- Code / architecture / modules → `technical.md`
- Tests / QA utilities → `TOOLS.md`
- NASA facts / science → `SCIENCE.md`
- Content / JSON schemas → `DATA.md`
- Everything user-facing → `README.md`
"