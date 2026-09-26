## Why

Someone reviewing a transaction export for fraud currently has to scan every row by hand. The README describes a tool that gives them a shortlist of transactions worth a closer look, with a reason for each. This change delivers the smallest version of that tool that runs end to end tonight: rules only, no trained model, tested on synthetic data.

## What Changes

- New command-line entry point `fraudsense.py` with two subcommands:
  - `score <csv>`: loads and validates a transaction CSV, scores every transaction, prints a summary and writes `reports/fraud_report.csv`.
  - `explain --id <transaction_id>`: prints the features and rules behind one transaction's score.
- Input validation: the program exits with an error naming any required column that is missing. Rows that cannot be parsed are skipped and counted instead of crashing the run.
- Two per-customer behavioural features: average spend and transaction velocity (how many transactions fall in a short window).
- Two rules built on those features, combined into one risk score between 0 and 1, with a readable reason for each rule that fires.
- A report of flagged transactions (score above 0.75), sorted from highest score down.
- A reproducible synthetic sample file, `data/sample_transactions.csv`, with planted anomalies, plus the script that generates it.

### Non-goals (deferred to future changes)

- Training and comparing 2+ ML models using precision, recall, F1 and PR-AUC.
- Location and payment-method features.
- Richer explanations beyond the rule reasons (for example SHAP).
- Everything in the README's "Not this term" list.

## Capabilities

### New Capabilities
- `transaction-ingest`: reading a transaction CSV, checking required columns, and cleaning or skipping bad rows.
- `rule-scoring`: per-customer features (average spend, velocity), the rules that use them, and the combined 0–1 risk score with reasons.
- `fraud-report`: the run summary and `reports/fraud_report.csv` listing flagged transactions.
- `transaction-explain`: looking up one transaction by id and showing the features and rules behind its score.

### Modified Capabilities
<!-- None: there are no existing specs. -->

## Impact

- New code: `fraudsense.py` (CLI), a `fraudsense_core/` package, `tests/`, `scripts/make_sample.py`, `data/sample_transactions.csv`.
- New output location: `reports/` (created when needed).
- Dependencies: Python 3.10+ standard library only. No third-party packages, so there is nothing to install before running.
