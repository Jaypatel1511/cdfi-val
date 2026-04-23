from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np

from cdfival.data.schema import BankProfile


@dataclass
class ComparableTransaction:
    """Represents a single precedent transaction in the comps table."""
    acquiree_name: str
    deal_date: str                        # e.g. "2022-06-15"
    deal_value: float                     # total deal value in dollars
    acquiree_tce: float                   # tangible common equity at deal time
    acquiree_net_income: float            # LTM net income at deal time
    acquiree_total_assets: float          # total assets at deal time
    institution_type: Optional[str] = None  # "CDFI", "MDI", "CDFI/MDI"

    @property
    def ptbv_multiple(self) -> float:
        """Price-to-Tangible-Book-Value multiple implied by the deal."""
        if self.acquiree_tce <= 0:
            raise ValueError(f"Cannot compute P/TBV for {self.acquiree_name}: TCE <= 0")
        return self.deal_value / self.acquiree_tce

    @property
    def pe_multiple(self) -> Optional[float]:
        """Price-to-Earnings multiple implied by the deal."""
        if self.acquiree_net_income <= 0:
            return None
        return self.deal_value / self.acquiree_net_income

    @property
    def assets_mm(self) -> float:
        return self.acquiree_total_assets / 1_000_000


@dataclass
class CompsResult:
    """Output object from comparable transactions analysis."""
    bank_name: str
    shares: int
    transactions: list
    metric: str                    # "tbv" or "pe"
    multiples: list
    median_multiple: float
    mean_multiple: float
    low_multiple: float
    high_multiple: float
    implied_equity_median: float
    implied_equity_low: float
    implied_equity_high: float
    implied_price_median: float
    implied_price_low: float
    implied_price_high: float

    def summary(self) -> pd.DataFrame:
        rows = []
        for t, m in zip(self.transactions, self.multiples):
            rows.append({
                "Acquiree": t.acquiree_name,
                "Date": t.deal_date,
                "Assets ($MM)": f"${t.assets_mm:.0f}",
                f"{'P/TBV' if self.metric == 'tbv' else 'P/E'} Multiple": f"{m:.2f}x",
            })
        df = pd.DataFrame(rows)

        label = "P/TBV" if self.metric == "tbv" else "P/E"
        print(f"\nComparable Transactions — {self.bank_name}")
        print(f"Metric: {label}  |  Transactions: {len(self.transactions)}")
        print("-" * 60)
        print(df.to_string(index=False))
        print("-" * 60)
        print(f"  Low    ({self.low_multiple:.2f}x):  ${self.implied_equity_low/1e6:.1f}MM   ${self.implied_price_low:.4f}/sh")
        print(f"  Median ({self.median_multiple:.2f}x):  ${self.implied_equity_median/1e6:.1f}MM   ${self.implied_price_median:.4f}/sh")
        print(f"  Mean   ({self.mean_multiple:.2f}x):  ${(self._base()*self.mean_multiple)/1e6:.1f}MM")
        print(f"  High   ({self.high_multiple:.2f}x):  ${self.implied_equity_high/1e6:.1f}MM   ${self.implied_price_high:.4f}/sh")
        print()
        return df

    def _base(self):
        """Internal: return the base metric of the subject bank (used for mean equity)."""
        return self.implied_equity_median / self.median_multiple

    def to_dict(self) -> dict:
        return {
            "bank_name": self.bank_name,
            "metric": self.metric,
            "median_multiple": self.median_multiple,
            "mean_multiple": self.mean_multiple,
            "low_multiple": self.low_multiple,
            "high_multiple": self.high_multiple,
            "implied_equity_median": self.implied_equity_median,
            "implied_price_median": self.implied_price_median,
            "implied_equity_low": self.implied_equity_low,
            "implied_equity_high": self.implied_equity_high,
        }


def value(
    bank: BankProfile,
    transactions: list,
    metric: str = "tbv",
) -> CompsResult:
    """
    Compute implied equity value based on precedent comparable transactions.

    Args:
        bank:         BankProfile instance for the subject institution
        transactions: List of ComparableTransaction objects
        metric:       "tbv" to use P/TBV multiples, "pe" to use P/E multiples

    Returns:
        CompsResult object with .summary() and .to_dict() methods
    """
    if metric not in ("tbv", "pe"):
        raise ValueError("metric must be 'tbv' or 'pe'")
    if len(transactions) < 2:
        raise ValueError("At least 2 comparable transactions are required.")

    # Extract multiples
    if metric == "tbv":
        multiples = [t.ptbv_multiple for t in transactions]
        base = bank.tangible_common_equity
        if base <= 0:
            raise ValueError("Cannot apply TBV comps: subject bank TCE <= 0")
    else:
        multiples = [t.pe_multiple for t in transactions]
        if any(m is None for m in multiples):
            raise ValueError(
                "One or more transactions have non-positive net income. "
                "Cannot compute P/E multiple. Use metric='tbv' instead."
            )
        base = bank.net_income_ltm
        if base <= 0:
            raise ValueError("Cannot apply P/E comps: subject bank net income <= 0")

    median_m = float(np.median(multiples))
    mean_m   = float(np.mean(multiples))
    low_m    = float(np.min(multiples))
    high_m   = float(np.max(multiples))

    def price(eq): return eq / bank.shares_outstanding

    return CompsResult(
        bank_name=bank.name,
        shares=bank.shares_outstanding,
        transactions=transactions,
        metric=metric,
        multiples=multiples,
        median_multiple=median_m,
        mean_multiple=mean_m,
        low_multiple=low_m,
        high_multiple=high_m,
        implied_equity_median=base * median_m,
        implied_equity_low=base * low_m,
        implied_equity_high=base * high_m,
        implied_price_median=price(base * median_m),
        implied_price_low=price(base * low_m),
        implied_price_high=price(base * high_m),
    )
