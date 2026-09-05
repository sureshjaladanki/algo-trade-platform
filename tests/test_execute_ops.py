"""L0: placement refusals, ₹1 recon, IST calendar, paper sessions."""

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import polars as pl
import pytest

from src.books.ledger import Lot
from src.execute import (
    IST,
    AuthState,
    Fill,
    Instruction,
    LedgerLine,
    OrderError,
    OrderType,
    PaperBroker,
    RateLimiter,
    SessionPhase,
    Side,
    format_instruction_list,
    parse_instruction_list,
    place,
    session_phase,
)
from src.ops import (
    BOOK_A_REVIEW,
    DeskState,
    KillSwitch,
    bse_expiry_session,
    calendar_flags,
    is_session,
    morning_gate,
    next_sessions,
    nse_expiry_session,
    nse_monthly_expiry,
    paper_day,
    reconcile,
    replay_printed_list,
    run_note,
)
from src.portfolio import DESIGN_EQUITY
from src.universe import load_flag_intervals

AUTH = AuthState(
    static_ip_ok=True,
    oauth_ok=True,
    two_fa_ok=True,
    token_date=date(2026, 9, 7),
    algo_id="NSEALGO1",
)
CONTINUOUS = datetime(2026, 9, 7, 10, 0, tzinfo=IST)
SIGMA = {"N50": Decimal("0.01")}


def _flags(rows: list[dict] | None = None) -> pl.DataFrame:
    empty = load_flag_intervals(Path("missing-flags.csv"))
    if not rows:
        return empty
    return pl.DataFrame(rows)


def _lot() -> Lot:
    return Lot(
        symbol="N50",
        quantity=Decimal(100),
        acquired=date(2025, 1, 2),
        cost_per_share=Decimal(800),
        price=Decimal(1000),
        sector="IT",
        sleeve="core",
    )


def _sell(**kwargs) -> Instruction:
    base = {
        "symbol": "N50",
        "side": Side.SELL,
        "quantity": Decimal(1),
        "order_type": OrderType.LIMIT,
        "limit_price": Decimal(1000),
        "algo_id": "NSEALGO1",
        "phase": SessionPhase.CONTINUOUS,
        "notional": Decimal("1000.00"),
        "sleeve": "core",
        "sector": "IT",
    }
    base.update(kwargs)
    return Instruction(**base)


def _place(instruction: Instruction, **kwargs):
    defaults = {
        "auth": AUTH,
        "clock": CONTINUOUS,
        "limiter": RateLimiter(),
        "lots": [_lot()],
        "equity": DESIGN_EQUITY,
        "daily_sigma": SIGMA,
        "flag_intervals": _flags(),
        "broker": PaperBroker(),
    }
    defaults.update(kwargs)
    return place(instruction, **defaults)


def test_session_phases() -> None:
    assert session_phase(datetime(2026, 9, 7, 9, 2, tzinfo=IST)) is SessionPhase.PRE_OPEN_1
    assert session_phase(datetime(2026, 9, 7, 9, 7, tzinfo=IST)) is SessionPhase.PRE_OPEN_2
    assert session_phase(datetime(2026, 9, 4, 9, 7, tzinfo=IST)) is SessionPhase.PRE_OPEN_1
    assert session_phase(datetime(2026, 9, 7, 10, 0, tzinfo=IST)) is SessionPhase.CONTINUOUS
    assert session_phase(datetime(2026, 9, 7, 15, 22, tzinfo=IST)) is SessionPhase.CAS
    assert session_phase(datetime(2026, 9, 7, 16, 15, tzinfo=IST)) is SessionPhase.CLOSED


def test_refuse_untagged_order() -> None:
    with pytest.raises(OrderError, match="untagged"):
        _place(_sell(algo_id=""))
    with pytest.raises(OrderError, match="untagged"):
        _place(_sell(algo_id="OTHER"))


def test_refuse_stale_token_and_auth() -> None:
    with pytest.raises(OrderError, match="token"):
        _place(_sell(), auth=AuthState(True, True, True, date(2026, 9, 6), "NSEALGO1"))
    with pytest.raises(OrderError, match="static IP"):
        _place(_sell(), auth=AuthState(False, True, True, date(2026, 9, 7), "NSEALGO1"))


def test_refuse_market_in_pre_open_phase_2() -> None:
    clock = datetime(2026, 9, 7, 9, 7, tzinfo=IST)
    with pytest.raises(OrderError, match="market order"):
        _place(
            _sell(order_type=OrderType.MARKET, phase=SessionPhase.PRE_OPEN_2),
            clock=clock,
        )


def test_refuse_ninth_order_same_second() -> None:
    limiter = RateLimiter()
    broker = PaperBroker()
    for _ in range(8):
        _place(_sell(), limiter=limiter, broker=broker)
    with pytest.raises(OrderError, match="8/second"):
        _place(_sell(), limiter=limiter, broker=broker)


