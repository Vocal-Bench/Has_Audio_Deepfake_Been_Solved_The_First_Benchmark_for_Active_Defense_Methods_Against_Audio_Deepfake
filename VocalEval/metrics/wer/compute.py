#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.asr_tools import transcribe
from common.text_tools import wer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-text")
    parser.add_argument("--hypothesis-text")
    parser.add_argument("--reference-audio")
    parser.add_argument("--hypothesis-audio")
    parser.add_argument("--asr-model", default="tiny")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    ref = args.reference_text or transcribe(args.reference_audio, model_name=args.asr_model, device=args.device)
    hyp = args.hypothesis_text or transcribe(args.hypothesis_audio, model_name=args.asr_model, device=args.device)
    print(json.dumps({"metric": "WER", "score": wer(ref or "", hyp or ""), "reference": ref, "hypothesis": hyp}, ensure_ascii=False))


if __name__ == "__main__":
    main()
