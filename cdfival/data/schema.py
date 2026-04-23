from dataclasses import dataclass
from typing import Optional


@dataclass
class BankProfile:
    """
    Represents a single CDFI or MDI institution for valuation purposes.
    This is the core input object passed to all valuation modules.
    """
    name: str
    total_assets: float                    # in dollars, e.g. 700_000_000
    tangible_common_equity: float          # in dollars
    shares_outstanding: int
    net_income_ltm: float                  # last twelve months, in dollars
    eps_ltm: float                         # last twelve months, in dollars per share
    cet1_ratio: float                      # e.g. 0.12 for 12%
    ticker: Optional[str] = None
    fiscal_year_end: Optional[str] = None  # e.g. "2024-03-31"
    institution_type: Optional[str] = None # "CDFI", "MDI", or "CDFI/MDI"

    def __post_init__(self):
        if self.total_assets <= 0:
            raise ValueError("total_assets must be positive")
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be positive")
        if not (0 < self.cet1_ratio < 1):
            raise ValueError("cet1_ratio must be between 0 and 1 (e.g. 0.12 for 12%)")

    @property
    def assets_mm(self) -> float:
        """Total assets in millions."""
        return self.total_assets / 1_000_000

    @property
    def tce_mm(self) -> float:
        """Tangible common equity in millions."""
        return self.tangible_common_equity / 1_000_000

    def __repr__(self):
        return (
            f"BankProfile(name='{self.name}', "
            f"assets=${self.assets_mm:.1f}MM, "
            f"TCE=${self.tce_mm:.1f}MM, "
            f"shares={self.shares_outstanding:,})"
        )
