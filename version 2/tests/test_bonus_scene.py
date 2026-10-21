"""Karuna bonus level tests (Epic G2): the clock, the outcomes, and the round trip.

The bonus level is the glimpse of the punya's fruit that the Namokar Mantra opens.
Its four minutes are the four that used to be a flat +4:00: both rescues done banks
whatever is left, running the clock out banks nothing, and either way Level 3 is
resumed in place with its own clock untouched.

The two rescues are G3, so these tests set ``injured_saved`` / ``lost_saved`` by hand
to stand in for them.

Needs pygame, so it is skipped on the dependency-free CI worker and runs locally in
the project venv (like ``test_transitions``).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class BonusWiringTests(unittest.TestCase):
    """Source-level checks that need neither pygame nor a display."""

    def test_main_registers_the_bonus_scene(self) -> None:
        main_src = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("from bonus_scene import BonusScene", main_src)
        self.assertRegex(main_src, r"register\(\s*SCENE_BONUS\s*,\s*BonusScene\(")

    def test_the_flat_jiv_daya_bonus_is_gone(self) -> None:
        """Q6: the +4:00 became the bonus clock, so nothing may award it directly."""
        for name in ("level_scene.py", "settings.py"):
            with self.subTest(file=name):
                self.assertNotIn("JIV_DAYA_TIME_BONUS",
                                 (SRC / name).read_text(encoding="utf-8"))

    def test_the_bonus_clock_is_the_four_minutes_it_replaced(self) -> None:
        settings_src = (SRC / "settings.py").read_text(encoding="utf-8")
        found = re.search(r"^BONUS_TIME_LIMIT\s*=\s*(\d+)", settings_src, re.M)
        self.assertIsNotNone(found, "BONUS_TIME_LIMIT not found")
        self.assertEqual(int(found.group(1)), 240)


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class BonusSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import bonus_scene
        import debug_monitor
        import level_scene
        import settings

        # The monitor is off by default and its writes are now encoding-safe
        # (see tests/test_debug_monitor.py), but these tests must not depend on
        # debug logging either way.
        cls._monitor = debug_monitor.monitor
        cls._monitor_was_enabled = cls._monitor.enabled
        cls._monitor.enabled = False
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
        cls.bonus_scene = bonus_scene
        cls.level_scene = level_scene
        cls.SceneManager = SceneManager
        cls.RecordingManager = RecordingManager
        cls.assets = AssetManager()
        cls.input = InputManager()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._monitor.enabled = cls._monitor_was_enabled
        sys.path.remove(str(SRC))

    def enter(self):
        manager = self.RecordingManager()
        scene = self.bonus_scene.BonusScene(manager, self.assets, self.input)
        scene.on_enter(input_mgr=self.input)
        return manager, scene

    def run_for(self, scene, seconds, step=1 / 60):
        for _ in range(int(seconds / step)):
            scene.update(step)

    # ── the clock ─────────────────────────────────────────────────────────────

    def test_starts_on_a_four_minute_clock_and_counts_down(self) -> None:
        _, scene = self.enter()
        self.assertEqual(scene.time_remaining, float(self.settings.BONUS_TIME_LIMIT))

        self.run_for(scene, 10.0)

        self.assertAlmostEqual(scene.time_remaining,
                               self.settings.BONUS_TIME_LIMIT - 10.0, delta=0.2)
        self.assertIsNone(scene.outcome, "still playing")

    # ── failure: the clock runs out ───────────────────────────────────────────

    def test_running_out_of_time_is_failure_and_banks_nothing(self) -> None:
        manager, scene = self.enter()

        self.run_for(scene, self.settings.BONUS_TIME_LIMIT + 1.0)

        self.assertEqual(scene.outcome, "out_of_time")
        self.assertEqual(scene.banked, 0.0)
        self.assertEqual(scene.time_remaining, 0.0, "the clock never goes negative")
        self.assertEqual(manager.switches, [], "holds the closing card before returning")

        self.run_for(scene, self.bonus_scene.OUTCOME_HOLD_SECONDS + 0.5)

        self.assertEqual(manager.shared["bonus_banked_seconds"], 0.0)
        self.assert_returns_home(manager)

    # ── success: both rescues ─────────────────────────────────────────────────

    def test_both_rescues_bank_the_time_that_is_left(self) -> None:
        manager, scene = self.enter()
        self.run_for(scene, 30.0)
        left = scene.time_remaining

        scene.injured_saved = True          # G3 will set these
        scene.lost_saved = True
        scene.update(1 / 60)

        self.assertEqual(scene.outcome, "saved")
        self.assertAlmostEqual(scene.banked, left, delta=0.2)
        self.assertLess(scene.banked, self.settings.BONUS_TIME_LIMIT,
                        "dawdling banks less — the reward scales")

        self.run_for(scene, self.bonus_scene.OUTCOME_HOLD_SECONDS + 0.5)

        self.assertAlmostEqual(manager.shared["bonus_banked_seconds"], left, delta=0.2)
        self.assert_returns_home(manager)

    def test_one_rescue_alone_banks_nothing(self) -> None:
        """Q8: all or nothing."""
        _, scene = self.enter()
        scene.injured_saved = True

        self.run_for(scene, 30.0)

        self.assertIsNone(scene.outcome, "one rescue does not end the detour")
        self.assertEqual(scene.banked, 0.0)

    def assert_returns_home(self, manager):
        self.assertTrue(manager.switches, "returned to the Hall")
        key, kwargs = manager.switches[-1]
        self.assertEqual(key, self.settings.SCENE_LEVEL)
        self.assertEqual(kwargs.get("level"), self.bonus_scene.HOME_LEVEL)
        self.assertTrue(kwargs.get("resume"), "resumed in place, not rebuilt (G1)")

    # ── Level 3 is untouched while the detour plays ───────────────────────────

    def test_level3s_clock_does_not_run_while_the_bonus_scene_is_active(self) -> None:
        manager = self.SceneManager()
        level = self.level_scene.LevelScene(manager, self.assets, self.input)
        bonus = self.bonus_scene.BonusScene(manager, self.assets, self.input)
        manager.register(self.settings.SCENE_LEVEL, level)
        manager.register(self.settings.SCENE_BONUS, bonus)

        manager.switch_to(self.settings.SCENE_LEVEL, level=3, input_mgr=self.input)
        level.player.x = 640.0
        manager.update(1 / 60)
        clock_before = level.time_remaining

        manager.switch_to(self.settings.SCENE_BONUS, input_mgr=self.input)
        for _ in range(120):
            manager.update(1 / 60)

        self.assertEqual(level.time_remaining, clock_before, "the Hall's clock is paused")
        self.assertEqual(level.player.x, 640.0, "and the devotee has not moved")

    # ── the mantra now opens the detour instead of paying out ─────────────────

    def test_saving_the_bird_opens_the_bonus_scene_and_adds_no_flat_time(self) -> None:
        manager = self.RecordingManager()
        manager.scenes[self.settings.SCENE_BONUS] = object()   # registered, so routing happens
        level = self.level_scene.LevelScene(manager, self.assets, self.input)
        level.on_enter(level=3, input_mgr=self.input)

        clock_before = level.time_remaining
        level.rescue_phase = "reviving"
        level.bird.state = "leaving"            # the revival has finished
        level._update_rescue(1 / 60)

        self.assertTrue(level.bird_saved)
        self.assertEqual(level.time_remaining, clock_before, "no flat +4:00 any more (Q6)")
        self.assertEqual(level.jiv_daya_bonus, 0.0)
        self.assertEqual([k for k, _ in manager.switches], [self.settings.SCENE_BONUS])

    # ── drawing ───────────────────────────────────────────────────────────────

    def test_draws_without_crashing_while_playing_and_on_both_outcomes(self) -> None:
        surf = self.pygame.Surface((1920, 1080))
        for setup in (lambda s: None,
                      lambda s: s._finish("saved"),
                      lambda s: s._finish("out_of_time")):
            with self.subTest(setup=setup):
                _, scene = self.enter()
                self.run_for(scene, 2.0)
                setup(scene)
                scene.draw(surf)


if __name__ == "__main__":
    unittest.main()
