import pytest
import pandas as pd
from cdfival.data.schema import BankProfile
from cdfival.models import dcf


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


def test_basic_dcf_runs(sample_bank):
    result = dcf.value(sample_bank, wacc=0.10, terminal_growth=0.025)
    assert result.implied_equity > 0
    assert result.implied_price > 0


def test_projection_years_count(sample_bank):
    result = dcf.value(sample_bank, wacc=0.10, terminal_growth=0.025, projection_years=7)
    assert len(result.projected_earnings) == 7
    assert len(result.pv_earnings) == 7


def test_implied_price_math(sample_bank):
    result = dcf.value(sample_bank, wacc=0.10, terminal_growth=0.025)
    expected_price = result.implied_equity / sample_bank.shares_outstanding
    assert result.implied_price == pytest.approx(expected_price, rel=1e-6)


def test_terminal_value_positive(sample_bank):
    result = dcf.value(sample_bank, wacc=0.10, terminal_growth=0.025)
    assert result.terminal_value > 0
    assert result.pv_terminal_value > 0


def test_wacc_invalid_raises(sample_bank):
    with pytest.raises(ValueError, match="wacc must be between"):
        dcf.value(sample_bank, wacc=1.5, terminal_growth=0.025)


def test_terminal_growth_exceeds_wacc_raises(sample_bank):
    with pytest.raises(ValueError, match="less than wacc"):
        dcf.value(sample_bank, wacc=0.10, terminal_growth=0.15)


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
    with pytest.raises(ValueError, match="positive net income"):
        dcf.value(bank, wacc=0.10, terminal_growth=0.025)


def test_summary_returns_dataframe(sample_bank):
    result = dcf.value(sample_bank, wacc=0.10, terminal_growth=0.025)
    df = result.summary()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5


def test_to_dict_keys(sample_bank):
    result = dcf.value(sample_bank, wacc=0.10, terminal_growth=0.025)
    d = result.to_dict()
    assert "implied_equity" in d
    assert "terminal_value" in d
    assert "pv_terminal_value" in d


def test_custom_growth_rate(sample_bank):
    result = dcf.value(sample_bank, wacc=0.10, terminal_growth=0.025, earnings_growth_rate=0.05)
    assert result.projected_earnings[0] == pytest.approx(2_100_000 * 1.05, rel=1e-6)
