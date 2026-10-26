"""In-game controller rebinding (2026-10-25).

The Controller Buttons screen (reached from Game Options) lets a player choose
which pad button does each of seven actions. These tests cover the parts that
can be checked without a pad in hand:

* ``InputManager.capture_binding`` turns a raw press into the same binding dict
  that ``tools/assign_controller.py`` writes, and ignores stick noise.
* ``InputManager.capture_mode`` mutes pad dispatch while listening, so pressing B
  to bind it does not also fire BACK and leave the screen. The keyboard stays
  live so Esc can still cancel.
* The seven on-screen actions expand to the thirteen keys of the map file.
* ``ProfileManager.save_controller_map`` writes what ``InputManager`` reads back.
* The scene never touches raw joystick events itself (architecture invariant).

Like ``test_input_bindings``, the manager is loaded through ``runpy`` with a stub
``pygame`` so this runs on a headless CI worker with no display and no pygame.
"""

from __future__ import annotations

import json
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

_KEY_NAMES = (
    "K_SPACE", "K_UP", "K_DOWN", "K_LEFT", "K_RIGHT",
    "K_w", "K_s", "K_a", "K_d", "K_RETURN", "K_e", "K_ESCAPE", "K_F11", "K_f",
)
_EVENT_NAMES = (
    "KEYDOWN", "KEYUP", "JOYBUTTONDOWN", "JOYBUTTONUP", "JOYDEVICEADDED",
    "JOYDEVICEREMOVED", "JOYAXISMOTION", "JOYHATMOTION", "MOUSEBUTTONDOWN",
    "MOUSEBUTTONUP", "MOUSEMOTION", "FINGERDOWN", "FINGERUP",
)


class _NoKeys:
    def __getitem__(self, key):
        return False


def _fake_pygame():
    fake = types.ModuleType("pygame")
    for index, name in enumerate(_KEY_NAMES):
        setattr(fake, name, 1000 + index)
    for index, name in enumerate(_EVENT_NAMES):
        setattr(fake, name, 2000 + index)
    fake.KMOD_CTRL = 1
    fake.KMOD_META = 2
    fake.key = types.SimpleNamespace(get_pressed=lambda: _NoKeys())
    fake.mouse = types.SimpleNamespace(
        get_pos=lambda: (0, 0), get_pressed=lambda: (False, False, False),
    )
    fake.joystick = types.SimpleNamespace(
        get_count=lambda: 0, init=lambda: None, Joystick=lambda index: None,
    )
    return fake


def _fake_settings(base_dir):
    fake = types.ModuleType("settings")
    fake.TOUCH_BUTTON_SIZE = 64
    fake.TOUCH_BUTTON_MARGIN = 8
    fake.TOUCH_BUTTON_ALPHA = 100
    fake.LOGICAL_WIDTH = 1920
    fake.LOGICAL_HEIGHT = 1080
    fake.COLOR_WHITE = (255, 255, 255)
    fake.COLOR_GOLD = (235, 180, 50)
    fake.COLOR_SHADOW = (0, 0, 0, 128)
    fake.BASE_DIR = str(base_dir)
    fake.BUNDLED_DATA_DIR = str(ROOT / "does-not-exist")
    return fake


def _load_manager(base_dir=ROOT / "does-not-exist"):
    """Return (bare InputManager instance, module namespace, fake pygame)."""
    fake_pygame = _fake_pygame()
    with mock.patch.dict(
        sys.modules, {"pygame": fake_pygame, "settings": _fake_settings(base_dir)}
    ):
        namespace = runpy.run_path(str(SRC / "input_manager.py"))
    cls = namespace["InputManager"]
    manager = cls.__new__(cls)
    action_keys = [
        getattr(cls, n) for n in (
            "LEFT", "RIGHT", "UP", "JUMP", "ACTION", "BACK", "FULLSCREEN",
            "MENU_UP", "MENU_DOWN", "MENU_LEFT", "MENU_RIGHT", "MENU_SELECT", "MENU_BACK",
        )
    ]
    manager.actions = {k: False for k in action_keys}
    manager.just_pressed = {k: False for k in action_keys}
    manager._touch_held = {k: False for k in action_keys}
    manager._nav_cooldown = {k: 0.0 for k in action_keys}
    manager.custom_mappings = {}
    manager._pending_raw_map = None
    manager.joysticks = {}
    manager.touch_buttons = {}
    manager.gamepad_name = ""
    manager.capture_mode = False
    # The module keeps its own reference to the stub, so update() can run after
    # the patch has been lifted.
    return manager, namespace, fake_pygame


