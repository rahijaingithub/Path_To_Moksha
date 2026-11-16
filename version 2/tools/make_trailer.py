"""
make_trailer.py — Cut the gameplay trailer from two autoplay recordings.

    venv\\Scripts\\python.exe tools\\autoplay.py --game --out recordings\\game_boy.mp4
    venv\\Scripts\\python.exe tools\\autoplay.py --game --character girl --seed 7 --out recordings\\game_girl.mp4
    venv\\Scripts\\python.exe tools\\make_trailer.py

It writes, into recordings\\ (git-ignored):

    trailer_tall.mp4            1080x1920, for WhatsApp and phones, with the date
    trailer_tall_whatsapp.mp4   the same, smaller, to send
    trailer_wide.mp4            1920x1080, for YouTube, with the date
    trailer_tall_undated.mp4, trailer_wide_undated.mp4   to use after the day

The plan (designer, 2026-11-15): one trailer for kids and parents, built on four
words in this order — Adventure, Fun, Gyan, Dharam — so it opens on what draws a
child and closes on what a parent is looking for, then the invitation.

The cut list below is in seconds of the recordings, which autoplay makes the same
every time for a given seed (boy: 3, girl: 7). If the game changes so that a run
plays out differently, the beat times autoplay prints say where each moment went.

The tall cut does not shrink the screen into a strip: it crops a window that
follows the devotee, using the .track.csv autoplay writes beside each video.
Needs ffmpeg on PATH and pygame (for the lettering).
"""
import argparse
import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
SRC_W, SRC_H = 1920, 1080

# The words on the last card. The date is the Jain Tithi Darpan's (Songadh) for
# Paush Krishna 2; check it against JSOT's own calendar before publishing.
TITLE = "The Path to Moksha"
PRESENTS = "DIGAMBER PAATHSHALA PRESENTS"
OCCASION = "Mallinath Bhagwan Gyan Kalyanak"
DATE = "25 December 2026"
PLACE = "JSOT Digamber Paathshala"
INVITATION = "Kids and parents, come and play!"
PILLARS = ("ADVENTURE", "FUN", "GYAN", "DHARAM")

# (section, line under it, whose run, start, seconds, where the tall window looks)
# "follow" tracks the devotee; "centre" holds the middle of the screen.
CUTS = [
    (None, None, "boy", 0.8, 3.2, "centre"),                       # the title screen
    (None, "Choose your pilgrim", "girl", 12.5, 2.2, "centre"),
    ("ADVENTURE", "The Commute", "boy", 16.5, 2.4, "follow"),
    ("ADVENTURE", "The Cave", "girl", 74.0, 2.4, "follow"),
    ("ADVENTURE", "The Hall", "boy", 161.5, 2.4, "follow"),
    ("ADVENTURE", "The Summit", "girl", 236.5, 2.4, "follow"),
    ("FUN", "Leap across the rooftops", "boy", 28.0, 2.6, "follow"),
    ("FUN", "Fly!", "boy", 110.8, 3.0, "follow"),
    ("FUN", "Hop across the lotus lake", "girl", 157.6, 2.3, "follow"),
    ("FUN", "Mind the snow on Kailash", "boy", 244.0, 2.6, "follow"),
    ("GYAN", "Answer the Monk", "boy", 33.0, 3.4, "centre"),
    ("GYAN", "Knowledge lights the way", "boy", 38.0, 2.2, "follow"),
    ("GYAN", "Learn the Namokar Mantra", "boy", 170.0, 3.6, "centre"),
    ("DHARAM", "Save a fallen bird", "boy", 163.3, 1.9, "follow"),
    ("DHARAM", "Help those in need", "boy", 190.6, 3.0, "follow"),
    ("DHARAM", "Offer the Akshat", "boy", 219.0, 2.8, "follow"),
    ("DHARAM", "Bow to Bhagwan", "boy", 124.0, 2.6, "centre"),
    ("DHARAM", "Climb to the summit", "boy", 277.4, 2.0, "follow"),
    (None, "Complete the pilgrimage", "boy", 294.5, 2.6, "centre"),
]
END_CARD_SECONDS = 6.5

# Tall layout: a band of lettering, the game, a band of lettering.
TALL = (1080, 1920)
TALL_GAME = (1080, 1350)             # the game's place on the tall screen
TALL_GAME_Y = 300
# What is cropped from the recording to fill it. A screen held on its centre (a
# question, the mantra) is taken full height. A window that follows the devotee
# leaves out the HUD bars top and bottom, which a moving crop would cut mid-word.
WINDOWS = {"centre": (864, 1080, 0), "follow": (760, 950, 49)}      # width, height, top

