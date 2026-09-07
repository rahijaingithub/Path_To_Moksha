# The Path to Moksha

## Story Synopsis

*The Path to Moksha* is a spiritual 2D arcade platformer representing the arduous but rewarding pilgrimage of a Jain practitioner. Playing as either a Shravak (boy) or Shravika (girl), you embark on a journey that begins in the bustling Toronto cityscape (Samsara) and ascends through challenging terrains to finally reach the peak of spiritual liberation (Moksha).

Along the journey, your ultimate goal is to seek darshan (divine sight) of the Bhagwans residing at the Jain Society of Toronto (JSOT). However, the path is fraught with obstacles representing Paap (spiritual demerit) in the form of water and fire hazards, as well as worldly distractions that threaten to consume your most precious resource: time.

Guided by venerable Monks who impart timeless Jain wisdom, you must collect sacred items, avoid pitfalls, and conquer four distinct trials of resilience and valor. The choices you make and the focus you maintain will determine your spiritual rank upon reaching the summit.

## Gameplay Overview

### Controls

The game features a unified input system supporting Keyboard, Gamepad, and On-Screen Touch controls:
* **Move:** Left / Right Arrows, A / D, Gamepad Stick/D-Pad, or On-Screen Arrows.
* **Jump:** Spacebar, Up Arrow, Gamepad Button A (Cross), or On-Screen 'JUMP' button.
* **Interact/Action:** Enter, E, Gamepad Button X (Square), or On-Screen 'ACT' button.
* **Speak to Monk:** Up Arrow when near a Monk.

### Objectives & Mechanics

Your objective in each level is to locate the **Goal Box** (containing the Temple Key or Akshat) and then reach the temple gate at the end of the level before the timer runs out. 

To aid or hinder your journey, you will encounter Mystery Boxes (Box Roulette). When opened, they reveal one of four categories:
* **Goal (Gold):** Contains the required item to complete the level.
* **Support (Green):** Grants a +15 second time bonus (e.g., TTC Bus, Temple Bell).
* **Distraction (Red):** Penalizes you with a -30 second time deduction and freezes your character in place for 5 seconds (e.g., Mobile Phone, Foe).
* **No-Effect (Grey):** Contains incorrect items (e.g., Wrong Lakshan) that have no impact.

### The Monk & Spiritual Q&A

In each level, you will encounter a meditative Monk. Approaching the Monk and pressing UP opens a full-screen antique parchment dialogue. The Monk will ask you a spiritual question. If you answer correctly, the Monk blesses your path by visually highlighting the Goal box and a Support box in the level, saving you precious time!

## Installation & Running the Game

### macOS players

1. Download `PathToMoksha-mac.zip` from the project's
   [Releases page](https://github.com/rahijaingithub/Path_To_Moksha/releases)
   and double-click it to extract `PathToMoksha.app`.
2. Optionally move the app to `Applications`.
3. Double-click the app to play.

Local and automated builds may be ad-hoc signed but not Apple-notarized. On the
first launch of such a build, right-click `PathToMoksha.app` in Finder, select
**Open**, and confirm **Open**. This approval is normally required only once for
that build.

The automated release contains the native architecture of its macOS build
runner. If macOS reports that it is incompatible, use the source-code
instructions below or create a native local build. A universal2 package
supports both Apple Silicon and Intel only when every bundled dependency is
universal.

Player profiles, high scores, and writable configuration from both source and
packaged macOS runs are stored outside the project/application bundle at:

```text
~/Library/Application Support/PathToMoksha
```

### Windows players

Download `dist/PathToMoksha.exe` and double-click it.

### Run from source

Python 3.11 or newer is recommended. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python src/main.py
```

On macOS, you can instead double-click `play_macos.command`. If macOS does not
treat it as executable, run `chmod +x play_macos.command` once from Terminal.
Dependency versions are defined by `requirements.txt`; do not install both
`pygame` and `pygame-ce` into the same environment.

For packaging and code-signing instructions, see
[the developer reference](DEV_REFERENCE.md).

## Screenshots

*[TODO: Insert Gameplay Screenshot 1 - Cityscape]*
*[TODO: Insert Gameplay Screenshot 2 - Box Opening]*
*[TODO: Insert Gameplay Screenshot 3 - Monk Dialogue]*
