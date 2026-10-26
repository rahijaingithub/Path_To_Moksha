"""The Options screen's starting level (2026-10-25).

Level 3 opened to kid and standard, but this screen went on capping their start at
Level 2 — the cap was a `max_level = 2` written out in four places, none of which
knew about the gate in `level_scene._advance_level`.

The cap now comes from one table, and the last test here ties that table to the
gate, so the two cannot drift apart again.

The scene tests need pygame; the cross-check is source-level and runs anywhere.
"""

from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import re
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
        self.mouse_x = self.mouse_y = -500


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class StartLevelOptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import options_scene
        from asset_manager import AssetManager
        from scene_manager import SceneManager
        cls.options_scene = options_scene
        cls.SceneManager = SceneManager
        cls.assets = AssetManager()

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def scene(self, mode, level=1):
        manager = self.SceneManager()
        manager.shared["game_mode"] = mode
        manager.shared["starting_level"] = level
        s = self.options_scene.OptionsScene(manager, self.assets, StubInput())
        s.on_enter(input_mgr=StubInput())
        s.game_mode, s.starting_level = mode, level
        return s

    # ── what each mode offers ────────────────────────────────────────────────

    def test_kid_and_standard_can_start_on_level_3(self) -> None:
        """The Karuna bonus level lives in Level 3, so they must be able to reach it."""
        for mode in ("kid", "standard"):
            with self.subTest(mode=mode):
                s = self.scene(mode, 1)
                seen = set()
                for _ in range(6):
                    seen.add(s.starting_level)
                    s._cycle_start_level(1)
                self.assertEqual(seen, {1, 2, 3}, "cycles 1, 2, 3 and wraps")

    def test_level_4_is_not_offered_outside_developer_mode(self) -> None:
        """It has no background yet — starting there would open on a placeholder."""
        for mode in ("kid", "standard"):
            with self.subTest(mode=mode):
                s = self.scene(mode, 1)
                for _ in range(12):
                    s._cycle_start_level(1)
                    self.assertNotEqual(s.starting_level, 4)

    def test_developer_still_gets_the_whole_sequence(self) -> None:
        s = self.scene("developer", 1)
        seen = set()
        for _ in range(len(self.options_scene.DEV_SEQ) * 2):
            seen.add(s.starting_level)
            s._cycle_start_level(1)
        self.assertEqual(seen, set(self.options_scene.DEV_SEQ))

    def test_cycling_backwards_wraps_too(self) -> None:
        s = self.scene("standard", 1)
        s._cycle_start_level(-1)
        self.assertEqual(s.starting_level, 3, "back from the first lands on the last")
        s._cycle_start_level(-1)
        self.assertEqual(s.starting_level, 2)

    # ── clamping when the mode changes ───────────────────────────────────────

    def test_leaving_developer_mode_drops_a_transition_start(self) -> None:
        s = self.scene("developer", -2)
        s.game_mode = "kid"
        s._clamp_start_level()
        self.assertEqual(s.starting_level, 1)

    def test_leaving_developer_mode_keeps_level_3(self) -> None:
        """It used to be thrown back to 1; kid and standard can play it now."""
        s = self.scene("developer", 3)
        s.game_mode = "standard"
        s._clamp_start_level()
        self.assertEqual(s.starting_level, 3)

    def test_leaving_developer_mode_drops_level_4(self) -> None:
        s = self.scene("developer", 4)
        s.game_mode = "kid"
        s._clamp_start_level()
        self.assertEqual(s.starting_level, 1)


class CapMatchesTheGateTests(unittest.TestCase):
    """The option and the gate must agree, which is what broke the first time."""

    def test_the_offered_start_matches_where_the_run_ends(self) -> None:
        options = (SRC / "options_scene.py").read_text(encoding="utf-8")
        table = re.search(r"HIGHEST_START_LEVEL = \{([^}]*)\}", options)
        self.assertIsNotNone(table, "HIGHEST_START_LEVEL not found")
        offered = dict(re.findall(r'"(\w+)":\s*(\d+)', table.group(1)))

        level_scene = (SRC / "level_scene.py").read_text(encoding="utf-8")
        gate = re.search(
            r"if self\.level == (\d+) and self\.game_mode in \(\"kid\", \"standard\"\)",
            level_scene)
        self.assertIsNotNone(gate, "the to-be-continued gate was not found")
        last_level = int(gate.group(1))

        for mode in ("kid", "standard"):
            self.assertEqual(int(offered[mode]), last_level,
                             f"{mode} is offered a start the run does not reach, "
                             "or stops short of one it does")


if __name__ == "__main__":
    unittest.main()
