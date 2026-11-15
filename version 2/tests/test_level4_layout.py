"""Level 4 (Kailash): the ledges, the crumbling rule, cold shock and the summit gate.

Three layers:

* ``CrumblingRuleTests`` exercise the pure rule in ``src/crumbling.py``.
* ``Level4RouteTests`` make every jump on the designer-confirmed route with the
  real ``Player.update``: both ways up, and out of the valley from the floor.
* ``Level4SceneTests`` run the real ``LevelScene``: the clock doubles on the
  valley floor and nowhere else, a ledge leaves and rejoins the platform list,
  and the gate is not there until the Akshat is found.

The last two need pygame, so they are skipped on the dependency-free CI worker
and run locally in the project venv.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest

from test_rescues import StubInput


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DT = 1 / 60
NEEDS_PYGAME = unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                                   "needs pygame (runs locally in the venv, skipped on CI)")


def _load_crumbling():
    spec = importlib.util.spec_from_file_location("crumbling", SRC / "crumbling.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CrumblingRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.c = _load_crumbling()
        self.ledge = self.c.CrumblingLedge(rect=object())

    def run_for(self, seconds, stood_on=False, clear=True):
        events = []
        for _ in range(round(seconds * 60)):
            events.append(self.ledge.update(DT, stood_on, clear))
        return [e for e in events if e]

    def test_it_holds_until_someone_stands_on_it(self) -> None:
        self.assertEqual(self.run_for(10), [])
        self.assertEqual(self.ledge.state, self.c.SOLID)

    def test_it_cracks_for_one_second_then_breaks(self) -> None:
        self.ledge.update(DT, True)
        self.assertEqual(self.run_for(0.9, stood_on=True), [])
        self.assertEqual(self.ledge.state, self.c.CRACKING)
        self.assertEqual(self.run_for(0.2, stood_on=True), ["broke"])

    def test_stepping_off_does_not_save_it(self) -> None:
        self.ledge.update(DT, True)
        self.assertEqual(self.run_for(1.1, stood_on=False), ["broke"])

    def test_it_returns_three_seconds_after_breaking(self) -> None:
        self.ledge.update(DT, True)
        self.run_for(1.1)
        self.assertEqual(self.run_for(2.8), [])
        self.assertEqual(self.run_for(0.3), ["returned"])
        self.assertEqual(self.ledge.state, self.c.SOLID)

    def test_it_never_closes_around_the_devotee(self) -> None:
        self.ledge.update(DT, True)
        self.run_for(1.1)
        self.assertEqual(self.run_for(6, clear=False), [])
        self.assertEqual(self.run_for(0.1, clear=True), ["returned"])

    def test_one_timing_for_every_mode(self) -> None:
        """Designer, 2026-11-13: no longer hold in kid mode."""
        self.assertEqual((self.c.CRACK_SECONDS, self.c.GONE_SECONDS), (1.0, 3.0))


class _PygameCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import debug_monitor
        debug_monitor.monitor.enabled = False
        import level_layouts
        import level_scene
        import monk_system
        import settings
        cls.pygame, cls.layouts, cls.level_scene = pygame, level_layouts, level_scene
        cls.monk_system, cls.settings = monk_system, settings

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))


@NEEDS_PYGAME
class Level4RouteTests(_PygameCase):
    """Every arrow on the confirmed proposal is one jump the real Player can make."""

    def setUp(self) -> None:
        L, s, Monk = self.layouts, self.settings, self.monk_system.Monk
        self.platforms = L.build_level_platforms(4)
        # The Monk's sacred column stands in the level too: ceiling down to his head.
        x, top, width = L.LEVEL4_MONK_SHELF
        monk_x = x + width - Monk.WIDTH - 24
        self.platforms.append(self.pygame.Rect(monk_x, L.WALL, Monk.WIDTH, top - Monk.HEIGHT - L.WALL))
        self.floor = (L.WALL, s.LOGICAL_HEIGHT - L.WALL, s.LOGICAL_WIDTH - 2 * L.WALL)
        self.jump = s.LEVEL_JUMP_FORCES[4]

    def step(self, p, move, jump):
        p.vx += (move * self.settings.PLAYER_SPEED - p.vx) * 15 * DT
        if jump and p.on_ground:
            p.vy = self.jump
        p.update(DT, self.platforms)

    def standing_on(self, p, ledge):
        x, top, width = ledge
        return p.on_ground and abs(p.y + p.height - top) < 2 and x - p.width < p.x < x + width

    def one_jump(self, a, b):
        """Brute force: take-off spot, direction, and how long the direction is held."""
        Player, height = self.level_scene.Player, self.settings.PLAYER_HEIGHT
        ax, atop, awidth = a
        for start_x in range(int(ax) - 20, int(ax + awidth), 12):
            for move in (-1, 1):
                for hold in (0, 6, 12, 18, 25, 32, 40, 50, 60, 80):
                    p = Player(start_x, atop - height)
                    p.update(DT, self.platforms)
                    if not self.standing_on(p, a):
                        continue
                    self.step(p, move, True)
                    for i in range(200):
                        self.step(p, move if i < hold else 0, False)
                        if p.on_ground:
                            break
                    if self.standing_on(p, b):
                        return True
        return False

    def test_both_ways_up_and_the_spire_detour(self) -> None:
        L = self.layouts
        start, block, ice, mesa, spire, plateau, outcrop, terrace, ridge, monk, summit = L.LEVEL4_LEDGES
        route = [("start", start, "stream block", block), ("stream block", block, "ice shelf", ice),
                 # left, over the mesa
                 ("ice shelf", ice, "great mesa", mesa), ("great mesa", mesa, "spire", spire),
                 ("great mesa", mesa, "high plateau", plateau), ("high plateau", plateau, "summit", summit),
                 # right, past the Monk
                 ("ice shelf", ice, "rock outcrop", outcrop), ("rock outcrop", outcrop, "right terrace", terrace),
                 ("right terrace", terrace, "right ridge", ridge), ("right ridge", ridge, "Monk's shelf", monk),
                 ("Monk's shelf", monk, "summit", summit)]
        for name_a, a, name_b, b in route:
            with self.subTest(jump=f"{name_a} to {name_b}"):
                self.assertTrue(self.one_jump(a, b))

    def test_cold_shock_can_always_be_escaped(self) -> None:
        """From the valley floor there is a jump back to a ledge on each side of the stream."""
        L = self.layouts
        for name, ledge in (("start shelf", L.LEVEL4_LEDGES[0]), ("stream block", L.LEVEL4_LEDGES[1]),
                            ("rock outcrop", L.LEVEL4_LEDGES[6])):
            with self.subTest(out_to=name):
                self.assertTrue(self.one_jump(self.floor, ledge))

    def test_every_ledge_can_be_seen(self) -> None:
        """A devotee standing anywhere is below the clock bar: the world is drawn 80px
        up and the bar is 48px, so nothing above world y 128 is ever shown."""
        for x, top, width in self.layouts.LEVEL4_LEDGES:
            self.assertGreaterEqual(top - self.settings.PLAYER_HEIGHT, 128, (x, top, width))


@NEEDS_PYGAME
class Level4SceneTests(_PygameCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from asset_manager import AssetManager
        from scene_manager import SceneManager
        cls.assets, cls.SceneManager = AssetManager(), SceneManager

    def setUp(self) -> None:
        self.input = StubInput()
        self.manager = self.SceneManager()
        self.manager.shared["game_mode"] = "kid"
        self.scene = self.level_scene.LevelScene(self.manager, self.assets, self.input)
        self.manager.register(self.settings.SCENE_LEVEL, self.scene)
        self.manager.switch_to(self.settings.SCENE_LEVEL, level=4, input_mgr=self.input)

    def frames(self, seconds):
        for _ in range(round(seconds * 60)):
            self.scene.update(DT)

    def put_on(self, x, top):
        p = self.scene.player
        p.x, p.y, p.vx, p.vy = x, top - p.height, 0.0, 0.0

    def test_the_devotee_starts_on_the_shelf_not_in_the_cold(self) -> None:
        self.frames(1.0)
        self.assertFalse(self.scene.cold_shock)
        self.assertAlmostEqual(self.scene.player.y + self.scene.player.height,
                               self.layouts.LEVEL4_START_SHELF[1], delta=2)

    def test_the_clock_runs_double_on_the_valley_floor_and_only_there(self) -> None:
        self.frames(0.5)
        before = self.scene.time_remaining
        self.frames(2.0)
        self.assertAlmostEqual(before - self.scene.time_remaining, 2.0, delta=0.05)

        self.put_on(600, self.scene.floor.top)
        self.frames(0.2)
        self.assertTrue(self.scene.cold_shock)
        before = self.scene.time_remaining
        self.frames(2.0)
        self.assertAlmostEqual(before - self.scene.time_remaining, 4.0, delta=0.05)

    def test_nobody_is_lifted_out_and_a_jump_from_the_floor_is_still_cold(self) -> None:
        self.put_on(600, self.scene.floor.top)
        self.frames(1.0)
        self.assertAlmostEqual(self.scene.player.x, 600, delta=1, msg="left where they fell")
        self.input.tap(self.input.JUMP)
        self.scene.update(DT)
        self.input.clear_taps()
        self.frames(0.3)
        self.assertFalse(self.scene.player.on_ground)
        self.assertTrue(self.scene.cold_shock, "in the air above the floor is not safe ground")

    def test_a_ledge_ends_the_cold(self) -> None:
        self.put_on(600, self.scene.floor.top)
        self.frames(0.2)
        x, top, _ = self.layouts.LEVEL4_LEDGES[1]
        self.put_on(x + 40, top)
        self.frames(0.2)
        self.assertFalse(self.scene.cold_shock)

    def test_the_spire_gives_way_and_comes_back(self) -> None:
        x, top, width = self.layouts.LEVEL4_CRUMBLING[0]
        ledge = next(c for c in self.scene.crumbling if c.rect.width == width)
        self.put_on(x + 15, top)
        self.frames(0.9)
        self.assertIn(ledge.rect, self.scene.platforms)
        self.frames(0.3)
        self.assertFalse(any(p is ledge.rect for p in self.scene.platforms), "broken after a second")
        self.frames(1.0)
        self.assertGreater(self.scene.player.y + self.scene.player.height, top + 50, "the devotee fell")
        self.assertFalse(self.scene.cold_shock, "the mesa caught the fall, not the valley")
        self.frames(3.0)
        self.assertTrue(any(p is ledge.rect for p in self.scene.platforms), "back after three more")

    def test_no_box_on_the_floor_a_crumbling_ledge_the_monks_shelf_or_the_summit(self) -> None:
        allowed = {top for _, top, _ in self.layouts.LEVEL4_BOX_LEDGES}
        boxes = self.scene.box_system.boxes
        tops = [box.y + box.SIZE + 5 for box in boxes]
        self.assertTrue(all(top in allowed for top in tops), tops)
        ledges = [(top, next(x for x, t, w in self.layouts.LEVEL4_BOX_LEDGES if t == top and x <= box.x <= x + w))
                  for top, box in zip(tops, boxes)]
        self.assertEqual(len(set(ledges)), len(boxes), "one box to a ledge")

    def test_the_monk_sits_on_his_shelf(self) -> None:
        x, top, width = self.layouts.LEVEL4_MONK_SHELF
        monk = self.scene.monk
        self.assertEqual(monk.y + monk.HEIGHT, top)
        self.assertTrue(x <= monk.x and monk.x + monk.WIDTH <= x + width)

    def test_the_gate_is_not_there_until_the_akshat_is_found(self) -> None:
        x, top, width = self.layouts.LEVEL4_SUMMIT
        self.put_on(x + width // 2, top)
        self.frames(0.2)
        self.input.tap(self.input.ACTION)
        self.scene.handle_events([], self.input)
        self.assertFalse(self.scene.level_complete, "no gate, nothing to enter")

        self.scene.box_system.goal_found = True
        self.scene.handle_events([], self.input)
        self.assertTrue(self.scene.level_complete)

    def test_finding_the_akshat_does_not_end_the_level(self) -> None:
        goal = next(b for b in self.scene.box_system.boxes if b.item["cat"] == "goal")
        self.scene.item_popup = {"item": goal.item, "time_delta": 0, "freeze_dur": 0, "timer": 0}
        self.scene.box_system.goal_found = True
        self.scene._dismiss_item_popup()
        self.assertFalse(self.scene.level_complete)
        self.assertGreater(self.scene.gate_appear_timer, 0, "the gate begins to appear")

    def test_the_gate_stands_clear_of_the_clock_bar(self) -> None:
        self.assertGreaterEqual(self.scene._summit_gate_rect().top, 128)


if __name__ == "__main__":
    unittest.main()
