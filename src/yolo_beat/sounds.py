"""Step 3: drum sounds synthesised with numpy (no sample files) and played via pygame.

Synthesis functions are pure (return float32 arrays in [-1, 1]) so they can be tested
without an audio device; DrumKit wraps pygame.mixer for playback.
"""
from __future__ import annotations

import os

import numpy as np

SAMPLE_RATE = 44100
_rng = np.random.default_rng(0)  # fixed seed: same sound every run


def _t(duration: float) -> np.ndarray:
    return np.arange(int(SAMPLE_RATE * duration), dtype=np.float32) / SAMPLE_RATE


def _env(t: np.ndarray, decay: float) -> np.ndarray:
    """Exponential decay envelope with a 2 ms fade-in to avoid clicks."""
    attack = np.clip(t / 0.002, 0, 1)
    return attack * np.exp(-t / decay)


def _noise(n: int) -> np.ndarray:
    return _rng.uniform(-1, 1, n).astype(np.float32)


def _highpass(x: np.ndarray) -> np.ndarray:
    """Crude high-pass: first difference (removes low end, brightens noise)."""
    return np.diff(x, prepend=x[:1])


def _sweep(t: np.ndarray, f_start: float, f_end: float, k: float) -> np.ndarray:
    """Sine whose pitch falls exponentially from f_start to f_end."""
    freq = f_end + (f_start - f_end) * np.exp(-t * k)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    return np.sin(phase)


def _normalise(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    return (x / np.abs(x).max() * peak).astype(np.float32)


def kick() -> np.ndarray:
    t = _t(0.45)
    return _normalise(_sweep(t, 150, 45, 30) * _env(t, 0.12))


def snare() -> np.ndarray:
    t = _t(0.25)
    body = np.sin(2 * np.pi * 185 * t) * _env(t, 0.04)
    rattle = _highpass(_noise(len(t))) * _env(t, 0.06)
    return _normalise(0.5 * body + rattle)


def hihat() -> np.ndarray:
    t = _t(0.08)
    return _normalise(_highpass(_highpass(_noise(len(t)))) * _env(t, 0.015), 0.6)


def tom() -> np.ndarray:
    t = _t(0.4)
    return _normalise(_sweep(t, 140, 95, 12) * _env(t, 0.12))


def ride() -> np.ndarray:
    t = _t(0.9)
    metal = sum(np.sin(2 * np.pi * f * t) for f in (520, 845, 1310, 2110, 3370))
    shimmer = _highpass(_noise(len(t))) * 0.6
    return _normalise((0.25 * metal + shimmer) * _env(t, 0.2), 0.6)


def crash() -> np.ndarray:
    t = _t(1.4)
    return _normalise(_highpass(_noise(len(t))) * _env(t, 0.3), 0.7)


SYNTHS = {"kick": kick, "snare": snare, "hihat": hihat, "tom": tom, "ride": ride, "crash": crash}


def synth_all() -> dict[str, np.ndarray]:
    return {name: fn() for name, fn in SYNTHS.items()}


def to_int16(x: np.ndarray, channels: int) -> np.ndarray:
    a = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    if channels == 1:
        return a
    return np.ascontiguousarray(np.repeat(a[:, None], channels, axis=1))


class DrumKit:
    """Loads all synthesised sounds into pygame and plays them by pad name."""

    def __init__(self, buffer: int = 256) -> None:
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame

        self._pygame = pygame
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, buffer)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)  # let hits overlap
        _, _, channels = pygame.mixer.get_init()
        self.sounds = {
            name: pygame.sndarray.make_sound(to_int16(s, channels))
            for name, s in synth_all().items()
        }

    def play(self, name: str) -> None:
        snd = self.sounds.get(name)
        if snd is not None:
            snd.play()

    def close(self) -> None:
        self._pygame.mixer.quit()
