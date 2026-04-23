import pytest
import pandas as pd
from cdfival.data.schema import BankProfile
from cdfival.portfolio.tracker import ValuationTracker


@pytest.fixture
def bank_a():
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
def bank_b():
    return BankProfile(
        name="Harbor Community Bank",
        ticker="HCB",
        total_assets=500_000_000,
        tangible_common_equity=38_000_000,
        shares_outstanding=90_000_000,
        net_income_ltm=1_800_000,
        eps_ltm=0.020,
        cet1_ratio=0.110,
        institution_type="CDFI",
    )


@pytest.fixture
def tracker(bank_a, bank_b):
    t = ValuationTracker()
    t.add(bank_a)
    t.add(bank_b)
    return t


def test_add_and_count(bank_a, bank_b):
    t = ValuationTracker()
    t.add(bank_a)
    assert t.count() == 1
    t.add(bank_b)
    assert t.count() == 2


def test_duplicate_raises(bank_a):
    t = ValuationTracker()
    t.add(bank_a)
    with pytest.raises(ValueError, match="already in the portfolio"):
        t.add(bank_a)


def test_remove(tracker, bank_a):
    tracker.remove(bank_a.name)
    assert tracker.count() == 1
    assert bank_a.name not in tracker.names()


def test_tbv_summary_returns_dataframe(tracker):
    df = tracker.summary_table(method="tbv", multiple_range=(0.5, 1.0), steps=3)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_pe_summary_returns_dataframe(tracker):
    df = tracker.summary_table(method="pe", multiple_range=(8.0, 15.0), steps=3)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_dcf_summary_returns_dataframe(tracker):
    df = tracker.summary_table(method="dcf", wacc=0.10, terminal_growth=0.025)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_invalid_method_raises(tracker):
    with pytest.raises(ValueError, match="method must be"):
        tracker.summary_table(method="ev_ebitda")


def test_empty_tracker_raises():
    t = ValuationTracker()
    with pytest.raises(ValueError, match="No banks in portfolio"):
        t.summary_table(method="tbv")


def test_all_methods_returns_dict(tracker):
    results = tracker.all_methods()
    assert set(results.keys()) == {"tbv", "pe", "dcf"}
    for df in results.values():
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2


def test_institution_column_present(tracker):
    df = tracker.summary_table(method="tbv", multiple_range=(0.5, 1.0), steps=3)
    assert "Institution" in df.columns
    assert "Carver Federal Savings Bank" in df["Institution"].values
