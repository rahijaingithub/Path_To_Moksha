# PYGAME Version
import pygame
import math

def draw_monk(surface, x, y):
    WIDTH, HEIGHT = 80, 100
    monk_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # ── Color Palette ──────────────────────────────────────────────
    SKIN        = (210, 170, 130)
    SKIN_SHADOW = (170, 125,  90)
    SKIN_HI     = (235, 200, 160)
    BROWN       = (130,  80,  30)
    BROWN_DARK  = ( 90,  55,  15)
    TEAL        = (  0, 140, 120)
    TEAL_DARK   = (  0,  90,  80)
    EYE_COLOR   = ( 30,  20,  10)
    
    cx = WIDTH // 2   # horizontal center

    # ── 1. CROSSED LEGS (Padmasana) ────────────────────────────────
    # Wide base ellipse — the overall leg mass
    pygame.draw.ellipse(monk_surf, SKIN_SHADOW,
                        pygame.Rect(2, HEIGHT - 28, WIDTH - 4, 26))
    # Upper leg highlight — left shin arc
    pygame.draw.ellipse(monk_surf, SKIN,
                        pygame.Rect(4, HEIGHT - 26, (WIDTH // 2) - 2, 20))
    # Upper leg highlight — right shin arc
    pygame.draw.ellipse(monk_surf, SKIN,
                        pygame.Rect(cx + 2, HEIGHT - 26, (WIDTH // 2) - 4, 20))
    # Knee knobs
    pygame.draw.circle(monk_surf, SKIN_HI, (10, HEIGHT - 20), 5)
    pygame.draw.circle(monk_surf, SKIN_HI, (WIDTH - 10, HEIGHT - 20), 5)

    # ── 2. TORSO (trapezoid — wider at shoulders) ──────────────────
    torso_pts = [
        (cx - 18, 34),   # left shoulder
        (cx + 18, 34),   # right shoulder
        (cx + 13, HEIGHT - 26),  # right hip
        (cx - 13, HEIGHT - 26),  # left hip
    ]
    pygame.draw.polygon(monk_surf, SKIN, torso_pts)
    # Shadow on left side of torso
    shadow_pts = [
        (cx - 18, 34),
        (cx - 5,  34),
        (cx - 5,  HEIGHT - 26),
        (cx - 13, HEIGHT - 26),
    ]
    pygame.draw.polygon(monk_surf, SKIN_SHADOW, shadow_pts)
    # Collar-bone / chest highlight
    pygame.draw.line(monk_surf, SKIN_HI, (cx - 10, 38), (cx + 10, 38), 2)

    # ── 3. SHOULDERS (rounded caps) ───────────────────────────────
    pygame.draw.circle(monk_surf, SKIN,    (cx - 17, 36), 7)
    pygame.draw.circle(monk_surf, SKIN,    (cx + 17, 36), 7)
    pygame.draw.circle(monk_surf, SKIN_HI, (cx - 17, 34), 4)
    pygame.draw.circle(monk_surf, SKIN_HI, (cx + 17, 34), 4)

    # ── 4. ARMS (resting on knees toward lap) ─────────────────────
    # Left arm
    pygame.draw.line(monk_surf, SKIN,        (cx - 17, 40), (cx - 8, HEIGHT - 30), 6)
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx - 17, 40), (cx - 14, HEIGHT - 30), 3)
    # Right arm
    pygame.draw.line(monk_surf, SKIN,        (cx + 17, 40), (cx + 8, HEIGHT - 30), 6)
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx + 17, 40), (cx + 14, HEIGHT - 30), 3)

    # ── 5. HANDS in Dhyana mudra (resting in lap) ─────────────────
    pygame.draw.ellipse(monk_surf, SKIN,
                        pygame.Rect(cx - 13, HEIGHT - 34, 14, 9))
    pygame.draw.ellipse(monk_surf, SKIN,
                        pygame.Rect(cx -  1, HEIGHT - 34, 14, 9))

    # ── 6. NECK ───────────────────────────────────────────────────
    pygame.draw.rect(monk_surf, SKIN,
                     pygame.Rect(cx - 5, 22, 10, 14))

    # ── 7. HEAD (bald, elderly) ────────────────────────────────────
    # Main skull
    pygame.draw.circle(monk_surf, SKIN,    (cx, 14), 13)
    # Bald-head highlight (top)
    pygame.draw.circle(monk_surf, SKIN_HI, (cx - 3, 8), 6)
    # Jaw / lower-face shadow
    pygame.draw.ellipse(monk_surf, SKIN_SHADOW,
                        pygame.Rect(cx - 8, 20, 16, 8))
    # Ear nubs
    pygame.draw.circle(monk_surf, SKIN_SHADOW, (cx - 13, 15), 3)
    pygame.draw.circle(monk_surf, SKIN_SHADOW, (cx + 13, 15), 3)

    # ── 8. FACE DETAILS ───────────────────────────────────────────
    # Closed eyes (meditative lines)
    pygame.draw.arc(monk_surf, EYE_COLOR,
                    pygame.Rect(cx - 9, 12, 7, 5), 0, math.pi, 2)
    pygame.draw.arc(monk_surf, EYE_COLOR,
                    pygame.Rect(cx + 2, 12, 7, 5), 0, math.pi, 2)
    # Nose
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx, 16), (cx - 2, 20), 2)
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx, 16), (cx + 2, 20), 2)
    # Mouth (slight downward curve — serene)
    pygame.draw.arc(monk_surf, SKIN_SHADOW,
                    pygame.Rect(cx - 5, 20, 10, 5), math.pi, 2 * math.pi, 1)
    # Brow wrinkle lines
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx - 7, 11), (cx - 3, 10), 1)
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx + 3, 10), (cx + 7, 11), 1)

    # ── 9. PICCHI — Peacock Feather Whisk (left of figure) ────────
    # Wooden handle
    pygame.draw.line(monk_surf, BROWN_DARK, (10, HEIGHT - 2), (14, HEIGHT - 28), 3)
    # Fan of feather stems radiating from top of handle
    stem_origin = (14, HEIGHT - 28)
    angles = [-60, -40, -20, 0, 20, 40, 60]
    for angle_deg in angles:
        angle = math.radians(angle_deg - 90)
        ex = int(stem_origin[0] + 12 * math.cos(angle))
        ey = int(stem_origin[1] + 12 * math.sin(angle))
        pygame.draw.line(monk_surf, TEAL,      stem_origin, (ex, ey), 1)
    # Eye spots on outer feathers
    for angle_deg in [-50, 0, 50]:
        angle = math.radians(angle_deg - 90)
        ex = int(stem_origin[0] + 11 * math.cos(angle))
        ey = int(stem_origin[1] + 11 * math.sin(angle))
        pygame.draw.circle(monk_surf, TEAL_DARK, (ex, ey), 2)
        pygame.draw.circle(monk_surf, (0, 0, 180), (ex, ey), 1)

    # ── 10. KAMANDALU — Clay Water Pot (right of figure) ──────────
    pot_cx = WIDTH - 13
    # Bulbous pot body
    pygame.draw.ellipse(monk_surf, BROWN,
                        pygame.Rect(pot_cx - 8, HEIGHT - 20, 16, 18))
    # Shadow on pot
    pygame.draw.ellipse(monk_surf, BROWN_DARK,
                        pygame.Rect(pot_cx - 2, HEIGHT - 18, 8, 14))
    # Narrow neck
    pygame.draw.rect(monk_surf, BROWN,
                     pygame.Rect(pot_cx - 3, HEIGHT - 26, 6, 7))
    # Flared rim
    pygame.draw.ellipse(monk_surf, BROWN_DARK,
                        pygame.Rect(pot_cx - 5, HEIGHT - 28, 10, 4))
    # Handle arc over the neck
    pygame.draw.arc(monk_surf, BROWN_DARK,
                    pygame.Rect(pot_cx - 7, HEIGHT - 34, 14, 14),
                    0, math.pi, 2)

    surface.blit(monk_surf, (x, y))

