## Purpose

Checks the program's high-risk flags against known `is_fraud` labels in the input CSV, so the reviewer can see precision, recall and F1 at several cutoffs without writing any files.

## ADDED Requirements

### Requirement: Evaluate command
The system SHALL provide `python fraudsense.py evaluate <csv>`. It SHALL score the file exactly as `score` does, including which rows are skipped, and SHALL read the `is_fraud` column from the same file. It SHALL NOT write any file and SHALL NOT create the `reports/` directory. On success it SHALL exit with code 0.

#### Scenario: Nothing written
- **WHEN** the user runs `evaluate` on a valid labelled file in an empty working directory
- **THEN** the command exits with code 0
- **AND** the working directory is still empty afterwards

### Requirement: Evaluation summary
The output SHALL start with the line `Evaluated N transactions against the is_fraud labels: F fraud, M not fraud.`, where N is the number of scored transactions and F and M count their labels. When rows were skipped, the next line SHALL be `Skipped K malformed rows.` (`row` when K is 1); otherwise that line SHALL be absent.

#### Scenario: Summary on the spike slice
- **WHEN** the user runs `evaluate data/spike_slice.csv`
- **THEN** the first line is `Evaluated 26658 transactions against the is_fraud labels: 157 fraud, 26501 not fraud.`

#### Scenario: Skipped rows reported
- **WHEN** the file has one row with an unparseable amount
- **THEN** the output includes `Skipped 1 malformed row.`

### Requirement: Cutoff table
After the summary, the system SHALL print a table with a header row and one row for each cutoff 0.75, 0.80, 0.85, 0.90 and 0.95, in that order, with the columns `cutoff`, `flagged`, `TP`, `FP`, `FN`, `precision`, `recall` and `F1`. A transaction SHALL count as flagged at a cutoff when its score is greater than the cutoff. TP counts flagged fraud, FP flagged not-fraud, FN unflagged fraud. Precision SHALL be TP / flagged, recall TP / (TP + FN), and F1 the harmonic mean of precision and recall. Cutoffs SHALL be printed with 2 decimal places and ratios with 3.

#### Scenario: Hand-computed fixture
- **WHEN** a 15-row file has one fraud row scoring 0.92, one not-fraud row scoring 1.00, one fraud row that is not flagged, and no other row above 0.75
- **THEN** the 0.75 row shows flagged 2, TP 1, FP 1, FN 1, precision 0.500, recall 0.500, F1 0.500
- **AND** the 0.95 row shows flagged 1, TP 0, FP 1, FN 2, precision 0.000, recall 0.000, F1 0.000

### Requirement: Undefined ratios
A ratio whose denominator is zero SHALL print as `n/a`, not 0: precision when nothing is flagged, recall when the file has no fraud rows. F1 SHALL print `n/a` when precision or recall is undefined, and SHALL print `0.000` only when both are defined and both are zero.

#### Scenario: Nothing flagged
- **WHEN** the file has fraud rows but no transaction scores above the cutoff
- **THEN** precision and F1 print `n/a` and recall prints `0.000`

#### Scenario: No fraud in the file
- **WHEN** every label is 0 and one transaction is flagged
- **THEN** recall and F1 print `n/a` and precision prints `0.000`

#### Scenario: Neither defined
- **WHEN** every label is 0 and nothing is flagged
- **THEN** precision, recall and F1 all print `n/a`

### Requirement: Label errors
If the header has no `is_fraud` column, the system SHALL print `error: missing required column: is_fraud` to stderr and exit with code 1. If a scored row's label, after trimming spaces, is anything other than `0` or `1`, the system SHALL print an error to stderr that names the transaction id and the value, and exit with code 1. Labels on rows that ingest skips SHALL be ignored. When a transaction id repeats, the label SHALL come from the first row for that id, counting only rows that ingest keeps (the same row that is scored). Header names SHALL be matched the same way ingest matches them (trimmed, byte-order mark ignored). Ingest errors SHALL be reported as they are for `score`.

#### Scenario: Missing column
- **WHEN** the file has no `is_fraud` column
- **THEN** stderr is `error: missing required column: is_fraud` and the exit code is 1

#### Scenario: Bad label on a scored row
- **WHEN** scored transaction T5 has `is_fraud` value `2`
- **THEN** the exit code is 1 and the error names `T5` and `2`

#### Scenario: Bad label on a skipped row
- **WHEN** a row with an unparseable amount has `is_fraud` value `yes`
- **THEN** the command succeeds and that row is counted only as skipped

#### Scenario: Repeated id
- **WHEN** a transaction id appears twice, labelled `1` then `maybe`
- **THEN** the command succeeds and the transaction counts as fraud

#### Scenario: Repeated id after a malformed row
- **WHEN** a transaction id appears first on a row with an unparseable amount labelled `1`, then on a valid row labelled `0`
- **THEN** the valid row is the one scored and the transaction counts as not fraud
