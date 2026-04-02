from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import librosa
import numpy as np


def asv_cosine(ref_path: str | Path, test_path: str | Path, source: str = "speechbrain/spkrec-ecapa-voxceleb", device: str = "auto") -> Optional[float]:
    try:
        from speechbrain.pretrained import EncoderClassifier  # type: ignore
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("speechbrain and torch are required for ASV evaluation") from exc

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    classifier = EncoderClassifier.from_hparams(source=source, run_opts={"device": device})
    ref, _ = librosa.load(str(ref_path), sr=16000, mono=True)
    test, _ = librosa.load(str(test_path), sr=16000, mono=True)
    ref_t = torch.tensor(ref, dtype=torch.float32).unsqueeze(0)
    test_t = torch.tensor(test, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        ref_emb = classifier.encode_batch(ref_t).squeeze().cpu().numpy().astype(np.float32)
        test_emb = classifier.encode_batch(test_t).squeeze().cpu().numpy().astype(np.float32)
    denom = (np.linalg.norm(ref_emb) + 1e-12) * (np.linalg.norm(test_emb) + 1e-12)
    return float(np.dot(ref_emb, test_emb) / denom)


def eer_from_scores(labels: Iterable[int], scores: Iterable[float]) -> float:
    labels = list(labels)
    scores = list(scores)
    if not labels or len(labels) != len(scores):
        raise RuntimeError("labels and scores must have the same non-zero length")

    thresholds = sorted(set(scores))
    best = 1.0
    for thr in thresholds:
        fp = fn = tp = tn = 0
        for label, score in zip(labels, scores):
            pred = 1 if score >= thr else 0
            if label == 1 and pred == 1:
                tp += 1
            elif label == 1 and pred == 0:
                fn += 1
            elif label == 0 and pred == 1:
                fp += 1
            else:
                tn += 1
        far = fp / (fp + tn) if (fp + tn) else 0.0
        frr = fn / (fn + tp) if (fn + tp) else 0.0
        best = min(best, abs(far - frr))
    return float(best)
