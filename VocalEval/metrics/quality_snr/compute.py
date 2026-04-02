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
    parser.add_argument("--pre-audio", required=True)
    parser.add_argument("--post-audio", required=True)
    args = parser.parse_args()
    print(json.dumps({"metric": "Quality_SNR", "score": snr_db_from_files(args.pre_audio, args.post_audio)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
