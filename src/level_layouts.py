"""
level_layouts.py — Unique platform layouts for each of the 4 levels.
Separated from level_scene.py for clarity and maintainability.
"""
import pygame
from settings import LOGICAL_WIDTH, LOGICAL_HEIGHT

WALL = 30
PH = 8   # platform thickness — thin to blend with building rooftops


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
    """The Commute (Samsara) — Easy. Toronto cityscape.
    Platforms aligned to building rooftops in level1_background.png (1920x1080).
    Updated per user feedback: removed TTC step and rightmost row house,
    moved all Tier 2 platforms DOWN ~70px, moved Tier 3 DOWN ~65px.
    """

    # ── TIER 1: Shop rooftops (ground-floor commercial buildings)
    # Continuous roofline: ~y=555 from top
    p.append(pygame.Rect(207.0, H - 532.5, 215, PH))   # Roof of building left to Pizza place
    p.append(pygame.Rect(505.5, H - 391.5, 50, PH))  # Toronto Pizza Window
    p.append(pygame.Rect(1111.5, H - 526.5, 395, PH))  # Bookshop roof
    p.append(pygame.Rect(1495.5, H - 556.5, 265, PH))   # TTC Subway / corner roof
    p.append(pygame.Rect(1018.5, H - 393.0, 150, PH))  # Grocery Shop  Window

    # ── AWNING PLATFORMS: Low street-level stepping stones on shop awnings
    # Toronto Pizza striped awning (~x:225-370, awning top ~y=650 → H-430)
    p.append(pygame.Rect(439.5, H - 219.0, 200, PH))  # Bus Stop roof
    # City Bakery striped awning (~x:390-530, awning top ~y=650 → H-430)
    p.append(pygame.Rect(727.433628318584, H - 299.46902654867256, 200, PH)) # City Bakery awning

    # ── TIER 2: 2-storey row-house rooftops (moved DOWN ~70px from original)
    p.append(pygame.Rect(759.0, H - 625.5, 200, PH))  # House behind Grocery store
    p.append(pygame.Rect(360.0, H - 690.0, 100, PH))   # Second-left row house peak
    # p.append(pygame.Rect(440,  H - 695, 210, PH))   # Left-centre row house
    # p.append(pygame.Rect(720,  H - 720, 220, PH))   # Centre row house
    # p.append(pygame.Rect(1000, H - 695, 210, PH))   # Right-centre row house
    p.append(pygame.Rect(1407.0, H - 690.0, 115, PH))   # Far-right row house peak
    # REMOVED: (1550, H-760) — rightmost row house (marked X by user)

    # ── TIER 3: Tallest building ridge peaks (moved DOWN ~65px from original)
    p.append(pygame.Rect(777.0, H - 697.5, 50, PH))  # Tall peak centre above centre house
    p.append(pygame.Rect(1084.5, H - 726.0, 50, PH))  # Tall peak L of CN tower
    p.append(pygame.Rect(1383.0, H - 789.0, 50, PH))   # Tall peak R of CN tower
  
    # REMOVED: far-right (1550+) Tier 3 — marked X by user

    # ── GOAL AREA: Temple door platform at street level, far right ──
    # p.append(pygame.Rect(1740, H - 120, 160, PH))   # Temple door landing platform


def _build_level2(p, W, H):
    """The Cave (Resilience) — Medium. Stone cave with water channels."""
    # Low shelves
    p.append(pygame.Rect(130, H - 160, 170, PH)) # Left
    p.append(pygame.Rect(730, H - 132, 120, PH)) #Middle
    p.append(pygame.Rect(1220, H - 190, 120, PH)) #Right

    # Mid platforms — wider gaps
    p.append(pygame.Rect(1700,H - 197,50,PH)) # Small Platform on the right
    p.append(pygame.Rect(1195, H - 395, 380, PH)) # Big Platform in middle right
    # p.append(pygame.Rect(350, H - 420, 220, PH))
    # p.append(pygame.Rect(100, H - 350, 150, PH))

    # Upper cave
    p.append(pygame.Rect(110, H - 495, 290,PH))
    p.append(pygame.Rect(500, H - 495, 380, PH))
    p.append(pygame.Rect(1150, H - 508, 250, PH))

    # High passage
    p.append(pygame.Rect(1500, H - 625, 155, PH))
    p.append(pygame.Rect(1700, H - 680, 120, PH))
    # p.append(pygame.Rect(700, H - 750, 220, PH))
    # p.append(pygame.Rect(300, H - 780, 180, PH))

    # Exit ledge (top-left this time — variation)
    # p.append(pygame.Rect(100, H - 900, 250, PH))


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
