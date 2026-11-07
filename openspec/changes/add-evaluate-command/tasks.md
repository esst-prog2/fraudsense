## 1. Evaluation module

- [x] 1.1 Create `fraudsense_core/evaluate.py` with `EvaluateError`, `CUTOFFS = (0.75, 0.80, 0.85, 0.90, 0.95)` and `load_labels(path)` (utf-8-sig, trimmed header, `missing required column: is_fraud`, label from the first row ingest keeps via `ingest._parse_row`); verify with the label-reading tests in 3.x
- [x] 1.2 Add `labels_for(scored, labels)` that returns a 0/1 label per scored transaction and raises `EvaluateError` naming the id and value for anything other than trimmed `0`/`1`; verify with the bad-label tests
- [x] 1.3 Add `confusion_at(scored, labels, cutoff)` and `ratios(tp, fp, fn)` (precision, recall, F1 as numbers or `None` per the n/a rules); verify with the fixture and n/a tests
- [x] 1.4 Add `format_evaluation(scored, labels, skipped)` that builds the summary line, the optional skipped line and the aligned table; verify with the output-format tests

## 2. CLI

- [x] 2.1 Add the `evaluate <csv>` subparser to `fraudsense.py`, a `run_evaluate` that calls `score_file`, `load_labels` and `format_evaluation`, catch `EvaluateError` as `error: ...` on stderr with exit 1, and add the usage line to the module docstring; verify with the CLI tests and `python fraudsense.py evaluate data/spike_slice.csv`

## 3. Tests (`tests/test_evaluate.py`)

- [x] 3.1 Hand-computed 15-row fixture: customer A with six 100.00 rows and one 800.00 fraud row (ratio 8, score 0.92), customer B with six 50.00 rows and one 600.00 not-fraud row (ratio 12, score 1.00), customer C with one fraud row (too little history, score 0); assert 0.75 gives flagged 2 / TP 1 / FP 1 / FN 1 / 0.500 / 0.500 / 0.500 and 0.95 gives flagged 1 / TP 0 / FP 1 / FN 2 / F1 0.000
- [x] 3.2 n/a cases: nothing flagged (precision and F1 n/a, recall 0.000), no fraud (recall and F1 n/a, precision 0.000), neither defined (all n/a)
- [x] 3.3 Label errors: missing column message, bad label on a scored row names id and value, bad label on a skipped row ignored, repeated id uses the first kept row (including the malformed-first case)
- [x] 3.4 CLI: exit 0 with the summary and table on stdout, the skipped line only when rows were skipped, exit 1 for missing column and bad label with the message on stderr, and the working directory still empty afterwards (no `reports/`)

## 4. Wrap-up

- [x] 4.1 Append the four 2026-11-07 lines to PLANNING_LOG.md without editing earlier lines; verify with `git diff PLANNING_LOG.md` showing only additions
- [x] 4.2 Run `python -m unittest discover tests` (all pass) and `python fraudsense.py evaluate data/spike_slice.csv`; confirm `git status` shows no changes to ingest, rules, features, pipeline, report, explain, models or README.md
