"""
level_layouts.py — Unique platform layouts for each of the 4 levels.
Separated from level_scene.py for clarity and maintainability.
"""
import pygame
from settings import LOGICAL_WIDTH, LOGICAL_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT
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

# Level 3: the flat lotus flowers and lily pads, as (x, top, width). Numbers are the
# designer's line numbers. They are ONE-WAY (designer, 2026-11-14): a jump passes up
# through them and they hold whoever comes down onto them, like the curved petals.
# build_level_platforms still lists them as rects, because boxes are placed on
# them; build_level_slopes turns each into a flat Slope for the physics, and
# solid_platforms() is what the devotee actually collides with.
_H = LOGICAL_HEIGHT
# The island's rocks and the pavilion: solid from every side, as (x, top, width).
LEVEL3_ROCKS = (
    (790, _H - 454, 336),    # 2  Pavilion plinth (Monk sits centre)
    (642, _H - 462, 83),     # 1  Top of the rock mound
    (501, _H - 380, 139),    # 5a Left rock ledge
    (1143, _H - 428, 139),   # 3  Right rocks, upper
    (1292, _H - 398, 80),    # 4  Right rocks, lower
)
LEVEL3_FLOWERS = (
    # Lotus flowers
    (82, _H - 313, 119),     # 10 Pink lotus, far left
    (248, _H - 274, 120),    # 13 White lotus, second from left
    (419, _H - 339, 71),     # 8  Small white lotus, left
    (1581, _H - 357, 56),    # 6  Small pink lotus, far right
    (1704, _H - 259, 149),   # 14 White lotus, far right
    # Lily pads (12, 15, 17 trimmed where they ran under a neighbour)
    (370, _H - 249, 46),     # 15 Left
    (137, _H - 154, 169),    # 18 Lower left
    (633, _H - 198, 116),    # 16 Centre
    (1268, _H - 196, 76),    # 17 Right of centre
    (1362, _H - 292, 92),    # 11 Under the right-centre pink lotus
    (1532, _H - 279, 46),    # 12 Right
)
# A rect holds the devotee while any part of them overlaps it; a Slope holds them
# by their centre. Half a devotee-width each side keeps the standing room the same.
LEVEL3_FLOWER_OVERHANG = 13

# Level 4 (Kailash): ledges as (x, top, width), read off level4_background.png
# after tools/prepare_level4_background.py slid it down 150px, and confirmed by
# the designer on the marked-up proposal (2026-11-14). Numbered in climbing order.
LEVEL4_START_SHELF = (30, 965, 470)       # S: the snowy shelf, bottom left
LEVEL4_MONK_SHELF = (1680, 430, 200)      # 9: the snow shelf beside Kailash
LEVEL4_SUMMIT = (1340, 285, 140)          # 10: wider than the snow cap, so the gate has room
LEVEL4_CRUMBLING = ((960, 755, 240),      # 2: the ice shelf (designer, 2026-11-14) — the way
                                          #    onto the left route; the right route starts
                                          #    from the outcrop and does not need it
                    (705, 460, 60),       # 4: the rock spire (the mesa catches a fall)
                    (1500, 550, 260))     # 8: the right ridge (the terrace catches most)
LEVEL4_LEDGES = (
    LEVEL4_START_SHELF,
    (685, 1000, 155),      # 1 stream block
    LEVEL4_CRUMBLING[0],   # 2 ice shelf
    (320, 645, 570),       # 3 great mesa
    LEVEL4_CRUMBLING[1],   # 4 spire
    (1010, 500, 290),      # 5 high plateau
    (1120, 1000, 440),     # 6 rock outcrop
    (1600, 805, 290),      # 7 right terrace
    LEVEL4_CRUMBLING[2],   # 8 right ridge
    LEVEL4_MONK_SHELF,
    LEVEL4_SUMMIT,
)
# Boxes: the wide, lasting ledges only. Not the valley floor (cold shock), not a
# ledge that crumbles, not the Monk's, not the summit where the gate appears.
LEVEL4_BOX_LEDGES = tuple(l for l in LEVEL4_LEDGES
                          if l not in LEVEL4_CRUMBLING + (LEVEL4_MONK_SHELF, LEVEL4_SUMMIT))


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


