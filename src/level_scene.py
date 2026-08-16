"""
level_scene.py — Core platformer gameplay scene with Box Roulette and Monk systems.
"""
import pygame
import math
import random
import os
from settings import IMAGES_DIR
from scene_manager import Scene
from box_system import BoxSystem, CAT_GOAL, CAT_SUPPORT, CAT_DISTRACTION, CAT_NO_EFFECT, CAT_COLORS
from monk_system import create_monk
from hazards import create_hazards_for_level, HAZARD_TIME_PENALTY, HAZARD_STUN_DURATION
from level_layouts import build_level_platforms
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, GRAVITY, PLAYER_SPEED,
    PLAYER_JUMP_FORCE, LEVEL_JUMP_FORCES, PLAYER_MAX_FALL_SPEED, PLAYER_WIDTH, PLAYER_HEIGHT,
    LEVEL_TIME_LIMIT, LEVEL_NAMES, LEVEL_SUBTITLES,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_WHITE, COLOR_CREAM,
    COLOR_RED, COLOR_GREEN, COLOR_SAFFRON, COLOR_GOLD_DIM,
    GAME_FONT_SIZE_HUD, GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL,
    SCENE_TITLE, SCENE_LEVEL, SCENE_TRANSITION, SCENE_VICTORY,
    DEFAULT_GAME_MODE, ASSETS_DIR,
)


def get_item_image_name(name):
    """Convert item name string to standard image filename."""
    name_clean = name.lower()
    name_clean = name_clean.replace("(", "").replace(")", "")
    name_clean = name_clean.replace(" ", "_")
    return f"{name_clean}.png"