class CaptureBindingTests(unittest.TestCase):
    def test_button_press_becomes_button_binding(self):
        manager, _, pg = _load_manager()
        ev = types.SimpleNamespace(type=pg.JOYBUTTONDOWN, button=3)
        self.assertEqual(manager.capture_binding([ev]), {"type": "button", "index": 3})

    def test_small_stick_drift_is_ignored_but_a_real_push_is_taken(self):
        manager, _, pg = _load_manager()
        drift = types.SimpleNamespace(type=pg.JOYAXISMOTION, axis=1, value=0.2)
        self.assertIsNone(manager.capture_binding([drift]))
        push = types.SimpleNamespace(type=pg.JOYAXISMOTION, axis=1, value=-0.9)
        self.assertEqual(
            manager.capture_binding([push]),
            {"type": "axis", "index": 1, "direction": "negative", "threshold": 0.5},
        )

    def test_hat_release_is_ignored_but_a_direction_is_taken(self):
        manager, _, pg = _load_manager()
        centre = types.SimpleNamespace(type=pg.JOYHATMOTION, hat=0, value=(0, 0))
        self.assertIsNone(manager.capture_binding([centre]))
        up = types.SimpleNamespace(type=pg.JOYHATMOTION, hat=0, value=(0, 1))
        self.assertEqual(manager.capture_binding([up]), {"type": "hat", "index": 0, "value": [0, 1]})

    def test_keyboard_is_never_captured(self):
        """Gamepad only — keyboard bindings are not rebindable in this release."""
        manager, _, pg = _load_manager()
        ev = types.SimpleNamespace(type=pg.KEYDOWN, key=pg.K_SPACE, mod=0)
        self.assertIsNone(manager.capture_binding([ev]))


class CaptureModeTests(unittest.TestCase):
    def _press_a(self, manager, pg):
        ev = types.SimpleNamespace(type=pg.JOYBUTTONDOWN, button=0, instance_id=0)
        with mock.patch("builtins.print"):
            manager.update([ev])

    def test_pad_fires_normally_when_not_listening(self):
        manager, ns, pg = _load_manager()
        self._press_a(manager, pg)
        self.assertTrue(manager.just_pressed[ns["InputManager"].JUMP])

    def test_pad_is_muted_while_listening(self):
        """Binding B must not also fire BACK and throw the player off the screen."""
        manager, ns, pg = _load_manager()
        manager.capture_mode = True
        self._press_a(manager, pg)
        cls = ns["InputManager"]
        self.assertFalse(manager.just_pressed[cls.JUMP])
        self.assertFalse(manager.just_pressed[cls.MENU_SELECT])

    def test_keyboard_still_works_while_listening(self):
        """Esc must still cancel a rebind."""
        manager, ns, pg = _load_manager()
        manager.capture_mode = True
        ev = types.SimpleNamespace(type=pg.KEYDOWN, key=pg.K_ESCAPE, mod=0)
        with mock.patch("builtins.print"):
            manager.update([ev])
        self.assertTrue(manager.just_pressed[ns["InputManager"].BACK])


