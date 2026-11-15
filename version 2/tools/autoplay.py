"""
autoplay.py — Let the game play Level 3 and its Karuna bonus level, or Level 4, and record it.

    venv\\Scripts\\python.exe tools\\autoplay.py --out recordings\\level3_boy.mp4
    venv\\Scripts\\python.exe tools\\autoplay.py --character girl --out recordings\\level3_girl.mp4
    venv\\Scripts\\python.exe tools\\autoplay.py --level 4 --out recordings\\level4_boy.mp4

It runs the real game — `main.Game.run`, every scene, the real physics — and
presses the same abstract actions a player would (left, right, jump, action).
Nothing is teleported and no game state is written. It differs from a person at
the keyboard in three ways only, all so that a run can be repeated exactly:

* the frame time is fixed at 1/60s instead of read from the wall clock;
* `random` is seeded, so the boxes, the Monk's question and the mantra shuffle
  fall the same way every time;
* nothing is shown or played aloud (SDL's dummy drivers), and the profile it
  saves on finishing goes to a temporary folder, not the player's leaderboard.

This is a shortcut to Epic H's H4 (see docs/V2_TASKS.md): the route through the
level is found by tools/route_planner.py for the errands scripted below. It does
not check that a level is always finishable — H1-H3 are still unbuilt.

Exit code 0 only when the bird was saved, both men were helped, and Level 3 was
completed — or, for Level 4, when a ledge crumbled underfoot, cold shock was
caught and escaped, the Monk was answered and the summit gate was entered.
"""
import argparse
import os
import random
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
FRAME_MS = 1000.0 / 60.0
DT = FRAME_MS / 1000.0          # computed the way main.py computes it


class SimClock:
    """Stands in for pygame.time.Clock: every frame is exactly one sixtieth."""

    def __init__(self):
        self.ms = 0.0

    def tick(self, _fps=0):
        self.ms += FRAME_MS
        return FRAME_MS

    def get_fps(self):
        return 60.0


class RunFailed(Exception):
    pass


