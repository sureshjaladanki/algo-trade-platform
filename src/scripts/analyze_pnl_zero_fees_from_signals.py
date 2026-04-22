"""
Pair LONG/SHORT with the next EXIT_* per symbol and side using an *aggregate* open:

- The **first** LONG (or SHORT) for a symbol opens a single logical position.
- Any further LONG (or SHORT) for that symbol **before** the first matching exit is treated
  as the same position (entry price remains the **first** open); those rows are counted in
  `aggregated_entry_signals` but do not create extra PnL legs.
- The **first** EXIT_LONG (or EXIT_SHORT) after that closes the position and realizes PnL.

Orphan exits (no prior open for that symbol/side) are excluded from realized PnL.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd


@dataclass
class OpenLeg:
    timestamp: pd.Timestamp
    price: float
    reason: str


@dataclass
class AggregateOpen:
    """First open for a symbol/side; later opens before exit are folded in."""

    first: OpenLeg
    extra_opens: int = 0


_ACTION_ORDER = {"LONG": 0, "SHORT": 1, "EXIT_LONG": 2, "EXIT_SHORT": 3}


def _trade_pnl_pct(side: str, entry_price: float, exit_price: float) -> float:
    if not entry_price:
        return 0.0
    if side == "LONG":
        return (exit_price - entry_price) / entry_price * 100.0
    return (entry_price - exit_price) / entry_price * 100.0


def _max_drawdown_from_pnls(pnls: pd.Series) -> float:
    """Largest peak-to-trough drop on cumulative PnL (same units as pnl). Returns <= 0."""
    if pnls.empty:
        return 0.0
    equity = pnls.cumsum()
    return float((equity - equity.cummax()).min())


def _profit_factor(gross_profit: float, gross_loss: float) -> float | None:
    if gross_loss == 0:
        return None
    return gross_profit / gross_loss


def _raw_signal_counts_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Count LONG / SHORT / EXIT_* per symbol in the signals file (includes orphans)."""
    cols = ["LONG", "SHORT", "EXIT_LONG", "EXIT_SHORT"]
    if df.empty:
        return pd.DataFrame(columns=["symbol", *cols, "total"])
    pivot = (
        pd.crosstab(df["symbol"], df["action"])
        .reindex(columns=cols, fill_value=0)
        .astype(int)
    )
    pivot["total"] = pivot.sum(axis=1).astype(int)
    return pivot.reset_index().sort_values("symbol")


