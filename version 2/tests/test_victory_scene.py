"""Victory page tests: the picture, the labels, and the focus score.

The page ends the pilgrimage on the title screen's own photograph of the temple
(designer, 2026-11-13). Three faults were fixed with it: a magenta placeholder
where a never-made image was asked for, a button that said "restart" and opened
the leaderboard, and a focus score that counted every unopened box as a
distraction avoided.

The scene tests need pygame, so they are skipped on the dependency-free CI worker
and run locally in the project venv (like ``test_bonus_scene``).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class VictoryWiringTests(unittest.TestCase):
    """Source-level checks that need neither pygame nor a display."""

    def setUp(self) -> None:
        self.source = (SRC / "victory_scene.py").read_text(encoding="utf-8")

    def test_the_picture_is_the_title_screens_and_exists(self) -> None:
        self.assertIn('"title_background.png", "backgrounds"', self.source)
        self.assertNotIn("digambar_garbhalaya", self.source)
        self.assertTrue((ROOT / "assets/images/backgrounds/title_background.png").is_file())

    def test_the_button_says_where_it_goes(self) -> None:
        import re
        label = re.search(r'^CONTINUE_LABEL\s*=\s*"([^"]+)"', self.source, re.M)
        self.assertIsNotNone(label, "CONTINUE_LABEL not found")
        self.assertIn("LEADERBOARD", label.group(1))
        self.assertNotIn("RESTART", label.group(1))
        self.assertIn("SCENE_LEADERBOARD", self.source)

    def test_every_level_records_its_distractions(self) -> None:
        level_src = (SRC / "level_scene.py").read_text(encoding="utf-8")
        self.assertIn('setdefault("distractions", {})[self.level]', level_src)
        # A new pilgrimage must not inherit the last one's count.
        for name in ("level_scene.py", "leaderboard_scene.py", "player_select_scene.py"):
            with self.subTest(file=name):
                self.assertIn('shared["distractions"] = {}',
                              (SRC / name).read_text(encoding="utf-8"))


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class VictorySceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import debug_monitor
        import profile_manager
        import victory_scene
        from asset_manager import AssetManager
        from input_manager import InputManager
        from scene_manager import SceneManager

        cls._monitor = debug_monitor.monitor
        cls._monitor_was_enabled = cls._monitor.enabled
        cls._monitor.enabled = False
        # Entering the page saves the score; a test must not write a profile.
        cls._profile_manager = profile_manager.ProfileManager
        cls._real_save = profile_manager.ProfileManager.save_profile
        profile_manager.ProfileManager.save_profile = lambda *a, **k: None

        cls.pygame = pygame
        cls.victory_scene = victory_scene
        cls.SceneManager = SceneManager
        cls.assets = AssetManager()
        cls.input = InputManager()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._profile_manager.save_profile = cls._real_save
        cls._monitor.enabled = cls._monitor_was_enabled
        sys.path.remove(str(SRC))

    def enter(self, **shared):
        manager = self.SceneManager()
        manager.shared.update(shared)
        scene = self.victory_scene.VictoryScene(manager, self.assets, self.input)
        scene.on_enter()
        return scene

    def test_focus_counts_distraction_boxes_only(self) -> None:
        """Six boxes shut out of twelve is not six distractions avoided."""
        scene = self.enter(boxes_opened={1: (2, 6), 2: (4, 6)},
                           distractions={1: (1, 2), 2: (0, 2)})
        self.assertEqual(scene.focus_line(),
                         "Pilgrimage Focus Score: Avoided 3 / 4 Distractions")

    def test_focus_does_not_invent_a_total(self) -> None:
        self.assertNotIn("18", self.enter().focus_line())

    def test_nothing_on_the_page_is_the_missing_asset_pink(self) -> None:
        scene = self.enter(total_time=400.0)
        scene.update(0.5)
        surface = self.pygame.Surface((1920, 1080))
        scene.draw(surface)
        for point in ((960, 380), (300, 300), (1600, 500), (960, 1000)):
            with self.subTest(point=point):
                self.assertNotEqual(tuple(surface.get_at(point))[:3], (255, 0, 220))


if __name__ == "__main__":
    unittest.main()
