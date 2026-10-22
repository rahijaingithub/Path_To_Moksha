"""The two rescues in the Karuna bonus level (Epic G3).

Two kinds of help, so two verbs plus a third at the end of the first:

* the **injured** man is *carried* to the hospital and *treated* there — his body;
* the **lost** man is *led*, and recognises the temple himself — his soul.

Driven through the real scene with a stub input device, so the tests exercise the
same ACTION handling and movement the player does.

Needs pygame, so it is skipped on the dependency-free CI worker and runs locally in
the project venv.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class StubInput:
    """Holds whatever is pressed. Mirrors InputManager's two dicts and its keys."""

    LEFT, RIGHT, UP = "left", "right", "up"
    JUMP, ACTION, BACK = "jump", "action", "back"
    MENU_UP, MENU_DOWN, MENU_LEFT, MENU_RIGHT = "menu_up", "menu_down", "menu_left", "menu_right"
    MENU_SELECT, MENU_BACK = "menu_select", "menu_back"

    def __init__(self):
        keys = (self.LEFT, self.RIGHT, self.UP, self.JUMP, self.ACTION, self.BACK,
                self.MENU_UP, self.MENU_DOWN, self.MENU_LEFT, self.MENU_RIGHT,
                self.MENU_SELECT, self.MENU_BACK)
        self.actions = {k: False for k in keys}
        self.just_pressed = {k: False for k in keys}

    def hold(self, key):
        self.actions[key] = True

    def release_all(self):
        for k in self.actions:
            self.actions[k] = False

    def tap(self, key):
        self.just_pressed[key] = True

    def clear_taps(self):
        for k in self.just_pressed:
            self.just_pressed[k] = False


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class RescueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((64, 64))
        import bonus_scene
        import rescue_npc
        from asset_manager import AssetManager
        from scene_manager import SceneManager

        class RecordingManager(SceneManager):
            def __init__(self):
                super().__init__()
                self.switches = []

            def switch_to(self, key, input_mgr=None, **kwargs):
                self.switches.append((key, kwargs))

        cls.pygame = pygame
        cls.bonus_scene = bonus_scene
        cls.rescue_npc = rescue_npc
        cls.RecordingManager = RecordingManager
        cls.assets = AssetManager()

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def setUp(self) -> None:
        self.input = StubInput()
        self.manager = self.RecordingManager()
        self.scene = self.bonus_scene.BonusScene(self.manager, self.assets, self.input)
        self.scene.on_enter(input_mgr=self.input)

    # ── helpers that play the level the way a player would ────────────────────

    def step(self, seconds=1 / 60):
        self.scene.update(seconds)

    def act(self):
        """One ACTION press, consumed like the real input manager consumes it."""
        self.input.tap(self.input.ACTION)
        self.scene.handle_events([], self.input)
        self.input.clear_taps()

    def walk_to(self, x, limit_seconds=30.0):
        """Hold a direction until the devotee is there (or give up)."""
        self.input.release_all()
        steps = int(limit_seconds * 60)
        for _ in range(steps):
            if abs(self.scene.player_x - x) <= 6:
                break
            self.input.release_all()
            self.input.hold(self.input.RIGHT if x > self.scene.player_x else self.input.LEFT)
            self.step()
        self.input.release_all()

    # ── walking ───────────────────────────────────────────────────────────────

    def test_the_devotee_walks_both_ways_and_stays_on_screen(self) -> None:
        start = self.scene.player_x
        self.input.hold(self.input.RIGHT)
        for _ in range(30):
            self.step()
        self.assertGreater(self.scene.player_x, start)
        self.assertTrue(self.scene.facing_right)

        self.input.release_all()
        self.input.hold(self.input.LEFT)
        for _ in range(600):
            self.step()
        self.assertFalse(self.scene.facing_right)
        self.assertGreaterEqual(self.scene.player_x, self.bonus_scene.PLAYER_HALF_W,
                                "the left wall holds")

    # ── the injured man: carry, then treat ────────────────────────────────────

    def test_the_injured_man_is_carried_then_treated_at_the_hospital(self) -> None:
        s = self.scene
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()
        self.assertEqual(s.injured.state, "carried")
        self.assertTrue(s.carrying)

        # He travels with the devotee rather than staying put.
        self.walk_to(self.bonus_scene.HOSPITAL_X)
        self.assertAlmostEqual(s.injured.x, s.player_x, delta=1.0)
        self.assertFalse(s.injured_saved, "carrying him is not yet helping him")

        self.act()                                   # begin tending to him
        self.assertEqual(s.injured.state, "treating")
        self.assertGreater(s.treat_timer, 0)
        self.assertFalse(s.injured_saved, "treatment takes a moment")

        for _ in range(int(self.bonus_scene.TREAT_SECONDS * 60) + 4):
            self.step()
        self.assertTrue(s.injured_saved)
        self.assertEqual(s.injured.state, "delivered")

    def test_he_cannot_be_treated_anywhere_but_the_hospital(self) -> None:
        s = self.scene
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()
        self.assertEqual(s.injured.state, "carried")

        self.act()                                   # still out in the open
        self.assertEqual(s.injured.state, "carried", "no hospital here")
        self.assertEqual(s.treat_timer, 0)

    def test_carrying_a_man_is_slower_than_walking_free(self) -> None:
        s = self.scene
        self.input.hold(self.input.RIGHT)
        before = s.player_x
        for _ in range(30):
            self.step()
        free = s.player_x - before
        self.input.release_all()

        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()
        self.input.hold(self.input.LEFT)
        before = s.player_x
        for _ in range(30):
            self.step()
        carried = abs(s.player_x - before)
        self.input.release_all()

        self.assertLess(carried, free, "compassion costs effort")

    # ── the lost man: lead him, and he knows the temple ───────────────────────

    def test_the_lost_man_casts_about_until_he_is_offered_the_way(self) -> None:
        s = self.scene
        start = s.lost.x
        moved = False
        for _ in range(240):
            self.step()
            if abs(s.lost.x - start) > 10:
                moved = True
        self.assertTrue(moved, "he wanders, looking for the way")
        self.assertLessEqual(abs(s.lost.x - s.lost.home_x), self.rescue_npc.WANDER_SPAN + 2,
                             "but never strays far")

    def test_the_lost_man_follows_and_knows_the_temple_when_he_reaches_it(self) -> None:
        s = self.scene
        self.walk_to(s.lost.x)
        self.act()
        self.assertEqual(s.lost.state, "following")

        self.walk_to(self.bonus_scene.TEMPLE_X)
        for _ in range(240):                         # he trails a little behind
            if s.lost_saved:
                break
            self.step()

        self.assertTrue(s.lost_saved, "no second button press — he recognises it himself")
        self.assertEqual(s.lost.state, "delivered")

    def test_he_is_not_delivered_by_the_devotee_visiting_the_temple_alone(self) -> None:
        s = self.scene
        self.walk_to(self.bonus_scene.TEMPLE_X)
        for _ in range(120):
            self.step()
        self.assertFalse(s.lost_saved, "he was left behind, so nobody was guided")
        self.assertEqual(s.lost.state, "waiting")

    # ── both, and the banking ─────────────────────────────────────────────────

    def test_doing_both_ends_the_detour_and_banks_the_time_that_is_left(self) -> None:
        s = self.scene
        self.walk_to(s.lost.x)
        self.act()                                   # lead the lost man
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()                                   # and carry the injured one
        self.walk_to(self.bonus_scene.HOSPITAL_X)
        self.act()
        for _ in range(int(self.bonus_scene.TREAT_SECONDS * 60) + 4):
            self.step()
        self.assertTrue(s.injured_saved)

        self.walk_to(self.bonus_scene.TEMPLE_X)
        for _ in range(360):
            if s.outcome is not None:
                break
            self.step()

        self.assertTrue(s.both_rescued)
        self.assertEqual(s.outcome, "saved")
        self.assertGreater(s.banked, 0, "time left over comes back")
        self.assertLess(s.banked, self.bonus_scene.BONUS_TIME_LIMIT)

    def test_the_hint_names_the_verb_within_reach(self) -> None:
        s = self.scene
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.step()
        self.assertIn("lift", s.hint.lower())
        self.act()
        self.step()
        self.assertIn("hospital", s.hint.lower())

    # ── the G5 art drops in without a code change ─────────────────────────────

    def test_art_is_used_for_each_pose_when_the_files_exist(self) -> None:
        """RescueNPC prefers a pose image over its procedural figure, and scales it."""
        npc = self.rescue_npc.RescueNPC(self.rescue_npc.KIND_INJURED, 400, 900,
                                        {"sitting": self.pygame.Surface((300, 300), self.pygame.SRCALPHA),
                                         "carried": self.pygame.Surface((300, 300), self.pygame.SRCALPHA)})
        self.assertEqual(npc._pose_image("sitting", self.rescue_npc.SIT_DRAW_HEIGHT).get_height(),
                         self.rescue_npc.SIT_DRAW_HEIGHT)
        self.assertEqual(npc._pose_image("carried", self.rescue_npc.CARRY_DRAW_HEIGHT).get_height(),
                         self.rescue_npc.CARRY_DRAW_HEIGHT)
        self.assertIsNone(npc._pose_image("walk", 100), "absent poses fall back")

    def test_a_four_frame_walk_strip_cycles_and_is_scaled(self) -> None:
        strip = self.pygame.Surface((128 * 4, 128), self.pygame.SRCALPHA)
        npc = self.rescue_npc.RescueNPC(self.rescue_npc.KIND_LOST, 400, 900, {"walk": strip})
        frame = npc._walk_image()
        self.assertEqual(frame.get_height(), self.rescue_npc.DRAW_HEIGHT)
        self.assertEqual(frame.get_width(), self.rescue_npc.DRAW_HEIGHT, "square frames stay square")

    def test_missing_art_never_draws_the_pink_placeholder(self) -> None:
        """The scene checks the file exists first, so nothing loads a placeholder."""
        self.assertEqual(self.scene.injured.poses, {}, "no G5 art on disk yet")
        self.assertEqual(self.scene.lost.poses, {})

    def test_the_time_left_reaches_the_hall_end_to_end(self) -> None:
        """Both rescues → the Hall resumes with exactly those seconds banked (G2+G4)."""
        import level_scene
        from scene_manager import SceneManager
        import settings

        manager = SceneManager()
        level = level_scene.LevelScene(manager, self.assets, self.input)
        manager.register(settings.SCENE_LEVEL, level)
        manager.register(settings.SCENE_BONUS,
                         self.bonus_scene.BonusScene(manager, self.assets, self.input))
        manager.switch_to(settings.SCENE_LEVEL, level=3, input_mgr=self.input)
        clock_in_the_hall = level.time_remaining

        manager.switch_to(settings.SCENE_BONUS, input_mgr=self.input)
        bonus = manager.active_scene
        bonus.injured.deliver()
        bonus.lost.deliver()
        bonus.update(1 / 60)
        left = bonus.banked
        self.assertGreater(left, 0)

        for _ in range(int(self.bonus_scene.OUTCOME_HOLD_SECONDS * 60) + 4):
            if manager.active_scene is level:
                break
            manager.update(1 / 60)

        self.assertIs(manager.active_scene, level, "back in the Hall")
        self.assertAlmostEqual(level.time_remaining, clock_in_the_hall + left, delta=0.2)
        self.assertAlmostEqual(level.jiv_daya_bonus, left, delta=0.2,
                               msg="banked, so it will not be counted as time taken")

    def test_draws_with_people_carried_led_and_delivered(self) -> None:
        surf = self.pygame.Surface((1920, 1080))
        s = self.scene
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()
        self.step()
        s.draw(surf)                                 # carried
        s.lost.take()
        self.step()
        s.draw(surf)                                 # following
        s.lost.deliver()
        s.injured.deliver()
        self.step()
        s.draw(surf)                                 # delivered


if __name__ == "__main__":
    unittest.main()
