"""
options_scene.py — Options and Settings menu for The Path to Moksha.
Allows configuring Game Mode, Starting Level, and Audio Volume.
"""
import math
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_TITLE, SCENE_TUTORIAL, SCENE_OPTIONS,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM,
    COLOR_WHITE, COLOR_SAFFRON, COLOR_BLUE_WATER,
    GAME_FONT_SIZE_TITLE, GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL,
    LEVEL_NAMES, GAME_MODES, DEFAULT_GAME_MODE,
)



class OptionsScene(Scene):
    """Options and Settings screen."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.elapsed = 0.0

        # Settings state
        self.game_mode = DEFAULT_GAME_MODE
        self.starting_level = 1
        self.music_volume = 0.7
        self.sfx_volume = 0.8

        # UI elements layout
        self.mode_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 250, 310, 500, 60)
        self.level_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 250, 400, 500, 60)
        self.music_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 250, 490, 500, 60)
        self.sfx_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 250, 580, 500, 60)
        self.tutorial_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 250, 670, 500, 60)
        self.back_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 200, 860, 400, 64)

        # Hover states
        self.hover_mode = False
        self.hover_level = False
        self.hover_music = False
        self.hover_sfx = False
        self.hover_tutorial = False
        self.hover_back = False

        self.bg = None
        self.particles = []

    def on_enter(self, **kwargs):
        self.elapsed = 0.0
        self.selected_index = 0  # 0: Mode, 1: Level, 2: Music, 3: SFX, 4: Tutorial, 5: Save & Return
        self.game_mode = self.manager.shared.get("game_mode", DEFAULT_GAME_MODE)
        self.starting_level = self.manager.shared.get("starting_level", 1)
        self.music_volume = self.manager.shared.get("music_volume", 0.7)
        self.sfx_volume = self.manager.shared.get("sfx_volume", 0.8)

        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False, scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )

        # Fonts
        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_TITLE)
        self.font_subtitle = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

    def handle_events(self, events, input_mgr):
        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            self._save_and_exit()
            return

        # Controller / Keyboard Navigation Up / Down
        if input_mgr.just_pressed[input_mgr.MENU_UP] or input_mgr.just_pressed[input_mgr.UP]:
            self.selected_index = (self.selected_index - 1) % 6
            self.assets.play_sound("jump.wav", volume=0.15)
        elif input_mgr.just_pressed[input_mgr.MENU_DOWN]:
            self.selected_index = (self.selected_index + 1) % 6
            self.assets.play_sound("jump.wav", volume=0.15)

        # Controller / Keyboard Selection or Horizontal adjustment
        is_select = input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]
        is_left = input_mgr.just_pressed[input_mgr.MENU_LEFT] or input_mgr.just_pressed[input_mgr.LEFT]
        is_right = input_mgr.just_pressed[input_mgr.MENU_RIGHT] or input_mgr.just_pressed[input_mgr.RIGHT]

        if is_select or is_left or is_right:
            step = -1 if is_left else 1
            if self.selected_index == 0 and is_select:
                idx = GAME_MODES.index(self.game_mode)
                self.game_mode = GAME_MODES[(idx + step) % len(GAME_MODES)]
                if self.game_mode == "kid" and (self.starting_level > 2 or self.starting_level < 1):
                    self.starting_level = 1
                elif self.game_mode != "developer" and self.starting_level < 1:
                    self.starting_level = 1
                self.assets.play_sound("jump.wav", volume=0.15)
            elif self.selected_index == 1 and (is_select or is_left or is_right):
                DEV_SEQ = [1, -1, 2, -2, 3, 4]
                if self.game_mode == "developer":
                    cur_idx = DEV_SEQ.index(self.starting_level) if self.starting_level in DEV_SEQ else 0
                    self.starting_level = DEV_SEQ[(cur_idx + step) % len(DEV_SEQ)]
                else:
                    # Kid and Standard both cap at Level 2
                    max_level = 2
                    self.starting_level = (self.starting_level % max_level) + 1 if step > 0 else ((self.starting_level - 2) % max_level) + 1
                self.assets.play_sound("jump.wav", volume=0.15)
            elif self.selected_index == 2 and (is_select or is_left or is_right):
                v_steps = [0.0, 0.3, 0.7, 1.0]
                closest = min(v_steps, key=lambda x: abs(x - self.music_volume))
                idx = v_steps.index(closest)
                self.music_volume = v_steps[(idx + step) % len(v_steps)]
                self.assets.set_music_volume(self.music_volume)
                self.assets.play_sound("jump.wav", volume=0.15)
            elif self.selected_index == 3 and (is_select or is_left or is_right):
                v_steps = [0.0, 0.3, 0.7, 1.0]
                closest = min(v_steps, key=lambda x: abs(x - self.sfx_volume))
                idx = v_steps.index(closest)
                self.sfx_volume = v_steps[(idx + step) % len(v_steps)]
                self.assets.play_sound("jump.wav", volume=self.sfx_volume)
            elif self.selected_index == 4 and is_select:
                self.assets.play_sound("jump.wav", volume=0.2)
                self.manager.switch_to(SCENE_TUTORIAL, return_scene=SCENE_OPTIONS)

            elif self.selected_index == 5 and is_select:
                self.assets.play_sound("box_open.wav", volume=0.2)
                self._save_and_exit()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y

                # Mode click -> cycle
                if self.mode_rect.collidepoint(mx, my):
                    self.selected_index = 0
                    idx = GAME_MODES.index(self.game_mode)
                    self.game_mode = GAME_MODES[(idx + 1) % len(GAME_MODES)]
                    # Clamp level when leaving developer mode
                    if self.game_mode != "developer" and self.starting_level not in (1, 2):
                        self.starting_level = 1
                    self.assets.play_sound("jump.wav", volume=0.15)

                # Level click -> cycle
                elif self.level_rect.collidepoint(mx, my):
                    self.selected_index = 1
                    DEV_SEQ = [1, -1, 2, -2, 3, 4]
                    if self.game_mode == "developer":
                        cur_idx = DEV_SEQ.index(self.starting_level) if self.starting_level in DEV_SEQ else 0
                        self.starting_level = DEV_SEQ[(cur_idx + 1) % len(DEV_SEQ)]
                    else:
                        # Kid and Standard both cap at Level 2
                        max_level = 2
                        self.starting_level = self.starting_level + 1 if self.starting_level < max_level else 1
                    self.assets.play_sound("jump.wav", volume=0.15)


                # Music volume click -> cycle (0.0 -> 0.3 -> 0.7 -> 1.0)
                elif self.music_rect.collidepoint(mx, my):
                    self.selected_index = 2
                    v_steps = [0.0, 0.3, 0.7, 1.0]
                    closest = min(v_steps, key=lambda x: abs(x - self.music_volume))
                    idx = v_steps.index(closest)
                    self.music_volume = v_steps[(idx + 1) % len(v_steps)]
                    self.assets.set_music_volume(self.music_volume)
                    self.assets.play_sound("jump.wav", volume=0.15)

                # SFX volume click -> cycle (0.0 -> 0.3 -> 0.7 -> 1.0)
                elif self.sfx_rect.collidepoint(mx, my):
                    self.selected_index = 3
                    v_steps = [0.0, 0.3, 0.7, 1.0]
                    closest = min(v_steps, key=lambda x: abs(x - self.sfx_volume))
                    idx = v_steps.index(closest)
                    self.sfx_volume = v_steps[(idx + 1) % len(v_steps)]
                    self.assets.play_sound("jump.wav", volume=self.sfx_volume)

                # Tutorial button
                elif self.tutorial_rect.collidepoint(mx, my):
                    self.selected_index = 4
                    self.assets.play_sound("jump.wav", volume=0.2)
                    self.manager.switch_to(SCENE_TUTORIAL, return_scene=SCENE_OPTIONS)


                # Back button
                elif self.back_rect.collidepoint(mx, my):
                    self.selected_index = 5
                    self.assets.play_sound("box_open.wav", volume=0.2)
                    self._save_and_exit()

    def _save_and_exit(self):
        self.manager.shared["game_mode"] = self.game_mode
        self.manager.shared["starting_level"] = self.starting_level
        self.manager.shared["music_volume"] = self.music_volume
        self.manager.shared["sfx_volume"] = self.sfx_volume
        self.manager.switch_to(SCENE_TITLE)

    def update(self, dt):
        self.elapsed += dt
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y

        if self.mode_rect.collidepoint(mx, my):
            self.selected_index = 0
        elif self.level_rect.collidepoint(mx, my):
            self.selected_index = 1
        elif self.music_rect.collidepoint(mx, my):
            self.selected_index = 2
        elif self.sfx_rect.collidepoint(mx, my):
            self.selected_index = 3
        elif self.tutorial_rect.collidepoint(mx, my):
            self.selected_index = 4
        elif self.back_rect.collidepoint(mx, my):
            self.selected_index = 5

        self.hover_mode = (self.selected_index == 0)
        self.hover_level = (self.selected_index == 1)
        self.hover_music = (self.selected_index == 2)
        self.hover_sfx = (self.selected_index == 3)
        self.hover_tutorial = (self.selected_index == 4)
        self.hover_back = (self.selected_index == 5)


    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))

        # Dark overlay
        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 18, 32, 220))
        surface.blit(overlay, (0, 0))

        # Title Header
        title_surf = self.font_title.render("GAME OPTIONS", True, COLOR_GOLD_BRIGHT)
        title_rect = title_surf.get_rect(center=(LOGICAL_WIDTH // 2, 140))
        surface.blit(title_surf, title_rect)

        sub_surf = self.font_body.render("Customize your pilgrimage experience", True, COLOR_WHITE)
        sub_rect = sub_surf.get_rect(center=(LOGICAL_WIDTH // 2, 210))
        surface.blit(sub_surf, sub_rect)

        # Mode text
        mode_labels = {"kid": "🧒 Kid Mode (Default)", "standard": "🧘 Standard Mode", "developer": "🛠 Developer Mode"}
        mode_str = f"Game Mode:  {mode_labels.get(self.game_mode, self.game_mode)}"

        # Level text
        _trans_labels = {-1: "🏛 Transition 1 (Jyot Temple)", -2: "🙏 Transition 2 (Parshvanath)"}
        if self.starting_level in _trans_labels:
            lvl_name = f"🛠 DEV: {_trans_labels[self.starting_level]}"
        else:
            lvl_name = f"Level {self.starting_level} ({LEVEL_NAMES.get(self.starting_level, '???')})"
        level_str = f"Starting Level:  {lvl_name}"

        music_pct = int(self.music_volume * 100)
        music_str = f"Music Volume:  {music_pct}%"

        sfx_pct = int(self.sfx_volume * 100)
        sfx_str = f"Sound Effects:  {sfx_pct}%"

        buttons = [
            {"rect": self.mode_rect,     "hover": self.hover_mode,     "text": mode_str},
            {"rect": self.level_rect,    "hover": self.hover_level,    "text": level_str},
            {"rect": self.music_rect,    "hover": self.hover_music,    "text": music_str},
            {"rect": self.sfx_rect,      "hover": self.hover_sfx,      "text": sfx_str},
            {"rect": self.tutorial_rect, "hover": self.hover_tutorial, "text": "📖 How to Play & Controls"},
        ]

        for b in buttons:
            rect = b["rect"]
            hover = b["hover"]
            bg_col = COLOR_GOLD if hover else COLOR_BG_DARK
            border_col = COLOR_GOLD_BRIGHT if hover else COLOR_GOLD_DIM

            btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(btn_surf, (*bg_col[:3], 230), btn_surf.get_rect(), border_radius=10)
            pygame.draw.rect(btn_surf, border_col, btn_surf.get_rect(), width=2 if hover else 1, border_radius=10)
            surface.blit(btn_surf, rect)

            text_col = COLOR_BG_DARK if hover else COLOR_WHITE
            txt_s = self.font_body.render(b["text"], True, text_col)
            txt_r = txt_s.get_rect(center=rect.center)
            surface.blit(txt_s, txt_r)

        # Controller Status Card
        pad_name = self.input_mgr.gamepad_name if self.input_mgr.has_gamepad else "Keyboard & Mouse"
        pad_icon = "🎮 Controller Connected: " if self.input_mgr.has_gamepad else "⌨ Input Mode: "
        pad_str = f"{pad_icon}{pad_name}"

        pad_card_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 400, 790, 800, 48)
        pad_surf = pygame.Surface((pad_card_rect.width, pad_card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(pad_surf, (20, 32, 54, 220), pad_surf.get_rect(), border_radius=8)
        pygame.draw.rect(pad_surf, COLOR_GOLD_BRIGHT if self.input_mgr.has_gamepad else COLOR_GOLD_DIM, pad_surf.get_rect(), width=1, border_radius=8)
        surface.blit(pad_surf, pad_card_rect)

        pad_txt = self.font_small.render(pad_str, True, COLOR_GOLD_BRIGHT if self.input_mgr.has_gamepad else COLOR_WHITE)
        surface.blit(pad_txt, pad_txt.get_rect(center=pad_card_rect.center))

        # Back Button
        bg_col = COLOR_GOLD if self.hover_back else COLOR_SAFFRON
        border_col = COLOR_GOLD_BRIGHT if self.hover_back else COLOR_GOLD
        btn_surf = pygame.Surface((self.back_rect.width, self.back_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (*bg_col[:3], 240), btn_surf.get_rect(), border_radius=12)
        pygame.draw.rect(btn_surf, border_col, btn_surf.get_rect(), width=3, border_radius=12)
        surface.blit(btn_surf, self.back_rect)

        back_txt = self.font_body.render("Save & Return to Title", True, COLOR_BG_DARK if self.hover_back else COLOR_WHITE)
        back_r = back_txt.get_rect(center=self.back_rect.center)
        surface.blit(back_txt, back_r)

