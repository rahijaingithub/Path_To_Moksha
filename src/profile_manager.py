"""
profile_manager.py — Manages persistent player profiles and global high scores for Path to Moksha.
Saves data to the writable platform-specific data directory from settings.py.
"""
import os
import json
from settings import BASE_DIR


DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
SCORES_FILE = os.path.join(DATA_DIR, "high_scores.json")


class ProfileManager:
    """Singleton helper class for player profiles & global rankings."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.profiles = self._load_json(PROFILES_FILE, default={})
        self.high_scores = self._load_json(SCORES_FILE, default=[])

    def _load_json(self, filepath, default):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ProfileManager] Error loading {filepath}: {e}")
        return default

    def _save_json(self, filepath, data):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ProfileManager] Error saving {filepath}: {e}")

    def get_profiles(self):
        """Returns list of profile dicts."""
        return list(self.profiles.values())

    def get_profile(self, name):
        """Returns profile dict for name or None."""
        return self.profiles.get(name.strip())

    def save_profile(self, name, character="boy", score=0, level_reached=1):
        """Creates or updates a player profile."""
        from datetime import datetime
        name = name.strip()
        if not name:
            name = "Pilgrim"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        if name not in self.profiles:
            self.profiles[name] = {
                "name": name,
                "character": character,  # "boy" (Shravak) or "girl" (Shravika)
                "high_score": score,
                "date_achieved": now_str if score > 0 else "N/A",
                "highest_level": level_reached,
                "games_played": 1
            }
            self._save_json(PROFILES_FILE, self.profiles)
            self.record_score(name, character, score, level_reached, now_str)
        else:
            prof = self.profiles[name]
            prof["character"] = character
            prof["games_played"] = prof.get("games_played", 0) + 1
            
            # ONLY update high_score if the new score is STRICTLY HIGHER than previous score!
            if score > prof.get("high_score", 0):
                prof["high_score"] = score
                prof["date_achieved"] = now_str
                prof["highest_level"] = max(prof.get("highest_level", 1), level_reached)
                self._save_json(PROFILES_FILE, self.profiles)
                self.record_score(name, character, score, level_reached, now_str)
            else:
                self._save_json(PROFILES_FILE, self.profiles)

        return self.profiles[name]

    def record_score(self, name, character, score, level_reached, timestamp=None):
        """Records or updates a completed game score entry into global high scores ONLY if strictly higher."""
        from datetime import datetime
        now_str = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")
        name_clean = name.strip()
        name_key = name_clean.lower()
        
        # Search case-insensitively for existing player entry
        existing = None
        for entry in self.high_scores:
            if entry["name"].strip().lower() == name_key:
                existing = entry
                break

        if existing:
            # Update entry with best score ONLY if strictly higher!
            if score > existing.get("score", 0):
                existing["name"] = name_clean
                existing["score"] = score
                existing["character"] = "Shravak" if character == "boy" else "Shravika"
                existing["level"] = max(existing.get("level", 1), level_reached)
                existing["date"] = now_str
        else:
            self.high_scores.append({
                "name": name_clean,
                "character": "Shravak" if character == "boy" else "Shravika",
                "score": score,
                "level": level_reached,
                "date": now_str,
            })

        # Sort descending by score
        self.high_scores.sort(key=lambda x: x["score"], reverse=True)

        # Keep top 500 scores maximum
        self.high_scores = self.high_scores[:500]
        self._save_json(SCORES_FILE, self.high_scores)





    def get_global_rankings(self):
        """Returns sorted list of all high scores."""
        return self.high_scores

    def get_player_rank(self, name, current_score):
        """Finds player's 1-based global rank."""
        for rank, entry in enumerate(self.high_scores, 1):
            if entry["name"] == name and entry["score"] == current_score:
                return rank
        return len(self.high_scores)
