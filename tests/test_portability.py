"""Portable, dependency-free integrity tests for Path to Moksha.

Run from the repository root with::

    python3 -m unittest discover -s tests -v

These tests deliberately avoid importing the game modules so they can run before
Pygame is installed and on non-graphical CI workers.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import runpy
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def assert_exact_case_file(test_case: unittest.TestCase, relative_path: str) -> None:
    """Assert every component exists with the spelling committed to the repo."""
    current = ROOT
    for component in PurePosixPath(relative_path).parts:
        test_case.assertTrue(
            current.is_dir(),
            f"Parent directory does not exist while checking {relative_path}: {current}",
        )
        entries = {entry.name for entry in current.iterdir()}
        test_case.assertIn(
            component,
            entries,
            f"Missing or incorrectly cased path component {component!r} in {relative_path}",
        )
        current /= component
    test_case.assertTrue(current.is_file(), f"Expected a file: {relative_path}")


class SourceIntegrityTests(unittest.TestCase):
    def test_python_sources_compile(self) -> None:
        source_roots = (ROOT, SRC, ROOT / "tools", ROOT / "backups", ROOT / "tests")
        paths: set[Path] = set(ROOT.glob("*.py"))
        for source_root in source_roots[1:]:
            if source_root.is_dir():
                paths.update(source_root.rglob("*.py"))

        self.assertTrue(paths, "No Python source files were discovered")
        for path in sorted(paths):
            with self.subTest(path=path.relative_to(ROOT)):
                source = path.read_text(encoding="utf-8")
                compile(source, str(path), "exec")

    def test_pyinstaller_specs_compile(self) -> None:
        paths = [ROOT / name for name in ("PathToMoksha.spec", "build_mac.spec")]
        for path in paths:
            with self.subTest(path=path.name):
                self.assertTrue(
                    path.is_file(),
                    f"Missing required PyInstaller specification: {path.name}",
                )
                compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_runtime_source_has_no_absolute_windows_paths(self) -> None:
        drive_path = re.compile(r"^[A-Za-z]:[\\/]")
        unc_path = re.compile(r"^\\\\[^\\]")

        for path in sorted(SRC.glob("*.py")):
            if path.name in {"test.py", "fidelity_loop_demo.py"}:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    with self.subTest(path=path.name, line=getattr(node, "lineno", None)):
                        self.assertFalse(
                            drive_path.match(node.value) or unc_path.match(node.value),
                            f"Platform-specific absolute path in {path.name}: {node.value!r}",
                        )


class DataIntegrityTests(unittest.TestCase):
    def test_all_project_json_is_valid_utf8(self) -> None:
        json_roots = (ROOT / "assets", ROOT / "data", ROOT / "template" / "schemas")
        paths = sorted(
            path
            for json_root in json_roots
            if json_root.is_dir()
            for path in json_root.rglob("*.json")
        )
        self.assertTrue(paths, "No JSON data files were discovered")

        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                with path.open("r", encoding="utf-8") as handle:
                    json.load(handle)


class AssetPortabilityTests(unittest.TestCase):
    # These assets are selected dynamically at runtime and therefore cannot all
    # be found by inspecting literal AssetManager calls.
    DYNAMIC_REQUIRED_ASSETS = (
        "assets/images/backgrounds/level1_background.png",
        "assets/images/backgrounds/level2_background.png",
        "assets/images/transitions/jsot_temple.png",
        "assets/images/transitions/parshvanath.png",
        "assets/images/items/monk_sprite.png",
        "assets/images/items/temple_key.png",
        "assets/images/items/ttc_bus.png",
        "assets/images/items/personal_car.png",
        "assets/images/items/mobile_phone.png",
        "assets/images/items/food.png",
        "assets/images/items/movie_ticket.png",
        "assets/images/items/akshat.png",
        "assets/images/items/ghanta.png",
        "assets/images/items/lakshan_snake.png",
        "assets/images/items/wrong_lakshan_bull.png",
        "assets/images/items/friend.png",
        "assets/images/items/chanvar.png",
        "assets/images/items/lakshan_lion.png",
        "assets/images/items/foe.png",
        "assets/images/items/lakshan_bull.png",
        "assets/images/items/wrong_lakshan_lion.png",
        "assets/monk_questions.json",
        "assets/monk_questions_kids.json",
        "assets/level_goals.json",
        "data/controller_map.json",
    ) + tuple(
        f"assets/images/sprites/player_{character}_{state}_{facing}.png"
        for character in ("boy", "girl")
        for state in ("idle", "walk", "run", "jump", "fall", "stun")
        for facing in ("left", "right")
    ) + tuple(
        f"assets/images/sprites/player_{character}_bowing.png"
        for character in ("boy", "girl")
    )

    # Missing optional/fallback artwork is already tolerated by AssetManager.
    # It is omitted here so this portability suite remains a regression suite
    # rather than a content-completeness gate.
    ALLOWED_MISSING_LITERAL_ASSETS = {
        "assets/images/transitions/digambar_garbhalaya.png",
    }

    @staticmethod
    def _literal_asset_references() -> set[str]:
        references: set[str] = set()
        for path in sorted(SRC.glob("*.py")):
            if path.name in {"test.py", "fidelity_loop_demo.py"}:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if not node.args or not isinstance(node.args[0], ast.Constant):
                    continue
                name = node.args[0].value
                if not isinstance(name, str):
                    continue

                if node.func.attr == "load_image":
                    subfolder = ""
                    if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                        subfolder = node.args[1].value
                    if isinstance(subfolder, str):
                        parts = ["assets", "images"]
                        if subfolder:
                            parts.append(subfolder)
                        parts.append(name)
                        references.add(PurePosixPath(*parts).as_posix())
                elif node.func.attr == "play_sound":
                    references.add(PurePosixPath("assets", "audio", "sfx", name).as_posix())
                elif node.func.attr == "play_music":
                    references.add(PurePosixPath("assets", "audio", "bgm", name).as_posix())
        return references

    def test_source_referenced_assets_exist_with_exact_case(self) -> None:
        references = self._literal_asset_references() - self.ALLOWED_MISSING_LITERAL_ASSETS
        references.update(self.DYNAMIC_REQUIRED_ASSETS)
        self.assertTrue(references, "No runtime asset references were discovered")

        for relative_path in sorted(references):
            with self.subTest(path=relative_path):
                assert_exact_case_file(self, relative_path)

    def test_runtime_asset_paths_have_no_casefold_collisions(self) -> None:
        seen: dict[str, Path] = {}
        for root_name in ("assets", "data"):
            for path in sorted((ROOT / root_name).rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(ROOT)
                key = relative.as_posix().casefold()
                with self.subTest(path=relative):
                    self.assertNotIn(
                        key,
                        seen,
                        f"Case-insensitive path collision: {seen.get(key)} and {relative}",
                    )
                seen[key] = relative


class ControllerMappingPortabilityTests(unittest.TestCase):
    def test_darwin_rejects_windows_map_and_accepts_darwin_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            bundled_data = temporary_root / "bundle" / "data"
            bundled_data.mkdir(parents=True)
            config_path = bundled_data / "controller_map.json"

            fake_pygame = types.ModuleType("pygame")
            fake_settings = types.ModuleType("settings")
            fake_settings.TOUCH_BUTTON_SIZE = 64
            fake_settings.TOUCH_BUTTON_MARGIN = 8
            fake_settings.TOUCH_BUTTON_ALPHA = 100
            fake_settings.LOGICAL_WIDTH = 1920
            fake_settings.LOGICAL_HEIGHT = 1080
            fake_settings.COLOR_WHITE = (255, 255, 255)
            fake_settings.COLOR_GOLD = (235, 180, 50)
            fake_settings.COLOR_SHADOW = (0, 0, 0, 128)
            fake_settings.BASE_DIR = str(temporary_root / "user-data")
            fake_settings.BUNDLED_DATA_DIR = str(bundled_data)

            with (
                mock.patch.dict(
                    sys.modules,
                    {"pygame": fake_pygame, "settings": fake_settings},
                ),
                mock.patch.object(platform, "system", return_value="Darwin"),
            ):
                namespace = runpy.run_path(str(SRC / "input_manager.py"))
                manager_class = namespace["InputManager"]

                windows_mapping = {
                    "controller_name": "Controller (Dinput)",
                    "platform": "Windows",
                    "mapping": {"jump": {"type": "button", "index": 2}},
                }
                config_path.write_text(
                    json.dumps(windows_mapping),
                    encoding="utf-8",
                )
                windows_manager = manager_class.__new__(manager_class)
                windows_manager.custom_mappings = {}
                with mock.patch("builtins.print"):
                    windows_manager._load_custom_mappings()
                self.assertEqual(
                    windows_manager.custom_mappings,
                    {},
                    "Darwin must not apply a Windows DirectInput mapping",
                )

                darwin_binding = {"type": "button", "index": 0}
                darwin_mapping = {
                    "controller_name": "Mac Game Controller",
                    "platform": "Darwin",
                    "mapping": {"jump": darwin_binding},
                }
                config_path.write_text(
                    json.dumps(darwin_mapping),
                    encoding="utf-8",
                )
                darwin_manager = manager_class.__new__(manager_class)
                darwin_manager.custom_mappings = {}
                with mock.patch("builtins.print"):
                    darwin_manager._load_custom_mappings()
                self.assertEqual(
                    darwin_manager.custom_mappings,
                    {"jump": [darwin_binding]},
                    "Darwin should load a mapping captured on Darwin",
                )


class MacOSPathTests(unittest.TestCase):
    def _load_frozen_darwin_settings(
        self,
        temporary_home: Path,
        data_directory_override: Path | None = None,
    ) -> dict[str, object]:
        bundle_root = temporary_home / "bundle"
        (bundle_root / "assets").mkdir(parents=True)
        (bundle_root / "data").mkdir()

        environment = dict(os.environ)
        environment.pop("PATH_TO_MOKSHA_DATA_DIR", None)
        if data_directory_override is not None:
            environment["PATH_TO_MOKSHA_DATA_DIR"] = str(data_directory_override)

        def expand_temporary_home(path: str) -> str:
            if path == "~":
                return str(temporary_home)
            if path.startswith("~/"):
                return str(temporary_home / path[2:])
            return path

        patches = (
            mock.patch.object(sys, "frozen", True, create=True),
            mock.patch.object(sys, "_MEIPASS", str(bundle_root), create=True),
            mock.patch.object(
                sys,
                "executable",
                "/Applications/PathToMoksha.app/Contents/MacOS/PathToMoksha",
            ),
            mock.patch.object(platform, "system", return_value="Darwin"),
            mock.patch.object(os.path, "expanduser", side_effect=expand_temporary_home),
            mock.patch.dict(os.environ, environment, clear=True),
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            return runpy.run_path(str(SRC / "settings.py"))

    def test_frozen_macos_uses_bundle_assets_and_user_application_support(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_home = Path(temporary_directory)
            settings = self._load_frozen_darwin_settings(temporary_home)

            expected_base = temporary_home / "Library" / "Application Support" / "PathToMoksha"
            expected_bundle = temporary_home / "bundle"
            self.assertEqual(Path(settings["BASE_DIR"]), expected_base)
            self.assertEqual(Path(settings["ASSETS_DIR"]), expected_bundle / "assets")
            self.assertEqual(Path(settings["BUNDLED_DATA_DIR"]), expected_bundle / "data")
            self.assertEqual(Path(settings["IMAGES_DIR"]), expected_bundle / "assets" / "images")
            self.assertEqual(Path(settings["AUDIO_DIR"]), expected_bundle / "assets" / "audio")
            self.assertTrue(expected_base.is_dir(), "Writable macOS data directory was not created")

    def test_frozen_macos_honors_data_directory_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_home = Path(temporary_directory)
            override = temporary_home / "smoke-test-data"
            settings = self._load_frozen_darwin_settings(
                temporary_home,
                data_directory_override=override,
            )

            expected_bundle = temporary_home / "bundle"
            self.assertEqual(Path(settings["BASE_DIR"]), override)
            self.assertTrue(override.is_dir(), "Configured data directory was not created")
            self.assertEqual(Path(settings["ASSETS_DIR"]), expected_bundle / "assets")
            self.assertEqual(Path(settings["BUNDLED_DATA_DIR"]), expected_bundle / "data")

    def test_profile_data_is_written_below_configured_base_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base_directory = Path(temporary_directory) / "Library" / "Application Support" / "PathToMoksha"
            fake_settings = types.ModuleType("settings")
            fake_settings.BASE_DIR = str(base_directory)

            with mock.patch.dict(sys.modules, {"settings": fake_settings}):
                namespace = runpy.run_path(str(SRC / "profile_manager.py"))

            profile_manager = namespace["ProfileManager"]()
            profile_manager.save_profile("Portability Test", score=10, level_reached=1)

            data_directory = base_directory / "data"
            self.assertEqual(Path(namespace["DATA_DIR"]), data_directory)
            self.assertTrue((data_directory / "profiles.json").is_file())
            self.assertTrue((data_directory / "high_scores.json").is_file())
            with (data_directory / "profiles.json").open("r", encoding="utf-8") as handle:
                self.assertIn("Portability Test", json.load(handle))


if __name__ == "__main__":
    unittest.main()
