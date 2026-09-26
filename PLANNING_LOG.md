2026-09-26: Initialized OpenSpec 1.13.0 with the Claude Code integration and spec-driven schema; decided by assistant based on the CLI default.
2026-09-26: MVP scope is a rules-only walking skeleton: ingest + validate, per-customer average-spend and transaction-velocity features, rule-based score with reasons, reports/fraud_report.csv, and `explain --id`; decided by user (outline proposed by assistant).
2026-09-26: MVP is tested on a small synthetic CSV with planted anomalies, so no labelled public dataset is needed until model training; decided by user (proposed by assistant).
2026-09-26: Deferred to a future change: offline comparison of 2+ trained models using precision, recall, F1 and PR-AUC; decided by user.
2026-09-26: Deferred to a future change: location and payment-method features; decided by user.
2026-09-26: Deferred to a future change: richer explanations beyond rule reasons; decided by user.
2026-09-26: MVP change is named `add-rules-only-mvp`; decided by user (name proposed by assistant).
2026-09-26: Amount rule fires at 5x or more the customer's average spend; decided by user (proposed by assistant).
2026-09-26: Velocity rule fires at 5 or more of a customer's transactions within 10 minutes; decided by user (proposed by assistant).
2026-09-26: Risk score is the strongest rule's sub-score scaled to 0–1, and transactions scoring above 0.75 are flagged; decided by user (proposed by assistant).
2026-09-26: Sub-score constants: a fired rule scores 0.80, rising to 1.00 at 10x or 10 transactions; below threshold it scales from 0 up to 0.75; decided by assistant.
2026-09-26: Average spend is the mean of the customer's other transactions in the file (excluding the one being scored), and the amount rule needs at least 3 of them; decided by assistant.
2026-09-26: Required input columns are transaction_id, customer_id, amount and timestamp (ISO 8601); location and payment_method are optional for the MVP; decided by assistant.
2026-09-26: Malformed or duplicate-id rows are skipped and counted instead of stopping the run; decided by assistant.
2026-09-26: Report columns are transaction_id, customer_id, amount, timestamp, risk_score (2 decimal places) and reasons (joined with "; "), sorted by score descending; decided by assistant.
2026-09-26: `explain` takes `--id` and an optional `--file`, defaulting to data/sample_transactions.csv; decided by assistant.
2026-09-26: Python 3.10+ standard library only (csv, datetime, argparse, unittest), with no third-party dependencies; decided by assistant.
2026-09-26: Code layout is a thin `fraudsense.py` CLI plus a `fraudsense_core/` package with one module per stage; decided by assistant.
2026-09-26: Sample data comes from scripts/make_sample.py (seed 42, ~40 customers, 500 rows, 10–15 planted anomalies) and the generated CSV is committed; decided by assistant.
2026-09-26: Reason text always shows the customer's average rounded to whole dollars (e.g. "$86"), while the transaction amount keeps its cents unless it is a whole number; decided by assistant.
2026-09-26: `explain` output uses a plain ASCII " - " in its header line instead of an em dash, so it prints safely on Windows consoles and pipes; decided by assistant.
