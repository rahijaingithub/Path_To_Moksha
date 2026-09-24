"""
sprite_utils.py — Sprite helpers shared by more than one scene.
"""
import pygame


def extract_bow_frames(bow_strip, standing_height):
    """Cut the bowing sheet into poses and scale them together.

    The bowing art is not a clean strip: poses are found as separate alpha
    islands (2D mask extraction — slicing by rows made one pose's feet bleed into
    the next), sorted top row first, then left to right. Every pose is scaled by
    the same ratio, chosen so the FIRST (standing) pose is `standing_height` px
    tall, so the bow shrinks naturally instead of each pose filling the frame.
    Returns [] when there is no strip.
    """
    if not bow_strip:
        return []
    mask = pygame.mask.from_surface(bow_strip, threshold=8)
    island_rects = mask.get_bounding_rects()

    # Filter out tiny 1x1 noise dots and sort poses top-to-bottom, left-to-right
    valid_rects = [r for r in island_rects if r.width > 20 and r.height > 20]
    valid_rects.sort(key=lambda r: (0 if r.y < 400 else 1, r.x))

    raw_cropped = []
    standing_h = None
    for rect in valid_rects:
        cell = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cell.blit(bow_strip, (0, 0), rect)
        raw_cropped.append(cell)
        if standing_h is None:
            standing_h = rect.height  # Pose 0 standing height reference (~377px)

    scale_ratio = standing_height / standing_h if (standing_h and standing_h > 0) else 0.40

    frames = []
    for cropped in raw_cropped:
        tw = max(10, int(cropped.get_width() * scale_ratio))
        th = max(10, int(cropped.get_height() * scale_ratio))
        frames.append(pygame.transform.smoothscale(cropped, (tw, th)))
    return frames
