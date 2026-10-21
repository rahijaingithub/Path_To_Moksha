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
| B1 | Background art `level3_background.png` — **done 2026-09-23 as the Jal Mandir lotus lake** (spec amended; see DECISION_LOG Phase 7) | `assets/images/backgrounds/`, `image_generation_prompts.md` | M (art) | asset test |
| B2 | Rebuild `_build_level3` platforms against the art — **done 2026-09-23** (traced lines + one-way slopes; Monk fixed in the pavilion; Monk-fade → Mahavir reveal → offering; Mahavir art added 2026-09-26) | `level_layouts.py` | M | A2 + playtest #8 |
| B3 | ~~Disappearing tiles in Level 3~~ — **moved to Level 4 as C8** (designer, 2026-09-27) | — | — | — |
| B4 | Hazards — **done 2026-09-23 (designer):** no hazard blocks in Level 3; the lake floor itself drowns | `hazards.py` | S | A2 |
| B5 | Transition 3→4 — **done 2026-09-27**: shows Mahavir Bhagwan (`transitions/mahavir.png`, lion lanchhan) and walks in **without** bowing (the bow is inside Level 3) | `transition_scene.py`, assets | playtest #10 |

## Epic C — Level 4: The Summit (Moksha) — P0
| ID | Task | Files | Effort | Verify |
|---|---|---|---|---|
| C1 | Background art `level4_background.png` (Shikhar, white/gold/open sky) | assets | M (art) | asset test |
| C2 | Rebuild `_build_level4` against the art | `level_layouts.py` | M | A2 + playtest #9 |
| C3 | Crumbling blocks: `CrumblingPlatform` breaks 1s after landing, respawns after N s | `level_layouts.py`, `level_scene.py` | M | unit test + playtest |
| C4 | Hazards: water channels + flame pillars against art | `hazards.py` | S | A2 |
| C5 | Transition 4→Victory — **done 2026-09-27** (same work as backlog BL4): Moolnayak Adinath Bhagwan, bow, golden glow, then Victory | `transition_scene.py`, `level_scene.py` | M | playtest #11 |
| C6 | Victory: `digambar_garbhalaya.png`; remove from `ALLOWED_MISSING_LITERAL_ASSETS` | `victory_scene.py`, `tests/test_portability.py`, assets | S (+art) | asset test |
| C7 | Open Levels 3–4 to kid/standard modes once B and C are complete (Q2: gated only because L3/L4 are unfinished) | `level_scene.py:810` | S | playtest #7 |
| C8 | Disappearing tiles ("Illusions of permanence" — moved here from Level 3, designer 2026-09-27): `TimedPlatform` fading in/out on a cycle. **Open:** which support reveals them in Level 4 — the spec's reveal was Mahavir's Lion (Level 3), while Level 4's correct Lakshan is the Bull; and how it combines with C3's crumbling blocks | `level_layouts.py`, `level_scene.py`, `box_system.py` | L | unit test on cycle timing + playtest |

## Epic G — Level 3 bonus level: Karuna (the two rescues) — P2 (designer idea, 2026-10-20)
Opened by the Namokar Mantra puzzle that already exists in Level 3. The mantra's current
flat **+4:00 is removed**; the four minutes becomes the bonus level's own clock, and the
devotee banks **whatever is left on it** when both rescues are done. Reward therefore
scales with how efficiently the player helps, and still caps at 240s — so Q1 scoring and
the Level 3 balance are unchanged.

**Narrative frame (designer, 2026-10-20):** the Jiv Daya of saving the bird creates so much
**punya** that the soul is born as a compassionate spiritual doctor — who then gets the
chance to save an injured man's **body** (carry him to hospital and treat him) and a lost
man's **soul** (guide him to the temple). So the bonus level is a *next birth*, not a side
area: its setting, and arguably its player sprite (a doctor, not the devotee), are its own.
Note this adds a third verb beyond carry/lead — **treating** at the hospital. See the
DECISION_LOG for the one doctrinal wrinkle to put to the Paathshala (returning from a next
birth into the same Level 3 life).

Flow: mantra solved → bird revives and flies off → bonus level loads automatically →
carry the injured man to the hospital **and** lead the lost man to the temple → Level 3
resumes **at the exact position left**, with the banked seconds added. Bonus clock reaches
0:00 → failure: return to Level 3 with 0:00 banked (Level 3 loses nothing; only upside is
forfeited). The bird stays saved either way, since it revives before the bonus begins.

