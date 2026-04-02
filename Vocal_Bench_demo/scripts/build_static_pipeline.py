#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "demo_assets" / "pipeline.json"
sys.path.insert(0, str(ROOT))

import server

TITLE = "VocalBench Demo"
SUBTITLE = (
    "同一条源语音经过不同主动防御、通道变体和克隆模型后的静态对比页面。"
    "页面已改为纯静态资源，可直接上传到 GitHub Pages。"
)
OVERVIEW = (
    "先试听左侧统一源样本，再比较每个 defense 分支的防御后参考音频。"
    "右侧的 variant 表示在该防御音频基础上继续加入不同通道扰动，展开后可以分别试听"
    " TTS 和 VC 模型的输出。"
)
READING_STEPS = [
    "Source Audio 是页面统一入口样本，便于横向比较。",
    "Defense 节点是各主动防御方法输出的参考说话人音频。",
    "Variant 胶囊表示在对应防御音频上继续施加的通道变化。",
    "VC 模型里已将原来的 GPTSoVITS_VC 替换为 AdaIN-VC。",
]
VARIANT_GUIDE = [
    {
        "key": "original",
        "label": "Original",
        "badge": "Original",
        "description": "原始防御音频，不叠加额外通道扰动。",
    },
    {
        "key": "denoised",
        "label": "Denoised",
        "badge": "Denoised",
        "description": "在对应防御音频基础上再做一次降噪处理。",
    },
    {
        "key": "downsampled_8k",
        "label": "8 kHz",
        "badge": "8 kHz",
        "description": "在对应防御音频基础上降采样到 8 kHz，模拟窄带语音。",
    },
    {
        "key": "compressed_mp3",
        "label": "MP3",
        "badge": "MP3",
        "description": "在对应防御音频基础上做有损 MP3 压缩，再用于后续模型推理。",
    },
]
DEFENSE_NOTES = {
    "Original": "无主动防御，作为基线参考。",
    "AntiFake": "对抗式保护分支，用于提升克隆难度。",
    "Attack-VC": "Attack-VC 主动防御分支。",
    "ClearMask": "ClearMask 主动防御分支。",
    "SampleMask": "SampleMask 主动防御分支。",
    "SafeSpeech": "SafeSpeech 主动防御分支。",
    "VoiceGuard": "VoiceGuard 主动防御分支。",
}
VARIANT_LABELS = {item["key"]: item["label"] for item in VARIANT_GUIDE}
VARIANT_BADGES = {item["key"]: item["badge"] for item in VARIANT_GUIDE}
VARIANT_NOTES = {item["key"]: item["description"] for item in VARIANT_GUIDE}
MODEL_RENAMES = {
    "GPTSoVITS_VC": "AdaIN-VC",
}


def media_to_relative(url: str | None) -> str | None:
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.path != "/media":
        return url.lstrip("/")

    raw_path = parse_qs(parsed.query).get("path", [None])[-1]
    if not raw_path:
        return None

    abs_path = Path(unquote(raw_path)).resolve()
    try:
        rel_path = abs_path.relative_to(ROOT).as_posix()
    except ValueError:
        rel_path = abs_path.as_posix()

    if rel_path.endswith("/GPTSoVITS_VC.wav"):
        rel_path = rel_path[: -len("GPTSoVITS_VC.wav")] + "AdaIN-VC.wav"

    rel_file = ROOT / rel_path
    return rel_path if rel_file.exists() else None


def transform_payload(payload: dict) -> dict:
    sample = dict(payload["sample"])
    sample["audio"] = media_to_relative(sample.get("audio"))
    sample["note"] = (
        "左侧这条音频是统一源样本。页面中所有 defense、variant 和模型输出都围绕它做横向比较。"
    )

    branches = []
    for branch in payload["branches"]:
        branch_copy = dict(branch)
        branch_copy["protected_audio"] = media_to_relative(branch.get("protected_audio"))
        branch_copy["note"] = DEFENSE_NOTES.get(branch["group"], branch.get("note"))

        variants = []
        for variant in branch["variants"]:
            variant_copy = dict(variant)
            variant_copy["audio"] = media_to_relative(variant.get("audio"))
            variant_copy["label"] = VARIANT_LABELS.get(variant["key"], variant["label"])
            variant_copy["badge"] = VARIANT_BADGES.get(variant["key"], variant["label"])
            variant_copy["note"] = VARIANT_NOTES.get(variant["key"], variant.get("note"))

            leaves = []
            for leaf in variant["leaves"]:
                leaf_copy = dict(leaf)
                leaf_copy["model"] = MODEL_RENAMES.get(leaf["model"], leaf["model"])
                leaf_copy["audio"] = media_to_relative(leaf.get("audio"))
                leaves.append(leaf_copy)

            variant_copy["leaves"] = leaves
            variants.append(variant_copy)

        branch_copy["variants"] = variants
        branches.append(branch_copy)

    meta = dict(payload["meta"])
    meta["overview"] = OVERVIEW
    meta["reading_steps"] = READING_STEPS
    meta["variant_guide"] = VARIANT_GUIDE
    meta["sample_note"] = (
        "为了便于快速试听，当前页面中的 TTS / VC 输出统一使用短句内容；"
        "其中 VC 模型使用各防御分支音频作为目标说话人参考。"
    )
    meta["tts_models"] = ["XTTS", "E2", "Vocus", "F5", "GPTSoVITS"]
    meta["vc_models"] = ["SeedVC", "AdaIN-VC"]

    return {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "sample": sample,
        "meta": meta,
        "branches": branches,
    }


def main() -> None:
    payload = server.get_index().get_pipeline()
    static_payload = transform_payload(payload)
    OUT_PATH.write_text(json.dumps(static_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
