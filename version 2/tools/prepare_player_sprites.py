"""
prepare_player_sprites.py
Run from anywhere; paths resolve relative to this file (repo/tools/).
It reads from <repo>/assets/images/sprites/, removes white backgrounds,
normalizes each frame to 128x128 (feet-aligned), and overwrites in-place.

Usage:
    python prepare_player_sprites.py
"""
import os
from PIL import Image

# Repo root is the parent of tools/ — same idiom as clean_temple_gate.py.
SPRITES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "images", "sprites",
)

# File → (rows, cols) grid layout in the SOURCE image.
#
# NOTE: the girl entries were missing entirely, so her sheets were never
# normalized and are still at their generated resolution (416–720 px tall) while
# the boy's are 128 px. Nothing in the game breaks because of that on its own —
# frame size is derived from strip height — but any code that assumed 128 px
# counted her frames roughly 4x over. See level_scene.strip_frame_count().
#
# The BOY's walk is now a real 8-frame cycle. The GIRL's is still four copies of
# one standing pose; change her two entries to (1, 8) when her redrawn sheet
# lands. Her replacement must have bold dark outlines — her white kurta is the
# same value as the white background, so remove_white_bg() floods straight
# through the edge and eats holes in her clothing.
SPRITE_GRID = {
    "player_boy_idle_left.png":  (2, 2),
    "player_boy_idle_right.png": (2, 2),
    "player_boy_walk_left.png":  (1, 8),
    "player_boy_walk_right.png": (1, 8),
    "player_boy_run_left.png":   (1, 6),
    "player_boy_run_right.png":  (1, 6),
    "player_boy_jump_left.png":  (1, 4),
    "player_boy_jump_right.png": (1, 4),
    "player_boy_fall_left.png":  (1, 3),
    "player_boy_fall_right.png": (1, 3),
    "player_boy_stun_left.png":  (1, 2),
    "player_boy_stun_right.png": (1, 2),

    "player_girl_idle_left.png":  (1, 4),
    "player_girl_idle_right.png": (1, 4),
    "player_girl_walk_left.png":  (1, 8),
    "player_girl_walk_right.png": (1, 8),
    "player_girl_run_left.png":   (1, 6),
    "player_girl_run_right.png":  (1, 6),
    "player_girl_jump_left.png":  (1, 4),
    "player_girl_jump_right.png": (1, 4),
    "player_girl_fall_left.png":  (1, 3),
    "player_girl_fall_right.png": (1, 3),
    "player_girl_stun_left.png":  (1, 2),
    "player_girl_stun_right.png": (1, 2),
}

FRAME_W    = 128   # Output frame width (px)
FRAME_H    = 128   # Output frame height (px)
BASELINE_Y = 120   # Row inside frame canvas where feet should land


def remove_white_bg(cell):
    """Flood-fill from all 4 edges, erase whitish pixels (R,G,B > 230)."""
    cw, ch = cell.size
    cpix = cell.load()
    visited = set()
    stack = []

    # Seed all border pixels
    for x in range(cw):
        stack += [(x, 0), (x, ch - 1)]
        visited.add((x, 0))
        visited.add((x, ch - 1))
    for y in range(1, ch - 1):
        stack += [(0, y), (cw - 1, y)]
        visited.add((0, y))
        visited.add((cw - 1, y))

    bg = set()
    while stack:
        x, y = stack.pop()
        r, g, b, a = cpix[x, y]
        if (r > 230 and g > 230 and b > 230) or a < 50:
            bg.add((x, y))
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < cw and 0 <= ny < ch and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    stack.append((nx, ny))

    for (x, y) in bg:
        cpix[x, y] = (0, 0, 0, 0)

    return cell


