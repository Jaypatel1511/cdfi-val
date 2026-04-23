from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np

from cdfival.data.schema import BankProfile


@dataclass
class TBVResult:
    """Output object from TBV valuation."""
    bank_name: str
    tce: float
    shares: int
    multiples: list
    implied_equity: list
    implied_price: list
    peer_median: Optional[float] = None

    def summary(self) -> pd.DataFrame:
        rows = []
        for m, eq, pr in zip(self.multiples, self.implied_equity, self.implied_price):
            rows.append({
                "P/TBV Multiple": f"{m:.2f}x",
                "Implied Equity ($MM)": f"${eq/1e6:.1f}",
                "Implied Price ($/sh)": f"${pr:.4f}",
            })
        df = pd.DataFrame(rows)

        print(f"\nTBV Valuation — {self.bank_name}")
        print(f"TCE: ${self.tce/1e6:.1f}MM  |  Shares: {self.shares:,}")
        print("-" * 55)
        print(df.to_string(index=False))

        if self.peer_median is not None:
            peer_eq = self.tce * self.peer_median
            peer_pr = peer_eq / self.shares
            print("-" * 55)
            print(f"  Peer Median ({self.peer_median:.2f}x):  "
                  f"${peer_eq/1e6:.1f}MM   ${peer_pr:.4f}/sh")
        print()
        return df

    def to_dict(self) -> dict:
        return {
            "bank_name": self.bank_name,
            "tce": self.tce,
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
) -> TBVResult:
    """
    Compute implied equity value and share price across a P/TBV multiple range.

    Args:
        bank:           BankProfile instance
        multiple_range: (low, high) tuple of P/TBV multiples
        steps:          Number of points to evaluate (default 5)
        peer_median:    Optional peer group median multiple for benchmarking

    Returns:
        TBVResult object with .summary() and .to_dict() methods
    """
    tce = bank.tangible_common_equity

    if tce <= 0:
        raise ValueError(
            f"Cannot apply TBV multiple to non-positive TCE (got ${tce:,.0f}). "
            "Check your BankProfile inputs."
        )
    if bank.shares_outstanding <= 0:
        raise ValueError("shares_outstanding must be greater than zero.")

    low, high = multiple_range
    if low > high:
        low, high = high, low

    if steps < 2:
        steps = 5

    multiples = list(np.linspace(low, high, steps))
    implied_equity = [tce * m for m in multiples]
    implied_price = [eq / bank.shares_outstanding for eq in implied_equity]

    return TBVResult(
        bank_name=bank.name,
        tce=tce,
        shares=bank.shares_outstanding,
        multiples=multiples,
        implied_equity=implied_equity,
        implied_price=implied_price,
        peer_median=peer_median,
    )
