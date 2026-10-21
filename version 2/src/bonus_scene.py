"""
bonus_scene.py — Level 3's Karuna bonus level (Epic G).

Opened by the Namokar Mantra puzzle: the Jiv Daya of saving the fallen bird creates
so much punya that the devotee is shown a glimpse of its fruit — the life of a
compassionate spiritual doctor, who saves one man's body and another man's soul.
It is a glimpse, not a rebirth, which is why the devotee returns to the same Level 3
afterwards, standing exactly where he left (designer, 2026-10-20).

The four minutes that used to be a flat +4:00 reward are this scene's clock instead.
Both rescues done -> whatever is left is banked back into Level 3. The clock running
out is failure: the devotee returns with nothing banked, having lost no Level 3 time,
since Level 3's own clock is paused while this scene is the active one.

G2 builds the frame: the clock, the HUD, and the round trip. The two rescues
themselves are G3, so for now there is nothing to complete and nothing is banked.
"""
import math
import pygame
from scene_manager import Scene
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, BONUS_TIME_LIMIT,
    SCENE_LEVEL, SCENE_TITLE,
    COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM, COLOR_CREAM, COLOR_WHITE,
    COLOR_GREEN, COLOR_RED, COLOR_SAFFRON,
    GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL, GAME_FONT_SIZE_HUD,
)

# The level this scene is a detour from, and returns to.
HOME_LEVEL = 3

# How long the closing card is held before the devotee is returned (seconds).
OUTCOME_HOLD_SECONDS = 3.0


