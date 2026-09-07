"""Keyboard binding tests for InputManager.

These guard the fix for the barrier that made the game effectively unplayable
for anyone on a keyboard: every MENU_* action used to be written only by the
gamepad code paths, so the title-screen highlight could not move off index 0 and
Options — and therefore the tutorial and the fullscreen toggle — were
unreachable without a gamepad or a mouse.

Like ``test_portability``, this loads ``input_manager.py`` through ``runpy`` with
a stub ``pygame`` so it runs on a headless CI worker with no display and no
pygame installed.
"""

from __future__ import annotations

from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Arbitrary distinct ints standing in for pygame's key/event constants.
_KEY_NAMES = (
    "K_SPACE", "K_UP", "K_DOWN", "K_LEFT", "K_RIGHT",
    "K_w", "K_s", "K_a", "K_d", "K_RETURN", "K_e", "K_ESCAPE", "K_F11", "K_f",
)
_EVENT_NAMES = (
    "KEYDOWN", "KEYUP", "JOYBUTTONDOWN", "JOYBUTTONUP", "JOYDEVICEADDED",
    "JOYDEVICEREMOVED", "JOYAXISMOTION", "JOYHATMOTION", "MOUSEBUTTONDOWN",
    "MOUSEBUTTONUP", "MOUSEMOTION", "FINGERDOWN", "FINGERUP",
)


class _FakeKeyState:
    """Stands in for the sequence returned by ``pygame.key.get_pressed()``."""

    def __init__(self, held=()):
        self._held = set(held)

    def __getitem__(self, key):
        return key in self._held


def _make_fake_pygame(held_keys=()):
    fake = types.ModuleType("pygame")
    for index, name in enumerate(_KEY_NAMES):
        setattr(fake, name, 1000 + index)
    for index, name in enumerate(_EVENT_NAMES):
        setattr(fake, name, 2000 + index)
    fake.KMOD_CTRL = 1
    fake.KMOD_META = 2

    fake.key = types.SimpleNamespace(
        get_pressed=lambda: _FakeKeyState(held_keys),
    )
    fake.mouse = types.SimpleNamespace(
        get_pos=lambda: (0, 0),
        get_pressed=lambda: (False, False, False),
    )
    fake.joystick = types.SimpleNamespace(
        get_count=lambda: 0,
        init=lambda: None,
        Joystick=lambda index: None,
    )
    return fake


def _make_fake_settings():
    fake = types.ModuleType("settings")
    fake.TOUCH_BUTTON_SIZE = 64
    fake.TOUCH_BUTTON_MARGIN = 8
    fake.TOUCH_BUTTON_ALPHA = 100
    fake.LOGICAL_WIDTH = 1920
    fake.LOGICAL_HEIGHT = 1080
    fake.COLOR_WHITE = (255, 255, 255)
    fake.COLOR_GOLD = (235, 180, 50)
    fake.COLOR_SHADOW = (0, 0, 0, 128)
    fake.BASE_DIR = str(ROOT / "does-not-exist")
    fake.BUNDLED_DATA_DIR = str(ROOT / "does-not-exist")
    return fake


