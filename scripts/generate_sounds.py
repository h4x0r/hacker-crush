#!/usr/bin/env python3
"""Generate Matrix-style cyberpunk sound effects for Hacker Crush."""

import numpy as np
from scipy.io import wavfile
import os

SAMPLE_RATE = 44100


def normalize(audio: np.ndarray) -> np.ndarray:
    """Normalize audio to 16-bit range."""
    audio = audio / np.max(np.abs(audio)) * 0.8
    return (audio * 32767).astype(np.int16)


def envelope(length: int, attack: float = 0.01, decay: float = 0.1,
             sustain: float = 0.7, release: float = 0.2) -> np.ndarray:
    """Create ADSR envelope."""
    total = attack + decay + release
    samples = int(length)
    env = np.zeros(samples)

    attack_samples = int(attack * samples / total)
    decay_samples = int(decay * samples / total)
    release_samples = samples - attack_samples - decay_samples

    # Attack
    env[:attack_samples] = np.linspace(0, 1, attack_samples)
    # Decay
    env[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain, decay_samples)
    # Sustain + Release
    env[attack_samples + decay_samples:] = np.linspace(sustain, 0, release_samples)

    return env


def freq_sweep(duration: float, start_freq: float, end_freq: float) -> np.ndarray:
    """Create frequency sweep (chirp)."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    freq = np.linspace(start_freq, end_freq, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    return np.sin(phase)


def digital_noise(duration: float, intensity: float = 0.3) -> np.ndarray:
    """Create digital-sounding noise."""
    samples = int(SAMPLE_RATE * duration)
    # Quantized noise for digital feel
    noise = np.random.random(samples) * 2 - 1
    # Bitcrush effect
    bits = 4
    noise = np.round(noise * (2**bits)) / (2**bits)
    return noise * intensity


def generate_swap():
    """Quick digital data transfer whoosh."""
    duration = 0.15
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Fast frequency sweep (high to low)
    sweep = freq_sweep(duration, 2000, 400)

    # Add digital artifacts
    digital = digital_noise(duration, 0.2)

    # Quick envelope
    env = envelope(len(t), attack=0.01, decay=0.05, sustain=0.3, release=0.1)

    audio = (sweep * 0.7 + digital * 0.3) * env
    return normalize(audio)


def generate_match():
    """Binary beep sequence - code compiling."""
    duration = 0.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Three quick beeps at different frequencies
    audio = np.zeros(len(t))
    beep_len = len(t) // 4

    freqs = [880, 1100, 1320]  # Rising sequence
    for i, freq in enumerate(freqs):
        start = i * beep_len
        end = start + beep_len
        if end <= len(t):
            beep_t = np.linspace(0, beep_len / SAMPLE_RATE, beep_len)
            beep = np.sin(2 * np.pi * freq * beep_t)
            beep *= np.exp(-beep_t * 20)  # Quick decay
            audio[start:end] += beep

    # Add subtle digital texture
    audio += digital_noise(duration, 0.1)

    return normalize(audio)


def generate_match_big():
    """Successful hack confirmation - deeper, resonant."""
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Base tone with harmonics
    base_freq = 220
    audio = np.sin(2 * np.pi * base_freq * t) * 0.5
    audio += np.sin(2 * np.pi * base_freq * 2 * t) * 0.3
    audio += np.sin(2 * np.pi * base_freq * 3 * t) * 0.2

    # Rising sweep overlay
    sweep = freq_sweep(duration, 400, 1200) * 0.4

    # Envelope
    env = envelope(len(t), attack=0.02, decay=0.1, sustain=0.5, release=0.3)

    audio = (audio + sweep) * env
    audio += digital_noise(duration, 0.15)

    return normalize(audio)


def generate_striped():
    """Scanning line sweep - laser sound."""
    duration = 0.25
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Sharp sweep
    sweep = freq_sweep(duration, 300, 2500)

    # Add harmonic for "laser" quality
    sweep2 = freq_sweep(duration, 600, 5000) * 0.3

    # Envelope with sharp attack
    env = envelope(len(t), attack=0.005, decay=0.05, sustain=0.4, release=0.3)

    audio = (sweep + sweep2) * env
    return normalize(audio)


def generate_wrapped():
    """Data decompression burst - expanding pulse."""
    duration = 0.3
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Expanding frequency (low to high burst)
    sweep = freq_sweep(duration, 150, 800)

    # Pulse modulation
    pulse_freq = 30
    pulse = (np.sin(2 * np.pi * pulse_freq * t) > 0).astype(float)

    # Impact sound
    impact = np.exp(-t * 15) * np.sin(2 * np.pi * 100 * t)

    # Envelope
    env = envelope(len(t), attack=0.01, decay=0.15, sustain=0.3, release=0.2)

    audio = (sweep * pulse * 0.5 + impact * 0.5 + digital_noise(duration, 0.2)) * env
    return normalize(audio)


def generate_color_bomb():
    """System breach cascade - layered digital explosion."""
    duration = 0.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Multiple sweeps cascading
    audio = np.zeros(len(t))

    # Main impact
    impact = np.exp(-t * 8) * np.sin(2 * np.pi * 80 * t)
    audio += impact * 0.4

    # Cascading sweeps
    for i, (start_f, end_f) in enumerate([(200, 2000), (400, 3000), (600, 4000)]):
        delay = int(i * 0.03 * SAMPLE_RATE)
        sweep_dur = duration - i * 0.03
        if sweep_dur > 0:
            sweep = freq_sweep(sweep_dur, start_f, end_f)
            sweep *= np.exp(-np.linspace(0, sweep_dur, len(sweep)) * 5)
            audio[delay:delay + len(sweep)] += sweep * 0.3

    # Heavy digital texture
    audio += digital_noise(duration, 0.25)

    # Envelope
    env = envelope(len(t), attack=0.01, decay=0.2, sustain=0.4, release=0.3)
    audio *= env

    return normalize(audio)


def generate_combo():
    """Escalating pitch sequence - system overload."""
    duration = 0.25
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Rising tone sequence
    audio = np.zeros(len(t))
    num_tones = 5
    tone_len = len(t) // num_tones

    base_freq = 440
    for i in range(num_tones):
        freq = base_freq * (1.2 ** i)  # Exponential rise
        start = i * tone_len
        end = min(start + tone_len, len(t))

        tone_t = np.linspace(0, (end - start) / SAMPLE_RATE, end - start)
        tone = np.sin(2 * np.pi * freq * tone_t)
        tone *= np.exp(-tone_t * 15)
        audio[start:end] += tone

    # Add urgency with noise
    audio += digital_noise(duration, 0.15)

    return normalize(audio)


def generate_invalid():
    """Access Denied - sharp rejection buzz."""
    duration = 0.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Harsh buzzing tone
    freq = 180
    audio = np.sign(np.sin(2 * np.pi * freq * t))  # Square wave

    # Add dissonant overtone
    audio += np.sign(np.sin(2 * np.pi * freq * 1.5 * t)) * 0.5

    # Two-tone pattern (like error beep)
    gate = (t < duration / 2).astype(float) * 0.7 + (t >= duration / 2).astype(float) * 1.0
    audio *= gate

    # Quick decay envelope
    env = envelope(len(t), attack=0.005, decay=0.05, sustain=0.8, release=0.1)
    audio *= env * 0.5  # Lower volume - harsh sound

    return normalize(audio)


def generate_game_over():
    """System disconnect - powering down sequence."""
    duration = 1.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Descending tones
    audio = np.zeros(len(t))

    # Main descending sweep
    sweep = freq_sweep(duration, 800, 50)
    audio += sweep * 0.4

    # Layered descending beeps
    num_beeps = 6
    beep_len = len(t) // num_beeps

    for i in range(num_beeps):
        freq = 600 * (0.7 ** i)  # Descending
        start = i * beep_len
        end = min(start + beep_len, len(t))

        beep_t = np.linspace(0, (end - start) / SAMPLE_RATE, end - start)
        beep = np.sin(2 * np.pi * freq * beep_t)
        beep *= np.exp(-beep_t * 8)
        audio[start:end] += beep * 0.5

    # Fading digital noise
    noise = digital_noise(duration, 0.3)
    noise *= np.linspace(1, 0, len(t))
    audio += noise

    # Long fadeout envelope
    env = envelope(len(t), attack=0.01, decay=0.1, sustain=0.6, release=0.5)
    audio *= env

    return normalize(audio)


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

    print("Generating Matrix-style cyberpunk sounds...")
    for name, generator in sounds.items():
        audio = generator()
        filepath = os.path.join(output_dir, f"{name}.wav")
        wavfile.write(filepath, SAMPLE_RATE, audio)
        print(f"  Generated: {name}.wav")

    print("\nDone! All sounds saved to assets/sounds/")


if __name__ == "__main__":
    main()
