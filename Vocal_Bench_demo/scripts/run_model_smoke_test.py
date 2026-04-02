#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import requests


API_BASE = "http://127.0.0.1:28888"
TTS_ENDPOINT = f"{API_BASE}/api/tts"
VC_ENDPOINT = f"{API_BASE}/api/vc"
INPUT_AUDIO = Path("/home/torfqy/data/Vocal_Bench_demo/demo_assets/original.wav")
OUT_DIR = Path("/home/torfqy/data/Vocal_Bench_demo/tmp_smoke")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TTS_MODELS = ["XTTS", "E2", "Vocus", "F5", "GPTSoVITS"]
VC_MODELS = ["GPTSoVITS_VC", "SeedVC"]
GEN_TEXT = "The reality is that the richest people on the planet do not pay their fair share in taxes."


def run_tts(model: str) -> dict:
    with INPUT_AUDIO.open("rb") as audio_file:
        files = {"ref_audio": (INPUT_AUDIO.name, audio_file, "audio/wav")}
        data = {"model_name": model, "gen_text": GEN_TEXT}
        response = requests.post(TTS_ENDPOINT, data=data, files=files, timeout=600)

    result = {
        "model": model,
        "task": "tts",
        "status_code": response.status_code,
    }
    if response.status_code == 200:
        out_path = OUT_DIR / f"{model}.wav"
        out_path.write_bytes(response.content)
        result["ok"] = True
        result["output_path"] = str(out_path)
        result["size"] = out_path.stat().st_size
    else:
        result["ok"] = False
        result["error"] = response.text[:500]
    return result


def run_vc(model: str) -> dict:
    with INPUT_AUDIO.open("rb") as ref_file, INPUT_AUDIO.open("rb") as target_file:
        files = {
            "ref_audio": (INPUT_AUDIO.name, ref_file, "audio/wav"),
            "target_audio": (INPUT_AUDIO.name, target_file, "audio/wav"),
        }
        data = {"model_name": model}
        response = requests.post(VC_ENDPOINT, data=data, files=files, timeout=600)

    result = {
        "model": model,
        "task": "vc",
        "status_code": response.status_code,
    }
    if response.status_code == 200:
        out_path = OUT_DIR / f"{model}.wav"
        out_path.write_bytes(response.content)
        result["ok"] = True
        result["output_path"] = str(out_path)
        result["size"] = out_path.stat().st_size
    else:
        result["ok"] = False
        result["error"] = response.text[:500]
    return result


def main() -> None:
    results = []
    for model in TTS_MODELS:
        print(f"[TTS] {model}", flush=True)
        results.append(run_tts(model))
    for model in VC_MODELS:
        print(f"[VC] {model}", flush=True)
        results.append(run_vc(model))

    report_path = OUT_DIR / "report.json"
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"report saved to {report_path}")


if __name__ == "__main__":
    main()
