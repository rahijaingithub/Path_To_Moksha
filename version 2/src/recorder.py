"""
recorder.py — Record gameplay to a video file while you play.

Frames are taken from the game's logical 1920x1080 surface, not from the window,
so a recording is clean 16:9 whatever size the window happens to be and whether or
not it is fullscreen. They are piped straight into ffmpeg; nothing is written to
disk frame by frame.

Recording is sampled down to RECORD_FPS. The game runs at 60, and handing a
full-size frame to the encoder sixty times a second is more than most machines
will do without the game itself stuttering.

If ffmpeg is not on PATH the recorder says so once and stays off; the game plays
on exactly as before.
"""
import datetime
import os
import shutil
import subprocess

import pygame

RECORD_FPS = 30
RECORD_SIZE = (1280, 720)


class Recorder:
    """Pipes the logical surface into ffmpeg, between start() and stop()."""

    def __init__(self, out_dir, logical_size):
        self.out_dir = out_dir
        self.logical_size = logical_size
        self._proc = None
        self._path = None
        self._due = 0.0
        self._frames = 0
        self._warned = False

    @property
    def recording(self):
        return self._proc is not None

    @property
    def path(self):
        return self._path

    # ── control ───────────────────────────────────────────────────────────────

    def toggle(self):
        """Start if stopped, stop if started. Returns True when now recording."""
        if self.recording:
            self.stop()
            return False
        self.start()
        return self.recording

    def start(self):
        if self.recording:
            return
        if not shutil.which("ffmpeg"):
            if not self._warned:
                self._warned = True
                print("[Recorder] ffmpeg is not on PATH — recording unavailable. "
                      "Install ffmpeg and add it to PATH, then try again.")
            return

        os.makedirs(self.out_dir, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = os.path.join(self.out_dir, f"PathToMoksha_{stamp}.mp4")
        w, h = self.logical_size
        try:
            self._proc = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error",
                 "-f", "rawvideo", "-pix_fmt", "rgb24",
                 "-s", f"{w}x{h}", "-r", str(RECORD_FPS), "-i", "-",
                 "-vf", f"scale={RECORD_SIZE[0]}:{RECORD_SIZE[1]}",
                 "-c:v", "libx264", "-preset", "veryfast",
                 "-pix_fmt", "yuv420p", "-crf", "22", self._path],
                stdin=subprocess.PIPE)
        except OSError as exc:
            print(f"[Recorder] could not start ffmpeg: {exc}")
            self._proc = None
            return

        self._due = 0.0
        self._frames = 0
        print(f"[Recorder] recording to {self._path}")

    def stop(self):
        """Finish the file. Safe to call when not recording."""
        if not self.recording:
            return
        try:
            self._proc.stdin.close()
            self._proc.wait(timeout=30)
        except Exception as exc:                     # never take the game down
            print(f"[Recorder] trouble closing the file: {exc}")
        seconds = self._frames / RECORD_FPS
        print(f"[Recorder] saved {self._path}  ({seconds:.1f}s, {self._frames} frames)")
        self._proc = None

    # ── per frame ─────────────────────────────────────────────────────────────

    def capture(self, surface, dt):
        """Offer a frame. Written only when one is due at RECORD_FPS."""
        if not self.recording:
            return
        self._due += dt
        interval = 1.0 / RECORD_FPS
        if self._due < interval:
            return
        # Never bank more than one spare frame: a long stall would otherwise
        # write a burst of identical frames trying to catch up.
        self._due = min(self._due - interval, interval)
        try:
            self._proc.stdin.write(pygame.image.tobytes(surface, "RGB"))
            self._frames += 1
        except (BrokenPipeError, OSError) as exc:
            print(f"[Recorder] the encoder went away: {exc}")
            self._proc = None

    def draw_indicator(self, surface, font):
        """A red dot, drawn after the frame is captured so it stays out of the file."""
        if not self.recording:
            return
        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        text = font.render("REC", True, (255, 80, 80))
        pad = 10
        width = text.get_width() + 34 + pad * 2
        plate = pygame.Surface((width, text.get_height() + pad), pygame.SRCALPHA)
        pygame.draw.rect(plate, (12, 8, 16, 190), plate.get_rect(), border_radius=6)
        if blink:
            pygame.draw.circle(plate, (255, 60, 60), (pad + 8, plate.get_height() // 2), 8)
        plate.blit(text, (pad + 26, pad // 2))
        surface.blit(plate, (surface.get_width() - width - 16, 16))
