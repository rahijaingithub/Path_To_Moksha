"""
transition_scene.py — Displays Bhagwan images between levels with bowing animation.
"""
import math
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_LEVEL,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_CREAM,
    COLOR_SAFFRON, COLOR_WHITE,
    FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
)

# Transition data per level boundary
TRANSITION_DATA = {
    2: {
        "title": "Entering the Temple",
        "subtitle": "Jain Society of Toronto",
        "image": "jsot_temple.png",
        "message": "The devotee removes their shoes and enters with reverence...",
    },
    3: {
        "title": "Parshvanath Bhagwan",
        "subtitle": "The 23rd Tirthankara",
        "image": "parshvanath.png",
        "message": "The devotee bows before Parshvanath Bhagwan...",
    },
    4: {
        "title": "Mahavir Bhagwan",
        "subtitle": "The 24th Tirthankara",
        "image": "mahavir.png",
        "message": "The devotee bows before Mahavir Bhagwan...",
    },
    5: {  # After level 4 → victory (used as pre-victory transition)
        "title": "Adinath Bhagwan",
        "subtitle": "The First Tirthankara — Moolnayak",
        "image": "adinath.png",
        "message": "The devotee bows in deep reverence before Adinath Bhagwan...",
    },
}


class TransitionScene(Scene):
    """Full-screen transition between levels showing Bhagwan images."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.next_level = 2
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.auto_advance_timer = 7.0  # extended slightly to allow reading the typing text
        self.data = {}
        self.bg_image = None

    def on_enter(self, **kwargs):
        self.next_level = kwargs.get("next_level", 2)
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.auto_advance_timer = 7.0

        self.data = TRANSITION_DATA.get(self.next_level, TRANSITION_DATA[2])

        # Fonts
        self.font_title = self.assets.load_font(None, FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, FONT_SIZE_SMALL)

        # Try to load the transition image
        self.bg_image = self.assets.load_image(
            self.data["image"], "transitions",
            scale=(500, 500)
        )

        # Stop level bgm during divine transition, play transition ambiance or silent prayer drone
        self.assets.stop_music()

    def handle_events(self, events, input_mgr):
        if self.elapsed > 1.0:
            if (input_mgr.just_pressed[input_mgr.ACTION] or
                    input_mgr.just_pressed[input_mgr.JUMP]):
                self._advance()
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._advance()

    def _advance(self):
        self.manager.switch_to(SCENE_LEVEL, level=self.next_level)

    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 200 * dt)
        self.auto_advance_timer -= dt
        if self.auto_advance_timer <= 0:
            self._advance()

    def draw(self, surface):
        # Background — dark gradient
        for y in range(LOGICAL_HEIGHT):
            t = y / LOGICAL_HEIGHT
            r = int(18 * (1 - t) + 10 * t)
            g = int(12 * (1 - t) + 8 * t)
            b = int(28 * (1 - t) + 20 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (LOGICAL_WIDTH, y))

        # Double-layered divine light halo behind the image
        glow_r1 = 260 + int(24 * math.sin(self.elapsed * 1.8))
        glow1 = pygame.Surface((glow_r1 * 2, glow_r1 * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow1, (255, 210, 80, 24), (glow_r1, glow_r1), glow_r1)
        surface.blit(glow1, (LOGICAL_WIDTH // 2 - glow_r1, LOGICAL_HEIGHT // 2 - glow_r1 - 40))

        glow_r2 = 200 + int(12 * math.cos(self.elapsed * 2.4))
        glow2 = pygame.Surface((glow_r2 * 2, glow_r2 * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow2, (255, 140, 40, 36), (glow_r2, glow_r2), glow_r2)
        surface.blit(glow2, (LOGICAL_WIDTH // 2 - glow_r2, LOGICAL_HEIGHT // 2 - glow_r2 - 40))

        # Bhagwan / Temple image (with Ken Burns subtle breathing zoom effect)
        if self.bg_image:
            zoom = 1.0 + 0.04 * math.sin(self.elapsed * 0.4)
            w = int(500 * zoom)
            h = int(500 * zoom)
            zoomed_img = pygame.transform.smoothscale(self.bg_image, (w, h))
            img_rect = zoomed_img.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 40))
            surface.blit(zoomed_img, img_rect)

        # Title
        title = self.font_title.render(self.data["title"], True, COLOR_GOLD_BRIGHT)
        surface.blit(title, title.get_rect(
            center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 250)))

        # Subtitle
        sub = self.font_body.render(self.data["subtitle"], True, COLOR_SAFFRON)
        surface.blit(sub, sub.get_rect(
            center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 295)))

        # Typewriter text reveal logic for description message
        chars_to_show = int(self.elapsed * 32)  # reveal 32 characters per second
        msg_text = self.data["message"][:chars_to_show]
        msg = self.font_small.render(msg_text, True, COLOR_CREAM)
        surface.blit(msg, msg.get_rect(
            center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 340)))

        # "Press ENTER or Tap to continue..." glow prompt
        if self.elapsed > 1.8:
            alpha = int(128 + 127 * math.sin(self.elapsed * 4))
            cont = self.font_small.render(
                "Press ENTER or Tap to continue...", True, COLOR_WHITE)
            cont.set_alpha(alpha)
            surface.blit(cont, cont.get_rect(
                center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 60)))

        # Fade-in
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
