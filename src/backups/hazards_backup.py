"""
hazards.py — Water and Fire hazard system for The Path to Moksha.
Both hazards appear in every level per the GDD. Contact causes time penalty + stun.
"""
import math
import random
import pygame
from settings import (
    COLOR_BLUE_WATER, COLOR_RED, LOGICAL_HEIGHT,
)

HAZARD_TIME_PENALTY = 5       # seconds lost on contact
HAZARD_STUN_DURATION = 1.0    # seconds stunned
HAZARD_COOLDOWN = 2.0         # seconds before same hazard can hurt again


class Hazard:
    """Base hazard class."""
    def __init__(self, x, y, w, h, hazard_type="water"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hazard_type = hazard_type  # "water" or "fire"
        self.cooldown = 0.0
        self.anim_timer = 0.0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, dt):
        self.anim_timer += dt
        if self.cooldown > 0:
            self.cooldown -= dt

    def check_collision(self, player_rect):
        """Returns True if player touches this hazard and cooldown is expired."""
        if self.cooldown > 0:
            return False
        if self.rect.colliderect(player_rect):
            self.cooldown = HAZARD_COOLDOWN
            return True
        return False

    def draw(self, surface):
        if self.hazard_type == "water":
            self._draw_water(surface)
        else:
            self._draw_fire(surface)

    def _draw_water(self, surface):
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        # Animated wave color
        wave = int(20 * math.sin(self.anim_timer * 3 + self.x * 0.05))
        base = (40, 100 + wave, 220, 160)
        pygame.draw.rect(s, base, s.get_rect(), border_radius=4)
        # Wave lines
        for i in range(0, self.w, 20):
            wy = int(4 * math.sin(self.anim_timer * 4 + i * 0.3))
            pygame.draw.circle(s, (80, 160, 255, 120),
                               (i + 10, self.h // 2 + wy), 3)
        surface.blit(s, (self.x, self.y))

    def _draw_fire(self, surface):
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        # Animated flame color
        flicker = int(30 * math.sin(self.anim_timer * 6 + self.x * 0.1))
        base = (200 + flicker % 55, 60 + abs(flicker), 20, 180)
        pygame.draw.rect(s, base, s.get_rect(), border_radius=4)
        # Flame tips
        for i in range(0, self.w, 16):
            fy = int(6 * math.sin(self.anim_timer * 5 + i * 0.5))
            tip_h = 8 + abs(fy)
            pygame.draw.polygon(s, (255, 200, 40, 200), [
                (i + 4, self.h),
                (i + 8, self.h - tip_h),
                (i + 12, self.h),
            ])
        surface.blit(s, (self.x, self.y))


def create_hazards_for_level(level, platforms):
    """Create water and fire hazards for a given level, placed between platforms."""
    hazards = []
    W = platforms[0].width if platforms else 1920  # floor width
    H = LOGICAL_HEIGHT
    WALL = 30

    if level == 1:
        # Water: puddles on the ground floor
        hazards.append(Hazard(400, H - WALL - 15, 120, 15, "water"))
        hazards.append(Hazard(900, H - WALL - 15, 100, 15, "water"))
        # Fire: steam vents
        hazards.append(Hazard(700, H - WALL - 18, 80, 18, "fire"))
        hazards.append(Hazard(1200, H - WALL - 18, 90, 18, "fire"))

    elif level == 2:
        # Water: rain shafts near Tier 2-3
        hazards.append(Hazard(350, H - 400, 40, 100, "water"))
        hazards.append(Hazard(650, H - 350, 40, 80, "water"))
        hazards.append(Hazard(1000, H - WALL - 15, 130, 15, "water"))
        # Fire: torch sconces
        hazards.append(Hazard(250, H - 280, 60, 18, "fire"))
        hazards.append(Hazard(850, H - 500, 70, 18, "fire"))

    elif level == 3:
        # Fire: fire pits along the floor
        hazards.append(Hazard(300, H - WALL - 20, 150, 20, "fire"))
        hazards.append(Hazard(800, H - WALL - 20, 130, 20, "fire"))
        hazards.append(Hazard(1300, H - WALL - 20, 100, 20, "fire"))
        # Water: overflowing pools
        hazards.append(Hazard(550, H - 500, 50, 80, "water"))
        hazards.append(Hazard(1100, H - 650, 50, 60, "water"))

    elif level == 4:
        # Water: sacred water channels
        hazards.append(Hazard(200, H - WALL - 15, 160, 15, "water"))
        hazards.append(Hazard(700, H - WALL - 15, 140, 15, "water"))
        # Fire: ceremonial flame pillars
        hazards.append(Hazard(500, H - 300, 30, 80, "fire"))
        hazards.append(Hazard(1000, H - 500, 30, 90, "fire"))
        hazards.append(Hazard(1500, H - 700, 30, 80, "fire"))

    return hazards
