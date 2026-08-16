"""
victory_scene.py — The final screen displayed upon completing the game.
Calculates final time, determines rank, and shows the Digambar Garbhalaya.
"""
import math
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_TITLE,
    COLOR_BG_DARK, COLOR_GOLD_BRIGHT, COLOR_GOLD, COLOR_CREAM, COLOR_WHITE,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
)


class VictoryScene(Scene):
    """Calculates score and displays final victory screen."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.elapsed = 0.0
        self.total_time = 0.0
        self.rank_title = ""
        self.bg_image = None
        self.font_title = None
        self.font_sub = None
        self.font_body = None
        self.font_small = None

    def on_enter(self, **kwargs):
        self.elapsed = 0.0

        # Calculate final score (total time)
        self.total_time = self.manager.shared.get("total_time", 999.0)

        # Determine Rank
        mins = self.total_time / 60.0
        if mins < 4.0:
            self.rank_title = "Moksha Margi"
        elif mins < 8.0:
            self.rank_title = "Shravak"
        else:
            self.rank_title = "Bhakt"

        # Load fonts
        self.font_title = self.assets.load_font(None, FONT_SIZE_TITLE)
        self.font_sub = self.assets.load_font(None, FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, FONT_SIZE_SMALL)

        # Load image (Garbhalaya)
        self.bg_image = self.assets.load_image(
            "digambar_garbhalaya.png", "transitions",
            scale=(500, 500)
        )

        # Stop any lingering level music and maybe play a victory fanfare if we had one
        self.assets.stop_music()

    def handle_events(self, events, input_mgr):
        if self.elapsed > 3.0:
            if (input_mgr.just_pressed[input_mgr.ACTION] or
                    input_mgr.just_pressed[input_mgr.JUMP] or
                    input_mgr.just_pressed[input_mgr.BACK]):
                self.manager.switch_to(SCENE_TITLE)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.manager.switch_to(SCENE_TITLE)

    def update(self, dt):
        self.elapsed += dt

    def draw(self, surface):
        surface.fill(COLOR_BG_DARK)

        # Pulsing golden aura
        glow_r = 280 + int(30 * math.sin(self.elapsed * 1.5))
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 60, 40), (glow_r, glow_r), glow_r)
        surface.blit(glow, (LOGICAL_WIDTH // 2 - glow_r, 100))

        # Main Image
        if self.bg_image:
            img_rect = self.bg_image.get_rect(center=(LOGICAL_WIDTH // 2, 380))
            surface.blit(self.bg_image, img_rect)

        # Text Elements
        title = self.font_title.render("Pilgrimage Complete", True, COLOR_GOLD_BRIGHT)
        surface.blit(title, title.get_rect(center=(LOGICAL_WIDTH // 2, 700)))

        # Time
        mins = int(self.total_time) // 60
        secs = int(self.total_time) % 60
        time_text = f"Total Time: {mins}m {secs}s"
        time_surf = self.font_sub.render(time_text, True, COLOR_CREAM)
        surface.blit(time_surf, time_surf.get_rect(center=(LOGICAL_WIDTH // 2, 780)))

        # Rank
        rank_text = f"Rank: {self.rank_title}"
        rank_surf = self.font_sub.render(rank_text, True, COLOR_GOLD)
        surface.blit(rank_surf, rank_surf.get_rect(center=(LOGICAL_WIDTH // 2, 830)))

        # Continue prompt
        if self.elapsed > 3.0:
            alpha = int(128 + 127 * math.sin(self.elapsed * 4))
            cont = self.font_small.render("Press ENTER to return to Title", True, COLOR_WHITE)
            cont.set_alpha(alpha)
            surface.blit(cont, cont.get_rect(center=(LOGICAL_WIDTH // 2, 950)))
