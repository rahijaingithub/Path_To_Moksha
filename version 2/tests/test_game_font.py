"""No text the game draws may come out as the empty "missing glyph" box (2026-11-15).

The game's strings carry about thirty-five symbols (▲ ► ★ ✔ ⚠ ⌫ 🎮 ...) that its
font, pygame's default, does not have. Every one was drawn as an empty box: on the
box popups' headings, beside the Monk's chosen answer, on the name keyboard's
backspace key, on the title screen's buttons. game_font.GameFont draws the ones it
knows and leaves out the rest.

Needs pygame; skipped on the dependency-free CI worker.
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
# Not drawn on screen: the console log, and a scratch file that is not the game.
NOT_ON_SCREEN = {"debug_monitor.py", "test.py", "recorder.py"}


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class GameFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, str(SRC))
        import pygame
        pygame.init()
        pygame.display.set_mode((16, 16))
        from asset_manager import AssetManager
        import game_font
        cls.pygame = pygame
        cls.game_font = game_font
        cls.font = AssetManager().load_font(None, 32)
        plain = pygame.font.Font(None, 32)
        cls.plain = plain
        cls.tofu = {cls.pixels(plain.render(ch, True, (255, 255, 255)))
                    for ch in ("", "\U000f0000")}

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    @staticmethod
    def pixels(surface):
        import pygame
        return surface.get_size(), pygame.image.tobytes(surface, "RGBA")

    def symbols_in_the_games_strings(self):
        found = set()
        for path in SRC.glob("*.py"):
            if path.name in NOT_ON_SCREEN:
                continue
            for literal in re.findall(r'"[^"\n]*"|\'[^\'\n]*\'', path.read_text(encoding="utf-8")):
                found.update(ch for ch in literal if ord(ch) > 127)
        return found

    def test_the_fonts_the_game_uses_are_game_fonts(self) -> None:
        self.assertIsInstance(self.font, self.game_font.GameFont)

    def test_the_bug_was_real(self) -> None:
        """The plain font really does box these, or this file tests nothing."""
        for ch in "★✔⚠►⌫":
            self.assertIn(self.pixels(self.plain.render(ch, True, (255, 255, 255))), self.tofu, ch)

    def test_no_symbol_in_the_games_strings_is_drawn_as_an_empty_box(self) -> None:
        symbols = self.symbols_in_the_games_strings()
        self.assertGreater(len(symbols), 20, "the scan found too few symbols to be working")
        for ch in sorted(symbols):
            drawn = self.font.render(f"A{ch}B", True, (255, 255, 255))
            boxed = self.plain.render(f"A{ch}B", True, (255, 255, 255))
            if self.font.lacks(ch):
                self.assertNotEqual(self.pixels(drawn), self.pixels(boxed),
                                    f"U+{ord(ch):04X} is still drawn as a box")

    def test_a_known_symbol_is_drawn_in_the_colour_of_the_text(self) -> None:
        for ch in self.game_font.SHAPES:
            image = self.font.render(ch, True, (10, 200, 30))
            self.assertGreater(image.get_width(), 4, f"U+{ord(ch):04X}")
            mask = self.pygame.mask.from_surface(image, 200)
            self.assertGreater(mask.count(), 8, f"U+{ord(ch):04X} drew nothing")
            x, y = mask.get_bounding_rects()[0].center
            colours = {tuple(image.get_at((px, py))[:3]) for px in range(image.get_width())
                       for py in range(image.get_height()) if image.get_at((px, py))[3] > 200}
            self.assertEqual(colours, {(10, 200, 30)}, f"U+{ord(ch):04X}")

    def test_a_picture_the_font_cannot_draw_is_left_out_with_its_space(self) -> None:
        self.assertEqual(self.font.size("\U0001f3ae Controller Buttons"), self.font.size("Controller Buttons"))
        self.assertEqual(self.font.size("Arham \U0001f464"), self.font.size("Arham"))

    def test_plain_text_is_untouched(self) -> None:
        for words in ("Goal: Find the Temple Key!", "Jai Jinendra — Parasparopagraho Jīvānām", ""):
            self.assertEqual(self.pixels(self.font.render(words, True, (255, 255, 255))),
                             self.pixels(self.plain.render(words, True, (255, 255, 255))))

    def test_size_agrees_with_what_is_drawn(self) -> None:
        for words in ("★ SACRED GOAL ITEM FOUND ★", "▲▼ or Hover to choose", "⌫"):
            drawn = self.font.render(words, True, (255, 255, 255))
            self.assertEqual(self.font.size(words)[0], drawn.get_width())
            self.assertEqual(self.font.size(words)[1], self.plain.size("A")[1])
            self.assertEqual(drawn.get_height(), self.plain.render("A", True, (255, 255, 255)).get_height())


if __name__ == "__main__":
    unittest.main()
