# ENGINE SPEC: 2D Arcade Platformer

## Engine Core Modules
* **`main.py`:** Core Pygame initialization, display setup (1920x1080 logical scaling), and primary 60FPS loop.
* **`scene_manager.py`:** Standard FSM (Finite State Machine). Routes events, updates, and draws to active scene (`title`, `character_select`, `level`, `victory`).
* **`asset_manager.py`:** Caches loaded surfaces/sounds. **Crucial feature:** graceful fallbacks. If an asset is missing, returns a hot-pink placeholder instead of crashing.
* **`input_manager.py`:** Aggregates keyboard, touch/mouse UI rects, and joystick (D-input) using `controller_map.json`. Emits standard virtual buttons (e.g., `jump`, `action`).
* **`level_scene.py`:** Manages the game world, player physics (gravity, jump arcs, rectangle AABB collisions), timer, and delegates to `box_system` and `monk_system`.
* **`box_system.py`:** Engine for "Box Roulette". Resolves interactions with predefined categories (Goal = progress, Support = time+, Distraction = time-/stun, No_Effect).
* **`monk_system.py`:** Dialogue overlay renderer and state machine. Uses typewriter effect and handles MCQ selection logic.

---

## Configuration Schemas

### 1. `dialogue.json`
* **Schema:** `{"LevelID": [{"question": str, "choices": [str], "correct": int}]}`
* **Example:**
```json
{
  "1": [
    {
      "question": "What opens the first door?",
      "choices": ["The blue key", "The red key"],
      "correct": 0
    }
  ]
}
```

### 2. `boxes.json`
* **Schema:** `{"LevelID": [{"cat": str(enum), "name": str, "desc": str}]}`
* **Enum Categories:** `"goal", "support", "distraction", "no_effect"`
* **Example:**
```json
{
  "1": [
    {
      "cat": "support",
      "name": "Speed Boots",
      "desc": "Found Speed Boots! +15s"
    }
  ]
}
```

### 3. `levels.json`
* **Schema:** `{"LevelID": {"platforms": [{"x": float, "y": float, "width": float, "height": float}]}}`
* **Example:**
```json
{
  "1": {
    "platforms": [
      {"x": 0, "y": 1050, "width": 1920, "height": 30},
      {"x": 500, "y": 900, "width": 150, "height": 10}
    ]
  }
}
```

### 4. `controller_map.json`
* **Schema:** `{"mapping": {"ActionName": [{"type": enum("button", "axis", "hat"), "index": int, "value": [int]}]}}`
* **Example:**
```json
{
  "mapping": {
    "jump": [
      {"type": "button", "index": 2}
    ]
  }
}
```

### 5. `sprite_manifest.json` (Target / Inferred)
* **Schema:** `{"AssetType": {"Key": "Filename.png"}}`
* **Example:**
```json
{
  "backgrounds": {
    "level_1": "bg_city.png"
  }
}
```

---

## Decoupling Backlog (Tech Debt)
To make this engine perfectly reusable for any new theme, the following hardcoded elements in the Python code must be extracted to JSON configuration:

1. **`levels.json` implementation:** Currently, level layouts (Rects) are strictly hardcoded in Python within `src/level_layouts.py`. This must be refactored to parse `levels.json`.
2. **`boxes.json` implementation:** Box definitions are currently hardcoded in a `LEVEL_BOX_DEFS` dictionary in `src/box_system.py`. Must be refactored to read `boxes.json`.
3. **Asset & Sprite Paths:** Hardcoded references (e.g., `monk_sprite.png`, `boy_sprite.png`, `girl_sprite.png`) in multiple systems. Needs a central `sprite_manifest.json`.
4. **Ranking System Strings:** Hardcoded ranks ("Moksha Margi", "Shravak", "Bhakt") and their time thresholds (<4m, 4-8m, >8m) exist directly in the victory state logic. Should be abstracted to a config file.
5. **NPC Render Fallback:** The procedural Skia/Cairo Padmasana monk rendering in `monk_system.py` is deeply Jain-specific. The fallback should be a generic geometric shape or removed in favor of strict `AssetManager` placeholder logic.
