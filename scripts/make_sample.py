"""Generate data/sample_transactions.csv: 500 synthetic transactions with planted anomalies.

    python scripts/make_sample.py

The generator is seeded, so running it twice writes an identical file. It
prints the planted anomalies so you can check they show up in the report.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
TOTAL_ROWS = 500
START = datetime(2026, 9, 1)
DAYS = 7
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_transactions.csv"
COLUMNS = ["transaction_id", "timestamp", "customer_id", "amount", "location", "payment_method"]

REGULAR_CUSTOMERS = 37
# Too little history for the amount rule (it needs 3 *other* transactions).
SHORT_HISTORY = {"C038": 2, "C039": 3, "C040": 1}
AMOUNT_SPIKES = 6      # one transaction at 7-12x the customer's typical spend
BURSTS = 4             # 5-7 transactions inside 8 minutes
SPIKES_IN_BURST = 2    # a burst whose last transaction is also a spike

CITIES = ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Bristol", "Cardiff", "Belfast"]
PAYMENT_METHODS = ["credit_card", "debit_card", "mobile_wallet", "bank_transfer"]


class Generator:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.rows = []
        self.planted = []

    def profile(self, customer_id):
        return {
            "customer_id": customer_id,
            "typical": self.rng.uniform(20, 600),
            "city": self.rng.choice(CITIES),
            "method": self.rng.choice(PAYMENT_METHODS),
        }

    def random_time(self):
        day = self.rng.randrange(DAYS)
        seconds = self.rng.randrange(7 * 3600, 23 * 3600)  # 07:00 to 23:00
        return START + timedelta(days=day, seconds=seconds)

    def add(self, profile, amount, timestamp):
        rng = self.rng
        row = {
            "customer_id": profile["customer_id"],
            "amount": round(amount, 2),
            "timestamp": timestamp,
            "location": profile["city"] if rng.random() < 0.9 else rng.choice(CITIES),
            "payment_method": profile["method"] if rng.random() < 0.85 else rng.choice(PAYMENT_METHODS),
        }
        self.rows.append(row)
        return row

    def normal_amount(self, profile):
        return profile["typical"] * self.rng.uniform(0.7, 1.3)

    def spike_amount(self, profile):
        return profile["typical"] * self.rng.uniform(7, 12)

    def add_normal(self, profile, count):
        for _ in range(count):
            self.add(profile, self.normal_amount(profile), self.random_time())

    def add_spike(self, profile):
        row = self.add(profile, self.spike_amount(profile), self.random_time())
        self.planted.append(("amount spike", [row]))

    def add_burst(self, profile, with_spike):
        size = self.rng.randint(5, 7)
        start = self.random_time()
        offsets = [0] + sorted(self.rng.sample(range(1, 8 * 60 + 1), size - 1))
        rows = []
        for i, offset in enumerate(offsets):
            last = i == size - 1
            amount = self.spike_amount(profile) if with_spike and last else self.normal_amount(profile)
            rows.append(self.add(profile, amount, start + timedelta(seconds=offset)))
        self.planted.append(("burst + spike" if with_spike else "burst", rows))
        return size

    def build(self):
        rng = self.rng
        regular = [self.profile(f"C{n:03d}") for n in range(1, REGULAR_CUSTOMERS + 1)]
        anomalous = rng.sample(regular, AMOUNT_SPIKES + BURSTS + SPIKES_IN_BURST)
        spikes = anomalous[:AMOUNT_SPIKES]
        bursts = anomalous[AMOUNT_SPIKES:AMOUNT_SPIKES + BURSTS]
        burst_spikes = anomalous[AMOUNT_SPIKES + BURSTS:]

        for profile in spikes:
            self.add_spike(profile)
        for profile in bursts:
            self.add_burst(profile, with_spike=False)
        for profile in burst_spikes:
            self.add_burst(profile, with_spike=True)

        # Short-history customers; C039's big purchase must NOT be flagged.
        for customer_id, count in SHORT_HISTORY.items():
            profile = self.profile(customer_id)
            self.add_normal(profile, count - 1)
            amount = self.spike_amount(profile) if customer_id == "C039" else self.normal_amount(profile)
            self.add(profile, amount, self.random_time())

        # Fill the rest of the 500 rows with ordinary spending.
        remaining = TOTAL_ROWS - len(self.rows)
        base, extra = divmod(remaining, REGULAR_CUSTOMERS)
        lucky = set(p["customer_id"] for p in rng.sample(regular, extra))
        for profile in regular:
            self.add_normal(profile, base + (1 if profile["customer_id"] in lucky else 0))

        self.rows.sort(key=lambda r: (r["timestamp"], r["customer_id"]))
        for n, row in enumerate(self.rows, start=1):
            row["transaction_id"] = f"T{n:05d}"


def write(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([
                row["transaction_id"],
                row["timestamp"].isoformat(),
                row["customer_id"],
                f"{row['amount']:.2f}",
                row["location"],
                row["payment_method"],
            ])


def main():
    generator = Generator(SEED)
    generator.build()
    write(generator.rows, OUTPUT)
    print(f"Wrote {len(generator.rows)} transactions to {OUTPUT.relative_to(OUTPUT.parent.parent).as_posix()}")
    print(f"Planted {len(generator.planted)} anomalies:")
    for kind, rows in generator.planted:
        ids = ", ".join(r["transaction_id"] for r in rows)
        print(f"  {kind:<14} {rows[0]['customer_id']}  {ids}")


if __name__ == "__main__":
    main()
