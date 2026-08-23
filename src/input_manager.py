"""
input_manager.py — Unified input system for keyboard + gamepad/controller + touch/click controls.
Renders on-screen touch buttons and maps all input methods to the same actions.

Gamepad button mapping (standard layout — works for Xbox, PlayStation, Logitech, etc.):
  Left Analog Stick / D-Pad  →  LEFT / RIGHT / UP movement
  Button 0 (A / Cross)       →  JUMP
  Button 1 (B / Circle)      →  BACK
  Button 2 (X / Square)      →  ACTION (interact/confirm)
  Button 3 (Y / Triangle)    →  ACTION (interact/confirm)
  Button 7 (Start)           →  ACTION (confirm menus)
  Button 6 (Back/Select)     →  BACK
  Button 8 (Guide/Home)      →  FULLSCREEN toggle
"""
import pygame
from settings import (
    TOUCH_BUTTON_SIZE, TOUCH_BUTTON_MARGIN, TOUCH_BUTTON_ALPHA,
    LOGICAL_WIDTH, LOGICAL_HEIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_SHADOW,
)

# ── Gamepad axis dead-zone: ignore tiny stick drift ───────────────────────────
AXIS_DEADZONE = 0.25


class InputManager:
    """Handles keyboard, USB gamepad/controller, and on-screen touch/click input."""

    # Action flags
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    JUMP = "jump"
    ACTION = "action"   # generic interact / confirm
    BACK = "back"       # ESC / cancel
    FULLSCREEN = "fullscreen"
    MENU_UP = "menu_up"
    MENU_DOWN = "menu_down"
    MENU_LEFT = "menu_left"
    MENU_RIGHT = "menu_right"
    MENU_SELECT = "menu_select"
    MENU_BACK = "menu_back"

    def __init__(self):
        self.actions = {
            self.LEFT: False,
            self.RIGHT: False,
            self.UP: False,
            self.JUMP: False,
            self.ACTION: False,
            self.BACK: False,
            self.FULLSCREEN: False,
            self.MENU_UP: False,
            self.MENU_DOWN: False,
            self.MENU_LEFT: False,
            self.MENU_RIGHT: False,
            self.MENU_SELECT: False,
            self.MENU_BACK: False,
        }
        # One-shot events (pressed THIS frame only)
        self.just_pressed = {key: False for key in self.actions}



        # Touch button rects (in logical coordinates)
        self._build_touch_buttons()

        # Track which buttons are being held by mouse/touch
        self._touch_held = {key: False for key in self.actions}

        # Scale and offset for mouse translation
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.mouse_x = 0.0
        self.mouse_y = 0.0

        # ── Gamepad / Controller setup ────────────────────────────────────────
        pygame.joystick.init()
        self.joysticks = {}   # device_index → Joystick object
        self.gamepad_name = None   # name of first connected controller (for HUD)
        self.custom_mappings = {}   # loaded from controller_map.json
        self._load_custom_mappings()
        self._init_joysticks()     # must come AFTER gamepad_name is defined
        self._validate_and_apply_mappings()  # only trust the map if it matches what's connected

    def _load_custom_mappings(self):
        """Loads custom controller bindings saved by assign_controller.py."""
        import os, json
        from settings import BASE_DIR, BUNDLED_DATA_DIR
        config_path = os.path.join(BASE_DIR, "data", "controller_map.json")
        if not os.path.exists(config_path):
            config_path = os.path.join(BUNDLED_DATA_DIR, "controller_map.json")

        self._pending_raw_map = None

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_map = data.get("mapping", {})
                    normalized = {}
                    for key, val in raw_map.items():
                        if isinstance(val, dict):
                            normalized[key] = [val]
                        elif isinstance(val, list):
                            normalized[key] = val
                    # Don't apply yet — stash until we know what controller is
                    # actually connected, so we can validate the layout matches.
                    self._pending_raw_map = normalized
                    saved_for = data.get("controller_name", "unknown")
                print(f"[InputManager] Found controller mapping file '{config_path}' "
                      f"(saved for: '{saved_for}')")
            except Exception as e:
                print(f"[InputManager] Could not load controller_map.json: {e}")

    def _validate_and_apply_mappings(self):
        """
        Called after joysticks are detected. Only trusts the loaded custom_mappings
        if the connected controller's physical button/axis/hat count matches what
        the mapping expects. Name is ignored, since the same physical controller
        can enumerate under different driver names (DirectInput vs XInput) on
        different Windows machines, depending on installed drivers.
        """
        if not self._pending_raw_map or not self.joysticks:
            return

        js = next(iter(self.joysticks.values()))
        connected_name = js.get_name()
        num_buttons = js.get_numbuttons()
        num_axes = js.get_numaxes()
        num_hats = js.get_numhats()

        # Capability check: every referenced index must exist on this device.
        max_button = max_axis = max_hat = -1
        for bindings in self._pending_raw_map.values():
            for b in bindings:
                if b.get("type") == "button":
                    max_button = max(max_button, b.get("index", -1))
                elif b.get("type") == "axis":
                    max_axis = max(max_axis, b.get("index", -1))
                elif b.get("type") == "hat":
                    max_hat = max(max_hat, b.get("index", 0))

        capability_ok = (
            max_button < num_buttons and
            max_axis < num_axes and
            max_hat < num_hats
        )

        if capability_ok:
            self.custom_mappings = self._pending_raw_map
            print(f"[InputManager] Applied custom mappings for '{connected_name}' "
                  f"({num_buttons} buttons, {num_axes} axes, {num_hats} hats).")
        else:
            self.custom_mappings = {}
            print(f"[InputManager] IGNORED custom mappings — connected controller "
                  f"'{connected_name}' lacks required indices. "
                  f"Expected: button ≤ {max_button}, axis ≤ {max_axis}, hat ≤ {max_hat}. "
                  f"Found: {num_buttons} buttons, {num_axes} axes, {num_hats} hats. "
                  f"Falling back to hardcoded defaults.")

    # ── Gamepad helpers ───────────────────────────────────────────────────────


    def _init_joysticks(self):
        """Detect and initialise all currently connected joysticks/gamepads."""
        count = pygame.joystick.get_count()
        for i in range(count):
            try:
                js = pygame.joystick.Joystick(i)
                js.init()
                self.joysticks[i] = js
                name = js.get_name()
                if self.gamepad_name is None:
                    self.gamepad_name = name
                print(f"[InputManager] Controller #{i} detected: '{name}' "
                      f"({js.get_numaxes()} axes, {js.get_numbuttons()} buttons, "
                      f"{js.get_numhats()} hats)")
            except Exception as e:
                print(f"[InputManager] Could not init joystick {i}: {e}")

    @property
    def has_gamepad(self):
        """True if at least one USB gamepad is connected and ready."""
        return len(self.joysticks) > 0

    def _check_mapping_active(self, action_key, event=None, is_hold=False):
        """
        Checks if any binding for action_key is active.
        If event is provided (JOYBUTTONDOWN/UP), checks against event.button.
        If is_hold=True, checks continuous joystick state (axes/hats/buttons).
        """
        bindings = self.custom_mappings.get(action_key, [])
        if not bindings:
            return False

        for js in self.joysticks.values():
            for m in bindings:
                m_type = m.get("type")
                if m_type == "button":
                    b_idx = m.get("index")
                    if event is not None and event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                        if event.button == b_idx:
                            return True
                    elif is_hold:
                        if b_idx < js.get_numbuttons() and js.get_button(b_idx):
                            return True

                elif m_type == "axis":
                    a_idx = m.get("index")
                    direction = m.get("direction", "positive")
                    thresh = m.get("threshold", 0.4)
                    if a_idx < js.get_numaxes():
                        val = js.get_axis(a_idx)
                        if direction == "positive" and val > thresh:
                            return True
                        elif direction == "negative" and val < -thresh:
                            return True

                elif m_type == "hat":
                    h_idx = m.get("index", 0)
                    target_val = m.get("value", [0, 0])
                    if h_idx < js.get_numhats():
                        hx, hy = js.get_hat(h_idx)
                        if (hx, hy) == tuple(target_val):
                            return True

        return False

    def _read_gamepad_axes(self):
        """
        Read custom bindings (or fallback to defaults) from all connected gamepads
        and merge into action flags (held state).
        """
        if self.custom_mappings:
            pad_left  = self._check_mapping_active("move_left", is_hold=True) or self._check_mapping_active("menu_left", is_hold=True)
            pad_right = self._check_mapping_active("move_right", is_hold=True) or self._check_mapping_active("menu_right", is_hold=True)
            pad_up    = (self._check_mapping_active("jump", is_hold=True) or 
                         self._check_mapping_active("fly_up", is_hold=True) or 
                         self._check_mapping_active("menu_up", is_hold=True))

            # Menu & movement action flags
            m_up = self._check_mapping_active("menu_up", is_hold=True) or self._check_mapping_active("fly_up", is_hold=True)
            m_down = self._check_mapping_active("menu_down", is_hold=True) or self._check_mapping_active("fly_down", is_hold=True)
            m_left = self._check_mapping_active("menu_left", is_hold=True)
            m_right = self._check_mapping_active("menu_right", is_hold=True)

            m_sel = self._check_mapping_active("menu_select", is_hold=True)
            m_back = self._check_mapping_active("menu_back", is_hold=True) or self._check_mapping_active("back", is_hold=True)

            # Trigger just_pressed when state shifts to True
            if m_up and not self.actions[self.MENU_UP]:
                self.just_pressed[self.MENU_UP] = True
            if m_down and not self.actions[self.MENU_DOWN]:
                self.just_pressed[self.MENU_DOWN] = True
            if m_left and not self.actions[self.MENU_LEFT]:
                self.just_pressed[self.MENU_LEFT] = True
            if m_right and not self.actions[self.MENU_RIGHT]:
                self.just_pressed[self.MENU_RIGHT] = True
            if m_sel and not self.actions[self.MENU_SELECT]:
                self.just_pressed[self.MENU_SELECT] = True
            if m_back and not self.actions[self.MENU_BACK]:
                self.just_pressed[self.MENU_BACK] = True

            self.actions[self.MENU_UP] = m_up
            self.actions[self.MENU_DOWN] = m_down
            self.actions[self.MENU_LEFT] = m_left
            self.actions[self.MENU_RIGHT] = m_right
            self.actions[self.MENU_SELECT] = m_sel
            self.actions[self.MENU_BACK] = m_back

            # Continuous action triggers via hats or analog axes
            if self._check_mapping_active("jump", is_hold=True):
                self.actions[self.JUMP] = True
            if self._check_mapping_active("action", is_hold=True) or m_sel:
                self.actions[self.ACTION] = True
            if m_back:
                self.actions[self.BACK] = True

            return pad_left, pad_right, pad_up


        # Default fallback if no custom map file present
        pad_left = pad_right = pad_up = False
        for js in self.joysticks.values():
            if js.get_numaxes() > 1:
                ax = js.get_axis(0)
                ay = js.get_axis(1)
                if ax < -AXIS_DEADZONE:
                    pad_left = True
                if ax > AXIS_DEADZONE:
                    pad_right = True
                if ay < -AXIS_DEADZONE:
                    pad_up = True

            if js.get_numhats() > 0:
                hx, hy = js.get_hat(0)
                if hx < 0:
                    pad_left = True
                if hx > 0:
                    pad_right = True
                if hy > 0:
                    pad_up = True

        return pad_left, pad_right, pad_up


    def _handle_gamepad_event(self, event):
        """
        Map JOYBUTTONDOWN / JOYBUTTONUP / JOYDEVICEADDED / JOYDEVICEREMOVED events.
        """
        if event.type == pygame.JOYDEVICEADDED:
            idx = event.device_index
            try:
                js = pygame.joystick.Joystick(idx)
                js.init()
                self.joysticks[idx] = js
                self.gamepad_name = js.get_name()
                print(f"[InputManager] Controller connected: '{js.get_name()}'")
                self._validate_and_apply_mappings()  # re-check saved map against this device
            except Exception as e:
                print(f"[InputManager] Hot-plug init error: {e}")

        elif event.type == pygame.JOYDEVICEREMOVED:
            idx = event.instance_id
            removed = self.joysticks.pop(idx, None)
            if removed:
                print(f"[InputManager] Controller disconnected: '{removed.get_name()}'")
            if not self.joysticks:
                self.gamepad_name = None

        elif event.type == pygame.JOYBUTTONDOWN:
            if self.custom_mappings:
                if self._check_mapping_active("jump", event=event):
                    self.just_pressed[self.JUMP] = True
                    self.actions[self.JUMP] = True
                if self._check_mapping_active("action", event=event) or self._check_mapping_active("menu_select", event=event):
                    self.just_pressed[self.ACTION] = True
                    self.just_pressed[self.MENU_SELECT] = True
                    self.actions[self.ACTION] = True
                    self.actions[self.MENU_SELECT] = True
                if self._check_mapping_active("back", event=event) or self._check_mapping_active("menu_back", event=event):
                    self.just_pressed[self.BACK] = True
                    self.just_pressed[self.MENU_BACK] = True
                    self.actions[self.BACK] = True
                    self.actions[self.MENU_BACK] = True
                if self._check_mapping_active("menu_up", event=event):
                    self.just_pressed[self.MENU_UP] = True
                    self.actions[self.MENU_UP] = True
                if self._check_mapping_active("menu_down", event=event):
                    self.just_pressed[self.MENU_DOWN] = True
                    self.actions[self.MENU_DOWN] = True
                if self._check_mapping_active("menu_left", event=event):
                    self.just_pressed[self.MENU_LEFT] = True
                    self.actions[self.MENU_LEFT] = True
                if self._check_mapping_active("menu_right", event=event):
                    self.just_pressed[self.MENU_RIGHT] = True
                    self.actions[self.MENU_RIGHT] = True
            else:
                btn = event.button
                if btn == 0:
                    self.just_pressed[self.JUMP] = True
                    self.actions[self.JUMP] = True
                elif btn in (2, 3, 7):
                    self.just_pressed[self.ACTION] = True
                    self.actions[self.ACTION] = True
                elif btn in (1, 6):
                    self.just_pressed[self.BACK] = True
                    self.just_pressed[self.MENU_BACK] = True
                    self.actions[self.BACK] = True
                    self.actions[self.MENU_BACK] = True
                elif btn == 8:
                    self.just_pressed[self.FULLSCREEN] = True
                    self.actions[self.FULLSCREEN] = True

        elif event.type == pygame.JOYBUTTONUP:
            if self.custom_mappings:
                if self._check_mapping_active("jump", event=event):
                    self.actions[self.JUMP] = False
                if self._check_mapping_active("action", event=event) or self._check_mapping_active("menu_select", event=event):
                    self.actions[self.ACTION] = False
                    self.actions[self.MENU_SELECT] = False
                if self._check_mapping_active("back", event=event) or self._check_mapping_active("menu_back", event=event):
                    self.actions[self.BACK] = False
                    self.actions[self.MENU_BACK] = False

                if self._check_mapping_active("menu_up", event=event):
                    self.actions[self.MENU_UP] = False
                if self._check_mapping_active("menu_down", event=event):
                    self.actions[self.MENU_DOWN] = False
                if self._check_mapping_active("menu_left", event=event):
                    self.actions[self.MENU_LEFT] = False
                if self._check_mapping_active("menu_right", event=event):
                    self.actions[self.MENU_RIGHT] = False
            else:
                btn = event.button
                if btn == 0:
                    self.actions[self.JUMP] = False
                elif btn in (2, 3, 7):
                    self.actions[self.ACTION] = False
                elif btn in (1, 6):
                    self.actions[self.BACK] = False



    # ── Touch buttons ─────────────────────────────────────────────────────────

    def _build_touch_buttons(self):
        """Define on-screen button positions — all in a single row at the very bottom."""
        s = TOUCH_BUTTON_SIZE
        m = TOUCH_BUTTON_MARGIN
        bottom = LOGICAL_HEIGHT - m - s

        # All buttons in one horizontal row at the bottom
        # Left side: ◄  ▲  ►
        self.touch_buttons = {
            self.LEFT:   pygame.Rect(m, bottom, s, s),
            self.UP:     pygame.Rect(m + s + m, bottom, s, s),
            self.RIGHT:  pygame.Rect(m + 2 * (s + m), bottom, s, s),
            # Right side: ACT  JUMP
            self.JUMP:   pygame.Rect(LOGICAL_WIDTH - m - s, bottom, s, s),
            self.ACTION:  pygame.Rect(LOGICAL_WIDTH - m - s - m - s, bottom, s, s),
        }

        # Labels for drawing
        self.touch_labels = {
            self.LEFT: "◄",
            self.RIGHT: "►",
            self.UP: "▲",
            self.JUMP: "JUMP",
            self.ACTION: "ACT",
        }

    # ── Main update ───────────────────────────────────────────────────────────

    def update(self, events, scale_x=1.0, scale_y=1.0, offset_x=0, offset_y=0):
        """
        Process one frame of input.
        scale_x/y and offset_x/y convert screen mouse coords → logical coords.
        """
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.offset_x = offset_x
        self.offset_y = offset_y

        # Track logical mouse position
        mx, my = pygame.mouse.get_pos()
        self.mouse_x = (mx - offset_x) / scale_x if scale_x != 0 else 0
        self.mouse_y = (my - offset_y) / scale_y if scale_y != 0 else 0

        # Reset one-shot events
        for key in self.just_pressed:
            self.just_pressed[key] = False

        # Reset per-frame flags
        self.actions[self.FULLSCREEN] = False

        # ── Keyboard ──────────────────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        self.actions[self.LEFT] = keys[pygame.K_LEFT] or keys[pygame.K_a]
        self.actions[self.RIGHT] = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.actions[self.UP] = keys[pygame.K_UP] or keys[pygame.K_w]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.just_pressed[self.JUMP] = True
                    self.actions[self.JUMP] = True
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.just_pressed[self.UP] = True
                    self.actions[self.UP] = True
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
                if event.key == pygame.K_SPACE:
                    self.actions[self.JUMP] = False
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.actions[self.UP] = False
                if event.key in (pygame.K_RETURN, pygame.K_e):
                    self.actions[self.ACTION] = False
                if event.key == pygame.K_ESCAPE:
                    self.actions[self.BACK] = False

            # ── Gamepad / Controller events ───────────────────────────────────
            if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP,
                               pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self._handle_gamepad_event(event)

            # ── Mouse / Touch ─────────────────────────────────────────────────
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                mx, my = self._get_logical_pos(event, scale_x, scale_y, offset_x, offset_y)
                for action_key, rect in self.touch_buttons.items():
                    if rect.collidepoint(mx, my):
                        self._touch_held[action_key] = True
                        self.actions[action_key] = True
                        self.just_pressed[action_key] = True

            if event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                for action_key in self._touch_held:
                    if self._touch_held[action_key]:
                        self._touch_held[action_key] = False

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

        # ── Gamepad analog / D-pad continuous hold state ──────────────────────
        pad_left, pad_right, pad_up = self._read_gamepad_axes()
        if pad_left:
            self.actions[self.LEFT] = True
        if pad_right:
            self.actions[self.RIGHT] = True
        if pad_up:
            self.actions[self.UP] = True

        # Merge touch holds into actions
        for action_key in self._touch_held:
            if self._touch_held[action_key]:
                self.actions[action_key] = True

    # ── Helpers ───────────────────────────────────────────────────────────────

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
        """Render premium dark glassmorphic on-screen buttons onto the logical surface."""
        for action_key, rect in self.touch_buttons.items():
            # Button background — dark glass with subtle warm tint
            btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            is_held = self._touch_held.get(action_key, False)
            if is_held:
                # Warm saffron glow when pressed
                bg_color = (180, 100, 20, TOUCH_BUTTON_ALPHA + 50)
                border_color = (255, 200, 80, TOUCH_BUTTON_ALPHA + 60)
            else:
                # Dark smoky glass at rest
                bg_color = (15, 12, 25, TOUCH_BUTTON_ALPHA)
                border_color = (120, 100, 70, TOUCH_BUTTON_ALPHA)
            pygame.draw.rect(btn_surf, bg_color, btn_surf.get_rect(), border_radius=10)
            pygame.draw.rect(btn_surf, border_color, btn_surf.get_rect(), width=2, border_radius=10)
            surface.blit(btn_surf, rect.topleft)

            # Label
            label_color = (255, 220, 140) if is_held else (200, 180, 140)
            if action_key in (self.LEFT, self.UP, self.RIGHT):
                # Draw high-quality custom vector arrows instead of relying on Unicode system fonts
                cx, cy = rect.centerx, rect.centery
                if action_key == self.LEFT:
                    points = [(cx - 10, cy), (cx + 8, cy - 10), (cx + 8, cy + 10)]
                elif action_key == self.UP:
                    points = [(cx, cy - 10), (cx - 10, cy + 8), (cx + 10, cy + 8)]
                else:  # RIGHT
                    points = [(cx + 10, cy), (cx - 8, cy - 10), (cx - 8, cy + 10)]
                pygame.draw.polygon(surface, label_color, points)
            else:
                label = self.touch_labels.get(action_key, "?")
                text_surf = font.render(label, True, label_color)
                text_rect = text_surf.get_rect(center=rect.center)
                surface.blit(text_surf, text_rect)
