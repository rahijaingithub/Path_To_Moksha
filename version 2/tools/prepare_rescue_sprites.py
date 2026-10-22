"""
prepare_rescue_sprites.py
Turn the designer's lost-man sheets into the game's strip format (Epic G5).

Input : assets/images/sprites/_source/lost_man_walk_right.jpg  — 6 frames, side
        view facing right, on white.
        assets/images/sprites/_source/lost_man_confused.jpg    — 4 frames, front
        view, hand rising to the head and down again, on white.
Output: assets/images/sprites/lost_man_walk_right.png
        assets/images/sprites/lost_man_confused.png

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

# (source file, output file, frame count)
SHEETS = [
    ("lost_man_walk_right.jpg", "lost_man_walk_right.png", 6),
    ("lost_man_confused.jpg", "lost_man_confused.png", 4),
]

WHITE_THRESHOLD = 236     # >= this on every channel counts as background
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


def frame_cells(sheet, frames):
    """Slice by frame count, not by height — the cells are not square on disk."""
    width = sheet.width // frames
    return [sheet.crop((i * width, 0, (i + 1) * width, sheet.height))
            for i in range(frames)]


def build_strip(path, frames):
    sheet = key_out_white(Image.open(path))
    cells = frame_cells(sheet, frames)

    trimmed = []
    for cell in cells:
        box = cell.getbbox()          # the man, with the background now transparent
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
    for source, output, frames in SHEETS:
        src_path = os.path.join(SOURCE_DIR, source)
        if not os.path.exists(src_path):
            raise SystemExit(f"missing source: {src_path}")
        strip = build_strip(src_path, frames)
        out_path = os.path.join(SPRITES_DIR, output)
        strip.save(out_path)
        print(f"{source} -> {output}  {strip.width}x{strip.height}  ({frames} frames)")


if __name__ == "__main__":
    main()
