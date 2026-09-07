# New Game Checklist

To build a brand new 2D Arcade Platformer using this engine, follow this step-by-step checklist.

## Phase 1: Re-Theming Assets
You must replace the game content, but you **never** need to change the engine core scripts (`main.py`, `scene_manager.py`, `asset_manager.py`, `input_manager.py`).

1. **Backgrounds:** Replace files in `/assets/images/bg/`. Ensure they are `1920x1080`.
2. **Characters:** Replace the player sprites in `/assets/images/chars/`. (Keep bounding box sizes consistent if you don't want to adjust collision code).
3. **Items & NPC:** Replace `/assets/images/items/` (e.g., the Box sprite, the NPC sprite).
4. **Audio:** Replace sound effects in `/assets/audio/` (`jump.wav`, `box_open.wav`, `correct.wav`, `wrong.wav`, `bgm.wav`).
5. **Fonts:** Update `/assets/fonts/` if you want a different typography style, and rename the file in `settings.py` (or manifest).

## Phase 2: Configuration 
*(Note: Refer to `template/ENGINE_SPEC.md` for schemas)*

1. **`dialogue.json`**: Write your new NPC Q&A text. Place it in `/assets/data/`.
2. **`boxes.json`**: Define your themed pick-ups. Map your theme's items to the engine's strict `goal`, `support`, and `distraction` categories.
3. **`levels.json`**: Design your platforms. Provide the `x`, `y`, `width`, `height` rects for your new world.

## Phase 3: Engine Decoupling (If not yet complete)
If the "Decoupling Backlog" from `ENGINE_SPEC.md` has not been implemented yet, you will need to manually edit these Python files:
1. Edit `src/level_layouts.py` to change platform layouts.
2. Edit `src/box_system.py` to update the `LEVEL_BOX_DEFS` dictionary.
3. Edit `src/settings.py` (and relevant scenes) to rename the victory ranks and threshold times.

## Phase 4: Build
1. Update `PathToMoksha.spec` and `build_mac.spec` to rename the executable/app bundle (e.g., `MyNewGame.spec`).
2. Run PyInstaller: `pyinstaller MyNewGame.spec`.
