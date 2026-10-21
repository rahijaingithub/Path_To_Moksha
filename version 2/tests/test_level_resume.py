"""Resume tests (Epic G1): going back into a level without rebuilding it.

The bonus level returns the devotee to Level 3 at the exact spot he left, which
works because ``SceneManager`` keeps one ``LevelScene`` instance per key and
``LevelScene`` has no ``on_exit`` — the state survives the trip, and is only lost
because ``on_enter`` normally rebuilds it. ``on_enter(resume=True)`` skips that
rebuild; anything that cannot be resumed must still build normally.

Needs pygame, so it is skipped on the dependency-free CI worker and runs locally
in the project venv (like ``test_transitions``).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class LevelResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import level_scene
        import settings
        from asset_manager import AssetManager
        from input_manager import InputManager
        from scene_manager import SceneManager

        cls.pygame = pygame
        cls.settings = settings
        cls.level_scene = level_scene
        cls.SceneManager = SceneManager
        cls.assets = AssetManager()
        cls.input = InputManager()

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def fresh_scene(self, level=3):
        """A LevelScene that has already played `level` for a while."""
        manager = self.SceneManager()
        scene = self.level_scene.LevelScene(manager, self.assets, self.input)
        scene.on_enter(level=level, input_mgr=self.input)
        return manager, scene

    def mark(self, scene):
        """Put the level in a distinctive mid-play state and return what to check."""
        scene.player.x, scene.player.y = 777.0, 321.0
        scene.time_remaining = 123.5
        scene.elapsed = 42.0
        if scene.box_system.boxes:
            scene.box_system.boxes[0].opened = True
        return {
            "player": scene.player,
            "box_system": scene.box_system,
            "monk": scene.monk,
            "platforms": scene.platforms,
        }

    # ── resuming keeps everything ─────────────────────────────────────────────

    def test_resume_keeps_the_devotee_exactly_where_he_left_off(self) -> None:
        _, scene = self.fresh_scene(3)
        kept = self.mark(scene)

        scene.on_enter(level=3, resume=True, input_mgr=self.input)

        self.assertIs(scene.player, kept["player"], "same player object, not a respawn")
        self.assertEqual((scene.player.x, scene.player.y), (777.0, 321.0))
        self.assertEqual(scene.time_remaining, 123.5, "the clock is not refilled")
        self.assertEqual(scene.elapsed, 42.0)
        self.assertEqual(scene.level, 3)

    def test_resume_keeps_the_boxes_the_monk_and_the_layout(self) -> None:
        _, scene = self.fresh_scene(3)
        kept = self.mark(scene)

        scene.on_enter(level=3, resume=True, input_mgr=self.input)

        self.assertIs(scene.box_system, kept["box_system"], "boxes are not re-rolled")
        self.assertTrue(scene.box_system.boxes[0].opened, "an opened box stays opened")
        self.assertIs(scene.monk, kept["monk"], "the Monk keeps his question and spot")
        self.assertIs(scene.platforms, kept["platforms"])

    def test_resume_fades_back_in_and_restores_the_level_in_shared_state(self) -> None:
        manager, scene = self.fresh_scene(3)
        self.mark(scene)
        manager.shared["current_level"] = 99          # as a bonus scene might leave it

        scene.on_enter(level=3, resume=True, input_mgr=self.input)

        self.assertEqual(manager.shared["current_level"], 3)
        self.assertEqual(scene.fade_alpha, 255, "fades back in on the way home")

    # ── anything that cannot be resumed still builds ──────────────────────────

    def test_a_normal_enter_still_rebuilds_the_level(self) -> None:
        _, scene = self.fresh_scene(3)
        kept = self.mark(scene)

        scene.on_enter(level=3, input_mgr=self.input)   # no resume

        self.assertIsNot(scene.player, kept["player"], "a fresh run respawns")
        self.assertIsNot(scene.box_system, kept["box_system"], "boxes are re-rolled")
        self.assertEqual(scene.time_remaining,
                         float(self.settings.LEVEL_TIME_LIMIT[3]), "full clock")

    def test_resume_on_a_level_that_was_never_entered_builds_it(self) -> None:
        manager = self.SceneManager()
        scene = self.level_scene.LevelScene(manager, self.assets, self.input)
        self.assertIsNone(scene.player, "nothing built yet")

        scene.on_enter(level=3, resume=True, input_mgr=self.input)

        self.assertIsNotNone(scene.player, "built rather than resuming into nothing")
        self.assertEqual(scene.level, 3)
        self.assertEqual(scene.time_remaining, float(self.settings.LEVEL_TIME_LIMIT[3]))

    def test_resume_into_a_different_level_builds_that_level(self) -> None:
        _, scene = self.fresh_scene(3)
        self.mark(scene)

        scene.on_enter(level=4, resume=True, input_mgr=self.input)

        self.assertEqual(scene.level, 4)
        self.assertEqual(scene.time_remaining, float(self.settings.LEVEL_TIME_LIMIT[4]))

    def test_resume_after_the_level_already_ended_builds_it(self) -> None:
        for ended in ("level_complete", "game_over"):
            with self.subTest(ended=ended):
                _, scene = self.fresh_scene(3)
                self.mark(scene)
                setattr(scene, ended, True)

                scene.on_enter(level=3, resume=True, input_mgr=self.input)

                self.assertFalse(getattr(scene, ended), "rebuilt, not resumed into an ended level")
                self.assertEqual(scene.time_remaining,
                                 float(self.settings.LEVEL_TIME_LIMIT[3]))


if __name__ == "__main__":
    unittest.main()
