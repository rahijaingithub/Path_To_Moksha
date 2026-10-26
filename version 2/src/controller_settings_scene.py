"""
controller_settings_scene.py — Controller Buttons screen, reached from Game Options.
Lets the player choose which pad button, stick direction or D-pad direction does
each of the seven player-facing actions, then saves the map so it is used right
away and on the next launch.

The scene never reads raw pad events. InputManager.capture_binding()
turns a press into a binding dict, and InputManager.capture_mode keeps that press
from also firing its current action while we are listening.
"""
import pygame
from scene_manager import Scene
from input_manager import InputManager, GAMEPAD_BIND_ACTIONS
from profile_manager import ProfileManager
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCENE_OPTIONS,
    COLOR_BG_DARK, COLOR_GOLD, COLOR_GOLD_BRIGHT, COLOR_GOLD_DIM,
    COLOR_WHITE, COLOR_SAFFRON,
    GAME_FONT_SIZE_TITLE, GAME_FONT_SIZE_BODY, GAME_FONT_SIZE_SMALL,
)

LISTEN_SECONDS = 6.0
# What the built-in SDL layout does when no custom map is saved (see the
# module docstring of input_manager.py).
DEFAULT_LABELS = {
    "move_left": "Stick / D-pad Left",
    "move_right": "Stick / D-pad Right",
    "jump": "Button 0 (A)",
    "fly_up": "Stick / D-pad Up",
    "fly_down": "Stick / D-pad Down",
    "action": "Button 2 / 3 (X, Y)",
    "back": "Button 1 (B)",
}
ROW_RESET = len(GAMEPAD_BIND_ACTIONS)       # index of "Reset to Defaults"
ROW_SAVE = ROW_RESET + 1                    # index of "Save & Return"
ROW_COUNT = ROW_SAVE + 1


