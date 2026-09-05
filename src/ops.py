"""L0 operations: IST calendar, ₹1 reconciliation, kill switch, run log. No LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from src.books.ledger import Lot
from src.execute import (
    AuthState,
    Fill,
    Instruction,
    LedgerLine,
    OrderError,
    PaperBroker,
    RateLimiter,
    SessionPhase,
    format_instruction_list,
    instructions_from_schedule,
    lots_after,
    parse_instruction_list,
    place,
)
from src.portfolio import SchedulerResult, apply_realisation
from src.tax import tax_year

PAISE = Decimal("0.01")
RECON_TOLERANCE = Decimal("1.00")
BOOK_A_REVIEW = date(2027, 8, 31)
BUDGET_2026 = date(2026, 2, 1)
MUHURAT_2026 = date(2026, 11, 8)

# NSE/CMTR/71775 plus NSE/CMTR/72260 (15 Jan municipal-election holiday).
NSE_HOLIDAYS_2026 = frozenset(
    {
        date(2026, 1, 15),
        date(2026, 1, 26),
        date(2026, 3, 3),
        date(2026, 3, 26),
        date(2026, 3, 31),
        date(2026, 4, 3),
        date(2026, 4, 14),
        date(2026, 5, 1),
        date(2026, 5, 28),
        date(2026, 6, 26),
        date(2026, 9, 14),
        date(2026, 10, 2),
        date(2026, 10, 20),
        date(2026, 11, 10),
        date(2026, 11, 24),
        date(2026, 12, 25),
    }
)

# RBI press release 2025-2026/2306 — announcement day is the last sitting day.
MPC_ANNOUNCEMENT = frozenset(
    {
        date(2026, 4, 8),
        date(2026, 6, 5),
        date(2026, 8, 5),
        date(2026, 10, 7),
        date(2026, 12, 4),
        date(2027, 2, 5),
    }
)

ADVANCE_TAX_MD = frozenset({(6, 15), (9, 15), (12, 15), (3, 15)})
RESULTS_MONTHS = frozenset({1, 4, 7, 10})


@dataclass
class KillSwitch:
    killed: bool = False
    reason: str = ""

    def trip(self, reason: str) -> None:
        self.killed = True
        self.reason = reason


@dataclass
class ReconResult:
    ok: bool
    residual: Decimal
    breaks: tuple[str, ...]


@dataclass
class DeskState:
    kill: KillSwitch = field(default_factory=KillSwitch)
    last_recon: ReconResult | None = None
    log: list[str] = field(default_factory=list)

    def note(self, line: str) -> None:
        self.log.append(line)


def is_session(day: date) -> bool:
    if day == MUHURAT_2026:
        return True
    if day.weekday() >= 5:
        return False
    return not (day.year == 2026 and day in NSE_HOLIDAYS_2026)


def next_sessions(start: date, n: int) -> list[date]:
    out: list[date] = []
    cur = start
    while len(out) < n:
        if is_session(cur):
            out.append(cur)
        cur += timedelta(days=1)
    return out


def weekly_expiry_date(day: date, weekday: int) -> date:
    """That weekday in this week, or the previous session if it is a holiday."""
    target = day - timedelta(days=day.weekday() - weekday)
    while not is_session(target):
        target -= timedelta(days=1)
    return target


def nse_expiry_session(day: date) -> bool:
    return is_session(day) and day == weekly_expiry_date(day, 1)


def bse_expiry_session(day: date) -> bool:
    return is_session(day) and day == weekly_expiry_date(day, 3)


def last_weekday_session(year: int, month: int, weekday: int) -> date:
    if month == 12:
        cursor = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        cursor = date(year, month + 1, 1) - timedelta(days=1)
    while cursor.weekday() != weekday:
        cursor -= timedelta(days=1)
    while not is_session(cursor):
        cursor -= timedelta(days=1)
    return cursor


def nse_monthly_expiry(day: date) -> bool:
    return day == last_weekday_session(day.year, day.month, 1)


def bse_monthly_expiry(day: date) -> bool:
    return day == last_weekday_session(day.year, day.month, 3)


def is_budget_day(day: date) -> bool:
    return day == BUDGET_2026 or (day.month == 2 and day.day == 1)


def is_mpc_announcement(day: date) -> bool:
    return day in MPC_ANNOUNCEMENT


def is_results_season(day: date) -> bool:
    return day.month in RESULTS_MONTHS


def is_tax_year_boundary(day: date) -> bool:
    return day.month == 3 and day.day == 31


def is_itr_deadline(day: date) -> bool:
    return (day.month == 8 and day.day == 31) or (day.month == 10 and day.day == 31)


def is_advance_tax(day: date) -> bool:
    return (day.month, day.day) in ADVANCE_TAX_MD


def calendar_flags(day: date) -> dict[str, bool | str]:
    return {
        "session": is_session(day),
        "nse_expiry": nse_expiry_session(day),
        "bse_expiry": bse_expiry_session(day),
        "nse_monthly_expiry": nse_monthly_expiry(day),
        "bse_monthly_expiry": bse_monthly_expiry(day),
        "budget": is_budget_day(day),
        "mpc": is_mpc_announcement(day),
        "results_season": is_results_season(day),
        "tax_year_boundary": is_tax_year_boundary(day),
        "itr_deadline": is_itr_deadline(day),
        "advance_tax": is_advance_tax(day),
        "book_a_review": day == BOOK_A_REVIEW,
        "tax_year": tax_year(day),
    }


def reconcile(fills: list[Fill], ledger: list[LedgerLine]) -> ReconResult:
    breaks: list[str] = []
    residual = Decimal("0.00")
    if len(fills) != len(ledger):
        breaks.append(f"count fills {len(fills)} vs ledger {len(ledger)}")
    n = min(len(fills), len(ledger))
    for fill, line in zip(fills[:n], ledger[:n], strict=True):
        if fill.symbol != line.symbol or fill.side != line.side or fill.quantity != line.quantity:
            breaks.append(f"mismatch {fill.symbol} vs {line.symbol}")
            continue
        gap = abs(fill.rupees - line.rupees)
        residual = max(residual, gap)
        if gap > RECON_TOLERANCE:
            breaks.append(f"{fill.symbol} residual ₹{gap}")
    ok = not breaks and residual <= RECON_TOLERANCE
    return ReconResult(ok=ok, residual=residual, breaks=tuple(breaks))


def morning_gate(state: DeskState, recon: ReconResult) -> bool:
    """09:00 IST. A failed recon emits no instructions today."""
    state.last_recon = recon
    if state.kill.killed:
        state.note("KILL: no instructions")
        return False
    if not recon.ok:
        state.note(f"RECON FAIL residual ₹{recon.residual}: {'; '.join(recon.breaks)}")
        return False
    state.note(f"RECON OK residual ₹{recon.residual}")
    return True


def afternoon_instructions(
    lots: list[Lot],
    target_weights: dict[str, Decimal],
    as_of: date,
    auth: AuthState,
    *,
    harvest_exemption: bool = False,
) -> tuple[SchedulerResult, list[Instruction]]:
    result = apply_realisation(
        lots,
        target_weights,
        as_of,
        harvest_exemption=harvest_exemption,
    )
    instructions = instructions_from_schedule(result, auth, SessionPhase.CONTINUOUS)
    return result, instructions


def write_instruction_file(path: Path, as_of: date, instructions: list[Instruction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_instruction_list(as_of, tuple(instructions)), encoding="utf-8")


def write_run_log(path: Path, state: DeskState, as_of: date) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = calendar_flags(as_of)
    body = [f"# run log {as_of.isoformat()}", f"# calendar {flags}"]
    body.extend(state.log)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def run_note(state: DeskState) -> str:
    """Prose note from the run log. Template only — L10 forbids model output in the book."""
    if not state.log:
        return "nothing changed."
    return "what changed: " + "; ".join(state.log)


def paper_day(
    as_of: date,
    *,
    lots: list[Lot],
    target_weights: dict[str, Decimal],
    auth: AuthState,
    equity: Decimal,
    daily_sigma: dict[str, Decimal],
    flag_intervals,
    state: DeskState,
    broker: PaperBroker,
    clock: datetime,
    prior_fills: list[Fill],
    prior_ledger: list[LedgerLine],
    limiter: RateLimiter | None = None,
) -> tuple[bool, list[Instruction]]:
    """One paper session: 09:00 recon, then 16:15 list, then place on the paper venue."""
    if state.kill.killed:
        state.note("KILL: skip session")
        return False, []
    allowed = morning_gate(state, reconcile(prior_fills, prior_ledger))
    if not allowed:
        return False, []
    _result, instructions = afternoon_instructions(lots, target_weights, as_of, auth)
    for line in _result.log:
        state.note(line)
    rate = limiter if limiter is not None else RateLimiter()
    held = lots
    for item in instructions:
        try:
            fill = place(
                item,
                auth=auth,
                clock=clock,
                limiter=rate,
                lots=held,
                equity=equity,
                daily_sigma=daily_sigma,
                flag_intervals=flag_intervals,
                broker=broker,
            )
        except OrderError as exc:
            state.note(f"PLACE FAIL {item.symbol}: {exc}")
            return False, instructions
        held = lots_after(held, item, fill.price)
    return True, instructions


def replay_printed_list(
    text: str,
    *,
    auth: AuthState,
    clock: datetime,
    lots: list[Lot],
    equity: Decimal,
    daily_sigma: dict[str, Decimal],
    flag_intervals,
    broker: PaperBroker,
) -> list[Fill]:
    limiter = RateLimiter()
    fills: list[Fill] = []
    for item in parse_instruction_list(text):
        fills.append(
            place(
                item,
                auth=auth,
                clock=clock,
                limiter=limiter,
                lots=lots,
                equity=equity,
                daily_sigma=daily_sigma,
                flag_intervals=flag_intervals,
                broker=broker,
            )
        )
    return fills
