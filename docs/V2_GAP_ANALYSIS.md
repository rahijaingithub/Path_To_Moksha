# V2 Gap Analysis — Spec (`GDD_v2_refined.txt`) vs. Code at `v1.0`

Method: every row below was verified by reading the file cited. "Done" means the code
matches the spec; "Gap" means it does not. Nothing here is inferred from memory.

## Summary
| Area | Status |
|---|---|
| Game flow (Title → Character Select → L1 → … → Victory) | **Done**, but kid/standard modes stop after L2 (`level_scene.py:810-812`) |
| Box definitions for all 4 levels | **Done** — `box_system.LEVEL_BOX_DEFS` matches spec item-for-item |
| Box categories incl. No-Effect (Wrong Lakshan) | **Done** |
| Support item *distinct effects* (speed boost, water immunity, fire clear, reveal platforms, jump boost) | **Gap** — every support item does the same thing: `+15s` (`box_system._apply_item`) |
| Water + Fire hazards in every level | **Gap in L2** — L2 has two patrolling *snakes* and no water/fire (`hazards.py:158-164`) |
| Distinct hazard behaviour (water slows, fire stuns) | **Gap** — both give `-30s` + 1s stun (`hazards.py:14-16`) |
| L2 moving stone platforms | **Gap** — all platforms static (`level_layouts.py`) |
| L3 disappearing marble tiles | **Gap** — docstring says "disappearing-style", nothing implements it |
| L4 crumbling blocks (break 1s after landing) | **Gap** — not implemented |
| L3 / L4 backgrounds | **Gap** — only `level1_background.png`, `level2_background.png` exist; L3/L4 load a pink placeholder |
| Transition 1→2 (JSOT temple, walk) | **Done** — `transition_scene.TRANSITION_DATA[2]` |
| Transition 2→3 (Parshvanath, bow) | **Done** |
| Transition 3→4 (Mahavir, bow) | **Gap** — reuses `jsot_temple.png`; no `mahavir.png` asset |
| Transition 4→Victory (Adinath, bow, golden glow) | **Gap** — L4 completion jumps straight to `VictoryScene`; no `adinath.png` |
| Victory screen shows Digambar Garbhalaya | **Gap** — `digambar_garbhalaya.png` is missing (explicitly allow-listed as missing in tests) |
| Monk per-level questions (4 per level, adult + kids pools, non-repeating) | **Done** |
| Monk reward: highlight Goal + one Support box | **Done** (`box_system.highlight_goal_box`) |
| Monk reward: *camera pans* to the box | **Gap** — highlight only; single-screen levels, so a pan may be unnecessary (see Open Questions) |
| Scoring: total time, lower is better | **Gap / inconsistent** — three formulas coexist: per-level `time_remaining*10` (`level_scene.py:1135`), victory `10000 - time*15 + monk*1500` (`victory_scene.py:49`), leaderboard sorts by `final_score`. Spec says the metric is time. |
| Rankings Moksha Margi / Shravak / Bhakt (optional) | **Done** (`victory_scene.py:59-65`) |
| Character select Boy/Girl (Shravak/Shravika) | **Done** |
| Keyboard + gamepad + touch | **Done** (`input_manager.py`) |

## Things in the code that are NOT in the spec (decide: keep, cut, or spec them)
1. **Flight in Level 2** — after finding Akshat the player can fly to a Bhagwan platform
   (`level_scene.py:47,562,692`; `level_goals.json` "Fly to the Bhagwan…"). A deliberate v1
   design; not in `GDD_v2_refined.txt`.
2. **Snakes as hazards in Level 2** — spec makes the Snake a *support* Lakshan, not a threat.
3. **"To be continued" after Level 2** in kid/standard modes — a v1 release cut, not a design.
4. **Three game modes** (kid / standard / developer) affecting platform visibility and game-over.
5. **Level-2-only jump-force table** (`settings.LEVEL_JUMP_FORCES`).

## Repository hygiene gaps (not gameplay)
- `assets/images/*/Old*` and `assets/audio/Old` — 36 legacy files tracked in git (~bloat).
- `.github/workflows/build.yml` `commit-builds` job does `git add dist/PathToMoksha.exe`;
  since `dist/` is now ignored this job **will fail on the next push to `main`**. The job
  is redundant with the artifact upload + tagged release; remove it.
- `victory_scene.py:83` plays `bgm_loop.wav`; only `bgm_loop.ogg` exists (AssetManager
  falls back, but the reference is stale).
- Only one test module; nothing covers scene-transition resets, profile I/O, level
  completability, or box/hazard placement — the four areas where the last 8 bug-fix
  commits landed.
