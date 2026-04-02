#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.asv_tools import asv_cosine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-audio", required=True)
    parser.add_argument("--test-audio", required=True)
    parser.add_argument("--source", default="speechbrain/spkrec-ecapa-voxceleb")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    score = asv_cosine(args.reference_audio, args.test_audio, source=args.source, device=args.device)
    print(json.dumps({"metric": "ASV", "score": score}, ensure_ascii=False))


if __name__ == "__main__":
    main()
