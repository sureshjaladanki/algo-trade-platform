"""Stage C — multiclass first-hit head, calibration, geometry argmax (M5/M5R).

Production ``GBMHorizonModel`` stays untouched. Fresh trainer lives here.

Class encoding is fixed everywhere: 0 = SL first, 1 = timeout, 2 = TP first,
mapped from the labeler's −1 / 0 / +1.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import lightgbm as lgb
import numpy as np
from sklearn.isotonic import IsotonicRegression

from src.horizon.fresh.friction import C_STAR

_CLASS_ORDER: tuple[int, ...] = (0, 1, 2)  # SL, TO, TP


def encode_labels(labels: np.ndarray) -> np.ndarray:
    """−1/0/+1 first-hit labels → class indices 0/1/2."""
    return np.where(labels == 1, 2, np.where(labels == -1, 0, 1))


@dataclass
class FreshHorizonModel:
    """Multiclass P(SL)/P(TO)/P(TP) with optional isotonic calibration."""

    model: lgb.LGBMClassifier | None = None
    to_model: lgb.LGBMRegressor | None = None
    calibrators: dict[int, IsotonicRegression] = field(default_factory=dict)
    n_estimators: int = 300
    learning_rate: float = 0.05
    num_leaves: int = 31
    min_child_samples: int = 40

    def fit(
        self,
        x: np.ndarray,
        labels: np.ndarray,
        *,
        to_returns: np.ndarray | None = None,
    ) -> FreshHorizonModel:
        y = encode_labels(labels)
        self.model = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            num_leaves=self.num_leaves,
            min_child_samples=self.min_child_samples,
            verbosity=-1,
        )
        self.model.fit(x, y)
        if to_returns is not None:
            to_mask = labels == 0
            if to_mask.sum() >= 50:
                self.to_model = lgb.LGBMRegressor(
                    n_estimators=200, learning_rate=0.05, verbosity=-1
                )
                self.to_model.fit(x[to_mask], to_returns[to_mask])
        return self

    def calibrate(self, x_val: np.ndarray, labels_val: np.ndarray) -> FreshHorizonModel:
        """
        Fit per-class isotonic maps on a held-out (purged) validation slice.

        Without this the head is scored on raw GBDT margins, which are not
        probabilities and shift with the outcome base rate between folds — the
        K3 reliability gate then measures the missing calibrator, not the model.
        """
        raw = self._raw_proba(x_val)
        y = encode_labels(labels_val)
        self.calibrators = {}
        for cls in _CLASS_ORDER:
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            iso.fit(raw[:, cls], (y == cls).astype(float))
            self.calibrators[cls] = iso
        return self

    def _raw_proba(self, x: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("fit required")
        proba = self.model.predict_proba(x)
        # LightGBM drops classes absent from train; re-expand to the fixed order.
        out = np.zeros((proba.shape[0], len(_CLASS_ORDER)))
        for i, cls in enumerate(self.model.classes_):
            out[:, int(cls)] = proba[:, i]
        return out

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        """Columns: P(SL), P(TO), P(TP). Calibrated when ``calibrate`` was called."""
        proba = self._raw_proba(x)
        if not self.calibrators:
            return proba
        cal = np.column_stack(
            [self.calibrators[cls].predict(proba[:, cls]) for cls in _CLASS_ORDER]
        )
        total = cal.sum(axis=1, keepdims=True)
        return np.divide(cal, total, out=np.full_like(cal, 1 / 3), where=total > 0)


def expected_ev_net(
    p_tp: float | np.ndarray,
    p_sl: float | np.ndarray,
    p_to: float | np.ndarray,
    tp_w: float | np.ndarray,
    sl_w: float | np.ndarray,
    e_to: float | np.ndarray = 0.0,
    *,
    cost: float | np.ndarray = C_STAR,
) -> float | np.ndarray:
    """
    EV_net = p_tp·g − p_sl·s + p_to·E[r|TO] − cost.

    ``cost`` is scalar ``c*`` (stress / design) or a row-level ``c_eff`` array
    (blueprint §3.1). Flat ``C_STAR`` is the universe average, not the per-trade
    hurdle wherever Stage A has run.
    """
    return (
        np.asarray(p_tp) * np.asarray(tp_w)
        - np.asarray(p_sl) * np.asarray(sl_w)
        + np.asarray(p_to) * np.asarray(e_to)
        - np.asarray(cost)
    )


def geometry_argmax(
    proba_for: Callable[[float, float], tuple[float, float, float]],
    range_hat: float,
    *,
    tp_mults: tuple[float, ...] = (0.4, 0.5, 0.6),
    sl_mults: tuple[float, ...] = (0.2, 0.25, 0.3),
    e_to: float = 0.0,
    cost: float = C_STAR,
) -> tuple[float, float, float]:
    """
    Sweep ``(tp_mult, sl_mult)`` as fractions of Stage B range; pick argmax EV_net.

    ``proba_for(tp_mult, sl_mult)`` must return geometry-**conditional**
    ``(p_tp, p_sl, p_to)``. Blueprint §5.3 requires the multipliers to be model
    features for exactly this reason: with geometry-invariant probabilities
    ``EV_net`` rises monotonically in ``g`` and falls in ``s``, so the sweep
    always returns the widest target and tightest stop regardless of the data.

    Returns ``(g_star, s_star, ev_net_hat)``.
    """
    best = (-np.inf, 0.0, 0.0)
    for tm in tp_mults:
        for sm in sl_mults:
            g, s = tm * range_hat, sm * range_hat
            if g <= 0 or s <= 0:
                continue
            p_tp, p_sl, p_to = proba_for(tm, sm)
            ev = expected_ev_net(p_tp, p_sl, p_to, g, s, e_to, cost=cost)
            if ev > best[0]:
                best = (ev, g, s)
    return best[1], best[2], best[0]
