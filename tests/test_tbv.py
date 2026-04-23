import pytest
import pandas as pd
from cdfival.data.schema import BankProfile
from cdfival.models import tbv


@pytest.fixture
def sample_bank():
    return BankProfile(
        name="Carver Federal Savings Bank",
        ticker="CARV",
        total_assets=700_000_000,
        tangible_common_equity=45_000_000,
        shares_outstanding=179_600_000,
        net_income_ltm=2_100_000,
        eps_ltm=0.012,
        cet1_ratio=0.118,
        institution_type="MDI",
    )


def test_basic_tbv_range(sample_bank):
    result = tbv.value(sample_bank, multiple_range=(0.5, 0.9), steps=5)
    assert len(result.multiples) == 5
    assert result.multiples[0] == pytest.approx(0.5)
    assert result.multiples[-1] == pytest.approx(0.9)


def test_implied_equity_math(sample_bank):
    result = tbv.value(sample_bank, multiple_range=(0.5, 0.5), steps=1)
    expected = 45_000_000 * 0.5
    assert result.implied_equity[0] == pytest.approx(expected)


def test_implied_price_math(sample_bank):
    result = tbv.value(sample_bank, multiple_range=(1.0, 1.0), steps=1)
    expected_price = 45_000_000 / 179_600_000
    assert result.implied_price[0] == pytest.approx(expected_price, rel=1e-4)


def test_negative_tce_raises():
    bank = BankProfile(
        name="BadBank",
        total_assets=100_000_000,
        tangible_common_equity=-1_000_000,
        shares_outstanding=10_000_000,
        net_income_ltm=500_000,
        eps_ltm=0.05,
        cet1_ratio=0.10,
    )
    with pytest.raises(ValueError, match="non-positive TCE"):
        tbv.value(bank, multiple_range=(0.5, 0.9))


def test_reversed_range_swaps(sample_bank):
    result = tbv.value(sample_bank, multiple_range=(0.9, 0.5), steps=3)
    assert result.multiples[0] < result.multiples[-1]


def test_summary_returns_dataframe(sample_bank):
    result = tbv.value(sample_bank, multiple_range=(0.5, 0.9), steps=5)
    df = result.summary()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5


def test_peer_median_stored(sample_bank):
    result = tbv.value(sample_bank, multiple_range=(0.5, 0.9), peer_median=0.72)
    assert result.peer_median == 0.72


def test_to_dict_keys(sample_bank):
    result = tbv.value(sample_bank, multiple_range=(0.5, 0.9))
    d = result.to_dict()
    assert "implied_equity" in d
    assert "implied_price" in d
    assert "peer_median" in d
