#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Markdown report from a VocalEval summary JSON.")
    parser.add_argument("--summary-json", required=True, help="Input summary JSON produced by summarize_metrics_csv.py")
    parser.add_argument("--out-md", required=True, help="Output markdown report path")
    return parser.parse_args()


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_table(title: str, rows: list[dict[str, Any]], metrics: list[dict[str, Any]], key_name: str) -> list[str]:
    headers = [key_name, "count"] + [m["display_name"] for m in metrics]
    lines = [f"## {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        cells = [fmt(row.get(key_name)), fmt(row.get("count"))]
        for metric in metrics:
            cells.append(fmt(row.get(metric["key"])))
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    out_path = Path(args.out_md).expanduser().resolve()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    metrics = summary["metrics"]

    lines: list[str] = []
    lines.append("# VocalEval Metric Report")
    lines.append("")
    lines.append(f"- Source CSV: `{summary['source_csv']}`")
    lines.append(f"- Encoding: `{summary['source_encoding']}`")
    lines.append(f"- Rows: `{summary['row_count']}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    for key, value in summary["unique_counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.extend(render_table("By Method", summary["summaries"]["by_method"], metrics, "method"))
    lines.extend(render_table("By Variant", summary["summaries"]["by_variant"], metrics, "variant"))
    lines.extend(render_table("By Backend", summary["summaries"]["by_backend"], metrics, "backend"))
    lines.extend(render_table("By Language", summary["summaries"]["by_language"], metrics, "language"))
    lines.extend(render_table("By Scenario", summary["summaries"]["by_scenario"], metrics, "scenario"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
