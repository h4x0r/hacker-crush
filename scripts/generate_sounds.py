#!/usr/bin/env python3
"""Generate moody Matrix-style cyberpunk sound effects for Hacker Crush.

Design philosophy: Dark, atmospheric, low-frequency, ominous.
NOT arcade beeps - think slow digital ambience with reverb.
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import os

SAMPLE_RATE = 44100


def normalize(audio: np.ndarray, level: float = 0.7) -> np.ndarray:
    """Normalize audio to 16-bit range."""
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio)) * level
    return (audio * 32767).astype(np.int16)


def lowpass_filter(audio: np.ndarray, cutoff: float = 2000) -> np.ndarray:
    """Apply lowpass filter for darker tone."""
    nyq = SAMPLE_RATE / 2
    b, a = butter(2, cutoff / nyq, btype='low')
    return lfilter(b, a, audio)


def add_reverb(audio: np.ndarray, decay: float = 0.4, delays: int = 5) -> np.ndarray:
    """Add simple reverb effect for atmosphere."""
    result = audio.copy().astype(float)
    for i in range(1, delays + 1):
        delay_samples = int(0.03 * i * SAMPLE_RATE)  # 30ms increments
        delayed = np.zeros(len(audio) + delay_samples)
        delayed[delay_samples:delay_samples + len(audio)] = audio * (decay ** i)
        result = np.pad(result, (0, max(0, len(delayed) - len(result))))
        delayed = np.pad(delayed, (0, max(0, len(result) - len(delayed))))
        result += delayed[:len(result)]
    return result


def dark_drone(duration: float, base_freq: float = 60) -> np.ndarray:
    """Create dark droning bass tone."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    # Low fundamental with subtle movement
    lfo = 1 + 0.1 * np.sin(2 * np.pi * 0.5 * t)  # Slow wobble
    audio = np.sin(2 * np.pi * base_freq * lfo * t)
    # Add subtle harmonics
    audio += 0.3 * np.sin(2 * np.pi * base_freq * 2 * t)
    audio += 0.1 * np.sin(2 * np.pi * base_freq * 3 * t)
    return audio


def digital_texture(duration: float, intensity: float = 0.1) -> np.ndarray:
    """Subtle digital grain texture."""
    samples = int(SAMPLE_RATE * duration)
    # Very subtle, filtered noise
    noise = np.random.random(samples) * 2 - 1
    noise = lowpass_filter(noise, 800)
    return noise * intensity