class BonusScene(Scene):
    """The Karuna detour: its own four-minute clock, then back into Level 3."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.time_remaining = float(BONUS_TIME_LIMIT)
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.outcome = None          # None while playing, then "saved" or "out_of_time"
        self.outcome_timer = 0.0
        self.banked = 0.0            # seconds handed back to Level 3
        self.injured_saved = False   # G3
        self.lost_saved = False      # G3

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self, **kwargs):
        self.time_remaining = float(BONUS_TIME_LIMIT)
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.outcome = None
        self.outcome_timer = 0.0
        self.banked = 0.0
        self.injured_saved = False
        self.lost_saved = False

        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)
        self.font_hud = self.assets.load_font(None, GAME_FONT_SIZE_HUD)

        self.assets.play_music("bgm_loop.ogg",
                               volume=self.manager.shared.get("music_volume", 0.35))

    @property
    def both_rescued(self):
        """Both rescues done. Nothing can set these until G3, so this is False for now."""
        return self.injured_saved and self.lost_saved

    # ── input ─────────────────────────────────────────────────────────────────

    def handle_events(self, events, input_mgr):
        if self.outcome is not None:
            # On the closing card any confirm returns early instead of waiting.
            if (input_mgr.just_pressed[input_mgr.ACTION] or
                    input_mgr.just_pressed[input_mgr.JUMP] or
                    input_mgr.just_pressed[input_mgr.MENU_SELECT]):
                self._return_home()
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._return_home()
            return

        # Leaving for the title is the same gesture as in a level. The Level 3 that
        # is still held in memory is abandoned with it, exactly as ESC from a level.
        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            self.manager.switch_to(SCENE_TITLE, input_mgr=self.input_mgr)

    # ── update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 300 * dt)

        if self.outcome is not None:
            self.outcome_timer -= dt
            if self.outcome_timer <= 0:
                self._return_home()
            return

        self.time_remaining -= dt
        if self.both_rescued:
            self._finish("saved")
        elif self.time_remaining <= 0:
            self.time_remaining = 0.0
            self._finish("out_of_time")

    def _finish(self, outcome):
        """Close the detour. Only both rescues bank time; running out banks nothing."""
        self.outcome = outcome
        self.outcome_timer = OUTCOME_HOLD_SECONDS
        self.banked = max(0.0, self.time_remaining) if outcome == "saved" else 0.0
        self.assets.stop_music()
        self.assets.play_sound("correct.wav" if outcome == "saved" else "wrong.wav")

    def _return_home(self):
        """Back to the Level 3 still held in memory, at the exact spot left (G1).

        The banked seconds are published for Level 3 to pick up; adding them to its
        clock without counting them as time taken is G4.
        """
        self.manager.shared["bonus_banked_seconds"] = self.banked
        self.manager.switch_to(SCENE_LEVEL, level=HOME_LEVEL, resume=True,
                               input_mgr=self.input_mgr)

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        self._draw_sky(surface)
        self._draw_placeholder_world(surface)
        self._draw_hud(surface)
        if self.outcome is not None:
            self._draw_outcome(surface)
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill((0, 0, 0))
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))

    def _draw_sky(self, surface):
        """A warm dawn wash — the punya's fruit seen in a kinder light than the Hall."""
        for y in range(0, LOGICAL_HEIGHT, 2):
            t = y / LOGICAL_HEIGHT
            r = int(46 * (1 - t) + 150 * t)
            g = int(38 * (1 - t) + 108 * t)
            b = int(66 * (1 - t) + 78 * t)
            pygame.draw.rect(surface, (r, g, b), (0, y, LOGICAL_WIDTH, 2))

        # Dawn light sits low, where the sky is already warm — over the dark top of
        # the gradient the same glow only reads as a grey smudge.
        halo = 170 + int(12 * math.sin(self.elapsed * 1.4))
        cy = LOGICAL_HEIGHT - 300
        for radius, alpha in ((halo, 22), (halo // 2, 30)):
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 198, 120, alpha), (radius, radius), radius)
            surface.blit(glow, (LOGICAL_WIDTH // 2 - radius, cy - radius))

    def _draw_placeholder_world(self, surface):
        """Stand-in staging until G3 and G5: the ground, and where the two errands go.

        Drawn rather than left blank so the scene reads as a place, and so the
        destinations sit where the rescues will need them.
        """
        ground_y = LOGICAL_HEIGHT - 120
        pygame.draw.rect(surface, (92, 74, 58), (0, ground_y, LOGICAL_WIDTH, 120))
        pygame.draw.line(surface, (126, 104, 80), (0, ground_y), (LOGICAL_WIDTH, ground_y), 3)

        self._draw_marker(surface, 300, ground_y, "HOSPITAL", COLOR_CREAM, self.injured_saved)
        self._draw_marker(surface, LOGICAL_WIDTH - 300, ground_y, "TEMPLE", COLOR_GOLD, self.lost_saved)

        note = self.font_small.render(
            "The two rescues arrive in G3 — this is the staging for them.", True, COLOR_GOLD_DIM)
        surface.blit(note, note.get_rect(center=(LOGICAL_WIDTH // 2, ground_y + 60)))

    def _draw_marker(self, surface, cx, ground_y, label, color, done):
        """A destination: a plain plinth with its name, ticked once its errand is done."""
        w, h = 180, 150
        rect = pygame.Rect(cx - w // 2, ground_y - h, w, h)
        pygame.draw.rect(surface, (38, 32, 48), rect, border_radius=8)
        pygame.draw.rect(surface, color, rect, width=3, border_radius=8)

        name = self.font_body.render(label, True, color)
        surface.blit(name, name.get_rect(center=(rect.centerx, rect.centery)))

        tick = self.font_small.render("saved" if done else "waiting", True,
                                      COLOR_GREEN if done else COLOR_GOLD_DIM)
        surface.blit(tick, tick.get_rect(center=(rect.centerx, rect.bottom - 26)))

    def _draw_hud(self, surface):
        bar = pygame.Surface((LOGICAL_WIDTH, 48), pygame.SRCALPHA)
        bar.fill((12, 10, 22, 190))
        surface.blit(bar, (0, 0))

        title = self.font_hud.render("A Glimpse of the Punya's Fruit", True, COLOR_GOLD_BRIGHT)
        surface.blit(title, (28, 12))

        secs_left = max(0, int(math.ceil(self.time_remaining)))
        clock = self.font_hud.render(f"Bonus Time: {secs_left // 60:02d}:{secs_left % 60:02d}",
                                     True, COLOR_RED if secs_left <= 30 else COLOR_WHITE)
        surface.blit(clock, clock.get_rect(topright=(LOGICAL_WIDTH - 28, 12)))

        goal = self.font_hud.render("Carry the injured man to the hospital; lead the lost man to the temple",
                                    True, COLOR_CREAM)
        surface.blit(goal, goal.get_rect(center=(LOGICAL_WIDTH // 2, 36 + 36)))

        if self.elapsed < 6.0:
            intro = self.font_small.render(
                "Level 3 waits, its clock paused. Whatever time is left when both are saved comes back with you.",
                True, COLOR_SAFFRON)
            surface.blit(intro, intro.get_rect(center=(LOGICAL_WIDTH // 2, 36 + 72)))

    def _draw_outcome(self, surface):
        veil = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((8, 6, 16, 190))
        surface.blit(veil, (0, 0))

        saved = self.outcome == "saved"
        heading = "Both souls are helped" if saved else "The glimpse fades"
        head = self.font_title.render(heading, True, COLOR_GOLD_BRIGHT if saved else COLOR_CREAM)
        surface.blit(head, head.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 60)))

        banked = int(self.banked)
        detail = (f"Time carried back to the Hall: {banked // 60:02d}:{banked % 60:02d}"
                  if saved else "No time is carried back — but nothing in the Hall was lost.")
        body = self.font_body.render(detail, True, COLOR_GREEN if saved else COLOR_CREAM)
        surface.blit(body, body.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2)))

        prompt = self.font_small.render("Returning to the Hall...", True, COLOR_GOLD)
        surface.blit(prompt, prompt.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 60)))
