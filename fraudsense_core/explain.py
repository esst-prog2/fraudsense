"""Explain one transaction's score."""

from fraudsense_core.features import MIN_OTHER_TRANSACTIONS
from fraudsense_core.rules import AMOUNT_RATIO_THRESHOLD, amount_reason, velocity_reason


class ExplainError(Exception):
    """The requested transaction can't be explained."""


def find_transaction(scored, transaction_id):
    for s in scored:
        if s.transaction.transaction_id == transaction_id:
            return s
    raise ExplainError(f"transaction {transaction_id} not found among the valid transactions")


def format_explanation(s):
    txn = s.transaction
    lines = [f"Transaction {txn.transaction_id} - risk score {s.score:.2f}"]
    if s.reasons:
        lines += [f"  {reason}" for reason in s.reasons]
        return "\n".join(lines)

    lines.append("  no rule fired")
    if s.amount_ratio is None:
        lines.append(
            "  amount rule not evaluated: this customer needs at least "
            f"{MIN_OTHER_TRANSACTIONS} other transactions in the file"
        )
    else:
        lines.append(
            f"  {amount_reason(txn.amount, s.average_spend, s.amount_ratio)} "
            f"(rule fires at {AMOUNT_RATIO_THRESHOLD:g}x)"
        )
    lines.append(f"  {velocity_reason(s.window_count)}")
    return "\n".join(lines)
