from __future__ import annotations

import math
from pathlib import Path

import librosa
import numpy as np

SR = 16000


def load_audio(path: str | Path, sr: int = SR) -> np.ndarray:
    audio, _ = librosa.load(str(path), sr=sr, mono=True)
    if audio is None:
        return np.zeros(1, dtype=np.float32)
    return audio.astype(np.float32)


def align_audio(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = min(a.size, b.size)
    if n <= 0:
        return np.zeros(1, dtype=np.float32), np.zeros(1, dtype=np.float32)
    return a[:n], b[:n]


def snr_db_from_arrays(ref: np.ndarray, test: np.ndarray) -> float:
    ref, test = align_audio(ref, test)
    signal_power = float(np.mean(np.square(ref)))
    noise_power = float(np.mean(np.square(ref - test)))
    if noise_power < 1e-12:
        return 100.0
    if signal_power < 1e-12:
        return -100.0
    return float(10.0 * np.log10(signal_power / noise_power))


def snr_db_from_files(ref_path: str | Path, test_path: str | Path, sr: int = SR) -> float:
    ref = load_audio(ref_path, sr=sr)
    test = load_audio(test_path, sr=sr)
    return snr_db_from_arrays(ref, test)


def json_ready(value: float | int | None) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
