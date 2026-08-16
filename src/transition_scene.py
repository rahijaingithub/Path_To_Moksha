"""
transition_scene.py — Cutscene between levels with story text, Bhagwan imagery,
walking arrival animation, and deep bowing prostration sequence.
"""
import os
import math
import random
import pygame
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, IMAGES_DIR,
    COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_WHITE, COLOR_SAFFRON,
    GAME_FONT_SIZE_SUBTITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL,
    SCENE_LEVEL, SCENE_TITLE,
)


TRANSITION_DATA = {
    2: {
        "title": "Level 1 Complete — Sacred Temple Reverence",
        "subtitle": "You have overcome early obstacles. Bow in devotion before the sacred flame.",
        "image": "jsot_temple.png",
        "story": [
            "With purity of mind and determination,",
            "you offer heartfelt reverence at the temple.",
            "May your journey towards Moksha be filled with wisdom.",
        ],
    },
    3: {
        "title": "Level 2 Complete — Reverence to Lord Parshvanath",
        "subtitle": "Deepening your spiritual practice at the feet of Bhagwan.",
        "image": "parshvanath.png",
        "story": [
            "Every step forward purifies the soul.",
            "Hold steadfast to Truth, Non-Violence, and Devotion.",
        ],
    },
    4: {
        "title": "Level 3 Complete — Final Steps",
        "subtitle": "The summit of enlightenment approaches.",
        "image": "jsot_temple.png",
        "story": [
            "The ultimate destination is near.",
            "Focus your mind on supreme peace.",
        ],
    },
}