class Player:
    """Player with physics, trail tracking, and squash-and-stretch animations."""
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
        self.can_fly = False   # Activated when Akshat is found in Level 2

        # Squash and stretch state
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.was_on_ground = True
        self.trail = []

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def freeze(self, duration):
        self.frozen = True
        self.freeze_timer = duration

    def update(self, dt, platforms):
        # Update trail
        self.trail.append((self.x + self.width // 2, self.y + self.height // 2))
        if len(self.trail) > 12:
            self.trail.pop(0)

        # Decay squash and stretch back to neutral
        self.scale_x += (1.0 - self.scale_x) * 12 * dt
        self.scale_y += (1.0 - self.scale_y) * 12 * dt

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
            
            # Resolve vertical collisions
            pr = self.rect
            for plat in platforms:
                if pr.colliderect(plat):
                    if self.vy > 0:
                        self.y = plat.top - self.height
                        self.vy = 0
                        if not self.was_on_ground:
                            self.scale_y = 0.65
                            self.scale_x = 1.35
                    elif self.vy < 0:
                        self.y = plat.bottom
                        self.vy = 0
            
            # Stable ground check (shift down 1px)
            self.on_ground = False
            test_rect = pygame.Rect(int(self.x), int(self.y) + 1, self.width, self.height)
            for plat in platforms:
                if test_rect.colliderect(plat):
                    if self.y + self.height <= plat.top + 2:
                        self.on_ground = True
                        break

            self.was_on_ground = self.on_ground
            return

        # Apply gravity (skip if flying)
        if not self.can_fly:
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
        pr = self.rect
        for plat in platforms:
            if pr.colliderect(plat):
                if self.vy > 0:
                    self.y = plat.top - self.height
                    self.vy = 0
                    if not self.was_on_ground:
                        # Landing squash
                        self.scale_y = 0.65
                        self.scale_x = 1.35
                elif self.vy < 0:
                    self.y = plat.bottom
                    self.vy = 0

        # Stable ground check (shift down 1px)
        self.on_ground = False
        test_rect = pygame.Rect(int(self.x), int(self.y) + 1, self.width, self.height)
        for plat in platforms:
            if test_rect.colliderect(plat):
                if self.y + self.height <= plat.top + 2:
                    self.on_ground = True
                    break

        # Keep in bounds
        if self.x < 0:
            self.x = 0
        if self.can_fly and self.y < 0:
            self.y = 0
            self.vy = 0
        if self.y > LOGICAL_HEIGHT:
            self.y = 100
            self.vy = 0


        self.was_on_ground = self.on_ground


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
        self.game_over = False
        self.game_over_choice = 0   # 0 = Restart Level, 1 = Back to Start
        self.game_over_score_shown = False  # True after player confirms score
        self.level_goals = {}         # loaded from level_goals.json
        self.particles = []
        self.to_be_continued = False   # True on Level 2 complete for kid/standard
        self.item_popup = None         # Active box item pop-up dict

    def on_enter(self, **kwargs):
        self.level = kwargs.get("level", 1)
        self.manager.shared["current_level"] = self.level
        # Read game mode from shared state (set by title screen)
        self.game_mode = self.manager.shared.get("game_mode", DEFAULT_GAME_MODE)
        self.time_remaining = float(LEVEL_TIME_LIMIT.get(self.level, 120))
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.level_complete = False
        self.complete_timer = 0.0
        self.game_over = False
        self.game_over_choice = 0
        self.game_over_score_shown = False
        self.particles = []
        self.platform_glow_texture = None   # reset glow cache on each level enter
        self.to_be_continued = False
        self.item_popup = None

        # Load level goals from JSON
        import json, os
        goals_path = os.path.join(ASSETS_DIR, "level_goals.json")
        try:
            with open(goals_path, "r", encoding="utf-8") as f:
                self.level_goals = json.load(f)
        except Exception:
            self.level_goals = {}


        # ── Player sprite animation state ──
        self.anim_state  = "idle"   # current animation name
        self.anim_frame  = 0        # current frame index within the strip
        self.anim_timer  = 0.0      # seconds elapsed for current frame
        # How many seconds each frame is displayed per animation state
        self.anim_fps = {
            "idle": 0.20, "walk": 0.12, "run": 0.08,
            "jump": 0.15, "fall": 0.12, "stun": 0.25,
        }

        # Load all 12 sprite strips (128px-tall horizontal strips, N*128 wide)
        # Uses the character selected on the Character Select screen ("boy" or "girl").
        # Falls back to boy sprites if the chosen character's strip is missing.
        char_type = self.manager.shared.get("character", "boy")
        self.player_strips = {}
        for state in ("idle", "walk", "run", "jump", "fall", "stun"):
            for facing in ("left", "right"):
                key  = f"{state}_{facing}"
                name = f"player_{char_type}_{state}_{facing}.png"
                surf = self.assets.load_image(name, "sprites", alpha=True)
                if surf is None and char_type != "boy":
                    # Graceful fallback: use boy strip if girl strip is missing
                    name = f"player_boy_{state}_{facing}.png"
                    surf = self.assets.load_image(name, "sprites", alpha=True)
                self.player_strips[key] = surf

        # Fonts (Using larger gameplay sizes for modern visual AAA quality)
        self.font_hud = self.assets.load_font(None, GAME_FONT_SIZE_HUD)
        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

        # Background
        bg_name = f"level{self.level}_background.png"
        self.bg = self.assets.load_image(bg_name, "backgrounds", alpha=False,
                                         scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT))

        # Play level-specific background music
        vol = self.manager.shared.get("music_volume", 0.35)
        bgm_track = f"level{self.level}_bgm.wav" if os.path.exists(os.path.join(ASSETS_DIR, "audio", "bgm", f"level{self.level}_bgm.wav")) else "bgm_loop.wav"
        self.assets.play_music(bgm_track, volume=vol)

        self._score_registered = False

        # Reset or initialize game stats and unique question tracker on starting Level 1
        if self.level == 1:
            self.manager.shared["total_time"] = 0.0
            self.manager.shared["level_times"] = {}
            self.manager.shared["monk_correct"] = {}
            self.manager.shared["boxes_opened"] = {}
            self.manager.shared["asked_questions"] = []
            self.manager.shared["level_scores"] = {}
            self.manager.shared["total_score"] = 0

        elif "asked_questions" not in self.manager.shared:
            self.manager.shared["asked_questions"] = []

        if "level_scores" not in self.manager.shared:
            self.manager.shared["level_scores"] = {}
        if "total_score" not in self.manager.shared:
            self.manager.shared["total_score"] = 0

        # Load Bhagwan image if level 2
        self.bhagwan_img = None
        if self.level == 2:
            self.bhagwan_img = self.assets.load_image("bhagwan.jpg", "items", alpha=False)


        # Load Acharya Portrait for Q&A Scroll
        self.acharya_img = self.assets.load_image("acharya_portrait.png", "items", alpha=True, scale=(200, 220))

        # Goal Temple Gate for Level 1
        self.temple_gate_img = None
        if self.level == 1:
            # Scale of the Temple Gate can be adjusted here (Width, Height). Changed default to 220x280.
            self.temple_gate_img = self.assets.load_image("temple_gate.png", "items", alpha=True, scale=(220, 180))
            if self.temple_gate_img:
                # Keying out pure black background color to transparency
                self.temple_gate_img.set_colorkey((0, 0, 0))

        # Build level from layouts module
        self.platforms = build_level_platforms(self.level)
        # self.player = Player(80, LOGICAL_HEIGHT - 30 - PLAYER_HEIGHT - 10)
        if self.level == 2:
            # Change 150 and H - 250 to whatever starting X and Y coordinates you want
            self.player = Player(80, LOGICAL_HEIGHT - 50- PLAYER_HEIGHT - 100)
        else:
            self.player = Player(80, LOGICAL_HEIGHT - 30 - PLAYER_HEIGHT - 10)

        # Instantiation Order for fully randomized safe Q&A Monk and Box Roulette systems:
        # 1. Build hazards first
        self.hazards = create_hazards_for_level(self.level, self.platforms)
        
        # 2. Build monk second (passing hazards and the session question tracker to avoid repeating questions)
        self.monk = create_monk(self.level, self.platforms, self.hazards, self.manager.shared["asked_questions"], self.game_mode)
        
        # 3. Build box system third (passing hazards and monk so boxes don't overlap with them)
        self.box_system = BoxSystem(self.level, self.platforms, self.hazards, self.monk)
        self.box_system.akshat_found = False  # Level 2: set True when Akshat box is opened
        self.bhagwan_platform_added = False

        # Audio
        self.assets.play_music("bgm_loop.wav", volume=0.4)

    def handle_events(self, events, input_mgr):
        self.mouse_clicked_this_frame = False
        # Developer Coordinate Finder
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_clicked_this_frame = True
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y
                # Shift visual Y click coordinate back to background space (offset by +80)
                actual_my = my + 80
                print(f"p.append(pygame.Rect({mx}, H - {LOGICAL_HEIGHT - actual_my}, 200, PH))  # Clicked: x={mx}, y={actual_my} (relative to bottom: H - {LOGICAL_HEIGHT - actual_my})")

        # ── Item Pop-up Input: dismiss if key/click/jump/action/controller button ──
        if self.item_popup is not None:
            dismiss = False
            if (input_mgr.just_pressed[input_mgr.JUMP] or
                input_mgr.just_pressed[input_mgr.ACTION] or
                input_mgr.just_pressed[input_mgr.MENU_SELECT] or
                input_mgr.just_pressed[input_mgr.BACK] or
                input_mgr.just_pressed[input_mgr.MENU_BACK]):
                dismiss = True
            for event in events:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
                    dismiss = True
            if dismiss:
                self._dismiss_item_popup()
            return


        # ── Level Complete: wait for player to press Continue ──
        if self.level_complete:
            inp = input_mgr
            advance = inp.just_pressed[inp.ACTION] or inp.just_pressed[inp.JUMP]
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    advance = True
            if advance:
                self.assets.play_sound("level_complete.wav", volume=0.25)
                self._advance_level()
            return

        # ── Game Over screen input ──
        if self.game_over:
            inp = input_mgr
            # Phase 1: score shown, waiting for player to dismiss it and see buttons
            if not self.game_over_score_shown:
                # Any key, controller button, or click advances to button selection phase
                confirm = (inp.just_pressed[inp.ACTION] or inp.just_pressed[inp.JUMP]
                           or inp.just_pressed[inp.MENU_SELECT] or inp.just_pressed[inp.MENU_BACK])
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        confirm = True
                if confirm:
                    self.game_over_score_shown = True
                    self.assets.play_sound("jump.wav", volume=0.08)
            else:
                # Phase 2: toggle button highlight — keyboard OR controller
                nav_left  = inp.just_pressed[inp.MENU_LEFT]  or inp.just_pressed[inp.LEFT]
                nav_right = inp.just_pressed[inp.MENU_RIGHT] or inp.just_pressed[inp.RIGHT]
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            nav_left = True
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            nav_right = True
                if nav_left:
                    self.game_over_choice = 0
                    self.assets.play_sound("jump.wav", volume=0.08)
                elif nav_right:
                    self.game_over_choice = 1
                    self.assets.play_sound("jump.wav", volume=0.08)

                # Confirm via controller or keyboard
                if (inp.just_pressed[inp.ACTION] or inp.just_pressed[inp.JUMP]
                        or inp.just_pressed[inp.MENU_SELECT]):
                    if self.game_over_choice == 0:
                        self.manager.switch_to(SCENE_LEVEL, level=self.level)
                    else:
                        self.manager.switch_to(SCENE_TITLE)

                # Mouse hover updates highlight; click confirms
                band_h = 110
                band_y = LOGICAL_HEIGHT // 2 - 70
                btn_y  = band_y + band_h + 30
                btn_gap = 340
                btn_rects = [
                    pygame.Rect(LOGICAL_WIDTH // 2 - btn_gap // 2 - 150, btn_y, 300, 70),
                    pygame.Rect(LOGICAL_WIDTH // 2 + btn_gap // 2 - 150, btn_y, 300, 70),
                ]
                mx, my = inp.mouse_x, inp.mouse_y
                for i, r in enumerate(btn_rects):
                    if r.collidepoint(mx, my):
                        self.game_over_choice = i  # hover syncs highlight
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for i, r in enumerate(btn_rects):
                            if r.collidepoint(inp.mouse_x, inp.mouse_y):
                                self.assets.play_sound("level_complete.wav", volume=0.3)
                                if i == 0:
                                    self.manager.switch_to(SCENE_LEVEL, level=self.level)
                                else:
                                    self.manager.switch_to(SCENE_TITLE)
            return

        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            if self.monk and self.monk.dialogue_active:
                self.monk.dialogue_active = False
            else:
                self.manager.switch_to(SCENE_TITLE)
            return

        # Proximity interaction with the Temple Gate for Level 1
        if self.level == 1:
            gate_rect = pygame.Rect(1740, LOGICAL_HEIGHT - 280, 160, 260)
            if self.player.rect.colliderect(gate_rect):
                if self.box_system.goal_found:
                    # Player is at the gate with the key!
                    if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.UP] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:

                        self.assets.play_sound("level_complete.wav")
                        self.assets.stop_music()
                        self.level_complete = True
                        self.complete_timer = 3.0
                        return

        # Monk dialogue navigation
        if self.monk and self.monk.dialogue_active:
            # Match the actual monk_system.py enlarged box dimensions:
            box_w, box_h = 920, 380
            bx = (LOGICAL_WIDTH - box_w) // 2
            by = (LOGICAL_HEIGHT - box_h) // 2
            text_cx = bx + 260 + (box_w - 290) // 2

            opt0_rect = pygame.Rect(text_cx - 280, by + 200 - 22, 560, 44)
            opt1_rect = pygame.Rect(text_cx - 280, by + 258 - 22, 560, 44)

            # Hover detection
            mx, my = input_mgr.mouse_x, input_mgr.mouse_y
            if opt0_rect.collidepoint(mx, my):
                if self.monk.selected_choice != 0:
                    self.monk.selected_choice = 0
                    self.assets.play_sound("jump.wav", volume=0.08)
            elif opt1_rect.collidepoint(mx, my):
                if self.monk.selected_choice != 1:
                    self.monk.selected_choice = 1
                    self.assets.play_sound("jump.wav", volume=0.08)

            # Controller & Keyboard navigation
            if input_mgr.just_pressed[input_mgr.MENU_UP]:
                self.monk.selected_choice = 0
                self.assets.play_sound("jump.wav", volume=0.08)
            elif input_mgr.just_pressed[input_mgr.JUMP] or input_mgr.just_pressed[input_mgr.MENU_DOWN]:
                self.monk.selected_choice = 1
                self.assets.play_sound("jump.wav", volume=0.08)


            # Mouse click submission
            clicked = False
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if opt0_rect.collidepoint(mx, my) or opt1_rect.collidepoint(mx, my):
                        clicked = True

            if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT] or clicked:
                correct = self.monk.submit_answer()
                if correct:
                    self.assets.play_sound("correct.wav")
                    self.box_system.highlight_goal_box()
                else:
                    self.assets.play_sound("wrong.wav")
            return

        # Monk interaction (ACTION, MENU_UP, or MENU_SELECT when near monk)
        if (input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_UP] or input_mgr.just_pressed[input_mgr.MENU_SELECT]) and self.monk:
            if self.monk.show_prompt and not self.monk.interacted:
                self.monk.start_dialogue()
                return

        # Open box (ACTION or MENU_SELECT near a box)
        if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]:


            result = self.box_system.try_open_nearest(self.player.rect)
            if result:
                self.assets.play_sound("box_open.wav")
                item, time_delta, freeze_dur = result
                
                # Open particle effects burst (delegated to draw/update)
                # Spawn some star particles at the box center!
                bx = self.player.x + self.player.width // 2
                by = self.player.y - 10
                p_color = COLOR_GREEN if time_delta > 0 else (COLOR_RED if freeze_dur > 0 else COLOR_GOLD)
                for _ in range(12):
                    self.particles.append({
                        "x": bx, "y": by,
                        "vx": random.uniform(-60, 60),
                        "vy": random.uniform(-80, -20),
                        "color": p_color,
                        "size": random.randint(3, 6),
                        "lifetime": random.uniform(0.5, 0.9),
                        "age": 0.0
                    })

                # Show item pop-up instead of applying immediately
                self.item_popup = {
                    "item": item,
                    "time_delta": time_delta,
                    "freeze_dur": freeze_dur,
                    "message": self.box_system.message,
                    "timer": 5.0
                }

    def _dismiss_item_popup(self):
        if self.item_popup is None:
            return
        popup = self.item_popup
        self.item_popup = None

        item = popup["item"]
        time_delta = popup["time_delta"]
        freeze_dur = popup["freeze_dur"]

        # Apply time change
        self.time_remaining += time_delta

        # Apply freeze/stun
        if freeze_dur > 0:
            self.player.freeze(freeze_dur)
            self.assets.play_sound("wrong.wav")

        # Apply goal effects or completed triggers
        if item["cat"] == CAT_GOAL:
            if self.level == 1:
                self.assets.play_sound("correct.wav")
            elif self.level == 2:
                # Akshat found: activate flying, new goal - do NOT complete level yet
                self.assets.play_sound("correct.wav")
                self.player.can_fly = True
                self.box_system.akshat_found = True
            else:
                self.assets.play_sound("level_complete.wav")
                self.assets.stop_music()
                self.level_complete = True
                self.complete_timer = 3.0

    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 300 * dt)

        # Update running particles
        for p in self.particles:
            p["age"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
        self.particles = [p for p in self.particles if p["age"] < p["lifetime"]]

        # ── Item pop-up update: count down timer and suspend other gameplay updates ──
        if self.item_popup is not None:
            self.item_popup["timer"] -= dt
            if self.item_popup["timer"] <= 0:
                self._dismiss_item_popup()

            # Maintain visual animations of the player & boxes so the screen doesn't feel dead
            p = self.player
            new_state = "stun" if p.frozen else "idle"
            if new_state != self.anim_state:
                self.anim_state = new_state
                self.anim_frame = 0
                self.anim_timer = 0.0

            self.anim_timer += dt
            frame_dur = self.anim_fps.get(self.anim_state, 0.15)
            if self.anim_timer >= frame_dur:
                self.anim_timer -= frame_dur
                facing = "right" if p.facing_right else "left"
                strip = self.player_strips.get(f"{self.anim_state}_{facing}")
                if strip:
                    n_frames = strip.get_width() // 128
                    self.anim_frame = (self.anim_frame + 1) % n_frames

            self.box_system.update(dt, self.elapsed)
            return

        # If monk dialogue is active, update the monk (to advance typewriter question text) and return early
        if self.monk and self.monk.dialogue_active:
            self.monk.update(dt, self.elapsed, self.player.rect)
            return

        # Level complete countdown
        if self.level_complete:
            # No auto-advance: wait for player to press Continue
            return

        # Timer
        if not self.game_over:
            self.time_remaining -= dt
        if self.time_remaining <= 0 and not self.game_over:
            self.time_remaining = 0
            # Developer mode: timer shows 0 but never triggers game over
            if self.game_mode != "developer":
                self.game_over = True
                self.assets.stop_music()
                self.assets.play_sound("wrong.wav")


        # Player input
        if not self.player.frozen:
            inp = self.input_mgr
            target_vx = 0
            if inp.actions[inp.LEFT]:
                target_vx = -PLAYER_SPEED
                self.player.facing_right = False
            elif inp.actions[inp.RIGHT]:
                target_vx = PLAYER_SPEED
                self.player.facing_right = True

            # Smooth acceleration (lerp)
            self.player.vx += (target_vx - self.player.vx) * 15 * dt

            if self.player.can_fly:
                # 8-way responsive flying/floating controls — keyboard + controller
                target_vy = 0
                keys = pygame.key.get_pressed()
                if (inp.actions[inp.UP] or inp.actions[inp.JUMP]
                        or inp.actions[inp.MENU_UP]):
                    target_vy = -PLAYER_SPEED
                elif (keys[pygame.K_DOWN] or keys[pygame.K_s]
                        or inp.actions[inp.MENU_DOWN]):
                    target_vy = PLAYER_SPEED

                # Instant responsiveness on direction change
                if target_vy > 0 and self.player.vy < 0:
                    self.player.vy = 0
                elif target_vy < 0 and self.player.vy > 0:
                    self.player.vy = 0

                # Smooth vertical acceleration
                self.player.vy += (target_vy - self.player.vy) * 20 * dt

            elif inp.just_pressed[inp.JUMP] and self.player.on_ground:
                self.player.vy = LEVEL_JUMP_FORCES.get(self.level, PLAYER_JUMP_FORCE)
                self.assets.play_sound("jump.wav")
                self.player.scale_y = 1.35
                self.player.scale_x = 0.7
                for _ in range(6):
                    self.particles.append({
                        "x": self.player.x + self.player.width/2 + random.uniform(-10, 10),
                        "y": self.player.y + self.player.height,
                        "vx": random.uniform(-40, 40),
                        "vy": random.uniform(-20, -5),
                        "color": COLOR_WHITE,
                        "size": random.randint(2, 4),
                        "lifetime": random.uniform(0.2, 0.4),
                        "age": 0.0
                    })

        # Level 2: Dynamically add Bhagwan platform when Akshat is found
        if self.level == 2 and getattr(self.box_system, "akshat_found", False):
            if not getattr(self, "bhagwan_platform_added", False):
                self.platforms.append(pygame.Rect(15, 150, 150, 150))
                self.bhagwan_platform_added = True

        was_on_ground = self.player.on_ground
        self.player.update(dt, self.platforms)

        # Level 2: check if player reached Bhagwan (interact on lower side of image)
        if self.level == 2 and self.player.can_fly and not self.level_complete:
            # Trigger zone at the lower side of Bhagwan (Bhagwan rect is y=150 to y=300)
            trigger_rect = pygame.Rect(15 - 20, 300, 150 + 40, 100)
            if self.player.rect.colliderect(trigger_rect):
                keys = pygame.key.get_pressed()
                inp = self.input_mgr
                interact = (
                    inp.just_pressed[inp.ACTION] or 
                    inp.just_pressed[inp.UP] or 
                    keys[pygame.K_RETURN] or 
                    keys[pygame.K_KP_ENTER] or 
                    getattr(self, "mouse_clicked_this_frame", False)
                )
                if interact:
                    self.assets.play_sound("level_complete.wav")
                    self.assets.stop_music()
                    self.level_complete = True
                    self.complete_timer = 3.0
        
        # Landing Dust
        if self.player.on_ground and not was_on_ground:
            for _ in range(8):
                self.particles.append({
                    "x": self.player.x + self.player.width/2 + random.uniform(-15, 15),
                    "y": self.player.y + self.player.height,
                    "vx": random.uniform(-60, 60),
                    "vy": random.uniform(-20, 0),
                    "color": COLOR_GOLD_DIM,
                    "size": random.randint(3, 6),
                    "lifetime": random.uniform(0.2, 0.5),
                    "age": 0.0
                })
        self.box_system.update(dt, self.elapsed)
        self.monk.update(dt, self.elapsed, self.player.rect)

        # ── Player animation state machine ──
        p = self.player
        if p.frozen:
            new_state = "stun"
        elif not p.on_ground and p.vy < 0:
            new_state = "jump"
        elif not p.on_ground and p.vy >= 0:
            new_state = "fall"
        elif abs(p.vx) > PLAYER_SPEED * 0.6:
            new_state = "run"
        elif abs(p.vx) > 0.5:
            new_state = "walk"
        else:
            new_state = "idle"

        if new_state != self.anim_state:
            self.anim_state = new_state
            self.anim_frame = 0
            self.anim_timer = 0.0

        self.anim_timer += dt
        frame_dur = self.anim_fps.get(self.anim_state, 0.15)
        if self.anim_timer >= frame_dur:
            self.anim_timer -= frame_dur
            facing = "right" if p.facing_right else "left"
            strip = self.player_strips.get(f"{self.anim_state}_{facing}")
            if strip:
                n_frames = strip.get_width() // 128
                self.anim_frame = (self.anim_frame + 1) % n_frames

        # Spawn dust trail when running
        if abs(self.player.vx) > 0 and self.player.on_ground and not self.player.frozen:
            if random.random() < 0.35:
                px = self.player.x + (self.player.width // 2)
                py = self.player.y + self.player.height
                self.particles.append({
                    "x": px, "y": py,
                    "vx": random.uniform(-20, 20),
                    "vy": random.uniform(-10, -30),
                    "color": random.choice([COLOR_GOLD, COLOR_SAFFRON, COLOR_WHITE]),
                    "size": random.randint(2, 4),
                    "lifetime": random.uniform(0.3, 0.6),
                    "age": 0.0
                })

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
        self.manager.shared["total_time"] = self.manager.shared.get("total_time", 0.0) + time_spent
        self.manager.shared["monk_correct"][self.level] = (
            self.monk.answered_correctly if self.monk.interacted else None
        )
        
        # Distraction boxes opened vs avoided metrics tracking
        opened_count = sum(1 for box in self.box_system.boxes if box.opened)
        total_boxes = len(self.box_system.boxes)
        self.manager.shared["boxes_opened"][self.level] = (opened_count, total_boxes)

        # Score is already computed and stored by the draw code when the
        # level-complete banner was registered (_score_registered flag).
        # Just read it here — do NOT recalculate or we double-count!
        cur_total = self.manager.shared.get("total_score", 0)
        self.manager.shared["final_score"] = cur_total

        # Save score persistently to profile!
        player_name = self.manager.shared.get("player_name", "Pilgrim")
        character = self.manager.shared.get("character", "boy")
        from profile_manager import ProfileManager
        ProfileManager().save_profile(player_name, character=character, score=cur_total, level_reached=self.level)



        next_level = self.level + 1
        tbc = False
        if self.level == 2 and self.game_mode in ("kid", "standard"):
            tbc = True

        if next_level > 4:
            # Check if victory scene is registered, else go to title
            if SCENE_VICTORY in self.manager.scenes:
                self.manager.switch_to(SCENE_VICTORY)
            else:
                from settings import SCENE_LEADERBOARD
                self.manager.switch_to(SCENE_LEADERBOARD)
        else:
            # Check if transition scene is registered
            if SCENE_TRANSITION in self.manager.scenes:
                self.manager.switch_to(SCENE_TRANSITION, next_level=next_level, to_be_continued=tbc)
            else:
                if tbc:
                    from settings import SCENE_LEADERBOARD
                    self.manager.switch_to(SCENE_LEADERBOARD)
                else:
                    self.manager.switch_to(SCENE_LEVEL, level=next_level)


    def draw(self, surface):
        # Create gameplay temporary surface for shifting the visual viewport upwards
        gameplay_surf = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
        gameplay_surf.blit(self.bg, (0, 0))

        # All modes: Initialize gradient texture lazily if it doesn't exist
        if not hasattr(self, "platform_glow_texture") or self.platform_glow_texture is None:
            
            grad_ht = 10
            grad = pygame.Surface((1, grad_ht), pygame.SRCALPHA)
            for y in range(grad_ht):
                dist = grad_ht - y
                # Quadratic fade produces a beautiful soft aura
                alpha = int(180 * (1.0 - (dist / grad_ht) ** 1.5))
                alpha = max(0, min(180, alpha))
                grad.set_at((0, y), (255, 215, 0, alpha))
            self.platform_glow_texture = grad

        # Platforms (Solid Black with High-Contrast White Outline for Developer Calibration)
        for plat in self.platforms:
            # Skip drawing boundary walls/floor/ceiling to remove the ugly "double boundary" boxes
            is_boundary = (
                plat.left == 0 or 
                plat.right == LOGICAL_WIDTH or 
                plat.top == 0 or 
                plat.bottom == LOGICAL_HEIGHT
            )
            if is_boundary:
                continue

            # Skip drawing the solid Bhagwan collision block
            if self.level == 2 and plat.left == 15 and plat.top == 150 and plat.width == 150:
                continue

            # All modes except Kid mode: draw a beautiful golden glow to the upper border of platforms
            if self.game_mode in ("standard", "developer", "kid"):
                # Get the height of the generated texture dynamically
                glow_ht = self.platform_glow_texture.get_height()
                # Scale the 1-pixel-wide gradient to the platform width
                glow_surf = pygame.transform.scale(self.platform_glow_texture, (plat.width, glow_ht))
                # Align the bottom of the glow exactly with the platform's top edge
                gameplay_surf.blit(glow_surf, (plat.left, plat.top - glow_ht))
                # Draw a bright, solid core line at the top edge of the platform
                pygame.draw.line(gameplay_surf, (255, 255, 200, 255), (plat.left, plat.top), (plat.right, plat.top), 2)
                continue

            ps = pygame.Surface((plat.width, plat.height), pygame.SRCALPHA)
            pygame.draw.rect(ps, (0, 0, 0, 255), ps.get_rect(), border_radius=2)
            pygame.draw.rect(ps, (255, 255, 255, 255), ps.get_rect(), width=1, border_radius=2)
            gameplay_surf.blit(ps, plat.topleft)


        # Draw Temple Gate for Level 1
        if self.level == 1 and self.temple_gate_img:
            # ── TEMPLE GATE POSITION CALIBRATION ──
            # To adjust the temple gate manually:
            # - Adjust its dimensions via "scale=(width, height)" in LevelScene.on_enter (line ~185)
            # - Adjust the gate_x and gate_y offsets below:
            gate_w, gate_h = self.temple_gate_img.get_size()
            # Aligns the gate's center to the platform center (platform X: 1740, platform width: 160)
            gate_x = 1740 + (160 - gate_w) // 2
            # Places the bottom of the gate exactly on top of the platform (platform Y: H - 120 = 960)
            gate_y = (LOGICAL_HEIGHT - 50) - gate_h
            
            gameplay_surf.blit(self.temple_gate_img, (gate_x, gate_y))
            
            # Draw a beautiful golden/spiritual glowing aura around the gate if key is found
            if self.box_system.goal_found:
                glow_alpha = int(40 + 20 * math.sin(self.elapsed * 5))
                glow_w = gate_w + 20
                glow_h = gate_h + 20
                glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*COLOR_GOLD[:3], glow_alpha), glow_surf.get_rect(), border_radius=10)
                pygame.draw.rect(glow_surf, (*COLOR_GOLD_BRIGHT[:3], glow_alpha + 30), glow_surf.get_rect(), width=3, border_radius=10)
                gameplay_surf.blit(glow_surf, (gate_x - 10, gate_y - 10))

            # Proximity Prompt for Temple Gate
            gate_rect = pygame.Rect(1740, LOGICAL_HEIGHT - 280, 160, 260)
            if self.player.rect.colliderect(gate_rect):
                if self.box_system.goal_found:
                    prompt_text = "[ Press UP or ACTION to unlock Temple Gate ]"
                    prompt_surf = self.font_hud.render(prompt_text, True, COLOR_GOLD_BRIGHT)
                else:
                    prompt_text = "[ Temple Gate is locked. Find the Temple Key first! ]"
                    prompt_surf = self.font_hud.render(prompt_text, True, COLOR_RED)
                
                # Draw a nice clean prompt background box
                px = gate_rect.centerx - prompt_surf.get_width() // 2
                py = gate_rect.y - 45
                bg_surf = pygame.Surface((prompt_surf.get_width() + 20, prompt_surf.get_height() + 10), pygame.SRCALPHA)
                pygame.draw.rect(bg_surf, (0, 0, 0, 180), bg_surf.get_rect(), border_radius=6)
                gameplay_surf.blit(bg_surf, (px - 10, py - 5))
                gameplay_surf.blit(prompt_surf, (px, py))

        # Hazards
        for hazard in self.hazards:
            hazard.draw(gameplay_surf)

        # Draw running/burst particles
        for p in self.particles:
            alpha = int(255 * (1 - p["age"] / p["lifetime"]))
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"][:3], alpha), (p["size"], p["size"]), p["size"])
            gameplay_surf.blit(ps, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))

        # Boxes
        self.box_system.draw(gameplay_surf, self.font_hud)

        # Monk
        self.monk.draw(gameplay_surf, self.font_body, self.font_small)

        # ── Player Devotee sprite rendering ──
        facing = "right" if self.player.facing_right else "left"
        strip_key = f"{self.anim_state}_{facing}"
        strip = self.player_strips.get(strip_key)

        if strip:
            # Auto-detect frame size: frames are SQUARE with side = strip height.
            # Boy strips: 128px tall → 128×128 frames.
            # Girl strips: 416–720px tall → larger square frames.
            frame_h = strip.get_height()
            frame_w = frame_h  # square frames in all sprite sheets
            n_frames = max(1, strip.get_width() // frame_w)
            frame_idx = min(self.anim_frame, n_frames - 1)
            frame_surf = strip.subsurface((frame_idx * frame_w, 0, frame_w, frame_h))

            # Scale to player display size with squash/stretch applied
            # (visual width is 96, physics width is 32)
            disp_w = int(96 * self.player.scale_x)
            disp_h = int(self.player.height * self.player.scale_y)
            disp_w = max(1, disp_w)
            disp_h = max(1, disp_h)
            scaled = pygame.transform.smoothscale(frame_surf, (disp_w, disp_h))

            # Position: anchor bottom-center of sprite to bottom-center of player rect.
            # foot_pad corrects for the small transparent gap below the feet in the canvas
            # (maintained as a fixed ratio ~9/128 ≈ 7% regardless of source resolution).
            foot_pad = int(disp_h * 9 / 128)
            blit_x = int(self.player.x + (self.player.width  - disp_w) // 2)
            blit_y = int(self.player.y + (self.player.height - disp_h)) + foot_pad
            gameplay_surf.blit(scaled, (blit_x, blit_y))

            # Flashing red overlay when frozen/stunned
            if self.player.frozen and int(self.elapsed * 8) % 2:
                flash = pygame.Surface((disp_w, disp_h), pygame.SRCALPHA)
                flash.fill((255, 80, 80, 90))
                gameplay_surf.blit(flash, (blit_x, blit_y))
        else:
            # Fallback: draw orange rect if sprite is missing
            pygame.draw.rect(gameplay_surf, COLOR_SAFFRON,
                             pygame.Rect(int(self.player.x), int(self.player.y),
                                         self.player.width, self.player.height),
                             border_radius=6)

        # Draw Bhagwan on gameplay_surf if in Level 2 and Akshat is found
        if self.level == 2 and getattr(self.box_system, "akshat_found", False) and self.bhagwan_img:
            bw_size = 150
            bw_scaled = pygame.transform.smoothscale(self.bhagwan_img, (bw_size, bw_size))
            bw_x = 15
            bw_y = 150
            glow_rect = pygame.Rect(bw_x - 4, bw_y - 4, bw_size + 8, bw_size + 8)
            pulse = int(180 + 60 * math.sin(self.elapsed * 3))
            pygame.draw.rect(gameplay_surf, (255, 215, 0, pulse), glow_rect, width=3, border_radius=10)
            gameplay_surf.blit(bw_scaled, (bw_x, bw_y))
            offer_txt = self.font_small.render("Offer Akshat here!", True, COLOR_GOLD_BRIGHT)
            gameplay_surf.blit(offer_txt, offer_txt.get_rect(center=(bw_x + bw_size // 2, bw_y + bw_size + 12)))

        # ── Blit the gameplay surface shifted UPWARDS by 80 pixels onto logical surface ──
        # This makes the bottom Y space clear of gameplay and creates the solid controls zone
        surface.blit(gameplay_surf, (0, -80))

        # Fill the bottom 80 pixels with a solid dark premium background bar for controls
        pygame.draw.rect(surface, (15, 12, 22), (0, LOGICAL_HEIGHT - 80, LOGICAL_WIDTH, 80))
        pygame.draw.line(surface, COLOR_GOLD_DIM, (0, LOGICAL_HEIGHT - 80), (LOGICAL_WIDTH, LOGICAL_HEIGHT - 80), 2)

        # ── Level Goal Text (loaded from level_goals.json, editable) ──
        if not (self.box_system.message_timer > 0 and self.box_system.message):
            lvl_goals = self.level_goals.get(str(self.level), {})
            if self.level == 1 and self.box_system.goal_found:
                goal_text = lvl_goals.get("key_found", "Goal: Unlock and enter the Temple Gate!")
            elif self.level == 2 and getattr(self.box_system, "akshat_found", False):
                goal_text = lvl_goals.get("akshat_found", "Goal: Fly to the Bhagwan and offer Akshat!")
            else:
                goal_text = lvl_goals.get("default", "Goal: Find the sacred item!")
            goal_surf = self.font_body.render(goal_text, True, COLOR_GOLD_BRIGHT)
            goal_rect = goal_surf.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40))
            surface.blit(goal_surf, goal_rect)



        # ── Shelf of Unlocked Box Items (Drawn starting at x=240, spaced 50px apart) ──
        start_x = 240
        y_pos = LOGICAL_HEIGHT - 60
        box_size = 40
        
        opened_boxes = [b for b in self.box_system.boxes if b.opened]
        for idx, b in enumerate(opened_boxes):
            x_pos = start_x + idx * 50
            
            # Determine color backgrounds matching categories
            cat = b.item["cat"]
            if cat == CAT_GOAL:
                bg_color = (120, 95, 30)       # Gold background
                border_color = COLOR_GOLD_BRIGHT
            elif cat == CAT_SUPPORT:
                bg_color = (25, 75, 40)        # Green background
                border_color = COLOR_GREEN
            elif cat == CAT_DISTRACTION:
                bg_color = (85, 25, 25)        # Red background
                border_color = COLOR_RED
            else:  # CAT_NO_EFFECT
                bg_color = (40, 40, 45)        # Grey background
                border_color = (140, 140, 140)
                
            # Draw box background
            item_rect = pygame.Rect(x_pos, y_pos, box_size, box_size)
            pygame.draw.rect(surface, bg_color, item_rect, border_radius=6)
            pygame.draw.rect(surface, border_color, item_rect, width=2, border_radius=6)
            
            # Load item icon dynamically
            img_name = get_item_image_name(b.item["name"])
            img = self.assets.load_image(img_name, "items", alpha=True, scale=(box_size - 8, box_size - 8))
            
            # Check if file exists to decide whether to draw the image or fallback letters
            img_path = os.path.join(IMAGES_DIR, "items", img_name)
            if not os.path.exists(img_path):
                # Fallback to drawing a stylized letter abbreviation inside the colored box
                letter = b.item["name"][0].upper()
                if "Wrong" in b.item["name"]:
                    letter = "X"
                letter_surf = self.font_small.render(letter, True, border_color)
                letter_rect = letter_surf.get_rect(center=item_rect.center)
                surface.blit(letter_surf, letter_rect)
            else:
                # Blit loaded image
                img_rect = img.get_rect(center=item_rect.center)
                surface.blit(img, img_rect)

        # Draw a single, premium spiritual golden frame around the active playing field boundary (Y: 0 to 1000)
        # This replaces the double boundaries and matches the warm gold/saffron theme.
        border_thickness = 4
        # Left border
        pygame.draw.rect(surface, COLOR_GOLD_DIM, (0, 0, border_thickness, LOGICAL_HEIGHT - 80))
        # Right border
        pygame.draw.rect(surface, COLOR_GOLD_DIM, (LOGICAL_WIDTH - border_thickness, 0, border_thickness, LOGICAL_HEIGHT - 80))
        # Top border (just below the HUD gradient, or at the very top)
        pygame.draw.rect(surface, COLOR_GOLD_DIM, (0, 0, LOGICAL_WIDTH, border_thickness))

        # ── Premium HUD Header Bar (drawn on top surface directly) ──
        hud_bar = pygame.Surface((LOGICAL_WIDTH, 48), pygame.SRCALPHA)
        # Gradient background
        for i in range(48):
            alpha = int(210 * (1 - i / 48 * 0.4))
            pygame.draw.line(hud_bar, (20, 14, 30, alpha), (0, i), (LOGICAL_WIDTH, i))
        pygame.draw.line(hud_bar, COLOR_GOLD_DIM, (0, 47), (LOGICAL_WIDTH, 47), 1)
        surface.blit(hud_bar, (0, 0))

        # Level name
        name = f"Level {self.level}: {LEVEL_NAMES.get(self.level, '???')}"
        name_surf = self.font_hud.render(name, True, COLOR_GOLD_BRIGHT)
        surface.blit(name_surf, (15, 12))
        sub = f"({LEVEL_SUBTITLES.get(self.level, '')})"
        sub_surf = self.font_hud.render(sub, True, COLOR_SAFFRON)
        surface.blit(sub_surf, (15 + name_surf.get_width() + 10, 12))

        # Timer countdown with pulse when low
        mins = int(max(0, self.time_remaining)) // 60
        secs = int(max(0, self.time_remaining)) % 60
        t_color = COLOR_RED if self.time_remaining < 20 else COLOR_GREEN
        low_time = self.time_remaining < 20
        scale = 1.0 + 0.12 * math.sin(self.elapsed * 6.5) if low_time else 1.0
        timer_text = f"Time: {mins:02d}:{secs:02d}"

        if low_time:
            timer_surf = self.font_hud.render(timer_text, True, t_color)
            if scale != 1.0:
                w = int(timer_surf.get_width() * scale)
                h = int(timer_surf.get_height() * scale)
                timer_surf = pygame.transform.smoothscale(timer_surf, (w, h))
            surface.blit(timer_surf, (LOGICAL_WIDTH - timer_surf.get_width() - 15, 12 - (timer_surf.get_height() - 24) // 2))
        else:
            timer_surf = self.font_hud.render(timer_text, True, t_color)
            surface.blit(timer_surf, (LOGICAL_WIDTH - timer_surf.get_width() - 15, 12))

        # Freeze indicator
        if self.player.frozen:
            fz = self.font_body.render(f"STUNNED! {self.player.freeze_timer:.1f}s", True, COLOR_RED)
            surface.blit(fz, fz.get_rect(center=(LOGICAL_WIDTH // 2, 120)))

        # Box messages
        self.box_system.draw_message(surface, self.font_body)

        # Level complete banner
        if self.level_complete:
            overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            surface.blit(overlay, (0, 0))
            complete = self.font_title.render("LEVEL PILGRIMAGE COMPLETE!", True, COLOR_GOLD_BRIGHT)
            surface.blit(complete, complete.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 80)))

            # ── Register score once: simple formula = time_remaining * 10 ──
            if not self._score_registered:
                self._score_registered = True
                lvl_score = int(max(0, self.time_remaining)) * 10
                self.manager.shared["level_scores"][self.level] = lvl_score
                if self.level == 1:
                    self.manager.shared["total_score"] = lvl_score
                else:
                    self.manager.shared["total_score"] = self.manager.shared.get("total_score", 0) + lvl_score

            # ── Score summary band ──
            band_h = 110
            band_y = LOGICAL_HEIGHT // 2 - 10
            band = pygame.Surface((LOGICAL_WIDTH, band_h), pygame.SRCALPHA)
            pygame.draw.rect(band, (20, 12, 0, 210), band.get_rect(), border_radius=0)
            pygame.draw.line(band, COLOR_GOLD_DIM, (0, 0), (LOGICAL_WIDTH, 0), 2)
            pygame.draw.line(band, COLOR_GOLD_DIM, (0, band_h - 1), (LOGICAL_WIDTH, band_h - 1), 2)
            surface.blit(band, (0, band_y))

            t_left    = max(0, self.time_remaining)
            lvl_score = self.manager.shared["level_scores"].get(self.level, 0)
            total_score = self.manager.shared["total_score"]

            # Level score (current) and total score
            sc_label = self.font_body.render(f"★ Level Score: {lvl_score}  |  Total Score: {total_score}", True, COLOR_GOLD_BRIGHT)
            surface.blit(sc_label, sc_label.get_rect(center=(LOGICAL_WIDTH // 2, band_y - 28)))


            time_col = COLOR_GREEN if t_left > 60 else (COLOR_GOLD if t_left > 20 else COLOR_RED)
            t_label = self.font_body.render(f"⏱ Time Left: {int(t_left)}s", True, time_col)

            monk_answered = getattr(self.monk, "interacted", False) if self.monk else False
            monk_correct  = getattr(self.monk, "answered_correctly", False) if self.monk else False
            if monk_answered:
                monk_text = "✔ Sage Answered" if monk_correct else "✘ Sage Missed"
                monk_col  = COLOR_GREEN if monk_correct else COLOR_RED
            else:
                monk_text, monk_col = "— Sage Not Visited", COLOR_GOLD_DIM
            m_label = self.font_body.render(monk_text, True, monk_col)

            opened = sum(1 for b in self.box_system.boxes if b.opened)
            total  = len(self.box_system.boxes)
            b_label = self.font_body.render(f"◈ Boxes: {opened}/{total}", True, COLOR_GOLD_BRIGHT)

            col_w = LOGICAL_WIDTH // 3
            cy = band_y + band_h // 2
            surface.blit(t_label, t_label.get_rect(center=(col_w // 2, cy)))
            surface.blit(m_label, m_label.get_rect(center=(col_w + col_w // 2, cy)))
            surface.blit(b_label, b_label.get_rect(center=(2 * col_w + col_w // 2, cy)))

            # ── Normal continue button ──
            cont_surf = self.font_title.render("▶  CONTINUE", True, COLOR_GOLD_BRIGHT)
            cont_r = cont_surf.get_rect(center=(LOGICAL_WIDTH // 2, band_y + band_h + 70))
            btn_bg = pygame.Surface((cont_r.width + 60, cont_r.height + 24), pygame.SRCALPHA)
            btn_alpha = 150 + int(60 * math.sin(self.elapsed * 4))
            pygame.draw.rect(btn_bg, (30, 20, 0, btn_alpha), btn_bg.get_rect(), border_radius=14)
            pygame.draw.rect(btn_bg, COLOR_GOLD_BRIGHT, btn_bg.get_rect(), width=3, border_radius=14)
            surface.blit(btn_bg, (cont_r.x - 30, cont_r.y - 12))
            surface.blit(cont_surf, cont_r)
            hint_c = self.font_small.render("Press ENTER / SPACE / click anywhere to continue", True, COLOR_GOLD_DIM)
            surface.blit(hint_c, hint_c.get_rect(center=(LOGICAL_WIDTH // 2, cont_r.bottom + 24)))


        # ── Game Over overlay ── (renders on top of a darkened frozen frame)
        if self.game_over:
            # Solid dark panel covers the full screen — no live game behind it
            go_overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            go_overlay.fill((10, 6, 18))
            surface.blit(go_overlay, (0, 0))
            # Decorative golden border
            pygame.draw.rect(surface, COLOR_GOLD_DIM, (30, 30, LOGICAL_WIDTH - 60, LOGICAL_HEIGHT - 60), width=2, border_radius=16)

            # Title
            go_title = self.font_title.render("TIME'S UP!", True, COLOR_RED)
            surface.blit(go_title, go_title.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 200)))

            sub = self.font_body.render("The path to Moksha requires more practice...", True, COLOR_CREAM)
            surface.blit(sub, sub.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 140)))

            # ── Score summary band (always shown) ──
            band_h = 110
            band_y = LOGICAL_HEIGHT // 2 - 70
            band = pygame.Surface((LOGICAL_WIDTH - 80, band_h), pygame.SRCALPHA)
            pygame.draw.rect(band, (20, 12, 0, 210), band.get_rect(), border_radius=12)
            pygame.draw.rect(band, COLOR_GOLD_DIM, band.get_rect(), width=2, border_radius=12)
            surface.blit(band, (40, band_y))

            t_left = max(0, self.time_remaining)

            # Register level score once (time_remaining * 10)
            if not self._score_registered:
                self._score_registered = True
                _lvl_sc = int(t_left * 10)
                self.manager.shared["level_scores"][self.level] = _lvl_sc
                self.manager.shared["total_score"] = sum(self.manager.shared["level_scores"].values())

            lvl_score   = self.manager.shared["level_scores"].get(self.level, int(t_left * 10))
            total_score = self.manager.shared["total_score"]

            # Score headline above band
            score_surf = self.font_title.render(f"Level: {lvl_score}  |  Total: {total_score}", True, COLOR_GOLD_BRIGHT)
            surface.blit(score_surf, score_surf.get_rect(center=(LOGICAL_WIDTH // 2, band_y - 40)))

            t_label = self.font_body.render(f"⏱ Time Left: {int(t_left)}s", True, COLOR_RED)
            monk_answered = getattr(self.monk, "interacted", False) if self.monk else False
            monk_correct  = getattr(self.monk, "answered_correctly", False) if self.monk else False
            monk_text = ("✔ Sage Answered" if monk_correct else "✘ Sage Missed") if monk_answered else "— Sage Not Visited"
            monk_col  = COLOR_GREEN if monk_correct else (COLOR_RED if monk_answered else COLOR_GOLD_DIM)
            m_label = self.font_body.render(monk_text, True, monk_col)
            opened = sum(1 for b in self.box_system.boxes if b.opened)
            total  = len(self.box_system.boxes)
            b_label = self.font_body.render(f"◈ Boxes: {opened}/{total}", True, COLOR_GOLD_BRIGHT)

            col_w = (LOGICAL_WIDTH - 80) // 3
            cy = band_y + band_h // 2
            surface.blit(t_label, t_label.get_rect(center=(40 + col_w // 2, cy)))
            surface.blit(m_label, m_label.get_rect(center=(40 + col_w + col_w // 2, cy)))
            surface.blit(b_label, b_label.get_rect(center=(40 + 2 * col_w + col_w // 2, cy)))

            if not self.game_over_score_shown:
                # Phase 1: prompt player to continue to button selection
                pulse_a = 150 + int(80 * math.sin(self.elapsed * 4))
                hint_col = (255, 215, 0, pulse_a)
                hint_surf = self.font_body.render("Press SPACE or click to continue...", True, (255, 215, 0))
                surface.blit(hint_surf, hint_surf.get_rect(center=(LOGICAL_WIDTH // 2, band_y + band_h + 60)))
            else:
                # Phase 2: show Restart / Back to Start buttons
                btn_labels = ["↩  Restart Level", "⌂  Back to Start"]
                btn_y = band_y + band_h + 30
                btn_gap = 340
                for i, label in enumerate(btn_labels):
                    cx = int(LOGICAL_WIDTH // 2 - btn_gap // 2 + i * btn_gap)
                    selected = (self.game_over_choice == i)
                    bg_col = (180, 120, 0, 220) if selected else (40, 40, 40, 180)
                    btn_surf = pygame.Surface((300, 70), pygame.SRCALPHA)
                    pygame.draw.rect(btn_surf, bg_col, btn_surf.get_rect(), border_radius=14)
                    if selected:
                        pygame.draw.rect(btn_surf, COLOR_GOLD_BRIGHT, btn_surf.get_rect(), width=3, border_radius=14)
                    t_col = COLOR_GOLD_BRIGHT if selected else COLOR_CREAM
                    t_surf = self.font_body.render(label, True, t_col)
                    btn_surf.blit(t_surf, t_surf.get_rect(center=(150, 35)))
                    surface.blit(btn_surf, (cx - 150, btn_y))

                hint = self.font_small.render("◄ ► Arrow keys to choose   •   SPACE to confirm   •   or click a button", True, COLOR_GOLD_DIM)
                surface.blit(hint, hint.get_rect(center=(LOGICAL_WIDTH // 2, btn_y + 90)))

        # Touch controls (drawn centered inside the bottom black border zone)
        self.input_mgr.draw_touch_controls(surface, self.font_hud)

        # Monk dialogue overlay (drawn last, on top)
        if self.monk:
            self.monk.draw_dialogue(surface, self.font_title, self.font_body, self.font_small, self.acharya_img)

        # ── Item Pop-up Overlay (drawn on top of dialogue/gameplay) ──
        if self.item_popup is not None:
            popup = self.item_popup
            item = popup["item"]
            msg = popup["message"]
            timer = popup["timer"]
            cat = item["cat"]
            
            # Category colors
            border_color = CAT_COLORS.get(cat, COLOR_WHITE)
            
            # Dark transparent overlay over the entire screen
            overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 6, 18, 195))
            surface.blit(overlay, (0, 0))
            
            # Modal panel (centered)
            panel_w, panel_h = 760, 540
            px = (LOGICAL_WIDTH - panel_w) // 2
            py = (LOGICAL_HEIGHT - panel_h) // 2 - 20
            
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            # Semi-transparent dark background for the box
            pygame.draw.rect(panel, (24, 16, 32, 245), panel.get_rect(), border_radius=20)
            # Double border
            pygame.draw.rect(panel, border_color, panel.get_rect(), width=4, border_radius=20)
            pygame.draw.rect(panel, (255, 255, 255, 20), panel.get_rect().inflate(-10, -10), width=1, border_radius=16)
            
            # Title header background
            header_h = 56
            pygame.draw.rect(panel, (*border_color[:3], 45), (4, 4, panel_w - 8, header_h), border_top_left_radius=16, border_top_right_radius=16)
            pygame.draw.line(panel, border_color, (4, header_h + 4), (panel_w - 4, header_h + 4), 2)
            
            # Category title
            cat_names = {
                CAT_GOAL: "★ SACRED GOAL ITEM FOUND ★",
                CAT_SUPPORT: "✔ SUPPORT ITEM FOUND ✔",
                CAT_DISTRACTION: "⚠ DISTRACTION ENCOUNTERED ⚠",
                CAT_NO_EFFECT: "◈ NEUTRAL ITEM ◈"
            }
            cat_name = cat_names.get(cat, "ITEM FOUND")
            title_surf = self.font_title.render(cat_name, True, border_color)
            panel.blit(title_surf, title_surf.get_rect(center=(panel_w // 2, header_h // 2 + 4)))

            # Large Item Image Icon (Framed inside a 220x220 box - 3-4x larger)
            icon_box = pygame.Rect(panel_w // 2 - 110, 72, 220, 220)
            pygame.draw.rect(panel, (15, 10, 25), icon_box, border_radius=16)
            pygame.draw.rect(panel, border_color, icon_box, width=3, border_radius=16)

            img_name = get_item_image_name(item["name"])
            img = self.assets.load_image(img_name, "items", alpha=True, scale=(200, 200))
            img_path = os.path.join(IMAGES_DIR, "items", img_name)
            if os.path.exists(img_path):
                img_rect = img.get_rect(center=icon_box.center)
                panel.blit(img, img_rect)
            else:
                letter = item["name"][0].upper()
                if "Wrong" in item["name"]:
                    letter = "X"
                letter_surf = self.font_title.render(letter, True, border_color)
                letter_rect = letter_surf.get_rect(center=icon_box.center)
                panel.blit(letter_surf, letter_rect)

            # Item Name
            name_surf = self.font_title.render(item["name"], True, COLOR_WHITE)
            panel.blit(name_surf, name_surf.get_rect(center=(panel_w // 2, 318)))
            
            # Description
            desc_surf = self.font_body.render(msg, True, COLOR_CREAM)
            panel.blit(desc_surf, desc_surf.get_rect(center=(panel_w // 2, 378)))
            
            # Dismiss hint
            hint_surf = self.font_small.render("Press SPACE / Click / Press any key to close", True, COLOR_GOLD_DIM)
            panel.blit(hint_surf, hint_surf.get_rect(center=(panel_w // 2, 438)))
            
            # Progress/timer bar showing countdown
            bar_max_w = panel_w - 80
            bar_w = int(bar_max_w * (timer / 5.0))
            if bar_w > 0:
                pygame.draw.rect(panel, (40, 30, 50), (40, 490, bar_max_w, 10), border_radius=5)
                pygame.draw.rect(panel, border_color, (40, 490, bar_w, 10), border_radius=5)
                
            surface.blit(panel, (px, py))

        # Fade-in
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
