"""Typing a name and pressing Enter (2026-10-26).

Enter raised ACTION as well as arriving as a KEYDOWN, and the name screen acted on
both: the on-screen keyboard pressed whichever key was highlighted, *then* the raw
handler confirmed. So "Karuna" was saved as "KarunaA" — and with the highlight on
OK it confirmed twice, the second pass finding the profile it had just written and
launching straight into the level, leaving the character as the default boy.

Enter now means one thing per focus. A pad's confirm still types on the on-screen
keyboard, because that is the only way a pad can enter a name at all.

Needs pygame; skipped on the dependency-free CI worker.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class StubInput:
    LEFT, RIGHT, UP = "left", "right", "up"
    JUMP, ACTION, BACK = "jump", "action", "back"
    MENU_UP, MENU_DOWN, MENU_LEFT, MENU_RIGHT = "menu_up", "menu_down", "menu_left", "menu_right"
    MENU_SELECT, MENU_BACK = "menu_select", "menu_back"
    FULLSCREEN = "fullscreen"

    def __init__(self):
        keys = (self.LEFT, self.RIGHT, self.UP, self.JUMP, self.ACTION, self.BACK,
                self.MENU_UP, self.MENU_DOWN, self.MENU_LEFT, self.MENU_RIGHT,
                self.MENU_SELECT, self.MENU_BACK, self.FULLSCREEN)
        self.actions = {k: False for k in keys}
        self.just_pressed = {k: False for k in keys}
        self.mouse_x = self.mouse_y = -500

    def tap(self, *keys):
        for k in self.just_pressed:
            self.just_pressed[k] = False
        for k in keys:
            self.just_pressed[k] = True


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class NameEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import player_select_scene
        import settings
        from asset_manager import AssetManager
        from scene_manager import SceneManager

        class RecordingManager(SceneManager):
            def __init__(self):
                super().__init__()
                self.switches = []

            def switch_to(self, key, input_mgr=None, **kwargs):
                self.switches.append((key, kwargs))

        cls.pygame = pygame
        cls.settings = settings
        cls.pss = player_select_scene
        cls.RecordingManager = RecordingManager
        cls.assets = AssetManager()

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def setUp(self) -> None:
        self.input = StubInput()
        self.manager = self.RecordingManager()
        self.scene = self.pss.PlayerSelectScene(self.manager, self.assets, self.input)
        self.scene.on_enter(input_mgr=self.input)
        self.scene.focus = "vkb"
        self.scene.vkb_row = self.scene.vkb_col = 0
        self.saved = []
        # Never touch the real profiles.json from a test.
        self.scene.prof_mgr = mock.Mock()
        self.scene.prof_mgr.get_profile.return_value = None
        self.scene.prof_mgr.save_profile.side_effect = \
            lambda name, *a, **k: self.saved.append(name)

    def enter_key(self):
        return self.pygame.event.Event(
            self.pygame.KEYDOWN, {"key": self.pygame.K_RETURN, "mod": 0, "unicode": "\r"})

    def type_name(self, name):
        for ch in name:
            ev = self.pygame.event.Event(
                self.pygame.KEYDOWN, {"key": ord(ch.lower()), "mod": 0, "unicode": ch})
            self.input.tap()
            self.scene.handle_events([ev], self.input)

    # ── the reported bug ──────────────────────────────────────────────────────

    def test_enter_confirms_the_name_exactly_as_typed(self) -> None:
        self.type_name("Karuna")
        self.assertEqual(self.scene.input_name, "Karuna")

        self.input.tap(self.input.ACTION, self.input.MENU_SELECT)   # Enter raises these
        self.scene.handle_events([self.enter_key()], self.input)

        self.assertEqual(self.scene.input_name, "Karuna", "no stray letter appended")
        self.assertEqual(self.saved, ["Karuna"], "saved once, under the typed name")

    def test_enter_confirms_once_not_twice(self) -> None:
        """The second confirm found the just-written profile and skipped ahead."""
        self.type_name("Karuna")
        self.input.tap(self.input.ACTION, self.input.MENU_SELECT)
        self.scene.handle_events([self.enter_key()], self.input)

        self.assertEqual(len(self.manager.switches), 1, "one scene change, not two")
        self.assertEqual(self.manager.switches[0][0], self.settings.SCENE_CHARACTER_SELECT,
                         "a new name goes to Character Select, not straight into play")

    def test_enter_on_the_ok_key_does_not_confirm_twice_either(self) -> None:
        """The highlight sitting on OK was the case that cost the girl sprite."""
        self.type_name("Karuna")
        self.scene.vkb_row = len(self.pss.VKB_ROWS) - 1
        self.scene.vkb_col = self.pss.VKB_ROWS[-1].index("OK")

        self.input.tap(self.input.ACTION, self.input.MENU_SELECT)
        self.scene.handle_events([self.enter_key()], self.input)

        self.assertEqual(self.scene.input_name, "Karuna")
        self.assertEqual(len(self.manager.switches), 1)

    # ── letters that are also commands (2026-11-15) ───────────────────────────

    def type_as_a_keyboard_does(self, name):
        """As InputManager really reports it: E raises ACTION and MENU_SELECT, and
        W/A/S/D raise the menu directions, in the same frame the letter arrives."""
        also = {"e": (self.input.ACTION, self.input.MENU_SELECT), "w": (self.input.MENU_UP,),
                "s": (self.input.MENU_DOWN,), "a": (self.input.MENU_LEFT,), "d": (self.input.MENU_RIGHT,)}
        for ch in name:
            ev = self.pygame.event.Event(
                self.pygame.KEYDOWN, {"key": ord(ch.lower()), "mod": 0, "unicode": ch})
            self.input.tap(*also.get(ch.lower(), ()))
            self.scene.handle_events([ev], self.input)

    def test_a_typed_e_is_a_letter_and_presses_nothing(self) -> None:
        """"Dev" came out as "DAev": E pressed the highlighted on-screen key too."""
        self.type_as_a_keyboard_does("Dev")
        self.assertEqual(self.scene.input_name, "Dev")
        self.assertEqual(self.manager.switches, [])

    def test_typed_w_a_s_d_do_not_move_the_highlight(self) -> None:
        self.type_as_a_keyboard_does("Swadesh")
        self.assertEqual(self.scene.input_name, "Swadesh")
        self.assertEqual((self.scene.focus, self.scene.vkb_row, self.scene.vkb_col), ("vkb", 0, 0))

    def test_a_typed_e_does_not_start_the_highlighted_saved_profile(self) -> None:
        """With the list in focus, E used to launch whoever was highlighted."""
        self.scene.profiles = [{"name": "Arham", "character": "girl"}]
        self.scene.focus = "profile"
        self.type_as_a_keyboard_does("e")
        self.assertEqual(self.manager.switches, [], "typing a letter starts no game")
        self.assertEqual(self.scene.input_name, "e")

    # ── what a pad must still be able to do ───────────────────────────────────

    def test_a_pad_confirm_still_types_the_highlighted_letter(self) -> None:
        """Without this a pad could not enter a name at all."""
        self.scene.vkb_row = self.scene.vkb_col = 0        # "A"
        self.input.tap(self.input.ACTION)
        self.scene.handle_events([], self.input)           # no Enter in the events
        self.assertEqual(self.scene.input_name, "A")
        self.assertEqual(self.manager.switches, [], "typing is not confirming")

    def test_a_pad_confirm_on_ok_still_confirms(self) -> None:
        self.type_name("Karuna")
        self.scene.vkb_row = len(self.pss.VKB_ROWS) - 1
        self.scene.vkb_col = self.pss.VKB_ROWS[-1].index("OK")

        self.input.tap(self.input.ACTION)
        self.scene.handle_events([], self.input)

        self.assertEqual(self.saved, ["Karuna"])
        self.assertEqual(len(self.manager.switches), 1)

    def test_backspace_still_deletes(self) -> None:
        self.type_name("Karuna")
        back = self.pygame.event.Event(
            self.pygame.KEYDOWN, {"key": self.pygame.K_BACKSPACE, "mod": 0, "unicode": ""})
        self.input.tap()
        self.scene.handle_events([back], self.input)
        self.assertEqual(self.scene.input_name, "Karun")


if __name__ == "__main__":
    unittest.main()
