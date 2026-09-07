# Game Design Document (GDD)

## Core Gameplay Loop
The player spawns at the start of a level with a countdown timer. They must traverse the platforming layout while avoiding Fire and Water hazards (Paap). The primary objective is to open Mystery Boxes scattered throughout the level until they find the "Goal" item (Key or Akshat). Once the Goal item is acquired, the player must navigate to the Temple Gate to exit the level. Time is the score metric; finishing faster yields a higher final spiritual rank. Players can optionally seek out the Monk NPC to answer a trivia question, which, if answered correctly, highlights the exact location of the Goal box.

## Box Roulette Mechanic
Boxes are randomized at the start of each level. When a player collides with a box and presses the Action key, it opens, revealing its category, color, and effect:

| Category | Color | Game Effect | Example Item |
|----------|-------|-------------|--------------|
| **Goal** | Bright Gold | Required to exit level. Timer continues. | Temple Key, Akshat |
| **Support** | Green | Adds `+15.0` seconds to the timer (`SUPPORT_TIME_BONUS`). | TTC Bus, Ghanta |
| **Distraction** | Red | Subtracts `-30.0` seconds (`DISTRACTION_TIME_PENALTY`) AND freezes player input for `5.0` seconds (`DISTRACTION_FREEZE_DURATION`). | Mobile Phone, Foe |
| **No-Effect** | Grey | No mechanical effect. | Wrong Lakshan |

*Source: Confirmed against values in `box_system.py` and `settings.py`.*

## Level Breakdown

1. **Level 1: The Commute (Samsara)**
   * **Difficulty:** Easy
   * **Layout:** Toronto cityscape. Three tiers of platforms (street level awnings, 2-storey row-houses, tall building ridges).
   * **Goal:** Temple Key.
2. **Level 2: The Cave (Resilience)**
   * **Difficulty:** Medium
   * **Layout:** Stone cave with low shelves, mid platforms with wider gaps, upper cave, and a high passage. Dynamic Bhagwan platform appears when Akshat is found.
   * **Goal:** Akshat.
3. **Level 3: The Hall (Valor)**
   * **Difficulty:** Hard
   * **Layout:** Marble hall featuring smaller, tighter ledges and a narrow upper hall.
   * **Goal:** Akshat.
4. **Level 4: The Summit (Moksha)**
   * **Difficulty:** Expert
   * **Layout:** Ground level has few footholds. Ascends via narrow stepping stones into a demanding double-zigzag path to the peak.
   * **Goal:** Akshat.

## Monk NPC Dialogue System
* **Placement:** Spawned on a safe platform (specifically targeted spots in Lv1/Lv2, randomized elsewhere) avoiding hazards.
* **Trigger:** Player enters a `60x40` interaction zone and presses `UP`.
* **Data Storage:** Questions are loaded from `monk_questions.json` (or `monk_questions_kids.json` based on the selected game mode).
* **Mechanic:** The UI overlays an antique scroll with a typewriter text effect. The system filters out previously asked questions to prevent repetition. Answering correctly sets `highlighted = True` on the Goal box and one Support box.

## Design Rationale & Open Questions
* **Hazard Representation:** Fire and Water were chosen to represent *Paap* (demerit), causing the player to reset to the start of the level.
* **[TODO for Designer] Doctrinal Rationale:** Please clarify the specific Jain doctrinal rationale for mapping "Mobile Phone" and "Foe" to Distractions that freeze the player, and why "Wrong Lakshan (Bull/Lion)" is specifically categorized as No-Effect rather than a Distraction.
* **[TODO for Designer] Endings:** Explain the theological mapping of the final time-based ranks (Moksha Margi, Shravak, Bhakt).
