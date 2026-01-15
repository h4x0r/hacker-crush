"""Audio manager for sound effects and music."""

import os
import pygame


class AudioManager:
    """Manages game audio - sound effects and background music."""

    def __init__(self):
        """Initialize audio system."""
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self.sounds = {}
        self.music_playing = False
        self.sfx_enabled = True
        self.music_enabled = True
        self.sfx_volume = 0.5
        self.music_volume = 0.3

        self._load_sounds()

    def _get_asset_dir(self, subdir: str) -> str:
        """Get asset directory path (works for both local and web)."""
        base = os.path.dirname(__file__)
        # Try direct subdir first (for pygbag web builds: src/images, src/sounds)
        direct = os.path.join(base, subdir)
        if os.path.exists(direct):
            return direct
        # Try assets/subdir (for pygbag if packaged that way)
        assets_sub = os.path.join(base, "assets", subdir)
        if os.path.exists(assets_sub):
            return assets_sub
        # Fallback to ../assets (for local development)
        return os.path.join(base, "..", "assets", subdir)

    def _load_sounds(self) -> None:
        """Load all sound effects."""
        sound_dir = self._get_asset_dir("sounds")

        sound_files = {
            "swap": "swap.wav",
            "match": "match.wav",
            "match_big": "match_big.wav",
            "striped": "striped.wav",
            "wrapped": "wrapped.wav",
            "color_bomb": "color_bomb.wav",
            "combo": "combo.wav",
            "invalid": "invalid.wav",
            "game_over": "game_over.wav",
        }

        for name, filename in sound_files.items():
            path = os.path.join(sound_dir, filename)
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self.sfx_volume)
                self.sounds[name] = sound
            except Exception as e:
                print(f"Warning: Could not load sound {name}: {e}")
                self.sounds[name] = None

    def play(self, sound_name: str) -> None:
        """Play a sound effect."""
        if not self.sfx_enabled:
            return

        sound = self.sounds.get(sound_name)
        if sound:
            sound.play()

    def play_match(self, candy_count: int) -> None:
        """Play layered match sounds - more candies = more exciting layered audio."""
        if not self.sfx_enabled:
            return

        # Scale volume with match size
        volume_multiplier = 1.0 + max(0, (candy_count - 3) * 0.15)
        volume_multiplier = min(volume_multiplier, 1.5)

        if candy_count >= 7:
            # MASSIVE match - layer ALL sounds for epic effect
            for sound_name in ["match_big", "combo", "striped"]:
                sound = self.sounds.get(sound_name)
                if sound:
                    sound.set_volume(min(1.0, self.sfx_volume * volume_multiplier))
                    sound.play()
                    sound.set_volume(self.sfx_volume)

        elif candy_count >= 6:
            # Huge match - layer match_big + combo
            for sound_name in ["match_big", "combo"]:
                sound = self.sounds.get(sound_name)
                if sound:
                    sound.set_volume(min(1.0, self.sfx_volume * volume_multiplier))
                    sound.play()
                    sound.set_volume(self.sfx_volume)

        elif candy_count >= 5:
            # Big match - match_big with boost
            sound = self.sounds.get("match_big")
            if sound:
                sound.set_volume(min(1.0, self.sfx_volume * volume_multiplier))
                sound.play()
                sound.set_volume(self.sfx_volume)

        elif candy_count >= 4:
            # Good match - standard match + quiet combo undertone
            sound = self.sounds.get("match")
            if sound:
                sound.set_volume(min(1.0, self.sfx_volume * volume_multiplier))
                sound.play()
                sound.set_volume(self.sfx_volume)
            combo = self.sounds.get("combo")
            if combo:
                combo.set_volume(self.sfx_volume * 0.3)
                combo.play()
                combo.set_volume(self.sfx_volume)

        else:
            # Standard 3-match
            sound = self.sounds.get("match")
            if sound:
                sound.set_volume(self.sfx_volume)
                sound.play()

    def play_special(self, special_type: str) -> None:
        """Play sound for special candy activation."""
        sound_map = {
            "striped": "striped",
            "wrapped": "wrapped",
            "color_bomb": "color_bomb",
        }
        sound_name = sound_map.get(special_type, "match")
        self.play(sound_name)

    def play_cascade(self, cascade_level: int) -> None:
        """Play combo sound for cascades."""
        if cascade_level > 1:
            self.play("combo")

    def start_music(self) -> None:
        """Start background music loop."""
        if not self.music_enabled:
            return

        music_dir = self._get_asset_dir("music")
        music_file = os.path.join(music_dir, "background.ogg")

        if os.path.exists(music_file):
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # Loop forever
                self.music_playing = True
            except Exception as e:
                print(f"Warning: Could not play music: {e}")

    def stop_music(self) -> None:
        """Stop background music."""
        pygame.mixer.music.stop()
        self.music_playing = False

    def toggle_sfx(self) -> bool:
        """Toggle sound effects on/off."""
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled

    def toggle_music(self) -> bool:
        """Toggle music on/off."""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            self.start_music()
        else:
            self.stop_music()
        return self.music_enabled

    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.sfx_volume)

    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def cleanup(self) -> None:
        """Clean up audio resources."""
        pygame.mixer.quit()
