#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

import requests


API = "http://127.0.0.1:28888/api/tts"
OUT_ROOT = Path("/home/torfqy/data/Vocal_Bench_demo/demo_assets")
REPORT = OUT_ROOT / "generation_report.json"
GROUPS = ["Original", "AntiFake", "Attack-VC", "ClearMask", "SampleMask", "SafeSpeech", "VoiceGuard"]
VARIANTS = ["original", "denoised", "downsampled_8k", "compressed_mp3"]
GEN_TEXT = "This is a demo."


def read_report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}


def write_report(report: dict) -> None:
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    report = read_report()
    for group in GROUPS:
        for variant in VARIANTS:
            ref_audio = OUT_ROOT / group / variant / "input.wav"
            out_path = OUT_ROOT / group / variant / "Vocus.wav"
            key = f"{group}|{variant}|Vocus"
            print(f"run {key}", flush=True)
            started = time.time()
            try:
                with ref_audio.open("rb") as f:
                    resp = requests.post(
                        API,
                        data={"model_name": "Vocus", "gen_text": GEN_TEXT},
                        files={"ref_audio": (ref_audio.name, f, "audio/wav")},
                        timeout=600,
                    )
                if resp.status_code == 200:
                    out_path.write_bytes(resp.content)
                    result = {
                        "ok": True,
                        "status_code": 200,
                        "output_path": str(out_path),
                        "size": out_path.stat().st_size,
                        "elapsed_sec": round(time.time() - started, 2),
                        "gen_text": GEN_TEXT,
                        "rerun": "vocus_only",
                    }
                else:
                    result = {
                        "ok": False,
                        "status_code": resp.status_code,
                        "error": resp.text[:3000],
                        "elapsed_sec": round(time.time() - started, 2),
                        "gen_text": GEN_TEXT,
                        "rerun": "vocus_only",
                    }
            except Exception as exc:
                result = {
                    "ok": False,
                    "status_code": -1,
                    "error": str(exc),
                    "elapsed_sec": round(time.time() - started, 2),
                    "gen_text": GEN_TEXT,
                    "rerun": "vocus_only",
                }
            report[key] = result
            write_report(report)
            print(json.dumps({"key": key, **result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
