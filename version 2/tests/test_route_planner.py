"""Route planner tests (tools/route_planner.py, the route half of Epic H's H4).

The planner's whole claim is that a route it finds is one the game will give:
replaying its frames from the same start lands where it said, without the lake.
These check that claim on Level 3's real geometry.

Needs pygame, so it is skipped on the dependency-free CI worker and runs locally
in the project venv (like ``test_bonus_scene``).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
DT = (1000.0 / 60.0) / 1000.0


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class RoutePlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(ROOT / "src"))
        sys.path.insert(0, str(ROOT / "tools"))
        import pygame
        pygame.init()
        import level_layouts
        import level_scene
        import route_planner
        import settings
        cls.pygame = pygame
        cls.planner = route_planner
        cls.level_scene = level_scene
        cls.settings = settings
        cls.platforms = level_layouts.build_level_platforms(3)
        cls.world = route_planner.World(
            cls.platforms, level_layouts.build_level_slopes(3), cls.platforms[0].top,
            settings.LEVEL_JUMP_FORCES[3], DT)
        cls.plinth = next(p for p in cls.platforms if p.width == 336)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.quit()

    def standing_at_the_start(self):
        """On lily pad 18, where Level 3 begins, settled onto it."""
        s = self.settings
        player = self.level_scene.Player(137 + (169 - s.PLAYER_WIDTH) // 2,
                                         s.LOGICAL_HEIGHT - 154 - s.PLAYER_HEIGHT)
        for _ in range(5):
            self.planner.step(player, 0, False, self.world)
        self.assertTrue(player.on_ground)
        return player

    def on_the_plinth(self, player):
        return (abs(player.y + player.height - self.plinth.top) < 1
                and self.plinth.left < player.rect.centerx < self.plinth.right)

    def test_a_route_from_the_start_to_the_plinth_replays_exactly(self) -> None:
        player = self.standing_at_the_start()
        route = self.planner.plan(player, self.world, self.on_the_plinth, self.plinth.centerx)
        self.assertIsNotNone(route, "no route from lily pad 18 to the pavilion plinth")
        frames, positions = route
        self.assertEqual(len(frames), len(positions))

        for (move, jump), expected in zip(frames, positions):
            self.assertTrue(self.planner.step(player, move, jump, self.world),
                            "the planned route went into the lake")
            self.assertAlmostEqual(player.x, expected[0], places=6)
            self.assertAlmostEqual(player.y, expected[1], places=6)
        self.assertTrue(self.on_the_plinth(player))

    def test_planning_leaves_the_real_player_untouched(self) -> None:
        player = self.standing_at_the_start()
        before = (player.x, player.y, player.vx, player.vy)
        self.planner.plan(player, self.world, self.on_the_plinth, self.plinth.centerx)
        self.assertEqual((player.x, player.y, player.vx, player.vy), before)

    def test_an_unreachable_goal_gives_no_route(self) -> None:
        player = self.standing_at_the_start()
        self.assertIsNone(self.planner.plan(player, self.world, lambda p: p.y < -1000))

    def test_a_route_is_planned_from_standing_only(self) -> None:
        player = self.standing_at_the_start()
        player.on_ground = False
        with self.assertRaises(ValueError):
            self.planner.plan(player, self.world, self.on_the_plinth)


if __name__ == "__main__":
    unittest.main()