class KeyboardBindingTests(unittest.TestCase):
    def _drive(self, pressed_key, held_keys=()):
        """Feed one KEYDOWN through update() and return the manager."""
        fake_pygame = _make_fake_pygame(held_keys)
        fake_settings = _make_fake_settings()
        with mock.patch.dict(
            sys.modules, {"pygame": fake_pygame, "settings": fake_settings}
        ):
            namespace = runpy.run_path(str(SRC / "input_manager.py"))
            manager_class = namespace["InputManager"]

            manager = manager_class.__new__(manager_class)
            manager.actions = {key: False for key in _ACTION_KEYS(manager_class)}
            manager.just_pressed = {key: False for key in manager.actions}
            manager._touch_held = {key: False for key in manager.actions}
            manager._nav_cooldown = {key: 0.0 for key in manager.actions}
            manager.custom_mappings = {}
            manager.joysticks = {}
            manager.touch_buttons = {}
            manager.gamepad_name = ""

            event = types.SimpleNamespace(
                type=fake_pygame.KEYDOWN, key=pressed_key, mod=0
            )
            with mock.patch("builtins.print"):
                manager.update([event])
            return manager, manager_class, fake_pygame

    def test_arrow_keys_drive_menu_navigation(self):
        """The regression that froze every menu for keyboard-only players."""
        for key_name, action_name in (
            ("K_UP", "MENU_UP"),
            ("K_DOWN", "MENU_DOWN"),
            ("K_LEFT", "MENU_LEFT"),
            ("K_RIGHT", "MENU_RIGHT"),
            ("K_RETURN", "MENU_SELECT"),
            ("K_ESCAPE", "MENU_BACK"),
        ):
            with self.subTest(key=key_name, action=action_name):
                probe = _make_fake_pygame()
                manager, manager_class, _ = self._drive(getattr(probe, key_name))
                action = getattr(manager_class, action_name)
                self.assertTrue(
                    manager.just_pressed[action],
                    f"{key_name} must raise {action_name} on a keyboard; "
                    "without it the title screen cannot be navigated at all",
                )

    def test_wasd_also_drives_menu_navigation(self):
        for key_name, action_name in (
            ("K_w", "MENU_UP"),
            ("K_s", "MENU_DOWN"),
            ("K_a", "MENU_LEFT"),
            ("K_d", "MENU_RIGHT"),
        ):
            with self.subTest(key=key_name, action=action_name):
                probe = _make_fake_pygame()
                manager, manager_class, _ = self._drive(getattr(probe, key_name))
                action = getattr(manager_class, action_name)
                self.assertTrue(manager.just_pressed[action])

    def test_up_arrow_jumps(self):
        """The Controls tab has always promised 'SPACE / UP -> Jump'."""
        for key_name in ("K_UP", "K_w"):
            with self.subTest(key=key_name):
                probe = _make_fake_pygame()
                manager, manager_class, _ = self._drive(getattr(probe, key_name))
                self.assertTrue(
                    manager.just_pressed[manager_class.JUMP],
                    f"{key_name} must jump — the in-game tutorial says it does",
                )

    def test_space_still_jumps(self):
        probe = _make_fake_pygame()
        manager, manager_class, _ = self._drive(probe.K_SPACE)
        self.assertTrue(manager.just_pressed[manager_class.JUMP])

    def test_space_does_not_select_menu_items(self):
        """Space must not confirm.

        In the monk dialogue SPACE is JUMP; if it also raised MENU_SELECT it
        would move the highlight and submit in the same frame.
        """
        probe = _make_fake_pygame()
        manager, manager_class, _ = self._drive(probe.K_SPACE)
        self.assertFalse(
            manager.just_pressed[manager_class.MENU_SELECT],
            "SPACE must not raise MENU_SELECT",
        )

    def test_releasing_up_keeps_jump_held_while_space_is_down(self):
        """Level-2 flight holds a jump key continuously."""
        fake_pygame = _make_fake_pygame(held_keys=(1001,))  # K_UP index
        fake_pygame.key.get_pressed = lambda: _FakeKeyState({fake_pygame.K_SPACE})
        fake_settings = _make_fake_settings()
        with mock.patch.dict(
            sys.modules, {"pygame": fake_pygame, "settings": fake_settings}
        ):
            namespace = runpy.run_path(str(SRC / "input_manager.py"))
            manager_class = namespace["InputManager"]
            manager = manager_class.__new__(manager_class)
            manager.actions = {key: False for key in _ACTION_KEYS(manager_class)}
            manager.just_pressed = {key: False for key in manager.actions}
            manager._touch_held = {key: False for key in manager.actions}
            manager._nav_cooldown = {key: 0.0 for key in manager.actions}
            manager.custom_mappings = {}
            manager.joysticks = {}
            manager.touch_buttons = {}
            manager.gamepad_name = ""
            manager.actions[manager_class.JUMP] = True

            release_up = types.SimpleNamespace(
                type=fake_pygame.KEYUP, key=fake_pygame.K_UP, mod=0
            )
            with mock.patch("builtins.print"):
                manager.update([release_up])

            self.assertTrue(
                manager.actions[manager_class.JUMP],
                "Releasing UP while SPACE is held must not drop JUMP — that "
                "would stutter flight",
            )


def _ACTION_KEYS(manager_class):
    return (
        manager_class.LEFT, manager_class.RIGHT, manager_class.UP,
        manager_class.JUMP, manager_class.ACTION, manager_class.BACK,
        manager_class.FULLSCREEN, manager_class.MENU_UP,
        manager_class.MENU_DOWN, manager_class.MENU_LEFT,
        manager_class.MENU_RIGHT, manager_class.MENU_SELECT,
        manager_class.MENU_BACK,
    )


if __name__ == "__main__":
    unittest.main()
