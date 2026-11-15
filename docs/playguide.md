# MISSION LAIKA: THE RED HORIZON - Player Guide

## Installation

**Prerequisites:** Python 3.12 (3.11 also works).

```bash
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Never install plain `pygame`; use `pygame-ce`.

## How to Play

### Starting the Game
Run `python main.py`. The game shows a boot splash with NASA APOD (or "archive offline" if no internet). Press any key to continue to the title menu.

### Main Menu
- **New mission**: Resets all progress and starts Level 1 (Outpost)
- **Continue**: Loads last saved game (if exists)
- **Settings**: Change difficulty, volume, sound, text size
- **Quit**: Exit the game

### Difficulty Levels
- **Easy**: 5 hearts, longer timers, gentler storms, more retries. Good for first playthrough.
- **Normal**: The mission as designed on the slides. Standard experience.
- **Hard**: Short timers, harsher cold, stricter comms. 2 hearts, -15% time, hints on request only.

## Level 1: Living on the Outpost

### Overview
Three survival challenges test your decisions. Laika guides you through each task.

### 1. Food Challenge
- **Safety briefing first**: Laika explains "No open liquids: in microgravity, a spilled drink floats and can reach the panels, vents, and the outpost's most sensitive circuits. Choose sealed drinks you can drink through a straw or valve. No crumbly food: crumbs float into the ventilation grilles and circuit boards. Choose food that is sealed, moist, and eaten in one bite — like irradiated chicken in a pouch."
- **Vending machine**: Select TWO items. Correct: sealed drink + irradiated chicken. Wrong: can of soda + cookie → "FOOD SAFETY PROTOCOL VIOLATED" modal appears; player retries the food task (not full mission restart).
- **After eating**: Objective shifts to "Take your meal to the table and eat." Walk to the table and press E/Eat. Then: "Use the vacuum cleaner to remove all food particles from the panels." Vacuum proximity: press E near the vacuum rect to clean crumbs. Counter: CRUMBS 0/14. When all 14 cleaned, proceed.

### 2. Exercise Challenge
- **Vending machine**: Code mode. Must enter code for safety harness. Each item has a number: 1=duck, 2=ball, 3=toy rocket, 4=harness, 5=wrench. Select code 4 (harness).
- **Stationary bicycle**: 22-second rhythm game. Keep alternating left and right key presses. Same key twice in a row reduces gain. After 22 seconds: "Good choice, Astronaut. Strapping in keeps you safe in microgravity."
- **Goal**: Pedal for 22 seconds without losing rhythm.

### 3. Rest Challenge
- **Laika's question**: "Where should Laika sleep? In space, there is no vertical or horizontal. Astronauts attach their sleeping bags to the floor or walls. However, they must choose a location near ventilation grilles that remove the CO₂ we produce when breathing."
- **Three options**: 
  - Control area → CO₂ accumulation risk (wrong)
  - Exercise area → CO₂ accumulation risk (wrong)
  - Resting stations → safe (correct)
- **Correct choice**: Laika sleeps near ventilation grille. CO₂ is extracted. Mission secure.
- **Wrong choice**: Laika receives CO₂ accumulation warning. This could compromise the mission. But progression continues (the game doesn't restart for this one).

### Controls During Level 1
- `E`/Space: Interact / Eat / Take meal to table / Vending confirm
- Arrow keys/WASD: Move
- `H`: Laika hint (when available)

## Level 2: Preparing for the Mission

### Overview
Select essential landing equipment and test the delayed communication with Laika.

### 1. Equipment Selection
- **Vending machine**: Select THREE items from six options. Essential: Parachute, Heat Shield, Sky Crane. Distractors: Rubber Duck, Balloon, Disco Ball.
- **Correct selection**: All three essential items → proceed to communication test.
- **Wrong selection**: Missing essential items → modal feedback + return to briefing to try again.

### 2. Communication Delay Test
- **45-second countdown**: "Communications delay: 00:45. Do NOT press the button."
- **Goal**: Wait the full 45 seconds without pressing send. 
- **Trap**: Pressing space triggers: "Mission control warns: Do not send another message!" and audio deny. Does not restart, just penalizes.
- **Success**: After 45 seconds: "Laika confirms safe landing. Proceed to the surface level."

### Controls During Level 2
- `E`/Space: Vending machine selection / Confirm
- `H`: (Not used in this level specifically)
- Arrow keys/WASD: Move

## Level 3: Martian Surface

### Overview
Take photographs and survive the sandstorm and extreme cold.

### 1. Photography Mission
- **Objective**: Take photographs of 6 marked camera buttons.
- **How**: Walk near a camera button and press E. Shutter sound plays. Counter: "Photo 1/6, 2/6, ..." up to 6/6.
- **Time limit**: 5 minutes total countdown.
- **3:30 mark**: If mission not completed by 3:30, temperature begins to drop.

### 2. Sandstorm
- **When**: After enough photos taken or timer reaches ~45 seconds into the level.
- **Visual**: Storm clouds overlay, visibility reduced.
- **Action**: Find shelter behind the large rocks scattered across the surface. Stop all scientific activities (no more photo taking). Activate Low Power Mode.
- **Failure**: Continuing through the storm → Laika fails because dust blocks sunlight from reaching solar panels.

### 3. Extreme Cold
- **After sandstorm**: Temperature drops to -125°C.
- **Warning**: "Temperature dropping to -125°C! Activate Hibernation Mode."
- **Action**: Press **H** key to activate Hibernation Mode. A 45-second timer starts.
- **Goal**: Survive the cold period. If rover is not close enough to a lava tunnel (within proximity), it will be destroyed.
- **Success**: Hibernation mode protects rover batteries. Mission continues.

### Controls During Level 3
- `E`/Space: Take photo / Interact
- `H`: Activate Hibernation Mode
- Arrow keys/WASD: Move
- `Esc`: Pause menu

## Level 4: Lava Tunnel Exploration

### Overview
Navigate the lava tunnel with flashlight, find rock sample and camera buttons, and escape.

### 1. Flashlight
- **F key**: Toggle Laika's flashlight on/off.
- **Beam**: Lights up dark areas of the tunnel. Essential for finding safe path and buttons.

### 2. Platforming Navigation
- Jump between rocks following a straight path through the cave.
- Watch for falling rocks and uneven terrain.
- If Laika falls, restart from the initial checkpoint at the cave entrance.

### 3. Find Objects
- **Rock sample button**: Interact (E key) → "Rock sample obtained!"
- **Camera button**: Interact (E key) → "Camera activated!"
- **Both required**: Must activate both to escape the tunnel.

### 3. Escape
- After both objects activated, Laika exits the tunnel toward the final destination.
- **Victory sequence**: Final 2 minutes show Laika returning to Earth inside the spacecraft, reuniting with the player.

### Controls During Level 4
- `F`: Toggle flashlight on/off
- `E`/Space: Interact with buttons / Jump
- Arrow keys/WASD: Move / Jump
- `Esc`: Pause menu

## Endings

### Win
- Laika survives and returns home with mission completed.
- Stats screen: mission time, losses, parts recovered, facts learned, best times.
- Message: "Mission complete - Laika is home."

### Incomplete
- Laika returns but mission unfinished.
- Laika says: "I won't give up, try again before going back to Earth."
- Restart the game from the beginning.

### Lost
- Laika doesn't return.
- Whole mission was a failure.
- Message: "Laika did not return."

## HUD Elements
- **Top bar**: Level name, challenge/timer, objective, time left, part inventory
- **Counters**: Photos taken, samples collected, facts learned
- **Meters**: Various mission-specific gauges
- **Banner**: Temporary messages (safety briefing, warnings, toasts)
- **Toast**: Short-duration messages at bottom center
- **Hint prompt**: "H  Laika hint" when hint available

## Troubleshooting
- **Game runs slowly**: Check difficulty setting. Easy mode has longer timers.
- **No audio**: Check volume in settings. All sounds are synthesized.
- **Graphics appear minimal**: All art is procedural. Game runs fine with empty assets/ folder.
- **Game crashes on start**: Ensure Python 3.12+ and pygame-ce installed. Delete savegame.json if corrupt.
- **Level won't progress**: Check objective in HUD. May need to interact with specific object or press correct key.

## Accessibility
- Text size adjustable via settings (Large/Normal)
- Hints available via H key or dialogue box
- No timing requirements critical to progression (difficulty settings adjust timers)
- All mechanics have graceful fallbacks

## Target Play Time
Approximately 20-30 minutes total experience. Core gameplay runs 15-25 minutes depending on difficulty, with briefings and dialogue between levels extending the full experience. Mid-level checkpoints allow judges to see progress in one sitting.

## Quick Controls Summary
| Action | Key(s) |
|--------|--------|
| Advance dialogue / Interact | `E`, `Space` |
| Toggle flashlight (Level 4) | `F` |
| Laika hint | `H` |
| Pause menu | `Esc` |
| Move | Arrow keys, WASD |
| Crouch/duck | Not used |
| Run | Not used |

## After the Game
- Stats screen shows: mission time, losses, parts recovered, facts learned, best times per level
- "Fly again" returns to menu (resets progress)
- "Back to menu" returns to main menu
- Review facts learned about each planet/mission system