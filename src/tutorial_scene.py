"""
tutorial_scene.py — Premium tabbed How-to-Play screen for The Path to Moksha.
Tabs: Controls | Items | Sage Guide | Levels
Supports per-tab vertical scrolling and uses ASCII-compatible symbols for default font rendering.
"""
import math
import os
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT,
    SCENE_TITLE, SCENE_PLAYER_SELECT, SCENE_OPTIONS,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM,
    COLOR_WHITE, COLOR_CREAM, COLOR_SAFFRON, COLOR_RED, COLOR_GREEN,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
    IMAGES_DIR,
)


TABS = [
    {"symbol": "[+]", "label": "CONTROLS"},
    {"symbol": "[*]", "label": "ITEMS"},
    {"symbol": "[@]", "label": "SAGE GUIDE"},
    {"symbol": "[#]", "label": "LEVELS"},
]

TAB_CONTENT_Y = 180   # Content area starts below tabs
CONTENT_BOTTOM = LOGICAL_HEIGHT - 130
CLIP_HEIGHT = CONTENT_BOTTOM - TAB_CONTENT_Y
TAB_W = LOGICAL_WIDTH // len(TABS)


# ── Helper: draw a keycap badge ──────────────────────────────────────────────
def draw_keycap(surface, font, key_label, cx, cy, color=COLOR_GOLD_BRIGHT):
    """Draw a keyboard-key-style badge centred at (cx, cy)."""
    txt = font.render(key_label, True, color)
    tw, th = txt.get_size()
    pad_x, pad_y = 16, 8
    bw, bh = tw + pad_x * 2, th + pad_y * 2
    bx, by = cx - bw // 2, cy - bh // 2
    # Outer shadow
    pygame.draw.rect(surface, (10, 6, 18), (bx + 3, by + 5, bw, bh), border_radius=8)
    # Key face
    pygame.draw.rect(surface, (38, 28, 55), (bx, by, bw, bh), border_radius=8)
    # Border
    pygame.draw.rect(surface, color, (bx, by, bw, bh), width=2, border_radius=8)
    # Top highlight
    pygame.draw.rect(surface, (80, 65, 100), (bx + 3, by + 3, bw - 6, max(2, bh // 3)), border_radius=5)
    surface.blit(txt, (bx + pad_x, by + pad_y))
    return bw   # return width for spacing


# ── Helper: draw mandala accent ──────────────────────────────────────────────
def draw_mandala_accent(surface, cx, cy, r, elapsed):
    """Draw a simple rotating mandala ring."""
    n = 12
    for i in range(n):
        angle = math.radians(i * 360 / n + elapsed * 15)
        x = cx + int(r * math.cos(angle))
        y = cy + int(r * math.sin(angle))
        a2 = math.radians((i + 1) * 360 / n + elapsed * 15)
        x2 = cx + int(r * math.cos(a2))
        y2 = cy + int(r * math.sin(a2))
        col = (int(COLOR_GOLD[0]), int(COLOR_GOLD[1]), int(COLOR_GOLD[2]))
        pygame.draw.line(surface, col, (x, y), (x2, y2), 1)
        pygame.draw.circle(surface, col, (x, y), 3)


class TutorialScene(Scene):
    """Premium tabbed How-to-Play tutorial screen."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.active_tab = 0
        self.tab_anim = 1.0   # 0..1 slide-in progress
        self.prev_tab = 0
        self.tab_scroll = [0, 0, 0, 0]  # Vertical scroll offset per tab
        self.max_scroll = [0, 0, 0, 0]

        cx = LOGICAL_WIDTH // 2
        self.btn_start = pygame.Rect(cx - 340, LOGICAL_HEIGHT - 100, 300, 60)
        self.btn_back  = pygame.Rect(cx + 40,  LOGICAL_HEIGHT - 100, 300, 60)
        self.hover_start = self.hover_back = False
        self.focus_zone = "tabs"  # "tabs" or "buttons"
        self.selected_btn = 0     # 0: START GAME, 1: MAIN MENU

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_enter(self, return_scene=SCENE_TITLE, **kwargs):
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.active_tab = 0
        self.tab_anim = 1.0
        self.tab_scroll = [0, 0, 0, 0]
        self.hover_start = self.hover_back = False
        self.focus_zone = "tabs"
        self.selected_btn = 0
        self.return_scene = kwargs.get("return_scene", return_scene)

        self.font_title    = self.assets.load_font(None, FONT_SIZE_TITLE)
        self.font_subtitle = self.assets.load_font(None, FONT_SIZE_SUBTITLE)
        self.font_body     = self.assets.load_font(None, FONT_SIZE_BODY)
        self.font_small    = self.assets.load_font(None, FONT_SIZE_SMALL)
        self.font_key      = self.assets.load_font(None, FONT_SIZE_SMALL)

        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False, scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )
        self.assets.play_music("bgm_loop.wav", volume=0.3)


    # ── Events ───────────────────────────────────────────────────────────────

    def handle_events(self, events, input_mgr):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.elapsed > 0.5:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y
                # Tab click
                for i, tab in enumerate(TABS):
                    tab_rect = pygame.Rect(i * TAB_W, 100, TAB_W, 70)
                    if tab_rect.collidepoint(mx, my) and i != self.active_tab:
                        self._switch_tab(i)
                        self.focus_zone = "tabs"
                        return
                if self.btn_start.collidepoint(mx, my):
                    self._go_start()
                elif self.btn_back.collidepoint(mx, my):
                    self._go_back()

            # Mouse wheel scroll
            if event.type == pygame.MOUSEWHEEL:
                self.tab_scroll[self.active_tab] -= event.y * 35

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    if self.focus_zone == "tabs":
                        self._switch_tab((self.active_tab + 1) % len(TABS))
                    else:
                        self.selected_btn = 1
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if self.focus_zone == "tabs":
                        self._switch_tab((self.active_tab - 1) % len(TABS))
                    else:
                        self.selected_btn = 0
                elif event.key in (pygame.K_UP, pygame.K_w):
                    if self.focus_zone == "buttons":
                        self.focus_zone = "tabs"
                    else:
                        self.tab_scroll[self.active_tab] -= 40
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if self.focus_zone == "tabs":
                        self.focus_zone = "buttons"
                    else:
                        self.tab_scroll[self.active_tab] += 40

        # Clamp scroll position
        ms = self.max_scroll[self.active_tab]
        self.tab_scroll[self.active_tab] = max(0, min(self.tab_scroll[self.active_tab], ms))

        # D-Pad / Controller input
        if input_mgr.just_pressed[input_mgr.MENU_LEFT] or input_mgr.just_pressed[input_mgr.LEFT]:
            if self.focus_zone == "buttons":
                self.selected_btn = 0
                self.assets.play_sound("jump.wav", volume=0.12)
            else:
                self._switch_tab((self.active_tab - 1) % len(TABS))
        elif input_mgr.just_pressed[input_mgr.MENU_RIGHT] or input_mgr.just_pressed[input_mgr.RIGHT]:
            if self.focus_zone == "buttons":
                self.selected_btn = 1
                self.assets.play_sound("jump.wav", volume=0.12)
            else:
                self._switch_tab((self.active_tab + 1) % len(TABS))

        if input_mgr.just_pressed[input_mgr.MENU_DOWN]:
            if self.focus_zone == "tabs":
                self.focus_zone = "buttons"
                self.assets.play_sound("jump.wav", volume=0.12)
        elif input_mgr.just_pressed[input_mgr.MENU_UP]:
            if self.focus_zone == "buttons":
                self.focus_zone = "tabs"
                self.assets.play_sound("jump.wav", volume=0.12)

        # Vertical scrolling via hold on D-Pad / Stick when in tabs zone
        if self.focus_zone == "tabs":
            if input_mgr.actions[input_mgr.MENU_UP] or input_mgr.actions[input_mgr.UP]:
                self.tab_scroll[self.active_tab] = max(0, self.tab_scroll[self.active_tab] - 300 * 0.016)
            elif input_mgr.actions[input_mgr.MENU_DOWN]:
                self.tab_scroll[self.active_tab] = min(self.max_scroll[self.active_tab], self.tab_scroll[self.active_tab] + 300 * 0.016)

        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
            if self.focus_zone == "buttons":
                if self.selected_btn == 0:
                    self._go_start()
                else:
                    self._go_back()
            else:
                self._go_start()
        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            self._go_back()


    def _switch_tab(self, idx):
        self.prev_tab = self.active_tab
        self.active_tab = idx
        self.tab_anim = 0.0
        self.assets.play_sound("jump.wav", volume=0.12)

    def _go_start(self):
        self.assets.play_sound("level_complete.wav", volume=0.3)
        self.manager.switch_to(SCENE_PLAYER_SELECT)

    def _go_back(self):
        self.assets.play_sound("jump.wav", volume=0.15)
        self.manager.switch_to(self.return_scene)


    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 220 * dt)
        self.tab_anim = min(1.0, self.tab_anim + dt * 8)

        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
        if self.btn_start.collidepoint(mx, my):
            self.focus_zone = "buttons"
            self.selected_btn = 0
        elif self.btn_back.collidepoint(mx, my):
            self.focus_zone = "buttons"
            self.selected_btn = 1
        else:
            for i in range(len(TABS)):
                tab_rect = pygame.Rect(i * TAB_W, 100, TAB_W, 70)
                if tab_rect.collidepoint(mx, my):
                    self.focus_zone = "tabs"

        self.hover_start = (self.focus_zone == "buttons" and self.selected_btn == 0)
        self.hover_back = (self.focus_zone == "buttons" and self.selected_btn == 1)



    # ── Draw helpers ─────────────────────────────────────────────────────────

    def _draw_button(self, surface, rect, text, hover):
        off = 8 if hover else 0
        dr = rect.inflate(off, off)
        surf = pygame.Surface((dr.width, dr.height), pygame.SRCALPHA)
        bg = (55, 35, 80, 230) if hover else (25, 18, 38, 190)
        pygame.draw.rect(surf, bg, surf.get_rect(), border_radius=14)
        bc = COLOR_GOLD_BRIGHT if hover else COLOR_GOLD_DIM
        pygame.draw.rect(surf, bc, surf.get_rect(), width=2, border_radius=14)
        surface.blit(surf, dr.topleft)
        tc = COLOR_WHITE if hover else COLOR_CREAM
        ts = self.font_body.render(text, True, tc)
        surface.blit(ts, ts.get_rect(center=dr.center))

    def _draw_section_card(self, surface, x, y, w, h, alpha=200):
        card = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(card, (20, 14, 35, alpha), card.get_rect(), border_radius=14)
        pygame.draw.rect(card, COLOR_GOLD_DIM, card.get_rect(), width=1, border_radius=14)
        surface.blit(card, (x, y))

    # ── Tab content drawers ───────────────────────────────────────────────────

    def _draw_controls_tab(self, surface, scroll_y):
        """Tab 0: keycap badges + action labels."""
        rows = [
            (["A", "D", "LEFT", "RIGHT"], "Move Left / Right"),
            (["SPACE", "UP"],             "Jump"),
            (["ENTER", "E"],             "Open Box / Interact"),
            (["UP"],                     "Talk to Monk (stand near Sage)"),
            (["UP", "DOWN", "LEFT", "RIGHT"], "Fly in 8 directions (Level 2)"),
            (["ESC"],                    "Back to Main Menu"),
            (["MOUSE CLICK"],            "Select On-Screen Buttons"),
        ]

        row_h = 75
        card_w = LOGICAL_WIDTH - 180
        card_x = 80
        total_h = 20 + len(rows) * row_h
        self.max_scroll[0] = max(0, total_h - CLIP_HEIGHT)

        y = 20 - scroll_y

        for keys, action in rows:
            if y + row_h > 0 and y < CLIP_HEIGHT:
                self._draw_section_card(surface, card_x, y, card_w, row_h - 10)
                # Draw keycaps
                kx = card_x + 25
                ky = y + (row_h - 10) // 2
                for k in keys:
                    w = draw_keycap(surface, self.font_key, k, kx + 35, ky, COLOR_GOLD_BRIGHT)
                    kx += w + 12
                # Separator
                pygame.draw.line(surface, COLOR_GOLD_DIM, (card_x + 460, y + 10), (card_x + 460, y + row_h - 20), 1)
                # Action text
                act_surf = self.font_body.render(action, True, COLOR_CREAM)
                surface.blit(act_surf, (card_x + 485, y + (row_h - 10) // 2 - act_surf.get_height() // 2))
            y += row_h

    def _draw_items_tab(self, surface, scroll_y):
        """Tab 1: 4 item category cards with images."""
        categories = [
            ("Goal Item",    COLOR_GOLD_BRIGHT, (120, 95, 30), "temple_key.png",  "Find this sacred item to progress the level!"),
            ("Support Item", COLOR_GREEN,        (25, 75, 40),  "ghanta.png",      "+15 seconds added to your time remaining."),
            ("Distraction",  COLOR_RED,          (85, 25, 25),  "friend.png",      "-10 seconds lost & controls temporarily frozen!"),
            ("Neutral Item", (160,160,160),      (40, 40, 45),  "food.png",        "Neutral object. Has no effect on your timer."),
        ]

        card_w = (LOGICAL_WIDTH - 180 - 60) // 4
        card_h = 560
        total_h = 20 + card_h + 20
        self.max_scroll[1] = max(0, total_h - CLIP_HEIGHT)

        y = 20 - scroll_y
        x = 80

        for name, border, bg, img_file, desc in categories:
            if y + card_h > 0 and y < CLIP_HEIGHT:
                card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                pygame.draw.rect(card, (*bg, 220), card.get_rect(), border_radius=16)
                pygame.draw.rect(card, border, card.get_rect(), width=3, border_radius=16)
                surface.blit(card, (x, y))

                # Item image
                img_size = 180
                img = self.assets.load_image(img_file, "items", alpha=True, scale=(img_size, img_size))
                img_path = os.path.join(IMAGES_DIR, "items", img_file)
                if os.path.exists(img_path):
                    surface.blit(img, img.get_rect(center=(x + card_w // 2, y + 140)))
                pygame.draw.circle(surface, border, (x + card_w // 2, y + 140), img_size // 2 + 8, width=2)

                # Category name
                n_surf = self.font_subtitle.render(name, True, border)
                surface.blit(n_surf, n_surf.get_rect(center=(x + card_w // 2, y + 260)))

                # Description text wrapping
                words = desc.split()
                lines, line = [], []
                for w in words:
                    if len(" ".join(line + [w])) > 22:
                        lines.append(" ".join(line))
                        line = [w]
                    else:
                        line.append(w)
                if line:
                    lines.append(" ".join(line))

                for li, ln in enumerate(lines):
                    ls = self.font_body.render(ln, True, COLOR_CREAM)
                    surface.blit(ls, ls.get_rect(center=(x + card_w // 2, y + 315 + li * 30)))

            x += card_w + 20

    def _draw_sage_tab(self, surface, scroll_y):
        """Tab 2: Monk interaction steps with scrolling."""
        steps = [
            ("STEP 1", "Walk up to the Sage / Monk standing inside the level.", "[1]"),
            ("STEP 2", "Press UP Arrow when standing near him to talk.", "[2]"),
            ("STEP 3", "A Jain knowledge question appears. Read carefully!", "[3]"),
            ("STEP 4", "Answer correctly to reveal the hidden Goal Box!", "[4]"),
            ("STEP 5", "A wrong answer still unlocks boxes — but costs time!", "[5]"),
        ]

        step_h = 105
        card_w = LOGICAL_WIDTH - 180
        card_x = 80
        total_h = 20 + len(steps) * step_h + 90
        self.max_scroll[2] = max(0, total_h - CLIP_HEIGHT)

        y = 20 - scroll_y

        for title, desc, tag in steps:
            if y + step_h > 0 and y < CLIP_HEIGHT:
                self._draw_section_card(surface, card_x, y, card_w, step_h - 12)
                # Tag badge
                badge = self.font_subtitle.render(tag, True, COLOR_GOLD_BRIGHT)
                surface.blit(badge, (card_x + 25, y + (step_h - 12) // 2 - badge.get_height() // 2))
                # Title
                t_surf = self.font_subtitle.render(title, True, COLOR_GOLD_BRIGHT)
                surface.blit(t_surf, (card_x + 110, y + 14))
                # Desc
                d_surf = self.font_body.render(desc, True, COLOR_CREAM)
                surface.blit(d_surf, (card_x + 110, y + 52))
            y += step_h

        # Tip card at end
        if y + 70 > 0 and y < CLIP_HEIGHT:
            self._draw_section_card(surface, card_x, y, card_w, 70, alpha=180)
            tip = self.font_body.render("TIP: Correct answers also grant bonus timer rewards on some levels!", True, COLOR_GOLD_BRIGHT)
            surface.blit(tip, tip.get_rect(center=(LOGICAL_WIDTH // 2, y + 35)))

    def _draw_levels_tab(self, surface, scroll_y):
        """Tab 3: Level-by-level objective cards with scrolling."""
        levels = [
            {
                "num": 1, "name": "The Commute", "subtitle": "Samsara",
                "border": COLOR_GOLD_BRIGHT, "bg": (60, 45, 10),
                "steps": [
                    "[!] Find the Temple Key box scattered on platforms.",
                    "[!] Visit the Sage for a hint — answer his question!",
                    "[!] Carry the Key to the Temple Gate (far right side).",
                    "[!] Press ENTER or UP Arrow at the gate to complete Level 1.",
                ]
            },
            {
                "num": 2, "name": "The Cave", "subtitle": "Resilience",
                "border": COLOR_SAFFRON, "bg": (55, 20, 10),
                "steps": [
                    "[!] Find the Akshat box to unlock 8-way flying power.",
                    "[!] Use UP / SPACE to fly up, DOWN / S to fly down.",
                    "[!] Fly to the Bhagwan image located in the top-left corner.",
                    "[!] Press ENTER / Click at lower side of Bhagwan image to offer Akshat!",
                ]
            },
        ]

        card_h = 240
        card_w = LOGICAL_WIDTH - 180
        total_h = 20 + len(levels) * (card_h + 20)
        self.max_scroll[3] = max(0, total_h - CLIP_HEIGHT)

        y = 20 - scroll_y

        for lv in levels:
            if y + card_h > 0 and y < CLIP_HEIGHT:
                card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                pygame.draw.rect(card, (*lv["bg"], 215), card.get_rect(), border_radius=16)
                pygame.draw.rect(card, lv["border"], card.get_rect(), width=3, border_radius=16)
                surface.blit(card, (80, y))

                # Level badge
                badge = self.font_title.render(f"L{lv['num']}", True, lv["border"])
                surface.blit(badge, (110, y + card_h // 2 - badge.get_height() // 2))

                # Title block
                t_surf = self.font_subtitle.render(f"Level {lv['num']}: {lv['name']}", True, lv["border"])
                surface.blit(t_surf, (200, y + 16))
                sub_surf = self.font_small.render(lv["subtitle"], True, COLOR_CREAM)
                surface.blit(sub_surf, (202, y + 52))

                # Divider
                pygame.draw.line(surface, lv["border"], (200, y + 74), (80 + card_w - 20, y + 74), 1)

                # Steps
                sx = 200
                sy = y + 86
                for step in lv["steps"]:
                    s_surf = self.font_body.render(step, True, COLOR_CREAM)
                    surface.blit(s_surf, (sx, sy))
                    sy += 34

            y += card_h + 20

    # ── Main draw ────────────────────────────────────────────────────────────

    def draw(self, surface):
        # Background
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(COLOR_BG_DARK)

        # Dark overlay
        ov = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 6, 20, 180))
        surface.blit(ov, (0, 0))

        # ── Header: title + mandala accents ──────────────────────────────────
        draw_mandala_accent(surface, 120, 52, 44, self.elapsed)
        draw_mandala_accent(surface, LOGICAL_WIDTH - 120, 52, 44, self.elapsed)

        t = self.font_title.render("HOW TO PLAY", True, COLOR_GOLD_BRIGHT)
        surface.blit(t, t.get_rect(center=(LOGICAL_WIDTH // 2, 52)))
        pygame.draw.line(surface, COLOR_GOLD_DIM,
                         (LOGICAL_WIDTH // 2 - 400, 92),
                         (LOGICAL_WIDTH // 2 + 400, 92), 2)

        # ── Tab bar ──────────────────────────────────────────────────────────
        for i, tab in enumerate(TABS):
            tx = i * TAB_W
            active = (i == self.active_tab)
            hover_rect = pygame.Rect(tx, 100, TAB_W, 70)
            mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
            hovered = hover_rect.collidepoint(mx, my)

            tab_surf = pygame.Surface((TAB_W, 70), pygame.SRCALPHA)
            if active:
                pygame.draw.rect(tab_surf, (40, 28, 65, 240), tab_surf.get_rect())
                w = 3 if self.focus_zone == "tabs" else 1
                pygame.draw.rect(tab_surf, COLOR_GOLD_BRIGHT, tab_surf.get_rect(), width=w)
                pygame.draw.rect(tab_surf, COLOR_GOLD_BRIGHT, (0, 66, TAB_W, 4 if self.focus_zone == "tabs" else 2))
            elif hovered:
                pygame.draw.rect(tab_surf, (28, 20, 48, 180), tab_surf.get_rect())
                pygame.draw.rect(tab_surf, COLOR_GOLD_DIM, tab_surf.get_rect(), width=1)
            else:
                pygame.draw.rect(tab_surf, (18, 12, 30, 140), tab_surf.get_rect())
                pygame.draw.rect(tab_surf, (60, 45, 20, 200), tab_surf.get_rect(), width=1)
            surface.blit(tab_surf, (tx, 100))

            label = f"{tab['symbol']}  {tab['label']}"
            col = COLOR_GOLD_BRIGHT if active else (COLOR_CREAM if hovered else COLOR_GOLD_DIM)
            ls = self.font_body.render(label, True, col)
            surface.blit(ls, ls.get_rect(center=(tx + TAB_W // 2, 135)))

        # ── Content clip area ────────────────────────────────────────────────
        clip = pygame.Rect(0, TAB_CONTENT_Y, LOGICAL_WIDTH, CLIP_HEIGHT)
        surface.set_clip(clip)

        # Content surface
        content_surf = pygame.Surface((LOGICAL_WIDTH, CLIP_HEIGHT), pygame.SRCALPHA)
        scroll_y = self.tab_scroll[self.active_tab]

        if self.active_tab == 0:
            self._draw_controls_tab(content_surf, scroll_y)
        elif self.active_tab == 1:
            self._draw_items_tab(content_surf, scroll_y)
        elif self.active_tab == 2:
            self._draw_sage_tab(content_surf, scroll_y)
        else:
            self._draw_levels_tab(content_surf, scroll_y)

        # Slide-in transition offset
        slide_off = int((1.0 - self.tab_anim) * 160)
        surface.blit(content_surf, (slide_off, TAB_CONTENT_Y))
        surface.set_clip(None)

        # ── Scrollbar (if max_scroll > 0) ────────────────────────────────────
        ms = self.max_scroll[self.active_tab]
        if ms > 0:
            sb_x = LOGICAL_WIDTH - 30
            sb_y = TAB_CONTENT_Y + 10
            sb_h = CLIP_HEIGHT - 20
            # Track
            pygame.draw.rect(surface, (20, 14, 30, 160), (sb_x, sb_y, 10, sb_h), border_radius=5)
            # Thumb
            thumb_h = max(30, int(sb_h * (CLIP_HEIGHT / (CLIP_HEIGHT + ms))))
            thumb_y = sb_y + int((sb_h - thumb_h) * (scroll_y / ms))
            pygame.draw.rect(surface, COLOR_GOLD_BRIGHT, (sb_x, thumb_y, 10, thumb_h), border_radius=5)

        # ── Bottom navigation hint ───────────────────────────────────────────
        hint_text = "D-Pad UP/DOWN: Switch between Tabs & Buttons | D-Pad LEFT/RIGHT: Change Tab or Button"
        hint = self.font_small.render(hint_text, True, COLOR_GOLD_BRIGHT if self.focus_zone == "tabs" else COLOR_GOLD_DIM)
        surface.blit(hint, hint.get_rect(center=(LOGICAL_WIDTH // 2, CONTENT_BOTTOM + 18)))


        # ── Bottom buttons ────────────────────────────────────────────────────
        self._draw_button(surface, self.btn_start, "START GAME", self.hover_start)
        self._draw_button(surface, self.btn_back,  "MAIN MENU",  self.hover_back)

        # ── Fade-in ───────────────────────────────────────────────────────────
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
