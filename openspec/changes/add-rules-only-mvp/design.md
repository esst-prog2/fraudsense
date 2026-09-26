## Context

The repository has no code yet. The work is due tonight, so the design goes for the simplest thing that runs end to end and can be checked against the specs. See proposal.md for scope; the numbered thresholds are defined in `specs/rule-scoring/spec.md`.

## Goals / Non-Goals

**Goals:**
- Anyone with Python 3.10+ can run it straight from a clone, with nothing to install.
- Scoring is deterministic: the same file always gives the same scores and the same report.
- `score` and `explain` share one scoring path, so they can never disagree.
- The pipeline stages match the capabilities, so the future model-scoring change has an obvious place to plug in.

**Non-Goals:**
- Performance beyond a few thousand rows. Everything is held in memory.
- Keeping customer profiles between runs. Baselines are computed from the input file only.

## Decisions

### Layout: thin CLI plus a small package, one module per stage

```
fraudsense.py                 argparse CLI: `score`, `explain`
fraudsense_core/
  ingest.py                   load_transactions(path) -> (list[Transaction], skipped_count)
  features.py                 per-customer average spend, 10-minute count
  rules.py                    amount rule, velocity rule, scoring functions, reason text
  report.py                   summary text, write fraud_report.csv
  explain.py                  explanation text for one transaction
  pipeline.py                 score_file(path) -> list[ScoredTransaction], used by both commands
scripts/make_sample.py        generates data/sample_transactions.csv (fixed seed)
tests/                        unittest, one file per module plus a CLI end-to-end test
```

The package is named `fraudsense_core` rather than `fraudsense` so it doesn't collide with `fraudsense.py` on import.
*Alternative considered:* a single script. It would be quicker to start, but the future model change would then mean untangling it.

### Standard library only (`csv`, `datetime`, `argparse`, `unittest`)
With 500 rows, pandas brings no real benefit and adds an install step.
*Alternative considered:* pandas plus pytest. They're more familiar for data work but add setup risk tonight. Moving to pandas later is a local change inside `ingest` and `features`.

### Data model
`Transaction` is a frozen dataclass with `transaction_id`, `customer_id`, `amount: float` and `timestamp: datetime`.
`ScoredTransaction` holds the transaction, `amount_ratio: float | None` (None when there are fewer than 3 other transactions), `window_count: int`, `fired: list[str]` (rule names), `reasons: list[str]` and `score: float`.
Timestamps are parsed with `datetime.fromisoformat`. Naive and timezone-aware timestamps are not mixed; a file that mixes them has the minority kind treated as malformed rows. The synthetic file uses naive timestamps.

### Features
- **Average spend:** group amounts by customer once. For each transaction, `(customer_total - amount) / (customer_count - 1)`. This is O(n) and excludes the transaction itself. If the average is 0, the ratio is treated as not evaluated.
- **10-minute count:** sort each customer's transactions by timestamp. For each one, count the transactions with `t - 10 min <= ts <= t` using a two-pointer sweep. The window includes both ends, and ties on the same timestamp all count.

### Scoring formula
Each rule gives a sub-score, and the transaction's score is the higher of the two.

```
 amount sub-score (ratio r; 0 if not evaluated)
   r >= 5 : 0.80 + 0.20 * min(1, (r - 5) / 5)      5x -> 0.80,  10x or more -> 1.00
   r <  5 : 0.75 * clamp((r - 1) / 4, 0, 1)        1x or less -> 0.00, just under 5x -> ~0.75

 velocity sub-score (count c, which is always >= 1)
   c >= 5 : 0.80 + 0.20 * min(1, (c - 5) / 5)      5 -> 0.80,  10 or more -> 1.00
   c <  5 : 0.75 * (c - 1) / 4                      1 -> 0.00, 4 -> 0.56

 score = max(amount sub-score, velocity sub-score)
```

This satisfies the spec. A fired rule always gives at least 0.80, so it clears the 0.75 flag threshold. When no rule fires, the score stays at 0.75 or below but still grows with how unusual the transaction is, which makes near-misses visible in `explain`. Taking the max means the headline number always traces back to one rule, which keeps it easy to explain.
*Alternatives considered:* a weighted sum (harder to explain, and it pushes the threshold around); a binary 0/1 (loses ranking, so it can't satisfy "unusual outranks normal" for near-misses).

### Reason text
- Amount: `amount $4,200 is 8.0x this customer's average ($525)`, using thousands separators, whole dollars when the amount is a whole number, and the ratio to 1 decimal place.
- Velocity: `6 transactions in the last 10 minutes (rule fires at 5)`.

The same strings go into the report and the `explain` output.

### Synthetic sample data
`scripts/make_sample.py` uses `random.Random(42)` to create about 40 customers with 500 transactions over 7 days. Each customer has a typical spend drawn from $20–$600, with individual amounts spread ±30% around it. It then plants roughly 10–15 anomalies: large-amount spikes (6–12x), bursts of 5–7 transactions within 10 minutes, and a few with both. A small number of customers with fewer than 4 transactions are included to exercise the minimum-history rule. The generated CSV is committed, so the demo doesn't depend on running the script first. It also includes `location` and `payment_method` columns, unused for now, so the future feature change has data to work with.

### Testing
Unit tests build small in-memory CSVs (with `tempfile`) aimed at each spec scenario. One end-to-end test runs `fraudsense.py score` and `explain` as subprocesses against a temporary copy of a small fixture and checks exit codes, the summary text and the report rows. Tests run with `python -m unittest`.

## Risks / Trade-offs

- [Baselines come from the scored file only, so thin histories weaken the amount rule] → A minimum of 3 other transactions stops it firing on noise; `explain` states when it wasn't evaluated. Stored profiles are a candidate for a future change.
- [The mean is pulled up by one earlier spike from the same customer] → Accepted for the MVP. A median is an easy swap inside `features.py` if the sample data shows the problem.
- [The synthetic data is designed to be caught, so a good demo doesn't prove real-world value] → Acknowledged. Real-world value will be measured in the future model-comparison change with a labelled dataset and precision, recall, F1 and PR-AUC.
- [The sub-score constants (0.80 base, 10x or count 10 for 1.00) are arbitrary] → They live as named constants at the top of `rules.py`, and only the "fires means > 0.75" property is part of the spec.