class MapShapeTests(unittest.TestCase):
    def test_seven_actions_expand_to_the_menu_keys(self):
        _, ns, _ = _load_manager()
        cls = ns["InputManager"]
        a = {"type": "button", "index": 7}
        left = {"type": "hat", "index": 0, "value": [-1, 0]}
        full = cls.expand_player_bindings({"action": [a], "move_left": [left]})
        self.assertEqual(full["action"], [a])
        self.assertEqual(full["menu_select"], [a])
        self.assertEqual(full["move_left"], [left])
        self.assertEqual(full["menu_left"], [left])
        self.assertNotIn("jump", full, "unbound actions stay on the built-in layout")

    def test_every_on_screen_action_is_a_key_the_manager_reads(self):
        """The screen's rows must be the same vocabulary the loader understands."""
        _, ns, _ = _load_manager()
        source = (SRC / "input_manager.py").read_text(encoding="utf-8")
        for key, _label, mirrors in ns["GAMEPAD_BIND_ACTIONS"]:
            for k in (key, *mirrors):
                self.assertIn(f'"{k}"', source)

    def test_opposing_directions_sharing_an_input_are_flagged(self):
        _, ns, _ = _load_manager()
        cls = ns["InputManager"]
        b = {"type": "button", "index": 4}
        self.assertEqual(
            cls.find_opposing_conflicts({"move_left": [b], "move_right": [b]}),
            [("move_left", "move_right")],
        )
        self.assertEqual(cls.find_opposing_conflicts({"jump": [b], "action": [b]}), [])

    def test_describe_binding_names_dpad_directions(self):
        _, ns, _ = _load_manager()
        cls = ns["InputManager"]
        self.assertEqual(cls.describe_binding([{"type": "hat", "index": 0, "value": [0, -1]}]), "D-pad Down")
        self.assertEqual(cls.describe_binding([{"type": "button", "index": 2}]), "Button 2")
        self.assertEqual(cls.describe_binding([]), "")


class PersistenceTests(unittest.TestCase):
    def test_saved_map_is_what_the_manager_loads_next_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_settings = _fake_settings(tmp)
            with mock.patch.dict(sys.modules, {"settings": fake_settings}):
                pm_ns = runpy.run_path(str(SRC / "profile_manager.py"))
            pm = pm_ns["ProfileManager"]()
            mapping = {"jump": [{"type": "button", "index": 9}],
                       "action": [{"type": "button", "index": 1}],
                       "menu_select": [{"type": "button", "index": 1}]}
            path = pm.save_controller_map("Test Pad", mapping)
            self.assertIsNotNone(path)
            self.assertEqual(Path(path), Path(tmp) / "data" / "controller_map.json")
            with open(path, encoding="utf-8") as f:
                on_disk = json.load(f)
            self.assertEqual(on_disk["mapping"], mapping)
            self.assertEqual(on_disk["controller_name"], "Test Pad")

            manager, _, _ = _load_manager(base_dir=tmp)
            # The loader imports settings lazily, so the stub must be live here too.
            with mock.patch.dict(sys.modules, {"settings": fake_settings}),                     mock.patch("builtins.print"):
                manager._load_custom_mappings()
            self.assertEqual(manager._pending_raw_map, mapping)

    def test_apply_mappings_with_no_pad_waits_for_one(self):
        """Nothing to validate against yet; the map is stashed, not dropped."""
        manager, _, _ = _load_manager()
        manager.custom_mappings = {"jump": [{"type": "button", "index": 0}]}
        with mock.patch("builtins.print"):
            manager.apply_mappings({"jump": {"type": "button", "index": 5}})
        self.assertEqual(manager.custom_mappings, {})
        self.assertEqual(manager._pending_raw_map, {"jump": [{"type": "button", "index": 5}]})


class WiringTests(unittest.TestCase):
    def test_scene_reads_no_raw_joystick_input(self):
        """Scenes read abstract actions; InputManager is the only reader of the pad."""
        source = (SRC / "controller_settings_scene.py").read_text(encoding="utf-8")
        for token in ("JOYBUTTON", "JOYAXIS", "JOYHAT", "get_button(", "get_axis(", "get_hat(", "joystick"):
            self.assertNotIn(token, source, f"{token!r} belongs in input_manager.py")

    def test_scene_is_registered_and_reachable_from_options(self):
        self.assertIn('SCENE_CONTROLS = "controls"', (SRC / "settings.py").read_text(encoding="utf-8"))
        main_src = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("register(SCENE_CONTROLS, ControllerSettingsScene(", main_src)
        options_src = (SRC / "options_scene.py").read_text(encoding="utf-8")
        self.assertIn("switch_to(SCENE_CONTROLS", options_src)

    def test_scene_releases_capture_mode_on_exit(self):
        """A muted pad must never leak into the next scene."""
        source = (SRC / "controller_settings_scene.py").read_text(encoding="utf-8")
        exit_body = source.split("def on_exit(self):", 1)[1].split("def ", 1)[0]
        self.assertIn("_stop_listening()", exit_body)


if __name__ == "__main__":
    unittest.main()
