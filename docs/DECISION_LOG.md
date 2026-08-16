# Decision Log

This document records the chronological design decisions and architectural pivots made during the development of *Path to Moksha*.

## Phase 1: Foundation & Engine
* **Decision:** Use `pygame-ce` (Community Edition) over standard Pygame.
  * *Rationale:* Improved performance, active maintenance, and better modern gamepad support.
* **Decision:** Implement a centralized `AssetManager` with fail-safes.
  * *Rationale:* The game should not hard-crash if a `.png` or `.wav` is missing. Returning a pink placeholder surface ensures development and playtesting can continue uninterrupted.
* **Decision:** Dynamically scaled 1920x1080 Logical Surface.
  * *Rationale:* Guarantees consistent gameplay physics and UI layout across windowed mode, fullscreen, and varied monitor aspect ratios.

## Phase 2: Gameplay Mechanics
* **Decision:** "Box Roulette" item system.
  * *Rationale:* Creates a risk/reward loop. Players must decide whether to spend time opening boxes to find the Goal, risking hitting a Distraction (which costs 30 seconds and a 5-second stun).
* **Decision:** Monk Q&A highlights Goal Box.
  * *Rationale:* Rewards player knowledge of Jain trivia by removing the RNG element of the Box Roulette.

## Phase 3: Platforming & Scaling
* **Decision:** Four distinct levels of increasing difficulty.
  * *Rationale:* Mirrors the ascending difficulty of spiritual progress (Samsara -> Resilience -> Valor -> Moksha).
* **Decision:** Dynamic Bhagwan platform in Level 2.
  * *Rationale:* The code reveals a specific trigger: `if not getattr(self, "bhagwan_platform_added", False):` which spawns a platform only after the Akshat is found, rewarding goal completion with an easier exit route.

## Phase 4: Polish & Data
* **Decision:** Three-tier Time-based Ranking System.
  * *Rationale:* Moksha Margi (<4m), Shravak (4-8m), Bhakt (>8m). Focuses the core loop entirely on speed-running and time-management.
* **Decision:** Shift from local directory saves to OS-specific AppData paths.
  * *Rationale:* Packaging the game as a macOS `.app` or Windows `.exe` made the local `data/` folder read-only. `settings.py` was updated to route saves to `~/Library/Application Support/` or `%APPDATA%` to prevent silent I/O crashes.

## Unexplained Anomalies / Open Questions
* **The Skia/Cairo Test Script:** `test.py` contains intricate code to draw a Monk using advanced Bezier curves in Skia and Cairo. 
  * *Question for Lead:* Why was this level of vector rendering researched? Was there originally a plan to build the game engine around vector graphics rather than raster sprites? 