class TransitionScene:
    """Renders transition between levels with animated walking arrival & bowing sequence."""

    def __init__(self, manager, asset_mgr, input_mgr=None):
        self.manager = manager
        self.assets = asset_mgr
        self.input_mgr = input_mgr
        self.next_level = 2
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.auto_advance_timer = 8.5  # extended for complete walk + bow cutscene
        self.data = {}
        self.bg_image = None
        
        # Character animation assets
        self.walk_strip = None
        self.bow_strip = None
        self.idle_sprite = None
        self.particles = []

    def on_enter(self, **kwargs):
        self.next_level = kwargs.get("next_level", 2)
        self.to_be_continued = kwargs.get("to_be_continued", False)
        self.elapsed = 0.0
        self.fade_alpha = 255
        self.auto_advance_timer = 8.5
        self.particles = []

        self.data = TRANSITION_DATA.get(self.next_level, TRANSITION_DATA[2])

        # Fonts
        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_SUBTITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

        # Load transition image (Jyot / Temple for L1, Parshvanath Bhagwan for L2)
        img_name = self.data.get("image", "jsot_temple.png" if self.next_level == 2 else "parshvanath.png")
        self.bg_image = self.assets.load_image(img_name, "transitions", scale=(440, 420) if img_name == "jsot_temple.png" else (360, 480))
        if not self.bg_image or self.bg_image.get_at((0, 0))[:3] == (255, 0, 220):
            fallback_name = "jsot_temple.png" if self.next_level == 2 else "parshvanath.png"
            self.bg_image = self.assets.load_image(fallback_name, "transitions", scale=(440, 420))

        # Selected character ("boy" or "girl")
        char_type = self.manager.shared.get("character", "boy")

        # 1. Load walk_right strip for walking arrival animation
        walk_strip_name = f"player_{char_type}_walk_right.png"
        self.walk_strip = self.assets.load_image(walk_strip_name, "sprites", alpha=True)

        # 2. Load bowing sprite — 2D mask island extraction (prevents row-split foot bleed)
        bow_img_name = f"player_{char_type}_bowing.png"
        self.bow_strip = self.assets.load_image(bow_img_name, "sprites", alpha=True)
        self.bow_frames = []

        if self.bow_strip:
            mask = pygame.mask.from_surface(self.bow_strip, threshold=8)
            island_rects = mask.get_bounding_rects()

            # Filter out tiny 1x1 noise dots and sort poses top-to-bottom, left-to-right
            valid_rects = [r for r in island_rects if r.width > 20 and r.height > 20]
            valid_rects.sort(key=lambda r: (0 if r.y < 400 else 1, r.x))

            raw_cropped = []
            standing_h = None

            for rect in valid_rects:
                cell = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                cell.blit(self.bow_strip, (0, 0), rect)
                raw_cropped.append(cell)
                if standing_h is None:
                    standing_h = rect.height  # Pose 0 standing height reference (~377px)

            scale_ratio = 150.0 / standing_h if (standing_h and standing_h > 0) else 0.40

            for cropped in raw_cropped:
                tw = max(10, int(cropped.get_width() * scale_ratio))
                th = max(10, int(cropped.get_height() * scale_ratio))
                scaled = pygame.transform.smoothscale(cropped, (tw, th))
                self.bow_frames.append(scaled)

            print(f"[Transition] Perfect 2D Mask Extraction: {len(self.bow_frames)} frames (standing_h={standing_h}px, scale={scale_ratio:.3f})")



        # 3. Load idle_right 1st frame as fallback / standing pose
        strip_name = f"player_{char_type}_idle_right.png"
        idle_strip = self.assets.load_image(strip_name, "sprites", alpha=True)
        if idle_strip:
            fh = idle_strip.get_height()
            frame_surf = pygame.Surface((fh, fh), pygame.SRCALPHA)
            frame_surf.blit(idle_strip, (0, 0), (0, 0, fh, fh))
            self.idle_sprite = pygame.transform.smoothscale(frame_surf, (150, 150))
        else:
            self.idle_sprite = None

        self.assets.stop_music()

    def on_exit(self):
        """Clean up when exiting scene."""
        pass

    def handle_events(self, events, input_mgr):
        if self.elapsed > 1.5:
            if (input_mgr.just_pressed[input_mgr.ACTION] or
                    input_mgr.just_pressed[input_mgr.JUMP] or
                    input_mgr.just_pressed[input_mgr.MENU_SELECT] or
                    input_mgr.just_pressed[input_mgr.MENU_BACK]):
                self._advance()
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._advance()


    def _advance(self):
        if self.to_be_continued:
            from settings import SCENE_LEADERBOARD
            final_score = self.manager.shared.get("total_score", 0)
            player_name = self.manager.shared.get("player_name", "Pilgrim")
            character = self.manager.shared.get("character", "boy")
            from profile_manager import ProfileManager
            ProfileManager().save_profile(player_name, character=character, score=final_score, level_reached=self.next_level - 1)
            self.manager.shared["final_score"] = final_score
            self.manager.switch_to(SCENE_LEADERBOARD)
        else:
            self.manager.switch_to(SCENE_LEVEL, level=self.next_level)



    def update(self, dt):
        self.elapsed += dt
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 200 * dt)
        self.auto_advance_timer -= dt
        if self.auto_advance_timer <= 0:
            self._advance()

        # Update spiritual golden particles
        for p in self.particles:
            p["age"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
        self.particles = [p for p in self.particles if p["age"] < p["lifetime"]]

        # Spawn new prayer sparkles from devotee up towards Bhagwan image when bowing
        is_t1 = (self.next_level == 2)
        if not is_t1 and self.elapsed > 2.5 and random.random() < 0.5:
            img_left = (LOGICAL_WIDTH // 2 - 220) if self.bg_image else 180
            target_x = img_left + 60
            self.particles.append({
                "x": target_x + random.uniform(-30, 30),
                "y": LOGICAL_HEIGHT // 2 + 140,
                "vx": random.uniform(-15, 15),
                "vy": random.uniform(-40, -90),
                "color": random.choice([COLOR_GOLD_BRIGHT, COLOR_SAFFRON, COLOR_WHITE]),
                "size": random.randint(2, 5),
                "age": 0.0,
                "lifetime": random.uniform(1.2, 2.2),
            })




    def draw(self, surface):
        # Dark celestial background with soft gradient
        for y in range(LOGICAL_HEIGHT):
            t = y / LOGICAL_HEIGHT
            r = int(18 * (1 - t) + 10 * t)
            g = int(12 * (1 - t) + 8 * t)
            b = int(28 * (1 - t) + 20 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (LOGICAL_WIDTH, y))

        # Double-layered divine light halo behind Bhagwan image
        glow_r1 = 240 + int(24 * math.sin(self.elapsed * 1.8))
        glow1 = pygame.Surface((glow_r1 * 2, glow_r1 * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow1, (255, 210, 80, 24), (glow_r1, glow_r1), glow_r1)
        surface.blit(glow1, (LOGICAL_WIDTH // 2 - glow_r1, LOGICAL_HEIGHT // 2 - glow_r1 - 70))

        glow_r2 = 180 + int(12 * math.cos(self.elapsed * 2.4))
        glow2 = pygame.Surface((glow_r2 * 2, glow_r2 * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow2, (255, 140, 40, 36), (glow_r2, glow_r2), glow_r2)
        surface.blit(glow2, (LOGICAL_WIDTH // 2 - glow_r2, LOGICAL_HEIGHT // 2 - glow_r2 - 70))

        # Bhagwan / Temple image with subtle floating Ken Burns zoom
        if self.bg_image:
            zoom = 1.0 + 0.03 * math.sin(self.elapsed * 0.4)
            w = int(self.bg_image.get_width() * zoom)
            h = int(self.bg_image.get_height() * zoom)
            zoomed_img = pygame.transform.smoothscale(self.bg_image, (w, h))
            img_rect = zoomed_img.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 70))
            surface.blit(zoomed_img, img_rect)

        # ── Animated Walking & Bowing Player Character ─────────────────────────
        # Alignment:
        # - Start: Left screen edge (start_x = -30)
        # - Destination: Left edge of the transition image (img_left)
        # - Transition 1: Walk from left screen edge to image left boundary, NO bowing.
        # - Transition 2: Walk from left screen edge to image left boundary, BOW at image left boundary facing right.

        img_left = (LOGICAL_WIDTH // 2 - 220) if self.bg_image else 180
        char_cy = LOGICAL_HEIGHT // 2 + 140
        is_transition_1 = (self.next_level == 2)

        if is_transition_1:
            # TRANSITION 1: Walk from left side (-30) to image's left endpoint (img_left + 40), NO bowing
            start_x = -30
            target_x = img_left + 60
            walk_duration = 4.0

            progress = min(1.0, self.elapsed / walk_duration)
            char_cx = int(start_x + (target_x - start_x) * progress)

            if self.walk_strip:
                fh = self.walk_strip.get_height()
                n_frames = max(1, self.walk_strip.get_width() // fh)
                frame_idx = int(self.elapsed / 0.12) % n_frames
                frame_surf = pygame.Surface((fh, fh), pygame.SRCALPHA)
                frame_surf.blit(self.walk_strip, (0, 0), (frame_idx * fh, 0, fh, fh))
                current_sprite = pygame.transform.smoothscale(frame_surf, (150, 150))
            else:
                current_sprite = self.idle_sprite

            if current_sprite:
                char_rect = current_sprite.get_rect(center=(char_cx, char_cy))
                surface.blit(current_sprite, char_rect)

        else:
            # TRANSITION 2: Walk from left side (-30) to image's left endpoint (img_left + 60), then BOW facing right
            start_x = -30
            target_x = img_left + 60
            walk_duration = 2.5

            if self.elapsed < walk_duration:
                # WALKING PHASE: walk right towards image's left edge
                progress = self.elapsed / walk_duration
                char_cx = int(start_x + (target_x - start_x) * progress)

                if self.walk_strip:
                    fh = self.walk_strip.get_height()
                    n_frames = max(1, self.walk_strip.get_width() // fh)
                    frame_idx = int(self.elapsed / 0.12) % n_frames
                    frame_surf = pygame.Surface((fh, fh), pygame.SRCALPHA)
                    frame_surf.blit(self.walk_strip, (0, 0), (frame_idx * fh, 0, fh, fh))
                    current_sprite = pygame.transform.smoothscale(frame_surf, (150, 150))
                else:
                    current_sprite = self.idle_sprite

                if current_sprite:
                    char_rect = current_sprite.get_rect(center=(char_cx, char_cy))
                    surface.blit(current_sprite, char_rect)

            else:
                # BOWING PHASE: at image's left endpoint (target_x) facing right towards Bhagwan
                char_cx = target_x
                n_bow = len(self.bow_frames)

                if n_bow > 0:
                    bow_time = self.elapsed - walk_duration
                    last = n_bow - 1
                    if bow_time < 1.8:
                        frame_idx = min(last, int(bow_time / 1.8 * n_bow))
                    elif bow_time < 3.8:
                        frame_idx = last  # Hold deepest bow
                    elif bow_time < 5.0:
                        t = (bow_time - 3.8) / 1.2
                        frame_idx = max(0, int((1.0 - t) * last))
                    else:
                        frame_idx = 0
                    bowed_sprite = self.bow_frames[frame_idx]
                else:
                    bowed_sprite = self.idle_sprite

                if bowed_sprite:
                    aura_radius = 45 + int(6 * math.sin(self.elapsed * 4))
                    aura_surf = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
                    pygame.draw.ellipse(aura_surf, (255, 215, 60, 90), (0, 0, aura_radius * 2, aura_radius // 2))
                    surface.blit(aura_surf, (char_cx - aura_radius, char_cy + 55))
                    char_rect = bowed_sprite.get_rect(midbottom=(char_cx, char_cy + 70))
                    surface.blit(bowed_sprite, char_rect)



        # ── Rising Prayer Light Particles ────────────────────────────────────
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (1.0 - p["age"] / p["lifetime"]))))
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"], alpha), (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]), int(p["y"])))

        # Title / Subtitle Text Card
        title_surf = self.font_title.render(self.data["title"], True, COLOR_GOLD_BRIGHT)
        title_rect = title_surf.get_rect(center=(LOGICAL_WIDTH // 2, 45))
        surface.blit(title_surf, title_rect)

        sub_surf = self.font_small.render(self.data["subtitle"], True, (210, 200, 180))
        sub_rect = sub_surf.get_rect(center=(LOGICAL_WIDTH // 2, 80))
        surface.blit(sub_surf, sub_rect)

        # Story overlay box at the bottom
        story_lines = self.data.get("story", [])
        if story_lines:
            box_h = 75
            box_y = LOGICAL_HEIGHT - box_h - 20
            box_surf = pygame.Surface((LOGICAL_WIDTH - 120, box_h), pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (10, 8, 20, 200), box_surf.get_rect(), border_radius=10)
            pygame.draw.rect(box_surf, COLOR_GOLD, box_surf.get_rect(), width=2, border_radius=10)
            surface.blit(box_surf, (60, box_y))

            for i, line in enumerate(story_lines):
                line_surf = self.font_body.render(line, True, COLOR_WHITE)
                line_rect = line_surf.get_rect(center=(LOGICAL_WIDTH // 2, box_y + 18 + i * 22))
                surface.blit(line_surf, line_rect)

        # Continue prompt at bottom right
        if self.elapsed > 1.5 and int(self.elapsed * 2) % 2 == 0:
            prompt_str = "Press SPACE / ENTER / ACT to Continue ➔" if not self.to_be_continued else "Press SPACE/ENTER"
            p_surf = self.font_small.render(prompt_str, True, COLOR_GOLD_BRIGHT)
            p_rect = p_surf.get_rect(bottomright=(LOGICAL_WIDTH - 70, LOGICAL_HEIGHT - 28))
            surface.blit(p_surf, p_rect)
        # Fade in overlay at beginning of scene
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(int(self.fade_alpha))
            surface.blit(fade_surf, (0, 0))
