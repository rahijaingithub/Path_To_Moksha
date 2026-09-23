"""Level 3 (Jal Mandir) layout, slope and Monk-placement tests.

Three layers:

* ``SlopeRuleTests`` exercise the pure landing rule in ``src/slopes.py``.
* ``Level3GeometryTests`` load ``level_layouts.py`` with a stub ``pygame``
  (like ``test_portability``) and check the data: nothing sits where the devotee
  would stand inside a platform, the Monk's sacred column and the Mahavir
  Bhagwan image cross no platform, and the image is in the visible band.
* ``Level3RealPhysicsTests`` drive the real ``Player.update`` over the real
  layout. They need pygame, so they are skipped on the dependency-free CI
  worker and run locally in the project venv.
"""

from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

LOGICAL_WIDTH, LOGICAL_HEIGHT = 1920, 1080
HUD_BAR_HEIGHT = 48        # level_scene draw_hud: Surface((LOGICAL_WIDTH, 48))
WORLD_Y_OFFSET = 80        # the world is drawn at (0, -80)


def _evaluate_constant(path: Path, name: str, class_name: str | None = None) -> float:
    """Read a simple numeric constant from source without executing the module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    body = tree.body
    if class_name:
        body = next(n.body for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    for node in body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return eval(compile(ast.Expression(node.value), str(path), "eval"), {"__builtins__": {}})
    raise AssertionError(f"{name} not found in {path.name}")


PLAYER_HEIGHT = _evaluate_constant(SRC / "settings.py", "PLAYER_HEIGHT")
PLAYER_WIDTH = int(_evaluate_constant(SRC / "settings.py", "PLAYER_WIDTH"))
MONK_WIDTH = _evaluate_constant(SRC / "monk_system.py", "WIDTH", "Monk")
MONK_HEIGHT = _evaluate_constant(SRC / "monk_system.py", "HEIGHT", "Monk")


def _load_slopes_module():
    spec = importlib.util.spec_from_file_location("slopes", SRC / "slopes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeRect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.width, self.height = x, y, w, h

    left = property(lambda self: self.x)
    top = property(lambda self: self.y)
    right = property(lambda self: self.x + self.width)
    bottom = property(lambda self: self.y + self.height)

    def colliderect(self, other) -> bool:
        return (self.left < other.right and other.left < self.right
                and self.top < other.bottom and other.top < self.bottom)


def _load_layouts():
    fake_pygame = types.ModuleType("pygame")
    fake_pygame.Rect = _FakeRect
    fake_settings = types.ModuleType("settings")
    fake_settings.LOGICAL_WIDTH = LOGICAL_WIDTH
    fake_settings.LOGICAL_HEIGHT = LOGICAL_HEIGHT
    modules = {"pygame": fake_pygame, "settings": fake_settings, "slopes": _load_slopes_module()}
    with mock.patch.dict(sys.modules, modules):
        return runpy.run_path(str(SRC / "level_layouts.py"))


class SlopeRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.slopes = _load_slopes_module()
        # 100px wide, rising 20px from left to right.
        self.slope = self.slopes.Slope([(100, 500), (200, 480)])
        self.reach = self.slopes.SLOPE_REACH

    def contact(self, center_x, prev_bottom, bottom, vy, current=None):
        return self.slopes.find_slope_contact(
            [self.slope], center_x, prev_bottom, bottom, vy, current, self.reach)

    def test_y_at_interpolates_and_is_none_off_the_ends(self) -> None:
        self.assertAlmostEqual(self.slope.y_at(150), 490)
        self.assertIsNone(self.slope.y_at(99))
        self.assertIsNone(self.slope.y_at(201))

    def test_points_must_run_left_to_right(self) -> None:
        with self.assertRaises(ValueError):
            self.slopes.Slope([(200, 500), (100, 480)])

    def test_falling_onto_the_line_lands(self) -> None:
        slope, y = self.contact(150, prev_bottom=480, bottom=495, vy=5)
        self.assertIs(slope, self.slope)
        self.assertAlmostEqual(y, 490)

    def test_rising_through_the_line_never_lands(self) -> None:
        self.assertEqual(self.contact(150, prev_bottom=500, bottom=488, vy=-12), (None, None))

    def test_far_below_the_line_does_not_snap_up(self) -> None:
        # e.g. walking on the floor beneath a petal: walks through it.
        self.assertEqual(self.contact(150, prev_bottom=560, bottom=561, vy=1), (None, None))

    def test_stays_glued_walking_downhill(self) -> None:
        # Feet left slightly above the line after stepping downhill.
        slope, y = self.contact(120, prev_bottom=491, bottom=492, vy=0.9, current=self.slope)
        self.assertIs(slope, self.slope)
        self.assertAlmostEqual(y, 496)

    def test_walking_off_the_end_releases(self) -> None:
        self.assertEqual(self.contact(205, 480, 481, 0.9, current=self.slope), (None, None))


class Level3GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        layouts = _load_layouts()
        platforms = layouts["build_level_platforms"](3)
        cls.floor = platforms[0]
        cls.rects = platforms[4:]                      # 0-3 are the boundaries
        cls.slopes = layouts["build_level_slopes"](3)
        cls.wall = layouts["WALL"]
        cls.bhagwan = _FakeRect(*layouts["LEVEL3_BHAGWAN_RECT"])

    def test_platforms_sit_inside_the_playfield(self) -> None:
        for r in self.rects:
            with self.subTest(rect=(r.x, r.y, r.width)):
                self.assertGreaterEqual(r.left, self.wall)
                self.assertLessEqual(r.right, LOGICAL_WIDTH - self.wall)
                self.assertGreater(r.top, WORLD_Y_OFFSET)
                self.assertLess(r.bottom, self.floor.top)

    def test_no_spot_puts_the_devotee_inside_a_platform(self) -> None:
        """Where two surfaces overlap in x, standing on the lower one fits under the upper."""
        surfaces = list(self.rects) + [self.floor]
        for upper in self.rects:
            for lower in surfaces:
                if lower is upper or lower.top <= upper.top:
                    continue
                if min(upper.right, lower.right) <= max(upper.left, lower.left):
                    continue
                with self.subTest(upper=(upper.x, upper.y), lower=(lower.x, lower.y)):
                    self.assertGreaterEqual(lower.top - PLAYER_HEIGHT, upper.bottom)

    def test_standing_anywhere_on_a_slope_clears_every_platform(self) -> None:
        for slope in self.slopes:
            x = slope.left
            while x <= slope.right:
                body = _FakeRect(x - PLAYER_WIDTH / 2, slope.y_at(x) - PLAYER_HEIGHT,
                                 PLAYER_WIDTH, PLAYER_HEIGHT)
                for r in self.rects:
                    with self.subTest(slope_left=slope.left, x=x, rect=(r.x, r.y)):
                        self.assertFalse(body.colliderect(r))
                x += 4

    def test_slopes_sit_inside_the_playfield(self) -> None:
        for slope in self.slopes:
            with self.subTest(slope_left=slope.left):
                self.assertGreaterEqual(slope.left, self.wall)
                self.assertLessEqual(slope.right, LOGICAL_WIDTH - self.wall)
                for _, y in slope.points:
                    self.assertLess(y, self.floor.top)

    def _plinth(self):
        # monk_system.create_monk targets x 790, H - 454 for Level 3.
        matches = [r for r in self.rects
                   if abs(r.x - 790) < 5 and abs(r.y - (LOGICAL_HEIGHT - 454)) < 5]
        self.assertEqual(len(matches), 1, "Level 3 Monk plinth missing or duplicated")
        return matches[0]

    def test_monk_sacred_column_crosses_no_platform(self) -> None:
        plinth = self._plinth()
        monk_x = plinth.x + (plinth.width - MONK_WIDTH) // 2
        monk_y = plinth.y - MONK_HEIGHT
        column = _FakeRect(monk_x, self.wall, MONK_WIDTH, monk_y - self.wall)
        for r in self.rects:
            with self.subTest(rect=(r.x, r.y)):
                self.assertFalse(column.colliderect(r))

    def test_bhagwan_image_is_visible_and_crosses_no_platform(self) -> None:
        self.assertGreaterEqual(self.bhagwan.top, WORLD_Y_OFFSET + HUD_BAR_HEIGHT)
        plinth = self._plinth()
        self.assertLess(self.bhagwan.bottom + PLAYER_HEIGHT, plinth.top,
                        "the devotee must be able to stand on the plinth under the image")
        for r in self.rects:
            with self.subTest(rect=(r.x, r.y)):
                self.assertFalse(self.bhagwan.colliderect(r))


def _pygame_available() -> bool:
    return importlib.util.find_spec("pygame") is not None


@unittest.skipUnless(_pygame_available(), "needs pygame (runs locally in the venv, skipped on CI)")
class Level3RealPhysicsTests(unittest.TestCase):
    """Drive the real Player.update over the real Level 3 layout."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import level_scene
        import level_layouts
        import settings
        cls.Player = level_scene.Player
        cls.platforms = level_layouts.build_level_platforms(3)
        cls.slopes = level_layouts.build_level_slopes(3)
        cls.jump = settings.LEVEL_JUMP_FORCES[3]
        cls.speed = settings.PLAYER_SPEED

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def _stand_on(self, slope, center_x):
        p = self.Player(center_x - PLAYER_WIDTH / 2, slope.y_at(center_x) - PLAYER_HEIGHT)
        p.update(1 / 60, self.platforms, self.slopes)   # settle
        return p

    def test_walks_the_length_of_every_slope_both_ways(self) -> None:
        for fps in (60, 30):
            for slope in self.slopes:
                for direction in (1, -1):
                    with self.subTest(fps=fps, slope_left=slope.left, direction=direction):
                        start = slope.left + 16 if direction > 0 else slope.right - 16
                        p = self._stand_on(slope, start)
                        p.vx = self.speed * direction
                        while slope.left + 16 <= p.x + PLAYER_WIDTH / 2 <= slope.right - 16:
                            p.update(1 / fps, self.platforms, self.slopes)
                            self.assertIs(p.slope, slope)
                            self.assertTrue(p.on_ground)
                            self.assertAlmostEqual(p.y + PLAYER_HEIGHT,
                                                   slope.y_at(p.x + PLAYER_WIDTH / 2), delta=0.5)

    def test_jump_from_below_passes_up_through_a_petal_then_lands_on_it(self) -> None:
        petal = next(s for s in self.slopes if 300 < s.left < 330)  # 20, big pink lotus left
        floor_top = self.platforms[0].top
        p = self.Player(400, floor_top - PLAYER_HEIGHT)
        p.update(1 / 60, self.platforms, self.slopes)
        self.assertIsNone(p.slope, "standing on the floor under the petal, not on it")
        p.vy = self.jump
        landed_on = None
        for _ in range(240):
            p.update(1 / 60, self.platforms, self.slopes)
            if p.vy < 0:
                self.assertIsNone(p.slope)
            if p.on_ground:
                landed_on = p.slope
                break
        self.assertIs(landed_on, petal)

    def test_walking_the_floor_passes_under_the_petals(self) -> None:
        floor_top = self.platforms[0].top
        p = self.Player(250, floor_top - PLAYER_HEIGHT)
        p.vx = self.speed
        for _ in range(60):                     # 420px: through the whole of petal 20
            p.update(1 / 60, self.platforms, self.slopes)
            self.assertIsNone(p.slope)
            # Rect collision tests int(y), so a grounded devotee idles up to one
            # gravity step (0.9px) into the floor between frames — pre-existing.
            self.assertAlmostEqual(p.y + PLAYER_HEIGHT, floor_top, delta=1)

    def test_every_surface_is_reachable_without_touching_the_lake(self) -> None:
        """From the start (lily pad 18), with the floor deadly: all reachable, no dead ends."""
        import pygame
        floor = self.platforms[0]
        surfaces = {id(r): r for r in self.platforms[4:]}
        names = {id(r): f"rect({r.x},{r.y})" for r in self.platforms[4:]}
        names.update({id(s): f"slope({int(s.left)})" for s in self.slopes})
        names[id(floor)] = "floor"
        start = next(r for r in self.platforms[4:] if r.x == 137)       # 18, lower-left pad
        plinth = next(r for r in self.platforms[4:] if r.x == 790)

        def landing(p):
            if p.slope is not None:
                return id(p.slope)
            probe = pygame.Rect(int(p.x), int(p.y) + 1, p.width, p.height)
            for r in [floor] + list(surfaces.values()):
                if probe.colliderect(r) and p.y + p.height <= r.top + 2:
                    return id(r)
            return None

        def starts(key):
            if key == id(floor):
                return [(x, floor.top - PLAYER_HEIGHT) for x in range(40, 1860, 40)]
            if key in surfaces:
                r = surfaces[key]
                xs = list(range(r.left, r.right - PLAYER_WIDTH + 1, 20)) + [r.right - PLAYER_WIDTH]
                return [(x, r.top - PLAYER_HEIGHT) for x in xs]
            s = next(s for s in self.slopes if id(s) == key)
            return [(cx - PLAYER_WIDTH / 2, s.y_at(cx) - PLAYER_HEIGHT)
                    for cx in range(int(s.left) + 14, int(s.right) - 14, 20)]

        def moves(x, y):
            for vx in (-self.speed, 0, self.speed):
                yield vx, self.jump, None
                yield vx, 0, None                    # walk off
            for delay in (8, 16):
                for steer in (-self.speed, self.speed):
                    yield 0, self.jump, (delay, steer)

        def exits(key):
            """Surfaces reachable in one move from `key`. Landing in the lake does not count."""
            found = set()
            for x, y in starts(key):
                for vx, vy, steer in moves(x, y):
                    p = self.Player(x, y)
                    p.update(1 / 60, self.platforms, self.slopes)
                    if landing(p) != key:
                        break                        # not a real standing spot
                    p.vx, p.vy = vx, vy
                    airborne = False
                    for frame in range(200):
                        if steer and frame == steer[0]:
                            p.vx = steer[1]
                        p.update(1 / 60, self.platforms, self.slopes)
                        if not p.on_ground:
                            airborne = True
                        elif airborne:
                            dest = landing(p)
                            if dest is not None and dest != id(floor):
                                found.add(dest)
                            break
                        elif frame > 60:
                            break                    # walked into a wall; never left the ground
            return found

        graph = {}
        seen, frontier = {id(start)}, [id(start)]
        while frontier:
            key = frontier.pop()
            graph[key] = exits(key)
            for dest in graph[key] - seen:
                seen.add(dest)
                frontier.append(dest)
        everything = set(surfaces) | {id(s) for s in self.slopes}
        self.assertGreaterEqual(len(everything), 20, "expected 16 platforms + 4 slopes")
        unreachable = sorted(names[k] for k in everything - seen)
        self.assertEqual(unreachable, [], f"unreachable Level 3 surfaces: {unreachable}")

        def can_reach_plinth(key):
            done, todo = {key}, [key]
            while todo:
                for dest in graph[todo.pop()] - done:
                    done.add(dest)
                    todo.append(dest)
            return id(plinth) in done
        dead_ends = sorted(names[k] for k in seen if not can_reach_plinth(k))
        self.assertEqual(dead_ends, [], f"surfaces the pavilion cannot be reached from: {dead_ends}")


