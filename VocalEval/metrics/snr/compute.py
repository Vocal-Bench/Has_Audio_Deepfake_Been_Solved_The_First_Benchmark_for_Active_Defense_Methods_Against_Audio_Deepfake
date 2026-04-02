#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.audio_tools import snr_db_from_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-audio", required=True)
    parser.add_argument("--test-audio", required=True)
    args = parser.parse_args()
    print(json.dumps({"metric": "SNR", "score": snr_db_from_files(args.reference_audio, args.test_audio)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
