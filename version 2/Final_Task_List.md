# Task Tracker: The Path to Moksha (Final)

## Phase 1: Engine Initialization & Asset Pipeline ✅ COMPLETE

- `[x]` Create project folder structure under `version 1`
- `[x]` Set up Python virtual environment and install `pygame-ce`
- `[x]` Create `settings.py` — game constants and configuration
- `[x]` Create `asset_manager.py` — centralized asset loader with caching
- `[x]` Create `input_manager.py` — unified keyboard + touch/click input
- `[x]` Create `scene_manager.py` — scene/state management system
- `[x]` Create `title_screen.py` — animated Title Screen scene
- `[x]` Create `character_select.py` — Boy/Girl selection scene
- `[x]` Create `level_scene.py` — core platformer physics loop
- `[x]` Create `main.py` — entry point with dynamic window scaling
- `[x]` Refine Engine: 1920x1080 logical scaling & increased jump force

## Phase 2: Core Mechanics Development ✅ COMPLETE

- `[x]` Box Roulette System (`box_system.py`)
- `[x]` Item effects — Goal, Support (+time), Distraction (-time + freeze), No-Effect
- `[x]` Monk/Guide NPC (`monk_system.py`)
- `[x]` Dialogue UI, Q&A, highlight reward on correct answer
- `[x]` Global Timer and Player freeze mechanic
- `[x]` Level completion logic and Multi-level progression

## Phase 3: Level Implementation ✅ COMPLETE

- `[x]` Level 1–4 unique platform layouts (`level_layouts.py`)
- `[x]` Water & Fire hazards per level (`hazards.py`)
- `[x]` Level transitions with Bhagwan images (`transition_scene.py`)
- `[x]` Level-specific box contents per GDD

## Phase 4: Polish & Audio ✅ COMPLETE

- `[x]` Generate procedural sound effects and background music (`generate_audio.py`)
- `[x]` Create `victory_scene.py`
- `[x]` Implement Ranking System (Moksha Margi, Shravak, Bhakt)
- `[x]` Hook up SFX to game events
- `[x]` Test full game loop (Title -> L1 -> L2 -> L3 -> L4 -> Victory)

## Phase 5: Custom Edits & Fixes ✅ COMPLETE
- `[x]` Relocate box roulette results message to the bottom band (centered)
- `[x]` Fix keyboard input mapping: Map K_UP and K_w to UP action instead of JUMP, resolving monk interaction bug
- `[x]` Fix drawing bug (float value for box result message border width) causing game to crash when pressing Enter
- `[x]` Add Level Goal display in bottom band (changes per level and reflects key-found state for Level 1)
- `[x]` Add Unlocked Item Shelf in bottom band — displays colored icon tiles per box opened (green/red/gold/grey)
- `[x]` Temple Gate interaction: expanded hitbox to allow ground-level activation without jumping
- `[x]` Temple Gate glow: now dynamically sized to match gate image dimensions (no longer hardcoded 140x180)
- `[x]` Monk character: updated to load monk_sprite.png from assets/images/items/ if present (falls back to procedural drawing)
- `[x]` Item icon images (see image_generation_prompts.md) — generated and saved in assets/images/items/
- `[x]` Monk sprite image (monk_sprite.png) — generated and cropped with transparency removal to blend perfectly with level background
- `[x]` Devotee (Shravak) Character Select Image: replaced preview image with the new high-fidelity version, cropped and background made transparent


## Phase 6: Expansion & Interactivity (Tutorial, Level Boundaries & Pop-ups) ✅ COMPLETE
- `[x]` Create `tutorial_scene.py` — **Premium tabbed** How-to-Play: ASCII keycap badges (no blank font glyph boxes), per-tab mouse wheel & arrow key vertical scrolling with scrollbar, item previews, sage guide, level objective cards, and mandala header accents
- `[x]` Add "How to Play" button to Main Menu / Title screen
- `[x]` Configure Level 2 ending to trigger transition scene first, then display "To be continued" screen redirecting to Title for Kid & Standard modes, featuring an animated player character (Boy/Girl) bowing in front of Bhagwan with golden devotional light particles
- `[x]` Implement premium Item Pop-up modal pausing gameplay timer, with auto-close progress bar and manual dismiss (Click / SPACE / any key)

---
**Project Status:** 100% Complete. Game is ready and fully integrated!
