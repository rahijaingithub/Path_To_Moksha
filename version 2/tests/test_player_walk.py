"""Walk animation tests: the walk is the normal-speed look, and its art is sound.

Needs pygame, so it is skipped on the dependency-free CI worker and runs locally
in the project venv (like the real-physics tests in ``test_level3_layout``).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SPRITES = ROOT / "assets" / "images" / "sprites"


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class PlayerWalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import level_scene
        from asset_manager import AssetManager
        from input_manager import InputManager
        from scene_manager import SceneManager
        cls.pygame = pygame
        cls.strip_frame_count = staticmethod(level_scene.strip_frame_count)
        cls.manager = SceneManager()
        cls.manager.shared["game_mode"] = "developer"
        cls.manager.shared["character"] = "boy"
        cls.input = InputManager()
        cls.scene = level_scene.LevelScene(cls.manager, AssetManager(), cls.input)

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def test_holding_a_direction_shows_the_walk_not_the_run(self) -> None:
        s = self.scene
        s.on_enter(level=1, input_mgr=self.input)
        s.hazards = []                       # a stun would switch the animation to "stun"
        for _ in range(30):
            s.update(1 / 60)
        for key in (self.input.RIGHT, self.input.LEFT):
            with self.subTest(key=key):
                states, frames = [], set()
                self.input.actions[key] = True
                try:
                    for _ in range(60):
                        s.update(1 / 60)
                        states.append(s.anim_state)
                        if s.anim_state == "walk":
                            frames.add(s.anim_frame)
                finally:
                    self.input.actions[key] = False
                self.assertNotIn("run", states)
                self.assertGreaterEqual(states.count("walk"), 58)
                n = self.strip_frame_count(s.player_strips["walk_right"])
                self.assertEqual(frames, set(range(n)), "every walk frame should play")
                for _ in range(40):
                    s.update(1 / 60)
                self.assertEqual(s.anim_state, "idle")

    def test_walk_left_is_the_right_strip_mirrored_frame_by_frame(self) -> None:
        pg = self.pygame
        for who in ("boy", "girl"):
            with self.subTest(character=who):
                right = pg.image.load(str(SPRITES / f"player_{who}_walk_right.png"))
                left = pg.image.load(str(SPRITES / f"player_{who}_walk_left.png"))
                self.assertEqual(right.get_size(), left.get_size())
                h = right.get_height()
                self.assertEqual(h, 128)
                self.assertEqual(right.get_width() % h, 0)
                for i in range(right.get_width() // h):
                    frame = right.subsurface((i * h, 0, h, h))
                    mirrored = pg.transform.flip(frame, True, False)
                    expected = pg.image.tobytes(mirrored, "RGBA")
                    actual = pg.image.tobytes(left.subsurface((i * h, 0, h, h)), "RGBA")
                    self.assertEqual(expected, actual, f"frame {i} is not a mirror")


if __name__ == "__main__":
    unittest.main()
