import pytest
import pandas as pd
from cdfival.data.schema import BankProfile
from cdfival.models.comps import ComparableTransaction, value


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


@pytest.fixture
def sample_transactions():
    return [
        ComparableTransaction(
            acquiree_name="Unity Bank",
            deal_date="2021-04-01",
            deal_value=36_000_000,
            acquiree_tce=45_000_000,
            acquiree_net_income=2_000_000,
            acquiree_total_assets=500_000_000,
            institution_type="MDI",
        ),
        ComparableTransaction(
            acquiree_name="Harbor Community Bank",
            deal_date="2022-08-15",
            deal_value=56_000_000,
            acquiree_tce=70_000_000,
            acquiree_net_income=3_500_000,
            acquiree_total_assets=650_000_000,
            institution_type="CDFI",
        ),
        ComparableTransaction(
            acquiree_name="Beacon MDI Bank",
            deal_date="2023-03-22",
            deal_value=32_000_000,
            acquiree_tce=40_000_000,
            acquiree_net_income=1_800_000,
            acquiree_total_assets=420_000_000,
            institution_type="MDI",
        ),
    ]


def test_ptbv_multiple_math(sample_transactions):
    t = sample_transactions[0]
    assert t.ptbv_multiple == pytest.approx(36_000_000 / 45_000_000)


def test_pe_multiple_math(sample_transactions):
    t = sample_transactions[0]
    assert t.pe_multiple == pytest.approx(36_000_000 / 2_000_000)


def test_basic_tbv_comps(sample_bank, sample_transactions):
    result = value(sample_bank, sample_transactions, metric="tbv")
    assert result.median_multiple > 0
    assert result.implied_equity_median > 0
    assert result.implied_price_median > 0


def test_basic_pe_comps(sample_bank, sample_transactions):
    result = value(sample_bank, sample_transactions, metric="pe")
    assert result.median_multiple > 0
    assert result.implied_equity_median > 0


def test_invalid_metric_raises(sample_bank, sample_transactions):
    with pytest.raises(ValueError, match="metric must be"):
        value(sample_bank, sample_transactions, metric="ev_ebitda")


def test_too_few_transactions_raises(sample_bank, sample_transactions):
    with pytest.raises(ValueError, match="At least 2"):
        value(sample_bank, [sample_transactions[0]], metric="tbv")


def test_summary_returns_dataframe(sample_bank, sample_transactions):
    result = value(sample_bank, sample_transactions, metric="tbv")
    df = result.summary()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3


def test_to_dict_keys(sample_bank, sample_transactions):
    result = value(sample_bank, sample_transactions, metric="tbv")
    d = result.to_dict()
    assert "median_multiple" in d
    assert "implied_equity_median" in d
    assert "implied_price_median" in d


def test_low_less_than_high(sample_bank, sample_transactions):
    result = value(sample_bank, sample_transactions, metric="tbv")
    assert result.low_multiple <= result.high_multiple


def test_median_within_range(sample_bank, sample_transactions):
    result = value(sample_bank, sample_transactions, metric="tbv")
    assert result.low_multiple <= result.median_multiple <= result.high_multiple
