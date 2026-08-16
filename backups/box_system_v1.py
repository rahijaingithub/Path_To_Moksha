"""
box_system.py — Box Roulette system for The Path to Moksha.
Handles box placement, randomization, opening, and item effects.
"""
import random
import math
import pygame
from settings import (
    COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM, COLOR_WHITE, COLOR_CREAM,
    COLOR_RED, COLOR_GREEN, COLOR_SAFFRON, COLOR_BLUE_WATER, COLOR_LOTUS_PINK,
    SUPPORT_TIME_BONUS, DISTRACTION_TIME_PENALTY, DISTRACTION_FREEZE_DURATION,
)

# Item categories
CAT_GOAL = "goal"
CAT_SUPPORT = "support"
CAT_DISTRACTION = "distraction"
CAT_NO_EFFECT = "no_effect"

# Color coding per category (revealed after opening)
CAT_COLORS = {
    CAT_GOAL: COLOR_GOLD_BRIGHT,
    CAT_SUPPORT: COLOR_GREEN,
    CAT_DISTRACTION: COLOR_RED,
    CAT_NO_EFFECT: (150, 150, 150),
}

# ── Level box definitions (from GDD) ──
LEVEL_BOX_DEFS = {
    1: [
        {"cat": CAT_GOAL, "name": "Temple Key", "desc": "You found the Temple Key!"},
        {"cat": CAT_SUPPORT, "name": "TTC Bus", "desc": "TTC Bus! +{t}s speed boost!"},
        {"cat": CAT_SUPPORT, "name": "Personal Car", "desc": "Personal Car! +{t}s fast boost!"},
        {"cat": CAT_DISTRACTION, "name": "Mobile Phone", "desc": "Distracted by phone! -{t}s"},
        {"cat": CAT_DISTRACTION, "name": "Food", "desc": "Stopped to eat! -{t}s"},
        {"cat": CAT_DISTRACTION, "name": "Movie Ticket", "desc": "Daydreaming! -{t}s"},
    ],
    2: [
        {"cat": CAT_GOAL, "name": "Akshat", "desc": "You found the Akshat (sacred rice)!"},
        {"cat": CAT_SUPPORT, "name": "Ghanta", "desc": "Temple Bell! +{t}s hazard repel!"},
        {"cat": CAT_SUPPORT, "name": "Lakshan (Snake)", "desc": "Dharanendra's protection! +{t}s"},
        {"cat": CAT_NO_EFFECT, "name": "Wrong Lakshan (Bull)", "desc": "A Bull Lakshan... nothing happens."},
        {"cat": CAT_DISTRACTION, "name": "Mobile Phone", "desc": "Selfie time! -{t}s"},
        {"cat": CAT_DISTRACTION, "name": "Friend", "desc": "Friend chats you up! -{t}s"},
    ],
    3: [
        {"cat": CAT_GOAL, "name": "Akshat", "desc": "You found the Akshat (sacred rice)!"},
        {"cat": CAT_SUPPORT, "name": "Chanvar", "desc": "Ceremonial Fan! +{t}s fire cleared!"},
        {"cat": CAT_SUPPORT, "name": "Lakshan (Lion)", "desc": "Lion reveals the path! +{t}s"},
        {"cat": CAT_NO_EFFECT, "name": "Wrong Lakshan (Bull)", "desc": "A Bull Lakshan... nothing happens."},
        {"cat": CAT_DISTRACTION, "name": "Mobile Phone", "desc": "Checking notifications! -{t}s"},
        {"cat": CAT_DISTRACTION, "name": "Foe", "desc": "A foe provokes you! -{t}s"},
    ],
    4: [
        {"cat": CAT_GOAL, "name": "Akshat", "desc": "You found the Akshat (sacred rice)!"},
        {"cat": CAT_SUPPORT, "name": "Ghanta", "desc": "Temple Bell! +{t}s hazard repel!"},
        {"cat": CAT_SUPPORT, "name": "Chanvar", "desc": "Ceremonial Fan! +{t}s fire cleared!"},
        {"cat": CAT_SUPPORT, "name": "Lakshan (Bull)", "desc": "Bull grants jump boost! +{t}s"},
        {"cat": CAT_NO_EFFECT, "name": "Wrong Lakshan (Lion)", "desc": "A Lion Lakshan... nothing happens."},
        {"cat": CAT_DISTRACTION, "name": "Foe", "desc": "A foe provokes you! -{t}s"},
    ],
}


