"""
draw_bird_sprites.py — draw the Level 3 bird (a house sparrow) from code alone.

Why a script: the first bird was a Gemini sheet that followed a third-party robin
sprite sheet nobody could trace, so its licence could not be cleared (backlog BL3).
This bird has no source to clear: every shape and colour is written below, with no
reference image, no image generator and no downloaded art. Re-running the script
reproduces the strips exactly.

Output: assets/images/sprites/bird_fly_left.png and bird_fly_right.png — ten SQUARE
frames each (level_scene derives the frame count from width / height). Frame 3 has
the wings tucked in: bird.FOLDED_FRAME uses it while the bird falls and rests on the
lotus. The right-facing strip mirrors each FRAME, not the whole strip (which would
also reverse the order and fly backwards).

Usage:
    python draw_bird_sprites.py          (needs Pillow)
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES_DIR = os.path.join(ROOT, "assets", "images", "sprites")

SIDE, SS, FRAMES = 211, 4, 10
ANGLES = [-70, -52, -24, 0, 46, 76, 56, 26, 0, -36]     # wing angle per frame; 0 = folded

BUFF, BACK, CHESTNUT = (214, 203, 186), (139, 98, 62), (150, 84, 46)
CROWN, CHEEK, BIB = (118, 106, 98), (226, 218, 204), (38, 30, 28)
WING, WING_DARK, BAR = (128, 90, 58), (66, 47, 37), (236, 229, 214)
TAIL, BEAK, OUTLINE = (78, 57, 44), (58, 52, 50), (46, 32, 24)


def P(pts):
    return [(x * SS, y * SS) for x, y in pts]


def ellipse_pts(cx, cy, rx, ry, tilt=0, n=48):
    t = math.radians(tilt)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)))
    return out


def mask_of(pts, blur=0):
    m = Image.new("L", (SIDE * SS, SIDE * SS), 0)
    ImageDraw.Draw(m).polygon(P(pts), fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur * SS)) if blur else m


def paint(img, colour, mask, clip=None):
    if clip is not None:
        mask = ImageChops.multiply(mask, clip)
    img.paste(Image.new("RGBA", img.size, colour + (255,)), (0, 0), mask)


def feather(root, lean_deg, length, width):
    """A lens-shaped feather in wing space (x toward the tail, y up)."""
    a = math.radians(lean_deg)
    ux, uy = math.sin(a), math.cos(a)            # along the feather
    px, py = uy, -ux                             # across it
    pts = []
    for i in range(13):
        f = i / 12
        w = width * (min(1, f * 5) ** 0.5) * (max(0.0, 1 - f ** 4) ** 0.5)
        pts.append((root[0] + ux * length * f + px * w, root[1] + uy * length * f + py * w))
    for i in range(12, -1, -1):
        f = i / 12
        w = width * (min(1, f * 5) ** 0.5) * (max(0.0, 1 - f ** 4) ** 0.5)
        pts.append((root[0] + ux * length * f - px * w, root[1] + uy * length * f - py * w))
    return pts


def wing(img, shoulder, angle, far=False):
    s = math.sin(math.radians(angle))
    shade = 0.72 if far else 1.0
    col = lambda c: tuple(int(v * shade) for v in c)
    sx, sy = shoulder

    def project(pts):
        sweep = -9 * s if s < 0 else 5 * s      # tips reach forward on the downstroke
        return [(sx + x + sweep * (y / 80.0), sy - y * s) for x, y in pts]

    if abs(s) < 0.12:                            # folded against the body
        if far:
            return
        paint(img, col(WING), mask_of(ellipse_pts(sx + 26, sy + 9, 36, 11, 7)))
        for k in range(4):
            paint(img, col(WING_DARK), mask_of(ellipse_pts(sx + 34 + k * 7, sy + 11 + k, 22 - k * 3, 2.2, 8)))
        paint(img, col(BAR), mask_of(ellipse_pts(sx + 12, sy + 6, 9, 1.8, 18)))
        paint(img, col(CHESTNUT), mask_of(ellipse_pts(sx + 6, sy + 4, 11, 6, 10)))
        return

    n = 10
    for k in range(n - 1, -1, -1):               # trailing feathers first
        f = k / (n - 1)
        root = (2 + 30 * f, 4)
        lean = 8 + 58 * f
        length = 84 - 30 * f - (6 if k == 0 else 0)
        pts = project(feather(root, lean, length, 8.5))
        paint(img, col(WING_DARK), mask_of(pts))
        inner = project(feather(root, lean, length * 0.95, 6.6))
        paint(img, col(WING if k % 2 else tuple(v - 10 for v in WING)), mask_of(inner))
    # coverts over the feather roots, with the sparrow's pale wing bar
    paint(img, col(BAR), mask_of(project(ellipse_pts(20, 27, 25, 9, -24))))
    paint(img, col(CHESTNUT), mask_of(project(ellipse_pts(17, 17, 25, 12, -20))))
    paint(img, col(BACK), mask_of(project(ellipse_pts(13, 9, 19, 7, -12)), blur=0.6))


def frame(angle):
    img = Image.new("RGBA", (SIDE * SS, SIDE * SS), (0, 0, 0, 0))
    bob = -2.5 * math.sin(math.radians(angle))   # the body dips as the wings rise
    cx, cy = 100, 102 + bob
    shoulder = (88, cy - 10)

    wing(img, (shoulder[0] + 5, shoulder[1] + 1), angle * 0.9, far=True)

    # tail
    for k, (dy, c) in enumerate([(-5, TAIL), (1, tuple(v + 14 for v in TAIL)), (7, TAIL)]):
        paint(img, c, mask_of([(132, cy - 6 + k), (188, cy - 3 + dy), (190, cy + 4 + dy), (134, cy + 9)]))

    # body: buff below, brown back blended in from above
    body = mask_of(ellipse_pts(cx, cy, 45, 23, -4))
    paint(img, BUFF, body)
    paint(img, BACK, mask_of(ellipse_pts(cx + 6, cy - 16, 52, 19, -4), blur=3), clip=body)
    paint(img, (176, 163, 146), mask_of(ellipse_pts(cx, cy + 24, 44, 9, -4), blur=3), clip=body)
    for k in range(5):                           # dark streaks on the back
        paint(img, WING_DARK, mask_of(ellipse_pts(cx + 2 + k * 9, cy - 14 + k * 0.6, 7, 1.3, -6)), clip=body)

    # head
    head = mask_of(ellipse_pts(62, cy - 7, 18, 16.5, -8))
    paint(img, CHEEK, head)
    paint(img, CHESTNUT, mask_of(ellipse_pts(72, cy - 10, 13, 12, 0), blur=1.5), clip=head)
    paint(img, CROWN, mask_of(ellipse_pts(62, cy - 19, 18, 8.5, -8), blur=1.2), clip=head)
    paint(img, CHEEK, mask_of(ellipse_pts(59, cy - 3, 8.5, 6, -10), blur=1.0), clip=head)
    both = ImageChops.lighter(head, body)
    paint(img, BIB, mask_of(ellipse_pts(54, cy + 7, 9, 7, -25), blur=1.2), clip=both)
    paint(img, BIB, mask_of(ellipse_pts(53, cy - 9, 7, 2.2, -12)), clip=head)      # eye stripe
    # beak, eye
    paint(img, BEAK, mask_of([(47, cy - 12), (33, cy - 5), (47, cy - 2)]))
    paint(img, (20, 16, 16), mask_of(ellipse_pts(55, cy - 10, 3.3, 3.3)))
    paint(img, (245, 245, 240), mask_of(ellipse_pts(54.2, cy - 11, 1.0, 1.0)))

    wing(img, shoulder, angle)

    # a thin dark outline round the whole silhouette, then soften
    alpha = img.split()[3]
    ring = alpha.filter(ImageFilter.MaxFilter(2 * int(1.3 * SS) + 1))
    out = Image.new("RGBA", img.size, OUTLINE + (0,))
    out.putalpha(ring)
    out.alpha_composite(img)
    return out.resize((SIDE, SIDE), Image.LANCZOS)


def main():
    left = Image.new("RGBA", (SIDE * FRAMES, SIDE), (0, 0, 0, 0))
    right = left.copy()
    for i, angle in enumerate(ANGLES):
        cell = frame(angle)
        left.paste(cell, (i * SIDE, 0))
        right.paste(ImageOps.mirror(cell), (i * SIDE, 0))
    left.save(os.path.join(SPRITES_DIR, "bird_fly_left.png"))
    right.save(os.path.join(SPRITES_DIR, "bird_fly_right.png"))
    print("wrote bird_fly_left.png and bird_fly_right.png:", left.size)


if __name__ == "__main__":
    main()
