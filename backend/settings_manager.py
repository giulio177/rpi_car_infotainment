# setting_manager.py
import json
import os

class SettingsManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.defaults = {
            "theme": "light",
            "obd_port": None,
            "obd_baudrate": None,
            "radio_type": "none",
            "radio_i2c_address": None,
            "last_fm_station": 98.5,
            "window_resolution": [1920, 1080]
        }
        self.settings = self._load_settings()

    # --- _load_settings --- (Make sure it correctly handles the new default)
    def _load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    updated_settings = self.defaults.copy()
                    updated_settings.update(loaded_settings)
                    
                    return updated_settings
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings file {self.config_file}: {e}")
                return self.defaults.copy()
        else:
            print(f"Settings file not found. Creating default: {self.config_file}")
            # Create default file using self.defaults directly
            with open(self.config_file, 'w') as f:
                json.dump(self.defaults, f, indent=4)
            return self.defaults.copy() # Return a copy

    def save_settings(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings file {self.config_file}: {e}")

    def get(self, key):
        # Ensure key exists in defaults for safety
        default_value = self.defaults.get(key)
        # Return the setting value, fallback to default_value if key missing in self.settings
        return self.settings.get(key, default_value)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings() # Auto-save on change
