# VocalEval

This folder organizes the benchmark evaluation framework by metric.

Each metric is placed under its own subfolder so that the metric definition, dependencies, and runnable entrypoint stay together.

## Structure

```text
VocalEval/
  common/
  metrics/
    asv/
    eer/
    wer/
    cer/
    stoi/
    snr/
    pesq/
    visqol/
    quality_snr/
    quality_stoi/
    quality_pesq/
    time_cost/
```

## Purpose

- centralize different evaluation standards
- keep each metric independently runnable
- make it easy to extend one metric without touching the others