| ID | Task | Files | Effort | Verify |
|---|---|---|---|---|
| G1 | ~~Resume plumbing~~ — **done 2026-10-20**: `on_enter(resume=True)` early-returns (restores `current_level`, re-fades, restarts BGM via the new `_play_level_music`); `_can_resume` refuses and falls through to a normal build when nothing is built yet, the level differs, or the level already ended | `level_scene.py` | S | `tests/test_level_resume.py` (7 tests) |
| G2 | ~~Bonus scene skeleton~~ — **done 2026-10-20**: `SCENE_BONUS` + `bonus_scene.py`, registered in `main.py`; `BONUS_TIME_LIMIT` (240) replaces `JIV_DAYA_TIME_BONUS`, which is gone; saving the bird now routes here instead of paying a flat +4:00; outcome card then `resume=True` back into Level 3. Level 3's clock is paused for free (SceneManager updates only the active scene). Hospital/temple staged as markers; banked seconds published to `shared["bonus_banked_seconds"]` for G4 | `settings.py`, `main.py`, `bonus_scene.py`, `level_scene.py` | M | `tests/test_bonus_scene.py` (10 tests) |
| G3 | ~~The two rescues~~ — **done 2026-10-20**: `rescue_npc.py` (`RescueNPC`, states waiting→carried/following→treating→delivered); three verbs — **carry** the injured man, **treat** him at the hospital (2.5s), **lead** the lost man, who recognises the temple himself. Carrying slows the devotee to 0.72×; the lost man wanders while unhelped. Figures drawn procedurally until G5 | `bonus_scene.py`, `rescue_npc.py` | L | `tests/test_rescues.py` (10 tests) |
| G4 | **Bank the reward through `jiv_daya_bonus`** (or an equivalent excluded field) so the banked seconds raise the clock and score but are **not** counted as time taken. Without this, Level 3's recorded time goes negative — the exact bug fixed on 2026-09-23 (see `_advance_level`'s comment) | `level_scene.py` | S | unit test: bank 240s, finish L3 in 1:30, assert `level_times[3]` is 1:30 and never negative |
| G5 | **Art + wording.** Prompts written 2026-10-20 as `image_generation_prompts.md` §8, **hyperrealistic** per the designer, bloodless (sitting holding his leg, or limping): `injured_man_sitting.png`, `injured_man_carried.png`, `lost_man_walk_right.png` (4 frames). Loading is wired and tested — dropping the files into `assets/images/sprites/` needs no code change. Still needs the bonus background. `injured_man.png`, `lost_man.png`, hospital and temple markers, bonus background; doctrinal line for why the mantra opens it (confirm with the Paathshala, as with the Chanvar/Lion wordings) | assets, `image_generation_prompts.md` | M (art) | asset test + playtest |

**Depends on C7.** Level 3 is still developer-mode-only (`level_scene.py` gates kid/standard
at `self.level == 2`), so none of Epic G reaches a Paathshala player until C7 opens L3/L4.

## Epic D — Spec fidelity for Levels 1–2 — P1
| ID | Task | Files | Effort | Verify |
|---|---|---|---|---|
| D1 | Support items get distinct effects: TTC Bus/Car speed boost; Ghanta hazard repel; Snake water immunity; Chanvar fire clear (Level 4; in Level 3 the Chanvar means "who bows in humility, rises higher" — effect to choose); Lion reveal; Bull jump boost | `box_system.py`, `level_scene.py` (Player), `hazards.py` | L | unit tests per effect + playtest #12 |
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
- **Level 3 bonus level (Karuna):** specced as **Epic G** above (designer, 2026-10-20).

## Backlog (designer, 2026-09-23)
| ID | Item | Where | Verify |
|---|---|---|---|
| BL1 | ~~Mahavir Bhagwan image for the Level 3 reveal~~ — **done 2026-09-26**: designer's lion-lanchhan image, square-cropped to the shikhar slot (`assets/images/items/mahavir_bhagwan.png`; original in `items/_source/`) | — | asset test + playtest #41 |
| BL2 | Tired-bird art (optional; prompt in `image_generation_prompts.md` §7) | `assets/images/sprites/bird_fallen.png` | playtest #44 |
| BL3 | Third-party web art to re-source or license **before any public release**: the bird flight sheet, and — if the designer sources rather than generates them (accepted 2026-10-20) — the Karuna bonus level's injured and lost men | `assets/images/sprites/bird_fly_*.png`, `_source/bird_sheet.jpg`, `sprites/injured_man_*.png`, `sprites/lost_man_*.png` | licence on file for each |
| BL4 | ~~Adinath in the Level 4 → Victory transition~~ — **done 2026-09-27**: Level 4 now ends in transition 5 (Moolnayak Adinath Bhagwan, bow, golden glow) which fades to Victory; image `transitions/adinath.png` (original in `transitions/_source/`) | `transition_scene.py`, `level_scene.py` | playtest #11 |

## Designer decisions (2026-09-06)
- **Q1 Scoring:** points derived only from total time, so ordering matches the spec. (Bonuses remain optional/future.)
- **Q2 Kid/standard end after L2** only because L3/L4 are unfinished; open them when Epics B+C are done. Designer has further ideas — see brainstorming.
- **Q3 Level 2 snakes:** keep, and **no** water/fire in Level 2. Spec amended so hazard types are designer-defined per level (Water/Fire is the default, not a rule).
- **Q4 Level 2 flight after Akshat:** keep; document in spec.
- **Q5 Monk reward:** highlight + pulse, no camera pan.

## Designer decisions (2026-10-20)
- **Q6 Mantra reward:** the flat +4:00 is **replaced** by the bonus level. The 4 minutes
  becomes the bonus clock; the devotee banks the time **left** on it.
- **Q7 Bonus failure:** running the bonus clock to 0:00 **is** failure — return to Level 3
  with nothing banked. Level 3's own clock and score are untouched.
- **Q8 Partial completion:** all-or-nothing. One rescue delivered banks 0:00.

## Suggested order
A0 → A1 → A2–A5 (tests first, so every later change is guarded) → A7 (after Q1) → B → C → D → E → G → F.
