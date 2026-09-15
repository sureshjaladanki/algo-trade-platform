"""L0 placement refusals, ₹1 recon, IST calendar, paper sessions, plus GL0 gates."""

import logging
from datetime import date, datetime, time
from decimal import Decimal

import pytest

from src.execute import (
    IST,
    AuthState,
    CliffMarginRefused,
    Fill,
    Instruction,
    LedgerLine,
    Order,
    OrderError,
    OrderType,
    PaperBroker,
    RateLimiter,
    ScreenResult,
    SessionPhase,
    SessionWindowRefused,
    Side,
    format_instruction_list,
    parse_instruction_list,
    screen,
    session_phase,
)
from src.ops import (
    BOOK_A_REVIEW,
    IDLE_CASH_ALERT_DAYS,
    IDLE_CASH_LIMIT_DAYS,
    DeskState,
    KillSwitch,
    bse_expiry_session,
    calendar_flags,
    gl_calendar_items,
    idle_offshore_cash,
    is_session,
    join_daily_artefact,
    morning_gate,
    nse_expiry_session,
    nse_monthly_expiry,
    reconcile,
    run_note,
    write_run_log,
)
from src.receipt import NonUsReceiptBlocked
from src.residency import rnor_cliff, ror_start
from src.settlement import (
    LSE_T1_SWITCH,
    ExposureClass,
    Venue,
    latest_safe_trade_date,
    uk_bst_start,
)
from src.situs import SitusCapBlocked, UkRegisterRefused


def _order(**kwargs: object) -> Order:
    fields: dict[str, object] = {
        "trade_date": date(2028, 3, 17),
        "venue": Venue.LSE,
        "exposure_class": ExposureClass.US_EXPOSURE,
        "london_time": time(15, 0),
        "settlement_country": "US",
        "uk_register": False,
        "us_situs_book_usd": 0.0,
    }
    fields.update(kwargs)
    return Order(**fields)  # type: ignore[arg-type]


