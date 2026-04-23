import pytest
import pandas as pd
from cdfival.data.schema import BankProfile
from cdfival.models import pe


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


def test_basic_pe_range(sample_bank):
    result = pe.value(sample_bank, multiple_range=(8.0, 15.0), steps=5)
    assert len(result.multiples) == 5
    assert result.multiples[0] == pytest.approx(8.0)
    assert result.multiples[-1] == pytest.approx(15.0)


def test_implied_equity_math(sample_bank):
    result = pe.value(sample_bank, multiple_range=(10.0, 10.0), steps=1)
    expected = 2_100_000 * 10.0
    assert result.implied_equity[0] == pytest.approx(expected)


def test_implied_price_math(sample_bank):
    result = pe.value(sample_bank, multiple_range=(10.0, 10.0), steps=1)
    expected_price = (2_100_000 * 10.0) / 179_600_000
    assert result.implied_price[0] == pytest.approx(expected_price, rel=1e-4)


def test_negative_income_raises():
    bank = BankProfile(
        name="LossBank",
        total_assets=100_000_000,
        tangible_common_equity=10_000_000,
        shares_outstanding=10_000_000,
        net_income_ltm=-500_000,
        eps_ltm=-0.05,
        cet1_ratio=0.10,
    )
    with pytest.raises(ValueError, match="non-positive net income"):
        pe.value(bank, multiple_range=(8.0, 15.0))


def test_reversed_range_swaps(sample_bank):
    result = pe.value(sample_bank, multiple_range=(15.0, 8.0), steps=3)
    assert result.multiples[0] < result.multiples[-1]


def test_summary_returns_dataframe(sample_bank):
    result = pe.value(sample_bank, multiple_range=(8.0, 15.0), steps=5)
    df = result.summary()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5


def test_peer_median_stored(sample_bank):
    result = pe.value(sample_bank, multiple_range=(8.0, 15.0), peer_median=11.5)
    assert result.peer_median == 11.5


def test_to_dict_keys(sample_bank):
    result = pe.value(sample_bank, multiple_range=(8.0, 15.0))
    d = result.to_dict()
    assert "net_income" in d
    assert "implied_equity" in d
    assert "peer_median" in d
