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
    COLOR_WHITE, COLOR_CREAM, COLOR_SAFFRON, COLOR_LOTUS_PINK, COLOR_BLUE_WATER,
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

        # Buttons (Logical coordinates)
        self.start_btn_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 220, LOGICAL_HEIGHT - 280, 440, 64)
        self.exit_btn_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 220, LOGICAL_HEIGHT - 190, 440, 64)

        self.hover_start = False
        self.hover_exit = False

    def on_enter(self, **kwargs):
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.particles = []
        self.hover_start = False
        self.hover_exit = False

        # Load assets
        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False,
            scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )

        # Pre-populate snowfall so the screen starts with falling snow
        import random
        for _ in range(40):
            x = random.randint(0, LOGICAL_WIDTH)
            speed = random.uniform(50, 120)
            y = random.randint(0, LOGICAL_HEIGHT)
            size = random.randint(2, 6)
            sway_speed = random.uniform(1.0, 3.0)
            sway_amount = random.uniform(15, 40)
            color = random.choice([COLOR_WHITE, COLOR_BLUE_WATER, (255, 255, 255)])
            alpha = random.randint(120, 245)
            age = y / speed
            lifetime = (LOGICAL_HEIGHT + 20) / speed
            self.particles.append({
                "x": x, "y": y,
                "speed": speed, "size": size, "color": color, "alpha": alpha,
                "lifetime": lifetime, "age": age,
                "sway_speed": sway_speed, "sway_amount": sway_amount,
                "sway_offset": random.uniform(0, 2 * math.pi)
            })

        # Fonts
        self.font_title = self.assets.load_font(None, FONT_SIZE_TITLE)
        self.font_subtitle = self.assets.load_font(None, FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, FONT_SIZE_SMALL)

        # Play title bgm if not already playing
        self.assets.play_music("bgm_loop.wav", volume=0.35)

    def handle_events(self, events, input_mgr):
        # Keyboard entry
        if input_mgr.just_pressed[input_mgr.ACTION]:
            self.assets.play_sound("level_complete.wav", volume=0.35)
            self.manager.switch_to(SCENE_CHARACTER_SELECT)
        if input_mgr.just_pressed[input_mgr.BACK]:
            pygame.quit()
            import sys
            sys.exit()

        # Mouse click triggers
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.elapsed > 0.8:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y
                if self.start_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("level_complete.wav", volume=0.35)
                    self.manager.switch_to(SCENE_CHARACTER_SELECT)
                elif self.exit_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("box_open.wav", volume=0.2)
                    pygame.quit()
                    import sys
                    sys.exit()

    def update(self, dt):
        self.elapsed += dt
        self.pulse_timer += dt

        # Fade in
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 200 * dt)

        # Track button hovers & trigger SFX on entry
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
        
        new_hover_start = self.start_btn_rect.collidepoint(mx, my)
        if new_hover_start and not self.hover_start:
            self.assets.play_sound("jump.wav", volume=0.12)
        self.hover_start = new_hover_start

        new_hover_exit = self.exit_btn_rect.collidepoint(mx, my)
        if new_hover_exit and not self.hover_exit:
            self.assets.play_sound("jump.wav", volume=0.12)
        self.hover_exit = new_hover_exit

        # Spawn falling snowflakes
        self.particle_timer += dt
        if self.particle_timer > 0.08 and len(self.particles) < 80:
            self.particle_timer = 0
            import random
            x = random.randint(0, LOGICAL_WIDTH)
            speed = random.uniform(50, 120)
            size = random.randint(2, 6)
            sway_speed = random.uniform(1.0, 3.0)
            sway_amount = random.uniform(15, 40)
            color = random.choice([COLOR_WHITE, COLOR_BLUE_WATER, (255, 255, 255)])
            alpha = random.randint(120, 245)
            lifetime = (LOGICAL_HEIGHT + 20) / speed
            self.particles.append({
                "x": x, "y": -10,
                "speed": speed, "size": size, "color": color, "alpha": alpha,
                "lifetime": lifetime, "age": 0.0,
                "sway_speed": sway_speed, "sway_amount": sway_amount,
                "sway_offset": random.uniform(0, 2 * math.pi)
            })

        # Update particles (snowfall)
        for p in self.particles:
            p["age"] += dt
            p["y"] += p["speed"] * dt
            p["x"] += math.sin(self.elapsed * p["sway_speed"] + p["sway_offset"]) * p["sway_amount"] * dt
        self.particles = [p for p in self.particles if p["age"] < p["lifetime"] and p["x"] >= -20 and p["x"] <= LOGICAL_WIDTH + 20]

    def draw(self, surface):
        # Background
        surface.blit(self.bg, (0, 0))

        # Dark gradient overlay for text readability (using the new COLOR_BG_DARK)
        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        for i in range(350): # Deepened top gradient to cover title and subtitle area
            alpha = int(220 * (1 - i / 350))
            pygame.draw.line(overlay, (*COLOR_BG_DARK, alpha), (0, i), (LOGICAL_WIDTH, i))
        for i in range(350): # Bottom gradient
            alpha = int(210 * (1 - i / 350))
            y = LOGICAL_HEIGHT - 1 - i
            pygame.draw.line(overlay, (*COLOR_BG_DARK, alpha), (0, y), (LOGICAL_WIDTH, y))
        surface.blit(overlay, (0, 0))

        # Draw falling snowflakes
        for p in self.particles:
            life_ratio = min(1.0, max(0.0, p["age"] / p["lifetime"]))
            alpha = int(p["alpha"] * (1.0 - life_ratio * 0.7))
            sz = p["size"]
            ps = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"][:3], alpha), (sz, sz), sz)
            surface.blit(ps, (int(p["x"]) - sz, int(p["y"]) - sz))

        # ── Title Text ──
        # Pulsing text color shifting
        title_text = "The Path to Moksha"
        pulse_col = (
            max(0, min(255, int(COLOR_GOLD_BRIGHT[0] + 10 * math.sin(self.pulse_timer * 2)))),
            max(0, min(255, int(COLOR_GOLD_BRIGHT[1] + 15 * math.sin(self.pulse_timer * 2)))),
            max(0, min(255, int(COLOR_GOLD_BRIGHT[2] + 20 * math.sin(self.pulse_timer * 2))))
        )

        # Shadow
        shadow_surf = self.font_title.render(title_text, True, (0, 0, 0))
        sr = shadow_surf.get_rect(center=(LOGICAL_WIDTH // 2 + 4, 160 + 4))
        surface.blit(shadow_surf, sr)

        # Main title
        title_surf = self.font_title.render(title_text, True, pulse_col)
        tr = title_surf.get_rect(center=(LOGICAL_WIDTH // 2, 160))
        surface.blit(title_surf, tr)

        # Subtitle (using COLOR_BG_DARK for maximum contrast against the light background)
        sub_text = "Jinalaya Dev Darshan"
        sub_surf = self.font_subtitle.render(sub_text, True, COLOR_BG_DARK)
        sub_r = sub_surf.get_rect(center=(LOGICAL_WIDTH // 2, 225))
        surface.blit(sub_surf, sub_r)

        # Decorative line
        line_y = 260
        line_w = 450
        pygame.draw.line(surface, COLOR_GOLD_DIM,
                         (LOGICAL_WIDTH // 2 - line_w // 2, line_y),
                         (LOGICAL_WIDTH // 2 + line_w // 2, line_y), 2)

        # ── Interactive Styled Buttons ──
        buttons = [
            {"rect": self.start_btn_rect, "hover": self.hover_start, "text": "START PILGRIMAGE", "color": COLOR_GOLD},
            {"rect": self.exit_btn_rect, "hover": self.hover_exit, "text": "EXIT PILGRIMAGE", "color": COLOR_SAFFRON}
        ]

        for btn in buttons:
            r = btn["rect"]
            hover = btn["hover"]
            
            # Hover scaling
            scale_offset = 8 if hover else 0
            draw_rect = r.inflate(scale_offset, scale_offset)
            
            # Button background
            btn_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            bg_alpha = 230 if hover else 170
            bg_color = (45, 30, 65, bg_alpha) if hover else (25, 18, 38, bg_alpha)
            pygame.draw.rect(btn_surf, bg_color, btn_surf.get_rect(), border_radius=16)
            
            # Glowing borders
            border_color = COLOR_GOLD_BRIGHT if hover else COLOR_GOLD_DIM
            border_w = 3 if hover else 1.5
            pygame.draw.rect(btn_surf, border_color, btn_surf.get_rect(), width=int(border_w), border_radius=16)
            
            surface.blit(btn_surf, draw_rect.topleft)

            # Button text
            t_surf = self.font_body.render(btn["text"], True, COLOR_WHITE if hover else COLOR_CREAM)
            tr = t_surf.get_rect(center=draw_rect.center)
            surface.blit(t_surf, tr)

            # Arrow indicators on hover
            if hover:
                glow_alpha = int(140 + 70 * math.sin(self.pulse_timer * 6))
                arr_l = self.font_body.render("►", True, (*COLOR_GOLD_BRIGHT[:3], glow_alpha))
                arr_r = self.font_body.render("◄", True, (*COLOR_GOLD_BRIGHT[:3], glow_alpha))
                surface.blit(arr_l, arr_l.get_rect(midright=(draw_rect.left - 15, draw_rect.centery)))
                surface.blit(arr_r, arr_r.get_rect(midleft=(draw_rect.right + 15, draw_rect.centery)))

        # Bottom credit
        credit = "Jai Jinendra — Parasparopagraho Jīvānām"
        credit_surf = self.font_small.render(credit, True, COLOR_GOLD_DIM)
        cr = credit_surf.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 45))
        surface.blit(credit_surf, cr)

        # Bottom right developer credit
        dev_text = "Developed by Rahi Jain and Shweta Ajmera, Digamber Paathshala, JSOT"
        dev_surf = self.font_small.render(dev_text, True, COLOR_GOLD_DIM)
        dr = dev_surf.get_rect(bottomright=(LOGICAL_WIDTH - 30, LOGICAL_HEIGHT - 30))
        surface.blit(dev_surf, dr)

        # Fade-in overlay
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
