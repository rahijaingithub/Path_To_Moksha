"""
level_layouts.py — Unique platform layouts for each of the 4 levels.
Separated from level_scene.py for clarity and maintainability.
"""
import pygame
from settings import LOGICAL_WIDTH, LOGICAL_HEIGHT
from slopes import Slope

WALL = 30
PH = 8   # platform thickness — thin to blend with building rooftops

# Level 3: where Mahavir Bhagwan appears once the Akshat is found — on the
# shikhar, centred on the spire (x 958). Top edge sits just under the 48px HUD
# bar; the world is drawn 80px up, so world y 128 is screen y 48.
LEVEL3_BHAGWAN_RECT = (883, 128, 150, 150)

# Level 3: where the fallen bird lies — centre-bottom on white lotus 14 (x 1704-1853,
# top H - 259), toward its right end so the devotee walks up to it from the left.
# Far from the pavilion on purpose: helping is a real detour.
LEVEL3_BIRD_REST = (1815, LOGICAL_HEIGHT - 259)


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


def build_level_slopes(level):
    """Returns the one-way sloped surfaces (slopes.Slope) for the given level."""
    H = LOGICAL_HEIGHT
    if level == 3:
        return [
            Slope([(707, H - 332), (752, H - 328), (823, H - 321)]),                   # 9  Pink lotus by the rock ledge
            # 20 and 19 start half a devotee-width (~13px) in from the traced tip,
            # so standing on the tip never overlaps lily pads 18 / 17 beside them.
            Slope([(323, H - 86), (444, H - 96), (618, H - 132)]),                     # 20 Big pink lotus, left
            Slope([(1361, H - 150), (1506, H - 113), (1666, H - 97)]),                 # 19 Big pink lotus, right
            Slope([(1672, H - 90), (1713, H - 89), (1796, H - 62), (1890, H - 59)]),   # 21 Lily pad, bottom right
        ]
    return []


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
    """The Hall (Valor) — Hard. Jal Mandir: a marble pavilion on a lotus lake.
    Platforms traced from the designer's blue lines on level3_background.png
    (1376x768, stretched to 1920x1080). Numbers in comments are the designer's
    line numbers. The curved petals (9, 19, 20, 21) are slopes — see
    build_level_slopes. Dropped: 5b (right half of the rock ledge, it sat over
    lotus 9), 7 (3px headroom under rock 3), 22-24 (at or below the floor).
    Rule every pair obeys: where two surfaces overlap in x, the upper one's
    underside is at least PLAYER_HEIGHT above the lower one's top, so no spot
    exists where the devotee would stand inside a platform.
    """
    # ── Island: rocks and the pavilion
    p.append(pygame.Rect(790, H - 454, 336, PH))    # 2  Pavilion plinth (Monk sits centre)
    p.append(pygame.Rect(642, H - 462, 83, PH))     # 1  Top of the rock mound
    p.append(pygame.Rect(501, H - 380, 139, PH))    # 5a Left rock ledge
    p.append(pygame.Rect(1143, H - 428, 139, PH))   # 3  Right rocks, upper
    p.append(pygame.Rect(1292, H - 398, 80, PH))    # 4  Right rocks, lower

    # ── Lotus flowers
    p.append(pygame.Rect(82, H - 313, 119, PH))     # 10 Pink lotus, far left
    p.append(pygame.Rect(248, H - 274, 120, PH))    # 13 White lotus, second from left
    p.append(pygame.Rect(419, H - 339, 71, PH))     # 8  Small white lotus, left
    p.append(pygame.Rect(1581, H - 357, 56, PH))    # 6  Small pink lotus, far right
    p.append(pygame.Rect(1704, H - 259, 149, PH))   # 14 White lotus, far right

    # ── Lily pads (12, 15, 17 trimmed where they ran under a neighbour)
    p.append(pygame.Rect(370, H - 249, 46, PH))     # 15 Left
    p.append(pygame.Rect(137, H - 154, 169, PH))    # 18 Lower left
    p.append(pygame.Rect(633, H - 198, 116, PH))    # 16 Centre
    p.append(pygame.Rect(1268, H - 196, 76, PH))    # 17 Right of centre
    p.append(pygame.Rect(1362, H - 292, 92, PH))    # 11 Under the right-centre pink lotus
    p.append(pygame.Rect(1532, H - 279, 46, PH))    # 12 Right


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