def test_refuse_esm_stage_two_and_fno_ban() -> None:
    esm = _flags(
        [
            {
                "symbol": "N50",
                "start": date(2026, 9, 1),
                "end": date(2026, 9, 30),
                "esm_stage": 2,
                "gsm_stage": 0,
                "price_band_pct": 2.0,
                "in_fno_ban": False,
                "fno_eligible": False,
            }
        ]
    )
    with pytest.raises(OrderError, match="ESM"):
        _place(_sell(), flag_intervals=esm)
    ban = _flags(
        [
            {
                "symbol": "N50",
                "start": date(2026, 9, 1),
                "end": date(2026, 9, 30),
                "esm_stage": 0,
                "gsm_stage": 0,
                "price_band_pct": 20.0,
                "in_fno_ban": True,
                "fno_eligible": True,
            }
        ]
    )
    with pytest.raises(OrderError, match="ban"):
        _place(_sell(), flag_intervals=ban)


def test_refuse_name_limit_plus_one_rupee() -> None:
    cap = DESIGN_EQUITY * Decimal("0.06")
    buy = Instruction(
        symbol="NEW",
        side=Side.BUY,
        quantity=Decimal(1),
        order_type=OrderType.LIMIT,
        limit_price=cap + Decimal("1.00"),
        algo_id="NSEALGO1",
        phase=SessionPhase.CONTINUOUS,
        notional=cap + Decimal("1.00"),
        sleeve="core",
        sector="IT",
    )
    with pytest.raises(OrderError, match="single name"):
        _place(buy, lots=[], daily_sigma={"NEW": Decimal("0.01")})


def test_recon_breaks_block_instructions() -> None:
    fills = [
        Fill(
            symbol="N50",
            side=Side.SELL,
            quantity=Decimal(1),
            price=Decimal(1000),
            rupees=Decimal("1000.00"),
            algo_id="NSEALGO1",
        )
    ]
    ledger = [
        LedgerLine(symbol="N50", side=Side.SELL, quantity=Decimal(1), rupees=Decimal("1002.00"))
    ]
    recon = reconcile(fills, ledger)
    assert not recon.ok
    assert recon.residual == Decimal("2.00")
    state = DeskState()
    assert morning_gate(state, recon) is False
    assert "RECON FAIL" in state.log[0]


def test_printed_list_matches_automated_path() -> None:
    instruction = _sell(sector="")
    text = format_instruction_list(date(2026, 9, 7), (instruction,))
    auto = PaperBroker()
    hand = PaperBroker()
    _place(instruction, broker=auto)
    replay_printed_list(
        text,
        auth=AUTH,
        clock=CONTINUOUS,
        lots=[_lot()],
        equity=DESIGN_EQUITY,
        daily_sigma=SIGMA,
        flag_intervals=_flags(),
        broker=hand,
    )
    assert parse_instruction_list(text) == [instruction]
    assert reconcile(auto.fills, hand.ledger).ok


def test_twenty_paper_sessions_zero_recon_breaks() -> None:
    sessions = next_sessions(date(2026, 9, 7), 20)
    assert len(sessions) == 20
    lots = [_lot()]
    targets = {"N50": Decimal(1)}
    flags = _flags()
    broker = PaperBroker()
    state = DeskState()
    for session in sessions:
        auth = replace(AUTH, token_date=session)
        clock = datetime(session.year, session.month, session.day, 10, 0, tzinfo=IST)
        ok, _instructions = paper_day(
            session,
            lots=lots,
            target_weights=targets,
            auth=auth,
            equity=DESIGN_EQUITY,
            daily_sigma=SIGMA,
            flag_intervals=flags,
            state=state,
            broker=broker,
            clock=clock,
            prior_fills=list(broker.fills),
            prior_ledger=list(broker.ledger),
        )
        assert ok
        assert state.last_recon is not None
        assert state.last_recon.ok
        assert state.last_recon.residual <= Decimal("1.00")
    assert run_note(state)


def test_kill_switch_blocks() -> None:
    state = DeskState(kill=KillSwitch(killed=True, reason="halt"))
    assert morning_gate(state, reconcile([], [])) is False


def test_calendar_nse_holiday_and_shifted_expiry() -> None:
    assert not is_session(date(2026, 9, 14))
    assert is_session(date(2026, 9, 7))
    assert is_session(date(2026, 11, 8))
    assert nse_expiry_session(date(2026, 9, 8))
    assert not nse_expiry_session(date(2026, 9, 7))
    assert bse_expiry_session(date(2026, 9, 10))
    assert nse_expiry_session(date(2026, 3, 2))
    assert not nse_expiry_session(date(2026, 3, 3))
    assert nse_monthly_expiry(date(2026, 3, 30))
    flags = calendar_flags(date(2026, 2, 1))
    assert flags["budget"] is True
    assert calendar_flags(date(2026, 4, 8))["mpc"] is True
    assert calendar_flags(BOOK_A_REVIEW)["book_a_review"] is True
    assert calendar_flags(date(2026, 3, 31))["tax_year_boundary"] is True
