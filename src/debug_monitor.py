import time
import pygame

class DebugMonitor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebugMonitor, cls).__new__(cls)
            cls._instance.enabled = True
            cls._instance.start_time = time.time()
        return cls._instance

    def _get_time(self):
        return f"{time.time() - self.start_time:07.3f}s"

    def log_raw_event(self, event, scene_name="Unknown"):
        if not self.enabled: return
        
        event_str = "UNKNOWN"
        if event.type == pygame.JOYBUTTONDOWN:
            event_str = f"JOYBUTTONDOWN btn={event.button}"
        elif event.type == pygame.JOYBUTTONUP:
            event_str = f"JOYBUTTONUP btn={event.button}"
        elif event.type == pygame.JOYDEVICEADDED:
            event_str = f"JOYDEVICEADDED idx={event.device_index}"
        elif event.type == pygame.JOYDEVICEREMOVED:
            event_str = f"JOYDEVICEREMOVED id={event.instance_id}"
        elif event.type == pygame.JOYAXISMOTION:
            # Too noisy, ignore unless large
            if abs(event.value) > 0.5:
                event_str = f"JOYAXISMOTION axis={event.axis} val={event.value:.2f}"
            else:
                return
        elif event.type == pygame.JOYHATMOTION:
            event_str = f"JOYHATMOTION hat={event.hat} val={event.value}"
        else:
            return

        print(f"[{self._get_time()}] RAW     │ {event_str:<30} │ Scene={scene_name}")

    def log_just_pressed(self, just_pressed_dict, scene_name="Unknown", extra_info=""):
        if not self.enabled: return
        
        active_keys = [k for k, v in just_pressed_dict.items() if v]
        if not active_keys: return

        keys_str = " ".join([f"{k}=True" for k in active_keys])
        print(f"[{self._get_time()}] FLAGGED │ {keys_str:<30} │ Scene={scene_name} {extra_info}")

    def log_action(self, scene_name, description):
        if not self.enabled: return
        print(f"[{self._get_time()}] ACTION  │ {scene_name:<15} → {description}")

    def log_switch(self, from_scene, to_scene):
        if not self.enabled: return
        from_str = from_scene if from_scene else "None"
        to_str = to_scene if to_scene else "None"
        print(f"[{self._get_time()}] SWITCH  │ {from_str} ──► {to_str}")

# Global instance
monitor = DebugMonitor()
