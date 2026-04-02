#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import mimetypes
import os
from dataclasses import dataclass
from functools import lru_cache
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT
DATA_ROOT = Path("/home/torfqy/data")
VOCALBENCH_ROOT = DATA_ROOT / "vocalbench"
VOCALEVAL_ROOT = DATA_ROOT / "vocaleval"
DEMO_ASSET_ROOT = ROOT / "demo_assets"
DEFAULT_PORT = int(os.environ.get("VOCAL_BENCH_DEMO_PORT", "8123"))

GROUP_ORDER = ["Original", "AntiFake", "Attack-VC", "ClearMask", "SampleMask", "SafeSpeech", "VoiceGuard"]
MODEL_ORDER = ["XTTS", "E2", "Vocus", "F5", "GPTSoVITS", "GPTSoVITS_VC", "SeedVC"]
MODEL_KIND = {
    "XTTS": "TTS",
    "E2": "TTS",
    "Vocus": "TTS",
    "F5": "TTS",
    "GPTSoVITS": "TTS",
    "GPTSoVITS_VC": "VC",
    "SeedVC": "VC",
}
LANGUAGE_LABELS = {
    "english": "English",
    "french": "French",
}
TASK_LABELS = {
    "full": "Full",
}
VARIANT_ORDER = ["original", "denoised", "downsampled_8k", "compressed_mp3"]
VARIANT_LABELS = {
    "original": "Clean",
    "denoised": "Denoised",
    "downsampled_8k": "Downsampled 8k",
    "compressed_mp3": "Compressed MP3",
}
VARIANT_NOTES = {
    "original": "Pure defended audio before channel corruption.",
    "denoised": "Robustness branch after denoising.",
    "downsampled_8k": "Robustness branch after narrowband 8 kHz degradation.",
    "compressed_mp3": "Robustness branch after lossy MP3 compression.",
}

SHARED_SAMPLE = {
    "task": "full",
    "lang": "english",
    "file_name": "english_target12.wav",
}


def media_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"/media?path={quote(path)}"


def safe_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 4)
    except ValueError:
        return None


def shorten_text(text: str | None, limit: int = 260) -> str | None:
    if not text:
        return None
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def group_prefix(group: str) -> str:
    return "" if group == "Original" else f"{group}_"


def bench_audio_path(group: str) -> Path:
    return DEMO_ASSET_ROOT / group / "branch.wav"


def bench_variant_audio_path(group: str, variant: str) -> Path:
    return DEMO_ASSET_ROOT / group / variant / "input.wav"


def original_audio_path() -> Path:
    return DEMO_ASSET_ROOT / "original.wav"


def eval_audio_path(group: str, model: str) -> Path:
    return DEMO_ASSET_ROOT / group / "original" / f"{model}.wav"


def eval_variant_audio_path(group: str, model: str, variant: str) -> Path:
    return DEMO_ASSET_ROOT / group / variant / f"{model}.wav"


def lookup_row(csv_path: Path, file_name: str) -> dict[str, str] | None:
    if not csv_path.exists():
        return None
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("file_name") == file_name:
                return row
    return None


def lookup_transcript() -> tuple[str | None, float | None]:
    info_path = VOCALBENCH_ROOT / "Original_VocalBench" / "original" / "info.csv"
    target = f"{SHARED_SAMPLE['task']}/{SHARED_SAMPLE['lang']}/{SHARED_SAMPLE['file_name']}".replace("/", "\\")
    if not info_path.exists():
        return None, None
    with info_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("relative_path") == target:
                return row.get("text"), safe_float(row.get("duration"))
    return None, None


@dataclass
class ModelLeaf:
    model: str
    kind: str
    audio_path: str | None
    metrics: dict[str, float | None]

    def to_api(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "kind": self.kind,
            "audio": media_url(self.audio_path),
            "metrics": {k: v for k, v in self.metrics.items() if v is not None},
        }


@dataclass
class VariantBranch:
    key: str
    label: str
    note: str
    audio_path: str
    leaves: list[ModelLeaf]

    def to_api(self) -> dict[str, Any]:
        tts_count = sum(1 for leaf in self.leaves if leaf.kind == "TTS")
        vc_count = sum(1 for leaf in self.leaves if leaf.kind == "VC")
        return {
            "key": self.key,
            "label": self.label,
            "note": self.note,
            "audio": media_url(self.audio_path),
            "model_count": len(self.leaves),
            "tts_count": tts_count,
            "vc_count": vc_count,
            "leaves": [leaf.to_api() for leaf in self.leaves],
        }


@dataclass
class DefenseBranch:
    group: str
    protected_audio: str
    note: str
    metrics: dict[str, float | None]
    variants: list[VariantBranch]

    def to_api(self) -> dict[str, Any]:
        return {
            "group": self.group,
            "note": self.note,
            "protected_audio": media_url(self.protected_audio),
            "metrics": {k: v for k, v in self.metrics.items() if v is not None},
            "variants": [variant.to_api() for variant in self.variants],
        }


