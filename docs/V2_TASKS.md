# V2 Task List

Priorities: **P0** = the game cannot be called "four levels" without it. **P1** = spec
fidelity. **P2** = polish / hygiene. Effort: S (<1 session), M (1–2), L (3+).
Every task names its files and its verification. Tasks marked ❓ depend on an answer in
"Open questions" below.

## Epic A — Foundations (do first; makes everything after cheaper)
| ID | Task | Files | Effort | Verify |
|---|---|---|---|---|
| A0 | **Fix the 2 failing tests at baseline** (CI is red on `main` right now): (a) `victory_scene.py:83` references `bgm_loop.wav` but only `.ogg` exists; (b) `test_darwin_rejects_windows_map_and_accepts_darwin_map` — `InputManager._load_custom_mappings` no longer loads a Darwin-captured map on Darwin | `victory_scene.py`, `input_manager.py` | S | unittest green |
| A1 | Remove `commit-builds` job from CI (breaks now that `dist/` is ignored) | `.github/workflows/build.yml` | S | CI green on next `main` push |
| A2 | Add `tests/test_levels.py`: every level builds; floor/walls present; every platform inside 1920×1080; boxes+monk+hazards place without overlap for 50 random seeds | `tests/` | M | unittest green |
| A3 | Add `tests/test_profiles.py`: save/load round-trip, corrupt JSON recovery, ranking order | `tests/` | S | unittest green |
| A4 | Add `tests/test_scene_transitions.py`: each scene's `on_enter` resets input state (headless pygame with `SDL_VIDEODRIVER=dummy`) | `tests/` | M | unittest green |
| A5 | Add `tests/test_box_defs.py`: `LEVEL_BOX_DEFS` has exactly 1 Goal per level, matches spec table, every item has an image in `assets/images/items/` | `tests/` | S | unittest green |
| A6 | Untrack `assets/**/Old*` folders (move to `_archive`) | `.gitignore`, assets | S | `git ls-files | grep -i old` empty |
| A7 | Unify scoring: points derived only from total time (lower time → higher points) so leaderboard order == spec order (Q1 decided) | `level_scene.py`, `victory_scene.py`, `leaderboard_scene.py`, `profile_manager.py` | M | test + playtest #14 |

## Epic B — Level 3: The Hall (Valor) — P0
| ID | Task | Files | Effort | Verify |
|---|---|---|---|---|
| B1 | Background art `level3_background.png` (white marble + gold hall) | `assets/images/backgrounds/`, `image_generation_prompts.md` | M (art) | asset test |
| B2 | Rebuild `_build_level3` platforms against the art (use the in-game coordinate logger) | `level_layouts.py` | M | A2 + playtest #8 |
| B3 | Disappearing marble tiles: new `TimedPlatform` type with fade cycle; Lakshan (Lion) reveals all for 10s | `level_layouts.py`, `level_scene.py`, `box_system.py` | L | unit test on cycle timing + playtest |
| B4 | Hazards: fire pits on floor + overflowing pools; verify against art | `hazards.py` | S | A2 |
| B5 | Transition 3→4: `mahavir.png` + bow animation entry in `TRANSITION_DATA[4]` | `transition_scene.py`, assets | S (+art) | playtest #10 |

## Epic C — Level 4: The Summit (Moksha) — P0
| ID | Task | Files | Effort | Verify |
|---|---|---|---|---|
| C1 | Background art `level4_background.png` (Shikhar, white/gold/open sky) | assets | M (art) | asset test |
| C2 | Rebuild `_build_level4` against the art | `level_layouts.py` | M | A2 + playtest #9 |
| C3 | Crumbling blocks: `CrumblingPlatform` breaks 1s after landing, respawns after N s | `level_layouts.py`, `level_scene.py` | M | unit test + playtest |
| C4 | Hazards: water channels + flame pillars against art | `hazards.py` | S | A2 |
| C5 | Transition 4→Victory: `adinath.png`, bow, golden glow, then Victory | `transition_scene.py`, `level_scene.py` (`next_level > 4` branch) | M (+art) | playtest #11 |
| C6 | Victory: `digambar_garbhalaya.png`; remove from `ALLOWED_MISSING_LITERAL_ASSETS` | `victory_scene.py`, `tests/test_portability.py`, assets | S (+art) | asset test |
| C7 | Open Levels 3–4 to kid/standard modes once B and C are complete (Q2: gated only because L3/L4 are unfinished) | `level_scene.py:810` | S | playtest #7 |

## Epic D — Spec fidelity for Levels 1–2 — P1
| ID | Task | Files | Effort | Verify |
|---|---|---|---|---|
| D1 | Support items get distinct effects: TTC Bus/Car speed boost; Ghanta hazard repel; Snake water immunity; Chanvar fire clear; Lion reveal; Bull jump boost | `box_system.py`, `level_scene.py` (Player), `hazards.py` | L | unit tests per effect + playtest #12 |
| D2 | Level 2: snakes are the hazard set (Q3 decided). No water/fire in L2. Spec amended: hazards are designer-defined per level | `hazards.py` | M | A2 + playtest #6 |
| D3 | Level 2 moving stone platforms | `level_layouts.py`, `level_scene.py` | M | playtest #6 |
| D4 | Distinct hazard behaviour: water slows + drains; fire stuns | `hazards.py`, `level_scene.py` | S | unit test |
| D5 | Keep L2 flight after Akshat (Q4 decided); add one paragraph to `docs/GDD_v2_refined.txt` documenting it | `docs/` | S | — |
| D6 | Fix stale `bgm_loop.wav` reference | `victory_scene.py` | S | asset test |

## Epic E — Polish — P2
| ID | Task | Files | Effort |
|---|---|---|---|
| E1 | Monk reward = existing highlight + brief pulse/zoom; no camera pan (Q5 decided) | `level_scene.py` |  S |
| E2 | Per-level music variations | `assets/audio/bgm`, `level_scene.py` | M (audio) |
| E3 | Golden-glow + hold on final transition | `transition_scene.py` | S |
| E4 | Refresh `docs/GDD.md` / `ARCHITECTURE.md` to reflect v2 | docs | S |

## Epic F — Release
| ID | Task |
|---|---|
| F1 | Full `docs/PLAYTEST_CHECKLIST.md` pass on a clean Windows machine with the built `.exe` |
| F2 | Merge `v2-dev` → `main`, tag `v2.0`, CI publishes release |

## Your new ideas (v2 is at ideation — add here, then we spec + ticket them)
- …

## Designer decisions (2026-09-06)
- **Q1 Scoring:** points derived only from total time, so ordering matches the spec. (Bonuses remain optional/future.)
- **Q2 Kid/standard end after L2** only because L3/L4 are unfinished; open them when Epics B+C are done. Designer has further ideas — see brainstorming.
- **Q3 Level 2 snakes:** keep, and **no** water/fire in Level 2. Spec amended so hazard types are designer-defined per level (Water/Fire is the default, not a rule).
- **Q4 Level 2 flight after Akshat:** keep; document in spec.
- **Q5 Monk reward:** highlight + pulse, no camera pan.

## Suggested order
A0 → A1 → A2–A5 (tests first, so every later change is guarded) → A7 (after Q1) → B → C → D → E → F.
