"""
monk_system.py — The Monk / Guide NPC system.
Handles monk placement, interaction, spiritual Q&A dialogue, and rewards.
"""
import math
import pygame
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, MONK_QUESTIONS,
    COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM, COLOR_WHITE, COLOR_CREAM,
    COLOR_SAFFRON, COLOR_GREEN, COLOR_RED, COLOR_BG_DARK,
    FONT_SIZE_BODY, FONT_SIZE_SUBTITLE, FONT_SIZE_SMALL,
)


class Monk:
    """The Monk / Guide NPC with interactive parchment scroll and typewriter Q&A."""

    WIDTH = 44
    HEIGHT = 70

    def __init__(self, x, y, level):
        self.x = x
        self.y = y
        self.level = level
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
        q = MONK_QUESTIONS.get(self.level)
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

    def draw(self, surface, font_body, font_small):
        dy = int(self.y + self.hover_offset)

        # Monk body — saffron robed figure
        monk_surf = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        # Robe
        pygame.draw.rect(monk_surf, COLOR_SAFFRON,
                         pygame.Rect(6, 20, self.WIDTH - 12, self.HEIGHT - 20), border_radius=6)
        # Head
        pygame.draw.circle(monk_surf, (200, 170, 130), (self.WIDTH // 2, 14), 14)
        # Eyes
        pygame.draw.circle(monk_surf, (0, 0, 0), (self.WIDTH // 2 - 4, 12), 2)
        pygame.draw.circle(monk_surf, (0, 0, 0), (self.WIDTH // 2 + 4, 12), 2)
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

        q = MONK_QUESTIONS.get(self.level)
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


# Monk placement positions per level (x, y on specific platforms)
MONK_POSITIONS = {
    1: (560, None),   # Will be placed on a platform
    2: (460, None),
    3: (710, None),
    4: (910, None),
}


def create_monk(level, platforms):
    """Create a monk placed on a suitable platform for the given level."""
    target_x = MONK_POSITIONS.get(level, (400, None))[0]

    # Find the best platform near target_x (skip boundary walls = first 4)
    best_plat = None
    best_dist = float("inf")
    for plat in platforms[4:]:
        dist = abs(plat.centerx - target_x)
        if dist < best_dist and plat.width >= 140:
            best_dist = dist
            best_plat = plat

    if best_plat is None:
        best_plat = platforms[4] if len(platforms) > 4 else platforms[0]

    mx = best_plat.x + (best_plat.width - Monk.WIDTH) // 2
    my = best_plat.y - Monk.HEIGHT
    return Monk(mx, my, level)
