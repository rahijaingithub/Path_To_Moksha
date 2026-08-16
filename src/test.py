# Standalone comparison test to compare pygame, skia and cairo monk design capability
import pygame
import math
import sys

# ── Dynamic imports with graceful fallbacks ──
try:
    import cairo
    CAIRO_AVAILABLE = True
except ImportError:
    CAIRO_AVAILABLE = False

try:
    import skia
    SKIA_AVAILABLE = True
except ImportError:
    SKIA_AVAILABLE = False


# ── Color Palette Constants ──
COLOR_BG_DARK = (15, 12, 22)
COLOR_CARD = (25, 20, 35)
COLOR_GOLD = (218, 165, 32)
COLOR_GOLD_BRIGHT = (255, 215, 0)
COLOR_WHITE = (240, 240, 240)
COLOR_GREEN = (40, 180, 120)
COLOR_RED = (220, 80, 80)
COLOR_SAFFRON = (245, 130, 48)


# ──────────────────────────────────────────────────────────────────────────────
# 1. PYGAME IMPLEMENTATION (Standard raster shapes)
# ──────────────────────────────────────────────────────────────────────────────
def draw_monk_pygame(surface, x, y):
    WIDTH, HEIGHT = 80, 100
    monk_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    SKIN        = (210, 170, 130)
    SKIN_SHADOW = (170, 125,  90)
    SKIN_HI     = (235, 200, 160)
    BROWN       = (130,  80,  30)
    BROWN_DARK  = ( 90,  55,  15)
    TEAL        = (  0, 140, 120)
    TEAL_DARK   = (  0,  90,  80)
    EYE_COLOR   = ( 30,  20,  10)
    
    cx = WIDTH // 2

    # Crossed legs
    pygame.draw.ellipse(monk_surf, SKIN_SHADOW, pygame.Rect(2, HEIGHT - 28, WIDTH - 4, 26))
    pygame.draw.ellipse(monk_surf, SKIN, pygame.Rect(4, HEIGHT - 26, (WIDTH // 2) - 2, 20))
    pygame.draw.ellipse(monk_surf, SKIN, pygame.Rect(cx + 2, HEIGHT - 26, (WIDTH // 2) - 4, 20))
    pygame.draw.circle(monk_surf, SKIN_HI, (10, HEIGHT - 20), 5)
    pygame.draw.circle(monk_surf, SKIN_HI, (WIDTH - 10, HEIGHT - 20), 5)

    # Torso
    torso_pts = [
        (cx - 18, 34),
        (cx + 18, 34),
        (cx + 13, HEIGHT - 26),
        (cx - 13, HEIGHT - 26),
    ]
    pygame.draw.polygon(monk_surf, SKIN, torso_pts)
    shadow_pts = [
        (cx - 18, 34),
        (cx - 5,  34),
        (cx - 5,  HEIGHT - 26),
        (cx - 13, HEIGHT - 26),
    ]
    pygame.draw.polygon(monk_surf, SKIN_SHADOW, shadow_pts)
    pygame.draw.line(monk_surf, SKIN_HI, (cx - 10, 38), (cx + 10, 38), 2)

    # Shoulders
    pygame.draw.circle(monk_surf, SKIN, (cx - 17, 36), 7)
    pygame.draw.circle(monk_surf, SKIN, (cx + 17, 36), 7)

    # Arms
    pygame.draw.line(monk_surf, SKIN, (cx - 17, 40), (cx - 8, HEIGHT - 30), 6)
    pygame.draw.line(monk_surf, SKIN, (cx + 17, 40), (cx + 8, HEIGHT - 30), 6)

    # Hands
    pygame.draw.ellipse(monk_surf, SKIN, pygame.Rect(cx - 13, HEIGHT - 34, 14, 9))
    pygame.draw.ellipse(monk_surf, SKIN, pygame.Rect(cx - 1, HEIGHT - 34, 14, 9))

    # Neck
    pygame.draw.rect(monk_surf, SKIN, pygame.Rect(cx - 5, 22, 10, 14))

    # Head
    pygame.draw.circle(monk_surf, SKIN, (cx, 14), 13)
    pygame.draw.circle(monk_surf, SKIN_HI, (cx - 3, 8), 6)
    pygame.draw.ellipse(monk_surf, SKIN_SHADOW, pygame.Rect(cx - 8, 20, 16, 8))
    pygame.draw.circle(monk_surf, SKIN_SHADOW, (cx - 13, 15), 3)
    pygame.draw.circle(monk_surf, SKIN_SHADOW, (cx + 13, 15), 3)

    # Face details
    pygame.draw.arc(monk_surf, EYE_COLOR, pygame.Rect(cx - 9, 12, 7, 5), 0, math.pi, 2)
    pygame.draw.arc(monk_surf, EYE_COLOR, pygame.Rect(cx + 2, 12, 7, 5), 0, math.pi, 2)
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx, 16), (cx - 2, 20), 2)
    pygame.draw.line(monk_surf, SKIN_SHADOW, (cx, 16), (cx + 2, 20), 2)

    # Picchi (Peacock whisk) - rests on ground feathers first, handle pointing up
    pygame.draw.line(monk_surf, BROWN_DARK, (10, 36), (14, 10), 3)  # Handle pointing up
    # Radiating feather stems from top of bottom feathers mass
    stem_origin = (10, 36)
    angles = [-60, -40, -20, 0, 20, 40, 60]
    for angle_deg in angles:
        angle = math.radians(angle_deg + 90)  # feathers pointing down
        ex = int(stem_origin[0] + 12 * math.cos(angle))
        ey = int(stem_origin[1] + 12 * math.sin(angle))
        pygame.draw.line(monk_surf, TEAL, stem_origin, (ex, ey), 1)

    # Kamandalu
    pot_cx = WIDTH - 13
    pygame.draw.ellipse(monk_surf, BROWN, pygame.Rect(pot_cx - 8, HEIGHT - 20, 16, 18))
    pygame.draw.rect(monk_surf, BROWN, pygame.Rect(pot_cx - 3, HEIGHT - 26, 6, 7))
    pygame.draw.arc(monk_surf, BROWN_DARK, pygame.Rect(pot_cx - 7, HEIGHT - 34, 14, 14), 0, math.pi, 2)

    surface.blit(monk_surf, (x, y))


# ──────────────────────────────────────────────────────────────────────────────
# 2. CAIRO IMPLEMENTATION (Hardware vector anti-aliased rendering)
# ──────────────────────────────────────────────────────────────────────────────
def draw_monk_cairo(ctx, cx, cy):
    # Enable anti-aliasing
    ctx.set_antialias(cairo.ANTIALIAS_BEST)

    # Smooth bald head with radial gradient (light from top-left)
    head_gradient = cairo.RadialGradient(cx - 4, cy - 6, 2, cx, cy, 14)
    head_gradient.add_color_stop_rgb(0,   0.94, 0.82, 0.68)
    head_gradient.add_color_stop_rgb(0.7, 0.82, 0.66, 0.47)
    head_gradient.add_color_stop_rgb(1.0, 0.62, 0.46, 0.27)
    ctx.arc(cx, cy, 14, 0, 2 * math.pi)
    ctx.set_source(head_gradient)
    ctx.fill()

    # Closed eye as smooth bezier arc
    ctx.set_source_rgb(0.1, 0.07, 0.04)
    ctx.set_line_width(1.5)
    ctx.move_to(cx - 9, cy + 2)
    ctx.curve_to(cx - 6, cy + 5, cx - 3, cy + 5, cx, cy + 2)
    ctx.stroke()

    ctx.move_to(cx + 2, cy + 2)
    ctx.curve_to(cx + 5, cy + 5, cx + 8, cy + 5, cx + 11, cy + 2)
    ctx.stroke()

    # Torso with linear gradient (lit from left)
    torso_grad = cairo.LinearGradient(cx - 20, cy + 20, cx + 20, cy + 60)
    torso_grad.add_color_stop_rgb(0,   0.94, 0.82, 0.68)
    torso_grad.add_color_stop_rgb(0.4, 0.82, 0.66, 0.47)
    torso_grad.add_color_stop_rgb(1.0, 0.58, 0.40, 0.22)
    
    ctx.move_to(cx - 18, cy + 34)
    ctx.line_to(cx + 18, cy + 34)
    ctx.line_to(cx + 13, cy + 74)
    ctx.line_to(cx - 13, cy + 74)
    ctx.close_path()
    ctx.set_source(torso_grad)
    ctx.fill()


# ──────────────────────────────────────────────────────────────────────────────
# 3. SKIA IMPLEMENTATION (High-fidelity Bezier curves based on Reference Image)
# ──────────────────────────────────────────────────────────────────────────────
def draw_monk_skia(canvas, cx, cy):
    # Save the canvas state and translate to draw at top-left relative to head center
    canvas.save()
    canvas.translate(cx - 40, cy - 14)

    # --- Paints / Styles ---
    # Colors extracted directly from the reference image for maximum fidelity
    C_SKIN_BASE = 0xFFC08A60   # Mid warm brown
    C_SKIN_HI = 0xFFE6BA95     # Light warm tan
    C_SKIN_SHADOW = 0xFF6A4025 # Dark brown
    C_SKIN_DEEP = 0xFF3A2010   # Very dark brown for crevices
    
    C_WOOD_LIGHT = 0xFFCBA37A
    C_WOOD_DARK = 0xFF7A4A28
    C_POT_BASE = 0xFF9E5C32
    C_POT_SHADOW = 0xFF4A2610
    C_FEATHER_GREEN = 0xFF2E5E35
    C_FEATHER_DARK = 0xFF14301B
    C_EYE_BLUE = 0xFF2A6E9B
    C_EYE_YELLOW = 0xFFC9A844

    def fill_paint(color_val):
        p = skia.Paint()
        p.setAntiAlias(True)
        p.setStyle(skia.Paint.kFill_Style)
        p.setColor(color_val)
        return p

    def stroke_paint(color_val, width):
        p = skia.Paint()
        p.setAntiAlias(True)
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setColor(color_val)
        return p

    def gradient_paint(pts, colors):
        p = skia.Paint()
        p.setAntiAlias(True)
        p.setStyle(skia.Paint.kFill_Style)
        p.setShader(skia.GradientShader.MakeLinear(pts, colors))
        return p

    # 1. Background shadow (under the monk)
    canvas.drawOval(skia.Rect.MakeXYWH(5, 80, 70, 15), fill_paint(0x60000000))

    # 2. Torso and Body Base (Organic musculature)
    body = skia.Path()
    body.moveTo(40, 30) # Neck base
    body.cubicTo(60, 30, 65, 45, 55, 75) # Right shoulder to waist
    body.cubicTo(75, 80, 70, 95, 40, 95) # Right leg
    body.cubicTo(10, 95, 5, 80, 25, 75) # Left leg
    body.cubicTo(15, 45, 20, 30, 40, 30) # Left waist to shoulder
    body.close()
    
    body_paint = gradient_paint(
        [skia.Point(20, 30), skia.Point(60, 95)],
        [C_SKIN_HI, C_SKIN_BASE, C_SKIN_SHADOW]
    )
    canvas.drawPath(body, body_paint)

    # 3. Chest Musculature (Pectorals)
    chest = skia.Path()
    chest.moveTo(40, 45) # Center chest
    chest.cubicTo(30, 45, 25, 40, 25, 35) # Left pec bottom
    chest.moveTo(40, 45)
    chest.cubicTo(50, 45, 55, 40, 55, 35) # Right pec bottom
    canvas.drawPath(chest, stroke_paint(C_SKIN_DEEP, 1.5))
    
    # 4. Belly / Navel
    canvas.drawArc(skia.Rect.MakeXYWH(30, 65, 20, 10), 0, 180, False, stroke_paint(C_SKIN_DEEP, 1.0)) # Belly fold
    canvas.drawCircle(40, 72, 1.5, fill_paint(C_SKIN_DEEP)) # Navel

    # 5. Arms
    # Left Arm
    l_arm = skia.Path()
    l_arm.moveTo(25, 35) # Shoulder
    l_arm.cubicTo(18, 50, 20, 65, 35, 80) # Upper arm to hand
    canvas.drawPath(l_arm, stroke_paint(C_SKIN_DEEP, 4.0)) # Shadow
    
    l_arm_fill = gradient_paint([skia.Point(20, 35), skia.Point(30, 80)], [C_SKIN_HI, C_SKIN_BASE])
    l_arm_path = skia.Path()
    l_arm_path.moveTo(25, 35)
    l_arm_path.cubicTo(15, 50, 18, 70, 35, 82)
    l_arm_path.lineTo(38, 78)
    l_arm_path.cubicTo(22, 65, 22, 45, 30, 38)
    l_arm_path.close()
    canvas.drawPath(l_arm_path, l_arm_fill)

    # Right Arm
    r_arm = skia.Path()
    r_arm.moveTo(55, 35)
    r_arm.cubicTo(62, 50, 60, 65, 45, 80)
    canvas.drawPath(r_arm, stroke_paint(C_SKIN_DEEP, 4.0)) # Shadow
    
    r_arm_fill = gradient_paint([skia.Point(60, 35), skia.Point(50, 80)], [C_SKIN_BASE, C_SKIN_SHADOW])
    r_arm_path = skia.Path()
    r_arm_path.moveTo(55, 35)
    r_arm_path.cubicTo(65, 50, 62, 70, 45, 82)
    r_arm_path.lineTo(42, 78)
    r_arm_path.cubicTo(58, 65, 58, 45, 50, 38)
    r_arm_path.close()
    canvas.drawPath(r_arm_path, r_arm_fill)

    # Hands (Clasped in lap)
    hands = skia.Path()
    hands.moveTo(35, 80)
    hands.cubicTo(40, 85, 45, 80, 45, 80)
    canvas.drawPath(hands, stroke_paint(C_SKIN_DEEP, 1.5))
    canvas.drawOval(skia.Rect.MakeXYWH(35, 78, 10, 5), fill_paint(C_SKIN_BASE))

    # 6. Legs detailed lines (Crossing)
    canvas.drawLine(20, 85, 40, 92, stroke_paint(C_SKIN_DEEP, 1.5))
    canvas.drawLine(60, 85, 40, 92, stroke_paint(C_SKIN_DEEP, 1.5))
    # Feet
    canvas.drawOval(skia.Rect.MakeXYWH(25, 85, 8, 5), fill_paint(C_SKIN_HI)) # Left foot sole
    canvas.drawOval(skia.Rect.MakeXYWH(47, 85, 8, 5), fill_paint(C_SKIN_SHADOW)) # Right foot sole

    # 7. Head & Neck
    canvas.drawRect(skia.Rect.MakeXYWH(36, 25, 8, 10), fill_paint(C_SKIN_SHADOW)) # Neck
    
    # Cranium (more oval, detailed shading)
    head_paint = skia.Paint()
    head_paint.setAntiAlias(True)
    head_paint.setStyle(skia.Paint.kFill_Style)
    head_paint.setShader(skia.GradientShader.MakeRadial(
        skia.Point(36, 10), 15,
        [C_SKIN_HI, C_SKIN_BASE, C_SKIN_DEEP]
    ))
    
    head = skia.Path()
    head.moveTo(40, 2) # Top
    head.cubicTo(50, 2, 52, 12, 48, 22) # Right side to jaw
    head.lineTo(43, 28) # Chin
    head.lineTo(37, 28) # Chin left
    head.lineTo(32, 22) # Left jaw
    head.cubicTo(28, 12, 30, 2, 40, 2) # Left side to top
    head.close()
    canvas.drawPath(head, head_paint)

    # Ears
    canvas.drawOval(skia.Rect.MakeXYWH(30, 12, 3, 6), fill_paint(C_SKIN_SHADOW))
    canvas.drawOval(skia.Rect.MakeXYWH(47, 12, 3, 6), fill_paint(C_SKIN_SHADOW))

    # Face details
    # Closed Eyes (downward curves)
    canvas.drawArc(skia.Rect.MakeXYWH(33, 14, 5, 3), 0, 180, False, stroke_paint(C_SKIN_DEEP, 1.0))
    canvas.drawArc(skia.Rect.MakeXYWH(42, 14, 5, 3), 0, 180, False, stroke_paint(C_SKIN_DEEP, 1.0))
    # Nose
    canvas.drawLine(40, 15, 39, 21, stroke_paint(C_SKIN_DEEP, 1.0))
    canvas.drawLine(39, 21, 41, 21, stroke_paint(C_SKIN_DEEP, 1.0)) # Nostrils
    # Mouth
    canvas.drawLine(38, 24, 42, 24, stroke_paint(C_SKIN_DEEP, 1.0))
    # Cheekbones
    canvas.drawArc(skia.Rect.MakeXYWH(33, 18, 4, 4), 90, 90, False, stroke_paint(C_SKIN_SHADOW, 0.5))
    canvas.drawArc(skia.Rect.MakeXYWH(43, 18, 4, 4), 0, 90, False, stroke_paint(C_SKIN_SHADOW, 0.5))

    # 8. Picchi (Peacock whisk)
    canvas.save()
    canvas.translate(15, 90)
    canvas.rotate(25) # Tilt it
    
    # Feathers mass
    feather_mass = skia.Path()
    feather_mass.moveTo(0, 0)
    feather_mass.cubicTo(-10, -10, -20, -5, -25, 0)
    feather_mass.cubicTo(-20, 10, -10, 10, 0, 0)
    canvas.drawPath(feather_mass, fill_paint(C_FEATHER_DARK))
    
    # Feather strands
    for i in range(-20, 0, 3):
        canvas.drawLine(0, 0, i, -8 + (i % 3), stroke_paint(C_FEATHER_GREEN, 1.0))
        canvas.drawLine(0, 0, i, 8 - (i % 3), stroke_paint(C_FEATHER_GREEN, 1.0))
        
    # 'Eye' spots
    canvas.drawCircle(-15, -2, 2, fill_paint(C_EYE_YELLOW))
    canvas.drawCircle(-15, -2, 1, fill_paint(C_EYE_BLUE))
    canvas.drawCircle(-10, 3, 1.5, fill_paint(C_EYE_YELLOW))
    canvas.drawCircle(-10, 3, 0.8, fill_paint(C_EYE_BLUE))

    # Handle
    canvas.drawLine(0, 0, 15, 0, stroke_paint(C_WOOD_LIGHT, 2.0))
    canvas.drawLine(0, 1, 15, 1, stroke_paint(C_WOOD_DARK, 1.0))
    canvas.restore()

    # 9. Kamandalu (Water Pot)
    canvas.save()
    canvas.translate(65, 80)
    
    # Pot Body
    pot_paint = skia.Paint()
    pot_paint.setAntiAlias(True)
    pot_paint.setStyle(skia.Paint.kFill_Style)
    pot_paint.setShader(skia.GradientShader.MakeRadial(
        skia.Point(-3, -3), 10,
        [C_WOOD_LIGHT, C_POT_BASE, C_POT_SHADOW]
    ))
    canvas.drawOval(skia.Rect.MakeXYWH(-8, -5, 16, 16), pot_paint)
    
    # Neck and Rim
    canvas.drawRect(skia.Rect.MakeXYWH(-4, -10, 8, 6), fill_paint(C_POT_BASE))
    canvas.drawOval(skia.Rect.MakeXYWH(-6, -12, 12, 4), fill_paint(C_WOOD_DARK))
    
    # Loop Handle
    handle_path = skia.Path()
    handle_path.moveTo(-4, -10)
    handle_path.cubicTo(-6, -25, 6, -25, 4, -10)
    canvas.drawPath(handle_path, stroke_paint(C_WOOD_LIGHT, 2.0))
    
    canvas.restore()

    # Restore the canvas state
    canvas.restore()


# ──────────────────────────────────────────────────────────────────────────────
# Standalone comparison test runner
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    
    # 800x450 window for generous side-by-side presentation
    screen = pygame.display.set_mode((840, 480))
    pygame.display.set_caption("Spiritual Monk Design Capability Comparison")
    
    # Load fonts
    try:
        font_title = pygame.font.SysFont("arial", 20, bold=True)
        font_body = pygame.font.SysFont("arial", 14)
        font_code = pygame.font.SysFont("courier", 13, bold=True)
    except:
        font_title = pygame.font.Font(None, 24)
        font_body = pygame.font.Font(None, 18)
        font_code = pygame.font.Font(None, 16)

    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Clear screen with dark premium base color
        screen.fill(COLOR_BG_DARK)
        
        # --- TITLE BANNER ---
        banner = font_title.render("Monk Render Engines Design Comparison", True, COLOR_GOLD_BRIGHT)
        screen.blit(banner, (420 - banner.get_width() // 2, 20))
        
        desc = font_body.render("Comparing drawing vector antialiasing, curves, and color gradients side-by-side", True, COLOR_WHITE)
        screen.blit(desc, (420 - desc.get_width() // 2, 48))

        # Panel coordinates
        panel_w, panel_h = 240, 320
        panel_y = 90
        
        # ──────────────────────────────────────────────────────────────────────
        # PANEL 1: PYGAME
        # ──────────────────────────────────────────────────────────────────────
        px1 = 30
        pygame.draw.rect(screen, COLOR_CARD, (px1, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(screen, COLOR_GOLD, (px1, panel_y, panel_w, panel_h), width=2, border_radius=12)
        
        p1_title = font_title.render("Pygame Render", True, COLOR_SAFFRON)
        screen.blit(p1_title, (px1 + panel_w // 2 - p1_title.get_width() // 2, panel_y + 15))
        
        # Draw Monk
        draw_monk_pygame(screen, px1 + panel_w // 2 - 40, panel_y + 90)
        
        features_pygame = [
            "• Pure Pygame rendering",
            "• Built-in pixel canvas",
            "• Performance: Ultra High",
            "• AA Quality: None (pixelated)",
            "• Gradient support: Hand-coded",
            "• Status: ACTIVE & COMPATIBLE"
        ]
        for idx, feat in enumerate(features_pygame):
            f_color = COLOR_GREEN if "Status:" in feat else COLOR_WHITE
            text = font_body.render(feat, True, f_color)
            screen.blit(text, (px1 + 20, panel_y + 200 + idx * 18))

        # ──────────────────────────────────────────────────────────────────────
        # PANEL 2: CAIRO
        # ──────────────────────────────────────────────────────────────────────
        px2 = 300
        pygame.draw.rect(screen, COLOR_CARD, (px2, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(screen, COLOR_GOLD, (px2, panel_y, panel_w, panel_h), width=2, border_radius=12)
        
        p2_title = font_title.render("Cairo Vector", True, COLOR_SAFFRON)
        screen.blit(p2_title, (px2 + panel_w // 2 - p2_title.get_width() // 2, panel_y + 15))
        
        if CAIRO_AVAILABLE:
            # Create a Pycairo surface, draw, and extract buffer
            c_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 120)
            ctx = cairo.Context(c_surf)
            # Fill transparent
            ctx.set_source_rgba(0, 0, 0, 0)
            ctx.set_operator(cairo.OPERATOR_SOURCE)
            ctx.paint()
            ctx.set_operator(cairo.OPERATOR_OVER)
            
            # Render
            draw_monk_cairo(ctx, 50, 30)
            
            # Blit onto pygame
            buf = c_surf.get_data()
            pygame_cairo_surf = pygame.image.frombuffer(buf, (100, 120), "ARGB")
            screen.blit(pygame_cairo_surf, (px2 + panel_w // 2 - 50, panel_y + 80))
            
            status_text = "• Status: LOADED SUCCESSFULLY"
            status_color = COLOR_GREEN
        else:
            # Drawing a simulated beautiful vector design using high-res drawing fallback as comparison representation
            pygame.draw.circle(screen, (235, 200, 160), (px2 + panel_w // 2, panel_y + 110), 14)
            pygame.draw.rect(screen, (210, 170, 130), (px2 + panel_w // 2 - 18, panel_y + 130, 36, 40), border_radius=4)
            
            warn1 = font_body.render("Module missing:", True, COLOR_RED)
            warn2 = font_code.render("pip install pycairo", True, COLOR_GOLD_BRIGHT)
            screen.blit(warn1, (px2 + panel_w // 2 - warn1.get_width() // 2, panel_y + 90))
            screen.blit(warn2, (px2 + panel_w // 2 - warn2.get_width() // 2, panel_y + 115))
            
            status_text = "• Status: MODULE MISSING"
            status_color = COLOR_RED

        features_cairo = [
            "• Hardware vector pipelines",
            "• Perfect subpixel curve AA",
            "• Performance: Good",
            "• AA Quality: Excellent (Smooth)",
            "• Gradient support: Linear/Radial",
            status_text
        ]
        for idx, feat in enumerate(features_cairo):
            f_color = status_color if "Status:" in feat else COLOR_WHITE
            text = font_body.render(feat, True, f_color)
            screen.blit(text, (px2 + 20, panel_y + 200 + idx * 18))

        # ──────────────────────────────────────────────────────────────────────
        # PANEL 3: SKIA
        # ──────────────────────────────────────────────────────────────────────
        px3 = 570
        pygame.draw.rect(screen, COLOR_CARD, (px3, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(screen, COLOR_GOLD, (px3, panel_y, panel_w, panel_h), width=2, border_radius=12)
        
        p3_title = font_title.render("Skia Bezier", True, COLOR_SAFFRON)
        screen.blit(p3_title, (px3 + panel_w // 2 - p3_title.get_width() // 2, panel_y + 15))
        
        if SKIA_AVAILABLE:
            # Create Skia surface
            info = skia.ImageInfo.MakeN32Premul(100, 120)
            s_surf = skia.Surface.MakeRaster(info)
            canvas = s_surf.getCanvas()
            canvas.clear(skia.ColorTRANSPARENT)
            
            # Render
            draw_monk_skia(canvas, 50, 30)
            
            # Blit
            image = s_surf.makeImageSnapshot()
            rgba_bytes = image.tobytes()
            pygame_skia_surf = pygame.image.frombuffer(rgba_bytes, (100, 120), "BGRA")
            screen.blit(pygame_skia_surf, (px3 + panel_w // 2 - 50, panel_y + 80))
            
            status_text = "• Status: LOADED SUCCESSFULLY"
            status_color = COLOR_GREEN
        else:
            # Drawing a simulated beautiful vector design using high-res drawing fallback as comparison representation
            pygame.draw.circle(screen, (235, 200, 160), (px3 + panel_w // 2, panel_y + 110), 14)
            pygame.draw.rect(screen, (210, 170, 130), (px3 + panel_w // 2 - 18, panel_y + 130, 36, 40), border_radius=4)
            
            warn1 = font_body.render("Module missing:", True, COLOR_RED)
            warn2 = font_code.render("pip install skia-python", True, COLOR_GOLD_BRIGHT)
            screen.blit(warn1, (px3 + panel_w // 2 - warn1.get_width() // 2, panel_y + 90))
            screen.blit(warn2, (px3 + panel_w // 2 - warn2.get_width() // 2, panel_y + 115))
            
            status_text = "• Status: MODULE MISSING"
            status_color = COLOR_RED

        features_skia = [
            "• Chrome graphics engine",
            "• GPU Accelerated vectors",
            "• Performance: Extreme",
            "• AA Quality: Outstanding",
            "• Gradient support: Full shaders",
            status_text
        ]
        for idx, feat in enumerate(features_skia):
            f_color = status_color if "Status:" in feat else COLOR_WHITE
            text = font_body.render(feat, True, f_color)
            screen.blit(text, (px3 + 20, panel_y + 200 + idx * 18))

        # --- FOOTER ---
        footer = font_body.render("Note: Cairo and Skia require external native DLL bindings. Pygame remains 100% portable.", True, COLOR_GOLD)
        screen.blit(footer, (420 - footer.get_width() // 2, 430))
        
        pygame.display.flip()
        clock.tick(30)
        
    pygame.quit()
    sys.exit()