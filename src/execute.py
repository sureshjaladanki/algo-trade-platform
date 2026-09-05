"""L0 instruction lists and placement. Paper venue only until L0 exits (L7, L8)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import ROUND_DOWN, Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

import polars as pl

from src.books.ledger import Lot
from src.portfolio import LimitError, SchedulerResult, assert_portfolio
from src.universe import flags_as_of

IST = ZoneInfo("Asia/Kolkata")
MAX_ORDERS_PER_SECOND = 8
PHASE2_START = date(2026, 9, 7)
PAISE = Decimal("0.01")


class OrderError(Exception):
    """An order was refused before it left the desk."""


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class SessionPhase(StrEnum):
    PRE_OPEN_1 = "pre_open_1"
    PRE_OPEN_2 = "pre_open_2"
    CONTINUOUS = "continuous"
    CAS = "cas"
    CLOSED = "closed"


@dataclass(frozen=True)
class AuthState:
    static_ip_ok: bool
    oauth_ok: bool
    two_fa_ok: bool
    token_date: date
    algo_id: str


@dataclass(frozen=True)
class Instruction:
    symbol: str
    side: Side
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal
    algo_id: str
    phase: SessionPhase
    notional: Decimal
    sleeve: str = "core"
    sector: str = ""


@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    quantity: Decimal
    price: Decimal
    rupees: Decimal
    algo_id: str


@dataclass(frozen=True)
class LedgerLine:
    symbol: str
    side: Side
    quantity: Decimal
    rupees: Decimal


class RateLimiter:
    """Count placements on the broker-server calendar second (TOPS)."""

    def __init__(self) -> None:
        self._stamps: list[datetime] = []

    def admit(self, clock: datetime) -> None:
        second = clock.replace(microsecond=0)
        self._stamps = [stamp for stamp in self._stamps if stamp.replace(microsecond=0) == second]
        if len(self._stamps) >= MAX_ORDERS_PER_SECOND:
            raise OrderError("order-rate cap 8/second")
        self._stamps.append(clock)


class PaperBroker:
    """In-process fills. No network, no live capital."""

    def __init__(self) -> None:
        self.fills: list[Fill] = []
        self.ledger: list[LedgerLine] = []

    def execute(self, instruction: Instruction, fill_price: Decimal) -> Fill:
        rupees = (instruction.quantity * fill_price).quantize(PAISE)
        fill = Fill(
            symbol=instruction.symbol,
            side=instruction.side,
            quantity=instruction.quantity,
            price=fill_price,
            rupees=rupees,
            algo_id=instruction.algo_id,
        )
        self.fills.append(fill)
        self.ledger.append(
            LedgerLine(
                symbol=instruction.symbol,
                side=instruction.side,
                quantity=instruction.quantity,
                rupees=rupees,
            )
        )
        return fill


def now_ist(clock: datetime | None = None) -> datetime:
    if clock is None:
        return datetime.now(tz=IST)
    if clock.tzinfo is None:
        return clock.replace(tzinfo=IST)
    return clock.astimezone(IST)


def session_phase(clock: datetime | None = None) -> SessionPhase:
    stamp = now_ist(clock)
    t = stamp.time()
    if time(9, 0) <= t < time(9, 5):
        return SessionPhase.PRE_OPEN_1
    if time(9, 5) <= t < time(9, 15):
        if stamp.date() >= PHASE2_START:
            return SessionPhase.PRE_OPEN_2
        return SessionPhase.PRE_OPEN_1
    if time(9, 15) <= t < time(15, 20):
        return SessionPhase.CONTINUOUS
    if time(15, 20) <= t < time(15, 35):
        return SessionPhase.CAS
    return SessionPhase.CLOSED


def assert_auth(auth: AuthState, as_of: date) -> None:
    if not auth.static_ip_ok:
        raise OrderError("static IP whitelist required")
    if not auth.oauth_ok:
        raise OrderError("OAuth required")
    if not auth.two_fa_ok:
        raise OrderError("2FA required")
    if auth.token_date != as_of:
        raise OrderError("daily token renewal required")
    if not auth.algo_id:
        raise OrderError("untagged order refused")


def _whole_shares(quantity: Decimal) -> Decimal:
    return quantity.quantize(Decimal(1), rounding=ROUND_DOWN)


def instructions_from_schedule(
    result: SchedulerResult,
    auth: AuthState,
    phase: SessionPhase,
    *,
    order_type: OrderType = OrderType.LIMIT,
) -> list[Instruction]:
    """Sells the scheduler kept, as a hand-placeable list. Buys are not inferred."""
    out: list[Instruction] = []
    for sell in result.executed.sells:
        qty = _whole_shares(sell.quantity)
        if qty < 1:
            continue
        price = (sell.proceeds / sell.quantity).quantize(PAISE)
        out.append(
            Instruction(
                symbol=sell.symbol,
                side=Side.SELL,
                quantity=qty,
                order_type=order_type,
                limit_price=price,
                algo_id=auth.algo_id,
                phase=phase,
                notional=(qty * price).quantize(PAISE),
            )
        )
    for sell in result.harvested.sells:
        qty = _whole_shares(sell.quantity)
        if qty < 1:
            continue
        price = (sell.proceeds / sell.quantity).quantize(PAISE)
        out.append(
            Instruction(
                symbol=sell.symbol,
                side=Side.SELL,
                quantity=qty,
                order_type=order_type,
                limit_price=price,
                algo_id=auth.algo_id,
                phase=phase,
                notional=(qty * price).quantize(PAISE),
            )
        )
    return out


def format_instruction_list(as_of: date, instructions: tuple[Instruction, ...]) -> str:
    lines = [
        f"# instruction list {as_of.isoformat()}",
        "# place by hand if the API is down; one line per order",
        "# SIDE SYMBOL QTY TYPE LIMIT ALGO PHASE",
    ]
    for item in instructions:
        lines.append(
            f"{item.side.value.upper()} {item.symbol} {item.quantity} "
            f"{item.order_type.value.upper()} {item.limit_price} {item.algo_id} {item.phase.value}"
        )
    return "\n".join(lines) + "\n"


def parse_instruction_list(text: str) -> list[Instruction]:
    orders: list[Instruction] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        side_s, symbol, qty_s, type_s, price_s, algo_id, phase_s = line.split()
        qty = Decimal(qty_s)
        price = Decimal(price_s)
        orders.append(
            Instruction(
                symbol=symbol,
                side=Side(side_s.lower()),
                quantity=qty,
                order_type=OrderType(type_s.lower()),
                limit_price=price,
                algo_id=algo_id,
                phase=SessionPhase(phase_s),
                notional=(qty * price).quantize(PAISE),
            )
        )
    return orders


def lots_after(lots: list[Lot], instruction: Instruction, price: Decimal) -> list[Lot]:
    if instruction.side is Side.BUY:
        return [
            *lots,
            Lot(
                symbol=instruction.symbol,
                quantity=instruction.quantity,
                acquired=date.min,
                cost_per_share=price,
                price=price,
                sector=instruction.sector,
                sleeve=instruction.sleeve,
            ),
        ]
    remaining = instruction.quantity
    out: list[Lot] = []
    for lot in lots:
        if lot.symbol != instruction.symbol or remaining <= 0:
            out.append(lot)
            continue
        take = min(lot.quantity, remaining)
        leftover = lot.quantity - take
        remaining -= take
        if leftover > 0:
            out.append(
                Lot(
                    symbol=lot.symbol,
                    quantity=leftover,
                    acquired=lot.acquired,
                    cost_per_share=lot.cost_per_share,
                    price=lot.price,
                    sector=lot.sector,
                    sleeve=lot.sleeve,
                )
            )
    if remaining > 0:
        raise OrderError(f"sell {instruction.symbol} exceeds holdings")
    return out


def place(
    instruction: Instruction,
    *,
    auth: AuthState,
    clock: datetime,
    limiter: RateLimiter,
    lots: list[Lot],
    equity: Decimal,
    daily_sigma: dict[str, Decimal],
    flag_intervals: pl.DataFrame,
    broker: PaperBroker,
    fill_price: Decimal | None = None,
) -> Fill:
    as_of = now_ist(clock).date()
    assert_auth(auth, as_of)
    if instruction.algo_id != auth.algo_id or not instruction.algo_id:
        raise OrderError("untagged order refused")
    phase = session_phase(clock)
    if phase is SessionPhase.CLOSED:
        raise OrderError("market closed")
    if instruction.phase != phase:
        raise OrderError(f"instruction phase {instruction.phase} is not {phase}")
    if instruction.order_type is OrderType.MARKET and phase in {
        SessionPhase.PRE_OPEN_2,
        SessionPhase.CAS,
    }:
        raise OrderError("market order refused in this phase")
    flags = flags_as_of(flag_intervals, instruction.symbol, as_of)
    if flags["esm_stage"] >= 2:
        raise OrderError("ESM Stage II is not tradable")
    if flags["in_fno_ban"]:
        raise OrderError("F&O ban list")
    if phase is SessionPhase.CAS and not flags["cas_eligible"]:
        raise OrderError("CAS orders only for CAS-eligible names")
    price = fill_price if fill_price is not None else instruction.limit_price
    projected = lots_after(lots, instruction, price)
    try:
        assert_portfolio(projected, equity, daily_sigma)
    except LimitError as exc:
        raise OrderError(str(exc)) from exc
    limiter.admit(clock)
    return broker.execute(instruction, price)
