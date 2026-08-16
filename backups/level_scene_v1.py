"""
level_scene.py — Core platformer gameplay scene with Box Roulette and Monk systems.
"""
import pygame
from scene_manager import Scene
from box_system import BoxSystem, CAT_GOAL
from monk_system import create_monk
from hazards import create_hazards_for_level, HAZARD_TIME_PENALTY, HAZARD_STUN_DURATION
from level_layouts import build_level_platforms
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, GRAVITY, PLAYER_SPEED,
    PLAYER_JUMP_FORCE, PLAYER_MAX_FALL_SPEED, PLAYER_WIDTH, PLAYER_HEIGHT,
    LEVEL_TIME_LIMIT, LEVEL_NAMES, LEVEL_SUBTITLES,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_WHITE, COLOR_CREAM,
    COLOR_RED, COLOR_GREEN, COLOR_SAFFRON, COLOR_GOLD_DIM,
    FONT_SIZE_HUD, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
    SCENE_TITLE, SCENE_LEVEL, SCENE_TRANSITION, SCENE_VICTORY,
)


class Player:
    """Player with physics."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.facing_right = True
        self.frozen = False
        self.freeze_timer = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def freeze(self, duration):
        self.frozen = True
        self.freeze_timer = duration

    def update(self, dt, platforms):
        # Freeze countdown
        if self.frozen:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.frozen = False
                self.freeze_timer = 0
            # Still apply gravity while frozen, but no player input
            self.vy += GRAVITY
            if self.vy > PLAYER_MAX_FALL_SPEED:
                self.vy = PLAYER_MAX_FALL_SPEED
            self.y += self.vy
            self.on_ground = False
            pr = self.rect
            for plat in platforms:
                if pr.colliderect(plat):
                    if self.vy > 0:
                        self.y = plat.top - self.height
                        self.vy = 0
                        self.on_ground = True
                    elif self.vy < 0:
                        self.y = plat.bottom
                        self.vy = 0
            return

        # Apply gravity
        self.vy += GRAVITY
        if self.vy > PLAYER_MAX_FALL_SPEED:
            self.vy = PLAYER_MAX_FALL_SPEED

        # Move horizontally
        self.x += self.vx
        pr = self.rect
        for plat in platforms:
            if pr.colliderect(plat):
                if self.vx > 0:
                    self.x = plat.left - self.width
                elif self.vx < 0:
                    self.x = plat.right
                pr = self.rect

        # Move vertically
        self.y += self.vy
        self.on_ground = False
        pr = self.rect
        for plat in platforms:
            if pr.colliderect(plat):
                if self.vy > 0:
                    self.y = plat.top - self.height
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = plat.bottom
                    self.vy = 0

        # Keep in bounds
        if self.x < 0:
            self.x = 0
        if self.y > LOGICAL_HEIGHT:
            self.y = 100
            self.vy = 0


class LevelScene(Scene):
    """Full gameplay level with Box Roulette and Monk systems."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.player = None
        self.platforms = []
        self.box_system = None
        self.monk = None
        self.hazards = []
        self.level = 1
        self.time_remaining = 0.0
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.level_complete = False
        self.complete_timer = 0.0

    def on_enter(self, **kwargs):
        self.level = kwargs.get("level", 1)
        self.manager.shared["current_level"] = self.level
        self.time_remaining = float(LEVEL_TIME_LIMIT.get(self.level, 120))
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.level_complete = False
        self.complete_timer = 0.0

        # Fonts
        self.font_hud = self.assets.load_font(None, FONT_SIZE_HUD)
        self.font_title = self.assets.load_font(None, FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, FONT_SIZE_SMALL)

        # Background
        bg_name = f"level{self.level}_background.png"
        self.bg = self.assets.load_image(bg_name, "backgrounds", alpha=False,
                                         scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT))

        # Build level from layouts module
        self.platforms = build_level_platforms(self.level)
        self.player = Player(80, LOGICAL_HEIGHT - 30 - PLAYER_HEIGHT - 10)

        # Phase 2 systems
        self.box_system = BoxSystem(self.level, self.platforms)
        self.monk = create_monk(self.level, self.platforms)

        # Phase 3 — hazards
        self.hazards = create_hazards_for_level(self.level, self.platforms)

        # Audio
        self.assets.play_music("bgm_loop.wav", volume=0.4)

    # _build_platforms is now handled by level_layouts.build_level_platforms()

    def handle_events(self, events, input_mgr):
        if input_mgr.just_pressed[input_mgr.BACK]:
            if self.monk and self.monk.dialogue_active:
                self.monk.dialogue_active = False
            else:
                self.manager.switch_to(SCENE_TITLE)
            return

        # Monk dialogue navigation
        if self.monk and self.monk.dialogue_active:
            if input_mgr.just_pressed[input_mgr.UP]:
                self.monk.selected_choice = 0
            elif input_mgr.just_pressed[input_mgr.JUMP]:
                # DOWN maps to selecting choice 1
                self.monk.selected_choice = 1
            if input_mgr.just_pressed[input_mgr.ACTION]:
                correct = self.monk.submit_answer()
                if correct:
                    self.assets.play_sound("correct.wav")
                    self.box_system.highlight_goal_box()
                else:
                    self.assets.play_sound("wrong.wav")
            return

        # Monk interaction
        if input_mgr.just_pressed[input_mgr.UP] and self.monk:
            if self.monk.show_prompt and not self.monk.interacted:
                self.monk.start_dialogue()
                return

        # Open box (press UP near a box)
        if input_mgr.just_pressed[input_mgr.ACTION]:
            result = self.box_system.try_open_nearest(self.player.rect)
            if result:
                self.assets.play_sound("box_open.wav")
                item, time_delta, freeze_dur = result
                self.time_remaining += time_delta
                if freeze_dur > 0:
                    self.player.freeze(freeze_dur)
                    self.assets.play_sound("wrong.wav") # play wrong sound for distraction too
                if item["cat"] == CAT_GOAL:
                    self.assets.play_sound("level_complete.wav")
                    self.assets.stop_music()
                    self.level_complete = True
                    self.complete_timer = 3.0

    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 300 * dt)

        # If monk dialogue is active, pause gameplay
        if self.monk and self.monk.dialogue_active:
            return

        # Level complete countdown
        if self.level_complete:
            self.complete_timer -= dt
            if self.complete_timer <= 0:
                self._advance_level()
            return

        # Timer
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.time_remaining = 0

        # Player input
        if not self.player.frozen:
            inp = self.input_mgr
            self.player.vx = 0
            if inp.actions[inp.LEFT]:
                self.player.vx = -PLAYER_SPEED
                self.player.facing_right = False
            if inp.actions[inp.RIGHT]:
                self.player.vx = PLAYER_SPEED
                self.player.facing_right = True
            if inp.just_pressed[inp.JUMP] and self.player.on_ground:
                self.player.vy = PLAYER_JUMP_FORCE
                self.assets.play_sound("jump.wav")

        self.player.update(dt, self.platforms)
        self.box_system.update(dt, self.elapsed)
        self.monk.update(dt, self.elapsed, self.player.rect)

        # Update hazards and check collision
        for hazard in self.hazards:
            hazard.update(dt)
            if not self.player.frozen and hazard.check_collision(self.player.rect):
                self.assets.play_sound("hazard.wav")
                self.time_remaining -= HAZARD_TIME_PENALTY
                self.player.freeze(HAZARD_STUN_DURATION)

    def _advance_level(self):
        """Move to next level or victory."""
        time_spent = LEVEL_TIME_LIMIT.get(self.level, 120) - self.time_remaining
        self.manager.shared["level_times"][self.level] = time_spent
        self.manager.shared["total_time"] += time_spent
        self.manager.shared["monk_correct"][self.level] = (
            self.monk.answered_correctly if self.monk.interacted else None
        )

        next_level = self.level + 1
        if next_level > 4:
            # Check if victory scene is registered, else go to title
            if SCENE_VICTORY in self.manager.scenes:
                self.manager.switch_to(SCENE_VICTORY)
            else:
                self.manager.switch_to(SCENE_TITLE)
        else:
            # Check if transition scene is registered
            if SCENE_TRANSITION in self.manager.scenes:
                self.manager.switch_to(SCENE_TRANSITION, next_level=next_level)
            else:
                self.manager.switch_to(SCENE_LEVEL, level=next_level)

    def draw(self, surface):
        surface.blit(self.bg, (0, 0))

        # Platforms
        for plat in self.platforms:
            ps = pygame.Surface((plat.width, plat.height), pygame.SRCALPHA)
            pygame.draw.rect(ps, (80, 60, 40, 200), ps.get_rect(), border_radius=4)
            pygame.draw.rect(ps, (120, 100, 70, 200), ps.get_rect(), width=2, border_radius=4)
            surface.blit(ps, plat.topleft)

        # Hazards
        for hazard in self.hazards:
            hazard.draw(surface)

        # Boxes
        self.box_system.draw(surface, self.font_hud)

        # Monk
        self.monk.draw(surface, self.font_body, self.font_small)

        # Player
        color = (100, 180, 255) if self.manager.shared.get("character") == "boy" else (255, 140, 180)
        if self.player.frozen:
            # Flashing when frozen
            if int(self.elapsed * 8) % 2:
                color = (255, 80, 80)
        pygame.draw.rect(surface, color, self.player.rect, border_radius=6)
        # Eyes
        ey = self.player.rect.y + 15
        if self.player.facing_right:
            pygame.draw.circle(surface, COLOR_WHITE, (self.player.rect.x + 32, ey), 5)
            pygame.draw.circle(surface, (0, 0, 0), (self.player.rect.x + 34, ey), 2)
        else:
            pygame.draw.circle(surface, COLOR_WHITE, (self.player.rect.x + 16, ey), 5)
            pygame.draw.circle(surface, (0, 0, 0), (self.player.rect.x + 14, ey), 2)

        # ── HUD ──
        hud_bar = pygame.Surface((LOGICAL_WIDTH, 45), pygame.SRCALPHA)
        hud_bar.fill((0, 0, 0, 150))
        surface.blit(hud_bar, (0, 0))

        # Level name
        name = f"Level {self.level}: {LEVEL_NAMES.get(self.level, '???')}"
        name_surf = self.font_hud.render(name, True, COLOR_GOLD_BRIGHT)
        surface.blit(name_surf, (15, 12))
        sub = f"({LEVEL_SUBTITLES.get(self.level, '')})"
        sub_surf = self.font_hud.render(sub, True, COLOR_SAFFRON)
        surface.blit(sub_surf, (15 + name_surf.get_width() + 10, 12))

        # Timer
        mins = int(max(0, self.time_remaining)) // 60
        secs = int(max(0, self.time_remaining)) % 60
        t_color = COLOR_RED if self.time_remaining < 20 else COLOR_GREEN
        timer_surf = self.font_hud.render(f"Time: {mins:02d}:{secs:02d}", True, t_color)
        surface.blit(timer_surf, (LOGICAL_WIDTH - timer_surf.get_width() - 15, 12))

        # Goal status
        status = "KEY FOUND!" if self.box_system.goal_found else "Find the Goal Item"
        st_color = COLOR_GOLD_BRIGHT if self.box_system.goal_found else COLOR_GOLD_DIM
        st_surf = self.font_hud.render(status, True, st_color)
        surface.blit(st_surf, (LOGICAL_WIDTH // 2 - st_surf.get_width() // 2, 12))

        # Freeze indicator
        if self.player.frozen:
            fz = self.font_body.render(f"FROZEN! {self.player.freeze_timer:.1f}s", True, COLOR_RED)
            surface.blit(fz, fz.get_rect(center=(LOGICAL_WIDTH // 2, 120)))

        # Box messages
        self.box_system.draw_message(surface, self.font_body)

        # Level complete banner
        if self.level_complete:
            overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, (0, 0))
            complete = self.font_title.render("LEVEL COMPLETE!", True, COLOR_GOLD_BRIGHT)
            surface.blit(complete, complete.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2)))

        # Touch controls
        self.input_mgr.draw_touch_controls(surface, self.font_hud)

        # Monk dialogue overlay (drawn last, on top)
        if self.monk:
            self.monk.draw_dialogue(surface, self.font_title, self.font_body, self.font_small)

        # Fade-in
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
