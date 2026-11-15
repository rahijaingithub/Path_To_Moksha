"""
crumbling.py — Level 4 ledges that give way underfoot, and come back.

Kailash's snow looks like ground and is not: a ledge the devotee stands on
cracks for CRACK_SECONDS, breaks, and reforms GONE_SECONDS later. The reading is
the spec's "illusions of permanence" — nothing here can be rested on for long.
One timing for every mode (designer, 2026-11-13).

The rule lives here, free of pygame, so it can be tested on its own;
LevelScene owns taking the rect out of the platform list and drawing it.
"""

CRACK_SECONDS = 1.0     # from the first footfall to the break
GONE_SECONDS = 3.0      # how long the gap stays open
SOLID, CRACKING, GONE = "solid", "cracking", "gone"


class CrumblingLedge:
    def __init__(self, rect):
        self.rect = rect
        self.state = SOLID
        self.timer = 0.0

    @property
    def progress(self):
        """0..1 through the current cracking or gone spell; 0 while solid."""
        if self.state == CRACKING:
            return min(1.0, self.timer / CRACK_SECONDS)
        if self.state == GONE:
            return min(1.0, self.timer / GONE_SECONDS)
        return 0.0

    def update(self, dt, stood_on, clear_to_return=True):
        """Advance one frame. Returns "broke", "returned" or None.

        Once it starts cracking it does not stop: stepping off does not save it.
        It will not reform while `clear_to_return` is false — the caller passes
        that when the devotee is in the gap, so it never closes around them.
        """
        if self.state == SOLID:
            if stood_on:
                self.state, self.timer = CRACKING, 0.0
            return None
        self.timer += dt
        if self.state == CRACKING and self.timer >= CRACK_SECONDS:
            self.state, self.timer = GONE, 0.0
            return "broke"
        if self.state == GONE and self.timer >= GONE_SECONDS and clear_to_return:
            self.state, self.timer = SOLID, 0.0
            return "returned"
        return None
