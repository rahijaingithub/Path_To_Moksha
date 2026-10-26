"""
prepare_bonus_background.py
Turn the designer's two bonus-level sheets into game assets (Epic G5).

Input : assets/images/backgrounds/_source/Toronto Background.jpg
        The street the Karuna bonus level is set on. The generator drew the
        coordinates from the prompt into the picture as chart axes — numbers down
        the left and along the bottom — so the artwork is cropped out of the plot
        area before it is scaled — including the row of tick marks just above
        the numbers, which otherwise survives along the bottom edge.
        assets/images/items/_source/Hospital BG.jpg
        The hospital entrance, front elevation on white, to be laid over the
        hospital in the street.
Output: assets/images/backgrounds/bonus_background.png   (1920x1080)
        assets/images/items/hospital_gate.png            (keyed, trimmed)

The street is squeezed about 3% horizontally to reach 16:9 rather than cropped,
which would have cost either the hospital on the left or the temple on the right.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKGROUNDS = os.path.join(ROOT, "assets", "images", "backgrounds")
ITEMS = os.path.join(ROOT, "assets", "images", "items")

# The plot area inside the source, measured off the drawn axes: the numbers down
# the left end by x=55, and the artwork's road ends at y=717 before the bottom row
# of numbers.
STREET_CROP = (55, 0, 1376, 712)      # 713-717 is the axis tick row
LOGICAL = (1920, 1080)

WHITE_THRESHOLD = 236


def key_out_white(img):
    img = img.convert("RGBA")
    img.putdata([(r, g, b, 0) if r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD
                 and b >= WHITE_THRESHOLD else (r, g, b, a)
                 for r, g, b, a in img.getdata()])
    return img


def build_street():
    src = Image.open(os.path.join(BACKGROUNDS, "_source", "Toronto Background.jpg"))
    art = src.convert("RGB").crop(STREET_CROP)
    out = art.resize(LOGICAL, Image.LANCZOS)
    path = os.path.join(BACKGROUNDS, "bonus_background.png")
    out.save(path)
    print(f"street  -> {os.path.basename(path)}  {out.width}x{out.height}")


def build_hospital():
    src = Image.open(os.path.join(ITEMS, "_source", "Hospital BG.jpg"))
    keyed = key_out_white(src)
    box = keyed.getbbox()
    if box is None:
        raise SystemExit("hospital sheet is empty after keying")
    out = keyed.crop(box)
    path = os.path.join(ITEMS, "hospital_gate.png")
    out.save(path)
    print(f"hospital-> {os.path.basename(path)}  {out.width}x{out.height}")


def main():
    build_street()
    build_hospital()


if __name__ == "__main__":
    main()
