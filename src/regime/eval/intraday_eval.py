"""Intraday Regime eval — I1 hit rate, I5 admission, I4 dwell, I7 state-map."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.session import (
    LONG_LAST_ENTRY,
    MIS_EXIT_BAR_END,
    SHORT_LAST_ENTRY,
    long_entry_ok_expr,
    short_entry_ok_expr,
)
from src.labels.triple_barrier import (
    SL_FLOOR,
    TOD_LOOKBACK_DAYS,
    TP_FLOOR_LONG,
    TP_FLOOR_SHORT,
    TP_PENETRATION,
)
from src.regime.eval.common import (
    H_BARS,
    MIN_BARS,
    MetricResult,
    TRADEABLE_DAILY,
)
from src.regime.intraday import open_auction_bleed_expr
from src.regime.intraday_model import IntradayHMMRegimeModel
from src.regime.types import IntradayRegime


def _index_tb_labels(bars: pl.DataFrame) -> pl.DataFrame:
    """
    Absolute-path IndexTB on Nifty 15m.

    Same locked widths as stock TB (TOD rv + cost floors), but **no** stock
    eligibility screen — index path quality is scored on every MIS-valid bar.
    """
    min_periods = max(10, TOD_LOOKBACK_DAYS // 4)
    df = (
        bars.sort("date")
        .with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
            range_pct=(pl.col("high") - pl.col("low")) / pl.col("close").shift(1),
        )
        .sort(["time_only", "date_only"])
        .with_columns(
            atr_pct=pl.col("range_pct")
            .shift(1)
            .rolling_mean(window_size=TOD_LOOKBACK_DAYS, min_samples=min_periods)
            .over("time_only"),
        )
        .sort("date")
        .with_columns(
            entry_px=pl.col("close"),
            long_tp_w=pl.max_horizontal(2.5 * pl.col("atr_pct"), pl.lit(TP_FLOOR_LONG)),
            long_sl_w=pl.max_horizontal(1.0 * pl.col("atr_pct"), pl.lit(SL_FLOOR)),
            short_tp_w=pl.max_horizontal(2.0 * pl.col("atr_pct"), pl.lit(TP_FLOOR_SHORT)),
            short_sl_w=pl.max_horizontal(0.9 * pl.col("atr_pct"), pl.lit(SL_FLOOR)),
        )
    )

    for h in range(1, H_BARS + 1):
        df = df.with_columns(
            **{
                f"_hi_{h}": pl.col("high").shift(-h),
                f"_lo_{h}": pl.col("low").shift(-h),
                f"_c_{h}": pl.col("close").shift(-h),
                f"_t_{h}": pl.col("date").shift(-h).dt.time(),
                f"_d_{h}": pl.col("date").shift(-h).dt.date(),
            }
        )

    df = df.with_columns(
        _long_event=pl.lit(0, dtype=pl.Int8),
        _short_event=pl.lit(0, dtype=pl.Int8),
    )

    for h in range(1, H_BARS + 1):
        in_session = (
            (pl.col(f"_d_{h}") == pl.col("date_only"))
            & (pl.col(f"_t_{h}") <= MIS_EXIT_BAR_END)
            & pl.col(f"_c_{h}").is_not_null()
        )
        long_tp = in_session & (
            pl.col(f"_hi_{h}")
            >= pl.col("entry_px") * (1.0 + pl.col("long_tp_w") + TP_PENETRATION)
        )
        long_sl = in_session & (
            pl.col(f"_lo_{h}") <= pl.col("entry_px") * (1.0 - pl.col("long_sl_w"))
        )
        short_tp = in_session & (
            pl.col(f"_lo_{h}")
            <= pl.col("entry_px") * (1.0 - pl.col("short_tp_w") - TP_PENETRATION)
        )
        short_sl = in_session & (
            pl.col(f"_hi_{h}") >= pl.col("entry_px") * (1.0 + pl.col("short_sl_w"))
        )
        still_long = pl.col("_long_event") == 0
        still_short = pl.col("_short_event") == 0
        df = df.with_columns(
            _long_event=pl.when(still_long & long_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still_long & long_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_long_event")),
            _short_event=pl.when(still_short & short_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still_short & short_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_short_event")),
        )

    # Full H-path must be in-session for timeouts; barrier hits already require in_session.
    path_ok = (
        (pl.col(f"_d_{H_BARS}") == pl.col("date_only"))
        & (pl.col(f"_t_{H_BARS}") <= MIS_EXIT_BAR_END)
        & pl.col(f"_c_{H_BARS}").is_not_null()
    )
    return df.with_columns(
        tb_label_long=pl.when(
            (pl.col("time_only") <= LONG_LAST_ENTRY)
            & ((pl.col("_long_event") != 0) | path_ok)
        )
        .then(
            pl.when(pl.col("_long_event") != 0)
            .then(pl.col("_long_event"))
            .otherwise(pl.lit(0, dtype=pl.Int8))
        )
        .otherwise(None),
        tb_label_short=pl.when(
            (pl.col("time_only") <= SHORT_LAST_ENTRY)
            & ((pl.col("_short_event") != 0) | path_ok)
        )
        .then(
            pl.when(pl.col("_short_event") != 0)
            .then(pl.col("_short_event"))
            .otherwise(pl.lit(0, dtype=pl.Int8))
        )
        .otherwise(None),
    ).select(["date", "tb_label_long", "tb_label_short"])


def attach_index_paths(market_15m: pl.DataFrame) -> pl.DataFrame:
    """R60 + IndexTB + session masks on Nifty 15m."""
    bars = market_15m.sort("date").select(["date", "open", "high", "low", "close"])
    tb = _index_tb_labels(bars)
    return (
        bars.with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
            _fwd_close=pl.col("close").shift(-H_BARS),
            _fwd_date=pl.col("date").shift(-H_BARS).dt.date(),
        )
        .with_columns(
            r60=pl.when(pl.col("_fwd_date") == pl.col("date_only"))
            .then(pl.col("_fwd_close") / pl.col("close") - 1.0)
            .otherwise(None),
            long_entry_ok=long_entry_ok_expr("time_only"),
            short_entry_ok=short_entry_ok_expr("time_only"),
            open_bleed=open_auction_bleed_expr("date"),
        )
        .join(tb, on="date", how="left")
        .select(
            [
                "date",
                "date_only",
                "time_only",
                "close",
                "r60",
                "tb_label_long",
                "tb_label_short",
                "long_entry_ok",
                "short_entry_ok",
                "open_bleed",
            ]
        )
    )


def join_regime_paths(regime_preds: pl.DataFrame, path_df: pl.DataFrame) -> pl.DataFrame:
    return path_df.join(
        regime_preds.select(["date", "daily_regime", "intraday_regime"]),
        on="date",
        how="inner",
    )


def i7_state_map_audit(hmm: IntradayHMMRegimeModel) -> MetricResult:
    """Mapped labels cover four states; TREND_UP emit r_15 > TREND_DOWN."""
    labels = {r.value for r in hmm.state_map.values()}
    expected = {
        IntradayRegime.TREND_UP.value,
        IntradayRegime.TREND_DOWN.value,
        IntradayRegime.CHOP.value,
        IntradayRegime.HIGH_VOL.value,
    }
    inv = {regime.value: idx for idx, regime in hmm.state_map.items()}
    up_r = float(hmm.model.means_[inv[IntradayRegime.TREND_UP.value], 0])
    down_r = float(hmm.model.means_[inv[IntradayRegime.TREND_DOWN.value], 0])
    ok = labels == expected and up_r > down_r
    return MetricResult(
        "I7",
        "-",
        up_r - down_r,
        None,
        None,
        4,
        ok,
        f"emit_r_up={up_r:.3f} emit_r_down={down_r:.3f}",
    )


def _tod_null_hit_rate(
    day_ids: np.ndarray,
    tod: np.ndarray,
    regimes: np.ndarray,
    hits: np.ndarray,
    state: str,
    n_null: int,
    rng: np.random.Generator,
) -> float:
    n_sessions = int(day_ids.max()) + 1
    label_at = {(int(d), t): lab for d, t, lab in zip(day_ids, tod, regimes)}
    rates = np.empty(n_null)
    for b in range(n_null):
        perm = rng.permutation(n_sessions)
        shuffled = np.array(
            [label_at.get((int(perm[int(d)]), t), lab) for d, t, lab in zip(day_ids, tod, regimes)]
        )
        mask = shuffled == state
        rates[b] = float(hits[mask].mean()) if mask.any() else float("nan")
    return float(np.nanmean(rates))


def i1_directional_hit_rate(
    regime_paths: pl.DataFrame,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """P(R60 sign matches sleeve) - TOD null; gate on CI(Edge) LB > 0."""
    base = regime_paths.filter(~pl.col("open_bleed") & pl.col("r60").is_not_null())
    results = []

    for side_name, state, entry_col, positive in (
        ("long", IntradayRegime.TREND_UP.value, "long_entry_ok", True),
        ("short", IntradayRegime.TREND_DOWN.value, "short_entry_ok", False),
    ):
        panel = base.filter(pl.col(entry_col)).select(
            ["date_only", "time_only", "intraday_regime", "r60"]
        )
        sessions = panel["date_only"].unique().sort().to_list()
        session_idx = {d: i for i, d in enumerate(sessions)}
        day_ids = np.array([session_idx[d] for d in panel["date_only"].to_list()], dtype=int)
        tod = np.array(panel["time_only"].to_list(), dtype=object)
        regimes = panel["intraday_regime"].to_numpy()
        r60 = panel["r60"].to_numpy()
        hits = (r60 > 0) if positive else (r60 < 0)
        mask = regimes == state
        n = int(mask.sum())

        if n < MIN_BARS:
            results.append(MetricResult("I1", side_name, None, None, None, n, False, "thin"))
            continue

        hit_rate = float(hits[mask].mean())
        null_mean = _tod_null_hit_rate(day_ids, tod, regimes, hits, state, n_boot, rng)

        sess_hit = np.array(
            [
                float(hits[(panel["date_only"] == d).to_numpy() & mask].mean())
                for d in sessions
                if ((panel["date_only"] == d).to_numpy() & mask).any()
            ]
        )
        edge = float(sess_hit.mean()) - null_mean
        boot = (
            rng.choice(sess_hit, size=(n_boot, sess_hit.size), replace=True).mean(axis=1)
            - null_mean
        )
        ci_lo, ci_hi = float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))
        results.append(
            MetricResult(
                "I1",
                side_name,
                edge,
                ci_lo,
                ci_hi,
                n,
                ci_lo > 0.0,
                f"hit={hit_rate:.3f} null={null_mean:.3f}",
            )
        )
    return results


def _i5_session_counts(
    panel: pl.DataFrame, state: str, label_col: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    adm_tp, adm_n, rej_tp, rej_n = [], [], [], []
    for _, day in panel.group_by("date_only"):
        admitted = (day["intraday_regime"] == state).to_numpy()
        tp = (day[label_col] == 1).to_numpy()
        n_a = int(admitted.sum())
        n_r = int((~admitted).sum())
        adm_tp.append(int(tp[admitted].sum()) if n_a else 0)
        adm_n.append(n_a)
        rej_tp.append(int(tp[~admitted].sum()) if n_r else 0)
        rej_n.append(n_r)
    return (
        np.asarray(adm_tp, dtype=float),
        np.asarray(adm_n, dtype=float),
        np.asarray(rej_tp, dtype=float),
        np.asarray(rej_n, dtype=float),
    )


def i5_cascade_admission(
    regime_paths: pl.DataFrame,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """P(IndexTB=+1 | admitted) - P(+1 | rejected) on daily-open days."""
    daily_open = regime_paths.filter(
        pl.col("daily_regime").is_in(list(TRADEABLE_DAILY)) & ~pl.col("open_bleed")
    )
    results = []

    for side_name, state, entry_col, label_col in (
        ("long", IntradayRegime.TREND_UP.value, "long_entry_ok", "tb_label_long"),
        ("short", IntradayRegime.TREND_DOWN.value, "short_entry_ok", "tb_label_short"),
    ):
        panel = daily_open.filter(pl.col(entry_col) & pl.col(label_col).is_not_null())
        admitted = (panel["intraday_regime"] == state).to_numpy()
        tp = panel[label_col].to_numpy() == 1
        n_adm = int(admitted.sum())
        n_rej = int((~admitted).sum())

        if n_adm < MIN_BARS or n_rej < MIN_BARS:
            results.append(
                MetricResult(
                    "I5", side_name, None, None, None, min(n_adm, n_rej), False,
                    f"adm={n_adm} rej={n_rej}",
                )
            )
            continue

        p_adm = float(tp[admitted].mean())
        p_rej = float(tp[~admitted].mean())
        i5 = p_adm - p_rej

        adm_tp, adm_n, rej_tp, rej_n = _i5_session_counts(panel, state, label_col)
        boot = np.empty(n_boot)
        for b in range(n_boot):
            idx = rng.integers(0, adm_n.size, size=adm_n.size)
            a_n, r_n = adm_n[idx].sum(), rej_n[idx].sum()
            boot[b] = (
                float(adm_tp[idx].sum() / a_n - rej_tp[idx].sum() / r_n)
                if a_n > 0 and r_n > 0
                else i5
            )
        ci_lo, ci_hi = float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))
        results.append(
            MetricResult(
                "I5",
                side_name,
                i5,
                ci_lo,
                ci_hi,
                n_adm,
                ci_lo > 0.0,
                f"p_adm={p_adm:.3f} p_rej={p_rej:.3f} n_rej={n_rej}",
            )
        )
    return results


def i4_dwell_flip(regime_paths: pl.DataFrame) -> list[MetricResult]:
    """Average state dwell (bars) and TREND_UP<->DOWN flip rate."""
    ordered = regime_paths.filter(pl.col("intraday_regime").is_not_null()).sort("date")
    regimes = ordered["intraday_regime"].to_list()
    lengths = (
        ordered.group_by("date_only", maintain_order=True)
        .len()
        .get_column("len")
        .to_numpy()
        .astype(int)
    )
    flip = IntradayHMMRegimeModel.trend_flip_rate(regimes, lengths)

    dwell: dict[str, list[int]] = {s.value: [] for s in IntradayRegime}
    offset = 0
    for length in lengths:
        block = regimes[offset : offset + int(length)]
        offset += int(length)
        run_state, run_len = block[0], 1
        for state in block[1:]:
            if state == run_state:
                run_len += 1
                continue
            dwell[run_state].append(run_len)
            run_state, run_len = state, 1
        dwell[run_state].append(run_len)

    results = [MetricResult("I4", "flip_rate", flip, None, None, int(lengths.sum()), None)]
    for state in (
        IntradayRegime.TREND_UP.value,
        IntradayRegime.TREND_DOWN.value,
        IntradayRegime.CHOP.value,
        IntradayRegime.HIGH_VOL.value,
    ):
        episodes = dwell[state]
        asd = float(np.mean(episodes)) if episodes else float("nan")
        results.append(MetricResult("I4", f"ASD/{state}", asd, None, None, len(episodes), None))
    return results


def evaluate_intraday(
    regime_preds: pl.DataFrame,
    market_15m: pl.DataFrame,
    hmm: IntradayHMMRegimeModel,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    paths = join_regime_paths(regime_preds, attach_index_paths(market_15m))
    metrics = [i7_state_map_audit(hmm)]
    metrics.extend(i5_cascade_admission(paths, n_boot, rng))
    metrics.extend(i1_directional_hit_rate(paths, n_boot, rng))
    metrics.extend(i4_dwell_flip(paths))
    return metrics
