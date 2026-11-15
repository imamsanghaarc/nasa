# MISSION LAIKA: THE RED HORIZON - Design Document

## Premise
Today you are going to help with a really important mission, gathering information about Mars. Your base will be the martian output where you and Laika, a robotic dog, will gather information about invisible solar radiation, solar storms, environmental hazards, and possible signs of life, and take important decisions to secure your safety and from the mission.

## Design Pillars
1. **Decision-based gameplay**: Every level presents choices with consequences. Wrong food choice restarts the game; wrong comms action wastes time; wrong resting spot causes CO₂ risk.
2. **Science integration**: Every mechanic is grounded in real NASA data. The three systems from the briefing (RADLAB+DONKI, OSDR, MARS TREK) provide the science layer.
3. **Procedural everything**: Art, audio, and worlds are all generated in code. No image files required. Game runs with empty `assets/`.
4. **Graceful fallbacks**: Missing data/assets/audio/save never crashes the game.
5. **Short play sessions**: 20-30 minutes total experience. Core gameplay is ~15-25 minutes depending on difficulty, with briefings and dialogue extending the full experience. Judges can see the full arc in one sitting.

## Level Design

### Level 1: Living on the Outpost
- **Survival challenges test your decisions**. Laika guides you through three tasks.
- **Food challenge**: Two-step process. First, safety briefing explains why no open liquids (microgravity spills) and no crumbly food (crumbs damage circuits/vents). Then vending machine: select sealed drink + irradiated chicken. Wrong choice triggers "FOOD SAFETY PROTOCOL VIOLATED" modal; player retries the food task (not full mission restart).
- **Exercise challenge**: Vending machine in code mode. Must enter code 4 for safety harness. Then stationary bicycle: 22-second QTE with alternating left/right key presses. Running freely launches player to ceiling (lose).
- **Rest challenge**: Laika asks where to sleep. Three options: Control area (CO₂ risk), Exercise area (CO₂ risk), Resting stations (safe). Only resting stations is correct. Correct choice: Laika sleeps, CO₂ is extracted, mission secure.

### Level 2: Preparing for the Mission
- **Equipment selection**: Vending machine, cart mode. Must select exactly 3 essential items from 6 options. Essential: Parachute, Heat Shield, Sky Crane. Distractors: Rubber Duck, Balloon, Disco Ball.
- **Communication delay test**: 45-second countdown. Player sends instruction to Laika but must NOT press the send button. If they wait without sending, Laika confirms safe landing. Trap: pressing the button again sends another message, delaying communication further. Correct: wait without sending.

### Level 3: Martian Surface
- **Photography mission**: Take photographs of 6 marked camera buttons. Time limit: 5 minutes. If not completed by 3:30-minute mark, temperature begins to drop (-125°C at 3:30).
- **Sandstorm**: When sandstorm begins, find shelter behind rocks, stop all scientific activities, and activate Low Power Mode. The dust is so dense that sunlight cannot reach the solar panels.
- **Extreme cold**: After sandstorm, temperature drops to -125°C. Activate Hibernation Mode (press H key) to protect rover batteries. Hibernation mode has a 45-second timer. If rover not close enough to lava tunnel, it will be destroyed.

### Level 4: Lava Tunnel Exploration
- **Platforming navigation**: Navigate lava tunnel with flashlight (F key). Not all tunnels are safe. Flashlight reveals path through dark areas.
- **Obstacles**: Jump between rocks following a straight path. Falling rocks and uneven terrain.
- **Required objects**: Find and interact with two buttons: rock sample and camera. Both must be activated to escape.
- **Time limit**: Approximately 4 minutes total. Final 2 minutes: victory sequence showing Laika returning to Earth.
- **Victory**: Laika returns to spacecraft, reuniting with player. Mission complete.

## Win/Lose Structure
- **Win**: Laika survives and returns home with mission completed. Player wins the game.
- **Incomplete**: Laika returns but mission unfinished. Laika says "I won't give up, try again before going back to Earth." Restart the game.
- **Lost**: Laika doesn't return. Whole mission was a failure.

## Science Systems
- **RADLAB + DONKI**: Radiation and real measurements. Mars surface dose ~0.64 mSv/day. Solar particle events watched via feed.
- **OSDR**: Health and biology. Bone density loss ~1-1.5%/month without loading. Muscle loss without exercise.
- **MARS TREK**: Real Mars terrain. Survey sites (Gale Crater). Night low -125°C. Fastest winds in solar system (>2,000 km/h on Neptune, referenced for scale).

## Art & Audio
- All procedural/synthesized. No image or audio files required.
- Game runs with empty `assets/` folder.
- Portraits: Laika happy.png from assets/images (optional, falls back to hologram).
- Sounds: All generated in code via sine/square wave recipes.

## Difficulty Levels
- **Easy**: 5 hearts, +25% time, frequent hints, longer timers.
- **Normal**: The mission as designed on the slides. 3 hearts, standard hazards, standard time.
- **Hard**: 2 hearts, -15% time, shorter timers, harsher cold, stricter comms, hints on request only.

## Fail Handling
- **Food wrong**: "FOOD SAFETY PROTOCOL VIOLATED" modal. Player retries only the food task. On Easy difficulty, one heart is costed; on Normal/Hard, task is retried without penalty.
- **Other task failures**: Retry the specific challenge, not full game restart.
- **Catastrophic losses** (rover destroyed, fallen into pit): End game with appropriate outcome.

## Target Audience
NASA Space Apps Challenge 2026 judges and players. Kid-facing but with real science content. Suitable for ages 10+.

## Core Loop
1. Boot splash → Menu → Briefing (level intro + Laika dialogue) → Level gameplay → Complete → Briefing (next level) → ... → Level 4 complete → Ending (win/incomplete/lost)