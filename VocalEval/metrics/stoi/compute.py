#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.quality_tools import stoi_score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-audio", required=True)
    parser.add_argument("--test-audio", required=True)
    args = parser.parse_args()
    print(json.dumps({"metric": "STOI", "score": stoi_score(args.reference_audio, args.test_audio)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
