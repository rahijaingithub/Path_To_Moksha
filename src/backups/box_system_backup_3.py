"""
box_system.py — Box Roulette system for The Path to Moksha.
Handles box placement, randomization, opening, and item effects.
"""
from settings import LOGICAL_WIDTH
import random
import math
import pygame
from settings import (
    COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM, COLOR_WHITE, COLOR_CREAM,
    COLOR_RED, COLOR_GREEN, COLOR_SAFFRON, COLOR_BLUE_WATER, COLOR_LOTUS_PINK,
    SUPPORT_TIME_BONUS, DISTRACTION_TIME_PENALTY, DISTRACTION_FREEZE_DURATION,
    LOGICAL_WIDTH,
)

# Item categories
CAT_GOAL = "goal"
CAT_SUPPORT = "support"
CAT_DISTRACTION = "distraction"
CAT_NO_EFFECT = "no_effect"

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
        {"cat": CAT_DISTRACTION, "name": "Movie Ticket", "desc": "Watching Movie! -{t}s"},
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
            # Highlight glow (Emerald green) or subtle regular gold aura
            if self.highlighted:
                # Pulse outline
                alpha = int(95 + 60 * math.sin(pygame.time.get_ticks() * 0.007))
                glow = pygame.Surface((self.SIZE + 16, self.SIZE + 16), pygame.SRCALPHA)
                pygame.draw.rect(glow, (60, 255, 100, alpha), glow.get_rect(), border_radius=12)
                pygame.draw.rect(glow, (100, 255, 140, 255), glow.get_rect(), width=2, border_radius=12)
                surface.blit(glow, (self.x - 8, draw_y - 8))
            else:
                # Subtle floating gold aura
                alpha = int(35 + 20 * math.sin(pygame.time.get_ticks() * 0.004))
                glow = pygame.Surface((self.SIZE + 8, self.SIZE + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*COLOR_GOLD_DIM[:3], alpha), glow.get_rect(), border_radius=8)
                surface.blit(glow, (self.x - 4, draw_y - 4))

            # Closed box — detailed wood chest with metal bands
            box_surf = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
            # Wood base
            pygame.draw.rect(box_surf, (155, 105, 45), box_surf.get_rect(), border_radius=6)
            # Metal bands (top and bottom straps)
            pygame.draw.rect(box_surf, (80, 55, 25), (0, 0, self.SIZE, 8))
            pygame.draw.rect(box_surf, (80, 55, 25), (0, self.SIZE - 8, self.SIZE, 8))
            # Gold corner rivets
            pygame.draw.circle(box_surf, COLOR_GOLD, (6, 4), 2)
            pygame.draw.circle(box_surf, COLOR_GOLD, (self.SIZE - 6, 4), 2)
            pygame.draw.circle(box_surf, COLOR_GOLD, (6, self.SIZE - 4), 2)
            pygame.draw.circle(box_surf, COLOR_GOLD, (self.SIZE - 6, self.SIZE - 4), 2)
            # Center lock plate (gold shield/diamond shape)
            lock_points = [
                (self.SIZE // 2, self.SIZE // 2 - 10),
                (self.SIZE // 2 + 10, self.SIZE // 2),
                (self.SIZE // 2, self.SIZE // 2 + 10),
                (self.SIZE // 2 - 10, self.SIZE // 2)
            ]
            pygame.draw.polygon(box_surf, COLOR_GOLD, lock_points)
            # Black keyhole
            pygame.draw.circle(box_surf, (0, 0, 0), (self.SIZE // 2, self.SIZE // 2 + 1), 3)
            pygame.draw.line(box_surf, (0, 0, 0), (self.SIZE // 2, self.SIZE // 2 + 1), (self.SIZE // 2, self.SIZE // 2 + 6), 2)

            surface.blit(box_surf, (self.x, draw_y))
        else:
            # Opened box — show glowing spiritual aura and category color
            cat = self.item["cat"]
            color = CAT_COLORS.get(cat, COLOR_WHITE)
            
            # Pulsing background glow
            alpha = int(70 + 40 * math.sin(pygame.time.get_ticks() * 0.005))
            glow = pygame.Surface((self.SIZE + 12, self.SIZE + 12), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color[:3], alpha), (self.SIZE // 2 + 6, self.SIZE // 2 + 6), self.SIZE // 2 + 6)
            surface.blit(glow, (self.x - 6, draw_y - 6))

            # Open chest bottom base
            box_surf = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (120, 80, 40, 180), (0, self.SIZE // 2, self.SIZE, self.SIZE // 2), border_radius=3)
            pygame.draw.rect(box_surf, (80, 50, 20), (0, self.SIZE // 2, self.SIZE, self.SIZE // 2), width=2, border_radius=3)
            
            # Opened lid angled upwards
            pygame.draw.rect(box_surf, (140, 95, 45, 200), (4, 4, self.SIZE - 8, self.SIZE // 2 - 4), border_radius=2)
            pygame.draw.rect(box_surf, (90, 60, 25), (4, 4, self.SIZE - 8, self.SIZE // 2 - 4), width=1, border_radius=2)

            # Floating item label or name
            name_short = self.item["name"][:7]
            n = font.render(name_short, True, color)
            nr = n.get_rect(center=(self.SIZE // 2, self.SIZE // 2 + 2))
            box_surf.blit(n, nr)
            surface.blit(box_surf, (self.x, draw_y))


class BoxSystem:
    """Manages all boxes in a level."""

    def __init__(self, level, platforms, hazards, monk):
        self.level = level
        self.boxes = []
        self.message = ""
        self.message_timer = 0.0
        self.message_color = COLOR_WHITE
        self.goal_found = False
        self._place_boxes(platforms, hazards, monk)

    def _place_boxes(self, platforms, hazards, monk):
        """Randomly place boxes on platforms or the ground, avoiding all hazards and the monk."""
        defs = LEVEL_BOX_DEFS.get(self.level, LEVEL_BOX_DEFS[1])
        shuffled = list(defs)
        random.shuffle(shuffled)

        def is_placement_safe(x, y, width, hazards, monk):
            # Check Monk proximity (to avoid spawning on top of the monk)
            if monk:
                monk_on_same_surface = abs(monk.y + monk.HEIGHT - y) < 25
                if monk_on_same_surface:
                    overlap = not (x + width < monk.x - 30 or x > monk.x + monk.WIDTH + 30)
                    if overlap:
                        return False

            # Check other placed boxes to avoid overlapping boxes
            for b in self.boxes:
                box_on_same_surface = abs(b.y + Box.SIZE - y) < 25
                if box_on_same_surface:
                    overlap = not (x + width < b.x - 30 or x > b.x + Box.SIZE + 30)
                    if overlap:
                        return False

            # Check hazards
            for h in hazards:
                h_bottom = h.y + h.h
                on_same_surface = abs(h_bottom - y) < 25 or abs(h.y - y) < 35
                if on_same_surface:
                    overlap = not (x + width < h.x or x > h.x + h.w)
                    if overlap:
                        return False
            return True

        # Floor is platforms[0]. Standard platforms are platforms[4:].
        candidates = [platforms[0]] + [p for p in platforms[4:] if p.width >= 100]

        for item_def in shuffled:
            placed = False
            # Make up to 50 attempts to find a safe location for this box
            for _ in range(50):
                plat = random.choice(candidates)
                x_min = plat.x + 15
                x_max = plat.x + plat.width - Box.SIZE - 15

                if plat == platforms[0]:
                    # Limit ground floor to active screen bounds
                    x_min = max(x_min, 120)
                    x_max = min(x_max, LOGICAL_WIDTH - 150)

                if x_min >= x_max:
                    continue

                bx = random.randint(int(x_min), int(x_max))
                by = plat.y - Box.SIZE - 5

                if is_placement_safe(bx, plat.y, Box.SIZE, hazards, monk):
                    self.boxes.append(Box(bx, by, item_def))
                    placed = True
                    break

            if not placed:
                # Fallback to standard middle spot if randomizing fails completely
                for fallback_plat in candidates:
                    bx = fallback_plat.x + (fallback_plat.width - Box.SIZE) // 2
                    by = fallback_plat.y - Box.SIZE - 5
                    self.boxes.append(Box(bx, by, item_def))
                    break

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
