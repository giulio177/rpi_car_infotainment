# backend/audio_manager.py

import subprocess
import re # Regular expressions for parsing amixer output
from .media_info import get_album_art, get_lyrics

class AudioManager:
    # Default mixer control name. Might need changing based on your RPi setup
    # Common alternatives: 'PCM', 'HDMI', 'Speaker'
    # Run 'amixer scontrols' in your RPi terminal to see available controls.
    MIXER_CONTROL = "Master"
    # MIXER_CONTROL = "PCM" # Try this if Master doesn't work
    cover_url = get_album_art(title, artist)
    lyrics = get_lyrics(title, artist)

    def _run_amixer_command(self, args):
        """Helper function to run amixer commands."""
        command = ["amixer"] + args
        try:
            # Use check_output to capture stdout, stderr to DEVNULL to hide errors
            # Use text=True for easier string handling
            result = subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True)
            # print(f"Ran: {' '.join(command)}\nOutput:\n{result}") # Uncomment for debugging
            return result
        except FileNotFoundError:
            print(f"ERROR: 'amixer' command not found. Make sure alsa-utils is installed.")
            return None
        except subprocess.CalledProcessError as e:
            # This might happen if the control name is wrong or volume is invalid
            print(f"ERROR: Command '{' '.join(command)}' failed: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error running amixer: {e}")
            return None

    def set_volume(self, level_percent):
        """Sets the system volume for the specified control."""
        if not 0 <= level_percent <= 100:
            print(f"ERROR: Invalid volume level {level_percent}. Must be 0-100.")
            return False

        print(f"AudioManager: Setting volume to {level_percent}%")
        # Format: amixer sset 'ControlName' 50%
        args = ["sset", self.MIXER_CONTROL, f"{level_percent}%"]
        result = self._run_amixer_command(args)
        return result is not None # Return True if command likely succeeded

    def set_mute(self, muted: bool):
        """Mutes or unmutes the system volume."""
        state = "mute" if muted else "unmute"
        print(f"AudioManager: Setting mute state to {state}")
        # Format: amixer sset 'ControlName' mute/unmute
        args = ["sset", self.MIXER_CONTROL, state]
        result = self._run_amixer_command(args)
        return result is not None # Return True if command likely succeeded

    def get_volume(self):
        """Gets the current volume percentage. Returns int or None."""
        # Format: amixer sget 'ControlName'
        args = ["sget", self.MIXER_CONTROL]
        output = self._run_amixer_command(args)
        if output:
            # Use regex to find percentage, e.g., [80%]
            # This regex looks for digits inside square brackets followed by %
            match = re.search(r"\[(\d+)%\]", output)
            if match:
                volume = int(match.group(1))
                # print(f"AudioManager: Got volume {volume}%") # Debug
                return volume
            else:
                print(f"ERROR: Could not parse volume percentage from amixer output for {self.MIXER_CONTROL}.")
        return None # Return None if command failed or parsing failed

    def get_mute_status(self):
        """Checks if the system is muted. Returns bool (True=muted) or None."""
        args = ["sget", self.MIXER_CONTROL]
        output = self._run_amixer_command(args)
        if output:
            # Use regex to find mute state, e.g., [on] or [off]
            match = re.search(r"\[(on|off)\]", output)
            if match:
                status = match.group(1)
                is_muted = (status == "off")
                # print(f"AudioManager: Got mute status: {status} (Muted: {is_muted})") # Debug
                return is_muted
            else:
                print(f"ERROR: Could not parse mute status from amixer output for {self.MIXER_CONTROL}.")
        return None # Return None if command failed or parsing failed
