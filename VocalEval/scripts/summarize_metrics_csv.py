#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "metric_standards.json"
DEFAULT_CSV = Path("/home/torfqy/data/A(1).csv")
ENCODINGS = ["utf-8-sig", "gb18030", "gbk", "latin1"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize VocalEval metrics from a CSV file.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Input CSV path.")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Metric standards config path.")
    parser.add_argument("--out-json", required=True, help="Output summary JSON path.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rows(path: Path) -> tuple[list[dict[str, str]], str]:
    last_error: Exception | None = None
    for encoding in ENCODINGS:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                rows = list(csv.DictReader(handle))
            return rows, encoding
        except Exception as exc:  # pragma: no cover
            last_error = exc
    raise RuntimeError(f"failed to read CSV {path}: {last_error}")


def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def available_metrics(config: dict[str, Any], sample_row: dict[str, str]) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for item in config["metrics"]:
        col = item.get("source_column")
        if col and col in sample_row:
            metrics.append(item)
    return metrics


def aggregate(rows: list[dict[str, str]], group_key: str, axes: dict[str, str], metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_key = axes[group_key]
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"_count": 0, "_sums": defaultdict(float)})

    for row in rows:
        bucket = row[source_key]
        grouped[bucket]["_count"] += 1
        for metric in metrics:
            key = metric["key"]
            col = metric["source_column"]
            value = to_float(row.get(col))
            if value is None:
                continue
            grouped[bucket]["_sums"][key] += value

    output: list[dict[str, Any]] = []
    for bucket, payload in sorted(grouped.items()):
        entry: dict[str, Any] = {group_key: bucket, "count": payload["_count"]}
        for metric in metrics:
            key = metric["key"]
            total = payload["_sums"].get(key)
            entry[key] = round(total / payload["_count"], 4) if total is not None else None
        output.append(entry)
    return output


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()
    out_path = Path(args.out_json).expanduser().resolve()

    config = load_json(config_path)
    rows, encoding = load_rows(csv_path)
    if not rows:
        raise RuntimeError(f"no rows found in {csv_path}")

    axes = config["axes"]
    metrics = available_metrics(config, rows[0])

    summary = {
        "source_csv": str(csv_path),
        "source_encoding": encoding,
        "row_count": len(rows),
        "axes": axes,
        "metric_groups": config["metric_groups"],
        "metrics": metrics,
        "unique_counts": {
            key: len({row[source] for row in rows})
            for key, source in axes.items()
        },
        "summaries": {
            "by_method": aggregate(rows, "method", axes, metrics),
            "by_variant": aggregate(rows, "variant", axes, metrics),
            "by_backend": aggregate(rows, "backend", axes, metrics),
            "by_language": aggregate(rows, "language", axes, metrics),
            "by_scenario": aggregate(rows, "scenario", axes, metrics)
        }
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
