## Purpose

Loads a transaction CSV, checks that it has the columns scoring needs, and cleans it so that later steps only ever see well-formed transactions.

## ADDED Requirements

### Requirement: Required columns are checked before any scoring
The system SHALL require the input CSV to contain the columns `transaction_id`, `customer_id`, `amount` and `timestamp`. If one or more are missing, the system MUST exit with a non-zero status and an error message naming every missing column, and MUST NOT write a report.

#### Scenario: Missing amount column
- **WHEN** the user runs `score` on a CSV that has no `amount` column
- **THEN** the program exits with a non-zero status
- **AND** the error message names `amount`
- **AND** no report file is written

#### Scenario: Several columns missing
- **WHEN** the input CSV has neither `amount` nor `customer_id`
- **THEN** the error message names both `amount` and `customer_id`

#### Scenario: Extra columns are allowed
- **WHEN** the input CSV contains the four required columns plus others (for example `location`, `payment_method`)
- **THEN** the file is accepted and the extra columns are ignored

### Requirement: Input file errors are reported clearly
The system SHALL exit with a non-zero status and a readable error message when the input file does not exist or is empty.

#### Scenario: File not found
- **WHEN** the user runs `score` with a path that does not exist
- **THEN** the program exits with a non-zero status and an error message containing that path

### Requirement: Malformed rows are skipped and counted
The system SHALL skip any row whose `amount` is not a non-negative number, whose `timestamp` is not a valid ISO 8601 date-time, or whose `transaction_id` or `customer_id` is empty. It SHALL skip any row whose `transaction_id` repeats an earlier row's. The run SHALL continue with the remaining rows and report how many rows were skipped.

#### Scenario: Unparseable amount
- **WHEN** one row has `amount` set to `abc` and the other rows are valid
- **THEN** that row is left out of scoring and out of the report
- **AND** the run completes and reports 1 skipped row

#### Scenario: Duplicate transaction id
- **WHEN** two rows share the `transaction_id` `T00001`
- **THEN** only the first of them is scored and 1 skipped row is reported

#### Scenario: No valid rows remain
- **WHEN** every row in the file is malformed
- **THEN** the program exits with a non-zero status and an error message saying no valid transactions were found
