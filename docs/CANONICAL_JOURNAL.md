# Canonical Journal: Path to Moksha

- **Project Identifier:** Path to Moksha (`version 1`)
- **Version:** v0.1
- **Status:** Approved / Active
- **Last-Entry Date:** 2026-09-07

## 1. Project Goal
Deliver a high-fidelity Jain pilgrimage game with polished arcade game feel, smooth sprite animation, clean asset transparency, and responsive audio/interactivity.

## 2. Definition of Done (Walk Animation & Asset Integrity)
1. All player character sprite sheets (`boy` and `girl`) are 32-bit PNGs with clean alpha channels (`SRCALPHA`) and zero background artifacts or color halos.
2. Walk cycle sprite strips are formatted as 1×N horizontal rows of uniform square frames (`height × height`).
3. Asset loading in `AssetManager` succeeds without triggering magenta (`RGB 255, 0, 220`) fallbacks.
4. Walk animation in transition scenes and level scenes renders smoothly without stuttering or mid-body frame slicing.

## 3. Locked Decisions
- **DEC-001:** All active game sprite sheets must be transparent `.png` files; `.jpg` formats are disallowed for character sprites.
- **DEC-002:** Walk strips must follow a 1×N horizontal layout.
- **DEC-003:** Missing images must be resolved at the asset level rather than relying on fallback placeholders.

## 4. Completed Work Items & History
- **2026-09-07 (v0.1 - Complete):**
  - **TASK-001:** Replaced white-backed sprite sheets with 32-bit transparent PNGs for `player_boy_walk_right.png` and `player_girl_walk_right.png` (`alpha at (0,0) == 0`).
  - **TASK-002:** Formatted walk strips into 8-frame 1×N horizontal strips (`1024×128` px).
  - **TASK-003:** Updated `transition_scene.py` step timing to `0.08s` (~12.5 FPS) for fluid walk animations.
  - **TASK-004:** Verified with `test.py` and headless Pygame transparency assertion scripts. All checks passed.
