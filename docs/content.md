# fraudsense

**A shortlist of the transactions worth a second look, each with the reason it was picked.**

fraudsense is a command-line program. You give it a CSV export of transactions. It gives back the ones that look unusual for the customer who made them, with a risk score and a one-line reason in plain words.

[Get it on GitHub](https://github.com/esst-prog2/fraudsense)

## What it is for

Finding fraud in a transaction export by hand means reading every row. fraudsense reads every row for you and hands back a short list to check.

It compares each transaction with the same customer's own history and applies two rules:

- **Unusual amount.** The amount is at least 5 times that customer's average.
- **Burst of activity.** The customer made 5 or more transactions within 10 minutes.

Every flagged transaction comes with the reason it was flagged:

```
Transaction T00101 - risk score 0.89
  amount $622.04 is 7.2x this customer's average ($86)
  7 transactions in the last 10 minutes (rule fires at 5)
```

There is no model to trust blindly. If a transaction is on the list, you can see which rule put it there and by how much.

## Who it is for

- Anyone who has to go through a transaction export looking for fraud and wants a shortlist instead of the whole file.
- Students and teachers who want a small, readable example of rule-based fraud detection with honest numbers attached.

It is not a production fraud system. It does not run in real time, connect to a bank or payment system, or block anything. It reads a file and writes a report.

## How to try it

You need Python 3.10 or newer. There is nothing else to install.

```
git clone https://github.com/esst-prog2/fraudsense.git
cd fraudsense
python fraudsense.py score data/sample_transactions.csv
```

This scores the 500 sample transactions that come with the repository and prints:

```
Scored 500 transactions in 0.04s.
18 flagged as high-risk (score > 0.75).
Report written to reports/fraud_report.csv.
```

The time on the first line varies from run to run. Open `reports/fraud_report.csv` to see the 18 flagged transactions with their scores and reasons. To see why one of them was flagged:

```
python fraudsense.py explain --id T00101
```

To use your own file, pass it to `score`. It needs four columns: `transaction_id`, `customer_id`, `amount` and `timestamp`. If one is missing, the program stops and names the missing column.

The sample file is synthetic, with unusual transactions planted in it on purpose. No real customer data is in the repository.

## How well it works: the honest scoreboard

The sample file is easy, because the unusual transactions were planted for the rules to find. A fairer test is data the rules were not written for.

fraudsense was run on 26,658 transactions from 20 customers in the [Sparkov credit card dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection). That dataset is simulated, not real bank data, and each transaction is labeled as fraud or not fraud. 157 of the 26,658 are fraud.

| | Count |
| --- | --- |
| Transactions flagged | 500 |
| Flagged and really fraud | 68 |
| Flagged but not fraud | 432 |
| Fraud that was missed | 89 |

- **Precision 0.136.** About 1 flagged transaction in 7 was really fraud.
- **Recall 0.433.** It caught 68 of the 157 frauds, and missed more than half.
- All 500 flags came from the unusual-amount rule. The burst rule did not fire at all on this data.

These are weak results, and they are stated here on purpose. The thresholds, 5 times the average and 5 transactions in 10 minutes, are starting values. They have not been tuned or validated. Treat the shortlist as a place to start looking, not as a verdict.

You can reproduce the numbers yourself. The labeled slice is in the repository:

```
python fraudsense.py evaluate data/spike_slice.csv
```

It prints the same measurement at five score cutoffs:

```
Evaluated 26658 transactions against the is_fraud labels: 157 fraud, 26501 not fraud.

cutoff  flagged  TP   FP   FN  precision  recall     F1
  0.75      500  68  432   89      0.136   0.433  0.207
  0.80      500  68  432   89      0.136   0.433  0.207
  0.85      291  55  236  102      0.189   0.350  0.246
  0.90      223  52  171  105      0.233   0.331  0.274
  0.95      175  48  127  109      0.274   0.306  0.289
```

TP is fraud that was flagged, FP is a false alarm, and FN is fraud that was missed. A stricter cutoff raises fewer false alarms and misses more fraud: at 0.95 about 1 flag in 4 is real, but only 48 of the 157 frauds are caught.

## Get it

The code, the sample data and the tests are on GitHub: [github.com/esst-prog2/fraudsense](https://github.com/esst-prog2/fraudsense)
