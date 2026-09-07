# The Path to Moksha — Project Constitution

This file is loaded into every Claude Code session. It is the durable memory of the
project: north star, scope, working rules, and quality gates. Keep it under ~150 lines.
Detailed material lives in `docs/` (see map at the bottom).

## What this is
A 2D arcade platformer (Python 3.11+, `pygame-ce`, packaged with PyInstaller) built for
JSOT Digamber Paathshala. The player is a devotee (Shravak / Shravika) making a pilgrimage
through four levels — The Commute (Samsara) → The Cave (Resilience) → The Hall (Valor) →
The Summit (Moksha) — opening mystery boxes to find the Goal item, avoiding Water and Fire
hazards (Paap), and optionally seeking a Monk who rewards Jain knowledge with guidance.

## North star (never trade this away)
- **"Guidance over Gating."** The Monk is a guide, never a gatekeeper. Knowledge is
  rewarded; ignorance is never punished. No player is ever shamed.
- **Every mechanic carries a Jain meaning.** Water = attachment/Samsara. Fire = Kashaya
  (passions). Distraction boxes = Pramad. Wrong Lakshan teaches discernment. If a new
  mechanic has no doctrinal reading, question whether it belongs.
- **Playable by kids and adults**, keyboard, gamepad, and touch, on any Windows/Mac
  laptop as a single self-contained executable.
- **The spec of record is `docs/GDD_v2_refined.txt`.** Where it conflicts with older docs
  or with code, the spec wins — unless a logged decision says otherwise.

## Where we are (as of 2026-09-07)
- `v1.0` tag = shipped baseline. Levels 1–2 are complete and polished; kid/standard modes
  end after Level 2 ("to be continued"). Levels 3–4 exist only as skeleton layouts
  reachable in developer mode.
- **Folders replace branches.** The repo root is `Path to Moksha/`. `version 1/` is a
  frozen snapshot — do not edit it. `version 2/` is where all active work happens. There
  is a single `main` branch; commit directly to it, scoped to `version 2/`.
- v2 objective: **make the full four-level pilgrimage playable and true to the spec**,
  then layer in new ideas. See `docs/V2_GAP_ANALYSIS.md` and `docs/V2_TASKS.md`.

## Working process — apply to any non-trivial task
Ground → Analyze → Evaluate → Refine → Verify → Final.
1. **Ground.** Read the actual file / run the actual command before reasoning. Never
   answer from memory about this codebase.
2. **Analyze.** Name the pitfalls and faulty assumptions in the request (including the
   user's and your own).
3. **Evaluate.** Critique your own plan. What would make it wrong?
4. **Refine.** Propose the better approach the critique implies.
5. **Verify.** State how the result is checked *outside your own reasoning*: a test that
   runs, a command with an exit code, a playtest item. Anything without a verification
   step is labelled an **assumption**, not a conclusion.
6. **Final.** Deliver.
Skip the ceremony for typo fixes and one-line tweaks. Use it fully for anything touching
`scene_manager`, `input_manager`, save data, scoring, physics, or level design.

## Standing rules for Claude
- **Ask before executing or writing anything the user has not explicitly approved.** A
  question is a question — answer it; do not start building.
- State assumptions explicitly. Flag low-confidence claims. Never present unverified
  reasoning as verified.
- **Git is the only backup.** Never create `*_backup.py`, `*_v2.py`, or `backups/` folders.
  Commit at every green checkpoint (in `version 2/`) with a message that says *why*.
- Never track build output (`dist/`, `build/`) or scratch folders. `.gitignore` is authoritative.
- One task per session where possible; name the files in scope to keep token use low.
- Every non-trivial decision gets one dated line in `docs/DECISION_LOG.md` with the *why*.
- Match the surrounding code's idiom and comment density. Don't refactor what you weren't asked to.
- Report outcomes faithfully: failing tests are reported with output, skipped steps are named.

## Architecture invariants (breaking these caused every recent bug)
- `main.py` owns the loop, window, and 1920×1080 logical-surface letterbox scaling.
- `SceneManager` is the only thing that switches scenes; scenes receive `input_mgr` via
  `switch_to(...)` kwargs and must reset input state on `on_enter`.
- `InputManager` is the single source of truth for input; scenes read abstract actions
  (`JUMP`, `ACTION`, `MENU_SELECT`, …), never raw keys/buttons.
- `AssetManager` never hard-crashes on a missing asset (pink placeholder / silent audio).
- Persistent data goes through `ProfileManager` into `settings.BASE_DIR` (AppData / exe dir
  when frozen). Nothing else writes to disk.
- Levels are data: `level_layouts.py` (platforms), `hazards.py`, `box_system.LEVEL_BOX_DEFS`,
  `assets/monk_questions*.json`, `assets/level_goals.json`.
- Physics are frame-rate independent (`dt * 60` scaling). Keep it that way.

## Definition of Done (for any v2 task)
1. Code change is in `version 2/`, committed to `main` with a *why* message.
2. `python -m unittest discover -s tests -v` is green (this is what CI runs).
3. New behaviour has either an automated test or a named item in `docs/PLAYTEST_CHECKLIST.md`.
4. `docs/DECISION_LOG.md` updated if a design choice was made.
5. Any new asset is referenced by exact-case filename and listed in
   `tests/test_portability.py::DYNAMIC_REQUIRED_ASSETS` if loaded dynamically.

## Build & run
Run these from `version 2/` — that's the game root; this file lives one level up.
- Dev run: `venv\Scripts\python.exe src\main.py` (Python 3.12 venv; runtime dep is `pygame-ce`).
- Tests: `venv\Scripts\python.exe -m unittest discover -s tests -v` (stdlib only, no pytest).
- Windows exe: `build_exe.bat` → `dist\PathToMoksha.exe` (single-file; `dist/` is untracked).
- CI: `.github/workflows/build.yml` (repo root) runs tests, builds Windows + macOS, publishes
  on `v*` tags. Defaults to `version 2/`; `version 1/` builds only via manual dispatch.

## Docs map
- `docs/GDD_v2_refined.txt` — spec of record (with review notes and update log).
- `docs/GDD.md`, `docs/ARCHITECTURE.md`, `docs/DEV_REFERENCE.md` — v1 reference.
- `docs/V2_GAP_ANALYSIS.md` — spec vs. code, with evidence.
- `docs/V2_TASKS.md` — prioritized, verifiable task list + open questions.
- `docs/PLAYTEST_CHECKLIST.md` — manual QA gate before any release.
- `docs/DECISION_LOG.md` — why things are the way they are.
