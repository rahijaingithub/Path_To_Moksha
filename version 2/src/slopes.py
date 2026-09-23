"""
slopes.py — One-way sloped walking surfaces (the Level 3 lotus petals).

Pure geometry, no pygame: the landing rule is unit-tested on a headless CI worker
that has no pygame installed (see tests/test_level3_layout.py).

A slope is a polyline the devotee can stand and walk on. It is ONE-WAY: you land
on it from above and stay on it while walking, but you pass through it when
rising (jumping up from below) or when walking into it from the side. Rect
platforms stay fully solid; slopes never block anything.
"""

# How far (px at 60fps) the feet may be from the line and still count as on it.
# Walking at PLAYER_SPEED over the steepest Level 3 petal moves the line ~3px a
# frame, so 16 keeps the devotee glued going up or downhill without catching a
# player who is merely passing close underneath.
SLOPE_REACH = 16


class Slope:
    """A walkable polyline; points are (x, y) in world space, left to right."""

    def __init__(self, points):
        self.points = [(float(x), float(y)) for x, y in points]
        if len(self.points) < 2:
            raise ValueError("A slope needs at least two points")
        for (x0, _), (x1, _) in zip(self.points, self.points[1:]):
            if x1 <= x0:
                raise ValueError("Slope points must run strictly left to right")
        self.left = self.points[0][0]
        self.right = self.points[-1][0]

    def y_at(self, x):
        """Surface height at x, or None when x is off the end of the slope."""
        if x < self.left or x > self.right:
            return None
        for (x0, y0), (x1, y1) in zip(self.points, self.points[1:]):
            if x0 <= x <= x1:
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return None


def find_slope_contact(slopes, center_x, prev_bottom, bottom, vy, current, reach):
    """Which slope the feet rest on this frame, as (slope, surface_y), or (None, None).

    center_x    -- the devotee's horizontal centre (feet are sampled there)
    prev_bottom -- feet y before this frame's vertical move
    bottom      -- feet y after it
    current     -- the slope stood on last frame, or None
    reach       -- SLOPE_REACH scaled by dt * 60 for frame-rate independence

    Rising (vy < 0) never lands, so a jump passes up through a petal. Otherwise
    the feet land if they were at or above the line last frame (within reach)
    and are at or below it now; and they stay stuck to the slope they already
    stand on while within reach, which is what carries them downhill instead of
    skipping off the line every frame.
    """
    if vy < 0:
        return None, None
    best, best_y = None, None
    for slope in slopes:
        surface_y = slope.y_at(center_x)
        if surface_y is None:
            continue
        if slope is current:
            touching = abs(bottom - surface_y) <= reach
        else:
            touching = prev_bottom <= surface_y + reach and bottom >= surface_y
        if touching and (best_y is None or abs(bottom - surface_y) < abs(bottom - best_y)):
            best, best_y = slope, surface_y
    return best, best_y
