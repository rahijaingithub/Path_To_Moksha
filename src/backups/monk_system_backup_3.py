"""
monk_system.py — The Monk / Guide NPC system.
Handles monk placement, interaction, spiritual Q&A dialogue, and rewards.
"""
import math
import pygame
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT,
    COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM, COLOR_WHITE, COLOR_CREAM,
    COLOR_SAFFRON, COLOR_GREEN, COLOR_RED, COLOR_BG_DARK,
    FONT_SIZE_BODY, FONT_SIZE_SUBTITLE, FONT_SIZE_SMALL,
)


class Monk:
    """The Monk / Guide NPC with interactive parchment scroll and typewriter Q&A."""

    WIDTH = 44
    HEIGHT = 70

    def __init__(self, x, y, level, question_data):
        self.x = x
        self.y = y
        self.level = level
        self.question_data = question_data
        self.interacted = False      # Has the player spoken to this monk?
        self.answered_correctly = False
        self.show_prompt = False      # Show "Press UP" hint
        self.dialogue_active = False  # Is the Q&A dialogue open?
        self.selected_choice = 0      # 0 or 1
        self.result_text = ""
        self.result_timer = 0.0
        self.result_correct = False
        self.hover_offset = 0.0
        self.dialogue_elapsed = 0.0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    @property
    def interaction_zone(self):
        return self.rect.inflate(60, 40)

    def update(self, dt, elapsed, player_rect):
        self.hover_offset = math.sin(elapsed * 1.5) * 3
        self.show_prompt = (not self.interacted and
                            self.interaction_zone.collidepoint(player_rect.centerx, player_rect.centery))
        if self.result_timer > 0:
            self.result_timer -= dt

        if self.dialogue_active:
            self.dialogue_elapsed += dt
        else:
            self.dialogue_elapsed = 0.0

    def start_dialogue(self):
        if not self.interacted:
            self.dialogue_active = True
            self.selected_choice = 0
            self.dialogue_elapsed = 0.0

    def submit_answer(self):
        """Submit the selected answer. Returns True if correct."""
        q = self.question_data
        if not q:
            return False
        self.interacted = True
        self.dialogue_active = False
        correct = (self.selected_choice == q["correct"])
        self.answered_correctly = correct
        if correct:
            self.result_text = "Correct! The path is revealed..."
            self.result_correct = True
        else:
            self.result_text = "Incorrect. You must search on your own."
            self.result_correct = False
        self.result_timer = 3.0
        return correct

    # def draw(self, surface, font_body, font_small):
    #     dy = int(self.y + self.hover_offset)

    #     # Monk body — saffron robed figure
    #     monk_surf = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
    #     # Robe
    #     pygame.draw.rect(monk_surf, COLOR_SAFFRON,
    #                      pygame.Rect(6, 20, self.WIDTH - 12, self.HEIGHT - 20), border_radius=6)
    #     # Head
    #     pygame.draw.circle(monk_surf, (200, 170, 130), (self.WIDTH // 2, 14), 14)
    #     # Eyes
    #     pygame.draw.circle(monk_surf, (0, 0, 0), (self.WIDTH // 2 - 4, 12), 2)
    #     pygame.draw.circle(monk_surf, (0, 0, 0), (self.WIDTH // 2 + 4, 12), 2)
    #     surface.blit(monk_surf, (self.x, dy))
    def draw(self, surface, font_body, font_small):
        dy = int(self.y + self.hover_offset)

        # Digamber body in Padmasana (Seated, sky-clad figure)
        monk_surf = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        
        # Color Palette
        SKIN_COLOR = (220, 185, 145)
        PEACOCK_BLUE = (0, 128, 128)
        WOOD_BROWN = (139, 69, 19)
        
        # Head
        pygame.draw.circle(monk_surf, SKIN_COLOR, (self.WIDTH // 2, 14), 12)
        
        # Eyes (Closed / Meditative state)
        pygame.draw.line(monk_surf, (0, 0, 0), (self.WIDTH // 2 - 5, 14), (self.WIDTH // 2 - 1, 14), 2)
        pygame.draw.line(monk_surf, (0, 0, 0), (self.WIDTH // 2 + 1, 14), (self.WIDTH // 2 + 5, 14), 2)
        
        # Torso (Seated upright)
        pygame.draw.rect(monk_surf, SKIN_COLOR, 
                         pygame.Rect(12, 24, self.WIDTH - 24, self.HEIGHT - 36), border_radius=4)
        
        # Crossed Legs (Widened Padmasana base covering full bottom width)
        pygame.draw.ellipse(monk_surf, SKIN_COLOR, 
                            pygame.Rect(0, self.HEIGHT - 16, self.WIDTH, 16))
        
        # 1. Picchi (Peacock Feather Whisk) - Rested on the ground
        # Handle extending down
        pygame.draw.line(monk_surf, WOOD_BROWN, (8, self.HEIGHT - 24), (8, self.HEIGHT - 4), 2)
        # Feather fan sitting low
        pygame.draw.ellipse(monk_surf, PEACOCK_BLUE, pygame.Rect(2, self.HEIGHT - 32, 12, 16))
        
        # 2. Kamandalu (Water Pot) - Placed on the ground to the right
        # Pot Base
        pygame.draw.circle(monk_surf, WOOD_BROWN, (self.WIDTH - 10, self.HEIGHT - 10), 6)
        # Pot Neck & Spout
        pygame.draw.rect(monk_surf, WOOD_BROWN, pygame.Rect(self.WIDTH - 12, self.HEIGHT - 18, 4, 4))
        # Handle loop
        pygame.draw.arc(monk_surf, WOOD_BROWN, pygame.Rect(self.WIDTH - 14, self.HEIGHT - 22, 8, 8), 0, 3.14, 2)
        
        surface.blit(monk_surf, (self.x, dy))


        # Interaction prompt
        if self.show_prompt and not self.dialogue_active:
            prompt = font_small.render("▲ Press UP to speak", True, COLOR_GOLD_BRIGHT)
            pr = prompt.get_rect(center=(self.x + self.WIDTH // 2, dy - 25))
            bg = pygame.Surface((pr.width + 16, pr.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, 160), bg.get_rect(), border_radius=6)
            surface.blit(bg, (pr.x - 8, pr.y - 4))
            surface.blit(prompt, pr)

        # Result message
        if self.result_timer > 0:
            color = COLOR_GREEN if self.result_correct else COLOR_RED
            res = font_body.render(self.result_text, True, color)
            rr = res.get_rect(center=(self.x + self.WIDTH // 2, dy - 30))
            bg = pygame.Surface((rr.width + 20, rr.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, 180), bg.get_rect(), border_radius=8)
            surface.blit(bg, (rr.x - 10, rr.y - 6))
            surface.blit(res, rr)

    def draw_dialogue(self, surface, font_title, font_body, font_small):
        """Draw the full-screen dialogue overlay with antique scroll and typewriter question."""
        if not self.dialogue_active:
            return

        q = self.question_data
        if not q:
            return

        # Dim background overlay
        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Dialogue box dimensions
        box_w, box_h = 750, 340
        bx = (LOGICAL_WIDTH - box_w) // 2
        by = (LOGICAL_HEIGHT - box_h) // 2

        # ── Scroll Wood Roll Rollers on Left and Right borders ──
        # Left Roller Cylindrical scroll roll
        pygame.draw.rect(surface, (120, 80, 40), (bx - 12, by - 12, 24, box_h + 24), border_radius=6)
        pygame.draw.rect(surface, COLOR_GOLD, (bx - 12, by - 12, 24, box_h + 24), width=2, border_radius=6)
        # Right Roller Cylindrical scroll roll
        pygame.draw.rect(surface, (120, 80, 40), (bx + box_w - 12, by - 12, 24, box_h + 24), border_radius=6)
        pygame.draw.rect(surface, COLOR_GOLD, (bx + box_w - 12, by - 12, 24, box_h + 24), width=2, border_radius=6)

        # Parchment Paper central canvas
        pygame.draw.rect(surface, (246, 232, 202), (bx, by, box_w, box_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD_BRIGHT, (bx, by, box_w, box_h), width=3, border_radius=4)
        
        # Delicate antique interior border frame
        pygame.draw.rect(surface, (210, 185, 145), (bx + 8, by + 8, box_w - 16, box_h - 16), width=2, border_radius=2)

        # Title (Rendered in rich deep brown wood-tone)
        title = font_title.render("THE VENERABLE MONK SPEAKS", True, (110, 45, 10))
        surface.blit(title, title.get_rect(center=(LOGICAL_WIDTH // 2, by + 42)))

        # Typewriter reveal question logic
        chars_to_show = int(self.dialogue_elapsed * 32)
        question_full = f'"{q["question"]}"'
        revealed_q = question_full[:chars_to_show]
        
        question = font_body.render(revealed_q, True, (45, 30, 20))
        surface.blit(question, question.get_rect(center=(LOGICAL_WIDTH // 2, by + 105)))

        # Choices (drawn only when question is fully typed to encourage reading)
        is_typed = chars_to_show >= len(question_full)
        
        for i, choice in enumerate(q["choices"]):
            is_sel = (i == self.selected_choice)
            cy = by + 170 + i * 54
            
            # Selection backing plate with custom highlight
            if is_sel:
                hl = pygame.Surface((620, 40), pygame.SRCALPHA)
                # Golden-Saffron glowing selection
                pygame.draw.rect(hl, (255, 140, 0, 40), hl.get_rect(), border_radius=10)
                pygame.draw.rect(hl, (220, 110, 20, 150), hl.get_rect(), width=2, border_radius=10)
                surface.blit(hl, ((LOGICAL_WIDTH - 620) // 2, cy - 20))
            
            # Text option
            prefix = "► " if is_sel else "  "
            opt_color = (210, 100, 10) if is_sel else (95, 75, 60)
            c_surf = font_body.render(f"{prefix}{choice}", True, opt_color)
            surface.blit(c_surf, c_surf.get_rect(center=(LOGICAL_WIDTH // 2, cy)))

        # Instructions / Navigation hints
        hint = font_small.render("▲▼ or Hover to choose  •  ENTER or Click option to answer  •  ESC to leave", True, (130, 110, 90))
        surface.blit(hint, hint.get_rect(center=(LOGICAL_WIDTH // 2, by + box_h - 26)))


def create_monk(level, platforms, hazards, asked_questions):
    """Create a monk placed randomly on a safe platform or ground, avoiding all hazards and choosing a unique question."""
    import random
    import json
    import os
    from settings import ASSETS_DIR, LOGICAL_WIDTH

    # Load questions pool dynamically from JSON
    json_path = os.path.join(ASSETS_DIR, "monk_questions.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            pool = json.load(f)
    except Exception as e:
        print(f"[MonkSystem] Error loading questions: {e}")
        pool = {
            str(level): [{
                "question": "To find peace, what must one leave behind?",
                "choices": ["Ego and pride", "Physical car"],
                "correct": 0
            }]
        }

    level_questions = pool.get(str(level), [])
    if not level_questions:
        level_questions = [{
            "question": "To find peace, what must one leave behind?",
            "choices": ["Ego and pride", "Physical car"],
            "correct": 0
        }]

    # Filter out asked questions to prevent repetition
    candidates = [q for q in level_questions if q["question"] not in asked_questions]
    if not candidates:
        # If all questions have been asked, reset tracking for this level
        candidates = level_questions
        for q in level_questions:
            if q["question"] in asked_questions:
                asked_questions.remove(q["question"])

    selected_q = random.choice(candidates)
    asked_questions.append(selected_q["question"])

    def is_placement_safe(x, y, width, hazards):
        for h in hazards:
            h_bottom = h.y + h.h
            on_same_surface = abs(h_bottom - y) < 25 or abs(h.y - y) < 35
            if on_same_surface:
                overlap = not (x + width < h.x or x > h.x + h.w)
                if overlap:
                    return False
        return True

    # Floor is platforms[0]. Standard platforms are platforms[4:]
    candidates_plats = [platforms[0]] + [p for p in platforms[4:] if p.width >= 120]
    random.shuffle(candidates_plats)

    for plat in candidates_plats:
        x_min = plat.x + 15
        x_max = plat.x + plat.width - Monk.WIDTH - 15
        
        if plat == platforms[0]:
            # Limit ground floor to avoid player spawning zone (x<250) and far right temple gate
            x_min = max(x_min, 250)
            x_max = min(x_max, LOGICAL_WIDTH - 250)

        if x_min >= x_max:
            continue

        # Try multiple random offsets on this platform
        for _ in range(15):
            mx = random.randint(int(x_min), int(x_max))
            my = plat.y - Monk.HEIGHT
            if is_placement_safe(mx, plat.y, Monk.WIDTH, hazards):
                return Monk(mx, my, level, selected_q)

    # Fallback safe spot
    plat = platforms[4] if len(platforms) > 4 else platforms[0]
    mx = plat.x + (plat.width - Monk.WIDTH) // 2
    my = plat.y - Monk.HEIGHT
    return Monk(mx, my, level, selected_q)
