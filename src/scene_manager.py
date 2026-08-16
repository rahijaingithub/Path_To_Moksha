"""
scene_manager.py — Manages game scenes/states (Title, Character Select, Level, etc.)
Each scene is a class with update(), draw(), and handle_events() methods.
"""


class Scene:
    """Base class for all game scenes."""

    def __init__(self, manager):
        self.manager = manager

    def on_enter(self, **kwargs):
        """Called when the scene becomes active."""
        pass

    def on_exit(self):
        """Called when the scene is being replaced."""
        pass

    def handle_events(self, events, input_mgr):
        """Process input events."""
        pass

    def update(self, dt):
        """Update game logic. dt is delta time in seconds."""
        pass

    def draw(self, surface):
        """Draw the scene onto the logical surface."""
        pass


class SceneManager:
    """Registry and switcher for game scenes."""

    def __init__(self):
        self.scenes = {}
        self.active_scene = None
        self.active_key = None
        # Shared data across scenes
        self.shared = {
            "character": "boy",    # "boy" or "girl"
            "current_level": 1,
            "total_time": 0.0,      # accumulated time across all levels
            "level_times": {},
            "monk_correct": {},
            "boxes_opened": {},
        }

    def register(self, key, scene):
        """Register a scene by key."""
        self.scenes[key] = scene

    def switch_to(self, key, **kwargs):
        """Transition to a different scene."""
        if self.active_scene:
            self.active_scene.on_exit()
        self.active_key = key
        self.active_scene = self.scenes[key]
        self.active_scene.on_enter(**kwargs)

    def handle_events(self, events, input_mgr):
        if self.active_scene:
            self.active_scene.handle_events(events, input_mgr)

    def update(self, dt):
        if self.active_scene:
            self.active_scene.update(dt)

    def draw(self, surface):
        if self.active_scene:
            self.active_scene.draw(surface)