class Box:
    """A single mystery box in the level."""

    SIZE = 50

    def __init__(self, x, y, item_def):
        self.x = x
        self.y = y
        self.item = item_def  # dict with cat, name, desc
        self.opened = False
        self.highlighted = False  # True if monk revealed this box
        self.open_timer = 0.0     # animation timer after opening
        self.hover_offset = 0.0   # floating animation

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)

    def open(self):
        """Open the box. Returns the item definition."""
        if not self.opened:
            self.opened = True
            self.open_timer = 3.0  # show result for 3 seconds
            return self.item
        return None

    def update(self, dt, elapsed):
        self.hover_offset = math.sin(elapsed * 2 + self.x * 0.01) * 4
        if self.open_timer > 0:
            self.open_timer -= dt

    def draw(self, surface, font):
        draw_y = int(self.y + self.hover_offset)

        if not self.opened:
            # Closed box — golden crate
            box_surf = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
            base_color = (200, 160, 40, 220) if not self.highlighted else (100, 255, 100, 220)
            pygame.draw.rect(box_surf, base_color, box_surf.get_rect(), border_radius=6)
            pygame.draw.rect(box_surf, COLOR_GOLD_BRIGHT, box_surf.get_rect(), width=2, border_radius=6)
            # Question mark
            q = font.render("?", True, COLOR_WHITE)
            qr = q.get_rect(center=(self.SIZE // 2, self.SIZE // 2))
            box_surf.blit(q, qr)
            # Highlight glow
            if self.highlighted:
                glow = pygame.Surface((self.SIZE + 12, self.SIZE + 12), pygame.SRCALPHA)
                pygame.draw.rect(glow, (100, 255, 100, 60), glow.get_rect(), border_radius=10)
                surface.blit(glow, (self.x - 6, draw_y - 6))
            surface.blit(box_surf, (self.x, draw_y))
        else:
            # Opened box — show category color
            cat = self.item["cat"]
            color = CAT_COLORS.get(cat, COLOR_WHITE)
            box_surf = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (*color[:3], 100), box_surf.get_rect(), border_radius=6)
            pygame.draw.rect(box_surf, color, box_surf.get_rect(), width=2, border_radius=6)
            # Item name (small)
            name_short = self.item["name"][:6]
            n = font.render(name_short, True, color)
            nr = n.get_rect(center=(self.SIZE // 2, self.SIZE // 2))
            box_surf.blit(n, nr)
            surface.blit(box_surf, (self.x, draw_y))


class BoxSystem:
    """Manages all boxes in a level."""

    def __init__(self, level, platforms):
        self.level = level
        self.boxes = []
        self.message = ""
        self.message_timer = 0.0
        self.message_color = COLOR_WHITE
        self.goal_found = False
        self._place_boxes(platforms)

    def _place_boxes(self, platforms):
        """Place boxes on top of random platforms (not boundary walls)."""
        defs = LEVEL_BOX_DEFS.get(self.level, LEVEL_BOX_DEFS[1])
        shuffled = list(defs)
        random.shuffle(shuffled)

        # Pick platforms to place boxes on (skip first 4 = boundary walls)
        available = [p for p in platforms[4:] if p.width >= 120]
        if len(available) < len(shuffled):
            available = platforms[4:]  # fallback to all non-wall platforms

        random.shuffle(available)
        for i, item_def in enumerate(shuffled):
            plat = available[i % len(available)]
            bx = plat.x + random.randint(10, max(10, plat.width - Box.SIZE - 10))
            by = plat.y - Box.SIZE - 5
            self.boxes.append(Box(bx, by, item_def))

    def try_open_nearest(self, player_rect):
        """Try to open the closest un-opened box near the player. Returns (item_def, time_delta) or None."""
        for box in self.boxes:
            if box.opened:
                continue
            if player_rect.colliderect(box.rect.inflate(30, 30)):
                item = box.open()
                if item:
                    return self._apply_item(item)
        return None

    def _apply_item(self, item):
        """Apply item effect. Returns (item, time_change, freeze_duration)."""
        cat = item["cat"]
        if cat == CAT_GOAL:
            self.goal_found = True
            desc = item["desc"]
            self.message = desc
            self.message_timer = 3.0
            self.message_color = COLOR_GOLD_BRIGHT
            return (item, 0, 0)
        elif cat == CAT_SUPPORT:
            desc = item["desc"].replace("{t}", str(SUPPORT_TIME_BONUS))
            self.message = desc
            self.message_timer = 2.5
            self.message_color = COLOR_GREEN
            return (item, SUPPORT_TIME_BONUS, 0)
        elif cat == CAT_DISTRACTION:
            desc = item["desc"].replace("{t}", str(DISTRACTION_TIME_PENALTY))
            self.message = desc
            self.message_timer = 2.5
            self.message_color = COLOR_RED
            return (item, -DISTRACTION_TIME_PENALTY, DISTRACTION_FREEZE_DURATION)
        elif cat == CAT_NO_EFFECT:
            self.message = item["desc"]
            self.message_timer = 2.5
            self.message_color = (150, 150, 150)
            return (item, 0, 0)
        return (item, 0, 0)

    def highlight_goal_box(self):
        """Monk reward: highlight the goal box and first support box."""
        for box in self.boxes:
            if not box.opened and box.item["cat"] == CAT_GOAL:
                box.highlighted = True
        for box in self.boxes:
            if not box.opened and box.item["cat"] == CAT_SUPPORT:
                box.highlighted = True
                break  # only highlight one support

    def update(self, dt, elapsed):
        for box in self.boxes:
            box.update(dt, elapsed)
        if self.message_timer > 0:
            self.message_timer -= dt

    def draw(self, surface, font):
        for box in self.boxes:
            box.draw(surface, font)

    def draw_message(self, surface, font):
        """Draw the floating item message at top-center."""
        if self.message_timer > 0 and self.message:
            alpha = min(255, int(self.message_timer * 200))
            msg_surf = font.render(self.message, True, self.message_color)
            msg_surf.set_alpha(alpha)
            r = msg_surf.get_rect(center=(surface.get_width() // 2, 80))
            # Background bar
            bg = pygame.Surface((r.width + 40, r.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, min(180, alpha)), bg.get_rect(), border_radius=8)
            surface.blit(bg, (r.x - 20, r.y - 8))
            surface.blit(msg_surf, r)