class Bot:
    """Plays the level. `script()` is a generator: one yield is one frame's input."""

    def __init__(self, game, pygame, modules):
        self.game = game
        self.pygame = pygame
        self.m = modules
        self.inp = game.input_mgr
        self.mgr = game.scene_mgr
        self.frames = 0
        self.result = {"bird_saved": False, "both_rescued": False, "level_complete": False}

    # ── the pieces a script is built from ────────────────────────────────────

    @property
    def level(self):
        return self.mgr.scenes[self.m.settings.SCENE_LEVEL]

    @property
    def bonus(self):
        return self.mgr.scenes[self.m.settings.SCENE_BONUS]

    def mark(self, beat):
        """Note when a story beat happens, for whoever cuts the video."""
        print(f"[autoplay] {self.frames / 60.0:6.1f}s  {beat}")

    def wait(self, seconds):
        for _ in range(int(round(seconds * 60))):
            yield (), ()

    def press(self, action, then=0.0):
        yield (), (action,)
        yield from self.wait(then)

    def wait_until(self, condition, timeout=30.0, what="something"):
        for _ in range(int(timeout * 60)):
            if condition():
                return
            yield (), ()
        raise RunFailed(f"timed out waiting for {what}")

    def go_to(self, is_goal, goal_x, what, floor_is_ground=False):
        """Walk and jump to wherever `is_goal(player)` holds, replanning if thrown off.

        The planner treats the level's floor as the lake and never touches it.
        `floor_is_ground` lifts that, for Level 4's valley floor: cold, not fatal.
        """
        planner = self.m.route_planner
        scene = self.level
        for _attempt in range(8):
            yield from self.wait_until(
                lambda: scene.player.on_ground and scene.drown_timer <= 0
                and not scene.player.frozen, what="the devotee to be standing")
            if is_goal(scene.player):
                return
            floor_top = scene.floor.top + (10000 if floor_is_ground else 0)
            world = planner.World(scene.platforms, scene.slopes, floor_top,
                                  self.m.settings.LEVEL_JUMP_FORCES[scene.level], DT)
            route = planner.plan(scene.player, world, is_goal, goal_x)
            if route is None:
                raise RunFailed(f"no route found to {what}")
            frames, positions = route
            on_course = True
            for (move, jump), expected in zip(frames, positions):
                held = (self.inp.LEFT,) if move < 0 else (self.inp.RIGHT,) if move > 0 else ()
                yield held, ((self.inp.JUMP,) if jump else ())
                actual = (scene.player.x, scene.player.y)
                if abs(actual[0] - expected[0]) > 0.01 or abs(actual[1] - expected[1]) > 0.01:
                    on_course = False
                    print(f"[autoplay] off course on the way to {what}; replanning")
                    break
            if on_course and is_goal(scene.player):
                return
        raise RunFailed(f"could not reach {what}")

    # ── Level 4 ──────────────────────────────────────────────────────────────

    def to_ledge(self, ledge, what, floor_is_ground=False):
        """Stand still on the Level 4 ledge given as (x, top, width)."""
        x, top, width = ledge
        yield from self.go_to(
            lambda p: (p.on_ground and abs(p.y + p.height - top) < 2 and abs(p.vx) < 1
                       and x - p.width / 2 < p.x < x + width - p.width / 2),
            x + width / 2, what, floor_is_ground)

    def answer_monk(self):
        scene, inp, monk = self.level, self.inp, self.level.monk
        yield from self.go_to(
            lambda p: monk.interaction_zone.collidepoint(p.rect.center) and abs(p.vx) < 1,
            monk.x + monk.WIDTH / 2, "the Monk")
        self.mark("at the Monk")
        yield from self.wait(0.8)
        yield from self.press(inp.ACTION, then=4.0)    # time to read the question
        if not monk.dialogue_active:
            raise RunFailed("the Monk's question did not open")
        for _ in range(monk.question_data["correct"]):
            yield from self.press(inp.MENU_DOWN, then=0.6)
        yield from self.wait(1.0)
        yield from self.press(inp.ACTION, then=3.0)
        if not monk.answered_correctly:
            raise RunFailed("the Monk was answered wrongly")

    def script_level4(self):
        scene, inp = self.level, self.inp
        L = self.m.level_layouts
        ledges = L.LEVEL4_LEDGES
        block, ice, mesa, spire, plateau, outcrop, terrace, ridge = ledges[1:9]
        self.result = {"ledge_crumbled": False, "cold_shock_escaped": False,
                       "monk_answered": False, "gate_entered": False}
        yield from self.wait(2.5)                      # Kailash, before anyone moves

        # 1. The left way: stream block, ice shelf, great mesa.
        yield from self.to_ledge(block, "the stream block")
        yield from self.to_ledge(ice, "the ice shelf")
        yield from self.to_ledge(mesa, "the great mesa")
        self.mark("on the great mesa")
        yield from self.wait(1.0)

        # 2. The spire: snow that looks like ground. Stand on it and it gives way.
        yield from self.to_ledge(spire, "the spire")
        self.mark("on the spire")
        spire_ledge = next(c for c in scene.crumbling if c.rect.width == spire[2])
        yield from self.wait_until(lambda: spire_ledge.state == "gone", timeout=5, what="the spire to crumble")
        self.result["ledge_crumbled"] = True
        self.mark("the spire crumbled")
        yield from self.wait_until(lambda: scene.player.on_ground, timeout=5, what="the fall to end")
        yield from self.wait_until(lambda: spire_ledge.state == "solid", timeout=6, what="the snow to drift back")
        yield from self.wait(1.0)

        # 3. Cold shock: step down to the valley floor, feel the clock race, climb out.
        yield from self.to_ledge(ice, "the ice shelf again")
        yield from self.go_to(lambda p: p.on_ground and abs(p.y + p.height - scene.floor.top) <= 2 and abs(p.vx) < 1
                              and 860 < p.x < 1080, 960, "the valley floor", floor_is_ground=True)
        if not scene.cold_shock:
            raise RunFailed("the valley floor did not bring on cold shock")
        self.mark("cold shock")
        before = scene.time_remaining
        yield from self.wait(3.0)
        lost = before - scene.time_remaining
        yield from self.to_ledge(outcrop, "the rock outcrop", floor_is_ground=True)
        self.result["cold_shock_escaped"] = (not scene.cold_shock) and 5.9 < lost < 6.1
        self.mark(f"out of the cold ({lost:.1f}s lost in 3.0s)")
        yield from self.wait(1.0)

        # 4. The right way, past the Monk: terrace, the crumbling ridge, his shelf.
        # A waypoint: from under the ice shelf the search for the terrace can run out
        # of its budget, so walk to the far end of the outcrop first.
        yield from self.to_ledge((outcrop[0] + 280, outcrop[1], 160), "the far end of the outcrop")
        yield from self.to_ledge(terrace, "the right terrace")
        yield from self.answer_monk()
        self.result["monk_answered"] = True

        # 5. The Akshat, wherever this play hid it.
        goal = next(b for b in scene.box_system.boxes if b.item["cat"] == "goal")
        yield from self.open_box(goal)
        if not scene.box_system.goal_found:
            raise RunFailed("the Akshat was not found")
        self.mark("Akshat found; the gate appears on the summit")
        yield from self.wait(2.0)

        # 6. The summit of Kailash, and the gate.
        yield from self.go_to(lambda p: p.on_ground and p.rect.colliderect(scene._summit_gate_rect()) and abs(p.vx) < 1,
                              L.LEVEL4_SUMMIT[0] + L.LEVEL4_SUMMIT[2] / 2, "the summit gate")
        self.mark("at the summit gate")
        yield from self.wait(2.0)
        yield from self.press(inp.ACTION)
        yield from self.wait_until(lambda: scene.level_complete, timeout=3, what="the gate to open")
        self.result["gate_entered"] = True
        self.mark("level complete")
        yield from self.wait(6.0)                      # the completion banner

    # ── Level 3 ──────────────────────────────────────────────────────────────

    def script(self):
        if self.level.level == 4:
            yield from self.script_level4()
            return
        scene = self.level
        inp = self.inp
        yield from self.wait(2.5)                      # the Hall, before anyone moves

        # 1. The Monk: a guide, not a gate. Answer him and the Akshat's box is shown.
        monk = scene.monk
        yield from self.go_to(
            lambda p: monk.interaction_zone.collidepoint(p.rect.center) and abs(p.vx) < 1,
            monk.x + monk.WIDTH / 2, "the Monk")
        self.mark("at the Monk")
        yield from self.wait(0.8)
        yield from self.press(inp.ACTION, then=4.0)    # time to read the question
        if not monk.dialogue_active:
            raise RunFailed("the Monk's question did not open")
        for _ in range(monk.question_data["correct"]):
            yield from self.press(inp.MENU_DOWN, then=0.6)
        yield from self.wait(1.0)
        yield from self.press(inp.ACTION, then=3.0)
        if not monk.answered_correctly:
            raise RunFailed("the Monk was answered wrongly")

        # 2. A box he pointed to that helps, then the Akshat itself.
        boxes = scene.box_system.boxes
        support = next((b for b in boxes if b.highlighted and b.item["cat"] == "support"), None)
        goal = next(b for b in boxes if b.item["cat"] == "goal")
        for box in (support, goal):
            if box is None:
                continue
            yield from self.open_box(box)

        self.mark("Akshat found; the bird falls")
        # 3. The Monk fades, Mahavir Bhagwan appears, and the bird falls.
        yield from self.wait_until(
            lambda: scene.reveal_phase == "ready" and scene.bird.is_fallen,
            what="the reveal and the bird's fall")
        yield from self.wait(2.0)

        # 4. Jiv Daya: go to the bird, share the Akshat, put the mantra in order.
        bird = scene.bird
        yield from self.go_to(
            lambda p: (bird.help_zone.collidepoint(p.rect.center) and abs(p.vx) < 1
                       and p.rect.centerx < bird.rest_x - 45),
            bird.rest_x - 70, "the fallen bird")
        self.mark("at the bird")
        yield from self.wait(1.0)
        yield from self.press(inp.ACTION)
        yield from self.wait_until(lambda: scene.rescue_phase == "puzzle", what="the mantra puzzle")
        yield from self.wait(2.5)
        for line in range(len(scene.puzzle_order)):
            row = scene.puzzle_order.index(line)
            while scene.puzzle_cursor != row:
                step = inp.MENU_DOWN if row > scene.puzzle_cursor else inp.MENU_UP
                yield from self.press(step, then=0.35)
            yield from self.wait(0.4)
            yield from self.press(inp.ACTION, then=0.9)

        # 5. The glimpse: the devotee as the doctor.
        yield from self.wait_until(
            lambda: self.mgr.active_key == self.m.settings.SCENE_BONUS, what="the bonus level")
        self.mark("bonus level begins")
        self.result["bird_saved"] = scene.bird_saved
        yield from self.play_bonus()

        # 6. Back in the Hall, at the spot left. Offer the Akshat from the Monk's seat.
        yield from self.wait_until(
            lambda: self.mgr.active_key == self.m.settings.SCENE_LEVEL, what="the return to Level 3")
        self.mark("back in Level 3")
        yield from self.wait(3.5)
        yield from self.go_to(
            lambda p: monk.interaction_zone.collidepoint(p.rect.center) and abs(p.vx) < 1,
            monk.x + monk.WIDTH / 2, "the offering spot")
        self.mark("at the offering spot")
        yield from self.wait(1.0)
        yield from self.press(inp.ACTION)
        yield from self.wait_until(lambda: scene.level_complete, what="the offering bow")
        self.mark("level complete")
        self.result["level_complete"] = True
        yield from self.wait(6.0)                      # the completion banner

    def open_box(self, box):
        scene = self.level
        inp = self.inp
        others = [b for b in scene.box_system.boxes if b is not box]

        def beside_only_this_box(p):
            reach = p.rect
            return (abs(p.vx) < 1 and reach.colliderect(box.rect.inflate(30, 30))
                    and not any(not b.opened and reach.colliderect(b.rect.inflate(30, 30))
                                for b in others))

        yield from self.go_to(beside_only_this_box, box.x + box.SIZE / 2,
                              f"the {box.item['name']} box")
        yield from self.wait(0.6)
        yield from self.press(inp.ACTION)
        if not box.opened:
            raise RunFailed(f"the {box.item['name']} box did not open")
        yield from self.wait(3.5)                      # read what was inside
        if scene.item_popup is not None:
            yield from self.press(inp.ACTION)
        yield from self.wait(1.0)

    # ── the bonus level ──────────────────────────────────────────────────────

    def play_bonus(self):
        bonus = self.bonus
        inp = self.inp
        consts = self.m.bonus_scene
        yield from self.wait(7.0)                      # the two opening lines

        def walk(direction, keep_going):
            key = inp.LEFT if direction < 0 else inp.RIGHT
            while keep_going():
                yield (key,), ()

        def lead(npc, direction, arrived, max_lead, stop_x):
            """Walk ahead of a man who is following, then stand until he catches up.

            The devotee is faster than either man, so he walks in a few long
            strides with a pause after each, as a person would. Letting go of the
            key the moment the lead opens and pressing it again a frame later
            made him stutter. He goes no further than `stop_x`, the door.
            """
            key = inp.LEFT if direction < 0 else inp.RIGHT
            gap = sys.modules["rescue_npc"].FOLLOW_GAP
            striding = True
            for _ in range(120 * 60):
                if arrived():
                    return
                ahead = (bonus.player_x - npc.x) * direction
                at_door = (bonus.player_x - stop_x) * direction >= 0
                if striding and (ahead >= max_lead or at_door):
                    striding = False
                elif not striding and not at_door and ahead <= gap + 4:
                    striding = True
                yield ((key,) if striding else ()), ()
            raise RunFailed("a rescue took far too long")

        # The injured man first: he is slow, so he is walked, and waited for.
        injured = bonus.injured
        yield from walk(1 if injured.x > bonus.player_x else -1,
                        lambda: abs(injured.x - bonus.player_x) > 60)
        yield from self.wait(1.2)
        yield from self.press(inp.ACTION, then=1.5)
        self.mark("injured man picked up")
        if injured.state != "following":
            raise RunFailed("the injured man was not picked up")
        reach = consts.DESTINATION_REACH - 25
        yield from lead(injured, -1, lambda: abs(injured.x - consts.HOSPITAL_X) <= reach, 300,
                        consts.HOSPITAL_X)
        yield from self.wait(0.8)
        yield from self.press(inp.ACTION)
        self.mark("treating at the hospital")
        yield from self.wait_until(lambda: bonus.injured_saved, what="the injured man's treatment")
        yield from self.wait(1.5)

        # Then the lost man, who only needs to be shown the way.
        lost = bonus.lost
        yield from walk(1 if lost.x > bonus.player_x else -1,
                        lambda: abs(lost.x - bonus.player_x) > 60)
        yield from self.wait(1.2)
        yield from self.press(inp.ACTION, then=1.2)
        self.mark("lost man picked up")
        if lost.state != "following":
            raise RunFailed("the lost man was not picked up")
        yield from lead(lost, 1, lambda: bonus.lost_saved, 260, consts.TEMPLE_X)
        self.mark("both rescued")
        self.result["both_rescued"] = bonus.both_rescued
        # The closing card holds for its own five seconds and returns by itself.


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--character", choices=("boy", "girl"), default="boy")
    parser.add_argument("--mode", choices=("kid", "standard"), default="kid")
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--level", type=int, choices=(3, 4), default=3)
    parser.add_argument("--out", help="where to save the video (omit to play without recording)")
    parser.add_argument("--size", default="1920x1080", help="recorded size, e.g. 1280x720")
    args = parser.parse_args(argv)

    data_dir = tempfile.mkdtemp(prefix="moksha_autoplay_")
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["PATH_TO_MOKSHA_DATA_DIR"] = data_dir
    sys.path.insert(0, SRC)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    import pygame
    import bonus_scene
    import level_layouts
    import main as game_main
    import recorder
    import route_planner
    import settings

    class Modules:
        pass
    modules = Modules()
    modules.bonus_scene, modules.settings, modules.route_planner = bonus_scene, settings, route_planner
    modules.level_layouts = level_layouts

    random.seed(args.seed)
    game = game_main.Game()
    clock = SimClock()
    game.clock = clock
    pygame.time.get_ticks = lambda: int(clock.ms)      # glows pulse in game time, not wall time

    shared = game.scene_mgr.shared
    shared.update({"character": args.character, "game_mode": args.mode,
                   "player_name": "Pilgrim", "starting_level": args.level, "current_level": args.level,
                   "total_score": 0, "final_score": 0, "total_time": 0.0,
                   "level_times": {}, "monk_correct": {}, "boxes_opened": {}, "distractions": {}})
    game.scene_mgr.switch_to(settings.SCENE_LEVEL, level=args.level, input_mgr=game.input_mgr)

    bot = Bot(game, pygame, modules)
    script = bot.script()
    managed = (game.input_mgr.LEFT, game.input_mgr.RIGHT, game.input_mgr.JUMP,
               game.input_mgr.ACTION, game.input_mgr.MENU_UP, game.input_mgr.MENU_DOWN)
    failure = []
    real_update = game.input_mgr.update

    def update_with_bot(*a, **kw):
        real_update(*a, **kw)
        try:
            held, pressed = next(script)
        except StopIteration:
            held, pressed = (), ()
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        except RunFailed as exc:
            failure.append(str(exc))
            held, pressed = (), ()
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        inp = game.input_mgr
        for action in managed:
            inp.actions[action] = action in held or action in pressed
        for action in pressed:
            inp.just_pressed[action] = True
        bot.frames += 1

    game.input_mgr.update = update_with_bot

    if args.out:
        width, height = (int(n) for n in args.size.lower().split("x"))
        recorder.RECORD_SIZE = (width, height)
        game.recorder.start()
        if not game.recorder.recording:
            print("[autoplay] the recorder did not start (is ffmpeg on PATH?)")
            return 2
    recorded = game.recorder.path

    game.run(max_frames=60 * 60 * 15)                  # a quarter of an hour is a stuck run
    shutil.rmtree(data_dir, ignore_errors=True)

    if args.out and recorded and os.path.exists(recorded):
        out = os.path.abspath(args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        os.replace(recorded, out)
        print(f"[autoplay] video: {out}")

    seconds = bot.frames / 60.0
    print(f"[autoplay] {seconds:.1f}s of play; {bot.result}")
    if failure:
        print(f"[autoplay] FAILED: {failure[0]}")
        return 1
    if not all(bot.result.values()):
        print("[autoplay] FAILED: the run ended without finishing everything")
        return 1
    print("[autoplay] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
