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

    # ── hazards (Level 1) and flight (Level 2) ───────────────────────────────

    def test_a_route_along_the_street_never_touches_the_water(self) -> None:
        import hazards
        import level_layouts
        s = self.settings
        platforms = level_layouts.build_level_platforms(1)
        dangers = hazards.create_hazards_for_level(1, platforms)
        water = next(h for h in dangers if h.hazard_type == "water")
        world = self.planner.World(
            platforms, [], platforms[0].top + 10000, s.LEVEL_JUMP_FORCES[1], DT,
            self.planner.forecast(dangers, DT, 60 * 40))
        player = self.level_scene.Player(80, s.LOGICAL_HEIGHT - 30 - s.PLAYER_HEIGHT - 10)
        for _ in range(30):
            self.planner.step(player, 0, False, world)
        self.assertTrue(player.on_ground)

        def past_the_water(p):
            return p.on_ground and p.x > water.x + water.w + 100 and p.y + p.height >= platforms[0].top - 1

        route = self.planner.plan(player, world, past_the_water, water.x + water.w + 200)
        self.assertIsNotNone(route, "no way along the street past the water")
        for move, jump in route[0]:
            self.planner.step(player, move, jump, world)
            self.assertFalse(player.rect.colliderect(water.rect), "the route stepped in the water")
        self.assertTrue(past_the_water(player))

    def test_a_forecast_follows_a_snake_along_its_beat(self) -> None:
        import hazards
        import level_layouts
        snake = next(h for h in hazards.create_hazards_for_level(2, level_layouts.build_level_platforms(2))
                     if h.patrol_range)
        start_x = snake.x
        ahead = self.planner.forecast([snake], DT, 120)
        self.assertEqual(snake.x, start_x, "forecasting moved the real snake")
        self.assertAlmostEqual(ahead[59][0].x, start_x + snake.move_speed, delta=2)

    def test_a_flight_keeps_clear_of_every_ledge(self) -> None:
        import level_layouts
        s = self.settings
        pygame = self.pygame
        platforms = level_layouts.build_level_platforms(2)
        ledge = next(p for p in platforms if (p.x, p.width) == (500, 380))
        player = self.level_scene.Player(650, ledge.top - s.PLAYER_HEIGHT)   # standing on it
        target = pygame.Rect(25, 315, 130, 70)                               # under the murti
        bounds = pygame.Rect(30, 30, s.LOGICAL_WIDTH - 60, s.LOGICAL_HEIGHT - 60)
        path = self.planner.plan_flight(player, platforms, target, bounds)
        self.assertIsNotNone(path, "no way through the air to the murti")
        body = lambda x, y: pygame.Rect(x, y, int(player.width), int(player.height))
        for x, y in path:
            self.assertLess(body(x, y).collidelist(platforms), 0, "a waypoint is inside a ledge")
        self.assertTrue(body(*path[-1]).colliderect(target))

    def test_a_flight_begins_from_under_a_snake_on_a_low_shelf(self) -> None:
        """Where the Akshat once left the devotee: on the right low shelf, ten
        pixels under the upper snake's beat. No cell of a fixed grid fitted."""
        import level_layouts
        s = self.settings
        pygame = self.pygame
        platforms = level_layouts.build_level_platforms(2)
        beat = pygame.Rect(950, 760, 520, 24)
        player = self.level_scene.Player(1294, 794)
        bounds = pygame.Rect(30, 30, s.LOGICAL_WIDTH - 60, s.LOGICAL_HEIGHT - 60)
        path = self.planner.plan_flight(player, platforms + [beat], pygame.Rect(25, 315, 130, 70), bounds)
        self.assertIsNotNone(path, "no way out from under the snake")
        self.assertEqual(path[0], (1294, 794))

    def test_no_flight_into_a_sealed_place(self) -> None:
        s = self.settings
        pygame = self.pygame
        player = self.level_scene.Player(400, 400)
        bounds = pygame.Rect(30, 30, s.LOGICAL_WIDTH - 60, s.LOGICAL_HEIGHT - 60)
        wall = pygame.Rect(900, 0, 40, s.LOGICAL_HEIGHT)                     # floor to ceiling
        self.assertIsNone(self.planner.plan_flight(player, [wall], pygame.Rect(1500, 400, 60, 60), bounds))


if __name__ == "__main__":
    unittest.main()
