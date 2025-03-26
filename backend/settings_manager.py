import json
import os

class SettingsManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.defaults = {
            "theme": "light",
            "obd_port": None, # e.g., "/dev/rfcomm0" for BT, "/dev/ttyUSB0" for USB
            "obd_baudrate": None, # Often auto-detected by python-obd
            "radio_type": "none", # 'sdr', 'si4703', 'none'
            "radio_i2c_address": None, # e.g., 0x10 for some Si chips
            "last_fm_station": 98.5
        }
        self.settings = self._load_settings()

    def _load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Ensure all default keys are present
                    for key, value in self.defaults.items():
                        if key not in loaded_settings:
                            loaded_settings[key] = value
                    return loaded_settings
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings file {self.config_file}: {e}")
                # Fallback to defaults if file is corrupt or unreadable
                return self.defaults.copy()
        else:
            # Create default file if it doesn't exist
            print(f"Settings file not found. Creating default: {self.config_file}")
            self.settings = self.defaults.copy()
            self.save_settings() # Save defaults immediately
            return self.settings


    def save_settings(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings file {self.config_file}: {e}")

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key)) # Return default if key missing

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings() # Auto-save on change