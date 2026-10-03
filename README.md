# Explainable Fraud Detection for Transactions

*This is for whoever has to manually sift through a transaction export looking for fraud — the report gives them a shortlist of the transactions worth a closer look, instead of scanning everything by hand.*

## 1. The demo

I run `python fraudsense.py score data/sample_transactions.csv`. It cleans the data, scores all 500 transactions, and prints:

```
Scored 500 transactions in 0.01s.
18 flagged as high-risk (score > 0.75).
Report written to reports/fraud_report.csv.
```

I open `reports/fraud_report.csv` and see the 18 flagged rows, each with a transaction id, a risk score, and a short reason. I then run `python fraudsense.py explain --id T00101` on one of them, and it prints the features that pushed the score up:

```
Transaction T00101 - risk score 0.89
  amount $622.04 is 7.2x this customer's average ($86)
  7 transactions in the last 10 minutes (rule fires at 5)
```

The sample file is synthetic, with planted anomalies; `python scripts/make_sample.py` regenerates it identically. Python 3.10+ is all it needs, and `python -m unittest discover tests` runs the tests.

## 2. The shape


in            a CSV of transactions — amount, timestamp, customer_id,
              location, payment_method

out           a report of flagged transactions, each with a risk score
              and the top reasons it was flagged

in between    clean and validate the data; build per-customer behavioural
              features (typical spend, transaction frequency, location
              and payment-method patterns); score each transaction with
              a trained model plus a few simple rules; keep the
              highest-scoring transactions and their reasons


Model training and comparison happens once, offline, before this pipeline runs on new data — it is not something that happens on every run.

The first version scores with rules only; the trained model is a planned future change.

## 3. The size

**First useful version (rules only)**

* Reads a transaction CSV and cleans it, exiting with a clear error if a required column is missing.
* Computes per-customer behavioural features: typical spend and transaction frequency.
* Applies a small set of rule-based checks (e.g. an amount far above the customer's average, many transactions in a short window).
* Writes `reports/fraud_report.csv` listing the high-risk transactions, their scores and reasons.
* Lets me look up any transaction by id and see the specific features and rules behind its score.

**Future changes**

* Scores every transaction with a trained ML model, chosen by comparing at least two candidate models offline using precision, recall, F1 and PR-AUC.
* Location and payment-method features.
* Richer explanations beyond the rule reasons.

**Not this term**

* Real-time fraud detection.
* Connecting to a real bank or payment system.
* Blocking transactions automatically.
* Using real private customer data.
* Building a full web application.
* Deploying the system online.
* Making it work on millions of transactions.

## 4. How we would know it works

1. Given a file missing a required column (e.g. amount or customer_id), the program exits with an error naming the missing column.
2. Given a test file containing an obviously unusual transaction an amount far above a customer's typical spend, or many transactions in a short time window — that transaction receives a risk score higher than the file's normal transactions.
3. Given a transaction flagged as high-risk, selecting it shows the specific features or rules that pushed its score up (e.g. "amount 8x customer average" or "5 transactions in 10 minutes").

## 5. What could stop this

The biggest risk is the data. Real bank transaction data is not available to me, so I will use a public dataset or build a small synthetic one if the public data does not contain the fields I need. Either way, the data and results can be shown in class.

Fraud cases are usually far less common than normal transactions, so accuracy alone would give a misleading picture — I will rely on precision, recall, F1 and PR-AUC instead.

I do not yet know which behavioural features will hold up on the dataset I choose — for example, I may not have enough history to calculate a reliable "normal spending pattern" per customer. I will adapt the features to what the data actually supports rather than forcing ones it can't.

The explanation feature is also untested territory. If model-based explanations turn out to be too complex for the first version, I will fall back to explanations based on the rules and the model's raw feature weights.

The rule thresholds are not validated yet. On a slice of Sparkov (simulated data), the amount rule at 5x flagged 500 rows, of which 68 were true positives: precision 0.136, recall 0.433. The velocity rule never fired. So I no longer treat the 5x default as validated, and a threshold study is the next change. See `reports/spike_counts.txt`.
