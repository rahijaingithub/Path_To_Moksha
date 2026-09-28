"""
prepare_bhagwan_images.py
Build the in-game Bhagwan images from the designer's originals (kept in _source/).

    items/mahavir_bhagwan.png   Level 3 shikhar reveal — square (the slot is 150x150)
    transitions/mahavir.png     Level 3 -> 4 transition — 3:4 portrait (shown 360x480)
    transitions/adinath.png     Level 4 -> Victory transition — 3:4 portrait (shown 360x480)

Each original carries a generator watermark in its bottom-right corner; every
output either crops it away or covers it with the marble beside it. Coordinates
were measured on the originals (see DECISION_LOG Phase 9c/9d).

Usage:
    python prepare_bhagwan_images.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(ROOT, "assets", "images")


def cover(img, box, dx):
    """Paste the strip `dx` px to the left of `box` over `box` (hides a watermark)."""
    x0, y0, x1, y1 = box
    img.paste(img.crop((x0 - dx, y0, x1 - dx, y1)), (x0, y0))


def main():
    # Mahavir Bhagwan (lion lanchhan). Watermark ~x 815-868, y 1118-1168.
    src = Image.open(os.path.join(IMAGES, "items", "_source", "mahavir_bhagwan_original.jpg")).convert("RGB")

    square = src.copy()
    cover(square, (812, 1110, 869, 1146), 57)
    side = square.width           # full width, bottom at the pedestal's lower edge (1146):
    square = square.crop((0, 1146 - side, side, 1146))   # whole figure + lion plaque
    square.resize((600, 600), Image.LANCZOS).save(os.path.join(IMAGES, "items", "mahavir_bhagwan.png"))

    portrait = src.copy()
    cover(portrait, (812, 1110, 869, 1170), 57)
    portrait = portrait.crop((0, 0, 896, 1195))           # 3:4, the whole image
    portrait.resize((720, 960), Image.LANCZOS).save(os.path.join(IMAGES, "transitions", "mahavir.png"))

    # Moolnayak Adinath Bhagwan (bull lanchhan). Watermark ~x 863-913, y 1030-1080:
    # a 3:4 crop ending at x 863 leaves it out entirely.
    adi = Image.open(os.path.join(IMAGES, "transitions", "_source", "adinath_original.jpg")).convert("RGB")
    adi = adi.crop((29, 0, 863, 1112))
    adi.resize((720, 960), Image.LANCZOS).save(os.path.join(IMAGES, "transitions", "adinath.png"))
    print("OK: items/mahavir_bhagwan.png, transitions/mahavir.png, transitions/adinath.png")


if __name__ == "__main__":
    main()