class ControllerSettingsScene(Scene):
    """Rebind the gamepad, one action at a time."""

    def __init__(self, manager, assets, input_mgr):
        super().__init__(manager)
        self.assets = assets
        self.input_mgr = input_mgr
        self.elapsed = 0.0

        self.action_rects = []
        y = 290
        for _ in GAMEPAD_BIND_ACTIONS:
            self.action_rects.append(pygame.Rect(LOGICAL_WIDTH // 2 - 420, y, 840, 56))
            y += 66
        self.reset_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 430, 850, 400, 64)
        self.save_rect = pygame.Rect(LOGICAL_WIDTH // 2 + 30, 850, 400, 64)

        self.selected_index = 0
        self.working = {}          # action key -> list of binding dicts (the 7 keys only)
        self.listening_key = None  # action key being rebound, or None
        self.listen_timer = 0.0
        self.message = ""
        self.message_timer = 0.0
        self.bg = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self, **kwargs):
        self.elapsed = 0.0
        self.selected_index = 0
        self._stop_listening()
        self.message = ""
        self.message_timer = 0.0
        # Start from what the pad is actually using right now.
        self.working = {
            key: list(self.input_mgr.custom_mappings[key])
            for key, _l, _m in GAMEPAD_BIND_ACTIONS
            if self.input_mgr.custom_mappings.get(key)
        }

        self.bg = self.assets.load_image(
            "title_background.png", "backgrounds",
            alpha=False, scale=(LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )
        self.font_title = self.assets.load_font(None, GAME_FONT_SIZE_TITLE)
        self.font_body = self.assets.load_font(None, GAME_FONT_SIZE_BODY)
        self.font_small = self.assets.load_font(None, GAME_FONT_SIZE_SMALL)

    def on_exit(self):
        # Never leave the pad muted for the next scene.
        self._stop_listening()

    # ── Listening ─────────────────────────────────────────────────────────────

    def _start_listening(self, key):
        if not self.input_mgr.has_gamepad:
            self._say("Connect a controller to change its buttons.")
            return
        self.listening_key = key
        self.listen_timer = LISTEN_SECONDS
        self.input_mgr.capture_mode = True
        self.assets.play_sound("jump.wav", volume=0.15)

    def _stop_listening(self):
        self.listening_key = None
        self.listen_timer = 0.0
        self.input_mgr.capture_mode = False

    def _say(self, text, seconds=3.0):
        self.message = text
        self.message_timer = seconds

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_events(self, events, input_mgr):
        if self.listening_key is not None:
            # Pad events are muted by capture_mode, so BACK here is Esc or a touch.
            if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
                self._stop_listening()
                return
            binding = input_mgr.capture_binding(events)
            if binding is not None:
                self.working[self.listening_key] = [binding]
                self.assets.play_sound("box_open.wav", volume=0.2)
                self._stop_listening()
            return

        if input_mgr.just_pressed[input_mgr.BACK] or input_mgr.just_pressed[input_mgr.MENU_BACK]:
            self._save_and_exit()
            return

        if input_mgr.just_pressed[input_mgr.MENU_UP] or input_mgr.just_pressed[input_mgr.UP]:
            self.selected_index = (self.selected_index - 1) % ROW_COUNT
            self.assets.play_sound("jump.wav", volume=0.15)
        elif input_mgr.just_pressed[input_mgr.MENU_DOWN]:
            self.selected_index = (self.selected_index + 1) % ROW_COUNT
            self.assets.play_sound("jump.wav", volume=0.15)
        elif input_mgr.just_pressed[input_mgr.MENU_LEFT] or input_mgr.just_pressed[input_mgr.MENU_RIGHT]:
            # The two footer buttons sit side by side.
            if self.selected_index == ROW_RESET:
                self.selected_index = ROW_SAVE
            elif self.selected_index == ROW_SAVE:
                self.selected_index = ROW_RESET

        is_select = input_mgr.just_pressed[input_mgr.ACTION] or input_mgr.just_pressed[input_mgr.MENU_SELECT]
        if is_select:
            self._activate(self.selected_index)

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                idx = self._row_at(input_mgr.mouse_x, input_mgr.mouse_y)
                if idx is not None:
                    self.selected_index = idx
            elif event.type == pygame.MOUSEBUTTONDOWN:
                idx = self._row_at(input_mgr.mouse_x, input_mgr.mouse_y)
                if idx is not None:
                    self.selected_index = idx
                    self._activate(idx)

    def _row_at(self, mx, my):
        for i, rect in enumerate(self.action_rects):
            if rect.collidepoint(mx, my):
                return i
        if self.reset_rect.collidepoint(mx, my):
            return ROW_RESET
        if self.save_rect.collidepoint(mx, my):
            return ROW_SAVE
        return None

    def _activate(self, idx):
        if idx < len(GAMEPAD_BIND_ACTIONS):
            self._start_listening(GAMEPAD_BIND_ACTIONS[idx][0])
        elif idx == ROW_RESET:
            self.working = {}
            self.assets.play_sound("jump.wav", volume=0.15)
            self._say("Back to the built-in layout. Save to keep it.")
        elif idx == ROW_SAVE:
            self.assets.play_sound("box_open.wav", volume=0.2)
            self._save_and_exit()

    def _save_and_exit(self):
        full_map = InputManager.expand_player_bindings(self.working)
        ProfileManager().save_controller_map(self.input_mgr.gamepad_name, full_map)
        self.input_mgr.apply_mappings(full_map)
        self.manager.switch_to(SCENE_OPTIONS, input_mgr=self.input_mgr)

    # ── Frame ─────────────────────────────────────────────────────────────────

    def update(self, dt):
        self.elapsed += dt
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0:
                self.message = ""
        if self.listening_key is not None:
            self.listen_timer -= dt
            if self.listen_timer <= 0:
                self._stop_listening()

    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))
        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 18, 32, 220))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("CONTROLLER BUTTONS", True, COLOR_GOLD_BRIGHT)
        surface.blit(title, title.get_rect(center=(LOGICAL_WIDTH // 2, 130)))

        if self.input_mgr.has_gamepad:
            sub = f"🎮 {self.input_mgr.gamepad_name}  —  pick an action, then press the button you want"
            sub_col = COLOR_WHITE
        else:
            sub = "⌨ No controller connected — connect one to change its buttons"
            sub_col = COLOR_GOLD_DIM
        sub_s = self.font_small.render(sub, True, sub_col)
        surface.blit(sub_s, sub_s.get_rect(center=(LOGICAL_WIDTH // 2, 210)))

        conflicts = InputManager.find_opposing_conflicts(self.working)
        conflict_keys = {k for pair in conflicts for k in pair}

        for i, (key, label, _mirrors) in enumerate(GAMEPAD_BIND_ACTIONS):
            rect = self.action_rects[i]
            hover = (self.selected_index == i)
            listening = (self.listening_key == key)
            if listening:
                bg_col, border_col = COLOR_SAFFRON, COLOR_GOLD_BRIGHT
            elif hover:
                bg_col, border_col = COLOR_GOLD, COLOR_GOLD_BRIGHT
            else:
                bg_col, border_col = COLOR_BG_DARK, COLOR_GOLD_DIM
            btn = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(btn, (*bg_col[:3], 230), btn.get_rect(), border_radius=10)
            pygame.draw.rect(btn, border_col, btn.get_rect(), width=2 if hover else 1, border_radius=10)
            surface.blit(btn, rect)

            text_col = COLOR_BG_DARK if (hover or listening) else COLOR_WHITE
            name_s = self.font_body.render(label, True, text_col)
            surface.blit(name_s, name_s.get_rect(midleft=(rect.left + 24, rect.centery)))

            if listening:
                value = f"Press a button... {int(self.listen_timer) + 1}"
            elif self.working.get(key):
                value = InputManager.describe_binding(self.working[key])
            else:
                value = f"Default: {DEFAULT_LABELS.get(key, '')}"
            if key in conflict_keys and not listening:
                value = "⚠ " + value
            val_s = self.font_body.render(value, True, text_col)
            surface.blit(val_s, val_s.get_rect(midright=(rect.right - 24, rect.centery)))

        # Guidance line: conflict warning, a transient message, or the standing hint.
        if conflicts:
            a, b = conflicts[0]
            names = {k: l for k, l, _m in GAMEPAD_BIND_ACTIONS}
            note = f"⚠ {names[a]} and {names[b]} share one input — the player could not move. Pick again."
            note_col = COLOR_SAFFRON
        elif self.message:
            note, note_col = self.message, COLOR_GOLD_BRIGHT
        elif self.listening_key is not None:
            note, note_col = "Esc cancels.  Each action takes the last button you pressed.", COLOR_WHITE
        else:
            note, note_col = "Back saves and returns.  Keyboard controls never change.", COLOR_GOLD_DIM
        note_s = self.font_small.render(note, True, note_col)
        surface.blit(note_s, note_s.get_rect(center=(LOGICAL_WIDTH // 2, 790)))

        for rect, idx, text in (
            (self.reset_rect, ROW_RESET, "Reset to Defaults"),
            (self.save_rect, ROW_SAVE, "Save & Return"),
        ):
            hover = (self.selected_index == idx)
            bg_col = COLOR_GOLD if hover else COLOR_SAFFRON
            border_col = COLOR_GOLD_BRIGHT if hover else COLOR_GOLD
            btn = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(btn, (*bg_col[:3], 240), btn.get_rect(), border_radius=12)
            pygame.draw.rect(btn, border_col, btn.get_rect(), width=3, border_radius=12)
            surface.blit(btn, rect)
            txt = self.font_body.render(text, True, COLOR_BG_DARK if hover else COLOR_WHITE)
            surface.blit(txt, txt.get_rect(center=rect.center))
