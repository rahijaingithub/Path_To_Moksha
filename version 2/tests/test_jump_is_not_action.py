"""Jump must not act on the world (2026-10-25).

On a gamepad, `jump` also raises `MENU_SELECT` — deliberately, so A confirms in
menus. Gameplay was reading `ACTION or MENU_SELECT`, so on a pad jumping beside a
box opened it instead of jumping, and a reflex jump while the Monk's scroll was
open submitted whatever answer happened to be highlighted.

The world now listens to ACTION alone. Menu-shaped overlays keep MENU_SELECT,
where confirming with A is wanted and nothing is lost by it.

These are source-level checks: they need neither pygame nor a display, so they run
on the dependency-free CI worker too, and they fail if someone reintroduces
MENU_SELECT into a world interaction.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

# `unittest discover` puts this directory on the path; a direct
# `python -m unittest tests.<module>` does not, so do it either way.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_tools import function_source, strip_comments


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class JumpIsNotActionTests(unittest.TestCase):

    def test_the_gamepad_still_lets_a_confirm_menus(self) -> None:
        """The overlap is intended in menus; the fix belongs in the scenes."""
        src = (SRC / "input_manager.py").read_text(encoding="utf-8")
        self.assertIn("MENU_SELECT", src, "jump still raises MENU_SELECT for menus")

    def test_opening_a_box_does_not_listen_to_menu_select(self) -> None:
        src = function_source(SRC / "level_scene.py", "handle_events")
        at = src.index("self.box_system.try_open_nearest")
        box = src[at - 300:at]
        self.assertIn("ACTION", box)
        self.assertNotIn("MENU_SELECT", box,
                         "jumping beside a box would open it on a pad")

    def test_the_monk_answer_is_not_submitted_by_a_jump(self) -> None:
        src = function_source(SRC / "level_scene.py", "handle_events")
        submit = src[src.index("self.monk.submit_answer()") - 400:
                     src.index("self.monk.submit_answer()")]
        self.assertNotIn("MENU_SELECT", submit,
                         "a reflex jump would answer the Monk")

    def test_the_bonus_level_does_not_act_on_a_jump(self) -> None:
        src = function_source(SRC / "bonus_scene.py", "handle_events")
        act = src[src.index("self._act()") - 300:src.index("self._act()")]
        self.assertNotIn("MENU_SELECT", act)

    def test_menu_overlays_keep_their_confirm(self) -> None:
        """Pause, game over and the item pop-up are menus: A should confirm them."""
        src = function_source(SRC / "level_scene.py", "handle_events")
        for marker in ("if self.item_popup is not None:",
                       "if self.game_over:",
                       "if self.paused:"):
            with self.subTest(overlay=marker):
                block = src[src.index(marker):]
                self.assertIn("MENU_SELECT", block[:1100],
                              f"{marker} should still confirm on MENU_SELECT")


class ModeProgressionTests(unittest.TestCase):
    """Kid and standard reach Level 3 and its bonus level (C7, part one)."""

    def test_kid_and_standard_end_after_level_3(self) -> None:
        src = function_source(SRC / "level_scene.py", "_advance_level")
        found = re.search(r"if self\.level == (\d+) and self\.game_mode in \(\"kid\", \"standard\"\)",
                          src)
        self.assertIsNotNone(found, "the to-be-continued gate was not found")
        self.assertEqual(int(found.group(1)), 3,
                         "the run should continue through Level 3, bonus level included")


if __name__ == "__main__":
    unittest.main()
