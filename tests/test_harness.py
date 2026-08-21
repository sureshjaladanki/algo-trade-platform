"""H0: MDE printer, harness guard, trial ledger, deflated Sharpe, walk-forward."""

from pathlib import Path

import pytest

from src.harness import (
    MDE_RATIO_MAX,
    TRIAL_BUDGET,
    Declaration,
    HarnessGuardError,
    MdeGateError,
    TrialBudgetError,
    TrialLedger,
    deflated_sharpe,
    print_mde,
    purged_embargoed_splits,
    require_declared,
    reset,
    run_declared,
)
from src.hurdles import BOOK_A, BOOK_B, BOOK_C, PUBLISHED_BOOKS, books_clearing_mde_gate


def setup_function() -> None:
    reset()


def test_published_mde_table_clears_at_least_one_book() -> None:
    assert BOOK_C.mde == pytest.approx(0.0)
    assert BOOK_A.mde == pytest.approx(2.8 * 150.0 / (240**0.5))
    assert BOOK_A.mde_ratio == pytest.approx(BOOK_A.mde / 116.0)
    assert BOOK_A.mde_ratio <= MDE_RATIO_MAX
    assert BOOK_B.n_effective == pytest.approx(6_000)
    assert BOOK_B.mde == pytest.approx(2.8 * 800.0 / (6_000**0.5))
    assert BOOK_B.mde_ratio <= MDE_RATIO_MAX
    clearing = books_clearing_mde_gate()
    assert BOOK_C in clearing and BOOK_A in clearing and BOOK_B in clearing
    assert len(PUBLISHED_BOOKS) == 3
    for book in PUBLISHED_BOOKS:
        reset()
        print_mde(book)


def test_harness_guard_blocks_undeclared_test() -> None:
    with pytest.raises(HarnessGuardError):
        require_declared()
    with pytest.raises(HarnessGuardError):
        run_declared(lambda: 1)


def test_print_mde_then_run_is_allowed() -> None:
    print_mde(BOOK_A)
    assert run_declared(lambda: 42) == 42


def test_mde_gate_closes_without_peek() -> None:
    dead = Declaration(
        book_id="X",
        spec_id="X.unmeasurable",
        n=20,
        sigma=200.0,
        hypothesized_effect=30.0,
    )
    peeked = {"ran": False}

    def peek() -> None:
        peeked["ran"] = True

    with pytest.raises(MdeGateError):
        print_mde(dead)
    with pytest.raises(HarnessGuardError):
        run_declared(peek)
    assert peeked["ran"] is False


def test_purged_embargoed_splits_drop_overlap() -> None:
    folds = purged_embargoed_splits(100, n_folds=4, purge_size=5, embargo_size=3)
    assert len(folds) == 4
    for fold in folds:
        test_set = set(fold.test_index)
        train_set = set(fold.train_index)
        assert test_set.isdisjoint(train_set)
        start, stop = fold.test_index[0], fold.test_index[-1] + 1
        for i in fold.train_index:
            assert not (start - 5 <= i < start)
            assert not (stop <= i < stop + 3)


def test_deflated_sharpe_penalizes_trials() -> None:
    one = deflated_sharpe(0.4, n_obs=36, n_trials=1)
    five = deflated_sharpe(0.4, n_obs=36, n_trials=5)
    assert 0.0 < five < one < 1.0


def test_trial_ledger_budget_and_abandonment(tmp_path: Path) -> None:
    ledger = TrialLedger(path=tmp_path / "trial_ledger.jsonl")
    for i in range(TRIAL_BUDGET):
        ledger.register(spec_id=f"B.spec{i}", book_id="B", hypothesis="numeric surprise")
    with pytest.raises(TrialBudgetError):
        ledger.register(spec_id="B.spec5", book_id="B", hypothesis="sixth")
    ledger.abandon("B.spec4", "replaced by numeric-only")
    reloaded = TrialLedger.load(ledger.path)
    assert reloaded._count("B") == TRIAL_BUDGET
    abandoned = next(t for t in reloaded.trials if t.spec_id == "B.spec4")
    assert abandoned.status == "abandoned"
    assert abandoned.abandoned_reason == "replaced by numeric-only"
