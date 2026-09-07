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
10. [ ] Transition 3→4 shows Mahavir and the bow animation.
11. [ ] Transition 4→Victory shows Adinath, glow, then Victory with the Garbhalaya image.

## Mechanics
12. [ ] Each Support item does its *specific* thing (bus/car boost, bell repel, snake water
        immunity, chanvar fire clear, lion reveal, bull jump).
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
33. [ ] Levels 3-4 in developer mode: the Monk is placed randomly, so confirm his
        invisible column has not landed somewhere that blocks a needed route.
