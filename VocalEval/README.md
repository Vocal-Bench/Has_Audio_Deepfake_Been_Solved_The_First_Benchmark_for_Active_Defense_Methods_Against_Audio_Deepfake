# VocalEval

This directory centralizes the evaluation framework used to summarize benchmark results across different detection and assessment standards.

## Scope

The framework groups metrics into consistent categories so that defense results can be compared under a single evaluation view.

### Metric categories

- `speech_quality`
  - `STOI`
  - `SNR`
  - `PESQ`
  - `ViSQOL`
  - `Quality_SNR`
  - `Quality_STOI`
  - `Quality_PESQ`

- `content_consistency`
  - `WER`
  - `CER`

- `speaker_similarity`
  - `ASV`

- `defense_effectiveness`
  - `EER`

- `efficiency`
  - `TimeCost`

## Files

- `metric_standards.json`
  Central registry of metric semantics, source columns, and optimization direction.
- `scripts/summarize_metrics_csv.py`
  Reads a result CSV and produces grouped summaries by method / variant / backend / language / scenario.
- `scripts/build_metric_report.py`
  Converts a summary JSON into a compact Markdown report.

## Example

```bash
python VocalEval/scripts/summarize_metrics_csv.py \
  --csv /home/torfqy/data/A(1).csv \
  --out-json /tmp/vocaleval_summary.json

python VocalEval/scripts/build_metric_report.py \
  --summary-json /tmp/vocaleval_summary.json \
  --out-md /tmp/vocaleval_summary.md
```

## Notes

- The current local `A(1).csv` contains:
  - `STOI`
  - `SNR`
  - `PESQ`
  - `ViSQOL`
  - `WER`
  - `CER`
  - `ASV`
- The framework also reserves `EER`, `TimeCost`, and quality-preservation metrics, even if they are absent from the current CSV snapshot.
