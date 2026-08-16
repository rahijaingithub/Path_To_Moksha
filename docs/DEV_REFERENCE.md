# Developer Reference

## File & Folder Inventory

| File / Folder | Responsibility |
|---------------|----------------|
| `assets/` | Contains all read-only game media (`audio`, `fonts`, `images`, and JSON files for questions/goals). |
| `data/` | Stores writable user data (profiles, high scores, custom controller mappings). |
| `src/main.py` | Application entry point; handles window scaling, Pygame init, and the master game loop. |
| `src/settings.py` | Global constants, color definitions, gameplay variables, and cross-platform path resolution. |
| `src/scene_manager.py` | State machine orchestrator for transitioning between game screens. |
| `src/asset_manager.py` | Robust caching loader for images, audio, and fonts with missing-file fallbacks. |
| `src/input_manager.py` | Unified input handler for keyboard, controllers, and on-screen touch buttons. |
| `src/profile_manager.py` | Handles JSON serialization for player save data and global leaderboards. |
| `src/level_scene.py` | Core gameplay scene; orchestrates player movement, collision, boxes, and the Monk. |
| `src/level_layouts.py` | Defines the specific `pygame.Rect` platform layouts for all 4 levels. |
| `src/box_system.py` | Handles Box Roulette logic, placement, and time penalty/bonus application. |
| `src/monk_system.py` | Manages the Monk NPC, proximity interaction, and typewriter dialogue overlay. |
| `src/test.py` | Standalone rendering benchmark comparing Pygame, Cairo, and Skia drawing APIs. |
| `generate_audio.py` | Utility script to procedurally synthesize 16-bit retro `.wav` sound effects. |
| `PathToMoksha.spec` | PyInstaller build specification tailored for Windows (.exe). |
| `build_mac.spec` | PyInstaller build specification tailored for macOS (.app bundle). |

## Build, Run, and Test Instructions

**To run from source (Development):**
```bash
# Ensure you are in the "version 1" directory
python src/main.py
```

**To build for Windows:**
```bash
pyinstaller PathToMoksha.spec
# Executable will be in dist/PathToMoksha/
```

**To build for macOS (Must be run on a Mac):**
```bash
pyinstaller build_mac.spec
# Bundle will be in dist/PathToMoksha.app
```

## Asset Pipeline
* **Audio:** Placeholder sound effects are generated procedurally using the `generate_audio.py` script.
* **Graphics:** Several sprites and background images were authored via AI generation. The specific prompts used for these generations are documented in `image_generation_prompts.md` in the root directory.
* **Dependencies:** The game strictly relies on `pygame-ce`. The `skia` and `cairo` dependencies referenced in `test.py` are strictly for R&D/benchmarking and are excluded from final builds via the `.spec` files.
