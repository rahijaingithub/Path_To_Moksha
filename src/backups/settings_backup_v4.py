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
# Curated spiritual palette, updated for cool mountain theme
COLOR_BG_DARK = (10, 18, 32)           # Deep mountain night blue
COLOR_BG_MEDIUM = (24, 38, 58)         # Cool dark slate blue
COLOR_GOLD = (235, 180, 50)            # Warm temple gold (contrasts with blue)
COLOR_GOLD_BRIGHT = (255, 215, 110)    # Warm highlights
COLOR_GOLD_DIM = (160, 120, 30)        # Shadow gold
COLOR_SAFFRON = (240, 110, 30)         # Warm saffron
COLOR_WHITE = (238, 242, 245)          # Snowy ice white
COLOR_CREAM = (245, 238, 225)          # Warm cream stone
COLOR_RED = (210, 60, 60)              # Danger red
COLOR_BLUE_WATER = (73, 152, 219)      # Soft ice blue from title background
COLOR_GREEN = (70, 180, 110)           # Support green
COLOR_GREY = (107, 98, 93)             # Earthy warm grey from background
COLOR_SHADOW = (0, 0, 0, 128)          # Semi-transparent black
COLOR_TRANSPARENT = (0, 0, 0, 0)
COLOR_LOTUS_PINK = (220, 120, 150)     # Cool lotus accent

# ─── Fonts ────────────────────────────────────────────────────────────────────
FONT_SIZE_TITLE = 72
FONT_SIZE_SUBTITLE = 36
FONT_SIZE_BODY = 24
FONT_SIZE_SMALL = 18
FONT_SIZE_HUD = 20

# Separate larger font size constants for all gameplay scenes to improve readability
GAME_FONT_SIZE_TITLE = 82
GAME_FONT_SIZE_SUBTITLE = 46
GAME_FONT_SIZE_BODY = 32
GAME_FONT_SIZE_SMALL = 24
GAME_FONT_SIZE_HUD = 28

# ─── Physics ──────────────────────────────────────────────────────────────────
GRAVITY = 0.9
PLAYER_SPEED = 7
PLAYER_JUMP_FORCE = -24
LEVEL_JUMP_FORCES = {
    1: -20,
    2: -23,  # Custom jump force for Level 2
    3: -24,
    4: -24,
}
PLAYER_MAX_FALL_SPEED = 14
PLAYER_WIDTH = 96
PLAYER_HEIGHT = 128

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
TOUCH_BUTTON_SIZE = 64
TOUCH_BUTTON_MARGIN = 8
TOUCH_BUTTON_ALPHA = 100  # more subtle transparency (0-255)

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

# Monk questions are loaded dynamically from assets/monk_questions.json
