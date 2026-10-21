"""Transition tests: Level 1 -> 2 walks to the temple door and stops there, Level 3 -> 4
shows Mahavir Bhagwan (bow), Level 4 -> Victory shows Moolnayak Adinath Bhagwan
(bow + golden glow) and then goes to Victory.

Needs pygame, so it is skipped on the dependency-free CI worker and runs locally
in the project venv (like ``test_level3_layout``'s scene tests).
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
PINK = (255, 0, 220)       # AssetManager's missing-image placeholder


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class TransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import settings
        import transition_scene
        import level_scene
        from asset_manager import AssetManager
        from input_manager import InputManager
        from scene_manager import SceneManager

        class RecordingManager(SceneManager):
            """Records scene switches instead of performing them."""
            def __init__(self):
                super().__init__()
                self.switches = []

            def switch_to(self, key, input_mgr=None, **kwargs):
                self.switches.append((key, kwargs))

        cls.pygame = pygame
        cls.settings = settings
        cls.ts = transition_scene
        cls.ls = level_scene
        cls.RecordingManager = RecordingManager
        cls.assets = AssetManager()
        cls.input = InputManager()

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def enter(self, next_level):
        manager = self.RecordingManager()
        scene = self.ts.TransitionScene(manager, self.assets, self.input)
        scene.on_enter(next_level=next_level, input_mgr=self.input)
        return manager, scene

    def assert_real_image(self, scene, name):
        self.assertEqual(scene.data["image"], name)
        self.assertEqual(scene.bg_image.get_size(), (360, 480))
        self.assertNotEqual(scene.bg_image.get_at((0, 0))[:3], PINK, f"{name} is missing")

    def test_level1_to_2_stops_walking_at_the_temple_door(self) -> None:
        """The devotee walks in, then stands still — no stepping on the spot."""
        manager, scene = self.enter(2)
        self.assertIn(2, self.ts.NO_BOW_TRANSITIONS, "walk-in only, no bow")
        surf = self.pygame.Surface((1920, 1080))

        scene.update(1.0)                      # mid-walk (walk_duration is 4.0s)
        scene.draw(surf)
        self.assertFalse(scene.walk_arrived, "still walking one second in")

        scene.update(3.5)                      # past the end of the walk
        scene.draw(surf)
        self.assertTrue(scene.walk_arrived, "arrived at the door")

        scene.update(0.5)                      # and stays arrived while it holds
        scene.draw(surf)
        self.assertTrue(scene.walk_arrived)

    def test_level3_to_4_shows_mahavir_and_bows(self) -> None:
        manager, scene = self.enter(4)
        self.assert_real_image(scene, "mahavir.png")
        self.assertNotIn(4, self.ts.NO_BOW_TRANSITIONS, "bows here as well as inside Level 3")
        self.assertTrue(scene.bow_frames, "bow poses loaded")
        scene._advance()
        self.assertEqual(manager.switches, [(self.settings.SCENE_LEVEL, {"level": 4})])

    def test_level4_to_victory_shows_adinath_bows_and_glows_then_victory(self) -> None:
        manager, scene = self.enter(self.ts.FINAL_TRANSITION)
        self.assert_real_image(scene, "adinath.png")
        self.assertNotIn(self.ts.FINAL_TRANSITION, self.ts.NO_BOW_TRANSITIONS)
        self.assertTrue(scene.bow_frames, "bow poses loaded")
        surf = self.pygame.Surface((1920, 1080))
        for _ in range(int(4.0 * 60)):         # through the walk-in and into the bow + glow
            scene.update(1 / 60)
        scene.draw(surf)
        self.assertEqual(manager.switches, [], "holds on the image before fading out")
        for _ in range(int(5.0 * 60)):         # auto-advance at 8.5s
            scene.update(1 / 60)
        self.assertEqual(manager.switches[0][0], self.settings.SCENE_VICTORY)

    def test_finishing_level4_goes_to_the_adinath_transition(self) -> None:
        manager = self.RecordingManager()
        manager.shared.update({"game_mode": "developer", "level_times": {}, "monk_correct": {},
                               "boxes_opened": {}, "asked_questions": []})
        manager.scenes = {self.settings.SCENE_TRANSITION: None, self.settings.SCENE_VICTORY: None}
        scene = self.ls.LevelScene(manager, self.assets, self.input)
        scene.on_enter(level=4, input_mgr=self.input)
        with mock.patch("profile_manager.ProfileManager.save_profile"):
            scene._advance_level()
        key, kwargs = manager.switches[-1]
        self.assertEqual(key, self.settings.SCENE_TRANSITION)
        self.assertEqual(kwargs["next_level"], self.ts.FINAL_TRANSITION)


if __name__ == "__main__":
    unittest.main()
