import csv, collections

rows = list(csv.DictReader(open("data/spike_slice.csv", newline="", encoding="utf-8")))
tot = collections.defaultdict(float)
n = collections.Counter()
for r in rows:
    tot[r["customer_id"]] += float(r["amount"])
    n[r["customer_id"]] += 1

fires = fires_fraud = 0
for r in rows:
    c = r["customer_id"]
    others = n[c] - 1
    if others < 3:
        continue
    avg = (tot[c] - float(r["amount"])) / others
    if avg > 0 and round(float(r["amount"]) / avg, 6) >= 5:
        fires += 1
        fires_fraud += r["is_fraud"] == "1"
print(f"independent check: amount >=5x average of customer's other rows: {fires} rows, {fires_fraud} are fraud")
