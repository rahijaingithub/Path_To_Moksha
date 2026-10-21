"""
rescue_npc.py — The two souls helped in Level 3's Karuna bonus level (Epic G).

Two different kinds of help, so two different verbs:

* the **injured** man cannot move himself. He is carried, and then treated at the
  hospital — his *body* is saved.
* the **lost** man can walk but does not know where to go. He is led, and he
  recognises the temple himself when he reaches it — his *soul* is saved.

Both draw procedurally until the art of G5 arrives, the way the Monk does, so the
level is playable and testable with no assets at all.
"""
import math
import pygame
from settings import (
    COLOR_CREAM, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GREEN, COLOR_WHITE, COLOR_SAFFRON,
)

KIND_INJURED = "injured"
KIND_LOST = "lost"

# On-screen heights for the G5 art. The devotee is drawn 150px tall beside them.
DRAW_HEIGHT = 150
SIT_DRAW_HEIGHT = 96
CARRY_DRAW_HEIGHT = 130

# How close the devotee must be to pick someone up or be followed.
REACH = 90
# The lost man keeps this far behind the devotee, and never outruns him.
FOLLOW_GAP = 86
FOLLOW_SPEED = 250.0
# How far he drifts while he is still lost, and how fast.
WANDER_SPAN = 70
WANDER_SPEED = 46.0


