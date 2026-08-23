"""
player_select_scene.py — Player Profile Selection and New Player Entry scene.
Supports full controller navigation:
  - Virtual on-screen keyboard (focus='vkb') for typing a new name
  - Profile list navigation (focus='profile') for selecting saved profiles
  - MENU_LEFT/RIGHT/UP/DOWN moves within each focus area
  - MENU_DOWN from keyboard area shifts focus to profiles (and vice versa)
  - MENU_SELECT / ACTION confirms the highlighted key or profile
  - BACK / MENU_BACK returns to Title
"""
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_CHARACTER_SELECT, SCENE_TITLE,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM,
    COLOR_WHITE, COLOR_SAFFRON, COLOR_CREAM,
    GAME_FONT_SIZE_TITLE, GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL
)
from profile_manager import ProfileManager

# Virtual keyboard layout — 3 rows
VKB_ROWS = [
    list("ABCDEFGHIJ"),
    list("KLMNOPQRST"),
    list("UVWXYZ _  "),
]
VKB_SPECIAL = {"⌫": "backspace", "OK": "ok"}
# Add special keys at end of row 3
VKB_ROWS[2] = list("UVWXYZ") + ["⌫", "OK"]

VKB_COLS = max(len(r) for r in VKB_ROWS)
VKB_KEY_W = 68
VKB_KEY_H = 56
VKB_GAP   = 8


