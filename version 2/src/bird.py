"""
bird.py — Level 3's bird (Jiv Daya twist).

It flies across the sky until the Akshat is found, then falls onto a lotus and
lies there tired. The devotee may help it — share some Akshat and chant the
Namokar Mantra (orchestrated by level_scene) — and it revives and flies away.
Ignoring it carries no penalty. Purely visual: the bird never collides.

States: waiting -> flying -> (waiting ...) ; fall(): falling -> fallen ;
revive(): reviving -> leaving -> gone.
"""
import math
import random
import pygame
from settings import LOGICAL_WIDTH

BIRD_SIZE = 84          # on-screen size of one square frame (the body is ~half of it)
FLY_SPEED = 220         # px/s across the sky
FLY_Y = 330             # world y of the flight line: sky, below the HUD, above the island
FLAP_SECONDS = 0.07     # per wing frame
FALL_SECONDS = 1.6
REVIVE_SECONDS = 1.5
LEAVE_SPEED = 320       # px/s, up and away after reviving
FOLDED_FRAME = 3        # wings tucked in — used while falling and lying on the lotus


class Bird:
    def __init__(self, strip_right, strip_left, rest_point, fallen_img=None):
        self.frames = {1: self._cut(strip_right), -1: self._cut(strip_left)}
        # Optional dedicated art for the tired bird (facing right); until it exists
        # a wings-folded flight frame is tilted onto the lotus instead.
        self.fallen_img = (pygame.transform.smoothscale(fallen_img, (BIRD_SIZE, BIRD_SIZE))
                           if fallen_img else None)
        self.rest_x, self.rest_y = rest_point   # centre-bottom where it lies (a lotus top)
        self.state = "waiting"
        self.timer = random.uniform(1.0, 3.0)
        self.direction = 1
        self.x, self.y = -BIRD_SIZE, FLY_Y
        self.t = 0.0
        self.angle = 0.0
        self.fall_from = (0.0, 0.0)

    @staticmethod
    def _cut(strip):
        """Square frames (see tools/prepare_bird_sprites.py), scaled to BIRD_SIZE."""
        side = strip.get_height()
        return [pygame.transform.smoothscale(strip.subsurface((i * side, 0, side, side)),
                                             (BIRD_SIZE, BIRD_SIZE))
                for i in range(max(1, strip.get_width() // side))]

    @property
    def is_fallen(self):
        return self.state == "fallen"

    @property
    def rest_center(self):
        # The folded body sits a little above the frame's centre; lift it onto the petals.
        return self.rest_x, self.rest_y - BIRD_SIZE * 0.32

    @property
    def help_zone(self):
        """Where the devotee's centre must be to help it (standing on its lotus)."""
        return pygame.Rect(self.rest_x - 110, self.rest_y - 130, 220, 130)

    def fall(self):
        """The Akshat has been found: tumble from wherever it is onto the lotus."""
        if self.state in ("falling", "fallen", "reviving", "leaving", "gone"):
            return
        on_screen = self.state == "flying" and 0 <= self.x <= LOGICAL_WIDTH
        self.fall_from = (self.x, self.y) if on_screen else (self.rest_x - 260, 190.0)
        self.state, self.t = "falling", 0.0

    def revive(self):
        if self.state == "fallen":
            self.state, self.t = "reviving", 0.0

    def update(self, dt):
        self.t += dt
        if self.state == "waiting":
            self.timer -= dt
            if self.timer <= 0:
                self.direction = random.choice((1, -1))
                self.x = -BIRD_SIZE if self.direction > 0 else LOGICAL_WIDTH + BIRD_SIZE
                self.state, self.t = "flying", 0.0
        elif self.state == "flying":
            self.x += self.direction * FLY_SPEED * dt
            self.y = FLY_Y + 20 * math.sin(self.t * 2.0)
            if self.x < -BIRD_SIZE * 2 or self.x > LOGICAL_WIDTH + BIRD_SIZE * 2:
                self.state, self.timer = "waiting", random.uniform(2.0, 5.0)
        elif self.state == "falling":
            p = min(1.0, self.t / FALL_SECONDS)
            (x0, y0), (x1, y1) = self.fall_from, self.rest_center
            self.x = x0 + (x1 - x0) * p
            self.y = y0 + (y1 - y0) * p * p          # accelerating drop
            self.angle = 540 * p                      # tumbling
            if p >= 1.0:
                self.state, self.t = "fallen", 0.0
                self.direction = 1 if self.fall_from[0] <= x1 else -1
        elif self.state == "fallen":
            self.x, self.y = self.rest_center
            self.angle = 20 + 6 * math.sin(self.t * 3.0)   # lying tilted, a tired wobble
        elif self.state == "reviving":
            self.angle = 20 * max(0.0, 1.0 - self.t / REVIVE_SECONDS)
            if self.t >= REVIVE_SECONDS:
                self.state, self.t, self.angle = "leaving", 0.0, 0.0
        elif self.state == "leaving":
            self.x += self.direction * LEAVE_SPEED * dt
            self.y -= LEAVE_SPEED * 0.6 * dt
            if self.y < -BIRD_SIZE or not -BIRD_SIZE * 2 <= self.x <= LOGICAL_WIDTH + BIRD_SIZE * 2:
                self.state = "gone"

    def draw(self, surface):
        if self.state in ("waiting", "gone"):
            return
        frames = self.frames[self.direction]
        if self.state in ("flying", "leaving"):
            img = frames[int(self.t / FLAP_SECONDS) % len(frames)]
        elif self.fallen_img and self.state in ("fallen", "reviving"):
            img = self.fallen_img if self.direction > 0 else pygame.transform.flip(self.fallen_img, True, False)
        else:
            img = frames[min(FOLDED_FRAME, len(frames) - 1)]
            if self.angle:
                img = pygame.transform.rotate(img, -self.angle * self.direction)
        if self.state == "reviving":
            r = int(20 + 40 * min(1.0, self.t / REVIVE_SECONDS))
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 215, 80, 110), (r, r), r)
            surface.blit(glow, (int(self.x) - r, int(self.y) - r))
        surface.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
