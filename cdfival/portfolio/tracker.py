from typing import Optional
import pandas as pd

from cdfival.data.schema import BankProfile
from cdfival.models import tbv, pe, dcf


class ValuationTracker:
    """
    Aggregate TBV, P/E, and DCF valuations across a portfolio of
    CDFI and MDI institutions into a single summary table.
    """

    def __init__(self):
        self._banks: list[BankProfile] = []

    def add(self, bank: BankProfile) -> None:
        """Add a BankProfile to the portfolio."""
        if not isinstance(bank, BankProfile):
            raise TypeError("Only BankProfile objects can be added to the tracker.")
        if any(b.name == bank.name for b in self._banks):
            raise ValueError(f"'{bank.name}' is already in the portfolio.")
        self._banks.append(bank)

    def remove(self, name: str) -> None:
        """Remove a bank by name."""
        self._banks = [b for b in self._banks if b.name != name]

    def count(self) -> int:
        """Return number of institutions in the portfolio."""
        return len(self._banks)

    def names(self) -> list:
        """Return list of institution names."""
        return [b.name for b in self._banks]

    def summary_table(
        self,
        method: str = "tbv",
        multiple_range: tuple = (0.5, 1.0),
        steps: int = 3,
        wacc: float = 0.10,
        terminal_growth: float = 0.025,
        projection_years: int = 5,
        peer_median: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Run the chosen valuation method across all banks and return
        a consolidated summary DataFrame.

        Args:
            method:          "tbv", "pe", or "dcf"
            multiple_range:  (low, high) for tbv/pe methods
            steps:           Number of multiple steps (tbv/pe only)
            wacc:            Discount rate for DCF
            terminal_growth: Terminal growth rate for DCF
            projection_years: Projection horizon for DCF
            peer_median:     Optional peer median multiple (tbv/pe only)

        Returns:
            pandas DataFrame with one row per institution
        """
        if method not in ("tbv", "pe", "dcf"):
            raise ValueError("method must be 'tbv', 'pe', or 'dcf'")
        if not self._banks:
            raise ValueError("No banks in portfolio. Use .add() to add institutions.")

        rows = []
        skipped = []

        for bank in self._banks:
            try:
                if method == "tbv":
                    result = tbv.value(bank, multiple_range=multiple_range,
                                       steps=steps, peer_median=peer_median)
                    mid = len(result.implied_price) // 2
                    rows.append({
                        "Institution": bank.name,
                        "Ticker": bank.ticker or "—",
                        "Type": bank.institution_type or "—",
                        "Assets ($MM)": round(bank.assets_mm, 1),
                        "TCE ($MM)": round(bank.tce_mm, 1),
                        f"P/TBV Low ({multiple_range[0]:.2f}x)": f"${result.implied_price[0]:.4f}",
                        f"P/TBV Mid ({result.multiples[mid]:.2f}x)": f"${result.implied_price[mid]:.4f}",
                        f"P/TBV High ({multiple_range[1]:.2f}x)": f"${result.implied_price[-1]:.4f}",
                    })

                elif method == "pe":
                    result = pe.value(bank, multiple_range=multiple_range,
                                      steps=steps, peer_median=peer_median)
                    mid = len(result.implied_price) // 2
                    rows.append({
                        "Institution": bank.name,
                        "Ticker": bank.ticker or "—",
                        "Type": bank.institution_type or "—",
                        "Assets ($MM)": round(bank.assets_mm, 1),
                        "Net Income ($MM)": round(bank.net_income_ltm / 1e6, 2),
                        f"P/E Low ({multiple_range[0]:.1f}x)": f"${result.implied_price[0]:.4f}",
                        f"P/E Mid ({result.multiples[mid]:.1f}x)": f"${result.implied_price[mid]:.4f}",
                        f"P/E High ({multiple_range[1]:.1f}x)": f"${result.implied_price[-1]:.4f}",
                    })

                elif method == "dcf":
                    result = dcf.value(bank, wacc=wacc,
                                       terminal_growth=terminal_growth,
                                       projection_years=projection_years)
                    rows.append({
                        "Institution": bank.name,
                        "Ticker": bank.ticker or "—",
                        "Type": bank.institution_type or "—",
                        "Assets ($MM)": round(bank.assets_mm, 1),
                        "WACC": f"{wacc*100:.1f}%",
                        "Terminal Growth": f"{terminal_growth*100:.1f}%",
                        "Implied Equity ($MM)": round(result.implied_equity / 1e6, 2),
                        "Implied Price ($/sh)": f"${result.implied_price:.4f}",
                    })

            except ValueError as e:
                skipped.append({"Institution": bank.name, "Reason": str(e)})

        df = pd.DataFrame(rows)

        if skipped:
            print(f"\n⚠️  Skipped {len(skipped)} institution(s):")
            for s in skipped:
                print(f"   - {s['Institution']}: {s['Reason']}")

        return df

    def all_methods(
        self,
        tbv_range: tuple = (0.5, 1.0),
        pe_range: tuple = (8.0, 15.0),
        wacc: float = 0.10,
        terminal_growth: float = 0.025,
    ) -> dict:
        """
        Run all three valuation methods and return a dict of DataFrames.

        Returns:
            {"tbv": df, "pe": df, "dcf": df}
        """
        return {
            "tbv": self.summary_table(method="tbv", multiple_range=tbv_range),
            "pe":  self.summary_table(method="pe",  multiple_range=pe_range),
            "dcf": self.summary_table(method="dcf", wacc=wacc,
                                      terminal_growth=terminal_growth),
        }
