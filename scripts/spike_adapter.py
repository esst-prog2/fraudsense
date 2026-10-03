import csv, sys, collections

SRC, DST = sys.argv[1], sys.argv[2]
N_CUSTOMERS = 20

counts = collections.Counter()
with open(SRC, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        counts[r["cc_num"]] += 1
total = sum(counts.values())
enough = sum(c for c in counts.values() if c >= 4)
print(f"rows={total} customers={len(counts)}")
print(f"share of rows whose customer has >=4 transactions: {enough/total:.3f}")

keep = set(sorted(counts)[:N_CUSTOMERS])
rows = fraud = 0
with open(SRC, newline="", encoding="utf-8") as f, \
     open(DST, "w", newline="", encoding="utf-8") as out:
    w = csv.writer(out)
    w.writerow(["transaction_id", "amount", "timestamp",
                "customer_id", "location", "payment_method", "is_fraud"])
    for r in csv.DictReader(f):
        if r["cc_num"] in keep:
            w.writerow([r["trans_num"], r["amt"], r["trans_date_trans_time"],
                        r["cc_num"], r["city"], r["category"], r["is_fraud"]])
            rows += 1
            fraud += r["is_fraud"] == "1"
print(f"slice: customers={len(keep)} rows={rows} fraud_rows={fraud}")