@unittest.skipUnless(_pygame_available(), "needs pygame (runs locally in the venv, skipped on CI)")
class Level3SceneTests(unittest.TestCase):
    """Drive the real LevelScene for Level 3: drowning, box placement, reveal order."""

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
        from box_system import CAT_GOAL
        cls.pygame = pygame
        cls.ls = level_scene
        cls.CAT_GOAL = CAT_GOAL
        cls.manager = SceneManager()
        cls.manager.shared["game_mode"] = "developer"
        cls.input = InputManager()
        cls.scene = level_scene.LevelScene(cls.manager, AssetManager(), cls.input)

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def setUp(self) -> None:
        self.scene.on_enter(level=3, input_mgr=self.input)

    def run_frames(self, seconds):
        for _ in range(int(seconds * 60) + 2):
            self.scene.update(1 / 60)

    def test_starts_standing_on_lily_pad_18(self) -> None:
        self.run_frames(0.5)
        p = self.scene.player
        self.assertEqual(self.scene.drown_timer, 0)
        self.assertTrue(p.on_ground)
        self.assertEqual(p.y + PLAYER_HEIGHT, LOGICAL_HEIGHT - 154)
        self.assertTrue(137 <= p.x and p.x + PLAYER_WIDTH <= 137 + 169)

    def test_falling_into_the_lake_costs_30s_and_rises_on_the_last_golden_surface(self) -> None:
        self.run_frames(0.5)
        safe = self.scene.last_safe_pos
        before = self.scene.time_remaining
        p = self.scene.player
        p.x, p.y = 1000, 700            # over open water: nothing below until the floor
        for _ in range(120):
            self.scene.update(1 / 60)
            if self.scene.drown_timer > 0:
                break
        self.assertGreater(self.scene.drown_timer, 0, "never drowned")
        self.assertAlmostEqual(before - self.scene.time_remaining, 30, delta=3)
        self.run_frames(self.ls.DROWN_SECONDS)
        self.assertEqual(self.scene.drown_timer, 0)
        self.assertAlmostEqual(p.x, safe[0], delta=1)
        self.assertAlmostEqual(p.y, safe[1], delta=1)    # idles up to 0.9px, as on any ledge
        self.run_frames(0.2)
        self.assertTrue(p.on_ground)
        self.assertEqual(self.scene.drown_timer, 0, "rose again straight into the lake")

    def test_no_box_is_ever_placed_in_the_lake(self) -> None:
        import random
        floor_top = self.scene.floor.top
        for seed in range(25):
            random.seed(seed)
            self.scene.on_enter(level=3, input_mgr=self.input)
            with self.subTest(seed=seed):
                self.assertEqual(len(self.scene.box_system.boxes), 6)
                for box in self.scene.box_system.boxes:
                    self.assertNotEqual(box.y + box.SIZE + 5, floor_top)

    def test_monk_fades_before_bhagwan_appears_and_offering_waits_for_it(self) -> None:
        s = self.scene
        self.assertEqual((s.monk.x, s.monk.y + s.monk.HEIGHT), (924, LOGICAL_HEIGHT - 454))
        s.player.x, s.player.y = s.monk.x + 20, LOGICAL_HEIGHT - 454 - PLAYER_HEIGHT
        goal = next(b for b in s.box_system.boxes if b.item["cat"] == self.CAT_GOAL)
        s.item_popup = {"item": goal.item, "time_delta": 0, "freeze_dur": 0, "message": "", "timer": 5.0}
        s._dismiss_item_popup()
        self.assertFalse(s.level_complete, "finding the Akshat must not end Level 3")
        column = s.monk_column
        self.run_frames(self.ls.MONK_FADE_SECONDS / 2)
        self.assertEqual(s.reveal_phase, "monk_fading")
        self.assertFalse(s._at_level3_offering_spot())
        self.run_frames(self.ls.MONK_FADE_SECONDS / 2)
        self.assertEqual(s.reveal_phase, "bhagwan_appearing")
        self.assertEqual(s.monk.opacity, 0)
        self.assertFalse(any(p is column for p in s.platforms), "Monk's column not lifted")
        self.assertFalse(s._at_level3_offering_spot(), "offering allowed before the image is fully shown")
        self.run_frames(self.ls.BHAGWAN_APPEAR_SECONDS)
        self.assertEqual(s.reveal_phase, "ready")
        self.assertTrue(s._at_level3_offering_spot())
        self.input.just_pressed[self.input.ACTION] = True
        try:
            s.handle_events([], self.input)
        finally:
            self.input.just_pressed[self.input.ACTION] = False
        self.assertTrue(s.level_complete)


if __name__ == "__main__":
    unittest.main()
