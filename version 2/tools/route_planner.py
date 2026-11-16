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

Hazards (Level 1's water and fire, Level 2's snakes) are avoided by forecast:
`forecast()` runs copies of them forward, and a frame that would touch one is
treated like a frame that ends in the lake. `plan_flight()` is the Level 2
counterpart for after the Akshat, when the devotee flies and nothing above
applies: it finds a way through the open air on a grid.
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

    Returns False when the frame ends in the lake, or touching a hazard.
    """
    player.vx += (move * PLAYER_SPEED - player.vx) * 15 * world.dt
    if jump and player.on_ground:
        player.vy = world.jump_force
    player.update(world.dt, world.platforms, world.slopes)
    player.frame = getattr(player, "frame", 0) + 1
    if player.y + player.height >= world.floor_top:
        return False
    return not touches_hazard(player, world.hazards)


def forecast(hazards, dt, frames, margin=(0, 0)):
    """Where the hazards will be: entry k is their rects after k + 1 more frames.

    That is what frame k + 1 of a route meets, since LevelScene moves the devotee
    and then the hazards before it checks them against each other. `margin`
    widens each rect, so a route keeps its distance rather than brushing past.
    """
    twins = [copy.copy(h) for h in hazards]
    ahead = []
    for _ in range(frames):
        for twin in twins:
            twin.update(dt)
        ahead.append([twin.rect.inflate(2 * margin[0], 2 * margin[1]) for twin in twins])
    return ahead


def touches_hazard(player, hazards, frames_ahead=1):
    """True if `player`, standing as it is, meets a forecast hazard in the next frames."""
    if not hazards:
        return False
    rect = player.rect
    first = max(getattr(player, "frame", 0) - 1, 0)
    for k in range(first, min(first + frames_ahead, len(hazards))):
        if any(danger.colliderect(rect) for danger in hazards[k]):
            return True
    if first >= len(hazards):                       # past the forecast: assume the last of it
        return any(danger.colliderect(rect) for danger in hazards[-1])
    return False


class World:
    """What the search needs to know about a level: geometry and the frame time."""

    def __init__(self, platforms, slopes, floor_top, jump_force, dt, hazards=None):
        self.platforms = platforms
        self.slopes = slopes
        self.floor_top = floor_top
        self.jump_force = jump_force
        self.dt = dt
        self.hazards = hazards          # from forecast(), or None for a level without any


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
    start.frame = 0                     # the forecast is counted from now
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


# ── Flight (Level 2, once the Akshat is found) ───────────────────────────────

FLIGHT_CELL = 16
FLIGHT_MARGIN = 14


def plan_flight(player, obstacles, target, bounds):
    """Waypoints through the open air from `player` to the rect `target`.

    Each waypoint is where the devotee's top-left corner should be. Steps run
    along a row, a column or a diagonal — the eight ways flight can be steered.
    The way keeps FLIGHT_MARGIN clear of every rect in `obstacles` wherever it
    can; a gap too narrow for that is still flown, but counted as a long way
    round, so it is taken only when nothing wider exists. Returns None when the
    air offers no way.
    """
    import pygame

    # The grid is laid so that the devotee is on it exactly where they are now,
    # and a body is the rect Player.rect gives: a devotee standing on a ledge, or
    # just under one, is in a cell that fits, not one a few pixels inside the stone.
    width, height = int(player.width), int(player.height)
    here_x, here_y = int(player.x), int(player.y)
    left = bounds.x + (here_x - bounds.x) % FLIGHT_CELL
    top = bounds.y + (here_y - bounds.y) % FLIGHT_CELL
    cols = int((bounds.right - width - left) // FLIGHT_CELL)
    rows = int((bounds.bottom - height - top) // FLIGHT_CELL)

    def spot(cell):
        return left + cell[0] * FLIGHT_CELL, top + cell[1] * FLIGHT_CELL

    room_cache = {}

    def room(cell):
        """2 with the margin clear all round, 1 when only the body fits, 0 when it does not."""
        if cell not in room_cache:
            x, y = spot(cell)
            body = pygame.Rect(x, y, width, height)
            if not (0 <= cell[0] <= cols and 0 <= cell[1] <= rows) or body.collidelist(obstacles) >= 0:
                room_cache[cell] = 0
            else:
                wide = body.inflate(2 * FLIGHT_MARGIN, 2 * FLIGHT_MARGIN)
                room_cache[cell] = 2 if wide.collidelist(obstacles) < 0 else 1
        return room_cache[cell]

    def free(cell):
        return room(cell) > 0

    def reaches(cell):
        x, y = spot(cell)
        return pygame.Rect(x, y, width, height).colliderect(target)

    start = ((here_x - left) // FLIGHT_CELL, (here_y - top) // FLIGHT_CELL)
    room_cache[start] = 1               # wherever the devotee is, that is where it begins
    tiebreak = itertools.count()
    queue = [(0.0, next(tiebreak), 0.0, start)]
    came_from = {start: None}
    cost_to = {start: 0.0}
    tx, ty = target.centerx - width / 2, target.centery - height / 2
    while queue:
        _, _, cost, cell = heapq.heappop(queue)
        if cost > cost_to[cell]:
            continue
        if reaches(cell) and cell != start:
            cells = []
            while cell is not None:
                cells.append(cell)
                cell = came_from[cell]
            cells.reverse()
            # Keep the corners only: the points where the heading changes.
            corners = [cells[i] for i in range(1, len(cells) - 1)
                       if (cells[i][0] - cells[i - 1][0], cells[i][1] - cells[i - 1][1])
                       != (cells[i + 1][0] - cells[i][0], cells[i + 1][1] - cells[i][1])]
            return [spot(c) for c in [cells[0]] + corners + [cells[-1]]]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not (dx or dy):
                    continue
                nxt = (cell[0] + dx, cell[1] + dy)
                if not free(nxt):
                    continue
                if dx and dy and not (free((cell[0] + dx, cell[1])) and free((cell[0], cell[1] + dy))):
                    continue                # no squeezing past a corner
                new_cost = cost + (1.414 if dx and dy else 1.0) * (1 if room(nxt) == 2 else 8)
                if new_cost < cost_to.get(nxt, float("inf")):
                    cost_to[nxt] = new_cost
                    came_from[nxt] = cell
                    x, y = spot(nxt)
                    ahead = max(abs(x - tx), abs(y - ty)) / FLIGHT_CELL
                    heapq.heappush(queue, (new_cost + ahead, next(tiebreak), new_cost, nxt))
    return None
