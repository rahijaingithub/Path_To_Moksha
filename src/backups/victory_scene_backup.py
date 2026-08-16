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
    """Calculates score and displays final victory screen with stats."""

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

        # Interactive restart button
        self.restart_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 220, 870, 440, 56)
        self.hover_restart = False
        self.particles = []
        self.particle_timer = 0.0

    def on_enter(self, **kwargs):
        self.elapsed = 0.0
        self.particles = []
        self.particle_timer = 0.0
        self.hover_restart = False

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

        # Play peaceful victory music/drone loop
        self.assets.play_music("bgm_loop.wav", volume=0.25)

    def handle_events(self, events, input_mgr):
        if self.elapsed > 1.5:
            if (input_mgr.just_pressed[input_mgr.ACTION] or
                    input_mgr.just_pressed[input_mgr.JUMP] or
                    input_mgr.just_pressed[input_mgr.BACK]):
                self.assets.play_sound("level_complete.wav", volume=0.35)
                self.manager.switch_to(SCENE_TITLE)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = input_mgr.mouse_x, input_mgr.mouse_y
                    if self.restart_rect.collidepoint(mx, my):
                        self.assets.play_sound("level_complete.wav", volume=0.35)
                        self.manager.switch_to(SCENE_TITLE)

    def update(self, dt):
        self.elapsed += dt
        self.particle_timer += dt

        # Spawn falling lotus petals
        if self.particle_timer > 0.18 and len(self.particles) < 35:
            self.particle_timer = 0.0
            import random
            self.particles.append({
                "x": random.randint(-50, LOGICAL_WIDTH + 50),
                "y": -20,
                "speed_y": random.uniform(35, 75),
                "speed_x": random.uniform(-20, 20),
                "size": random.randint(4, 9),
                "sway_speed": random.uniform(1.8, 3.5),
                "sway_offset": random.uniform(0.0, 15.0),
                "lifetime": random.uniform(7.5, 11.5),
                "age": 0.0
            })

        # Update lotus particles
        for p in self.particles:
            p["age"] += dt
            p["y"] += p["speed_y"] * dt
            p["x"] += p["speed_x"] * dt + math.sin(self.elapsed * p["sway_speed"] + p["sway_offset"]) * 0.5
        self.particles = [p for p in self.particles if p["age"] < p["lifetime"] and p["y"] < LOGICAL_HEIGHT + 20]

        # Check button hover and play sfx on enter
        mx, my = self.input_mgr.mouse_x, self.input_mgr.mouse_y
        new_hover = self.restart_rect.collidepoint(mx, my)
        if new_hover and not self.hover_restart:
            self.assets.play_sound("jump.wav", volume=0.12)
        self.hover_restart = new_hover

    def draw(self, surface):
        surface.fill(COLOR_BG_DARK)

        # Pulsing divine golden aura behind temple
        glow_r = 280 + int(30 * math.sin(self.elapsed * 1.5))
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 60, 36), (glow_r, glow_r), glow_r)
        surface.blit(glow, (LOGICAL_WIDTH // 2 - glow_r, 110))

        # Main Garbhalaya Temple Image
        if self.bg_image:
            # Subtle breathing zoom on temple
            zoom = 1.0 + 0.02 * math.sin(self.elapsed * 0.3)
            w = int(500 * zoom)
            h = int(500 * zoom)
            zoomed_img = pygame.transform.smoothscale(self.bg_image, (w, h))
            img_rect = zoomed_img.get_rect(center=(LOGICAL_WIDTH // 2, 380))
            
            # Gold frame around temple
            frame_rect = img_rect.inflate(12, 12)
            pygame.draw.rect(surface, COLOR_GOLD, frame_rect, width=3, border_radius=8)
            surface.blit(zoomed_img, img_rect)

        # Draw falling lotus petals
        for p in self.particles:
            alpha = int(220 * (1 - p["age"] / p["lifetime"]))
            sz = p["size"]
            ps = pygame.Surface((sz * 3, sz * 4), pygame.SRCALPHA)
            # Beautiful lotus petal pink ellipse
            pygame.draw.ellipse(ps, (255, 175, 200, alpha), pygame.Rect(sz // 2, 0, sz * 1.5, sz * 3.5))
            # Gold rim highlight
            pygame.draw.ellipse(ps, (255, 215, 0, alpha), pygame.Rect(sz // 2, 0, sz * 1.5, sz * 3.5), width=1)
            surface.blit(ps, (int(p["x"]) - sz, int(p["y"]) - sz))

        # ── Pilgrim Rank Banner ──
        rank_text = f"PILGRIM RANK: {self.rank_title.upper()}"
        rank_surf = self.font_sub.render(rank_text, True, COLOR_GOLD_BRIGHT)
        rr = rank_surf.get_rect(center=(LOGICAL_WIDTH // 2, 60))
        
        # Banner background plate
        plate = pygame.Surface((rr.width + 48, rr.height + 16), pygame.SRCALPHA)
        pygame.draw.rect(plate, (20, 12, 32, 220), plate.get_rect(), border_radius=12)
        pygame.draw.rect(plate, COLOR_SAFFRON, plate.get_rect(), width=2, border_radius=12)
        surface.blit(plate, (rr.x - 24, rr.y - 8))
        surface.blit(rank_surf, rr)

        # ── Scorecard Stats Panel ──
        panel_w, panel_h = 740, 180
        panel_x = (LOGICAL_WIDTH - panel_w) // 2
        panel_y = 665
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (28, 20, 48, 220), panel_surf.get_rect(), border_radius=20)
        pygame.draw.rect(panel_surf, COLOR_GOLD, panel_surf.get_rect(), width=2, border_radius=20)
        surface.blit(panel_surf, (panel_x, panel_y))

        # Scorecard title
        p_title = self.font_body.render("--- SACRED ARCADE STATS ---", True, COLOR_GOLD_BRIGHT)
        surface.blit(p_title, p_title.get_rect(center=(LOGICAL_WIDTH // 2, panel_y + 24)))

        # 1. Time spent
        mins = int(self.total_time) // 60
        secs = int(self.total_time) % 60
        time_str = f"Accumulated Time Spent: {mins}m {secs}s"
        time_surf = self.font_body.render(time_str, True, COLOR_CREAM)
        surface.blit(time_surf, time_surf.get_rect(center=(LOGICAL_WIDTH // 2, panel_y + 64)))

        # 2. Wisdom score (Monk Correct Questions)
        monk_correct_dict = self.manager.shared.get("monk_correct", {})
        correct_count = sum(1 for v in monk_correct_dict.values() if v is True)
        total_questions = sum(1 for v in monk_correct_dict.values() if v is not None)
        wisdom_str = f"Spiritual Wisdom Score: {correct_count} / {total_questions if total_questions > 0 else 4} Correct Answers"
        wisdom_surf = self.font_body.render(wisdom_str, True, COLOR_SAFFRON)
        surface.blit(wisdom_surf, wisdom_surf.get_rect(center=(LOGICAL_WIDTH // 2, panel_y + 104)))

        # 3. Focus score (Distractions Avoided)
        boxes_dict = self.manager.shared.get("boxes_opened", {})
        total_opened = sum(v[0] for v in boxes_dict.values() if isinstance(v, tuple))
        total_boxes = sum(v[1] for v in boxes_dict.values() if isinstance(v, tuple))
        avoided_count = total_boxes - total_opened
        focus_str = f"Pilgrimage Focus Score: Avoided {avoided_count} / {total_boxes if total_boxes > 0 else 18} Distractions"
        focus_surf = self.font_body.render(focus_str, True, COLOR_WHITE)
        surface.blit(focus_surf, focus_surf.get_rect(center=(LOGICAL_WIDTH // 2, panel_y + 144)))

        # ── Interactive Restart Button ──
        r = self.restart_rect
        hover = self.hover_restart
        scale_offset = 6 if hover else 0
        draw_rect = r.inflate(scale_offset, scale_offset)

        btn_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        bg_alpha = 240 if hover else 175
        bg_color = (48, 32, 68, bg_alpha) if hover else (26, 18, 40, bg_alpha)
        pygame.draw.rect(btn_surf, bg_color, btn_surf.get_rect(), border_radius=16)
        
        border_color = COLOR_GOLD_BRIGHT if hover else COLOR_GOLD_DIM
        border_w = 3 if hover else 1.5
        pygame.draw.rect(btn_surf, border_color, btn_surf.get_rect(), width=int(border_w), border_radius=16)
        surface.blit(btn_surf, draw_rect.topleft)

        btn_text = self.font_body.render("RESTART PILGRIMAGE", True, COLOR_WHITE if hover else COLOR_CREAM)
        tr = btn_text.get_rect(center=draw_rect.center)
        surface.blit(btn_text, tr)

        # Small continue prompt
        if self.elapsed > 2.0:
            alpha = int(120 + 100 * math.sin(self.elapsed * 4))
            cont = self.font_small.render("Press ENTER or Click button to proceed", True, COLOR_GOLD_DIM)
            cont.set_alpha(alpha)
            surface.blit(cont, cont.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 12)))