def _sell(**kwargs: object) -> Instruction:
    base: dict[str, object] = {
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
    return Instruction(**base)  # type: ignore[arg-type]


def test_session_phases() -> None:
    assert session_phase(datetime(2026, 9, 7, 9, 2, tzinfo=IST)) is SessionPhase.PRE_OPEN_1
    assert session_phase(datetime(2026, 9, 7, 9, 7, tzinfo=IST)) is SessionPhase.PRE_OPEN_2
    assert session_phase(datetime(2026, 9, 4, 9, 7, tzinfo=IST)) is SessionPhase.PRE_OPEN_1
    assert session_phase(datetime(2026, 9, 7, 10, 0, tzinfo=IST)) is SessionPhase.CONTINUOUS
    assert session_phase(datetime(2026, 9, 7, 15, 22, tzinfo=IST)) is SessionPhase.CAS
    assert session_phase(datetime(2026, 9, 7, 16, 15, tzinfo=IST)) is SessionPhase.CLOSED


def test_refuse_stale_token_and_auth() -> None:
    from src.execute import assert_auth

    with pytest.raises(OrderError, match="token"):
        assert_auth(AuthState(True, True, True, date(2026, 9, 6), "NSEALGO1"), date(2026, 9, 7))
    with pytest.raises(OrderError, match="static IP"):
        assert_auth(AuthState(False, True, True, date(2026, 9, 7), "NSEALGO1"), date(2026, 9, 7))


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


def test_printed_list_round_trips() -> None:
    instruction = _sell(sector="")
    text = format_instruction_list(date(2026, 9, 7), (instruction,))
    assert parse_instruction_list(text) == [instruction]


def test_kill_switch_blocks() -> None:
    state = DeskState(kill=KillSwitch(killed=True, reason="halt"))
    assert morning_gate(state, reconcile([], [])) is False
    assert run_note(state)


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


def test_paper_broker_records_a_fill() -> None:
    broker = PaperBroker()
    fill = broker.execute(_sell(), Decimal(1000))
    assert fill.rupees == Decimal("1000.00")
    assert reconcile(broker.fills, broker.ledger).ok
    limiter = RateLimiter()
    clock = datetime(2026, 9, 7, 10, 0, tzinfo=IST)
    for _ in range(8):
        limiter.admit(clock)
    with pytest.raises(OrderError, match="8/second"):
        limiter.admit(clock)


def test_refuses_us_exposure_at_1100_london() -> None:
    with pytest.raises(SessionWindowRefused):
        screen(_order(london_time=time(11, 0)))


def test_allows_1100_under_logged_cliff_margin_override(caplog: pytest.LogCaptureFixture) -> None:
    order = _order(
        london_time=time(11, 0),
        override="cliff_margin",
        override_reason="GL-H3 last safe day outranks the overlap window",
    )
    with caplog.at_level(logging.INFO):
        result = screen(order)
    assert result == ScreenResult(
        allowed=True,
        override="cliff_margin",
        reason="GL-H3 last safe day outranks the overlap window",
    )
    assert "cliff-margin override" in caplog.text


def test_n6_receipt_has_no_override() -> None:
    with pytest.raises(NonUsReceiptBlocked):
        screen(
            _order(
                settlement_country="IN",
                override="cliff_margin",
                override_reason="cannot override N6",
            )
        )


def test_n5_situs_has_no_override() -> None:
    with pytest.raises(SitusCapBlocked):
        screen(
            _order(
                us_situs_book_usd=60_000.0,
                us_situs_additional_usd=1.0,
                override="cliff_margin",
                override_reason="cannot override N5",
            )
        )


def test_uk_register_has_no_override() -> None:
    with pytest.raises(UkRegisterRefused):
        screen(_order(uk_register=True, override="session_window", override_reason="no"))


def test_30_mar_2028_lse_is_refused_as_cliff_straddle() -> None:
    with pytest.raises(CliffMarginRefused):
        screen(_order(trade_date=date(2028, 3, 30), london_time=time(15, 0)))


def test_idle_cash_alerts_at_120_on_synthetic_balance() -> None:
    idle_since = date(2027, 1, 1)
    at_alert = idle_offshore_cash(
        balance_usd=25_000.0, idle_since=idle_since, as_of=date(2027, 5, 1)
    )
    assert at_alert.days == IDLE_CASH_ALERT_DAYS
    assert at_alert.alert
    assert not at_alert.limit_breached
    before = idle_offshore_cash(
        balance_usd=25_000.0, idle_since=idle_since, as_of=date(2027, 4, 30)
    )
    assert before.days == 119
    assert not before.alert
    at_limit = idle_offshore_cash(
        balance_usd=25_000.0, idle_since=idle_since, as_of=date(2027, 6, 30)
    )
    assert at_limit.days == IDLE_CASH_LIMIT_DAYS
    assert at_limit.limit_breached


def test_gl_calendar_items() -> None:
    items = {item.key: item.on for item in gl_calendar_items()}
    assert items["rnor_cliff"] == rnor_cliff()
    assert items["ror_start"] == ror_start()
    assert items["latest_safe_trade_date"] == latest_safe_trade_date(rnor_cliff())
    assert items["lse_t1_switch"] == LSE_T1_SWITCH
    assert items["uk_bst_2028"] == uk_bst_start(2028)


def test_join_artefact_dual_rnor_ror_and_fa_count(tmp_path) -> None:
    from decimal import Decimal

    from src.books.ledger import Lot as IndiaLot
    from src.household import AlienLot, from_desks, usd_rate

    as_of = date(2026, 9, 14)
    fx = usd_rate(Decimal("95.69"), source="yahoo_usdinr_working", as_of=as_of)
    ledger = from_desks(
        india=[
            IndiaLot(
                symbol="N50",
                quantity=Decimal(1),
                acquired=date(2025, 4, 1),
                cost_per_share=Decimal(1000),
                price=Decimal(1000),
            )
        ],
        alien=[
            AlienLot(
                lot_id="a1",
                symbol="CSPX",
                acquired=date(2025, 7, 15),
                usd_cost=Decimal("100.00"),
                usd_value=Decimal("110.00"),
                fx_cost=fx,
                fx_value=fx,
            ),
            AlienLot(
                lot_id="a2",
                symbol="XUSE",
                acquired=date(2025, 8, 1),
                usd_cost=Decimal("50.00"),
                usd_value=Decimal("55.00"),
                fx_cost=fx,
                fx_value=fx,
            ),
        ],
        as_of=as_of,
    )
    artefact = join_daily_artefact(as_of=as_of, ledger=ledger)
    assert artefact["fa_line_count"] == 2
    assert artefact["fa_lines"] == ("CSPX", "XUSE")
    assert artefact["book_j"]["rnor"] == "0"
    assert artefact["book_j"]["ror"] == "65000"
    assert artefact["book_j"]["governs"] == artefact["book_j"]["ror"]
    assert "working" in str(artefact["total_india_exposure_source"])
    state = DeskState()
    state.note("join")
    path = tmp_path / "run.log"
    write_run_log(path, state, as_of, join=artefact)
    text = path.read_text(encoding="utf-8")
    assert "fa_line_count" in text
    assert "65000" in text

