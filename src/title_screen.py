"""
title_screen.py — The game's Title Screen scene.
Displays the game title over the temple background with animated elements.
"""
import math
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_CHARACTER_SELECT, SCENE_OPTIONS, SCENE_PLAYER_SELECT, SCENE_TUTORIAL,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM,
    COLOR_WHITE, COLOR_CREAM, COLOR_SAFFRON, COLOR_LOTUS_PINK, COLOR_BLUE_WATER,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
    LEVEL_NAMES, GAME_MODES, DEFAULT_GAME_MODE,
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
        # Layout: Start Game → Options → Exit Game → Fullscreen Toggle
        self.start_btn_rect      = pygame.Rect(LOGICAL_WIDTH // 2 - 220, LOGICAL_HEIGHT - 460, 440, 65)
        self.options_btn_rect    = pygame.Rect(LOGICAL_WIDTH // 2 - 220, LOGICAL_HEIGHT - 375, 440, 65)
        self.exit_btn_rect       = pygame.Rect(LOGICAL_WIDTH // 2 - 220, LOGICAL_HEIGHT - 290, 440, 65)
        self.fullscreen_btn_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 220, LOGICAL_HEIGHT - 205, 440, 65)

        self.hover_start      = False
        self.hover_options    = False
        self.hover_exit       = False
        self.hover_fullscreen = False
        self.starting_level = 1
        self._game_mode = DEFAULT_GAME_MODE

    def on_enter(self, **kwargs):
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.particles = []
        self.hover_start      = False
        self.hover_options    = False
        self.hover_exit       = False
        self.hover_fullscreen = False

        # Load or initialize starting level and game mode from shared state
        self.starting_level = self.manager.shared.get("starting_level", 1)
        self._game_mode = self.manager.shared.get("game_mode", DEFAULT_GAME_MODE)

        # Load assets
        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False, scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )

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
        self.assets.play_music("bgm_loop.wav", volume=self.manager.shared.get("music_volume", 0.35))

        # Menu navigation index (0: Start, 1: Options, 2: Exit, 3: Fullscreen)
        self.selected_index = 0

    def handle_events(self, events, input_mgr):
        # Controller / Keyboard Menu Navigation (Up / Down)
        if input_mgr.just_pressed[input_mgr.MENU_UP]:
            self.selected_index = (self.selected_index - 1) % 4
            self.assets.play_sound("jump.wav", volume=0.12)
        elif input_mgr.just_pressed[input_mgr.MENU_DOWN]:
            self.selected_index = (self.selected_index + 1) % 4
            self.assets.play_sound("jump.wav", volume=0.12)

        # Controller / Keyboard Selection
        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
            if self.selected_index == 0:
                self.assets.play_sound("level_complete.wav", volume=0.35)
                self.manager.shared["game_mode"] = self._game_mode
                self.manager.switch_to(SCENE_PLAYER_SELECT)
            elif self.selected_index == 1:
                self.assets.play_sound("jump.wav", volume=0.2)
                self.manager.switch_to(SCENE_OPTIONS)
            elif self.selected_index == 2:
                self.assets.play_sound("box_open.wav", volume=0.2)
                pygame.quit()
                import sys
                sys.exit()
            elif self.selected_index == 3:
                self.assets.play_sound("jump.wav", volume=0.2)
                input_mgr.just_pressed[input_mgr.FULLSCREEN] = True

        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            pygame.quit()
            import sys
            sys.exit()

        # Mouse click triggers
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.elapsed > 0.5:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y
                if self.start_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("level_complete.wav", volume=0.35)
                    self.manager.shared["game_mode"] = self._game_mode
                    self.manager.switch_to(SCENE_PLAYER_SELECT)
                elif self.options_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("jump.wav", volume=0.2)
                    self.manager.switch_to(SCENE_OPTIONS)
                elif self.exit_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("box_open.wav", volume=0.2)
                    pygame.quit()
                    import sys
                    sys.exit()
                elif self.fullscreen_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("jump.wav", volume=0.2)
                    input_mgr.just_pressed[input_mgr.FULLSCREEN] = True

    def update(self, dt):
        self.elapsed += dt
        self.pulse_timer += dt

        # Fade in
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 200 * dt)

        # Track mouse hovers (sync mouse hover with selected_index)
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y

        if self.start_btn_rect.collidepoint(mx, my):
            self.selected_index = 0
        elif self.options_btn_rect.collidepoint(mx, my):
            self.selected_index = 1
        elif self.exit_btn_rect.collidepoint(mx, my):
            self.selected_index = 2
        elif self.fullscreen_btn_rect.collidepoint(mx, my):
            self.selected_index = 3

        self.hover_start      = (self.selected_index == 0)
        self.hover_options    = (self.selected_index == 1)
        self.hover_exit       = (self.selected_index == 2)
        self.hover_fullscreen = (self.selected_index == 3)



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

        # ── Interactive Main Buttons (Start, Options, Exit) ──
        main_buttons = [
            {"rect": self.start_btn_rect,   "hover": self.hover_start,   "text": "▶  START GAME"},
            {"rect": self.options_btn_rect, "hover": self.hover_options, "text": "⚙  OPTIONS"},
            {"rect": self.exit_btn_rect,    "hover": self.hover_exit,    "text": "🚪  EXIT GAME"},
        ]

        for btn in main_buttons:
            r = btn["rect"]
            hover = btn["hover"]

            btn_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            if hover:
                # Hover state: Warm gold background with bright glowing border
                pygame.draw.rect(btn_surf, (*COLOR_GOLD[:3], 230), btn_surf.get_rect(), border_radius=14)
                pygame.draw.rect(btn_surf, COLOR_GOLD_BRIGHT, btn_surf.get_rect(), width=3, border_radius=14)
            else:
                # Idle state: Completely transparent background with subtle thin gold border
                pygame.draw.rect(btn_surf, (0, 0, 0, 0), btn_surf.get_rect(), border_radius=14)
                pygame.draw.rect(btn_surf, COLOR_GOLD_DIM, btn_surf.get_rect(), width=2, border_radius=14)
            
            surface.blit(btn_surf, r)

            txt_col = COLOR_BG_DARK if hover else COLOR_WHITE
            txt_surf = self.font_body.render(btn["text"], True, txt_col)
            txt_rect = txt_surf.get_rect(center=r.center)
            surface.blit(txt_surf, txt_rect)

            # Side arrow indicators on hover
            if hover:
                arr_l_ind = self.font_body.render("►", True, COLOR_GOLD_BRIGHT)
                arr_r_ind = self.font_body.render("◄", True, COLOR_GOLD_BRIGHT)
                surface.blit(arr_l_ind, arr_l_ind.get_rect(midright=(r.left - 15, r.centery)))
                surface.blit(arr_r_ind, arr_r_ind.get_rect(midleft=(r.right + 15, r.centery)))

        # ── Clean Fullscreen Checkbox Option (No Golden Button Box) ──
        r_fs = self.fullscreen_btn_rect
        hover_fs = self.hover_fullscreen
        is_fs = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)

        fs_col = COLOR_GOLD_BRIGHT if hover_fs else COLOR_WHITE
        box_border_col = COLOR_GOLD_BRIGHT if hover_fs else COLOR_GOLD_DIM

        # Draw Checkbox Square
        box_size = 28
        box_x = r_fs.centerx - 140
        box_y = r_fs.centery - box_size // 2
        box_rect = pygame.Rect(box_x, box_y, box_size, box_size)

        pygame.draw.rect(surface, (*COLOR_BG_DARK, 220), box_rect, border_radius=6)
        pygame.draw.rect(surface, box_border_col, box_rect, width=2, border_radius=6)

        # Draw checkmark indicator when checked
        if is_fs:
            inner_rect = box_rect.inflate(-8, -8)
            pygame.draw.rect(surface, COLOR_GOLD_BRIGHT, inner_rect, border_radius=3)

        # Checkbox label text
        fs_txt_surf = self.font_body.render("FULLSCREEN MODE", True, fs_col)
        fs_txt_rect = fs_txt_surf.get_rect(midleft=(box_rect.right + 15, r_fs.centery))
        surface.blit(fs_txt_surf, fs_txt_rect)

        # Focus arrow indicators when selected
        if hover_fs:
            arr_l_ind = self.font_body.render("►", True, COLOR_GOLD_BRIGHT)
            arr_r_ind = self.font_body.render("◄", True, COLOR_GOLD_BRIGHT)
            surface.blit(arr_l_ind, arr_l_ind.get_rect(midright=(box_rect.left - 15, r_fs.centery)))
            surface.blit(arr_r_ind, arr_r_ind.get_rect(midleft=(fs_txt_rect.right + 15, r_fs.centery)))


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
