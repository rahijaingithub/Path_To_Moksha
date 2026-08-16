"""
leaderboard_scene.py — Global High Scores and Rankings Leaderboard for Path to Moksha.
Displays top 10 spotlight, paginated scrollable rankings (100 entries per page), and current player rank.
"""
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_TITLE, SCENE_CHARACTER_SELECT,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM,
    COLOR_WHITE, COLOR_SAFFRON, COLOR_CREAM, COLOR_BLUE_WATER,
    GAME_FONT_SIZE_TITLE, GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL
)
from profile_manager import ProfileManager


class LeaderboardScene(Scene):
    """Global Rankings & High Scores screen with pagination up to 100 items per page."""

    ENTRIES_PER_PAGE = 100

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.prof_mgr = ProfileManager()

        self.rankings = []
        self.current_page = 0
        self.total_pages = 1
        self.elapsed = 0.0
        self.player_name = ""
        self.player_rank = None

        self.prev_btn_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 260, 960, 220, 50)
        self.next_btn_rect = pygame.Rect(LOGICAL_WIDTH // 2 + 40, 960, 220, 50)
        self.home_btn_rect = pygame.Rect(60, 60, 160, 50)
        self.restart_btn_rect = pygame.Rect(240, 60, 200, 50)

        self.hover_prev = False
        self.hover_next = False
        self.hover_home = False
        self.hover_restart = False
        self.selected_btn = 0  # 0: Main Menu, 1: Restart Game
        self.scroll_y = 0

    def on_enter(self, **kwargs):
        self.elapsed = 0.0
        self.current_page = 0
        self.scroll_y = 0
        self.selected_btn = 0

        # Re-fetch ProfileManager to guarantee real-time scores from disk
        self.prof_mgr = ProfileManager()
        self.rankings = self.prof_mgr.get_global_rankings()
        self.total_pages = max(1, (len(self.rankings) + self.ENTRIES_PER_PAGE - 1) // self.ENTRIES_PER_PAGE)

        self.player_name = self.manager.shared.get("player_name", "Pilgrim")
        current_score = self.manager.shared.get("final_score", 0)
        self.player_rank = self.prof_mgr.get_player_rank(self.player_name, current_score)


        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False, scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )

        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_TITLE)
        self.font_subtitle = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

        # Play victory / high score music
        self.assets.play_music("bgm_loop.wav", volume=0.35)

    def handle_events(self, events, input_mgr):
        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            self.manager.switch_to(SCENE_TITLE)
            return

        # Controller Left/Right toggle between buttons: 0 = Main Menu, 1 = Restart Game
        if input_mgr.just_pressed[input_mgr.MENU_LEFT] or input_mgr.just_pressed[input_mgr.LEFT]:
            self.selected_btn = 0
            self.assets.play_sound("jump.wav", volume=0.1)
        elif input_mgr.just_pressed[input_mgr.MENU_RIGHT] or input_mgr.just_pressed[input_mgr.RIGHT]:
            self.selected_btn = 1
            self.assets.play_sound("jump.wav", volume=0.1)

        # Controller Up/Down pagination
        if input_mgr.just_pressed[input_mgr.MENU_UP] and self.current_page > 0:
            self.current_page -= 1
            self.scroll_y = 0
            self.assets.play_sound("jump.wav", volume=0.15)
        elif input_mgr.just_pressed[input_mgr.MENU_DOWN] and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.scroll_y = 0
            self.assets.play_sound("jump.wav", volume=0.15)

        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
            if self.selected_btn == 0:
                self.assets.play_sound("box_open.wav", volume=0.2)
                self.manager.switch_to(SCENE_TITLE)
            else:
                self._restart_game()
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y

                if self.home_btn_rect.collidepoint(mx, my):
                    self.assets.play_sound("box_open.wav", volume=0.2)
                    self.manager.switch_to(SCENE_TITLE)

                elif self.restart_btn_rect.collidepoint(mx, my):
                    self._restart_game()

                elif self.prev_btn_rect.collidepoint(mx, my) and self.current_page > 0:
                    self.current_page -= 1
                    self.scroll_y = 0
                    self.assets.play_sound("jump.wav", volume=0.15)

                elif self.next_btn_rect.collidepoint(mx, my) and self.current_page < self.total_pages - 1:
                    self.current_page += 1
                    self.scroll_y = 0
                    self.assets.play_sound("jump.wav", volume=0.15)

            elif event.type == pygame.MOUSEWHEEL:
                # Scroll rankings list
                self.scroll_y = max(0, min(self.scroll_y - event.y * 30, 2000))

    def _restart_game(self):
        self.assets.play_sound("level_complete.wav", volume=0.35)
        self.manager.shared["total_score"] = 0
        self.manager.shared["final_score"] = 0
        self.manager.shared["total_time"] = 0.0
        self.manager.shared["level_times"] = {}
        self.manager.shared["monk_correct"] = {}
        self.manager.shared["boxes_opened"] = {}
        starting_level = self.manager.shared.get("starting_level", 1)
        from settings import SCENE_LEVEL, SCENE_TRANSITION
        if starting_level < 0:
            self.manager.switch_to(SCENE_TRANSITION, level=abs(starting_level))
        else:
            self.manager.switch_to(SCENE_LEVEL, level=starting_level)

    def update(self, dt):
        self.elapsed += dt
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
        if self.home_btn_rect.collidepoint(mx, my):
            self.selected_btn = 0
        elif self.restart_btn_rect.collidepoint(mx, my):
            self.selected_btn = 1

        self.hover_home = (self.selected_btn == 0)
        self.hover_restart = (self.selected_btn == 1)
        self.hover_prev = self.prev_btn_rect.collidepoint(mx, my) and self.current_page > 0
        self.hover_next = self.next_btn_rect.collidepoint(mx, my) and self.current_page < self.total_pages - 1



    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))

        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 18, 32, 235))
        surface.blit(overlay, (0, 0))

        # Title Header
        t_surf = self.font_title.render("GLOBAL HALL OF FAME", True, COLOR_GOLD_BRIGHT)
        surface.blit(t_surf, t_surf.get_rect(center=(LOGICAL_WIDTH // 2, 100)))

        sub_txt = f"Page {self.current_page + 1} of {self.total_pages}   |   Your Rank: #{self.player_rank} ({self.player_name})"
        sub_surf = self.font_body.render(sub_txt, True, COLOR_WHITE)
        surface.blit(sub_surf, sub_surf.get_rect(center=(LOGICAL_WIDTH // 2, 160)))

        # Table Headers
        table_x = LOGICAL_WIDTH // 2 - 500
        table_w = 1000
        header_y = 210

        hdr_surf = pygame.Surface((table_w, 48), pygame.SRCALPHA)
        pygame.draw.rect(hdr_surf, (30, 45, 75, 230), hdr_surf.get_rect(), border_radius=8)
        pygame.draw.rect(hdr_surf, COLOR_GOLD, hdr_surf.get_rect(), width=2, border_radius=8)
        surface.blit(hdr_surf, (table_x, header_y))

        col_ranks = self.font_body.render("RANK", True, COLOR_GOLD_BRIGHT)
        col_name  = self.font_body.render("PLAYER NAME", True, COLOR_GOLD_BRIGHT)
        col_char  = self.font_body.render("CHARACTER", True, COLOR_GOLD_BRIGHT)
        col_level = self.font_body.render("LEVEL", True, COLOR_GOLD_BRIGHT)
        col_score = self.font_body.render("SCORE", True, COLOR_GOLD_BRIGHT)

        surface.blit(col_ranks, (table_x + 30, header_y + 8))
        surface.blit(col_name,  (table_x + 180, header_y + 8))
        surface.blit(col_char,  (table_x + 460, header_y + 8))
        surface.blit(col_level, (table_x + 690, header_y + 8))
        surface.blit(col_score, (table_x + 850, header_y + 8))

        # Render Rankings Entries
        start_idx = self.current_page * self.ENTRIES_PER_PAGE
        end_idx = min(len(self.rankings), start_idx + self.ENTRIES_PER_PAGE)
        page_entries = self.rankings[start_idx:end_idx]

        start_y = 270
        visible_rows = 12  # Render 12 rows per screen view with smooth scroll offset

        for i in range(visible_rows):
            entry_idx = start_idx + i + int(self.scroll_y // 50)
            if entry_idx >= len(self.rankings):
                break

            e = self.rankings[entry_idx]
            rank_num = entry_idx + 1
            row_y = start_y + i * 54

            is_player = (e["name"] == self.player_name)
            bg_col = (60, 45, 15, 230) if is_player else ((25, 35, 55, 200) if i % 2 == 0 else (18, 25, 42, 200))
            border_col = COLOR_GOLD_BRIGHT if is_player else COLOR_GOLD_DIM

            row_surf = pygame.Surface((table_w, 48), pygame.SRCALPHA)
            pygame.draw.rect(row_surf, bg_col, row_surf.get_rect(), border_radius=6)
            pygame.draw.rect(row_surf, border_col, row_surf.get_rect(), width=2 if is_player else 1, border_radius=6)
            surface.blit(row_surf, (table_x, row_y))

            txt_col = COLOR_GOLD_BRIGHT if is_player else COLOR_WHITE
            
            # Rank text with trophy icons for Top 3
            rank_str = f"🥇 #{rank_num}" if rank_num == 1 else (f"🥈 #{rank_num}" if rank_num == 2 else (f"🥉 #{rank_num}" if rank_num == 3 else f"#{rank_num}"))
            r_s = self.font_body.render(rank_str, True, txt_col)
            n_s = self.font_body.render(e["name"], True, txt_col)
            c_s = self.font_small.render(e.get("character", "Shravak"), True, COLOR_CREAM)
            l_s = self.font_body.render(f"Lvl {e.get('level', 1)}", True, COLOR_WHITE)
            s_s = self.font_body.render(f"{e.get('score', 0):,}", True, COLOR_GOLD_BRIGHT)

            surface.blit(r_s, (table_x + 30, row_y + 8))
            surface.blit(n_s, (table_x + 180, row_y + 8))
            surface.blit(c_s, (table_x + 460, row_y + 12))
            surface.blit(l_s, (table_x + 690, row_y + 8))
            surface.blit(s_s, (table_x + 850, row_y + 8))

        # Pagination Controls
        if self.current_page > 0:
            p_surf = pygame.Surface((self.prev_btn_rect.width, self.prev_btn_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(p_surf, COLOR_GOLD if self.hover_prev else COLOR_BG_DARK, p_surf.get_rect(), border_radius=8)
            pygame.draw.rect(p_surf, COLOR_GOLD_BRIGHT, p_surf.get_rect(), width=2, border_radius=8)
            surface.blit(p_surf, self.prev_btn_rect)
            pt = self.font_small.render("◄ PREVIOUS PAGE", True, COLOR_BG_DARK if self.hover_prev else COLOR_WHITE)
            surface.blit(pt, pt.get_rect(center=self.prev_btn_rect.center))

        if self.current_page < self.total_pages - 1:
            n_surf = pygame.Surface((self.next_btn_rect.width, self.next_btn_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(n_surf, COLOR_GOLD if self.hover_next else COLOR_BG_DARK, n_surf.get_rect(), border_radius=8)
            pygame.draw.rect(n_surf, COLOR_GOLD_BRIGHT, n_surf.get_rect(), width=2, border_radius=8)
            surface.blit(n_surf, self.next_btn_rect)
            nt = self.font_small.render("NEXT PAGE ►", True, COLOR_BG_DARK if self.hover_next else COLOR_WHITE)
            surface.blit(nt, nt.get_rect(center=self.next_btn_rect.center))

        # Home / Main Menu button
        h_surf = pygame.Surface((self.home_btn_rect.width, self.home_btn_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(h_surf, (30, 20, 45, 220), h_surf.get_rect(), border_radius=8)
        pygame.draw.rect(h_surf, COLOR_GOLD_BRIGHT if self.hover_home else COLOR_GOLD_DIM, h_surf.get_rect(), width=2, border_radius=8)
        surface.blit(h_surf, self.home_btn_rect)
        ht = self.font_small.render("🏠 MAIN MENU", True, COLOR_GOLD_BRIGHT if self.hover_home else COLOR_WHITE)
        surface.blit(ht, ht.get_rect(center=self.home_btn_rect.center))

        # Restart Game button
        r_surf = pygame.Surface((self.restart_btn_rect.width, self.restart_btn_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(r_surf, COLOR_GOLD if self.hover_restart else COLOR_SAFFRON, r_surf.get_rect(), border_radius=8)
        pygame.draw.rect(r_surf, COLOR_GOLD_BRIGHT, r_surf.get_rect(), width=2, border_radius=8)
        surface.blit(r_surf, self.restart_btn_rect)
        rt = self.font_small.render("▶ RESTART GAME", True, COLOR_BG_DARK if self.hover_restart else COLOR_WHITE)
        surface.blit(rt, rt.get_rect(center=self.restart_btn_rect.center))

