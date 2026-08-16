"""
assign_controller.py — Interactive controller button assignment wizard for Path to Moksha.

Supports MULTIPLE button/axis/hat bindings per game action!

Run this script directly in terminal:
    python assign_controller.py
"""
import os
import sys
import json
import time
import pygame

# Find base project directory
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(TOOLS_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "controller_map.json")

# Full list of configurable actions with direction hints
ACTIONS = [
    ("move_left",   "Walk Player Left",                    "D-pad LEFT / Stick LEFT"),
    ("move_right",  "Walk Player Right",                   "D-pad RIGHT / Stick RIGHT"),
    ("jump",        "Jump",                                "D-pad UP / Stick UP / Face button"),
    ("fly_up",      "Fly Up (Level 2 Flying)",             "D-pad UP / Stick UP"),
    ("fly_down",    "Fly Down (Level 2 Flying)",           ">>> D-pad DOWN / Stick DOWN <<<"),
    ("action",      "Interact / Open Box / Gate Entry",    "Face button (e.g. A/Cross)"),
    ("back",        "Pause / Back to Menu",                "Face button (e.g. B/Circle)"),
    ("menu_up",     "Menu Cursor Up",                      "D-pad UP / Stick UP"),
    ("menu_down",   "Menu Cursor Down",                    ">>> D-pad DOWN / Stick DOWN <<<"),
    ("menu_left",   "Menu Cursor Left",                    "D-pad LEFT / Stick LEFT"),
    ("menu_right",  "Menu Cursor Right",                   "D-pad RIGHT / Stick RIGHT"),
    ("menu_select", "Menu Select / Confirm",               "Face button (A/Cross)"),
    ("menu_back",   "Menu Cancel / Back",                  "Face button (B/Circle)"),
]


def format_mapping_desc(mappings_list):
    """Formats a list of mapping dicts into human-readable label."""
    if not mappings_list:
        return "Not Assigned (Keyboard Only)"
    
    # Handle single dict legacy compatibility
    if isinstance(mappings_list, dict):
        mappings_list = [mappings_list]

    parts = []
    for mapping in mappings_list:
        m_type = mapping.get("type")
        if m_type == "button":
            parts.append(f"Button {mapping['index']}")
        elif m_type == "axis":
            direction = "+" if mapping.get("direction") == "positive" else "-"
            axis_hint = "(Stick DOWN)" if mapping.get("direction") == "positive" else "(Stick UP)"
            parts.append(f"Axis {mapping['index']} ({direction}) {axis_hint}")
        elif m_type == "hat":
            val = mapping.get("value", [0, 0])
            if val == [0, 1]:
                direction_hint = "(D-pad UP)"
            elif val == [0, -1]:
                direction_hint = "(D-pad DOWN)"
            elif val == [-1, 0]:
                direction_hint = "(D-pad LEFT)"
            elif val == [1, 0]:
                direction_hint = "(D-pad RIGHT)"
            else:
                direction_hint = ""
            parts.append(f"Hat {mapping['index']} {val} {direction_hint}")
        else:
            parts.append("Unknown")

    return " | ".join(parts)


