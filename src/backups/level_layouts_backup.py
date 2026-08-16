"""
level_layouts.py — Unique platform layouts for each of the 4 levels.
Separated from level_scene.py for clarity and maintainability.
"""
import pygame
from settings import LOGICAL_WIDTH, LOGICAL_HEIGHT

WALL = 30
PH = 20  # platform height


def build_level_platforms(level):
    """Returns a list of pygame.Rect platforms for the given level."""
    W = LOGICAL_WIDTH
    H = LOGICAL_HEIGHT

    platforms = []

    # ── Boundaries (same for all levels) ──
    platforms.append(pygame.Rect(0, H - WALL, W, WALL))      # Floor
    platforms.append(pygame.Rect(0, 0, W, WALL))              # Ceiling
    platforms.append(pygame.Rect(0, 0, WALL, H))              # Left wall
    platforms.append(pygame.Rect(W - WALL, 0, WALL, H))       # Right wall

    if level == 1:
        _build_level1(platforms, W, H)
    elif level == 2:
        _build_level2(platforms, W, H)
    elif level == 3:
        _build_level3(platforms, W, H)
    elif level == 4:
        _build_level4(platforms, W, H)

    return platforms


def _build_level1(p, W, H):
    """The Commute (Samsara) — Easy. Toronto cityscape."""
    # Tier 1 — ground level steps
    p.append(pygame.Rect(250, H - 180, 200, PH))
    p.append(pygame.Rect(550, H - 180, 160, PH))

    # Tier 2 — mid-low
    p.append(pygame.Rect(800, H - 300, 220, PH))
    p.append(pygame.Rect(450, H - 340, 180, PH))
    p.append(pygame.Rect(100, H - 370, 200, PH))

    # Tier 3 — middle
    p.append(pygame.Rect(350, H - 500, 250, PH))
    p.append(pygame.Rect(700, H - 480, 180, PH))
    p.append(pygame.Rect(1050, H - 440, 200, PH))

    # Tier 4 — mid-high
    p.append(pygame.Rect(1300, H - 560, 220, PH))
    p.append(pygame.Rect(900, H - 640, 200, PH))
    p.append(pygame.Rect(550, H - 680, 180, PH))
    p.append(pygame.Rect(200, H - 650, 160, PH))

    # Tier 5 — high
    p.append(pygame.Rect(400, H - 800, 200, PH))
    p.append(pygame.Rect(750, H - 820, 250, PH))
    p.append(pygame.Rect(1100, H - 780, 200, PH))

    # Tier 6 — near top
    p.append(pygame.Rect(1400, H - 880, 220, PH))
    p.append(pygame.Rect(1650, H - 800, 180, PH))

    # Goal area (top-right)
    p.append(pygame.Rect(1600, H - 950, 250, PH))


def _build_level2(p, W, H):
    """The Cave (Resilience) — Medium. Stone cave with water channels."""
    # Low shelves
    p.append(pygame.Rect(200, H - 160, 180, PH))
    p.append(pygame.Rect(500, H - 200, 200, PH))
    p.append(pygame.Rect(850, H - 170, 160, PH))

    # Mid platforms — wider gaps
    p.append(pygame.Rect(1100, H - 310, 200, PH))
    p.append(pygame.Rect(750, H - 380, 180, PH))
    p.append(pygame.Rect(350, H - 420, 220, PH))
    p.append(pygame.Rect(100, H - 350, 150, PH))

    # Upper cave
    p.append(pygame.Rect(500, H - 550, 200, PH))
    p.append(pygame.Rect(850, H - 580, 180, PH))
    p.append(pygame.Rect(1200, H - 520, 200, PH))

    # High passage
    p.append(pygame.Rect(1450, H - 650, 200, PH))
    p.append(pygame.Rect(1100, H - 720, 180, PH))
    p.append(pygame.Rect(700, H - 750, 220, PH))
    p.append(pygame.Rect(300, H - 780, 180, PH))

    # Exit ledge (top-left this time — variation)
    p.append(pygame.Rect(100, H - 900, 250, PH))


def _build_level3(p, W, H):
    """The Hall (Valor) — Hard. Marble hall with disappearing-style platforms."""
    # Ground level small ledges
    p.append(pygame.Rect(180, H - 160, 140, PH))
    p.append(pygame.Rect(450, H - 190, 140, PH))
    p.append(pygame.Rect(700, H - 160, 140, PH))
    p.append(pygame.Rect(950, H - 200, 140, PH))

    # Middle rows — smaller, tighter
    p.append(pygame.Rect(1200, H - 320, 160, PH))
    p.append(pygame.Rect(900, H - 400, 150, PH))
    p.append(pygame.Rect(600, H - 440, 150, PH))
    p.append(pygame.Rect(300, H - 380, 160, PH))

    # Upper hall — narrow ledges
    p.append(pygame.Rect(100, H - 540, 140, PH))
    p.append(pygame.Rect(400, H - 580, 140, PH))
    p.append(pygame.Rect(700, H - 620, 150, PH))
    p.append(pygame.Rect(1000, H - 570, 140, PH))
    p.append(pygame.Rect(1300, H - 530, 160, PH))

    # High passage
    p.append(pygame.Rect(1500, H - 680, 160, PH))
    p.append(pygame.Rect(1200, H - 760, 150, PH))
    p.append(pygame.Rect(800, H - 800, 180, PH))
    p.append(pygame.Rect(450, H - 840, 150, PH))

    # Goal area (top-center)
    p.append(pygame.Rect(850, H - 950, 220, PH))


def _build_level4(p, W, H):
    """The Summit (Moksha) — Expert. Narrow, demanding path to the peak."""
    # Ground level — very few footholds
    p.append(pygame.Rect(200, H - 180, 120, PH))
    p.append(pygame.Rect(500, H - 200, 120, PH))

    # Narrow stepping stones
    p.append(pygame.Rect(780, H - 300, 110, PH))
    p.append(pygame.Rect(1050, H - 350, 110, PH))
    p.append(pygame.Rect(1300, H - 280, 120, PH))

    # Mid section — zigzag
    p.append(pygame.Rect(1500, H - 430, 130, PH))
    p.append(pygame.Rect(1250, H - 520, 120, PH))
    p.append(pygame.Rect(950, H - 560, 130, PH))
    p.append(pygame.Rect(650, H - 510, 120, PH))
    p.append(pygame.Rect(350, H - 580, 130, PH))

    # Upper zigzag
    p.append(pygame.Rect(150, H - 680, 120, PH))
    p.append(pygame.Rect(400, H - 740, 120, PH))
    p.append(pygame.Rect(700, H - 780, 130, PH))
    p.append(pygame.Rect(1000, H - 730, 120, PH))
    p.append(pygame.Rect(1300, H - 800, 120, PH))

    # Final narrow ascent
    p.append(pygame.Rect(1550, H - 880, 120, PH))
    p.append(pygame.Rect(1300, H - 940, 130, PH))

    # Summit — goal (top-center-right)
    p.append(pygame.Rect(1000, H - 980, 200, PH))
