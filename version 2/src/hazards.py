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

# ── Global Toggle to easily test Level 2 with or without snakes ──────────────
ENABLE_LEVEL2_SNAKES = True   # Set to False to test Level 2 with NO snakes

HAZARD_TIME_PENALTY = 30      # seconds lost on contact
HAZARD_STUN_DURATION = 1.0    # seconds stunned
HAZARD_COOLDOWN = 2.0         # seconds before same hazard can hurt again


class Hazard:
    """Base hazard class with optional horizontal patrol movement."""
    def __init__(self, x, y, w, h, hazard_type="water", patrol_range=None, move_speed=70):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hazard_type = hazard_type  # "water", "fire", or "snake"
        self.cooldown = 0.0
        self.anim_timer = 0.0
        
        # Patrol movement parameters
        self.patrol_range = patrol_range  # Tuple of (min_x, max_x) or None
        self.move_speed = move_speed
        self.facing_dir = 1  # +1 for right, -1 for left

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, dt):
        self.anim_timer += dt
        if self.cooldown > 0:
            self.cooldown -= dt

        # Patrol movement if configured
        if self.patrol_range:
            min_x, max_x = self.patrol_range
            self.x += self.move_speed * self.facing_dir * dt
            if self.x >= max_x:
                self.x = max_x
                self.facing_dir = -1
            elif self.x <= min_x:
                self.x = min_x
                self.facing_dir = 1

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
        elif self.hazard_type == "snake":
            self._draw_snake(surface)
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

    def _draw_snake(self, surface):
        """Draw an animated slithering snake facing the movement direction."""
        s = pygame.Surface((self.w + 30, self.h + 30), pygame.SRCALPHA)
        
        num_segments = 14
        seg_w = self.w / num_segments
        wave_speed = self.anim_timer * 10
        
        # Calculate undulating spine points
        points = []
        for i in range(num_segments + 1):
            px = i * seg_w + 10
            py = (self.h // 2 + 10) + math.sin(wave_speed + i * 0.55) * 6
            points.append((px, py))
            
        # Draw ground shadow
        shadow_points = [(p[0] + 2, p[1] + 5) for p in points]
        if len(shadow_points) > 1:
            pygame.draw.lines(s, (10, 6, 18, 120), False, shadow_points, width=10)

        # Draw rocky cavern snake body segments (slate brown & dark stone tones)
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i+1]
            col = (75 + (i * 8) % 30, 68 + (i * 6) % 25, 62 + (i * 5) % 20)
            pygame.draw.line(s, col, p1, p2, 10)
            # Sandstone / ochre scale highlights
            if i % 2 == 0:
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2
                pygame.draw.circle(s, (180, 150, 90), (int(mid_x), int(mid_y)), 3)
                
        # Head position based on facing direction
        if self.facing_dir > 0:
            head_x, head_y = points[-1]
            eye_off_x, tongue_dir = 2, 1
        else:
            head_x, head_y = points[0]
            eye_off_x, tongue_dir = -2, -1

        # Draw Snake Head (Rocky charcoal slate)
        pygame.draw.circle(s, (60, 52, 48), (int(head_x), int(head_y)), 9)
        pygame.draw.circle(s, (240, 160, 40), (int(head_x) + eye_off_x, int(head_y) - 3), 3) # Glowing amber eye
        pygame.draw.circle(s, (10, 10, 10), (int(head_x) + eye_off_x * 1.5, int(head_y) - 3), 1)  # Pupil
        
        # Animated flicking red tongue
        tongue_flick = math.sin(self.anim_timer * 14)
        if tongue_flick > 0.1:
            tx = head_x + (6 * tongue_dir) + (tongue_flick * 7 * tongue_dir)
            ty = head_y
            pygame.draw.line(s, (230, 40, 40), (head_x + 5 * tongue_dir, head_y), (tx, ty), 2)
            pygame.draw.line(s, (230, 40, 40), (tx, ty), (tx + 3 * tongue_dir, ty - 3), 2)
            pygame.draw.line(s, (230, 40, 40), (tx, ty), (tx + 3 * tongue_dir, ty + 3), 2)
            
        surface.blit(s, (self.x - 10, self.y - 10))

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
    """Create water, fire, and moving snake hazards for a given level, placed between platforms."""
    hazards = []
    W = platforms[0].width if platforms else 1920  # floor width
    H = LOGICAL_HEIGHT
    WALL = 30

    if level == 1:
        # ── WATER POOLS (magenta loops on street in image) ──
        hazards.append(Hazard(850, H - WALL - 18, 160, 18, "water"))

        # ── BONFIRE / FIRE HAZARD (orange loop on rooftop in image) ──
        hazards.append(Hazard(820, H - 520 - 28, 80, 28, "fire"))

    elif level == 2:
        if ENABLE_LEVEL2_SNAKES:
            # Slithering & MOVING snake hazards replacing fire in Level 2 cave
            # Snake 1: Ground floor patrol from x=600 to x=1100
            hazards.append(Hazard(600, H - WALL - 20, 140, 24, "snake", patrol_range=(550, 1150), move_speed=80))
            # Snake 2: Cave platform patrol from x=1000 to x=1350
            hazards.append(Hazard(1000, H - 320, 120, 24, "snake", patrol_range=(950, 1350), move_speed=65))

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
