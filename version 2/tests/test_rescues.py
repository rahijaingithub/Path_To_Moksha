"""The two rescues in the Karuna bonus level (Epic G3).

Two kinds of help, so two verbs plus a third at the end of the first:

* the **injured** man *limps along* to the hospital and is *treated* there — his body.
  He sets the pace, so the devotee has to wait for him;
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

    def wait_until(self, predicate, limit_seconds=20.0):
        """Stand still and let the world run until something becomes true."""
        self.input.release_all()
        for _ in range(int(limit_seconds * 60)):
            if predicate():
                return True
            self.step()
        return False

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

    def take_injured_to_hospital(self):
        """Offer him an arm, walk to the hospital, and wait for him to catch up."""
        s = self.scene
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()
        self.walk_to(self.bonus_scene.HOSPITAL_X)
        return self.wait_until(
            lambda: abs(s.injured.x - self.bonus_scene.HOSPITAL_X)
            <= self.bonus_scene.DESTINATION_REACH)

    def test_the_injured_man_limps_along_then_is_treated_at_the_hospital(self) -> None:
        s = self.scene
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()
        self.assertEqual(s.injured.state, "following", "he walks, he is not carried")
        self.assertTrue(s.helping_injured)

        self.walk_to(self.bonus_scene.HOSPITAL_X)
        self.assertGreater(abs(s.injured.x - s.player_x), 1.0,
                           "he trails behind rather than moving with the devotee")
        self.assertTrue(self.wait_until(
            lambda: abs(s.injured.x - self.bonus_scene.HOSPITAL_X)
            <= self.bonus_scene.DESTINATION_REACH), "he arrives in his own time")
        self.assertFalse(s.injured_saved, "arriving is not yet helping him")

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
        self.assertEqual(s.injured.state, "following")

        self.act()                                   # still out in the open
        self.assertEqual(s.injured.state, "following", "no hospital here")
        self.assertEqual(s.treat_timer, 0)

    def test_he_cannot_be_treated_while_he_is_still_on_his_way(self) -> None:
        """The devotee can outrun him; the help is not done until he arrives."""
        s = self.scene
        self.walk_to(self.bonus_scene.INJURED_START_X)
        self.act()
        self.walk_to(self.bonus_scene.HOSPITAL_X)

        if abs(s.injured.x - self.bonus_scene.HOSPITAL_X) > self.bonus_scene.DESTINATION_REACH:
            self.act()
            self.assertEqual(s.injured.state, "following", "he is not there yet")
            self.assertEqual(s.treat_timer, 0)

    def test_the_injured_man_cannot_keep_up_with_the_lost_man(self) -> None:
        """A limp is slower than a walk, so the devotee has to wait for him."""
        self.assertLess(self.rescue_npc.LIMP_FOLLOW_SPEED, self.rescue_npc.FOLLOW_SPEED)
        s = self.scene
        self.assertEqual(s.injured.follow_speed, self.rescue_npc.LIMP_FOLLOW_SPEED)
        self.assertEqual(s.lost.follow_speed, self.rescue_npc.FOLLOW_SPEED)

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

    def test_he_paces_then_stops_to_wonder_with_a_hand_to_his_head(self) -> None:
        """Being lost is not pacing without pause (the designer's confused pose)."""
        s = self.scene
        seen_pacing = seen_pondering = False
        moved_while_pondering = False

        for _ in range(int((self.rescue_npc.PACE_SECONDS +
                            self.rescue_npc.PONDER_SECONDS) * 2 * 60)):
            was_x = s.lost.x
            self.step()
            if s.lost.is_pondering:
                seen_pondering = True
                if abs(s.lost.x - was_x) > 0.01:
                    moved_while_pondering = True
            else:
                seen_pacing = True

        self.assertTrue(seen_pacing, "he casts about")
        self.assertTrue(seen_pondering, "and stops to wonder")
        self.assertFalse(moved_while_pondering, "he stands still while wondering")

    def test_only_the_lost_man_ponders(self) -> None:
        s = self.scene
        for _ in range(240):
            self.step()
            self.assertFalse(s.injured.is_pondering, "the injured man sits, he does not wonder")

    def test_the_confused_strip_plays_while_he_wonders(self) -> None:
        """Each strip stands in for the other, so either one alone still works."""
        npc = self.rescue_npc.RescueNPC(self.rescue_npc.KIND_LOST, 400, 900, {
            "walk": self.pygame.Surface((128 * 4, 128), self.pygame.SRCALPHA),
            "confused": self.pygame.Surface((64 * 4, 64), self.pygame.SRCALPHA),
        })
        npc.pondering = False
        self.assertEqual(npc._walk_image().get_width(), self.rescue_npc.DRAW_HEIGHT)

        npc.pondering = True
        self.assertTrue(npc.is_pondering)
        self.assertIsNotNone(npc._walk_image(), "the confused strip is used")

        only_walk = self.rescue_npc.RescueNPC(self.rescue_npc.KIND_LOST, 400, 900, {
            "walk": self.pygame.Surface((128 * 4, 128), self.pygame.SRCALPHA)})
        only_walk.pondering = True
        self.assertIsNotNone(only_walk._walk_image(), "walk stands in for a missing gesture")

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
        self.assertTrue(self.take_injured_to_hospital())
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
        self.assertIn("arm", s.hint.lower())
        self.act()
        self.step()
        self.assertIn("hospital", s.hint.lower())

    # ── the G5 art drops in without a code change ─────────────────────────────

    def test_art_is_used_for_each_pose_when_the_files_exist(self) -> None:
        """RescueNPC prefers a pose image over its procedural figure, and scales it."""
        npc = self.rescue_npc.RescueNPC(self.rescue_npc.KIND_INJURED, 400, 900,
                                        {"walk": self.pygame.Surface((128 * 6, 128),
                                                                     self.pygame.SRCALPHA)})
        self.assertEqual(npc._walk_image().get_height(), self.rescue_npc.DRAW_HEIGHT)
        self.assertIsNone(npc._pose_image("confused", 100), "absent poses fall back")

    def test_a_four_frame_walk_strip_cycles_and_is_scaled(self) -> None:
        strip = self.pygame.Surface((128 * 4, 128), self.pygame.SRCALPHA)
        npc = self.rescue_npc.RescueNPC(self.rescue_npc.KIND_LOST, 400, 900, {"walk": strip})
        frame = npc._walk_image()
        self.assertEqual(frame.get_height(), self.rescue_npc.DRAW_HEIGHT)
        self.assertEqual(frame.get_width(), self.rescue_npc.DRAW_HEIGHT, "square frames stay square")

    def test_only_art_that_exists_is_loaded(self) -> None:
        """AssetManager answers a missing image with an opaque pink placeholder, which
        would be drawn instead of falling back — so each file is checked for first.

        Asserted as an invariant rather than against today's files, so it still holds
        as the remaining G5 art lands.
        """
        s = self.scene
        self.assertEqual(s._load_poses(nope="definitely_not_here.png"), {},
                         "a missing file is not loaded at all")
        for npc, who in ((s.injured, "injured"), (s.lost, "lost")):
            for key, img in npc.poses.items():
                with self.subTest(who=who, pose=key):
                    corner = img.get_at((0, 0))
                    self.assertFalse(corner[:3] == (255, 0, 220) and corner[3] == 255,
                                     f"{who}/{key} loaded the pink placeholder")

    def test_the_temple_uses_level_1s_gate_art(self) -> None:
        """The door he is led to is the same door Level 1 ends at."""
        img = self.scene.temple_img
        self.assertIsNotNone(img, "temple_gate.png loaded")
        self.assertEqual(img.get_size(), (240, 196))
        corner = img.get_at((0, 0))
        self.assertFalse(corner[:3] == (255, 0, 220) and corner[3] == 255,
                         "not the pink placeholder")

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
        s.draw(surf)                                 # following, limping
        s.lost.take()
        self.step()
        s.draw(surf)                                 # following
        s.lost.deliver()
        s.injured.deliver()
        self.step()
        s.draw(surf)                                 # delivered


if __name__ == "__main__":
    unittest.main()
