"""
input_manager.py — Unified input system for keyboard + touch/click controls.
Renders on-screen touch buttons and maps both input methods to the same actions.
"""
import pygame
from settings import (
    TOUCH_BUTTON_SIZE, TOUCH_BUTTON_MARGIN, TOUCH_BUTTON_ALPHA,
    LOGICAL_WIDTH, LOGICAL_HEIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_SHADOW,
)


class InputManager:
    """Handles keyboard and on-screen touch/click input."""

    # Action flags
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    JUMP = "jump"
    ACTION = "action"   # generic interact / confirm
    BACK = "back"       # ESC / cancel
    FULLSCREEN = "fullscreen"

    def __init__(self):
        self.actions = {
            self.LEFT: False,
            self.RIGHT: False,
            self.UP: False,
            self.JUMP: False,
            self.ACTION: False,
            self.BACK: False,
            self.FULLSCREEN: False,
        }
        # One-shot events (pressed THIS frame only)
        self.just_pressed = {key: False for key in self.actions}

        # Touch button rects (in logical coordinates)
        self._build_touch_buttons()

        # Track which buttons are being held by mouse/touch
        self._touch_held = {key: False for key in self.actions}

    def _build_touch_buttons(self):
        """Define on-screen button positions (bottom-left for D-pad, bottom-right for action)."""
        s = TOUCH_BUTTON_SIZE
        m = TOUCH_BUTTON_MARGIN
        bottom = LOGICAL_HEIGHT - m - s

        # D-Pad (bottom-left)
        self.touch_buttons = {
            self.LEFT:  pygame.Rect(m, bottom, s, s),
            self.RIGHT: pygame.Rect(m + s + m, bottom, s, s),
            self.UP:    pygame.Rect(m + (s + m) // 2, bottom - s - m, s, s),
            # Action buttons (bottom-right)
            self.JUMP:  pygame.Rect(LOGICAL_WIDTH - m - s, bottom, s, s),
            self.ACTION: pygame.Rect(LOGICAL_WIDTH - m - s - m - s, bottom, s, s),
        }

        # Labels for drawing
        self.touch_labels = {
            self.LEFT: "◄",
            self.RIGHT: "►",
            self.UP: "▲",
            self.JUMP: "JUMP",
            self.ACTION: "ACT",
        }

    def update(self, events, scale_x=1.0, scale_y=1.0, offset_x=0, offset_y=0):
        """
        Process one frame of input.
        scale_x/y and offset_x/y convert screen mouse coords → logical coords.
        """
        # Reset one-shot events
        for key in self.just_pressed:
            self.just_pressed[key] = False

        # Reset keyboard-triggered fullscreen flag
        self.actions[self.FULLSCREEN] = False

        # ── Keyboard ──
        keys = pygame.key.get_pressed()
        self.actions[self.LEFT] = keys[pygame.K_LEFT] or keys[pygame.K_a]
        self.actions[self.RIGHT] = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.actions[self.UP] = keys[pygame.K_UP] or keys[pygame.K_w]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.just_pressed[self.JUMP] = True
                    self.actions[self.JUMP] = True
                if event.key in (pygame.K_RETURN, pygame.K_e):
                    self.just_pressed[self.ACTION] = True
                    self.actions[self.ACTION] = True
                if event.key == pygame.K_ESCAPE:
                    self.just_pressed[self.BACK] = True
                    self.actions[self.BACK] = True
                if event.key == pygame.K_F11:
                    self.just_pressed[self.FULLSCREEN] = True
                    self.actions[self.FULLSCREEN] = True

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.actions[self.JUMP] = False
                if event.key in (pygame.K_RETURN, pygame.K_e):
                    self.actions[self.ACTION] = False
                if event.key == pygame.K_ESCAPE:
                    self.actions[self.BACK] = False

            # ── Mouse / Touch ──
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                mx, my = self._get_logical_pos(event, scale_x, scale_y, offset_x, offset_y)
                for action_key, rect in self.touch_buttons.items():
                    if rect.collidepoint(mx, my):
                        self._touch_held[action_key] = True
                        self.actions[action_key] = True
                        self.just_pressed[action_key] = True

            if event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                # Release all touch holds
                for action_key in self._touch_held:
                    if self._touch_held[action_key]:
                        self._touch_held[action_key] = False
                        # Only release if keyboard isn't also holding it
                        # (handled by keyboard state above)

            if event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                mx, my = self._get_logical_pos(event, scale_x, scale_y, offset_x, offset_y)
                for action_key, rect in self.touch_buttons.items():
                    if rect.collidepoint(mx, my):
                        if not self._touch_held[action_key]:
                            self._touch_held[action_key] = True
                            self.actions[action_key] = True
                    else:
                        if self._touch_held[action_key]:
                            self._touch_held[action_key] = False

        # Merge touch holds into actions
        for action_key in self._touch_held:
            if self._touch_held[action_key]:
                self.actions[action_key] = True

    def _get_logical_pos(self, event, scale_x, scale_y, offset_x, offset_y):
        """Convert screen mouse/touch position to logical coordinates."""
        if hasattr(event, "x") and isinstance(event.x, float):
            # FINGERDOWN events give normalized 0-1 positions
            info = pygame.display.get_surface().get_size()
            sx = event.x * info[0]
            sy = event.y * info[1]
        else:
            sx, sy = pygame.mouse.get_pos()

        lx = (sx - offset_x) / scale_x if scale_x != 0 else 0
        ly = (sy - offset_y) / scale_y if scale_y != 0 else 0
        return lx, ly

    def draw_touch_controls(self, surface, font):
        """Render semi-transparent on-screen buttons onto the logical surface."""
        for action_key, rect in self.touch_buttons.items():
            # Button background
            btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            alpha = TOUCH_BUTTON_ALPHA + 60 if self._touch_held.get(action_key) else TOUCH_BUTTON_ALPHA
            color = (*COLOR_GOLD[:3], alpha) if self._touch_held.get(action_key) else (255, 255, 255, alpha)
            pygame.draw.rect(btn_surf, color, btn_surf.get_rect(), border_radius=12)
            pygame.draw.rect(btn_surf, (*COLOR_WHITE[:3], alpha), btn_surf.get_rect(), width=2, border_radius=12)
            surface.blit(btn_surf, rect.topleft)

            # Label
            label = self.touch_labels.get(action_key, "?")
            text_surf = font.render(label, True, COLOR_WHITE)
            text_rect = text_surf.get_rect(center=rect.center)
            surface.blit(text_surf, text_rect)