def _matched_trades_by_symbol_summary(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol stats for matched round-trips only (one row per symbol with activity)."""
    p = trades_df["pnl"]
    t = trades_df.assign(
        _w=p.gt(0),
        _l=p.lt(0),
        _f=p.eq(0),
        _gp=p.clip(lower=0),
        _gn=(-p.clip(upper=0)),
    )
    g = t.groupby("symbol", sort=True)
    summary = g.agg(
        trades=("pnl", "size"),
        wins=("_w", "sum"),
        losses=("_l", "sum"),
        flat=("_f", "sum"),
        total_pnl=("pnl", "sum"),
        avg_pnl=("pnl", "mean"),
        gross_profit=("_gp", "sum"),
        gross_loss=("_gn", "sum"),
        best_trade=("pnl", "max"),
        worst_trade=("pnl", "min"),
    ).reset_index()

    summary["win_pct"] = (
        100.0 * summary["wins"] / summary["trades"].where(summary["trades"] > 0)
    ).fillna(0.0)
    summary["sym_pf"] = summary["gross_profit"] / summary["gross_loss"].where(
        summary["gross_loss"] > 0
    )

    side_ct = (
        trades_df.groupby(["symbol", "side"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["LONG", "SHORT"], fill_value=0)
        .rename(columns={"LONG": "long_trades", "SHORT": "short_trades"})
        .reset_index()
    )
    summary = summary.merge(side_ct, on="symbol", how="left")
    summary[["long_trades", "short_trades"]] = summary[
        ["long_trades", "short_trades"]
    ].fillna(0)

    num = [
        "win_pct",
        "total_pnl",
        "avg_pnl",
        "gross_profit",
        "gross_loss",
        "sym_pf",
        "best_trade",
        "worst_trade",
    ]
    summary[num] = summary[num].round(4)
    summary["profit_factor"] = summary["sym_pf"].apply(
        lambda x: f"{x:,.4f}" if pd.notna(x) and math.isfinite(float(x)) else "n/a"
    )
    summary = summary.drop(columns=["sym_pf"])
    int_cols = ["trades", "wins", "losses", "flat", "long_trades", "short_trades"]
    summary[int_cols] = summary[int_cols].astype(int)
    out_cols = [
        "symbol",
        "long_trades",
        "short_trades",
        "trades",
        "wins",
        "losses",
        "flat",
        "win_pct",
        "total_pnl",
        "avg_pnl",
        "gross_profit",
        "gross_loss",
        "profit_factor",
        "best_trade",
        "worst_trade",
    ]
    return summary[out_cols]


def _load_signals_sorted(signals_path: Path) -> pd.DataFrame:
    df = pd.read_csv(signals_path, parse_dates=["timestamp"])
    df["_proc_order"] = df["action"].map(_ACTION_ORDER)
    return df.sort_values(["timestamp", "symbol", "_proc_order"]).drop(
        columns=["_proc_order"]
    )


def _register_open(
    agg: dict[str, AggregateOpen | None],
    sym: str,
    ts: pd.Timestamp,
    price: float,
    reason: str,
) -> None:
    cur = agg.get(sym)
    if cur is None:
        agg[sym] = AggregateOpen(OpenLeg(ts, price, reason), 0)
    else:
        cur.extra_opens += 1


def _close_round_trip(
    agg: dict[str, AggregateOpen | None],
    sym: str,
    ts: pd.Timestamp,
    price: float,
    reason: str,
    *,
    side: Literal["LONG", "SHORT"],
    units: float,
    trades: list[dict],
    orphan_exits: list[dict],
) -> None:
    cur = agg.get(sym)
    if cur is None:
        orphan_exits.append(
            {"timestamp": ts, "symbol": sym, "price": price, "reason": reason}
        )
        return

    leg = cur.first
    n_agg = 1 + cur.extra_opens
    ep, xp = leg.price, price
    if side == "LONG":
        pnl = (xp - ep) * units
    else:
        pnl = (ep - xp) * units

    trades.append(
        {
            "symbol": sym,
            "side": side,
            "entry_time": leg.timestamp,
            "exit_time": ts,
            "entry_price": ep,
            "exit_price": xp,
            "units": units,
            "pnl": pnl,
            "pnl_pct": _trade_pnl_pct(side, ep, xp),
            "exit_reason": reason,
            "aggregated_entry_signals": n_agg,
        }
    )
    agg[sym] = None


def _match_aggregate_round_trips(
    df: pd.DataFrame, units: float
) -> tuple[
    pd.DataFrame,
    list[dict],
    list[dict],
    set[str],
    set[str],
]:
    long_agg: dict[str, AggregateOpen | None] = {}
    short_agg: dict[str, AggregateOpen | None] = {}
    trades: list[dict] = []
    orphan_exit_long: list[dict] = []
    orphan_exit_short: list[dict] = []

    for row in df.itertuples(index=False):
        sym = row.symbol
        action = row.action
        ts = row.timestamp
        price = float(row.price)
        reason = row.reason

        if action == "LONG":
            _register_open(long_agg, sym, ts, price, reason)
        elif action == "SHORT":
            _register_open(short_agg, sym, ts, price, reason)
        elif action == "EXIT_LONG":
            _close_round_trip(
                long_agg,
                sym,
                ts,
                price,
                reason,
                side="LONG",
                units=units,
                trades=trades,
                orphan_exits=orphan_exit_long,
            )
        elif action == "EXIT_SHORT":
            _close_round_trip(
                short_agg,
                sym,
                ts,
                price,
                reason,
                side="SHORT",
                units=units,
                trades=trades,
                orphan_exits=orphan_exit_short,
            )

    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    still_long = {s for s, v in long_agg.items() if v is not None}
    still_short = {s for s, v in short_agg.items() if v is not None}
    return trades_df, orphan_exit_long, orphan_exit_short, still_long, still_short


def _print_signal_overview(
    df: pd.DataFrame,
    signals_path: Path,
    units: float,
    orphan_exit_long: list[dict],
    orphan_exit_short: list[dict],
    still_long: set[str],
    still_short: set[str],
) -> None:
    print(
        "=== Signal PnL (first open -> first exit per symbol/side; stacked opens folded) ===\n"
    )
    print(f"Signals file: {signals_path}")
    print(
        f"Units per round-trip: {units} (PnL = price diff * units; no fees/slippage)\n"
    )

    vc = df["action"].value_counts()
    print(
        "Raw counts: "
        f"LONG={vc.get('LONG', 0)}, SHORT={vc.get('SHORT', 0)}, "
        f"EXIT_LONG={vc.get('EXIT_LONG', 0)}, EXIT_SHORT={vc.get('EXIT_SHORT', 0)}\n"
    )

    print(f"Orphan EXIT_LONG (no open long): {len(orphan_exit_long)}")
    print(f"Orphan EXIT_SHORT (no open short): {len(orphan_exit_short)}")

    if still_long:
        print(f"Open long position (no exit in log): {sorted(still_long)}")
    if still_short:
        print(f"Open short position (no exit in log): {sorted(still_short)}")
    print()

    raw_sym = _raw_signal_counts_by_symbol(df)
    print("Raw signals by symbol:")
    print(raw_sym.to_string(index=False))
    print()


def _format_trade_detail_table(trades_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "symbol",
        "side",
        "entry_price",
        "exit_price",
        "pnl",
        "pnl_pct",
        "entry_time",
        "exit_time",
        "aggregated_entry_signals",
        "exit_reason",
    ]
    detail = trades_df.loc[:, cols].copy()
    nums = ["entry_price", "exit_price", "pnl", "pnl_pct"]
    detail[nums] = detail[nums].map(lambda x: f"{x:,.4f}")
    detail[["entry_time", "exit_time"]] = detail[["entry_time", "exit_time"]].astype(
        str
    )
    return detail


def _print_global_metrics(trades_df: pd.DataFrame) -> None:
    p = trades_df["pnl"]
    total = p.sum()
    wins = int(p.gt(0).sum())
    losses = int(p.lt(0).sum())
    n = len(trades_df)

    gp_series = p.clip(lower=0)
    gl_series = -p.clip(upper=0)
    gross_profit = gp_series.sum()
    gross_loss = gl_series.sum()
    pf = _profit_factor(gross_profit, gross_loss)

    max_dd = _max_drawdown_from_pnls(p)
    max_dd_abs = abs(max_dd) if max_dd < 0 else 0.0
    recovery = (
        (total / max_dd_abs) if max_dd_abs > 0 else (None if total != 0 else None)
    )

    win_rate_pct = 100.0 * wins / n if n else 0.0
    avg_win = gp_series[gp_series > 0].mean() if wins else 0.0
    avg_loss_mag = gl_series[gl_series > 0].mean() if losses else 0.0
    payoff_ratio = (avg_win / avg_loss_mag) if avg_loss_mag > 0 else None

    print("Summary:")
    if pf is None:
        print("  Profit factor (gross gains / gross losses): n/a (no losing trades)")
    else:
        print(f"  Profit factor (gross gains / gross losses): {pf:,.4f}")
    print(f"  Maximum drawdown (cum PnL, exit-time order): {max_dd:,.4f}")
    if recovery is None:
        print("  Recovery factor (net PnL / |max DD|): n/a")
    else:
        print(f"  Recovery factor (net PnL / |max DD|): {recovery:,.4f}")
    print(f"  Win rate: {win_rate_pct:,.2f}%")
    if payoff_ratio is None:
        print("  Avg win / avg loss (payoff): n/a (no losing trades)")
    else:
        print(f"  Avg win / avg loss (payoff): {payoff_ratio:,.4f}")
    print()


def _write_matched_trade_csvs(
    signals_path: Path, trades_df: pd.DataFrame, sym_summary: pd.DataFrame
) -> None:
    sym_csv = signals_path.parent / "matched_trades_pnl_by_symbol.csv"
    sym_summary.to_csv(sym_csv, index=False)
    print(f"Wrote by-symbol matched summary: {sym_csv}\n")

    out = signals_path.parent / "matched_trades_pnl.csv"
    trades_out = trades_df.assign(
        entry_time=trades_df["entry_time"].astype(str),
        exit_time=trades_df["exit_time"].astype(str),
    )
    trades_out.to_csv(out, index=False)
    print(f"Wrote matched trades: {out}")


def analyze(signals_path: Path, units: float) -> None:
    df = _load_signals_sorted(signals_path)
    trades_df, orphan_l, orphan_s, still_long, still_short = (
        _match_aggregate_round_trips(df, units)
    )

    _print_signal_overview(
        df, signals_path, units, orphan_l, orphan_s, still_long, still_short
    )

    if trades_df.empty:
        print("No matched round-trips; nothing to sum for realized PnL.")
        return

    trades_df = trades_df.sort_values("exit_time", ignore_index=True)
    n = len(trades_df)
    wins = (trades_df["pnl"] > 0).sum()
    losses = (trades_df["pnl"] < 0).sum()
    flat = (trades_df["pnl"] == 0).sum()
    total = trades_df["pnl"].sum()

    print(f"Matched round-trips: {n}")
    print(f"Total realized PnL: {total:,.4f}")
    print(f"Win / loss / flat: {wins} / {losses} / {flat}\n")

    by_symbol = _matched_trades_by_symbol_summary(trades_df)
    print("By symbol (matched trades summary):")
    print(by_symbol.to_string(index=False))
    print()

    by_side = trades_df.groupby("side", as_index=False).agg(
        trades=("pnl", "count"), pnl=("pnl", "sum")
    )
    print("By side:")
    print(by_side.to_string(index=False))
    print()

    print("All matched trades (exit-time order):")
    print(_format_trade_detail_table(trades_df).to_string(index=False))
    print()

    _print_global_metrics(trades_df)
    _write_matched_trade_csvs(signals_path, trades_df, by_symbol)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Match first open -> first exit per symbol/side; fold stacked opens into one position."
    )
    p.add_argument(
        "--signals",
        type=Path,
        default=Path("data/output/all_signals.csv"),
        help="Path to all_signals.csv",
    )
    p.add_argument(
        "--units",
        type=float,
        default=1.0,
        help="Position size per round-trip (e.g. shares)",
    )
    args = p.parse_args()
    if not args.signals.exists():
        raise SystemExit(f"Missing {args.signals}")
    analyze(args.signals, args.units)


if __name__ == "__main__":
    main()
