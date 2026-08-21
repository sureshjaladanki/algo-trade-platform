"""Book C: asset location, rebalance bands, and harvest on a substitute whitelist.

Priced through `costs` and `tax`. Substitutes are treated as not substantially
identical, so a VTI sale + ITOT buy is not a wash; buying the harvested name
inside 31 days is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from src.costs import ProductBucket, round_trip_bps
from src.tax import HARVEST_QUARANTINE_DAYS, STCG_RATE, Lot, Wrapper
from src.vti import DailyBar

HARVEST_UNIVERSE: dict[str, tuple[str, ...]] = {
    "VTI": ("ITOT", "SCHB"),
    "ITOT": ("VTI", "SCHB"),
    "SCHB": ("VTI", "ITOT"),
}
HARVEST_LOSS_BAND = 0.05
REBALANCE_BAND = 0.05
HIGH_TURNOVER_PER_YEAR = 2.0
C1_HURDLE_BPS = 25.0


def locate(
    *,
    turnover_per_year: float,
    is_1256: bool,
    ira_room_usd: float,
) -> Wrapper:
    if is_1256:
        return Wrapper.TAXABLE
    if turnover_per_year >= HIGH_TURNOVER_PER_YEAR and ira_room_usd > 0:
        return Wrapper.IRA
    return Wrapper.TAXABLE


def in_rebalance_band(weight: float, target: float, band: float = REBALANCE_BAND) -> bool:
    return abs(weight - target) <= band


def mes_overlay_notional(*, equity_usd: float, weight: float, target: float) -> float:
    """Dollar overlay to restore beta without realizing the cash-equity lot.

    Sign: positive = long MES (underweight equity), negative = short MES.
    """
    if in_rebalance_band(weight, target):
        return 0.0
    return equity_usd * (target - weight)


@dataclass(frozen=True)
class HarvestEvent:
    date: date
    sell_symbol: str
    buy_symbol: str
    quantity: float
    proceeds: float
    basis: float
    realized_loss: float
    cost_usd: float
    tax_savings: float
    lot_id: str


@dataclass
class SimResult:
    years: float
    static_terminal: float
    harvest_terminal: float
    excess_bps_per_year: float
    wash_sale_violations: int
    audit: tuple[HarvestEvent, ...]

    @property
    def passed(self) -> bool:
        return self.excess_bps_per_year >= C1_HURDLE_BPS and self.wash_sale_violations == 0


def _round_trip_cost(notional: float) -> float:
    return notional * round_trip_bps(ProductBucket.LIQUID_ETF) / 1e4


def _next_substitute(
    sold: str,
    *,
    holding_symbols: set[str],
    asof: date,
    quarantine: dict[str, date],
) -> str:
    def free(symbol: str) -> bool:
        until = quarantine.get(symbol)
        return until is None or asof > until

    for candidate in HARVEST_UNIVERSE[sold]:
        if candidate not in holding_symbols and free(candidate):
            return candidate
    for candidate in HARVEST_UNIVERSE[sold]:
        if free(candidate):
            return candidate
    raise ValueError(f"no harvest substitute outside quarantine for {sold}")


@dataclass
class _State:
    lots: list[Lot]
    quarantine_until: dict[str, date] = field(default_factory=dict)
    next_lot: int = 1
    wash_sale_violations: int = 0
    audit: list[HarvestEvent] = field(default_factory=list)

    def _id(self) -> str:
        lot_id = f"c1-{self.next_lot}"
        self.next_lot += 1
        return lot_id

    def _make_lot(
        self,
        *,
        symbol: str,
        quantity: float,
        cost_basis: float,
        acquired: date,
    ) -> Lot:
        until = self.quarantine_until.get(symbol)
        if until is not None and acquired <= until:
            self.wash_sale_violations += 1
        return Lot(
            lot_id=self._id(),
            taxpayer_id="hh1",
            account_id="taxable-1",
            wrapper=Wrapper.TAXABLE,
            symbol=symbol,
            quantity=quantity,
            cost_basis=cost_basis,
            acquired=acquired,
        )

    def buy(
        self,
        *,
        symbol: str,
        quantity: float,
        cost_basis: float,
        acquired: date,
    ) -> None:
        self.lots.append(
            self._make_lot(
                symbol=symbol,
                quantity=quantity,
                cost_basis=cost_basis,
                acquired=acquired,
            )
        )


def run_harvest_sim(
    bars: list[DailyBar],
    *,
    initial_usd: float = 100_000.0,
    monthly_usd: float = 500.0,
    start: date = date(2018, 1, 2),
    end: date = date(2023, 12, 29),
) -> SimResult:
    """Five-year retrospective on a representative taxable DCA lot structure.

    ITOT/SCHB are priced at the VTI close (same total-market exposure). Harvested
    losses are assumed to offset short-term gains elsewhere in the household at
    the working ST rate; tax savings are reinvested.
    """
    window = [bar for bar in bars if start <= bar.date <= end]
    if len(window) < 400:
        raise ValueError("need a multi-year VTI window for C1")
    static = _State(lots=[])
    harvest = _State(lots=[])
    static.buy(
        symbol="VTI",
        quantity=initial_usd / window[0].close,
        cost_basis=initial_usd,
        acquired=window[0].date,
    )
    harvest.buy(
        symbol="VTI",
        quantity=initial_usd / window[0].close,
        cost_basis=initial_usd,
        acquired=window[0].date,
    )
    last_month = window[0].date.month
    for bar in window[1:]:
        if bar.date.month != last_month:
            qty = monthly_usd / bar.close
            static.buy(symbol="VTI", quantity=qty, cost_basis=monthly_usd, acquired=bar.date)
            harvest.buy(
                symbol=_contribution_symbol(harvest, bar.date),
                quantity=qty,
                cost_basis=monthly_usd,
                acquired=bar.date,
            )
            last_month = bar.date.month
        _harvest_lots_below_band(harvest, bar)

    years = (window[-1].date - window[0].date).days / 365.25
    static_terminal = _mark(static, window[-1].close)
    harvest_terminal = _mark(harvest, window[-1].close)
    excess = (harvest_terminal / static_terminal) ** (1.0 / years) - 1.0
    return SimResult(
        years=years,
        static_terminal=static_terminal,
        harvest_terminal=harvest_terminal,
        excess_bps_per_year=1e4 * excess,
        wash_sale_violations=harvest.wash_sale_violations,
        audit=tuple(harvest.audit),
    )


def _open_core_symbol(state: _State) -> str:
    if not state.lots:
        return "VTI"
    return max(state.lots, key=lambda lot: lot.quantity).symbol


def _contribution_symbol(state: _State, acquired: date) -> str:
    core = _open_core_symbol(state)
    until = state.quarantine_until.get(core)
    if until is None or acquired > until:
        return core
    return _next_substitute(
        core,
        holding_symbols={lot.symbol for lot in state.lots},
        asof=acquired,
        quarantine=state.quarantine_until,
    )


def _mark(state: _State, close: float) -> float:
    return sum(lot.quantity * close for lot in state.lots)


def _harvest_lots_below_band(state: _State, bar: DailyBar) -> None:
    original = list(state.lots)
    kept: list[Lot] = []
    holding = {lot.symbol for lot in original}
    for lot in original:
        per_share = lot.cost_basis / lot.quantity
        loss_frac = (bar.close - per_share) / per_share
        sold_until = state.quarantine_until.get(lot.symbol)
        blocked = sold_until is not None and bar.date <= sold_until
        if loss_frac > -HARVEST_LOSS_BAND or blocked:
            kept.append(lot)
            continue
        proceeds = lot.quantity * bar.close
        realized_loss = lot.cost_basis - proceeds
        if realized_loss <= 0:
            kept.append(lot)
            continue
        try:
            substitute = _next_substitute(
                lot.symbol,
                holding_symbols=holding,
                asof=bar.date,
                quarantine=state.quarantine_until,
            )
        except ValueError:
            kept.append(lot)
            continue
        cost = _round_trip_cost(proceeds)
        tax_savings = STCG_RATE * realized_loss
        net = proceeds - cost + tax_savings
        state.audit.append(
            HarvestEvent(
                date=bar.date,
                sell_symbol=lot.symbol,
                buy_symbol=substitute,
                quantity=lot.quantity,
                proceeds=proceeds,
                basis=lot.cost_basis,
                realized_loss=realized_loss,
                cost_usd=cost,
                tax_savings=tax_savings,
                lot_id=lot.lot_id,
            )
        )
        state.quarantine_until[lot.symbol] = bar.date + timedelta(
            days=HARVEST_QUARANTINE_DAYS
        )
        kept.append(
            state._make_lot(
                symbol=substitute,
                quantity=net / bar.close,
                cost_basis=net,
                acquired=bar.date,
            )
        )
        holding.add(substitute)
        holding.discard(lot.symbol)
    state.lots = kept
