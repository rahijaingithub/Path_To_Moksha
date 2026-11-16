"""The goal line under the level must point where the thing actually is (2026-11-15).

Level 2's line sent the devotee to "the Bhagwan at the top-right" while the
Parshvanath murti stands in the top-left corner — the tutorial had it right, the
goal line did not. Stdlib only, so it runs on the dependency-free CI worker.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LevelGoalTests(unittest.TestCase):
    def test_level_2_sends_the_devotee_to_the_side_the_murti_is_on(self) -> None:
        goals = json.loads((ROOT / "assets" / "level_goals.json").read_text(encoding="utf-8"))
        line = goals["2"]["akshat_found"]

        # Where level_scene puts the murti once the Akshat is found.
        source = (ROOT / "src" / "level_scene.py").read_text(encoding="utf-8")
        match = re.search(r"_add_blocker\(pygame\.Rect\((\d+), (\d+), (\d+), (\d+)\)\)", source)
        self.assertIsNotNone(match, "the murti's rect is no longer where this test looks")
        x, _y, width, _h = (int(n) for n in match.groups())
        side = "left" if x + width / 2 < 1920 / 2 else "right"

        self.assertIn(f"top-{side}", line)
        self.assertNotIn("top-right" if side == "left" else "top-left", line)


if __name__ == "__main__":
    unittest.main()
