# Playtest Checklist — manual QA gate

Run before any merge to `main` and before any release. Use the **built `.exe`** on a
machine that is *not* the dev machine at least once per release. Tick, date, initial.

## Launch & first run
1. [ ] Fresh machine, no prior data: exe starts, no console window, no error dialog.
2. [ ] Audio plays (bgm + sfx) with default Windows audio drivers.
3. [ ] Windowed → fullscreen → windowed: no letterbox artefacts, no input loss.
4. [ ] Title screen: keyboard, gamepad, and mouse/touch each navigate the menu.

## Flow
5. [ ] Character select → Level 1 → Level 2 with the *keyboard only*.
6. [ ] Same run with a *gamepad only* (no stuck menu options, Back button behaves).
7. [ ] Kid / standard / developer modes each reach the intended last level.
8. [ ] Level 3 completable start-to-finish without developer mode.
9. [ ] Level 4 completable start-to-finish without developer mode.
10. [ ] Transition 3→4 shows Mahavir and the devotee walks in and **bows** (a second bow
        after Level 3's in-level one — intended, see #48). On 1→2 the devotee walks to the
        temple door and then **stands still** — no stepping on the spot. Boy and girl.
11. [ ] Transition 4→Victory shows Adinath, glow, then Victory over the title screen's
        photograph of the temple (no magenta anywhere). The score panel reads clearly over
        the photo; the button says "SEE THE LEADERBOARD" and goes there; the focus line
        counts distraction boxes only (open one distraction and one support box, leave the
        rest: the support box must not change the count).

## Mechanics
12. [ ] Each Support item does its *specific* thing (bus/car boost, bell repel, snake water
        immunity, chanvar fire clear in L4 / "who bows, rises" text in L3, lion reveal,
        bull jump).
13. [ ] Distraction: −30s and 5s freeze, stun sprite shown, input ignored during freeze.
14. [ ] Score on Victory, Leaderboard, and saved profile all agree with each other.
15. [ ] Monk: answer correctly → goal + one support box highlighted; wrong → nothing; not
        visited → nothing. No question repeats in one run.
16. [ ] Hazard contact: penalty applied once per contact (cooldown works), player never
        gets stuck inside a hazard or platform.
17. [ ] Timer expiry → game over screen → Restart and Back-to-title both work.

## Persistence
18. [ ] Profile saved; leaderboard shows the run; relaunch exe and it is still there.
19. [ ] Corrupt `profiles.json` by hand → game still starts (recovers, does not crash).

## Regression traps (each was a real bug)
20. [ ] Enter/leave every scene twice in a row: no input lockup, no stale score shown.
21. [ ] Analog stick held on menu, then released: selection stops moving.
22. [ ] Missing asset test: temporarily rename one PNG → pink placeholder, no crash.
23. [ ] **Keyboard-only, no mouse, no gamepad, from a cold start:** reach Options,
        then the tutorial, then start a level. (Item 4 above already covered this
        and was never ticked; the keyboard could not navigate any menu at all.)
24. [ ] Press **UP** to jump — not just SPACE. Both must work everywhere.
25. [ ] Level 2 after Akshat: hold SPACE to fly, tap and release UP mid-flight —
        flight must not stutter or drop.
26. [ ] Tutorial: each arrow-key tap moves **one** tab, not two.
27. [ ] Monk question on a keyboard: tapping SPACE must NOT move the highlight.
        Up/Down move it; Enter submits. Confirm you can return to the first option.
28. [ ] Monk questions: play several and confirm the correct answer is **not**
        always the top option. (All 32 questions ship with correct at index 0.)
29. [ ] Play as the **girl** character and watch the walk/run/idle/jump/fall
        animations: the drawn pose must change, not freeze mid-cycle.
30. [ ] Gamepad **A** confirms: selects on the title screen and submits a Monk answer.
31. [ ] **Sacred volume — Monk:** you cannot jump or fly above the Monk's head in
        Levels 1 and 2, AND you can still land on his ledge and talk to him.
        (Clearance is only 3px by design — Monk.HEIGHT minus PLAYER_HEIGHT.)
32. [ ] **Sacred volume — Parshvanath:** after the Akshat box in Level 2, you cannot
        fly above the murti. No visible platform appears where the wall is.
33. [ ] Level 4 in developer mode: the Monk is placed randomly, so confirm his
        invisible column has not landed somewhere that blocks a needed route.
        (Level 3's Monk is fixed since 2026-09-23 — see #39.)
34. [ ] **Esc on the title** shows "Leave the pilgrimage?" — it does not quit outright.
        Esc again cancels; Enter/A quits. Same for the Exit menu item and mouse click.
35. [ ] **Pause:** Esc mid-level opens the pause menu. The countdown clock stops.
        Resume returns to play with the clock where it was; Quit to title discards
        the run (and says so). Nothing behind the overlay responds while paused.
36. [ ] Monk questions show **three** options. All three are selectable by keyboard,
        gamepad and mouse, and the third is not clipped by the hint line.
37. [ ] Read the two wrong options: each should be a real Jain idea that is
        plausibly confusable, not an obvious joke. Flag any that give the answer away.

## Level 3 — Jal Mandir (added 2026-09-23)
38. [ ] **Slopes (lotus 9, 19, 20, 21):** walk up and down each petal both ways — the
        devotee follows the curve, never jitters or drops through. Jump up from below
        a big petal: you pass through it and land on top.
39. [ ] **Monk fixed in the centre arch:** he stands in the middle of the pavilion,
        you can walk past him on the plinth, and you cannot jump over him.
40. [ ] **Reveal order:** open the Akshat box. The Monk fades out completely **before**
        the Bhagwan image starts to appear, and pressing UP/ACTION at his seat does
        nothing until the image is fully shown. Then the offering completes the level.
41. [ ] **Mahavir image art:** the shikhar shows Mahavir Bhagwan, not a pink square
        (fails until `mahavir_bhagwan.png` is added).
42. [ ] **Level 3 lake:** you start on the lower-left lily pad. Drop into the water
        anywhere: you sink (splash + bubbles) with the red danger flicker, lose 30s,
        and rise again on the last rock, flower or petal you stood on — never back in
        the water. No box ever appears down in the lake, and there are no hazard
        blocks anywhere in Level 3.
43. [ ] **Walk, boy AND girl (2026-09-23/26):** hold left/right as each character — the new 6-frame walk
        plays the whole time you move (not a run), faces the right way both directions,
        no pink/magenta edges, no size jump between standing and walking. Note whether
        the feet look like they slide; if so, flag it (frame-time tweak, see DECISION_LOG
        Phase 8).
44. [ ] **Level 3 bird:** a bird crosses the sky every few seconds, both directions,
        and never blocks you. When you find the Akshat it tumbles onto the white lotus
        at the far right and lies there, and the goal line offers both choices.
45. [ ] **Helping the bird — mantra puzzle:** stand beside it, press ACTION: grains fly
        to it, then the Namokar Mantra's 5 lines appear shuffled. UP/DOWN (or the mouse)
        moves the highlight; ACTION numbers a line 1, 2, 3... in the order you pick them.
        A line turns green if its number is its true place, red if not. With all five
        numbered, reds clear after a moment and greens stay; keep going until all green.
        The clock never moves meanwhile. All green: the bird glows, flies away, +4:00.
        **Skip** ends the bonus round: the bird stays resting, the help prompt never
        returns, no bonus, and the clock runs again. Try keyboard, gamepad and mouse.
46. [ ] **Ignoring the bird:** offer the Akshat without helping — no penalty, no message
        about the bird. Your Level 3 time on the results/Victory screen is your real time
        either way (never negative after the bonus).
47. [ ] **Karuna bonus level:** solving the Namokar Mantra drops you into "A Glimpse of
        the Punya's Fruit" on its own 4:00 clock. Carry the injured man to the hospital and
        ACT to treat him; lead the lost man to the temple (he needs no press). Both done →
        the time left is shown, you land back in the Hall exactly where you stood, and the
        Hall's clock jumps up by that amount ("Karuna returns MM:SS to your path"). Finish
        Level 3 and check the results screen records the time you really took — never
        negative, never shorter than the clock says. Let the clock run out once: you return with nothing banked and
        nothing lost. In the glimpse the player is drawn as **the doctor** (the community's
        Dr. Mahendra Jain, with his consent), not the boy or the girl — check it with both
        devotees, and that his clothes and height do not change when he stops walking.
        His legs should alternate as he walks (grey trousers, six frames), and when he
        stops he turns to face you, the same height, feet side by side on the sidewalk line.
        The opening line says who he is ("This is you in a life to come…") and stays long
        enough for a child to read it.
        *Doctor checks passed 2026-11-13 (designer, via `main.py`, as the boy and as the girl):
        opening line, alternating walk, front-facing stop.*
48. [ ] **Offering bow:** at the Monk's seat, ACTION plays the bow (down, hold, up) with
        light rising to Mahavir Bhagwan, then the level ends. The 3→4 transition then
        walks in and bows AGAIN (intended since 2026-10-20). Check the boy and the girl.

## Controller Buttons screen (added 2026-10-25)
49. [ ] **Rebind on a pad:** Options → "Controller Buttons". Pick *Jump*, press a different
        face button: the row shows "Button N", the press did NOT jump, confirm or leave the
        screen. Save & Return, then play Level 1: the new button jumps, and the old one
        does not. Quit and relaunch: the binding survived.
50. [ ] **Escape hatches:** while a row is listening, Esc cancels with nothing changed and
        the countdown runs out on its own after ~6 s. Bind *Walk Left* and *Walk Right* to
        the same button: an orange warning appears but nothing is blocked (guidance, not
        gating). Reset to Defaults → Save: the pad is back on the built-in A/B layout.
51. [ ] **No pad:** unplug the controller. The Options row still opens the screen, every
        row reads "Default: …", and selecting one shows "Connect a controller…" instead
        of listening. Keyboard controls are unchanged throughout.

## Level 4: Kailash (added 2026-11-14; open to every mode)
52. [ ] **Both ways up:** from the start shelf go stream block, ice shelf. Then climb once
        by the left (great mesa, high plateau, summit) and once by the right (drop to the
        rock outcrop, terrace, ridge, Monk's shelf, summit). Every jump is makeable without
        pixel-perfect timing, and the devotee is always visible, including on the summit.
53. [ ] **Crumbling:** stand on the ice shelf, the spire's snow, and the right ridge's. It cracks and
        shakes for about a second, breaks into falling pieces, and drifts back about three
        seconds later. A fall from the spire lands on the great mesa. It never reforms
        around the devotee. Does a painted rock with snow that vanishes read as "this
        ledge is gone"?
54. [ ] **Cold shock:** step onto the valley floor. The clock turns icy blue, reads
        "COLD x2" and loses two seconds a second; the goal line says why. Jumping on the
        floor does not stop it. Nobody lifts the devotee out: climb to the start shelf,
        the stream block or the rock outcrop and the clock is normal again. No box ever
        sits on the valley floor.
55. [ ] **The summit gate:** the summit is bare until the Akshat is found; then Level 1's
        gate fades in, clear of the clock bar. UP or ACTION at the gate ends the level,
        then the bow to Adinath Bhagwan and the Victory page follow. Before the Akshat,
        ACTION on the summit does nothing.
56. [ ] **The whole pilgrimage in kid and in standard mode:** after Level 3 and its bow the
        run goes on to Level 4, not to "to be continued". Finishing Level 4 leads to the
        bow to Adinath Bhagwan, the Victory page, then the leaderboard with all four
        levels scored. Options offers Starting Level 1 to 4 in every mode.
57. [ ] **Snow ledges (Level 4 only):** no gold lines on Kailash. Every ledge is an uneven
        drift of snow with a soft blue shadow; Levels 1 to 3 keep their gold. Can each
        ledge be found at a glance, above all the start shelf and the stream block, which
        lie on white ground? The spire, the ice shelf and the right ridge are thinner,
        bluer ice with hairline cracks: does a player notice the difference after one
        fall, and does a young child cope if they do not?
58. [ ] **Level 3 flowers hold only from above:** jump straight up under any lotus or
        lily pad: no head bump, you pass through and land on it. Walking sideways into
        one does not stop you. The rocks and the pavilion still block from every side.
        Is the level still hard enough now that some climbs are a single hop?
59. [ ] **Level 3 has no gold lines:** each flower and lily pad carries only a faint pale
        light on the edge that holds, with a short brighter pulse when you land. The
        rocks and the pavilion carry no mark. Can a new player tell where to stand,
        on the rocks above all? Does the devotee look as if they stand on the flower,
        not above it or inside it?
