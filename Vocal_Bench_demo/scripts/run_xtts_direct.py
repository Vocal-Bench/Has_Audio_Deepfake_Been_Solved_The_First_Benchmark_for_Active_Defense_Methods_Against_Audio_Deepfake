#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import faulthandler


sys.path.insert(0, "/home/torfqy/data/voicekit_api_bundle")

from VoiceKit import AVAILABLE_TTS_MODELS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref-audio", required=True)
    parser.add_argument("--gen-text", required=True)
    parser.add_argument("--out-path", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    faulthandler.enable()
    faulthandler.dump_traceback_later(60, repeat=True)
    xtts = AVAILABLE_TTS_MODELS["XTTS"]
    result = xtts.infer(ref_audio=args.ref_audio, gen_text=args.gen_text)
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(str(out_path))
    print(out_path)


if __name__ == "__main__":
    main()
