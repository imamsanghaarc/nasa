"""Global constants and paths.

Nothing in here mutates at runtime; scenes and systems read from it.
"""

from pathlib import Path

# --- window -----------------------------------------------------------------
WIDTH = 1280
HEIGHT = 720
FPS = 60

TITLE = "MISSION LAIKA: THE RED HORIZON"
SUBTITLE = "A Junior Astronaut Mission Trainer"
CAPTION = f"{TITLE} - {SUBTITLE}"
HACKATHON = "NASA Space Apps Challenge 2026"

# --- paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
SAVE_FILE = ROOT / "savegame.json"

FONT_DISPLAY = "PressStart2P-Regular.ttf"
FONT_BODY = "VT323-Regular.ttf"

PORTRAIT = "laika_happy.png"

# --- palette ----------------------------------------------------------------
SPACE = (9, 7, 14)
SPACE_DEEP = (4, 3, 8)
PANEL = (20, 16, 24)
PANEL_LIGHT = (32, 25, 34)
PANEL_EDGE = (78, 56, 58)
INK = (245, 238, 230)
DIM = (176, 160, 158)
FAINT = (112, 96, 98)

ACCENT = (94, 230, 208)
ACCENT_DARK = (22, 84, 82)
WARN = (255, 179, 71)
DANGER = (255, 92, 122)
GOLD = (255, 209, 102)
GREEN = (124, 224, 150)
RED = (224, 88, 88)

# Mars environment tones
RUST = (193, 84, 47)
RUST_DARK = (122, 50, 30)
DUST = (214, 150, 90)
DUST_PALE = (233, 190, 148)
BASALT = (58, 46, 46)
METAL = (52, 60, 74)
METAL_LIGHT = (86, 98, 116)

DIFFICULTIES = ("easy", "normal", "hard")
DIFFICULTY_LABELS = {"easy": "Cadet", "normal": "Astronaut", "hard": "Veteran"}
DIFFICULTY_BLURB = {
    "easy": "Longer timers, gentler storms, more retries.",
    "normal": "The mission as designed on the slides.",
    "hard": "Short timers, harsher cold, stricter comms.",
}

# --- scene names ------------------------------------------------------------
BOOT = "boot"
MENU = "menu"
MAP = "map"
BRIEFING = "briefing"
TUTORIAL = "tutorial"
LEVEL1 = "level1"
LEVEL2 = "level2"
LEVEL3 = "level3"
LEVEL4 = "level4"
ENDING = "ending"
PAUSE = "pause"

# --- playable scenes (for docs / quick reference) ---
PLAYABLE_SCENES = ("tutorial", "level1", "level2", "level3", "level4", "ending")

# --- mission planets (each one runs the shared world engine) ----------------
MERCURY = "mercury"
VENUS = "venus"
MARS = "mars"
JUPITER = "jupiter"
SATURN = "saturn"
URANUS = "uranus"
NEPTUNE = "neptune"
PLANET_SCENES = (MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE)

# --- campaign ---------------------------------------------------------------
LEVEL_IDS = ("outpost", "landing", "surface", "tunnel")
LEVEL_SCENES = {
    "outpost": LEVEL1,
    "landing": LEVEL2,
    "surface": LEVEL3,
    "tunnel": LEVEL4,
}
FIRST_LEVEL = "outpost"
PLAYABLE_SCENES = (LEVEL1, LEVEL2, LEVEL3, LEVEL4, ENDING)
