#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.asv_tools import eer_from_scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores-csv", required=True)
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--score-column", default="score")
    parser.add_argument("--positive-label", default="1")
    args = parser.parse_args()

    labels = []
    scores = []
    with open(args.scores_csv, "r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            labels.append(1 if str(row[args.label_column]) == str(args.positive_label) else 0)
            scores.append(float(row[args.score_column]))

    print(json.dumps({"metric": "EER", "score": eer_from_scores(labels, scores)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
