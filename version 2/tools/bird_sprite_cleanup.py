"""
Clean a Gemini bird sprite sheet whose background is a painted (fake) checkerboard.

Why this works: the checkerboard is NEUTRAL (black / gray, no colour), while the bird is
COLOURED (brown wings, orange breast). So we keep coloured pixels, fill holes, and redraw a
uniform dark-brown outline (the original outline is lost where it touched black squares).

Outputs (in --out folder):
  frames/bird_XX.png       every detected frame, transparent, equal size, aligned on the tail tip
  bird_fly_left.png        horizontal strip of the selected frames (facing left, as drawn)
  bird_fly_right.png       mirrored strip (facing right)
  preview.gif              animated preview of the selected cycle

Usage:
  pip install pillow numpy scipy
  python bird_sprite_cleanup.py sheet.jpg --out bird_out --pick 1,5,6,7,9,11,15,16,17,19 --fps 15
"""
import argparse, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

OUTLINE = (45, 28, 20)


def foreground_mask(rgb, chroma_min=18, light_min=112, margin=28):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(2), rgb.min(2)
    chroma = mx - mn
    magenta = (r - g > 40) & (b - g > 40)             # vignette / border tint
    warm = ((r - b) >= 8) & (g >= b - 4)                                 # bird colours are warm (brown/orange/yellow)
    fg = (((chroma >= chroma_min) & warm) | (rgb.mean(2) >= light_min)) & ~magenta
    fg = ndi.binary_opening(fg, np.ones((2, 2)))        # kill JPEG specks
    fg = ndi.binary_closing(fg, np.ones((5, 5)))        # bridge feather gaps
    fg = ndi.binary_fill_holes(fg)
    m = margin
    fg[:m] = fg[-m:] = False; fg[:, :m] = fg[:, -m:] = False   # drop tinted border
    return fg


def group_birds(mask, rgb, min_area=400, min_chroma=15):
    lab, n = ndi.label(mask)                             # drop small specks before grouping
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    mask = np.isin(lab, 1 + np.flatnonzero(sizes >= 150))
    # join nearby pieces (separate feather tips) into one bird per frame
    grouped, n = ndi.label(ndi.binary_dilation(mask, np.ones((15, 15))))
    birds = []
    for i in range(1, n + 1):
        m = mask & (grouped == i)
        # keep only the bird body pieces; tinted checker squares are small loose blobs
        lab, k = ndi.label(m)
        if k > 1:
            sizes = ndi.sum(m, lab, range(1, k + 1))
            m = np.isin(lab, 1 + np.flatnonzero(sizes >= 0.2 * sizes.max()))
        # remove thin spurs (checker edges touching the outline)
        m = ndi.binary_opening(m, np.ones((3, 3)))
        if m.sum() < min_area:
            continue
        px = rgb[m]
        if (px.max(1) - px.min(1)).mean() < min_chroma:   # grey/white blobs, e.g. the Gemini sparkle
            continue
        ys, xs = np.nonzero(m)
        birds.append(dict(mask=m, cy=ys.mean(), cx=xs.mean(), box=(ys.min(), ys.max(), xs.min(), xs.max())))
    # reading order: cluster into rows by centre y, then left to right
    birds.sort(key=lambda b: b["cy"])
    rows, cur = [], [birds[0]]
    for b in birds[1:]:
        if abs(b["cy"] - np.mean([c["cy"] for c in cur])) < 60:
            cur.append(b)
        else:
            rows.append(cur); cur = [b]
    rows.append(cur)
    return [b for row in rows for b in sorted(row, key=lambda b: b["cx"])]


def render(rgb, bird, stroke=2):
    m = bird["mask"]
    ring = ndi.binary_dilation(m, iterations=stroke) & ~m
    inner_edge = m & ~ndi.binary_erosion(m, iterations=1)   # thicken outline inward by 1 px
    full = m | ring
    out = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    out[m, :3] = rgb[m]
    out[ring | inner_edge, :3] = OUTLINE
    out[full, 3] = 255
    ys, xs = np.nonzero(full)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = out[y0:y1, x0:x1]
    # anchor = tail tip (right-most pixel); stable across wing positions
    col = full[:, x1 - 1]
    ay = int(np.nonzero(col)[0].mean()) - y0
    return Image.fromarray(crop, "RGBA"), (crop.shape[1], ay)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("--out", default="bird_out")
    ap.add_argument("--pick", default="1,5,6,7,9,11,15,16,17,18", help="1-based frame numbers for the loop")
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--pad", type=int, default=8)
    a = ap.parse_args()

    rgb = np.asarray(Image.open(a.sheet).convert("RGB")).astype(int)
    birds = group_birds(foreground_mask(rgb), rgb)
    print(f"Detected {len(birds)} frames")

    sprites = [render(rgb.astype(np.uint8), b) for b in birds]
    # common cell: align every sprite so its tail tip lands on the same point
    left = max(w for _, (w, _) in sprites)
    up = max(ay for _, (_, ay) in sprites)
    down = max(im.height - ay for im, (_, ay) in sprites)
    W, H = left + 2 * a.pad, up + down + 2 * a.pad
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    cells = []
    for i, (im, (w, ay)) in enumerate(sprites, 1):
        cell = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cell.paste(im, (a.pad + left - w, a.pad + up - ay), im)
        cell.save(os.path.join(a.out, "frames", f"bird_{i:02d}.png"))
        cells.append(cell)

    pick = [int(p) - 1 for p in a.pick.split(",") if p.strip()]
    loop = [cells[i] for i in pick if i < len(cells)]
    strip = Image.new("RGBA", (W * len(loop), H), (0, 0, 0, 0))
    for i, c in enumerate(loop):
        strip.paste(c, (i * W, 0))
    strip.save(os.path.join(a.out, "bird_fly_left.png"))
    strip.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(a.out, "bird_fly_right.png"))
    # note: mirroring the strip reverses frame order; re-order so the cycle still plays forward
    right = Image.new("RGBA", strip.size, (0, 0, 0, 0))
    for i, c in enumerate(loop):
        right.paste(c.transpose(Image.FLIP_LEFT_RIGHT), (i * W, 0))
    right.save(os.path.join(a.out, "bird_fly_right.png"))

    bg = (135, 190, 235, 255)  # sky blue preview background
    gif = [Image.alpha_composite(Image.new("RGBA", (W, H), bg), c).convert("P", palette=Image.ADAPTIVE) for c in loop]
    gif[0].save(os.path.join(a.out, "preview.gif"), save_all=True, append_images=gif[1:],
                duration=int(1000 / a.fps), loop=0, disposal=2)
    print(f"Frame size {W}x{H}; loop = frames {a.pick} ({len(loop)} frames @ {a.fps} fps)")


if __name__ == "__main__":
    main()
