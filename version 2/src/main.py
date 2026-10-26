
"""
main.py — Entry point for The Path to Moksha.
Handles window management, dynamic scaling, and the main game loop.
"""
import os
import sys
import pygame
from settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, GAME_TITLE, FPS,
    DEFAULT_WINDOWED_SIZE, COLOR_BG_DARK,
    SCENE_TITLE, SCENE_OPTIONS, SCENE_CONTROLS, SCENE_PLAYER_SELECT, SCENE_LEADERBOARD, SCENE_TUTORIAL, SCENE_CHARACTER_SELECT, SCENE_LEVEL, SCENE_TRANSITION, SCENE_VICTORY, SCENE_BONUS,
)
from scene_manager import SceneManager
from input_manager import InputManager
from asset_manager import AssetManager
from recorder import Recorder
from title_screen import TitleScreen
from options_scene import OptionsScene
from controller_settings_scene import ControllerSettingsScene
from player_select_scene import PlayerSelectScene
from leaderboard_scene import LeaderboardScene
from character_select import CharacterSelect
from level_scene import LevelScene
from transition_scene import TransitionScene
from victory_scene import VictoryScene
from bonus_scene import BonusScene
from tutorial_scene import TutorialScene


class Game:
    """Main game class — owns the window, loop, and scaling logic."""

    def __init__(self, record=False):
        pygame.init()
        try:
            if pygame.mixer.get_init() is None:
                try:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                except pygame.error:
                    pygame.mixer.init()
            # Ensure enough sound channels are allocated for SFX & BGM
            pygame.mixer.set_num_channels(16)
            info = pygame.mixer.get_init()
            print(f"[Game] Audio initialized successfully: freq={info[0]}, format={info[1]}, channels={info[2]}")
        except pygame.error as exc:
            print(f"[Game] Audio disabled/unavailable: {exc}")
        pygame.display.set_caption(GAME_TITLE)

        # Window state
        self.windowed_size = DEFAULT_WINDOWED_SIZE
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF)

        # The game always renders to this fixed-size surface
        self.logical_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))

        # Scaling parameters (updated every frame)
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # Core systems
        self.clock = pygame.time.Clock()
        self.input_mgr = InputManager()
        self.assets = AssetManager()
        self.scene_mgr = SceneManager()

        # Register scenes
        self.scene_mgr.register(SCENE_TITLE, TitleScreen(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_OPTIONS, OptionsScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_CONTROLS, ControllerSettingsScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_PLAYER_SELECT, PlayerSelectScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_LEADERBOARD, LeaderboardScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_TUTORIAL, TutorialScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_CHARACTER_SELECT, CharacterSelect(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_LEVEL, LevelScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_TRANSITION, TransitionScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_VICTORY, VictoryScene(self.scene_mgr, self.assets, self.input_mgr))
        self.scene_mgr.register(SCENE_BONUS, BonusScene(self.scene_mgr, self.assets, self.input_mgr))



        # FPS Counter overlay toggle
        self.show_fps = False
        self.fps_font = pygame.font.SysFont("Consolas", 18, bold=True)

        # Screen recording. F9 toggles it at any time; --record starts it at launch.
        # Recordings land beside the game so they are easy to find.
        self.recorder = Recorder(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "recordings"),
            (LOGICAL_WIDTH, LOGICAL_HEIGHT))
        if record:
            self.recorder.start()

        # Start at title
        self.scene_mgr.switch_to(SCENE_TITLE, input_mgr=self.input_mgr)

    def _toggle_fullscreen(self):
        """Switch between windowed and fullscreen."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF)

    def _compute_scaling(self):
        """Compute letterboxed scaling from logical to screen size."""
        sw, sh = self.screen.get_size()
        scale = min(sw / LOGICAL_WIDTH, sh / LOGICAL_HEIGHT)
        self.scale_x = scale
        self.scale_y = scale
        scaled_w = int(LOGICAL_WIDTH * scale)
        scaled_h = int(LOGICAL_HEIGHT * scale)
        self.offset_x = (sw - scaled_w) // 2
        self.offset_y = (sh - scaled_h) // 2

    def run(self, max_frames=None):
        """Main game loop."""
        running = True
        frame_count = 0
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            # Cap dt to prevent spiral of death
            if dt > 0.1:
                dt = 0.1

            events = pygame.event.get()

            # Handle window-level events
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                    self.windowed_size = (event.w, event.h)
                    self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    self.show_fps = not self.show_fps
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
                    self.recorder.toggle()

            # Update input
            self.input_mgr.update(events, self.scale_x, self.scale_y, self.offset_x, self.offset_y, dt)

            # Update scene & handle events
            self.scene_mgr.handle_events(events, self.input_mgr)

            # Fullscreen toggle (check after handle_events so title/options scene actions trigger it)
            if self.input_mgr.just_pressed[InputManager.FULLSCREEN]:
                self._toggle_fullscreen()

            self.scene_mgr.update(dt)

            # Draw to logical surface
            self.logical_surface.fill(COLOR_BG_DARK)
            self.scene_mgr.draw(self.logical_surface)

            # Draw FPS overlay if enabled
            if self.show_fps:
                fps_val = int(self.clock.get_fps())
                mode_str = "FULLSCREEN" if self.is_fullscreen else "WINDOWED"
                fps_text = f"FPS: {fps_val} | {dt*1000:.1f}ms | {self.screen.get_width()}x{self.screen.get_height()} | {mode_str}"
                txt_surf = self.fps_font.render(fps_text, True, (0, 255, 128))
                bg_surf = pygame.Surface((txt_surf.get_width() + 16, txt_surf.get_height() + 8), pygame.SRCALPHA)
                bg_surf.fill((0, 0, 0, 190))
                bg_surf.blit(txt_surf, (8, 4))
                self.logical_surface.blit(bg_surf, (16, 16))

            # Record before the REC badge is drawn, so the badge is on screen for
            # the player but never in the file.
            self.recorder.capture(self.logical_surface, dt)
            self.recorder.draw_indicator(self.logical_surface, self.fps_font)

            # Scale and blit to screen
            self._compute_scaling()
            self.screen.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(
                self.logical_surface,
                (int(LOGICAL_WIDTH * self.scale_x), int(LOGICAL_HEIGHT * self.scale_y))
            )
            self.screen.blit(scaled, (self.offset_x, self.offset_y))
            pygame.display.flip()

            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                running = False

        # Close the file before the window goes, so quitting mid-recording still
        # leaves a playable video rather than a truncated one.
        self.recorder.stop()
        pygame.quit()


def main(argv=None):
    """Start the game, or briefly initialize it for a packaging smoke test.

    --record starts recording at launch; F9 toggles it any time while playing.
    """
    argv = sys.argv[1:] if argv is None else argv
    max_frames = 2 if "--smoke-test" in argv else None
    Game(record="--record" in argv).run(max_frames=max_frames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
