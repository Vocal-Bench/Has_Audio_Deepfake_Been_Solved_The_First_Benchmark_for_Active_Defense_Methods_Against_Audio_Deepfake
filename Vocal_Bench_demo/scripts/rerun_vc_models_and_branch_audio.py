#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import requests
import soundfile as sf


API_BASE = "http://127.0.0.1:28888"
VC_ENDPOINT = f"{API_BASE}/api/vc"
OUT_ROOT = Path("/home/torfqy/data/Vocal_Bench_demo/demo_assets")
REPORT_PATH = OUT_ROOT / "generation_report.json"
VOCALBENCH_ROOT = Path("/home/torfqy/data/vocalbench")

GROUPS = ["Original", "AntiFake", "Attack-VC", "ClearMask", "SampleMask", "SafeSpeech", "VoiceGuard"]
VARIANTS = ["original", "denoised", "downsampled_8k", "compressed_mp3"]
VC_MODELS = ["SeedVC", "GPTSoVITS_VC"]
DISPLAY_GROUPS = ["AntiFake", "Attack-VC", "VoiceGuard"]
TASK = "full"
LANG = "english"
SAMPLE = "english_target12.wav"
VC_TARGET = OUT_ROOT / "vc_target.wav"
GEN_TEXT = "This is a demo."


def group_prefix(group: str) -> str:
    return "" if group == "Original" else f"{group}_"


def read_report() -> dict:
    if REPORT_PATH.exists():
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    return {}


def write_report(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def best_energy_window(audio: np.ndarray, sr: int, seconds: float = 6.0) -> np.ndarray:
    win = int(seconds * sr)
    if len(audio) <= win:
        return audio
    hop = max(1, win // 10)
    best_start = 0
    best_score = -1.0
    mono = audio.mean(axis=1) if audio.ndim > 1 else audio
    for start in range(0, len(mono) - win + 1, hop):
        seg = mono[start : start + win]
        score = float(np.mean(seg * seg))
        if score > best_score:
            best_score = score
            best_start = start
    return audio[best_start : best_start + win]


def refresh_display_branch(group: str) -> None:
    prefix = group_prefix(group)
    src = VOCALBENCH_ROOT / f"{group}_VocalBench" / "original" / TASK / LANG / f"{prefix}{SAMPLE}"
    dst = OUT_ROOT / group / "branch.wav"
    audio, sr = sf.read(src, dtype="float32", always_2d=False)
    segment = best_energy_window(audio, sr, 6.0)
    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(dst, segment, sr)
    print(f"branch {group} -> {dst}")


def rerun_one_vc(group: str, variant: str, model: str, report: dict) -> None:
    ref_audio = OUT_ROOT / group / variant / "input.wav"
    out_path = OUT_ROOT / group / variant / f"{model}.wav"
    key = f"{group}|{variant}|{model}"
    start = time.time()
    try:
        with ref_audio.open("rb") as rf, VC_TARGET.open("rb") as tf:
            data = {"model_name": model}
            if model == "GPTSoVITS_VC":
                data["target_text"] = GEN_TEXT
            response = requests.post(
                VC_ENDPOINT,
                data=data,
                files={
                    "ref_audio": (ref_audio.name, rf, "audio/wav"),
                    "target_audio": (VC_TARGET.name, tf, "audio/wav"),
                },
                timeout=600,
            )
        if response.status_code == 200:
            out_path.write_bytes(response.content)
            result = {
                "ok": True,
                "status_code": 200,
                "output_path": str(out_path),
                "size": out_path.stat().st_size,
                "elapsed_sec": round(time.time() - start, 2),
            }
        else:
            result = {
                "ok": False,
                "status_code": response.status_code,
                "error": response.text[:2000],
                "elapsed_sec": round(time.time() - start, 2),
            }
    except Exception as exc:
        result = {
            "ok": False,
            "status_code": -1,
            "error": str(exc),
            "elapsed_sec": round(time.time() - start, 2),
        }
        result["gen_text"] = GEN_TEXT
        report[key] = result
    write_report(report)
    print(json.dumps({"key": key, **result}, ensure_ascii=False), flush=True)


def main() -> None:
    assert VC_TARGET.exists(), f"missing {VC_TARGET}"
    report = read_report()

    for group in DISPLAY_GROUPS:
        refresh_display_branch(group)

    for group in GROUPS:
        for variant in VARIANTS:
            for model in VC_MODELS:
                rerun_one_vc(group, variant, model, report)


if __name__ == "__main__":
    main()
