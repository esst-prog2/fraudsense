## 1. Setup

- [x] 1.1 Create `fraudsense_core/` (with `__init__.py`), `tests/`, `scripts/` and `data/`; verify `python -c "import fraudsense_core"` succeeds from the repo root
- [x] 1.2 Define the `Transaction` and `ScoredTransaction` dataclasses as described in design.md; verify with a unit test that builds one of each

## 2. Ingest (transaction-ingest)

- [x] 2.1 Implement `load_transactions(path)` with a required-column check that names every missing column; verify unit tests for "missing amount" and "several columns missing" pass
- [x] 2.2 Add handling for a missing file and an empty file; verify unit tests for both pass
- [x] 2.3 Skip and count malformed rows (bad amount, bad timestamp, empty ids, duplicate `transaction_id`), and fail when no valid rows remain; verify unit tests for each spec scenario pass

## 3. Features and rules (rule-scoring)

- [x] 3.1 Implement the leave-one-out average spend and amount ratio, returning None when there are fewer than 3 other transactions; verify unit tests for the 100/100/100/800 case and the 2-transaction customer pass
- [x] 3.2 Implement the 10-minute inclusive window count with a per-customer two-pointer sweep; verify unit tests for the 6-in-8-minutes burst and the 15-minutes-apart cases pass
- [x] 3.3 Implement the amount and velocity rules, the sub-score formulas (with named constants) and max-combination; verify unit tests for the 5x/4.9x boundaries, "fires if and only if score > 0.75", and monotonic scores pass
- [x] 3.4 Implement the reason strings in the formats given in design.md; verify unit tests check the exact text for both rules and for a transaction where both fire
- [x] 3.5 Implement `score_file(path)` in `pipeline.py`, joining ingest, features and rules; verify a unit test where an 8x transaction outranks the same customer's normal transactions

## 4. Report (fraud-report)

- [x] 4.1 Implement `write_report` (creating `reports/`, overwriting, keeping only rows with score > 0.75, sorting descending, 2-decimal scores, reasons joined with `; `); verify unit tests for the flagged-only and nothing-flagged cases pass
- [x] 4.2 Implement the run summary (scored count, time taken, skipped rows, flagged count with threshold, report path); verify a unit test checks the summary text

## 5. Explain (transaction-explain)

- [x] 5.1 Implement the explanation text for flagged transactions, for transactions where no rule fired (ratio and count shown against their thresholds), and for the "amount rule not evaluated" case; verify unit tests for each pass
- [x] 5.2 Handle an unknown id with a non-zero exit and an error naming the id; verify with a unit test

## 6. CLI

- [x] 6.1 Implement `fraudsense.py` with argparse subcommands `score <csv>` and `explain --id <id> [--file <csv>]` (defaulting to `data/sample_transactions.csv`); errors go to stderr with exit code 1. Verify `python fraudsense.py --help` lists both subcommands.
- [x] 6.2 Add an end-to-end unittest that runs both subcommands as subprocesses on a small fixture and checks exit codes, the summary text, report rows, and that `explain` scores and reasons match the report

## 7. Sample data and demo

- [ ] 7.1 Write `scripts/make_sample.py` (seed 42, about 40 customers, 500 rows, 10–15 planted anomalies, a few short-history customers, unused `location` and `payment_method` columns) and commit the generated `data/sample_transactions.csv`; verify the file has 500 data rows and that running the script twice produces an identical file
- [x] 7.2 Run `python fraudsense.py score data/sample_transactions.csv`, then `explain` on one flagged id; verify the planted anomalies appear in the report with sensible reasons, and note the actual flagged count
- [x] 7.3 Update the README demo section so its numbers and example output match the real run, and mark the model and location/payment items as future changes; verify every command in the README runs as written
- [x] 7.4 Run the whole test suite with `python -m unittest discover tests`; verify all tests pass
