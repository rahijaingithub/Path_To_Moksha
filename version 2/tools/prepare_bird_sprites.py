"""
prepare_bird_sprites.py
Turn the cleaned bird flight strip into the game's strip format.

Input : assets/images/sprites/_source/bird_fly_left.png — 10 frames, facing left,
        produced from _source/bird_sheet.jpg by tools/bird_sprite_cleanup.py
        (frames 1,5,6,7,9,11,15,16,17,19 of the sheet; every frame aligned on
        the tail tip, 132x211 each).
Output: assets/images/sprites/bird_fly_left.png and bird_fly_right.png.

Every game strip has SQUARE frames — level_scene.strip_frame_count() derives the
frame count from width / height. So each cell is centred on a square canvas as
tall as the source cell; the tail-tip alignment between frames is kept because
every cell moves by the same offset. The right-facing strip mirrors each FRAME,
not the whole strip (which would also reverse the order and fly backwards).

Usage:
    python prepare_bird_sprites.py
"""
import os
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES_DIR = os.path.join(ROOT, "assets", "images", "sprites")
SOURCE = os.path.join(SPRITES_DIR, "_source", "bird_fly_left.png")
FRAMES = 10


def main():
    src = Image.open(SOURCE).convert("RGBA")
    cell_w, side = src.width // FRAMES, src.height
    left = Image.new("RGBA", (side * FRAMES, side), (0, 0, 0, 0))
    right = left.copy()
    for i in range(FRAMES):
        cell = src.crop((i * cell_w, 0, (i + 1) * cell_w, side))
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(cell, ((side - cell_w) // 2, 0))
        left.paste(square, (i * side, 0))
        right.paste(ImageOps.mirror(square), (i * side, 0))
    left.save(os.path.join(SPRITES_DIR, "bird_fly_left.png"))
    right.save(os.path.join(SPRITES_DIR, "bird_fly_right.png"))
    print(f"OK: bird_fly_left/right.png ({FRAMES} frames, {left.width}x{left.height})")


if __name__ == "__main__":
    main()
