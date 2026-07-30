import numpy as np
import polars as pl
from hmmlearn.hmm import GaussianHMM
from .types import IntradayRegime

class IntradayHMMRegime:
    """
    Tier 1 Intraday Regime Classifier using a 4-state Gaussian HMM.
    Runs on 15m Nifty candles with TOD-normalized emissions.
    """
    
    def __init__(self, random_state: int = 42, n_iter: int = 100):
        self.n_components = 4
        self.model = GaussianHMM(
            n_components=self.n_components, 
            covariance_type="diag", 
            n_iter=n_iter, 
            random_state=random_state,
            init_params="kmeans"
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
        2: volz_15 (Volume z-score)
        3: vwap_dist (Signed VWAP distance)
        """
        states = list(range(self.n_components))
        
        # HIGH_VOL is characterized by highest volatility and volume
        rv_means = means[:, 1]
        high_vol_state = int(np.argmax(rv_means))
        states.remove(high_vol_state)
        
        # CHOP is characterized by lowest absolute directional features and low volatility
        # We can look at the lowest absolute vwap_dist and r_15 among remaining
        abs_dir_means = np.abs(means[states, 0]) + np.abs(means[states, 3])
        chop_state = states[int(np.argmin(abs_dir_means))]
        states.remove(chop_state)
        
        # The remaining two are TREND_UP and TREND_DOWN, distinguishable by r_15 and vwap_dist signs
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
            trend_down_state: IntradayRegime.TREND_DOWN
        }

    def fit(self, df: pl.DataFrame, feature_cols: list[str] = ["r_15", "rv_15", "volz_15", "vwap_dist"]):
        """
        Fits the HMM on historical TOD-normalized features.
        """
        X = df.select(feature_cols).to_numpy()
        # Drop NaNs
        X = X[~np.isnan(X).any(axis=1)]
        self.model.fit(X)
        self.is_fitted = True
        self._map_states(self.model.means_)
        
    def predict(self, df: pl.DataFrame, feature_cols: list[str] = ["r_15", "rv_15", "volz_15", "vwap_dist"], apply_hysteresis: bool = True) -> pl.DataFrame:
        """
        Predicts the intraday regime for a given dataframe of features.
        Optionally applies hysteresis to avoid flickering between TREND_UP and TREND_DOWN.
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
            
        X = df.select(feature_cols).to_numpy()
        # Handle NaNs by masking or forwarding. For simplicity, filling with 0
        X = np.nan_to_num(X)
        
        hidden_states = self.model.predict(X)
        regimes = [self.state_map[s].value for s in hidden_states]
        
        df = df.with_columns(pl.Series(name="intraday_regime_raw", values=regimes))
        
        if apply_hysteresis:
            df = self._apply_hysteresis(df, "intraday_regime_raw", "intraday_regime")
        else:
            df = df.with_columns(pl.col("intraday_regime_raw").alias("intraday_regime"))
            
        return df

    def _apply_hysteresis(self, df: pl.DataFrame, in_col: str, out_col: str) -> pl.DataFrame:
        """
        Applies a simple minimum dwell time / hysteresis logic to avoid rapid flips
        between TREND_UP and TREND_DOWN.
        Requires at least 2 consecutive bars of the opposite trend to flip.
        """
        raw_regimes = df[in_col].to_list()
        smoothed = []
        
        current_state = None
        for i, state in enumerate(raw_regimes):
            if current_state is None:
                current_state = state
                smoothed.append(current_state)
                continue
                
            # If we are flipping between TREND_UP and TREND_DOWN, require confirmation
            if current_state in (IntradayRegime.TREND_UP.value, IntradayRegime.TREND_DOWN.value) and \
               state in (IntradayRegime.TREND_UP.value, IntradayRegime.TREND_DOWN.value) and \
               state != current_state:
                
                # Check previous bar if we have one to see if this is a confirmed flip
                # Simplest hysteresis: delay the flip by 1 bar unless the next bar confirms it
                # For online prediction, we can't look ahead. So we hold the previous state unless
                # the current state and the previous state are the same (new state maintained for 2 bars).
                if i >= 1 and raw_regimes[i] == raw_regimes[i-1]:
                    current_state = state
            else:
                current_state = state
                
            smoothed.append(current_state)
            
        return df.with_columns(pl.Series(name=out_col, values=smoothed))