class PipelineIndex:
    def __init__(self) -> None:
        self.allowed_media_paths: set[str] = set()
        self.pipeline = self._build_pipeline()

    def _register(self, *paths: str | Path | None) -> None:
        for path in paths:
            if path:
                self.allowed_media_paths.add(str(Path(path).resolve()))

    def _defense_note(self, group: str) -> str:
        notes = {
            "Original": "No defense / baseline",
            "AntiFake": "Adv / Adv+Transfer / Adv+Transfer+Ablation",
            "Attack-VC": "Embedding / Embedding+Feedback / Embedding+Feedback+E2E",
            "ClearMask": "Filter / Filter+Style / Filter+Style+Reverb",
            "SampleMask": "Mask / Mask+Constraint / Mask+Constraint+Robust",
            "SafeSpeech": "Surrogate / Surrogate+Perceptual / Surrogate+Perceptual+Robust",
            "VoiceGuard": "Time / Time+Psychoacoustic / Time+Psychoacoustic+Masking",
        }
        return notes[group]

    def _build_pipeline(self) -> dict[str, Any]:
        transcript, duration = lookup_transcript()
        root_audio = original_audio_path()
        self._register(root_audio)

        branches: list[DefenseBranch] = []

        for group in GROUP_ORDER:
            protected_audio = bench_audio_path(group)
            protected_name = protected_audio.name
            bench_row = lookup_row(
                VOCALBENCH_ROOT / f"{group}_VocalBench" / "info_original（原始）.csv",
                protected_name,
            )
            branch = DefenseBranch(
                group=group,
                protected_audio=str(protected_audio),
                note=self._defense_note(group),
                metrics={
                    "snr_db": safe_float(bench_row.get("snr_db") if bench_row else None),
                    "mfcc_cos": safe_float(bench_row.get("mfcc_cos") if bench_row else None),
                    "wer": safe_float(bench_row.get("wer") if bench_row else None),
                },
                variants=[],
            )
            self._register(protected_audio)

            for variant in VARIANT_ORDER:
                variant_audio = bench_variant_audio_path(group, variant)
                self._register(variant_audio)
                leaves: list[ModelLeaf] = []
                for model in MODEL_ORDER:
                    clone_audio = eval_variant_audio_path(group, model, variant)
                    eval_row = None
                    if clone_audio.exists():
                        csv_name = {
                            "original": "info_original（原始）.csv",
                            "denoised": "info_denoised（降噪）.csv",
                            "downsampled_8k": "info_downsampled_8k（降采样8k）.csv",
                            "compressed_mp3": "info_compressed_mp3（压缩mp3）.csv",
                        }[variant]
                        eval_row = lookup_row(
                            VOCALEVAL_ROOT / f"{group}_VocalEval" / model / csv_name,
                            clone_audio.name,
                        )
                        self._register(clone_audio)
                    leaves.append(
                        ModelLeaf(
                            model=model,
                            kind=MODEL_KIND[model],
                            audio_path=str(clone_audio) if clone_audio.exists() else None,
                            metrics={
                                "snr_db": safe_float(eval_row.get("snr_db") if eval_row else None),
                                "mfcc_cos": safe_float(eval_row.get("mfcc_cos") if eval_row else None),
                                "wer": safe_float(eval_row.get("wer") if eval_row else None),
                            },
                        )
                    )

                branch.variants.append(
                    VariantBranch(
                        key=variant,
                        label=VARIANT_LABELS[variant],
                        note=VARIANT_NOTES[variant],
                        audio_path=str(variant_audio),
                        leaves=leaves,
                    )
                )

            branches.append(branch)

        return {
            "title": "Original Audio -> Active Defense -> TTS / VC",
            "sample": {
                "task": SHARED_SAMPLE["task"],
                "lang": SHARED_SAMPLE["lang"],
                "file_name": SHARED_SAMPLE["file_name"],
                "task_label": TASK_LABELS[SHARED_SAMPLE["task"]],
                "lang_label": LANGUAGE_LABELS[SHARED_SAMPLE["lang"]],
                "duration": duration,
                "transcript": shorten_text(transcript),
                "audio": media_url(str(root_audio)),
            },
            "meta": {
                "defense_count": len(GROUP_ORDER),
                "model_count": len(MODEL_ORDER),
                "tts_count": sum(1 for model in MODEL_ORDER if MODEL_KIND[model] == "TTS"),
                "vc_count": sum(1 for model in MODEL_ORDER if MODEL_KIND[model] == "VC"),
                "paper_points": [
                    "VocalGen collects authentic social-media speech and builds channel variants.",
                    "VocalBench applies active defenses to the same source utterance.",
                    "VocalEval sends each defended sample into both TTS and VC cloning models.",
                ],
            },
            "branches": [branch.to_api() for branch in branches],
        }

    def get_pipeline(self) -> dict[str, Any]:
        return self.pipeline


@lru_cache(maxsize=1)
def get_index() -> PipelineIndex:
    return PipelineIndex()


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        ctype = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        with path.open("rb") as handle:
            stat = path.stat()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(stat.st_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.copyfile(handle, self.wfile)
            except (BrokenPipeError, ConnectionResetError):
                return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}

        if parsed.path == "/api/pipeline":
            self.end_json(get_index().get_pipeline())
            return
        if parsed.path == "/media":
            raw_path = params.get("path")
            if not raw_path:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing path")
                return
            file_path = Path(unquote(raw_path)).resolve()
            if str(file_path) not in get_index().allowed_media_paths:
                self.send_error(HTTPStatus.FORBIDDEN, "Media not published")
                return
            self.send_file(file_path)
            return
        return super().do_GET()

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    get_index()
    server = ThreadingHTTPServer(("0.0.0.0", DEFAULT_PORT), DemoHandler)
    print(f"Serving Vocal Bench demo at http://127.0.0.1:{DEFAULT_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
