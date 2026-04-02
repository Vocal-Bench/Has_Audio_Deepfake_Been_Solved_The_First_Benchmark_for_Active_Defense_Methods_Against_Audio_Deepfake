#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import requests


API_BASE = "http://127.0.0.1:28888"
TTS_ENDPOINT = f"{API_BASE}/api/tts"
VC_ENDPOINT = f"{API_BASE}/api/vc"
OUT_ROOT = Path("/home/torfqy/data/Vocal_Bench_demo/demo_assets")
REPORT_PATH = OUT_ROOT / "generation_report.json"

GROUPS = ["Original", "AntiFake", "Attack-VC", "ClearMask", "SampleMask", "SafeSpeech", "VoiceGuard"]
VARIANTS = ["original", "denoised", "downsampled_8k", "compressed_mp3"]
TTS_MODELS = ["E2", "F5", "GPTSoVITS", "Vocus", "XTTS"]
VC_MODELS = ["SeedVC", "GPTSoVITS_VC"]

REF_TEXT = "The reality is that the richest people on the planet do not pay their fair share in taxes."
GEN_TEXT = "This is a demo."
VC_TARGET_AUDIO = OUT_ROOT / "vc_target.wav"
VC_TARGET_META = OUT_ROOT / "vc_target.json"


def read_report() -> dict:
    if REPORT_PATH.exists():
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    return {}


def write_report(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def is_cached_ok(report: dict, key: str, out_path: Path) -> bool:
    item = report.get(key)
    return (
        item is not None
        and item.get("ok") is True
        and item.get("gen_text") == GEN_TEXT
        and out_path.exists()
        and out_path.stat().st_size > 20000
    )


def run_tts(model: str, ref_audio: Path, out_path: Path) -> dict:
    with ref_audio.open("rb") as f:
        data = {"model_name": model, "gen_text": GEN_TEXT}
        if model in {"E2", "F5"}:
            data["ref_text"] = REF_TEXT
        response = requests.post(
            TTS_ENDPOINT,
            data=data,
            files={"ref_audio": (ref_audio.name, f, "audio/wav")},
            timeout=600,
        )
    result = {
        "status_code": response.status_code,
        "ok": response.status_code == 200,
    }
    if response.status_code == 200:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(response.content)
        result["size"] = out_path.stat().st_size
        result["output_path"] = str(out_path)
    else:
        result["error"] = response.text[:2000]
    return result


def run_xtts_direct(ref_audio: Path, out_path: Path) -> dict:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "conda", "run", "-n", "voicekit", "python",
        "/home/torfqy/data/Vocal_Bench_demo/scripts/run_xtts_direct.py",
        "--ref-audio", str(ref_audio),
        "--gen-text", GEN_TEXT,
        "--out-path", str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    start = time.time()
    try:
        while True:
            ret = proc.poll()
            if ret is not None:
                break
            if out_path.exists() and out_path.stat().st_size > 20000:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return {
                    "status_code": 200,
                    "ok": True,
                    "size": out_path.stat().st_size,
                    "output_path": str(out_path),
                }
            if time.time() - start > 900:
                proc.kill()
                raise TimeoutError("XTTS generation timed out")
            time.sleep(5)

        stdout, stderr = proc.communicate()
        if out_path.exists() and out_path.stat().st_size > 20000:
            return {
                "status_code": 200,
                "ok": True,
                "size": out_path.stat().st_size,
                "output_path": str(out_path),
            }
        return {
            "status_code": ret,
            "ok": False,
            "error": (stdout + "\n" + stderr)[:4000],
        }
    finally:
        if proc.poll() is None:
            proc.kill()


def run_vc(model: str, ref_audio: Path, target_audio: Path, out_path: Path) -> dict:
    with ref_audio.open("rb") as rf, target_audio.open("rb") as tf:
        data = {"model_name": model}
        if model == "GPTSoVITS_VC":
            data["target_text"] = GEN_TEXT
        response = requests.post(
            VC_ENDPOINT,
            data=data,
            files={
                "ref_audio": (ref_audio.name, rf, "audio/wav"),
                "target_audio": (target_audio.name, tf, "audio/wav"),
            },
            timeout=600,
        )
    result = {
        "status_code": response.status_code,
        "ok": response.status_code == 200,
    }
    if response.status_code == 200:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(response.content)
        result["size"] = out_path.stat().st_size
        result["output_path"] = str(out_path)
    else:
        result["error"] = response.text[:2000]
    return result


def ensure_vc_target(source_audio: Path) -> Path:
    if VC_TARGET_AUDIO.exists() and VC_TARGET_META.exists():
        meta = json.loads(VC_TARGET_META.read_text(encoding="utf-8"))
        if meta.get("gen_text") == GEN_TEXT and VC_TARGET_AUDIO.stat().st_size > 1000:
            return VC_TARGET_AUDIO
    # Prefer a longer canonical target for VC. XTTS produces a longer and more
    # stable prompt sentence than E2/F5 for the same text on this machine.
    xtts_result = run_xtts_direct(source_audio, VC_TARGET_AUDIO)
    if xtts_result.get("ok"):
        VC_TARGET_META.write_text(json.dumps({"gen_text": GEN_TEXT, "source_model": "XTTS"}, ensure_ascii=False), encoding="utf-8")
        return VC_TARGET_AUDIO
    e2_result = run_tts("E2", source_audio, VC_TARGET_AUDIO)
    if not e2_result.get("ok"):
        raise RuntimeError(f"Failed to build VC target audio: {e2_result.get('error')}")
    VC_TARGET_META.write_text(json.dumps({"gen_text": GEN_TEXT, "source_model": "E2"}, ensure_ascii=False), encoding="utf-8")
    return VC_TARGET_AUDIO


def main() -> None:
    source_audio = OUT_ROOT / "original.wav"
    assert source_audio.exists(), f"Missing original demo asset: {source_audio}"
    report = {}
    target_audio = ensure_vc_target(source_audio)

    for group in GROUPS:
        for variant in VARIANTS:
            ref_audio = OUT_ROOT / group / variant / "input.wav"
            if not ref_audio.exists():
                print(f"skip {group}/{variant}: missing ref input", flush=True)
                continue

            for model in TTS_MODELS + VC_MODELS:
                key = f"{group}|{variant}|{model}"
                out_path = OUT_ROOT / group / variant / f"{model}.wav"
                if is_cached_ok(report, key, out_path):
                    report[key] = {
                        "ok": True,
                        "status_code": 200,
                        "output_path": str(out_path),
                        "size": out_path.stat().st_size,
                        "cached": True,
                        "gen_text": GEN_TEXT,
                    }
                    write_report(report)
                    continue
                print(f"run {key}", flush=True)
                started = time.time()
                try:
                    if model in TTS_MODELS:
                        if model == "XTTS":
                            result = run_xtts_direct(ref_audio, out_path)
                        else:
                            result = run_tts(model, ref_audio, out_path)
                    else:
                        result = run_vc(model, ref_audio, target_audio, out_path)
                except Exception as exc:
                    result = {"ok": False, "status_code": -1, "error": str(exc)}
                result["gen_text"] = GEN_TEXT
                result["elapsed_sec"] = round(time.time() - started, 2)
                report[key] = result
                write_report(report)
                print(json.dumps({"key": key, **result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
