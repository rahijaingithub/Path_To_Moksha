"""
level_scene.py — Core platformer gameplay scene with Box Roulette and Monk systems.
"""
import pygame
import math
import random
from scene_manager import Scene
from box_system import BoxSystem, CAT_GOAL
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
)


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
            self.on_ground = False
            pr = self.rect
            for plat in platforms:
                if pr.colliderect(plat):
                    if self.vy > 0:
                        self.y = plat.top - self.height
                        self.vy = 0
                        self.on_ground = True
                        if not self.was_on_ground:
                            self.scale_y = 0.65
                            self.scale_x = 1.35
                    elif self.vy < 0:
                        self.y = plat.bottom
                        self.vy = 0
            self.was_on_ground = self.on_ground
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
                    if not self.was_on_ground:
                        # Landing squash
                        self.scale_y = 0.65
                        self.scale_x = 1.35
                elif self.vy < 0:
                    self.y = plat.bottom
                    self.vy = 0

        # Keep in bounds
        if self.x < 0:
            self.x = 0
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
        self.particles = []

    def on_enter(self, **kwargs):
        self.level = kwargs.get("level", 1)
        self.manager.shared["current_level"] = self.level
        self.time_remaining = float(LEVEL_TIME_LIMIT.get(self.level, 120))
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.level_complete = False
        self.complete_timer = 0.0
        self.particles = []

        # Fonts (Using larger gameplay sizes for modern visual AAA quality)
        self.font_hud = self.assets.load_font(None, GAME_FONT_SIZE_HUD)
        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

        # Background
        bg_name = f"level{self.level}_background.png"
        self.bg = self.assets.load_image(bg_name, "backgrounds", alpha=False,
                                         scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT))

        # Reset or initialize game stats and unique question tracker on starting Level 1
        if self.level == 1:
            self.manager.shared["total_time"] = 0.0
            self.manager.shared["level_times"] = {}
            self.manager.shared["monk_correct"] = {}
            self.manager.shared["boxes_opened"] = {}
            self.manager.shared["asked_questions"] = []
        elif "asked_questions" not in self.manager.shared:
            self.manager.shared["asked_questions"] = []

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
        self.monk = create_monk(self.level, self.platforms, self.hazards, self.manager.shared["asked_questions"])
        
        # 3. Build box system third (passing hazards and monk so boxes don't overlap with them)
        self.box_system = BoxSystem(self.level, self.platforms, self.hazards, self.monk)

        # Audio
        self.assets.play_music("bgm_loop.wav", volume=0.4)

    def handle_events(self, events, input_mgr):
        # Developer Coordinate Finder
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = input_mgr.mouse_x, input_mgr.mouse_y
                # Shift visual Y click coordinate back to background space (offset by +80)
                actual_my = my + 80
                print(f"p.append(pygame.Rect({mx}, H - {LOGICAL_HEIGHT - actual_my}, 200, PH))  # Clicked: x={mx}, y={actual_my} (relative to bottom: H - {LOGICAL_HEIGHT - actual_my})")

        if input_mgr.just_pressed[input_mgr.BACK]:
            if self.monk and self.monk.dialogue_active:
                self.monk.dialogue_active = False
            else:
                self.manager.switch_to(SCENE_TITLE)
            return

        # Proximity interaction with the Temple Gate for Level 1
        if self.level == 1:
            gate_rect = pygame.Rect(1740, LOGICAL_HEIGHT - 280, 160, 160)
            if self.player.rect.colliderect(gate_rect):
                if self.box_system.goal_found:
                    # Player is at the gate with the key!
                    if input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.UP]:
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

            # Keyboard navigation
            if input_mgr.just_pressed[input_mgr.UP]:
                self.monk.selected_choice = 0
                self.assets.play_sound("jump.wav", volume=0.08)
            elif input_mgr.just_pressed[input_mgr.JUMP]:
                # DOWN maps to selecting choice 1
                self.monk.selected_choice = 1
                self.assets.play_sound("jump.wav", volume=0.08)

            # Mouse click submission
            clicked = False
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if opt0_rect.collidepoint(mx, my) or opt1_rect.collidepoint(mx, my):
                        clicked = True

            if input_mgr.just_pressed[input_mgr.ACTION] or clicked:
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

                if freeze_dur > 0:
                    self.player.freeze(freeze_dur)
                    self.assets.play_sound("wrong.wav")

                if item["cat"] == CAT_GOAL:
                    if self.level == 1:
                        # For Level 1, we just found the key! Chime sound, but do not complete level immediately
                        self.assets.play_sound("correct.wav")
                    else:
                        # Other levels complete immediately as before
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

        # If monk dialogue is active, update the monk (to advance typewriter question text) and return early
        if self.monk and self.monk.dialogue_active:
            self.monk.update(dt, self.elapsed, self.player.rect)
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
            target_vx = 0
            if inp.actions[inp.LEFT]:
                target_vx = -PLAYER_SPEED
                self.player.facing_right = False
            elif inp.actions[inp.RIGHT]:
                target_vx = PLAYER_SPEED
                self.player.facing_right = True

            # Smooth acceleration (lerp)
            self.player.vx += (target_vx - self.player.vx) * 15 * dt

            if inp.just_pressed[inp.JUMP] and self.player.on_ground:
                self.player.vy = LEVEL_JUMP_FORCES.get(self.level, PLAYER_JUMP_FORCE)
                self.assets.play_sound("jump.wav")
                # Squash/stretch jump effect
                self.player.scale_y = 1.35
                self.player.scale_x = 0.7
                # Jump Dust Particles
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

        was_on_ground = self.player.on_ground
        self.player.update(dt, self.platforms)
        
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
        self.manager.shared["total_time"] += time_spent
        self.manager.shared["monk_correct"][self.level] = (
            self.monk.answered_correctly if self.monk.interacted else None
        )
        
        # Distraction boxesopened vs avoided metrics tracking
        opened_count = sum(1 for box in self.box_system.boxes if box.opened)
        total_boxes = len(self.box_system.boxes)
        self.manager.shared["boxes_opened"][self.level] = (opened_count, total_boxes)

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
        # Create gameplay temporary surface for shifting the visual viewport upwards
        gameplay_surf = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
        gameplay_surf.blit(self.bg, (0, 0))

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
                glow_surf = pygame.Surface((140, 180), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*COLOR_GOLD[:3], glow_alpha), glow_surf.get_rect(), border_radius=10)
                pygame.draw.rect(glow_surf, (*COLOR_GOLD_BRIGHT[:3], glow_alpha + 30), glow_surf.get_rect(), width=3, border_radius=10)
                gameplay_surf.blit(glow_surf, (gate_x - 10, gate_y - 10))

            # Proximity Prompt for Temple Gate
            gate_rect = pygame.Rect(1740, LOGICAL_HEIGHT - 280, 160, 160)
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

        # ── Player Devotee sprite rendering with squash & stretch ──
        char_type = self.manager.shared.get("character", "boy")
        
        # Calculate squashed/stretched rect anchored at bottom center of original rect
        w = int(self.player.width * self.player.scale_x)
        h = int(self.player.height * self.player.scale_y)
        px = int(self.player.x + (self.player.width - w) // 2)
        py = int(self.player.y + (self.player.height - h))
        draw_rect = pygame.Rect(px, py, w, h)

        # Draw flowing dupatta/scarf (trail)
        if len(self.player.trail) > 1:
            points = []
            for idx, pt in enumerate(self.player.trail):
                # Offset trail slightly upwards towards neck level
                tx = pt[0] - (10 if self.player.facing_right else -10)
                ty = pt[1] - 8
                # Add slight wave
                ty += math.sin(self.elapsed * 10 + idx) * 3
                points.append((tx, ty))
            
            # Draw beautiful flowing saffron dupatta trail
            if len(points) >= 3:
                # Dupatta gets thinner towards the end
                for idx in range(len(points) - 1):
                    thick = int(4 * (idx / len(points))) + 2
                    col = COLOR_SAFFRON
                    pygame.draw.line(gameplay_surf, col, points[idx], points[idx+1], thick)

        # Draw devotee body outline
        body_color = COLOR_SAFFRON if char_type == "boy" else COLOR_WHITE
        border_color = COLOR_GOLD if char_type == "boy" else COLOR_SAFFRON
        
        # Draw robe/body
        pygame.draw.rect(gameplay_surf, body_color, draw_rect, border_radius=int(8 * self.player.scale_x))
        pygame.draw.rect(gameplay_surf, border_color, draw_rect, width=2, border_radius=int(8 * self.player.scale_x))

        # Face/Head
        head_r = int(12 * self.player.scale_x)
        head_cx = draw_rect.x + w // 2
        head_cy = draw_rect.y + int(14 * self.player.scale_y)
        pygame.draw.circle(gameplay_surf, (230, 190, 160), (head_cx, head_cy), head_r)
        
        # Hair/Crown
        pygame.draw.circle(gameplay_surf, (40, 30, 40), (head_cx, head_cy - head_r + 2), int(head_r * 0.9))

        # Flashing red overlay if frozen/stunned
        if self.player.frozen:
            if int(self.elapsed * 8) % 2:
                pygame.draw.rect(gameplay_surf, (255, 80, 80, 120), draw_rect, border_radius=int(8 * self.player.scale_x))
                pygame.draw.circle(gameplay_surf, (255, 80, 80, 120), (head_cx, head_cy), head_r)

        # Eyes facing direction
        eye_r = int(3 * self.player.scale_x)
        pupil_r = int(1.2 * self.player.scale_x)
        eye_y = head_cy - int(2 * self.player.scale_y)
        if self.player.facing_right:
            ex = head_cx + int(4 * self.player.scale_x)
            pygame.draw.circle(gameplay_surf, COLOR_WHITE, (ex, eye_y), eye_r)
            pygame.draw.circle(gameplay_surf, (0, 0, 0), (ex + 1, eye_y), pupil_r)
        else:
            ex = head_cx - int(4 * self.player.scale_x)
            pygame.draw.circle(gameplay_surf, COLOR_WHITE, (ex, eye_y), eye_r)
            pygame.draw.circle(gameplay_surf, (0, 0, 0), (ex - 1, eye_y), pupil_r)

        # ── Blit the gameplay surface shifted UPWARDS by 80 pixels onto logical surface ──
        # This makes the bottom Y space clear of gameplay and creates the solid controls zone
        surface.blit(gameplay_surf, (0, -80))

        # Fill the bottom 80 pixels with a solid dark premium background bar for controls
        pygame.draw.rect(surface, (15, 12, 22), (0, LOGICAL_HEIGHT - 80, LOGICAL_WIDTH, 80))
        pygame.draw.line(surface, COLOR_GOLD_DIM, (0, LOGICAL_HEIGHT - 80), (LOGICAL_WIDTH, LOGICAL_HEIGHT - 80), 2)

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
            surface.blit(complete, complete.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2)))

        # Touch controls (drawn centered inside the bottom black border zone)
        self.input_mgr.draw_touch_controls(surface, self.font_hud)

        # Monk dialogue overlay (drawn last, on top)
        if self.monk:
            self.monk.draw_dialogue(surface, self.font_title, self.font_body, self.font_small, self.acharya_img)

        # Fade-in
        if self.fade_alpha > 0:
            fade = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade.fill(COLOR_BG_DARK)
            fade.set_alpha(int(self.fade_alpha))
            surface.blit(fade, (0, 0))
