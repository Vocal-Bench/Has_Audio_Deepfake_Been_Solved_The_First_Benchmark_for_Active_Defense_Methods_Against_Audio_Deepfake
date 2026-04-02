from __future__ import annotations

from pathlib import Path
from typing import Optional

import librosa


def transcribe(path: str | Path, model_name: str = "tiny", device: str = "auto") -> Optional[str]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:
        raise RuntimeError("faster-whisper is required for ASR-backed WER/CER evaluation") from exc

    if device == "auto":
        try:
            import torch  # type: ignore
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"

    model = WhisperModel(model_name, device=device, compute_type="float16" if device == "cuda" else "int8")
    audio, sr = librosa.load(str(path), sr=16000, mono=True)
    segments, _ = model.transcribe(audio, sampling_rate=sr, vad_filter=False, beam_size=1, best_of=1)
    texts = [(seg.text or "").strip() for seg in segments]
    output = " ".join([t for t in texts if t]).strip()
    return output or None
