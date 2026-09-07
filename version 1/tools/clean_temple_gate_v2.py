"""
clean_temple_gate_v2.py — Aggressively remove ALL non-temple pixels from the edges.

The previous pass missed the checkered transparency pattern because those pixels
are medium-gray (brightness ~128-204), not dark. This script:
  1. Works from the ORIGINAL backup image (before any prior cleaning).
  2. In the left/right edge zones, keeps ONLY bright warm-toned marble pixels.
  3. Everything else in those zones is made fully transparent.
  4. Also cleans any semi-transparent artifact pixels across the full image.
"""
import os
from PIL import Image

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "images", "items")
BACKUP = os.path.join(ASSETS_DIR, "temple_gate_original_backup.png")
OUTPUT = os.path.join(ASSETS_DIR, "temple_gate.png")


def clean_image_aggressive(path, out_path):
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    w, h = img.size

    # Edge zones: the left and right 28% of the image
    edge_left = int(w * 0.28)
    edge_right = w - int(w * 0.28)

    cleaned = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]

            # Skip already transparent
            if a == 0:
                continue

            brightness = (r + g + b) / 3.0

            # ── FULL IMAGE: remove any semi-transparent dark pixel ──
            if a < 220 and brightness < 120:
                pixels[x, y] = (0, 0, 0, 0)
                cleaned += 1
                continue

            # ── EDGE ZONES: aggressive removal ──
            if x < edge_left or x > edge_right:
                # Keep only pixels that look like bright warm marble:
                #   - High brightness (> 180)
                #   - Warm tone: red channel > blue channel
                # Everything else (grays, darks, checkered pattern) gets removed.
                is_marble = (brightness > 180 and r > b - 10)

                if not is_marble:
                    pixels[x, y] = (0, 0, 0, 0)
                    cleaned += 1
                    continue

                # Even for "marble-like" pixels in edge zones, check if they're isolated
                # (surrounded mostly by transparent pixels — likely an artifact)
                transparent_neighbors = 0
                total_neighbors = 0
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            total_neighbors += 1
                            if pixels[nx, ny][3] < 50:
                                transparent_neighbors += 1
                if total_neighbors > 0 and transparent_neighbors / total_neighbors > 0.6:
                    pixels[x, y] = (0, 0, 0, 0)
                    cleaned += 1

    img.save(out_path, "PNG")
    print(f"[CleanV2] Removed {cleaned} artifact pixels.")
    print(f"[CleanV2] Saved to: {out_path}")


if __name__ == "__main__":
    if os.path.exists(BACKUP):
        print(f"[CleanV2] Working from original backup: {BACKUP}")
        clean_image_aggressive(BACKUP, OUTPUT)
    else:
        print(f"[CleanV2] ERROR: No backup found at {BACKUP}. Cannot proceed.")
    print("[CleanV2] Done!")
