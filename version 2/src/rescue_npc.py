"""
rescue_npc.py — The two souls helped in Level 3's Karuna bonus level (Epic G).

Two different kinds of help, so two different verbs:

* the **injured** man walks, but slowly and with a limp. He is helped along to the
  hospital and treated there — his *body* is saved. He sets the pace, so the
  devotee has to wait for him.
* the **lost** man walks freely but does not know where to go. He is led, and he
  recognises the temple himself when he reaches it — his *soul* is saved.

Both draw procedurally until the art of G5 arrives, the way the Monk does, so the
level is playable and testable with no assets at all.
"""
import math
import pygame
from settings import (
    LOGICAL_WIDTH,
    COLOR_CREAM, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GREEN, COLOR_WHITE, COLOR_SAFFRON,
)

KIND_INJURED = "injured"
KIND_LOST = "lost"

# On-screen height for the G5 art. The devotee is drawn 150px tall beside them.
DRAW_HEIGHT = 150

# How close the devotee must be to pick someone up or be followed.
REACH = 90
# Each man keeps this far behind the devotee, and neither outruns him.
FOLLOW_GAP = 86
FOLLOW_SPEED = 250.0
# The injured man limps, so he cannot keep up: the devotee must wait for him.
LIMP_FOLLOW_SPEED = 132.0
# How far he drifts while he is still lost, and how fast.
WANDER_SPAN = 70
WANDER_SPEED = 46.0
# Being lost is not pacing without pause: he casts about, stops, puts a hand to his
# head wondering, then tries another way.
PACE_SECONDS = 2.2
PONDER_SECONDS = 1.8

# What a man waiting for help calls out, and how the bubble comes and goes.
# The injured man's art carries no bandage, so without this he reads as someone
# walking slowly rather than someone hurt; the bubble says what the sprite cannot.
SPEECH = {
    (KIND_INJURED, "waiting"): "Help! My leg hurts!",
    (KIND_INJURED, "following"): "Slowly, please... my leg.",
}
# How far ahead of him the bubble sits, on the side he is facing.
BUBBLE_LEAD = 46
BUBBLE_SHOW_SECONDS = 2.6
BUBBLE_HIDE_SECONDS = 1.4
BUBBLE_FADE_SECONDS = 0.35


