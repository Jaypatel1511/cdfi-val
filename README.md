# cdfi-val 🏦

**Institutional-grade valuation toolkit for CDFIs and Minority Depository Institutions.**

Built for investment analysts, IC teams, and impact finance practitioners who need
reproducible, auditable valuation outputs — without starting from scratch in Excel.

---

## Why cdfi-val?

Community banks, CDFIs, and MDIs are consistently underserved by open-source finance
tooling. Existing Python libraries target derivatives, public equities, and trading —
not mission-driven depositories where valuation requires:

- Tangible Book Value multiples calibrated to peer community banks
- P/E analysis on thin or volatile earnings bases
- DCF models with WACC and terminal growth inputs
- Comparable transaction analysis across precedent MDI/CDFI deals
- Portfolio-level aggregation across 10-12 institutions

cdfi-val fills that gap.

---

## Installation

    pip install cdfi-val

---

## Quickstart

    from cdfival import BankProfile, tbv, pe, dcf

    bank = BankProfile(
        name="Broadway Financial Corporation",
        ticker="BYFC",
        total_assets=655_000_000,
        tangible_common_equity=48_000_000,
        shares_outstanding=142_500_000,
        net_income_ltm=1_950_000,
        eps_ltm=0.014,
        cet1_ratio=0.122,
        institution_type="CDFI/MDI",
    )

    result = tbv.value(bank, multiple_range=(0.5, 0.9))
    result.summary()

    result = pe.value(bank, multiple_range=(8.0, 16.0))
    result.summary()

    result = dcf.value(bank, wacc=0.10, terminal_growth=0.025, projection_years=5)
    result.summary()

---

## Portfolio Mode

    from cdfival import BankProfile, ValuationTracker

    tracker = ValuationTracker()
    tracker.add(bank1)
    tracker.add(bank2)

    df = tracker.summary_table(method="tbv", multiple_range=(0.5, 1.0))
    print(df)

    results = tracker.all_methods(
        tbv_range=(0.5, 1.0),
        pe_range=(8.0, 15.0),
        wacc=0.10,
        terminal_growth=0.025,
    )

---

## Comparable Transactions

    from cdfival.models.comps import ComparableTransaction, value

    transactions = [
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
    ]

    result = value(bank, transactions, metric="tbv")
    result.summary()

---

## Valuation Methodologies

- Tangible Book Value (models.tbv) — TCE, shares outstanding, P/TBV range
- Price / Earnings (models.pe) — Net income, EPS, P/E range
- Discounted Cash Flow (models.dcf) — WACC, terminal growth, projection years
- Comparable Transactions (models.comps) — Precedent deal multiples, TBV or P/E metric

---

## Who This Is For

- CDFI Fund staff reviewing investment proposals
- Impact investors conducting IC-level diligence on MDIs
- Analysts at CDFIs building valuation models for equity transactions
- Researchers studying community bank valuations at scale

---

## Running Tests

    PYTHONPATH=. pytest tests/ -v

46 tests across all modules.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss what you'd like to change.

---

## License

MIT 2026 Jaypatel1511
