## Purpose

Gives the reviewer a short summary of each scoring run and a CSV shortlist of the transactions worth a closer look.

## ADDED Requirements

### Requirement: Run summary
After a successful `score` run, the system SHALL print the number of transactions scored, the time taken, the number of skipped rows (if any), the number flagged as high-risk with the threshold (`score > 0.75`), and the path of the report written.

#### Scenario: Summary printed
- **WHEN** the user runs `score` on a file with 500 valid transactions, 14 of which are flagged
- **THEN** the output includes `Scored 500 transactions`, `14 flagged as high-risk (score > 0.75)` and `reports/fraud_report.csv`

### Requirement: Flagged-transaction report
The system SHALL write `reports/fraud_report.csv`, creating the `reports/` directory if needed and overwriting any earlier report. The file SHALL contain a header row and one row per flagged transaction (score > 0.75), with the columns `transaction_id`, `customer_id`, `amount`, `timestamp`, `risk_score` and `reasons`. Rows SHALL be sorted by `risk_score` from highest to lowest. `risk_score` SHALL have 2 decimal places. Multiple reasons SHALL be joined with `; `.

#### Scenario: Report contains only flagged rows
- **WHEN** a run scores 500 transactions and 14 have a score above 0.75
- **THEN** the report has a header plus exactly 14 data rows, sorted by score, highest first

#### Scenario: Nothing flagged
- **WHEN** no transaction scores above 0.75
- **THEN** the report is still written, containing only the header row
- **AND** the summary says 0 transactions were flagged
