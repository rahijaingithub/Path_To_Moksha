"""
game_font.py — A font that never draws the empty "missing glyph" box.

The game's text is full of small symbols: ▲ Press UP to speak, ★ SACRED GOAL ITEM
FOUND ★, ► beside the Monk's chosen answer, ⌫ on the name keyboard, 🎮 in Options.
The font the game ships with (pygame's default, FreeSans Bold) has none of them,
so every one of them was drawn as an empty box — on every machine, since the font
travels inside the executable.

GameFont draws the symbols it knows as simple shapes, in the text's own colour
and at the text's own size, so they need no second font file and look the same
on Windows and macOS. A symbol it does not know (the picture emoji) is left out
rather than boxed, together with the space that followed it.

AssetManager.load_font returns these, so no scene has to know.
"""
import math
import pygame

# Symbols drawn by hand: the character -> (shape name, width as a share of a square).
SHAPES = {
    "▲": ("up", 1.0), "▼": ("down", 1.0),                    # ▲ ▼
    "►": ("right", 0.9), "▶": ("right", 0.9),                # ► ▶
    "◄": ("left", 0.9),                                           # ◄
    "→": ("arrow_right", 1.2), "➔": ("arrow_right", 1.2),    # → ➔
    "↓": ("arrow_down", 1.0), "↩": ("arrow_left", 1.2),      # ↓ ↩
    "★": ("star", 1.1), "✔": ("tick", 1.1), "✘": ("cross", 1.0),   # ★ ✔ ✘
    "⚠": ("warning", 1.15), "◈": ("diamond", 1.0),           # ⚠ ◈
    "⌫": ("backspace", 1.5), "⚙": ("gear", 1.1),             # ⌫ ⚙
    "⏱": ("clock", 1.05), "⌂": ("house", 1.1), "\U0001f3e0": ("house", 1.1),   # ⏱ ⌂ 🏠
}
# Symbols with a plain-text twin the font does have.
TWINS = {"≈": "~", "─": "-"}                                 # ≈ ─

_SUPERSAMPLE = 4


def _star():
    points = []
    for i in range(10):
        radius = 1.0 if i % 2 == 0 else 0.42
        angle = -math.pi / 2 + i * math.pi / 5
        points.append((radius * math.cos(angle), radius * math.sin(angle) + 0.06))
    return points


def _gear_teeth():
    ops = []
    for i in range(8):
        a = i * math.pi / 4
        ops.append(("line", (0.62 * math.cos(a), 0.62 * math.sin(a)), (1.0 * math.cos(a), 1.0 * math.sin(a))))
    return ops


# Each shape is a list of strokes on a square from -1 to 1 (y grows downward).
_STROKES = {
    "up": [("fill", [(0, -0.9), (0.95, 0.75), (-0.95, 0.75)])],
    "down": [("fill", [(0, 0.9), (0.95, -0.75), (-0.95, -0.75)])],
    "right": [("fill", [(-0.75, -0.95), (0.85, 0), (-0.75, 0.95)])],
    "left": [("fill", [(0.75, -0.95), (-0.85, 0), (0.75, 0.95)])],
    "arrow_right": [("line", (-1, 0), (0.45, 0)), ("fill", [(0.2, -0.7), (1, 0), (0.2, 0.7)])],
    "arrow_left": [("line", (1, 0), (-0.45, 0)), ("fill", [(-0.2, -0.7), (-1, 0), (-0.2, 0.7)])],
    "arrow_down": [("line", (0, -1), (0, 0.45)), ("fill", [(-0.7, 0.2), (0, 1), (0.7, 0.2)])],
    "star": [("fill", _star())],
    "tick": [("line", (-0.9, 0.05), (-0.3, 0.7)), ("line", (-0.3, 0.7), (0.95, -0.8))],
    "cross": [("line", (-0.8, -0.8), (0.8, 0.8)), ("line", (-0.8, 0.8), (0.8, -0.8))],
    "warning": [("outline", [(0, -0.95), (1, 0.8), (-1, 0.8)]),
                ("line", (0, -0.3), (0, 0.2)), ("dot", (0, 0.5), 0.1)],
    "diamond": [("outline", [(0, -1), (1, 0), (0, 1), (-1, 0)]),
                ("fill", [(0, -0.4), (0.4, 0), (0, 0.4), (-0.4, 0)])],
    "backspace": [("outline", [(-1, 0), (-0.45, -0.8), (1, -0.8), (1, 0.8), (-0.45, 0.8)]),
                  ("line", (-0.05, -0.35), (0.6, 0.35)), ("line", (-0.05, 0.35), (0.6, -0.35))],
    "gear": [("ring", (0, 0), 0.55)] + _gear_teeth(),
    "clock": [("ring", (0, 0), 0.9), ("line", (0, 0), (0, -0.55)), ("line", (0, 0), (0.4, 0.2))],
    "house": [("outline", [(-1, 0), (0, -0.95), (1, 0)]),
              ("outline", [(-0.7, 0), (-0.7, 0.9), (0.7, 0.9), (0.7, 0)])],
}


