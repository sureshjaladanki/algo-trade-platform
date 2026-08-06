import itertools

import numpy as np
import polars as pl
from hmmlearn.hmm import GaussianHMM

from .types import IntradayRegime

DEFAULT_FEATURE_COLS = ["r_15", "rv_15", "vwap_dist"]


class IntradayHMMRegimeModel:
    """
    Tier 1 Intraday Regime Classifier using a 4-state Gaussian HMM.
    Runs on 15m candles with TOD-normalized emissions.
    Sequences are (date) day sessions via hmmlearn `lengths`.
    """

    def __init__(self, random_state: int = 42, n_iter: int = 100):
        self.n_components = 4
        self.random_state = random_state
        self.n_iter = n_iter
        self.model = GaussianHMM(
            n_components=self.n_components,
            covariance_type="diag",
            n_iter=n_iter,
            random_state=random_state,
            init_params="kmeans",
        )
        self.is_fitted = False
        self.state_map = {}  # Maps internal HMM states (0,1,2,3) to IntradayRegime

    def _map_states(self, means: np.ndarray):
        """
        Maps the 4 unlabelled HMM states to:
        TREND_UP, TREND_DOWN, CHOP, HIGH_VOL
        based on emission means.

        Assumed feature order:
        0: r_15 (Signed return)
        1: rv_15 (Range / Volatility)
        2: vwap_dist (Signed TWAP distance; feature name kept for compatibility)
        """
        states = list(range(self.n_components))

        # HIGH_VOL is characterized by highest volatility
        rv_means = means[:, 1]
        high_vol_state = int(np.argmax(rv_means))
        states.remove(high_vol_state)

        # CHOP is characterized by lowest absolute directional features
        abs_dir_means = np.abs(means[states, 0]) + np.abs(means[states, 2])
        chop_state = states[int(np.argmin(abs_dir_means))]
        states.remove(chop_state)

        # The remaining two are TREND_UP and TREND_DOWN, distinguishable by r_15
        state_a, state_b = states
        if means[state_a, 0] > means[state_b, 0]:
            trend_up_state = state_a
            trend_down_state = state_b
        else:
            trend_up_state = state_b
            trend_down_state = state_a

        self.state_map = {
            high_vol_state: IntradayRegime.HIGH_VOL,
            chop_state: IntradayRegime.CHOP,
            trend_up_state: IntradayRegime.TREND_UP,
            trend_down_state: IntradayRegime.TREND_DOWN,
        }

    @staticmethod
    def prepare_sequences(
        df: pl.DataFrame,
        *,
        drop_nonfinite: bool = True,
    ) -> tuple[pl.DataFrame, np.ndarray, np.ndarray]:
        """
        Build emission matrix X and per-session lengths for day sessions.

        Rows are sorted by date (datetime). Non-finite feature rows are dropped
        (fit/score) so lengths stay consistent with X.
        """
        feature_cols = DEFAULT_FEATURE_COLS
        required = {"date", *feature_cols}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns for HMM sequences: {sorted(missing)}")

        ordered = df.sort("date")
        X = ordered.select(feature_cols).to_numpy().astype(float)

        if drop_nonfinite:
            finite_mask = np.isfinite(X).all(axis=1)
            ordered = ordered.filter(pl.Series(finite_mask))
            X = X[finite_mask]
        else:
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        if ordered.height == 0:
            return ordered, np.empty((0, len(feature_cols))), np.array([], dtype=int)

        lengths = (
            ordered.group_by(pl.col("date").dt.date(), maintain_order=True)
            .len()
            .get_column("len")
            .to_numpy()
            .astype(int)
        )
        return ordered, X, lengths

    @staticmethod
    def n_free_params(n_components: int, n_features: int, covariance_type: str = "diag") -> int:
        """
        Free parameter count for AIC/BIC.

        For diag GaussianHMM: k = N^2 - 1 + 2 N D
          - startprob: N - 1
          - transmat: N (N - 1)
          - means: N D
          - diag covars: N D
        """
        if covariance_type != "diag":
            raise ValueError(f"n_free_params only implemented for diag, got {covariance_type}")
        n, d = n_components, n_features
        return n * n - 1 + 2 * n * d

    def fit(self, df: pl.DataFrame):
        """
        Fits the HMM on historical TOD-normalized features using day-session lengths.

        Caller is responsible for cascade gates (daily tradeable days, no open-auction bleed).
        """
        _, X, lengths = self.prepare_sequences(df, drop_nonfinite=True)
        if X.shape[0] == 0:
            raise ValueError("No finite intraday rows available to fit HMM.")

        self.model.fit(X, lengths=lengths)
        self.is_fitted = True
        self._map_states(self.model.means_)

    def score(self, df: pl.DataFrame) -> tuple[float, int]:
        """
        Total log-likelihood under the fitted model.

        Caller should pass the same cascade-gated rows used for fit/predict.

        Returns (total_loglik, n_samples).
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before score.")

        _, X, lengths = self.prepare_sequences(df, drop_nonfinite=True)
        if X.shape[0] == 0:
            return float("nan"), 0
        return float(self.model.score(X, lengths=lengths)), int(X.shape[0])

    def predict(
        self,
        df: pl.DataFrame,
        apply_hysteresis: bool = True,
    ) -> pl.DataFrame:
        """
        Predicts the intraday regime for cascade-gated feature rows.
        Decodes per date session via `lengths`.
        Optionally applies hysteresis within each session.

        Hard rules (daily HOSTILE/NO_TRADE, open-auction NO_TRADE) are applied by the
        pipeline gate — this method only runs the HMM on the rows it is given.
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")

        # Keep row alignment with caller by filling non-finite; still decode per session.
        ordered, X, lengths = self.prepare_sequences(df, drop_nonfinite=False)
        if ordered.height == 0:
            return df.with_columns(
                pl.lit(None).alias("intraday_regime_raw"),
                pl.lit(None).alias("intraday_regime"),
            )

        hidden_states = self.model.predict(X, lengths=lengths)
        regimes = [self.state_map[int(s)].value for s in hidden_states]
        ordered = ordered.with_columns(pl.Series(name="intraday_regime_raw", values=regimes))

        if apply_hysteresis:
            ordered = self._apply_hysteresis_by_lengths(
                ordered, "intraday_regime_raw", "intraday_regime", lengths
            )
        else:
            ordered = ordered.with_columns(pl.col("intraday_regime_raw").alias("intraday_regime"))

        return df.join(
            ordered.select(["date", "intraday_regime_raw", "intraday_regime"]),
            on="date",
            how="left",
        )

    def _apply_hysteresis_by_lengths(
        self,
        df: pl.DataFrame,
        in_col: str,
        out_col: str,
        lengths: np.ndarray,
    ) -> pl.DataFrame:
        raw_regimes = df[in_col].to_list()
        smoothed: list[str] = []
        offset = 0
        for length in lengths:
            block = raw_regimes[offset : offset + int(length)]
            smoothed.extend(self._hysteresis_block(block))
            offset += int(length)
        return df.with_columns(pl.Series(name=out_col, values=smoothed))

    @staticmethod
    def _hysteresis_block(raw_regimes: list[str]) -> list[str]:
        """
        Minimum dwell / hysteresis within one session.
        Requires 2 consecutive opposite TREND bars to flip TREND_UP <-> TREND_DOWN.
        """
        trend_states = {IntradayRegime.TREND_UP.value, IntradayRegime.TREND_DOWN.value}
        smoothed = []
        current_state = None

        for i, state in enumerate(raw_regimes):
            if current_state is None:
                current_state = state
            elif (
                current_state in trend_states
                and state in trend_states
                and state != current_state
            ):
                if i >= 1 and state == raw_regimes[i - 1]:
                    current_state = state
            else:
                current_state = state

            smoothed.append(current_state)
        return smoothed

    @staticmethod
    def trend_flip_rate(regimes: list[str], lengths: np.ndarray) -> float:
        """
        Direct TREND_UP <-> TREND_DOWN flips / non-self transitions, within sessions.
        """
        trend = {IntradayRegime.TREND_UP.value, IntradayRegime.TREND_DOWN.value}
        flips = 0
        non_self = 0
        offset = 0
        for length in lengths:
            block = regimes[offset : offset + int(length)]
            offset += int(length)
            for prev, curr in itertools.pairwise(block):
                if prev == curr:
                    continue
                non_self += 1
                if prev in trend and curr in trend:
                    flips += 1
        if non_self == 0:
            return 0.0
        return flips / non_self

    def fit_diagnostics(self) -> dict[str, float]:
        """Train-side fit diagnostics from the fitted hmmlearn model (no data needed)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before diagnostics.")

        m = self.model
        monitor = getattr(m, "monitor_", None)
        history = list(monitor.history) if monitor is not None else []
        n = self.n_components
        d = int(m.n_features)
        k = self.n_free_params(n, d, m.covariance_type)

        out: dict[str, float] = {
            "hmm_converged": float(bool(monitor.converged)) if monitor is not None else 0.0,
            "hmm_n_iter_ran": float(len(history)),
        }

        if history:
            train_ll = float(history[-1])
            out["train_loglik_total"] = train_ll
            # n_samples for per-sample / AIC is recovered by caller when scoring train X

        out["hmm_n_free_params"] = float(k)

        for state_idx, regime in self.state_map.items():
            label = regime.value
            out[f"trans_self_{label}"] = float(m.transmat_[state_idx, state_idx])
            for j, feat in enumerate(DEFAULT_FEATURE_COLS):
                out[f"emit_mean_{label}_{feat}"] = float(m.means_[state_idx, j])

        return out