def detect_conflicts(mappings):
    """Return a list of (action_a, action_b, shared_input) conflict tuples."""
    conflicts = []
    keys = list(mappings.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            for inp in mappings.get(a, []):
                if inp in mappings.get(b, []):
                    conflicts.append((a, b, format_mapping_desc([inp])))
    return conflicts


def load_existing_mapping():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_mappings = data.get("mapping", {})
                
                # Normalize legacy single-dict mappings into lists
                normalized = {}
                for k, v in raw_mappings.items():
                    if isinstance(v, dict):
                        normalized[k] = [v]
                    elif isinstance(v, list):
                        normalized[k] = v
                return normalized
        except Exception:
            pass
    return {}


def save_mapping(controller_name, mappings):
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "controller_name": controller_name,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mapping": mappings
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\n[✔] Mapping saved successfully to: {CONFIG_FILE}\n")


def listen_for_input_multiple(js, screen, font, action_name, action_desc, hint, max_inputs=3, timeout=7.0):
    """Listens for up to `max_inputs` controller inputs for a single action."""
    print(f"\n>> Assigning [{action_name}] — {action_desc}")
    print(f"   💡 Expected input: {hint}")
    print("   Press physical controller button / move stick / press D-pad...")
    print("   (To add multiple buttons, press them one after another!)")

    collected = []
    clock = pygame.time.Clock()

    for input_slot in range(1, max_inputs + 1):
        if len(collected) > 0:
            print(f"   Current bindings for [{action_name}]: {format_mapping_desc(collected)}")
            print("   Press ANOTHER button to add it, or wait for timeout to finish this action.")

        start_time = time.time()
        detected = None

        while time.time() - start_time < timeout:
            dt = clock.tick(60)
            remaining = max(0, int(timeout - (time.time() - start_time)))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return collected

                elif event.type == pygame.JOYBUTTONDOWN:
                    detected = {"type": "button", "index": event.button}

                elif event.type == pygame.JOYAXISMOTION:
                    if abs(event.value) > 0.55:
                        direction = "positive" if event.value > 0 else "negative"
                        detected = {"type": "axis", "index": event.axis, "direction": direction, "threshold": 0.5}

                elif event.type == pygame.JOYHATMOTION:
                    if event.value != (0, 0):
                        detected = {"type": "hat", "index": event.hat, "value": list(event.value)}

            if detected is not None:
                # Avoid duplicate entries in the list
                if detected not in collected:
                    collected.append(detected)
                    print(f"   [✔] Added Slot #{len(collected)}: {format_mapping_desc([detected])}")
                else:
                    print(f"   [!] Input already assigned to this action.")
                time.sleep(0.45)  # debounce threshold
                pygame.event.clear()
                break

            # Render countdown on pop-up window
            screen.fill((25, 30, 45))
            txt0 = font.render(f"💡 Hint: {hint}", True, (200, 230, 255))
            txt1 = font.render(f"Assigning: {action_desc}", True, (255, 215, 0))
            if len(collected) == 0:
                txt2 = font.render(f"Press physical controller input... ({remaining}s)", True, (200, 240, 200))
            else:
                txt2 = font.render(f"Bound: {format_mapping_desc(collected)} | Press 2nd input... ({remaining}s)", True, (255, 255, 150))

            screen.blit(txt0, (20, 10))
            screen.blit(txt1, (20, 50))
            screen.blit(txt2, (20, 90))
            pygame.display.flip()

        if detected is None and len(collected) > 0:
            # Timeout reached after at least 1 input added -> finish this action
            break

    if not collected:
        print("   [!] Skipped (No input recorded).")

    return collected


def main():
    print("=" * 65)
    print("      PATH TO MOKSHA — MULTI-BUTTON CONTROLLER WIZARD")
    print("=" * 65)
    print("\n⚠️  IMPORTANT REMINDERS:")
    print("  • fly_up  / menu_up   → Press D-pad UP   (hat value [0, +1])")
    print("  • fly_down / menu_down → Press D-pad DOWN  (hat value [0, -1])")
    print("  • Each action shows a 💡 hint — follow it carefully!")
    print("  • After all actions, a conflict check will run automatically.")

    pygame.init()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    if count == 0:
        print("\n[!] No controller connected. Connect controller and try again.\n")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    controller_name = js.get_name()

    print(f"\n[✔] Connected Controller: {controller_name}")

    screen = pygame.display.set_mode((620, 170))
    pygame.display.set_caption("Controller Rebinding — Press buttons to assign")
    font = pygame.font.SysFont("Arial", 15)

    mappings = load_existing_mapping()

    try:
        print("\nStarting binding process for all 13 game actions...")

        for key, desc, hint in ACTIONS:
            cur_map = mappings.get(key, [])
            print(f"\nCurrent: {format_mapping_desc(cur_map)}")
            res = listen_for_input_multiple(js, screen, font, key, desc, hint)
            if res:
                mappings[key] = res

        # Conflict detection
        conflicts = detect_conflicts(mappings)
        if conflicts:
            print("\n" + "=" * 75)
            print("  ⚠️  CONFLICT WARNINGS — Same input mapped to multiple actions!")
            print("=" * 75)
            for a, b, inp in conflicts:
                # Only warn on conflicts between opposing directional actions
                opposing = {("fly_up", "fly_down"), ("menu_up", "menu_down"),
                            ("move_left", "move_right"), ("menu_left", "menu_right")}
                pair = (min(a, b), max(a, b))
                severity = "🔴 CRITICAL" if pair in opposing else "🟡 WARNING"
                print(f"  {severity}: [{a}] and [{b}] share input → {inp}")
            print("  Consider editing conflicting actions before saving.")
        else:
            print("\n[✔] No conflicts detected — all mappings are unique!")

        # Interactive summary & review loop
        while True:
            print("\n" + "=" * 75)
            print("                  PROPOSED CONTROLLER MAPPINGS")
            print("=" * 75)
            print(f"{'ACTION KEY':<14} | {'DESCRIPTION':<30} | {'ASSIGNED INPUT(S)'}")
            print("-" * 75)
            for key, desc, hint in ACTIONS:
                m_str = format_mapping_desc(mappings.get(key, []))
                print(f"{key:<14} | {desc:<30} | {m_str}")
            print("=" * 75)

            print("\n[S] Save & Apply Mapping")
            print("[E] Edit a Specific Action")
            print("[R] Redo All Actions")
            print("[C] Re-run Conflict Check")
            print("[Q] Quit Without Saving")

            choice = input("\nSelect Option (S/E/R/C/Q): ").strip().upper()

            if choice == "S":
                save_mapping(controller_name, mappings)
                break
            elif choice == "E":
                act_key = input("Enter Action Key to edit (e.g. fly_down): ").strip().lower()
                matching = [a for a in ACTIONS if a[0] == act_key]
                if matching:
                    k, d, h = matching[0]
                    res = listen_for_input_multiple(js, screen, font, k, d, h)
                    if res:
                        mappings[k] = res
                else:
                    print("[!] Invalid Action Key.")
            elif choice == "R":
                mappings = {}
                for key, desc, hint in ACTIONS:
                    res = listen_for_input_multiple(js, screen, font, key, desc, hint)
                    if res:
                        mappings[key] = res
            elif choice == "C":
                conflicts = detect_conflicts(mappings)
                if conflicts:
                    for a, b, inp in conflicts:
                        opposing = {("fly_up", "fly_down"), ("menu_up", "menu_down"),
                                    ("move_left", "move_right"), ("menu_left", "menu_right")}
                        pair = (min(a, b), max(a, b))
                        severity = "🔴 CRITICAL" if pair in opposing else "🟡 WARNING"
                        print(f"  {severity}: [{a}] and [{b}] share input → {inp}")
                else:
                    print("[✔] No conflicts detected!")
            elif choice == "Q":
                print("\n[!] Cancelled without saving.\n")
                break

    except KeyboardInterrupt:
        print("\n\n[!] Wizard interrupted by user.")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
