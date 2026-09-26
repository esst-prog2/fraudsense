"""Data types shared by every pipeline stage."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    customer_id: str
    amount: float
    timestamp: datetime


@dataclass(frozen=True)
class ScoredTransaction:
    transaction: Transaction
    # Mean amount of the customer's other transactions; None when the
    # amount rule could not be evaluated (too little history).
    average_spend: float | None
    amount_ratio: float | None
    # The customer's transactions in the window ending at this one, itself included.
    window_count: int
    fired: tuple[str, ...]
    reasons: tuple[str, ...]
    score: float