class GameFont(pygame.font.Font):
    """pygame's Font, with the symbols it lacks drawn in or left out."""

    def __init__(self, path, size):
        super().__init__(path, size)
        self._lacking = {}
        self._tofu = None

    # ── which characters this font cannot draw ───────────────────────────────

    def _plain(self, text, color=(255, 255, 255)):
        return pygame.font.Font.render(self, text, True, color)

    def lacks(self, ch):
        """True if this font has no glyph for `ch` (it would draw the empty box)."""
        if ord(ch) < 128:
            return False
        if ch not in self._lacking:
            if self._tofu is None:
                self._tofu = {self._signature(c) for c in ("", "\U000f0000")}
            self._lacking[ch] = self._signature(ch) in self._tofu
        return self._lacking[ch]

    def _signature(self, ch):
        image = self._plain(ch)
        return image.get_size(), pygame.image.tobytes(image, "RGBA")

    def _pieces(self, text):
        """`text` as a list of plain runs (str) and drawn symbols (("shape", name, width))."""
        pieces, run = [], []
        skip_space = False
        ended_on_a_gap = False
        for ch in text:
            if skip_space and ch == " ":
                skip_space = False
                continue
            skip_space = False
            ended_on_a_gap = False
            if not self.lacks(ch):
                run.append(ch)
            elif ch in TWINS:
                run.append(TWINS[ch])
            elif ch in SHAPES:
                if run:
                    pieces.append("".join(run))
                    run = []
                pieces.append(("shape",) + SHAPES[ch])
            else:
                # Unknown and undrawable: leave it out, and the space after it,
                # so "🎮 Controller" does not begin with a gap.
                skip_space = True
                ended_on_a_gap = True
        if ended_on_a_gap and run and run[-1] == " ":
            run.pop()                              # it ended the line: drop the space before it
        if run:
            pieces.append("".join(run))
        return pieces

    def _needs_help(self, text):
        return (not text.isascii()) and any(self.lacks(ch) for ch in text)

    # ── drawing ──────────────────────────────────────────────────────────────

    def _shape(self, name, share, color, height):
        """One symbol on a surface as tall as a line of text."""
        side = max(6, int(height * 0.72))                 # about the height of a capital
        width = max(4, int(side * share))
        pad = max(1, side // 10)
        big = pygame.Surface(((width + 2 * pad) * _SUPERSAMPLE, height * _SUPERSAMPLE), pygame.SRCALPHA)
        cx = big.get_width() / 2
        cy = height * _SUPERSAMPLE * 0.45
        rx = width * _SUPERSAMPLE / 2
        ry = side * _SUPERSAMPLE / 2
        stroke = max(_SUPERSAMPLE, int(side * _SUPERSAMPLE * 0.19))
        rgb = tuple(color[:3])
        big.fill((*rgb, 0))             # so the scaled-down edge fades in the text's colour, not to black

        def at(point):
            return cx + point[0] * rx, cy + point[1] * ry

        for op in _STROKES[name]:
            if op[0] == "fill":
                pygame.draw.polygon(big, rgb, [at(p) for p in op[1]])
            elif op[0] == "outline":
                pygame.draw.lines(big, rgb, True, [at(p) for p in op[1]], stroke)
                for p in op[1]:
                    pygame.draw.circle(big, rgb, at(p), stroke // 2)
            elif op[0] == "line":
                pygame.draw.line(big, rgb, at(op[1]), at(op[2]), stroke)
                for p in op[1:3]:
                    pygame.draw.circle(big, rgb, at(p), stroke // 2)
            elif op[0] == "ring":
                pygame.draw.circle(big, rgb, at(op[1]), int(op[2] * min(rx, ry)), stroke)
            elif op[0] == "dot":
                pygame.draw.circle(big, rgb, at(op[1]), max(stroke // 2, int(op[2] * ry) + stroke // 3))
        return pygame.transform.smoothscale(big, (width + 2 * pad, height))

    def render(self, text, antialias=True, color=(255, 255, 255), bgcolor=None, wraplength=0):
        if not isinstance(text, str) or not self._needs_help(text):
            if bgcolor is None:
                return super().render(text, antialias, color, None, wraplength)
            return super().render(text, antialias, color, bgcolor, wraplength)

        height = self._plain("A").get_height()            # as tall as any line this font draws
        parts = []
        for piece in self._pieces(text):
            if isinstance(piece, str):
                if piece:
                    parts.append(pygame.font.Font.render(self, piece, antialias, color))
            else:
                parts.append(self._shape(piece[1], piece[2], color, height))
        width = sum(p.get_width() for p in parts)
        out = pygame.Surface((max(1, width), max([height] + [p.get_height() for p in parts])), pygame.SRCALPHA)
        if bgcolor is not None:
            out.fill(bgcolor)
        x = 0
        for part in parts:
            out.blit(part, (x, 0))
            x += part.get_width()
        if len(color) > 3 and color[3] < 255:
            out.set_alpha(color[3])
        return out

    def size(self, text):
        if not isinstance(text, str) or not self._needs_help(text):
            return super().size(text)
        # pygame's own size() and render() differ a little in height; keep its habit.
        return self.render(text, True, (255, 255, 255)).get_width(), super().size("A")[1]
