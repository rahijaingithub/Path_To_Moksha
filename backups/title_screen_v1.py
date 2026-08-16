"""
title_screen.py — The game's Title Screen scene.
Displays the game title over the temple background with animated elements.
"""
import math
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_CHARACTER_SELECT,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM,
    COLOR_WHITE, COLOR_CREAM, COLOR_SAFFRON, COLOR_LOTUS_PINK,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
)


class TitleScreen(Scene):
    """Beautiful animated title screen for The Path to Moksha."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.elapsed = 0.0

        # Animation state
        self.fade_alpha = 255  # fade-in from black
        self.pulse_timer = 0.0
        self.particle_timer = 0.0
        self.particles = []

    def on_enter(self, **kwargs):
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.particles = []

        # Load assets
        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False,
            scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )

        # Fonts
        self.font_title = self.assets.load_font(None, FONT_SIZE_TITLE)
        self.font_subtitle = self.assets.load_font(None, FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, FONT_SIZE_SMALL)

    def handle_events(self, events, input_mgr):
        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.JUMP]:
            self.manager.switch_to(SCENE_CHARACTER_SELECT)

        # Also allow mouse click anywhere to proceed
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.elapsed > 1.0:
                self.manager.switch_to(SCENE_CHARACTER_SELECT)

    def update(self, dt):
        self.elapsed += dt
        self.pulse_timer += dt

        # Fade in
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 200 * dt)

        # Spawn floating particles (lotus petals / golden sparkles)
        self.particle_timer += dt
        if self.particle_timer > 0.15 and len(self.particles) < 40:
            self.particle_timer = 0
            import random
            x = random.randint(0, LOGICAL_WIDTH)
            speed = random.uniform(20, 60)
            size = random.randint(2, 5)
            color = random.choice([COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_LOTUS_PINK, COLOR_SAFFRON])
            lifetime = random.uniform(3.0, 6.0)
            self.particles.append({
                "x": x, "y": LOGICAL_HEIGHT + 10,
                "speed": speed, "size": size, "color": color,
                "lifetime": lifetime, "age": 0.0,
                "drift": random.uniform(-15, 15),
            })

        # Update particles
        for p in self.particles:
            p["age"] += dt
            p["y"] -= p["speed"] * dt
            p["x"] += p["drift"] * dt
        self.particles = [p for p in self.particles if p["age"] < p["lifetime"]]

    def draw(self, surface):
        # Background
        surface.blit(self.bg, (0, 0))

        # Dark gradient overlay at top and bottom for text readability
        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        for i in range(200):
            alpha = int(180 * (1 - i / 200))
            pygame.draw.line(overlay, (18, 12, 28, alpha), (0, i), (LOGICAL_WIDTH, i))
        for i in range(250):
            alpha = int(200 * (1 - i / 250))
            y = LOGICAL_HEIGHT - 1 - i
            pygame.draw.line(overlay, (18, 12, 28, alpha), (0, y), (LOGICAL_WIDTH, y))
        surface.blit(overlay, (0, 0))

        # Floating particles
        for p in self.particles:
            alpha = int(255 * (1 - p["age"] / p["lifetime"]))
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"][:3], alpha), (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))

        # ── Title Text ──
        # Pulsing glow
        glow_scale = 1.0 + 0.03 * math.sin(self.pulse_timer * 2)
        title_text = "The Path to Moksha"

        # Shadow
        shadow_surf = self.font_title.render(title_text, True, (0, 0, 0))
        sr = shadow_surf.get_rect(center=(LOGICAL_WIDTH // 2 + 3, 160 + 3))
        surface.blit(shadow_surf, sr)

        # Main title
        title_surf = self.font_title.render(title_text, True, COLOR_GOLD_BRIGHT)
        tr = title_surf.get_rect(center=(LOGICAL_WIDTH // 2, 160))
        surface.blit(title_surf, tr)

        # Subtitle
        sub_text = "An Arcade Pilgrimage — Digambar Jain Tradition"
        sub_surf = self.font_subtitle.render(sub_text, True, COLOR_CREAM)
        sub_r = sub_surf.get_rect(center=(LOGICAL_WIDTH // 2, 220))
        surface.blit(sub_surf, sub_r)

        # Decorative line
        line_y = 255
        line_w = 400
        pygame.draw.line(surface, COLOR_GOLD_DIM,
                         (LOGICAL_WIDTH // 2 - line_w // 2, line_y),
                         (LOGICAL_WIDTH // 2 + line_w // 2, line_y), 2)
        # Small diamond at center
        cx, cy = LOGICAL_WIDTH // 2, line_y
        diamond = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)]
        pygame.draw.polygon(surface, COLOR_GOLD, diamond)

        # Tagline
        tag_text = '"Guidance over Gating"'
        tag_surf = self.font_body.render(tag_text, True, COLOR_SAFFRON)
        tag_r = tag_surf.get_rect(center=(LOGICAL_WIDTH // 2, 290))
        surface.blit(tag_surf, tag_r)

        # ── "Press ENTER to begin" with pulse ──
        if self.elapsed > 0.8:
            alpha = int(128 + 127 * math.sin(self.pulse_timer * 3))
            prompt_surf = self.font_body.render("Press ENTER or Tap to Begin", True, COLOR_WHITE)
            prompt_surf.set_alpha(alpha)
            pr = prompt_surf.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 120))
            surface.blit(prompt_surf, pr)

        # Bottom credit
        credit = "Jai Jinendra — Parasparopagraho Jīvānām"
        credit_surf = self.font_small.render(credit, True, COLOR_GOLD_DIM)
        cr = credit_surf.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40))
        surface.blit(credit_surf, cr)

        # Fade-in overlay
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