def slow_sweep(duration: float, start_freq: float, end_freq: float) -> np.ndarray:
    """Slow, dark frequency sweep."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    # Exponential sweep for more natural feel
    freq = start_freq * (end_freq / start_freq) ** (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    return np.sin(phase)


def fade_envelope(length: int, fade_in: float = 0.1, fade_out: float = 0.3) -> np.ndarray:
    """Simple fade in/out envelope."""
    env = np.ones(length)
    fade_in_samples = int(fade_in * length)
    fade_out_samples = int(fade_out * length)

    env[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)
    env[-fade_out_samples:] = np.linspace(1, 0, fade_out_samples)
    return env


def generate_swap():
    """Dark whoosh - like data passing through the Matrix."""
    duration = 0.25
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Low filtered sweep
    sweep = slow_sweep(duration, 150, 80)
    sweep = lowpass_filter(sweep, 400)

    # Subtle texture
    texture = digital_texture(duration, 0.05)

    # Smooth envelope
    env = fade_envelope(len(t), 0.05, 0.4)

    audio = (sweep * 0.8 + texture) * env
    audio = add_reverb(audio, 0.3, 3)

    return normalize(audio[:int(SAMPLE_RATE * 0.3)])


def generate_match():
    """Subtle confirmation - like code accepting input."""
    duration = 0.3
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Soft tone cluster (not beepy)
    freq = 220
    audio = np.sin(2 * np.pi * freq * t) * 0.5
    audio += np.sin(2 * np.pi * freq * 1.5 * t) * 0.3  # Fifth
    audio += np.sin(2 * np.pi * freq * 2 * t) * 0.2

    # Filter for darkness
    audio = lowpass_filter(audio, 600)

    # Gentle envelope
    env = fade_envelope(len(t), 0.02, 0.5)
    audio *= env

    audio = add_reverb(audio, 0.4, 4)
    return normalize(audio[:int(SAMPLE_RATE * 0.4)])


def generate_match_big():
    """Deeper resonance - successful breach."""
    duration = 0.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Deep bass hit with slow release
    bass = dark_drone(duration, 55)

    # Subtle rising undertone
    rise = slow_sweep(duration, 80, 200) * 0.3
    rise = lowpass_filter(rise, 500)

    audio = bass * 0.6 + rise * 0.4

    # Long decay envelope
    env = fade_envelope(len(t), 0.01, 0.6)
    audio *= env

    audio = add_reverb(audio, 0.5, 5)
    return normalize(audio[:int(SAMPLE_RATE * 0.7)])


def generate_striped():
    """Line activation - scanning through the Matrix."""
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Filtered sweep with resonance
    sweep = slow_sweep(duration, 100, 400)
    sweep = lowpass_filter(sweep, 800)

    # Add subtle pulsing
    pulse = 1 + 0.2 * np.sin(2 * np.pi * 8 * t)
    audio = sweep * pulse

    # Texture layer
    audio += digital_texture(duration, 0.08)

    env = fade_envelope(len(t), 0.02, 0.4)
    audio *= env

    audio = add_reverb(audio, 0.4, 4)
    return normalize(audio[:int(SAMPLE_RATE * 0.45)])


def generate_wrapped():
    """Implosion/explosion - wrapped candy detonation."""
    duration = 0.4
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Deep thump
    thump = np.exp(-t * 8) * np.sin(2 * np.pi * 50 * t)

    # Expanding low rumble
    rumble = dark_drone(duration, 40)
    rumble *= np.linspace(0.2, 1, len(t)) * np.exp(-t * 3)

    audio = thump * 0.6 + rumble * 0.4
    audio = lowpass_filter(audio, 500)

    env = fade_envelope(len(t), 0.01, 0.5)
    audio *= env

    audio = add_reverb(audio, 0.5, 5)
    return normalize(audio[:int(SAMPLE_RATE * 0.55)])


def generate_color_bomb():
    """System breach - ominous cascade."""
    duration = 0.7
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Deep impact
    impact = np.exp(-t * 5) * np.sin(2 * np.pi * 35 * t)

    # Slow descending sweep (ominous)
    sweep = slow_sweep(duration, 300, 50)
    sweep = lowpass_filter(sweep, 600)

    # Layered drones
    drone = dark_drone(duration, 45) * np.exp(-t * 2)

    audio = impact * 0.4 + sweep * 0.3 + drone * 0.3
    audio += digital_texture(duration, 0.1)

    env = fade_envelope(len(t), 0.01, 0.4)
    audio *= env

    audio = add_reverb(audio, 0.5, 6)
    return normalize(audio[:int(SAMPLE_RATE * 0.9)])


def generate_combo():
    """Building intensity - cascading through layers."""
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Rising filtered tone
    sweep = slow_sweep(duration, 80, 250)
    sweep = lowpass_filter(sweep, 700)

    # Intensity builds
    intensity = np.linspace(0.3, 1, len(t))
    audio = sweep * intensity

    # Add subtle urgency without being shrill
    pulse = 1 + 0.15 * np.sin(2 * np.pi * 6 * t)
    audio *= pulse

    env = fade_envelope(len(t), 0.02, 0.3)
    audio *= env

    audio = add_reverb(audio, 0.4, 4)
    return normalize(audio[:int(SAMPLE_RATE * 0.45)])


def generate_invalid():
    """Rejection - dark denial tone."""
    duration = 0.25
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Low dissonant tone (not harsh buzz)
    freq = 80
    audio = np.sin(2 * np.pi * freq * t)
    # Dissonant interval
    audio += np.sin(2 * np.pi * freq * 1.06 * t) * 0.7  # Minor second

    # Filter heavily
    audio = lowpass_filter(audio, 300)

    # Two pulses
    pulse1 = np.exp(-((t - 0.05) ** 2) / 0.002)
    pulse2 = np.exp(-((t - 0.15) ** 2) / 0.002)
    audio *= (pulse1 + pulse2 * 0.7)

    audio = add_reverb(audio, 0.3, 3)
    return normalize(audio[:int(SAMPLE_RATE * 0.35)], 0.6)


def generate_game_over():
    """System shutdown - slow, ominous fadeout."""
    duration = 1.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Descending drone
    freq_start, freq_end = 120, 30
    freq = freq_start * (freq_end / freq_start) ** (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    drone = np.sin(phase)

    # Add dark harmonics
    drone += 0.3 * np.sin(phase * 2)
    drone = lowpass_filter(drone, 400)

    # Pulsing that slows down
    pulse_freq = 4 * (1 - t / duration * 0.8)  # Slowing pulse
    pulse = 0.7 + 0.3 * np.sin(2 * np.pi * np.cumsum(pulse_freq) / SAMPLE_RATE)

    audio = drone * pulse

    # Add texture that fades
    texture = digital_texture(duration, 0.15)
    texture *= np.linspace(1, 0, len(t))
    audio += texture

    # Long fadeout
    env = fade_envelope(len(t), 0.02, 0.7)
    audio *= env

    audio = add_reverb(audio, 0.5, 6)
    return normalize(audio[:int(SAMPLE_RATE * 2.0)])


def main():
    """Generate all sound effects."""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
    os.makedirs(output_dir, exist_ok=True)

    sounds = {
        "swap": generate_swap,
        "match": generate_match,
        "match_big": generate_match_big,
        "striped": generate_striped,
        "wrapped": generate_wrapped,
        "color_bomb": generate_color_bomb,
        "combo": generate_combo,
        "invalid": generate_invalid,
        "game_over": generate_game_over,
    }

    print("Generating moody Matrix-style sounds...")
    print("(Dark, atmospheric, low-frequency, ominous)\n")

    for name, generator in sounds.items():
        audio = generator()
        filepath = os.path.join(output_dir, f"{name}.wav")
        wavfile.write(filepath, SAMPLE_RATE, audio)
        duration_ms = len(audio) / SAMPLE_RATE * 1000
        print(f"  {name}.wav ({duration_ms:.0f}ms)")

    print("\nDone! Sounds are darker and more atmospheric now.")


if __name__ == "__main__":
    main()
