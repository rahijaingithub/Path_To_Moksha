"""
clean_temple_gate.py — Remove dark mosaic artifacts from the temple gate PNG edges.

Strategy:
  1. Scan every pixel in the image.
  2. Any pixel that is very dark (low brightness) AND semi-transparent
     is likely a mosaic remnant from background removal.
  3. Make those pixels fully transparent (alpha=0).
  4. Also clean up any fully opaque near-black pixels on the far-left
     and far-right edge strips (the red-circled zones in the user's screenshot).
"""
import os
import sys
from PIL import Image

# Paths
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "images", "items")
INPUT  = os.path.join(ASSETS_DIR, "temple_gate.png")
BACKUP = os.path.join(ASSETS_DIR, "temple_gate_original_backup.png")
OUTPUT = os.path.join(ASSETS_DIR, "temple_gate.png")

def clean_image(path, out_path, brightness_threshold=50, edge_fraction=0.20):
    """
    Remove dark mosaic artifacts from the PNG.
    
    - brightness_threshold: pixels with R+G+B < this * 3 are considered dark
    - edge_fraction: the left/right edge strips (as fraction of width) 
      where even opaque dark pixels are removed
    """
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    
    edge_left  = int(w * edge_fraction)
    edge_right = w - int(w * edge_fraction)
    
    cleaned_count = 0
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            
            # Skip already transparent pixels
            if a == 0:
                continue
            
            brightness = (r + g + b) / 3.0
            
            # Strategy 1: Any semi-transparent dark pixel anywhere → fully transparent
            if a < 200 and brightness < brightness_threshold:
                pixels[x, y] = (0, 0, 0, 0)
                cleaned_count += 1
                continue
            
            # Strategy 2: In the far-left and far-right edge strips,
            # remove dark pixels even if they are opaque (the mosaic zones)
            if (x < edge_left or x > edge_right):
                if brightness < brightness_threshold:
                    pixels[x, y] = (0, 0, 0, 0)
                    cleaned_count += 1
                    continue
                    
                # Also clean up any checkered pattern artifacts (alternating dark/transparent)
                # Check if this pixel is isolated (surrounded mostly by transparent pixels)
                transparent_neighbors = 0
                total_neighbors = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            total_neighbors += 1
                            if pixels[nx, ny][3] < 30:
                                transparent_neighbors += 1
                # If more than half the neighbors are transparent, this is likely an artifact
                if total_neighbors > 0 and transparent_neighbors / total_neighbors > 0.5:
                    if brightness < 100:  # slightly higher threshold for isolated pixels
                        pixels[x, y] = (0, 0, 0, 0)
                        cleaned_count += 1
    
    img.save(out_path, "PNG")
    print(f"[Clean] Removed {cleaned_count} mosaic artifact pixels.")
    print(f"[Clean] Saved cleaned image to: {out_path}")
    return cleaned_count


if __name__ == "__main__":
    print(f"[Clean] Input:  {INPUT}")
    print(f"[Clean] Backup: {BACKUP}")
    
    # Create backup of original
    if not os.path.exists(BACKUP):
        img = Image.open(INPUT)
        img.save(BACKUP, "PNG")
        print(f"[Clean] Backup created: {BACKUP}")
    else:
        print(f"[Clean] Backup already exists, skipping.")
    
    # Clean and overwrite
    clean_image(INPUT, OUTPUT)
    print("[Clean] Done!")
