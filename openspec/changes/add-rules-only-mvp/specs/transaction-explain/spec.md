## Purpose

Lets the reviewer look up any single transaction by id and see exactly which features and rules produced its risk score.

## ADDED Requirements

### Requirement: Explain a transaction by id
The system SHALL provide `explain --id <transaction_id>` with an optional `--file <csv>` argument, defaulting to `data/sample_transactions.csv`. It SHALL score the file the same way `score` does, then print the transaction id and its risk score, followed by one line per rule that fired, using the same reason text as the report.

#### Scenario: Flagged transaction
- **WHEN** the user runs `explain --id T00231` and the amount and velocity rules both fire for T00231
- **THEN** the output starts with the transaction id and its risk score
- **AND** it includes a line naming the amount compared with the customer's average, and a line naming the number of transactions in the last 10 minutes

#### Scenario: Scores match the report
- **WHEN** a transaction appears in `reports/fraud_report.csv` produced from the same file
- **THEN** `explain` shows the same risk score and the same reasons for it

### Requirement: Explain transactions that were not flagged
For a transaction where no rule fires, `explain` SHALL still print its score, state that no rule fired, and show its amount ratio and 10-minute count next to the rule thresholds. If the amount rule was not evaluated because of too little history, it SHALL say so.

#### Scenario: Normal transaction
- **WHEN** the user runs `explain` on a transaction where no rule fires
- **THEN** the output shows its score, says no rule fired, and shows its amount ratio against 5x and its 10-minute count against 5

### Requirement: Unknown transaction id
If the id is not among the file's valid transactions, the system SHALL exit with a non-zero status and an error message naming the id.

#### Scenario: Id not found
- **WHEN** the user runs `explain --id T99999` and no valid row has that id
- **THEN** the program exits with a non-zero status and the error message contains `T99999`
