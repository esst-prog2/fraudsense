# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- People who have to go through a transaction export looking for fraud and want a shortlist instead of the whole file.
- Students and teachers who want a small, readable example of rule-based fraud detection with honest numbers attached.

## Product Purpose

fraudsense is a command-line program. It reads a CSV export of transactions and gives back the ones that look unusual for the customer who made them, each with a risk score and a one-line reason in plain words. Success is a reader who can see why each transaction is on the shortlist.

## Positioning

Every flag is explained by the rule that raised it, and the tool's weak results on outside data are published openly instead of hidden: on a Sparkov slice, precision 0.136 and recall 0.433.

## Operating Context

- Run from a terminal: `python fraudsense.py score <csv>`, `explain --id <id>`, `evaluate <csv>`.
- Input is a CSV with `transaction_id`, `customer_id`, `amount` and `timestamp`. Output is `reports/fraud_report.csv` and terminal text.
- The program is distributed through its GitHub repository, https://github.com/esst-prog2/fraudsense. The promo page is a static page on GitHub Pages that links there.

## Capabilities and Constraints

- Two rules: an amount at least 5 times the customer's average, and 5 or more transactions within 10 minutes.
- Python 3.10 or newer, standard library only.
- Not a production fraud system: not real-time, does not connect to a bank or payment system, does not block anything.
- The rule thresholds are starting values. They have not been tuned or validated.
- The promo page is plain HTML and CSS with no JavaScript.

## Brand Commitments

- Name: fraudsense, lower case.
- Results are stated honestly, including the weak ones.
- Nothing personal appears on public pages: no author name, contact details or course references.

## Evidence on Hand

- `docs/content.md`: the approved promo page wording.
- `data/sample_transactions.csv`: 500 synthetic transactions with planted anomalies; 18 are flagged.
- `data/spike_slice.csv`: 26,658 labeled transactions from 20 customers in the simulated Sparkov dataset, 157 of them fraud. `python fraudsense.py evaluate data/spike_slice.csv` reproduces the published table: 500 flagged, 68 true, 432 false, 89 missed.
- `reports/spike_counts.txt` and `reports/spike_source.txt`: the original run and the dataset source.
- There are no testimonials, users, screenshots, logo or licence. Do not invent them.

## Product Principles

1. Say why. A flag without a reason is not shown.
2. Publish the real numbers, in counts a person can picture, before the decimals.
3. Claim only what a visitor can reproduce with the commands on the page.
4. Stay small: one file in, one report out, nothing to install.
