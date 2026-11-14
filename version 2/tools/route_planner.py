"""
route_planner.py — Find the key presses that walk the devotee from A to B.

Used by tools/autoplay.py to play a level for a recording. It is the route half
of Epic H's H4 only: it searches by running the real `Player.update` forward,
so a jump it finds is the jump the game gives. It builds no reachability graph
and proves nothing about a level (that is H1-H3, still unbuilt).

A plan is a list of frames, each `(move, jump)`: move is -1, 0 or +1 for
left / none / right, jump is True on the frame the jump key goes down. Replayed
at the same fixed dt from the same starting state, it lands exactly where the
search said it would — the physics has no randomness in it.
"""
import copy
import heapq
import itertools

from level_scene import Player
from settings import PLAYER_SPEED

# Search effort. Positions are bucketed this coarsely to tell states apart; the
# states themselves stay exact, so coarseness costs optimality, not accuracy.
X_BUCKET = 10
WALK_FRAMES = (3, 8, 20)
JUMP_HOLD_FRAMES = (0, 3, 6, 9, 12, 16, 20, 25, 30, 36, 43, 50, 60)
MAX_AIR_FRAMES = 200
MAX_EXPANSIONS = 6000


def clone(player):
    """A Player that can be simulated without disturbing the one in the scene."""
    twin = copy.copy(player)
    twin.trail = []
    return twin


def step(player, move, jump, world):
    """One frame, exactly as LevelScene.update moves the devotee.

    Returns False when the frame ends in the lake.
    """
    player.vx += (move * PLAYER_SPEED - player.vx) * 15 * world.dt
    if jump and player.on_ground:
        player.vy = world.jump_force
    player.update(world.dt, world.platforms, world.slopes)
    return player.y + player.height < world.floor_top


class World:
    """What the search needs to know about a level: geometry and the frame time."""

    def __init__(self, platforms, slopes, floor_top, jump_force, dt):
        self.platforms = platforms
        self.slopes = slopes
        self.floor_top = floor_top
        self.jump_force = jump_force
        self.dt = dt


def _run(player, frames, world):
    """Apply `frames` to a clone. Returns (end_state, positions) or None if it drowns."""
    twin = clone(player)
    positions = []
    for move, jump in frames:
        if not step(twin, move, jump, world):
            return None
        positions.append((twin.x, twin.y))
    return twin, positions


def _until_landed(twin, move, world, frames, positions):
    """Keep `move` held until the feet are down. False if it drowns or never lands."""
    for _ in range(MAX_AIR_FRAMES):
        if twin.on_ground:
            return True
        if not step(twin, move, False, world):
            return False
        frames.append((move, False))
        positions.append((twin.x, twin.y))
    return False


def _moves_from(player, world):
    """Every action tried from a standing state: yields (frames, end_state, positions)."""
    for move in (-1, 0, 1):
        for count in WALK_FRAMES:
            if move == 0 and count != WALK_FRAMES[1]:
                continue                     # one way of standing still is enough
            frames = [(move, False)] * count
            result = _run(player, frames, world)
            if result is None:
                continue
            twin, positions = result
            frames = list(frames)
            if _until_landed(twin, move, world, frames, positions):
                yield frames, twin, positions

    for move in (-1, 0, 1):
        for hold in JUMP_HOLD_FRAMES:
            if move == 0 and hold:
                break
            twin = clone(player)
            frames, positions = [], []
            alive = True
            landed_early = False
            for i in range(hold + 1):
                jump = i == 0
                if not step(twin, move, jump, world):
                    alive = False
                    break
                frames.append((move, jump))
                positions.append((twin.x, twin.y))
                if i > 0 and twin.on_ground:
                    landed_early = True      # longer holds would only repeat this
                    break
            if not alive:
                continue
            if _until_landed(twin, 0, world, frames, positions):
                yield frames, twin, positions
            if landed_early:
                break


def _key(player):
    speed = 0 if abs(player.vx) < 2 else (1 if player.vx > 0 else -1)
    return (int(player.x // X_BUCKET), int(round(player.y)), speed)


def plan(player, world, is_goal, goal_x=None):
    """Frames that take `player` to a state where `is_goal(state)` is true.

    Returns (frames, positions) — positions is where the devotee should be after
    each frame, for the caller to check the replay against — or None when no
    route is found. `goal_x` only steers the search towards the target.
    """
    if not player.on_ground:
        raise ValueError("a route is planned from standing, not from mid-air")

    def estimate(state):
        if goal_x is None:
            return 0.0
        return abs(state.x + state.width / 2 - goal_x) / PLAYER_SPEED

    start = clone(player)
    tiebreak = itertools.count()
    queue = [(estimate(start), next(tiebreak), 0, start, None)]
    seen = {}
    parents = {}
    expansions = 0
    while queue and expansions < MAX_EXPANSIONS:
        _, node_id, cost, state, link = heapq.heappop(queue)
        key = _key(state)
        if key in seen:
            continue
        seen[key] = cost
        parents[node_id] = link
        if is_goal(state):
            frames, positions = [], []
            while link is not None:
                parent_id, part_frames, part_positions = link
                frames[:0] = part_frames
                positions[:0] = part_positions
                link = parents[parent_id]
            return frames, positions
        expansions += 1
        for part_frames, end, part_positions in _moves_from(state, world):
            if _key(end) in seen:
                continue
            new_cost = cost + len(part_frames)
            heapq.heappush(queue, (new_cost + estimate(end), next(tiebreak), new_cost,
                                   end, (node_id, part_frames, part_positions)))
    return None
