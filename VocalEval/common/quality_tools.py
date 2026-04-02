from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path

from .audio_tools import load_audio


def stoi_score(ref_path: str | Path, test_path: str | Path) -> float:
    try:
        from pystoi import stoi  # type: ignore
    except Exception as exc:
        raise RuntimeError("pystoi is required for STOI evaluation") from exc
    ref = load_audio(ref_path, sr=16000)
    test = load_audio(test_path, sr=16000)
    return float(stoi(ref, test, 16000, extended=False))


def pesq_score(ref_path: str | Path, test_path: str | Path, mode: str = "wb") -> float:
    try:
        from pesq import pesq  # type: ignore
    except Exception as exc:
        raise RuntimeError("pesq is required for PESQ evaluation") from exc
    ref = load_audio(ref_path, sr=16000)
    test = load_audio(test_path, sr=16000)
    return float(pesq(16000, ref, test, mode))


def visqol_score(ref_path: str | Path, test_path: str | Path, visqol_bin: str | Path, model_path: str | Path) -> float:
    visqol_bin = Path(visqol_bin)
    model_path = Path(model_path)
    if not visqol_bin.exists() or not model_path.exists():
        raise RuntimeError("valid ViSQOL binary and model path are required")

    with tempfile.TemporaryDirectory(prefix="visqol_metric_") as td_s:
        td = Path(td_s)
        ref_wav = td / "ref.wav"
        deg_wav = td / "deg.wav"
        batch_csv = td / "batch.csv"
        result_csv = td / "results.csv"

        for src, dst in ((ref_path, ref_wav), (test_path, deg_wav)):
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(dst)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        with batch_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["reference", "degraded"])
            writer.writerow([str(ref_wav), str(deg_wav)])

        subprocess.run(
            [
                str(visqol_bin),
                "--batch_input_csv",
                str(batch_csv),
                "--results_csv",
                str(result_csv),
                "--use_speech_mode",
                "--similarity_to_quality_model",
                str(model_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(visqol_bin.parent.parent.parent),
        )

        with result_csv.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise RuntimeError("ViSQOL returned no rows")
        return float(rows[0]["moslqo"])