def solid_platforms(level, platforms):
    """The rects that block from every side: `platforms` without the one-way
    flowers of Level 3, which are stood on through build_level_slopes instead."""
    if level != 3:
        return list(platforms)
    flowers = set(LEVEL3_FLOWERS)
    return [p for p in platforms if (p.x, p.y, p.width) not in flowers]


def _flower_slope(x, top, width):
    """A flat one-way Slope for a Level 3 flower, overhanging by
    LEVEL3_FLOWER_OVERHANG at each end — less where a rock stands beside it, so no
    spot on the flower puts the devotee's body inside solid stone."""
    half = PLAYER_WIDTH / 2
    left, right = x - LEVEL3_FLOWER_OVERHANG, x + width + LEVEL3_FLOWER_OVERHANG
    for rx, rtop, rwidth in LEVEL3_ROCKS:
        if not (rtop < top and rtop + PH > top - PLAYER_HEIGHT):
            continue                                  # not at body height
        if rx >= x + width:
            right = min(right, rx - half - 1)
        elif rx + rwidth <= x:
            left = max(left, rx + rwidth + half + 1)
    return Slope([(left, top), (right, top)])


def build_level_slopes(level):
    """Returns the one-way surfaces (slopes.Slope) for the given level: the curved
    petals, and every flat flower and lily pad of Level 3."""
    H = LOGICAL_HEIGHT
    if level == 3:
        return [_flower_slope(*flower) for flower in LEVEL3_FLOWERS] + [
            Slope([(707, H - 332), (752, H - 328), (823, H - 321)]),                   # 9  Pink lotus by the rock ledge
            # 20 and 19 start half a devotee-width (~13px) in from the traced tip,
            # so standing on the tip never overlaps lily pads 18 / 17 beside them.
            Slope([(323, H - 86), (444, H - 96), (618, H - 132)]),                     # 20 Big pink lotus, left
            Slope([(1361, H - 150), (1506, H - 113), (1666, H - 97)]),                 # 19 Big pink lotus, right
            Slope([(1672, H - 90), (1713, H - 89), (1796, H - 62), (1890, H - 59)]),   # 21 Lily pad, bottom right
        ]
    return []


def _build_level1(p, W, H):
    """The City (Samsara) — Easy. Toronto cityscape.
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
    """The Forest (Resilience) — Medium. Forest ledges with water channels."""
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
    """The Lake (Valor) — Hard. Jal Mandir: a marble pavilion on a lotus lake.
    Platforms traced from the designer's blue lines on level3_background.png
    (1376x768, stretched to 1920x1080). Numbers in comments are the designer's
    line numbers. The curved petals (9, 19, 20, 21) are slopes — see
    build_level_slopes. Dropped: 5b (right half of the rock ledge, it sat over
    lotus 9), 7 (3px headroom under rock 3), 22-24 (at or below the floor).
    Rule every pair obeys: where two surfaces overlap in x, the upper one's
    underside is at least PLAYER_HEIGHT above the lower one's top, so no spot
    exists where the devotee would stand inside a platform.
    """
    # ── Island: rocks and the pavilion, solid: see LEVEL3_ROCKS
    for x, top, width in LEVEL3_ROCKS:
        p.append(pygame.Rect(x, top, width, PH))

    # ── Lotus flowers and lily pads: one-way, see LEVEL3_FLOWERS
    for x, top, width in LEVEL3_FLOWERS:
        p.append(pygame.Rect(x, top, width, PH))


def _build_level4(p, W, H):
    """The Mountain (Moksha) — Kailash. Two ways up from the ice shelf: left over
    the great mesa, right past the Monk. Every hop is checked with the real
    Player in tests/test_level4_layout.py."""
    for x, top, width in LEVEL4_LEDGES:
        p.append(pygame.Rect(x, top, width, PH))