INK = (11, 9, 24)
INDIGO = (26, 20, 52)
GOLD = (236, 190, 92)
GOLD_DIM = (150, 120, 60)
CREAM = (245, 236, 214)
FONTS = r"C:\Windows\Fonts"


def run(args):
    result = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args])
    if result.returncode:
        raise SystemExit(f"ffmpeg failed: {' '.join(args)[:300]}")


# ── lettering (pygame) ───────────────────────────────────────────────────────

def lettering():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    pygame.init()
    pygame.display.set_mode((16, 16))

    def font(name, size):
        path = os.path.join(FONTS, name)
        return pygame.font.Font(path if os.path.exists(path) else None, size)

    def text(surface, words, name, size, color, centre, shadow=True, spacing=0):
        f = font(name, size)
        if spacing:
            glyphs = [f.render(ch, True, color) for ch in words]
            width = sum(g.get_width() for g in glyphs) + spacing * (len(glyphs) - 1)
            img = pygame.Surface((width, f.get_height()), pygame.SRCALPHA)
            x = 0
            for g in glyphs:
                img.blit(g, (x, 0))
                x += g.get_width() + spacing
        else:
            img = f.render(words, True, color)
        rect = img.get_rect(center=centre)
        if shadow:
            dark = img.copy()
            dark.fill((0, 0, 0, 170), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(dark, rect.move(3, 4))
        surface.blit(img, rect)
        return rect

    def gradient(size, top, bottom):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        for y in range(size[1]):
            k = y / max(1, size[1] - 1)
            color = [int(top[i] + (bottom[i] - top[i]) * k) for i in range(len(top))]
            pygame.draw.line(surface, color, (0, y), (size[0], y))
        return surface

    def pillars(surface, centre_y, current, size, gap):
        """The four words in a row, the one being shown lit."""
        f = font("segoeuib.ttf", size)
        widths = [f.size(p)[0] for p in PILLARS]
        x = (surface.get_width() - sum(widths) - gap * (len(PILLARS) - 1)) // 2
        for word, width in zip(PILLARS, widths):
            lit = word == current
            img = f.render(word, True, GOLD if lit else GOLD_DIM)
            if not lit:
                img.set_alpha(150)
            surface.blit(img, img.get_rect(midleft=(x, centre_y)))
            if lit:
                pygame.draw.rect(surface, GOLD, (x, centre_y + size // 2 + 8, width, 4), border_radius=2)
            x += width + gap

    def tall_panel(section, line):
        w, h = TALL
        surface = gradient(TALL, INDIGO, INK)
        pygame.draw.rect(surface, (0, 0, 0), (0, TALL_GAME_Y, w, TALL_GAME[1]))
        for y in (TALL_GAME_Y - 5, TALL_GAME_Y + TALL_GAME[1] + 1):
            pygame.draw.rect(surface, GOLD, (0, y, w, 4))
        if section:
            text(surface, section, "segoeuib.ttf", 124, GOLD, (w // 2, 132), spacing=6)
            if line:
                text(surface, line, "seguisb.ttf", 50, CREAM, (w // 2, 240))
        else:
            if line:
                text(surface, TITLE, "georgiab.ttf", 88, GOLD, (w // 2, 118))
                text(surface, line, "seguisb.ttf", 50, CREAM, (w // 2, 226))
            else:                       # the title screen says the name itself
                text(surface, "DIGAMBER PAATHSHALA", "segoeuib.ttf", 64, GOLD, (w // 2, 118), spacing=4)
                text(surface, "presents", "seguisb.ttf", 50, CREAM, (w // 2, 212))
        below = TALL_GAME_Y + TALL_GAME[1]
        pillars(surface, below + 92, section, 40, 44)
        text(surface, TITLE, "georgiab.ttf", 40, GOLD_DIM, (w // 2, below + 190), shadow=False)
        return surface

    def wide_overlay(section, line):
        w, h = SRC_W, SRC_H
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        surface.blit(gradient((w, 300), (0, 0, 0, 0), (0, 0, 0, 215)), (0, h - 300))
        if section:
            f = font("segoeuib.ttf", 120)
            rect = text(surface, section, "segoeuib.ttf", 120, GOLD,
                        (90 + f.size(section)[0] // 2 + 3 * len(section), h - 150), spacing=6)
            pygame.draw.rect(surface, GOLD, (60, rect.top + 14, 10, rect.height - 28), border_radius=4)
            if line:
                lf = font("seguisb.ttf", 54)
                text(surface, line, "seguisb.ttf", 54, CREAM, (92 + lf.size(line)[0] // 2, h - 58))
        else:
            tf = font("georgiab.ttf", 84)
            text(surface, TITLE, "georgiab.ttf", 84, GOLD, (90 + tf.size(TITLE)[0] // 2, h - 140))
            words = line or PRESENTS.title()
            lf = font("seguisb.ttf", 48)
            text(surface, words, "seguisb.ttf", 48, CREAM, (92 + lf.size(words)[0] // 2, h - 58))
        return surface

    def end_card(size, dated):
        w, h = size
        tall = h > w
        surface = pygame.Surface(size)
        art = pygame.image.load(os.path.join(ROOT, "assets", "images", "backgrounds", "title_background.png"))
        scale = max(w / art.get_width(), h / art.get_height())
        art = pygame.transform.smoothscale(art, (int(art.get_width() * scale) + 1, int(art.get_height() * scale) + 1))
        surface.blit(art, art.get_rect(center=(w // 2, h // 2)))
        surface.blit(gradient(size, (*INK, 150), (*INK, 235)), (0, 0))
        k = 1.0 if tall else 0.82
        mid = w // 2
        y = int(h * (0.19 if tall else 0.13))

        def put(words, name, size_, color, gap, **kw):
            nonlocal y
            size_ = int(size_ * k)
            while size_ > 20 and font(name, size_).size(words)[0] > w - 110:
                size_ -= 2              # a long line is set smaller, never cut off
            text(surface, words, name, size_, color, (mid, y), **kw)
            y += int(gap * k)

        put("Digamber Paathshala presents", "seguisb.ttf", 42, CREAM, 110)
        put(TITLE, "georgiab.ttf", 104, GOLD, 150)
        pillars_y = y
        row = pygame.Surface((w, 90), pygame.SRCALPHA)
        f = font("segoeuib.ttf", int(42 * k))
        words = "   \u2022   ".join(p.title() for p in PILLARS)
        img = f.render(words, True, CREAM)
        row.blit(img, img.get_rect(center=(w // 2, 45)))
        surface.blit(row, (0, pillars_y - 45))
        y += int((250 if tall else 150) * k)
        if dated:
            put("Play it on", "seguisb.ttf", 50, CREAM, 100)
            put(OCCASION, "georgiab.ttf", 76, GOLD, 120)
            put(DATE, "segoeuib.ttf", 96, CREAM, 190 if tall else 150)
        else:
            put("Play it at", "seguisb.ttf", 50, CREAM, 110)
        put(PLACE, "segoeuib.ttf", 60, GOLD, 110)
        put(INVITATION, "seguisb.ttf", 52, CREAM, 0)
        return surface

    return pygame, tall_panel, wide_overlay, end_card


# ── the tall window: where to look ───────────────────────────────────────────

def load_track(path):
    xs = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            xs.append(float(row["x"]) if row["x"] else None)
    return xs                                   # one a sixtieth of a second


def window_x(track, start, seconds, look):
    """An ffmpeg expression in t for the left edge of the tall window."""
    width = WINDOWS[look][0]
    limit = SRC_W - width
    if look != "follow":
        return str(int(limit / 2))
    keys = []
    step = 0.2
    count = int(seconds / step) + 2
    for i in range(count):
        t = i * step
        lo = int((start + t - 0.4) * 60)
        hi = int((start + t + 0.4) * 60)
        near = [x for x in track[max(0, lo):hi] if x is not None]
        centre = sum(near) / len(near) if near else SRC_W / 2
        keys.append((t, min(limit, max(0.0, centre - width / 2))))
    expr = f"{keys[-1][1]:.1f}"
    for (t0, a), (t1, b) in reversed(list(zip(keys, keys[1:]))):
        expr = f"if(lt(t,{t1:.2f}),{a:.1f}+({b - a:.1f})*(t-{t0:.2f})/{step},{expr})"
    return expr


# ── the cut ──────────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--recordings", default=os.path.join(ROOT, "recordings"))
    parser.add_argument("--work", help="folder for the pieces (default: recordings\\_trailer_work)")
    parser.add_argument("--music", default=os.path.join(ROOT, "assets", "audio", "bgm", "bgm_loop.ogg"),
                        help="the track under it (default: the game's own music)")
    parser.add_argument("--suffix", default="",
                        help="added to the file names, to keep two cuts side by side (e.g. _high_impact)")
    args = parser.parse_args(argv)

    rec = args.recordings
    work = args.work or os.path.join(rec, "_trailer_work")
    os.makedirs(work, exist_ok=True)
    sources = {who: os.path.join(rec, f"game_{who}.mp4") for who in ("boy", "girl")}
    tracks = {who: load_track(os.path.join(rec, f"game_{who}.track.csv")) for who in sources}
    for path in sources.values():
        if not os.path.exists(path):
            raise SystemExit(f"missing {path}: record it with tools\\autoplay.py --game first")

    pygame, tall_panel, wide_overlay, end_card = lettering()
    encode = ["-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-an"]

    pieces = {"tall": [], "wide": []}
    for n, (section, line, who, start, seconds, look) in enumerate(CUTS):
        panel = os.path.join(work, f"panel_{n:02d}.png")
        strip = os.path.join(work, f"strip_{n:02d}.png")
        pygame.image.save(tall_panel(section, line), panel)
        pygame.image.save(wide_overlay(section, line), strip)
        clip = ["-ss", f"{start:.3f}", "-t", f"{seconds:.3f}", "-i", sources[who]]

        tall = os.path.join(work, f"tall_{n:02d}.mp4")
        x = window_x(tracks[who], start, seconds, look)
        run(["-loop", "1", "-t", f"{seconds:.3f}", "-i", panel, *clip, "-filter_complex",
             f"[1:v]crop={WINDOWS[look][0]}:{WINDOWS[look][1]}:x='{x}':y={WINDOWS[look][2]},"
             f"scale={TALL_GAME[0]}:{TALL_GAME[1]}:flags=lanczos[game];"
             f"[0:v][game]overlay=0:{TALL_GAME_Y}:shortest=1", *encode, tall])
        pieces["tall"].append(tall)

        wide = os.path.join(work, f"wide_{n:02d}.mp4")
        run([*clip, "-loop", "1", "-t", f"{seconds:.3f}", "-i", strip, "-filter_complex",
             "[0:v][1:v]overlay=0:0:shortest=1", *encode, wide])
        pieces["wide"].append(wide)
        print(f"[trailer] {n + 1:2d}/{len(CUTS)}  {section or 'opening/closing':10s} {line or ''}")

    body = sum(c[4] for c in CUTS)
    total = body + END_CARD_SECONDS
    outputs = []
    for shape, size in (("tall", TALL), ("wide", (SRC_W, SRC_H))):
        for dated in (True, False):
            card_png = os.path.join(work, f"end_{shape}_{'dated' if dated else 'undated'}.png")
            card = card_png.replace(".png", ".mp4")
            pygame.image.save(end_card(size, dated), card_png)
            run(["-loop", "1", "-t", f"{END_CARD_SECONDS}", "-i", card_png,
                 "-vf", "fade=t=in:st=0:d=0.5", *encode, card])
            listing = os.path.join(work, f"list_{shape}.txt")
            with open(listing, "w", encoding="utf-8") as f:
                for piece in pieces[shape] + [card]:
                    f.write("file '" + piece.replace("\\", "/") + "'\n")
            out = os.path.join(rec, f"trailer_{shape}{'' if dated else '_undated'}{args.suffix}.mp4")
            run(["-f", "concat", "-safe", "0", "-i", listing, "-stream_loop", "-1", "-i", args.music,
                 "-filter_complex",
                 f"[0:v]fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.8:.2f}:d=0.8[v];"
                 f"[1:a]atrim=0:{total:.2f},afade=t=in:st=0:d=0.6,afade=t=out:st={total - 2.5:.2f}:d=2.5,"
                 "volume=0.9[a]",
                 "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-c:v", "libx264", "-preset", "slow",
                 "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", "-t", f"{total:.2f}", out])
            outputs.append(out)

    send = os.path.join(rec, f"trailer_tall_whatsapp{args.suffix}.mp4")
    run(["-i", os.path.join(rec, f"trailer_tall{args.suffix}.mp4"), "-vf", "scale=720:1280:flags=lanczos",
         "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", send])
    outputs.append(send)

    print(f"[trailer] {total:.1f}s")
    for out in outputs:
        print(f"[trailer] {out}  ({os.path.getsize(out) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
