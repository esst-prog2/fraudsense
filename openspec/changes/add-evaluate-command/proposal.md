## Why

The HW4 spike measured precision and recall on the Sparkov slice with one-off scripts (`scripts/spike_run.py`, `scripts/spike_crosscheck.py`). The next planned change is a threshold study, and it needs a repeatable way to check the program's flags against known fraud labels at several cutoffs, using exactly the scoring path that `score` uses.

## What Changes

- New subcommand `python fraudsense.py evaluate <csv>`. It scores the file the same way as `score` and reads the `is_fraud` column (1 = fraud, 0 = not fraud) from the same CSV.
- It prints one summary line with the number of transactions evaluated and the fraud / not-fraud counts, a "Skipped N malformed rows." line only when rows were skipped, and a table with one row per cutoff 0.75, 0.80, 0.85, 0.90, 0.95 and the columns cutoff, flagged, TP, FP, FN, precision, recall, F1.
- It writes nothing to disk. Unlike `score`, it does not create `reports/`.
- Undefined ratios print `n/a`, never 0.
- A missing `is_fraud` column, or a label other than 0 or 1 on a scored row, ends the command with exit code 1 and an error on stderr.
- Not changed: scoring, ingest, report, explain, the `Transaction` type and README.md.

## Capabilities

### New Capabilities
- `fraud-evaluation`: checks the program's flags against `is_fraud` labels in the input CSV and reports flagged, TP, FP, FN, precision, recall and F1 at fixed cutoffs.

### Modified Capabilities
(none)

## Impact

- New module `fraudsense_core/evaluate.py` (reads labels, counts results, formats the output).
- `fraudsense.py` gains the `evaluate` subparser and catches the new error type.
- New tests in `tests/test_evaluate.py`.
- Standard library only; no new dependencies.
