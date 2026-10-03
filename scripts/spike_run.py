import csv, subprocess, sys, shutil

subprocess.run([sys.executable, "fraudsense.py", "score", "data/spike_slice.csv"], check=True)

with open("data/spike_slice.csv", newline="", encoding="utf-8") as f:
    fraud = {r["transaction_id"] for r in csv.DictReader(f) if r["is_fraud"] == "1"}
with open("reports/fraud_report.csv", newline="", encoding="utf-8") as f:
    flagged = [r["transaction_id"] for r in csv.DictReader(f)]

tp = sum(1 for t in flagged if t in fraud)
fp = len(flagged) - tp
precision = tp / len(flagged) if flagged else 0.0
recall = tp / len(fraud) if fraud else 0.0
print(f"flagged={len(flagged)} TP={tp} FP={fp} fraud_in_slice={len(fraud)} missed={len(fraud)-tp}")
print(f"precision={precision:.3f} recall={recall:.3f}")

shutil.copy("reports/fraud_report.csv", "reports/spike_fraud_report.csv")
