"""Book L — realisation schedule, ETF vs constituents, ETF vs index fund. Arithmetic only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.costs import BookKind, Product, Side, Venue, round_trip_bps, stt
from src.tax import LTCG_EXEMPTION, long_term_holding, ltcg, stcg

DESIGN_CAPITAL = Decimal(5000000)
GROSS_ASSUMPTION = Decimal("0.11")  # W17, not a forecast
TURNOVER_60 = Decimal("0.60")
KILL_BPS = Decimal(50)


@dataclass(frozen=True)
class Lot:
    symbol: str
    quantity: Decimal
    acquired: date
    cost_per_share: Decimal
    price: Decimal
    sector: str = ""
    sleeve: str = "core"


@dataclass(frozen=True)
class ProposedSell:
    symbol: str
    quantity: Decimal
    acquired: date
    proceeds: Decimal
    cost: Decimal
    gain: Decimal
    long_term: bool
    tax: Decimal


@dataclass(frozen=True)
class Schedule:
    sells: tuple[ProposedSell, ...]
    tax: Decimal
    exemption_used: Decimal


@dataclass(frozen=True)
class RouteChoice:
    venue: str
    stt_gap_bps: Decimal


@dataclass(frozen=True)
class CoreVehicleChoice:
    vehicle: str
    etf_drag_bps: Decimal
    fund_drag_bps: Decimal
    crossover_turns: Decimal | None


def lot_value(lot: Lot) -> Decimal:
    return lot.quantity * lot.price


def stt_gap_bps(notional: Decimal) -> Decimal:
    """Delivery STT both legs minus ETF STT, in bps of notional."""
    delivery = stt(Product.DELIVERY, Side.BUY, notional) + stt(Product.DELIVERY, Side.SELL, notional)
    etf = stt(Product.ETF, Side.BUY, notional) + stt(Product.ETF, Side.SELL, notional)
    return (delivery - etf) / notional * Decimal(10000)


def tax_on_gain(gain: Decimal, long_term: bool, exemption_used: Decimal) -> tuple[Decimal, Decimal]:
    """Returns (tax, exemption_used after this gain). Loss is untaxed."""
    if gain <= 0:
        return Decimal("0.00"), exemption_used
    if long_term:
        tax = ltcg(gain, exemption_used)
        remaining = LTCG_EXEMPTION - exemption_used
        used = max(Decimal(0), min(remaining, gain))
        return tax, exemption_used + used
    return stcg(gain), exemption_used


def realisation_schedule(
    lots: list[Lot],
    target_weights: dict[str, Decimal],
    as_of: date,
    *,
    exemption_used: Decimal = Decimal(0),
) -> Schedule:
    """Sells to reach target weights at FIFO lots, priced with `tax` at as_of."""
    total = sum((lot_value(lot) for lot in lots), Decimal(0))
    by_symbol: dict[str, list[Lot]] = {}
    for lot in lots:
        by_symbol.setdefault(lot.symbol, []).append(lot)
    for symbol, held_lots in by_symbol.items():
        by_symbol[symbol] = sorted(held_lots, key=lambda lot: lot.acquired)

    sells: list[ProposedSell] = []
    used = exemption_used
    for symbol, held in by_symbol.items():
        current = sum((lot_value(lot) for lot in held), Decimal(0))
        target = target_weights.get(symbol, Decimal(0)) * total
        need = current - target
        if need <= 0:
            continue
        remaining = need
        for lot in held:
            if remaining <= 0:
                break
            value = lot_value(lot)
            take_value = min(value, remaining)
            frac = take_value / value
            qty = lot.quantity * frac
            proceeds = take_value
            cost = lot.cost_per_share * qty
            gain = proceeds - cost
            lt = long_term_holding(lot.acquired, as_of)
            tax, used = tax_on_gain(gain, lt, used)
            sells.append(
                ProposedSell(
                    symbol=symbol,
                    quantity=qty,
                    acquired=lot.acquired,
                    proceeds=proceeds,
                    cost=cost,
                    gain=gain,
                    long_term=lt,
                    tax=tax,
                )
            )
            remaining -= take_value

    return Schedule(
        sells=tuple(sells),
        tax=sum((s.tax for s in sells), Decimal("0.00")),
        exemption_used=used,
    )


def etf_vs_constituents(turnover_value: Decimal, etf_spread_bps: Decimal) -> RouteChoice:
    """Route a rebalance through ETF units unless the quoted spread exceeds the STT gap."""
    gap = stt_gap_bps(turnover_value)
    venue = "constituents" if etf_spread_bps > gap else "etf"
    return RouteChoice(venue=venue, stt_gap_bps=gap)


def routing_saving(turnover_value: Decimal) -> Decimal:
    """ETF vs cash-delivery round trip on the same notional. DP nets out (one ISIN each)."""
    delivery = round_trip_bps(
        product=Product.DELIVERY,
        venue=Venue.NSE,
        buy_value=turnover_value,
        sell_value=turnover_value,
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.CAPITAL_GAINS,
        n_isins_sold=1,
    )
    etf = round_trip_bps(
        product=Product.ETF,
        venue=Venue.NSE,
        buy_value=turnover_value,
        sell_value=turnover_value,
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.CAPITAL_GAINS,
        n_isins_sold=1,
    )
    return delivery.rupees - etf.rupees


def tax_schedule_delta(
    capital: Decimal,
    turnover: Decimal = TURNOVER_60,
    gross: Decimal = GROSS_ASSUMPTION,
) -> Decimal:
    """Naive STCG on realised gain versus LTCG with the s.198 exemption unused at year start."""
    realised_gain = capital * turnover * gross
    return stcg(realised_gain) - ltcg(realised_gain, Decimal(0))


def etf_friction_bps(notional: Decimal) -> Decimal:
    trip = round_trip_bps(
        product=Product.ETF,
        venue=Venue.NSE,
        buy_value=notional,
        sell_value=notional,
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.CAPITAL_GAINS,
        n_isins_sold=1,
    )
    return trip.bps


def etf_vs_index_fund(
    capital: Decimal,
    annual_turns: Decimal,
    ter_etf: Decimal,
    ter_fund: Decimal,
    spread_bps: Decimal,
    exit_load: Decimal,
) -> CoreVehicleChoice:
    """Annual drag of trading the core through ETF units versus holding a direct index fund."""
    friction = etf_friction_bps(capital)
    extra_per_turn = spread_bps + friction
    etf_drag = ter_etf * Decimal(10000) + annual_turns * extra_per_turn
    hold_days = Decimal(365) / annual_turns if annual_turns > 0 else Decimal(365)
    load_bps = exit_load * Decimal(10000) if hold_days < 15 else Decimal(0)
    fund_drag = ter_fund * Decimal(10000) + annual_turns * load_bps
    crossover = None
    if extra_per_turn > 0:
        crossover = (ter_fund - ter_etf) * Decimal(10000) / extra_per_turn
    vehicle = "etf" if etf_drag < fund_drag else "index_fund"
    return CoreVehicleChoice(
        vehicle=vehicle,
        etf_drag_bps=etf_drag,
        fund_drag_bps=fund_drag,
        crossover_turns=crossover,
    )


def schedule_delta_bps(capital: Decimal) -> Decimal:
    tax_delta = tax_schedule_delta(capital)
    turnover_value = capital * TURNOVER_60
    routing = routing_saving(turnover_value)
    return (tax_delta + routing) / capital * Decimal(10000)
