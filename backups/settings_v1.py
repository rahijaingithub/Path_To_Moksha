"""
settings.py — Global constants and configuration for The Path to Moksha.
"""
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# ─── Display ──────────────────────────────────────────────────────────────────
# The game renders to this logical resolution, then scales to the window.
# Using 1920x1080 as the base so fullscreen on modern monitors is crisp.
LOGICAL_WIDTH = 1920
LOGICAL_HEIGHT = 1080
GAME_TITLE = "The Path to Moksha"
FPS = 60
DEFAULT_WINDOWED_SIZE = (1280, 720)

# ─── Colors ───────────────────────────────────────────────────────────────────
# Curated spiritual palette
COLOR_BG_DARK = (18, 12, 28)           # Deep indigo — night sky
COLOR_BG_MEDIUM = (32, 24, 48)         # Dark purple
COLOR_GOLD = (255, 200, 60)            # Temple gold
COLOR_GOLD_BRIGHT = (255, 223, 100)    # Highlight gold
COLOR_GOLD_DIM = (180, 140, 40)        # Shadow gold
COLOR_SAFFRON = (255, 130, 40)         # Saffron / sacred orange
COLOR_WHITE = (245, 242, 235)          # Warm white (like marble)
COLOR_CREAM = (255, 248, 230)          # Cream / parchment
COLOR_RED = (200, 50, 50)              # Danger / fire
COLOR_BLUE_WATER = (60, 120, 200)      # Water hazard
COLOR_GREEN = (80, 200, 100)           # Support / positive
COLOR_GREY = (120, 115, 130)           # UI neutral
COLOR_SHADOW = (0, 0, 0, 128)         # Semi-transparent black
COLOR_TRANSPARENT = (0, 0, 0, 0)
COLOR_LOTUS_PINK = (230, 130, 170)     # Lotus accent

# ─── Fonts ────────────────────────────────────────────────────────────────────
FONT_SIZE_TITLE = 72
FONT_SIZE_SUBTITLE = 36
FONT_SIZE_BODY = 24
FONT_SIZE_SMALL = 18
FONT_SIZE_HUD = 20

# ─── Physics ──────────────────────────────────────────────────────────────────
GRAVITY = 0.9
PLAYER_SPEED = 7
PLAYER_JUMP_FORCE = -20
PLAYER_MAX_FALL_SPEED = 14
PLAYER_WIDTH = 48
PLAYER_HEIGHT = 64

# ─── Gameplay ─────────────────────────────────────────────────────────────────
LEVEL_TIME_LIMIT = {
    1: 120,  # seconds
    2: 150,
    3: 180,
    4: 210,
}
SUPPORT_TIME_BONUS = 15      # seconds added
DISTRACTION_TIME_PENALTY = 10  # seconds lost
DISTRACTION_FREEZE_DURATION = 2.0  # seconds of control freeze

# ─── Touch Controls ──────────────────────────────────────────────────────────
TOUCH_BUTTON_SIZE = 90
TOUCH_BUTTON_MARGIN = 20
TOUCH_BUTTON_ALPHA = 140  # semi-transparent (0-255)

# ─── Scene Keys ───────────────────────────────────────────────────────────────
SCENE_TITLE = "title"
SCENE_CHARACTER_SELECT = "character_select"
SCENE_LEVEL = "level"
SCENE_TRANSITION = "transition"
SCENE_VICTORY = "victory"

# ─── Level Data ───────────────────────────────────────────────────────────────
LEVEL_NAMES = {
    1: "The Commute",
    2: "The Cave",
    3: "The Hall",
    4: "The Summit",
}
LEVEL_SUBTITLES = {
    1: "Samsara",
    2: "Resilience",
    3: "Valor",
    4: "Moksha",
}

# ─── Monk Questions ──────────────────────────────────────────────────────────
MONK_QUESTIONS = {
    1: {
        "question": "To find peace, what must one leave behind?",
        "choices": ["Ego", "Car"],
        "correct": 0,
    },
    2: {
        "question": "Who shielded the Lord from the storm?",
        "choices": ["Dharanendra", "Kamatha"],
        "correct": 0,
    },
    3: {
        "question": "What is the weapon of the Tirthankara?",
        "choices": ["Ahimsa", "Sword"],
        "correct": 0,
    },
    4: {
        "question": "Who was the first to show the path?",
        "choices": ["Adinath", "Bahubali"],
        "correct": 0,
    },
}
