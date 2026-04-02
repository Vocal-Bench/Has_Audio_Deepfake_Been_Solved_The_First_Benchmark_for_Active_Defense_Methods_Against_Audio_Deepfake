#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("usage: compute.py -- <command ...>")
    start = time.perf_counter()
    completed = subprocess.run(command, check=False)
    elapsed = time.perf_counter() - start
    print(json.dumps({"metric": "TimeCost", "seconds": elapsed, "returncode": completed.returncode}, ensure_ascii=False))


if __name__ == "__main__":
    main()