class PlayerSelectScene(Scene):
    """Scene for selecting or creating player profiles — full controller support."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets   = assets
        self.input_mgr = input_mgr
        self.prof_mgr  = ProfileManager()

        self.input_name = ""
        self.is_typing  = False
        self.profiles   = []
        self.elapsed    = 0.0

        # Controller focus: 'vkb' (virtual keyboard) or 'profile' (existing profiles)
        self.focus = "vkb"
        # Virtual keyboard cursor position [row, col]
        self.vkb_row = 0
        self.vkb_col = 0
        # Selected profile index (for controller navigation)
        self.selected_profile_idx = 0
        self.scroll_offset = 0
        self.max_visible_profiles = 4  # Display 4 profiles at a time with clean spacing

        # UI Layout
        self.input_rect       = pygame.Rect(LOGICAL_WIDTH // 2 - 290, 230, 580, 56)
        self.confirm_btn_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 290, 860, 580, 60)
        self.back_btn_rect    = pygame.Rect(60, 60, 140, 50)
        self.profile_rects    = []
        self.hover_back    = False
        self.hover_confirm = False

        # Compute virtual keyboard top-left origin (centered on screen)
        total_vkb_w = VKB_COLS * VKB_KEY_W + (VKB_COLS - 1) * VKB_GAP
        self.vkb_x = (LOGICAL_WIDTH - total_vkb_w) // 2
        self.vkb_y = 305  # just below the input box

    def on_enter(self, **kwargs):
        self.elapsed   = 0.0
        self.profiles  = self.prof_mgr.get_profiles()
        self.input_name = ""
        self.is_typing  = True
        self.focus      = "vkb"
        self.vkb_row    = 0
        self.vkb_col    = 0
        self.selected_profile_idx = 0
        self.scroll_offset = 0

        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False, scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )
        self.font_title    = self.assets.load_font(None, GAME_FONT_SIZE_TITLE)
        self.font_subtitle = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body     = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small    = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

    # ── Controller virtual keyboard helpers ────────────────────────────────────

    def _vkb_key_at(self, row, col):
        """Return the key label at given (row, col), or None if out of range."""
        if 0 <= row < len(VKB_ROWS) and 0 <= col < len(VKB_ROWS[row]):
            return VKB_ROWS[row][col]
        return None

    def _vkb_activate(self):
        """Press the currently highlighted virtual keyboard key."""
        key = self._vkb_key_at(self.vkb_row, self.vkb_col)
        if key is None:
            return
        if key == "⌫":
            self.input_name = self.input_name[:-1]
            self.assets.play_sound("jump.wav", volume=0.12)
        elif key == "OK":
            self._confirm_selection()
        elif key == " ":
            if len(self.input_name) < 15:
                self.input_name += " "
            self.assets.play_sound("jump.wav", volume=0.08)
        else:
            if len(self.input_name) < 15:
                self.input_name += key
            self.assets.play_sound("jump.wav", volume=0.08)

    # ── handle_events ─────────────────────────────────────────────────────────

    def handle_events(self, events, input_mgr):
        # Global back
        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            self.manager.switch_to(SCENE_TITLE)
            return

        # ── Controller navigation ──
        if self.focus == "back":
            if input_mgr.just_pressed[input_mgr.MENU_DOWN] or input_mgr.just_pressed[input_mgr.MENU_RIGHT]:
                self.focus = "vkb"
                self.vkb_row = 0
                self.vkb_col = 0
                self.assets.play_sound("jump.wav", volume=0.06)

            if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
                self.assets.play_sound("box_open.wav", volume=0.2)
                self.manager.switch_to(SCENE_TITLE)
                return

        elif self.focus == "vkb":
            row_len = len(VKB_ROWS[self.vkb_row])

            if input_mgr.just_pressed[input_mgr.MENU_LEFT]:
                if self.vkb_row == 0 and self.vkb_col == 0:
                    self.focus = "back"
                    self.assets.play_sound("jump.wav", volume=0.06)
                else:
                    self.vkb_col = (self.vkb_col - 1) % row_len
                    self.assets.play_sound("jump.wav", volume=0.06)

            elif input_mgr.just_pressed[input_mgr.MENU_RIGHT]:
                self.vkb_col = (self.vkb_col + 1) % row_len
                self.assets.play_sound("jump.wav", volume=0.06)

            elif input_mgr.just_pressed[input_mgr.MENU_UP]:
                if self.vkb_row == 0:
                    self.focus = "back"
                    self.assets.play_sound("jump.wav", volume=0.06)
                else:
                    new_row = self.vkb_row - 1
                    self.vkb_col = min(self.vkb_col, len(VKB_ROWS[new_row]) - 1)
                    self.vkb_row = new_row
                    self.assets.play_sound("jump.wav", volume=0.06)

            elif input_mgr.just_pressed[input_mgr.MENU_DOWN]:
                if self.vkb_row == len(VKB_ROWS) - 1:
                    if self.profiles:
                        self.focus = "profile"
                        self.selected_profile_idx = 0
                    else:
                        self.focus = "confirm"
                    self.assets.play_sound("jump.wav", volume=0.12)
                else:
                    new_row = self.vkb_row + 1
                    self.vkb_col = min(self.vkb_col, len(VKB_ROWS[new_row]) - 1)
                    self.vkb_row = new_row
                    self.assets.play_sound("jump.wav", volume=0.06)

            # Select current VKB key
            if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
                self._vkb_activate()

        elif self.focus == "profile":
            if not self.profiles:
                self.focus = "vkb"
                return

            if input_mgr.just_pressed[input_mgr.MENU_UP]:
                if self.selected_profile_idx == 0:
                    # Go back up to VKB
                    self.focus = "vkb"
                    self.vkb_row = len(VKB_ROWS) - 1
                    self.assets.play_sound("jump.wav", volume=0.12)
                else:
                    self.selected_profile_idx -= 1
                    if self.selected_profile_idx < self.scroll_offset:
                        self.scroll_offset = self.selected_profile_idx
                    self.assets.play_sound("jump.wav", volume=0.06)

            elif input_mgr.just_pressed[input_mgr.MENU_DOWN]:
                if self.selected_profile_idx >= len(self.profiles) - 1:
                    self.focus = "confirm"
                    self.assets.play_sound("jump.wav", volume=0.06)
                else:
                    self.selected_profile_idx += 1
                    if self.selected_profile_idx >= self.scroll_offset + self.max_visible_profiles:
                        self.scroll_offset = self.selected_profile_idx - self.max_visible_profiles + 1
                    self.assets.play_sound("jump.wav", volume=0.06)

            # Launch selected profile
            if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
                idx = self.selected_profile_idx
                if idx < len(self.profiles):
                    prof = self.profiles[idx]
                    self.input_name = prof["name"]
                    self.manager.shared["player_name"] = prof["name"]
                    self.manager.shared["character"]   = prof.get("character", "boy")
                    self.assets.play_sound("level_complete.wav", volume=0.3)
                    self._launch_game_level()

        elif self.focus == "confirm":
            if input_mgr.just_pressed[input_mgr.MENU_UP]:
                if self.profiles:
                    self.focus = "profile"
                    self.selected_profile_idx = len(self.profiles) - 1
                    self.scroll_offset = max(0, len(self.profiles) - self.max_visible_profiles)
                else:
                    self.focus = "vkb"
                    self.vkb_row = len(VKB_ROWS) - 1
                self.assets.play_sound("jump.wav", volume=0.06)

            elif input_mgr.just_pressed[input_mgr.MENU_DOWN]:
                self.focus = "back"
                self.assets.play_sound("jump.wav", volume=0.06)

            if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
                self._confirm_selection()

        # ── Keyboard & Mouse Events ─────────────────────────────────────────
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                # Scroll up/down through profiles
                if self.profiles:
                    max_offset = max(0, len(self.profiles) - self.max_visible_profiles)
                    self.scroll_offset = max(0, min(max_offset, self.scroll_offset - event.y))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._confirm_selection()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_name = self.input_name[:-1]
                elif event.key == pygame.K_TAB:
                    # Toggle focus between vkb and profile list
                    if self.profiles:
                        self.focus = "profile" if self.focus == "vkb" else "vkb"
                else:
                    if len(self.input_name) < 15 and (event.unicode.isalnum() or event.unicode in " _-"):
                        self.input_name += event.unicode
                        self.focus = "vkb"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y

                if self.input_rect.collidepoint(mx, my):
                    self.is_typing = True
                    self.focus = "vkb"

                elif self.back_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("box_open.wav", volume=0.2)
                    self.manager.switch_to(SCENE_TITLE)

                elif self.confirm_btn_rect.collidepoint(mx, my):
                    self._confirm_selection()

                else:
                    # Check VKB mouse click
                    for row_i, row in enumerate(VKB_ROWS):
                        for col_i, key in enumerate(row):
                            kr = self._vkb_key_rect(row_i, col_i)
                            if kr.collidepoint(mx, my):
                                self.vkb_row = row_i
                                self.vkb_col = col_i
                                self.focus = "vkb"
                                self._vkb_activate()

                    # Check profile click (taking scroll_offset into account)
                    for vis_i, r in enumerate(self.profile_rects):
                        actual_idx = self.scroll_offset + vis_i
                        if r.collidepoint(mx, my) and actual_idx < len(self.profiles):
                            prof = self.profiles[actual_idx]
                            self.selected_profile_idx = actual_idx
                            self.focus = "profile"
                            self.input_name = prof["name"]
                            self.manager.shared["player_name"] = prof["name"]
                            self.manager.shared["character"]   = prof.get("character", "boy")
                            self.assets.play_sound("level_complete.wav", volume=0.3)
                            self._launch_game_level()

    def _confirm_selection(self):
        name = self.input_name.strip() or "Pilgrim"
        prof = self.prof_mgr.get_profile(name)
        self.manager.shared["player_name"] = name
        if prof:
            self.manager.shared["character"] = prof.get("character", "boy")
            self.assets.play_sound("level_complete.wav", volume=0.35)
            self._launch_game_level()
        else:
            self.manager.shared["character"] = "boy"
            self.prof_mgr.save_profile(name, "boy")
            self.assets.play_sound("level_complete.wav", volume=0.35)
            self.manager.switch_to(SCENE_CHARACTER_SELECT)

    def _launch_game_level(self):
        self.manager.shared["total_score"]  = 0
        self.manager.shared["final_score"]  = 0
        self.manager.shared["total_time"]   = 0.0
        self.manager.shared["level_times"]  = {}
        self.manager.shared["monk_correct"] = {}
        self.manager.shared["boxes_opened"] = {}

        starting_level = self.manager.shared.get("starting_level", 1)
        from settings import SCENE_LEVEL, SCENE_TRANSITION
        if starting_level < 0:
            self.manager.switch_to(SCENE_TRANSITION, level=abs(starting_level))
        else:
            self.manager.switch_to(SCENE_LEVEL, level=starting_level)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _vkb_key_rect(self, row, col):
        """Return the screen Rect for a virtual keyboard key."""
        x = self.vkb_x + col * (VKB_KEY_W + VKB_GAP)
        y = self.vkb_y + row * (VKB_KEY_H + VKB_GAP)
        return pygame.Rect(x, y, VKB_KEY_W, VKB_KEY_H)

    def update(self, dt):
        self.elapsed += dt
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
        self.hover_back    = self.back_btn_rect.collidepoint(mx, my)
        self.hover_confirm = self.confirm_btn_rect.collidepoint(mx, my)

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))

        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 18, 32, 225))
        surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_title.render("SELECT PLAYER PROFILE", True, COLOR_GOLD_BRIGHT)
        surface.blit(title_surf, title_surf.get_rect(center=(LOGICAL_WIDTH // 2, 110)))

        sub_surf = self.font_body.render("D-Pad to type name  |  Move down to select saved profile", True, COLOR_WHITE)
        surface.blit(sub_surf, sub_surf.get_rect(center=(LOGICAL_WIDTH // 2, 170)))

        # Name Input Box
        box_col = COLOR_GOLD_BRIGHT if self.focus == "vkb" else COLOR_GOLD_DIM
        inp_surf = pygame.Surface((self.input_rect.width, self.input_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(inp_surf, (20, 30, 48, 230), inp_surf.get_rect(), border_radius=10)
        pygame.draw.rect(inp_surf, box_col, inp_surf.get_rect(), width=2, border_radius=10)
        surface.blit(inp_surf, self.input_rect)

        cursor = "|" if (self.focus == "vkb" and int(self.elapsed * 2) % 2 == 0) else ""
        display_name = self.input_name + cursor
        txt_s = self.font_body.render(
            display_name or "Use D-Pad to type name...",
            True, COLOR_WHITE if self.input_name else COLOR_GOLD_DIM
        )
        surface.blit(txt_s, txt_s.get_rect(midleft=(self.input_rect.left + 20, self.input_rect.centery)))

        # ── Virtual Keyboard ───────────────────────────────────────────────────
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
        for row_i, row in enumerate(VKB_ROWS):
            for col_i, key in enumerate(row):
                kr = self._vkb_key_rect(row_i, col_i)
                is_controller_sel = (self.focus == "vkb" and row_i == self.vkb_row and col_i == self.vkb_col)
                is_mouse_hover    = kr.collidepoint(mx, my)
                is_special        = key in ("⌫", "OK")

                if is_controller_sel:
                    bg_c = COLOR_GOLD_BRIGHT
                    border_c = COLOR_GOLD_BRIGHT
                    text_c = COLOR_BG_DARK
                elif is_mouse_hover:
                    bg_c = COLOR_GOLD
                    border_c = COLOR_GOLD_BRIGHT
                    text_c = COLOR_BG_DARK
                elif is_special:
                    bg_c = (60, 20, 20) if key == "⌫" else (20, 55, 20)
                    border_c = COLOR_SAFFRON if key == "⌫" else COLOR_GOLD
                    text_c = COLOR_WHITE
                else:
                    bg_c = (25, 35, 55)
                    border_c = COLOR_GOLD_DIM
                    text_c = COLOR_CREAM

                ks = pygame.Surface((kr.width, kr.height), pygame.SRCALPHA)
                pygame.draw.rect(ks, (*bg_c[:3], 220), ks.get_rect(), border_radius=8)
                pygame.draw.rect(ks, border_c, ks.get_rect(), width=2 if is_controller_sel else 1, border_radius=8)
                surface.blit(ks, kr)

                kt = self.font_body.render(key, True, text_c)
                surface.blit(kt, kt.get_rect(center=kr.center))

        # VKB hint label
        hint_y = self.vkb_y + len(VKB_ROWS) * (VKB_KEY_H + VKB_GAP) + 6
        hint = self.font_small.render(
            "D-Pad: move  |  A/Select: press key  |  ⌫: delete  |  OK: confirm  |  D-Pad ↓: switch to profiles",
            True, COLOR_GOLD_DIM
        )
        surface.blit(hint, hint.get_rect(center=(LOGICAL_WIDTH // 2, hint_y)))

        # ── Existing Profiles ──────────────────────────────────────────────────
        profiles_y = hint_y + 36
        lbl = self.font_body.render("Saved Profiles:  (D-Pad / Scroll Wheel to view all)", True, COLOR_GOLD)
        surface.blit(lbl, (LOGICAL_WIDTH // 2 - 290, profiles_y))

        self.profile_rects = []
        start_y = profiles_y + 46

        if not self.profiles:
            empty_txt = self.font_small.render("No saved profiles found. Enter a name above to begin!", True, COLOR_CREAM)
            surface.blit(empty_txt, (LOGICAL_WIDTH // 2 - 290, start_y))
        else:
            visible_profiles = self.profiles[self.scroll_offset : self.scroll_offset + self.max_visible_profiles]
            for vis_i, p in enumerate(visible_profiles):
                actual_idx = self.scroll_offset + vis_i
                r = pygame.Rect(LOGICAL_WIDTH // 2 - 290, start_y + vis_i * 60, 580, 50)
                self.profile_rects.append(r)

                is_ctrl_sel = (self.focus == "profile" and actual_idx == self.selected_profile_idx)
                mouse_hover = r.collidepoint(mx, my)
                highlighted = is_ctrl_sel or mouse_hover

                bg_c    = COLOR_GOLD       if highlighted else COLOR_BG_DARK
                border_c = COLOR_GOLD_BRIGHT if highlighted else COLOR_GOLD_DIM

                ps = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
                pygame.draw.rect(ps, (*bg_c[:3], 220), ps.get_rect(), border_radius=10)
                pygame.draw.rect(ps, border_c, ps.get_rect(), width=3 if is_ctrl_sel else (2 if mouse_hover else 1), border_radius=10)
                surface.blit(ps, r)

                char_title = "Shravak" if p.get("character") == "boy" else "Shravika"
                date_str   = p.get("date_achieved", "N/A")
                arrow      = " ▶" if is_ctrl_sel else ""
                p_text = f"👤 {p['name']}   |   {char_title}   |   Best: {p.get('high_score', 0):,} pts   ({date_str}){arrow}"
                txt_col = COLOR_BG_DARK if highlighted else COLOR_WHITE
                ts = self.font_small.render(p_text, True, txt_col)
                surface.blit(ts, ts.get_rect(midleft=(r.left + 20, r.centery)))

            # ── Scroll Indicators & Scrollbar ──
            if len(self.profiles) > self.max_visible_profiles:
                # Scrollbar track
                track_x = LOGICAL_WIDTH // 2 + 302
                track_y = start_y
                track_h = self.max_visible_profiles * 60 - 10
                track_rect = pygame.Rect(track_x, track_y, 8, track_h)
                pygame.draw.rect(surface, (20, 30, 50, 200), track_rect, border_radius=4)
                pygame.draw.rect(surface, COLOR_GOLD_DIM, track_rect, width=1, border_radius=4)

                # Scrollbar thumb
                thumb_h = max(20, int(track_h * (self.max_visible_profiles / len(self.profiles))))
                max_scroll = len(self.profiles) - self.max_visible_profiles
                thumb_y = track_y + int((track_h - thumb_h) * (self.scroll_offset / max_scroll)) if max_scroll > 0 else track_y
                thumb_rect = pygame.Rect(track_x, thumb_y, 8, thumb_h)
                pygame.draw.rect(surface, COLOR_GOLD_BRIGHT, thumb_rect, border_radius=4)

                # Up / Down arrow indicators
                if self.scroll_offset > 0:
                    up_txt = self.font_small.render("▲", True, COLOR_GOLD_BRIGHT)
                    surface.blit(up_txt, up_txt.get_rect(center=(LOGICAL_WIDTH // 2, profiles_y + 16)))
                if self.scroll_offset + self.max_visible_profiles < len(self.profiles):
                    dn_txt = self.font_small.render("▼", True, COLOR_GOLD_BRIGHT)
                    surface.blit(dn_txt, dn_txt.get_rect(center=(LOGICAL_WIDTH // 2, start_y + track_h + 10)))

        # Confirm Button
        is_ctrl_confirm = (self.focus == "confirm")
        highlight_confirm = is_ctrl_confirm or self.hover_confirm

        bg_col   = COLOR_GOLD if highlight_confirm else COLOR_SAFFRON
        btn_surf = pygame.Surface((self.confirm_btn_rect.width, self.confirm_btn_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (*bg_col[:3], 240), btn_surf.get_rect(), border_radius=12)
        pygame.draw.rect(btn_surf, COLOR_GOLD_BRIGHT if highlight_confirm else COLOR_GOLD_DIM, btn_surf.get_rect(), width=3 if highlight_confirm else 2, border_radius=12)
        surface.blit(btn_surf, self.confirm_btn_rect)

        c_str = "START PILGRIMAGE ➔" if self.prof_mgr.get_profile(self.input_name.strip()) else "CONTINUE TO CHARACTER SELECT ➔"
        c_txt = self.font_body.render(c_str, True, COLOR_BG_DARK if highlight_confirm else COLOR_WHITE)
        surface.blit(c_txt, c_txt.get_rect(center=self.confirm_btn_rect.center))

        # Back Button
        is_ctrl_back = (self.focus == "back")
        highlight_back = is_ctrl_back or self.hover_back

        b_surf = pygame.Surface((self.back_btn_rect.width, self.back_btn_rect.height), pygame.SRCALPHA)
        bg_back = (80, 50, 110) if highlight_back else (30, 20, 45)
        border_back = COLOR_GOLD_BRIGHT if highlight_back else COLOR_GOLD_DIM

        pygame.draw.rect(b_surf, (*bg_back, 220), b_surf.get_rect(), border_radius=8)
        pygame.draw.rect(b_surf, border_back, b_surf.get_rect(), width=3 if highlight_back else 2, border_radius=8)
        surface.blit(b_surf, self.back_btn_rect)

        bk_label = "◄ BACK" if not is_ctrl_back else "► ◄ BACK ◄"
        bk_txt = self.font_small.render(bk_label, True, COLOR_GOLD_BRIGHT if highlight_back else COLOR_WHITE)
        surface.blit(bk_txt, bk_txt.get_rect(center=self.back_btn_rect.center))
