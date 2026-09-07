"""
detect_controller.py — Standalone tool to inspect controller inputs for Path to Moksha.

Run this script directly in terminal:
    python detect_controller.py
"""
import sys
import time
import pygame

def main():
    print("=" * 65)
    print("      PATH TO MOKSHA — CONTROLLER DETECTION & INSPECTOR TOOL")
    print("=" * 65)
    
    # Initialize Pygame and Joystick subsystems
    pygame.init()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    if count == 0:
        print("\n[!] No controller detected on this computer.")
        print("    Please connect a controller (USB or Bluetooth) and run again.\n")
        return

    print(f"\n[✔] Found {count} controller(s):")
    for i in range(count):
        js = pygame.joystick.Joystick(i)
        js.init()
        print(f"    [{i}] {js.get_name()} (Buttons: {js.get_numbuttons()}, Axes: {js.get_numaxes()}, Hats: {js.get_numhats()})")

    # Select controller if multiple
    selected_idx = 0
    if count > 1:
        try:
            choice = input(f"\nSelect controller index (0-{count-1}) [Default 0]: ").strip()
            if choice.isdigit() and 0 <= int(choice) < count:
                selected_idx = int(choice)
        except Exception:
            selected_idx = 0

    js = pygame.joystick.Joystick(selected_idx)
    js.init()

    print("\n" + "=" * 65)
    print(f"   ACTIVE CONTROLLER: {js.get_name()}")
    print("=" * 65)
    print(f"   • Total Buttons : {js.get_numbuttons()}")
    print(f"   • Total Axes    : {js.get_numaxes()}")
    print(f"   • Total Hats    : {js.get_numhats()}")
    print("-" * 65)
    print("   Press physical buttons, move sticks, or press D-pad.")
    print("   Press Ctrl+C in terminal or close window to exit.")
    print("=" * 65 + "\n")

    # Need a small dummy Pygame display to catch OS events reliably on Windows
    screen = pygame.display.set_mode((400, 150))
    pygame.display.set_caption("Controller Inspector — Press buttons to test")
    font = pygame.font.SysFont("Arial", 16)

    clock = pygame.time.Clock()
    running = True
    last_event_str = "Waiting for input..."

    try:
        while running:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                elif event.type == pygame.JOYBUTTONDOWN:
                    msg = f"  [BUTTON PRESS]   Button ID: {event.button}"
                    print(msg)
                    last_event_str = msg

                elif event.type == pygame.JOYBUTTONUP:
                    msg = f"  [BUTTON RELEASE] Button ID: {event.button}"
                    print(msg)

                elif event.type == pygame.JOYAXISMOTION:
                    # Apply deadzone filter to avoid terminal spam from minor analog float
                    if abs(event.value) > 0.35:
                        direction = "Positive (+)" if event.value > 0 else "Negative (-)"
                        msg = f"  [AXIS MOVE]      Axis ID: {event.axis} | Value: {event.value:.2f} ({direction})"
                        print(msg)
                        last_event_str = msg

                elif event.type == pygame.JOYHATMOTION:
                    if event.value != (0, 0):
                        msg = f"  [HAT / D-PAD]    Hat ID: {event.hat} | Value: {event.value}"
                        print(msg)
                        last_event_str = msg

            # Render lightweight info in dummy window
            screen.fill((20, 24, 35))
            txt1 = font.render(f"Controller: {js.get_name()}", True, (255, 215, 0))
            txt2 = font.render(f"Last Event: {last_event_str[:45]}", True, (200, 220, 255))
            txt3 = font.render("Close window or press Ctrl+C to quit", True, (150, 150, 150))
            screen.blit(txt1, (15, 20))
            screen.blit(txt2, (15, 55))
            screen.blit(txt3, (15, 100))
            pygame.display.flip()

    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
        print("\n" + "=" * 65)
        print("  [✔] Inspection complete.")
        print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