class RescueNPC:
    """One person to help: waiting → carried/following → (treating) → delivered."""

    WIDTH = 52
    HEIGHT = 96

    def __init__(self, kind, x, ground_y, poses=None):
        self.kind = kind
        self.x = float(x)
        self.home_x = float(x)
        self.ground_y = ground_y
        # G5 art, when it exists: "sitting"/"carried" for the injured man, "walk"
        # (a square-framed strip) for the lost one. Missing poses fall back to the
        # procedural figure, one pose at a time.
        self.poses = poses or {}
        self.state = "waiting"        # waiting | carried | following | treating | delivered
        self.facing_right = True
        self.anim = 0.0
        self.wander_dir = 1

    # ── geometry ──────────────────────────────────────────────────────────────

    SITTING_HEIGHT = 62       # he sits holding his leg until he is picked up

    @property
    def rect(self):
        """Standing box, except the injured man, who sits until he is carried."""
        if self.kind == KIND_INJURED and self.state in ("waiting", "treating"):
            return pygame.Rect(int(self.x - self.WIDTH // 2), self.ground_y - self.SITTING_HEIGHT,
                               self.WIDTH, self.SITTING_HEIGHT)
        return pygame.Rect(int(self.x - self.WIDTH // 2), self.ground_y - self.HEIGHT,
                           self.WIDTH, self.HEIGHT)

    def is_near(self, x):
        return abs(self.x - x) <= REACH

    @property
    def helped(self):
        return self.state == "delivered"

    # ── update ────────────────────────────────────────────────────────────────

    def update(self, dt, player_x, player_facing_right):
        self.anim += dt

        if self.state == "waiting" and self.kind == KIND_LOST:
            # Casting about for the way: he walks a little one way, then the other.
            self.x += WANDER_SPEED * self.wander_dir * dt
            if self.x > self.home_x + WANDER_SPAN:
                self.x, self.wander_dir = self.home_x + WANDER_SPAN, -1
            elif self.x < self.home_x - WANDER_SPAN:
                self.x, self.wander_dir = self.home_x - WANDER_SPAN, 1
            self.facing_right = self.wander_dir > 0

        elif self.state == "carried":
            # Held against the devotee's shoulder, so he moves exactly with him.
            self.x = player_x
            self.facing_right = player_facing_right

        elif self.state == "following":
            target = player_x - FOLLOW_GAP if player_facing_right else player_x + FOLLOW_GAP
            step = FOLLOW_SPEED * dt
            if abs(target - self.x) > step:
                direction = 1 if target > self.x else -1
                self.x += step * direction
                self.facing_right = direction > 0
            else:
                self.x = target

    def take(self):
        """The devotee takes him up: carried if he cannot walk, following if he can."""
        if self.state != "waiting":
            return False
        self.state = "carried" if self.kind == KIND_INJURED else "following"
        return True

    def deliver(self):
        self.state = "delivered"

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface, font, player_x=None, player_top=None):
        if self.state == "carried" and player_x is not None:
            # Across the shoulders, at nearly full size — shrunk much further he
            # stops reading as a person being carried at all.
            cx = player_x + (26 if self.facing_right else -26)
            art = self._pose_image("carried", CARRY_DRAW_HEIGHT)
            if art:
                self._blit(surface, art, cx, player_top + 58)
            else:
                self._draw_figure(surface, cx, player_top + 58, lying=True, scale=0.95)
            return

        sitting = self.kind == KIND_INJURED and self.state in ("waiting", "treating")
        if sitting:
            art = self._pose_image("sitting", SIT_DRAW_HEIGHT)
        else:
            art = self._walk_image()
        if art:
            self._blit(surface, art, self.x, self.ground_y)
        else:
            self._draw_figure(surface, self.x, self.ground_y, sitting=sitting)

        if self.state == "waiting":
            self._draw_call(surface, font)

    def _draw_call(self, surface, font):
        """The mark that says someone here needs help."""
        bob = math.sin(self.anim * 3.0) * 4
        mark = "!" if self.kind == KIND_INJURED else "?"
        color = COLOR_SAFFRON if self.kind == KIND_INJURED else COLOR_GOLD_BRIGHT
        glyph = font.render(mark, True, color)
        top = self.ground_y - (self.SITTING_HEIGHT if self.kind == KIND_INJURED else self.HEIGHT)
        surface.blit(glyph, glyph.get_rect(center=(int(self.x), int(top - 24 + bob))))

    def _pose_image(self, key, target_h):
        """One still pose, scaled to `target_h`. None when that art is not present."""
        img = self.poses.get(key)
        return self._to_height(img, target_h) if img else None

    def _walk_image(self):
        """The current frame of the walk strip — square frames, left to right."""
        strip = self.poses.get("walk")
        if not strip:
            return None
        fh = strip.get_height()
        frames = max(1, strip.get_width() // fh)
        moving = self.state in ("waiting", "following")
        idx = int(self.anim / 0.14) % frames if moving else 0
        cell = pygame.Surface((fh, fh), pygame.SRCALPHA)
        cell.blit(strip, (0, 0), (idx * fh, 0, fh, fh))
        return self._to_height(cell, DRAW_HEIGHT)

    @staticmethod
    def _to_height(img, target_h):
        ratio = target_h / img.get_height()
        return pygame.transform.smoothscale(
            img, (max(1, int(img.get_width() * ratio)), int(target_h)))

    def _blit(self, surface, img, cx, base_y):
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, img.get_rect(midbottom=(int(cx), int(base_y))))

    def _draw_figure(self, surface, cx, base_y, lying=False, sitting=False, scale=1.0):
        """A plain figure — a stand-in until the art of G5 arrives."""
        h = int(self.HEIGHT * scale)
        w = int(self.WIDTH * scale)
        skin = (214, 176, 134)
        cloth = (176, 94, 70) if self.kind == KIND_INJURED else (92, 110, 168)

        body = pygame.Surface((max(w, h), max(w, h)), pygame.SRCALPHA)
        c = body.get_width() // 2
        # torso, head, and a leg line — enough to read as a person at this size
        pygame.draw.rect(body, cloth, (c - w // 4, c - h // 4, w // 2, h // 2), border_radius=6)
        pygame.draw.circle(body, skin, (c, c - h // 4 - int(10 * scale)), int(13 * scale))
        pygame.draw.line(body, cloth, (c, c + h // 4), (c - int(9 * scale), c + h // 2), max(3, int(6 * scale)))
        pygame.draw.line(body, cloth, (c, c + h // 4), (c + int(9 * scale), c + h // 2), max(3, int(6 * scale)))

        if self.kind == KIND_INJURED:
            # A bandage, not a wound — the art direction for this game keeps hurt
            # gentle (see the tired-bird prompt: "tired, not injured").
            pygame.draw.rect(body, COLOR_CREAM, (c - int(9 * scale), c - h // 4 - int(18 * scale),
                                                 int(18 * scale), int(7 * scale)), border_radius=2)
        if self.state == "delivered":
            halo = int(16 * scale)
            pygame.draw.circle(body, (*COLOR_GREEN[:3], 120),
                               (c, c - h // 4 - int(10 * scale)), halo, width=3)

        if lying:                     # carried across the shoulders
            body = pygame.transform.rotate(body, 90)
        elif sitting:                 # on the ground, holding his leg
            body = pygame.transform.smoothscale(
                body, (body.get_width(), int(body.get_height() * 0.66)))

        surface.blit(body, body.get_rect(midbottom=(int(cx), int(base_y))))