class RescueNPC:
    """One person to help: waiting → following → (treating) → delivered."""

    WIDTH = 52
    HEIGHT = 96

    def __init__(self, kind, x, ground_y, poses=None):
        self.kind = kind
        self.x = float(x)
        self.home_x = float(x)
        self.ground_y = ground_y
        # G5 art, when it exists: a square-framed "walk" strip for each man (the
        # injured one's limps), and "confused" for the lost one's wondering. Missing
        # poses fall back to the procedural figure, one pose at a time.
        self.poses = poses or {}
        self.state = "waiting"        # waiting | following | treating | delivered
        self.facing_right = True
        self.anim = 0.0
        self.wander_dir = 1
        self.pondering = False        # stopped, hand to his head
        self.phase_timer = PACE_SECONDS

    # ── geometry ──────────────────────────────────────────────────────────────

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.WIDTH // 2), self.ground_y - self.HEIGHT,
                           self.WIDTH, self.HEIGHT)

    @property
    def follow_speed(self):
        return LIMP_FOLLOW_SPEED if self.kind == KIND_INJURED else FOLLOW_SPEED

    def is_near(self, x):
        return abs(self.x - x) <= REACH

    @property
    def helped(self):
        return self.state == "delivered"

    # ── update ────────────────────────────────────────────────────────────────

    def update(self, dt, player_x, player_facing_right):
        self.anim += dt

        if self.state == "waiting" and self.kind == KIND_LOST:
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.pondering = not self.pondering
                self.phase_timer = PONDER_SECONDS if self.pondering else PACE_SECONDS
                if not self.pondering:
                    self.wander_dir *= -1      # having wondered, he tries the other way

            if not self.pondering:
                self.x += WANDER_SPEED * self.wander_dir * dt
                if self.x > self.home_x + WANDER_SPAN:
                    self.x, self.wander_dir = self.home_x + WANDER_SPAN, -1
                elif self.x < self.home_x - WANDER_SPAN:
                    self.x, self.wander_dir = self.home_x - WANDER_SPAN, 1
                self.facing_right = self.wander_dir > 0

        elif self.state == "following":
            target = player_x - FOLLOW_GAP if player_facing_right else player_x + FOLLOW_GAP
            step = self.follow_speed * dt
            if abs(target - self.x) > step:
                direction = 1 if target > self.x else -1
                self.x += step * direction
                self.facing_right = direction > 0
            else:
                self.x = target

    @property
    def is_pondering(self):
        """Standing still with a hand to his head — the confused pose."""
        return self.kind == KIND_LOST and self.state == "waiting" and self.pondering

    @property
    def speech(self):
        """What he is calling out, or None. Only while he still needs help."""
        return SPEECH.get((self.kind, self.state))

    @property
    def speech_alpha(self):
        """0-255 over the appear/hold/disappear cycle, 0 while it is away."""
        if not self.speech:
            return 0
        cycle = BUBBLE_SHOW_SECONDS + BUBBLE_HIDE_SECONDS
        t = self.anim % cycle
        if t > BUBBLE_SHOW_SECONDS:
            return 0
        if t < BUBBLE_FADE_SECONDS:
            return int(255 * t / BUBBLE_FADE_SECONDS)
        if t > BUBBLE_SHOW_SECONDS - BUBBLE_FADE_SECONDS:
            return int(255 * (BUBBLE_SHOW_SECONDS - t) / BUBBLE_FADE_SECONDS)
        return 255

    def take(self):
        """The devotee offers to walk with him; from here he follows at his own pace."""
        if self.state != "waiting":
            return False
        self.state = "following"
        return True

    def deliver(self):
        self.state = "delivered"

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface, font, player_x=None, player_top=None, speech_font=None):
        art = self._walk_image()
        if art:
            self._blit(surface, art, self.x, self.ground_y)
        else:
            self._draw_figure(surface, self.x, self.ground_y)

        if self.speech:
            self._draw_speech(surface, speech_font or font)
        elif self.state == "waiting":
            self._draw_call(surface, font)

    def _draw_speech(self, surface, font):
        """A speech bubble over his head, fading in and out.

        Built opaque and then faded as a whole with a BLEND_RGBA_MULT pass: setting
        an alpha on a per-pixel-alpha surface does not reliably dim what is drawn
        onto it, and the text would stay solid over a fading bubble.
        """
        alpha = self.speech_alpha
        if alpha <= 0:
            return

        pad_x, pad_y, tail = 20, 11, 15
        label = font.render(self.speech, True, (32, 26, 42))
        w = label.get_width() + pad_x * 2
        h = label.get_height() + pad_y * 2

        # The bubble leads him, on the side he is walking towards, and its tail
        # points back down to his head — so it reads as his, whichever way he turns.
        lead = BUBBLE_LEAD if self.facing_right else -BUBBLE_LEAD
        cx = self.x + lead
        tip = int(w * (0.26 if self.facing_right else 0.74))

        bubble = pygame.Surface((w, h + tail), pygame.SRCALPHA)
        body = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(bubble, (252, 248, 238), body, border_radius=13)
        foot = (tip - lead // 3, h + tail)
        pygame.draw.polygon(bubble, (252, 248, 238),
                            [(tip - 13, h - 3), (tip + 13, h - 3), foot])
        pygame.draw.rect(bubble, (126, 108, 88), body, width=2, border_radius=13)
        pygame.draw.lines(bubble, (126, 108, 88), False,
                          [(tip - 13, h - 2), foot, (tip + 13, h - 2)], 2)
        bubble.blit(label, (pad_x, pad_y))
        bubble.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)

        bob = math.sin(self.anim * 2.4) * 3
        top = self.ground_y - self.HEIGHT
        rect = bubble.get_rect(midbottom=(int(cx), int(top - 6 + bob)))
        rect.clamp_ip(pygame.Rect(8, 0, LOGICAL_WIDTH - 16, 10_000))   # keep it on screen
        surface.blit(bubble, rect)

    def _draw_call(self, surface, font):
        """The mark that says someone here needs help."""
        bob = math.sin(self.anim * 3.0) * 4
        mark = "!" if self.kind == KIND_INJURED else "?"
        color = COLOR_SAFFRON if self.kind == KIND_INJURED else COLOR_GOLD_BRIGHT
        glyph = font.render(mark, True, color)
        top = self.ground_y - self.HEIGHT
        surface.blit(glyph, glyph.get_rect(center=(int(self.x), int(top - 24 + bob))))

    def _pose_image(self, key, target_h):
        """One still pose, scaled to `target_h`. None when that art is not present."""
        img = self.poses.get(key)
        return self._to_height(img, target_h) if img else None

    def _walk_image(self):
        """The current frame, from whichever strip suits what he is doing.

        While he wonders, the confused strip plays — hand rising to his head and
        down again. Either strip stands in for the other when only one exists.
        """
        if self.is_pondering:
            strip = self.poses.get("confused") or self.poses.get("walk")
        else:
            strip = self.poses.get("walk") or self.poses.get("confused")
        if not strip:
            return None
        fh = strip.get_height()
        frames = max(1, strip.get_width() // fh)
        rate = 0.22 if self.is_pondering else 0.14      # the gesture is unhurried
        moving = self.state in ("waiting", "following")
        idx = int(self.anim / rate) % frames if moving else 0
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

    def _draw_figure(self, surface, cx, base_y, scale=1.0):
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

        if self.is_pondering:
            # Hand up to the head, so the stand-in reads as the pose too.
            pygame.draw.line(body, cloth, (c + w // 5, c - h // 8),
                             (c + int(6 * scale), c - h // 4 - int(16 * scale)),
                             max(3, int(5 * scale)))

        if self.kind == KIND_INJURED:
            # A bandage, not a wound — the art direction for this game keeps hurt
            # gentle (see the tired-bird prompt: "tired, not injured").
            pygame.draw.rect(body, COLOR_CREAM, (c - int(9 * scale), c - h // 4 - int(18 * scale),
                                                 int(18 * scale), int(7 * scale)), border_radius=2)
        if self.state == "delivered":
            halo = int(16 * scale)
            pygame.draw.circle(body, (*COLOR_GREEN[:3], 120),
                               (c, c - h // 4 - int(10 * scale)), halo, width=3)

        surface.blit(body, body.get_rect(midbottom=(int(cx), int(base_y))))
