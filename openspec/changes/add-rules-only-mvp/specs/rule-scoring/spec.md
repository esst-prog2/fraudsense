## Purpose

Computes per-customer behavioural features and applies simple, explainable rules to give every transaction a risk score between 0 and 1, with the reasons behind it.

## ADDED Requirements

### Requirement: Average-spend feature
For each transaction, the system SHALL compute the customer's average spend as the mean `amount` of that customer's other valid transactions in the same file, excluding the transaction itself. The amount ratio is the transaction's `amount` divided by that average.

#### Scenario: Transaction excluded from its own average
- **WHEN** a customer has transactions of 100, 100, 100 and 800
- **THEN** the average spend used for the 800 transaction is 100, and its amount ratio is 8

### Requirement: Amount rule needs enough history
The amount rule SHALL only be evaluated when the customer has at least 3 other valid transactions in the file. With fewer, the amount rule MUST NOT fire and MUST NOT contribute to the score.

#### Scenario: New customer with one large transaction
- **WHEN** a customer has only 2 transactions in the file, one of them for 5,000
- **THEN** the amount rule does not fire for either transaction

### Requirement: Amount rule
The amount rule SHALL fire when a transaction's amount ratio is 5 or more.

#### Scenario: Amount at the threshold
- **WHEN** a customer's average spend over other transactions is 100 and a transaction's amount is 500
- **THEN** the amount rule fires for that transaction

#### Scenario: Amount below the threshold
- **WHEN** a customer's average spend is 100 and a transaction's amount is 490
- **THEN** the amount rule does not fire

### Requirement: Velocity feature and rule
For each transaction, the system SHALL count the same customer's valid transactions whose timestamp falls within the 10 minutes ending at this transaction's timestamp, including the transaction itself. The velocity rule SHALL fire when that count is 5 or more.

#### Scenario: Burst of transactions
- **WHEN** a customer makes 6 transactions within 8 minutes
- **THEN** the velocity rule fires for the 5th and 6th of them and does not fire for the first 4

#### Scenario: Transactions spread out
- **WHEN** a customer makes 6 transactions, each 15 minutes apart
- **THEN** the velocity rule fires for none of them

### Requirement: Combined risk score
Every valid transaction SHALL receive a risk score between 0 and 1 inclusive. A transaction's score MUST be greater than 0.75 if and only if at least one rule fires for it. Among transactions where no rule fires, a higher amount ratio or a higher 10-minute count MUST NOT give a lower score. Among transactions where a rule fires, a more extreme amount ratio or count MUST NOT give a lower score.

#### Scenario: Unusual transaction outranks normal ones
- **WHEN** a file contains a customer with several transactions near their usual amount and one transaction at 8 times their average
- **THEN** the unusual transaction's score is higher than every one of that customer's normal transactions
- **AND** it is greater than 0.75

#### Scenario: No rule fires
- **WHEN** neither rule fires for a transaction
- **THEN** its score is 0.75 or less

### Requirement: Reasons for fired rules
For every rule that fires, the system SHALL produce a one-line, human-readable reason stating the observed value and the customer's baseline. Examples: `amount $4,200 is 8.0x this customer's average ($525)` and `6 transactions in the last 10 minutes (rule fires at 5)`.

#### Scenario: Both rules fire
- **WHEN** both the amount rule and the velocity rule fire for a transaction
- **THEN** the transaction has two reasons, one for each rule
