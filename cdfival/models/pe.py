from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np

from cdfival.data.schema import BankProfile


@dataclass
class PEResult:
    """Output object from P/E valuation."""
    bank_name: str
    net_income: float
    eps: float
    shares: int
    multiples: list
    implied_equity: list
    implied_price: list
    peer_median: Optional[float] = None

    def summary(self) -> pd.DataFrame:
        rows = []
        for m, eq, pr in zip(self.multiples, self.implied_equity, self.implied_price):
            rows.append({
                "P/E Multiple": f"{m:.1f}x",
                "Implied Equity ($MM)": f"${eq/1e6:.1f}",
                "Implied Price ($/sh)": f"${pr:.4f}",
            })
        df = pd.DataFrame(rows)

        print(f"\nP/E Valuation — {self.bank_name}")
        print(f"Net Income (LTM): ${self.net_income/1e6:.2f}MM  |  EPS: ${self.eps:.4f}  |  Shares: {self.shares:,}")
        print("-" * 60)
        print(df.to_string(index=False))

        if self.peer_median is not None:
            peer_eq = self.net_income * self.peer_median
            peer_pr = peer_eq / self.shares
            print("-" * 60)
            print(f"  Peer Median ({self.peer_median:.1f}x):  "
                  f"${peer_eq/1e6:.1f}MM   ${peer_pr:.4f}/sh")
        print()
        return df

    def to_dict(self) -> dict:
        return {
            "bank_name": self.bank_name,
            "net_income": self.net_income,
            "eps": self.eps,
            "shares": self.shares,
            "multiples": self.multiples,
            "implied_equity": self.implied_equity,
            "implied_price": self.implied_price,
            "peer_median": self.peer_median,
        }


def value(
    bank: BankProfile,
    multiple_range: tuple,
    steps: int = 5,
    peer_median: Optional[float] = None,
) -> PEResult:
    """
    Compute implied equity value and share price across a P/E multiple range.

    Args:
        bank:           BankProfile instance
        multiple_range: (low, high) tuple of P/E multiples e.g. (8.0, 15.0)
        steps:          Number of points to evaluate (default 5)
        peer_median:    Optional peer group median P/E for benchmarking

    Returns:
        PEResult object with .summary() and .to_dict() methods
    """
    net_income = bank.net_income_ltm

    if net_income <= 0:
        raise ValueError(
            f"Cannot apply P/E multiple to non-positive net income (got ${net_income:,.0f}). "
            "Consider using TBV or DCF method instead for loss-making institutions."
        )
    if bank.shares_outstanding <= 0:
        raise ValueError("shares_outstanding must be greater than zero.")

    low, high = multiple_range
    if low > high:
        low, high = high, low

    if steps < 2:
        steps = 5

    multiples = list(np.linspace(low, high, steps))
    implied_equity = [net_income * m for m in multiples]
    implied_price = [eq / bank.shares_outstanding for eq in implied_equity]

    return PEResult(
        bank_name=bank.name,
        net_income=net_income,
        eps=bank.eps_ltm,
        shares=bank.shares_outstanding,
        multiples=multiples,
        implied_equity=implied_equity,
        implied_price=implied_price,
        peer_median=peer_median,
    )
