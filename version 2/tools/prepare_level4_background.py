"""
prepare_level4_background.py — Slide the Kailash picture down so its summit can be seen.

    D:/Installation/Anaconda/python.exe tools/prepare_level4_background.py

LevelScene draws the world 80px up and lays the 48px clock bar over what is left,
so the top 128px of any level background (at 1920x1080) is never seen. The
generated picture puts the summit of Kailash at y 135 — inside that strip, so a
devotee standing on it, and the gate that appears there, would be hidden.

This moves the whole picture down by SHIFT and fills the gap with the picture's
own topmost sky, carried upward. Nearly all of the new sky is in the hidden strip.
The price is the bottom SHIFT rows: foreground snow and the near bend of the
frozen stream. With SHIFT = 150 the level's floor line (y 1050) falls on the
stream's surface at the foot of the stream block.

Source: assets/images/backgrounds/_source/level4_background.jpg (as generated).
Needs Pillow, which the game's venv does not have.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "images", "backgrounds", "_source", "level4_background.jpg")
OUT = os.path.join(ROOT, "assets", "images", "backgrounds", "level4_background.png")
SHIFT = 150            # in 1920x1080 game pixels
SKY_ROWS = 2           # the top rows, repeated upward: sky that meets the picture with no seam


def main():
    src = Image.open(SRC).convert("RGB")
    w, h = src.size
    shift = round(SHIFT * h / 1080)
    out = Image.new("RGB", (w, h))
    out.paste(src.crop((0, 0, w, SKY_ROWS)).resize((w, shift), Image.BICUBIC), (0, 0))
    out.paste(src.crop((0, 0, w, h - shift)), (0, shift))
    out.save(OUT)
    print(f"{OUT}: {w}x{h}, moved down {shift} source rows ({SHIFT} game pixels)")


if __name__ == "__main__":
    main()
