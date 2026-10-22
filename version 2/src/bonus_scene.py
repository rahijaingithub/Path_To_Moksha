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
import os
import pygame
from scene_manager import Scene
from rescue_npc import RescueNPC, KIND_INJURED, KIND_LOST
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, BONUS_TIME_LIMIT, PLAYER_SPEED, IMAGES_DIR,
    SCENE_LEVEL, SCENE_TITLE,
    COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM, COLOR_CREAM, COLOR_WHITE,
    COLOR_GREEN, COLOR_RED, COLOR_SAFFRON,
    GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL, GAME_FONT_SIZE_HUD,
)

# The level this scene is a detour from, and returns to.
HOME_LEVEL = 3

# How long the closing card is held before the devotee is returned (seconds).
OUTCOME_HOLD_SECONDS = 3.0

# The ground, and where the two errands begin and end. The injured man starts to
# the right of the hospital and the lost man to the left of the temple, so the two
# errands cross and the devotee has to choose an order.
GROUND_Y = LOGICAL_HEIGHT - 120
HOSPITAL_X = 300
TEMPLE_X = LOGICAL_WIDTH - 300
INJURED_START_X = 1150
LOST_START_X = 700
PLAYER_START_X = LOGICAL_WIDTH // 2

PLAYER_HALF_W = 32            # half the drawn sprite, for the walls
DESTINATION_REACH = 120       # how close counts as "at" the hospital or the temple
TREAT_SECONDS = 2.5           # tending to the injured man once he is at the hospital


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
        self.player_x = float(PLAYER_START_X)
        self.facing_right = True
        self.walking = False
        self.treat_timer = 0.0       # counting down while tending the injured man
        self.injured = None
        self.lost = None
        self.hint = ""               # what ACTION would do right now

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self, **kwargs):
        self.time_remaining = float(BONUS_TIME_LIMIT)
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.outcome = None
        self.outcome_timer = 0.0
        self.banked = 0.0
        self.player_x = float(PLAYER_START_X)
        self.facing_right = True
        self.walking = False
        self.treat_timer = 0.0
        self.hint = ""

        self.injured = RescueNPC(KIND_INJURED, INJURED_START_X, GROUND_Y,
                                 self._load_poses(walk="injured_man_limp_walk_right.png"))
        self.lost = RescueNPC(KIND_LOST, LOST_START_X, GROUND_Y,
                              self._load_poses(walk="lost_man_walk_right.png",
                                               confused="lost_man_confused.png"))

        char = self.manager.shared.get("character", "boy")
        self.walk_strip = self.assets.load_image(f"player_{char}_walk_right.png", "sprites", alpha=True)
        self.idle_strip = self.assets.load_image(f"player_{char}_idle_right.png", "sprites", alpha=True)

        # The same temple gate art Level 1 uses for its goal door, keyed the same way.
        self.temple_img = self.assets.load_image("temple_gate.png", "items", alpha=True,
                                                 scale=(240, 196))
        if self.temple_img:
            self.temple_img.set_colorkey((0, 0, 0))

        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)
        self.font_hud = self.assets.load_font(None, GAME_FONT_SIZE_HUD)

        self.assets.play_music("bgm_loop.ogg",
                               volume=self.manager.shared.get("music_volume", 0.35))

    def _load_poses(self, **names):
        """The optional G5 art for one person, by pose.

        Each file is checked for first: AssetManager answers a missing image with a
        pink placeholder, which would be drawn rather than fall back to the figure.
        """
        poses = {}
        for key, name in names.items():
            if os.path.exists(os.path.join(IMAGES_DIR, "sprites", name)):
                poses[key] = self.assets.load_image(name, "sprites", alpha=True)
        return poses

    @property
    def injured_saved(self):
        return self.injured is not None and self.injured.helped

    @property
    def lost_saved(self):
        return self.lost is not None and self.lost.helped

    @property
    def both_rescued(self):
        """A body saved and a soul guided — the detour is complete (Q8: both, or nothing)."""
        return self.injured_saved and self.lost_saved

    @property
    def helping_injured(self):
        return self.injured is not None and self.injured.state == "following"

    def _at(self, x):
        return abs(self.player_x - x) <= DESTINATION_REACH

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
            return

        if self.treat_timer > 0:          # hands busy tending him
            return

        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:
            self._act()

    def _act(self):
        """One button, whichever kind of help is within reach."""
        # Tending the injured man, once he has walked as far as the hospital.
        if self.helping_injured and abs(self.injured.x - HOSPITAL_X) <= DESTINATION_REACH:
            self.injured.state = "treating"
            self.injured.x = HOSPITAL_X
            self.treat_timer = TREAT_SECONDS
            self.assets.play_sound("box_open.wav", volume=0.3)
            return

        # Offering to walk with someone; from there each follows at his own pace.
        for npc in (self.injured, self.lost):
            if npc.state == "waiting" and npc.is_near(self.player_x):
                npc.take()
                self.assets.play_sound("jump.wav", volume=0.2)
                return

    def _current_hint(self):
        """What ACTION would do from here — shown so the verbs are never guessed at."""
        if self.treat_timer > 0:
            return "Tending to him..."
        if self.helping_injured:
            if abs(self.injured.x - HOSPITAL_X) <= DESTINATION_REACH:
                return "ACT: treat him at the hospital"
            return "Walk him to the hospital — he cannot hurry"
        if self.injured.state == "waiting" and self.injured.is_near(self.player_x):
            return "ACT: offer the injured man your arm"
        if self.lost.state == "waiting" and self.lost.is_near(self.player_x):
            return "ACT: offer to show him the way"
        if self.lost.state == "following":
            return "Lead him to the temple"
        return ""

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
        self._move_devotee(dt)
        self._update_rescues(dt)
        self.hint = self._current_hint()

        if self.both_rescued:
            self._finish("saved")
        elif self.time_remaining <= 0:
            self.time_remaining = 0.0
            self._finish("out_of_time")

    def _move_devotee(self, dt):
        """Walk left and right along the ground. Carrying a man is slower."""
        self.walking = False
        if self.treat_timer > 0:
            return

        speed = PLAYER_SPEED * 60.0
        inp = self.input_mgr
        if inp.actions[inp.LEFT] and not inp.actions[inp.RIGHT]:
            self.player_x -= speed * dt
            self.facing_right = False
            self.walking = True
        elif inp.actions[inp.RIGHT] and not inp.actions[inp.LEFT]:
            self.player_x += speed * dt
            self.facing_right = True
            self.walking = True

        self.player_x = max(PLAYER_HALF_W, min(LOGICAL_WIDTH - PLAYER_HALF_W, self.player_x))

    def _update_rescues(self, dt):
        for npc in (self.injured, self.lost):
            npc.update(dt, self.player_x, self.facing_right)

        # The injured man: tended to at the hospital, then he is well.
        if self.treat_timer > 0:
            self.treat_timer -= dt
            if self.treat_timer <= 0:
                self.treat_timer = 0.0
                self.injured.deliver()
                self.assets.play_sound("correct.wav", volume=0.4)

        # The lost man needs no prompting at the end: he knows the temple when he
        # sees it. Guiding him there is the whole of the help.
        if self.lost.state == "following" and abs(self.lost.x - TEMPLE_X) <= DESTINATION_REACH:
            self.lost.x = TEMPLE_X
            self.lost.deliver()
            self.assets.play_sound("correct.wav", volume=0.4)

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
        self._draw_world(surface)
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
        # the gradient the same glow only reads as a grey smudge. Stacked in many
        # faint steps, because two or three leave visible rings.
        halo = 190 + int(12 * math.sin(self.elapsed * 1.4))
        cy = LOGICAL_HEIGHT - 300
        glow = pygame.Surface((halo * 2, halo * 2), pygame.SRCALPHA)
        for i in range(14):
            radius = int(halo * (1.0 - i / 15.0))
            pygame.draw.circle(glow, (255, 198, 120, 5), (halo, halo), radius)
        surface.blit(glow, (LOGICAL_WIDTH // 2 - halo, cy - halo))

    def _draw_world(self, surface):
        """The ground, the two destinations, the two people, and the devotee.

        Anything without art yet falls back to a plain drawn stand-in, the way the
        Monk does, so the level stays playable as the art arrives piece by piece.
        """
        pygame.draw.rect(surface, (92, 74, 58), (0, GROUND_Y, LOGICAL_WIDTH, 120))
        pygame.draw.line(surface, (126, 104, 80), (0, GROUND_Y), (LOGICAL_WIDTH, GROUND_Y), 3)

        self._draw_marker(surface, HOSPITAL_X, GROUND_Y, "HOSPITAL", COLOR_CREAM, self.injured_saved)
        self._draw_temple(surface)

        player_top = GROUND_Y - 150
        for npc in (self.lost, self.injured):
            npc.draw(surface, self.font_title, self.player_x, player_top)
        self._draw_devotee(surface)

        if self.treat_timer > 0:
            self._draw_treating(surface)
        if self.hint:
            tip = self.font_body.render(self.hint, True, COLOR_GOLD_BRIGHT)
            surface.blit(tip, tip.get_rect(center=(int(self.player_x), player_top - 30)))

    def _draw_devotee(self, surface):
        """The devotee himself, from the walk strip — as the transition scenes do."""
        strip = self.walk_strip if self.walking else self.idle_strip
        sprite = None
        if strip:
            fh = strip.get_height()
            frames = max(1, strip.get_width() // fh)
            idx = int(self.elapsed / 0.1) % frames if self.walking else 0
            cell = pygame.Surface((fh, fh), pygame.SRCALPHA)
            cell.blit(strip, (0, 0), (idx * fh, 0, fh, fh))
            sprite = pygame.transform.smoothscale(cell, (150, 150))
            if not self.facing_right:
                sprite = pygame.transform.flip(sprite, True, False)

        if sprite:
            surface.blit(sprite, sprite.get_rect(midbottom=(int(self.player_x), GROUND_Y + 18)))
        else:                                  # no art at all: a plain marker
            pygame.draw.rect(surface, COLOR_WHITE,
                             (int(self.player_x) - 16, GROUND_Y - 110, 32, 110), border_radius=6)

    def _draw_treating(self, surface):
        """A bar while the injured man is tended to, so the wait reads as work."""
        done = 1.0 - max(0.0, self.treat_timer) / TREAT_SECONDS
        w, h = 260, 14
        x, y = HOSPITAL_X - w // 2, GROUND_Y - 230
        pygame.draw.rect(surface, (30, 26, 40), (x, y, w, h), border_radius=7)
        pygame.draw.rect(surface, COLOR_GREEN, (x, y, int(w * done), h), border_radius=7)
        pygame.draw.rect(surface, COLOR_CREAM, (x, y, w, h), width=2, border_radius=7)

    def _draw_temple(self, surface):
        """Level 1's temple gate, so the door he is led to is the door of that world."""
        if not self.temple_img:
            self._draw_marker(surface, TEMPLE_X, GROUND_Y, "TEMPLE", COLOR_GOLD, self.lost_saved)
            return

        rect = self.temple_img.get_rect(midbottom=(TEMPLE_X, GROUND_Y + 4))
        if self.lost_saved:                       # a soft welcome once he is inside
            halo = pygame.Surface((rect.width + 60, rect.height + 60), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (255, 215, 120, 60), halo.get_rect())
            surface.blit(halo, (rect.x - 30, rect.y - 30))
        surface.blit(self.temple_img, rect)

        # Both labels clear of the gate — at the gate's own top edge they sit on the
        # carving and neither reads.
        label = self.font_small.render("TEMPLE", True, COLOR_GOLD)
        surface.blit(label, label.get_rect(center=(TEMPLE_X, rect.top - 54)))
        tick = self.font_small.render("saved" if self.lost_saved else "waiting", True,
                                      COLOR_GREEN if self.lost_saved else COLOR_GOLD_DIM)
        surface.blit(tick, tick.get_rect(center=(TEMPLE_X, rect.top - 28)))

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

        goal = self.font_hud.render("Walk the injured man to the hospital; lead the lost man to the temple",
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
