"""
character_select.py — Boy / Girl character selection screen.
"""
import math
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_LEVEL,
    COLOR_BG_DARK, COLOR_BG_MEDIUM, COLOR_GOLD, COLOR_GOLD_BRIGHT,
    COLOR_GOLD_DIM, COLOR_WHITE, COLOR_CREAM, COLOR_SAFFRON,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
)


class CharacterSelect(Scene):
    """Character selection: Boy or Girl devotee."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.selected = 0  # 0 = Boy, 1 = Girl
        self.elapsed = 0.0
        self.fade_alpha = 255

    def on_enter(self, **kwargs):
        self.selected = 0
        self.elapsed = 0.0
        self.fade_alpha = 255

        # Load character preview images
        self.boy_img = self.assets.load_image("player_boy.png", "sprites", scale=(200, 200))
        self.girl_img = self.assets.load_image("player_girl.png", "sprites", scale=(200, 200))

        # Fonts
        self.font_title = self.assets.load_font(None, FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, FONT_SIZE_SMALL)

        # Card positions
        self.card_width = 260
        self.card_height = 340
        gap = 80
        total = self.card_width * 2 + gap
        self.card_x = [(LOGICAL_WIDTH - total) // 2,
                       (LOGICAL_WIDTH - total) // 2 + self.card_width + gap]
        self.card_y = (LOGICAL_HEIGHT - self.card_height) // 2 + 20

        # Card rects for click detection
        self.card_rects = [
            pygame.Rect(self.card_x[0], self.card_y, self.card_width, self.card_height),
            pygame.Rect(self.card_x[1], self.card_y, self.card_width, self.card_height),
        ]

    def handle_events(self, events, input_mgr):
        if input_mgr.just_pressed[input_mgr.LEFT]:
            self.selected = 0
        if input_mgr.just_pressed[input_mgr.RIGHT]:
            self.selected = 1

        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.JUMP]:
            self._confirm_selection()

        # Click on card
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Convert mouse to logical coords (handled by main.py scaling)
                # For now we check raw against card rects on the logical surface
                for i, rect in enumerate(self.card_rects):
                    if rect.collidepoint(event.pos[0], event.pos[1]):
                        self.selected = i
                        self._confirm_selection()

    def _confirm_selection(self):
        self.manager.shared["character"] = "boy" if self.selected == 0 else "girl"
        self.manager.shared["current_level"] = 1
        self.manager.shared["total_time"] = 0.0
        self.manager.switch_to(SCENE_LEVEL, level=1)

    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 300 * dt)

    def draw(self, surface):
        # Background gradient
        for y in range(LOGICAL_HEIGHT):
            t = y / LOGICAL_HEIGHT
            r = int(COLOR_BG_DARK[0] * (1 - t) + COLOR_BG_MEDIUM[0] * t)
            g = int(COLOR_BG_DARK[1] * (1 - t) + COLOR_BG_MEDIUM[1] * t)
            b = int(COLOR_BG_DARK[2] * (1 - t) + COLOR_BG_MEDIUM[2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (LOGICAL_WIDTH, y))

        # Title
        title_surf = self.font_title.render("Choose Your Devotee", True, COLOR_GOLD_BRIGHT)
        tr = title_surf.get_rect(center=(LOGICAL_WIDTH // 2, 60))
        surface.blit(title_surf, tr)

        # Decorative line
        line_y = 95
        line_w = 300
        pygame.draw.line(surface, COLOR_GOLD_DIM,
                         (LOGICAL_WIDTH // 2 - line_w // 2, line_y),
                         (LOGICAL_WIDTH // 2 + line_w // 2, line_y), 2)

        # Draw cards
        labels = ["Boy", "Girl"]
        images = [self.boy_img, self.girl_img]

        for i in range(2):
            x = self.card_x[i]
            y = self.card_y
            w = self.card_width
            h = self.card_height
            is_sel = (i == self.selected)

            # Card background
            card_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            bg_color = (50, 40, 70, 220) if is_sel else (35, 28, 50, 180)
            pygame.draw.rect(card_surf, bg_color, card_surf.get_rect(), border_radius=16)

            # Border
            border_color = COLOR_GOLD_BRIGHT if is_sel else COLOR_GOLD_DIM
            border_width = 3 if is_sel else 1
            pygame.draw.rect(card_surf, border_color, card_surf.get_rect(),
                             width=border_width, border_radius=16)

            surface.blit(card_surf, (x, y))

            # Character image centered in card
            img = images[i]
            img_rect = img.get_rect(center=(x + w // 2, y + h // 2 - 30))
            surface.blit(img, img_rect)

            # Label
            label_surf = self.font_body.render(labels[i], True,
                                               COLOR_GOLD_BRIGHT if is_sel else COLOR_CREAM)
            lr = label_surf.get_rect(center=(x + w // 2, y + h - 45))
            surface.blit(label_surf, lr)

            # Selection glow
            if is_sel:
                glow_alpha = int(40 + 25 * math.sin(self.elapsed * 4))
                glow = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*COLOR_GOLD[:3], glow_alpha),
                                 glow.get_rect(), border_radius=20)
                surface.blit(glow, (x - 8, y - 8))

        # Instructions
        hint = "◄ ► to select  •  ENTER or Tap to confirm"
        hint_surf = self.font_small.render(hint, True, COLOR_GOLD_DIM)
        hr = hint_surf.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 50))
        surface.blit(hint_surf, hr)

        # Fade-in
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
