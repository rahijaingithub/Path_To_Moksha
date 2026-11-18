"""The Options screen's starting level (2026-10-25).

Level 3 opened to kid and standard, but this screen went on capping their start at
Level 2 — the cap was a `max_level = 2` written out in four places, none of which
knew about the gate in `level_scene._advance_level`.

The cap now comes from one table, and the last test here ties that table to the
gate, so the two cannot drift apart again.

The scene tests need pygame; the cross-check is source-level and runs anywhere.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import re
import sys
import unittest

# `unittest discover` puts this directory on the path; a direct
# `python -m unittest tests.<module>` does not, so do it either way.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_tools import strip_comments


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

    def test_kid_and_standard_can_start_on_any_level(self) -> None:
        """All four: Level 4 opened to every mode on 2026-11-14."""
        for mode in ("kid", "standard"):
            with self.subTest(mode=mode):
                s = self.scene(mode, 1)
                seen = set()
                for _ in range(6):
                    seen.add(s.starting_level)
                    s._cycle_start_level(1)
                self.assertEqual(seen, {1, 2, 3, 4}, "cycles 1 to 4 and wraps")

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
        self.assertEqual(s.starting_level, 4, "back from the first lands on the last")
        s._cycle_start_level(-1)
        self.assertEqual(s.starting_level, 3)

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

    def test_leaving_developer_mode_keeps_level_4(self) -> None:
        """It used to be thrown back to 1; every mode can play it now."""
        s = self.scene("developer", 4)
        s.game_mode = "kid"
        s._clamp_start_level()
        self.assertEqual(s.starting_level, 4)


class CapMatchesTheGateTests(unittest.TestCase):
    """The option and the gate must agree, which is what broke the first time."""

    def test_the_offered_start_matches_where_the_run_ends(self) -> None:
        options = (SRC / "options_scene.py").read_text(encoding="utf-8")
        table = re.search(r"HIGHEST_START_LEVEL = \{([^}]*)\}", options)
        self.assertIsNotNone(table, "HIGHEST_START_LEVEL not found")
        offered = dict(re.findall(r'"(\w+)":\s*(\d+)', table.group(1)))

        # There is no to-be-continued gate any more (2026-11-14): the run ends
        # after Level 4 for everyone. If a gate comes back, it sets the last level.
        level_scene = (SRC / "level_scene.py").read_text(encoding="utf-8")
        gate = re.search(
            r"if self\.level == (\d+) and self\.game_mode in \(\"kid\", \"standard\"\)",
            level_scene)
        last_level = int(gate.group(1)) if gate else 4

        for mode in ("kid", "standard"):
            self.assertEqual(int(offered[mode]), last_level,
                             f"{mode} is offered a start the run does not reach, "
                             "or stops short of one it does")


class DevTransitionStartTests(unittest.TestCase):
    """A negative Starting Level opens on a cutscene (2026-10-25).

    v1 had `abs(starting_level, input_mgr=...)` here, a misplaced bracket that
    raised TypeError. v2 fixed the bracket and kept two subtler faults: the call
    passed `level=`, which TransitionScene ignores (it reads `next_level`), so the
    scene always fell back to its default; and it used `abs(n)` where the meaning
    is `abs(n) + 1`. Both together meant Transition 2 opened on the Jyot temple and
    ran into Level 2 instead of Parshvanath and Level 3.
    """

    def test_a_negative_start_is_the_transition_after_that_level(self) -> None:
        sys.path.insert(0, str(SRC))
        try:
            from scene_manager import dev_transition_next_level
        finally:
            sys.path.remove(str(SRC))
        self.assertEqual(dev_transition_next_level(-1), 2, "Jyot, then Level 2")
        self.assertEqual(dev_transition_next_level(-2), 3, "Parshvanath, then Level 3")

    @unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                         "needs pygame (runs locally in the venv, skipped on CI)")
    def test_every_dev_start_matches_the_label_options_shows(self) -> None:
        """-1 is labelled Jyot and -2 Parshvanath; the transitions must agree."""
        sys.path.insert(0, str(SRC))
        try:
            from scene_manager import dev_transition_next_level
            import transition_scene
        finally:
            sys.path.remove(str(SRC))
        expected = {-1: "jsot_temple.png", -2: "parshvanath.png"}
        for start, image in expected.items():
            with self.subTest(start=start):
                data = transition_scene.TRANSITION_DATA[dev_transition_next_level(start)]
                self.assertEqual(data["image"], image)

    def test_no_scene_routes_a_transition_with_the_wrong_keyword(self) -> None:
        """TransitionScene reads `next_level`; a `level=` kwarg is silently dropped."""
        for name in ("player_select_scene.py", "leaderboard_scene.py",
                     "character_select.py"):
            with self.subTest(scene=name):
                src = strip_comments((SRC / name).read_text(encoding="utf-8"))
                for call in re.findall(r"switch_to\(\s*SCENE_TRANSITION[^)]*\)", src,
                                       re.S):
                    self.assertNotIn("level=abs", call,
                                     "routes a transition by the wrong keyword")
                    self.assertIn("next_level=", call)

    def test_all_three_scenes_use_the_shared_helper(self) -> None:
        """Three copies of this rule is how it came to differ between them."""
        for name in ("player_select_scene.py", "leaderboard_scene.py",
                     "character_select.py"):
            with self.subTest(scene=name):
                src = (SRC / name).read_text(encoding="utf-8")
                self.assertIn("dev_transition_next_level", src)


if __name__ == "__main__":
    unittest.main()
