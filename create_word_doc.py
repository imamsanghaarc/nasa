from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

doc = Document()

# Set default font
style = doc.styles['Normal']
font = style.font
font.name = 'Consolas'
font.size = Pt(10)

# Title
title = doc.add_heading('MISSION LAIKA: THE RED HORIZON — Project Journey Document', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()

# ==================== SECTION 1: PROJECT OVERVIEW ====================
doc.add_heading('1. Project Overview', level=1)

p = doc.add_paragraph()
run = p.add_run('Project: ')
run.bold = True
p.add_run('MISSION LAIKA: THE RED HORIZON')

p = doc.add_paragraph()
run = p.add_run('NASA Space Apps Challenge 2026 ')
run.bold = True
p.add_run('Game')

p = doc.add_paragraph()
p.add_run('Genre: ')
run.bold = True
p.add_run('Junior Astronaut Mission Trainer — solar system survival mission')

p = doc.add_paragraph()
p.add_run('Target Audience: ')
run.bold = True
p.add_run('NASA Space Apps Challenge 2026 judges and players; ages 10+')

p = doc.add_paragraph()
p.add_run('Target Play Time: ')
run.bold = True
p.add_run('25-30 minutes full arc with mid-level checkpoints')

p = doc.add_paragraph()
p.add_run('Development Status: ')
run.bold = True
p.add_run('Complete 4-level build with all scenes, art, UI, and data. All 14 headless smoke tests pass.')

doc.add_paragraph()

# ==================== SECTION 2: LEVELS OVERVIEW ====================
doc.add_heading('2. Four-Level Mission Arc', level=1)

# Level 1 table
doc.add_heading('Level 1: Living on the Outpost', level=2)
table = doc.add_table(rows=6, cols=2, style='Light List Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.LEFT
cells = [
    ('Challenge', 'Description'),
    ('Food', 'Safety briefing → Vending machine: select sealed drink + irradiated chicken. Wrong = "FOOD SAFETY PROTOCOL VIOLATED" + restart mission.'),
    ('Exercise', 'Vending code mode: enter code 4 for safety harness → 22s bicycle QTE with alternating left/right key presses. Running freely = lose.'),
    ('Rest', 'Laika asks where to sleep. Three options: Control area (CO₂ risk), Exercise area (CO₂ risk), Resting stations (safe, correct).'),
    ('Outcome', 'All three challenges complete → proceed to Level 2 briefing.'),
    ('Fail handling', 'Food wrong = restart mission. Other challenges = retry task.'),
]
for i, (c1, c2) in enumerate(cells):
    table.rows[i].cells[0].text = c1
    table.rows[i].cells[1].text = c2
    for paragraph in table.rows[i].cells[0].paragraphs:
        for run in paragraph.runs:
            run.bold = True

doc.add_paragraph()

# Level 2 table
doc.add_heading('Level 2: Preparing for the Mission', level=2)
table2 = doc.add_table(rows=5, cols=2, style='Light List Accent 1')
table2.alignment = WD_TABLE_ALIGNMENT.LEFT
cells2 = [
    ('Challenge', 'Description'),
    ('Equipment', 'Vending machine: select 3/6 items. Essential: Parachute, Heat Shield, Sky Crane. Distractors: Rubber Duck, Balloon, Disco Ball.'),
    ('Comms Test', '45-second countdown. Send instruction to Laika but DO NOT press send button. Wait for response. Correct: wait without sending. Trap: pressing button wastes mission time.'),
    ('Outcome', 'Correct: proceed to Level 3. Wrong: return to briefing.'),
    ('Fail handling', 'Wrong equipment = return to briefing. Pressing send during comms = penalty toast (no restart).'),
]
for i, (c1, c2) in enumerate(cells2):
    table2.rows[i].cells[0].text = c1
    table2.rows[i].cells[1].text = c2
    for paragraph in table2.rows[i].cells[0].paragraphs:
        for run in paragraph.runs:
            run.bold = True

doc.add_paragraph()

# Level 3 table
doc.add_heading('Level 3: Martian Surface', level=2)
table3 = doc.add_table(rows=7, cols=2, style='Light List Accent 1')
table3.alignment = WD_TABLE_ALIGNMENT.LEFT
cells3 = [
    ('Challenge', 'Description'),
    ('Photography', 'Take photos of 6 marked camera buttons. E near button. Shutter sound per photo. Counter: Photo X/6. Time limit: 5 min. At 3:30 mark, temperature begins dropping to -125°C.'),
    ('Sandstorm', 'When triggered: find shelter behind rocks, stop all activities, activate Low Power Mode. Dust blocks solar panels. Failure: Laika fails if continuing through storm.'),
    ('Extreme Cold', 'After sandstorm: -125°C. Warning: "Temperature dropping to -125°C! Activate Hibernation Mode." Press H to activate. 45-second timer protects rover batteries. If rover not near lava tunnel, destroyed.'),
    ('Time Mechanics', '5-minute countdown. Temperature drops at 3:30 mark. Hibernation mode: 45 seconds.'),
    ('Outcome', 'Hibernation active → proceed. Rover destroyed → game over / incomplete.'),
    ('Fail handling', 'Continue through sandstorm = fail. Forget Hibernation = rover destroyed. Otherwise retry sections.'),
]
for i, (c1, c2) in enumerate(cells3):
    table3.rows[i].cells[0].text = c1
    table3.rows[i].cells[1].text = c2
    for paragraph in table3.rows[i].cells[0].paragraphs:
        for run in paragraph.runs:
            run.bold = True

doc.add_paragraph()

# Level 4 table
doc.add_heading('Level 4: Lava Tunnel Exploration', level=2)
table4 = doc.add_table(rows=6, cols=2, style='Light List Accent 1')
table4.alignment = WD_TABLE_ALIGNMENT.LEFT
cells4 = [
    ('Challenge', 'Description'),
    ('Platforming', 'Navigate lava tunnel with jump rocks. Falling = restart from cave entrance checkpoint.'),
    ('Flashlight', "F key toggles Laika's flashlight. Essential for dark areas and finding buttons. Beam visual in-game."),
    ('Required Objects', 'Find & interact with Rock sample button + Camera button. Both must be activated (E key) to escape.'),
    ('Escape', 'Both activated → Laika exits tunnel → 2-min victory sequence showing return to Earth.'),
    ('Time Limit', '~4 minutes total. Final 2 min: victory sequence.'),
]
for i, (c1, c2) in enumerate(cells4):
    table4.rows[i].cells[0].text = c1
    table4.rows[i].cells[1].text = c2
    for paragraph in table4.rows[i].cells[0].paragraphs:
        for run in paragraph.runs:
            run.bold = True

doc.add_paragraph()

# ==================== SECTION 3: SCIENCE LAYER ====================
doc.add_heading('3. Science Systems', level=1)

p = doc.add_paragraph()
p.add_run('Three NASA systems integrated per briefing:').bold = True

systems_data = [
    ('RADLAB + DONKI', 'Radiation and real measurements', 'https://ccmc.gsfc.nasa.gov/tools/DONKI/', 'Mars surface dose ~0.64 mSv/day; Solar particle events watched via feed'),
    ('OSDR', 'Health and biology', 'https://osdr.nasa.gov/', 'Bone density loss ~1-1.5%/month without loading; Muscle loss without exercise'),
    ('MARS TREK', 'Real Mars terrain', 'https://trek.nasa.gov/mars/', 'Night low -125°C; Survey site Gale Crater; Fastest winds >2,000 km/h (Neptune scale)'),
]

table5 = doc.add_table(rows=4, cols=4, style='Light List Accent 1')
table5.alignment = WD_TABLE_ALIGNMENT.LEFT
headers = ['System', 'Role', 'URL', 'In-Game Metrics']
for i, h in enumerate(headers):
    table5.rows[0].cells[i].text = h
    for run in table5.rows[0].cells[i].paragraphs[0].runs:
        run.bold = True

for r, (sys, role, url, metrics) in enumerate(systems_data, 1):
    table5.rows[r].cells[0].text = sys
    table5.rows[r].cells[1].text = role
    table5.rows[r].cells[2].text = url
    table5.rows[r].cells[3].text = metrics

doc.add_paragraph()

p = doc.add_paragraph()
p.add_run('Cached Data: ').bold = True
p.add_run('All science values bundled in data/science.json for offline play. Game never touches network during gameplay. tools/fetch_science.py can refresh when online.')

doc.add_paragraph()

# ==================== SECTION 4: TECHNICAL SUMMARY ====================
doc.add_heading('4. Technical Summary', level=1)

tech_items = [
    ('Scenes', '14 total: boot, menu, map, tutorial, level1-4, briefing, ending. All pass headless smoke test.'),
    ('Art', '100% procedural. No image/audio files required. Game runs with empty assets/ folder.'),
    ('Movement', 'Walker (top-down), Platformer (side-view with gravity), CombatPlayer (blaster extension).'),
    ('UI', 'Dialogue box (Laika portrait), HUD (top bar + counters + meters + banner + toast), Modal (confirmation), Vending (3 modes: cart/code/load).'),
    ('Save System', 'VERSION 2 JSON (savegame.json). Preferences survive reset; campaign progress does not.'),
    ('Difficulty', 'Easy (5 hearts, +25% time, frequent hints), Normal (standard), Hard (2 hearts, -15% time, hints on request only).'),
    ('Fail handling', 'Food wrong = restart mission. Other tasks = retry. Catastrophic losses = game over.'),
    ('Dependencies', 'pygame-ce only. No plain pygame. Python 3.12+. No network required during gameplay.'),
]

for item in tech_items:
    p = doc.add_paragraph()
    run = p.add_run(item)
    run.font.size = Pt(10)

doc.add_paragraph()

# ==================== SECTION 5: DOCUMENTATION ====================
doc.add_heading('5. Documentation Files', level=1)

docs_list = [
    ('README.md', 'Project overview, install, run, controls, level descriptions'),
    ('DOCS.md', 'Documentation index and keeping docs in sync'),
    ('design.md', 'Game design document — premise, story, pillars, level design, mechanics, art/audio, win-lose structure'),
    ('technical.md', 'Technical reference — architecture, scene design, data flow, module guide, engineering rules, save system'),
    ('playguide.md', 'Player-facing guide — install, run, controls, level objectives, Laika/hints, difficulty, troubleshooting'),
    ('SCIENCE.md', 'NASA science appendix — planetary facts, sources, APOD, verification'),
    ('DATA.md', 'Data & content format reference — planets, levels, dialogue, APOD JSON schemas'),
    ('TOOLS.md', 'Developer/QA tools — smoke test, APOD cache, science refresh, screen shots'),
    ('HACKATHON.md', 'Hackathon-specific: project summary, judging criteria, controls, checklists'),
    ('CONTRIBUTING.md', 'Contributing guide — code conventions, adding levels/dialogue/difficulty, art, science, documentation'),
]

for fname, desc in docs_list:
    p = doc.add_paragraph()
    run = p.add_run(fname)
    run.bold = True
    p.add_run(f' — {desc}')

doc.add_paragraph()

# ==================== SECTION 6: CURRENT STATE ====================
doc.add_heading('6. Current Build State', level=1)

p = doc.add_paragraph()
run = p.add_run('Scenes: ')
run.bold = True
p.add_run('14 scenes all passing headless smoke test: boot, menu, map, tutorial, level1-4, briefing, ending')

p = doc.add_paragraph()
run = p.add_run('Levels: ')
run.bold = True
p.add_run('4 levels complete: Outpost (L1), Landing (L2), Martian Surface (L3), Lava Tunnel (L4)')

p = doc.add_paragraph()
run = p.add_run('Art: ')
run.bold = True
p.add_run('100% procedural. No image/audio files required.')

p = doc.add_paragraph()
run = p.add_run('Data: ')
run.bold = True
p.add_run('All JSON under data/. Seven parts from planets.json. Four level JSONs. Dialogue in data/dialogue/.')

p = doc.add_paragraph()
run = p.add_run('UI: ')
run.bold = True
p.add_run('Dialogue box, HUD, Modal, Vending (3 modes). All tested.')

p = doc.add_paragraph()
run = p.add_run('Fail handling: ')
run.bold = True
p.add_run('Food wrong = restart mission. Other tasks = retry specific challenge.')

p = doc.add_paragraph()
run = p.add_run('Difficulties: ')
run.bold = True
p.add_run('Easy (5 hearts, +25% time, hints), Normal (standard), Hard (2 hearts, -15% time, hints on request)')

doc.add_paragraph()

# ==================== SECTION 7: NEXT STEPS ====================
doc.add_heading('7. Next Steps', level=1)

p = doc.add_paragraph()
run = p.add_run('1. Ending screen polish ')
run.bold = True
p.add_run('— Win/lost/incomplete outcomes with Laika return animation and stats screen')

p = doc.add_paragraph()
run = p.add_run('2. Documentation review ')
run.bold = True
p.add_run('')

p = doc.add_paragraph()
run = p.add_run('3. Final build test ')
run.bold = True
p.add_run('— Verify all mechanics, difficulties, save/load, smoke test')

p = doc.add_paragraph()
run = p.add_run('4. Judge presentation prep ')
run.bold = True
p.add_run('— Build pygbag version for web demo if needed')

doc.add_paragraph()

# ==================== SECTION 8: CONTACT ====================
doc.add_heading('8. Contact', level=1)
p = doc.add_paragraph('Project: MISSION LAIKA: THE RED HORIZON')
p = doc.add_paragraph('NASA Space Apps Challenge 2026')
p = doc.add_paragraph('Built with Python + pygame-ce — 100% procedural, no image/audio files required')

doc.add_paragraph()
doc.add_paragraph('_' * 50)
doc.add_paragraph('Generated: ' + __import__('datetime').datetime.now().strftime('%B %d, %Y'))

# Save the document
output_path = 'LAIKA_MARS_MISSION_Project_Journey.docx'
doc.save(output_path)
print(f'Word document saved successfully to {output_path}')