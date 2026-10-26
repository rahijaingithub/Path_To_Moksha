"""The title screen's quit prompt (2026-10-25).

It used to be a pair of key hints — "Enter / A - Yes, quit", "Esc / B - No, stay" —
and confirmed on ACTION or MENU_SELECT. But which physical button those are is
whatever a pad's mapping says: on the Retro-bit map in `data/controller_map.json`
`action` is buttons 1 and 5, and `jump` (button 0) also confirms, so B meant "yes"
and the game closed under almost any button.

It is now two highlighted options, and confirming acts on the highlight, which no
mapping can get wrong. These tests pin that down: the default is to stay, a bare
confirm never quits, and quitting takes a deliberate move onto "Yes, leave".

Needs pygame, so it is skipped on the dependency-free CI worker.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest


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
        self.mouse_x = -500          # parked off every button
        self.mouse_y = -500

    def tap(self, *keys):
        for k in self.just_pressed:
            self.just_pressed[k] = False
        for k in keys:
            self.just_pressed[k] = True


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class QuitConfirmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import title_screen
        from asset_manager import AssetManager
        from scene_manager import SceneManager
        cls.pygame = pygame
        cls.title_screen = title_screen
        cls.SceneManager = SceneManager
        cls.assets = AssetManager()

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def setUp(self) -> None:
        self.input = StubInput()
        self.manager = self.SceneManager()
        self.scene = self.title_screen.TitleScreen(self.manager, self.assets, self.input)
        self.scene.on_enter(input_mgr=self.input)
        self.quit_calls = []
        self.scene._quit_game = lambda: self.quit_calls.append(True)
        self.scene._open_quit_confirm()

    def press(self, *keys):
        self.input.tap(*keys)
        self.scene.handle_events([], self.input)
        self.input.tap()

    # ── the default ───────────────────────────────────────────────────────────

    def test_the_prompt_opens_on_stay(self) -> None:
        self.assertTrue(self.scene.confirm_quit)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_STAY)

    def test_confirming_straight_away_does_not_quit(self) -> None:
        """The bug: nearly any button used to close the game."""
        for key in (self.input.ACTION, self.input.MENU_SELECT, self.input.JUMP):
            with self.subTest(key=key):
                self.scene._open_quit_confirm()
                self.press(key)
                self.assertEqual(self.quit_calls, [], "a bare confirm means stay")
                self.assertFalse(self.scene.confirm_quit, "and closes the prompt")

    def test_back_always_stays(self) -> None:
        for key in (self.input.BACK, self.input.MENU_BACK):
            with self.subTest(key=key):
                self.scene._open_quit_confirm()
                self.scene.confirm_quit_choice = self.title_screen.QUIT_LEAVE
                self.press(key)
                self.assertEqual(self.quit_calls, [], "backing out never quits")
                self.assertFalse(self.scene.confirm_quit)

    # ── moving the highlight ──────────────────────────────────────────────────

    def test_left_and_right_choose_an_answer(self) -> None:
        self.press(self.input.MENU_LEFT)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_LEAVE)
        self.press(self.input.MENU_RIGHT)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_STAY)
        self.press(self.input.LEFT)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_LEAVE)
        self.press(self.input.RIGHT)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_STAY)

    def test_left_twice_stays_on_leave(self) -> None:
        """Directions set an answer; they do not toggle back and forth."""
        self.press(self.input.MENU_LEFT)
        self.press(self.input.MENU_LEFT)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_LEAVE)

    def test_up_or_down_flips_between_the_two(self) -> None:
        self.press(self.input.MENU_UP)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_LEAVE)
        self.press(self.input.MENU_DOWN)
        self.assertEqual(self.scene.confirm_quit_choice, self.title_screen.QUIT_STAY)

    # ── actually leaving ──────────────────────────────────────────────────────

    def test_quitting_takes_a_deliberate_move_then_a_confirm(self) -> None:
        self.press(self.input.MENU_LEFT)
        self.assertEqual(self.quit_calls, [], "moving the highlight does not act")
        self.press(self.input.ACTION)
        self.assertEqual(self.quit_calls, [True])

    # ── the menu behind is untouched ──────────────────────────────────────────

    def test_the_menu_behind_cannot_be_used_while_the_prompt_is_up(self) -> None:
        before = self.scene.selected_index
        self.press(self.input.MENU_DOWN)
        self.assertEqual(self.scene.selected_index, before, "swallowed by the prompt")
        self.assertEqual(self.manager.switches if hasattr(self.manager, "switches") else [], [])

    # ── layout ────────────────────────────────────────────────────────────────

    def test_the_two_buttons_do_not_overlap_and_sit_inside_the_panel(self) -> None:
        box, btns = self.scene._quit_button_rects()
        self.assertEqual(len(btns), 2)
        self.assertFalse(btns[0].colliderect(btns[1]), "the answers are separate targets")
        for r in btns:
            self.assertTrue(box.contains(r), "and both sit inside the panel")

    def test_draws_on_both_answers(self) -> None:
        surf = self.pygame.Surface((1920, 1080))
        for choice in (self.title_screen.QUIT_LEAVE, self.title_screen.QUIT_STAY):
            with self.subTest(choice=choice):
                self.scene.confirm_quit_choice = choice
                self.scene.draw(surf)


if __name__ == "__main__":
    unittest.main()
