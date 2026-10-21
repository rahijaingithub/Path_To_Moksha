"""The debug monitor must never be able to kill the game.

Its log lines are drawn with box-drawing glyphs (``│``, ``──►``). When stdout is a
pipe or a file rather than a console, Windows encodes it as cp1252 and those glyphs
raise ``UnicodeEncodeError`` — which ``SceneManager.switch_to`` catches as
``ImportError`` only, so the first scene switch used to take the process down
(``PathToMoksha.exe > log.txt``, or any redirected/CI run).

Fixed two ways, so these tests check both: the monitor is off unless
``PATH_TO_MOKSHA_DEBUG_MONITOR`` is set, and when it *is* on the writes fall back to
ASCII instead of raising.

The module imports pygame for its event constants, so the behavioural tests are
skipped on the dependency-free CI worker (like ``test_transitions``).
"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import re
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class MonitorSourceTests(unittest.TestCase):
    """Source-level checks that need neither pygame nor a display."""

    def test_the_monitor_is_not_hardcoded_on(self) -> None:
        src = (SRC / "debug_monitor.py").read_text(encoding="utf-8")
        self.assertNotIn("enabled = True", src)
        self.assertIn("PATH_TO_MOKSHA_DEBUG_MONITOR", src)

    def test_no_log_method_prints_directly(self) -> None:
        """Every log line goes through the guarded writer, not a bare print."""
        src = (SRC / "debug_monitor.py").read_text(encoding="utf-8")
        self.assertIn("def _emit(", src)
        # Drop the writer itself — it is the one place allowed to call print().
        outside_emit = re.sub(r"\n    def _emit\(.*?(?=\n    def )", "",
                              src, flags=re.S)
        bare = [line.strip() for line in outside_emit.splitlines()
                if line.strip().startswith("print(")]
        self.assertEqual(bare, [], f"unguarded prints: {bare}")
        for method in ("log_raw_event", "log_just_pressed", "log_action", "log_switch"):
            with self.subTest(method=method):
                body = src.split(f"def {method}(", 1)[1].split("\n    def ", 1)[0]
                self.assertIn("self._emit(", body)


@unittest.skipUnless(importlib.util.find_spec("pygame") is not None,
                     "needs pygame (runs locally in the venv, skipped on CI)")
class MonitorBehaviourTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(SRC))
        import debug_monitor
        import scene_manager
        cls.debug_monitor = debug_monitor
        cls.scene_manager = scene_manager

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SRC))

    def setUp(self) -> None:
        self.monitor = self.debug_monitor.monitor
        self._was_enabled = self.monitor.enabled
        self._real_stdout = sys.stdout

    def tearDown(self) -> None:
        sys.stdout = self._real_stdout
        self.monitor.enabled = self._was_enabled

    def cp1252_stdout(self):
        """Stand in for a redirected console: a stream that cannot hold the glyphs."""
        self._raw = io.BytesIO()
        self._wrapper = io.TextIOWrapper(self._raw, encoding="cp1252", errors="strict")
        sys.stdout = self._wrapper

    def collect(self) -> bytes:
        """Restore the real stdout and hand back whatever reached the byte stream."""
        self._wrapper.flush()
        sys.stdout = self._real_stdout
        self._wrapper.detach()        # keep the BytesIO open once the wrapper goes
        return self._raw.getvalue()

    # ── the default ───────────────────────────────────────────────────────────

    def test_off_unless_the_env_flag_is_set(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(self.debug_monitor._env_enabled())
        for value in ("1", "true", "TRUE", "yes", "on"):
            with self.subTest(value=value), \
                    mock.patch.dict(
                        "os.environ", {"PATH_TO_MOKSHA_DEBUG_MONITOR": value}):
                self.assertTrue(self.debug_monitor._env_enabled())
        for value in ("", "0", "false", "no"):
            with self.subTest(value=value), \
                    mock.patch.dict(
                        "os.environ", {"PATH_TO_MOKSHA_DEBUG_MONITOR": value}):
                self.assertFalse(self.debug_monitor._env_enabled())

    def test_a_fresh_monitor_follows_the_env_flag(self) -> None:
        DebugMonitor = self.debug_monitor.DebugMonitor
        kept = DebugMonitor._instance
        try:
            with mock.patch.dict("os.environ", {}, clear=True):
                DebugMonitor._instance = None
                self.assertFalse(DebugMonitor().enabled)
            with mock.patch.dict(
                    "os.environ", {"PATH_TO_MOKSHA_DEBUG_MONITOR": "1"}):
                DebugMonitor._instance = None
                self.assertTrue(DebugMonitor().enabled)
        finally:
            DebugMonitor._instance = kept

    # ── the crash ─────────────────────────────────────────────────────────────

    def test_a_real_scene_switch_survives_a_cp1252_stdout(self) -> None:
        """The regression: a genuine switch_to with the monitor on and stdout piped."""
        manager = self.scene_manager.SceneManager()
        manager.register("title", self.scene_manager.Scene(manager))
        manager.register("level", self.scene_manager.Scene(manager))

        self.monitor.enabled = True
        self.cp1252_stdout()
        try:
            manager.switch_to("title")
            manager.switch_to("level")
        finally:
            written = self.collect()

        self.assertEqual(manager.active_key, "level")
        self.assertIn(b"SWITCH", written)
        self.assertIn(b"title", written)
        self.assertIn(b"-->", written)      # the ASCII spelling of ──►

    def test_the_other_log_methods_survive_it_too(self) -> None:
        self.monitor.enabled = True
        self.cp1252_stdout()
        try:
            self.monitor.log_action("LevelScene", "opened a box")
            self.monitor.log_just_pressed({"JUMP": True, "ACTION": False},
                                          scene_name="LevelScene")
            self.monitor.log_switch(None, "title")
        finally:
            written = self.collect()

        for expected in (b"ACTION", b"FLAGGED", b"SWITCH", b"JUMP=True"):
            self.assertIn(expected, written)

    def test_a_stdout_that_refuses_everything_is_swallowed(self) -> None:
        class Hostile(io.TextIOBase):
            def write(self, _text):
                raise OSError("broken pipe")

        self.monitor.enabled = True
        sys.stdout = Hostile()
        try:
            self.monitor.log_switch("title", "level")
            self.monitor.log_action("LevelScene", "opened a box")
        finally:
            sys.stdout = self._real_stdout


if __name__ == "__main__":
    unittest.main()