# Cairo Version
import cairo
import math

def draw_monk(ctx, cx, cy):
    # Smooth bald head with radial gradient (light from top-left)
    head_gradient = cairo.RadialGradient(cx - 4, cy - 6, 2, cx, cy, 14)
    head_gradient.add_color_stop_rgb(0,   0.94, 0.82, 0.68)   # highlight
    head_gradient.add_color_stop_rgb(0.7, 0.82, 0.66, 0.47)   # mid skin
    head_gradient.add_color_stop_rgb(1.0, 0.62, 0.46, 0.27)   # shadow
    ctx.arc(cx, cy, 14, 0, 2 * math.pi)
    ctx.set_source(head_gradient)
    ctx.fill()

    # Closed eye as smooth bezier arc
    ctx.set_source_rgb(0.1, 0.07, 0.04)
    ctx.set_line_width(1.5)
    ctx.move_to(cx - 9, cy + 2)
    ctx.curve_to(cx - 6, cy + 5, cx - 3, cy + 5, cx, cy + 2)
    ctx.stroke()

    # Torso with linear gradient (lit from left)
    torso_grad = cairo.LinearGradient(cx - 20, 0, cx + 20, 0)
    torso_grad.add_color_stop_rgb(0,   0.94, 0.82, 0.68)
    torso_grad.add_color_stop_rgb(0.4, 0.82, 0.66, 0.47)
    torso_grad.add_color_stop_rgb(1.0, 0.58, 0.40, 0.22)
    ctx.move_to(cx - 20, cy + 20)
    ctx.curve_to(cx - 22, cy + 55, cx + 22, cy + 55, cx + 20, cy + 20)
    ctx.line_to(cx + 20, cy + 20)
    ctx.set_source(torso_grad)
    ctx.fill()

# Skia Version
# pyrefly: ignore [missing-import]
import skia

def draw_monk(canvas):
    # Skin gradient paint
    paint = skia.Paint()
    paint.setShader(
        skia.GradientShader.MakeRadial(
            center=(-4, -6), radius=14,
            colors=[0xFFF0D0A8, 0xFFD4A878, 0xFFAA7040],
        )
    )
    # Anti-aliased head
    paint.setAntiAlias(True)
    canvas.drawCircle(0, 0, 14, paint)

    # Bezier path for organic body shape
    path = skia.Path()
    path.moveTo(-20, 20)
    path.cubicTo(-25, 60, 25, 60, 20, 20)
    path.close()
    canvas.drawPath(path, paint)

# ── Standalone test ────────────────────────────────────────────────
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((200, 200))
    pygame.display.set_caption("Digambara Monk")
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((0, 180, 0))          # green-screen style bg
        draw_monk(screen, 60, 50)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()