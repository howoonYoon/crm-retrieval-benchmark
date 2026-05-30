# Reproduce Instructions

These instructions reproduce the reported benchmark results from the checked-in processed corpus.

## Install

```bash
pip install -r requirements.txt
```

## Run Evaluation

On macOS or Linux, or on Windows if `make` is installed:

```bash
make run
```

On Windows without `make`, use the equivalent PowerShell command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run.ps1
```

Both commands write:

```text
results/metrics.csv
results/per_query_results.csv
results/metrics_plot.png
```

## Rebuild Corpus

The reported evaluation uses the checked-in processed corpus:

```text
data/processed/documents.jsonl
data/processed/queries.jsonl
```

To rebuild the processed corpus from the raw source list, the local PDF references in `data/raw/source_urls.txt` must also be available on the machine, or replaced with equivalent public PDF URLs. Then run:

```bash
make build-corpus
make inspect
make run
```
