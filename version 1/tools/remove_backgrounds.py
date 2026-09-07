"""
remove_backgrounds.py — Utility script for The Path to Moksha.
Removes the solid background colour from all item icon PNG sprites
so they blend seamlessly with the game's level backgrounds.

HOW IT WORKS:
- Detects the background color by sampling the four corner pixels
- Flood-fills from all corners to find connected background pixels
- Replaces all background-colored pixels with transparency (alpha=0)
- Saves the result back over the original PNG

USAGE:
  & D:/Installation/Anaconda/python.exe remove_backgrounds.py

The script processes EVERY .png file in the target directory.
Already-transparent images are skipped safely.
Originals are backed up to items/backup/ before any modification.
"""

import os
import shutil
from PIL import Image

# ── Configuration ─────────────────────────────────────────────────────────────
# Repo root is the parent of tools/ — same idiom as clean_temple_gate.py.
TARGET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "images", "items"
)

# Color tolerance: pixels within this Euclidean distance from the corner
# color will be treated as background. Increase (e.g. 40) for messy edges.
TOLERANCE = 30

# Files that should NOT have their background removed (already transparent or
# are full-scene images where we want to keep the original)
SKIP_FILES = {
    "acharya_portrait.png",
    "temple_gate_original_backup.png",
}
# ─────────────────────────────────────────────────────────────────────────────


def color_distance(c1, c2):
    """Euclidean distance between two RGB tuples."""
    return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5


def flood_fill_background(img_rgba, start_points, bg_color, tolerance):
    """
    Flood fill from start_points and mark all connected bg-color pixels.
    Returns a set of (x, y) pixel positions that are part of the background.
    """
    width, height = img_rgba.size
    pixels = img_rgba.load()
    visited = set()
    queue = list(start_points)
    bg_pixels = set()

    while queue:
        x, y = queue.pop()
        if (x, y) in visited:
            continue
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        visited.add((x, y))

        px = pixels[x, y]
        if color_distance(px[:3], bg_color) <= tolerance:
            bg_pixels.add((x, y))
            queue.append((x+1, y))
            queue.append((x-1, y))
            queue.append((x, y+1))
            queue.append((x, y-1))

    return bg_pixels


def remove_background(image_path, tolerance=TOLERANCE):
    """Remove the background from a single PNG file. Returns True if modified."""
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    pixels = img.load()

    # ── Specialized logic for monk_sprite.png (Dynamic Box crop + Grid Transparentizer) ──
    if os.path.basename(image_path) == "monk_sprite.png":
        # 1. Find the non-white/non-grey bounding box dynamically
        non_white_pixels = []
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                is_bg_shade = (max(r, g, b) - min(r, g, b) < 22) and (max(r, g, b) > 40)
                if not is_bg_shade and a > 50:
                    non_white_pixels.append((x, y))
        
        if non_white_pixels:
            xs = [p[0] for p in non_white_pixels]
            ys = [p[1] for p in non_white_pixels]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # Add small padding to avoid cutting edge pixels
            min_x = max(0, min_x - 6)
            max_x = min(width - 1, max_x + 6)
            min_y = max(0, min_y - 6)
            max_y = min(height - 1, max_y + 6)
            
            box = (min_x, min_y, max_x + 1, max_y + 1)
            img = img.crop(box)
            width, height = img.size
            pixels = img.load()
            print(f"  [PROC] monk_sprite.png — dynamically cropped to box {box} (size {width}x{height})")
            
        # 2. Flood fill from the outer edges of the cropped monk sprite
        visited = set()
        queue = []
        for x in range(width):
            queue.append((x, 0))
            queue.append((x, height - 1))
        for y in range(1, height - 1):
            queue.append((0, y))
            queue.append((width - 1, y))
            
        bg_pixels = set()
        while queue:
            x, y = queue.pop(0)
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            r, g, b, a = pixels[x, y]
            if a < 50:
                bg_pixels.add((x, y))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        queue.append((nx, ny))
                continue
                
            is_low_sat = max(r, g, b) - min(r, g, b) < 25
            is_bg_color = is_low_sat and (max(r, g, b) > 35)
            if is_bg_color:
                bg_pixels.add((x, y))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        queue.append((nx, ny))
                        
        for y in range(height):
            for x in range(width):
                if (x, y) in bg_pixels:
                    pixels[x, y] = (0, 0, 0, 0)
                    
        img.save(image_path, "PNG")
        return True

    # ── Standard logic for other item PNG sprites ──
    # Sample all four corners to determine background color candidates
    corners = [
        pixels[0, 0],
        pixels[width-1, 0],
        pixels[0, height-1],
        pixels[width-1, height-1],
    ]

    # Skip images that already have transparent corners (already done)
    if all(c[3] < 200 for c in corners):
        print(f"  [SKIP] Already transparent: {os.path.basename(image_path)}")
        return False

    # Use the most common corner color as the background
    rgb_corners = [c[:3] for c in corners]
    bg_color = max(set(rgb_corners), key=rgb_corners.count)

    print(f"  [PROC] {os.path.basename(image_path)} — detected background: rgb{bg_color}")

    # Flood fill from all 4 corners to find background region
    start_points = [
        (0, 0), (width-1, 0), (0, height-1), (width-1, height-1)
    ]
    bg_pixels = flood_fill_background(img, start_points, bg_color, tolerance)

    # Make background pixels transparent
    for (x, y) in bg_pixels:
        r, g, b, a = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)

    img.save(image_path, "PNG")
    return True


def main():
    print(f"\n===  Background Removal Utility — Path to Moksha")
    print(f"    Target folder: {TARGET_DIR}\n")

    if not os.path.isdir(TARGET_DIR):
        print(f"ERROR: Target directory not found:\n  {TARGET_DIR}")
        return

    # Create backup folder
    backup_dir = os.path.join(TARGET_DIR, "backup_pre_bg_removal")
    os.makedirs(backup_dir, exist_ok=True)

    png_files = [f for f in os.listdir(TARGET_DIR)
                 if f.lower().endswith(".png") and f not in SKIP_FILES
                 and not os.path.isdir(os.path.join(TARGET_DIR, f))]

    if not png_files:
        print("No PNG files found to process.")
        return

    modified = 0
    skipped = 0

    for filename in sorted(png_files):
        filepath = os.path.join(TARGET_DIR, filename)

        # Back up original
        backup_path = os.path.join(backup_dir, filename)
        if not os.path.exists(backup_path):
            shutil.copy2(filepath, backup_path)

        try:
            if remove_background(filepath):
                modified += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  [ERROR] {filename}: {e}")
            skipped += 1

    print(f"\n[DONE]")
    print(f"    Modified : {modified} image(s)")
    print(f"    Skipped  : {skipped} image(s) (already transparent)")
    print(f"    Backups  : {backup_dir}")
    print(f"\n    You can restore any original from the backup folder above.\n")


if __name__ == "__main__":
    main()