def sweep_ground_shadow(cell):
    """Erase a soft drop shadow that remove_white_bg() cannot reach.

    Both walk sheets render a soft gray shadow under the feet, down to ~150 on
    each channel — well below remove_white_bg's ">230" test, so the flood fill
    correctly leaves it (it fails the whiteness test) even though it isn't part
    of the character either. It can't be fixed by connected-component analysis
    either: the shadow touches the sandal directly at the ground-contact point,
    so it is the SAME connected blob as the character, not a separate island.

    Exploit the geometry instead of color alone. A cast shadow always sits
    strictly below the feet, in every column of the image. So sweep each
    column bottom-up: while a pixel is neutral-toned and reasonably light,
    treat it as shadow and erase it; the moment a column hits a pixel with real
    color saturation or darkness — the cel-shade outline, skin, cloth, the
    sandal itself — stop. Everything above that point in the column is left
    untouched, so a kurta fold-shadow (which sits behind and above the feet)
    is never reached: the sweep in its column already stopped at the sandal.

    Verified against real art, not just reasoned about: on the boy's and
    girl's 8-frame walk sheets this clears the shadow blob in every frame
    (confirmed on both a magenta and a cyan background, so it isn't a
    translucency artifact) while the kurta/dhoti's own fold shading — which
    reaches as dark as near-black at outlines, unlike the shadow's ~150 floor —
    is untouched.
    """
    cw, ch = cell.size
    cpix = cell.load()
    for x in range(cw):
        for y in range(ch - 1, -1, -1):
            r, g, b, a = cpix[x, y]
            if a < 10:
                continue  # already transparent; keep sweeping upward
            spread = max(r, g, b) - min(r, g, b)
            if r > 150 and spread < 14:
                cpix[x, y] = (r, g, b, 0)
                continue
            break  # real content: stop sweeping this column
    return cell


def tight_crop(cell):
    """Crop to non-transparent pixels only."""
    bbox = cell.getbbox()          # Pillow built-in: (left,top,right,bottom) of non-zero alpha
    if bbox is None:
        return None
    return cell.crop(bbox)


def place_on_canvas(char_img):
    """Place character so feet align to BASELINE_Y, centered horizontally."""
    char_w, char_h = char_img.size

    # Scale down if character is taller than canvas allows
    max_h = BASELINE_Y          # maximum character height before feet hit baseline
    max_w = FRAME_W - 4         # 2px margin each side
    scale = min(max_h / char_h, max_w / char_w, 1.0)   # never enlarge
    if scale < 1.0:
        new_w = max(1, int(char_w * scale))
        new_h = max(1, int(char_h * scale))
        char_img = char_img.resize((new_w, new_h), Image.LANCZOS)
        char_w, char_h = new_w, new_h

    frame = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    ox = (FRAME_W - char_w) // 2
    oy = BASELINE_Y - char_h
    frame.paste(char_img, (ox, oy), char_img)
    return frame


def process_sprite(filename, rows, cols):
    path = os.path.join(SPRITES_DIR, filename)
    if not os.path.exists(path):
        print(f"  MISSING: {filename} — skipping.")
        return

    img = Image.open(path).convert("RGBA")
    W, H = img.size

    # This script overwrites in place and is NOT idempotent: re-running it on an
    # already-normalized strip would re-slice the finished 128px frames by the
    # SOURCE grid and destroy the art (player_boy_idle_*.png is the worst case —
    # a (2,2) grid applied to a finished 1x4 strip). A processed strip is exactly
    # FRAME_H tall and a whole number of square frames wide, so detect that and
    # skip. This is what makes it safe to run after adding only new files.
    if H == FRAME_H and W % FRAME_H == 0:
        print(f"  SKIP: {filename} is already normalized "
              f"({W // FRAME_H} frames, {W}x{H}).")
        return

    cell_w = W // cols
    cell_h = H // rows

    frames = []
    for r in range(rows):
        for c in range(cols):
            left   = c * cell_w
            top    = r * cell_h
            cell   = img.crop((left, top, left + cell_w, top + cell_h)).copy()
            cell   = remove_white_bg(cell)
            cell   = sweep_ground_shadow(cell)
            cell   = tight_crop(cell)
            if cell is None:
                print(f"  WARN: empty cell at row={r} col={c} in {filename}")
                continue
            frames.append(place_on_canvas(cell))

    if not frames:
        print(f"  ERROR: no frames extracted from {filename}")
        return

    # Save as a single horizontal strip
    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f, (i * FRAME_W, 0), f)

    strip.save(path, "PNG")
    print(f"  OK: {filename}  ({len(frames)} frames, {strip.width}x{strip.height})")


if __name__ == "__main__":
    print("=== Preparing player boy sprites ===")
    for filename, (rows, cols) in SPRITE_GRID.items():
        process_sprite(filename, rows, cols)
    print("=== Done ===")
