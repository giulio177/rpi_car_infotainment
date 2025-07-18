# backend/audio_manager.py

import subprocess
import re  # Regular expressions for parsing amixer output
from .media_info import get_album_art, get_lyrics


class AudioManager:
    """
    Manages system audio by controlling the default PipeWire mixer ('Master')
    using the 'amixer' command-line utility.
    """
    
    # Come hai scoperto, il controllo creato da PipeWire si chiama "Master".
    MIXER_CONTROL = "Master"
    def get_media_info(self, title, artist):
        """Get album art and lyrics for a song"""
        if not title or not artist or title == "---" or artist == "---":
            return None, "No lyrics available"

        cover_url = get_album_art(title, artist)
        lyrics = get_lyrics(title, artist)
        return cover_url, lyrics

    def _run_amixer_command(self, args):
        """Helper function to run amixer commands on the default card."""
        # Non specifichiamo una card (-c) per operare sul dispositivo di default,
        # che è esattamente quello che PipeWire ci presenta.
        command = ["amixer"] + args
        try:
            return subprocess.check_output(
                command, stderr=subprocess.DEVNULL, text=True, timeout=3
            )
        except FileNotFoundError:
            print("ERROR: 'amixer' command not found. Is alsa-utils installed?")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error running amixer for control '{self.MIXER_CONTROL}': {e}")
            return None

    def set_volume(self, level_percent):
        """Sets the system volume for the 'Master' control."""
        if not 0 <= level_percent <= 100:
            print(f"ERROR: Invalid volume level {level_percent}.")
            return False

        print(f"AudioManager: Setting volume to {level_percent}% using 'amixer'")
        args = ["sset", self.MIXER_CONTROL, f"{level_percent}%"]
        result = self._run_amixer_command(args)
        return result is not None

    def set_mute(self, muted: bool):
        """Mutes or unmutes the 'Master' control."""
        state = "mute" if muted else "unmute"
        print(f"AudioManager: Setting mute state to {state} using 'amixer'")
        args = ["sset", self.MIXER_CONTROL, state]
        result = self._run_amixer_command(args)
        return result is not None

    def get_volume(self):
        """Gets the current volume percentage for the 'Master' control."""
        args = ["sget", self.MIXER_CONTROL]
        output = self._run_amixer_command(args)
        if output:
            match = re.search(r"\[(\d+)%\]", output)
            if match:
                return int(match.group(1))
        return None

    def get_mute_status(self):
        """Checks if the 'Master' control is muted."""
        args = ["sget", self.MIXER_CONTROL]
        output = self._run_amixer_command(args)
        if output:
            match = re.search(r"\[(on|off)\]", output)
            if match:
                # 'off' in amixer significa mutato
                is_muted = match.group(1) == "off"
                return is_muted
        return None