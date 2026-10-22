"""
prepare_rescue_sprites.py
Turn the designer's lost-man sheets into the game's strip format (Epic G5).

Input : assets/images/sprites/_source/lost_man_walk_right.jpg  — 6 frames, side
        view facing right, on white.
        assets/images/sprites/_source/lost_man_confused.jpg    — 4 frames, front
        view, hand rising to the head and down again, on white.
        assets/images/sprites/_source/injured_man_limp_walk_rightV2.jpg — 6 frames,
        side view, limping, on white but with a frame border drawn per cell.
Output: assets/images/sprites/lost_man_walk_right.png
        assets/images/sprites/lost_man_confused.png
        assets/images/sprites/injured_man_limp_walk_right.png

Three things have to be true of the result, and none of them are true of the
sheets as supplied:

1. **Square frames.** RescueNPC._walk_image derives the frame count from
   width // height, so a cell that is not square silently shifts every frame
   after the first. The confused sheet is 2064x512 — 4 cells of 516, not 512.
2. **One baseline.** The man must stand on the same line in every frame of both
   strips, or he bobs when the animation plays and jumps when the game switches
   between the two strips.
3. **One size, across both strips.** The game scales each strip to the same
   on-screen height, so the man must occupy the same fraction of his cell in
   both — otherwise he changes size the moment he stops to wonder.

So each frame is keyed off its white background, trimmed to the man, then placed
on a square canvas at a fixed height and baseline. JPEG ringing means the white
is not pure, hence the tolerance; nothing on the man is near-white (red sweater,
blue jeans, navy or brown shoes), so a generous threshold is safe.

Usage (PIL is not in the game venv; the Anaconda interpreter has it):
    D:/Installation/Anaconda/python.exe tools/prepare_rescue_sprites.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES_DIR = os.path.join(ROOT, "assets", "images", "sprites")
SOURCE_DIR = os.path.join(SPRITES_DIR, "_source")

# (source file, output file, frame count, border inset)
# `inset` steps past a frame border drawn into the sheet: the white key cannot
# remove a black line, and a flood fill stops dead at one.
SHEETS = [
    ("lost_man_walk_right.jpg", "lost_man_walk_right.png", 6, 0),
    ("lost_man_confused.jpg", "lost_man_confused.png", 4, 0),
    ("injured_man_limp_walk_rightV2.jpg", "injured_man_limp_walk_right.png", 6, 22),
]

WHITE_THRESHOLD = 236     # >= this on every channel counts as background
ALPHA_FLOOR = 24          # below this a pixel is background, not part of the figure
CELL = 512                # square cell side in the finished strip
MAN_HEIGHT = int(CELL * 0.88)   # his height within the cell, the same in both strips
BASELINE = int(CELL * 0.97)     # where his feet sit, measured from the cell top


def key_out_white(img):
    """White background to transparency, with a tolerance for JPEG ringing."""
    img = img.convert("RGBA")
    out = []
    for r, g, b, a in img.getdata():
        if r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD:
            out.append((r, g, b, 0))
        else:
            out.append((r, g, b, a))
    img.putdata(out)
    return img


def frame_cells(sheet, frames, inset):
    """Slice by frame count, not by height — the cells are not square on disk."""
    width = sheet.width // frames
    return [sheet.crop((i * width + inset, inset,
                        (i + 1) * width - inset, sheet.height - inset))
            for i in range(frames)]


def keep_the_man(cell):
    """Drop everything but the figure: border fragments, specks, stray marks.

    A frame border drawn into the sheet does not always sit on the mathematical
    cell boundary, so insetting alone leaves slivers of it behind — and a sliver
    survives `getbbox`, which then reports almost the whole cell and throws the
    centring and the scale out. Islands smaller than a tenth of the largest are
    discarded; a 3px-wide border line is well under one percent of the man, while
    a limb that anti-aliasing has separated is well over a tenth.
    """
    px = cell.load()
    w, h = cell.size
    seen = [[False] * w for _ in range(h)]
    islands = []
    for sy in range(h):
        for sx in range(w):
            if seen[sy][sx] or px[sx, sy][3] <= ALPHA_FLOOR:
                continue
            stack, pixels = [(sx, sy)], []
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                pixels.append((x, y))
                for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] \
                            and px[nx, ny][3] > ALPHA_FLOOR:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            islands.append(pixels)

    if not islands:
        return cell
    biggest = max(len(i) for i in islands)
    for pixels in islands:
        if len(pixels) < biggest * 0.10:
            for x, y in pixels:
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, 0)
    return cell


def build_strip(path, frames, inset=0):
    sheet = key_out_white(Image.open(path))
    cells = frame_cells(sheet, frames, inset)

    trimmed = []
    for cell in cells:
        cell = keep_the_man(cell)
        box = cell.getbbox()          # the man, with everything else now transparent
        if box is None:
            raise SystemExit(f"{os.path.basename(path)}: a frame is empty after keying")
        trimmed.append(cell.crop(box))

    # One scale for the whole strip, from the tallest pose, so the frames that
    # reach higher (a raised arm) do not shrink the man relative to the others.
    tallest = max(c.height for c in trimmed)
    scale = MAN_HEIGHT / tallest

    strip = Image.new("RGBA", (CELL * frames, CELL), (0, 0, 0, 0))
    for i, cell in enumerate(trimmed):
        w = max(1, round(cell.width * scale))
        h = max(1, round(cell.height * scale))
        resized = cell.resize((w, h), Image.LANCZOS)
        x = i * CELL + (CELL - w) // 2          # centred across the cell
        y = BASELINE - h                        # and standing on the baseline
        strip.paste(resized, (x, y), resized)
    return strip


def main():
    for source, output, frames, inset in SHEETS:
        src_path = os.path.join(SOURCE_DIR, source)
        if not os.path.exists(src_path):
            raise SystemExit(f"missing source: {src_path}")
        strip = build_strip(src_path, frames, inset)
        out_path = os.path.join(SPRITES_DIR, output)
        strip.save(out_path)
        print(f"{source} -> {output}  {strip.width}x{strip.height}  ({frames} frames)")


if __name__ == "__main__":
    main()
