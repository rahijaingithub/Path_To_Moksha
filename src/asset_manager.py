"""
asset_manager.py — Centralised loader and cache for images, sounds, and fonts.
"""
import os
import pygame
from settings import IMAGES_DIR, AUDIO_DIR, FONTS_DIR


class AssetManager:
    """Loads and caches game assets."""

    def __init__(self):
        self._images = {}
        self._sounds = {}
        self._music_loaded = None
        self._fonts = {}

    # ── Images ────────────────────────────────────────────────────────────────

    def load_image(self, name, subfolder="", alpha=True, scale=None):
        """
        Load an image from assets/images/<subfolder>/<name>.
        Returns a pygame.Surface. Cached after first load.
        Scale is included in the cache key so different sizes are stored separately.
        """
        key = (os.path.join(subfolder, name), scale)
        if key not in self._images:
            path = os.path.join(IMAGES_DIR, subfolder, name)
            if not os.path.exists(path):
                # Return a pink placeholder so the game doesn't crash
                surf = pygame.Surface(scale or (64, 64))
                surf.fill((255, 0, 220))
                self._images[key] = surf
                print(f"[AssetManager] WARNING: Missing image: {path}")
                return surf
            img = pygame.image.load(path)
            if alpha:
                img = img.convert_alpha()
            else:
                img = img.convert()
            if scale:
                img = pygame.transform.smoothscale(img, scale)
            self._images[key] = img
        return self._images[key]

    def get_image(self, name, subfolder=""):
        """Retrieve a previously loaded image."""
        key = os.path.join(subfolder, name)
        return self._images.get(key)

    # ── Sounds ────────────────────────────────────────────────────────────────

    def load_sound(self, name, subfolder="sfx"):
        """Load a sound effect. Cached after first load."""
        key = os.path.join(subfolder, name)
        if key not in self._sounds:
            path = os.path.join(AUDIO_DIR, subfolder, name)
            if not os.path.exists(path):
                print(f"[AssetManager] WARNING: Missing sound: {path}")
                return None
            self._sounds[key] = pygame.mixer.Sound(path)
        return self._sounds[key]

    def play_sound(self, name, subfolder="sfx", volume=0.5):
        """Load (if needed) and play a sound effect."""
        snd = self.load_sound(name, subfolder)
        if snd:
            snd.set_volume(volume)
            snd.play()

    def play_music(self, name, subfolder="bgm", volume=0.3, loops=-1):
        """Stream background music."""
        path = os.path.join(AUDIO_DIR, subfolder, name)
        if not os.path.exists(path):
            print(f"[AssetManager] WARNING: Missing music: {path}")
            return
        if self._music_loaded != path:
            pygame.mixer.music.load(path)
            self._music_loaded = path
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)

    def set_music_volume(self, volume):
        """Update music playback volume."""
        pygame.mixer.music.set_volume(volume)

    def stop_music(self):
        pygame.mixer.music.stop()


    # ── Fonts ─────────────────────────────────────────────────────────────────

    def load_font(self, name, size):
        """Load a font. If name is None, uses the default pygame font."""
        key = (name, size)
        if key not in self._fonts:
            if name is None:
                self._fonts[key] = pygame.font.Font(None, size)
            else:
                path = os.path.join(FONTS_DIR, name)
                if os.path.exists(path):
                    self._fonts[key] = pygame.font.Font(path, size)
                else:
                    print(f"[AssetManager] WARNING: Missing font: {path}, using default.")
                    self._fonts[key] = pygame.font.Font(None, size)
        return self._fonts[key]
