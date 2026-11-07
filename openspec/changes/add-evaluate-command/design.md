## Context

`pipeline.score_file` returns the scored transactions (file order) and the skipped-row count; ingest drops malformed rows and repeated ids (first row wins) and never keeps extra columns. `Transaction` has no label field and must not get one, so labels have to be read from the file a second time and joined by `transaction_id`. See proposal.md for motivation and specs/fraud-evaluation/spec.md for the behaviour.

## Goals / Non-Goals

**Goals:**
- Reuse `score_file` unchanged so `evaluate` can never disagree with `score` about which rows are scored or flagged.
- Keep all label handling and metrics in one new module, `fraudsense_core/evaluate.py`.

**Non-Goals:**
- Configurable cutoffs, other metrics (ROC, AUC), or writing results to a file.
- Any change to scoring, ingest, report, explain or README.md.

## Decisions

- **Second pass over the CSV for labels.** `load_labels(path)` opens the file with `utf-8-sig`, trims header names (as ingest does), and returns `{transaction_id: raw label text}`. "First row wins" means the first row that ingest would keep for that id: ingest skips a malformed row without reserving its id, so a later valid row with the same id is the one scored. `load_labels` therefore keeps a row's label only if ingest's own `_parse_row` accepts it and the id has not been seen, reusing ingest's parser instead of copying it. It does not validate labels; validation happens only for ids that `score_file` returned, which is how labels on skipped rows are ignored. Alternative: extend ingest to return extra columns — rejected because ingest must not change.
- **Order of checks.** `score_file` runs first, so ingest errors (missing file, missing scoring columns, no valid rows) appear exactly as for `score`. Then the `is_fraud` header check, then label validation in file order (the first bad label is reported).
- **Strict labels.** Only the trimmed strings `0` and `1` are accepted; `1.0`, `true`, blank and the like are errors. The message is `transaction <id> has is_fraud value '<value>' (expected 0 or 1)`.
- **Errors.** A new `EvaluateError` in `evaluate.py`; `fraudsense.py` catches it next to `IngestError` and `ExplainError`, prints `error: <message>` to stderr and returns 1. The missing-column message is `missing required column: is_fraud`.
- **Metrics as `None` when undefined.** Precision and recall are `None` when their denominator is 0; F1 is `None` if either is `None`, `0.0` if both are 0, else `2PR / (P + R)`. Formatting turns `None` into `n/a` and numbers into `:.3f`.
- **Flag test.** `score > cutoff`, the same comparison `report.flagged_transactions` uses with `FLAG_THRESHOLD`. Cutoffs are the constant tuple `(0.75, 0.80, 0.85, 0.90, 0.95)`.
- **Table layout.** Right-aligned columns separated by two spaces, each as wide as its longest cell, header row first, a blank line between the summary and the table. Plain ASCII, so it prints safely on Windows consoles.
- **No disk writes.** `evaluate` only reads the input and prints; it never imports or calls `write_report`.

## Risks / Trade-offs

- [The file is read twice] → Acceptable: the spike slice is about 2.6 MB and the second pass is plain `csv` reading.
- [`evaluate.py` imports ingest's private `_parse_row`] → Accepted coupling: it is the only way to guarantee the label comes from the same row ingest scored, without changing ingest. A test covers the malformed-first duplicate so a change in ingest that breaks this shows up.
- [Strict `0`/`1` labels reject files that use `1.0` or `True`] → Intended: a wrong label silently miscounted is worse than a clear error naming the row.
