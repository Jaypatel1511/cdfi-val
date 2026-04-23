from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np

from cdfival.data.schema import BankProfile


@dataclass
class DCFResult:
    """Output object from DCF valuation."""
    bank_name: str
    shares: int
    wacc: float
    terminal_growth: float
    projection_years: int
    projected_earnings: list
    discount_factors: list
    pv_earnings: list
    terminal_value: float
    pv_terminal_value: float
    implied_equity: float
    implied_price: float
    peer_median_price: Optional[float] = None

    def summary(self) -> pd.DataFrame:
        rows = []
        for yr, earn, df, pv in zip(
            range(1, self.projection_years + 1),
            self.projected_earnings,
            self.discount_factors,
            self.pv_earnings,
        ):
            rows.append({
                "Year": f"Y{yr}",
                "Projected Earnings ($MM)": f"${earn/1e6:.2f}",
                "Discount Factor": f"{df:.4f}",
                "PV of Earnings ($MM)": f"${pv/1e6:.2f}",
            })

        df = pd.DataFrame(rows)

        print(f"\nDCF Valuation — {self.bank_name}")
        print(f"WACC: {self.wacc*100:.1f}%  |  Terminal Growth: {self.terminal_growth*100:.1f}%  |  Years: {self.projection_years}")
        print("-" * 65)
        print(df.to_string(index=False))
        print("-" * 65)
        print(f"  Terminal Value:           ${self.terminal_value/1e6:.2f}MM")
        print(f"  PV of Terminal Value:     ${self.pv_terminal_value/1e6:.2f}MM")
        print(f"  PV of Projected Earnings: ${sum(self.pv_earnings)/1e6:.2f}MM")
        print(f"  ── Implied Equity Value:  ${self.implied_equity/1e6:.2f}MM")
        print(f"  ── Implied Share Price:   ${self.implied_price:.4f}/sh")
        print()
        return df

    def to_dict(self) -> dict:
        return {
            "bank_name": self.bank_name,
            "wacc": self.wacc,
            "terminal_growth": self.terminal_growth,
            "projection_years": self.projection_years,
            "projected_earnings": self.projected_earnings,
            "pv_earnings": self.pv_earnings,
            "terminal_value": self.terminal_value,
            "pv_terminal_value": self.pv_terminal_value,
            "implied_equity": self.implied_equity,
            "implied_price": self.implied_price,
        }


def value(
    bank: BankProfile,
    wacc: float,
    terminal_growth: float,
    projection_years: int = 5,
    earnings_growth_rate: Optional[float] = None,
) -> DCFResult:
    """
    Compute implied equity value via Discounted Cash Flow analysis.

    Projects net income forward, applies a Gordon Growth terminal value,
    and discounts all cash flows back at WACC.

    Args:
        bank:                 BankProfile instance
        wacc:                 Discount rate e.g. 0.10 for 10%
        terminal_growth:      Perpetual growth rate e.g. 0.025 for 2.5%
        projection_years:     Number of years to project (default 5)
        earnings_growth_rate: Annual earnings growth rate. If None, defaults
                              to (wacc + terminal_growth) / 2 as a midpoint estimate.

    Returns:
        DCFResult object with .summary() and .to_dict() methods
    """
    if wacc <= 0 or wacc >= 1:
        raise ValueError("wacc must be between 0 and 1 (e.g. 0.10 for 10%)")
    if terminal_growth <= 0 or terminal_growth >= wacc:
        raise ValueError(
            "terminal_growth must be positive and less than wacc "
            "(e.g. 0.025 for 2.5% when wacc is 0.10)"
        )
    if projection_years < 1:
        raise ValueError("projection_years must be at least 1")
    if bank.net_income_ltm <= 0:
        raise ValueError(
            "DCF requires positive net income as the base earnings figure. "
            "Check your BankProfile inputs."
        )

    # Default growth rate: midpoint between WACC and terminal growth
    growth = earnings_growth_rate if earnings_growth_rate is not None \
        else (wacc + terminal_growth) / 2

    # Project earnings
    projected_earnings = [
        bank.net_income_ltm * ((1 + growth) ** yr)
        for yr in range(1, projection_years + 1)
    ]

    # Discount factors
    discount_factors = [
        1 / ((1 + wacc) ** yr)
        for yr in range(1, projection_years + 1)
    ]

    # PV of projected earnings
    pv_earnings = [e * d for e, d in zip(projected_earnings, discount_factors)]

    # Terminal value (Gordon Growth Model) at end of projection period
    terminal_value = (projected_earnings[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value * discount_factors[-1]

    # Implied equity and price
    implied_equity = sum(pv_earnings) + pv_terminal_value
    implied_price = implied_equity / bank.shares_outstanding

    return DCFResult(
        bank_name=bank.name,
        shares=bank.shares_outstanding,
        wacc=wacc,
        terminal_growth=terminal_growth,
        projection_years=projection_years,
        projected_earnings=projected_earnings,
        discount_factors=discount_factors,
        pv_earnings=pv_earnings,
        terminal_value=terminal_value,
        pv_terminal_value=pv_terminal_value,
        implied_equity=implied_equity,
        implied_price=implied_price,
    )
