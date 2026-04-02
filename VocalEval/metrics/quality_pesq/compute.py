#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.quality_tools import pesq_score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-audio", required=True)
    parser.add_argument("--post-audio", required=True)
    parser.add_argument("--mode", default="wb")
    args = parser.parse_args()
    print(json.dumps({"metric": "Quality_PESQ", "score": pesq_score(args.pre_audio, args.post_audio, mode=args.mode)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
