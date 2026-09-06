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
