# Implementation Plan: The Path to Moksha (Version 1)

Based on the refined Game Design Document and your feedback, this is the updated technical implementation strategy for "The Path to Moksha" using Python.

## 1. Assessment and Analysis

The project is a 2D arcade platformer ("Dangerous Dave" style) with spiritual elements, a Box Roulette mechanic, and an NPC Monk wager system. Based on your recent input, we have solidified the technical requirements:

*   **Platform & Engine:** Windows 10/11 using **Python** (specifically the `pygame-ce` library, which is excellent for 2D platformers and handling modern inputs).
*   **Controls:** Keyboard (Arrow keys) and on-screen Touch/Click controls.
*   **Resolution:** Dynamic scaling. The game will render to a base logical resolution (e.g., 1920x1080) and smoothly scale up/down when switching between windowed and fullscreen modes without losing aspect ratio.
*   **Assets:** AI generation will be used to create pixel art environments, UI elements, and character sprites.
*   **Audio:** Sound effects (jump, collect, hit, error) and background music (bhajans/atmospheric) will be integrated.

## 2. Proposed Implementation Phases

### Phase 1: Engine Initialization & Asset Pipeline
*   **Project Setup:** Initialize the Python project and install `pygame-ce`.
*   **Asset Generation:** Use AI tools to generate the necessary assets:
    *   Player Sprites (Boy/Girl).
    *   Bhagwan Images (Parshvanath, Mahavir, Adinath) and Temple exteriors/interiors.
    *   Tilesets (Toronto cityscape, Stone Cave, Marble Hall, Golden Summit).
    *   Items (Key, Akshat, TTC Bus, Car, Ghanta, Chanvar, Lakshans).
*   **Core Window Management:** Implement dynamic screen scaling and fullscreen toggle logic.

### Phase 2: Core Mechanics Development
*   **Physics Engine:** Implement platforming physics (gravity, jumping, collision detection, movement).
*   **Input Manager:** Create a unified input system that accepts both Arrow Keys and on-screen Touch/Click inputs (rendering UI buttons for touch).
*   **Box Roulette System:** Implement the randomizer logic for the 6 boxes (Goal, Support, Distraction, No-Effect).
*   **The Monk System:** Implement the NPC interaction, dialogue UI, the Q&A logic, and the camera-pan reward.
*   **Global Timer/Scoring:** Implement the descending clock and penalty/bonus logic.

### Phase 3: Level Implementation
*   **Level 1 (The Commute):** Toronto pixel art, easy platforms, TTC/Car boxes, Bus Stop Monk.
*   **Level 2 (The Cave):** Stone textures, medium platforms, rain/fire hazards, Cave Monk.
*   **Level 3 (The Hall):** Marble tiles, hard platforms (disappearing), fire/water hazards, Lotus Monk.
*   **Level 4 (The Summit):** Gold/sky theme, expert platforms (crumbling), all hazards, Peak Monk.
*   **Transitions:** Implement full-screen Bhagwan images and bowing animations between levels.

### Phase 4: Polish & Audio
*   Implement Title Screen and Character Select (Boy/Girl).
*   Implement Victory Screen and Ranking logic (Moksha Margi, Shravak, Bhakt).
*   **Audio Integration:** Hook up SFX and BGM to the game events.
*   Final physics tuning and testing.

## 3. User Review Required

> [!IMPORTANT]
> **Asset Generation Approval:** I will begin Phase 1 by setting up the Python environment and generating the first batch of assets (Player sprites and Level 1 background/tiles). I will present these AI-generated assets to you for approval.
> 
> **Version Control Folder:** As requested, I will also save a copy of this implementation plan and all code in the `version 1` subfolder within your workspace.

## 4. Verification Plan

*   **Scaling Test:** Run the game windowed and maximize it to ensure the aspect ratio is maintained.
*   **Input Test:** Verify that both keyboard arrows and clicking the on-screen buttons move the character.
*   **Mechanic Testing:** Intentionally hit all hazards and verify the Box Roulette system.
