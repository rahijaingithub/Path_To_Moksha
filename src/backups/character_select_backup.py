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
    GAME_FONT_SIZE_TITLE, GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL,
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
        self.sparkles = []
        self.sparkle_timer = 0.0

    def on_enter(self, **kwargs):
        self.selected = 0
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.sparkles = []
        self.sparkle_timer = 0.0

        # Load character preview images
        self.boy_img = self.assets.load_image("player_boy.png", "sprites", scale=(200, 200))
        self.girl_img = self.assets.load_image("player_girl.png", "sprites", scale=(200, 200))

        # Fonts (Using larger gameplay sizes for modern visual AAA quality)
        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

        # Card positions
        self.card_width = 300
        self.card_height = 380
        gap = 100
        total = self.card_width * 2 + gap
        self.card_x = [(LOGICAL_WIDTH - total) // 2,
                       (LOGICAL_WIDTH - total) // 2 + self.card_width + gap]
        self.card_y = (LOGICAL_HEIGHT - self.card_height) // 2 + 10

        # Card rects for hover/click detection
        self.card_rects = [
            pygame.Rect(self.card_x[0], self.card_y, self.card_width, self.card_height),
            pygame.Rect(self.card_x[1], self.card_y, self.card_width, self.card_height),
        ]

    def handle_events(self, events, input_mgr):
        if input_mgr.just_pressed[input_mgr.LEFT]:
            if self.selected != 0:
                self.selected = 0
                self.assets.play_sound("jump.wav", volume=0.12)
        if input_mgr.just_pressed[input_mgr.RIGHT]:
            if self.selected != 1:
                self.selected = 1
                self.assets.play_sound("jump.wav", volume=0.12)

        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.JUMP]:
            self._confirm_selection()

        # Click on card
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y
                for i, rect in enumerate(self.card_rects):
                    if rect.collidepoint(mx, my):
                        self.selected = i
                        self._confirm_selection()

    def _confirm_selection(self):
        self.assets.play_sound("level_complete.wav", volume=0.3)
        self.manager.shared["character"] = "boy" if self.selected == 0 else "girl"
        self.manager.shared["current_level"] = 1
        self.manager.shared["total_time"] = 0.0
        self.manager.switch_to(SCENE_LEVEL, level=1)

    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 300 * dt)

        # Dynamic mouse hover selects devotee card
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(mx, my):
                if self.selected != i:
                    self.selected = i
                    self.assets.play_sound("jump.wav", volume=0.08)

        # Spawn background mist sparkles
        self.sparkle_timer += dt
        if self.sparkle_timer > 0.18 and len(self.sparkles) < 30:
            self.sparkle_timer = 0
            import random
            self.sparkles.append({
                "x": random.randint(0, LOGICAL_WIDTH),
                "y": LOGICAL_HEIGHT + 10,
                "speed": random.uniform(20, 50),
                "size": random.randint(2, 5),
                "alpha": 0,
                "max_alpha": random.randint(100, 220),
                "lifetime": random.uniform(3.5, 6.0),
                "age": 0.0,
            })

        # Update sparkles
        for s in self.sparkles:
            s["age"] += dt
            s["y"] -= s["speed"] * dt
            if s["age"] < 1.0:
                s["alpha"] = int(s["max_alpha"] * (s["age"] / 1.0))
            elif s["age"] > s["lifetime"] - 1.0:
                s["alpha"] = int(s["max_alpha"] * (max(0.0, s["lifetime"] - s["age"]) / 1.0))
            else:
                s["alpha"] = s["max_alpha"]
        self.sparkles = [s for s in self.sparkles if s["age"] < s["lifetime"]]

    def draw(self, surface):
        # Background gradient
        for y in range(LOGICAL_HEIGHT):
            t = y / LOGICAL_HEIGHT
            r = int(COLOR_BG_DARK[0] * (1 - t) + COLOR_BG_MEDIUM[0] * t)
            g = int(COLOR_BG_DARK[1] * (1 - t) + COLOR_BG_MEDIUM[1] * t)
            b = int(COLOR_BG_DARK[2] * (1 - t) + COLOR_BG_MEDIUM[2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (LOGICAL_WIDTH, y))

        # Render background sparkles
        for s in self.sparkles:
            ps = pygame.Surface((s["size"] * 2, s["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*COLOR_GOLD[:3], s["alpha"]), (s["size"], s["size"]), s["size"])
            surface.blit(ps, (int(s["x"]) - s["size"], int(s["y"]) - s["size"]))

        # Title
        title_surf = self.font_title.render("Choose Your Pilgrim", True, COLOR_GOLD_BRIGHT)
        tr = title_surf.get_rect(center=(LOGICAL_WIDTH // 2, 70))
        surface.blit(title_surf, tr)

        # Decorative line
        line_y = 105
        line_w = 360
        pygame.draw.line(surface, COLOR_GOLD_DIM,
                         (LOGICAL_WIDTH // 2 - line_w // 2, line_y),
                         (LOGICAL_WIDTH // 2 + line_w // 2, line_y), 2)

        # Devotee labels and descriptions
        labels = ["Shravak", "Shravika"]
        images = [self.boy_img, self.girl_img]
        descs = [
            "A sincere pilgrim seeking concentration and determination on the sacred climb.",
            "A peaceful seeker aiming for quiet contemplation and spiritual awareness."
        ]

        for i in range(2):
            is_sel = (i == self.selected)
            
            # Card hover scale
            inflate_val = 14 if is_sel else 0
            x = self.card_x[i] - inflate_val // 2
            y = self.card_y - inflate_val // 2
            w = self.card_width + inflate_val
            h = self.card_height + inflate_val

            # Card background
            card_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            bg_color = (55, 42, 78, 230) if is_sel else (30, 24, 44, 170)
            pygame.draw.rect(card_surf, bg_color, card_surf.get_rect(), border_radius=20)

            # Border
            border_color = COLOR_GOLD_BRIGHT if is_sel else COLOR_GOLD_DIM
            border_w = 3.5 if is_sel else 1.5
            pygame.draw.rect(card_surf, border_color, card_surf.get_rect(),
                             width=int(border_w), border_radius=20)

            surface.blit(card_surf, (x, y))

            # Character image centered in card
            img = images[i]
            if is_sel:
                img = pygame.transform.smoothscale(img, (220, 220))
            img_rect = img.get_rect(center=(x + w // 2, y + h // 2 - 35))
            surface.blit(img, img_rect)

            # Label
            label_surf = self.font_body.render(labels[i], True,
                                               COLOR_GOLD_BRIGHT if is_sel else COLOR_CREAM)
            lr = label_surf.get_rect(center=(x + w // 2, y + h - 50))
            surface.blit(label_surf, lr)

            # Selection glow aura
            if is_sel:
                glow_alpha = int(45 + 30 * math.sin(self.elapsed * 5))
                glow = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*COLOR_GOLD[:3], glow_alpha),
                                 glow.get_rect(), border_radius=24)
                surface.blit(glow, (x - 12, y - 12))

                # Display devotee descriptions at bottom center
                desc_surf = self.font_body.render(descs[i], True, COLOR_CREAM)
                dr = desc_surf.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 130))
                
                # Draw small desc plate
                plate = pygame.Surface((dr.width + 40, dr.height + 16), pygame.SRCALPHA)
                pygame.draw.rect(plate, (0, 0, 0, 160), plate.get_rect(), border_radius=8)
                pygame.draw.rect(plate, COLOR_SAFFRON, plate.get_rect(), width=2, border_radius=8)
                
                surface.blit(plate, (dr.x - 20, dr.y - 8))
                surface.blit(desc_surf, dr)

        # Instructions hint
        hint = "◄ ► or Mouse to select  •  ENTER or Tap to confirm"
        hint_surf = self.font_small.render(hint, True, COLOR_GOLD_DIM)
        hr = hint_surf.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 50))
        surface.blit(hint_surf, hr)

        # Fade-in
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
